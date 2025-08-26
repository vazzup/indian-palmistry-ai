"""
Tests for OpenAI service JSON parsing fixes applied during debugging session.

These tests specifically validate the fixes for handling markdown code blocks
in OpenAI responses that were causing database corruption.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from app.services.openai_service import OpenAIService


class TestOpenAIServiceJSONParsing:
    """Test the enhanced JSON parsing in OpenAI service that fixes markdown code block issues."""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance."""
        return OpenAIService()
    
    def test_parse_json_response_clean_json(self, openai_service):
        """Test parsing clean JSON without markdown code blocks."""
        clean_json = '{"summary": "Clear life line indicates strong vitality", "full_report": "Detailed analysis..."}'
        
        result = openai_service._parse_analysis_response(clean_json)
        
        assert result["summary"] == "Clear life line indicates strong vitality"
        assert result["full_report"] == "Detailed analysis..."
    
    def test_parse_json_response_with_json_markdown(self, openai_service):
        """Test parsing JSON wrapped in ```json markdown blocks."""
        markdown_json = '''```json
{
    "summary": "Clear life line indicates strong vitality",
    "full_report": "Detailed palm analysis with traditional insights"
}
```'''
        
        result = openai_service._parse_analysis_response(markdown_json)
        
        assert result["summary"] == "Clear life line indicates strong vitality" 
        assert result["full_report"] == "Detailed palm analysis with traditional insights"
    
    def test_parse_json_response_with_generic_markdown(self, openai_service):
        """Test parsing JSON wrapped in generic ``` markdown blocks."""
        markdown_json = '''```
{
    "summary": "Strong heart line shows emotional stability",
    "full_report": "Your heart line reveals deep emotional connections"
}
```'''
        
        result = openai_service._parse_analysis_response(markdown_json)
        
        assert result["summary"] == "Strong heart line shows emotional stability"
        assert result["full_report"] == "Your heart line reveals deep emotional connections"
    
    def test_parse_json_response_with_extra_whitespace(self, openai_service):
        """Test parsing with extra whitespace and newlines."""
        whitespace_json = '''   ```json
        
{
    "summary": "Fate line indicates career success",
    "full_report": "Your destiny line suggests professional achievement"
}

```   '''
        
        result = openai_service._parse_analysis_response(whitespace_json)
        
        assert result["summary"] == "Fate line indicates career success"
        assert result["full_report"] == "Your destiny line suggests professional achievement"
    
    def test_parse_json_response_malformed_markdown(self, openai_service):
        """Test handling of malformed markdown that doesn't affect JSON parsing."""
        malformed_json = '```json\n{"summary": "Money line shows prosperity", "full_report": "Financial indicators are positive"}'
        
        result = openai_service._parse_analysis_response(malformed_json)
        
        assert result["summary"] == "Money line shows prosperity"
        assert result["full_report"] == "Financial indicators are positive"
    
    def test_parse_json_response_invalid_json_raises_error(self, openai_service):
        """Test that invalid JSON after markdown removal still raises appropriate error."""
        invalid_json = '''```json
{
    "summary": "Invalid JSON structure"
    "missing_comma": "causes error"
}
```'''
        
        with pytest.raises(json.JSONDecodeError):
            openai_service._parse_analysis_response(invalid_json)
    
    def test_parse_json_response_nested_markdown_patterns(self, openai_service):
        """Test parsing when JSON content contains markdown-like strings."""
        nested_markdown = '''```json
{
    "summary": "Life line analysis with ```special formatting```",
    "full_report": "Analysis mentions ```json code``` in explanation"
}
```'''
        
        result = openai_service._parse_analysis_response(nested_markdown)
        
        assert "```special formatting```" in result["summary"]
        assert "```json code```" in result["full_report"]
    
    @pytest.mark.asyncio
    async def test_analyze_palm_with_markdown_response(self, openai_service):
        """Test full palm analysis with markdown-wrapped response."""
        mock_response = '''```json
{
    "summary": "Your palm reveals strength and wisdom through clear major lines",
    "full_report": "Complete traditional palmistry analysis based on Hast Rekha Shastra principles"
}
```'''
        
        # Mock the OpenAI client call
        with patch.object(openai_service, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock()
            mock_client.chat.completions.create.return_value.choices = [
                type('Choice', (), {
                    'message': type('Message', (), {'content': mock_response})()
                })()
            ]
            mock_client.chat.completions.create.return_value.usage = type('Usage', (), {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            })()
            
            result = await openai_service.analyze_palm("base64_image_data")
            
            assert result["analysis"]["summary"] == "Your palm reveals strength and wisdom through clear major lines"
            assert result["analysis"]["full_report"] == "Complete traditional palmistry analysis based on Hast Rekha Shastra principles"
            assert result["tokens_used"] == 150
            assert result["cost"] > 0
    
    @pytest.mark.asyncio 
    async def test_database_corruption_regression(self, openai_service):
        """Test that the fix prevents the specific database corruption issue found in session."""
        # This is the exact type of response that was causing corruption
        problematic_response = '''```json
{"summary": "Your life line indicates strong vitality and longevity. The clear, unbroken line suggests good health throughout your life.", "full_report": "Based on traditional Indian palmistry (Hast Rekha Shastra), your palm reveals several important insights: **Life Line Analysis:** Your life line is well-formed and extends around the thumb, indicating robust health and vitality. **Heart Line:** The heart line shows emotional stability and capacity for deep relationships. **Head Line:** A clear head line suggests practical thinking and decision-making abilities."}
```'''
        
        # This should not raise an exception and should return properly parsed data
        result = openai_service._parse_analysis_response(problematic_response)
        
        assert isinstance(result, dict)
        assert "summary" in result
        assert "full_report" in result
        assert not result["summary"].startswith('```')
        assert not result["full_report"].endswith('```')
        assert "Your life line indicates strong vitality" in result["summary"]
        assert "Based on traditional Indian palmistry" in result["full_report"]


class TestOpenAIServiceErrorHandling:
    """Test enhanced error handling in OpenAI service."""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance."""
        return OpenAIService()
    
    def test_empty_response_handling(self, openai_service):
        """Test handling of empty responses."""
        with pytest.raises(ValueError, match="Empty response"):
            openai_service._parse_analysis_response("")
    
    def test_null_response_handling(self, openai_service):
        """Test handling of null responses."""
        with pytest.raises(ValueError, match="Empty response"):
            openai_service._parse_analysis_response(None)
    
    def test_whitespace_only_response(self, openai_service):
        """Test handling of whitespace-only responses."""
        with pytest.raises(ValueError, match="Empty response"):
            openai_service._parse_analysis_response("   \n\t   ")
    
    @pytest.mark.asyncio
    async def test_openai_api_error_handling(self, openai_service):
        """Test proper error handling for OpenAI API failures."""
        from openai import APIError
        
        with patch.object(openai_service, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock()
            mock_client.chat.completions.create.side_effect = APIError("Rate limit exceeded")
            
            with pytest.raises(Exception, match="OpenAI API error"):
                await openai_service.analyze_palm("base64_image_data")