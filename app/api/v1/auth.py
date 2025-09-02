"""
Authentication API endpoints for user registration, login, and logout.
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest, 
    AuthResponse,
    LoginResponse,
    LogoutResponse,
    UserResponse,
    UserProfileUpdateRequest
)
from app.services.user_service import UserService
from app.core.redis import session_manager
from app.dependencies.auth import (
    get_current_user,
    get_current_user_optional,
    generate_session_id,
    generate_csrf_token,
    verify_csrf_token
)
from app.services.session_service import session_service
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=AuthResponse)
async def register_user(
    user_data: UserRegisterRequest,
    response: Response
) -> AuthResponse:
    """Register a new user account.
    
    Creates a new user account with the provided email and password.
    Automatically logs the user in upon successful registration.
    """
    try:
        user_service = UserService()
        
        # Create new user
        user = await user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create session for the new user with enhanced security
        client_info = {
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "registration": True
        }
        
        try:
            session_id, csrf_token = await session_service.create_session(
                user_id=user.id,
                user_email=user.email,
                user_name=user.name,
                client_info=client_info
            )
        except Exception as e:
            logger.error(f"Failed to create session for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user session"
            )
        
        # Set secure session cookie with hardened settings
        response.set_cookie(
            key=settings.session_cookie_name,
            value=session_id,
            max_age=settings.session_expire_seconds,
            path="/",
            httponly=True,
            secure=True,  # Always require HTTPS for security
            samesite=settings.session_cookie_samesite.lower()
        )
        
        logger.info(f"User registered and logged in: {user.id} ({user.email})")
        
        return AuthResponse(
            success=True,
            message="User registered successfully",
            user=UserResponse.model_validate(user),
            csrf_token=csrf_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    user_data: UserLoginRequest,
    request: Request,
    response: Response
) -> LoginResponse:
    """Login user with email and password.
    
    Authenticates user credentials and creates a new session.
    """
    try:
        user_service = UserService()
        
        # Authenticate user
        user = await user_service.authenticate_user(
            email=user_data.email,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create new session with enhanced security
        client_info = {
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "login": True
        }
        
        try:
            session_id, csrf_token = await session_service.create_session(
                user_id=user.id,
                user_email=user.email,
                user_name=user.name,
                client_info=client_info
            )
        except Exception as e:
            logger.error(f"Failed to create session for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user session"
            )
        
        login_time = datetime.utcnow()
        
        # Set secure session cookie with hardened settings
        response.set_cookie(
            key=settings.session_cookie_name,
            value=session_id,
            max_age=settings.session_expire_seconds,
            path="/",
            httponly=True,
            secure=True,  # Always require HTTPS for security
            samesite=settings.session_cookie_samesite.lower()
        )
        
        session_expires = login_time + timedelta(seconds=settings.session_expire_seconds)
        
        logger.info(f"User logged in: {user.id} ({user.email})")
        
        return LoginResponse(
            success=True,
            message="Login successful",
            user=UserResponse.model_validate(user),
            csrf_token=csrf_token,
            session_expires=session_expires.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    request: Request,
    response: Response
) -> LogoutResponse:
    """Logout current user.
    
    Destroys the user session and clears the session cookie.
    """
    try:
        # Get session ID from cookie
        session_id = request.cookies.get(settings.session_cookie_name)
        
        if session_id:
            # Delete session from Redis
            await session_manager.delete_session(session_id)
            logger.info(f"Session deleted: {session_id}")
        
        # Clear session cookie
        response.delete_cookie(
            key=settings.session_cookie_name,
            path="/",
            httponly=True,
            secure=True,
            samesite=settings.session_cookie_samesite.lower()
        )
        
        return LogoutResponse(
            success=True,
            message="Logout successful"
        )
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        # Even if there's an error, clear the cookie
        response.delete_cookie(
            key="session_id",
            httponly=True,
            secure=settings.is_production,
            samesite="lax"
        )
        
        return LogoutResponse(
            success=True,
            message="Logout successful"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user information.
    
    Returns the profile information of the currently authenticated user.
    """
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse, dependencies=[Depends(verify_csrf_token)])
async def update_user_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Update current user's profile information.
    
    Updates the profile information of the currently authenticated user.
    Requires CSRF token for security.
    """
    try:
        user_service = UserService()
        
        updated_user = await user_service.update_user_profile(
            user_id=current_user.id,
            name=profile_data.name,
            picture=profile_data.picture
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User profile updated: {updated_user.id}")
        
        return UserResponse.model_validate(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/csrf-token")
async def get_csrf_token(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get CSRF token for the current session.
    
    Returns a fresh CSRF token that can be used for state-changing requests.
    """
    try:
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
        
        csrf_token = session_data.get("csrf_token")
        if not csrf_token:
            # Generate new CSRF token if not exists
            csrf_token = generate_csrf_token()
            session_data["csrf_token"] = csrf_token
            await session_manager.update_session(session_id, session_data)
        
        return {"csrf_token": csrf_token}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CSRF token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/sessions")
async def list_user_sessions(
    current_user: User = Depends(get_current_user)
) -> dict:
    """List all active sessions for the current user.
    
    Returns information about all active sessions including creation time,
    last activity, and client information for security monitoring.
    """
    try:
        sessions = await session_service.list_user_sessions(current_user.id)
        
        return {
            "sessions": sessions,
            "total": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/sessions/invalidate-all", dependencies=[Depends(verify_csrf_token)])
async def invalidate_all_sessions(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Invalidate all sessions except the current one.
    
    This is useful when a user wants to log out from all other devices
    while keeping their current session active.
    """
    try:
        current_session_id = request.cookies.get(settings.session_cookie_name)
        
        invalidated_count = await session_service.invalidate_user_sessions(
            user_id=current_user.id,
            except_session=current_session_id
        )
        
        return {
            "success": True,
            "message": f"Invalidated {invalidated_count} sessions",
            "sessions_invalidated": invalidated_count
        }
        
    except Exception as e:
        logger.error(f"Error invalidating sessions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/sessions/rotate", dependencies=[Depends(verify_csrf_token)])
async def rotate_current_session(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Rotate the current session ID for enhanced security.
    
    This generates a new session ID while preserving session data.
    Should be called periodically or after sensitive operations.
    """
    try:
        current_session_id = request.cookies.get(settings.session_cookie_name)
        if not current_session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No active session"
            )
        
        new_session_id, new_csrf_token = await session_service.rotate_session(current_session_id)
        
        # Set new session cookie
        response.set_cookie(
            key=settings.session_cookie_name,
            value=new_session_id,
            max_age=settings.session_expire_seconds,
            path="/",
            httponly=True,
            secure=True,
            samesite=settings.session_cookie_samesite.lower()
        )
        
        return {
            "success": True,
            "message": "Session rotated successfully",
            "csrf_token": new_csrf_token
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rotating session for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )