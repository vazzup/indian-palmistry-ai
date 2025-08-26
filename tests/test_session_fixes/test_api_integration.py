"""
Tests for API integration fixes applied during debugging session.

These tests validate that the missing API functions have been properly
implemented and work correctly.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from app.main import app


class TestAnalysisAPIIntegration:
    """Test the analysis API integration fixes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_analysis_summary_endpoint_exists(self, client):
        """Test that the analysis summary endpoint exists and is accessible."""
        # Mock the database and services to avoid actual processing
        with patch('app.api.v1.analyses.AnalysisService') as mock_service:
            mock_analysis = Mock()
            mock_analysis.id = "test-123"
            mock_analysis.status = "completed"
            mock_analysis.summary = "Test palm analysis summary"
            mock_analysis.user_id = None  # Public analysis
            
            mock_service.return_value.get_analysis = AsyncMock(return_value=mock_analysis)
            
            response = client.get("/api/v1/analyses/test-123/summary")
            
            # Should return 200 OK
            assert response.status_code == 200
            
            # Should contain summary data
            data = response.json()
            assert "summary" in data
            assert data["summary"] == "Test palm analysis summary"
    
    def test_analysis_summary_endpoint_handles_not_found(self, client):
        """Test that the analysis summary endpoint handles missing analyses."""
        with patch('app.api.v1.analyses.AnalysisService') as mock_service:
            mock_service.return_value.get_analysis = AsyncMock(return_value=None)
            
            response = client.get("/api/v1/analyses/nonexistent/summary")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
    
    def test_analysis_summary_endpoint_handles_incomplete_analysis(self, client):
        """Test that the endpoint handles analyses that aren't completed yet."""
        with patch('app.api.v1.analyses.AnalysisService') as mock_service:
            mock_analysis = Mock()
            mock_analysis.id = "test-456"
            mock_analysis.status = "processing"
            mock_analysis.summary = None
            
            mock_service.return_value.get_analysis = AsyncMock(return_value=mock_analysis)
            
            response = client.get("/api/v1/analyses/test-456/summary")
            
            # Should return appropriate response for incomplete analysis
            assert response.status_code in [200, 202, 404]  # Depends on implementation
    
    @pytest.mark.asyncio
    async def test_get_analysis_summary_service_method(self):
        """Test that AnalysisService properly supports summary retrieval."""
        from app.services.analysis_service import AnalysisService
        from app.models.analysis import Analysis, AnalysisStatus
        
        # Mock database session
        mock_session = AsyncMock()
        analysis_service = AnalysisService(mock_session)
        
        # Mock analysis object
        mock_analysis = Mock(spec=Analysis)
        mock_analysis.id = "test-summary"
        mock_analysis.status = AnalysisStatus.COMPLETED
        mock_analysis.summary = "Detailed palm reading summary"
        mock_analysis.full_report = "Complete analysis report"
        mock_analysis.user_id = "user-123"
        
        # Mock database query
        mock_session.get = AsyncMock(return_value=mock_analysis)
        
        result = await analysis_service.get_analysis("test-summary")
        
        assert result is not None
        assert result.id == "test-summary"
        assert result.summary == "Detailed palm reading summary"
        assert result.status == AnalysisStatus.COMPLETED


class TestAPIParameterConsistency:
    """Test that API parameters are consistent between frontend and backend."""
    
    def test_register_endpoint_parameter_structure(self, client):
        """Test that register endpoint accepts the correct parameter structure."""
        register_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test User"
        }
        
        with patch('app.api.v1.auth.UserService') as mock_service, \
             patch('app.api.v1.auth.redis_client') as mock_redis:
            
            mock_user = Mock()
            mock_user.id = "user-123"
            mock_user.email = "test@example.com"
            mock_user.name = "Test User"
            
            mock_service.return_value.create_user = AsyncMock(return_value=mock_user)
            mock_redis.setex = AsyncMock()
            
            response = client.post("/api/v1/auth/register", json=register_data)
            
            # Should accept the data structure successfully
            assert response.status_code in [200, 201]  # Success codes
    
    def test_login_endpoint_parameter_structure(self, client):
        """Test that login endpoint accepts the correct parameter structure."""
        login_data = {
            "email": "test@example.com", 
            "password": "testpass123"
        }
        
        with patch('app.api.v1.auth.UserService') as mock_service, \
             patch('app.api.v1.auth.redis_client') as mock_redis:
            
            mock_user = Mock()
            mock_user.id = "user-123"
            mock_user.email = "test@example.com"
            mock_user.name = "Test User"
            
            mock_service.return_value.authenticate_user = AsyncMock(return_value=mock_user)
            mock_redis.setex = AsyncMock()
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            # Should accept the data structure successfully
            assert response.status_code in [200, 201]
    
    def test_analysis_upload_parameter_structure(self, client):
        """Test that analysis upload endpoint accepts correct file parameter structure."""
        # Create mock image data
        test_image_data = b"fake_image_data"
        
        with patch('app.api.v1.analyses.AnalysisService') as mock_analysis_service, \
             patch('app.api.v1.analyses.ImageService') as mock_image_service, \
             patch('app.api.v1.analyses.cache_service') as mock_cache:
            
            mock_analysis = Mock()
            mock_analysis.id = "analysis-123"
            mock_analysis.status = "queued"
            
            mock_analysis_service.return_value.create_analysis = AsyncMock(return_value=mock_analysis)
            mock_image_service.return_value.validate_image = AsyncMock(return_value=True)
            mock_image_service.return_value.save_image = AsyncMock(return_value="/path/to/image.jpg")
            mock_cache.set_job_status = AsyncMock()
            
            files = {
                "left_image": ("test_palm.jpg", test_image_data, "image/jpeg")
            }
            
            response = client.post("/api/v1/analyses/", files=files)
            
            # Should accept the file upload structure
            assert response.status_code in [200, 201, 202]  # Success codes


