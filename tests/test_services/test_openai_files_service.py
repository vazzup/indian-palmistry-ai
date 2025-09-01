"""
Unit tests for OpenAI Files Service.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import os
from typing import Dict, List

from app.services.openai_files_service import OpenAIFilesService, OpenAIFilesServiceError
from app.models.analysis import Analysis, AnalysisStatus


class TestOpenAIFilesService:
    """Test suite for OpenAI Files Service."""

    @pytest.fixture
    def service(self) -> OpenAIFilesService:
        """Create OpenAI Files Service instance."""
        return OpenAIFilesService()

    @pytest.fixture
    def mock_analysis(self) -> Analysis:
        """Create mock analysis with image paths."""
        analysis = Mock(spec=Analysis)
        analysis.id = 1
        analysis.left_image_path = "/fake/path/left_palm.jpg"
        analysis.right_image_path = "/fake/path/right_palm.jpg"
        return analysis

    @pytest.fixture
    def temp_image_file(self):
        """Create temporary image file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            # Write some fake image data
            f.write(b'fake_image_data_for_testing' * 100)  # Make it reasonably sized
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        mock_response = Mock()
        mock_response.id = "file-test123"
        mock_response.filename = "test_image.jpg"
        mock_response.purpose = "vision"
        mock_response.status = "processed"
        mock_response.bytes = 1024
        mock_response.created_at = 1234567890
        return mock_response

    # Test upload_analysis_images
    @pytest.mark.asyncio
    async def test_upload_analysis_images_success(self, service, mock_analysis, temp_image_file):
        """Test successful image upload for analysis."""
        # Setup mock analysis with real temp files
        mock_analysis.left_image_path = temp_image_file
        mock_analysis.right_image_path = temp_image_file

        with patch.object(service, '_upload_single_image_with_retry', new_callable=AsyncMock) as mock_upload:
            mock_upload.side_effect = [
                ("left_palm", "file-left123"),
                ("right_palm", "file-right456")
            ]

            result = await service.upload_analysis_images(mock_analysis)

            assert result == {
                "left_palm": "file-left123",
                "right_palm": "file-right456"
            }
            assert mock_upload.call_count == 2

    @pytest.mark.asyncio
    async def test_upload_analysis_images_no_images(self, service):
        """Test upload with no images raises error."""
        mock_analysis = Mock(spec=Analysis)
        mock_analysis.id = 1
        mock_analysis.left_image_path = None
        mock_analysis.right_image_path = None

        with pytest.raises(OpenAIFilesServiceError, match="No images to upload"):
            await service.upload_analysis_images(mock_analysis)

    @pytest.mark.asyncio
    async def test_upload_analysis_images_partial_failure(self, service, mock_analysis, temp_image_file):
        """Test handling of partial upload failures."""
        mock_analysis.left_image_path = temp_image_file
        mock_analysis.right_image_path = temp_image_file

        with patch.object(service, '_upload_single_image_with_retry', new_callable=AsyncMock) as mock_upload:
            mock_upload.side_effect = [
                ("left_palm", "file-left123"),
                Exception("Upload failed")
            ]

            with pytest.raises(OpenAIFilesServiceError, match="Failed to upload image"):
                await service.upload_analysis_images(mock_analysis)

    # Test _upload_single_image
    @pytest.mark.asyncio
    async def test_upload_single_image_success(self, service, temp_image_file, mock_openai_response):
        """Test successful single image upload."""
        with patch('aiofiles.open') as mock_open:
            mock_file = AsyncMock()
            mock_file.read.return_value = b'fake_image_data'
            mock_open.return_value.__aenter__.return_value = mock_file

            with patch.object(service.client.files, 'create', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_openai_response

                result = await service._upload_single_image(temp_image_file, "left_palm")

                assert result == ("left_palm", "file-test123")
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_single_image_file_not_found(self, service):
        """Test upload with non-existent file."""
        with pytest.raises(OpenAIFilesServiceError, match="Image file not found"):
            await service._upload_single_image("/nonexistent/path.jpg", "left_palm")

    @pytest.mark.asyncio
    async def test_upload_single_image_unsupported_format(self, service):
        """Test upload with unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(OpenAIFilesServiceError, match="Unsupported file format"):
                await service._upload_single_image(temp_path, "left_palm")
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_upload_single_image_too_large(self, service):
        """Test upload with file too large."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            # Write data larger than max size
            f.write(b'x' * (service.max_file_size + 1))
            temp_path = f.name

        try:
            with pytest.raises(OpenAIFilesServiceError, match="File too large"):
                await service._upload_single_image(temp_path, "left_palm")
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_upload_single_image_empty_file(self, service):
        """Test upload with empty file."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name  # Empty file

        try:
            with pytest.raises(OpenAIFilesServiceError, match="File is empty"):
                await service._upload_single_image(temp_path, "left_palm")
        finally:
            os.unlink(temp_path)

    # Test delete_files
    @pytest.mark.asyncio
    async def test_delete_files_success(self, service):
        """Test successful file deletion."""
        file_ids = ["file-123", "file-456"]

        with patch.object(service, '_delete_single_file', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            result = await service.delete_files(file_ids)

            assert result == {"file-123": True, "file-456": True}
            assert mock_delete.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_files_empty_list(self, service):
        """Test deletion with empty file list."""
        result = await service.delete_files([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_delete_files_partial_failure(self, service):
        """Test deletion with some failures."""
        file_ids = ["file-123", "file-456"]

        with patch.object(service, '_delete_single_file', new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = [True, Exception("Delete failed")]

            result = await service.delete_files(file_ids)

            assert result == {"file-123": True, "file-456": False}

    @pytest.mark.asyncio
    async def test_delete_single_file_success(self, service):
        """Test successful single file deletion."""
        with patch.object(service.client.files, 'delete', new_callable=AsyncMock) as mock_delete:
            result = await service._delete_single_file("file-123")
            assert result is True
            mock_delete.assert_called_once_with("file-123")

    @pytest.mark.asyncio
    async def test_delete_single_file_failure(self, service):
        """Test single file deletion failure."""
        with patch.object(service.client.files, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = Exception("API Error")
            result = await service._delete_single_file("file-123")
            assert result is False

    # Test get_file_info
    @pytest.mark.asyncio
    async def test_get_file_info_success(self, service, mock_openai_response):
        """Test successful file info retrieval."""
        with patch.object(service.client.files, 'retrieve', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = mock_openai_response

            result = await service.get_file_info("file-123")

            expected = {
                'id': "file-test123",
                'filename': "test_image.jpg",
                'purpose': "vision",
                'status': "processed",
                'bytes': 1024,
                'created_at': 1234567890
            }
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_file_info_failure(self, service):
        """Test file info retrieval failure."""
        with patch.object(service.client.files, 'retrieve', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.side_effect = Exception("File not found")

            result = await service.get_file_info("file-123")
            assert result is None

    # Test validate_files
    @pytest.mark.asyncio
    async def test_validate_files_success(self, service):
        """Test successful file validation."""
        file_ids = ["file-123", "file-456"]

        with patch.object(service, '_validate_single_file', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True

            result = await service.validate_files(file_ids)

            assert result == {"file-123": True, "file-456": True}
            assert mock_validate.call_count == 2

    @pytest.mark.asyncio
    async def test_validate_files_empty_list(self, service):
        """Test validation with empty file list."""
        result = await service.validate_files([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_validate_files_mixed_results(self, service):
        """Test validation with mixed results."""
        file_ids = ["file-123", "file-456"]

        with patch.object(service, '_validate_single_file', new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = [True, Exception("Validation failed")]

            result = await service.validate_files(file_ids)

            assert result == {"file-123": True, "file-456": False}

    @pytest.mark.asyncio
    async def test_validate_single_file_success(self, service):
        """Test successful single file validation."""
        mock_file_info = Mock()
        mock_file_info.status = "processed"

        with patch.object(service.client.files, 'retrieve', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = mock_file_info

            result = await service._validate_single_file("file-123")
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_single_file_not_processed(self, service):
        """Test validation of file that's not processed."""
        mock_file_info = Mock()
        mock_file_info.status = "pending"

        with patch.object(service.client.files, 'retrieve', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = mock_file_info

            result = await service._validate_single_file("file-123")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_single_file_failure(self, service):
        """Test single file validation failure."""
        with patch.object(service.client.files, 'retrieve', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.side_effect = Exception("File not found")

            result = await service._validate_single_file("file-123")
            assert result is False

    # Test retry logic
    @pytest.mark.asyncio
    async def test_upload_with_retry_success_first_attempt(self, service, temp_image_file):
        """Test successful upload on first attempt."""
        with patch.object(service, '_upload_single_image', new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = ("left_palm", "file-123")

            result = await service._upload_single_image_with_retry(temp_image_file, "left_palm")

            assert result == ("left_palm", "file-123")
            assert mock_upload.call_count == 1

    @pytest.mark.asyncio
    async def test_upload_with_retry_success_after_failures(self, service, temp_image_file):
        """Test successful upload after initial failures."""
        with patch.object(service, '_upload_single_image', new_callable=AsyncMock) as mock_upload:
            mock_upload.side_effect = [
                Exception("Temporary error"),
                Exception("Another temporary error"),
                ("left_palm", "file-123")
            ]

            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await service._upload_single_image_with_retry(temp_image_file, "left_palm")

                assert result == ("left_palm", "file-123")
                assert mock_upload.call_count == 3

    @pytest.mark.asyncio
    async def test_upload_with_retry_all_attempts_failed(self, service, temp_image_file):
        """Test upload failure after all retry attempts."""
        with patch.object(service, '_upload_single_image', new_callable=AsyncMock) as mock_upload:
            mock_upload.side_effect = Exception("Persistent error")

            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(Exception, match="Persistent error"):
                    await service._upload_single_image_with_retry(temp_image_file, "left_palm")

                assert mock_upload.call_count == service.max_retries

    # Test cleanup_old_files
    @pytest.mark.asyncio
    async def test_cleanup_old_files_success(self, service):
        """Test successful cleanup of old files."""
        # Mock old files
        mock_file_old = Mock()
        mock_file_old.id = "file-old123"
        mock_file_old.created_at = 1000000000  # Old timestamp
        mock_file_old.purpose = "vision"

        mock_file_new = Mock()
        mock_file_new.id = "file-new456"
        mock_file_new.created_at = 9999999999  # New timestamp
        mock_file_new.purpose = "vision"

        mock_files_response = Mock()
        mock_files_response.data = [mock_file_old, mock_file_new]

        with patch.object(service.client.files, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_files_response

            with patch.object(service, 'delete_files', new_callable=AsyncMock) as mock_delete:
                mock_delete.return_value = {"file-old123": True}

                with patch('time.time', return_value=5000000000):  # Current time
                    result = await service.cleanup_old_files(older_than_days=30)

                    assert result == 1
                    mock_delete.assert_called_once_with(["file-old123"])

    @pytest.mark.asyncio
    async def test_cleanup_old_files_no_old_files(self, service):
        """Test cleanup when no old files exist."""
        mock_files_response = Mock()
        mock_files_response.data = []

        with patch.object(service.client.files, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_files_response

            result = await service.cleanup_old_files(older_than_days=30)
            assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_files_failure(self, service):
        """Test cleanup failure handling."""
        with patch.object(service.client.files, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("API Error")

            result = await service.cleanup_old_files(older_than_days=30)
            assert result == 0