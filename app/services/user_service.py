"""
User service for user management and authentication.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.services.password_service import PasswordService
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and authentication."""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize user service with optional database session."""
        self.db = db
        
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db:
            return self.db
        return AsyncSessionLocal()
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None
    ) -> Optional[User]:
        """Create a new user account.
        
        Args:
            email: User email address (must be unique)
            password: Plain text password
            name: Optional user name
            
        Returns:
            Created User instance or None if email already exists
        """
        try:
            async with await self.get_session() as db:
                # Check if user already exists
                stmt = select(User).where(User.email == email.lower())
                result = await db.execute(stmt)
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    logger.warning(f"User with email {email} already exists")
                    return None
                
                # Create new user
                hashed_password = PasswordService.hash_password(password)
                user = User(
                    email=email.lower(),
                    password_hash=hashed_password,
                    name=name,
                    age=age,
                    gender=gender
                )
                
                db.add(user)
                await db.commit()
                await db.refresh(user)
                
                logger.info(f"Created new user: {user.id} ({user.email})")
                return user
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password.
        
        Args:
            email: User email address
            password: Plain text password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        try:
            async with await self.get_session() as db:
                stmt = select(User).where(
                    User.email == email.lower(),
                    User.is_active == True
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"User not found or inactive: {email}")
                    return None
                
                # Verify password
                if not PasswordService.verify_password(password, user.password_hash):
                    logger.warning(f"Invalid password for user: {email}")
                    return None
                
                logger.info(f"User authenticated successfully: {user.id} ({user.email})")
                return user
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance if found, None otherwise
        """
        try:
            async with await self.get_session() as db:
                stmt = select(User).where(
                    User.id == user_id,
                    User.is_active == True
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                return user
                
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: User email address
            
        Returns:
            User instance if found, None otherwise
        """
        try:
            async with await self.get_session() as db:
                stmt = select(User).where(
                    User.email == email.lower(),
                    User.is_active == True
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                return user
                
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def update_user_profile(self, user_id: int, name: Optional[str] = None, picture: Optional[str] = None) -> Optional[User]:
        """Update user profile information.
        
        Args:
            user_id: User ID
            name: Updated user name
            picture: Updated profile picture URL
            
        Returns:
            Updated User instance or None if user not found
        """
        try:
            async with await self.get_session() as db:
                stmt = select(User).where(
                    User.id == user_id,
                    User.is_active == True
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"User not found for profile update: {user_id}")
                    return None
                
                # Update fields
                if name is not None:
                    user.name = name
                if picture is not None:
                    user.picture = picture
                
                await db.commit()
                await db.refresh(user)
                
                logger.info(f"Updated profile for user: {user.id}")
                return user
                
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return None

    async def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[User]:
        """Get user by OAuth provider and ID.

        Args:
            provider: OAuth provider name (google, apple, instagram)
            oauth_id: Provider's user ID

        Returns:
            User instance if found, None otherwise
        """
        try:
            async with await self.get_session() as db:
                stmt = select(User).where(
                    User.oauth_provider == provider,
                    User.oauth_id == oauth_id,
                    User.is_active == True
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                return user

        except Exception as e:
            logger.error(f"Error getting user by OAuth {provider}:{oauth_id}: {e}")
            return None

    async def create_oauth_user(
        self,
        email: str,
        name: str,
        picture: str,
        provider: str,
        oauth_id: str,
        email_verified: bool = False
    ) -> Optional[User]:
        """Create a new user account from OAuth provider.

        Args:
            email: User email address
            name: User name from provider
            picture: Profile picture URL from provider
            provider: OAuth provider name
            oauth_id: Provider's user ID
            email_verified: Whether email is verified by provider

        Returns:
            Created User instance or None if email already exists
        """
        try:
            async with await self.get_session() as db:
                # Check if user already exists by email
                stmt = select(User).where(User.email == email.lower())
                result = await db.execute(stmt)
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    logger.warning(f"User with email {email} already exists")
                    return None

                # Create new OAuth user (no password)
                user = User(
                    email=email.lower(),
                    password_hash=None,  # OAuth users don't have passwords
                    name=name,
                    picture=picture,
                    oauth_provider=provider,
                    oauth_id=oauth_id,
                    oauth_email_verified=email_verified
                )

                db.add(user)
                await db.commit()
                await db.refresh(user)

                logger.info(f"Created new OAuth user: {user.id} ({user.email}) via {provider}")
                return user

        except Exception as e:
            logger.error(f"Error creating OAuth user: {e}")
            return None

    async def link_oauth_account(
        self,
        user_id: int,
        provider: str,
        oauth_id: str,
        email_verified: bool = False
    ) -> Optional[User]:
        """Link OAuth account to existing user.

        Args:
            user_id: Existing user ID
            provider: OAuth provider name
            oauth_id: Provider's user ID
            email_verified: Whether email is verified by provider

        Returns:
            Updated User instance or None if user not found
        """
        try:
            async with await self.get_session() as db:
                stmt = select(User).where(
                    User.id == user_id,
                    User.is_active == True
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(f"User not found for OAuth linking: {user_id}")
                    return None

                # Link OAuth account
                user.oauth_provider = provider
                user.oauth_id = oauth_id
                user.oauth_email_verified = email_verified

                await db.commit()
                await db.refresh(user)

                logger.info(f"Linked OAuth account {provider}:{oauth_id} to user {user.id}")
                return user

        except Exception as e:
            logger.error(f"Error linking OAuth account: {e}")
            return None

    async def update_oauth_user_info(
        self,
        user_id: int,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        email_verified: Optional[bool] = None
    ) -> Optional[User]:
        """Update OAuth user information from provider.

        Args:
            user_id: User ID
            name: Updated user name
            picture: Updated profile picture URL
            email_verified: Updated email verification status

        Returns:
            Updated User instance or None if user not found
        """
        try:
            async with await self.get_session() as db:
                stmt = select(User).where(
                    User.id == user_id,
                    User.is_active == True
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(f"User not found for OAuth update: {user_id}")
                    return None

                # Update fields
                if name is not None:
                    user.name = name
                if picture is not None:
                    user.picture = picture
                if email_verified is not None:
                    user.oauth_email_verified = email_verified

                await db.commit()
                await db.refresh(user)

                logger.info(f"Updated OAuth info for user: {user.id}")
                return user

        except Exception as e:
            logger.error(f"Error updating OAuth user info {user_id}: {e}")
            return None

    async def complete_user_profile(self, user_id: int, age: int, gender: str) -> Optional[User]:
        """Complete user profile with age and gender (for OAuth users).

        Args:
            user_id: User ID
            age: User age
            gender: User gender

        Returns:
            Updated User instance or None if user not found
        """
        try:
            async with await self.get_session() as db:
                # Get user
                stmt = select(User).where(
                    User.id == user_id,
                    User.is_active == True
                )
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(f"User not found for profile completion: {user_id}")
                    return None

                # Update age and gender
                user.age = age
                user.gender = gender

                await db.commit()
                await db.refresh(user)

                logger.info(f"Completed profile for user: {user.id}")
                return user

        except Exception as e:
            logger.error(f"Error completing user profile {user_id}: {e}")
            return None

    def is_profile_complete(self, user: User) -> bool:
        """Check if user profile is complete (has age and gender).

        Args:
            user: User instance

        Returns:
            True if profile is complete, False otherwise
        """
        return user.age is not None and user.gender is not None