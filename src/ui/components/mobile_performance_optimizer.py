"""
Mobile Performance Optimizer for PlantGuard UI.

This module provides performance optimizations specifically designed for mobile devices,
including lazy loading, resource caching, bundle optimization, and memory management.

Requirements addressed:
- 6.1: Performance and offline capability
- 6.4: Performance optimization
- 6.5: Memory management for mobile constraints
"""

import gc
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Any
from weakref import WeakValueDictionary

import streamlit as st

logger = logging.getLogger(__name__)


class ComponentRenderOptimizer:
    """Context manager for optimized component rendering."""

    def __init__(self, performance_optimizer, component_id: str):
        """Initialize the context manager."""
        self.performance_optimizer = performance_optimizer
        self.component_id = component_id
        self.start_time = None

    def __enter__(self):
        """Enter the context manager."""
        self.start_time = time.time()

        # Check if optimization is enabled
        if not self.performance_optimizer._optimization_enabled:
            return self

        # Check memory pressure
        try:
            memory_pressure = self.performance_optimizer.memory_manager.check_memory_pressure()
            if memory_pressure == "critical":
                self.performance_optimizer.memory_manager.cleanup_memory(force=True)
        except Exception as e:
            logger.warning(f"Memory pressure check failed: {e}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        if self.start_time:
            render_time = time.time() - self.start_time
            logger.debug(f"Component {self.component_id} rendered in {render_time:.3f}s")

        # Handle any exceptions gracefully
        if exc_type:
            logger.warning(f"Component {self.component_id} rendering failed: {exc_val}")

        return False  # Don't suppress exceptions


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""

    component_id: str
    render_time: float
    memory_usage: int
    cache_hits: int
    cache_misses: int
    lazy_loads: int
    timestamp: str


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size_bytes: int
    expires_at: datetime | None = None


class MobileResourceCache:
    """Resource caching system optimized for mobile devices."""

    def __init__(self, max_size_mb: int = 50, max_entries: int = 1000):
        """
        Initialize mobile resource cache.

        Args:
            max_size_mb: Maximum cache size in megabytes
            max_entries: Maximum number of cache entries
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self._cache: dict[str, CacheEntry] = {}
        self._current_size = 0
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Get item from cache."""
        if key in self._cache:
            entry = self._cache[key]

            # Check expiration
            if entry.expires_at and datetime.now() > entry.expires_at:
                self.remove(key)
                self._misses += 1
                return None

            # Update access info
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            self._hits += 1

            return entry.value

        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        """Set item in cache."""
        try:
            # Calculate size estimate
            size_estimate = len(str(value))

            # Check if we need to make space
            if self._current_size + size_estimate > self.max_size_bytes or len(self._cache) >= self.max_entries:
                self._evict_lru()

            # Create cache entry
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                size_bytes=size_estimate,
                expires_at=expires_at,
            )

            # Remove existing entry if present
            if key in self._cache:
                self.remove(key)

            # Add new entry
            self._cache[key] = entry
            self._current_size += size_estimate

            return True

        except Exception as e:
            logger.warning(f"Failed to cache item {key}: {e}")
            return False

    def remove(self, key: str) -> bool:
        """Remove item from cache."""
        if key in self._cache:
            entry = self._cache[key]
            self._current_size -= entry.size_bytes
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._current_size = 0
        self._hits = 0
        self._misses = 0

    def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        if not self._cache:
            return

        # Sort by last accessed time
        sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].last_accessed)

        # Remove oldest 25% of entries
        entries_to_remove = max(1, len(sorted_entries) // 4)

        for i in range(entries_to_remove):
            key, _ = sorted_entries[i]
            self.remove(key)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "entries": len(self._cache),
            "size_mb": self._current_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "utilization": (len(self._cache) / self.max_entries * 100),
        }


