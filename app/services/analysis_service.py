"""
Analysis service for managing palm reading analyses.
"""

import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import UploadFile
from app.models.analysis import Analysis, AnalysisStatus
from app.models.conversation import Conversation
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
        right_image: Optional[UploadFile] = None
    ) -> Analysis:
        """Create a new palm analysis.
        
        Args:
            user_id: User ID (None for anonymous)
            left_image: Left palm image file
            right_image: Right palm image file
            
        Returns:
            Created Analysis instance
        """
        try:
            # Validate quota first
            self.image_service.validate_quota(user_id)
            
            async with await self.get_session() as db:
                # For authenticated users: mark previous analysis as inactive (single reading approach)
                if user_id:
                    await self._mark_previous_analyses_inactive(db, user_id)

                # Create analysis record
                analysis = Analysis(
                    user_id=user_id,
                    status=AnalysisStatus.QUEUED,
                    is_current=True
                )
                
                db.add(analysis)
                await db.commit()
                await db.refresh(analysis)
                
                logger.info(f"Created analysis {analysis.id} for user {user_id}")
                
                # Save images if provided
                if left_image:
                    left_path, left_file_id = await self.image_service.save_image(
                        left_image, user_id, analysis.id, "left"
                    )
                    analysis.left_image_path = left_path
                    analysis.left_file_id = left_file_id
                
                if right_image:
                    right_path, right_file_id = await self.image_service.save_image(
                        right_image, user_id, analysis.id, "right"
                    )
                    analysis.right_image_path = right_path
                    analysis.right_file_id = right_file_id
                
                # Update with image paths
                await db.commit()
                await db.refresh(analysis)
                
                logger.info(f"Saved images for analysis {analysis.id}")
                
                # Queue background processing job
                from app.tasks.analysis_tasks import process_palm_analysis
                job = process_palm_analysis.delay(analysis.id)
                analysis.job_id = job.id
                await db.commit()
                await db.refresh(analysis)
                
                logger.info(f"Queued analysis job {job.id} for analysis {analysis.id}")
                
                # Invalidate user cache to ensure dashboard shows new analysis immediately
                if user_id:
                    await self._invalidate_user_cache(user_id)
                    logger.debug(f"Invalidated cache for user {user_id} after creating analysis {analysis.id}")
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            # Clean up images if analysis creation failed
            if 'analysis' in locals():
                await self.image_service.delete_analysis_images(
                    analysis.left_image_path, analysis.right_image_path,
                    analysis.left_file_id, analysis.right_file_id
                )
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
    
    async def get_analysis_with_conversation_mode(
        self, 
        analysis_id: int, 
        user_id: Optional[int] = None
    ) -> Tuple[Optional[Analysis], Optional[Conversation]]:
        """Get analysis and determine conversation mode based on existing conversation.
        
        Args:
            analysis_id: Analysis ID
            user_id: User ID for access control (None for anonymous access)
            
        Returns:
            Tuple of (Analysis, Conversation) where Conversation is None if no conversation exists
        """
        try:
            async with await self.get_session() as db:
                # Get analysis
                analysis_stmt = select(Analysis).where(Analysis.id == analysis_id)
                
                # Add user access control if user_id provided
                if user_id is not None:
                    analysis_stmt = analysis_stmt.where(Analysis.user_id == user_id)
                
                analysis_result = await db.execute(analysis_stmt)
                analysis = analysis_result.scalar_one_or_none()
                
                if not analysis:
                    return None, None
                
                # Get conversation if exists
                conversation_stmt = select(Conversation).where(Conversation.analysis_id == analysis_id)
                conversation_result = await db.execute(conversation_stmt)
                conversation = conversation_result.scalar_one_or_none()
                
                return analysis, conversation
                
        except Exception as e:
            logger.error(f"Error getting analysis with conversation mode {analysis_id}: {e}")
            return None, None
    
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
                await self.image_service.delete_analysis_images(
                    analysis.left_image_path, analysis.right_image_path,
                    analysis.left_file_id, analysis.right_file_id
                )
                
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
    
    async def associate_analysis(self, analysis_id: int, user_id: int) -> bool:
        """Associate an anonymous analysis with a user.

        This method allows authenticated users to claim ownership of an anonymous analysis
        that was created before they logged in. The analysis must have user_id = null to be
        associable.

        In the single reading model, this will mark any previous current analysis for this
        user as inactive before associating the new analysis.

        Args:
            analysis_id: Analysis ID to associate
            user_id: User ID to associate the analysis with

        Returns:
            True if association was successful, False otherwise
        """
        try:
            async with await self.get_session() as db:
                # Get the analysis
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()

                if not analysis:
                    logger.warning(f"Analysis {analysis_id} not found for association")
                    return False

                # Check if analysis is anonymous (user_id is null)
                if analysis.user_id is not None:
                    # If already associated with THIS user, return success (idempotent)
                    if analysis.user_id == user_id:
                        logger.info(f"Analysis {analysis_id} already associated with user {user_id} (idempotent)")
                        return True
                    # If associated with a DIFFERENT user, return failure
                    logger.warning(f"Analysis {analysis_id} is already associated with different user {analysis.user_id}")
                    return False

                # Mark previous current analyses as inactive (single reading model)
                await self._mark_previous_analyses_inactive(db, user_id)

                # Associate the analysis with the user and mark as current
                analysis.user_id = user_id
                analysis.is_current = True
                await db.commit()

                # Invalidate user cache to ensure dashboard shows new analysis immediately
                await self._invalidate_user_cache(user_id)
                logger.debug(f"Invalidated cache for user {user_id} after associating analysis {analysis_id}")

                logger.info(f"Successfully associated analysis {analysis_id} with user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Error associating analysis {analysis_id} with user {user_id}: {e}")
            return False

    async def get_current_analysis(self, user_id: int) -> Optional[Analysis]:
        """Get the current active analysis for a user.

        Args:
            user_id: User ID

        Returns:
            Current Analysis instance if found, None otherwise
        """
        logger.info(f"[DEBUG] AnalysisService.get_current_analysis called for user {user_id}")
        try:
            logger.info(f"[DEBUG] Getting database session")
            async with await self.get_session() as db:
                logger.info(f"[DEBUG] Building query for current analysis")
                stmt = select(Analysis).where(
                    Analysis.user_id == user_id,
                    Analysis.is_current == True
                )
                logger.info(f"[DEBUG] Executing query: {stmt}")
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()
                logger.info(f"[DEBUG] Query result: {analysis}")

                return analysis

        except Exception as e:
            logger.error(f"[DEBUG] Exception in get_current_analysis: {type(e).__name__}: {e}")
            logger.error(f"Error getting current analysis for user {user_id}: {e}")
            return None

    async def _mark_previous_analyses_inactive(self, db: AsyncSession, user_id: int) -> None:
        """Mark all previous analyses for a user as inactive.

        This supports the single reading model by ensuring only one analysis
        is current at a time. Also handles cleanup of conversations and files.

        Args:
            db: Database session
            user_id: User ID
        """
        try:
            # Get all current analyses for the user
            stmt = select(Analysis).where(
                Analysis.user_id == user_id,
                Analysis.is_current == True
            )
            result = await db.execute(stmt)
            previous_analyses = result.scalars().all()

            for analysis in previous_analyses:
                # Mark as inactive
                analysis.is_current = False

                # Schedule file cleanup (OpenAI files and local images)
                # Note: Files will be cleaned up by the scheduled cleanup job after 7 days
                logger.info(f"Marked analysis {analysis.id} as inactive for cleanup")

            if previous_analyses:
                await db.commit()
                logger.info(f"Marked {len(previous_analyses)} previous analyses as inactive for user {user_id}")

        except Exception as e:
            logger.error(f"Error marking previous analyses inactive for user {user_id}: {e}")
            raise

    async def get_conversation_count_for_analysis(self, analysis_id: int) -> int:
        """Get the number of conversations for an analysis.

        Args:
            analysis_id: Analysis ID

        Returns:
            Number of conversations
        """
        logger.info(f"[DEBUG] AnalysisService.get_conversation_count_for_analysis called for analysis {analysis_id}")
        try:
            logger.info(f"[DEBUG] Getting database session for conversation count")
            async with await self.get_session() as db:
                logger.info(f"[DEBUG] Importing Conversation model")
                from app.models.conversation import Conversation
                logger.info(f"[DEBUG] Building conversation count query")
                stmt = select(Conversation).where(Conversation.analysis_id == analysis_id)
                logger.info(f"[DEBUG] Executing conversation count query: {stmt}")
                result = await db.execute(stmt)
                conversations = result.scalars().all()
                count = len(conversations)
                logger.info(f"[DEBUG] Found {count} conversations for analysis {analysis_id}")

                return count

        except Exception as e:
            logger.error(f"[DEBUG] Exception in get_conversation_count_for_analysis: {type(e).__name__}: {e}")
            logger.error(f"Error getting conversation count for analysis {analysis_id}: {e}")
            return 0