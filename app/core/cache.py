"""
Enhanced Redis caching service for performance optimization.
Provides caching for expensive operations, job status tracking, and analytics.
"""
import json
import hashlib
import asyncio
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class CacheService:
    """Enhanced Redis caching service with job monitoring and analytics."""
    
    def __init__(self):
        self.redis_client = None
        self._connection_pool = None
    
    async def connect(self):
        """Initialize Redis connection with connection pooling."""
        try:
            self.redis_client = redis.Redis.from_url(
                settings.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache service connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis cache: {e}")
            raise
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        
        # Hash long keys to prevent Redis key size issues
        if len(key_data) > 200:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_data
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with error handling."""
        try:
            if not self.redis_client:
                await self.connect()
            
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        try:
            if not self.redis_client:
                await self.connect()
            
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, expire, serialized_value)
            return True
            
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if not self.redis_client:
                await self.connect()
            
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False
    
    async def get_or_set(self, key: str, callback: Callable, expire: int = 3600) -> Any:
        """Get from cache or execute callback and cache result."""
        # Try to get from cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_value
        
        # Execute callback and cache result
        logger.debug(f"Cache miss for key: {key}, executing callback")
        try:
            if asyncio.iscoroutinefunction(callback):
                value = await callback()
            else:
                value = callback()
            
            await self.set(key, value, expire)
            return value
            
        except Exception as e:
            logger.error(f"Callback execution failed for key {key}: {e}")
            raise
    
    # Job Status Management
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get background job status."""
        key = f"job_status:{job_id}"
        return await self.get(key)
    
    async def set_job_status(self, job_id: str, status: Dict[str, Any], expire: int = 7200) -> bool:
        """Set background job status with longer TTL."""
        key = f"job_status:{job_id}"
        status["updated_at"] = datetime.utcnow().isoformat()
        return await self.set(key, status, expire)
    
    async def update_job_progress(self, job_id: str, progress: int, message: str = None) -> bool:
        """Update job progress percentage."""
        current_status = await self.get_job_status(job_id) or {}
        current_status.update({
            "progress": progress,
            "message": message,
            "updated_at": datetime.utcnow().isoformat()
        })
        return await self.set_job_status(job_id, current_status)
    
    # Queue Monitoring
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics."""
        try:
            if not self.redis_client:
                await self.connect()
            
            # Get Celery queue lengths
            default_queue = await self.redis_client.llen("celery") or 0
            analysis_queue = await self.redis_client.llen("analysis") or 0
            images_queue = await self.redis_client.llen("images") or 0
            
            # Get worker stats from Redis (if available)
            active_jobs = len(await self.redis_client.keys("job_status:*"))
            
            # Get Redis memory usage
            memory_info = await self.redis_client.info("memory")
            memory_used = memory_info.get("used_memory_human", "Unknown")
            
            return {
                "queues": {
                    "default": default_queue,
                    "analysis": analysis_queue,
                    "images": images_queue,
                    "total": default_queue + analysis_queue + images_queue
                },
                "active_jobs": active_jobs,
                "redis_connected": True,
                "memory_usage": memory_used,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {
                "queues": {"default": 0, "analysis": 0, "images": 0, "total": 0},
                "active_jobs": 0,
                "redis_connected": False,
                "memory_usage": "Unknown",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Analysis Caching
    async def cache_analysis_result(self, analysis_id: int, result: Dict[str, Any], expire: int = 86400) -> bool:
        """Cache analysis result for fast retrieval."""
        key = f"analysis_result:{analysis_id}"
        return await self.set(key, result, expire)
    
    async def get_cached_analysis(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Get cached analysis result."""
        key = f"analysis_result:{analysis_id}"
        return await self.get(key)
    
    async def invalidate_analysis_cache(self, analysis_id: int) -> bool:
        """Remove analysis from cache."""
        key = f"analysis_result:{analysis_id}"
        return await self.delete(key)
    
    # User Analytics Caching
    async def cache_user_analytics(self, user_id: int, analytics: Dict[str, Any], expire: int = 3600) -> bool:
        """Cache user analytics data."""
        key = f"user_analytics:{user_id}"
        return await self.set(key, analytics, expire)
    
    async def get_user_analytics(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user analytics."""
        key = f"user_analytics:{user_id}"
        return await self.get(key)
    
    # Conversation Caching
    async def cache_conversation_context(self, conversation_id: int, context: List[Dict], expire: int = 1800) -> bool:
        """Cache conversation context for AI responses."""
        key = f"conversation_context:{conversation_id}"
        return await self.set(key, context, expire)
    
    async def get_conversation_context(self, conversation_id: int) -> Optional[List[Dict]]:
        """Get cached conversation context."""
        key = f"conversation_context:{conversation_id}"
        return await self.get(key)
    
    # Rate Limiting Support
    async def increment_rate_limit(self, identifier: str, window: int = 3600) -> int:
        """Increment rate limit counter for identifier."""
        try:
            if not self.redis_client:
                await self.connect()
            
            key = f"rate_limit:{identifier}"
            current_count = await self.redis_client.incr(key)
            
            if current_count == 1:
                await self.redis_client.expire(key, window)
            
            return current_count
            
        except Exception as e:
            logger.warning(f"Rate limit increment failed for {identifier}: {e}")
            return 0
    
    async def get_rate_limit(self, identifier: str) -> int:
        """Get current rate limit count."""
        try:
            if not self.redis_client:
                await self.connect()
            
            key = f"rate_limit:{identifier}"
            count = await self.redis_client.get(key)
            return int(count) if count else 0
            
        except Exception as e:
            logger.warning(f"Rate limit get failed for {identifier}: {e}")
            return 0
    
    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check."""
        try:
            if not self.redis_client:
                await self.connect()
            
            # Test basic operations
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.utcnow().isoformat()}
            
            # Test set and get
            await self.redis_client.setex(test_key, 10, json.dumps(test_value))
            retrieved = await self.redis_client.get(test_key)
            
            if not retrieved:
                raise Exception("Failed to retrieve test value")
            
            # Clean up
            await self.redis_client.delete(test_key)
            
            # Get Redis info
            info = await self.redis_client.info()
            
            return {
                "status": "healthy",
                "connected": True,
                "redis_version": info.get("redis_version", "unknown"),
                "total_connections": info.get("total_connections_received", 0),
                "memory_usage": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }

# Global cache service instance
cache_service = CacheService()

# Convenience functions for common operations
async def get_cached(key: str) -> Optional[Any]:
    """Get value from cache."""
    return await cache_service.get(key)

async def set_cached(key: str, value: Any, expire: int = 3600) -> bool:
    """Set value in cache."""
    return await cache_service.set(key, value, expire)

async def delete_cached(key: str) -> bool:
    """Delete value from cache."""
    return await cache_service.delete(key)

async def get_or_cache(key: str, callback: Callable, expire: int = 3600) -> Any:
    """Get from cache or execute callback and cache result."""
    return await cache_service.get_or_set(key, callback, expire)