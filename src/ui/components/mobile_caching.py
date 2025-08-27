"""
Mobile Caching Utilities

Optimized caching strategies for mobile devices.
"""

import hashlib
import logging
import pickle
import time
from functools import wraps
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class MobileCacheManager:
    """Cache manager optimized for mobile devices."""

    def __init__(self):
        self._cache: dict[str, tuple[Any, float, float]] = {}  # value, timestamp, ttl
        self._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._max_cache_size = 50  # Reduced for mobile
        self._default_ttl = 300  # 5 minutes

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if key not in self._cache:
            self._cache_stats["misses"] += 1
            return None

        value, timestamp, ttl = self._cache[key]

        # Check if expired
        if time.time() - timestamp > ttl:
            del self._cache[key]
            self._cache_stats["misses"] += 1
            return None

        self._cache_stats["hits"] += 1
        return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Set value in cache."""
        if ttl is None:
            ttl = self._default_ttl

        # Evict if cache is full
        if len(self._cache) >= self._max_cache_size:
            self._evict_oldest()

        self._cache[key] = (value, time.time(), ttl)

    def _evict_oldest(self) -> None:
        """Evict oldest cache entry."""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]
        self._cache_stats["evictions"] += 1

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / max(total_requests, 1)) * 100

        return {
            **self._cache_stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
            "max_cache_size": self._max_cache_size,
        }

    def generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = pickle.dumps((args, sorted(kwargs.items())))
        return hashlib.md5(key_data).hexdigest()


# Global cache manager
mobile_cache_manager = MobileCacheManager()


# Caching decorators
def mobile_cache(ttl: float = 300, key_func: callable | None = None):
    """Decorator for caching function results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{mobile_cache_manager.generate_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = mobile_cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            mobile_cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def streamlit_cache_optimized(func):
    """Optimized Streamlit caching for mobile."""

    @st.cache_data(ttl=300, max_entries=20)  # Reduced for mobile
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def cache_component_state(component_id: str, ttl: float = 600):
    """Cache component state."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"component_state_{component_id}"

            # Try to get from cache
            cached_state = mobile_cache_manager.get(cache_key)
            if cached_state is not None:
                return cached_state

            # Generate state and cache
            state = func(*args, **kwargs)
            mobile_cache_manager.set(cache_key, state, ttl)

            return state

        return wrapper

    return decorator


# Mobile-specific caching utilities
class MobileResourceCache:
    """Cache for mobile resources like images and data."""

    def __init__(self):
        self._resource_cache: dict[str, bytes] = {}
        self._max_resource_size = 5 * 1024 * 1024  # 5MB total
        self._current_size = 0

    def cache_image(self, image_key: str, image_data: bytes) -> bool:
        """Cache image data."""
        image_size = len(image_data)

        # Check if image is too large
        if image_size > self._max_resource_size // 2:
            return False

        # Evict if needed
        while self._current_size + image_size > self._max_resource_size:
            if not self._evict_largest_resource():
                break

        self._resource_cache[image_key] = image_data
        self._current_size += image_size
        return True

    def get_image(self, image_key: str) -> bytes | None:
        """Get cached image data."""
        return self._resource_cache.get(image_key)

    def _evict_largest_resource(self) -> bool:
        """Evict largest cached resource."""
        if not self._resource_cache:
            return False

        largest_key = max(self._resource_cache.keys(), key=lambda k: len(self._resource_cache[k]))

        evicted_size = len(self._resource_cache[largest_key])
        del self._resource_cache[largest_key]
        self._current_size -= evicted_size

        return True

    def clear(self) -> None:
        """Clear resource cache."""
        self._resource_cache.clear()
        self._current_size = 0


# Global resource cache
mobile_resource_cache = MobileResourceCache()
