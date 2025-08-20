"""
Tests for background analysis tasks.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.tasks.analysis_tasks import process_palm_analysis, generate_thumbnails
from app.models.analysis import Analysis, AnalysisStatus


@pytest.mark.asyncio
class TestAnalysisTasks:
    """Test background analysis tasks."""
    
    def test_process_palm_analysis_success(self):
        """Test successful palm analysis processing."""
        with patch('app.tasks.analysis_tasks.AsyncSessionLocal') as mock_session_class, \
             patch('app.tasks.analysis_tasks.OpenAIService') as mock_openai_class, \
             patch('app.tasks.analysis_tasks.redis_service') as mock_redis, \
             patch('app.tasks.analysis_tasks.generate_thumbnails') as mock_thumbnails, \
             patch('asyncio.run') as mock_asyncio_run:
            
            # Mock database operations
            mock_db = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_db
            
            # Mock analysis object
            mock_analysis = Analysis(
                id=1,
                left_image_path="left.jpg",
                right_image_path="right.jpg",
                status=AnalysisStatus.QUEUED
            )
            
            # Setup mock to return analysis for different calls
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_analysis
            
            # Mock OpenAI service
            mock_openai = MagicMock()
            mock_openai_class.return_value = mock_openai
            
            # Mock OpenAI analysis result
            openai_result = {
                "summary": "Test summary",
                "full_report": "Test full report",
                "tokens_used": 100,
                "cost": 0.01
            }
            
            # Setup asyncio.run to return the OpenAI result when called
            mock_asyncio_run.side_effect = [
                mock_analysis,  # First call: update analysis status
                openai_result,  # Second call: OpenAI analysis
                None,  # Third call: save results
                None,  # Fourth call: Redis operations
            ]
            
            # Mock task instance
            mock_task = MagicMock()
            mock_task.request.id = "test-job-id"
            mock_task.request.retries = 0
            
            # Call the task
            result = process_palm_analysis(mock_task, 1)
            
            # Verify result
            assert result["status"] == "completed"
            assert result["analysis_id"] == 1
            assert result["summary"] == "Test summary"
            assert result["tokens_used"] == 100
            
            # Verify thumbnail generation was queued
            mock_thumbnails.delay.assert_called_once_with(1)
    
    def test_process_palm_analysis_not_found(self):
        """Test processing when analysis doesn't exist."""
        with patch('app.tasks.analysis_tasks.AsyncSessionLocal') as mock_session_class, \
             patch('asyncio.run') as mock_asyncio_run:
            
            # Mock database returning None (analysis not found)
            mock_asyncio_run.side_effect = ValueError("Analysis 999 not found")
            
            mock_task = MagicMock()
            mock_task.request.id = "test-job-id"
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="Analysis 999 not found"):
                process_palm_analysis(mock_task, 999)
    
    def test_process_palm_analysis_openai_error(self):
        """Test processing when OpenAI service fails."""
        with patch('app.tasks.analysis_tasks.AsyncSessionLocal') as mock_session_class, \
             patch('app.tasks.analysis_tasks.OpenAIService') as mock_openai_class, \
             patch('app.tasks.analysis_tasks.redis_service') as mock_redis, \
             patch('asyncio.run') as mock_asyncio_run:
            
            # Mock analysis exists
            mock_analysis = Analysis(
                id=1,
                left_image_path="left.jpg",
                status=AnalysisStatus.QUEUED
            )
            
            # Setup asyncio.run calls
            openai_error = Exception("OpenAI API Error")
            mock_asyncio_run.side_effect = [
                mock_analysis,  # First call: update analysis status
                openai_error,   # Second call: OpenAI analysis fails
                None,           # Third call: update failed analysis
                None,           # Fourth call: Redis operations
            ]
            
            mock_task = MagicMock()
            mock_task.request.id = "test-job-id"
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            mock_task.retry = MagicMock(side_effect=Exception("Retry called"))
            
            # Should attempt retry
            with pytest.raises(Exception, match="Retry called"):
                process_palm_analysis(mock_task, 1)
            
            # Verify retry was called with exponential backoff
            mock_task.retry.assert_called_once_with(countdown=60, exc=openai_error)
    
    def test_process_palm_analysis_max_retries_exceeded(self):
        """Test processing when max retries are exceeded."""
        with patch('app.tasks.analysis_tasks.AsyncSessionLocal') as mock_session_class, \
             patch('app.tasks.analysis_tasks.OpenAIService') as mock_openai_class, \
             patch('asyncio.run') as mock_asyncio_run:
            
            # Mock analysis exists
            mock_analysis = Analysis(id=1, left_image_path="left.jpg")
            
            # Setup asyncio.run to fail on OpenAI call
            openai_error = Exception("OpenAI API Error")
            mock_asyncio_run.side_effect = [
                mock_analysis,  # Update analysis status
                openai_error,   # OpenAI analysis fails
                None,           # Update failed analysis
                None,           # Redis operations
            ]
            
            mock_task = MagicMock()
            mock_task.request.id = "test-job-id"
            mock_task.request.retries = 3  # Max retries reached
            mock_task.max_retries = 3
            
            result = process_palm_analysis(mock_task, 1)
            
            # Should return failed result
            assert result["status"] == "failed"
            assert result["retries_exhausted"] is True
    
    def test_generate_thumbnails_success(self):
        """Test successful thumbnail generation."""
        with patch('app.tasks.analysis_tasks.AsyncSessionLocal') as mock_session_class, \
             patch('app.tasks.analysis_tasks.ImageService') as mock_image_service_class, \
             patch('asyncio.run') as mock_asyncio_run:
            
            # Mock analysis with images
            mock_analysis = Analysis(
                id=1,
                left_image_path="left.jpg",
                right_image_path="right.jpg"
            )
            
            # Mock database operations
            mock_asyncio_run.side_effect = [
                mock_analysis,  # Load analysis
                None,           # Save thumbnails
            ]
            
            # Mock image service
            mock_image_service = MagicMock()
            mock_image_service_class.return_value = mock_image_service
            
            # Mock successful thumbnail generation
            mock_image_service.generate_thumbnail.side_effect = [
                "left_thumb.jpg",   # Left thumbnail
                "right_thumb.jpg"   # Right thumbnail
            ]
            
            mock_task = MagicMock()
            mock_task.request.id = "thumb-job-id"
            mock_task.request.retries = 0
            
            result = generate_thumbnails(mock_task, 1)
            
            # Verify result
            assert result["status"] == "completed"
            assert result["thumbnails_generated"] == 2
            assert "left_thumb.jpg" in result["thumbnail_paths"]
            assert "right_thumb.jpg" in result["thumbnail_paths"]
    
    def test_generate_thumbnails_analysis_not_found(self):
        """Test thumbnail generation when analysis doesn't exist."""
        with patch('asyncio.run') as mock_asyncio_run:
            
            # Mock analysis not found
            mock_asyncio_run.return_value = None
            
            mock_task = MagicMock()
            mock_task.request.id = "thumb-job-id"
            mock_task.request.retries = 0
            
            with pytest.raises(ValueError, match="Analysis 999 not found"):
                generate_thumbnails(mock_task, 999)
    
    def test_generate_thumbnails_partial_failure(self):
        """Test thumbnail generation with partial failures."""
        with patch('app.tasks.analysis_tasks.AsyncSessionLocal') as mock_session_class, \
             patch('app.tasks.analysis_tasks.ImageService') as mock_image_service_class, \
             patch('asyncio.run') as mock_asyncio_run:
            
            # Mock analysis with both images
            mock_analysis = Analysis(
                id=1,
                left_image_path="left.jpg",
                right_image_path="right.jpg"
            )
            
            mock_asyncio_run.side_effect = [
                mock_analysis,  # Load analysis
                None,           # Save thumbnails
            ]
            
            # Mock image service with partial failure
            mock_image_service = MagicMock()
            mock_image_service_class.return_value = mock_image_service
            
            # Left thumbnail succeeds, right thumbnail fails
            mock_image_service.generate_thumbnail.side_effect = [
                "left_thumb.jpg",           # Left thumbnail succeeds
                Exception("Thumbnail error") # Right thumbnail fails
            ]
            
            mock_task = MagicMock()
            mock_task.request.id = "thumb-job-id"
            mock_task.request.retries = 0
            
            result = generate_thumbnails(mock_task, 1)
            
            # Should still complete with partial success
            assert result["status"] == "completed"
            assert result["thumbnails_generated"] == 1
            assert len(result["thumbnail_paths"]) == 1
    
    def test_generate_thumbnails_retry_on_failure(self):
        """Test thumbnail generation retry mechanism."""
        with patch('asyncio.run') as mock_asyncio_run:
            
            # Mock complete failure
            mock_asyncio_run.side_effect = Exception("Database error")
            
            mock_task = MagicMock()
            mock_task.request.id = "thumb-job-id"
            mock_task.request.retries = 1  # First retry
            mock_task.max_retries = 2
            mock_task.retry = MagicMock(side_effect=Exception("Retry called"))
            
            with pytest.raises(Exception, match="Retry called"):
                generate_thumbnails(mock_task, 1)
            
            # Verify retry with exponential backoff
            mock_task.retry.assert_called_once_with(countdown=60, exc=mock_asyncio_run.side_effect)
    
    def test_generate_thumbnails_max_retries_exceeded(self):
        """Test thumbnail generation when max retries exceeded."""
        with patch('asyncio.run') as mock_asyncio_run:
            
            # Mock failure
            mock_asyncio_run.side_effect = Exception("Persistent error")
            
            mock_task = MagicMock()
            mock_task.request.id = "thumb-job-id"
            mock_task.request.retries = 2  # Max retries reached
            mock_task.max_retries = 2
            
            result = generate_thumbnails(mock_task, 1)
            
            # Should return failed result
            assert result["status"] == "failed"
            assert "Persistent error" in result["error"]