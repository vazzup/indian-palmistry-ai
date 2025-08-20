"""
Tests for analysis service functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import UploadFile
from app.services.analysis_service import AnalysisService
from app.models.analysis import Analysis, AnalysisStatus
from app.models.user import User


@pytest.fixture
def analysis_service():
    """Create analysis service instance for testing."""
    return AnalysisService()


@pytest.fixture
def mock_upload_file():
    """Create mock upload file."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_palm.jpg"
    mock_file.content_type = "image/jpeg"
    mock_file.size = 1024
    return mock_file


@pytest.mark.asyncio
class TestAnalysisService:
    """Test analysis service operations."""
    
    async def test_create_analysis_success(self, analysis_service, mock_upload_file):
        """Test successful analysis creation."""
        with patch.object(analysis_service, 'get_session') as mock_session, \
             patch.object(analysis_service.image_service, 'validate_quota') as mock_quota, \
             patch.object(analysis_service.image_service, 'save_image') as mock_save, \
             patch('app.services.analysis_service.process_palm_analysis') as mock_task:
            
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock successful image save
            mock_save.return_value = ("path/to/image.jpg", None)
            
            # Mock Celery task
            mock_job = MagicMock()
            mock_job.id = "test-job-id"
            mock_task.delay.return_value = mock_job
            
            # Mock analysis creation
            mock_analysis = Analysis(
                id=1,
                user_id=1,
                status=AnalysisStatus.QUEUED,
                job_id="test-job-id"
            )
            
            result = await analysis_service.create_analysis(
                user_id=1,
                left_image=mock_upload_file
            )
            
            # Verify validations and saves were called
            mock_quota.assert_called_once_with(1)
            mock_save.assert_called_once()
            mock_task.delay.assert_called_once()
            
            # Verify database operations
            assert mock_db.add.called
            assert mock_db.commit.call_count >= 2  # Once for creation, once for job_id
            assert mock_db.refresh.call_count >= 2
    
    async def test_create_analysis_quota_exceeded(self, analysis_service, mock_upload_file):
        """Test analysis creation when quota is exceeded."""
        with patch.object(analysis_service.image_service, 'validate_quota') as mock_quota:
            mock_quota.side_effect = ValueError("Quota exceeded")
            
            with pytest.raises(ValueError, match="Quota exceeded"):
                await analysis_service.create_analysis(
                    user_id=1,
                    left_image=mock_upload_file
                )
    
    async def test_create_analysis_image_save_failure(self, analysis_service, mock_upload_file):
        """Test analysis creation when image save fails."""
        with patch.object(analysis_service, 'get_session') as mock_session, \
             patch.object(analysis_service.image_service, 'validate_quota') as mock_quota, \
             patch.object(analysis_service.image_service, 'save_image') as mock_save, \
             patch.object(analysis_service.image_service, 'delete_analysis_images') as mock_delete:
            
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock image save failure
            mock_save.side_effect = Exception("Image save failed")
            
            with pytest.raises(Exception, match="Image save failed"):
                await analysis_service.create_analysis(
                    user_id=1,
                    left_image=mock_upload_file
                )
            
            # Verify cleanup was called
            mock_delete.assert_called_once()
    
    async def test_get_analysis_by_id(self, analysis_service):
        """Test getting analysis by ID."""
        with patch.object(analysis_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_analysis = Analysis(id=1, user_id=1)
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_analysis
            
            result = await analysis_service.get_analysis_by_id(1)
            
            assert result == mock_analysis
            assert mock_db.execute.called
    
    async def test_get_analysis_by_id_not_found(self, analysis_service):
        """Test getting non-existent analysis."""
        with patch.object(analysis_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await analysis_service.get_analysis_by_id(999)
            
            assert result is None
    
    async def test_get_user_analyses_with_pagination(self, analysis_service):
        """Test getting user analyses with pagination."""
        with patch.object(analysis_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock count query
            mock_count_result = MagicMock()
            mock_count_result.fetchall.return_value = [1, 2, 3]  # 3 total
            
            # Mock paginated query
            mock_analyses = [
                Analysis(id=1, user_id=1),
                Analysis(id=2, user_id=1)
            ]
            mock_paginated_result = MagicMock()
            mock_paginated_result.scalars.return_value.all.return_value = mock_analyses
            
            # Setup mock to return different results for different queries
            mock_db.execute.side_effect = [mock_count_result, mock_paginated_result]
            
            result_analyses, total = await analysis_service.get_user_analyses(
                user_id=1,
                page=1,
                per_page=2
            )
            
            assert len(result_analyses) == 2
            assert total == 3
            assert result_analyses == mock_analyses
    
    async def test_update_job_id(self, analysis_service):
        """Test updating analysis job ID."""
        with patch.object(analysis_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_analysis = Analysis(id=1, job_id=None)
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_analysis
            
            result = await analysis_service.update_job_id(1, "new-job-id")
            
            assert result is True
            assert mock_analysis.job_id == "new-job-id"
            mock_db.commit.assert_called_once()
    
    async def test_update_job_id_not_found(self, analysis_service):
        """Test updating job ID for non-existent analysis."""
        with patch.object(analysis_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await analysis_service.update_job_id(999, "new-job-id")
            
            assert result is False
    
    async def test_delete_analysis_success(self, analysis_service):
        """Test successful analysis deletion."""
        with patch.object(analysis_service, 'get_session') as mock_session, \
             patch.object(analysis_service.image_service, 'delete_analysis_images') as mock_delete_images:
            
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_analysis = Analysis(id=1, user_id=1)
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_analysis
            
            result = await analysis_service.delete_analysis(analysis_id=1, user_id=1)
            
            assert result is True
            mock_delete_images.assert_called_once_with(1, 1)
            mock_db.delete.assert_called_once_with(mock_analysis)
            mock_db.commit.assert_called_once()
    
    async def test_delete_analysis_not_found(self, analysis_service):
        """Test deleting non-existent analysis."""
        with patch.object(analysis_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await analysis_service.delete_analysis(analysis_id=999, user_id=1)
            
            assert result is False
    
    async def test_delete_analysis_wrong_user(self, analysis_service):
        """Test deleting analysis owned by different user."""
        with patch.object(analysis_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Analysis exists but belongs to different user
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await analysis_service.delete_analysis(analysis_id=1, user_id=2)
            
            assert result is False