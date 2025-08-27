"""
Mobile Performance Optimizer

Provides performance optimization utilities for mobile PlantGuard interface.
Includes lazy loading, caching, memory management, and bundle optimization.
"""

import gc
import hashlib
import json
import logging
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors and tracks performance metrics."""

    def __init__(self):
        self.metrics: dict[str, list[float]] = {}
        self.start_times: dict[str, float] = {}

    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.start_times[operation] = time.time()

    def end_timer(self, operation: str) -> float:
        """End timing an operation and record the duration."""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]

            if operation not in self.metrics:
                self.metrics[operation] = []

            self.metrics[operation].append(duration)
            del self.start_times[operation]

            return duration
        return 0.0

    def get_average_time(self, operation: str) -> float:
        """Get average time for an operation."""
        if self.metrics.get(operation):
            return sum(self.metrics[operation]) / len(self.metrics[operation])
        return 0.0

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of all performance metrics."""
        summary = {}

        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    "count": len(times),
                    "average": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "total": sum(times),
                }

        return summary


class LazyLoader:
    """Implements lazy loading for components and resources."""

    def __init__(self):
        self.loaded_components: dict[str, Any] = {}
        self.loading_states: dict[str, bool] = {}

    def lazy_load_component(self, component_id: str, loader_func: Callable) -> Any:
        """Lazy load a component."""
        if component_id not in self.loaded_components:
            if component_id not in self.loading_states:
                self.loading_states[component_id] = True

                try:
                    component = loader_func()
                    self.loaded_components[component_id] = component
                    logger.info(f"Lazy loaded component: {component_id}")
                except Exception as e:
                    logger.error(f"Failed to lazy load component {component_id}: {e}")
                    return None
                finally:
                    self.loading_states[component_id] = False

        return self.loaded_components.get(component_id)

    def is_loading(self, component_id: str) -> bool:
        """Check if component is currently loading."""
        return self.loading_states.get(component_id, False)

    def unload_component(self, component_id: str) -> None:
        """Unload a component to free memory."""
        if component_id in self.loaded_components:
            del self.loaded_components[component_id]
            logger.info(f"Unloaded component: {component_id}")

    def get_loaded_components(self) -> list[str]:
        """Get list of currently loaded components."""
        return list(self.loaded_components.keys())


class CacheManager:
    """Manages caching for mobile application."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path.cwd() / ".mobile_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache: dict[str, Any] = {}
        self.cache_metadata: dict[str, dict[str, Any]] = {}

    def _generate_cache_key(self, key: str, params: dict[str, Any] | None = None) -> str:
        """Generate a unique cache key."""
        if params:
            params_str = json.dumps(params, sort_keys=True)
            key_with_params = f"{key}_{params_str}"
        else:
            key_with_params = key

        return hashlib.sha256(key_with_params.encode()).hexdigest()

    def get_from_cache(self, key: str, params: dict[str, Any] | None = None) -> Any | None:
        """Get item from cache."""
        cache_key = self._generate_cache_key(key, params)

        # Check memory cache first
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]

        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)

                # Check if cache is still valid
                if self._is_cache_valid(cache_key):
                    self.memory_cache[cache_key] = data
                    return data
                else:
                    cache_file.unlink()  # Remove expired cache
            except Exception as e:
                logger.warning(f"Failed to load cache {cache_key}: {e}")

        return None

    def set_cache(self, key: str, value: Any, params: dict[str, Any] | None = None, ttl: int = 3600) -> None:
        """Set item in cache."""
        cache_key = self._generate_cache_key(key, params)

        # Store in memory cache
        self.memory_cache[cache_key] = value

        # Store metadata
        self.cache_metadata[cache_key] = {"created_at": time.time(), "ttl": ttl, "key": key, "params": params}

        # Store in disk cache
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, "w") as f:
                json.dump(value, f, default=str)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_key}: {e}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self.cache_metadata:
            return False

        metadata = self.cache_metadata[cache_key]
        age = time.time() - metadata["created_at"]

        return age < metadata["ttl"]

    def clear_cache(self, key_pattern: str | None = None) -> None:
        """Clear cache entries."""
        if key_pattern:
            # Clear specific pattern
            keys_to_remove = [k for k in self.memory_cache if key_pattern in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
                if key in self.cache_metadata:
                    del self.cache_metadata[key]
        else:
            # Clear all cache
            self.memory_cache.clear()
            self.cache_metadata.clear()

        # Clear disk cache
        if key_pattern:
            for cache_file in self.cache_dir.glob(f"*{key_pattern}*.json"):
                cache_file.unlink()
        else:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "memory_cache_size": len(self.memory_cache),
            "disk_cache_files": len(list(self.cache_dir.glob("*.json"))),
            "cache_directory": str(self.cache_dir),
            "total_metadata_entries": len(self.cache_metadata),
        }


class MemoryManager:
    """Manages memory usage for mobile application."""

    def __init__(self):
        self.memory_threshold = 100 * 1024 * 1024  # 100MB threshold
        self.cleanup_callbacks: list[Callable] = []

    def register_cleanup_callback(self, callback: Callable) -> None:
        """Register a cleanup callback."""
        self.cleanup_callbacks.append(callback)

    def get_memory_usage(self) -> dict[str, Any]:
        """Get current memory usage."""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
                "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            }
        except ImportError:
            return {"error": "psutil not available"}

    def check_memory_pressure(self) -> bool:
        """Check if memory usage is high."""
        memory_info = self.get_memory_usage()

        if "rss_mb" in memory_info:
            return memory_info["rss_mb"] * 1024 * 1024 > self.memory_threshold

        return False

    def cleanup_memory(self) -> None:
        """Perform memory cleanup."""
        logger.info("Performing memory cleanup")

        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"Cleanup callback failed: {e}")

        # Force garbage collection
        gc.collect()

        logger.info("Memory cleanup completed")

    def auto_cleanup_if_needed(self) -> None:
        """Automatically cleanup if memory pressure is high."""
        if self.check_memory_pressure():
            self.cleanup_memory()


class BundleOptimizer:
    """Optimizes resource bundles for mobile."""

    def __init__(self):
        self.css_cache: dict[str, str] = {}
        self.js_cache: dict[str, str] = {}

    def minify_css(self, css_content: str) -> str:
        """Minify CSS content."""
        if css_content in self.css_cache:
            return self.css_cache[css_content]

        # Simple CSS minification
        minified = css_content

        # Remove comments
        import re

        minified = re.sub(r"/\*.*?\*/", "", minified, flags=re.DOTALL)

        # Remove extra whitespace
        minified = re.sub(r"\s+", " ", minified)
        minified = re.sub(r";\s*}", "}", minified)
        minified = re.sub(r"{\s*", "{", minified)
        minified = re.sub(r"}\s*", "}", minified)
        minified = re.sub(r":\s*", ":", minified)
        minified = re.sub(r";\s*", ";", minified)

        # Cache result
        self.css_cache[css_content] = minified

        return minified

    def optimize_images(self, image_data: bytes, max_width: int = 800) -> bytes:
        """Optimize images for mobile."""
        try:
            import io

            from PIL import Image

            # Load image
            image = Image.open(io.BytesIO(image_data))

            # Resize if too large
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Convert to RGB if necessary
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Save optimized image
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)

            return output.getvalue()

        except ImportError:
            logger.warning("PIL not available for image optimization")
            return image_data
        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")
            return image_data

    def create_critical_css(self, full_css: str) -> str:
        """Extract critical CSS for above-the-fold content."""
        # Simple critical CSS extraction
        critical_selectors = [".mobile-", ".stButton", ".stMarkdown", ".main", "body", "html"]

        lines = full_css.split("\n")
        critical_lines = []

        for line in lines:
            if any(selector in line for selector in critical_selectors):
                critical_lines.append(line)

        return "\n".join(critical_lines)


def performance_timer(operation_name: str):
    """Decorator to time function execution."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            monitor.start_timer(operation_name)

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = monitor.end_timer(operation_name)
                logger.debug(f"{operation_name} took {duration:.3f}s")

        return wrapper

    return decorator


