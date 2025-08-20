"""
End-to-end integration tests for complete user workflows.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO
from app.main import app
from app.models.user import User
from app.models.analysis import Analysis, AnalysisStatus
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_image_file():
    """Create mock image file for upload."""
    return ("test_palm.jpg", BytesIO(b"fake_palm_image_data"), "image/jpeg")


@pytest.mark.asyncio
class TestCompleteWorkflow:
    """Test complete user workflows from start to finish."""
    
    def test_complete_user_journey_anonymous_to_authenticated(self, client, mock_image_file):
        """Test complete journey: anonymous upload -> analysis -> login -> full access -> conversation."""
        
        # Step 1: Anonymous user uploads palm image
        with patch('app.dependencies.auth.get_current_user_optional') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.create_analysis') as mock_create_analysis:
            
            mock_get_user.return_value = None  # Anonymous
            
            mock_analysis = Analysis(
                id=1,
                user_id=None,
                status=AnalysisStatus.QUEUED,
                job_id="test-job-id"
            )
            mock_create_analysis.return_value = mock_analysis
            
            response = client.post(
                "/api/v1/analyses/",
                files={"left_image": mock_image_file}
            )
            
            assert response.status_code == 200
            analysis_data = response.json()
            analysis_id = analysis_data["id"]
            assert analysis_data["user_id"] is None  # Anonymous
        
        # Step 2: Check analysis status (processing)
        with patch('app.services.analysis_service.AnalysisService.get_analysis_status') as mock_get_status:
            mock_processing_analysis = Analysis(
                id=analysis_id,
                status=AnalysisStatus.PROCESSING,
                error_message=None
            )
            mock_get_status.return_value = mock_processing_analysis
            
            response = client.get(f"/api/v1/analyses/{analysis_id}/status")
            
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "processing"
            assert status_data["progress"] == 50
        
        # Step 3: Get analysis summary (public, no auth required)
        with patch('app.services.analysis_service.AnalysisService.get_analysis_by_id') as mock_get_analysis:
            mock_completed_analysis = Analysis(
                id=analysis_id,
                summary="You have strong life and heart lines indicating...",
                status=AnalysisStatus.COMPLETED,
                created_at="2023-01-01T00:00:00"
            )
            mock_get_analysis.return_value = mock_completed_analysis
            
            response = client.get(f"/api/v1/analyses/{analysis_id}/summary")
            
            assert response.status_code == 200
            summary_data = response.json()
            assert "strong life and heart lines" in summary_data["summary"]
            assert summary_data["requires_login"] is True
        
        # Step 4: User registers to access full report
        with patch('app.services.user_service.UserService.create_user') as mock_create_user, \
             patch('app.dependencies.auth.generate_session_id') as mock_session_id, \
             patch('app.dependencies.auth.generate_csrf_token') as mock_csrf, \
             patch('app.core.redis.session_manager.create_session') as mock_session:
            
            mock_user = User(
                id=1,
                email="test@example.com",
                name="Test User"
            )
            mock_create_user.return_value = mock_user
            mock_session_id.return_value = "test-session-id"
            mock_csrf.return_value = "test-csrf-token"
            mock_session.return_value = True
            
            register_data = {
                "email": "test@example.com",
                "password": "testpass123",
                "name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=register_data)
            
            assert response.status_code == 200
            auth_data = response.json()
            assert auth_data["success"] is True
            csrf_token = auth_data["csrf_token"]
            
            # Save session cookie for subsequent requests
            session_cookie = response.cookies["session_id"]
        
        # Step 5: Access full analysis report (now authenticated)
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.get_analysis_by_id') as mock_get_analysis:
            
            mock_get_user.return_value = User(id=1, email="test@example.com")
            
            mock_full_analysis = Analysis(
                id=analysis_id,
                user_id=None,  # Still anonymous analysis, but user is now authenticated
                summary="You have strong life and heart lines...",
                full_report="Detailed analysis: Your life line indicates longevity and vitality...",
                status=AnalysisStatus.COMPLETED
            )
            mock_get_analysis.return_value = mock_full_analysis
            
            client.cookies.set("session_id", session_cookie)
            
            response = client.get(f"/api/v1/analyses/{analysis_id}")
            
            assert response.status_code == 200
            full_data = response.json()
            assert "Detailed analysis" in full_data["full_report"]
        
        # Step 6: Create conversation about the analysis
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.create_conversation') as mock_create_conv:
            
            mock_get_user.return_value = User(id=1, email="test@example.com")
            
            mock_conversation = Conversation(
                id=1,
                analysis_id=analysis_id,
                user_id=1,
                title="Questions about my palm reading"
            )
            mock_create_conv.return_value = mock_conversation
            
            conv_data = {"title": "Questions about my palm reading"}
            
            response = client.post(
                f"/api/v1/analyses/{analysis_id}/conversations/",
                json=conv_data
            )
            
            assert response.status_code == 200
            conversation_data = response.json()
            conversation_id = conversation_data["id"]
            assert conversation_data["title"] == "Questions about my palm reading"
        
        # Step 7: Ask follow-up question in conversation
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.dependencies.auth.verify_csrf_token') as mock_verify_csrf, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv, \
             patch('app.services.conversation_service.ConversationService.add_message_and_respond') as mock_add_msg:
            
            mock_get_user.return_value = User(id=1, email="test@example.com")
            mock_verify_csrf.return_value = None  # CSRF passes
            
            mock_conversation = Conversation(
                id=conversation_id,
                analysis_id=analysis_id,
                user_id=1
            )
            mock_get_conv.return_value = mock_conversation
            
            # Mock message exchange
            user_msg = Message(
                id=1,
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content="What does my heart line tell you about my relationships?"
            )
            ai_msg = Message(
                id=2,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content="Based on your heart line, you tend to be emotionally expressive...",
                tokens_used=85,
                cost=0.008
            )
            
            mock_add_msg.return_value = {
                "user_message": user_msg,
                "assistant_message": ai_msg,
                "tokens_used": 85,
                "cost": 0.008
            }
            
            talk_data = {"message": "What does my heart line tell you about my relationships?"}
            
            response = client.post(
                f"/api/v1/analyses/{analysis_id}/conversations/{conversation_id}/talk",
                json=talk_data,
                headers={"X-CSRF-Token": csrf_token}
            )
            
            assert response.status_code == 200
            talk_response = response.json()
            assert "emotionally expressive" in talk_response["assistant_message"]["content"]
            assert talk_response["tokens_used"] == 85
        
        # Step 8: Get conversation messages
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv, \
             patch('app.services.conversation_service.ConversationService.get_conversation_messages') as mock_get_msgs:
            
            mock_get_user.return_value = User(id=1, email="test@example.com")
            mock_get_conv.return_value = mock_conversation
            
            messages = [user_msg, ai_msg]
            mock_get_msgs.return_value = (messages, 2)
            
            response = client.get(
                f"/api/v1/analyses/{analysis_id}/conversations/{conversation_id}/messages"
            )
            
            assert response.status_code == 200
            messages_data = response.json()
            assert len(messages_data["messages"]) == 2
            assert messages_data["total"] == 2
        
        print("✅ Complete workflow test passed: Anonymous upload → Registration → Full access → Conversation")
    
    def test_authenticated_user_complete_workflow(self, client, mock_image_file):
        """Test workflow for already authenticated user."""
        
        # Step 1: User is already logged in
        mock_user = User(id=2, email="existing@example.com", name="Existing User")
        
        # Step 2: Upload palm images (both left and right)
        with patch('app.dependencies.auth.get_current_user_optional') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.create_analysis') as mock_create_analysis:
            
            mock_get_user.return_value = mock_user
            
            mock_analysis = Analysis(
                id=2,
                user_id=2,
                left_image_path="user_2/analysis_2/left.jpg",
                right_image_path="user_2/analysis_2/right.jpg",
                status=AnalysisStatus.QUEUED,
                job_id="auth-user-job-id"
            )
            mock_create_analysis.return_value = mock_analysis
            
            left_file = ("left_palm.jpg", BytesIO(b"left_image_data"), "image/jpeg")
            right_file = ("right_palm.jpg", BytesIO(b"right_image_data"), "image/jpeg")
            
            response = client.post(
                "/api/v1/analyses/",
                files={"left_image": left_file, "right_image": right_file}
            )
            
            assert response.status_code == 200
            analysis_data = response.json()
            analysis_id = analysis_data["id"]
            assert analysis_data["user_id"] == 2
            assert analysis_data["left_image_path"] is not None
            assert analysis_data["right_image_path"] is not None
        
        # Step 3: List user's analyses
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.get_user_analyses') as mock_get_analyses:
            
            mock_get_user.return_value = mock_user
            
            user_analyses = [
                Analysis(id=2, user_id=2, status=AnalysisStatus.COMPLETED),
                Analysis(id=3, user_id=2, status=AnalysisStatus.PROCESSING)
            ]
            mock_get_analyses.return_value = (user_analyses, 2)
            
            response = client.get("/api/v1/analyses/?page=1&per_page=5")
            
            assert response.status_code == 200
            list_data = response.json()
            assert len(list_data["analyses"]) == 2
            assert list_data["total"] == 2
        
        # Step 4: Access completed analysis immediately (no summary step needed)
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.get_analysis_by_id') as mock_get_analysis:
            
            mock_get_user.return_value = mock_user
            
            mock_completed_analysis = Analysis(
                id=analysis_id,
                user_id=2,
                summary="Your palms show balanced energy...",
                full_report="Comprehensive reading of both palms reveals...",
                status=AnalysisStatus.COMPLETED,
                tokens_used=150,
                cost=0.015
            )
            mock_get_analysis.return_value = mock_completed_analysis
            
            response = client.get(f"/api/v1/analyses/{analysis_id}")
            
            assert response.status_code == 200
            full_data = response.json()
            assert "Comprehensive reading" in full_data["full_report"]
            assert full_data["tokens_used"] == 150
        
        print("✅ Authenticated user workflow test passed: Upload → Analysis → Access")
    
    def test_error_handling_workflow(self, client, mock_image_file):
        """Test workflow with various error scenarios."""
        
        # Step 1: Try to upload without images
        response = client.post("/api/v1/analyses/")
        assert response.status_code == 400
        assert "At least one palm image is required" in response.json()["detail"]
        
        # Step 2: Try to access non-existent analysis
        response = client.get("/api/v1/analyses/999/summary")
        assert response.status_code == 404
        
        # Step 3: Try authenticated endpoint without authentication
        response = client.get("/api/v1/analyses/1")
        assert response.status_code == 401
        
        # Step 4: Try to access analysis owned by different user
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.get_analysis_by_id') as mock_get_analysis:
            
            mock_get_user.return_value = User(id=1, email="user1@example.com")
            
            # Analysis belongs to user 2, but user 1 is trying to access it
            mock_analysis = Analysis(id=1, user_id=2, status=AnalysisStatus.COMPLETED)
            mock_get_analysis.return_value = mock_analysis
            
            response = client.get("/api/v1/analyses/1")
            assert response.status_code == 403
            assert "permission" in response.json()["detail"]
        
        print("✅ Error handling workflow test passed")
    
    def test_background_job_status_tracking(self, client, mock_image_file):
        """Test background job status tracking workflow."""
        
        # Step 1: Create analysis (starts as QUEUED)
        with patch('app.dependencies.auth.get_current_user_optional') as mock_get_user, \
             patch('app.services.analysis_service.AnalysisService.create_analysis') as mock_create_analysis:
            
            mock_get_user.return_value = None
            
            mock_analysis = Analysis(
                id=3,
                status=AnalysisStatus.QUEUED,
                job_id="status-tracking-job-id"
            )
            mock_create_analysis.return_value = mock_analysis
            
            response = client.post(
                "/api/v1/analyses/",
                files={"left_image": mock_image_file}
            )
            
            assert response.status_code == 200
            analysis_id = response.json()["id"]
        
        # Step 2: Check status (QUEUED)
        with patch('app.services.analysis_service.AnalysisService.get_analysis_status') as mock_get_status:
            mock_queued_analysis = Analysis(id=analysis_id, status=AnalysisStatus.QUEUED)
            mock_get_status.return_value = mock_queued_analysis
            
            response = client.get(f"/api/v1/analyses/{analysis_id}/status")
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "queued"
            assert status_data["progress"] == 10
        
        # Step 3: Check status (PROCESSING)
        with patch('app.services.analysis_service.AnalysisService.get_analysis_status') as mock_get_status:
            mock_processing_analysis = Analysis(id=analysis_id, status=AnalysisStatus.PROCESSING)
            mock_get_status.return_value = mock_processing_analysis
            
            response = client.get(f"/api/v1/analyses/{analysis_id}/status")
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "processing"
            assert status_data["progress"] == 50
        
        # Step 4: Check status (COMPLETED)
        with patch('app.services.analysis_service.AnalysisService.get_analysis_status') as mock_get_status:
            mock_completed_analysis = Analysis(id=analysis_id, status=AnalysisStatus.COMPLETED)
            mock_get_status.return_value = mock_completed_analysis
            
            response = client.get(f"/api/v1/analyses/{analysis_id}/status")
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "completed"
            assert status_data["progress"] == 100
        
        # Step 5: Check status (FAILED)
        with patch('app.services.analysis_service.AnalysisService.get_analysis_status') as mock_get_status:
            mock_failed_analysis = Analysis(
                id=analysis_id,
                status=AnalysisStatus.FAILED,
                error_message="OpenAI API quota exceeded"
            )
            mock_get_status.return_value = mock_failed_analysis
            
            response = client.get(f"/api/v1/analyses/{analysis_id}/status")
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "failed"
            assert status_data["progress"] == 0
            assert "quota exceeded" in status_data["error_message"]
        
        print("✅ Background job status tracking test passed")