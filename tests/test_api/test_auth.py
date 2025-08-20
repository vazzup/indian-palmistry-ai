"""
Integration tests for authentication API endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models.user import User


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User"
    }


@pytest.mark.asyncio
class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_register_success(self, client, sample_user):
        """Test successful user registration."""
        with patch('app.services.user_service.UserService.create_user') as mock_create, \
             patch('app.dependencies.auth.generate_session_id') as mock_session_id, \
             patch('app.dependencies.auth.generate_csrf_token') as mock_csrf, \
             patch('app.core.redis.session_manager.create_session') as mock_session:
            
            # Mock successful user creation
            mock_user = User(
                id=1,
                email=sample_user["email"],
                name=sample_user["name"]
            )
            mock_create.return_value = mock_user
            mock_session_id.return_value = "test-session-id"
            mock_csrf.return_value = "test-csrf-token"
            mock_session.return_value = True
            
            response = client.post("/api/v1/auth/register", json=sample_user)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user"]["email"] == sample_user["email"]
            assert data["user"]["name"] == sample_user["name"]
            assert "csrf_token" in data
            
            # Verify session cookie was set
            assert "session_id" in response.cookies
    
    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email."""
        with patch('app.services.user_service.UserService.create_user') as mock_create:
            # Mock user creation failure (duplicate email)
            mock_create.return_value = None
            
            response = client.post("/api/v1/auth/register", json=sample_user)
            
            assert response.status_code == 400
            data = response.json()
            assert "User with this email already exists" in data["detail"]
    
    def test_register_invalid_data(self, client):
        """Test registration with invalid data."""
        invalid_data = {
            "email": "invalid-email",  # Invalid email format
            "password": "123",  # Too short
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self, client, sample_user):
        """Test successful user login."""
        with patch('app.services.user_service.UserService.authenticate_user') as mock_auth, \
             patch('app.dependencies.auth.generate_session_id') as mock_session_id, \
             patch('app.dependencies.auth.generate_csrf_token') as mock_csrf, \
             patch('app.core.redis.session_manager.create_session') as mock_session:
            
            # Mock successful authentication
            mock_user = User(
                id=1,
                email=sample_user["email"],
                name=sample_user["name"]
            )
            mock_auth.return_value = mock_user
            mock_session_id.return_value = "test-session-id"
            mock_csrf.return_value = "test-csrf-token"
            mock_session.return_value = True
            
            login_data = {
                "email": sample_user["email"],
                "password": sample_user["password"]
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user"]["email"] == sample_user["email"]
            assert "csrf_token" in data
            assert "session_expires" in data
            
            # Verify session cookie was set
            assert "session_id" in response.cookies
    
    def test_login_invalid_credentials(self, client, sample_user):
        """Test login with invalid credentials."""
        with patch('app.services.user_service.UserService.authenticate_user') as mock_auth:
            # Mock authentication failure
            mock_auth.return_value = None
            
            login_data = {
                "email": sample_user["email"],
                "password": "wrong_password"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid email or password" in data["detail"]
    
    def test_login_session_creation_failure(self, client, sample_user):
        """Test login when session creation fails."""
        with patch('app.services.user_service.UserService.authenticate_user') as mock_auth, \
             patch('app.dependencies.auth.generate_session_id') as mock_session_id, \
             patch('app.core.redis.session_manager.create_session') as mock_session:
            
            # Mock successful authentication but session creation failure
            mock_user = User(id=1, email=sample_user["email"])
            mock_auth.return_value = mock_user
            mock_session_id.return_value = "test-session-id"
            mock_session.return_value = False
            
            login_data = {
                "email": sample_user["email"],
                "password": sample_user["password"]
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to create user session" in data["detail"]
    
    def test_logout_success(self, client):
        """Test successful logout."""
        with patch('app.core.redis.session_manager.delete_session') as mock_delete:
            mock_delete.return_value = None
            
            # Set session cookie
            client.cookies.set("session_id", "test-session-id")
            
            response = client.post("/api/v1/auth/logout")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Logout successful"
            
            # Verify session was deleted
            mock_delete.assert_called_once_with("test-session-id")
    
    def test_logout_no_session(self, client):
        """Test logout without session cookie."""
        with patch('app.core.redis.session_manager.delete_session') as mock_delete:
            response = client.post("/api/v1/auth/logout")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Session delete should not be called
            mock_delete.assert_not_called()
    
    def test_get_current_user_success(self, client, sample_user):
        """Test getting current user information."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user:
            mock_user = User(
                id=1,
                email=sample_user["email"],
                name=sample_user["name"]
            )
            mock_get_user.return_value = mock_user
            
            # Mock authenticated request
            client.cookies.set("session_id", "test-session-id")
            
            response = client.get("/api/v1/auth/me")
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == sample_user["email"]
            assert data["name"] == sample_user["name"]
    
    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_update_profile_success(self, client, sample_user):
        """Test successful profile update."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.dependencies.auth.verify_csrf_token') as mock_csrf, \
             patch('app.services.user_service.UserService.update_user_profile') as mock_update:
            
            mock_user = User(id=1, email=sample_user["email"])
            mock_get_user.return_value = mock_user
            mock_csrf.return_value = None  # CSRF verification passes
            
            # Mock successful update
            updated_user = User(
                id=1,
                email=sample_user["email"],
                name="Updated Name"
            )
            mock_update.return_value = updated_user
            
            update_data = {"name": "Updated Name"}
            
            # Set session and CSRF cookies
            client.cookies.set("session_id", "test-session-id")
            
            response = client.put(
                "/api/v1/auth/profile",
                json=update_data,
                headers={"X-CSRF-Token": "test-csrf-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
    
    def test_update_profile_unauthenticated(self, client):
        """Test profile update without authentication."""
        update_data = {"name": "Updated Name"}
        
        response = client.put("/api/v1/auth/profile", json=update_data)
        
        assert response.status_code == 401
    
    def test_get_csrf_token_success(self, client):
        """Test getting CSRF token."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.core.redis.session_manager.get_session') as mock_get_session:
            
            mock_user = User(id=1, email="test@example.com")
            mock_get_user.return_value = mock_user
            
            # Mock session with CSRF token
            mock_get_session.return_value = {"csrf_token": "test-csrf-token"}
            
            client.cookies.set("session_id", "test-session-id")
            
            response = client.get("/api/v1/auth/csrf-token")
            
            assert response.status_code == 200
            data = response.json()
            assert data["csrf_token"] == "test-csrf-token"
    
    def test_get_csrf_token_no_session(self, client):
        """Test getting CSRF token without session."""
        response = client.get("/api/v1/auth/csrf-token")
        
        assert response.status_code == 401