"""
Background task modules for Celery workers.

This package contains task definitions for:
- Palm analysis processing
- Image processing and thumbnails
- File cleanup and maintenance
- Health monitoring
"""

# Import all tasks to ensure they're registered with Celery
from app.tasks.analysis_tasks import process_palm_analysis, generate_thumbnails, cleanup_failed_analysis, get_job_status

__all__ = [
    "process_palm_analysis",
    "generate_thumbnails", 
    "cleanup_failed_analysis",
    "get_job_status"
]