class LazyLoader:
    """Lazy loading system for mobile components and resources."""

    def __init__(self):
        """Initialize lazy loader."""
        self._loaded_components: WeakValueDictionary = WeakValueDictionary()
        self._loading_queue: list[str] = []
        self._load_callbacks: dict[str, Callable] = {}

    def register_component(self, component_id: str, load_callback: Callable) -> None:
        """Register a component for lazy loading."""
        self._load_callbacks[component_id] = load_callback
        logger.debug(f"Registered component for lazy loading: {component_id}")

    def load_component(self, component_id: str) -> Any:
        """Load component on demand."""
        # Check if already loaded
        if component_id in self._loaded_components:
            return self._loaded_components[component_id]

        # Check if callback exists
        if component_id not in self._load_callbacks:
            logger.warning(f"No load callback registered for component: {component_id}")
            return None

        try:
            # Load component
            start_time = time.time()
            component = self._load_callbacks[component_id]()
            load_time = time.time() - start_time

            # Store in weak reference dictionary
            self._loaded_components[component_id] = component

            logger.debug(f"Lazy loaded component {component_id} in {load_time:.3f}s")
            return component

        except Exception as e:
            logger.error(f"Failed to lazy load component {component_id}: {e}")
            return None

    def preload_components(self, component_ids: list[str]) -> None:
        """Preload components in background."""
        for component_id in component_ids:
            if component_id not in self._loaded_components:
                self._loading_queue.append(component_id)

    def process_loading_queue(self, max_items: int = 3) -> None:
        """Process loading queue with throttling."""
        processed = 0
        while self._loading_queue and processed < max_items:
            component_id = self._loading_queue.pop(0)
            self.load_component(component_id)
            processed += 1

    def get_loaded_components(self) -> list[str]:
        """Get list of currently loaded components."""
        return list(self._loaded_components.keys())

    def unload_component(self, component_id: str) -> bool:
        """Unload component to free memory."""
        if component_id in self._loaded_components:
            del self._loaded_components[component_id]
            return True
        return False


class MemoryManager:
    """Memory management system for mobile constraints."""

    def __init__(self, warning_threshold_mb: int = 100, critical_threshold_mb: int = 150):
        """
        Initialize memory manager.

        Args:
            warning_threshold_mb: Memory usage warning threshold
            critical_threshold_mb: Memory usage critical threshold
        """
        self.warning_threshold = warning_threshold_mb * 1024 * 1024
        self.critical_threshold = critical_threshold_mb * 1024 * 1024
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=5)

    def get_memory_usage(self) -> dict[str, Any]:
        """Get current memory usage statistics."""
        import os

        import psutil

        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024),
                "percent": process.memory_percent(),
                "available_mb": psutil.virtual_memory().available / (1024 * 1024),
            }
        except ImportError:
            # Fallback if psutil not available
            return {
                "rss_mb": 0,
                "vms_mb": 0,
                "percent": 0,
                "available_mb": 1000,  # Assume 1GB available
            }

    def check_memory_pressure(self) -> str:
        """Check current memory pressure level."""
        memory_info = self.get_memory_usage()
        rss_bytes = memory_info["rss_mb"] * 1024 * 1024

        if rss_bytes > self.critical_threshold:
            return "critical"
        elif rss_bytes > self.warning_threshold:
            return "warning"
        else:
            return "normal"

    def cleanup_memory(self, force: bool = False) -> dict[str, Any]:
        """Perform memory cleanup operations."""
        now = datetime.now()

        if not force and (now - self._last_cleanup) < self._cleanup_interval:
            return {"skipped": True, "reason": "too_recent"}

        cleanup_stats = {"before_mb": self.get_memory_usage()["rss_mb"], "actions_taken": []}

        try:
            # Clear Streamlit cache
            if hasattr(st, "cache_data") and hasattr(st.cache_data, "clear"):
                st.cache_data.clear()
                cleanup_stats["actions_taken"].append("streamlit_cache_cleared")

            # Force garbage collection
            collected = gc.collect()
            cleanup_stats["actions_taken"].append(f"gc_collected_{collected}")

            # Clear session state of old data
            self._cleanup_session_state()
            cleanup_stats["actions_taken"].append("session_state_cleaned")

            self._last_cleanup = now
            cleanup_stats["after_mb"] = self.get_memory_usage()["rss_mb"]
            cleanup_stats["freed_mb"] = cleanup_stats["before_mb"] - cleanup_stats["after_mb"]

            logger.info(f"Memory cleanup completed: freed {cleanup_stats['freed_mb']:.1f}MB")

        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            cleanup_stats["error"] = str(e)

        return cleanup_stats

    def _cleanup_session_state(self) -> None:
        """Clean up old session state data."""
        cutoff_time = datetime.now() - timedelta(hours=1)
        keys_to_remove = []

        for key in st.session_state:
            if isinstance(key, str) and key.startswith("mobile_"):
                # Check if this is a timestamped entry
                state_data = st.session_state.get(key)
                if isinstance(state_data, dict):
                    created_at_str = state_data.get("created_at")
                    if created_at_str:
                        with suppress(ValueError, TypeError):
                            created_at = datetime.fromisoformat(created_at_str)
                            if created_at < cutoff_time:
                                keys_to_remove.append(key)

        # Remove old entries
        for key in keys_to_remove:
            del st.session_state[key]

        logger.debug(f"Cleaned up {len(keys_to_remove)} old session state entries")


