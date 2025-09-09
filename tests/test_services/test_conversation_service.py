"""
Tests for conversation service functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.conversation_service import ConversationService
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole, MessageType
from app.models.analysis import Analysis


@pytest.fixture
def conversation_service():
    """Create conversation service instance for testing."""
    return ConversationService()


@pytest.mark.asyncio
class TestConversationService:
    """Test conversation service operations."""
    
    async def test_create_conversation_success(self, conversation_service):
        """Test successful conversation creation."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock analysis exists and belongs to user
            mock_analysis = Analysis(id=1, user_id=1)
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_analysis,  # Analysis query
            ]
            
            result = await conversation_service.create_conversation(
                analysis_id=1,
                user_id=1,
                title="Test Conversation"
            )
            
            # Verify database operations
            assert mock_db.add.called
            assert mock_db.commit.called
            assert mock_db.refresh.called
    
    async def test_create_conversation_analysis_not_found(self, conversation_service):
        """Test conversation creation when analysis doesn't exist."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock analysis doesn't exist
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            with pytest.raises(ValueError, match="Analysis not found or access denied"):
                await conversation_service.create_conversation(
                    analysis_id=999,
                    user_id=1
                )
    
    async def test_create_conversation_wrong_user(self, conversation_service):
        """Test conversation creation by wrong user."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock analysis belongs to different user
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            with pytest.raises(ValueError, match="Analysis not found or access denied"):
                await conversation_service.create_conversation(
                    analysis_id=1,
                    user_id=2  # Different user
                )
    
    async def test_create_conversation_default_title(self, conversation_service):
        """Test conversation creation with default title generation."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock analysis exists
            mock_analysis = Analysis(id=1, user_id=1)
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_analysis
            
            await conversation_service.create_conversation(
                analysis_id=1,
                user_id=1
                # No title provided
            )
            
            # Should generate default title
            add_call = mock_db.add.call_args[0][0]
            assert "Conversation about Palm Reading #1" in add_call.title
    
    async def test_get_conversation_by_id_success(self, conversation_service):
        """Test getting conversation by ID."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_conversation = Conversation(id=1, user_id=1, analysis_id=1)
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_conversation
            
            result = await conversation_service.get_conversation_by_id(1, 1)
            
            assert result == mock_conversation
    
    async def test_get_conversation_by_id_wrong_user(self, conversation_service):
        """Test getting conversation by wrong user."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # No conversation found for this user
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await conversation_service.get_conversation_by_id(1, 2)
            
            assert result is None
    
    async def test_get_analysis_conversations_with_pagination(self, conversation_service):
        """Test getting conversations for analysis with pagination."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock analysis access check
            mock_analysis = Analysis(id=1, user_id=1)
            
            # Mock count and paginated results
            mock_conversations = [
                Conversation(id=1, analysis_id=1),
                Conversation(id=2, analysis_id=1)
            ]
            
            # Setup multiple return values for different queries
            mock_count_result = MagicMock()
            mock_count_result.fetchall.return_value = [1, 2, 3]  # 3 total
            
            mock_paginated_result = MagicMock()
            mock_paginated_result.scalars.return_value.all.return_value = mock_conversations
            
            mock_db.execute.side_effect = [
                MagicMock(scalar_one_or_none=lambda: mock_analysis),  # Analysis check
                mock_count_result,  # Count query
                mock_paginated_result  # Paginated query
            ]
            
            conversations, total = await conversation_service.get_analysis_conversations(
                analysis_id=1,
                user_id=1,
                page=1,
                per_page=2
            )
            
            assert len(conversations) == 2
            assert total == 3
            assert conversations == mock_conversations
    
    async def test_get_analysis_conversations_no_access(self, conversation_service):
        """Test getting conversations when user has no access to analysis."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock no analysis access
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            conversations, total = await conversation_service.get_analysis_conversations(
                analysis_id=1,
                user_id=2,
                page=1,
                per_page=5
            )
            
            assert conversations == []
            assert total == 0
    
    async def test_add_message_and_respond_success(self, conversation_service):
        """Test adding user message and generating AI response."""
        with patch.object(conversation_service, 'get_conversation_by_id') as mock_get_conv, \
             patch.object(conversation_service, 'get_session') as mock_session, \
             patch.object(conversation_service.openai_service, 'generate_conversation_response') as mock_ai:
            
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock conversation and analysis
            mock_conversation = Conversation(id=1, analysis_id=1, user_id=1)
            mock_get_conv.return_value = mock_conversation
            
            mock_analysis = Analysis(
                id=1, 
                summary="Test summary", 
                full_report="Test report"
            )
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_analysis,  # Analysis query
                MagicMock(scalars=lambda: MagicMock(all=lambda: []))  # Messages query
            ]
            
            # Mock AI response
            mock_ai.return_value = {
                "response": "AI response",
                "tokens_used": 100,
                "cost": 0.01
            }
            
            result = await conversation_service.add_message_and_respond(
                conversation_id=1,
                user_id=1,
                user_message="Test question"
            )
            
            # Verify messages were added
            assert mock_db.add.call_count == 2  # User message + AI message
            assert mock_db.commit.call_count == 2
            assert mock_db.refresh.call_count == 2
            
            # Verify AI service was called
            mock_ai.assert_called_once()
            
            # Check result structure
            assert "user_message" in result
            assert "assistant_message" in result
            assert result["tokens_used"] == 100
            assert result["cost"] == 0.01
    
    async def test_add_message_and_respond_no_conversation(self, conversation_service):
        """Test adding message when conversation doesn't exist."""
        with patch.object(conversation_service, 'get_conversation_by_id') as mock_get_conv:
            mock_get_conv.return_value = None
            
            with pytest.raises(ValueError, match="Conversation not found or access denied"):
                await conversation_service.add_message_and_respond(
                    conversation_id=999,
                    user_id=1,
                    user_message="Test question"
                )
    
    async def test_update_conversation_title_success(self, conversation_service):
        """Test updating conversation title."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_conversation = Conversation(id=1, user_id=1, title="Old Title")
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_conversation
            
            result = await conversation_service.update_conversation_title(
                conversation_id=1,
                user_id=1,
                new_title="New Title"
            )
            
            assert result is True
            assert mock_conversation.title == "New Title"
            mock_db.commit.assert_called_once()
    
    async def test_update_conversation_title_not_found(self, conversation_service):
        """Test updating title for non-existent conversation."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await conversation_service.update_conversation_title(
                conversation_id=999,
                user_id=1,
                new_title="New Title"
            )
            
            assert result is False
    
    async def test_delete_conversation_success(self, conversation_service):
        """Test successful conversation deletion."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_conversation = Conversation(id=1, user_id=1)
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_conversation
            
            result = await conversation_service.delete_conversation(
                conversation_id=1,
                user_id=1
            )
            
            assert result is True
            mock_db.delete.assert_called_once_with(mock_conversation)
            mock_db.commit.assert_called_once()
    
    async def test_delete_conversation_not_found(self, conversation_service):
        """Test deleting non-existent conversation."""
        with patch.object(conversation_service, 'get_session') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            result = await conversation_service.delete_conversation(
                conversation_id=999,
                user_id=1
            )
            
            assert result is False
    
    async def test_get_conversation_messages_with_pagination(self, conversation_service):
        """Test getting conversation messages with pagination."""
        with patch.object(conversation_service, 'get_conversation_by_id') as mock_get_conv, \
             patch.object(conversation_service, 'get_session') as mock_session:
            
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock conversation exists
            mock_conversation = Conversation(id=1, user_id=1)
            mock_get_conv.return_value = mock_conversation
            
            # Mock messages
            mock_messages = [
                Message(id=1, conversation_id=1, role=MessageRole.USER, content="Question"),
                Message(id=2, conversation_id=1, role=MessageRole.ASSISTANT, content="Answer")
            ]
            
            # Mock count and paginated results
            mock_count_result = MagicMock()
            mock_count_result.fetchall.return_value = [1, 2]  # 2 total
            
            mock_paginated_result = MagicMock()
            mock_paginated_result.scalars.return_value.all.return_value = mock_messages
            
            mock_db.execute.side_effect = [mock_count_result, mock_paginated_result]
            
            messages, total = await conversation_service.get_conversation_messages(
                conversation_id=1,
                user_id=1,
                page=1,
                per_page=10
            )
            
            assert len(messages) == 2
            assert total == 2
            assert messages == mock_messages
    
    async def test_unified_contextual_response_method(self, conversation_service):
        """Test the unified contextual response method that replaces thread-specific logic."""
        with patch.object(conversation_service, 'get_conversation_by_id') as mock_get_conv, \
             patch.object(conversation_service, 'get_session') as mock_session, \
             patch.object(conversation_service, '_generate_contextual_response') as mock_generate:
            
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock conversation and analysis
            mock_conversation = Conversation(id=1, analysis_id=1, user_id=1)
            mock_get_conv.return_value = mock_conversation
            
            mock_analysis = Analysis(
                id=1, 
                summary="Test palm reading summary", 
                full_report="Detailed palm analysis",
                thread_id="test_thread_id"  # Has thread_id but should use unified method
            )
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_analysis,  # Analysis query
                MagicMock(scalars=lambda: MagicMock(all=lambda: []))  # Messages query (conversation history)
            ]
            
            # Mock the unified contextual response
            mock_generate.return_value = {
                "response": "Unified AI response about your palm",
                "tokens_used": 150,
                "cost": 0.015
            }
            
            result = await conversation_service.add_message_and_respond(
                conversation_id=1,
                user_id=1,
                user_message="What does this line mean?"
            )
            
            # Verify unified method was called instead of thread-specific logic
            mock_generate.assert_called_once_with(
                mock_analysis,
                "What does this line mean?",
                []  # conversation history
            )
            
            # Verify result contains unified response data
            assert result["assistant_message"]["content"] == "Unified AI response about your palm"
            assert result["tokens_used"] == 150
            assert result["cost"] == 0.015