"""
Image service for handling palm image uploads, validation, and processing.
"""

import os
import io
import logging
from typing import Optional, Tuple
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from PIL import Image, ImageOps
import pillow_heif
from app.core.config import settings
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

# Allowed image types and their magic bytes
ALLOWED_MIME_TYPES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/heic": [b"ftypheic", b"ftypmif1"],
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
        self.openai_service = OpenAIService()
        # Register HEIF opener
        pillow_heif.register_heif_opener()
    
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
                detail="Invalid file type. Only JPEG, PNG, and HEIC images are allowed"
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
    
    def get_image_paths(self, analysis_id: int) -> Tuple[Path, Path]:
        """Get directory paths for storing images and thumbnails.
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Tuple of (images_dir, thumbnails_dir)
        """
        analysis_folder = f"analysis_{analysis_id}"
        
        images_dir = self.storage_root / analysis_folder / "images"
        thumbnails_dir = self.storage_root / analysis_folder / "thumbnails"
        
        # Create directories
        images_dir.mkdir(parents=True, exist_ok=True)
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        return images_dir, thumbnails_dir
    
    def compress_image(self, image_data: bytes, quality: int = 85, max_dimension: int = 2048) -> bytes:
        """Compress image while maintaining quality.
        
        Args:
            image_data: Raw image bytes
            quality: JPEG quality (1-100, default 85)
            max_dimension: Maximum width or height in pixels
            
        Returns:
            Compressed image bytes as JPEG
        """
        try:
            # Open image from bytes
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if necessary (handles HEIC/PNG with transparency)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Auto-orient based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Resize if too large while maintaining aspect ratio
                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                
                # Compress to JPEG
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Error compressing image: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to compress image"
            )
    
    def convert_heic_to_png(self, heic_data: bytes) -> bytes:
        """Convert HEIC image to PNG format.
        
        Args:
            heic_data: Raw HEIC image bytes
            
        Returns:
            PNG image bytes
        """
        try:
            # Open HEIC image
            with Image.open(io.BytesIO(heic_data)) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Auto-orient based on EXIF data
                img = ImageOps.exif_transpose(img)
                
                # Convert to PNG
                output = io.BytesIO()
                img.save(output, format='PNG', optimize=True)
                
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Error converting HEIC to PNG: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to convert HEIC image to PNG"
            )
    
    async def upload_image_to_openai(self, file_path: str) -> str:
        """Upload image to OpenAI and return file_id.
        
        Args:
            file_path: Path to the image file to upload
            
        Returns:
            OpenAI file ID
            
        Raises:
            Exception: If upload fails
        """
        try:
            with open(file_path, "rb") as file_content:
                response = await self.openai_service.client.files.create(
                    file=file_content,
                    purpose="vision"
                )
            logger.info(f"Uploaded image to OpenAI: {file_path}, file_id: {response.id}")
            return response.id
            
        except Exception as e:
            logger.error(f"Error uploading image to OpenAI: {e}")
            raise

    async def save_image(
        self, 
        file: UploadFile, 
        user_id: Optional[int], 
        analysis_id: int, 
        palm_type: str
    ) -> Tuple[str, str]:
        """Save compressed image locally and upload to OpenAI.
        
        Args:
            file: Uploaded image file
            user_id: User ID (None for anonymous) - kept for API compatibility
            analysis_id: Analysis ID
            palm_type: "left" or "right"
            
        Returns:
            Tuple of (local_file_path, openai_file_id) - local path and OpenAI file ID
        """
        # Validate file
        self.validate_image_file(file)
        
        try:
            # Read and compress the image
            file.file.seek(0)
            original_image_data = await file.read()
            file.file.seek(0)
            
            # Compress the image (converts to JPEG automatically)
            compressed_image_data = self.compress_image(original_image_data)
            
            # Get storage paths using new structure (no user folder)
            images_dir, _ = self.get_image_paths(analysis_id)
            
            # Create filename for compressed image
            filename = f"{palm_type}_palm_compressed.jpg"
            file_path = images_dir / filename
            
            # Save compressed image to local storage
            with open(file_path, 'wb') as f:
                f.write(compressed_image_data)
            
            # Create relative path for database storage
            relative_path = file_path.relative_to(self.storage_root)
            
            # Upload to OpenAI using the local file path
            openai_file_id = await self.upload_image_to_openai(str(file_path))
            
            logger.info(f"Saved {palm_type} palm image locally and uploaded to OpenAI for analysis {analysis_id}, path: {relative_path}, file_id: {openai_file_id}")
            
            # Return both local file path and OpenAI file ID
            return str(relative_path), openai_file_id
            
        except Exception as e:
            logger.error(f"Error saving image locally: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save image"
            )
    
    
    async def delete_openai_file(self, file_id: str) -> bool:
        """Delete a file from OpenAI storage.
        
        Args:
            file_id: OpenAI file ID to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            await self.openai_service.client.files.delete(file_id)
            logger.info(f"Deleted OpenAI file: {file_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete OpenAI file {file_id}: {e}")
            return False

    async def delete_analysis_images(
        self, 
        left_image_path: Optional[str], 
        right_image_path: Optional[str],
        left_file_id: Optional[str] = None,
        right_file_id: Optional[str] = None
    ) -> None:
        """Delete both local files and OpenAI files for an analysis.
        
        Args:
            left_image_path: Local path for left palm image
            right_image_path: Local path for right palm image
            left_file_id: OpenAI file ID for left palm image
            right_file_id: OpenAI file ID for right palm image
        """
        try:
            deleted_count = 0
            
            if left_image_path:
                try:
                    file_path = self.storage_root / left_image_path
                    if file_path.exists():
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted left palm image: {left_image_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete left image {left_image_path}: {e}")
                    
            if right_image_path:
                try:
                    file_path = self.storage_root / right_image_path
                    if file_path.exists():
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted right palm image: {right_image_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete right image {right_image_path}: {e}")
            
            # Delete OpenAI files
            if left_file_id:
                if await self.delete_openai_file(left_file_id):
                    deleted_count += 1
            
            if right_file_id:
                if await self.delete_openai_file(right_file_id):
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} files (local + OpenAI) for analysis")
                
        except Exception as e:
            logger.error(f"Error deleting files: {e}")
    
    async def get_image_url(self, file_path: str) -> str:
        """Get URL for accessing a local file.
        
        Args:
            file_path: Local file path relative to storage root
            
        Returns:
            URL to access the file
        """
        # Return a path that can be served by your web server
        # This assumes you have an endpoint that serves files from /images/ route
        return f"/images/{file_path}"
    
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
