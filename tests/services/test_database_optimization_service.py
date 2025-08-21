"""
Tests for Database Optimization Service.

This module tests the database performance monitoring, query optimization,
and maintenance operations service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.services.database_optimization_service import DatabaseOptimizationService, QueryPerformanceMonitor


class TestDatabaseOptimizationService:
    """Test suite for DatabaseOptimizationService class."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return DatabaseOptimizationService()

    @pytest.mark.asyncio
    async def test_analyze_query_performance_success(self, service):
        """Test successful query performance analysis."""
        with patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock query performance data
            mock_result = AsyncMock()
            mock_result.all.return_value = [
                MagicMock(
                    query="SELECT * FROM analyses WHERE user_id = ?",
                    total_time=2500.5,
                    calls=50,
                    mean_time=50.01,
                    rows=1000
                ),
                MagicMock(
                    query="SELECT * FROM conversations WHERE analysis_id = ?",
                    total_time=1200.3,
                    calls=25,
                    mean_time=48.012,
                    rows=500
                )
            ]
            mock_db.execute.return_value = mock_result
            
            result = await service.analyze_query_performance(days=7)
            
            assert "analysis_period" in result
            assert "slow_queries" in result
            assert "query_statistics" in result
            assert "recommendations" in result
            
            # Verify slow queries are identified
            assert len(result["slow_queries"]) == 2
            assert result["slow_queries"][0]["mean_time"] > 40  # Above slow query threshold
            
            # Verify caching
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_query_performance_cached(self, service):
        """Test cached query performance analysis."""
        cached_result = {
            "slow_queries": [{"query": "cached query", "mean_time": 100}],
            "analysis_period": {"days": 7}
        }
        
        with patch.object(service, 'cache_service') as mock_cache:
            mock_cache.get.return_value = cached_result
            
            result = await service.analyze_query_performance(days=7)
            
            assert result == cached_result
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_query_performance_sqlite(self, service):
        """Test query performance analysis for SQLite (limited functionality)."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.is_sqlite = True
            
            result = await service.analyze_query_performance()
            
            assert result["database_type"] == "sqlite"
            assert "message" in result
            assert "limited" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_get_database_statistics_success(self, service):
        """Test successful database statistics retrieval."""
        with patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_cache.get.return_value = None  # Cache miss
            
            # Mock database statistics queries
            mock_results = []
            
            # Table sizes query
            table_sizes_result = AsyncMock()
            table_sizes_result.all.return_value = [
                MagicMock(table_name="analyses", size_mb=45.2, row_count=1500),
                MagicMock(table_name="conversations", size_mb=12.8, row_count=850),
                MagicMock(table_name="messages", size_mb=8.3, row_count=2300)
            ]
            mock_results.append(table_sizes_result)
            
            # Index usage query
            index_usage_result = AsyncMock()
            index_usage_result.all.return_value = [
                MagicMock(
                    table_name="analyses",
                    index_name="ix_analyses_user_id_status",
                    scans=1500,
                    tuples_read=1500,
                    tuples_fetched=1500
                )
            ]
            mock_results.append(index_usage_result)
            
            # Connection statistics
            connection_stats_result = AsyncMock()
            connection_stats_result.first.return_value = MagicMock(
                active_connections=8,
                max_connections=100,
                connection_utilization=0.08
            )
            mock_results.append(connection_stats_result)
            
            mock_db.execute.side_effect = mock_results
            
            result = await service.get_database_statistics()
            
            assert "table_statistics" in result
            assert "index_usage" in result
            assert "connection_statistics" in result
            assert "database_size" in result
            
            # Verify table statistics
            assert len(result["table_statistics"]) == 3
            assert result["table_statistics"][0]["table_name"] == "analyses"
            assert result["table_statistics"][0]["size_mb"] == 45.2
            
            # Verify total database size calculation
            expected_total_size = 45.2 + 12.8 + 8.3  # Sum of table sizes
            assert abs(result["database_size"]["total_mb"] - expected_total_size) < 0.1

    @pytest.mark.asyncio
    async def test_get_database_statistics_sqlite(self, service):
        """Test database statistics for SQLite with different queries."""
        with patch('app.core.config.settings') as mock_settings, \
             patch.object(service, 'db') as mock_db, \
             patch.object(service, 'cache_service') as mock_cache:
            
            mock_settings.is_sqlite = True
            mock_cache.get.return_value = None
            
            # Mock SQLite-specific queries
            sqlite_result = AsyncMock()
            sqlite_result.all.return_value = [
                MagicMock(name="analyses", row_count=1500),
                MagicMock(name="conversations", row_count=850)
            ]
            mock_db.execute.return_value = sqlite_result
            
            result = await service.get_database_statistics()
            
            assert "table_statistics" in result
            assert result["database_type"] == "sqlite"

    @pytest.mark.asyncio
    async def test_optimize_queries_success(self, service):
        """Test successful query optimization recommendations."""
        with patch.object(service, 'analyze_query_performance') as mock_analyze, \
             patch.object(service, 'get_database_statistics') as mock_stats, \
             patch.object(service, '_generate_optimization_recommendations') as mock_recommendations:
            
            # Mock performance analysis
            mock_analyze.return_value = {
                "slow_queries": [
                    {"query": "SELECT * FROM analyses WHERE user_id = ?", "mean_time": 85.5},
                    {"query": "SELECT * FROM conversations WHERE title ILIKE ?", "mean_time": 120.2}
                ]
            }
            
            # Mock database statistics
            mock_stats.return_value = {
                "table_statistics": [
                    {"table_name": "analyses", "row_count": 10000, "size_mb": 150}
                ],
                "index_usage": [
                    {"index_name": "ix_analyses_user_id", "scans": 5000}
                ]
            }
            
            # Mock recommendations
            mock_recommendations.return_value = [
                {
                    "type": "index",
                    "priority": "high",
                    "description": "Add index on conversations.title for text searches",
                    "sql": "CREATE INDEX ix_conversations_title_gin ON conversations USING gin (to_tsvector('english', title))"
                }
            ]
            
            result = await service.optimize_queries()
            
            assert "optimization_summary" in result
            assert "recommendations" in result
            assert "performance_impact" in result
            assert len(result["recommendations"]) == 1
            assert result["recommendations"][0]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_vacuum_analyze_tables_success(self, service):
        """Test successful VACUUM ANALYZE operations."""
        with patch.object(service, 'db') as mock_db:
            # Mock successful VACUUM operations
            mock_db.execute.return_value = AsyncMock()
            mock_db.commit.return_value = None
            
            result = await service.vacuum_analyze_tables(["analyses", "conversations"])
            
            assert result["success"] is True
            assert "operations_completed" in result
            assert len(result["operations_completed"]) == 2
            assert "analyses" in result["operations_completed"]
            assert "conversations" in result["operations_completed"]

    @pytest.mark.asyncio
    async def test_vacuum_analyze_tables_sqlite(self, service):
        """Test VACUUM operations for SQLite."""
        with patch('app.core.config.settings') as mock_settings, \
             patch.object(service, 'db') as mock_db:
            
            mock_settings.is_sqlite = True
            mock_db.execute.return_value = AsyncMock()
            mock_db.commit.return_value = None
            
            result = await service.vacuum_analyze_tables()
            
            assert result["success"] is True
            assert result["database_type"] == "sqlite"

    @pytest.mark.asyncio
    async def test_create_missing_indexes_success(self, service):
        """Test successful creation of missing indexes."""
        with patch.object(service, '_identify_missing_indexes') as mock_identify, \
             patch.object(service, 'db') as mock_db:
            
            # Mock missing indexes identification
            mock_identify.return_value = [
                {
                    "table": "analyses",
                    "columns": ["user_id", "created_at"],
                    "index_name": "ix_analyses_user_id_created_at",
                    "sql": "CREATE INDEX ix_analyses_user_id_created_at ON analyses (user_id, created_at)"
                },
                {
                    "table": "messages", 
                    "columns": ["content"],
                    "index_name": "ix_messages_content_gin",
                    "sql": "CREATE INDEX ix_messages_content_gin ON messages USING gin (to_tsvector('english', content))"
                }
            ]
            
            mock_db.execute.return_value = AsyncMock()
            mock_db.commit.return_value = None
            
            result = await service.create_missing_indexes()
            
            assert result["success"] is True
            assert "indexes_created" in result
            assert len(result["indexes_created"]) == 2
            assert "ix_analyses_user_id_created_at" in [idx["index_name"] for idx in result["indexes_created"]]

    @pytest.mark.asyncio
    async def test_create_missing_indexes_error_handling(self, service):
        """Test error handling in index creation."""
        with patch.object(service, '_identify_missing_indexes') as mock_identify, \
             patch.object(service, 'db') as mock_db:
            
            mock_identify.return_value = [
                {
                    "table": "analyses",
                    "index_name": "ix_duplicate_index",
                    "sql": "CREATE INDEX ix_duplicate_index ON analyses (user_id)"
                }
            ]
            
            # Mock index creation failure (e.g., index already exists)
            mock_db.execute.side_effect = Exception("Index already exists")
            
            result = await service.create_missing_indexes()
            
            assert result["success"] is False
            assert "errors" in result
            assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_identify_missing_indexes_based_on_queries(self, service):
        """Test identification of missing indexes based on slow queries."""
        with patch.object(service, 'analyze_query_performance') as mock_analyze:
            
            mock_analyze.return_value = {
                "slow_queries": [
                    {
                        "query": "SELECT * FROM analyses WHERE user_id = ? AND status = ?",
                        "mean_time": 150.5,
                        "calls": 1000
                    },
                    {
                        "query": "SELECT * FROM conversations WHERE analysis_id = ? ORDER BY updated_at DESC",
                        "mean_time": 85.2,
                        "calls": 500
                    }
                ]
            }
            
            missing_indexes = await service._identify_missing_indexes()
            
            assert len(missing_indexes) > 0
            
            # Should suggest composite indexes for multi-column WHERE clauses
            index_suggestions = [idx["columns"] for idx in missing_indexes]
            
            # Look for composite indexes
            assert any(len(cols) > 1 for cols in index_suggestions)

    @pytest.mark.asyncio
    async def test_generate_optimization_recommendations(self, service):
        """Test generation of optimization recommendations."""
        performance_data = {
            "slow_queries": [
                {
                    "query": "SELECT * FROM analyses WHERE result ILIKE ?",
                    "mean_time": 200.5,
                    "calls": 800
                }
            ]
        }
        
        statistics_data = {
            "table_statistics": [
                {"table_name": "analyses", "row_count": 50000, "size_mb": 500}
            ]
        }
        
        recommendations = await service._generate_optimization_recommendations(
            performance_data, statistics_data
        )
        
        assert len(recommendations) > 0
        
        # Should include different types of recommendations
        recommendation_types = [rec["type"] for rec in recommendations]
        possible_types = ["index", "query", "maintenance", "configuration"]
        
        assert any(rec_type in possible_types for rec_type in recommendation_types)

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, service):
        """Test integration with performance monitoring."""
        with patch.object(service, 'cache_service') as mock_cache:
            # Test that performance metrics are cached for monitoring
            mock_cache.set.return_value = True
            
            # Simulate performance analysis that should be monitored
            with patch.object(service, 'db') as mock_db:
                mock_result = AsyncMock()
                mock_result.all.return_value = []
                mock_db.execute.return_value = mock_result
                
                await service.analyze_query_performance()
                
                # Should cache performance metrics
                mock_cache.set.assert_called()
                
                # Cache key should be for performance monitoring
                cache_calls = mock_cache.set.call_args_list
                assert any("performance" in str(call) for call in cache_calls)

    @pytest.mark.asyncio
    async def test_error_handling_database_unavailable(self, service):
        """Test error handling when database is unavailable."""
        with patch.object(service, 'db') as mock_db:
            mock_db.execute.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                await service.get_database_statistics()

    @pytest.mark.asyncio
    async def test_caching_behavior(self, service):
        """Test caching behavior for expensive operations."""
        cache_methods = [
            "analyze_query_performance",
            "get_database_statistics"
        ]
        
        for method_name in cache_methods:
            with patch.object(service, 'cache_service') as mock_cache, \
                 patch.object(service, 'db') as mock_db:
                
                # First call - cache miss
                mock_cache.get.return_value = None
                mock_result = AsyncMock()
                mock_result.all.return_value = []
                mock_result.first.return_value = None
                mock_db.execute.return_value = mock_result
                
                method = getattr(service, method_name)
                await method()
                
                # Should set cache
                mock_cache.set.assert_called()
                
                # Second call - cache hit
                mock_cache.get.return_value = {"cached": "data"}
                mock_cache.set.reset_mock()
                
                result = await method()
                
                # Should use cached data
                assert result == {"cached": "data"}
                mock_cache.set.assert_not_called()


class TestQueryPerformanceMonitor:
    """Test suite for QueryPerformanceMonitor context manager."""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance for testing."""
        return QueryPerformanceMonitor("test_query", {"param1": "value1"})

    def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.query_name == "test_query"
        assert monitor.parameters == {"param1": "value1"}
        assert monitor.start_time is None
        assert monitor.end_time is None

    @pytest.mark.asyncio
    async def test_monitor_context_manager(self, monitor):
        """Test monitor as async context manager."""
        with patch.object(monitor, '_log_performance') as mock_log:
            async with monitor:
                # Simulate some work
                await asyncio.sleep(0.01)
            
            assert monitor.start_time is not None
            assert monitor.end_time is not None
            assert monitor.end_time > monitor.start_time
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitor_exception_handling(self, monitor):
        """Test monitor handles exceptions properly."""
        with patch.object(monitor, '_log_performance') as mock_log:
            try:
                async with monitor:
                    raise Exception("Test exception")
            except Exception:
                pass
            
            # Should still log performance even if exception occurred
            mock_log.assert_called_once()

    def test_get_duration_ms(self, monitor):
        """Test duration calculation in milliseconds."""
        import time
        
        monitor.start_time = time.time()
        time.sleep(0.05)  # 50ms
        monitor.end_time = time.time()
        
        duration = monitor.get_duration_ms()
        
        # Should be approximately 50ms (with some tolerance)
        assert 40 <= duration <= 60

    @pytest.mark.asyncio
    async def test_monitor_slow_query_logging(self, monitor):
        """Test slow query detection and logging."""
        with patch.object(monitor, 'logger') as mock_logger:
            monitor.slow_query_threshold_ms = 10  # Very low threshold
            
            async with monitor:
                await asyncio.sleep(0.02)  # 20ms - should be "slow"
            
            # Should log slow query warning
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitor_with_cache_service(self, monitor):
        """Test monitor integration with cache service."""
        with patch('app.core.cache.cache_service') as mock_cache:
            async with monitor:
                await asyncio.sleep(0.01)
            
            # Should cache performance metrics
            mock_cache.set.assert_called_once()
            
            # Cache key should include query name
            call_args = mock_cache.set.call_args[0]
            assert "test_query" in call_args[0]  # Cache key

# Additional test to ensure asyncio is imported
import asyncio