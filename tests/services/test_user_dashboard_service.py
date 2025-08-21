"""
Tests for User Dashboard Service.

This module tests the comprehensive user dashboard with analytics, preferences,
achievements, and GDPR-compliant data export functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.services.user_dashboard_service import UserDashboardService, UserPreferenceKey
from app.models.user import User


class TestUserDashboardService:
    """Test suite for UserDashboardService class."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return UserDashboardService()

    @pytest.fixture
    def mock_user(self):
        """Mock user object."""
        user = MagicMock(spec=User)
        user.id = 456
        user.name = "Test User"
        user.email = "test@example.com"
        user.created_at = datetime.utcnow() - timedelta(days=30)
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_get_user_dashboard_success(self, service, mock_user):
        """Test successful user dashboard retrieval."""
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, '_get_user_analytics') as mock_analytics, \
             patch.object(service, '_get_recent_analyses') as mock_analyses, \
             patch.object(service, '_get_recent_conversations') as mock_conversations, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock analytics data
            mock_analytics.return_value = {
                "total_analyses": 15,
                "total_conversations": 25,
                "avg_analysis_rating": 4.2,
                "last_activity": datetime.utcnow()
            }
            
            # Mock recent data
            mock_analyses.return_value = [
                {"id": 1, "created_at": datetime.utcnow(), "status": "completed"}
            ]
            mock_conversations.return_value = [
                {"id": 1, "title": "Palm Discussion", "updated_at": datetime.utcnow()}
            ]
            
            result = await service.get_user_dashboard(456)
            
            assert "user_info" in result
            assert "analytics" in result
            assert "recent_analyses" in result
            assert "recent_conversations" in result
            assert "engagement_metrics" in result
            assert result["user_info"]["name"] == "Test User"
            assert result["analytics"]["total_analyses"] == 15

    @pytest.mark.asyncio
    async def test_get_user_dashboard_cached(self, service, mock_user):
        """Test cached user dashboard retrieval."""
        cached_dashboard = {
            "user_info": {"name": "Cached User"},
            "analytics": {"total_analyses": 10}
        }
        
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            mock_cache.get.return_value = cached_dashboard
            
            result = await service.get_user_dashboard(456)
            
            assert result == cached_dashboard
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_dashboard_user_not_found(self, service):
        """Test dashboard when user not found."""
        with patch.object(service, '_get_user_by_id') as mock_get_user:
            mock_get_user.return_value = None
            
            with pytest.raises(ValueError, match="User not found"):
                await service.get_user_dashboard(999)

    @pytest.mark.asyncio
    async def test_get_user_preferences_success(self, service, mock_user):
        """Test successful user preferences retrieval."""
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock database query for preferences
            mock_result = AsyncMock()
            mock_result.all.return_value = [
                MagicMock(preference_key="theme", preference_value="dark"),
                MagicMock(preference_key="notifications_email", preference_value="true"),
            ]
            mock_db.execute.return_value = mock_result
            
            result = await service.get_user_preferences(456)
            
            assert "preferences" in result
            assert result["preferences"]["theme"] == "dark"
            assert result["preferences"]["notifications_email"] == "true"
            
            # Should include defaults for missing preferences
            assert "language" in result["preferences"]  # Default value

    @pytest.mark.asyncio
    async def test_get_user_preferences_with_defaults(self, service, mock_user):
        """Test user preferences with default values."""
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            mock_cache.get.return_value = None
            
            # Mock empty preferences
            mock_result = AsyncMock()
            mock_result.all.return_value = []
            mock_db.execute.return_value = mock_result
            
            result = await service.get_user_preferences(456)
            
            # Should return default values
            expected_defaults = service._get_default_preferences()
            assert result["preferences"] == expected_defaults

    @pytest.mark.asyncio
    async def test_update_user_preferences_success(self, service, mock_user):
        """Test successful user preferences update."""
        preferences_data = {
            "theme": "light",
            "notifications_email": "false",
            "language": "es"
        }
        
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            
            # Mock database operations
            mock_result = AsyncMock()
            mock_db.execute.return_value = mock_result
            mock_db.commit.return_value = None
            
            result = await service.update_user_preferences(456, preferences_data)
            
            assert result["success"] is True
            assert result["updated_preferences"] == preferences_data
            
            # Verify cache invalidation
            mock_cache.delete.assert_called_with(f"user_preferences:{456}")

    @pytest.mark.asyncio
    async def test_update_user_preferences_invalid_key(self, service, mock_user):
        """Test update with invalid preference key."""
        invalid_preferences = {
            "invalid_key": "value"
        }
        
        with patch.object(service, '_get_user_by_id') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with pytest.raises(ValueError, match="Invalid preference key"):
                await service.update_user_preferences(456, invalid_preferences)

    @pytest.mark.asyncio
    async def test_get_user_statistics_success(self, service, mock_user):
        """Test successful user statistics retrieval."""
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock multiple database queries
            mock_results = []
            
            # Analysis statistics
            analysis_result = AsyncMock()
            analysis_result.first.return_value = MagicMock(
                total_analyses=20,
                completed_analyses=18,
                avg_cost=0.15,
                total_cost=3.00
            )
            mock_results.append(analysis_result)
            
            # Conversation statistics  
            conversation_result = AsyncMock()
            conversation_result.first.return_value = MagicMock(
                total_conversations=12,
                total_messages=156
            )
            mock_results.append(conversation_result)
            
            # Activity timeline
            activity_result = AsyncMock()
            activity_result.all.return_value = [
                MagicMock(date=datetime.utcnow().date(), analysis_count=2, conversation_count=3)
            ]
            mock_results.append(activity_result)
            
            mock_db.execute.side_effect = mock_results
            
            result = await service.get_user_statistics(456, days=30)
            
            assert "analysis_stats" in result
            assert "conversation_stats" in result
            assert "activity_timeline" in result
            assert "period_summary" in result
            assert result["analysis_stats"]["total"] == 20
            assert result["conversation_stats"]["total_conversations"] == 12

    @pytest.mark.asyncio
    async def test_get_user_achievements_success(self, service, mock_user):
        """Test successful user achievements retrieval."""
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, '_calculate_achievements') as mock_achievements, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock achievement calculation
            mock_achievements.return_value = {
                "unlocked": [
                    {
                        "id": "first_analysis",
                        "title": "First Palm Reading",
                        "description": "Completed your first palm analysis",
                        "unlocked_at": datetime.utcnow(),
                        "category": "analysis"
                    }
                ],
                "progress": [
                    {
                        "id": "analysis_master",
                        "title": "Analysis Master",
                        "description": "Complete 100 palm analyses",
                        "progress": 20,
                        "target": 100,
                        "category": "analysis"
                    }
                ]
            }
            
            result = await service.get_user_achievements(456)
            
            assert "unlocked_achievements" in result
            assert "progress_achievements" in result
            assert "achievement_summary" in result
            assert len(result["unlocked_achievements"]) == 1
            assert len(result["progress_achievements"]) == 1

    @pytest.mark.asyncio
    async def test_export_user_data_success(self, service, mock_user):
        """Test successful GDPR-compliant user data export."""
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, '_collect_user_data') as mock_collect:
            
            mock_get_user.return_value = mock_user
            
            # Mock comprehensive user data collection
            mock_collect.return_value = {
                "user_profile": {
                    "id": 456,
                    "name": "Test User",
                    "email": "test@example.com",
                    "created_at": "2023-12-01T00:00:00Z"
                },
                "analyses": [
                    {"id": 1, "created_at": "2024-01-01T00:00:00Z", "result": "Analysis data"}
                ],
                "conversations": [
                    {"id": 1, "title": "Palm Discussion", "messages": ["Message 1", "Message 2"]}
                ],
                "preferences": {
                    "theme": "dark",
                    "language": "en"
                }
            }
            
            result = await service.export_user_data(456)
            
            assert "export_info" in result
            assert "user_data" in result
            assert result["export_info"]["format"] == "json"
            assert "user_profile" in result["user_data"]
            assert "analyses" in result["user_data"]
            assert "conversations" in result["user_data"]

    @pytest.mark.asyncio
    async def test_calculate_achievements_analysis_milestones(self, service):
        """Test achievement calculation for analysis milestones."""
        user_data = {
            "total_analyses": 25,
            "total_conversations": 10,
            "account_age_days": 45
        }
        
        achievements = await service._calculate_achievements(456, user_data)
        
        # Should unlock first analysis achievement
        unlocked = [ach for ach in achievements["unlocked"] if ach["id"] == "first_analysis"]
        assert len(unlocked) == 1
        
        # Should have progress toward analysis milestones
        progress = [ach for ach in achievements["progress"] if "analysis" in ach["category"]]
        assert len(progress) > 0

    @pytest.mark.asyncio
    async def test_calculate_achievements_conversation_milestones(self, service):
        """Test achievement calculation for conversation milestones."""
        user_data = {
            "total_analyses": 5,
            "total_conversations": 50,
            "total_messages": 200,
            "account_age_days": 30
        }
        
        achievements = await service._calculate_achievements(456, user_data)
        
        # Should unlock conversation achievements
        unlocked_ids = [ach["id"] for ach in achievements["unlocked"]]
        assert "social_butterfly" in unlocked_ids or any("conversation" in ach["id"] for ach in achievements["unlocked"])

    @pytest.mark.asyncio
    async def test_get_default_preferences(self, service):
        """Test default preferences structure."""
        defaults = service._get_default_preferences()
        
        # Should have all required preference keys
        required_keys = [key.value for key in UserPreferenceKey]
        for key in required_keys:
            assert key in defaults
        
        # Should have reasonable default values
        assert defaults["theme"] in ["light", "dark"]
        assert defaults["language"] == "en"
        assert defaults["notifications_email"] in ["true", "false"]

    @pytest.mark.asyncio
    async def test_collect_user_data_comprehensive(self, service, mock_user):
        """Test comprehensive user data collection for export."""
        with patch.object(service, 'db') as mock_db:
            # Mock multiple database queries for different data types
            mock_results = []
            
            # User preferences
            prefs_result = AsyncMock()
            prefs_result.all.return_value = [
                MagicMock(preference_key="theme", preference_value="dark")
            ]
            mock_results.append(prefs_result)
            
            # User analyses
            analyses_result = AsyncMock()
            analyses_result.all.return_value = [
                MagicMock(
                    id=1,
                    created_at=datetime.utcnow(),
                    result={"summary": "Analysis result"},
                    cost=0.15
                )
            ]
            mock_results.append(analyses_result)
            
            # User conversations with messages
            conversations_result = AsyncMock()
            conversations_result.all.return_value = [
                MagicMock(
                    id=1,
                    title="Test Conversation",
                    created_at=datetime.utcnow(),
                    messages=[
                        MagicMock(content="User message", is_ai=False),
                        MagicMock(content="AI response", is_ai=True)
                    ]
                )
            ]
            mock_results.append(conversations_result)
            
            mock_db.execute.side_effect = mock_results
            
            user_data = await service._collect_user_data(mock_user)
            
            assert "user_profile" in user_data
            assert "preferences" in user_data
            assert "analyses" in user_data
            assert "conversations" in user_data
            
            # Verify data completeness
            assert len(user_data["analyses"]) == 1
            assert len(user_data["conversations"]) == 1
            assert user_data["conversations"][0]["messages_count"] == 2

    @pytest.mark.asyncio
    async def test_engagement_metrics_calculation(self, service):
        """Test engagement metrics calculation."""
        analytics = {
            "total_analyses": 15,
            "total_conversations": 25,
            "total_messages": 100,
            "last_activity": datetime.utcnow() - timedelta(days=2),
            "account_age_days": 30
        }
        
        engagement = await service._calculate_engagement_metrics(analytics)
        
        assert "activity_score" in engagement
        assert "engagement_level" in engagement
        assert "days_since_last_activity" in engagement
        assert "analyses_per_week" in engagement
        
        # Activity score should be reasonable
        assert 0 <= engagement["activity_score"] <= 100
        assert engagement["days_since_last_activity"] == 2

    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Test comprehensive error handling."""
        # Test user not found in preferences
        with patch.object(service, '_get_user_by_id') as mock_get_user:
            mock_get_user.return_value = None
            
            with pytest.raises(ValueError, match="User not found"):
                await service.get_user_preferences(999)
        
        # Test database error in statistics
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, 'db') as mock_db:
            
            mock_get_user.return_value = mock_user
            mock_db.execute.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                await service.get_user_statistics(456)

    @pytest.mark.asyncio
    async def test_preference_validation(self, service):
        """Test preference value validation."""
        valid_preferences = {
            "theme": "light",
            "language": "en", 
            "notifications_email": "true"
        }
        
        invalid_preferences = {
            "theme": "invalid_theme",
            "language": "zz",  # Invalid language code
            "privacy_level": "invalid_level"
        }
        
        # Valid preferences should pass
        service._validate_preferences(valid_preferences)
        
        # Invalid preferences should raise errors
        with pytest.raises(ValueError):
            service._validate_preferences(invalid_preferences)

    @pytest.mark.asyncio
    async def test_caching_behavior(self, service, mock_user):
        """Test caching behavior for dashboard components."""
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_get_user.return_value = mock_user
            
            # Test cache keys are properly formatted
            cache_methods = [
                ("get_user_dashboard", (456,)),
                ("get_user_preferences", (456,)),
                ("get_user_statistics", (456, 30)),
                ("get_user_achievements", (456,))
            ]
            
            for method_name, args in cache_methods:
                mock_cache.get.return_value = {"cached": "data"}
                
                method = getattr(service, method_name)
                result = await method(*args)
                
                assert result == {"cached": "data"}
                
                # Verify cache key format
                expected_key_prefix = f"{method_name.replace('get_', '')}:{args[0]}"
                mock_cache.get.assert_called()
                call_args = mock_cache.get.call_args[0]
                assert call_args[0].startswith(expected_key_prefix)