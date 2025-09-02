"""
Comprehensive tests for enhanced session management service.

Tests cover:
- Session creation and validation
- Session rotation and security  
- Rolling expiry mechanisms
- Concurrent session limits
- Mass session invalidation
- Client information tracking
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException

from app.services.session_service import SessionService, session_service
from app.core.config import settings
from app.core.redis import session_manager


class TestSessionService:
    """Test suite for SessionService class."""

    @pytest.fixture
    async def mock_redis(self):
        """Mock Redis client for testing."""
        redis_mock = AsyncMock()
        redis_mock.get.return_value = None
        redis_mock.set.return_value = True
        redis_mock.expire.return_value = True
        redis_mock.delete.return_value = True
        redis_mock.smembers.return_value = set()
        redis_mock.sadd.return_value = True
        redis_mock.srem.return_value = True
        redis_mock.pipeline.return_value.execute.return_value = [True, True]
        return redis_mock

    @pytest.fixture
    async def service(self, mock_redis):
        """SessionService instance with mocked Redis."""
        service = SessionService()
        service.redis = mock_redis
        return service

    @pytest.fixture
    def sample_client_info(self):
        """Sample client information for testing."""
        return {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Test Browser)",
            "login": True
        }

    async def test_create_session_success(self, service, mock_redis, sample_client_info):
        """Test successful session creation."""
        # Mock session manager
        with patch('app.services.session_service.session_manager.create_session', return_value=True):
            session_id, csrf_token = await service.create_session(
                user_id=123,
                user_email="test@example.com",
                user_name="Test User",
                client_info=sample_client_info
            )

        # Verify return values
        assert session_id is not None
        assert len(session_id) > 32  # High entropy
        assert csrf_token is not None
        assert len(csrf_token) > 32

        # Verify Redis interactions
        mock_redis.sadd.assert_called()
        mock_redis.expire.assert_called()

    async def test_create_session_with_concurrent_limit(self, service, mock_redis, sample_client_info):
        """Test session creation with concurrent session limit enforcement."""
        # Mock existing sessions (at limit)
        existing_sessions = [f"session_{i}" for i in range(settings.max_concurrent_sessions)]
        mock_redis.smembers.return_value = existing_sessions

        # Mock session info for oldest session detection
        with patch.object(service, 'get_session_info') as mock_get_info:
            mock_get_info.side_effect = [
                {"created_at": datetime.utcnow() - timedelta(hours=i), "session_id": f"session_{i}"}
                for i in range(len(existing_sessions))
            ]
            
            with patch('app.services.session_service.session_manager.create_session', return_value=True), \
                 patch('app.services.session_service.session_manager.delete_session', return_value=True):
                
                session_id, csrf_token = await service.create_session(
                    user_id=123,
                    user_email="test@example.com", 
                    user_name="Test User",
                    client_info=sample_client_info
                )

        # Should have removed oldest session
        assert session_id is not None
        mock_redis.srem.assert_called()

    async def test_create_session_redis_failure(self, service, sample_client_info):
        """Test session creation failure when Redis fails."""
        with patch('app.services.session_service.session_manager.create_session', return_value=False):
            with pytest.raises(RuntimeError, match="Failed to create session in Redis"):
                await service.create_session(
                    user_id=123,
                    user_email="test@example.com",
                    user_name="Test User",
                    client_info=sample_client_info
                )

    async def test_rotate_session_success(self, service, mock_redis):
        """Test successful session rotation."""
        old_session_id = "old_session_123"
        
        # Mock existing session data
        session_data = {
            "user_id": 123,
            "email": "test@example.com",
            "name": "Test User",
            "csrf_token": "old_csrf_token",
            "rotation_count": 0
        }
        
        with patch('app.services.session_service.session_manager.get_session', return_value=session_data), \
             patch('app.services.session_service.session_manager.create_session', return_value=True), \
             patch('app.services.session_service.session_manager.delete_session', return_value=True):
            
            new_session_id, new_csrf_token = await service.rotate_session(old_session_id)

        # Verify new session details
        assert new_session_id != old_session_id
        assert new_csrf_token != "old_csrf_token"
        assert len(new_session_id) > 32
        assert len(new_csrf_token) > 32

    async def test_rotate_session_not_found(self, service):
        """Test session rotation failure when session doesn't exist."""
        with patch('app.services.session_service.session_manager.get_session', return_value=None):
            with pytest.raises(ValueError, match="Session not found for rotation"):
                await service.rotate_session("nonexistent_session")

    async def test_rotate_session_creation_failure(self, service):
        """Test session rotation failure during new session creation."""
        session_data = {"user_id": 123, "csrf_token": "old_token"}
        
        with patch('app.services.session_service.session_manager.get_session', return_value=session_data), \
             patch('app.services.session_service.session_manager.create_session', return_value=False):
            
            with pytest.raises(RuntimeError, match="Failed to create rotated session"):
                await service.rotate_session("old_session")

    async def test_refresh_session_activity_success(self, service, mock_redis):
        """Test successful session activity refresh."""
        session_id = "test_session_123"
        current_time = datetime.utcnow()
        old_activity = current_time - timedelta(seconds=settings.session_rolling_window + 100)
        
        session_data = {
            "created_at": (current_time - timedelta(hours=1)).isoformat(),
            "last_activity": old_activity.isoformat()
        }
        
        with patch('app.services.session_service.session_manager.get_session', return_value=session_data), \
             patch('app.services.session_service.session_manager.update_session', return_value=True):
            
            result = await service.refresh_session_activity(session_id)

        assert result is True
        mock_redis.expire.assert_called_with(f"session:{session_id}", settings.session_expire_seconds)

    async def test_refresh_session_activity_not_needed(self, service):
        """Test session activity refresh when not needed (recent activity)."""
        session_id = "test_session_123"
        current_time = datetime.utcnow()
        recent_activity = current_time - timedelta(seconds=30)  # Recent activity
        
        session_data = {
            "created_at": (current_time - timedelta(hours=1)).isoformat(),
            "last_activity": recent_activity.isoformat()
        }
        
        with patch('app.services.session_service.session_manager.get_session', return_value=session_data):
            result = await service.refresh_session_activity(session_id)

        assert result is True  # Still active, but no refresh needed

    async def test_refresh_session_activity_expired_absolute(self, service):
        """Test session activity refresh failure due to absolute max age."""
        session_id = "test_session_123"
        current_time = datetime.utcnow()
        old_creation = current_time - timedelta(seconds=settings.session_absolute_max_age + 100)
        
        session_data = {
            "created_at": old_creation.isoformat(),
            "last_activity": (current_time - timedelta(minutes=30)).isoformat()
        }
        
        with patch('app.services.session_service.session_manager.get_session', return_value=session_data), \
             patch('app.services.session_service.session_manager.delete_session', return_value=True):
            
            result = await service.refresh_session_activity(session_id)

        assert result is False

    async def test_refresh_session_activity_not_found(self, service):
        """Test session activity refresh with non-existent session."""
        with patch('app.services.session_service.session_manager.get_session', return_value=None):
            result = await service.refresh_session_activity("nonexistent_session")
        
        assert result is False

    async def test_invalidate_user_sessions_success(self, service, mock_redis):
        """Test successful mass session invalidation."""
        user_id = 123
        sessions = ["session_1", "session_2", "session_3"]
        current_session = "session_2"
        
        mock_redis.smembers.return_value = sessions
        
        with patch('app.services.session_service.session_manager.delete_session', return_value=True):
            invalidated_count = await service.invalidate_user_sessions(
                user_id=user_id,
                except_session=current_session
            )

        # Should invalidate 2 sessions (excluding current)
        assert invalidated_count == 2
        mock_redis.delete.assert_called_with(f"user_sessions:{user_id}")
        mock_redis.sadd.assert_called_with(f"user_sessions:{user_id}", current_session)

    async def test_invalidate_user_sessions_all(self, service, mock_redis):
        """Test invalidation of all user sessions."""
        user_id = 123
        sessions = ["session_1", "session_2", "session_3"]
        
        mock_redis.smembers.return_value = sessions
        
        with patch('app.services.session_service.session_manager.delete_session', return_value=True):
            invalidated_count = await service.invalidate_user_sessions(user_id=user_id)

        # Should invalidate all sessions
        assert invalidated_count == 3
        mock_redis.delete.assert_called_with(f"user_sessions:{user_id}")

    async def test_get_session_info_success(self, service):
        """Test successful session info retrieval."""
        session_id = "test_session_123"
        current_time = datetime.utcnow()
        created_time = current_time - timedelta(hours=2)
        activity_time = current_time - timedelta(minutes=30)
        
        session_data = {
            "user_id": 123,
            "email": "test@example.com",
            "created_at": created_time.isoformat(),
            "last_activity": activity_time.isoformat(),
            "rotation_count": 1,
            "client_info": {"ip_address": "192.168.1.100"}
        }
        
        with patch('app.services.session_service.session_manager.get_session', return_value=session_data):
            info = await service.get_session_info(session_id)

        assert info is not None
        assert info["session_id"] == session_id
        assert info["user_id"] == 123
        assert info["email"] == "test@example.com"
        assert info["age_seconds"] > 7000  # ~2 hours
        assert info["idle_seconds"] > 1700  # ~30 minutes
        assert info["rotation_count"] == 1

    async def test_get_session_info_not_found(self, service):
        """Test session info retrieval for non-existent session."""
        with patch('app.services.session_service.session_manager.get_session', return_value=None):
            info = await service.get_session_info("nonexistent_session")
        
        assert info is None

    async def test_list_user_sessions_success(self, service, mock_redis):
        """Test successful user session listing."""
        user_id = 123
        sessions = ["session_1", "session_2"]
        
        mock_redis.smembers.return_value = sessions
        
        # Mock session info for each session
        session_infos = [
            {"session_id": "session_1", "user_id": 123, "age_seconds": 3600},
            {"session_id": "session_2", "user_id": 123, "age_seconds": 1800}
        ]
        
        with patch.object(service, 'get_session_info', side_effect=session_infos):
            user_sessions = await service.list_user_sessions(user_id)

        assert len(user_sessions) == 2
        assert user_sessions[0]["session_id"] == "session_1"
        assert user_sessions[1]["session_id"] == "session_2"

    async def test_list_user_sessions_with_expired(self, service, mock_redis):
        """Test user session listing with some expired sessions."""
        user_id = 123
        sessions = ["session_1", "session_2", "session_3"]
        
        mock_redis.smembers.return_value = sessions
        
        # Mock session info - one session expired (returns None)
        session_infos = [
            {"session_id": "session_1", "user_id": 123},
            None,  # session_2 expired
            {"session_id": "session_3", "user_id": 123}
        ]
        
        with patch.object(service, 'get_session_info', side_effect=session_infos):
            user_sessions = await service.list_user_sessions(user_id)

        # Should only return non-expired sessions
        assert len(user_sessions) == 2
        assert all(s["session_id"] in ["session_1", "session_3"] for s in user_sessions)

    async def test_enforce_concurrent_session_limit(self, service, mock_redis):
        """Test concurrent session limit enforcement."""
        user_id = 123
        
        # Mock more sessions than limit
        existing_sessions = [f"session_{i}" for i in range(settings.max_concurrent_sessions + 2)]
        mock_redis.smembers.return_value = existing_sessions
        
        # Mock session info with different creation times
        session_infos = [
            {
                "session_id": f"session_{i}",
                "created_at": datetime.utcnow() - timedelta(hours=i),
                "user_id": user_id
            }
            for i in range(len(existing_sessions))
        ]
        
        with patch.object(service, 'get_session_info', side_effect=session_infos), \
             patch('app.services.session_service.session_manager.delete_session', return_value=True):
            
            await service._enforce_concurrent_session_limit(user_id)

        # Should remove the 3 oldest sessions (to make room for new one)
        expected_deletions = len(existing_sessions) - settings.max_concurrent_sessions + 1
        assert mock_redis.srem.call_count == expected_deletions

    async def test_user_session_tracking_methods(self, service, mock_redis):
        """Test user session tracking helper methods."""
        user_id = 123
        session_id = "test_session"
        
        # Test _add_user_session
        await service._add_user_session(user_id, session_id)
        mock_redis.sadd.assert_called_with(f"user_sessions:{user_id}", session_id)
        mock_redis.expire.assert_called_with(f"user_sessions:{user_id}", settings.session_absolute_max_age)
        
        # Test _remove_user_session
        await service._remove_user_session(user_id, session_id)
        mock_redis.srem.assert_called_with(f"user_sessions:{user_id}", session_id)
        
        # Test _get_user_sessions
        mock_sessions = [b"session_1", b"session_2"]  # Bytes format from Redis
        mock_redis.smembers.return_value = mock_sessions
        
        sessions = await service._get_user_sessions(user_id)
        assert sessions == ["session_1", "session_2"]
        
        # Test _clear_user_sessions
        await service._clear_user_sessions(user_id)
        mock_redis.delete.assert_called_with(f"user_sessions:{user_id}")
        
        # Test _replace_user_session
        old_session = "old_session"
        new_session = "new_session"
        
        pipeline_mock = AsyncMock()
        mock_redis.pipeline.return_value = pipeline_mock
        
        await service._replace_user_session(user_id, old_session, new_session)
        
        pipeline_mock.srem.assert_called_with(f"user_sessions:{user_id}", old_session)
        pipeline_mock.sadd.assert_called_with(f"user_sessions:{user_id}", new_session)
        pipeline_mock.expire.assert_called_with(f"user_sessions:{user_id}", settings.session_absolute_max_age)
        pipeline_mock.execute.assert_called_once()


