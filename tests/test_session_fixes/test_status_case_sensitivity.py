"""
Tests for status case sensitivity fixes applied during debugging session.

These tests validate that status comparisons work correctly with lowercase
status values returned by the API.
"""
import pytest
from app.models.analysis import AnalysisStatus


class TestAnalysisStatusConsistency:
    """Test that analysis status values are consistent between backend and expected frontend usage."""
    
    def test_analysis_status_enum_values(self):
        """Test that AnalysisStatus enum has the expected lowercase values."""
        # The status values should be lowercase to match API responses
        assert AnalysisStatus.QUEUED.value == "queued"
        assert AnalysisStatus.PROCESSING.value == "processing" 
        assert AnalysisStatus.COMPLETED.value == "completed"
        assert AnalysisStatus.FAILED.value == "failed"
    
    def test_status_string_comparison(self):
        """Test status string comparisons work with lowercase values."""
        # These are the comparisons that were failing in frontend
        completed_status = "completed"
        failed_status = "failed"
        processing_status = "processing"
        
        # Test direct string comparisons
        assert completed_status == AnalysisStatus.COMPLETED.value
        assert failed_status == AnalysisStatus.FAILED.value
        assert processing_status == AnalysisStatus.PROCESSING.value
        
        # Test case sensitivity (uppercase should NOT match)
        assert completed_status != "COMPLETED"
        assert failed_status != "FAILED"
        assert processing_status != "PROCESSING"
    
    def test_case_insensitive_status_helper(self):
        """Test a helper function for case-insensitive status comparison if needed."""
        def normalize_status(status: str) -> str:
            """Normalize status string to lowercase for consistent comparison."""
            return status.lower() if status else ""
        
        # Test various case inputs
        test_cases = [
            ("COMPLETED", "completed"),
            ("completed", "completed"),
            ("Completed", "completed"),
            ("FAILED", "failed"),
            ("failed", "failed"),
            ("Failed", "failed"),
            ("PROCESSING", "processing"),
            ("processing", "processing")
        ]
        
        for input_status, expected in test_cases:
            assert normalize_status(input_status) == expected
    
    def test_status_validation(self):
        """Test that status validation accepts correct lowercase values."""
        valid_statuses = ["queued", "processing", "completed", "failed"]
        
        for status in valid_statuses:
            # Should not raise an exception
            assert status in [s.value for s in AnalysisStatus]
        
        # Invalid statuses
        invalid_statuses = ["COMPLETED", "FAILED", "invalid", "", None]
        for invalid_status in invalid_statuses:
            if invalid_status is not None:
                assert invalid_status not in [s.value for s in AnalysisStatus]


class TestBackendStatusConsistency:
    """Test that backend services return consistent status values."""
    
    @pytest.mark.asyncio
    async def test_analysis_service_status_format(self):
        """Test that AnalysisService returns properly formatted status values."""
        from unittest.mock import AsyncMock, Mock
        from app.services.analysis_service import AnalysisService
        from app.models.analysis import Analysis
        
        # Mock database session
        mock_session = AsyncMock()
        analysis_service = AnalysisService(mock_session)
        
        # Create mock analysis with different status values
        test_statuses = [
            AnalysisStatus.QUEUED,
            AnalysisStatus.PROCESSING, 
            AnalysisStatus.COMPLETED,
            AnalysisStatus.FAILED
        ]
        
        for status in test_statuses:
            mock_analysis = Mock(spec=Analysis)
            mock_analysis.id = f"test-{status.value}"
            mock_analysis.status = status
            mock_analysis.user_id = "test-user"
            
            # Mock the database query
            mock_session.get = AsyncMock(return_value=mock_analysis)
            
            result = await analysis_service.get_analysis(mock_analysis.id)
            
            # Verify status is returned as lowercase string
            assert result.status.value == status.value
            assert result.status.value.islower()
    
    def test_status_serialization_in_schemas(self):
        """Test that Pydantic schemas serialize status correctly."""
        from app.schemas.analysis import AnalysisResponse
        from datetime import datetime
        
        # Create test response data
        test_data = {
            "id": "test-123",
            "user_id": "user-456", 
            "status": "completed",  # lowercase as returned by API
            "summary": "Test summary",
            "full_report": "Test report",
            "created_at": datetime.now(),
            "processing_started_at": datetime.now(),
            "processing_completed_at": datetime.now(),
            "tokens_used": 100,
            "cost": 0.01
        }
        
        # Should serialize without error
        response = AnalysisResponse(**test_data)
        assert response.status == "completed"
        
        # Test all valid statuses
        for status in ["queued", "processing", "completed", "failed"]:
            test_data["status"] = status
            response = AnalysisResponse(**test_data)
            assert response.status == status


