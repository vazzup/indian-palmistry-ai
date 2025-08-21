"""
Tests for Redis caching service.

This module tests the enhanced Redis caching service with connection pooling,
job monitoring, rate limiting, and analytics features.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.core.cache import CacheService, cache_service


class TestCacheService:
    """Test suite for CacheService class."""

    @pytest.fixture
    async def cache_service_instance(self):
        """Create a fresh cache service instance for testing."""
        service = CacheService()
        yield service
        # Cleanup
        if service.redis_pool:
            await service.close()

    @pytest.fixture
    def mock_redis_pool(self):
        """Mock Redis connection pool."""
        mock_pool = AsyncMock()
        mock_redis = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_redis
        return mock_pool, mock_redis

    @pytest.mark.asyncio
    async def test_connect_success(self, cache_service_instance):
        """Test successful Redis connection."""
        with patch('aioredis.ConnectionPool.from_url') as mock_pool_create, \
             patch('aioredis.Redis') as mock_redis:
            
            mock_pool = AsyncMock()
            mock_pool_create.return_value = mock_pool
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = True
            
            await cache_service_instance.connect()
            
            assert cache_service_instance.redis_pool == mock_pool
            assert cache_service_instance.redis == mock_redis_instance
            mock_redis_instance.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, cache_service_instance):
        """Test Redis connection failure handling."""
        with patch('aioredis.ConnectionPool.from_url') as mock_pool_create:
            mock_pool_create.side_effect = Exception("Connection failed")
            
            await cache_service_instance.connect()
            
            # Should handle failure gracefully
            assert cache_service_instance.redis_pool is None
            assert cache_service_instance.redis is None

    @pytest.mark.asyncio
    async def test_get_success(self, cache_service_instance, mock_redis_pool):
        """Test successful cache get operation."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        mock_redis.get.return_value = b'{"test": "value"}'
        
        result = await cache_service_instance.get("test_key")
        
        assert result == {"test": "value"}
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_not_found(self, cache_service_instance, mock_redis_pool):
        """Test cache get when key not found."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        mock_redis.get.return_value = None
        
        result = await cache_service_instance.get("missing_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_unavailable(self, cache_service_instance):
        """Test cache get when Redis is unavailable."""
        # No Redis connection
        result = await cache_service_instance.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_success(self, cache_service_instance, mock_redis_pool):
        """Test successful cache set operation."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        mock_redis.set.return_value = True
        
        result = await cache_service_instance.set("test_key", {"test": "value"}, expire=3600)
        
        assert result is True
        mock_redis.set.assert_called_once_with("test_key", '{"test": "value"}', ex=3600)

    @pytest.mark.asyncio
    async def test_set_redis_unavailable(self, cache_service_instance):
        """Test cache set when Redis is unavailable."""
        result = await cache_service_instance.set("test_key", "value")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self, cache_service_instance, mock_redis_pool):
        """Test successful cache delete operation."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        mock_redis.delete.return_value = 1
        
        result = await cache_service_instance.delete("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache_service_instance, mock_redis_pool):
        """Test get_or_set when value is cached."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        mock_redis.get.return_value = b'"cached_value"'
        
        callback = AsyncMock(return_value="new_value")
        
        result = await cache_service_instance.get_or_set("test_key", callback)
        
        assert result == "cached_value"
        callback.assert_not_called()  # Should not call callback for cache hit

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, cache_service_instance, mock_redis_pool):
        """Test get_or_set when value is not cached."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        callback = AsyncMock(return_value="new_value")
        
        result = await cache_service_instance.get_or_set("test_key", callback, expire=1800)
        
        assert result == "new_value"
        callback.assert_called_once()
        mock_redis.set.assert_called_once_with("test_key", '"new_value"', ex=1800)

    @pytest.mark.asyncio
    async def test_job_status_operations(self, cache_service_instance, mock_redis_pool):
        """Test job status tracking operations."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        # Test set job status
        mock_redis.set.return_value = True
        await cache_service_instance.set_job_status("job_123", "processing", {"step": "analysis"})
        
        expected_data = '{"status": "processing", "data": {"step": "analysis"}}'
        mock_redis.set.assert_called_with("job:job_123", expected_data, ex=3600)
        
        # Test get job status
        mock_redis.get.return_value = expected_data.encode()
        status = await cache_service_instance.get_job_status("job_123")
        
        assert status["status"] == "processing"
        assert status["data"]["step"] == "analysis"

    @pytest.mark.asyncio
    async def test_queue_stats(self, cache_service_instance, mock_redis_pool):
        """Test queue statistics retrieval."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        # Mock Redis list operations for Celery queues
        mock_redis.llen.side_effect = [5, 2]  # celery queue, priority queue
        mock_redis.keys.return_value = [b'celery-task-meta-123', b'celery-task-meta-456']
        
        stats = await cache_service_instance.get_queue_stats()
        
        expected_stats = {
            "queues": {
                "celery": 5,
                "priority": 2
            },
            "active_tasks": 2,
            "total_pending": 7
        }
        
        assert stats == expected_stats

    @pytest.mark.asyncio
    async def test_rate_limiting(self, cache_service_instance, mock_redis_pool):
        """Test rate limiting operations."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        # Mock Redis pipeline for atomic operations
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.incr.return_value = mock_pipeline
        mock_pipeline.expire.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [1, True]  # incr result, expire result
        
        # Test increment rate limit
        count = await cache_service_instance.increment_rate_limit("user_123", "api_calls", 60)
        assert count == 1
        
        # Test get rate limit
        mock_redis.get.return_value = b'5'
        current = await cache_service_instance.get_rate_limit("user_123", "api_calls")
        assert current == 5

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, cache_service_instance, mock_redis_pool):
        """Test health check when Redis is healthy."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            'redis_version': '7.0.0',
            'connected_clients': 5,
            'used_memory_human': '1.2M',
            'uptime_in_seconds': 86400
        }
        
        health = await cache_service_instance.health_check()
        
        assert health["status"] == "healthy"
        assert health["redis_info"]["version"] == "7.0.0"
        assert health["redis_info"]["clients"] == 5

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, cache_service_instance):
        """Test health check when Redis is unavailable."""
        # No Redis connection
        health = await cache_service_instance.health_check()
        
        assert health["status"] == "unhealthy"
        assert health["error"] == "Redis not connected"

    @pytest.mark.asyncio
    async def test_close_success(self, cache_service_instance):
        """Test successful connection cleanup."""
        mock_pool = AsyncMock()
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = AsyncMock()
        
        await cache_service_instance.close()
        
        mock_pool.disconnect.assert_called_once()
        assert cache_service_instance.redis_pool is None
        assert cache_service_instance.redis is None

    @pytest.mark.asyncio
    async def test_json_serialization_error(self, cache_service_instance, mock_redis_pool):
        """Test handling of JSON serialization errors."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        # Object that can't be JSON serialized
        unserializable_obj = set([1, 2, 3])
        
        result = await cache_service_instance.set("test_key", unserializable_obj)
        assert result is False

    @pytest.mark.asyncio
    async def test_json_deserialization_error(self, cache_service_instance, mock_redis_pool):
        """Test handling of JSON deserialization errors."""
        mock_pool, mock_redis = mock_redis_pool
        cache_service_instance.redis_pool = mock_pool
        cache_service_instance.redis = mock_redis
        
        # Invalid JSON
        mock_redis.get.return_value = b'invalid json{'
        
        result = await cache_service_instance.get("test_key")
        assert result is None


class TestGlobalCacheService:
    """Test the global cache_service instance."""

    @pytest.mark.asyncio
    async def test_global_instance_connect(self):
        """Test global cache service connection."""
        with patch.object(cache_service, 'connect') as mock_connect:
            await cache_service.connect()
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_global_instance_operations(self):
        """Test global cache service operations."""
        with patch.object(cache_service, 'get') as mock_get, \
             patch.object(cache_service, 'set') as mock_set:
            
            mock_get.return_value = "cached_value"
            mock_set.return_value = True
            
            # Test get
            result = await cache_service.get("test_key")
            assert result == "cached_value"
            mock_get.assert_called_once_with("test_key")
            
            # Test set
            result = await cache_service.set("test_key", "new_value")
            assert result is True
            mock_set.assert_called_once_with("test_key", "new_value", 3600)