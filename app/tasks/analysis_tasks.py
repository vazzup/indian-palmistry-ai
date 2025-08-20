"""
Background tasks for palm analysis processing.

This module contains Celery tasks for handling OpenAI palm analysis
requests that need to be processed asynchronously to avoid request
timeouts and provide better user experience.

Tasks:
- process_palm_analysis: Main analysis processing task
- cleanup_failed_analysis: Cleanup after failed analysis
- retry_failed_analysis: Retry mechanism for failed analyses

Usage:
    from app.tasks.analysis_tasks import process_palm_analysis
    
    job = process_palm_analysis.delay(analysis_id)
    result = job.get()
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from celery import current_task
from celery.exceptions import Retry
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.core.redis import redis_service
from app.core.database import AsyncSessionLocal
from app.models.analysis import Analysis, AnalysisStatus
from app.services.openai_service import OpenAIService
from app.services.image_service import ImageService

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_palm_analysis(self, analysis_id: int) -> Dict[str, Any]:
    """
    Process palm analysis using OpenAI in background.
    
    This task handles the full palm analysis workflow:
    1. Load analysis record and images
    2. Call OpenAI API for analysis
    3. Update analysis record with results
    4. Update job status in Redis
    
    Args:
        analysis_id: ID of the analysis to process
        
    Returns:
        dict: Task result with status and analysis data
        
    Raises:
        Retry: If task should be retried due to temporary failure
    """
    task_id = self.request.id
    
    try:
        # Update job status to processing
        async def _update_analysis_status():
            async with AsyncSessionLocal() as db:
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    raise ValueError(f"Analysis {analysis_id} not found")
                
                analysis.status = AnalysisStatus.PROCESSING
                analysis.job_id = task_id
                analysis.processing_started_at = datetime.utcnow()
                await db.commit()
                return analysis
        
        analysis = asyncio.run(_update_analysis_status())
        
        # Update Redis job status
        asyncio.run(redis_service.set(
            f"job_status:{task_id}",
            {
                "status": "processing",
                "progress": 20,
                "analysis_id": analysis_id,
                "started_at": datetime.utcnow().isoformat()
            },
            expire_seconds=3600
        ))
        
        logger.info(
            f"Starting palm analysis processing for analysis {analysis_id}, "
            f"task {task_id}, retry {self.request.retries}"
        )
        
        # Initialize services
        openai_service = OpenAIService()
        
        # Process palm analysis with OpenAI
        try:
            result = asyncio.run(openai_service.analyze_palm_images(
                left_image_path=analysis.left_image_path,
                right_image_path=analysis.right_image_path
            ))
            
            # Update progress
            asyncio.run(redis_service.set(
                f"job_status:{task_id}",
                {
                    "status": "processing", 
                    "progress": 80,
                    "analysis_id": analysis_id,
                    "message": "Processing OpenAI response"
                },
                expire_seconds=3600
            ))
            
            # Save results to database
            async def _save_results():
                async with AsyncSessionLocal() as db:
                    stmt = select(Analysis).where(Analysis.id == analysis_id)
                    db_result = await db.execute(stmt)
                    analysis_record = db_result.scalar_one_or_none()
                    
                    if analysis_record:
                        analysis_record.summary = result["summary"]
                        analysis_record.full_report = result["full_report"]
                        analysis_record.status = AnalysisStatus.COMPLETED
                        analysis_record.processing_completed_at = datetime.utcnow()
                        analysis_record.tokens_used = result.get("tokens_used", 0)
                        analysis_record.cost = result.get("cost", 0.0)
                        await db.commit()
            
            asyncio.run(_save_results())
            
            # Update final status
            asyncio.run(redis_service.set(
                f"job_status:{task_id}",
                {
                    "status": "completed",
                    "progress": 100,
                    "analysis_id": analysis_id,
                    "completed_at": datetime.utcnow().isoformat(),
                    "tokens_used": result.get("tokens_used", 0),
                    "cost": result.get("cost", 0.0)
                },
                expire_seconds=3600
            ))
            
            logger.info(
                f"Palm analysis processing completed successfully for analysis {analysis_id}, "
                f"task {task_id}, tokens used: {result.get('tokens_used', 0)}"
            )
            
            # Queue thumbnail generation if images exist
            if analysis.left_image_path or analysis.right_image_path:
                generate_thumbnails.delay(analysis_id)
            
            return {
                "status": "completed",
                "analysis_id": analysis_id,
                "task_id": task_id,
                "summary": result["summary"],
                "tokens_used": result.get("tokens_used", 0),
                "cost": result.get("cost", 0.0)
            }
            
        except Exception as openai_error:
            logger.error(
                f"OpenAI analysis failed for analysis {analysis_id}, task {task_id}: {openai_error}"
            )
            raise openai_error
        
    except Exception as exc:
        logger.error(
            f"Palm analysis processing failed for analysis {analysis_id}, task {task_id}: {exc}, "
            f"retry {self.request.retries}",
            exc_info=True
        )
        
        # Update analysis status in database
        async def _update_failed_analysis():
            try:
                async with AsyncSessionLocal() as db:
                    stmt = select(Analysis).where(Analysis.id == analysis_id)
                    result = await db.execute(stmt)
                    analysis = result.scalar_one_or_none()
                    
                    if analysis:
                        analysis.status = AnalysisStatus.FAILED
                        analysis.error_message = str(exc)
                        await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update analysis status in database: {db_error}")
        
        asyncio.run(_update_failed_analysis())
        
        # Update job status with error
        asyncio.run(redis_service.set(
            f"job_status:{task_id}",
            {
                "status": "failed",
                "progress": 0,
                "analysis_id": analysis_id,
                "error": str(exc),
                "failed_at": datetime.utcnow().isoformat()
            },
            expire_seconds=3600
        ))
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying palm analysis processing for analysis {analysis_id}, task {task_id}, "
                f"retry {self.request.retries + 1}/{self.max_retries}"
            )
            
            # Exponential backoff: 60s, 120s, 240s
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        # Max retries exceeded, mark as permanently failed
        logger.error(
            "Palm analysis processing permanently failed",
            analysis_id=analysis_id,
            task_id=task_id,
            max_retries=self.max_retries
        )
        
        return {
            "status": "failed",
            "analysis_id": analysis_id,
            "task_id": task_id,
            "error": str(exc),
            "retries_exhausted": True
        }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_thumbnails(self, analysis_id: int) -> Dict[str, Any]:
    """
    Generate thumbnails for palm images in background.
    
    Args:
        analysis_id: ID of the analysis to generate thumbnails for
        
    Returns:
        dict: Task result with status and thumbnail paths
    """
    task_id = self.request.id
    
    try:
        logger.info(
            "Starting thumbnail generation",
            analysis_id=analysis_id,
            task_id=task_id
        )
        
        # Load analysis record
        async def _load_analysis():
            async with AsyncSessionLocal() as db:
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                result = await db.execute(stmt)
                return result.scalar_one_or_none()
        
        analysis = asyncio.run(_load_analysis())
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        
        # Initialize image service
        image_service = ImageService()
        
        # Generate thumbnails
        thumbnail_paths = []
        
        if analysis.left_image_path:
            try:
                left_thumb = image_service.generate_thumbnail(analysis.left_image_path)
                if left_thumb:
                    analysis.left_thumbnail_path = left_thumb
                    thumbnail_paths.append(left_thumb)
            except Exception as e:
                logger.warning(f"Failed to generate left thumbnail: {e}")
        
        if analysis.right_image_path:
            try:
                right_thumb = image_service.generate_thumbnail(analysis.right_image_path)
                if right_thumb:
                    analysis.right_thumbnail_path = right_thumb
                    thumbnail_paths.append(right_thumb)
            except Exception as e:
                logger.warning(f"Failed to generate right thumbnail: {e}")
        
        # Save thumbnail paths to database
        if thumbnail_paths:
            async def _save_thumbnails():
                async with AsyncSessionLocal() as db:
                    stmt = select(Analysis).where(Analysis.id == analysis_id)
                    result = await db.execute(stmt)
                    db_analysis = result.scalar_one_or_none()
                    
                    if db_analysis:
                        if analysis.left_thumbnail_path:
                            db_analysis.left_thumbnail_path = analysis.left_thumbnail_path
                        if analysis.right_thumbnail_path:
                            db_analysis.right_thumbnail_path = analysis.right_thumbnail_path
                        await db.commit()
            
            asyncio.run(_save_thumbnails())
        
        logger.info(
            "Thumbnail generation completed",
            analysis_id=analysis_id,
            task_id=task_id,
            thumbnail_count=len(thumbnail_paths)
        )
        
        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "task_id": task_id,
            "thumbnails_generated": len(thumbnail_paths),
            "thumbnail_paths": thumbnail_paths
        }
        
    except Exception as exc:
        logger.error(
            "Thumbnail generation failed",
            analysis_id=analysis_id,
            task_id=task_id,
            error=str(exc),
            retry_count=self.request.retries,
            exc_info=True
        )
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            countdown = 30 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        return {
            "status": "failed",
            "analysis_id": analysis_id,
            "task_id": task_id,
            "error": str(exc)
        }


@celery_app.task(bind=True)
def cleanup_failed_analysis(self, analysis_id: int, task_id: str) -> Dict[str, Any]:
    """
    Clean up resources after a failed analysis.
    
    Args:
        analysis_id: ID of the failed analysis
        task_id: ID of the failed task
        
    Returns:
        dict: Cleanup result
    """
    try:
        logger.info(
            "Starting cleanup for failed analysis",
            analysis_id=analysis_id,
            original_task_id=task_id
        )
        
        # TODO: In Phase 2, this will:
        # 1. Clean up uploaded image files
        # 2. Update analysis record status
        # 3. Send notification to user (if applicable)
        
        # Update job status to indicate cleanup completed
        asyncio.run(redis_service.set(
            f"job_status:{task_id}",
            {
                "status": "cleanup_completed",
                "analysis_id": analysis_id,
                "cleaned_up_at": "now"
            },
            expire_seconds=1800  # Keep for 30 minutes
        ))
        
        logger.info(
            "Cleanup completed for failed analysis",
            analysis_id=analysis_id,
            original_task_id=task_id
        )
        
        return {
            "status": "cleanup_completed",
            "analysis_id": analysis_id,
            "original_task_id": task_id
        }
        
    except Exception as exc:
        logger.error(
            "Cleanup failed for analysis",
            analysis_id=analysis_id,
            original_task_id=task_id,
            error=str(exc),
            exc_info=True
        )
        
        return {
            "status": "cleanup_failed",
            "analysis_id": analysis_id,
            "original_task_id": task_id,
            "error": str(exc)
        }


@celery_app.task(bind=True, max_retries=1)
def get_job_status(self, job_id: str) -> Dict[str, Any]:
    """
    Get the current status of a background job.
    
    Args:
        job_id: ID of the job to check
        
    Returns:
        dict: Job status information
    """
    try:
        status = asyncio.run(redis_service.get(f"job_status:{job_id}"))
        
        if status is None:
            return {
                "status": "not_found",
                "job_id": job_id,
                "message": "Job status not found"
            }
        
        return {
            "job_id": job_id,
            **status
        }
        
    except Exception as exc:
        logger.error(
            "Failed to get job status",
            job_id=job_id,
            error=str(exc)
        )
        
        return {
            "status": "error",
            "job_id": job_id,
            "error": str(exc)
        }