"""Caching utilities to avoid redundant API calls."""

import asyncio
import logging
import time
from typing import Any, Optional, Dict, Callable, Awaitable
from functools import wraps


class AsyncCache:
    """Thread-safe async cache with TTL support."""

    def __init__(self, default_ttl: int = 300):
        """Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        cache_entry = self._cache[key]
        current_time = time.time()

        if current_time > cache_entry["expires_at"]:
            # Entry has expired, remove it
            del self._cache[key]
            if key in self._locks:
                del self._locks[key]
            return None

        self.logger.debug("Cache hit for key: %s", key)
        return cache_entry["value"]

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl

        expires_at = time.time() + ttl
        self._cache[key] = {"value": value, "expires_at": expires_at, "created_at": time.time()}
        self.logger.debug("Cached value for key: %s (TTL: %d seconds)", key, ttl)

    async def get_or_set(self, key: str, factory: Callable[[], Awaitable[Any]], ttl: Optional[int] = None) -> Any:
        """Get from cache or set using factory function.

        Args:
            key: Cache key
            factory: Async function to generate value if not cached
            ttl: Time-to-live in seconds

        Returns:
            Cached or newly generated value
        """
        # Check cache first
        value = await self.get(key)
        if value is not None:
            return value

        # Use per-key lock to prevent multiple concurrent requests for same key
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            # Double-check cache in case another coroutine already populated it
            value = await self.get(key)
            if value is not None:
                return value

            # Generate new value
            self.logger.debug("Cache miss for key: %s, generating new value", key)
            value = await factory()
            await self.set(key, value, ttl)
            return value

    async def invalidate(self, key: str) -> bool:
        """Invalidate cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was found and removed
        """
        if key in self._cache:
            del self._cache[key]
            if key in self._locks:
                del self._locks[key]
            self.logger.debug("Invalidated cache key: %s", key)
            return True
        return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._locks.clear()
        self.logger.debug("Cleared all cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        active_entries = 0
        expired_entries = 0

        for cache_entry in self._cache.values():
            if current_time > cache_entry["expires_at"]:
                expired_entries += 1
            else:
                active_entries += 1

        return {
            "total_entries": len(self._cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "default_ttl": self.default_ttl,
        }


def cache_result(cache: AsyncCache, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Decorator to cache async function results.

    Args:
        cache: AsyncCache instance
        ttl: Time-to-live for cached results
        key_func: Function to generate cache key from function args

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation from function name and args
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

            # Try to get from cache or execute function
            return await cache.get_or_set(cache_key, lambda: func(*args, **kwargs), ttl)

        return wrapper

    return decorator


# Global cache instance
global_cache = AsyncCache(default_ttl=300)  # 5 minutes default TTL
