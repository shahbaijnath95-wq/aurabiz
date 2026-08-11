"""
Cache Service — Redis-backed caching with decorator pattern.
Gracefully degrades when Redis is unavailable.
"""

import json
import hashlib
from functools import wraps
from typing import Optional, Any, Callable
from loguru import logger

from database import redis_client


class CacheService:
    """Simple Redis cache with TTL and key prefixing."""

    def __init__(self, prefix: str = "cache"):
        self.prefix = prefix
        self.default_ttl = 300  # 5 minutes

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not redis_client:
            return None
        try:
            data = await redis_client.get(self._key(key))
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug("Cache get error: {}", e)
        return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with TTL."""
        if not redis_client:
            return False
        try:
            ttl = ttl or self.default_ttl
            data = json.dumps(value, default=str)
            await redis_client.setex(self._key(key), ttl, data)
            return True
        except Exception as e:
            logger.debug("Cache set error: {}", e)
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not redis_client:
            return False
        try:
            await redis_client.delete(self._key(key))
            return True
        except Exception as e:
            logger.debug("Cache delete error: {}", e)
            return False

    async def clear_prefix(self, prefix: str = None) -> int:
        """Clear all keys with given prefix."""
        if not redis_client:
            return 0
        try:
            p = f"{self.prefix}:{prefix}" if prefix else self.prefix
            keys = []
            async for key in redis_client.scan_iter(f"{p}:*"):
                keys.append(key)
            if keys:
                return await redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug("Cache clear error: {}", e)
            return 0

    async def incr(self, key: str, ttl: int = None) -> Optional[int]:
        """Increment counter."""
        if not redis_client:
            return None
        try:
            full_key = self._key(key)
            val = await redis_client.incr(full_key)
            if ttl and val == 1:
                await redis_client.expire(full_key, ttl)
            return val
        except Exception as e:
            logger.debug("Cache incr error: {}", e)
            return None


def cached(prefix: str = "cache", ttl: int = 300, key_builder: Callable = None):
    """
    Decorator for caching async function results.

    Usage:
        @cached(prefix="analytics", ttl=60)
        async def get_stats(business_id: str):
            ...
    """
    cache = CacheService(prefix=prefix)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Auto-generate key from function name + args
                key_parts = [func.__name__]
                for arg in args:
                    if isinstance(arg, (str, int, float)):
                        key_parts.append(str(arg))
                for k, v in sorted(kwargs.items()):
                    if isinstance(v, (str, int, float)):
                        key_parts.append(f"{k}={v}")
                cache_key = ":".join(key_parts)

            # Try cache first
            result = await cache.get(cache_key)
            if result is not None:
                return result

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            if result is not None:
                await cache.set(cache_key, result, ttl=ttl)

            return result

        wrapper.cache = cache
        return wrapper

    return decorator