class MobilePerformanceOptimizer:
    """Main performance optimization system for mobile devices."""

    def __init__(self):
        """Initialize mobile performance optimizer."""
        self.cache = MobileResourceCache()
        self.lazy_loader = LazyLoader()
        self.memory_manager = MemoryManager()
        self._metrics: list[PerformanceMetrics] = []
        self._optimization_enabled = True

        # Initialize session state for performance tracking
        self._initialize_performance_state()

    def _initialize_performance_state(self) -> None:
        """Initialize performance tracking in session state."""
        if "mobile_performance" not in st.session_state:
            st.session_state.mobile_performance = {
                "initialized_at": datetime.now().isoformat(),
                "total_renders": 0,
                "total_render_time": 0.0,
                "cache_enabled": True,
                "lazy_loading_enabled": True,
                "memory_management_enabled": True,
                "optimization_level": "auto",
            }

    def optimize_component_render(self, component_id: str):
        """
        Context manager to optimize component rendering.

        Args:
            component_id: Component identifier

        Returns:
            Context manager for optimized rendering
        """
        return ComponentRenderOptimizer(self, component_id)

    def optimize_component_render_decorator(self, component_id: str) -> Callable:
        """
        Decorator to optimize component rendering.

        Args:
            component_id: Component identifier

        Returns:
            Decorator function
        """

        def decorator(render_func: Callable) -> Callable:
            @wraps(render_func)
            def wrapper(*args, **kwargs):
                if not self._optimization_enabled:
                    return render_func(*args, **kwargs)

                start_time = time.time()

                try:
                    # Check cache first
                    cache_key = f"render_{component_id}_{hash(str(kwargs))}"
                    cached_result = self.cache.get(cache_key)

                    if cached_result is not None:
                        logger.debug(f"Cache hit for component {component_id}")
                        return cached_result

                    # Check memory pressure
                    memory_pressure = self.memory_manager.check_memory_pressure()
                    if memory_pressure == "critical":
                        self.memory_manager.cleanup_memory(force=True)

                    # Render component
                    result = render_func(*args, **kwargs)

                    # Cache result if appropriate
                    if self._should_cache_result(component_id, result):
                        self.cache.set(cache_key, result, ttl_seconds=300)  # 5 minute TTL

                    # Record metrics
                    render_time = time.time() - start_time
                    self._record_performance_metrics(component_id, render_time)

                    return result

                except Exception as e:
                    logger.error(f"Optimized render failed for {component_id}: {e}")
                    # Fallback to direct render
                    return render_func(*args, **kwargs)

            return wrapper

        return decorator

    def lazy_load_component(self, component_id: str, load_callback: Callable) -> Any:
        """
        Lazy load a component.

        Args:
            component_id: Component identifier
            load_callback: Function to load the component

        Returns:
            Loaded component or None
        """
        if not st.session_state.mobile_performance["lazy_loading_enabled"]:
            return load_callback()

        # Register for lazy loading
        self.lazy_loader.register_component(component_id, load_callback)

        # Load component
        return self.lazy_loader.load_component(component_id)

    def preload_critical_components(self, component_ids: list[str]) -> None:
        """Preload critical components for better performance."""
        if st.session_state.mobile_performance["lazy_loading_enabled"]:
            self.lazy_loader.preload_components(component_ids)

    def optimize_images(self, image_data: bytes, max_width: int = 800, quality: int = 85) -> bytes:
        """
        Optimize images for mobile display.

        Args:
            image_data: Original image data
            max_width: Maximum width for resizing
            quality: JPEG quality (1-100)

        Returns:
            Optimized image data
        """
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

            # Save with optimization
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True)

            optimized_data = output.getvalue()

            # Log optimization results
            original_size = len(image_data)
            optimized_size = len(optimized_data)
            reduction = (1 - optimized_size / original_size) * 100

            logger.debug(f"Image optimized: {original_size} -> {optimized_size} bytes ({reduction:.1f}% reduction)")

            return optimized_data

        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")
            return image_data

    def bundle_resources(self, resources: dict[str, Any]) -> str:
        """
        Bundle multiple resources for efficient loading.

        Args:
            resources: Dictionary of resources to bundle

        Returns:
            Bundle identifier
        """
        bundle_id = f"bundle_{hash(str(sorted(resources.keys())))}"

        # Check if bundle already exists
        if self.cache.get(bundle_id):
            return bundle_id

        try:
            # Create resource bundle
            bundle = {
                "id": bundle_id,
                "created_at": datetime.now().isoformat(),
                "resources": resources,
                "size": sum(len(str(v)) for v in resources.values()),
            }

            # Cache bundle
            self.cache.set(bundle_id, bundle, ttl_seconds=3600)  # 1 hour TTL

            logger.debug(f"Created resource bundle: {bundle_id}")
            return bundle_id

        except Exception as e:
            logger.error(f"Failed to create resource bundle: {e}")
            return ""

    def get_bundle_resources(self, bundle_id: str) -> dict[str, Any] | None:
        """Get resources from bundle."""
        bundle = self.cache.get(bundle_id)
        if bundle and isinstance(bundle, dict):
            return bundle.get("resources")
        return None

    def enable_offline_mode(self) -> None:
        """Enable offline mode optimizations."""
        # Preload critical resources
        critical_components = ["mobile_header", "mobile_input_ribbon", "mobile_image_analysis"]

        self.preload_critical_components(critical_components)

        # Increase cache size for offline usage
        self.cache.max_size_bytes = 100 * 1024 * 1024  # 100MB

        logger.info("Offline mode optimizations enabled")

    def get_performance_report(self) -> dict[str, Any]:
        """Get comprehensive performance report."""
        perf_state = st.session_state.mobile_performance

        return {
            "session_info": {
                "initialized_at": perf_state["initialized_at"],
                "total_renders": perf_state["total_renders"],
                "avg_render_time": (perf_state["total_render_time"] / perf_state["total_renders"] if perf_state["total_renders"] > 0 else 0),
                "optimization_level": perf_state["optimization_level"],
            },
            "cache_stats": self.cache.get_stats(),
            "memory_stats": self.memory_manager.get_memory_usage(),
            "memory_pressure": self.memory_manager.check_memory_pressure(),
            "loaded_components": self.lazy_loader.get_loaded_components(),
            "recent_metrics": self._metrics[-10:] if self._metrics else [],
        }

    def _should_cache_result(self, component_id: str, result: Any) -> bool:
        """Determine if result should be cached."""
        # Don't cache if result is too large
        result_size = len(str(result))
        if result_size > 1024 * 1024:  # 1MB
            return False

        # Don't cache dynamic content
        dynamic_components = ["mobile_chat_interface", "mobile_voice_interface"]
        return component_id not in dynamic_components

    def _record_performance_metrics(self, component_id: str, render_time: float) -> None:
        """Record performance metrics."""
        # Update session state
        perf_state = st.session_state.mobile_performance
        perf_state["total_renders"] += 1
        perf_state["total_render_time"] += render_time

        # Create metrics entry
        metrics = PerformanceMetrics(
            component_id=component_id,
            render_time=render_time,
            memory_usage=self.memory_manager.get_memory_usage()["rss_mb"],
            cache_hits=self.cache._hits,
            cache_misses=self.cache._misses,
            lazy_loads=len(self.lazy_loader.get_loaded_components()),
            timestamp=datetime.now().isoformat(),
        )

        self._metrics.append(metrics)

        # Keep only recent metrics
        if len(self._metrics) > 100:
            self._metrics = self._metrics[-100:]

    def set_optimization_level(self, level: str) -> None:
        """
        Set optimization level.

        Args:
            level: 'minimal', 'balanced', 'aggressive', or 'auto'
        """
        st.session_state.mobile_performance["optimization_level"] = level

        if level == "minimal":
            st.session_state.mobile_performance["cache_enabled"] = False
            st.session_state.mobile_performance["lazy_loading_enabled"] = False
        elif level == "balanced":
            st.session_state.mobile_performance["cache_enabled"] = True
            st.session_state.mobile_performance["lazy_loading_enabled"] = True
        elif level == "aggressive":
            st.session_state.mobile_performance["cache_enabled"] = True
            st.session_state.mobile_performance["lazy_loading_enabled"] = True
            self.enable_offline_mode()
        elif level == "auto":
            # Auto-adjust based on device capabilities
            memory_stats = self.memory_manager.get_memory_usage()
            if memory_stats["available_mb"] < 500:  # Low memory device
                self.set_optimization_level("aggressive")
            else:
                self.set_optimization_level("balanced")

        logger.info(f"Performance optimization level set to: {level}")


