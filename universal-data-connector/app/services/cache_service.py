# """
# Caching service with Redis support for data optimization.
# """

# import json
# import logging
# from typing import Any, Optional
# import redis
# from app.config import settings

# logger = logging.getLogger(__name__)

# class CacheService:
#     """Redis-based caching service for frequently accessed data."""
    
#     def __init__(self):
#         """Initialize the cache service."""
#         self.enabled = settings.CACHE_ENABLED and settings.REDIS_ENABLED
#         self.ttl = settings.CACHE_TTL_SECONDS
#         self.client: Optional[redis.Redis] = None
        
#         if self.enabled:
#             try:
#                 self.client = redis.from_url(
#                     settings.REDIS_URL,
#                     decode_responses=True,
#                     socket_connect_timeout=5,
#                     socket_keepalive=True
#                 )
#                 # Test connection
#                 self.client.ping()
#                 logger.info("Redis cache initialized successfully")
#             except Exception as e:
#                 logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to no-cache mode.")
#                 self.enabled = False
#                 self.client = None
    
#     def get_key(self, namespace: str, identifier: str) -> str:
#         """Generate a cache key."""
#         return f"{namespace}:{identifier}"
    
#     async def get(self, namespace: str, identifier: str) -> Optional[Any]:
#         """Get a value from cache."""
#         if not self.enabled or not self.client:
#             return None
        
#         try:
#             key = self.get_key(namespace, identifier)
#             value = self.client.get(key)
#             if value:
#                 logger.debug(f"Cache hit for {key}")
#                 return json.loads(value)
#             logger.debug(f"Cache miss for {key}")
#             return None
#         except Exception as e:
#             logger.error(f"Error getting cache value: {e}")
#             return None
    
#     async def set(self, namespace: str, identifier: str, value: Any, ttl: Optional[int] = None) -> bool:
#         """Set a value in cache."""
#         if not self.enabled or not self.client:
#             return False
        
#         try:
#             key = self.get_key(namespace, identifier)
#             ttl = ttl or self.ttl
#             self.client.setex(
#                 key,
#                 ttl,
#                 json.dumps(value)
#             )
#             logger.debug(f"Cached {key} for {ttl} seconds")
#             return True
#         except Exception as e:
#             logger.error(f"Error setting cache value: {e}")
#             return False
    
#     async def delete(self, namespace: str, identifier: str) -> bool:
#         """Delete a value from cache."""
#         if not self.enabled or not self.client:
#             return False
        
#         try:
#             key = self.get_key(namespace, identifier)
#             self.client.delete(key)
#             logger.debug(f"Deleted cache key {key}")
#             return True
#         except Exception as e:
#             logger.error(f"Error deleting cache value: {e}")
#             return False
    
#     async def clear_namespace(self, namespace: str) -> bool:
#         """Clear all keys in a namespace."""
#         if not self.enabled or not self.client:
#             return False
        
#         try:
#             pattern = f"{namespace}:*"
#             keys = self.client.keys(pattern)
#             if keys:
#                 self.client.delete(*keys)
#                 logger.info(f"Cleared {len(keys)} keys in namespace {namespace}")
#             return True
#         except Exception as e:
#             logger.error(f"Error clearing namespace: {e}")
#             return False
    
#     async def flush_all(self) -> bool:
#         """Flush all cache."""
#         if not self.enabled or not self.client:
#             return False
        
#         try:
#             self.client.flushdb()
#             logger.info("Flushed all cache")
#             return True
#         except Exception as e:
#             logger.error(f"Error flushing cache: {e}")
#             return False
    
#     def is_healthy(self) -> bool:
#         """Check if cache service is healthy."""
#         if not self.enabled or not self.client:
#             return True  # Return True if disabled
        
#         try:
#             self.client.ping()
#             return True
#         except Exception as e:
#             logger.error(f"Cache health check failed: {e}")
#             return False

