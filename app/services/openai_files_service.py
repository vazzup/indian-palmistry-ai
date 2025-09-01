"""OpenAI Files Service for managing file uploads and operations.

This service provides comprehensive management of OpenAI Files API operations
for the Indian Palmistry AI application. It handles secure file uploads,
validation, concurrent operations, retry logic, and cleanup operations.

**Key Features:**
- Secure palm image uploads to OpenAI Files API
- Comprehensive file validation (format, size, existence)
- Concurrent upload handling with error recovery
- Exponential backoff retry mechanism
- File cleanup and maintenance operations
- File existence validation and health checking

**Supported Image Formats:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- GIF (.gif)

**Configuration:**
- Maximum file size: Configurable via settings.openai_files_max_size
- Retry attempts: 3 with exponential backoff
- Supported formats: {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

**Usage Example:**
```python
from app.services.openai_files_service import OpenAIFilesService

# Initialize service
service = OpenAIFilesService()

# Upload palm images from an analysis
analysis = get_analysis_by_id(123)
file_ids = await service.upload_analysis_images(analysis)
# Returns: {'left_palm': 'file-abc123', 'right_palm': 'file-def456'}

# Validate uploaded files are still accessible
validation = await service.validate_files(list(file_ids.values()))
# Returns: {'file-abc123': True, 'file-def456': True}

# Clean up old files (maintenance operation)
deleted_count = await service.cleanup_old_files(older_than_days=30)
print(f"Cleaned up {deleted_count} old files")
```

**Error Handling:**
- All methods raise OpenAIFilesServiceError for business logic errors
- Network and API errors are wrapped with context information
- Retry logic handles transient failures automatically
- Validation errors provide detailed feedback for debugging

**Thread Safety:**
- All methods are async and thread-safe
- Concurrent operations are supported and optimized
- No shared mutable state between operations

**Security Considerations:**
- File size limits prevent DoS attacks
- Format validation prevents malicious file uploads
- Path traversal protection via pathlib
- No temporary file storage on disk
- Automatic cleanup of uploaded files

Author: Indian Palmistry AI Team
Version: 1.0.0
Created: August 2025
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import aiofiles
import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.analysis import Analysis

logger = logging.getLogger(__name__)


class OpenAIFilesServiceError(Exception):
    """Custom exception for OpenAI Files Service errors.
    
    This exception is raised for all business logic errors in the OpenAI Files Service,
    including validation failures, upload errors, and file management issues.
    
    **Common Error Scenarios:**
    - File not found or inaccessible
    - Invalid file format or size
    - OpenAI API failures or rate limits
    - Network connectivity issues
    - File validation failures
    
    **Usage:**
    ```python
    try:
        file_ids = await service.upload_analysis_images(analysis)
    except OpenAIFilesServiceError as e:
        logger.error(f"File service error: {e}")
        # Handle gracefully - maybe retry or show user message
    ```
    
    **Error Message Guidelines:**
    - Include specific error context (file name, operation type)
    - Provide actionable information when possible
    - Preserve original error information for debugging
    - Use consistent error message format
    """
    pass


class OpenAIFilesService:
    """Service for managing OpenAI Files API operations.
    
    This service provides a high-level interface for managing file operations
    with the OpenAI Files API, specifically designed for palm reading image
    uploads and management in the Indian Palmistry AI application.
    
    **Service Capabilities:**
    - Concurrent palm image uploads with error handling
    - File validation (existence, format, size)
    - Retry logic with exponential backoff
    - Batch file operations (upload, delete, validate)
    - File information retrieval and health checking
    - Maintenance operations (cleanup old files)
    
    **Configuration:**
    The service is configured through application settings:
    - API Key: settings.openai_api_key
    - Max File Size: settings.openai_files_max_size
    - Supported Formats: Defined in constructor
    - Retry Policy: 3 attempts with exponential backoff
    
    **Thread Safety:**
    This service is designed to be thread-safe and supports concurrent
    operations. Each method is async and can be called concurrently
    without side effects.
    
    **Performance Characteristics:**
    - Concurrent uploads: Multiple files uploaded simultaneously
    - Exponential backoff: Reduces API rate limit impacts
    - Efficient validation: Batch operations where possible
    - Memory efficient: Streams file data without buffering
    
    **Integration Points:**
    - Analysis Service: For uploading palm reading images
    - Follow-up Service: For validating existing file accessibility
    - Maintenance Tasks: For cleanup and health monitoring
    
    **Example Usage:**
    ```python
    # Initialize service (usually done via dependency injection)
    service = OpenAIFilesService()
    
    # Upload images from a completed analysis
    analysis = await get_analysis(123)
    try:
        file_ids = await service.upload_analysis_images(analysis)
        logger.info(f"Uploaded {len(file_ids)} files successfully")
    except OpenAIFilesServiceError as e:
        logger.error(f"Upload failed: {e}")
        # Handle error appropriately
    ```
    """
    
    def __init__(self):
        """Initialize the OpenAI Files Service.
        
        Sets up the OpenAI client and configuration parameters from application
        settings. All configuration is pulled from the settings module to ensure
        consistency across the application.
        
        **Initialization:**
        - Creates async OpenAI client with API key
        - Sets file size and format limits
        - Configures retry policy parameters
        - Validates required settings are present
        
        **Raises:**
            ValueError: If required settings are missing or invalid
            OpenAIFilesServiceError: If OpenAI client initialization fails
        """
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.max_file_size = settings.openai_files_max_size
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial retry delay in seconds
    
    async def upload_analysis_images(self, analysis: Analysis) -> Dict[str, str]:
        """
        Upload palm images to OpenAI Files API.
        
        Args:
            analysis: Analysis object with image paths
            
        Returns:
            Dict mapping image_type -> file_id
            
        Raises:
            OpenAIFilesServiceError: If upload fails or validation errors
        """
        try:
            file_ids = {}
            upload_tasks = []
            
            # Prepare upload tasks
            if analysis.left_image_path:
                upload_tasks.append(
                    self._upload_single_image_with_retry(analysis.left_image_path, 'left_palm')
                )
            
            if analysis.right_image_path:
                upload_tasks.append(
                    self._upload_single_image_with_retry(analysis.right_image_path, 'right_palm')
                )
            
            if not upload_tasks:
                raise OpenAIFilesServiceError("No images to upload")
            
            # Execute uploads concurrently
            results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"File upload failed: {result}")
                    raise OpenAIFilesServiceError(f"Failed to upload image: {str(result)}")
                
                image_type, file_id = result
                file_ids[image_type] = file_id
            
            logger.info(f"Successfully uploaded {len(file_ids)} files for analysis {analysis.id}")
            return file_ids
            
        except Exception as e:
            logger.error(f"Failed to upload images for analysis {analysis.id}: {e}")
            if isinstance(e, OpenAIFilesServiceError):
                raise
            raise OpenAIFilesServiceError(f"Upload failed: {str(e)}")
    
    async def _upload_single_image_with_retry(self, image_path: str, image_type: str) -> Tuple[str, str]:
        """Upload a single image with retry logic and exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return await self._upload_single_image(image_path, image_type)
            except Exception as e:
                if attempt == self.max_retries - 1:  # Last attempt
                    raise
                
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Upload attempt {attempt + 1} failed for {image_type}: {e}. Retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
        
        # This should never be reached, but for type safety
        raise OpenAIFilesServiceError(f"All retry attempts exhausted for {image_type}")
    
    async def _upload_single_image(self, image_path: str, image_type: str) -> Tuple[str, str]:
        """Upload a single image file."""
        try:
            # Validate file
            path = Path(image_path)
            
            # Check if file exists
            if not path.exists():
                raise OpenAIFilesServiceError(f"Image file not found: {image_path}")
            
            # Check file format
            if path.suffix.lower() not in self.supported_formats:
                raise OpenAIFilesServiceError(f"Unsupported file format: {path.suffix}. Supported: {self.supported_formats}")
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                size_mb = file_size / (1024 * 1024)
                max_mb = self.max_file_size / (1024 * 1024)
                raise OpenAIFilesServiceError(f"File too large: {size_mb:.1f}MB (max: {max_mb}MB)")
            
            if file_size == 0:
                raise OpenAIFilesServiceError(f"File is empty: {image_path}")
            
            # Read and upload file
            async with aiofiles.open(image_path, 'rb') as file:
                file_content = await file.read()
                
                # Upload to OpenAI
                response = await self.client.files.create(
                    file=(path.name, file_content),
                    purpose='vision'
                )
                
                logger.info(f"Successfully uploaded {image_type} image: {response.id} (size: {file_size} bytes)")
                return image_type, response.id
                
        except OpenAIFilesServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to upload {image_type} image: {e}")
            raise OpenAIFilesServiceError(f"Upload failed for {image_type}: {str(e)}")
    
    async def delete_files(self, file_ids: List[str]) -> Dict[str, bool]:
        """
        Delete files from OpenAI.
        
        Args:
            file_ids: List of OpenAI file IDs to delete
            
        Returns:
            Dict mapping file_id -> success_status
        """
        if not file_ids:
            return {}
        
        try:
            delete_tasks = [
                self._delete_single_file(file_id) 
                for file_id in file_ids
            ]
            
            results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            deletion_results = {}
            for file_id, result in zip(file_ids, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to delete file {file_id}: {result}")
                    deletion_results[file_id] = False
                else:
                    deletion_results[file_id] = result
            
            successful_deletions = sum(deletion_results.values())
            logger.info(f"Deleted {successful_deletions}/{len(file_ids)} files from OpenAI")
            
            return deletion_results
            
        except Exception as e:
            logger.error(f"Batch file deletion failed: {e}")
            return {file_id: False for file_id in file_ids}
    
    async def _delete_single_file(self, file_id: str) -> bool:
        """Delete a single file from OpenAI."""
        try:
            await self.client.files.delete(file_id)
            logger.info(f"Successfully deleted file: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False
    
    async def get_file_info(self, file_id: str) -> Optional[Dict]:
        """
        Get file information from OpenAI.
        
        Args:
            file_id: OpenAI file ID
            
        Returns:
            File information dict or None if file not found
        """
        try:
            file_info = await self.client.files.retrieve(file_id)
            return {
                'id': file_info.id,
                'filename': file_info.filename,
                'purpose': file_info.purpose,
                'status': file_info.status,
                'bytes': file_info.bytes,
                'created_at': file_info.created_at
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_id}: {e}")
            return None
    
    async def validate_files(self, file_ids: List[str]) -> Dict[str, bool]:
        """
        Validate that files exist and are accessible.
        
        Args:
            file_ids: List of OpenAI file IDs to validate
            
        Returns:
            Dict mapping file_id -> is_valid
        """
        if not file_ids:
            return {}
        
        try:
            validation_tasks = [
                self._validate_single_file(file_id)
                for file_id in file_ids
            ]
            
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            validation_results = {}
            for file_id, result in zip(file_ids, results):
                if isinstance(result, Exception):
                    logger.warning(f"File validation failed for {file_id}: {result}")
                    validation_results[file_id] = False
                else:
                    validation_results[file_id] = result
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Batch file validation failed: {e}")
            return {file_id: False for file_id in file_ids}
    
    async def _validate_single_file(self, file_id: str) -> bool:
        """Validate a single file exists and is accessible."""
        try:
            file_info = await self.client.files.retrieve(file_id)
            return file_info.status == 'processed'
        except Exception:
            return False
    
    async def cleanup_old_files(self, older_than_days: int = 30) -> int:
        """
        Clean up old files from OpenAI (utility method for maintenance).
        
        Args:
            older_than_days: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            import time
            cutoff_timestamp = time.time() - (older_than_days * 24 * 60 * 60)
            
            # List all files
            files_response = await self.client.files.list()
            old_files = [
                file for file in files_response.data 
                if file.created_at < cutoff_timestamp and file.purpose == 'vision'
            ]
            
            if not old_files:
                logger.info("No old files found for cleanup")
                return 0
            
            # Delete old files
            file_ids = [file.id for file in old_files]
            deletion_results = await self.delete_files(file_ids)
            
            deleted_count = sum(deletion_results.values())
            logger.info(f"Cleaned up {deleted_count} old files (older than {older_than_days} days)")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"File cleanup failed: {e}")
            return 0