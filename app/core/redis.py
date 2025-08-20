"""
Redis connection and session management.

This module provides Redis connection utilities for session storage,
caching, and background job coordination. Supports both development
and production Redis configurations.

Features:
- Async Redis connection management
- Session storage and retrieval
- Caching utilities
- Connection health checking
- Graceful error handling

Usage:
    from app.core.redis import get_redis, RedisService
    
    redis_client = await get_redis()
    await redis_client.set("key", "value", ex=3600)
"""

import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


async def create_redis_client() -> redis.Redis:
    """
    Create Redis client with connection pooling.
    
    Returns:
        Redis: Configured Redis client
        
    Raises:
        ConnectionError: If Redis connection fails
    """
    try:
        client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )
        
        # Test connection
        await client.ping()
        logger.info(f"Redis connection established: {settings.redis_url}")
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise ConnectionError(f"Redis connection failed: {e}")


async def get_redis() -> redis.Redis:
    """
    Get or create Redis client instance.
    
    Returns:
        Redis: Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = await create_redis_client()
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


async def check_redis_connection() -> bool:
    """
    Check if Redis connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


class RedisService:
    """Service class for Redis operations."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """Get Redis client."""
        if self.redis_client is None:
            self.redis_client = await get_redis()
        return self.redis_client
    
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized)
            expire_seconds: Optional expiration time in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value, default=str)
            
            if expire_seconds:
                result = await client.setex(key, expire_seconds, serialized_value)
            else:
                result = await client.set(key, serialized_value)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Any: Deserialized value or None if not found
        """
        try:
            client = await self.get_client()
            value = await client.get(key)
            
            if value is None:
                return None
                
            return json.loads(value)
            
        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: Redis key to delete
            
        Returns:
            bool: True if key was deleted, False otherwise
        """
        try:
            client = await self.get_client()
            result = await client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis DELETE failed for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Redis key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            client = await self.get_client()
            result = await client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis EXISTS failed for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Redis key
            seconds: Expiration time in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = await self.get_client()
            result = await client.expire(key, seconds)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis EXPIRE failed for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live for a key.
        
        Args:
            key: Redis key
            
        Returns:
            int: TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        try:
            client = await self.get_client()
            return await client.ttl(key)
            
        except Exception as e:
            logger.error(f"Redis TTL failed for key {key}: {e}")
            return -2


class SessionManager:
    """Redis-based session management."""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.session_prefix = "session:"
        self.default_expire = settings.session_expire_seconds
    
    async def create_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            user_data: User data to store in session
            
        Returns:
            bool: True if session was created successfully
        """
        session_data = {
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
        }
        
        key = f"{self.session_prefix}{session_id}"
        return await self.redis_service.set(key, session_data, self.default_expire)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict: Session data or None if not found
        """
        key = f"{self.session_prefix}{session_id}"
        session_data = await self.redis_service.get(key)
        
        if session_data:
            # Update last accessed time
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            await self.redis_service.set(key, session_data, self.default_expire)
        
        return session_data
    
    async def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            user_data: Updated user data
            
        Returns:
            bool: True if session was updated successfully
        """
        key = f"{self.session_prefix}{session_id}"
        existing_session = await self.redis_service.get(key)
        
        if not existing_session:
            return False
        
        existing_session["user_data"] = user_data
        existing_session["last_accessed"] = datetime.utcnow().isoformat()
        
        return await self.redis_service.set(key, existing_session, self.default_expire)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session was deleted successfully
        """
        key = f"{self.session_prefix}{session_id}"
        return await self.redis_service.delete(key)
    
    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if session exists
        """
        key = f"{self.session_prefix}{session_id}"
        return await self.redis_service.exists(key)


# Global services
redis_service = RedisService()
session_manager = SessionManager()