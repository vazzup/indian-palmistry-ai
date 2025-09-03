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
        
        # Create session for the new user
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        
        session_data = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "csrf_token": csrf_token,
            "login_time": datetime.utcnow().isoformat()
        }
        
        success = await session_manager.create_session(session_id, session_data)
        if not success:
            logger.error(f"Failed to create session for user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user session"
            )
        
        # Set secure session cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=settings.session_expire_seconds,
            httponly=True,
            secure=settings.is_production,
            samesite="lax"
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
        
        # Create new session
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        login_time = datetime.utcnow()
        
        session_data = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "csrf_token": csrf_token,
            "login_time": login_time.isoformat()
        }
        
        success = await session_manager.create_session(session_id, session_data)
        if not success:
            logger.error(f"Failed to create session for user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user session"
            )
        
        # Set secure session cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=settings.session_expire_seconds,
            httponly=True,
            secure=settings.is_production,
            samesite="lax"
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
        session_id = request.cookies.get("session_id")
        
        if session_id:
            # Delete session from Redis
            await session_manager.delete_session(session_id)
            logger.info(f"Session deleted: {session_id}")
        
        # Clear session cookie
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