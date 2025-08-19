"""
Celery application configuration for background task processing.

This module configures Celery for handling background jobs such as
OpenAI palm analysis processing, image processing, and other
long-running tasks that should not block HTTP requests.

Features:
- Redis as message broker and result backend
- Task routing and queue management
- Error handling and retry policies
- Task monitoring and logging
- Development and production configurations

Usage:
    # Start worker
    celery -A app.core.celery_app worker --loglevel=info
    
    # Start monitoring
    celery -A app.core.celery_app flower
"""

import os
from celery import Celery
from celery.signals import setup_logging
from app.core.config import settings
from app.core.logging import setup_logging as setup_app_logging, get_logger

logger = get_logger(__name__)

# Create Celery application
celery_app = Celery(
    "palmistry-ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"]  # Import task modules
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Task routing
    task_default_queue="default",
    task_routes={
        "app.tasks.analysis_tasks.*": {"queue": "analysis"},
        "app.tasks.image_tasks.*": {"queue": "images"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result settings
    result_expires=3600,  # 1 hour
    result_compression="gzip",
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
)

# Queue configuration
celery_app.conf.task_routes = {
    # Analysis tasks go to analysis queue
    "app.tasks.analysis_tasks.process_palm_analysis": {"queue": "analysis"},
    "app.tasks.analysis_tasks.cleanup_failed_analysis": {"queue": "analysis"},
    
    # Image processing tasks
    "app.tasks.image_tasks.generate_thumbnail": {"queue": "images"},
    "app.tasks.image_tasks.cleanup_analysis_files": {"queue": "images"},
}

# Development vs Production settings
if settings.is_development:
    celery_app.conf.update(
        # More verbose logging in development
        worker_log_level="DEBUG",
        
        # Shorter task timeouts for faster feedback
        task_soft_time_limit=60,   # 1 minute
        task_time_limit=120,       # 2 minutes
    )
else:
    celery_app.conf.update(
        # Production logging
        worker_log_level="INFO",
        
        # Longer timeouts for production workloads
        task_soft_time_limit=600,  # 10 minutes
        task_time_limit=900,       # 15 minutes
    )


@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure logging for Celery workers."""
    setup_app_logging()


# Health check task
@celery_app.task(bind=True, name="health_check")
def health_check_task(self):
    """
    Health check task for monitoring worker status.
    
    Returns:
        dict: Worker health information
    """
    return {
        "status": "healthy",
        "worker_id": self.request.id,
        "hostname": self.request.hostname,
        "queue": self.request.delivery_info.get("routing_key", "unknown"),
    }


# Test task for development
@celery_app.task(bind=True, name="test_task")
def test_task(self, message: str = "Hello from Celery!"):
    """
    Test task for verifying Celery setup.
    
    Args:
        message: Test message to return
        
    Returns:
        dict: Task result with message and worker info
    """
    logger.info("Test task executed", extra={"test_message": message, "task_id": self.request.id})
    
    return {
        "message": message,
        "task_id": self.request.id,
        "worker": self.request.hostname,
        "status": "completed"
    }


# Task monitoring
@celery_app.task(bind=True, name="monitor_queues")
def monitor_queues_task(self):
    """
    Monitor queue depths and worker health.
    
    Returns:
        dict: Queue monitoring information
    """
    try:
        # Get queue information
        inspect = celery_app.control.inspect()
        
        # Active tasks
        active_tasks = inspect.active()
        
        # Scheduled tasks
        scheduled_tasks = inspect.scheduled()
        
        # Reserved tasks
        reserved_tasks = inspect.reserved()
        
        return {
            "active_tasks": len(active_tasks) if active_tasks else 0,
            "scheduled_tasks": len(scheduled_tasks) if scheduled_tasks else 0,
            "reserved_tasks": len(reserved_tasks) if reserved_tasks else 0,
            "timestamp": self.request.id,
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error("Queue monitoring failed", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "timestamp": self.request.id
        }


if __name__ == "__main__":
    celery_app.start()