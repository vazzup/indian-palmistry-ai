"""
Authentication dependencies for FastAPI routes.
"""

import secrets
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User
from app.services.user_service import UserService
from app.core.redis import session_manager

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def generate_session_id() -> str:
    """Generate a secure session ID."""
    return secrets.token_urlsafe(32)


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


async def get_current_user_optional(request: Request) -> Optional[User]:
    """Get current user from session (optional - doesn't raise error if not authenticated).
    
    Args:
        request: FastAPI request object
        
    Returns:
        User instance if authenticated, None otherwise
    """
    try:
        # Get session ID from cookie
        session_id = request.cookies.get("session_id")
        if not session_id:
            return None
        
        # Get session data from Redis
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            return None
        
        user_data = session_data.get("user_data")
        if not user_data:
            return None
        
        # Get user from database
        user_service = UserService()
        user = await user_service.get_user_by_id(user_data.get("user_id"))
        
        return user
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


async def get_current_user(request: Request) -> User:
    """Get current user from session (required - raises error if not authenticated).
    
    Args:
        request: FastAPI request object
        
    Returns:
        User instance
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


async def verify_csrf_token(request: Request, current_user: User = Depends(get_current_user)) -> None:
    """Verify CSRF token for state-changing requests.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If CSRF token is invalid or missing
    """
    # Skip CSRF check for GET, HEAD, OPTIONS
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return
    
    # Get CSRF token from header or form
    csrf_token = request.headers.get("X-CSRF-Token")
    if not csrf_token:
        # Try to get from form data
        try:
            form_data = await request.form()
            csrf_token = form_data.get("csrf_token")
        except:
            pass
    
    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token required"
        )
    
    # Get session data to verify CSRF token
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session required"
        )
    
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    # Verify CSRF token matches session
    session_csrf_token = session_data.get("csrf_token")
    if not session_csrf_token or csrf_token != session_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )