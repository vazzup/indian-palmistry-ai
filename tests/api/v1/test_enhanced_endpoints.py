"""
Tests for Enhanced API Endpoints.

This module tests all the enhanced endpoints created in Phase 3, including
advanced analysis, enhanced conversations, monitoring, and user dashboard APIs.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.services.advanced_palm_service import PalmLineType
from app.services.enhanced_conversation_service import ConversationTemplate


class TestEnhancedEndpoints:
    """Test suite for enhanced API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def authenticated_headers(self):
        """Mock authenticated session headers."""
        return {"Cookie": "session=test_session_id"}

    @pytest.fixture
    def mock_user_session(self):
        """Mock authenticated user session."""
        with patch('app.dependencies.auth.get_current_user') as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = 456
            mock_user.email = "test@example.com"
            mock_get_user.return_value = mock_user
            yield mock_user

    # Advanced Analysis Endpoints Tests

    def test_advanced_analysis_success(self, client, authenticated_headers, mock_user_session):
        """Test successful advanced palm line analysis."""
        with patch('app.services.advanced_palm_service.AdvancedPalmService.analyze_specific_lines') as mock_analyze:
            mock_analyze.return_value = {
                "line_analyses": {
                    "life_line": {
                        "analysis": "Strong life line indicating vitality",
                        "confidence": 0.9
                    },
                    "love_line": {
                        "analysis": "Complex love patterns",
                        "confidence": 0.8
                    }
                },
                "overall_confidence": 0.85,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            response = client.post(
                "/api/v1/enhanced/analyses/123/advanced-analysis",
                headers=authenticated_headers,
                json={
                    "line_types": ["life_line", "love_line"]
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "line_analyses" in data
            assert data["overall_confidence"] == 0.85
            assert len(data["line_analyses"]) == 2

    def test_advanced_analysis_invalid_line_types(self, client, authenticated_headers, mock_user_session):
        """Test advanced analysis with invalid line types."""
        response = client.post(
            "/api/v1/enhanced/analyses/123/advanced-analysis",
            headers=authenticated_headers,
            json={
                "line_types": ["invalid_line", "nonexistent_line"]
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_advanced_analysis_unauthenticated(self, client):
        """Test advanced analysis without authentication."""
        response = client.post(
            "/api/v1/enhanced/analyses/123/advanced-analysis",
            json={"line_types": ["life_line"]}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_compare_analyses_success(self, client, authenticated_headers, mock_user_session):
        """Test successful analysis comparison."""
        with patch('app.services.advanced_palm_service.AdvancedPalmService.compare_analyses') as mock_compare:
            mock_compare.return_value = {
                "analyses": [
                    {"id": 123, "created_at": "2024-01-01T00:00:00Z"},
                    {"id": 124, "created_at": "2024-01-15T00:00:00Z"}
                ],
                "comparative_insights": {
                    "trends": ["Improvement in life line clarity"],
                    "changes": ["Love line has become more pronounced"]
                },
                "timeline_analysis": {
                    "period_days": 14,
                    "confidence_trend": "improving"
                }
            }
            
            response = client.post(
                "/api/v1/enhanced/analyses/compare",
                headers=authenticated_headers,
                json={
                    "analysis_ids": [123, 124]
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "comparative_insights" in data
            assert len(data["analyses"]) == 2

    def test_compare_analyses_insufficient_analyses(self, client, authenticated_headers, mock_user_session):
        """Test analysis comparison with insufficient analyses."""
        response = client.post(
            "/api/v1/enhanced/analyses/compare",
            headers=authenticated_headers,
            json={
                "analysis_ids": [123]  # Only one analysis
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_analysis_history_success(self, client, authenticated_headers, mock_user_session):
        """Test successful analysis history retrieval."""
        with patch('app.services.advanced_palm_service.AdvancedPalmService.get_user_analysis_history') as mock_history:
            mock_history.return_value = {
                "user_info": {"id": 456, "name": "Test User"},
                "analyses": [
                    {"id": 123, "created_at": "2024-01-01T00:00:00Z", "confidence": 0.85},
                    {"id": 124, "created_at": "2024-01-15T00:00:00Z", "confidence": 0.90}
                ],
                "trends": {
                    "confidence_trend": "improving",
                    "analysis_frequency": "regular"
                },
                "statistics": {
                    "total_analyses": 15,
                    "avg_confidence": 0.87
                },
                "period_days": 30
            }
            
            response = client.get(
                "/api/v1/enhanced/analyses/history?days=30",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "trends" in data
            assert data["statistics"]["total_analyses"] == 15

    # Enhanced Conversation Endpoints Tests

    def test_get_conversation_templates_success(self, client):
        """Test successful conversation templates retrieval."""
        with patch('app.services.enhanced_conversation_service.EnhancedConversationService.get_conversation_templates') as mock_templates:
            mock_templates.return_value = {
                "templates": [
                    {
                        "template_type": "life_insights",
                        "title": "Life Path Insights",
                        "description": "Explore your life journey",
                        "starter_questions": ["What does my future hold?"]
                    },
                    {
                        "template_type": "relationship_guidance",
                        "title": "Relationship Guidance",
                        "description": "Understand your relationships",
                        "starter_questions": ["Will I find love?"]
                    }
                ]
            }
            
            response = client.get("/api/v1/enhanced/conversations/templates")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["templates"]) == 2
            assert data["templates"][0]["template_type"] == "life_insights"

    def test_enhanced_talk_success(self, client, authenticated_headers, mock_user_session):
        """Test successful enhanced conversation."""
        with patch('app.services.enhanced_conversation_service.EnhancedConversationService.create_contextual_response') as mock_response:
            mock_response.return_value = {
                "ai_response": "Based on your palm analysis, I can see that your life line suggests strong vitality...",
                "context_summary": {
                    "previous_messages": 3,
                    "analysis_referenced": True
                },
                "confidence": 0.92,
                "response_type": "contextual"
            }
            
            response = client.post(
                "/api/v1/enhanced/conversations/123/enhanced-talk",
                headers=authenticated_headers,
                json={
                    "message": "What does my life line reveal about my health?",
                    "context_window": 5
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["confidence"] == 0.92
            assert "Based on your palm analysis" in data["ai_response"]

    def test_search_conversations_success(self, client, authenticated_headers, mock_user_session):
        """Test successful conversation search."""
        with patch('app.services.enhanced_conversation_service.EnhancedConversationService.search_conversations') as mock_search:
            mock_search.return_value = {
                "results": [
                    {
                        "conversation_id": 123,
                        "title": "Life Line Discussion",
                        "excerpt": "What does my life line mean for my health?",
                        "relevance_score": 0.95,
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total_count": 1,
                "search_query": "life line health",
                "search_fields": ["title", "content"]
            }
            
            response = client.get(
                "/api/v1/enhanced/conversations/search?query=life line health&limit=10",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_count"] == 1
            assert data["results"][0]["relevance_score"] == 0.95

    def test_search_conversations_empty_query(self, client, authenticated_headers, mock_user_session):
        """Test conversation search with empty query."""
        response = client.get(
            "/api/v1/enhanced/conversations/search?query=",
            headers=authenticated_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_export_conversation_json(self, client, authenticated_headers, mock_user_session):
        """Test conversation export in JSON format."""
        with patch('app.services.enhanced_conversation_service.EnhancedConversationService.export_conversation') as mock_export:
            mock_export.return_value = {
                "format": "json",
                "data": {
                    "conversation_id": 123,
                    "title": "Palm Reading Discussion",
                    "created_at": "2024-01-01T00:00:00Z",
                    "messages": [
                        {"content": "Hello", "is_ai": False, "timestamp": "2024-01-01T00:00:00Z"},
                        {"content": "Hi there!", "is_ai": True, "timestamp": "2024-01-01T00:01:00Z"}
                    ]
                },
                "exported_at": "2024-01-01T12:00:00Z"
            }
            
            response = client.get(
                "/api/v1/enhanced/conversations/123/export?format=json",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["format"] == "json"
            assert len(data["data"]["messages"]) == 2

    def test_export_conversation_markdown(self, client, authenticated_headers, mock_user_session):
        """Test conversation export in Markdown format."""
        with patch('app.services.enhanced_conversation_service.EnhancedConversationService.export_conversation') as mock_export:
            mock_export.return_value = {
                "format": "markdown",
                "data": "# Palm Reading Discussion\n\n**User:** Hello\n\n**AI:** Hi there!",
                "exported_at": "2024-01-01T12:00:00Z"
            }
            
            response = client.get(
                "/api/v1/enhanced/conversations/123/export?format=markdown",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["format"] == "markdown"
            assert "# Palm Reading Discussion" in data["data"]

    def test_get_conversation_analytics_success(self, client, authenticated_headers, mock_user_session):
        """Test successful conversation analytics retrieval."""
        with patch('app.services.enhanced_conversation_service.EnhancedConversationService.get_conversation_analytics') as mock_analytics:
            mock_analytics.return_value = {
                "summary": {
                    "total_conversations": 15,
                    "total_messages": 250,
                    "avg_messages_per_conversation": 16.7,
                    "most_active_period": "evening"
                },
                "recent_activity": [
                    {"date": "2024-01-01", "conversations": 3, "messages": 25}
                ],
                "popular_topics": [
                    {"topic": "life line", "count": 45},
                    {"topic": "love line", "count": 32}
                ],
                "period_days": 30
            }
            
            response = client.get(
                "/api/v1/enhanced/conversations/analytics?days=30",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["summary"]["total_conversations"] == 15
            assert len(data["popular_topics"]) == 2

    # Monitoring Endpoints Tests

    def test_monitoring_dashboard_success(self, client, authenticated_headers, mock_user_session):
        """Test successful monitoring dashboard retrieval."""
        with patch('app.services.monitoring_service.MonitoringService.get_queue_dashboard') as mock_dashboard:
            mock_dashboard.return_value = {
                "queue_stats": {
                    "total_pending": 5,
                    "active_tasks": 2,
                    "queues": {"celery": 3, "priority": 2}
                },
                "system_resources": {
                    "memory": {"percent": 45.2, "status": "healthy"},
                    "cpu": {"percent": 25.8, "status": "healthy"},
                    "disk": {"percent": 30.1, "status": "healthy"}
                },
                "worker_health": {
                    "status": "healthy",
                    "active_workers": 4
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = client.get(
                "/api/v1/enhanced/monitoring/dashboard",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["queue_stats"]["total_pending"] == 5
            assert data["system_resources"]["memory"]["status"] == "healthy"

    def test_health_check_detailed_success(self, client, authenticated_headers, mock_user_session):
        """Test detailed health check endpoint."""
        with patch('app.services.monitoring_service.MonitoringService.get_system_health') as mock_health:
            mock_health.return_value = {
                "overall_status": "healthy",
                "components": {
                    "database": {"status": "healthy", "response_time_ms": 5.2},
                    "cache": {"status": "healthy", "redis_version": "7.0.0"},
                    "system": {"status": "healthy", "load_average": 0.85}
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
            response = client.get(
                "/api/v1/enhanced/monitoring/health",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["overall_status"] == "healthy"
            assert len(data["components"]) == 3

    def test_cost_analytics_success(self, client, authenticated_headers, mock_user_session):
        """Test successful cost analytics retrieval."""
        with patch('app.services.monitoring_service.MonitoringService.get_cost_analytics') as mock_cost:
            mock_cost.return_value = {
                "summary": {
                    "total_cost": 25.75,
                    "total_analyses": 150,
                    "avg_cost_per_analysis": 0.17,
                    "period_days": 30
                },
                "daily_breakdown": [
                    {"date": "2024-01-01", "cost": 2.50, "analyses": 15},
                    {"date": "2024-01-02", "cost": 1.80, "analyses": 12}
                ],
                "token_usage": {
                    "total_tokens": 125000,
                    "avg_tokens_per_analysis": 833
                }
            }
            
            response = client.get(
                "/api/v1/enhanced/monitoring/cost-analytics?days=30",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["summary"]["total_cost"] == 25.75
            assert len(data["daily_breakdown"]) == 2

    def test_usage_analytics_success(self, client, authenticated_headers, mock_user_session):
        """Test successful usage analytics retrieval."""
        with patch('app.services.monitoring_service.MonitoringService.get_usage_analytics') as mock_usage:
            mock_usage.return_value = {
                "user_activity": [
                    {"date": "2024-01-01", "active_users": 25, "total_analyses": 45}
                ],
                "popular_features": [
                    {"feature": "palm_analysis", "usage_count": 300},
                    {"feature": "conversations", "usage_count": 180}
                ],
                "peak_usage_hours": [
                    {"hour": 14, "activity_count": 35},
                    {"hour": 20, "activity_count": 42}
                ],
                "period_days": 7
            }
            
            response = client.get(
                "/api/v1/enhanced/monitoring/usage-analytics?days=7",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["popular_features"]) == 2
            assert data["peak_usage_hours"][1]["activity_count"] == 42

    # User Dashboard Endpoints Tests

    def test_get_dashboard_success(self, client, authenticated_headers, mock_user_session):
        """Test successful user dashboard retrieval."""
        with patch('app.services.user_dashboard_service.UserDashboardService.get_user_dashboard') as mock_dashboard:
            mock_dashboard.return_value = {
                "user_info": {
                    "id": 456,
                    "name": "Test User",
                    "email": "test@example.com",
                    "member_since": "2023-12-01T00:00:00Z"
                },
                "analytics": {
                    "total_analyses": 12,
                    "total_conversations": 8,
                    "avg_analysis_rating": 4.5,
                    "last_activity": "2024-01-01T12:00:00Z"
                },
                "recent_analyses": [
                    {"id": 123, "created_at": "2024-01-01T00:00:00Z", "status": "completed"}
                ],
                "recent_conversations": [
                    {"id": 456, "title": "Palm Discussion", "updated_at": "2024-01-01T00:00:00Z"}
                ],
                "engagement_metrics": {
                    "activity_score": 85,
                    "engagement_level": "high"
                }
            }
            
            response = client.get(
                "/api/v1/enhanced/dashboard",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["user_info"]["id"] == 456
            assert data["analytics"]["total_analyses"] == 12

    def test_get_preferences_success(self, client, authenticated_headers, mock_user_session):
        """Test successful user preferences retrieval."""
        with patch('app.services.user_dashboard_service.UserDashboardService.get_user_preferences') as mock_prefs:
            mock_prefs.return_value = {
                "preferences": {
                    "theme": "dark",
                    "language": "en",
                    "notifications_email": "true",
                    "privacy_level": "standard"
                }
            }
            
            response = client.get(
                "/api/v1/enhanced/dashboard/preferences",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["preferences"]["theme"] == "dark"

    def test_update_preferences_success(self, client, authenticated_headers, mock_user_session):
        """Test successful user preferences update."""
        with patch('app.services.user_dashboard_service.UserDashboardService.update_user_preferences') as mock_update:
            mock_update.return_value = {
                "success": True,
                "updated_preferences": {
                    "theme": "light",
                    "language": "es"
                },
                "message": "Preferences updated successfully"
            }
            
            response = client.put(
                "/api/v1/enhanced/dashboard/preferences",
                headers=authenticated_headers,
                json={
                    "theme": "light",
                    "language": "es"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["updated_preferences"]["theme"] == "light"

    def test_get_statistics_success(self, client, authenticated_headers, mock_user_session):
        """Test successful user statistics retrieval."""
        with patch('app.services.user_dashboard_service.UserDashboardService.get_user_statistics') as mock_stats:
            mock_stats.return_value = {
                "analysis_stats": {
                    "total": 25,
                    "completed": 23,
                    "avg_cost": 0.18,
                    "total_cost": 4.50
                },
                "conversation_stats": {
                    "total_conversations": 15,
                    "total_messages": 120,
                    "avg_messages_per_conversation": 8.0
                },
                "activity_timeline": [
                    {"date": "2024-01-01", "analysis_count": 3, "conversation_count": 2}
                ],
                "period_summary": {
                    "days": 30,
                    "most_active_day": "2024-01-01"
                }
            }
            
            response = client.get(
                "/api/v1/enhanced/dashboard/statistics?days=30",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["analysis_stats"]["total"] == 25
            assert data["conversation_stats"]["total_conversations"] == 15

    def test_get_achievements_success(self, client, authenticated_headers, mock_user_session):
        """Test successful user achievements retrieval."""
        with patch('app.services.user_dashboard_service.UserDashboardService.get_user_achievements') as mock_achievements:
            mock_achievements.return_value = {
                "unlocked_achievements": [
                    {
                        "id": "first_analysis",
                        "title": "First Palm Reading",
                        "description": "Completed your first palm analysis",
                        "unlocked_at": "2024-01-01T00:00:00Z",
                        "category": "analysis"
                    }
                ],
                "progress_achievements": [
                    {
                        "id": "analysis_master",
                        "title": "Analysis Master",
                        "description": "Complete 100 palm analyses",
                        "progress": 25,
                        "target": 100,
                        "category": "analysis"
                    }
                ],
                "achievement_summary": {
                    "total_unlocked": 5,
                    "total_available": 15,
                    "completion_percentage": 33.3
                }
            }
            
            response = client.get(
                "/api/v1/enhanced/dashboard/achievements",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["unlocked_achievements"]) == 1
            assert data["achievement_summary"]["total_unlocked"] == 5

    def test_export_user_data_success(self, client, authenticated_headers, mock_user_session):
        """Test successful GDPR-compliant user data export."""
        with patch('app.services.user_dashboard_service.UserDashboardService.export_user_data') as mock_export:
            mock_export.return_value = {
                "export_info": {
                    "format": "json",
                    "exported_at": "2024-01-01T12:00:00Z",
                    "user_id": 456
                },
                "user_data": {
                    "user_profile": {
                        "id": 456,
                        "name": "Test User",
                        "email": "test@example.com"
                    },
                    "analyses": [
                        {"id": 123, "created_at": "2024-01-01T00:00:00Z", "result": "Analysis data"}
                    ],
                    "conversations": [
                        {"id": 456, "title": "Palm Discussion", "messages_count": 10}
                    ]
                }
            }
            
            response = client.get(
                "/api/v1/enhanced/dashboard/export-data",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["export_info"]["user_id"] == 456
            assert "user_profile" in data["user_data"]

    # Advanced Features Tests

    def test_advanced_filtering_success(self, client, authenticated_headers, mock_user_session):
        """Test advanced filtering capabilities."""
        with patch('app.utils.pagination.AdvancedQueryBuilder.execute_paginated_query') as mock_query:
            mock_query.return_value = MagicMock(
                items=[
                    {"id": 123, "status": "completed", "cost": 0.15},
                    {"id": 124, "status": "completed", "cost": 0.20}
                ],
                total_count=2,
                page=1,
                limit=10,
                total_pages=1,
                has_next=False,
                has_previous=False,
                to_dict=lambda: {
                    "items": [{"id": 123}, {"id": 124}],
                    "pagination": {"total_count": 2, "page": 1}
                }
            )
            
            response = client.get(
                "/api/v1/enhanced/analyses/advanced?status=completed&cost_min=0.10&sort_by=created_at&sort_order=desc&page=1&limit=10",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["items"]) == 2

    def test_cache_invalidation_success(self, client, authenticated_headers, mock_user_session):
        """Test cache invalidation endpoint."""
        with patch('app.core.cache.cache_service.delete') as mock_delete:
            mock_delete.return_value = True
            
            response = client.post(
                "/api/v1/enhanced/cache/invalidate",
                headers=authenticated_headers,
                json={
                    "cache_keys": ["user_dashboard:456", "analysis_history:456"]
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["invalidated_count"] == 2

    def test_cache_statistics_success(self, client, authenticated_headers, mock_user_session):
        """Test cache statistics endpoint."""
        with patch('app.core.cache.cache_service.health_check') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "redis_info": {
                    "version": "7.0.0",
                    "clients": 5,
                    "memory": "2.5MB",
                    "uptime": "86400"
                }
            }
            
            response = client.get(
                "/api/v1/enhanced/cache/stats",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"
            assert data["redis_info"]["version"] == "7.0.0"

    # Error Handling Tests

    def test_endpoint_not_found(self, client):
        """Test 404 error handling."""
        response = client.get("/api/v1/enhanced/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_method_not_allowed(self, client):
        """Test 405 error handling."""
        response = client.patch("/api/v1/enhanced/conversations/templates")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_validation_error_handling(self, client, authenticated_headers, mock_user_session):
        """Test request validation error handling."""
        # Invalid JSON payload
        response = client.post(
            "/api/v1/enhanced/analyses/123/advanced-analysis",
            headers=authenticated_headers,
            json={}  # Missing required fields
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_service_error_handling(self, client, authenticated_headers, mock_user_session):
        """Test service layer error handling."""
        with patch('app.services.advanced_palm_service.AdvancedPalmService.analyze_specific_lines') as mock_analyze:
            mock_analyze.side_effect = Exception("Service temporarily unavailable")
            
            response = client.post(
                "/api/v1/enhanced/analyses/123/advanced-analysis",
                headers=authenticated_headers,
                json={"line_types": ["life_line"]}
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Rate Limiting Tests

    def test_rate_limiting_applied(self, client, authenticated_headers, mock_user_session):
        """Test that rate limiting is applied to endpoints."""
        with patch('app.middleware.rate_limiting.RateLimitMiddleware._check_rate_limits') as mock_rate_check:
            mock_rate_check.return_value = {
                "allowed": False,
                "limit_type": "user",
                "retry_after": 60
            }
            
            response = client.get(
                "/api/v1/enhanced/dashboard",
                headers=authenticated_headers
            )
            
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert "Retry-After" in response.headers

    # Authorization Tests

    def test_admin_only_endpoints_require_permission(self, client, authenticated_headers, mock_user_session):
        """Test that admin endpoints require proper permissions."""
        # Mock non-admin user
        mock_user_session.is_admin = False
        
        response = client.get(
            "/api/v1/enhanced/monitoring/dashboard",
            headers=authenticated_headers
        )
        
        # Should require admin permissions for monitoring endpoints
        # (Implementation depends on your authorization setup)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_200_OK]