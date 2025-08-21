"""
Tests for Rate Limiting Middleware.

This module tests the comprehensive rate limiting middleware with adaptive security,
threat detection, brute force protection, and multi-level rate limiting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from fastapi import Request, Response
from fastapi.testclient import TestClient

from app.middleware.rate_limiting import RateLimitMiddleware, RateLimitType, SecurityService


class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware class."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance for testing."""
        return RateLimitMiddleware(
            app=MagicMock(),
            enable_security_monitoring=True
        )

    @pytest.fixture
    def mock_request(self):
        """Mock HTTP request."""
        request = MagicMock(spec=Request)
        request.client.host = "192.168.1.100"
        request.method = "POST"
        request.url.path = "/api/v1/analyses/"
        request.headers = {"user-agent": "Mozilla/5.0 (Test Browser)"}
        return request

    @pytest.fixture
    def mock_response(self):
        """Mock HTTP response."""
        response = MagicMock(spec=Response)
        response.status_code = 200
        return response

    @pytest.mark.asyncio
    async def test_dispatch_within_limits(self, middleware, mock_request, mock_response):
        """Test request processing within rate limits."""
        with patch.object(middleware, 'cache_service') as mock_cache, \
             patch.object(middleware, '_check_rate_limits') as mock_check_limits, \
             patch.object(middleware, '_perform_security_screening') as mock_security:
            
            mock_check_limits.return_value = {"allowed": True}
            mock_security.return_value = {"threat_level": "low", "allowed": True}
            
            # Mock call_next
            call_next = AsyncMock(return_value=mock_response)
            
            result = await middleware.dispatch(mock_request, call_next)
            
            assert result == mock_response
            call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_rate_limited(self, middleware, mock_request):
        """Test request blocked by rate limiting."""
        with patch.object(middleware, 'cache_service') as mock_cache, \
             patch.object(middleware, '_check_rate_limits') as mock_check_limits:
            
            mock_check_limits.return_value = {
                "allowed": False,
                "limit_type": "user",
                "retry_after": 60
            }
            
            call_next = AsyncMock()
            
            response = await middleware.dispatch(mock_request, call_next)
            
            assert response.status_code == 429
            assert "Retry-After" in response.headers
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_security_blocked(self, middleware, mock_request):
        """Test request blocked by security screening."""
        with patch.object(middleware, 'cache_service') as mock_cache, \
             patch.object(middleware, '_check_rate_limits') as mock_check_limits, \
             patch.object(middleware, '_perform_security_screening') as mock_security:
            
            mock_check_limits.return_value = {"allowed": True}
            mock_security.return_value = {
                "allowed": False,
                "threat_level": "high",
                "reason": "Suspicious activity detected"
            }
            
            call_next = AsyncMock()
            
            response = await middleware.dispatch(mock_request, call_next)
            
            assert response.status_code == 403
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_rate_limits_global(self, middleware, mock_request):
        """Test global rate limit checking."""
        with patch.object(middleware, 'cache_service') as mock_cache:
            # Mock global rate limit exceeded
            mock_cache.get_rate_limit.return_value = 105  # Over limit of 100
            
            result = await middleware._check_rate_limits(mock_request, user_id=None)
            
            assert result["allowed"] is False
            assert result["limit_type"] == "global"

    @pytest.mark.asyncio
    async def test_check_rate_limits_user(self, middleware, mock_request):
        """Test user-specific rate limit checking."""
        with patch.object(middleware, 'cache_service') as mock_cache:
            mock_cache.get_rate_limit.side_effect = [
                50,   # global - under limit
                25    # user - under limit of 50
            ]
            
            result = await middleware._check_rate_limits(mock_request, user_id=456)
            
            assert result["allowed"] is True
            mock_cache.get_rate_limit.assert_any_call("192.168.1.100", "global_requests")
            mock_cache.get_rate_limit.assert_any_call("user_456", "user_requests")

    @pytest.mark.asyncio
    async def test_check_rate_limits_endpoint_specific(self, middleware, mock_request):
        """Test endpoint-specific rate limiting."""
        mock_request.url.path = "/api/v1/analyses/"
        
        with patch.object(middleware, 'cache_service') as mock_cache:
            mock_cache.get_rate_limit.side_effect = [
                50,   # global
                25,   # user  
                15    # analysis endpoint - over limit of 10
            ]
            
            result = await middleware._check_rate_limits(mock_request, user_id=456)
            
            assert result["allowed"] is False
            assert result["limit_type"] == "analysis"

    @pytest.mark.asyncio
    async def test_perform_security_screening_clean_request(self, middleware, mock_request):
        """Test security screening for clean request."""
        with patch.object(middleware, '_check_ip_reputation') as mock_ip_check, \
             patch.object(middleware, '_analyze_request_patterns') as mock_pattern_check, \
             patch.object(middleware, '_check_brute_force') as mock_brute_force:
            
            mock_ip_check.return_value = {"reputation": "good", "blocked": False}
            mock_pattern_check.return_value = {"suspicious": False, "score": 0.1}
            mock_brute_force.return_value = {"attempts": 1, "blocked": False}
            
            result = await middleware._perform_security_screening(mock_request, user_id=456)
            
            assert result["allowed"] is True
            assert result["threat_level"] == "low"

    @pytest.mark.asyncio
    async def test_perform_security_screening_suspicious_request(self, middleware, mock_request):
        """Test security screening for suspicious request."""
        with patch.object(middleware, '_check_ip_reputation') as mock_ip_check, \
             patch.object(middleware, '_analyze_request_patterns') as mock_pattern_check, \
             patch.object(middleware, '_check_brute_force') as mock_brute_force:
            
            mock_ip_check.return_value = {"reputation": "suspicious", "blocked": False}
            mock_pattern_check.return_value = {"suspicious": True, "score": 0.8}
            mock_brute_force.return_value = {"attempts": 5, "blocked": False}
            
            result = await middleware._perform_security_screening(mock_request, user_id=456)
            
            assert result["threat_level"] == "high"
            # May or may not be blocked depending on threshold

    @pytest.mark.asyncio
    async def test_check_ip_reputation_good_ip(self, middleware):
        """Test IP reputation check for good IP."""
        with patch.object(middleware, 'cache_service') as mock_cache:
            # No previous security events
            mock_cache.get.return_value = None
            
            result = await middleware._check_ip_reputation("192.168.1.100")
            
            assert result["reputation"] == "good"
            assert result["blocked"] is False

    @pytest.mark.asyncio
    async def test_check_ip_reputation_bad_ip(self, middleware):
        """Test IP reputation check for bad IP."""
        with patch.object(middleware, 'cache_service') as mock_cache:
            # IP has security violations
            mock_cache.get.return_value = {
                "violations": 15,
                "last_violation": datetime.utcnow().isoformat(),
                "blocked_until": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            result = await middleware._check_ip_reputation("192.168.1.100")
            
            assert result["reputation"] == "bad"
            assert result["blocked"] is True

    @pytest.mark.asyncio
    async def test_analyze_request_patterns_normal(self, middleware, mock_request):
        """Test request pattern analysis for normal request."""
        with patch.object(middleware, 'cache_service') as mock_cache:
            # Normal request history
            mock_cache.get.return_value = [
                {"timestamp": datetime.utcnow().isoformat(), "path": "/api/v1/auth/me"},
                {"timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(), "path": "/api/v1/analyses/"}
            ]
            
            result = await middleware._analyze_request_patterns(mock_request)
            
            assert result["suspicious"] is False
            assert result["score"] < 0.5

    @pytest.mark.asyncio
    async def test_analyze_request_patterns_suspicious(self, middleware, mock_request):
        """Test request pattern analysis for suspicious activity."""
        with patch.object(middleware, 'cache_service') as mock_cache:
            # Rapid fire requests to same endpoint
            now = datetime.utcnow()
            mock_cache.get.return_value = [
                {"timestamp": (now - timedelta(seconds=1)).isoformat(), "path": "/api/v1/analyses/"},
                {"timestamp": (now - timedelta(seconds=2)).isoformat(), "path": "/api/v1/analyses/"},
                {"timestamp": (now - timedelta(seconds=3)).isoformat(), "path": "/api/v1/analyses/"},
                {"timestamp": (now - timedelta(seconds=4)).isoformat(), "path": "/api/v1/analyses/"},
                {"timestamp": (now - timedelta(seconds=5)).isoformat(), "path": "/api/v1/analyses/"}
            ]
            
            result = await middleware._analyze_request_patterns(mock_request)
            
            assert result["suspicious"] is True
            assert result["score"] > 0.7  # High suspicion score

    @pytest.mark.asyncio
    async def test_check_brute_force_normal(self, middleware, mock_request):
        """Test brute force check for normal login attempts."""
        mock_request.url.path = "/api/v1/auth/login"
        
        with patch.object(middleware, 'cache_service') as mock_cache:
            # Few failed attempts
            mock_cache.get.return_value = 2
            
            result = await middleware._check_brute_force(mock_request)
            
            assert result["attempts"] == 2
            assert result["blocked"] is False

    @pytest.mark.asyncio
    async def test_check_brute_force_blocked(self, middleware, mock_request):
        """Test brute force protection blocking."""
        mock_request.url.path = "/api/v1/auth/login"
        
        with patch.object(middleware, 'cache_service') as mock_cache:
            # Many failed attempts
            mock_cache.get.return_value = 8  # Over limit of 5
            
            result = await middleware._check_brute_force(mock_request)
            
            assert result["attempts"] == 8
            assert result["blocked"] is True

    @pytest.mark.asyncio
    async def test_log_security_event(self, middleware, mock_request):
        """Test security event logging."""
        with patch.object(middleware, 'cache_service') as mock_cache, \
             patch.object(middleware, 'logger') as mock_logger:
            
            await middleware._log_security_event(
                mock_request,
                "rate_limit_exceeded",
                {"limit_type": "user", "current_count": 105}
            )
            
            mock_logger.warning.assert_called_once()
            mock_cache.set.assert_called_once()  # Should cache security event

    @pytest.mark.asyncio
    async def test_increment_rate_counters(self, middleware, mock_request):
        """Test rate counter incrementation."""
        with patch.object(middleware, 'cache_service') as mock_cache:
            mock_cache.increment_rate_limit.return_value = 25
            
            await middleware._increment_rate_counters(mock_request, user_id=456)
            
            # Should increment multiple counters
            assert mock_cache.increment_rate_limit.call_count >= 2
            
            # Verify calls for different rate limit types
            call_args = [call[0] for call in mock_cache.increment_rate_limit.call_args_list]
            assert any("192.168.1.100" in str(args) for args in call_args)  # IP
            assert any("user_456" in str(args) for args in call_args)       # User

    @pytest.mark.asyncio
    async def test_file_upload_security(self, middleware, mock_request):
        """Test file upload security screening."""
        # Mock file upload request
        mock_request.method = "POST"
        mock_request.headers = {
            "content-type": "multipart/form-data",
            "content-length": "1048576"  # 1MB
        }
        
        with patch.object(middleware, '_validate_file_upload') as mock_validate:
            mock_validate.return_value = {"valid": True, "file_type": "image/jpeg"}
            
            result = await middleware._perform_security_screening(mock_request, user_id=456)
            
            mock_validate.assert_called_once()

    def test_get_rate_limits_config(self, middleware):
        """Test rate limits configuration."""
        config = middleware._get_rate_limits_config()
        
        # Should have all rate limit types
        expected_types = [
            RateLimitType.GLOBAL,
            RateLimitType.USER,
            RateLimitType.IP,
            RateLimitType.ANALYSIS,
            RateLimitType.CONVERSATION
        ]
        
        for limit_type in expected_types:
            assert limit_type in config
            assert "limit" in config[limit_type]
            assert "window" in config[limit_type]

    def test_calculate_threat_level(self, middleware):
        """Test threat level calculation."""
        test_cases = [
            # (ip_reputation, pattern_score, brute_force_attempts, expected_level)
            ("good", 0.1, 1, "low"),
            ("suspicious", 0.5, 3, "medium"),
            ("bad", 0.8, 6, "high"),
            ("good", 0.9, 1, "medium"),  # High pattern score
            ("good", 0.1, 8, "high")     # Many brute force attempts
        ]
        
        for ip_rep, pattern_score, bf_attempts, expected in test_cases:
            level = middleware._calculate_threat_level({
                "ip_reputation": {"reputation": ip_rep},
                "request_patterns": {"score": pattern_score},
                "brute_force": {"attempts": bf_attempts}
            })
            
            assert level == expected

    @pytest.mark.asyncio
    async def test_error_handling(self, middleware, mock_request, mock_response):
        """Test error handling in middleware."""
        # Test cache service failure
        with patch.object(middleware, 'cache_service') as mock_cache:
            mock_cache.get_rate_limit.side_effect = Exception("Redis connection failed")
            
            call_next = AsyncMock(return_value=mock_response)
            
            # Should handle cache failure gracefully and allow request
            result = await middleware.dispatch(mock_request, call_next)
            
            assert result == mock_response
            call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_disabled_security(self):
        """Test middleware with security monitoring disabled."""
        middleware_no_security = RateLimitMiddleware(
            app=MagicMock(),
            enable_security_monitoring=False
        )
        
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.100"
        mock_response = MagicMock(spec=Response)
        
        with patch.object(middleware_no_security, 'cache_service') as mock_cache, \
             patch.object(middleware_no_security, '_check_rate_limits') as mock_check_limits:
            
            mock_check_limits.return_value = {"allowed": True}
            call_next = AsyncMock(return_value=mock_response)
            
            result = await middleware_no_security.dispatch(mock_request, call_next)
            
            assert result == mock_response
            # Security screening should be skipped


class TestSecurityService:
    """Test suite for SecurityService utility class."""

    def test_validate_file_magic_bytes(self):
        """Test file validation using magic bytes."""
        # JPEG magic bytes
        jpeg_bytes = b'\xff\xd8\xff\xe0'
        assert SecurityService.validate_file_magic_bytes(jpeg_bytes, "image/jpeg") is True
        
        # PNG magic bytes  
        png_bytes = b'\x89\x50\x4e\x47'
        assert SecurityService.validate_file_magic_bytes(png_bytes, "image/png") is True
        
        # Invalid combination
        assert SecurityService.validate_file_magic_bytes(jpeg_bytes, "image/png") is False

    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = SecurityService.generate_secure_token(32)
        token2 = SecurityService.generate_secure_token(32)
        
        assert len(token1) == 64  # hex encoding doubles length
        assert len(token2) == 64
        assert token1 != token2  # Should be unique

    def test_is_suspicious_user_agent(self):
        """Test suspicious user agent detection."""
        suspicious_agents = [
            "curl/7.64.1",
            "python-requests/2.25.1",
            "Bot",
            "Scanner"
        ]
        
        normal_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]
        
        for agent in suspicious_agents:
            assert SecurityService.is_suspicious_user_agent(agent) is True
        
        for agent in normal_agents:
            assert SecurityService.is_suspicious_user_agent(agent) is False

    def test_calculate_request_frequency(self):
        """Test request frequency calculation."""
        now = datetime.utcnow()
        timestamps = [
            now - timedelta(seconds=10),
            now - timedelta(seconds=20),
            now - timedelta(seconds=30),
            now - timedelta(seconds=60),
            now - timedelta(seconds=90)
        ]
        
        # Should count requests in last minute
        frequency = SecurityService.calculate_request_frequency(timestamps, window_seconds=60)
        assert frequency == 4  # 4 requests in last 60 seconds

    def test_is_private_ip(self):
        """Test private IP address detection."""
        private_ips = [
            "192.168.1.100",
            "10.0.0.1", 
            "172.16.0.1",
            "127.0.0.1"
        ]
        
        public_ips = [
            "8.8.8.8",
            "1.1.1.1",
            "203.0.113.1"
        ]
        
        for ip in private_ips:
            assert SecurityService.is_private_ip(ip) is True
        
        for ip in public_ips:
            assert SecurityService.is_private_ip(ip) is False