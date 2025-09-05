"""
Tests for OpenAI service functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.openai_service import OpenAIService
from pathlib import Path
import json


@pytest.fixture
def openai_service():
    """Create OpenAI service instance for testing."""
    with patch('app.services.openai_service.settings') as mock_settings:
        mock_settings.openai_api_key = "test-api-key"
        return OpenAIService()


@pytest.fixture
def openai_service_no_key():
    """Create OpenAI service instance without API key."""
    with patch('app.services.openai_service.settings') as mock_settings:
        mock_settings.openai_api_key = None
        return OpenAIService()


@pytest.mark.asyncio
class TestOpenAIService:
    """Test OpenAI service operations."""
    
    def test_init_with_api_key(self, openai_service):
        """Test initialization with API key."""
        assert openai_service.client is not None
    
    def test_init_without_api_key(self, openai_service_no_key):
        """Test initialization without API key."""
        assert openai_service_no_key.client is None
    
    def test_encode_image_success(self, openai_service):
        """Test successful image encoding."""
        with patch('app.services.openai_service.Path') as mock_path_class, \
             patch('builtins.open', create=True) as mock_open, \
             patch('base64.b64encode') as mock_b64:
            
            # Mock file operations
            mock_path = MagicMock()
            mock_path_class.return_value.__truediv__.return_value = mock_path
            
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_file.read.return_value = b"image_data"
            
            mock_b64.return_value = b"encoded_data"
            
            result = openai_service._encode_image("test/path.jpg")
            
            assert result == "encoded_data"
            mock_b64.assert_called_once_with(b"image_data")
    
    def test_encode_image_file_not_found(self, openai_service):
        """Test image encoding when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = openai_service._encode_image("nonexistent.jpg")
            assert result is None
    
    async def test_analyze_palm_images_no_client(self, openai_service_no_key):
        """Test analysis when no OpenAI client is configured."""
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            await openai_service_no_key.analyze_palm_images("test.jpg")
    
    async def test_analyze_palm_images_no_images(self, openai_service):
        """Test analysis when no images are provided."""
        with pytest.raises(ValueError, match="At least one palm image is required"):
            await openai_service.analyze_palm_images()
    
    async def test_analyze_palm_images_success_single_image(self, openai_service):
        """Test successful palm analysis with single image."""
        with patch.object(openai_service, '_encode_image') as mock_encode, \
             patch.object(openai_service.client.chat.completions, 'create') as mock_create:
            
            # Mock image encoding
            mock_encode.return_value = "encoded_image_data"
            
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps({
                "summary": "Test summary",
                "full_report": "Test full report",
                "key_features": ["line1", "line2"],
                "strengths": ["strength1"],
                "guidance": ["guidance1"]
            })
            mock_response.usage.total_tokens = 150
            mock_create.return_value = mock_response
            
            result = await openai_service.analyze_palm_images(
                left_image_path="test_left.jpg"
            )
            
            # Verify result structure
            assert result["summary"] == "Test summary"
            assert result["full_report"] == "Test full report"
            assert result["tokens_used"] == 150
            assert "cost" in result
            
            # Verify OpenAI API was called correctly
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["model"] == "gpt-4o-mini"
            assert len(call_args["messages"]) == 2
            assert "left palm" in call_args["messages"][1]["content"][0]["text"]
    
    async def test_analyze_palm_images_success_both_images(self, openai_service):
        """Test successful palm analysis with both images."""
        with patch.object(openai_service, '_encode_image') as mock_encode, \
             patch.object(openai_service.client.chat.completions, 'create') as mock_create:
            
            # Mock image encoding
            mock_encode.return_value = "encoded_image_data"
            
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps({
                "summary": "Test summary",
                "full_report": "Test full report"
            })
            mock_response.usage.total_tokens = 200
            mock_create.return_value = mock_response
            
            result = await openai_service.analyze_palm_images(
                left_image_path="test_left.jpg",
                right_image_path="test_right.jpg"
            )
            
            # Verify both images were processed
            assert mock_encode.call_count == 2
            
            # Verify API call mentions both palms
            call_args = mock_create.call_args[1]
            assert "left palm and right palm" in call_args["messages"][1]["content"][0]["text"]
            
            # Verify result
            assert result["tokens_used"] == 200
    
    async def test_analyze_palm_images_markdown_json_response(self, openai_service):
        """Test analysis with JSON wrapped in markdown code blocks (session fix)."""
        with patch.object(openai_service, '_encode_image') as mock_encode, \
             patch.object(openai_service.client.chat.completions, 'create') as mock_create:
            
            # Mock image encoding
            mock_encode.return_value = "encoded_image_data"
            
            # Mock OpenAI response with markdown-wrapped JSON (the actual issue found)
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '''```json
{
    "summary": "Your life line indicates strong vitality and longevity",
    "full_report": "Based on traditional Indian palmistry (Hast Rekha Shastra), your palm reveals strength"
}
```'''
            mock_response.usage.total_tokens = 100
            mock_create.return_value = mock_response
            
            result = await openai_service.analyze_palm_images(
                left_image_path="test_left.jpg"
            )
            
            # Should properly parse the JSON from markdown
            assert result["summary"] == "Your life line indicates strong vitality and longevity"
            assert result["full_report"] == "Based on traditional Indian palmistry (Hast Rekha Shastra), your palm reveals strength"
            assert result["tokens_used"] == 100
    
    async def test_analyze_palm_images_invalid_json_response(self, openai_service):
        """Test analysis with invalid JSON response from OpenAI."""
        with patch.object(openai_service, '_encode_image') as mock_encode, \
             patch.object(openai_service.client.chat.completions, 'create') as mock_create:
            
            # Mock image encoding
            mock_encode.return_value = "encoded_image_data"
            
            # Mock OpenAI response with invalid JSON
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Invalid JSON response from AI"
            mock_response.usage.total_tokens = 100
            mock_create.return_value = mock_response
            
            result = await openai_service.analyze_palm_images(
                left_image_path="test_left.jpg"
            )
            
            # Should fall back to using raw response
            assert result["summary"] == "Invalid JSON response from AI"
            assert result["full_report"] == "Invalid JSON response from AI"
            assert result["tokens_used"] == 100
    
    async def test_analyze_palm_images_encoding_failure(self, openai_service):
        """Test analysis when image encoding fails."""
        with patch.object(openai_service, '_encode_image') as mock_encode:
            # Mock encoding failure
            mock_encode.return_value = None
            
            with pytest.raises(ValueError, match="Unable to process palm images"):
                await openai_service.analyze_palm_images(
                    left_image_path="test_left.jpg"
                )
    
    async def test_analyze_palm_images_openai_api_error(self, openai_service):
        """Test analysis when OpenAI API returns error."""
        with patch.object(openai_service, '_encode_image') as mock_encode, \
             patch.object(openai_service.client.chat.completions, 'create') as mock_create:
            
            # Mock image encoding
            mock_encode.return_value = "encoded_image_data"
            
            # Mock OpenAI API error
            mock_create.side_effect = Exception("OpenAI API Error")
            
            with pytest.raises(Exception, match="OpenAI API Error"):
                await openai_service.analyze_palm_images(
                    left_image_path="test_left.jpg"
                )
    
    def test_calculate_cost(self, openai_service):
        """Test cost calculation."""
        # Test with 1000 tokens (should use pricing formula)
        cost = openai_service._calculate_cost(1000)
        
        # Expected: 70% input (700 * 0.00015/1000) + 30% output (300 * 0.0006/1000)
        expected = (700 * 0.00015/1000) + (300 * 0.0006/1000)
        assert abs(cost - expected) < 0.000001  # Allow for floating point precision
    
    async def test_generate_conversation_response_no_client(self, openai_service_no_key):
        """Test conversation response when no client is configured."""
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            await openai_service_no_key.generate_conversation_response(
                "summary", "report", [], "question"
            )
    
    async def test_generate_conversation_response_success(self, openai_service):
        """Test successful conversation response generation."""
        with patch.object(openai_service.client.chat.completions, 'create') as mock_create:
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "AI response to question"
            mock_response.usage.total_tokens = 75
            mock_create.return_value = mock_response
            
            result = await openai_service.generate_conversation_response(
                analysis_summary="Test summary",
                analysis_full_report="Test full report",
                conversation_history=[
                    {"role": "user", "content": "Previous question"},
                    {"role": "assistant", "content": "Previous answer"}
                ],
                user_question="New question"
            )
            
            # Verify result
            assert result["response"] == "AI response to question"
            assert result["tokens_used"] == 75
            assert "cost" in result
            
            # Verify API call
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["model"] == "gpt-4o-mini"
            assert call_args["max_tokens"] == 800
            assert call_args["temperature"] == 0.8
            
            # Verify message structure includes context and history
            messages = call_args["messages"]
            assert len(messages) >= 4  # system + context + history + question
            assert messages[-1]["role"] == "user"
            assert messages[-1]["content"] == "New question"
    
    async def test_generate_conversation_response_api_error(self, openai_service):
        """Test conversation response when OpenAI API fails."""
        with patch.object(openai_service.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            with pytest.raises(Exception, match="API Error"):
                await openai_service.generate_conversation_response(
                    "summary", "report", [], "question"
                )

    # Tests for Responses API
    async def test_analyze_palm_images_with_responses_no_client(self, openai_service_no_key):
        """Test Responses API analysis when no OpenAI client is configured."""
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            await openai_service_no_key.analyze_palm_images_with_responses("file_123")

    async def test_analyze_palm_images_with_responses_no_files(self, openai_service):
        """Test Responses API analysis when no file IDs are provided."""
        with pytest.raises(ValueError, match="At least one palm image file ID is required"):
            await openai_service.analyze_palm_images_with_responses()

    async def test_analyze_palm_images_with_responses_success_single_file(self, openai_service):
        """Test successful palm analysis with Responses API using single file."""
        with patch.object(openai_service.client.responses, 'create') as mock_create:
            # Mock Responses API response
            mock_response = MagicMock()
            mock_response.output_text = json.dumps({
                "summary": "Test summary from Responses API",
                "full_report": "Test full report from Responses API",
                "key_features": ["line1", "line2"],
                "strengths": ["strength1"],
                "guidance": ["guidance1"]
            })
            mock_create.return_value = mock_response
            
            result = await openai_service.analyze_palm_images_with_responses(
                left_file_id="file_123"
            )
            
            # Verify result structure
            assert result["summary"] == "Test summary from Responses API"
            assert result["full_report"] == "Test full report from Responses API"
            assert result["key_features"] == ["line1", "line2"]
            assert result["strengths"] == ["strength1"]
            assert result["guidance"] == ["guidance1"]
            assert "tokens_used" in result
            assert "cost" in result
            
            # Verify Responses API was called correctly
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["model"] == "gpt-4o"
            assert len(call_args["input"]) == 1
            assert call_args["input"][0]["role"] == "user"
            
            # Verify content structure
            content = call_args["input"][0]["content"]
            assert any(part["type"] == "input_text" for part in content)
            assert any(part["type"] == "input_image" and part["file_id"] == "file_123" for part in content)

    async def test_analyze_palm_images_with_responses_success_both_files(self, openai_service):
        """Test successful palm analysis with Responses API using both files."""
        with patch.object(openai_service.client.responses, 'create') as mock_create:
            # Mock Responses API response
            mock_response = MagicMock()
            mock_response.output_text = json.dumps({
                "summary": "Test summary with both palms",
                "full_report": "Test full report with both palms"
            })
            mock_create.return_value = mock_response
            
            result = await openai_service.analyze_palm_images_with_responses(
                left_file_id="file_123",
                right_file_id="file_456"
            )
            
            # Verify API call mentions both palms
            call_args = mock_create.call_args[1]
            content = call_args["input"][0]["content"]
            
            # Find the text content
            text_part = next(part for part in content if part["type"] == "input_text")
            assert "left palm and right palm" in text_part["text"]
            
            # Verify both file IDs are included
            file_parts = [part for part in content if part["type"] == "input_image"]
            assert len(file_parts) == 2
            file_ids = {part["file_id"] for part in file_parts}
            assert file_ids == {"file_123", "file_456"}

    async def test_analyze_palm_images_with_responses_invalid_json(self, openai_service):
        """Test Responses API analysis with invalid JSON response."""
        with patch.object(openai_service.client.responses, 'create') as mock_create:
            # Mock Responses API response with invalid JSON
            mock_response = MagicMock()
            mock_response.output_text = "Invalid JSON response from Responses API"
            mock_create.return_value = mock_response
            
            result = await openai_service.analyze_palm_images_with_responses(
                left_file_id="file_123"
            )
            
            # Should fall back to using raw response
            assert result["summary"] == "Invalid JSON response from Responses API"
            assert result["full_report"] == "Invalid JSON response from Responses API"
            assert result["key_features"] == []
            assert result["strengths"] == []
            assert result["guidance"] == []

    async def test_analyze_palm_images_with_responses_api_error(self, openai_service):
        """Test Responses API analysis when API returns error."""
        with patch.object(openai_service.client.responses, 'create') as mock_create:
            # Mock Responses API error
            mock_create.side_effect = Exception("Responses API Error")
            
            with pytest.raises(Exception, match="Responses API Error"):
                await openai_service.analyze_palm_images_with_responses(
                    left_file_id="file_123"
                )