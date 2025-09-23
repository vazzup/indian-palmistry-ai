"""
OAuth service for handling Google, Apple, and Instagram authentication.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from authlib.integrations.starlette_client import OAuth
from authlib.jose import jwt as authlib_jwt
from app.core.config import settings
from app.models.user import User
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for handling OAuth authentication with multiple providers."""

    def __init__(self):
        self.oauth = OAuth()
        self.user_service = UserService()
        self._register_providers()

    def _register_providers(self):
        """Register OAuth providers with their configurations."""

        # Google OAuth with OIDC
        if settings.google_client_id and settings.google_client_secret:
            self.oauth.register(
                name="google",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={
                    "scope": "openid email profile",
                    "code_challenge_method": "S256"  # PKCE
                }
            )
            logger.info("Google OAuth provider registered")




    def get_provider_client(self, provider: str):
        """Get OAuth client for a specific provider."""
        if provider != "google":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )

        client = getattr(self.oauth, provider, None)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"OAuth provider {provider} not configured"
            )

        return client

    def get_redirect_uri(self, provider: str) -> str:
        """Get the redirect URI for a specific provider."""
        return settings.oauth_redirect_url.format(provider=provider)

    async def extract_user_info(self, provider: str, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user information from OAuth token data."""

        if provider == "google":
            # Debug: Log what we actually received from Google
            logger.info(f"Google token response keys: {list(token_data.keys())}")

            # Try to get user info from ID token first (preferred method)
            id_token = token_data.get("id_token")
            if id_token:
                logger.info("Found ID token, attempting to decode")
                try:
                    # Get Google's public keys for verification
                    client = self.get_provider_client("google")
                    response = await client.get("https://www.googleapis.com/oauth2/v3/certs")
                    jwks = response.json()

                    # Verify and decode the ID token
                    claims = authlib_jwt.decode(id_token, jwks)
                    claims.validate()

                    return {
                        "oauth_id": claims["sub"],
                        "email": claims["email"],
                        "name": claims.get("name", ""),
                        "picture": claims.get("picture", ""),
                        "email_verified": claims.get("email_verified", False)
                    }
                except Exception as e:
                    logger.warning(f"Failed to verify Google ID token, falling back to userinfo endpoint: {e}")

            # Fallback: Use Google's userinfo endpoint with access token
            access_token = token_data.get("access_token")
            if not access_token:
                logger.error(f"Neither ID token nor access token found. Available keys: {list(token_data.keys())}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No usable token found. Available keys: {list(token_data.keys())}"
                )

            logger.info("Using access token to fetch user info from Google userinfo endpoint")
            try:
                client = self.get_provider_client("google")
                # Use access token to get user info from Google's userinfo endpoint
                userinfo_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    token=token_data
                )
                userinfo = userinfo_response.json()

                return {
                    "oauth_id": userinfo["id"],
                    "email": userinfo["email"],
                    "name": userinfo.get("name", ""),
                    "picture": userinfo.get("picture", ""),
                    "email_verified": userinfo.get("verified_email", False)
                }
            except Exception as e:
                logger.error(f"Failed to fetch user info from Google userinfo endpoint: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user information from Google"
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )

    async def find_or_create_user(self, provider: str, user_info: Dict[str, Any]) -> User:
        """Find existing user or create new one from OAuth user info."""

        oauth_id = user_info["oauth_id"]
        email = user_info["email"]

        # First, try to find user by OAuth provider and ID
        user = await self.user_service.get_user_by_oauth(provider, oauth_id)

        if user:
            # Update user info if needed
            await self.user_service.update_oauth_user_info(
                user.id,
                name=user_info.get("name", user.name),
                picture=user_info.get("picture", user.picture),
                email_verified=user_info.get("email_verified", user.oauth_email_verified)
            )
            return user

        # If no OAuth user found, try to find by email (for account linking)
        if email:
            existing_user = await self.user_service.get_user_by_email(email)
            if existing_user:
                # Link OAuth account to existing user
                await self.user_service.link_oauth_account(
                    existing_user.id,
                    provider,
                    oauth_id,
                    user_info.get("email_verified", False)
                )
                return existing_user

        # Create new user
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required for account creation"
            )

        user = await self.user_service.create_oauth_user(
            email=email,
            name=user_info.get("name", ""),
            picture=user_info.get("picture", ""),
            provider=provider,
            oauth_id=oauth_id,
            email_verified=user_info.get("email_verified", False)
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )

        return user