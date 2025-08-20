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
    
    async def create_user(self, email: str, password: str, name: Optional[str] = None) -> Optional[User]:
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
                    name=name
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