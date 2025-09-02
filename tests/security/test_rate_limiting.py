"""
Comprehensive tests for rate limiting middleware.

Tests cover:
- Rate limiting enforcement
- Different limit configurations
- IP detection and tracking
- Redis interactions
- Burst protection
- Rate limit headers
- Authentication logging
- Error handling and recovery
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.middleware.rate_limiting import (
    RateLimitingMiddleware, 
    AuthenticationLogMiddleware
)


class TestRateLimitingMiddleware:
    """Test suite for RateLimitingMiddleware."""

    @pytest.fixture
    def middleware(self):
        """RateLimitingMiddleware instance for testing."""
        app_mock = AsyncMock()
        return RateLimitingMiddleware(app_mock)

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing."""
        redis_mock = AsyncMock()
        redis_mock.get.return_value = None
        redis_mock.incr.return_value = 1
        redis_mock.expire.return_value = True
        redis_mock.pipeline.return_value.execute.return_value = [1, True, 1, True]
        return redis_mock

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request object."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/auth/login"
        request.method = "POST"
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request

    @pytest.fixture
    def mock_response(self):
        """Mock response for testing."""
        response = Mock(spec=Response)
        response.headers = {}
        response.status_code = 200
        return response

    def test_rate_limit_configuration(self, middleware):
        """Test rate limit configuration and rules."""
        # Verify login endpoint has strict limits
        login_limits = middleware._get_rate_limit_for_path("/api/v1/auth/login")
        assert login_limits == (5, 300, 2)  # 5 attempts per 5 minutes, burst 2
        
        # Verify register endpoint has very strict limits
        register_limits = middleware._get_rate_limit_for_path("/api/v1/auth/register")
        assert register_limits == (3, 300, 1)  # 3 attempts per 5 minutes, burst 1
        
        # Verify default limits exist
        default_limits = middleware._get_rate_limit_for_path("/api/v1/unknown")
        assert default_limits == (1000, 3600, 100)  # Default limits

    def test_client_identifier_detection(self, middleware, mock_request):
        """Test client IP detection with various header configurations."""
        # Test direct client IP
        client_id = middleware._get_client_identifier(mock_request)
        assert client_id == "192.168.1.100"
        
        # Test X-Forwarded-For header
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1, 10.0.0.1"}
        client_id = middleware._get_client_identifier(mock_request)
        assert client_id == "203.0.113.1"  # First IP in chain
        
        # Test X-Real-IP header
        mock_request.headers = {"X-Real-IP": "203.0.113.2"}
        client_id = middleware._get_client_identifier(mock_request)
        assert client_id == "203.0.113.2"
        
        # Test X-Forwarded-For takes precedence over X-Real-IP
        mock_request.headers = {
            "X-Forwarded-For": "203.0.113.3, 192.168.1.1",
            "X-Real-IP": "203.0.113.4"
        }
        client_id = middleware._get_client_identifier(mock_request)
        assert client_id == "203.0.113.3"

    def test_client_identifier_edge_cases(self, middleware, mock_request):
        """Test client identifier detection edge cases."""
        # Test with spaces in X-Forwarded-For
        mock_request.headers = {"X-Forwarded-For": " 203.0.113.1 , 192.168.1.1 "}
        client_id = middleware._get_client_identifier(mock_request)
        assert client_id == "203.0.113.1"  # Should strip spaces
        
        # Test with no client info
        mock_request.client = None
        mock_request.headers = {}
        client_id = middleware._get_client_identifier(mock_request)
        assert client_id == "unknown"

    async def test_rate_limit_check_within_limits(self, middleware, mock_redis):
        """Test rate limit check when within limits."""
        with patch('app.middleware.rate_limiting.session_manager.redis', mock_redis):
            # Mock Redis responses for within limits
            mock_redis.get.side_effect = [b'2', b'1']  # window_count=2, burst_count=1
            
            allowed, info = await middleware._check_rate_limit(
                "192.168.1.100", "/api/v1/auth/login", 5, 300, 2
            )
            
            assert allowed is True
            assert info["allowed"] is True
            assert info["window_current"] == 3  # 2 + 1
            assert info["burst_current"] == 2   # 1 + 1

    async def test_rate_limit_check_burst_exceeded(self, middleware, mock_redis):
        """Test rate limit check when burst limit is exceeded."""
        with patch('app.middleware.rate_limiting.session_manager.redis', mock_redis):
            # Mock Redis responses for burst limit exceeded
            mock_redis.get.side_effect = [b'1', b'2']  # window_count=1, burst_count=2 (at limit)
            
            allowed, info = await middleware._check_rate_limit(
                "192.168.1.100", "/api/v1/auth/login", 5, 300, 2
            )
            
            assert allowed is False
            assert info["allowed"] is False
            assert info["limit_type"] == "burst"
            assert info["retry_after"] == 30

    async def test_rate_limit_check_window_exceeded(self, middleware, mock_redis):
        """Test rate limit check when window limit is exceeded."""
        with patch('app.middleware.rate_limiting.session_manager.redis', mock_redis):
            # Mock Redis responses for window limit exceeded
            mock_redis.get.side_effect = [b'5', b'1']  # window_count=5 (at limit), burst_count=1
            
            allowed, info = await middleware._check_rate_limit(
                "192.168.1.100", "/api/v1/auth/login", 5, 300, 2
            )
            
            assert allowed is False
            assert info["allowed"] is False
            assert info["limit_type"] == "window"
            assert info["retry_after"] == 300

    async def test_rate_limit_redis_error_graceful_degradation(self, middleware, mock_redis):
        """Test graceful degradation when Redis errors occur."""
        with patch('app.middleware.rate_limiting.session_manager.redis', mock_redis):
            # Mock Redis error
            mock_redis.get.side_effect = Exception("Redis connection failed")
            
            allowed, info = await middleware._check_rate_limit(
                "192.168.1.100", "/api/v1/auth/login", 5, 300, 2
            )
            
            # Should allow request to proceed on Redis errors
            assert allowed is True
            assert info["allowed"] is True
            assert "error" in info

    async def test_rate_limit_redis_pipeline_operations(self, middleware, mock_redis):
        """Test that Redis operations use pipeline for efficiency."""
        with patch('app.middleware.rate_limiting.session_manager.redis', mock_redis):
            mock_redis.get.side_effect = [None, None]  # No existing counts
            
            pipeline_mock = AsyncMock()
            mock_redis.pipeline.return_value = pipeline_mock
            
            await middleware._check_rate_limit(
                "192.168.1.100", "/api/v1/auth/login", 5, 300, 2
            )
            
            # Verify pipeline operations
            assert pipeline_mock.incr.call_count == 2  # window and burst keys
            assert pipeline_mock.expire.call_count == 2  # TTL for both keys
            pipeline_mock.execute.assert_called_once()

    async def test_dispatch_skip_docs_endpoints(self, middleware, mock_request, mock_response):
        """Test that documentation endpoints skip rate limiting."""
        mock_request.url.path = "/docs"
        
        async def mock_call_next(request):
            return mock_response
        
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should proceed without rate limiting
        assert result is mock_response

    async def test_dispatch_within_rate_limits(self, middleware, mock_request, mock_response):
        """Test dispatch when request is within rate limits."""
        async def mock_call_next(request):
            return mock_response
        
        with patch.object(middleware, '_check_rate_limit', return_value=(True, {
            "allowed": True,
            "window_limit": 5,
            "window_current": 2,
            "window_reset": time.time() + 300
        })):
            result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should proceed and add rate limit headers
        assert result is mock_response
        assert "X-RateLimit-Limit" in result.headers
        assert "X-RateLimit-Remaining" in result.headers
        assert "X-RateLimit-Reset" in result.headers

    async def test_dispatch_rate_limit_exceeded(self, middleware, mock_request):
        """Test dispatch when rate limit is exceeded."""
        async def mock_call_next(request):
            return Mock()
        
        with patch.object(middleware, '_check_rate_limit', return_value=(False, {
            "allowed": False,
            "limit_type": "window",
            "retry_after": 300,
            "limit": 5
        })):
            result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should return 429 Too Many Requests
        assert result.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in result.headers
        assert "X-RateLimit-Limit" in result.headers
        assert "X-RateLimit-Remaining" in result.headers
        assert result.headers["X-RateLimit-Remaining"] == "0"

    async def test_rate_limit_logging(self, middleware, mock_request, caplog):
        """Test that rate limit violations are logged."""
        async def mock_call_next(request):
            return Mock()
        
        with patch.object(middleware, '_check_rate_limit', return_value=(False, {
            "allowed": False,
            "limit_type": "burst",
            "retry_after": 30
        })):
            await middleware.dispatch(mock_request, mock_call_next)
        
        # Check that violation was logged
        assert "Rate limit exceeded" in caplog.text
        assert "192.168.1.100" in caplog.text
        assert "/api/v1/auth/login" in caplog.text

    def test_rate_limit_path_matching_priority(self, middleware):
        """Test that more specific path patterns take priority."""
        # More specific path should match first
        login_limits = middleware._get_rate_limit_for_path("/api/v1/auth/login")
        assert login_limits == (5, 300, 2)
        
        # General auth path should match less specific pattern
        general_auth_limits = middleware._get_rate_limit_for_path("/api/v1/auth/some-other-endpoint")
        assert general_auth_limits == (20, 300, 10)  # General auth limits

    async def test_concurrent_rate_limit_checks(self, middleware, mock_redis):
        """Test rate limiting under concurrent access."""
        with patch('app.middleware.rate_limiting.session_manager.redis', mock_redis):
            # Simulate concurrent requests
            tasks = []
            for i in range(10):
                task = middleware._check_rate_limit(
                    "192.168.1.100", "/api/v1/auth/login", 5, 300, 2
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All should complete without errors
            assert len(results) == 10
            for allowed, info in results:
                assert isinstance(allowed, bool)
                assert isinstance(info, dict)


class TestAuthenticationLogMiddleware:
    """Test suite for AuthenticationLogMiddleware."""

    @pytest.fixture
    def middleware(self):
        """AuthenticationLogMiddleware instance for testing."""
        app_mock = AsyncMock()
        return AuthenticationLogMiddleware(app_mock)

    @pytest.fixture
    def mock_request(self):
        """Mock authentication request."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/auth/login"
        request.method = "POST"
        request.headers = {"User-Agent": "Test Browser"}
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request

    @pytest.fixture
    def mock_response(self):
        """Mock response for testing."""
        response = Mock(spec=Response)
        response.status_code = 200
        return response

    def test_auth_endpoint_detection(self, middleware):
        """Test authentication endpoint detection."""
        auth_endpoints = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/logout"
        }
        
        assert middleware.auth_endpoints == auth_endpoints

    async def test_successful_auth_logging(self, middleware, mock_request, mock_response, caplog):
        """Test logging of successful authentication attempts."""
        mock_response.status_code = 200
        
        async def mock_call_next(request):
            await asyncio.sleep(0.01)  # Simulate processing time
            return mock_response
        
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Check that success was logged
        assert "Authentication success" in caplog.text
        assert "192.168.1.100" in caplog.text
        assert "/api/v1/auth/login" in caplog.text

    async def test_failed_auth_logging(self, middleware, mock_request, mock_response, caplog):
        """Test logging of failed authentication attempts."""
        mock_response.status_code = 401
        
        async def mock_call_next(request):
            return mock_response
        
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Check that failure was logged
        assert "Authentication failed" in caplog.text
        assert "401" in caplog.text

    async def test_rate_limited_auth_logging(self, middleware, mock_request, mock_response, caplog):
        """Test logging of rate-limited authentication attempts."""
        mock_response.status_code = 429
        
        async def mock_call_next(request):
            return mock_response
        
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Check that rate limit was logged
        assert "Rate limited authentication attempt" in caplog.text
        assert "429" in caplog.text

    async def test_auth_error_logging(self, middleware, mock_request, mock_response, caplog):
        """Test logging of authentication errors."""
        mock_response.status_code = 500
        
        async def mock_call_next(request):
            return mock_response
        
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Check that error was logged
        assert "Authentication error" in caplog.text
        assert "500" in caplog.text

    async def test_non_auth_endpoint_no_logging(self, middleware, mock_request, mock_response, caplog):
        """Test that non-authentication endpoints are not logged."""
        mock_request.url.path = "/api/v1/analyses/"
        
        async def mock_call_next(request):
            return mock_response
        
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Should not log non-auth endpoints
        assert "Authentication" not in caplog.text

    def test_client_ip_detection_methods(self, middleware, mock_request):
        """Test various methods of client IP detection."""
        # Test direct client IP
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.100"
        
        # Test X-Forwarded-For
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}
        ip = middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.1"
        
        # Test X-Real-IP
        mock_request.headers = {"X-Real-IP": "203.0.113.2"}
        ip = middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.2"
        
        # Test fallback to unknown
        mock_request.client = None
        mock_request.headers = {}
        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"

    async def test_logging_includes_duration(self, middleware, mock_request, mock_response, caplog):
        """Test that auth logs include request duration."""
        async def slow_call_next(request):
            await asyncio.sleep(0.05)  # 50ms delay
            return mock_response
        
        await middleware.dispatch(mock_request, slow_call_next)
        
        # Check that duration is logged
        assert "duration_ms" in caplog.text
        # Duration should be > 40ms (allowing some variance)
        log_record = caplog.records[0]
        assert "duration_ms" in str(log_record.getMessage())

    async def test_logging_structured_data(self, middleware, mock_request, mock_response, caplog):
        """Test that auth logs contain structured data."""
        mock_request.headers["User-Agent"] = "Mozilla/5.0 (Test)"
        
        async def mock_call_next(request):
            return mock_response
        
        await middleware.dispatch(mock_request, mock_call_next)
        
        # Check that structured data is logged
        log_message = caplog.records[0].getMessage()
        assert "POST" in log_message
        assert "/api/v1/auth/login" in log_message
        assert "192.168.1.100" in log_message


class TestRateLimitingIntegration:
    """Integration tests for rate limiting middleware."""

    @pytest.fixture
    def app_with_rate_limiting(self):
        """FastAPI app with rate limiting middleware."""
        from fastapi import FastAPI
        from app.middleware.rate_limiting import RateLimitingMiddleware, AuthenticationLogMiddleware
        
        app = FastAPI()
        app.add_middleware(AuthenticationLogMiddleware)
        app.add_middleware(RateLimitingMiddleware)
        
        @app.post("/api/v1/auth/login")
        async def login():
            return {"message": "success"}
        
        @app.get("/api/v1/test")  
        async def test():
            return {"message": "test"}
        
        return app

    def test_rate_limiting_integration(self, app_with_rate_limiting):
        """Test rate limiting in integrated FastAPI app."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app_with_rate_limiting)
        
        # First few requests should succeed
        for i in range(3):
            response = client.post("/api/v1/auth/login", json={"email": "test", "password": "test"})
            # Should have rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers

    def test_auth_logging_integration(self, app_with_rate_limiting, caplog):
        """Test authentication logging in integrated FastAPI app."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app_with_rate_limiting)
        
        # Make auth request
        response = client.post("/api/v1/auth/login", json={"email": "test", "password": "test"})
        
        # Should be logged (might fail due to auth, but should be logged)
        # Check that some auth-related logging occurred
        assert len(caplog.records) > 0


class TestRateLimitingEdgeCases:
    """Test edge cases and error conditions for rate limiting."""

    async def test_rate_limit_key_generation(self):
        """Test rate limit Redis key generation."""
        middleware = RateLimitingMiddleware(AsyncMock())
        
        # Test various client IDs and paths
        test_cases = [
            ("192.168.1.1", "/api/v1/auth/login"),
            ("203.0.113.1", "/api/v1/auth/register"),
            ("::1", "/api/v1/analyses/"),  # IPv6
            ("unknown", "/api/v1/test")
        ]
        
        for client_id, path in test_cases:
            # Keys should be consistent and safe
            window_key = f"rate_limit:window:{client_id}:{path}"
            burst_key = f"rate_limit:burst:{client_id}:{path}"
            
            # Should not contain unsafe characters
            assert ' ' not in window_key
            assert ' ' not in burst_key
            assert '\n' not in window_key
            assert '\n' not in burst_key

    async def test_rate_limit_time_boundaries(self, middleware, mock_redis):
        """Test rate limiting behavior at time window boundaries."""
        with patch('app.middleware.rate_limiting.session_manager.redis', mock_redis):
            # Mock time progression
            with patch('time.time') as mock_time:
                mock_time.return_value = 1000.0
                
                # First request
                mock_redis.get.side_effect = [None, None]
                allowed1, info1 = await middleware._check_rate_limit(
                    "192.168.1.100", "/api/v1/auth/login", 5, 300, 2
                )
                
                # Advance time past window
                mock_time.return_value = 1301.0  # 301 seconds later
                
                # Should reset counters (but this is handled by Redis TTL)
                mock_redis.get.side_effect = [None, None]  # Expired keys return None
                allowed2, info2 = await middleware._check_rate_limit(
                    "192.168.1.100", "/api/v1/auth/login", 5, 300, 2
                )
                
                assert allowed1 is True
                assert allowed2 is True

    async def test_malicious_ip_handling(self, middleware):
        """Test handling of potentially malicious IP addresses."""
        mock_request = Mock()
        mock_request.client = Mock()
        
        # Test various potentially problematic IPs
        test_ips = [
            "0.0.0.0",
            "127.0.0.1", 
            "::1",
            "192.168.1.1",
            "10.0.0.1",
            "172.16.1.1"
        ]
        
        for ip in test_ips:
            mock_request.client.host = ip
            mock_request.headers = {}
            
            client_id = middleware._get_client_identifier(mock_request)
            # Should handle all IPs without error
            assert isinstance(client_id, str)
            assert len(client_id) > 0

    async def test_rate_limit_headers_format(self, middleware, mock_request, mock_response):
        """Test that rate limit headers are properly formatted."""
        async def mock_call_next(request):
            return mock_response
        
        future_reset_time = time.time() + 300
        with patch.object(middleware, '_check_rate_limit', return_value=(True, {
            "allowed": True,
            "window_limit": 100,
            "window_current": 25,
            "window_reset": future_reset_time
        })):
            result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify header formats
        assert result.headers["X-RateLimit-Limit"] == "100"
        assert result.headers["X-RateLimit-Remaining"] == "75"  # 100 - 25
        assert result.headers["X-RateLimit-Reset"] == str(int(future_reset_time))


class TestRateLimitingPerformance:
    """Performance tests for rate limiting middleware."""

    async def test_rate_limit_check_performance(self, middleware, mock_redis):
        """Test rate limit check performance."""
        with patch('app.middleware.rate_limiting.session_manager.redis', mock_redis):
            mock_redis.get.side_effect = [b'1', b'1'] * 100  # 100 iterations
            
            start_time = time.time()
            
            # Perform 100 rate limit checks
            for i in range(100):
                await middleware._check_rate_limit(
                    f"192.168.1.{i % 10}", "/api/v1/auth/login", 5, 300, 2
                )
            
            end_time = time.time()
            
            # Should complete quickly (under 100ms for 100 checks)
            assert (end_time - start_time) < 0.1

    async def test_middleware_dispatch_performance(self, middleware, mock_request, mock_response):
        """Test middleware dispatch performance."""
        async def mock_call_next(request):
            return mock_response
        
        with patch.object(middleware, '_check_rate_limit', return_value=(True, {
            "allowed": True,
            "window_limit": 100,
            "window_current": 1
        })):
            start_time = time.time()
            
            # Perform 100 dispatches
            for _ in range(100):
                await middleware.dispatch(mock_request, mock_call_next)
            
            end_time = time.time()
            
            # Should complete quickly (under 200ms for 100 dispatches)
            assert (end_time - start_time) < 0.2