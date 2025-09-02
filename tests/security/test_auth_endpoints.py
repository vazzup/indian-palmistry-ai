"""
Comprehensive tests for enhanced authentication endpoints.

Tests cover:
- Cookie hardening in auth endpoints
- Session management endpoints
- CSRF token handling
- Enhanced error handling
- Session rotation functionality
- Mass session invalidation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.api.v1.auth import (
    register_user, login_user, logout_user, get_current_user_info,
    list_user_sessions, invalidate_all_sessions, rotate_current_session
)
from app.models.user import User


class TestEnhancedAuthEndpoints:
    """Test suite for enhanced authentication endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Mock user object for testing."""
        user = Mock(spec=User)
        user.id = 123
        user.email = "test@example.com"
        user.name = "Test User"
        return user

    @pytest.fixture
    def mock_session_service(self):
        """Mock session service for testing."""
        with patch('app.api.v1.auth.session_service') as mock:
            mock.create_session.return_value = ("session_123", "csrf_token_123")
            mock.rotate_session.return_value = ("new_session_123", "new_csrf_token_123")
            mock.invalidate_user_sessions.return_value = 3
            mock.list_user_sessions.return_value = [
                {
                    "session_id": "session_1",
                    "created_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow(),
                    "client_info": {"ip_address": "192.168.1.100"}
                }
            ]
            yield mock

    @pytest.fixture
    def mock_user_service(self):
        """Mock user service for testing."""
        with patch('app.services.user_service.UserService') as MockUserService:
            mock_service = AsyncMock()
            MockUserService.return_value = mock_service
            mock_service.create_user.return_value = Mock(
                id=123, email="test@example.com", name="Test User"
            )
            mock_service.authenticate_user.return_value = Mock(
                id=123, email="test@example.com", name="Test User"
            )
            yield mock_service

    async def test_register_user_hardened_cookie(self, mock_user_service, mock_session_service):
        """Test user registration sets hardened cookie."""
        from app.schemas.auth import UserRegisterRequest
        from fastapi import Request, Response
        
        # Mock request and response
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {"User-Agent": "Test Browser"}
        
        response = Mock(spec=Response)
        
        user_data = UserRegisterRequest(
            email="test@example.com",
            password="testpass123",
            name="Test User"
        )
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.session_cookie_name = "__Host-session_id"
            mock_settings.session_expire_seconds = 604800
            mock_settings.session_cookie_samesite = "Lax"
            
            result = await register_user(user_data, request, response)
            
            # Verify hardened cookie is set
            response.set_cookie.assert_called_once()
            cookie_call = response.set_cookie.call_args
            
            assert cookie_call[1]["key"] == "__Host-session_id"
            assert cookie_call[1]["value"] == "session_123"
            assert cookie_call[1]["path"] == "/"
            assert cookie_call[1]["httponly"] is True
            assert cookie_call[1]["secure"] is True
            assert cookie_call[1]["samesite"] == "lax"

    async def test_login_user_hardened_cookie(self, mock_user_service, mock_session_service):
        """Test user login sets hardened cookie."""
        from app.schemas.auth import UserLoginRequest
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {"User-Agent": "Test Browser"}
        
        response = Mock(spec=Response)
        
        user_data = UserLoginRequest(
            email="test@example.com",
            password="testpass123"
        )
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.session_cookie_name = "__Host-session_id"
            mock_settings.session_expire_seconds = 604800
            mock_settings.session_cookie_samesite = "Lax"
            
            result = await login_user(user_data, request, response)
            
            # Verify hardened cookie is set
            response.set_cookie.assert_called_once()
            cookie_call = response.set_cookie.call_args
            
            assert cookie_call[1]["key"] == "__Host-session_id"
            assert cookie_call[1]["secure"] is True
            assert cookie_call[1]["httponly"] is True
            assert cookie_call[1]["path"] == "/"

    async def test_register_includes_client_info(self, mock_user_service, mock_session_service):
        """Test registration includes client information in session."""
        from app.schemas.auth import UserRegisterRequest
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "203.0.113.1"
        request.headers = {"User-Agent": "Mozilla/5.0 Test Browser"}
        
        response = Mock(spec=Response)
        
        user_data = UserRegisterRequest(
            email="test@example.com",
            password="testpass123", 
            name="Test User"
        )
        
        await register_user(user_data, request, response)
        
        # Verify session created with client info
        mock_session_service.create_session.assert_called_once()
        call_args = mock_session_service.create_session.call_args
        
        client_info = call_args[1]["client_info"]
        assert client_info["ip_address"] == "203.0.113.1"
        assert client_info["user_agent"] == "Mozilla/5.0 Test Browser"
        assert client_info["registration"] is True

    async def test_login_includes_client_info(self, mock_user_service, mock_session_service):
        """Test login includes client information in session."""
        from app.schemas.auth import UserLoginRequest
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "203.0.113.2"
        request.headers = {"User-Agent": "Chrome Test Browser"}
        
        response = Mock(spec=Response)
        
        user_data = UserLoginRequest(
            email="test@example.com",
            password="testpass123"
        )
        
        await login_user(user_data, request, response)
        
        # Verify session created with client info
        mock_session_service.create_session.assert_called_once()
        call_args = mock_session_service.create_session.call_args
        
        client_info = call_args[1]["client_info"]
        assert client_info["ip_address"] == "203.0.113.2" 
        assert client_info["user_agent"] == "Chrome Test Browser"
        assert client_info["login"] is True

    async def test_session_creation_failure_handling(self, mock_user_service, mock_session_service):
        """Test proper error handling when session creation fails."""
        from app.schemas.auth import UserRegisterRequest
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}
        
        response = Mock(spec=Response)
        
        # Mock session creation failure
        mock_session_service.create_session.side_effect = Exception("Redis unavailable")
        
        user_data = UserRegisterRequest(
            email="test@example.com",
            password="testpass123",
            name="Test User"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await register_user(user_data, request, response)
        
        assert exc_info.value.status_code == 500
        assert "Failed to create user session" in str(exc_info.value.detail)

    async def test_logout_hardened_cookie_clearing(self):
        """Test logout clears hardened cookie properly."""
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.cookies = {"__Host-session_id": "session_123"}
        
        response = Mock(spec=Response)
        
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.core.redis.session_manager.delete_session') as mock_delete:
            
            mock_settings.session_cookie_name = "__Host-session_id"
            mock_settings.session_cookie_samesite = "Lax"
            
            result = await logout_user(request, response)
            
            # Verify session deleted
            mock_delete.assert_called_once_with("session_123")
            
            # Verify hardened cookie cleared
            response.delete_cookie.assert_called()
            cookie_call = response.delete_cookie.call_args
            
            assert cookie_call[1]["key"] == "__Host-session_id"
            assert cookie_call[1]["path"] == "/"
            assert cookie_call[1]["httponly"] is True
            assert cookie_call[1]["secure"] is True

    async def test_list_user_sessions_endpoint(self, mock_user, mock_session_service):
        """Test list user sessions endpoint."""
        result = await list_user_sessions(mock_user)
        
        assert "sessions" in result
        assert "total" in result
        assert result["total"] == 1
        
        # Verify session service called
        mock_session_service.list_user_sessions.assert_called_once_with(mock_user.id)

    async def test_invalidate_all_sessions_endpoint(self, mock_user, mock_session_service):
        """Test invalidate all sessions endpoint."""
        from fastapi import Request
        
        request = Mock(spec=Request)
        request.cookies = {"__Host-session_id": "current_session_123"}
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.session_cookie_name = "__Host-session_id"
            
            result = await invalidate_all_sessions(request, mock_user)
            
            assert result["success"] is True
            assert result["sessions_invalidated"] == 3
            
            # Verify correct parameters passed
            mock_session_service.invalidate_user_sessions.assert_called_once_with(
                user_id=mock_user.id,
                except_session="current_session_123"
            )

    async def test_rotate_current_session_endpoint(self, mock_user, mock_session_service):
        """Test rotate current session endpoint."""
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.cookies = {"__Host-session_id": "old_session_123"}
        
        response = Mock(spec=Response)
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.session_cookie_name = "__Host-session_id"
            mock_settings.session_expire_seconds = 604800
            mock_settings.session_cookie_samesite = "Lax"
            
            result = await rotate_current_session(request, response, mock_user)
            
            assert result["success"] is True
            assert result["csrf_token"] == "new_csrf_token_123"
            
            # Verify session rotation called
            mock_session_service.rotate_session.assert_called_once_with("old_session_123")
            
            # Verify new cookie set
            response.set_cookie.assert_called_once()
            cookie_call = response.set_cookie.call_args
            assert cookie_call[1]["value"] == "new_session_123"

    async def test_rotate_session_no_current_session(self, mock_user):
        """Test session rotation fails when no current session."""
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.cookies = {}  # No session cookie
        
        response = Mock(spec=Response)
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.session_cookie_name = "__Host-session_id"
            
            with pytest.raises(HTTPException) as exc_info:
                await rotate_current_session(request, response, mock_user)
            
            assert exc_info.value.status_code == 401
            assert "No active session" in str(exc_info.value.detail)

    async def test_rotate_session_failure_handling(self, mock_user, mock_session_service):
        """Test session rotation error handling."""
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.cookies = {"__Host-session_id": "old_session_123"}
        
        response = Mock(spec=Response)
        
        # Mock rotation failure
        mock_session_service.rotate_session.side_effect = ValueError("Session not found")
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.session_cookie_name = "__Host-session_id"
            
            with pytest.raises(HTTPException) as exc_info:
                await rotate_current_session(request, response, mock_user)
            
            assert exc_info.value.status_code == 400
            assert "Session not found" in str(exc_info.value.detail)

    async def test_csrf_token_endpoint_enhanced(self, mock_user):
        """Test enhanced CSRF token endpoint."""
        from fastapi import Request
        
        request = Mock(spec=Request)
        request.cookies = {"__Host-session_id": "session_123"}
        
        session_data = {
            "user_id": mock_user.id,
            "csrf_token": "existing_csrf_token"
        }
        
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.core.redis.session_manager') as mock_session_manager:
            
            mock_settings.session_cookie_name = "__Host-session_id"
            mock_session_manager.get_session.return_value = session_data
            
            from app.api.v1.auth import get_csrf_token
            result = await get_csrf_token(request, mock_user)
            
            assert result["csrf_token"] == "existing_csrf_token"

    async def test_auth_endpoints_require_https_cookie(self, mock_user_service, mock_session_service):
        """Test that auth endpoints always set secure cookies."""
        from app.schemas.auth import UserLoginRequest
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}
        
        response = Mock(spec=Response)
        
        user_data = UserLoginRequest(email="test@example.com", password="testpass123")
        
        # Even in development/test, should set secure=True
        await login_user(user_data, request, response)
        
        # Verify secure flag is always True
        cookie_call = response.set_cookie.call_args
        assert cookie_call[1]["secure"] is True

    async def test_session_invalidation_error_handling(self, mock_user, mock_session_service):
        """Test error handling in session invalidation."""
        from fastapi import Request
        
        request = Mock(spec=Request)
        request.cookies = {"__Host-session_id": "current_session"}
        
        # Mock service failure
        mock_session_service.invalidate_user_sessions.side_effect = Exception("Redis error")
        
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.session_cookie_name = "__Host-session_id"
            
            with pytest.raises(HTTPException) as exc_info:
                await invalidate_all_sessions(request, mock_user)
            
            assert exc_info.value.status_code == 500

    async def test_list_sessions_error_handling(self, mock_user, mock_session_service):
        """Test error handling in session listing."""
        # Mock service failure
        mock_session_service.list_user_sessions.side_effect = Exception("Redis error")
        
        with pytest.raises(HTTPException) as exc_info:
            await list_user_sessions(mock_user)
        
        assert exc_info.value.status_code == 500


class TestAuthEndpointsIntegration:
    """Integration tests for authentication endpoints."""

    @pytest.fixture
    def client(self):
        """Test client for integration testing."""
        from app.main import app
        return TestClient(app)

    def test_auth_endpoints_exist(self, client):
        """Test that all auth endpoints are properly registered."""
        # Test endpoints exist (will fail auth but shouldn't return 404)
        endpoints = [
            "/api/v1/auth/register",
            "/api/v1/auth/login", 
            "/api/v1/auth/logout",
            "/api/v1/auth/me",
            "/api/v1/auth/sessions",
            "/api/v1/auth/sessions/rotate",
            "/api/v1/auth/sessions/invalidate-all",
            "/api/v1/auth/csrf-token"
        ]
        
        for endpoint in endpoints:
            if endpoint in ["/api/v1/auth/register", "/api/v1/auth/login"]:
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)
            
            # Should not return 404 (Not Found)
            assert response.status_code != 404

    def test_csrf_protection_on_state_changing_endpoints(self, client):
        """Test that state-changing endpoints require CSRF tokens."""
        # These endpoints should require CSRF tokens
        csrf_endpoints = [
            "/api/v1/auth/sessions/rotate",
            "/api/v1/auth/sessions/invalidate-all"
        ]
        
        for endpoint in csrf_endpoints:
            response = client.post(endpoint, json={})
            
            # Should fail due to missing auth or CSRF, not 404
            assert response.status_code in [401, 403]  # Auth required or CSRF required

    def test_session_management_endpoints_require_auth(self, client):
        """Test that session management endpoints require authentication."""
        endpoints = [
            ("/api/v1/auth/sessions", "GET"),
            ("/api/v1/auth/sessions/rotate", "POST"),
            ("/api/v1/auth/sessions/invalidate-all", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            # Should require authentication
            assert response.status_code == 401


class TestCookieHardening:
    """Specific tests for cookie hardening implementation."""

    async def test_host_prefix_cookie_name(self):
        """Test that __Host- prefix is used in cookie name."""
        from app.core.config import settings
        
        # Verify configuration uses __Host- prefix
        assert settings.session_cookie_name.startswith("__Host-")

    async def test_cookie_security_attributes(self, mock_user_service, mock_session_service):
        """Test all security attributes are set on cookies."""
        from app.schemas.auth import UserLoginRequest
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}
        
        response = Mock(spec=Response)
        
        user_data = UserLoginRequest(email="test@example.com", password="testpass123")
        
        await login_user(user_data, request, response)
        
        # Verify all security attributes
        cookie_call = response.set_cookie.call_args[1]
        
        # Required for __Host- prefix
        assert cookie_call["path"] == "/"
        assert "domain" not in cookie_call  # Must not be set for __Host- prefix
        assert cookie_call["secure"] is True
        
        # Additional security attributes
        assert cookie_call["httponly"] is True
        assert cookie_call["samesite"] in ["lax", "strict"]

    async def test_logout_cookie_clearing_attributes(self):
        """Test that logout cookie clearing uses same security attributes."""
        from fastapi import Request, Response
        
        request = Mock(spec=Request)
        request.cookies = {"__Host-session_id": "session_123"}
        
        response = Mock(spec=Response)
        
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.core.redis.session_manager.delete_session'):
            
            mock_settings.session_cookie_name = "__Host-session_id"
            mock_settings.session_cookie_samesite = "Lax"
            
            await logout_user(request, response)
            
            # Verify cookie clearing uses same security attributes
            cookie_call = response.delete_cookie.call_args[1]
            
            assert cookie_call["path"] == "/"
            assert cookie_call["httponly"] is True
            assert cookie_call["secure"] is True

    def test_configuration_validation(self):
        """Test that configuration enforces security requirements."""
        from app.core.config import settings
        
        # Verify secure configuration
        assert settings.session_cookie_name.startswith("__Host-")
        assert settings.session_cookie_samesite in ["Lax", "Strict"]
        
        # Verify reasonable session timeouts
        assert settings.session_expire_seconds > 0
        assert settings.session_absolute_max_age >= settings.session_expire_seconds