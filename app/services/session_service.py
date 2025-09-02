"""
Enhanced session management service with security features.

This service provides comprehensive session management including:
- Session rotation on login and privilege changes
- Rolling expiry with absolute maximum age
- Concurrent session limiting
- Mass session invalidation
- Enhanced Redis storage with better security
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.core.redis import session_manager
from app.core.config import settings
from app.dependencies.auth import generate_session_id, generate_csrf_token

logger = logging.getLogger(__name__)


class SessionService:
    """
    Enhanced session management service with security hardening.
    
    Features:
    - Session ID rotation on login/privilege change
    - Rolling expiry mechanism
    - Concurrent session limits
    - Mass invalidation capabilities
    - Audit logging for session events
    """
    
    def __init__(self):
        self.redis = session_manager.redis
        
    async def create_session(
        self, 
        user_id: int, 
        user_email: str, 
        user_name: str,
        client_info: Optional[Dict] = None
    ) -> tuple[str, str]:
        """
        Create a new session with enhanced security features.
        
        Args:
            user_id: User database ID
            user_email: User email address
            user_name: User display name
            client_info: Optional client information (IP, user agent, etc.)
            
        Returns:
            Tuple of (session_id, csrf_token)
        """
        # Generate secure session ID and CSRF token
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        current_time = datetime.utcnow()
        
        # Prepare session data
        session_data = {
            "user_id": user_id,
            "email": user_email,
            "name": user_name,
            "csrf_token": csrf_token,
            "created_at": current_time.isoformat(),
            "last_activity": current_time.isoformat(),
            "login_time": current_time.isoformat(),
            "rotation_count": 0,  # Track how many times this session has been rotated
            "client_info": client_info or {}
        }
        
        # Check and enforce concurrent session limits
        if settings.max_concurrent_sessions > 0:
            await self._enforce_concurrent_session_limit(user_id)
        
        # Store session in Redis
        success = await session_manager.create_session(session_id, session_data)
        if not success:
            raise RuntimeError("Failed to create session in Redis")
        
        # Track user sessions
        await self._add_user_session(user_id, session_id)
        
        # Log session creation
        logger.info(
            f"Session created for user {user_id} ({user_email})",
            extra={
                "user_id": user_id,
                "session_id": session_id[:8] + "...",  # Only log partial session ID
                "client_info": client_info
            }
        )
        
        return session_id, csrf_token
    
    async def rotate_session(self, old_session_id: str) -> tuple[str, str]:
        """
        Rotate session ID while preserving session data.
        
        This should be called on login, privilege escalation, or periodically
        for high-security applications.
        
        Args:
            old_session_id: Current session ID to rotate
            
        Returns:
            Tuple of (new_session_id, new_csrf_token)
            
        Raises:
            ValueError: If session doesn't exist or rotation fails
        """
        # Get existing session data
        session_data = await session_manager.get_session(old_session_id)
        if not session_data:
            raise ValueError("Session not found for rotation")
        
        # Generate new session ID and CSRF token
        new_session_id = generate_session_id()
        new_csrf_token = generate_csrf_token()
        
        # Update session data
        session_data.update({
            "csrf_token": new_csrf_token,
            "last_activity": datetime.utcnow().isoformat(),
            "rotation_count": session_data.get("rotation_count", 0) + 1,
            "rotated_at": datetime.utcnow().isoformat(),
            "previous_session_id": old_session_id  # For audit purposes
        })
        
        # Create new session
        success = await session_manager.create_session(new_session_id, session_data)
        if not success:
            raise RuntimeError("Failed to create rotated session")
        
        # Update user session tracking
        user_id = session_data.get("user_id")
        if user_id:
            await self._replace_user_session(user_id, old_session_id, new_session_id)
        
        # Delete old session
        await session_manager.delete_session(old_session_id)
        
        logger.info(
            f"Session rotated for user {user_id}",
            extra={
                "user_id": user_id,
                "old_session": old_session_id[:8] + "...",
                "new_session": new_session_id[:8] + "...",
                "rotation_count": session_data.get("rotation_count", 0)
            }
        )
        
        return new_session_id, new_csrf_token
    
    async def refresh_session_activity(self, session_id: str) -> bool:
        """
        Refresh session activity timestamp and extend expiry if needed.
        
        Implements rolling expiry - sessions stay alive as long as they're
        being used, up to the absolute maximum age.
        
        Args:
            session_id: Session ID to refresh
            
        Returns:
            True if session was refreshed, False if not found or expired
        """
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            return False
        
        current_time = datetime.utcnow()
        created_at = datetime.fromisoformat(session_data.get("created_at", current_time.isoformat()))
        last_activity = datetime.fromisoformat(session_data.get("last_activity", current_time.isoformat()))
        
        # Check if session has exceeded absolute maximum age
        if (current_time - created_at).total_seconds() > settings.session_absolute_max_age:
            await session_manager.delete_session(session_id)
            logger.info(f"Session {session_id[:8]}... expired due to absolute max age")
            return False
        
        # Check if session needs activity refresh
        time_since_activity = (current_time - last_activity).total_seconds()
        if time_since_activity > settings.session_rolling_window:
            # Update last activity and extend expiry
            session_data["last_activity"] = current_time.isoformat()
            await session_manager.update_session(session_id, session_data)
            
            # Extend Redis TTL
            await self.redis.expire(f"session:{session_id}", settings.session_expire_seconds)
            
            return True
        
        return True  # Session is still active, no refresh needed
    
    async def invalidate_user_sessions(self, user_id: int, except_session: str = None) -> int:
        """
        Invalidate all sessions for a user.
        
        This should be called on password change, account deactivation,
        or when user explicitly logs out from all devices.
        
        Args:
            user_id: User ID to invalidate sessions for
            except_session: Optional session ID to keep (current session)
            
        Returns:
            Number of sessions invalidated
        """
        user_sessions = await self._get_user_sessions(user_id)
        
        invalidated_count = 0
        for session_id in user_sessions:
            if except_session and session_id == except_session:
                continue
                
            await session_manager.delete_session(session_id)
            invalidated_count += 1
        
        # Clear user session tracking
        await self._clear_user_sessions(user_id)
        
        # Add back the excepted session if it exists
        if except_session and except_session in user_sessions:
            await self._add_user_session(user_id, except_session)
        
        logger.info(
            f"Invalidated {invalidated_count} sessions for user {user_id}",
            extra={"user_id": user_id, "sessions_invalidated": invalidated_count}
        )
        
        return invalidated_count
    
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get comprehensive session information.
        
        Args:
            session_id: Session ID to get info for
            
        Returns:
            Dict with session information or None if not found
        """
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            return None
        
        current_time = datetime.utcnow()
        created_at = datetime.fromisoformat(session_data.get("created_at", current_time.isoformat()))
        last_activity = datetime.fromisoformat(session_data.get("last_activity", current_time.isoformat()))
        
        return {
            "session_id": session_id,
            "user_id": session_data.get("user_id"),
            "email": session_data.get("email"),
            "created_at": created_at,
            "last_activity": last_activity,
            "age_seconds": (current_time - created_at).total_seconds(),
            "idle_seconds": (current_time - last_activity).total_seconds(),
            "rotation_count": session_data.get("rotation_count", 0),
            "client_info": session_data.get("client_info", {}),
            "expires_in": settings.session_expire_seconds - (current_time - last_activity).total_seconds()
        }
    
    async def list_user_sessions(self, user_id: int) -> List[Dict]:
        """
        List all active sessions for a user.
        
        Args:
            user_id: User ID to list sessions for
            
        Returns:
            List of session information dicts
        """
        user_sessions = await self._get_user_sessions(user_id)
        session_infos = []
        
        for session_id in user_sessions:
            info = await self.get_session_info(session_id)
            if info:  # Session still exists
                session_infos.append(info)
        
        return session_infos
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions that Redis hasn't removed yet.
        
        This is a maintenance function that should be called periodically.
        
        Returns:
            Number of sessions cleaned up
        """
        # This would typically be implemented with a Redis SCAN operation
        # to find and clean up expired sessions. For now, we rely on Redis TTL.
        logger.info("Session cleanup completed (relying on Redis TTL)")
        return 0
    
    # Private helper methods
    
    async def _enforce_concurrent_session_limit(self, user_id: int) -> None:
        """Enforce maximum concurrent sessions per user."""
        user_sessions = await self._get_user_sessions(user_id)
        
        if len(user_sessions) >= settings.max_concurrent_sessions:
            # Remove oldest sessions
            sessions_to_remove = len(user_sessions) - settings.max_concurrent_sessions + 1
            
            # Get session info to find oldest
            session_infos = []
            for session_id in user_sessions:
                info = await self.get_session_info(session_id)
                if info:
                    session_infos.append(info)
            
            # Sort by creation time and remove oldest
            session_infos.sort(key=lambda x: x["created_at"])
            
            for i in range(sessions_to_remove):
                old_session = session_infos[i]
                await session_manager.delete_session(old_session["session_id"])
                await self._remove_user_session(user_id, old_session["session_id"])
                
            logger.info(
                f"Removed {sessions_to_remove} old sessions for user {user_id} due to limit",
                extra={"user_id": user_id, "limit": settings.max_concurrent_sessions}
            )
    
    async def _get_user_sessions(self, user_id: int) -> List[str]:
        """Get list of session IDs for a user."""
        sessions_data = await self.redis.smembers(f"user_sessions:{user_id}")
        return [session_id.decode() if isinstance(session_id, bytes) else session_id 
                for session_id in sessions_data or []]
    
    async def _add_user_session(self, user_id: int, session_id: str) -> None:
        """Add session to user's session set."""
        await self.redis.sadd(f"user_sessions:{user_id}", session_id)
        await self.redis.expire(f"user_sessions:{user_id}", settings.session_absolute_max_age)
    
    async def _remove_user_session(self, user_id: int, session_id: str) -> None:
        """Remove session from user's session set."""
        await self.redis.srem(f"user_sessions:{user_id}", session_id)
    
    async def _replace_user_session(self, user_id: int, old_session_id: str, new_session_id: str) -> None:
        """Replace old session with new session in user's session set."""
        pipe = self.redis.pipeline()
        pipe.srem(f"user_sessions:{user_id}", old_session_id)
        pipe.sadd(f"user_sessions:{user_id}", new_session_id)
        pipe.expire(f"user_sessions:{user_id}", settings.session_absolute_max_age)
        await pipe.execute()
    
    async def _clear_user_sessions(self, user_id: int) -> None:
        """Clear all sessions for a user."""
        await self.redis.delete(f"user_sessions:{user_id}")


# Global session service instance
session_service = SessionService()