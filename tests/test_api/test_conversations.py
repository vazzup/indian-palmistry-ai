"""
Integration tests for conversation API endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.models.user import User
from app.models.analysis import Analysis
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return User(id=1, email="test@example.com", name="Test User")


@pytest.fixture
def mock_analysis():
    """Mock analysis."""
    return Analysis(id=1, user_id=1, summary="Test summary", full_report="Test report")


@pytest.fixture
def mock_conversation():
    """Mock conversation."""
    return Conversation(id=1, analysis_id=1, user_id=1, title="Test Conversation")


@pytest.mark.asyncio
class TestConversationsAPI:
    """Test conversation API endpoints."""
    
    def test_create_conversation_success(self, client, mock_user):
        """Test successful conversation creation."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.create_conversation') as mock_create:
            
            mock_get_user.return_value = mock_user
            
            mock_conversation = Conversation(
                id=1,
                analysis_id=1,
                user_id=1,
                title="My Palm Reading Questions"
            )
            mock_create.return_value = mock_conversation
            
            conv_data = {"title": "My Palm Reading Questions"}
            
            response = client.post(
                "/api/v1/analyses/1/conversations/",
                json=conv_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["analysis_id"] == 1
            assert data["title"] == "My Palm Reading Questions"
    
    def test_create_conversation_unauthenticated(self, client):
        """Test conversation creation without authentication."""
        conv_data = {"title": "Test Conversation"}
        
        response = client.post(
            "/api/v1/analyses/1/conversations/",
            json=conv_data
        )
        
        assert response.status_code == 401
    
    def test_create_conversation_analysis_not_found(self, client, mock_user):
        """Test conversation creation for non-existent analysis."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.create_conversation') as mock_create:
            
            mock_get_user.return_value = mock_user
            mock_create.side_effect = ValueError("Analysis not found or access denied")
            
            conv_data = {"title": "Test Conversation"}
            
            response = client.post(
                "/api/v1/analyses/999/conversations/",
                json=conv_data
            )
            
            assert response.status_code == 403
            data = response.json()
            assert "Analysis not found or access denied" in data["detail"]
    
    def test_list_conversations_success(self, client, mock_user):
        """Test listing conversations for an analysis."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.get_analysis_conversations') as mock_get_conversations:
            
            mock_get_user.return_value = mock_user
            
            mock_conversations = [
                Conversation(id=1, analysis_id=1, title="First Conversation"),
                Conversation(id=2, analysis_id=1, title="Second Conversation")
            ]
            mock_get_conversations.return_value = (mock_conversations, 2)
            
            response = client.get("/api/v1/analyses/1/conversations/?page=1&per_page=5")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["conversations"]) == 2
            assert data["total"] == 2
            assert data["analysis_id"] == 1
    
    def test_list_conversations_unauthenticated(self, client):
        """Test listing conversations without authentication."""
        response = client.get("/api/v1/analyses/1/conversations/")
        
        assert response.status_code == 401
    
    def test_get_conversation_success(self, client, mock_user, mock_conversation):
        """Test getting specific conversation."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv:
            
            mock_get_user.return_value = mock_user
            mock_get_conv.return_value = mock_conversation
            
            response = client.get("/api/v1/analyses/1/conversations/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["analysis_id"] == 1
    
    def test_get_conversation_not_found(self, client, mock_user):
        """Test getting non-existent conversation."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv:
            
            mock_get_user.return_value = mock_user
            mock_get_conv.return_value = None
            
            response = client.get("/api/v1/analyses/1/conversations/999")
            
            assert response.status_code == 404
            data = response.json()
            assert "Conversation not found" in data["detail"]
    
    def test_get_conversation_wrong_analysis(self, client, mock_user):
        """Test getting conversation from wrong analysis."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv:
            
            mock_get_user.return_value = mock_user
            
            # Conversation belongs to analysis 2, but we're accessing via analysis 1
            wrong_conversation = Conversation(id=1, analysis_id=2, user_id=1)
            mock_get_conv.return_value = wrong_conversation
            
            response = client.get("/api/v1/analyses/1/conversations/1")
            
            assert response.status_code == 404
    
    def test_get_conversation_messages_success(self, client, mock_user, mock_conversation):
        """Test getting conversation messages."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv, \
             patch('app.services.conversation_service.ConversationService.get_conversation_messages') as mock_get_msgs:
            
            mock_get_user.return_value = mock_user
            mock_get_conv.return_value = mock_conversation
            
            mock_messages = [
                Message(id=1, conversation_id=1, role=MessageRole.USER, content="Question"),
                Message(id=2, conversation_id=1, role=MessageRole.ASSISTANT, content="Answer")
            ]
            mock_get_msgs.return_value = (mock_messages, 2)
            
            response = client.get("/api/v1/analyses/1/conversations/1/messages")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["messages"]) == 2
            assert data["total"] == 2
            assert data["conversation_id"] == 1
    
    def test_talk_to_ai_success(self, client, mock_user, mock_conversation):
        """Test sending message and getting AI response."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.dependencies.auth.verify_csrf_token') as mock_verify_csrf, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv, \
             patch('app.services.conversation_service.ConversationService.add_message_and_respond') as mock_add_msg:
            
            mock_get_user.return_value = mock_user
            mock_verify_csrf.return_value = None  # CSRF verification passes
            mock_get_conv.return_value = mock_conversation
            
            # Mock message exchange
            user_msg = Message(
                id=1,
                conversation_id=1,
                role=MessageRole.USER,
                content="What does my heart line mean?"
            )
            ai_msg = Message(
                id=2,
                conversation_id=1,
                role=MessageRole.ASSISTANT,
                content="Your heart line indicates emotional stability...",
                tokens_used=75,
                cost=0.007
            )
            
            mock_add_msg.return_value = {
                "user_message": user_msg,
                "assistant_message": ai_msg,
                "tokens_used": 75,
                "cost": 0.007
            }
            
            talk_data = {"message": "What does my heart line mean?"}
            
            response = client.post(
                "/api/v1/analyses/1/conversations/1/talk",
                json=talk_data,
                headers={"X-CSRF-Token": "test-csrf-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["user_message"]["content"] == "What does my heart line mean?"
            assert "emotional stability" in data["assistant_message"]["content"]
            assert data["tokens_used"] == 75
            assert data["cost"] == 0.007
    
    def test_talk_to_ai_unauthenticated(self, client):
        """Test talking to AI without authentication."""
        talk_data = {"message": "Test question"}
        
        response = client.post(
            "/api/v1/analyses/1/conversations/1/talk",
            json=talk_data
        )
        
        assert response.status_code == 401
    
    def test_talk_to_ai_no_csrf_token(self, client, mock_user):
        """Test talking to AI without CSRF token."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            talk_data = {"message": "Test question"}
            
            response = client.post(
                "/api/v1/analyses/1/conversations/1/talk",
                json=talk_data
                # No CSRF token header
            )
            
            # Should fail due to CSRF verification
            assert response.status_code == 403
    
    def test_talk_to_ai_conversation_not_found(self, client, mock_user):
        """Test talking to AI with non-existent conversation."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.dependencies.auth.verify_csrf_token') as mock_verify_csrf, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv:
            
            mock_get_user.return_value = mock_user
            mock_verify_csrf.return_value = None
            mock_get_conv.return_value = None  # Conversation not found
            
            talk_data = {"message": "Test question"}
            
            response = client.post(
                "/api/v1/analyses/1/conversations/999/talk",
                json=talk_data,
                headers={"X-CSRF-Token": "test-csrf-token"}
            )
            
            assert response.status_code == 404
    
    def test_update_conversation_success(self, client, mock_user, mock_conversation):
        """Test updating conversation metadata."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.dependencies.auth.verify_csrf_token') as mock_verify_csrf, \
             patch('app.services.conversation_service.ConversationService.update_conversation_title') as mock_update, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv:
            
            mock_get_user.return_value = mock_user
            mock_verify_csrf.return_value = None
            mock_update.return_value = True
            
            updated_conversation = Conversation(
                id=1,
                analysis_id=1,
                user_id=1,
                title="Updated Title"
            )
            mock_get_conv.return_value = updated_conversation
            
            update_data = {"title": "Updated Title"}
            
            response = client.put(
                "/api/v1/analyses/1/conversations/1",
                json=update_data,
                headers={"X-CSRF-Token": "test-csrf-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Title"
    
    def test_update_conversation_not_found(self, client, mock_user):
        """Test updating non-existent conversation."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.dependencies.auth.verify_csrf_token') as mock_verify_csrf, \
             patch('app.services.conversation_service.ConversationService.update_conversation_title') as mock_update:
            
            mock_get_user.return_value = mock_user
            mock_verify_csrf.return_value = None
            mock_update.return_value = False  # Update failed (not found)
            
            update_data = {"title": "New Title"}
            
            response = client.put(
                "/api/v1/analyses/1/conversations/999",
                json=update_data,
                headers={"X-CSRF-Token": "test-csrf-token"}
            )
            
            assert response.status_code == 404
    
    def test_delete_conversation_success(self, client, mock_user, mock_conversation):
        """Test successful conversation deletion."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv, \
             patch('app.services.conversation_service.ConversationService.delete_conversation') as mock_delete:
            
            mock_get_user.return_value = mock_user
            mock_get_conv.return_value = mock_conversation
            mock_delete.return_value = True
            
            response = client.delete("/api/v1/analyses/1/conversations/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Conversation deleted successfully"
    
    def test_delete_conversation_not_found(self, client, mock_user):
        """Test deleting non-existent conversation."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user, \
             patch('app.services.conversation_service.ConversationService.get_conversation_by_id') as mock_get_conv:
            
            mock_get_user.return_value = mock_user
            mock_get_conv.return_value = None
            
            response = client.delete("/api/v1/analyses/1/conversations/999")
            
            assert response.status_code == 404
    
    def test_delete_conversation_unauthenticated(self, client):
        """Test deleting conversation without authentication."""
        response = client.delete("/api/v1/analyses/1/conversations/1")
        
        assert response.status_code == 401