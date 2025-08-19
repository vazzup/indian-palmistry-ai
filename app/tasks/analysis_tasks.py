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
from typing import Dict, Any
from celery import current_task
from celery.exceptions import Retry

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.core.redis import redis_service

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
        asyncio.run(redis_service.set(
            f"job_status:{task_id}",
            {
                "status": "processing",
                "progress": 10,
                "analysis_id": analysis_id,
                "started_at": self.request.eta or "now"
            },
            expire_seconds=3600
        ))
        
        logger.info(
            "Starting palm analysis processing",
            analysis_id=analysis_id,
            task_id=task_id,
            retry_count=self.request.retries
        )
        
        # TODO: In Phase 2, this will:
        # 1. Load analysis record from database
        # 2. Load image files from storage
        # 3. Call OpenAI API for analysis
        # 4. Save results back to database
        
        # For Phase 1, simulate processing
        import time
        time.sleep(2)  # Simulate processing time
        
        # Update progress
        asyncio.run(redis_service.set(
            f"job_status:{task_id}",
            {
                "status": "completed",
                "progress": 100,
                "analysis_id": analysis_id,
                "completed_at": "now",
                "result": {
                    "summary": "Phase 1 test analysis completed",
                    "status": "success"
                }
            },
            expire_seconds=3600
        ))
        
        logger.info(
            "Palm analysis processing completed",
            analysis_id=analysis_id,
            task_id=task_id
        )
        
        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "task_id": task_id,
            "result": "Analysis completed successfully (Phase 1 stub)"
        }
        
    except Exception as exc:
        logger.error(
            "Palm analysis processing failed",
            analysis_id=analysis_id,
            task_id=task_id,
            error=str(exc),
            retry_count=self.request.retries,
            exc_info=True
        )
        
        # Update job status with error
        asyncio.run(redis_service.set(
            f"job_status:{task_id}",
            {
                "status": "failed",
                "progress": 0,
                "analysis_id": analysis_id,
                "error": str(exc),
                "failed_at": "now"
            },
            expire_seconds=3600
        ))
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(
                "Retrying palm analysis processing",
                analysis_id=analysis_id,
                task_id=task_id,
                retry_count=self.request.retries + 1,
                max_retries=self.max_retries
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