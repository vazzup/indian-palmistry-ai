"""
Tests for Advanced Palm Analysis Service.

This module tests the specialized palm line analysis with multi-reading comparison,
user history tracking, and confidence scoring features.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from app.services.advanced_palm_service import AdvancedPalmService, PalmLineType
from app.models.analysis import Analysis
from app.models.user import User


class TestAdvancedPalmService:
    """Test suite for AdvancedPalmService class."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return AdvancedPalmService()

    @pytest.fixture
    def mock_analysis(self):
        """Mock analysis object."""
        analysis = MagicMock(spec=Analysis)
        analysis.id = 123
        analysis.user_id = 456
        analysis.result = {
            "lines": {
                "life_line": "Strong and clear life line indicating vitality",
                "love_line": "Multiple love lines suggesting complex relationships"
            },
            "confidence": 0.85
        }
        analysis.left_image_path = "/path/to/left.jpg"
        analysis.right_image_path = "/path/to/right.jpg"
        analysis.created_at = datetime.utcnow()
        return analysis

    @pytest.fixture
    def mock_user(self):
        """Mock user object."""
        user = MagicMock(spec=User)
        user.id = 456
        user.name = "Test User"
        return user

    @pytest.mark.asyncio
    async def test_analyze_specific_lines_success(self, service, mock_analysis):
        """Test successful specialized line analysis."""
        line_types = [PalmLineType.LIFE_LINE, PalmLineType.LOVE_LINE]
        
        with patch.object(service, '_get_analysis_by_id') as mock_get_analysis, \
             patch.object(service, 'openai_service') as mock_openai, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_analysis.return_value = mock_analysis
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock OpenAI responses for each line type
            mock_openai.analyze_palm_with_custom_prompt.side_effect = [
                {"analysis": "Detailed life line analysis", "confidence": 0.9},
                {"analysis": "Detailed love line analysis", "confidence": 0.8}
            ]
            
            result = await service.analyze_specific_lines(123, line_types, user_id=456)
            
            assert "line_analyses" in result
            assert len(result["line_analyses"]) == 2
            assert result["line_analyses"]["life_line"]["confidence"] == 0.9
            assert result["line_analyses"]["love_line"]["confidence"] == 0.8
            assert result["overall_confidence"] == 0.85  # Average
            
            # Verify caching
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_specific_lines_cached(self, service, mock_analysis):
        """Test cached specialized line analysis."""
        line_types = [PalmLineType.LIFE_LINE]
        cached_result = {
            "line_analyses": {"life_line": {"analysis": "Cached analysis"}},
            "overall_confidence": 0.85
        }
        
        with patch.object(service, '_get_analysis_by_id') as mock_get_analysis, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_analysis.return_value = mock_analysis
            mock_cache.get.return_value = cached_result
            
            result = await service.analyze_specific_lines(123, line_types)
            
            assert result == cached_result
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_specific_lines_analysis_not_found(self, service):
        """Test analysis not found error."""
        with patch.object(service, '_get_analysis_by_id') as mock_get_analysis:
            mock_get_analysis.return_value = None
            
            with pytest.raises(ValueError, match="Analysis not found"):
                await service.analyze_specific_lines(999, [PalmLineType.LIFE_LINE])

    @pytest.mark.asyncio
    async def test_analyze_single_line_type(self, service):
        """Test individual line type analysis."""
        with patch.object(service, 'openai_service') as mock_openai:
            mock_openai.analyze_palm_with_custom_prompt.return_value = {
                "analysis": "Detailed life line analysis",
                "confidence": 0.9,
                "key_features": ["strong", "unbroken", "long"]
            }
            
            result = await service._analyze_single_line_type(
                PalmLineType.LIFE_LINE,
                "/path/to/left.jpg",
                "/path/to/right.jpg"
            )
            
            assert result["line_type"] == "life_line"
            assert result["analysis"] == "Detailed life line analysis"
            assert result["confidence"] == 0.9
            assert "key_features" in result

    @pytest.mark.asyncio
    async def test_compare_analyses_success(self, service):
        """Test multi-analysis temporal comparison."""
        analysis_ids = [123, 124, 125]
        
        # Mock analyses from different time periods
        analyses = []
        base_time = datetime.utcnow()
        for i, aid in enumerate(analysis_ids):
            analysis = MagicMock(spec=Analysis)
            analysis.id = aid
            analysis.user_id = 456
            analysis.created_at = base_time - timedelta(days=30*i)
            analysis.result = {
                "lines": {"life_line": f"Life line analysis {i}"},
                "confidence": 0.8 + (i * 0.05)
            }
            analyses.append(analysis)
        
        with patch.object(service, '_get_analysis_by_id') as mock_get_analysis, \
             patch.object(service, '_generate_comparative_insights') as mock_insights, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_analysis.side_effect = analyses
            mock_cache.get.return_value = None  # Cache miss
            mock_insights.return_value = {
                "trends": ["Improving confidence over time"],
                "changes": ["Life line clarity increased"]
            }
            
            result = await service.compare_analyses(analysis_ids, user_id=456)
            
            assert "analyses" in result
            assert len(result["analyses"]) == 3
            assert "comparative_insights" in result
            assert "timeline_analysis" in result
            assert result["trends"]["confidence_trend"] == "improving"

    @pytest.mark.asyncio
    async def test_compare_analyses_insufficient_data(self, service):
        """Test comparison with insufficient analyses."""
        with pytest.raises(ValueError, match="At least 2 analyses required"):
            await service.compare_analyses([123], user_id=456)

    @pytest.mark.asyncio
    async def test_get_user_analysis_history_success(self, service, mock_user):
        """Test user analysis history retrieval."""
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock database query
            mock_query = AsyncMock()
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [
                self._create_mock_analysis(1, datetime.utcnow()),
                self._create_mock_analysis(2, datetime.utcnow() - timedelta(days=30)),
            ]
            mock_query.execute.return_value = mock_result
            mock_db.execute.return_value = mock_result
            
            result = await service.get_user_analysis_history(456, days=90)
            
            assert "user_info" in result
            assert "analyses" in result
            assert "trends" in result
            assert "statistics" in result
            assert result["period_days"] == 90

    @pytest.mark.asyncio
    async def test_get_user_analysis_history_user_not_found(self, service):
        """Test user not found error in history."""
        with patch.object(service, '_get_user_by_id') as mock_get_user:
            mock_get_user.return_value = None
            
            with pytest.raises(ValueError, match="User not found"):
                await service.get_user_analysis_history(999)

    @pytest.mark.asyncio
    async def test_generate_comparative_insights(self, service):
        """Test comparative insights generation."""
        analyses_data = [
            {
                "id": 123,
                "created_at": datetime.utcnow(),
                "confidence": 0.8,
                "result": {"lines": {"life_line": "Strong life line"}}
            },
            {
                "id": 124, 
                "created_at": datetime.utcnow() - timedelta(days=30),
                "confidence": 0.9,
                "result": {"lines": {"life_line": "Very strong life line"}}
            }
        ]
        
        with patch.object(service, 'openai_service') as mock_openai:
            mock_openai.generate_response.return_value = {
                "comparative_analysis": "The life line has strengthened over time",
                "key_changes": ["Increased clarity", "Better definition"],
                "trends": ["Positive development"]
            }
            
            result = await service._generate_comparative_insights(analyses_data)
            
            assert "comparative_analysis" in result
            assert "key_changes" in result
            assert "trends" in result

    def _create_mock_analysis(self, id: int, created_at: datetime) -> MagicMock:
        """Helper to create mock analysis objects."""
        analysis = MagicMock(spec=Analysis)
        analysis.id = id
        analysis.user_id = 456
        analysis.created_at = created_at
        analysis.result = {
            "lines": {"life_line": f"Analysis {id}"},
            "confidence": 0.85
        }
        analysis.cost = 0.05
        analysis.tokens_used = 500
        return analysis

    @pytest.mark.asyncio
    async def test_line_type_prompts(self, service):
        """Test that different line types use appropriate prompts."""
        test_cases = [
            (PalmLineType.LIFE_LINE, "vitality", "health"),
            (PalmLineType.LOVE_LINE, "relationships", "emotions"),
            (PalmLineType.HEAD_LINE, "intelligence", "thinking"),
            (PalmLineType.FATE_LINE, "career", "destiny"),
            (PalmLineType.HEALTH_LINE, "health", "wellness"),
            (PalmLineType.CAREER_LINE, "professional", "career"),
            (PalmLineType.MARRIAGE_LINE, "marriage", "partnerships"),
            (PalmLineType.MONEY_LINE, "financial", "wealth")
        ]
        
        with patch.object(service, 'openai_service') as mock_openai:
            mock_openai.analyze_palm_with_custom_prompt.return_value = {
                "analysis": "Test analysis",
                "confidence": 0.8
            }
            
            for line_type, keyword1, keyword2 in test_cases:
                await service._analyze_single_line_type(
                    line_type, "/path/to/left.jpg", "/path/to/right.jpg"
                )
                
                # Verify the prompt contains expected keywords
                call_args = mock_openai.analyze_palm_with_custom_prompt.call_args
                prompt = call_args[0][2]  # Third argument is the prompt
                
                assert keyword1.lower() in prompt.lower() or keyword2.lower() in prompt.lower()

    @pytest.mark.asyncio
    async def test_error_handling(self, service, mock_analysis):
        """Test comprehensive error handling."""
        # Test OpenAI service failure
        with patch.object(service, '_get_analysis_by_id') as mock_get_analysis, \
             patch.object(service, 'openai_service') as mock_openai, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_analysis.return_value = mock_analysis
            mock_cache.get.return_value = None
            mock_openai.analyze_palm_with_custom_prompt.side_effect = Exception("OpenAI API error")
            
            with pytest.raises(Exception):
                await service.analyze_specific_lines(123, [PalmLineType.LIFE_LINE])

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, service, mock_analysis):
        """Test confidence score calculation."""
        line_types = [PalmLineType.LIFE_LINE, PalmLineType.LOVE_LINE, PalmLineType.HEAD_LINE]
        
        with patch.object(service, '_get_analysis_by_id') as mock_get_analysis, \
             patch.object(service, 'openai_service') as mock_openai, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_analysis.return_value = mock_analysis
            mock_cache.get.return_value = None
            
            # Different confidence scores for each line
            mock_openai.analyze_palm_with_custom_prompt.side_effect = [
                {"analysis": "Analysis 1", "confidence": 0.9},
                {"analysis": "Analysis 2", "confidence": 0.8},
                {"analysis": "Analysis 3", "confidence": 0.7}
            ]
            
            result = await service.analyze_specific_lines(123, line_types)
            
            # Should calculate average confidence: (0.9 + 0.8 + 0.7) / 3 = 0.8
            assert result["overall_confidence"] == 0.8
            
            # Should include individual line confidences
            assert result["line_analyses"]["life_line"]["confidence"] == 0.9
            assert result["line_analyses"]["love_line"]["confidence"] == 0.8
            assert result["line_analyses"]["head_line"]["confidence"] == 0.7