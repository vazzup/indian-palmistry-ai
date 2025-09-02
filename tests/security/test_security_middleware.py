"""
Comprehensive tests for security middleware.

Tests cover:
- Security headers middleware
- CORS security middleware
- Header injection prevention
- CSP policy validation
- CORS origin validation
- Security configuration validation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.types import Scope, Receive, Send

from app.middleware.security import SecurityHeadersMiddleware, CORSSecurityMiddleware


class TestSecurityHeadersMiddleware:
    """Test suite for SecurityHeadersMiddleware."""

    @pytest.fixture
    def middleware(self):
        """SecurityHeadersMiddleware instance for testing."""
        app_mock = AsyncMock()
        return SecurityHeadersMiddleware(app_mock)

    @pytest.fixture
    def mock_request(self):
        """Mock request for testing."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/test"
        return request

    @pytest.fixture
    def mock_response(self):
        """Mock response for testing."""
        response = Mock(spec=Response)
        response.headers = {}
        return response

    async def test_security_headers_added_to_response(self, middleware, mock_request, mock_response):
        """Test that all security headers are added to responses."""
        # Mock the call_next function
        async def mock_call_next(request):
            return mock_response

        # Dispatch the middleware
        result = await middleware.dispatch(mock_request, mock_call_next)

        # Verify all expected security headers are present
        expected_headers = {
            "Content-Security-Policy",
            "X-Content-Type-Options", 
            "X-Frame-Options",
            "Referrer-Policy",
            "Permissions-Policy",
            "X-XSS-Protection"
        }

        for header in expected_headers:
            assert header in result.headers, f"Missing security header: {header}"

    async def test_csp_policy_comprehensive(self, middleware, mock_request, mock_response):
        """Test Content Security Policy is comprehensive and secure."""
        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        csp_policy = result.headers["Content-Security-Policy"]
        
        # Verify key CSP directives
        assert "default-src 'self'" in csp_policy
        assert "object-src 'none'" in csp_policy  # Prevent Flash/plugin execution
        assert "frame-ancestors 'none'" in csp_policy  # Prevent embedding
        assert "base-uri 'self'" in csp_policy  # Prevent base tag hijacking
        assert "form-action 'self'" in csp_policy  # Restrict form submissions

        # Verify script sources are controlled
        assert "script-src" in csp_policy
        
        # Verify style sources are controlled  
        assert "style-src" in csp_policy

    async def test_x_content_type_options_nosniff(self, middleware, mock_request, mock_response):
        """Test X-Content-Type-Options is set to nosniff."""
        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result.headers["X-Content-Type-Options"] == "nosniff"

    async def test_x_frame_options_deny(self, middleware, mock_request, mock_response):
        """Test X-Frame-Options is set to DENY."""
        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result.headers["X-Frame-Options"] == "DENY"

    async def test_referrer_policy_strict(self, middleware, mock_request, mock_response):
        """Test Referrer-Policy is set to strict-origin-when-cross-origin."""
        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    async def test_permissions_policy_restrictive(self, middleware, mock_request, mock_response):
        """Test Permissions-Policy restricts dangerous features."""
        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        
        permissions_policy = result.headers["Permissions-Policy"]
        
        # Verify dangerous features are disabled
        dangerous_features = ["camera", "microphone", "location", "payment", "usb"]
        for feature in dangerous_features:
            assert f"{feature}=()" in permissions_policy

    async def test_x_xss_protection_enabled(self, middleware, mock_request, mock_response):
        """Test X-XSS-Protection is enabled with block mode."""
        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result.headers["X-XSS-Protection"] == "1; mode=block"

    async def test_headers_not_duplicated(self, middleware, mock_request):
        """Test that headers are not duplicated if already present."""
        # Create response that already has some headers
        response_with_headers = Mock(spec=Response)
        response_with_headers.headers = {"X-Frame-Options": "SAMEORIGIN"}

        async def mock_call_next(request):
            return response_with_headers

        result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Middleware should override existing security headers
        assert result.headers["X-Frame-Options"] == "DENY"

    async def test_middleware_preserves_original_response(self, middleware, mock_request):
        """Test that middleware preserves the original response object."""
        original_response = JSONResponse({"message": "test"})

        async def mock_call_next(request):
            return original_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should be the same response object with added headers
        assert result is original_response
        assert "Content-Security-Policy" in result.headers

    async def test_csp_allows_necessary_resources(self, middleware, mock_request, mock_response):
        """Test that CSP policy allows necessary resources for the application."""
        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        csp_policy = result.headers["Content-Security-Policy"]
        
        # Should allow necessary CDN resources
        assert "https://cdn.jsdelivr.net" in csp_policy
        assert "https://fonts.googleapis.com" in csp_policy
        assert "https://fonts.gstatic.com" in csp_policy
        
        # Should allow data: and blob: for images (common in modern apps)
        assert "data:" in csp_policy
        assert "blob:" in csp_policy


