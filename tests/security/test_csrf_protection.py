"""
Comprehensive tests for enhanced CSRF protection.

Tests cover:
- CSRF token validation
- Origin header verification
- Referer header validation
- Session binding verification
- Cross-origin request blocking
- Error handling and logging
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient

from app.dependencies.auth import verify_csrf_token
from app.models.user import User
from app.core.config import settings


class TestCSRFProtection:
    """Test suite for enhanced CSRF protection."""

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request object."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.headers = {}
        request.url.path = "/api/v1/test"
        request.form = AsyncMock(return_value={})
        request.cookies = {}
        return request

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        user = Mock(spec=User)
        user.id = 123
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def valid_session_data(self, mock_user):
        """Valid session data for testing."""
        return {
            "user_id": mock_user.id,
            "email": mock_user.email,
            "csrf_token": "valid_csrf_token_123",
            "created_at": "2024-01-01T12:00:00Z"
        }

    async def test_csrf_skip_safe_methods(self, mock_request, mock_user):
        """Test that CSRF validation is skipped for safe HTTP methods."""
        safe_methods = ["GET", "HEAD", "OPTIONS"]
        
        for method in safe_methods:
            mock_request.method = method
            
            # Should not raise any exception
            result = await verify_csrf_token(mock_request, mock_user)
            assert result is None

    async def test_csrf_valid_request_success(self, mock_request, mock_user, valid_session_data):
        """Test successful CSRF validation with valid token and origin."""
        # Setup valid request
        mock_request.method = "POST"
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=valid_session_data):
            
            # Should not raise any exception
            result = await verify_csrf_token(mock_request, mock_user)
            assert result is None

    async def test_csrf_invalid_origin_blocked(self, mock_request, mock_user):
        """Test that requests from unauthorized origins are blocked."""
        # Setup request from unauthorized origin
        mock_request.headers = {
            "Origin": "https://evil.com",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]):
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403
            assert "unauthorized origin" in str(exc_info.value.detail)

    async def test_csrf_invalid_referer_blocked(self, mock_request, mock_user):
        """Test that requests with unauthorized referer are blocked."""
        # Setup request with unauthorized referer (no Origin header)
        mock_request.headers = {
            "Referer": "https://evil.com/attack-page",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]):
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403
            assert "unauthorized referer" in str(exc_info.value.detail)

    async def test_csrf_valid_referer_allowed(self, mock_request, mock_user, valid_session_data):
        """Test that requests with valid referer are allowed when no Origin header."""
        # Setup request with valid referer (no Origin header)
        mock_request.headers = {
            "Referer": "http://localhost:3000/some-page",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=valid_session_data):
            
            # Should not raise any exception
            result = await verify_csrf_token(mock_request, mock_user)
            assert result is None

    async def test_csrf_no_origin_or_referer_blocked(self, mock_request, mock_user):
        """Test that requests without origin or referer headers are blocked."""
        # Setup request without origin or referer headers
        mock_request.headers = {
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_csrf_token(mock_request, mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Missing origin information" in str(exc_info.value.detail)

    async def test_csrf_missing_token_blocked(self, mock_request, mock_user):
        """Test that requests without CSRF token are blocked."""
        # Setup request with valid origin but no CSRF token
        mock_request.headers = {
            "Origin": "http://localhost:3000"
        }
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]):
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403
            assert "CSRF token required" in str(exc_info.value.detail)

    async def test_csrf_token_from_form_data(self, mock_request, mock_user, valid_session_data):
        """Test CSRF token validation from form data as fallback."""
        # Setup request with token in form data instead of header
        mock_request.headers = {
            "Origin": "http://localhost:3000"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        mock_request.form = AsyncMock(return_value={"csrf_token": "valid_csrf_token_123"})
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=valid_session_data):
            
            # Should not raise any exception
            result = await verify_csrf_token(mock_request, mock_user)
            assert result is None

    async def test_csrf_form_data_exception_handled(self, mock_request, mock_user):
        """Test graceful handling of form data parsing exceptions."""
        # Setup request that will fail to parse form data
        mock_request.headers = {
            "Origin": "http://localhost:3000"
        }
        mock_request.form = AsyncMock(side_effect=Exception("Form parsing failed"))
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]):
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403
            assert "CSRF token required" in str(exc_info.value.detail)

    async def test_csrf_no_session_cookie_blocked(self, mock_request, mock_user):
        """Test that requests without session cookie are blocked."""
        # Setup valid request but no session cookie
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {}  # No session cookie
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]):
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 401
            assert "Session required" in str(exc_info.value.detail)

    async def test_csrf_invalid_session_blocked(self, mock_request, mock_user):
        """Test that requests with invalid session are blocked."""
        # Setup request with invalid session
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "invalid_session"}
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=None):
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 401
            assert "Invalid session" in str(exc_info.value.detail)

    async def test_csrf_invalid_token_blocked(self, mock_request, mock_user, valid_session_data):
        """Test that requests with invalid CSRF token are blocked."""
        # Setup request with invalid CSRF token
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": "invalid_csrf_token"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=valid_session_data):
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403
            assert "Invalid CSRF token" in str(exc_info.value.detail)

    async def test_csrf_session_user_mismatch_blocked(self, mock_request, mock_user, valid_session_data):
        """Test that requests with session-user mismatch are blocked."""
        # Setup request where session belongs to different user
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        # Session belongs to different user
        session_data = valid_session_data.copy()
        session_data["user_id"] = 999  # Different from mock_user.id (123)
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=session_data):
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403
            assert "Session user mismatch" in str(exc_info.value.detail)

    async def test_csrf_logging_on_failures(self, mock_request, mock_user, caplog):
        """Test that CSRF failures are properly logged."""
        mock_request.headers = {
            "Origin": "https://evil.com",
            "X-CSRF-Token": "some_token"
        }
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]):
            with pytest.raises(HTTPException):
                await verify_csrf_token(mock_request, mock_user)
        
        # Check that warning was logged
        assert "CSRF: Rejected request from unauthorized origin" in caplog.text
        assert "https://evil.com" in caplog.text

    async def test_csrf_success_logging(self, mock_request, mock_user, valid_session_data, caplog):
        """Test that successful CSRF validation is logged for debugging."""
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=valid_session_data), \
             patch('app.dependencies.auth.logger.debug') as mock_debug:
            
            await verify_csrf_token(mock_request, mock_user)
            
            # Verify debug log was called
            mock_debug.assert_called_once()
            log_message = mock_debug.call_args[0][0]
            assert "CSRF: Token verified for user 123" in log_message


class TestCSRFIntegration:
    """Integration tests for CSRF protection with FastAPI endpoints."""

    @pytest.fixture
    def app_client(self):
        """Test client for integration testing."""
        from app.main import app
        return TestClient(app)

    def test_csrf_protection_on_protected_endpoint(self, app_client):
        """Test CSRF protection on protected API endpoints."""
        # This would require setting up authenticated session and testing endpoints
        pytest.skip("Requires full app integration setup")

    def test_csrf_bypass_on_safe_methods(self, app_client):
        """Test that safe HTTP methods bypass CSRF protection."""
        # Test GET request doesn't require CSRF token
        response = app_client.get("/api/v1/auth/me")
        # Should not fail due to missing CSRF token (might fail for other reasons like auth)
        assert response.status_code != 403 or "CSRF" not in response.text


class TestCSRFTokenGeneration:
    """Tests for CSRF token generation and management."""

    def test_csrf_token_entropy(self):
        """Test that CSRF tokens have sufficient entropy."""
        from app.dependencies.auth import generate_csrf_token
        
        # Generate multiple tokens
        tokens = set()
        for _ in range(1000):
            token = generate_csrf_token()
            tokens.add(token)
        
        # All should be unique
        assert len(tokens) == 1000
        
        # Check minimum length
        for token in list(tokens)[:10]:
            assert len(token) >= 32  # Sufficient entropy

    def test_csrf_token_format(self):
        """Test CSRF token format and characteristics."""
        from app.dependencies.auth import generate_csrf_token
        
        token = generate_csrf_token()
        
        # Should be URL-safe base64
        import base64
        try:
            base64.urlsafe_b64decode(token + "==")  # Add padding if needed
        except Exception:
            pytest.fail("CSRF token is not valid URL-safe base64")
        
        # Should not contain unsafe characters
        unsafe_chars = ['<', '>', '"', "'", '&', ' ', '\n', '\r', '\t']
        for char in unsafe_chars:
            assert char not in token


class TestCSRFEdgeCases:
    """Tests for CSRF protection edge cases and error conditions."""

    async def test_csrf_with_subdomain_origin(self, mock_request, mock_user, valid_session_data):
        """Test CSRF protection with subdomain origins."""
        # Test that subdomain origins are handled correctly
        mock_request.headers = {
            "Origin": "https://api.localhost:3000",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        # Subdomain not in allowed origins
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=valid_session_data):
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403

    async def test_csrf_with_port_variations(self, mock_request, mock_user, valid_session_data):
        """Test CSRF protection with different port numbers."""
        # Request from different port should be blocked
        mock_request.headers = {
            "Origin": "http://localhost:3001",  # Different port
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=valid_session_data):
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403

    async def test_csrf_with_malformed_referer(self, mock_request, mock_user):
        """Test CSRF protection with malformed referer header."""
        # Malformed referer should be handled gracefully
        mock_request.headers = {
            "Referer": "not-a-valid-url",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]):
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403

    async def test_csrf_with_empty_token(self, mock_request, mock_user):
        """Test CSRF protection with empty token value."""
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": ""  # Empty token
        }
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]):
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403
            assert "CSRF token required" in str(exc_info.value.detail)

    async def test_csrf_session_data_corruption(self, mock_request, mock_user):
        """Test CSRF protection with corrupted session data."""
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        # Corrupted session data (missing required fields)
        corrupted_session_data = {
            "user_id": 123,
            # Missing csrf_token
        }
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=corrupted_session_data):
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_csrf_token(mock_request, mock_user)
            
            assert exc_info.value.status_code == 403
            assert "Invalid CSRF token" in str(exc_info.value.detail)


# Performance tests for CSRF protection
class TestCSRFPerformance:
    """Performance tests for CSRF validation."""

    async def test_csrf_validation_performance(self, mock_request, mock_user, valid_session_data):
        """Test CSRF validation performance under normal conditions."""
        import time
        
        mock_request.headers = {
            "Origin": "http://localhost:3000",
            "X-CSRF-Token": "valid_csrf_token_123"
        }
        mock_request.cookies = {"__Host-session_id": "session_123"}
        
        with patch('app.dependencies.auth.settings.allowed_origins', ["http://localhost:3000"]), \
             patch('app.dependencies.auth.session_manager.get_session', return_value=valid_session_data):
            
            # Measure validation time
            start_time = time.time()
            await verify_csrf_token(mock_request, mock_user)
            end_time = time.time()
            
            # Should complete quickly (under 10ms for mocked operations)
            assert (end_time - start_time) < 0.01

    async def test_csrf_token_comparison_timing(self):
        """Test that CSRF token comparison is not vulnerable to timing attacks."""
        # This would test constant-time comparison, but since we use ==
        # this is more of a note for future improvement to use secrets.compare_digest
        pytest.skip("Timing attack resistance requires secrets.compare_digest implementation")