# # Global cache service instance
# cache_service = CacheService()


"""
Redis caching service for frequently accessed data.
"""

import json
import logging
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis package not installed. Cache service will use fallback mode.")
    REDIS_AVAILABLE = False


class CacheService:
    """Service for caching data with Redis fallback."""
    
    def __init__(self):
        """Initialize the cache service."""
        self.enabled = settings.CACHE_ENABLED or settings.REDIS_ENABLED
        # Get TTL from settings (try both naming conventions)
        self.ttl = getattr(settings, 'CACHE_TTL_SECONDS', 
                          getattr(settings, 'REDIS_TTL', 3600))
        self.redis_url = settings.REDIS_URL
        self.redis = None
        self.fallback_cache: Dict[str, Dict[str, Any]] = {}  # In-memory fallback
        
        if self.enabled and REDIS_AVAILABLE:
            try:
                self.redis = redis.from_url(self.redis_url, decode_responses=True)
                logger.info(f"Redis cache initialized with TTL={self.ttl}s")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis = None
                self.enabled = False
        elif self.enabled and not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory fallback cache")
            self.enabled = True  # Still enabled but using fallback
        else:
            logger.info("Cache service is disabled")
    
    def is_healthy(self) -> bool:
        """Check if cache service is healthy."""
        if not self.enabled:
            return True  # Disabled is considered healthy
        if self.redis:
            try:
                return self.redis.ping()
            except:
                return False
        return True  # Fallback cache is always healthy
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None
        
        # Try Redis first
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    logger.debug(f"Cache hit for key: {key}")
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error for key {key}: {e}")
        
        # Fallback to in-memory cache
        if key in self.fallback_cache:
            cache_entry = self.fallback_cache[key]
            if cache_entry["expires_at"] > datetime.now().timestamp():
                logger.debug(f"Fallback cache hit for key: {key}")
                return cache_entry["value"]
            else:
                # Expired
                del self.fallback_cache[key]
        
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self.enabled:
            return False
        
        ttl = ttl or self.ttl
        success = False
        
        # Try Redis first
        if self.redis:
            try:
                await self.redis.setex(key, ttl, json.dumps(value, default=str))
                logger.debug(f"Set Redis cache for key: {key} with TTL={ttl}s")
                success = True
            except Exception as e:
                logger.error(f"Redis set error for key {key}: {e}")
        
        # Always update fallback cache
        self.fallback_cache[key] = {
            "value": value,
            "expires_at": datetime.now().timestamp() + ttl
        }
        logger.debug(f"Set fallback cache for key: {key} with TTL={ttl}s")
        
        return success or True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled:
            return False
        
        success = False
        
        # Delete from Redis
        if self.redis:
            try:
                await self.redis.delete(key)
                logger.debug(f"Deleted Redis cache for key: {key}")
                success = True
            except Exception as e:
                logger.error(f"Redis delete error for key {key}: {e}")
        
        # Delete from fallback
        if key in self.fallback_cache:
            del self.fallback_cache[key]
            logger.debug(f"Deleted fallback cache for key: {key}")
        
        return success or True
    
    async def clear(self) -> bool:
        """Clear all cache."""
        if not self.enabled:
            return False
        
        success = False
        
        # Clear Redis
        if self.redis:
            try:
                await self.redis.flushdb()
                logger.info("Cleared Redis cache")
                success = True
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        # Clear fallback
        self.fallback_cache.clear()
        logger.info("Cleared fallback cache")
        
        return success or True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "enabled": self.enabled,
            "redis_connected": self.redis is not None,
            "fallback_cache_size": len(self.fallback_cache),
            "ttl": self.ttl
        }
        
        if self.redis:
            try:
                info = await self.redis.info()
                stats["redis"] = {
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_keys": await self.redis.dbsize()
                }
            except Exception as e:
                stats["redis_error"] = str(e)
        
        return stats


# Global cache service instance
cache_service = CacheService()