class TestCORSSecurityMiddleware:
    """Test suite for CORSSecurityMiddleware."""

    @pytest.fixture
    def allowed_origins(self):
        """Test allowed origins list."""
        return [
            "https://example.com",
            "https://www.example.com",
            "http://localhost:3000"
        ]

    @pytest.fixture
    def middleware(self, allowed_origins):
        """CORSSecurityMiddleware instance for testing."""
        app_mock = AsyncMock()
        return CORSSecurityMiddleware(app_mock, allowed_origins=allowed_origins)

    @pytest.fixture
    def mock_request(self):
        """Mock request for testing."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.headers = {}
        return request

    @pytest.fixture
    def mock_response(self):
        """Mock response for testing."""
        response = Mock(spec=Response)
        response.headers = {}
        response.status_code = 200
        return response

    async def test_preflight_request_allowed_origin(self, middleware, mock_request, allowed_origins):
        """Test preflight request handling for allowed origins."""
        mock_request.method = "OPTIONS"
        mock_request.headers = {"Origin": "https://example.com"}

        result = await middleware.dispatch(mock_request, lambda x: None)

        assert result.status_code == 204
        assert result.headers["Access-Control-Allow-Origin"] == "https://example.com"
        assert result.headers["Access-Control-Allow-Credentials"] == "true"
        assert "Vary" in result.headers
        assert "Origin" in result.headers["Vary"]

    async def test_preflight_request_disallowed_origin(self, middleware, mock_request):
        """Test preflight request handling for disallowed origins."""
        mock_request.method = "OPTIONS"
        mock_request.headers = {"Origin": "https://evil.com"}

        result = await middleware.dispatch(mock_request, lambda x: None)

        assert result.status_code == 204
        assert "Access-Control-Allow-Origin" not in result.headers
        assert "Vary" in result.headers

    async def test_preflight_request_no_origin(self, middleware, mock_request):
        """Test preflight request handling without Origin header."""
        mock_request.method = "OPTIONS"
        mock_request.headers = {}

        result = await middleware.dispatch(mock_request, lambda x: None)

        assert result.status_code == 204
        assert "Access-Control-Allow-Origin" not in result.headers
        assert "Vary" in result.headers

    async def test_actual_request_allowed_origin(self, middleware, mock_request, mock_response):
        """Test actual request handling for allowed origins."""
        mock_request.method = "GET"
        mock_request.headers = {"Origin": "https://example.com"}

        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result.headers["Access-Control-Allow-Origin"] == "https://example.com"
        assert result.headers["Access-Control-Allow-Credentials"] == "true"
        assert "Vary" in result.headers
        assert "Origin" in result.headers["Vary"]

    async def test_actual_request_disallowed_origin(self, middleware, mock_request, mock_response):
        """Test actual request handling for disallowed origins."""
        mock_request.method = "GET"
        mock_request.headers = {"Origin": "https://evil.com"}

        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert "Access-Control-Allow-Origin" not in result.headers
        assert "Vary" in result.headers

    async def test_actual_request_no_origin(self, middleware, mock_request, mock_response):
        """Test actual request handling without Origin header."""
        mock_request.method = "GET"
        mock_request.headers = {}

        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert "Access-Control-Allow-Origin" not in result.headers
        assert "Vary" in result.headers

    async def test_cors_headers_comprehensive(self, middleware, mock_request):
        """Test that all necessary CORS headers are set in preflight responses."""
        mock_request.method = "OPTIONS"
        mock_request.headers = {"Origin": "https://example.com"}

        result = await middleware.dispatch(mock_request, lambda x: None)

        # Verify all expected CORS headers
        expected_headers = {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-CSRF-Token, X-Requested-With, Accept, Origin",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400"
        }

        for header, expected_value in expected_headers.items():
            assert result.headers[header] == expected_value

    async def test_vary_header_preservation(self, middleware, mock_request, mock_response):
        """Test that existing Vary headers are preserved and extended."""
        mock_request.method = "GET"
        mock_request.headers = {"Origin": "https://example.com"}
        
        # Response already has a Vary header
        mock_response.headers = {"Vary": "Accept-Encoding"}

        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        # Should preserve existing and add Origin
        assert "Accept-Encoding" in result.headers["Vary"]
        assert "Origin" in result.headers["Vary"]

    async def test_case_insensitive_origin_matching(self, middleware, mock_request, mock_response):
        """Test that origin matching is case-sensitive (as per spec)."""
        mock_request.method = "GET"
        mock_request.headers = {"Origin": "HTTPS://EXAMPLE.COM"}  # Different case

        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)

        # Should not match (origins are case-sensitive)
        assert "Access-Control-Allow-Origin" not in result.headers

    async def test_default_allowed_origins(self):
        """Test middleware with default allowed origins."""
        app_mock = AsyncMock()
        middleware = CORSSecurityMiddleware(app_mock)
        
        # Should have localhost origins for development
        assert any("localhost" in origin for origin in middleware.allowed_origins)

    async def test_cors_max_age_security(self, middleware, mock_request):
        """Test that CORS max-age is set appropriately for security."""
        mock_request.method = "OPTIONS"
        mock_request.headers = {"Origin": "https://example.com"}

        result = await middleware.dispatch(mock_request, lambda x: None)

        # Max-age should be reasonable (24 hours = 86400 seconds)
        max_age = int(result.headers["Access-Control-Max-Age"])
        assert 0 < max_age <= 86400  # Between 0 and 24 hours

    async def test_cors_allowed_methods_restrictive(self, middleware, mock_request):
        """Test that CORS allowed methods are appropriately restrictive."""
        mock_request.method = "OPTIONS"
        mock_request.headers = {"Origin": "https://example.com"}

        result = await middleware.dispatch(mock_request, lambda x: None)

        allowed_methods = result.headers["Access-Control-Allow-Methods"]
        
        # Should include necessary methods but not dangerous ones
        assert "GET" in allowed_methods
        assert "POST" in allowed_methods
        assert "PUT" in allowed_methods
        assert "DELETE" in allowed_methods
        assert "OPTIONS" in allowed_methods
        
        # Should not include dangerous methods
        assert "TRACE" not in allowed_methods
        assert "CONNECT" not in allowed_methods

    async def test_cors_allowed_headers_secure(self, middleware, mock_request):
        """Test that CORS allowed headers include security headers."""
        mock_request.method = "OPTIONS"
        mock_request.headers = {"Origin": "https://example.com"}

        result = await middleware.dispatch(mock_request, lambda x: None)

        allowed_headers = result.headers["Access-Control-Allow-Headers"]
        
        # Should include security-related headers
        assert "X-CSRF-Token" in allowed_headers
        assert "Authorization" in allowed_headers
        assert "Content-Type" in allowed_headers


class TestSecurityMiddlewareIntegration:
    """Integration tests for security middleware."""

    @pytest.fixture
    def app_with_middleware(self):
        """FastAPI app with security middleware for testing."""
        from fastapi import FastAPI
        from app.middleware.security import SecurityHeadersMiddleware, CORSSecurityMiddleware
        
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(CORSSecurityMiddleware, allowed_origins=["http://localhost:3000"])
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app

    def test_middleware_order_and_interaction(self, app_with_middleware):
        """Test that multiple security middleware work together correctly."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app_with_middleware)
        
        # Make request with allowed origin
        response = client.get("/test", headers={"Origin": "http://localhost:3000"})
        
        # Should have both security headers and CORS headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"

    def test_preflight_with_security_headers(self, app_with_middleware):
        """Test that preflight requests also get security headers."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app_with_middleware)
        
        # Make preflight request
        response = client.options("/test", headers={"Origin": "http://localhost:3000"})
        
        # Should have both CORS and security headers
        assert response.status_code == 204
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Content-Security-Policy" in response.headers


class TestSecurityMiddlewareErrorHandling:
    """Test error handling in security middleware."""

    async def test_middleware_exception_handling(self):
        """Test middleware behavior when downstream raises exception."""
        app_mock = AsyncMock()
        middleware = SecurityHeadersMiddleware(app_mock)
        
        async def failing_call_next(request):
            raise Exception("Downstream error")
        
        # Should propagate exception but not interfere
        with pytest.raises(Exception, match="Downstream error"):
            await middleware.dispatch(Mock(), failing_call_next)

    async def test_cors_middleware_exception_handling(self):
        """Test CORS middleware behavior when downstream raises exception."""
        app_mock = AsyncMock()
        middleware = CORSSecurityMiddleware(app_mock)
        
        async def failing_call_next(request):
            raise Exception("Downstream error")
        
        # Should propagate exception but still add Vary header for non-OPTIONS
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.headers = {}
        
        with pytest.raises(Exception, match="Downstream error"):
            await middleware.dispatch(mock_request, failing_call_next)


class TestSecurityHeadersValidation:
    """Tests for security header validation and configuration."""

    def test_csp_policy_syntax_validation(self):
        """Test that CSP policy syntax is valid."""
        app_mock = AsyncMock()
        middleware = SecurityHeadersMiddleware(app_mock)
        
        csp_policy = middleware.csp_policy
        
        # Basic syntax validation
        assert csp_policy.count(';') > 5  # Multiple directives
        assert 'default-src' in csp_policy
        assert "'self'" in csp_policy
        assert "'none'" in csp_policy

    def test_security_headers_values_validation(self):
        """Test that security header values are valid."""
        app_mock = AsyncMock()
        middleware = SecurityHeadersMiddleware(app_mock)
        
        headers = middleware.security_headers
        
        # Validate header values
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]  # Both are valid
        assert "strict-origin" in headers["Referrer-Policy"]
        assert "1; mode=block" == headers["X-XSS-Protection"]

    def test_cors_configuration_validation(self):
        """Test that CORS configuration is secure."""
        app_mock = AsyncMock()
        
        # Test with secure origins
        secure_origins = ["https://example.com", "https://api.example.com"]
        middleware = CORSSecurityMiddleware(app_mock, allowed_origins=secure_origins)
        
        assert middleware.allowed_origins == secure_origins
        
        # Verify no wildcard origins
        for origin in middleware.allowed_origins:
            assert "*" not in origin
            assert origin.startswith(("http://", "https://"))


class TestSecurityMiddlewarePerformance:
    """Performance tests for security middleware."""

    async def test_security_headers_performance(self):
        """Test that security headers middleware has minimal performance impact."""
        import time
        
        app_mock = AsyncMock()
        middleware = SecurityHeadersMiddleware(app_mock)
        
        mock_request = Mock()
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Measure middleware overhead
        start_time = time.time()
        for _ in range(1000):
            await middleware.dispatch(mock_request, mock_call_next)
        end_time = time.time()
        
        # Should complete quickly (under 100ms for 1000 iterations)
        assert (end_time - start_time) < 0.1

    async def test_cors_middleware_performance(self):
        """Test that CORS middleware has minimal performance impact."""
        import time
        
        app_mock = AsyncMock()
        middleware = CORSSecurityMiddleware(app_mock)
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.headers = {"Origin": "https://example.com"}
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Measure middleware overhead
        start_time = time.time()
        for _ in range(1000):
            await middleware.dispatch(mock_request, mock_call_next)
        end_time = time.time()
        
        # Should complete quickly (under 100ms for 1000 iterations)
        assert (end_time - start_time) < 0.1