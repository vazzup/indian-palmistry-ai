"""
Analysis service for managing palm reading analyses.
"""

import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import UploadFile
from app.models.analysis import Analysis, AnalysisStatus
from app.services.image_service import ImageService
from app.core.database import AsyncSessionLocal
from app.core.cache import cache_service, CacheKeys

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for managing palm reading analyses with cache management."""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize analysis service."""
        self.db = db
        self.image_service = ImageService()
        
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db:
            return self.db
        return AsyncSessionLocal()
    
    async def create_analysis(
        self, 
        user_id: Optional[int] = None,
        left_image: Optional[UploadFile] = None,
        right_image: Optional[UploadFile] = None,
        start_analysis: bool = True
    ) -> Analysis:
        """Create a new palm analysis with optional processing start.
        
        Args:
            user_id: User ID (None for anonymous)
            left_image: Left palm image file
            right_image: Right palm image file
            start_analysis: Whether to start background processing immediately
            
        Returns:
            Created Analysis instance
        """
        try:
            # Validate quota first
            self.image_service.validate_quota(user_id)
            
            async with await self.get_session() as db:
                # Create analysis record first
                analysis = Analysis(
                    user_id=user_id,
                    status=AnalysisStatus.QUEUED
                )
                
                db.add(analysis)
                await db.commit()
                await db.refresh(analysis)
                
                logger.info(f"Created analysis {analysis.id} for user {user_id}")
                
                # Save images if provided
                if left_image:
                    left_path, left_thumb = await self.image_service.save_image(
                        left_image, user_id, analysis.id, "left"
                    )
                    analysis.left_image_path = left_path
                    analysis.left_thumbnail_path = left_thumb  # Will be None for now
                
                if right_image:
                    right_path, right_thumb = await self.image_service.save_image(
                        right_image, user_id, analysis.id, "right"
                    )
                    analysis.right_image_path = right_path
                    analysis.right_thumbnail_path = right_thumb  # Will be None for now
                
                # Update with image paths
                await db.commit()
                await db.refresh(analysis)
                
                logger.info(f"Saved images for analysis {analysis.id}")
                
                # Conditionally queue background processing job
                if start_analysis:
                    from app.tasks.analysis_tasks import process_palm_analysis
                    job = process_palm_analysis.delay(analysis.id)
                    analysis.job_id = job.id
                    await db.commit()
                    await db.refresh(analysis)
                    
                    logger.info(f"Queued analysis job {job.id} for analysis {analysis.id}")
                else:
                    logger.info(f"Analysis {analysis.id} created without starting background processing")
                
                # Invalidate user cache to ensure dashboard shows new analysis immediately
                if user_id:
                    await self._invalidate_user_cache(user_id)
                    logger.debug(f"Invalidated cache for user {user_id} after creating analysis {analysis.id}")
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            # Clean up images if analysis creation failed
            if 'analysis' in locals():
                self.image_service.delete_analysis_images(user_id, analysis.id)
            raise
    
    async def get_analysis_by_id(self, analysis_id: int) -> Optional[Analysis]:
        """Get analysis by ID.
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Analysis instance if found, None otherwise
        """
        try:
            async with await self.get_session() as db:
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error getting analysis {analysis_id}: {e}")
            return None
    
    async def get_analysis_status(self, analysis_id: int) -> Optional[Analysis]:
        """Get analysis status for polling.
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Analysis instance with status info
        """
        return await self.get_analysis_by_id(analysis_id)
    
    async def update_job_id(self, analysis_id: int, job_id: str) -> bool:
        """Update analysis with background job ID.
        
        Args:
            analysis_id: Analysis ID
            job_id: Celery job ID
            
        Returns:
            True if updated successfully
        """
        try:
            async with await self.get_session() as db:
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    return False
                
                analysis.job_id = job_id
                await db.commit()
                
                logger.info(f"Updated analysis {analysis_id} with job ID {job_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating job ID for analysis {analysis_id}: {e}")
            return False
    
    async def start_analysis(
        self, 
        analysis_id: int, 
        user_id: Optional[int] = None
    ) -> Optional[Analysis]:
        """Start processing for an existing analysis.
        
        Validates that the analysis exists, belongs to the user (if provided),
        and hasn't already been started. Then queues the background job.
        
        Args:
            analysis_id: Analysis ID to start
            user_id: User ID for authorization (None for anonymous)
            
        Returns:
            Updated Analysis instance with job_id, or None if not found/authorized
            
        Raises:
            ValueError: If analysis has already been started or is invalid for starting
        """
        try:
            async with await self.get_session() as db:
                # Find the analysis
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                if user_id is not None:
                    # For authenticated users, ensure they own the analysis
                    stmt = stmt.where(Analysis.user_id == user_id)
                else:
                    # For anonymous users, ensure analysis is anonymous
                    stmt = stmt.where(Analysis.user_id.is_(None))
                
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    logger.warning(f"Analysis {analysis_id} not found or not authorized for user {user_id}")
                    return None
                
                # Check if analysis has already been started
                if analysis.job_id is not None:
                    raise ValueError("Analysis has already been started")
                
                # Check if analysis has required images
                if not analysis.left_image_path and not analysis.right_image_path:
                    raise ValueError("Analysis has no images to process")
                
                # Check if analysis is in a valid state for starting
                if analysis.status not in [AnalysisStatus.QUEUED]:
                    raise ValueError(f"Analysis cannot be started from status: {analysis.status.value}")
                
                # Start the background processing job
                from app.tasks.analysis_tasks import process_palm_analysis
                job = process_palm_analysis.delay(analysis.id)
                
                # Update analysis with job information
                analysis.job_id = job.id
                analysis.status = AnalysisStatus.QUEUED  # Ensure status is queued
                await db.commit()
                await db.refresh(analysis)
                
                logger.info(f"Started analysis job {job.id} for analysis {analysis.id}")
                
                # Invalidate user cache
                if analysis.user_id:
                    await self._invalidate_user_cache(analysis.user_id)
                    logger.debug(f"Invalidated cache for user {analysis.user_id} after starting analysis {analysis.id}")
                
                return analysis
                
        except ValueError:
            # Re-raise business logic errors
            raise
        except Exception as e:
            logger.error(f"Error starting analysis {analysis_id}: {e}")
            raise
    
    async def get_user_analyses(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 5
    ) -> tuple[List[Analysis], int]:
        """Get analyses for a user with pagination.
        
        Args:
            user_id: User ID
            page: Page number (1-based)
            per_page: Number of analyses per page
            
        Returns:
            Tuple of (analyses_list, total_count)
        """
        try:
            async with await self.get_session() as db:
                # Get total count
                count_stmt = select(Analysis).where(Analysis.user_id == user_id)
                count_result = await db.execute(count_stmt)
                total = len(count_result.fetchall())
                
                # Get paginated results
                offset = (page - 1) * per_page
                stmt = (
                    select(Analysis)
                    .where(Analysis.user_id == user_id)
                    .order_by(desc(Analysis.created_at))
                    .limit(per_page)
                    .offset(offset)
                )
                
                result = await db.execute(stmt)
                analyses = result.scalars().all()
                
                return list(analyses), total
                
        except Exception as e:
            logger.error(f"Error getting analyses for user {user_id}: {e}")
            return [], 0
    
    async def delete_analysis(self, analysis_id: int, user_id: Optional[int] = None) -> bool:
        """Delete an analysis and its associated data.
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted successfully
        """
        try:
            async with await self.get_session() as db:
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                if user_id is not None:
                    stmt = stmt.where(Analysis.user_id == user_id)
                
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    return False
                
                # Delete associated images
                self.image_service.delete_analysis_images(analysis.user_id, analysis.id)
                
                # Invalidate user cache before deletion
                if analysis.user_id:
                    await self._invalidate_user_cache(analysis.user_id)
                    logger.debug(f"Invalidated cache for user {analysis.user_id} before deleting analysis {analysis_id}")
                
                # Delete analysis record (conversations and messages will cascade)
                await db.delete(analysis)
                await db.commit()
                
                logger.info(f"Deleted analysis {analysis_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
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
    
    async def invalidate_analysis_cache(self, analysis_id: int, user_id: Optional[int] = None) -> bool:
        """Invalidate cache related to a specific analysis."""
        try:
            # Invalidate analysis result cache
            analysis_key = CacheKeys.analysis_result(analysis_id)
            await cache_service.delete(analysis_key)
            
            # If user_id provided, invalidate user-related cache
            if user_id:
                await self._invalidate_user_cache(user_id)
            
            logger.debug(f"Successfully invalidated analysis cache for analysis {analysis_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to invalidate analysis cache for analysis {analysis_id}: {e}")
            return False
    
    async def update_analysis_status(self, analysis_id: int, status: AnalysisStatus, user_id: Optional[int] = None) -> bool:
        """Update analysis status and invalidate related cache."""
        try:
            async with await self.get_session() as db:
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    return False
                
                analysis.status = status
                await db.commit()
                
                # Invalidate cache when analysis status changes
                analysis_user_id = user_id or analysis.user_id
                if analysis_user_id:
                    await self._invalidate_user_cache(analysis_user_id)
                    logger.debug(f"Invalidated cache for user {analysis_user_id} after status change for analysis {analysis_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating analysis status for analysis {analysis_id}: {e}")
            return False