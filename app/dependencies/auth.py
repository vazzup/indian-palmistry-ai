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
from app.core.config import settings

logger = logging.getLogger(__name__)

# Import session service for enhanced session management
from app.services.session_service import session_service

security = HTTPBearer(auto_error=False)


def generate_session_id() -> str:
    """Generate a secure session ID with 128+ bits of entropy."""
    return secrets.token_urlsafe(48)  # 48 bytes = 384 bits of entropy


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


async def get_current_user_optional(request: Request) -> Optional[User]:
    """Get current user from session with rolling expiry (optional - doesn't raise error if not authenticated).
    
    Args:
        request: FastAPI request object
        
    Returns:
        User instance if authenticated, None otherwise
    """
    try:
        # Get session ID from cookie
        session_id = request.cookies.get(settings.session_cookie_name)
        if not session_id:
            return None
        
        # Refresh session activity (implements rolling expiry)
        session_active = await session_service.refresh_session_activity(session_id)
        if not session_active:
            return None
        
        # Get session data from Redis
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            return None
        
        user_id = session_data.get("user_id")
        if not user_id:
            return None
        
        # Get user from database
        user_service = UserService()
        user = await user_service.get_user_by_id(user_id)
        
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
    """Enhanced CSRF token verification for state-changing requests.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If CSRF token is invalid or missing
    """
    # Skip CSRF check for GET, HEAD, OPTIONS
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return
    
    # Verify origin header for additional CSRF protection
    origin = request.headers.get("Origin")
    referer = request.headers.get("Referer")
    
    # Check if request is coming from allowed origins
    allowed_origins = settings.allowed_origins
    if origin:
        if origin not in allowed_origins:
            logger.warning(f"CSRF: Rejected request from unauthorized origin: {origin}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request from unauthorized origin"
            )
    elif referer:
        # If no origin header, check referer
        referer_origin = "/".join(referer.split("/")[:3])  # Extract origin from referer
        if referer_origin not in allowed_origins:
            logger.warning(f"CSRF: Rejected request from unauthorized referer: {referer}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request from unauthorized referer"
            )
    else:
        # No origin or referer headers - potentially suspicious
        logger.warning("CSRF: Request without origin or referer headers")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing origin information"
        )
    
    # Get CSRF token from header (preferred) or form
    csrf_token = request.headers.get("X-CSRF-Token")
    if not csrf_token:
        # Try to get from form data as fallback
        try:
            form_data = await request.form()
            csrf_token = form_data.get("csrf_token")
        except:
            pass
    
    if not csrf_token:
        logger.warning(f"CSRF: Missing token for {request.method} {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token required"
        )
    
    # Get session data to verify CSRF token
    session_id = request.cookies.get(settings.session_cookie_name)
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
    
    # Verify CSRF token matches session and is bound to user
    session_csrf_token = session_data.get("csrf_token")
    session_user_id = session_data.get("user_id")
    
    if not session_csrf_token or csrf_token != session_csrf_token:
        logger.warning(f"CSRF: Invalid token for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )
    
    # Ensure the session belongs to the current user (double-check)
    if session_user_id != current_user.id:
        logger.error(f"CSRF: Session user mismatch - session: {session_user_id}, current: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session user mismatch"
        )
    
    # Log successful CSRF verification for audit purposes
    logger.debug(f"CSRF: Token verified for user {current_user.id} on {request.method} {request.url.path}")