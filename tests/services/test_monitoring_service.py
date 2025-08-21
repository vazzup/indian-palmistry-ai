"""
Tests for Monitoring Service.

This module tests the comprehensive system monitoring service with queue tracking,
resource monitoring, cost analytics, and health reporting.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.services.monitoring_service import MonitoringService


class TestMonitoringService:
    """Test suite for MonitoringService class."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return MonitoringService()

    @pytest.mark.asyncio
    async def test_get_queue_dashboard_success(self, service):
        """Test successful queue dashboard retrieval."""
        with patch.object(service, 'cache_service') as mock_cache, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu:
            
            # Mock cache service for queue stats
            mock_cache.get_queue_stats.return_value = {
                "queues": {"celery": 5, "priority": 2},
                "active_tasks": 3,
                "total_pending": 7
            }
            
            # Mock system resource data
            mock_memory.return_value = MagicMock(
                total=8589934592,  # 8GB
                available=4294967296,  # 4GB
                percent=50.0
            )
            mock_cpu.return_value = 25.5
            
            result = await service.get_queue_dashboard()
            
            assert "queue_stats" in result
            assert "system_resources" in result
            assert "worker_health" in result
            assert "timestamp" in result
            
            # Verify queue stats
            assert result["queue_stats"]["total_pending"] == 7
            assert result["queue_stats"]["active_tasks"] == 3
            
            # Verify system resources
            assert result["system_resources"]["memory"]["percent"] == 50.0
            assert result["system_resources"]["cpu"]["percent"] == 25.5

    @pytest.mark.asyncio
    async def test_get_queue_dashboard_cache_failure(self, service):
        """Test queue dashboard when cache service fails."""
        with patch.object(service, 'cache_service') as mock_cache, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu:
            
            # Mock cache service failure
            mock_cache.get_queue_stats.side_effect = Exception("Redis connection failed")
            
            mock_memory.return_value = MagicMock(
                total=8589934592,
                available=4294967296,
                percent=50.0
            )
            mock_cpu.return_value = 25.5
            
            result = await service.get_queue_dashboard()
            
            # Should handle cache failure gracefully
            assert result["queue_stats"]["error"] == "Failed to fetch queue stats"
            assert "system_resources" in result  # Should still work

    @pytest.mark.asyncio
    async def test_get_system_health_all_healthy(self, service):
        """Test system health check when all components are healthy."""
        with patch.object(service, 'cache_service') as mock_cache, \
             patch.object(service, '_get_connection_metrics') as mock_db_metrics, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Mock healthy cache
            mock_cache.health_check.return_value = {
                "status": "healthy",
                "redis_info": {"version": "7.0.0"}
            }
            
            # Mock healthy database
            mock_db_metrics.return_value = {
                "active_connections": 5,
                "max_connections": 100,
                "connection_health": "healthy"
            }
            
            # Mock healthy system resources
            mock_memory.return_value = MagicMock(percent=45.0)
            mock_cpu.return_value = 20.0
            mock_disk.return_value = MagicMock(percent=30.0)
            
            result = await service.get_system_health()
            
            assert result["overall_status"] == "healthy"
            assert result["components"]["cache"]["status"] == "healthy"
            assert result["components"]["database"]["status"] == "healthy"
            assert result["components"]["system"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_system_health_unhealthy_components(self, service):
        """Test system health check with unhealthy components."""
        with patch.object(service, 'cache_service') as mock_cache, \
             patch.object(service, '_get_connection_metrics') as mock_db_metrics, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Mock unhealthy cache
            mock_cache.health_check.return_value = {
                "status": "unhealthy",
                "error": "Redis connection failed"
            }
            
            # Mock database with high connections
            mock_db_metrics.return_value = {
                "active_connections": 95,
                "max_connections": 100,
                "connection_health": "warning"
            }
            
            # Mock high resource usage
            mock_memory.return_value = MagicMock(percent=95.0)
            mock_cpu.return_value = 90.0
            mock_disk.return_value = MagicMock(percent=85.0)
            
            result = await service.get_system_health()
            
            assert result["overall_status"] == "unhealthy"
            assert result["components"]["cache"]["status"] == "unhealthy"
            assert result["components"]["system"]["status"] == "critical"

    @pytest.mark.asyncio
    async def test_get_cost_analytics_success(self, service):
        """Test successful cost analytics retrieval."""
        with patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock database query results
            mock_results = []
            
            # Total cost query
            total_result = AsyncMock()
            total_result.scalar.return_value = 15.75
            mock_results.append(total_result)
            
            # Daily costs query
            daily_result = AsyncMock()
            daily_result.all.return_value = [
                MagicMock(date=datetime.utcnow().date(), total_cost=2.50, analysis_count=10),
                MagicMock(date=(datetime.utcnow() - timedelta(days=1)).date(), total_cost=3.25, analysis_count=15)
            ]
            mock_results.append(daily_result)
            
            # Token usage query
            token_result = AsyncMock()
            token_result.all.return_value = [
                MagicMock(date=datetime.utcnow().date(), total_tokens=12500, analysis_count=10)
            ]
            mock_results.append(token_result)
            
            mock_db.execute.side_effect = mock_results
            
            result = await service.get_cost_analytics(456, days=30)
            
            assert "summary" in result
            assert "daily_breakdown" in result
            assert "token_usage" in result
            assert result["summary"]["total_cost"] == 15.75
            assert len(result["daily_breakdown"]) == 2
            
            # Verify caching
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cost_analytics_cached(self, service):
        """Test cached cost analytics retrieval."""
        cached_data = {
            "summary": {"total_cost": 10.50},
            "daily_breakdown": [],
            "period_days": 30
        }
        
        with patch.object(service, 'cache_service') as mock_cache:
            mock_cache.get.return_value = cached_data
            
            result = await service.get_cost_analytics(456, days=30)
            
            assert result == cached_data
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_usage_analytics_success(self, service):
        """Test successful usage analytics retrieval."""
        with patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock multiple database queries for different analytics
            mock_results = []
            
            # User activity query
            activity_result = AsyncMock()
            activity_result.all.return_value = [
                MagicMock(date=datetime.utcnow().date(), active_users=25, total_analyses=50, total_conversations=75)
            ]
            mock_results.append(activity_result)
            
            # Popular features query
            features_result = AsyncMock()
            features_result.all.return_value = [
                MagicMock(feature="palm_analysis", usage_count=150),
                MagicMock(feature="conversations", usage_count=100)
            ]
            mock_results.append(features_result)
            
            # Peak hours query
            hours_result = AsyncMock()
            hours_result.all.return_value = [
                MagicMock(hour=14, activity_count=35),  # 2 PM
                MagicMock(hour=20, activity_count=42)   # 8 PM
            ]
            mock_results.append(hours_result)
            
            mock_db.execute.side_effect = mock_results
            
            result = await service.get_usage_analytics(days=7)
            
            assert "user_activity" in result
            assert "popular_features" in result
            assert "peak_usage_hours" in result
            assert len(result["user_activity"]) == 1
            assert len(result["popular_features"]) == 2

    @pytest.mark.asyncio
    async def test_get_connection_metrics_success(self, service):
        """Test successful database connection metrics."""
        with patch.object(service, 'db') as mock_db:
            # Mock database info query
            mock_result = AsyncMock()
            mock_result.mappings.return_value.all.return_value = [
                {"name": "max_connections", "setting": "100"},
                {"name": "shared_buffers", "setting": "128MB"}
            ]
            mock_db.execute.return_value = mock_result
            
            # Mock connection count query
            mock_count_result = AsyncMock()
            mock_count_result.scalar.return_value = 15
            mock_db.execute.side_effect = [mock_result, mock_count_result]
            
            metrics = await service._get_connection_metrics()
            
            assert "active_connections" in metrics
            assert "max_connections" in metrics
            assert "connection_health" in metrics
            assert metrics["active_connections"] == 15
            assert metrics["max_connections"] == 100

    @pytest.mark.asyncio
    async def test_get_recent_slow_queries_success(self, service):
        """Test slow queries detection."""
        with patch.object(service, 'db') as mock_db:
            # Mock slow queries result
            mock_result = AsyncMock()
            mock_result.all.return_value = [
                MagicMock(
                    query="SELECT * FROM analyses WHERE user_id = ?",
                    total_time=1500.0,  # 1.5 seconds
                    calls=10,
                    mean_time=150.0
                )
            ]
            mock_db.execute.return_value = mock_result
            
            slow_queries = await service._get_recent_slow_queries()
            
            assert len(slow_queries) == 1
            assert slow_queries[0]["mean_time"] == 150.0
            assert slow_queries[0]["calls"] == 10

    @pytest.mark.asyncio
    async def test_get_recent_slow_queries_sqlite(self, service):
        """Test slow queries detection for SQLite (should return empty)."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.is_sqlite = True
            
            slow_queries = await service._get_recent_slow_queries()
            
            assert slow_queries == []

    @pytest.mark.asyncio
    async def test_system_resource_thresholds(self, service):
        """Test system resource health thresholds."""
        test_cases = [
            # (memory_percent, cpu_percent, disk_percent, expected_status)
            (30.0, 20.0, 25.0, "healthy"),
            (60.0, 50.0, 60.0, "warning"),
            (85.0, 80.0, 85.0, "critical"),
            (95.0, 95.0, 95.0, "critical")
        ]
        
        for memory_pct, cpu_pct, disk_pct, expected_status in test_cases:
            with patch('psutil.virtual_memory') as mock_memory, \
                 patch('psutil.cpu_percent') as mock_cpu, \
                 patch('psutil.disk_usage') as mock_disk:
                
                mock_memory.return_value = MagicMock(percent=memory_pct)
                mock_cpu.return_value = cpu_pct
                mock_disk.return_value = MagicMock(percent=disk_pct)
                
                resources = await service._get_system_resources()
                
                if expected_status == "healthy":
                    assert all(
                        resources[component]["status"] in ["healthy", "warning"] 
                        for component in ["memory", "cpu", "disk"]
                    )
                elif expected_status == "critical":
                    assert any(
                        resources[component]["status"] == "critical"
                        for component in ["memory", "cpu", "disk"]
                    )

    @pytest.mark.asyncio
    async def test_worker_health_monitoring(self, service):
        """Test worker health status monitoring."""
        with patch.object(service, 'cache_service') as mock_cache:
            # Mock healthy workers
            mock_cache.get_queue_stats.return_value = {
                "queues": {"celery": 3, "priority": 1},
                "active_tasks": 2,
                "total_pending": 4
            }
            
            worker_health = await service._get_worker_health()
            
            assert "queue_depth" in worker_health
            assert "active_workers" in worker_health
            assert "status" in worker_health
            assert worker_health["queue_depth"] == 4

    @pytest.mark.asyncio
    async def test_error_handling(self, service):
        """Test comprehensive error handling."""
        # Test psutil failure
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.side_effect = Exception("System metrics unavailable")
            
            result = await service.get_queue_dashboard()
            
            # Should handle system metrics failure gracefully
            assert "error" in result["system_resources"]
        
        # Test database failure for cost analytics
        with patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_cache.get.return_value = None
            mock_db.execute.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                await service.get_cost_analytics(456)

    @pytest.mark.asyncio
    async def test_caching_behavior(self, service):
        """Test caching behavior for expensive operations."""
        cache_test_methods = [
            ("get_cost_analytics", (456,), {"days": 30}),
            ("get_usage_analytics", (), {"days": 7}),
        ]
        
        for method_name, args, kwargs in cache_test_methods:
            with patch.object(service, 'cache_service') as mock_cache, \
                 patch.object(service, 'db') as mock_db:
                
                # Mock cache miss first, then hit
                mock_cache.get.side_effect = [None, {"cached": "data"}]
                
                # Mock database results
                mock_result = AsyncMock()
                mock_result.scalar.return_value = 0
                mock_result.all.return_value = []
                mock_db.execute.return_value = mock_result
                
                method = getattr(service, method_name)
                
                # First call should cache
                await method(*args, **kwargs)
                mock_cache.set.assert_called()
                
                # Second call should use cache
                mock_cache.set.reset_mock()
                result = await method(*args, **kwargs)
                assert result == {"cached": "data"}
                mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_time_series_data_formatting(self, service):
        """Test time series data formatting for analytics."""
        with patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_cache.get.return_value = None
            
            # Mock time series data
            base_date = datetime.utcnow().date()
            mock_result = AsyncMock()
            mock_result.all.return_value = [
                MagicMock(date=base_date, active_users=25, total_analyses=50),
                MagicMock(date=base_date - timedelta(days=1), active_users=30, total_analyses=60),
            ]
            mock_db.execute.return_value = mock_result
            
            result = await service.get_usage_analytics(days=2)
            
            # Verify chronological ordering (most recent first)
            activity = result["user_activity"]
            assert len(activity) == 2
            assert activity[0]["date"] >= activity[1]["date"]