class TestSessionServiceIntegration:
    """Integration tests for session service with real Redis interactions."""
    
    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self):
        """Test complete session lifecycle from creation to expiry."""
        # This would require a test Redis instance
        pytest.skip("Requires Redis test instance")
    
    @pytest.mark.asyncio 
    async def test_concurrent_access(self):
        """Test session service under concurrent access."""
        # This would test race conditions and concurrent safety
        pytest.skip("Requires Redis test instance and concurrent execution")


# Fixtures for session service testing
@pytest.fixture
async def sample_session_data():
    """Sample session data for testing."""
    return {
        "user_id": 123,
        "email": "test@example.com",
        "name": "Test User",
        "csrf_token": "sample_csrf_token_123",
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
        "login_time": datetime.utcnow().isoformat(),
        "rotation_count": 0,
        "client_info": {
            "ip_address": "192.168.1.100",
            "user_agent": "Test Browser",
            "login": True
        }
    }


# Performance and edge case tests
class TestSessionServicePerformance:
    """Performance and edge case tests for session service."""
    
    async def test_high_entropy_session_id_generation(self, service):
        """Test that session IDs have sufficient entropy."""
        # Generate multiple session IDs
        session_ids = set()
        for _ in range(1000):
            with patch('app.services.session_service.session_manager.create_session', return_value=True):
                session_id, _ = await service.create_session(
                    user_id=1, user_email="test@example.com", user_name="Test"
                )
                session_ids.add(session_id)
        
        # All should be unique (no collisions)
        assert len(session_ids) == 1000
        
        # Check minimum length (base64 encoding of 48 bytes)
        for session_id in list(session_ids)[:10]:
            assert len(session_id) >= 64  # 48 bytes * 4/3 (base64) = 64 chars

    async def test_session_data_integrity(self, service):
        """Test session data integrity through operations."""
        user_id = 123
        email = "test@example.com"
        name = "Test User"
        client_info = {"ip": "192.168.1.1", "browser": "test"}
        
        with patch('app.services.session_service.session_manager') as mock_manager:
            mock_manager.create_session.return_value = True
            mock_manager.get_session.return_value = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "csrf_token": "token123",
                "rotation_count": 0,
                "client_info": client_info
            }
            
            # Create session
            session_id, csrf_token = await service.create_session(
                user_id, email, name, client_info
            )
            
            # Verify data integrity in create_session call
            create_call = mock_manager.create_session.call_args
            session_data = create_call[0][1]  # Second argument is session data
            
            assert session_data["user_id"] == user_id
            assert session_data["email"] == email  
            assert session_data["name"] == name
            assert session_data["client_info"] == client_info
            assert "created_at" in session_data
            assert "last_activity" in session_data
            assert "csrf_token" in session_data