class TestFrontendStatusHandling:
    """Test utilities for frontend status handling (for reference)."""
    
    def test_status_display_mapping(self):
        """Test status display mapping for frontend UI."""
        # Mapping of backend status to user-friendly display
        status_display_map = {
            "queued": "Queued for Processing",
            "processing": "Analysis in Progress", 
            "completed": "Analysis Complete",
            "failed": "Analysis Failed"
        }
        
        # Test all mappings exist
        for status_value in [s.value for s in AnalysisStatus]:
            assert status_value in status_display_map
            assert len(status_display_map[status_value]) > 0
    
    def test_status_color_mapping(self):
        """Test status color mapping for frontend UI indicators."""
        status_color_map = {
            "queued": "yellow",
            "processing": "blue",
            "completed": "green", 
            "failed": "red"
        }
        
        # Test all statuses have color mappings
        for status_value in [s.value for s in AnalysisStatus]:
            assert status_value in status_color_map
    
    def test_is_terminal_status_helper(self):
        """Test helper function to determine if status is terminal (no further processing)."""
        def is_terminal_status(status: str) -> bool:
            """Check if analysis status is terminal (completed or failed)."""
            return status in ["completed", "failed"]
        
        # Test terminal statuses
        assert is_terminal_status("completed") == True
        assert is_terminal_status("failed") == True
        
        # Test non-terminal statuses
        assert is_terminal_status("queued") == False
        assert is_terminal_status("processing") == False
    
    def test_should_poll_status_helper(self):
        """Test helper function to determine if status should continue polling."""
        def should_continue_polling(status: str) -> bool:
            """Check if we should continue polling for status updates."""
            return status in ["queued", "processing"]
        
        # Test polling statuses
        assert should_continue_polling("queued") == True
        assert should_continue_polling("processing") == True
        
        # Test non-polling statuses  
        assert should_continue_polling("completed") == False
        assert should_continue_polling("failed") == False


class TestStatusConsistencyRegression:
    """Regression tests to prevent status case sensitivity issues from recurring."""
    
    def test_all_status_references_use_enum_values(self):
        """Test that status references use enum values rather than hardcoded strings."""
        # This test serves as documentation of correct usage
        correct_usage_examples = [
            # Correct: Using enum values
            ("completed", AnalysisStatus.COMPLETED.value),
            ("failed", AnalysisStatus.FAILED.value),
            ("processing", AnalysisStatus.PROCESSING.value),
            ("queued", AnalysisStatus.QUEUED.value),
        ]
        
        for expected, actual in correct_usage_examples:
            assert expected == actual
        
        # Examples of incorrect usage that should be avoided
        incorrect_hardcoded_strings = ["COMPLETED", "FAILED", "PROCESSING", "QUEUED"]
        for incorrect_string in incorrect_hardcoded_strings:
            # These should NOT match the enum values
            assert incorrect_string not in [s.value for s in AnalysisStatus]
    
    def test_database_model_status_consistency(self):
        """Test that database model status field matches enum values."""
        from app.models.analysis import Analysis
        
        # Create analysis with each status
        for status in AnalysisStatus:
            analysis = Analysis()
            analysis.status = status
            
            # Verify the status value is lowercase
            assert analysis.status.value.islower()
            assert analysis.status.value == status.value
    
    def test_api_response_status_format(self):
        """Test that API responses format status consistently."""
        from app.schemas.analysis import AnalysisStatusResponse
        from datetime import datetime
        
        # Test status response schema
        for status in AnalysisStatus:
            response_data = {
                "analysis_id": "test-123",
                "status": status.value,  # Should be lowercase
                "progress_percentage": 50,
                "message": f"Analysis is {status.value}",
                "updated_at": datetime.now()
            }
            
            response = AnalysisStatusResponse(**response_data)
            assert response.status == status.value
            assert response.status.islower()