"""
Rate limiting middleware and security enhancements.
"""
import time
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import ipaddress

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cache import cache_service
from app.core.logging import get_logger

logger = get_logger(__name__)

class RateLimitType(Enum):
    """Types of rate limits."""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    ENDPOINT = "endpoint"
    ANALYSIS = "analysis"
    CONVERSATION = "conversation"

class SecurityThreatLevel(Enum):
    """Security threat levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RateLimitConfig:
    """Rate limit configuration."""
    
    def __init__(
        self,
        requests: int,
        window_seconds: int,
        burst_multiplier: float = 2.0,
        block_duration_seconds: int = 300
    ):
        self.requests = requests
        self.window_seconds = window_seconds
        self.burst_multiplier = burst_multiplier
        self.block_duration_seconds = block_duration_seconds
        self.burst_limit = int(requests * burst_multiplier)

# Default rate limit configurations
RATE_LIMITS = {
    # Global limits (per IP)
    RateLimitType.GLOBAL: RateLimitConfig(requests=100, window_seconds=60),
    
    # User-specific limits (per authenticated user)
    RateLimitType.USER: RateLimitConfig(requests=200, window_seconds=3600),
    
    # IP-based limits
    RateLimitType.IP: RateLimitConfig(requests=1000, window_seconds=3600),
    
    # Endpoint-specific limits
    RateLimitType.ENDPOINT: RateLimitConfig(requests=20, window_seconds=60),
    
    # Resource-intensive operations
    RateLimitType.ANALYSIS: RateLimitConfig(requests=10, window_seconds=3600),
    RateLimitType.CONVERSATION: RateLimitConfig(requests=50, window_seconds=3600)
}

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with adaptive security."""
    
    def __init__(self, app, enable_security_monitoring: bool = True):
        super().__init__(app)
        self.enable_security_monitoring = enable_security_monitoring
        self.blocked_ips = set()
        self.suspicious_patterns = [
            b"<script",
            b"javascript:",
            b"eval(",
            b"union select",
            b"drop table",
            b"../",
            b"passwd",
            b"etc/shadow"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting and security checks."""
        
        try:
            # Get client information
            client_info = await self._get_client_info(request)
            
            # Security screening
            if self.enable_security_monitoring:
                security_check = await self._security_screening(request, client_info)
                if security_check["blocked"]:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Request blocked",
                            "reason": security_check["reason"],
                            "retry_after": security_check.get("retry_after", 300)
                        }
                    )
            
            # Apply rate limits
            rate_limit_result = await self._apply_rate_limits(request, client_info)
            
            if rate_limit_result["limited"]:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "limit_type": rate_limit_result["type"],
                        "retry_after": rate_limit_result["retry_after"],
                        "limit": rate_limit_result["limit"],
                        "window": rate_limit_result["window"]
                    },
                    headers={
                        "Retry-After": str(rate_limit_result["retry_after"]),
                        "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                        "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                        "X-RateLimit-Reset": str(rate_limit_result["reset"])
                    }
                )
            
            # Process request
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add rate limit headers
            response.headers.update({
                "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                "X-RateLimit-Reset": str(rate_limit_result["reset"]),
                "X-Process-Time": str(round(process_time, 3))
            })
            
            # Log request metrics
            await self._log_request_metrics(request, response, process_time, client_info)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Allow request to proceed on middleware errors
            return await call_next(request)
    
    async def _get_client_info(self, request: Request) -> Dict[str, any]:
        """Extract client information from request."""
        
        # Get real IP address (considering proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        real_ip = request.headers.get("x-real-ip")
        
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif real_ip:
            client_ip = real_ip
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # Get user information if available
        user_id = getattr(request.state, "user_id", None)
        
        # Get user agent
        user_agent = request.headers.get("user-agent", "")
        
        return {
            "ip": client_ip,
            "user_id": user_id,
            "user_agent": user_agent,
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.utcnow()
        }
    
    async def _security_screening(self, request: Request, client_info: Dict) -> Dict[str, any]:
        """Perform security screening on request."""
        
        client_ip = client_info["ip"]
        
        # Check if IP is already blocked
        if client_ip in self.blocked_ips:
            return {
                "blocked": True,
                "reason": "IP temporarily blocked",
                "threat_level": SecurityThreatLevel.HIGH.value,
                "retry_after": 300
            }
        
        # Check for suspicious IP ranges
        if await self._is_suspicious_ip(client_ip):
            threat_level = SecurityThreatLevel.MEDIUM.value
        else:
            threat_level = SecurityThreatLevel.LOW.value
        
        # Check request body for malicious patterns
        body_check = await self._check_request_body(request)
        if body_check["suspicious"]:
            threat_level = SecurityThreatLevel.HIGH.value
        
        # Check for brute force attempts
        brute_force_check = await self._check_brute_force(client_info)
        if brute_force_check["detected"]:
            threat_level = SecurityThreatLevel.CRITICAL.value
            
            # Temporarily block IP for critical threats
            if threat_level == SecurityThreatLevel.CRITICAL.value:
                self.blocked_ips.add(client_ip)
                # Remove from blocked list after 1 hour
                import asyncio
                asyncio.create_task(self._unblock_ip_after_delay(client_ip, 3600))
                
                return {
                    "blocked": True,
                    "reason": "Brute force attack detected",
                    "threat_level": threat_level,
                    "retry_after": 3600
                }
        
        # Check rate of suspicious requests
        suspicious_rate = await self._check_suspicious_request_rate(client_ip)
        if suspicious_rate > 0.5:  # More than 50% suspicious requests
            return {
                "blocked": True,
                "reason": "High rate of suspicious requests",
                "threat_level": SecurityThreatLevel.HIGH.value,
                "retry_after": 600
            }
        
        return {
            "blocked": False,
            "threat_level": threat_level
        }
    
    async def _apply_rate_limits(self, request: Request, client_info: Dict) -> Dict[str, any]:
        """Apply various rate limits to the request."""
        
        user_id = client_info["user_id"]
        client_ip = client_info["ip"]
        path = client_info["path"]
        
        # Determine which limits to apply
        limits_to_check = [
            (RateLimitType.GLOBAL, f"global:{client_ip}"),
            (RateLimitType.IP, f"ip:{client_ip}")
        ]
        
        if user_id:
            limits_to_check.append((RateLimitType.USER, f"user:{user_id}"))
        
        # Endpoint-specific limits
        if path.startswith("/api/v1/analyses"):
            limits_to_check.append((RateLimitType.ANALYSIS, f"analysis:{user_id or client_ip}"))
        elif path.startswith("/api/v1/conversations") or "talk" in path:
            limits_to_check.append((RateLimitType.CONVERSATION, f"conversation:{user_id or client_ip}"))
        elif any(endpoint in path for endpoint in ["/auth/login", "/auth/register"]):
            limits_to_check.append((RateLimitType.ENDPOINT, f"auth:{client_ip}"))
        
        # Check each limit
        most_restrictive = None
        for limit_type, identifier in limits_to_check:
            limit_check = await self._check_rate_limit(limit_type, identifier)
            
            if limit_check["exceeded"]:
                if most_restrictive is None or limit_check["retry_after"] > most_restrictive["retry_after"]:
                    most_restrictive = limit_check
                    most_restrictive["type"] = limit_type.value
        
        if most_restrictive:
            return {
                "limited": True,
                **most_restrictive
            }
        
        # Increment counters for successful checks
        for limit_type, identifier in limits_to_check:
            await self._increment_rate_limit_counter(limit_type, identifier)
        
        # Return success with rate limit info
        global_limit = RATE_LIMITS[RateLimitType.GLOBAL]
        return {
            "limited": False,
            "limit": global_limit.requests,
            "remaining": global_limit.requests - 1,  # Simplified
            "reset": int(time.time()) + global_limit.window_seconds,
            "window": global_limit.window_seconds
        }
    
    async def _check_rate_limit(self, limit_type: RateLimitType, identifier: str) -> Dict[str, any]:
        """Check if rate limit is exceeded for identifier."""
        
        config = RATE_LIMITS[limit_type]
        current_time = int(time.time())
        window_start = current_time - config.window_seconds
        
        # Get current count
        count = await cache_service.get_rate_limit(identifier)
        
        if count > config.requests:
            # Check if we're in burst allowance
            if count > config.burst_limit:
                return {
                    "exceeded": True,
                    "retry_after": config.window_seconds,
                    "limit": config.requests,
                    "remaining": 0,
                    "reset": current_time + config.window_seconds
                }
        
        return {
            "exceeded": False,
            "limit": config.requests,
            "remaining": max(0, config.requests - count),
            "reset": current_time + config.window_seconds
        }
    
    async def _increment_rate_limit_counter(self, limit_type: RateLimitType, identifier: str):
        """Increment rate limit counter."""
        
        config = RATE_LIMITS[limit_type]
        await cache_service.increment_rate_limit(identifier, config.window_seconds)
    
    async def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP address is suspicious."""
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Check for private/local IPs (not suspicious in dev)
            if ip_obj.is_private or ip_obj.is_loopback:
                return False
            
            # Check against known malicious IP ranges (simplified)
            suspicious_ranges = [
                # Tor exit nodes (example ranges)
                ipaddress.ip_network("198.96.155.0/24"),
                # Add more suspicious ranges as needed
            ]
            
            for network in suspicious_ranges:
                if ip_obj in network:
                    return True
            
            return False
            
        except ValueError:
            # Invalid IP address
            return True
    
    async def _check_request_body(self, request: Request) -> Dict[str, any]:
        """Check request body for malicious patterns."""
        
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                # Check if content-type suggests file upload
                content_type = request.headers.get("content-type", "")
                
                if "multipart/form-data" in content_type:
                    # Skip body reading for file uploads to avoid issues
                    return {"suspicious": False}
                
                # For other content types, read and check body
                if hasattr(request, "_body"):
                    body = request._body
                else:
                    # Don't consume body here to avoid breaking downstream processing
                    return {"suspicious": False}
                
                if body:
                    body_lower = body.lower()
                    
                    # Check for malicious patterns
                    for pattern in self.suspicious_patterns:
                        if pattern in body_lower:
                            logger.warning(f"Suspicious pattern detected in request: {pattern.decode('utf-8', errors='ignore')}")
                            return {"suspicious": True, "pattern": pattern.decode('utf-8', errors='ignore')}
            
            return {"suspicious": False}
            
        except Exception as e:
            logger.error(f"Error checking request body: {e}")
            return {"suspicious": False}
    
    async def _check_brute_force(self, client_info: Dict) -> Dict[str, any]:
        """Check for brute force attack patterns."""
        
        client_ip = client_info["ip"]
        path = client_info["path"]
        
        # Only check for auth endpoints
        if not any(endpoint in path for endpoint in ["/auth/login", "/auth/register"]):
            return {"detected": False}
        
        # Check failed login attempts in the last 15 minutes
        brute_force_key = f"brute_force:{client_ip}"
        attempts = await cache_service.get_rate_limit(brute_force_key)
        
        # If more than 10 attempts in 15 minutes, consider it brute force
        if attempts > 10:
            logger.warning(f"Brute force attack detected from IP: {client_ip}")
            return {
                "detected": True,
                "attempts": attempts
            }
        
        return {"detected": False, "attempts": attempts}
    
    async def _check_suspicious_request_rate(self, client_ip: str) -> float:
        """Check the rate of suspicious requests from IP."""
        
        # Get total requests and suspicious requests from cache
        total_key = f"requests_total:{client_ip}"
        suspicious_key = f"requests_suspicious:{client_ip}"
        
        total_requests = await cache_service.get_rate_limit(total_key) or 1
        suspicious_requests = await cache_service.get_rate_limit(suspicious_key) or 0
        
        return suspicious_requests / total_requests
    
    async def _log_request_metrics(
        self,
        request: Request,
        response,
        process_time: float,
        client_info: Dict
    ):
        """Log request metrics for monitoring."""
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_info["ip"],
            "user_id": client_info["user_id"],
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": round(process_time, 3),
            "user_agent": client_info["user_agent"][:100]  # Truncate long user agents
        }
        
        # Log to structured logger
        logger.info("Request processed", extra={"metrics": metrics})
        
        # Update request counters
        total_key = f"requests_total:{client_info['ip']}"
        await cache_service.increment_rate_limit(total_key, 3600)  # 1 hour window
        
        # Track suspicious requests
        if response.status_code >= 400:
            suspicious_key = f"requests_suspicious:{client_info['ip']}"
            await cache_service.increment_rate_limit(suspicious_key, 3600)
    
    async def _unblock_ip_after_delay(self, ip: str, delay_seconds: int):
        """Remove IP from blocked list after delay."""
        
        import asyncio
        await asyncio.sleep(delay_seconds)
        self.blocked_ips.discard(ip)
        logger.info(f"Unblocked IP after delay: {ip}")

