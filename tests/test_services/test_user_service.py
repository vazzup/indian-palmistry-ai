"""
Tests for user service functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.user_service import UserService
from app.models.user import User


@pytest.fixture
def user_service():
    """Create user service instance for testing."""
    return UserService()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User"
    }


@pytest.mark.asyncio
class TestUserService:
    """Test user service operations."""
    
    async def test_create_user_success(self, user_service, sample_user_data):
        """Test successful user creation."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock user doesn't exist
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            # Mock successful creation
            mock_user = User(
                id=1,
                email=sample_user_data["email"],
                name=sample_user_data["name"],
                password_hash="hashed_password"
            )
            mock_db.refresh.return_value = None
            
            with patch('app.services.user_service.hash_password') as mock_hash:
                mock_hash.return_value = "hashed_password"
                
                result = await user_service.create_user(**sample_user_data)
                
                # Verify database operations
                assert mock_db.execute.called
                assert mock_db.add.called
                assert mock_db.commit.called
                assert mock_db.refresh.called
                
                # Verify password hashing
                mock_hash.assert_called_once_with(sample_user_data["password"])
    
    async def test_create_user_duplicate_email(self, user_service, sample_user_data):
        """Test user creation with duplicate email."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock user already exists
            existing_user = User(id=1, email=sample_user_data["email"])
            mock_db.execute.return_value.scalar_one_or_none.return_value = existing_user
            
            result = await user_service.create_user(**sample_user_data)
            
            assert result is None
    
    async def test_authenticate_user_success(self, user_service, sample_user_data):
        """Test successful user authentication."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock user exists with correct password
            mock_user = User(
                id=1,
                email=sample_user_data["email"],
                password_hash="hashed_password",
                is_active=True
            )
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            with patch('app.services.user_service.verify_password') as mock_verify:
                mock_verify.return_value = True
                
                result = await user_service.authenticate_user(
                    sample_user_data["email"],
                    sample_user_data["password"]
                )
                
                assert result == mock_user
                mock_verify.assert_called_once_with(
                    sample_user_data["password"],
                    "hashed_password"
                )
    
    async def test_authenticate_user_invalid_password(self, user_service, sample_user_data):
        """Test authentication with invalid password."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock user exists but password is wrong
            mock_user = User(
                id=1,
                email=sample_user_data["email"],
                password_hash="hashed_password",
                is_active=True
            )
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            with patch('app.services.user_service.verify_password') as mock_verify:
                mock_verify.return_value = False
                
                result = await user_service.authenticate_user(
                    sample_user_data["email"],
                    "wrong_password"
                )
                
                assert result is None
    
    async def test_authenticate_user_not_found(self, user_service, sample_user_data):
        """Test authentication with non-existent user."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock user doesn't exist
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await user_service.authenticate_user(
                sample_user_data["email"],
                sample_user_data["password"]
            )
            
            assert result is None
    
    async def test_authenticate_user_inactive(self, user_service, sample_user_data):
        """Test authentication with inactive user."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock inactive user
            mock_user = User(
                id=1,
                email=sample_user_data["email"],
                password_hash="hashed_password",
                is_active=False
            )
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            with patch('app.services.user_service.verify_password') as mock_verify:
                mock_verify.return_value = True
                
                result = await user_service.authenticate_user(
                    sample_user_data["email"],
                    sample_user_data["password"]
                )
                
                assert result is None
    
    async def test_get_user_by_id(self, user_service):
        """Test getting user by ID."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_user = User(id=1, email="test@example.com")
            mock_db.get.return_value = mock_user
            
            result = await user_service.get_user_by_id(1)
            
            assert result == mock_user
            mock_db.get.assert_called_once_with(User, 1)
    
    async def test_update_user_profile(self, user_service):
        """Test updating user profile."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_user = User(id=1, email="test@example.com", name="Old Name")
            mock_db.get.return_value = mock_user
            
            result = await user_service.update_user_profile(
                user_id=1,
                name="New Name",
                picture="https://example.com/pic.jpg"
            )
            
            assert result == mock_user
            assert mock_user.name == "New Name"
            assert mock_user.picture == "https://example.com/pic.jpg"
            mock_db.commit.assert_called_once()
    
    async def test_update_user_profile_not_found(self, user_service):
        """Test updating profile for non-existent user."""
        with patch.object(user_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_db.get.return_value = None
            
            result = await user_service.update_user_profile(
                user_id=999,
                name="New Name"
            )
            
            assert result is None