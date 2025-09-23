"""
OAuth authentication endpoints for Google, Apple, and Instagram.
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Response, status
from starlette.responses import RedirectResponse
from app.services.oauth_service import OAuthService
from app.services.user_service import UserService
from app.core.redis import session_manager
from app.dependencies.auth import generate_session_id, generate_csrf_token
from app.schemas.auth import UserResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])


@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login flow for the specified provider.

    Args:
        provider: OAuth provider name (google)
        request: FastAPI request object

    Returns:
        Redirect to provider's authorization URL
    """
    try:
        oauth_service = OAuthService()
        client = oauth_service.get_provider_client(provider)
        redirect_uri = oauth_service.get_redirect_uri(provider)

        # Generate state parameter for CSRF protection
        state = generate_csrf_token()

        # Store state in session for verification
        # Note: We could use Redis for this, but for simplicity we'll verify in callback

        # Generate authorization URL
        return await client.authorize_redirect(
            request,
            redirect_uri,
            state=state
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating OAuth login for {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth login"
        )


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, request: Request, response: Response):
    """Handle OAuth callback from provider.

    Args:
        provider: OAuth provider name (google)
        request: FastAPI request object
        response: FastAPI response object

    Returns:
        Redirect to frontend with authentication status
    """
    try:
        oauth_service = OAuthService()
        client = oauth_service.get_provider_client(provider)

        # Exchange authorization code for tokens
        try:
            token_data = await client.authorize_access_token(request)
            logger.info(f"Token exchange successful for {provider}")
            logger.info(f"Token data keys: {list(token_data.keys()) if token_data else 'None'}")
            # Don't log full token for security, but log structure
            if token_data:
                safe_data = {k: f"<{type(v).__name__}>" for k, v in token_data.items()}
                logger.info(f"Token data structure: {safe_data}")
        except Exception as e:
            logger.error(f"Failed to exchange OAuth code for {provider}: {e}")
            # Redirect to frontend with error
            error_url = f"{settings.frontend_success_url}?error=oauth_failed"
            return RedirectResponse(url=error_url)

        # Extract user information from token
        try:
            user_info = await oauth_service.extract_user_info(provider, token_data)
        except Exception as e:
            logger.error(f"Failed to extract user info for {provider}: {e}")
            error_url = f"{settings.frontend_success_url}?error=user_info_failed"
            return RedirectResponse(url=error_url)

        # Find or create user
        try:
            user = await oauth_service.find_or_create_user(provider, user_info)
        except Exception as e:
            logger.error(f"Failed to find/create user for {provider}: {e}")
            error_url = f"{settings.frontend_success_url}?error=user_creation_failed"
            return RedirectResponse(url=error_url)

        # Create session
        session_id = generate_session_id()
        csrf_token = generate_csrf_token()
        login_time = datetime.utcnow()

        session_data = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "csrf_token": csrf_token,
            "login_time": login_time.isoformat(),
            "oauth_provider": provider
        }

        success = await session_manager.create_session(session_id, session_data)
        if not success:
            logger.error(f"Failed to create session for OAuth user {user.id}")
            error_url = f"{settings.frontend_success_url}?error=session_failed"
            return RedirectResponse(url=error_url)

        # Check if user profile is complete, redirect to onboarding if needed
        user_service = UserService()
        if not user_service.is_profile_complete(user):
            logger.info(f"OAuth user {user.id} needs to complete profile, redirecting to onboarding")
            # Extract base URL from frontend_success_url (e.g., "http://localhost:3000/dashboard" -> "http://localhost:3000")
            from urllib.parse import urlparse
            parsed_url = urlparse(settings.frontend_success_url)
            frontend_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
            redirect_url = f"{frontend_base}/complete-profile"
        else:
            redirect_url = settings.frontend_success_url

        # Set secure session cookie (matching existing auth system)
        response = RedirectResponse(url=redirect_url)
        response.set_cookie(
            key="session_id",  # Use same cookie name as existing auth system
            value=session_id,
            max_age=settings.session_expire_seconds,
            httponly=True,
            secure=settings.is_production,
            samesite="lax",
            domain="localhost" if not settings.is_production else None
        )

        logger.info(f"OAuth login successful: {user.id} ({user.email}) via {provider}")
        return response

    except HTTPException as e:
        # Already logged
        error_url = f"{settings.frontend_success_url}?error={e.detail}"
        return RedirectResponse(url=error_url)
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback for {provider}: {e}")
        error_url = f"{settings.frontend_success_url}?error=internal_error"
        return RedirectResponse(url=error_url)


@router.post("/{provider}/link")
async def link_oauth_account(provider: str, request: Request):
    """Link OAuth account to existing authenticated user.

    This endpoint allows users who are already logged in to link
    additional OAuth providers to their account.

    Args:
        provider: OAuth provider name (google)
        request: FastAPI request object

    Returns:
        Success response with updated user info
    """
    # This would require the user to be authenticated first
    # Implementation would be similar to oauth_callback but would link
    # the OAuth account to the existing session user instead of creating new user

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth account linking not yet implemented"
    )


@router.get("/providers")
async def get_available_providers():
    """Get list of configured OAuth providers.

    Returns:
        List of available OAuth provider configurations
    """
    providers = []

    # Check which providers are configured
    if settings.google_client_id and settings.google_client_secret:
        providers.append({
            "name": "google",
            "display_name": "Google",
            "login_url": "/auth/oauth/google/login"
        })


    return {"providers": providers}