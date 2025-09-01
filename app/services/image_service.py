"""
Image service for handling palm image uploads, validation, and processing.
"""

import os
import logging
from typing import Optional, Tuple
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

# Allowed image types and their magic bytes
ALLOWED_MIME_TYPES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
}

# Maximum file size (15 MB)
MAX_FILE_SIZE = 15 * 1024 * 1024

# Thumbnail size
THUMBNAIL_SIZE = (300, 300)


class ImageService:
    """Service for image upload, validation, and processing."""
    
    def __init__(self):
        """Initialize image service."""
        self.storage_root = Path(settings.file_storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
    
    def validate_image_file(self, file: UploadFile) -> None:
        """Validate uploaded image file.
        
        Args:
            file: Uploaded file to validate
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB"
            )
        
        # Check content type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG and PNG images are allowed"
            )
        
        # Read first few bytes to check magic bytes
        file.file.seek(0)
        header = file.file.read(10)
        file.file.seek(0)
        
        # Validate magic bytes
        valid_magic = False
        for mime_type, magic_bytes_list in ALLOWED_MIME_TYPES.items():
            if file.content_type == mime_type:
                for magic_bytes in magic_bytes_list:
                    if header.startswith(magic_bytes):
                        valid_magic = True
                        break
                break
        
        if not valid_magic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. File content does not match declared type"
            )
    
    def get_image_paths(self, user_id: Optional[int], analysis_id: int) -> Tuple[Path, Path]:
        """Get directory paths for storing images and thumbnails.
        
        Args:
            user_id: User ID (None for anonymous)
            analysis_id: Analysis ID
            
        Returns:
            Tuple of (images_dir, thumbnails_dir)
        """
        user_folder = f"user_{user_id}" if user_id else "anonymous"
        analysis_folder = f"analysis_{analysis_id}"
        
        images_dir = self.storage_root / user_folder / analysis_folder / "images"
        thumbnails_dir = self.storage_root / user_folder / analysis_folder / "thumbnails"
        
        # Create directories
        images_dir.mkdir(parents=True, exist_ok=True)
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        return images_dir, thumbnails_dir
    
    async def save_image(
        self, 
        file: UploadFile, 
        user_id: Optional[int], 
        analysis_id: int, 
        palm_type: str
    ) -> Tuple[str, Optional[str]]:
        """Save uploaded image.
        
        Args:
            file: Uploaded image file
            user_id: User ID (None for anonymous)
            analysis_id: Analysis ID
            palm_type: "left" or "right"
            
        Returns:
            Tuple of (image_path, thumbnail_path) relative to storage root
            For now, thumbnail_path is None as we'll implement thumbnails in background
        """
        # Validate file
        self.validate_image_file(file)
        
        # Get storage directories
        images_dir, thumbnails_dir = self.get_image_paths(user_id, analysis_id)
        
        # Determine file extension
        extension = ".jpg" if file.content_type == "image/jpeg" else ".png"
        filename = f"{palm_type}_palm{extension}"
        
        # Save original image
        image_path = images_dir / filename
        
        try:
            # Read and save original file
            file.file.seek(0)
            content = await file.read()
            
            with open(image_path, "wb") as f:
                f.write(content)
            
            logger.info(f"Saved {palm_type} palm image for analysis {analysis_id}")
            
            # Return relative paths
            relative_image = str(image_path.relative_to(self.storage_root))
            
            # TODO: Implement thumbnail generation in background task
            return relative_image, None
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            # Clean up any partially saved files
            if image_path.exists():
                image_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save image"
            )
    
    
    def delete_analysis_images(self, user_id: Optional[int], analysis_id: int) -> None:
        """Delete all images for an analysis.
        
        Args:
            user_id: User ID (None for anonymous)
            analysis_id: Analysis ID
        """
        try:
            user_folder = f"user_{user_id}" if user_id else "anonymous"
            analysis_folder = f"analysis_{analysis_id}"
            analysis_dir = self.storage_root / user_folder / analysis_folder
            
            if analysis_dir.exists():
                # Remove all files in the analysis directory
                import shutil
                shutil.rmtree(analysis_dir)
                logger.info(f"Deleted images for analysis {analysis_id}")
                
        except Exception as e:
            logger.error(f"Error deleting analysis images: {e}")
    
    def delete_reading_images(self, user_id: Optional[int], reading_id: int) -> None:
        """Delete all images for a reading.
        
        Args:
            user_id: User ID (None for anonymous)
            reading_id: Reading ID
        """
        try:
            user_folder = f"user_{user_id}" if user_id else "anonymous"
            reading_folder = f"analysis_{reading_id}"  # Keep using analysis_ folder structure for backward compatibility
            reading_dir = self.storage_root / user_folder / reading_folder
            
            if reading_dir.exists():
                # Remove all files in the reading directory
                import shutil
                shutil.rmtree(reading_dir)
                logger.info(f"Deleted images for reading {reading_id}")
                
        except Exception as e:
            logger.error(f"Error deleting reading images: {e}")
    
    def get_image_url(self, relative_path: str) -> str:
        """Get URL for accessing an image.
        
        Args:
            relative_path: Relative path from storage root
            
        Returns:
            URL to access the image
        """
        # In development, images are served from the API
        # In production, this could be a CDN URL
        return f"/api/v1/images/{relative_path}"
    
    def validate_quota(self, user_id: Optional[int]) -> None:
        """Check if user has exceeded their quota.
        
        Args:
            user_id: User ID (None for anonymous)
            
        Raises:
            HTTPException: If quota is exceeded
        """
        # For MVP, implement basic quota checking
        # Anonymous users: 5 analyses per day
        # Authenticated users: 20 analyses per day
        
        if user_id is None:
            # For anonymous users, this would check IP-based limits
            # For now, we'll allow it
            pass
        else:
            # For authenticated users, this would check DB for daily usage
            # For now, we'll allow it
            pass