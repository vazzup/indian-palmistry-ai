"""
Tests for Enhanced Conversation Service.

This module tests the context-aware conversation service with memory preservation,
search functionality, export capabilities, and conversation analytics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from app.services.enhanced_conversation_service import EnhancedConversationService, ConversationTemplate
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.analysis import Analysis


class TestEnhancedConversationService:
    """Test suite for EnhancedConversationService class."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return EnhancedConversationService()

    @pytest.fixture
    def mock_conversation(self):
        """Mock conversation object."""
        conversation = MagicMock(spec=Conversation)
        conversation.id = 123
        conversation.user_id = 456
        conversation.analysis_id = 789
        conversation.title = "Test Conversation"
        conversation.created_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        return conversation

    @pytest.fixture
    def mock_messages(self):
        """Mock message objects."""
        messages = []
        base_time = datetime.utcnow()
        
        for i in range(3):
            message = MagicMock(spec=Message)
            message.id = i + 1
            message.conversation_id = 123
            message.content = f"Message {i + 1}"
            message.is_ai = i % 2 == 1  # Alternate between user and AI
            message.created_at = base_time + timedelta(minutes=i)
            messages.append(message)
        
        return messages

    @pytest.fixture
    def mock_analysis(self):
        """Mock analysis object."""
        analysis = MagicMock(spec=Analysis)
        analysis.id = 789
        analysis.user_id = 456
        analysis.result = {
            "lines": {
                "life_line": "Strong life line analysis",
                "love_line": "Complex love patterns"
            },
            "summary": "Overall palm reading summary"
        }
        return analysis

    @pytest.mark.asyncio
    async def test_create_contextual_response_success(self, service, mock_conversation, mock_messages, mock_analysis):
        """Test successful contextual response creation."""
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv, \
             patch.object(service, '_get_analysis_by_id') as mock_get_analysis, \
             patch.object(service, '_get_conversation_history') as mock_get_history, \
             patch.object(service, 'openai_service') as mock_openai, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_conv.return_value = mock_conversation
            mock_get_analysis.return_value = mock_analysis
            mock_get_history.return_value = mock_messages
            mock_cache.get.return_value = None  # Cache miss
            
            mock_openai.generate_response.return_value = {
                "response": "Based on your palm analysis, I can see...",
                "confidence": 0.9,
                "context_used": True
            }
            
            result = await service.create_contextual_response(
                123, "What does my life line mean?", 456, context_window=5
            )
            
            assert "ai_response" in result
            assert "context_summary" in result
            assert "confidence" in result
            assert result["ai_response"] == "Based on your palm analysis, I can see..."
            assert result["confidence"] == 0.9
            
            # Verify caching
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_contextual_response_cached(self, service, mock_conversation):
        """Test cached contextual response."""
        cached_response = {
            "ai_response": "Cached response",
            "confidence": 0.85,
            "context_summary": "Cached context"
        }
        
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_conv.return_value = mock_conversation
            mock_cache.get.return_value = cached_response
            
            result = await service.create_contextual_response(123, "Test message", 456)
            
            assert result == cached_response
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_contextual_response_unauthorized(self, service, mock_conversation):
        """Test unauthorized access to conversation."""
        mock_conversation.user_id = 999  # Different user
        
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv:
            mock_get_conv.return_value = mock_conversation
            
            with pytest.raises(ValueError, match="Unauthorized"):
                await service.create_contextual_response(123, "Test message", 456)

    @pytest.mark.asyncio
    async def test_get_conversation_templates_success(self, service):
        """Test conversation templates retrieval."""
        with patch.object(service, 'cache_service') as mock_cache:
            mock_cache.get.return_value = None  # Cache miss
            
            result = await service.get_conversation_templates()
            
            assert "templates" in result
            assert len(result["templates"]) == len(ConversationTemplate)
            
            # Check specific templates
            template_types = [t["template_type"] for t in result["templates"]]
            assert "life_insights" in template_types
            assert "relationship_guidance" in template_types
            assert "career_guidance" in template_types
            
            # Verify caching
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_conversation_templates_cached(self, service):
        """Test cached conversation templates."""
        cached_templates = {
            "templates": [{"template_type": "cached", "title": "Cached Template"}]
        }
        
        with patch.object(service, 'cache_service') as mock_cache:
            mock_cache.get.return_value = cached_templates
            
            result = await service.get_conversation_templates()
            
            assert result == cached_templates
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_conversations_success(self, service):
        """Test successful conversation search."""
        search_results = [
            MagicMock(
                conversation_id=123,
                title="Palm Reading Discussion",
                content="What does my life line mean?",
                created_at=datetime.utcnow(),
                relevance_score=0.9
            )
        ]
        
        with patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock database text search query
            mock_result = AsyncMock()
            mock_result.all.return_value = search_results
            mock_db.execute.return_value = mock_result
            
            result = await service.search_conversations(456, "life line", limit=10)
            
            assert "results" in result
            assert "total_count" in result
            assert "search_query" in result
            assert len(result["results"]) == 1
            assert result["results"][0]["conversation_id"] == 123
            assert result["search_query"] == "life line"

    @pytest.mark.asyncio
    async def test_search_conversations_empty_query(self, service):
        """Test search with empty query."""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await service.search_conversations(456, "")

    @pytest.mark.asyncio
    async def test_export_conversation_json(self, service, mock_conversation, mock_messages):
        """Test conversation export in JSON format."""
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv, \
             patch.object(service, '_get_conversation_messages') as mock_get_messages:
            
            mock_get_conv.return_value = mock_conversation
            mock_get_messages.return_value = mock_messages
            
            result = await service.export_conversation(123, "json", user_id=456)
            
            assert result["format"] == "json"
            assert "data" in result
            assert result["data"]["conversation_id"] == 123
            assert len(result["data"]["messages"]) == 3

    @pytest.mark.asyncio
    async def test_export_conversation_markdown(self, service, mock_conversation, mock_messages):
        """Test conversation export in Markdown format."""
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv, \
             patch.object(service, '_get_conversation_messages') as mock_get_messages:
            
            mock_get_conv.return_value = mock_conversation
            mock_get_messages.return_value = mock_messages
            
            result = await service.export_conversation(123, "markdown", user_id=456)
            
            assert result["format"] == "markdown"
            assert "data" in result
            assert "# Test Conversation" in result["data"]
            assert "**User:** Message 1" in result["data"]
            assert "**AI:** Message 2" in result["data"]

    @pytest.mark.asyncio
    async def test_export_conversation_text(self, service, mock_conversation, mock_messages):
        """Test conversation export in text format."""
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv, \
             patch.object(service, '_get_conversation_messages') as mock_get_messages:
            
            mock_get_conv.return_value = mock_conversation
            mock_get_messages.return_value = mock_messages
            
            result = await service.export_conversation(123, "text", user_id=456)
            
            assert result["format"] == "text"
            assert "data" in result
            assert "Test Conversation" in result["data"]
            assert "User: Message 1" in result["data"]
            assert "AI: Message 2" in result["data"]

    @pytest.mark.asyncio
    async def test_export_conversation_unsupported_format(self, service, mock_conversation):
        """Test export with unsupported format."""
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv:
            mock_get_conv.return_value = mock_conversation
            
            with pytest.raises(ValueError, match="Unsupported export format"):
                await service.export_conversation(123, "pdf", user_id=456)

    @pytest.mark.asyncio
    async def test_get_conversation_analytics_success(self, service):
        """Test conversation analytics retrieval."""
        with patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock multiple database queries for analytics
            mock_results = [
                AsyncMock(scalar=lambda: 25),  # total_conversations
                AsyncMock(scalar=lambda: 150), # total_messages
                AsyncMock(scalar=lambda: 2.5), # avg_messages_per_conversation
                AsyncMock(),  # recent_activity
                AsyncMock()   # popular_topics
            ]
            
            mock_results[3].all.return_value = [
                MagicMock(date=datetime.utcnow().date(), count=5)
            ]
            mock_results[4].all.return_value = [
                MagicMock(topic="life line", count=10)
            ]
            
            mock_db.execute.side_effect = mock_results
            
            result = await service.get_conversation_analytics(456, days=30)
            
            assert "summary" in result
            assert "recent_activity" in result
            assert "popular_topics" in result
            assert result["summary"]["total_conversations"] == 25
            assert result["summary"]["total_messages"] == 150

    @pytest.mark.asyncio
    async def test_build_context_from_history(self, service, mock_messages, mock_analysis):
        """Test context building from conversation history."""
        context = await service._build_context_from_history(
            mock_messages, mock_analysis, context_window=3
        )
        
        assert "conversation_history" in context
        assert "palm_analysis_summary" in context
        assert "key_topics" in context
        assert len(context["conversation_history"]) <= 3

    @pytest.mark.asyncio
    async def test_extract_key_topics(self, service, mock_messages):
        """Test key topic extraction from messages."""
        topics = await service._extract_key_topics(mock_messages)
        
        assert isinstance(topics, list)
        # Should extract meaningful words, not common stopwords
        assert all(len(topic) > 2 for topic in topics)

    @pytest.mark.asyncio
    async def test_template_prompts(self, service):
        """Test that different templates have appropriate prompts."""
        templates_data = await service._get_template_data()
        
        # Verify each template has required fields
        for template in templates_data:
            assert "template_type" in template
            assert "title" in template
            assert "description" in template
            assert "starter_questions" in template
            assert isinstance(template["starter_questions"], list)
            assert len(template["starter_questions"]) > 0

    @pytest.mark.asyncio
    async def test_context_window_limiting(self, service, mock_conversation, mock_analysis):
        """Test context window size limiting."""
        # Create many messages
        many_messages = []
        for i in range(20):
            message = MagicMock(spec=Message)
            message.content = f"Message {i}"
            message.is_ai = i % 2 == 1
            message.created_at = datetime.utcnow() + timedelta(minutes=i)
            many_messages.append(message)
        
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv, \
             patch.object(service, '_get_analysis_by_id') as mock_get_analysis, \
             patch.object(service, '_get_conversation_history') as mock_get_history, \
             patch.object(service, 'openai_service') as mock_openai, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_conv.return_value = mock_conversation
            mock_get_analysis.return_value = mock_analysis
            mock_get_history.return_value = many_messages
            mock_cache.get.return_value = None
            
            mock_openai.generate_response.return_value = {
                "response": "Test response",
                "confidence": 0.8
            }
            
            # Test with small context window
            await service.create_contextual_response(
                123, "Test message", 456, context_window=5
            )
            
            # Verify context was limited
            call_args = mock_openai.generate_response.call_args
            context = call_args[0][1]  # Second argument is context
            
            # Should only include last 5 messages in history
            assert len(context["conversation_history"]) <= 5

    @pytest.mark.asyncio
    async def test_error_handling(self, service, mock_conversation):
        """Test comprehensive error handling."""
        # Test conversation not found
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv:
            mock_get_conv.return_value = None
            
            with pytest.raises(ValueError, match="Conversation not found"):
                await service.create_contextual_response(999, "Test", 456)
        
        # Test OpenAI service failure
        with patch.object(service, '_get_conversation_by_id') as mock_get_conv, \
             patch.object(service, '_get_analysis_by_id') as mock_get_analysis, \
             patch.object(service, '_get_conversation_history') as mock_get_history, \
             patch.object(service, 'openai_service') as mock_openai, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_conv.return_value = mock_conversation
            mock_get_analysis.return_value = mock_analysis
            mock_get_history.return_value = []
            mock_cache.get.return_value = None
            mock_openai.generate_response.side_effect = Exception("OpenAI API error")
            
            with pytest.raises(Exception):
                await service.create_contextual_response(123, "Test", 456)