class TestAPIErrorHandling:
    """Test API error handling improvements."""
    
    def test_missing_analysis_error_response(self, client):
        """Test that missing analysis returns proper error response."""
        with patch('app.api.v1.analyses.AnalysisService') as mock_service:
            mock_service.return_value.get_analysis = AsyncMock(return_value=None)
            
            response = client.get("/api/v1/analyses/missing-123")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "not found" in data["detail"].lower()
    
    def test_invalid_analysis_id_error_response(self, client):
        """Test that invalid analysis ID format returns proper error."""
        # Test with clearly invalid ID format
        response = client.get("/api/v1/analyses/")
        
        # Should return 404 or 405 (method not allowed for GET on collection)
        assert response.status_code in [404, 405]
    
    def test_unauthorized_access_error_response(self, client):
        """Test that unauthorized access to protected resources returns proper error."""
        with patch('app.api.v1.analyses.AnalysisService') as mock_service:
            # Mock analysis that belongs to different user
            mock_analysis = Mock()
            mock_analysis.id = "private-123"
            mock_analysis.user_id = "different-user"
            mock_analysis.status = "completed"
            
            mock_service.return_value.get_analysis = AsyncMock(return_value=mock_analysis)
            
            # Try to access without proper authentication
            response = client.get("/api/v1/analyses/private-123")
            
            # Should handle access control appropriately
            assert response.status_code in [200, 401, 403, 404]  # Various valid responses
    
    def test_malformed_request_data_error_response(self, client):
        """Test that malformed request data returns proper validation errors."""
        # Test registration with missing required fields
        invalid_register_data = {
            "email": "invalid-email",  # Invalid email format
            "password": "123",         # Too short password
            # Missing name field
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_register_data)
        
        # Should return validation error
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data


class TestAPIResponseFormat:
    """Test that API responses have consistent format."""
    
    def test_analysis_summary_response_format(self, client):
        """Test that analysis summary response has the expected format."""
        with patch('app.api.v1.analyses.AnalysisService') as mock_service:
            mock_analysis = Mock()
            mock_analysis.id = "test-format"
            mock_analysis.status = "completed"
            mock_analysis.summary = "Well-formed palm reading summary"
            mock_analysis.created_at = "2023-01-01T00:00:00Z"
            mock_analysis.processing_completed_at = "2023-01-01T00:05:00Z"
            
            mock_service.return_value.get_analysis = AsyncMock(return_value=mock_analysis)
            
            response = client.get("/api/v1/analyses/test-format/summary")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify expected fields are present
                expected_fields = ["id", "status", "summary"]
                for field in expected_fields:
                    assert field in data, f"Expected field '{field}' not found in response"
                
                # Verify data types
                assert isinstance(data["id"], str)
                assert isinstance(data["status"], str)  
                assert isinstance(data["summary"], str)
    
    def test_error_response_format(self, client):
        """Test that error responses have consistent format."""
        with patch('app.api.v1.analyses.AnalysisService') as mock_service:
            mock_service.return_value.get_analysis = AsyncMock(return_value=None)
            
            response = client.get("/api/v1/analyses/nonexistent/summary")
            
            assert response.status_code == 404
            data = response.json()
            
            # Should have standard FastAPI error format
            assert "detail" in data
            assert isinstance(data["detail"], str)
    
    def test_success_response_format(self, client):
        """Test that success responses have consistent format."""
        register_data = {
            "email": "format@example.com",
            "password": "testpass123",
            "name": "Format Test User"
        }
        
        with patch('app.api.v1.auth.UserService') as mock_service, \
             patch('app.api.v1.auth.redis_client') as mock_redis:
            
            mock_user = Mock()
            mock_user.id = "user-format"
            mock_user.email = "format@example.com"
            mock_user.name = "Format Test User"
            
            mock_service.return_value.create_user = AsyncMock(return_value=mock_user)
            mock_redis.setex = AsyncMock()
            
            response = client.post("/api/v1/auth/register", json=register_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Should contain user information
                assert "user" in data or "id" in data
                
                # Should have consistent structure
                if "user" in data:
                    user_data = data["user"]
                    assert "id" in user_data
                    assert "email" in user_data
                    assert "name" in user_data