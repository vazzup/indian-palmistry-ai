"""
Integration tests for analysis API endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO
from app.main import app
from app.models.analysis import Analysis, AnalysisStatus
from app.models.user import User


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return User(id=1, email="test@example.com", name="Test User")


@pytest.fixture
def mock_image_file():
    """Create mock image file for upload."""
    return ("test_palm.jpg", BytesIO(b"fake_image_data"), "image/jpeg")


@pytest.mark.asyncio
class TestAnalysesAPI:
    """Test analysis API endpoints."""
    
    def test_create_analysis_success(self, client, mock_user, mock_image_file):
        """Test successful analysis creation."""
        with patch('app.dependencies.auth.get_current_user_optional') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.create_analysis') as mock_create:
            
            mock_get_user.return_value = mock_user
            
            # Mock successful analysis creation
            mock_analysis = Analysis(
                id=1,
                user_id=1,
                status=AnalysisStatus.QUEUED,
                job_id="test-job-id"
            )
            mock_create.return_value = mock_analysis
            
            response = client.post(
                "/api/v1/analyses/",
                files={"left_image": mock_image_file}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["user_id"] == 1
            assert data["status"] == "queued"
            assert data["job_id"] == "test-job-id"
    
    def test_create_analysis_anonymous(self, client, mock_image_file):
        """Test analysis creation by anonymous user."""
        with patch('app.dependencies.auth.get_current_user_optional') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.create_analysis') as mock_create:
            
            mock_get_user.return_value = None  # Anonymous user
            
            # Mock successful anonymous analysis creation
            mock_analysis = Analysis(
                id=2,
                user_id=None,
                status=AnalysisStatus.QUEUED,
                job_id="test-job-id-2"
            )
            mock_create.return_value = mock_analysis
            
            response = client.post(
                "/api/v1/analyses/",
                files={"left_image": mock_image_file}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 2
            assert data["user_id"] is None
            assert data["status"] == "queued"
    
    def test_create_analysis_no_images(self, client, mock_user):
        """Test analysis creation without images."""
        with patch('app.dependencies.auth.get_current_user_optional') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            response = client.post("/api/v1/analyses/")
            
            assert response.status_code == 400
            data = response.json()
            assert "At least one palm image is required" in data["detail"]
    
    def test_create_analysis_both_images(self, client, mock_user, mock_image_file):
        """Test analysis creation with both left and right images."""
        with patch('app.dependencies.auth.get_current_user_optional') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.create_analysis') as mock_create:
            
            mock_get_user.return_value = mock_user
            
            mock_analysis = Analysis(
                id=3,
                user_id=1,
                left_image_path="left.jpg",
                right_image_path="right.jpg",
                status=AnalysisStatus.QUEUED
            )
            mock_create.return_value = mock_analysis
            
            left_file = ("left_palm.jpg", BytesIO(b"left_image_data"), "image/jpeg")
            right_file = ("right_palm.jpg", BytesIO(b"right_image_data"), "image/jpeg")
            
            response = client.post(
                "/api/v1/analyses/",
                files={"left_image": left_file, "right_image": right_file}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["left_image_path"] == "left.jpg"
            assert data["right_image_path"] == "right.jpg"
    
    def test_create_analysis_service_error(self, client, mock_user, mock_image_file):
        """Test analysis creation when service fails."""
        with patch('app.dependencies.auth.get_current_user_optional') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.create_analysis') as mock_create:
            
            mock_get_user.return_value = mock_user
            mock_create.side_effect = Exception("Service error")
            
            response = client.post(
                "/api/v1/analyses/",
                files={"left_image": mock_image_file}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to create analysis" in data["detail"]
    
    def test_get_analysis_status(self, client):
        """Test getting analysis status."""
        with patch('app.services.analysis_service.AnalysisService.get_analysis_status') as mock_get_status:
            mock_analysis = Analysis(
                id=1,
                status=AnalysisStatus.PROCESSING,
                error_message=None
            )
            mock_get_status.return_value = mock_analysis
            
            response = client.get("/api/v1/analyses/1/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["analysis_id"] == 1
            assert data["status"] == "processing"
            assert data["progress"] == 50  # Processing = 50%
            assert data["message"] == "Analyzing palm images..."
    
    def test_get_analysis_status_not_found(self, client):
        """Test getting status for non-existent analysis."""
        with patch('app.services.analysis_service.AnalysisService.get_analysis_status') as mock_get_status:
            mock_get_status.return_value = None
            
            response = client.get("/api/v1/analyses/999/status")
            
            assert response.status_code == 404
            data = response.json()
            assert "Analysis not found" in data["detail"]
    
    def test_get_analysis_status_failed(self, client):
        """Test getting status for failed analysis."""
        with patch('app.services.analysis_service.AnalysisService.get_analysis_status') as mock_get_status:
            mock_analysis = Analysis(
                id=1,
                status=AnalysisStatus.FAILED,
                error_message="OpenAI API error"
            )
            mock_get_status.return_value = mock_analysis
            
            response = client.get("/api/v1/analyses/1/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert data["progress"] == 0
            assert data["error_message"] == "OpenAI API error"
    
    def test_get_analysis_summary(self, client):
        """Test getting analysis summary (public)."""
        with patch('app.services.analysis_service.AnalysisService.get_analysis_by_id') as mock_get_analysis:
            mock_analysis = Analysis(
                id=1,
                summary="Test palm reading summary",
                status=AnalysisStatus.COMPLETED,
                created_at="2023-01-01T00:00:00"
            )
            mock_get_analysis.return_value = mock_analysis
            
            response = client.get("/api/v1/analyses/1/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["analysis_id"] == 1
            assert data["summary"] == "Test palm reading summary"
            assert data["status"] == "completed"
            assert data["requires_login"] is True
    
    def test_get_analysis_summary_not_found(self, client):
        """Test getting summary for non-existent analysis."""
        with patch('app.services.analysis_service.AnalysisService.get_analysis_by_id') as mock_get_analysis:
            mock_get_analysis.return_value = None
            
            response = client.get("/api/v1/analyses/999/summary")
            
            assert response.status_code == 404
            data = response.json()
            assert "Analysis not found" in data["detail"]
    
    def test_get_analysis_full_authenticated(self, client, mock_user):
        """Test getting full analysis (authenticated)."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.get_analysis_by_id') as mock_get_analysis:
            
            mock_get_user.return_value = mock_user
            
            mock_analysis = Analysis(
                id=1,
                user_id=1,  # Belongs to the authenticated user
                summary="Summary",
                full_report="Full detailed report",
                status=AnalysisStatus.COMPLETED
            )
            mock_get_analysis.return_value = mock_analysis
            
            response = client.get(
                "/api/v1/analyses/1",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["summary"] == "Summary"
            assert data["full_report"] == "Full detailed report"
    
    def test_get_analysis_full_unauthenticated(self, client):
        """Test getting full analysis without authentication."""
        response = client.get("/api/v1/analyses/1")
        
        assert response.status_code == 401
    
    def test_get_analysis_full_wrong_user(self, client, mock_user):
        """Test getting analysis owned by different user."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.get_analysis_by_id') as mock_get_analysis:
            
            mock_get_user.return_value = mock_user  # User ID = 1
            
            mock_analysis = Analysis(
                id=1,
                user_id=2,  # Belongs to different user
                status=AnalysisStatus.COMPLETED
            )
            mock_get_analysis.return_value = mock_analysis
            
            response = client.get(
                "/api/v1/analyses/1",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 403
            data = response.json()
            assert "You don't have permission" in data["detail"]
    
    def test_list_user_analyses(self, client, mock_user):
        """Test listing user analyses with pagination."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.get_user_analyses') as mock_get_analyses:
            
            mock_get_user.return_value = mock_user
            
            mock_analyses = [
                Analysis(id=1, user_id=1, status=AnalysisStatus.COMPLETED),
                Analysis(id=2, user_id=1, status=AnalysisStatus.PROCESSING)
            ]
            mock_get_analyses.return_value = (mock_analyses, 5)  # 2 analyses, 5 total
            
            response = client.get(
                "/api/v1/analyses/?page=1&per_page=2",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["analyses"]) == 2
            assert data["total"] == 5
            assert data["page"] == 1
            assert data["per_page"] == 2
            assert data["has_more"] is True  # 1*2 < 5
    
    def test_list_user_analyses_unauthenticated(self, client):
        """Test listing analyses without authentication."""
        response = client.get("/api/v1/analyses/")
        
        assert response.status_code == 401
    
    def test_delete_analysis_success(self, client, mock_user):
        """Test successful analysis deletion."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.delete_analysis') as mock_delete:
            
            mock_get_user.return_value = mock_user
            mock_delete.return_value = True  # Successful deletion
            
            response = client.delete(
                "/api/v1/analyses/1",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Analysis deleted successfully"
    
    def test_delete_analysis_not_found(self, client, mock_user):
        """Test deleting non-existent analysis."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.delete_analysis') as mock_delete:
            
            mock_get_user.return_value = mock_user
            mock_delete.return_value = False  # Not found or no permission
            
            response = client.delete(
                "/api/v1/analyses/999",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "Analysis not found" in data["detail"]
    
    def test_delete_analysis_unauthenticated(self, client):
        """Test deleting analysis without authentication."""
        response = client.delete("/api/v1/analyses/1")
        
        assert response.status_code == 401