def cached_component(cache_key: str, ttl: int = 3600):
    """Decorator to cache component results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            # Generate cache key with function arguments
            params = {"args": str(args), "kwargs": str(kwargs)}
            cached_result = cache_manager.get_from_cache(cache_key, params)

            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set_cache(cache_key, result, params, ttl)

            return result

        return wrapper

    return decorator


def memory_efficient(cleanup_after: bool = True):
    """Decorator to ensure memory efficient execution."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            memory_manager = get_memory_manager()

            # Check memory before execution
            memory_manager.auto_cleanup_if_needed()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                if cleanup_after:
                    # Cleanup after execution
                    gc.collect()

        return wrapper

    return decorator


# Global instances
_performance_monitor = None
_cache_manager = None
_memory_manager = None
_lazy_loader = None
_bundle_optimizer = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_memory_manager() -> MemoryManager:
    """Get global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def get_lazy_loader() -> LazyLoader:
    """Get global lazy loader instance."""
    global _lazy_loader
    if _lazy_loader is None:
        _lazy_loader = LazyLoader()
    return _lazy_loader


def get_bundle_optimizer() -> BundleOptimizer:
    """Get global bundle optimizer instance."""
    global _bundle_optimizer
    if _bundle_optimizer is None:
        _bundle_optimizer = BundleOptimizer()
    return _bundle_optimizer


def optimize_mobile_performance() -> dict[str, Any]:
    """Run comprehensive mobile performance optimization."""
    logger.info("Running mobile performance optimization")

    results = {}

    # Memory cleanup
    memory_manager = get_memory_manager()
    memory_before = memory_manager.get_memory_usage()
    memory_manager.cleanup_memory()
    memory_after = memory_manager.get_memory_usage()

    results["memory_optimization"] = {
        "before_mb": memory_before.get("rss_mb", 0),
        "after_mb": memory_after.get("rss_mb", 0),
        "saved_mb": memory_before.get("rss_mb", 0) - memory_after.get("rss_mb", 0),
    }

    # Cache optimization
    cache_manager = get_cache_manager()
    cache_stats = cache_manager.get_cache_stats()
    results["cache_stats"] = cache_stats

    # Performance metrics
    performance_monitor = get_performance_monitor()
    performance_stats = performance_monitor.get_metrics_summary()
    results["performance_metrics"] = performance_stats

    # Lazy loading stats
    lazy_loader = get_lazy_loader()
    loaded_components = lazy_loader.get_loaded_components()
    results["lazy_loading"] = {"loaded_components": len(loaded_components), "component_list": loaded_components}

    logger.info("Mobile performance optimization completed")
    return results
