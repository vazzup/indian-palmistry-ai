"""
Security headers middleware for enhanced web security.

This middleware adds essential security headers to all HTTP responses
to protect against common web vulnerabilities including XSS, CSRF,
clickjacking, and information disclosure.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.
    
    Headers added:
    - Content-Security-Policy: Prevents XSS and code injection
    - X-Content-Type-Options: Prevents MIME-type sniffing
    - X-Frame-Options: Prevents clickjacking
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    - X-XSS-Protection: Legacy XSS protection
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Content Security Policy for production-ready security
        self.csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            "media-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Security headers to apply to all responses
        self.security_headers = {
            "Content-Security-Policy": self.csp_policy,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "camera=(), microphone=(), location=(), "
                "accelerometer=(), gyroscope=(), magnetometer=(), "
                "payment=(), usb=()"
            ),
            "X-XSS-Protection": "1; mode=block",
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add security headers to all HTTP responses.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with security headers added
        """
        # Process the request
        response = await call_next(request)
        
        # Add security headers to the response
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value
        
        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with strict security settings.
    
    Features:
    - Exact origin matching (no wildcards)
    - Credential support
    - Proper Vary header handling
    - Environment-specific allowed origins
    """
    
    def __init__(self, app: ASGIApp, allowed_origins: list[str] = None):
        super().__init__(app)
        
        # Default allowed origins for development
        self.allowed_origins = allowed_origins or [
            "http://localhost:3000",
            "http://localhost:3001", 
            "https://localhost:3000",
            "https://localhost:3001"
        ]
        
        # CORS headers for successful preflight
        self.cors_headers = {
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": (
                "Content-Type, Authorization, X-CSRF-Token, "
                "X-Requested-With, Accept, Origin"
            ),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",  # 24 hours
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Handle CORS with strict security settings.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with appropriate CORS headers
        """
        # Get the origin from the request
        origin = request.headers.get("Origin")
        
        # Always add Vary: Origin header for proper caching
        vary_header = "Origin"
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response(status_code=204)
            response.headers["Vary"] = vary_header
            
            # Only add CORS headers for allowed origins
            if origin in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                for header_name, header_value in self.cors_headers.items():
                    response.headers[header_name] = header_value
            
            return response
        
        # Process the actual request
        response = await call_next(request)
        
        # Add Vary header
        existing_vary = response.headers.get("Vary", "")
        if existing_vary:
            response.headers["Vary"] = f"{existing_vary}, {vary_header}"
        else:
            response.headers["Vary"] = vary_header
        
        # Add CORS headers for allowed origins
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response