class SecurityService:
    """Additional security utilities."""
    
    @staticmethod
    async def validate_file_upload(file_data: bytes, allowed_types: list = None) -> Dict[str, any]:
        """Validate uploaded file for security."""
        
        if allowed_types is None:
            allowed_types = ["image/jpeg", "image/png", "image/gif"]
        
        # Check file size (max 10MB)
        if len(file_data) > 10 * 1024 * 1024:
            return {
                "valid": False,
                "reason": "File too large",
                "max_size": "10MB"
            }
        
        # Check magic bytes for file type detection
        magic_bytes_map = {
            b"\xff\xd8\xff": "image/jpeg",
            b"\x89PNG\r\n\x1a\n": "image/png",
            b"GIF87a": "image/gif",
            b"GIF89a": "image/gif"
        }
        
        detected_type = None
        for magic_bytes, file_type in magic_bytes_map.items():
            if file_data.startswith(magic_bytes):
                detected_type = file_type
                break
        
        if not detected_type:
            return {
                "valid": False,
                "reason": "Unknown file type"
            }
        
        if detected_type not in allowed_types:
            return {
                "valid": False,
                "reason": f"File type {detected_type} not allowed",
                "allowed_types": allowed_types
            }
        
        # Additional security checks could be added here
        # - Scan for embedded scripts
        # - Check for malicious EXIF data
        # - Virus scanning integration
        
        return {
            "valid": True,
            "detected_type": detected_type,
            "size_bytes": len(file_data)
        }
    
    @staticmethod
    def generate_security_token(length: int = 32) -> str:
        """Generate a secure random token."""
        
        import secrets
        return secrets.token_urlsafe(length)
    
    @staticmethod
    async def log_security_event(
        event_type: str,
        severity: SecurityThreatLevel,
        details: Dict[str, any],
        client_info: Dict[str, any] = None
    ):
        """Log security events for monitoring."""
        
        security_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity.value,
            "details": details
        }
        
        if client_info:
            security_event["client_info"] = client_info
        
        logger.warning(f"Security event: {event_type}", extra={"security_event": security_event})
        
        # In production, this could be sent to a SIEM system or security monitoring service

# Global security service instance
security_service = SecurityService()