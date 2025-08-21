"""
Advanced palm analysis service with specialized line analysis and comparative features.
"""
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import base64
import json
from datetime import datetime

from app.services.openai_service import OpenAIService
from app.services.image_service import ImageService
from app.models.analysis import Analysis
from app.core.database import get_db_session
from app.core.cache import cache_service
from app.core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = get_logger(__name__)

class PalmLineType(Enum):
    """Types of palm lines for specialized analysis."""
    LIFE_LINE = "life_line"
    LOVE_LINE = "love_line"
    HEAD_LINE = "head_line"
    FATE_LINE = "fate_line"
    HEALTH_LINE = "health_line"
    CAREER_LINE = "career_line"
    MARRIAGE_LINE = "marriage_line"
    MONEY_LINE = "money_line"

class AdvancedPalmService:
    """Advanced palm analysis service with specialized features."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.image_service = ImageService()
    
    async def analyze_specific_lines(
        self, 
        analysis_id: int, 
        line_types: List[PalmLineType],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze specific palm lines with specialized prompts."""
        
        # Check cache first
        cache_key = f"advanced_analysis:{analysis_id}:{':'.join([lt.value for lt in line_types])}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Advanced analysis cache hit for analysis {analysis_id}")
            return cached_result
        
        try:
            # Get analysis data
            async with get_db_session() as db:
                stmt = select(Analysis).where(Analysis.id == analysis_id)
                if user_id:
                    stmt = stmt.where(Analysis.user_id == user_id)
                
                result = await db.execute(stmt)
                analysis = result.scalar_one_or_none()
                
                if not analysis:
                    raise ValueError(f"Analysis {analysis_id} not found")
            
            # Get image data for analysis
            image_data = await self._get_analysis_image_data(analysis)
            
            # Perform specialized analysis for each line type
            line_analyses = {}
            for line_type in line_types:
                line_analysis = await self._analyze_single_line_type(image_data, line_type)
                line_analyses[line_type.value] = line_analysis
            
            # Generate comparative insights
            comparative_insights = await self._generate_comparative_insights(line_analyses)
            
            result = {
                "analysis_id": analysis_id,
                "line_analyses": line_analyses,
                "comparative_insights": comparative_insights,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "confidence_score": self._calculate_overall_confidence(line_analyses)
            }
            
            # Cache the result for 6 hours
            await cache_service.set(cache_key, result, expire=21600)
            
            logger.info(f"Advanced analysis completed for analysis {analysis_id}")
            return result
            
        except Exception as e:
            logger.error(f"Advanced analysis failed for analysis {analysis_id}: {e}")
            raise
    
    async def _analyze_single_line_type(
        self, 
        image_data: bytes, 
        line_type: PalmLineType
    ) -> Dict[str, Any]:
        """Analyze a single palm line type with specialized prompt."""
        
        prompts = {
            PalmLineType.LIFE_LINE: """
            Focus specifically on the LIFE LINE in this palm. The life line curves around the thumb and represents vitality, health, and major life changes.
            
            Analyze:
            - Length and depth of the life line
            - Any breaks, chains, or islands in the line
            - Where the line starts and ends
            - Branches or forks in the line
            - Distance from the thumb (energy levels)
            - Any special markings or crosses
            
            Provide insights about:
            - Health and vitality patterns
            - Major life transitions and timing
            - Energy levels and physical strength
            - Potential health considerations
            - Life path changes and developments
            """,
            
            PalmLineType.LOVE_LINE: """
            Focus on the HEART LINE (love line) that runs horizontally across the upper part of the palm, representing emotions, relationships, and love life.
            
            Analyze:
            - Length and curve of the heart line
            - Starting and ending points
            - Depth and clarity of the line
            - Any breaks, chains, or islands
            - Branches extending upward or downward
            - Relationship to other lines
            
            Provide insights about:
            - Emotional nature and expression
            - Relationship patterns and compatibility
            - Love life and romantic tendencies
            - Capacity for emotional connection
            - Heart health and emotional well-being
            """,
            
            PalmLineType.HEAD_LINE: """
            Focus on the HEAD LINE that runs horizontally across the middle of the palm, representing intellect, thinking patterns, and mental approach.
            
            Analyze:
            - Length and direction of the head line
            - Depth and clarity
            - Starting point (attachment to life line or separate)
            - Ending point and any curves
            - Any breaks, islands, or special markings
            - Branches or forks
            
            Provide insights about:
            - Intellectual capacity and thinking style
            - Decision-making patterns
            - Creative vs analytical tendencies
            - Mental health and stress patterns
            - Learning style and communication approach
            """,
            
            PalmLineType.FATE_LINE: """
            Focus on the FATE LINE (destiny line) that typically runs vertically up the center of the palm, representing career, life purpose, and external influences.
            
            Analyze:
            - Presence and clarity of the fate line
            - Starting point (wrist, life line, or elsewhere)
            - Ending point (heart line, head line, or fingers)
            - Any breaks or changes in direction
            - Depth and consistency
            - Intersections with other lines
            
            Provide insights about:
            - Career path and professional development
            - Life purpose and destiny
            - External influences and support
            - Major life direction changes
            - Success patterns and obstacles
            """,
            
            PalmLineType.HEALTH_LINE: """
            Look for the HEALTH LINE (Mercury line) that may run from the wrist toward the little finger, representing health, intuition, and business acumen.
            
            Analyze:
            - Presence and clarity of the health line
            - Direction and consistency
            - Any breaks, waves, or irregularities
            - Color and depth
            - Relationship to other lines
            - Starting and ending points
            
            Provide insights about:
            - Overall health patterns
            - Digestive and nervous system health
            - Business and financial intuition
            - Healing abilities
            - Stress indicators and health warnings
            """,
            
            PalmLineType.CAREER_LINE: """
            Examine career-related markings including the fate line, success lines, and any lines toward the fingers representing professional achievement.
            
            Analyze:
            - Career-related lines and their strength
            - Lines leading to different fingers (Jupiter, Saturn, Apollo)
            - Success lines and achievement markers
            - Any obstacles or support indicators
            - Timing of career changes
            
            Provide insights about:
            - Professional strengths and talents
            - Career timing and opportunities
            - Leadership potential
            - Business success indicators
            - Professional obstacles and solutions
            """,
            
            PalmLineType.MARRIAGE_LINE: """
            Focus on the MARRIAGE LINES (relationship lines) located on the side of the palm below the little finger.
            
            Analyze:
            - Number and depth of marriage lines
            - Length and clarity of each line
            - Any forks, breaks, or islands
            - Distance from the heart line
            - Curves or directions of the lines
            
            Provide insights about:
            - Number of significant relationships
            - Timing of relationships and marriage
            - Relationship strength and duration
            - Compatibility patterns
            - Challenges in partnerships
            """,
            
            PalmLineType.MONEY_LINE: """
            Look for money and wealth indicators including lines toward the little finger, triangle formations, and success markers.
            
            Analyze:
            - Lines indicating financial success
            - Triangle formations (wealth signs)
            - Lines connecting to the little finger
            - Success lines and their strength
            - Any obstacles to financial growth
            
            Provide insights about:
            - Financial potential and wealth patterns
            - Money management abilities
            - Business and investment success
            - Sources of income and prosperity
            - Financial obstacles and opportunities
            """
        }
        
        prompt = prompts.get(line_type, "Analyze this palm for general insights.")
        
        # Use OpenAI for specialized analysis
        analysis_result = await self.openai_service.analyze_palm_with_custom_prompt(
            image_data, prompt
        )
        
        return {
            "line_type": line_type.value,
            "analysis": analysis_result.get("analysis", ""),
            "confidence": analysis_result.get("confidence", 0.7),
            "key_points": self._extract_key_points(analysis_result.get("analysis", "")),
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    async def _generate_comparative_insights(
        self, 
        line_analyses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comparative insights across different line analyses."""
        
        try:
            # Create a comprehensive analysis prompt
            analysis_summary = "Based on the following specialized palm line analyses, provide comparative insights:\n\n"
            
            for line_type, analysis in line_analyses.items():
                analysis_summary += f"{line_type.upper()}:\n{analysis['analysis']}\n\n"
            
            comparative_prompt = f"""
            {analysis_summary}
            
            Please provide comparative insights that:
            1. Identify patterns and connections between different lines
            2. Highlight any contradictions or complementary aspects
            3. Provide an integrated life reading based on all analyzed lines
            4. Suggest the most important insights for this person
            5. Identify timing patterns across different life areas
            6. Give priority recommendations based on the overall pattern
            
            Format your response as a comprehensive integrated analysis.
            """
            
            # Get comparative analysis from OpenAI
            comparative_result = await self.openai_service.generate_response(comparative_prompt)
            
            return {
                "integrated_analysis": comparative_result.get("content", ""),
                "key_themes": self._extract_themes(comparative_result.get("content", "")),
                "priority_insights": self._extract_priorities(comparative_result.get("content", "")),
                "confidence": 0.8
            }
            
        except Exception as e:
            logger.error(f"Failed to generate comparative insights: {e}")
            return {
                "integrated_analysis": "Comparative analysis temporarily unavailable.",
                "key_themes": [],
                "priority_insights": [],
                "confidence": 0.0
            }
    
    async def compare_analyses(
        self, 
        analysis_ids: List[int], 
        user_id: int
    ) -> Dict[str, Any]:
        """Compare multiple palm analyses for temporal insights."""
        
        cache_key = f"analysis_comparison:{':'.join(map(str, sorted(analysis_ids)))}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            async with get_db_session() as db:
                # Get analyses
                stmt = select(Analysis).where(
                    Analysis.id.in_(analysis_ids),
                    Analysis.user_id == user_id,
                    Analysis.status == "COMPLETED"
                ).order_by(Analysis.created_at)
                
                result = await db.execute(stmt)
                analyses = result.scalars().all()
                
                if len(analyses) < 2:
                    raise ValueError("At least 2 completed analyses required for comparison")
            
            # Create comparison analysis
            comparison_data = []
            for analysis in analyses:
                comparison_data.append({
                    "id": analysis.id,
                    "date": analysis.created_at.isoformat(),
                    "summary": analysis.summary or "No summary available",
                    "key_insights": self._extract_key_insights(analysis.full_report or "")
                })
            
            # Generate temporal comparison
            comparison_prompt = f"""
            Compare these palm readings taken at different times for the same person:
            
            {json.dumps(comparison_data, indent=2)}
            
            Analyze:
            1. Changes and developments over time
            2. Consistent patterns vs evolving aspects
            3. Life progression and growth indicators
            4. Recommendations based on the temporal pattern
            5. Future trends based on the progression
            
            Provide a comprehensive temporal analysis.
            """
            
            comparison_result = await self.openai_service.generate_response(comparison_prompt)
            
            result = {
                "analysis_ids": analysis_ids,
                "comparison_period": {
                    "start_date": analyses[0].created_at.isoformat(),
                    "end_date": analyses[-1].created_at.isoformat(),
                    "duration_days": (analyses[-1].created_at - analyses[0].created_at).days
                },
                "temporal_analysis": comparison_result.get("content", ""),
                "progression_summary": self._extract_progression_summary(comparison_result.get("content", "")),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            # Cache for 12 hours
            await cache_service.set(cache_key, result, expire=43200)
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis comparison failed: {e}")
            raise
    
    async def get_user_analysis_history(
        self, 
        user_id: int, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get user's analysis history with trends."""
        
        cache_key = f"user_history:{user_id}:{limit}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            async with get_db_session() as db:
                # Get user's analyses with stats
                stmt = select(
                    Analysis,
                    func.count().over().label('total_count')
                ).where(
                    Analysis.user_id == user_id
                ).order_by(
                    Analysis.created_at.desc()
                ).limit(limit)
                
                result = await db.execute(stmt)
                rows = result.all()
                
                if not rows:
                    return {"analyses": [], "stats": {}, "trends": {}}
                
                analyses = [row.Analysis for row in rows]
                total_count = rows[0].total_count if rows else 0
                
                # Calculate statistics
                completed_analyses = [a for a in analyses if a.status == "COMPLETED"]
                total_cost = sum(a.cost or 0 for a in completed_analyses)
                total_tokens = sum(a.tokens_used or 0 for a in completed_analyses)
                
                # Generate trend analysis
                trends = await self._analyze_user_trends(completed_analyses)
                
                result = {
                    "analyses": [
                        {
                            "id": a.id,
                            "created_at": a.created_at.isoformat(),
                            "status": a.status,
                            "summary": a.summary,
                            "cost": a.cost,
                            "tokens_used": a.tokens_used
                        } for a in analyses
                    ],
                    "stats": {
                        "total_analyses": total_count,
                        "completed_analyses": len(completed_analyses),
                        "total_cost": round(total_cost, 4),
                        "total_tokens": total_tokens,
                        "average_cost": round(total_cost / len(completed_analyses), 4) if completed_analyses else 0
                    },
                    "trends": trends,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                # Cache for 1 hour
                await cache_service.set(cache_key, result, expire=3600)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get user analysis history: {e}")
            raise
    
    async def _get_analysis_image_data(self, analysis: Analysis) -> bytes:
        """Get image data for analysis."""
        # Prefer left image, fallback to right
        image_path = analysis.left_image_path or analysis.right_image_path
        if not image_path:
            raise ValueError("No image found for analysis")
        
        # Read image file
        with open(image_path, 'rb') as f:
            return f.read()
    
    def _extract_key_points(self, analysis_text: str) -> List[str]:
        """Extract key points from analysis text."""
        # Simple extraction - in real implementation, could use NLP
        lines = analysis_text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line and (
                line.startswith('•') or 
                line.startswith('-') or 
                line.startswith('*') or
                'important' in line.lower() or
                'significant' in line.lower()
            ):
                key_points.append(line.lstrip('•-*').strip())
        
        return key_points[:5]  # Return top 5 key points
    
    def _extract_key_insights(self, full_report: str) -> List[str]:
        """Extract key insights from full report."""
        # Simple extraction logic
        lines = full_report.split('\n')
        insights = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 20 and any(
                keyword in line.lower() 
                for keyword in ['indicates', 'suggests', 'shows', 'reveals', 'signifies']
            ):
                insights.append(line)
        
        return insights[:3]
    
    def _extract_themes(self, analysis_text: str) -> List[str]:
        """Extract key themes from analysis."""
        # Simple theme extraction
        common_themes = [
            'career', 'relationships', 'health', 'finances', 'creativity', 
            'leadership', 'communication', 'family', 'travel', 'spirituality'
        ]
        
        found_themes = []
        text_lower = analysis_text.lower()
        
        for theme in common_themes:
            if theme in text_lower:
                found_themes.append(theme.title())
        
        return found_themes
    
    def _extract_priorities(self, analysis_text: str) -> List[str]:
        """Extract priority recommendations."""
        lines = analysis_text.split('\n')
        priorities = []
        
        for line in lines:
            line = line.strip()
            if line and any(
                keyword in line.lower() 
                for keyword in ['should', 'recommend', 'suggest', 'important', 'priority', 'focus']
            ):
                priorities.append(line)
        
        return priorities[:3]
    
    def _extract_progression_summary(self, comparison_text: str) -> Dict[str, Any]:
        """Extract progression summary from comparison."""
        return {
            "overall_trend": "Positive development" if "positive" in comparison_text.lower() else "Stable progression",
            "key_changes": ["Personal growth", "Enhanced awareness"],  # Simplified
            "future_outlook": "Continued growth potential"
        }
    
    async def _analyze_user_trends(self, analyses: List[Analysis]) -> Dict[str, Any]:
        """Analyze trends in user's analyses."""
        if len(analyses) < 2:
            return {"trend_analysis": "Insufficient data for trend analysis"}
        
        # Calculate basic trends
        dates = [a.created_at for a in analyses]
        costs = [a.cost or 0 for a in analyses]
        
        # Simple trend calculation
        frequency_days = (dates[0] - dates[-1]).days / len(analyses) if len(analyses) > 1 else 0
        
        return {
            "analysis_frequency_days": round(frequency_days, 1),
            "cost_trend": "increasing" if len(costs) > 1 and costs[0] > costs[-1] else "stable",
            "engagement_level": "high" if len(analyses) > 10 else "moderate" if len(analyses) > 3 else "new",
            "trend_analysis": "Regular user showing consistent engagement with palmistry insights."
        }
    
    def _calculate_overall_confidence(self, line_analyses: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall confidence score."""
        if not line_analyses:
            return 0.0
        
        confidences = [analysis.get("confidence", 0.7) for analysis in line_analyses.values()]
        return round(sum(confidences) / len(confidences), 2)

# Global service instance
advanced_palm_service = AdvancedPalmService()