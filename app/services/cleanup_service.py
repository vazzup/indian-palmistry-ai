"""
File cleanup service for managing inactive analyses and associated files.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.analysis import Analysis
from app.services.image_service import ImageService
from app.services.openai_service import OpenAIService
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up inactive analyses and their associated files."""

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize cleanup service."""
        self.db = db
        self.image_service = ImageService()
        self.openai_service = OpenAIService()

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.db:
            return self.db
        return AsyncSessionLocal()

    async def cleanup_inactive_analyses(self, max_age_days: int = 7) -> dict:
        """Clean up inactive analyses older than max_age_days.

        Args:
            max_age_days: Maximum age in days for inactive analyses to be kept

        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

        try:
            async with await self.get_session() as db:
                # Find inactive analyses older than cutoff date
                stmt = select(Analysis).where(
                    Analysis.is_current == False,
                    Analysis.created_at < cutoff_date
                )
                result = await db.execute(stmt)
                inactive_analyses = result.scalars().all()

                if not inactive_analyses:
                    logger.info("No inactive analyses found for cleanup")
                    return {
                        "analyses_cleaned": 0,
                        "files_deleted": 0,
                        "openai_files_deleted": 0,
                        "errors": []
                    }

                stats = {
                    "analyses_cleaned": 0,
                    "files_deleted": 0,
                    "openai_files_deleted": 0,
                    "errors": []
                }

                for analysis in inactive_analyses:
                    try:
                        await self._cleanup_analysis_files(analysis, stats)

                        # Delete the analysis record (conversations will cascade)
                        await db.delete(analysis)
                        stats["analyses_cleaned"] += 1

                        logger.info(f"Cleaned up inactive analysis {analysis.id}")

                    except Exception as e:
                        error_msg = f"Error cleaning up analysis {analysis.id}: {str(e)}"
                        logger.error(error_msg)
                        stats["errors"].append(error_msg)

                # Commit all deletions
                await db.commit()

                logger.info(f"Cleanup completed: {stats}")
                return stats

        except Exception as e:
            logger.error(f"Error during cleanup operation: {e}")
            raise

    async def _cleanup_analysis_files(self, analysis: Analysis, stats: dict) -> None:
        """Clean up files associated with a single analysis.

        Args:
            analysis: Analysis object to clean up
            stats: Statistics dictionary to update
        """
        # Clean up local image files
        local_files = []
        if analysis.left_image_path:
            local_files.append(analysis.left_image_path)
        if analysis.right_image_path:
            local_files.append(analysis.right_image_path)
        if analysis.left_thumbnail_path:
            local_files.append(analysis.left_thumbnail_path)
        if analysis.right_thumbnail_path:
            local_files.append(analysis.right_thumbnail_path)

        for file_path in local_files:
            try:
                if await self.image_service.delete_local_file(file_path):
                    stats["files_deleted"] += 1
            except Exception as e:
                error_msg = f"Error deleting local file {file_path}: {str(e)}"
                logger.warning(error_msg)
                stats["errors"].append(error_msg)

        # Clean up OpenAI files
        openai_files = []
        if analysis.left_file_id:
            openai_files.append(analysis.left_file_id)
        if analysis.right_file_id:
            openai_files.append(analysis.right_file_id)

        for file_id in openai_files:
            try:
                if await self.openai_service.delete_file(file_id):
                    stats["openai_files_deleted"] += 1
            except Exception as e:
                error_msg = f"Error deleting OpenAI file {file_id}: {str(e)}"
                logger.warning(error_msg)
                stats["errors"].append(error_msg)

    async def force_cleanup_analysis(self, analysis_id: int) -> bool:
        """Force cleanup of a specific analysis regardless of age.

        Args:
            analysis_id: ID of analysis to clean up

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            async with await self.get_session() as db:
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()

                if not analysis:
                    logger.warning(f"Analysis {analysis_id} not found for cleanup")
                    return False

                if analysis.is_current:
                    logger.warning(f"Cannot cleanup current analysis {analysis_id}")
                    return False

                stats = {
                    "analyses_cleaned": 0,
                    "files_deleted": 0,
                    "openai_files_deleted": 0,
                    "errors": []
                }

                await self._cleanup_analysis_files(analysis, stats)
                await db.delete(analysis)
                await db.commit()

                logger.info(f"Force cleaned up analysis {analysis_id}: {stats}")
                return True

        except Exception as e:
            logger.error(f"Error during force cleanup of analysis {analysis_id}: {e}")
            return False

    async def get_cleanup_candidates(self, max_age_days: int = 7) -> List[Analysis]:
        """Get list of analyses that are candidates for cleanup.

        Args:
            max_age_days: Maximum age in days for inactive analyses

        Returns:
            List of Analysis objects that can be cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

        try:
            async with await self.get_session() as db:
                stmt = select(Analysis).where(
                    Analysis.is_current == False,
                    Analysis.created_at < cutoff_date
                )
                result = await db.execute(stmt)
                return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting cleanup candidates: {e}")
            return []

    async def estimate_cleanup_impact(self, max_age_days: int = 7) -> dict:
        """Estimate the impact of cleanup operation without actually performing it.

        Args:
            max_age_days: Maximum age in days for inactive analyses

        Returns:
            Dictionary with estimated cleanup statistics
        """
        candidates = await self.get_cleanup_candidates(max_age_days)

        stats = {
            "analyses_to_clean": len(candidates),
            "files_to_delete": 0,
            "openai_files_to_delete": 0,
            "oldest_analysis_date": None,
            "newest_analysis_date": None
        }

        if candidates:
            # Count files
            for analysis in candidates:
                # Count local files
                local_files = [
                    analysis.left_image_path,
                    analysis.right_image_path,
                    analysis.left_thumbnail_path,
                    analysis.right_thumbnail_path
                ]
                stats["files_to_delete"] += sum(1 for f in local_files if f)

                # Count OpenAI files
                openai_files = [analysis.left_file_id, analysis.right_file_id]
                stats["openai_files_to_delete"] += sum(1 for f in openai_files if f)

            # Find date range
            dates = [analysis.created_at for analysis in candidates]
            stats["oldest_analysis_date"] = min(dates).isoformat()
            stats["newest_analysis_date"] = max(dates).isoformat()

        return stats