# Global performance optimizer instance
mobile_performance_optimizer = MobilePerformanceOptimizer()


def optimize_mobile_render(component_id: str):
    """Decorator for optimizing mobile component rendering."""
    return mobile_performance_optimizer.optimize_component_render(component_id)


def lazy_load_mobile_component(component_id: str, load_callback: Callable):
    """Lazy load a mobile component."""
    return mobile_performance_optimizer.lazy_load_component(component_id, load_callback)


@lru_cache(maxsize=128)
def get_optimized_css() -> str:
    """Get optimized CSS for mobile performance."""
    return """
    <style>
    /* Performance optimized CSS for mobile */
    .mobile-performance-optimized {
        /* Use hardware acceleration */
        transform: translateZ(0);
        -webkit-transform: translateZ(0);
        
        /* Optimize repaints */
        will-change: transform, opacity;
        
        /* Reduce layout thrashing */
        contain: layout style paint;
    }
    
    .mobile-lazy-load {
        /* Lazy loading placeholder */
        min-height: 100px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading-shimmer 1.5s infinite;
    }
    
    @keyframes loading-shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    .mobile-memory-efficient {
        /* Reduce memory usage */
        image-rendering: optimizeSpeed;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
    }
    
    /* Optimize touch interactions */
    .mobile-touch-optimized {
        touch-action: manipulation;
        -webkit-tap-highlight-color: transparent;
        -webkit-touch-callout: none;
        -webkit-user-select: none;
        user-select: none;
    }
    
    /* Reduce animations on low-end devices */
    @media (prefers-reduced-motion: reduce) {
        .mobile-performance-optimized * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """
