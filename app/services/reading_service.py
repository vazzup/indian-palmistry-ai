"""
Reading service for managing palm readings.
"""

import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import UploadFile
from app.models.reading import Reading, ReadingStatus
from app.services.image_service import ImageService
from app.core.database import AsyncSessionLocal
from app.core.cache import cache_service, CacheKeys

logger = logging.getLogger(__name__)


class ReadingService:
    """Service for managing palm readings with cache management."""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize reading service."""
        self.db = db
        self.image_service = ImageService()
        
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db:
            return self.db
        return AsyncSessionLocal()
    
    async def create_reading(
        self, 
        user_id: Optional[int] = None,
        left_image: Optional[UploadFile] = None,
        right_image: Optional[UploadFile] = None,
        start_analysis: bool = True
    ) -> Reading:
        """Create a new palm reading with optional processing start.
        
        Args:
            user_id: User ID (None for anonymous)
            left_image: Left palm image file
            right_image: Right palm image file
            start_analysis: Whether to start background processing immediately
            
        Returns:
            Created Reading instance
        """
        try:
            # Validate quota first
            self.image_service.validate_quota(user_id)
            
            async with AsyncSessionLocal() as db:
                # Create reading record first
                reading = Reading(
                    user_id=user_id,
                    status=ReadingStatus.QUEUED
                )
                
                db.add(reading)
                await db.commit()
                await db.refresh(reading)
                
                logger.info(f"Created reading {reading.id} for user {user_id}")
                
                # Save images if provided
                if left_image:
                    left_path, left_thumb = await self.image_service.save_image(
                        left_image, user_id, reading.id, "left"
                    )
                    reading.left_image_path = left_path
                    reading.left_thumbnail_path = left_thumb  # Will be None for now
                
                if right_image:
                    right_path, right_thumb = await self.image_service.save_image(
                        right_image, user_id, reading.id, "right"
                    )
                    reading.right_image_path = right_path
                    reading.right_thumbnail_path = right_thumb  # Will be None for now
                
                # Update with image paths
                await db.commit()
                await db.refresh(reading)
                
                logger.info(f"Saved images for reading {reading.id}")
                
                # Conditionally queue background processing job
                if start_analysis:
                    # TODO: Update task to work with Reading model instead of Analysis
                    # For now, set status to QUEUED but don't start background task
                    reading.status = ReadingStatus.QUEUED
                    await db.commit()
                    await db.refresh(reading)
                    
                    logger.info(f"Reading {reading.id} queued for processing (background task disabled temporarily)")
                else:
                    logger.info(f"Reading {reading.id} created without starting background processing")
                
                # Invalidate user cache to ensure dashboard shows new reading immediately
                if user_id:
                    await self._invalidate_user_cache(user_id)
                    logger.debug(f"Invalidated cache for user {user_id} after creating reading {reading.id}")
                
                return reading
                
        except Exception as e:
            logger.error(f"Error creating reading: {e}")
            # Clean up images if reading creation failed
            if 'reading' in locals():
                self.image_service.delete_reading_images(user_id, reading.id)
            raise
    
    async def get_reading_by_id(self, reading_id: int) -> Optional[Reading]:
        """Get reading by ID.
        
        Args:
            reading_id: Reading ID
            
        Returns:
            Reading instance if found, None otherwise
        """
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Reading).where(Reading.id == reading_id)
                result = await db.execute(stmt)
                reading = result.scalar_one_or_none()
                
                return reading
                
        except Exception as e:
            logger.error(f"Error getting reading {reading_id}: {e}")
            return None
    
    async def get_reading_status(self, reading_id: int) -> Optional[Reading]:
        """Get reading status for polling.
        
        Args:
            reading_id: Reading ID
            
        Returns:
            Reading instance with status info
        """
        return await self.get_reading_by_id(reading_id)
    
    async def update_job_id(self, reading_id: int, job_id: str) -> bool:
        """Update reading with background job ID.
        
        Args:
            reading_id: Reading ID
            job_id: Celery job ID
            
        Returns:
            True if updated successfully
        """
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Reading).where(Reading.id == reading_id)
                result = await db.execute(stmt)
                reading = result.scalar_one_or_none()
                
                if not reading:
                    return False
                
                reading.job_id = job_id
                await db.commit()
                
                logger.info(f"Updated reading {reading_id} with job ID {job_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating job ID for reading {reading_id}: {e}")
            return False
    
    async def start_reading(
        self, 
        reading_id: int, 
        user_id: Optional[int] = None
    ) -> Optional[Reading]:
        """Start processing for an existing reading.
        
        Validates that the reading exists, belongs to the user (if provided),
        and hasn't already been started. Then queues the background job.
        
        Args:
            reading_id: Reading ID to start
            user_id: User ID for authorization (None for anonymous)
            
        Returns:
            Updated Reading instance with job_id, or None if not found/authorized
            
        Raises:
            ValueError: If reading has already been started or is invalid for starting
        """
        try:
            async with AsyncSessionLocal() as db:
                # Find the reading
                stmt = select(Reading).where(Reading.id == reading_id)
                if user_id is not None:
                    # For authenticated users, ensure they own the reading
                    stmt = stmt.where(Reading.user_id == user_id)
                else:
                    # For anonymous users, ensure reading is anonymous
                    stmt = stmt.where(Reading.user_id.is_(None))
                
                result = await db.execute(stmt)
                reading = result.scalar_one_or_none()
                
                if not reading:
                    logger.warning(f"Reading {reading_id} not found or not authorized for user {user_id}")
                    return None
                
                # Check if reading has already been started
                if reading.job_id is not None:
                    raise ValueError("Reading has already been started")
                
                # Check if reading has required images
                if not reading.left_image_path and not reading.right_image_path:
                    raise ValueError("Reading has no images to process")
                
                # Check if reading is in a valid state for starting
                if reading.status not in [ReadingStatus.QUEUED]:
                    raise ValueError(f"Reading cannot be started from status: {reading.status.value}")
                
                # TODO: Start the background processing job
                # For now, just update status to QUEUED but don't start background task
                # from app.tasks.analysis_tasks import process_palm_analysis
                # job = process_palm_analysis.delay(reading.id)
                
                # Update reading status (background task disabled temporarily)
                # reading.job_id = job.id
                reading.status = ReadingStatus.QUEUED  # Ensure status is queued
                await db.commit()
                await db.refresh(reading)
                
                logger.info(f"Reading {reading.id} queued for processing (background task disabled temporarily)")
                
                # Invalidate user cache
                if reading.user_id:
                    await self._invalidate_user_cache(reading.user_id)
                    logger.debug(f"Invalidated cache for user {reading.user_id} after starting reading {reading.id}")
                
                return reading
                
        except ValueError:
            # Re-raise business logic errors
            raise
        except Exception as e:
            logger.error(f"Error starting reading {reading_id}: {e}")
            raise
    
    async def get_user_readings(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 5
    ) -> tuple[List[Reading], int]:
        """Get readings for a user with pagination.
        
        Args:
            user_id: User ID
            page: Page number (1-based)
            per_page: Number of readings per page
            
        Returns:
            Tuple of (readings_list, total_count)
        """
        try:
            async with AsyncSessionLocal() as db:
                # Get total count
                count_stmt = select(Reading).where(Reading.user_id == user_id)
                count_result = await db.execute(count_stmt)
                total = len(count_result.fetchall())
                
                # Get paginated results
                offset = (page - 1) * per_page
                stmt = (
                    select(Reading)
                    .where(Reading.user_id == user_id)
                    .order_by(desc(Reading.created_at))
                    .limit(per_page)
                    .offset(offset)
                )
                
                result = await db.execute(stmt)
                readings = result.scalars().all()
                
                return list(readings), total
                
        except Exception as e:
            logger.error(f"Error getting readings for user {user_id}: {e}")
            return [], 0
    
    async def delete_reading(self, reading_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a reading and its associated data.
        
        Args:
            reading_id: Reading ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted successfully
        """
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Reading).where(Reading.id == reading_id)
                if user_id is not None:
                    stmt = stmt.where(Reading.user_id == user_id)
                
                result = await db.execute(stmt)
                reading = result.scalar_one_or_none()
                
                if not reading:
                    return False
                
                # Delete associated images
                self.image_service.delete_reading_images(reading.user_id, reading.id)
                
                # Invalidate user cache before deletion
                if reading.user_id:
                    await self._invalidate_user_cache(reading.user_id)
                    logger.debug(f"Invalidated cache for user {reading.user_id} before deleting reading {reading_id}")
                
                # Delete reading record (conversations and messages will cascade)
                await db.delete(reading)
                await db.commit()
                
                logger.info(f"Deleted reading {reading_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting reading {reading_id}: {e}")
            return False
    
    async def _invalidate_user_cache(self, user_id: int) -> None:
        """Invalidate all cache entries related to a user."""
        try:
            # Invalidate dashboard cache
            await cache_service.invalidate_user_dashboard(user_id)
            
            # Invalidate analytics cache
            await cache_service.invalidate_user_analytics(user_id)
            
            # Invalidate user stats cache (pattern-based)
            pattern = f"user_stats:{user_id}:*"
            await cache_service.delete_pattern(pattern)
            
            # Invalidate user preferences cache
            key = CacheKeys.user_preferences(user_id)
            await cache_service.delete(key)
            
            logger.debug(f"Successfully invalidated cache for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for user {user_id}: {e}")
    
    async def invalidate_reading_cache(self, reading_id: int, user_id: Optional[int] = None) -> bool:
        """Invalidate cache related to a specific reading."""
        try:
            # Invalidate reading result cache
            reading_key = CacheKeys.reading_result(reading_id)
            await cache_service.delete(reading_key)
            
            # If user_id provided, invalidate user-related cache
            if user_id:
                await self._invalidate_user_cache(user_id)
            
            logger.debug(f"Successfully invalidated reading cache for reading {reading_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to invalidate reading cache for reading {reading_id}: {e}")
            return False
    
    async def update_reading_status(self, reading_id: int, status: ReadingStatus, user_id: Optional[int] = None) -> bool:
        """Update reading status and invalidate related cache."""
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Reading).where(Reading.id == reading_id)
                result = await db.execute(stmt)
                reading = result.scalar_one_or_none()
                
                if not reading:
                    return False
                
                reading.status = status
                await db.commit()
                
                # Invalidate cache when reading status changes
                reading_user_id = user_id or reading.user_id
                if reading_user_id:
                    await self._invalidate_user_cache(reading_user_id)
                    logger.debug(f"Invalidated cache for user {reading_user_id} after status change for reading {reading_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating reading status for reading {reading_id}: {e}")
            return False