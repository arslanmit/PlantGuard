"""
Mobile Memory Manager

Optimizes memory usage for mobile devices with limited resources.
"""

import gc
import logging
import time
import weakref
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class MobileMemoryManager:
    """Memory manager optimized for mobile devices."""

    def __init__(self) -> None:
        self._tracked_objects: dict[str, weakref.ref] = {}
        self._memory_thresholds = {
            "warning": 50 * 1024 * 1024,  # 50MB
            "critical": 100 * 1024 * 1024,  # 100MB
        }
        self._cleanup_callbacks: list[callable] = []
        self._last_cleanup = time.time()
        self._cleanup_interval = 30  # seconds

    def track_object(self, obj_id: str, obj: Any) -> None:
        """Track object for memory management."""

        def cleanup_callback(ref):
            if obj_id in self._tracked_objects:
                del self._tracked_objects[obj_id]
                logger.debug(f"Cleaned up tracked object: {obj_id}")

        self._tracked_objects[obj_id] = weakref.ref(obj, cleanup_callback)

    def get_memory_usage(self) -> dict[str, Any]:
        """Get current memory usage information."""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
                "tracked_objects": len(self._tracked_objects),
                "available": psutil.virtual_memory().available / 1024 / 1024,
            }
        except ImportError:
            return {
                "rss_mb": 0,
                "vms_mb": 0,
                "percent": 0,
                "tracked_objects": len(self._tracked_objects),
                "available": 0,
                "note": "psutil not available",
            }

    def check_memory_pressure(self) -> dict[str, Any]:
        """Check if memory pressure requires cleanup."""
        memory_info = self.get_memory_usage()
        rss_bytes = memory_info["rss_mb"] * 1024 * 1024

        pressure_level = "normal"
        if rss_bytes > self._memory_thresholds["critical"]:
            pressure_level = "critical"
        elif rss_bytes > self._memory_thresholds["warning"]:
            pressure_level = "warning"

        return {"pressure_level": pressure_level, "memory_usage": memory_info, "cleanup_recommended": pressure_level != "normal"}

    def perform_cleanup(self, force: bool = False) -> dict[str, Any]:
        """Perform memory cleanup."""
        current_time = time.time()

        if not force and (current_time - self._last_cleanup) < self._cleanup_interval:
            return {"status": "skipped", "reason": "cleanup_interval_not_reached"}

        logger.info("Performing memory cleanup")

        cleanup_results = {
            "objects_before": len(self._tracked_objects),
            "session_state_keys_before": len(st.session_state) if hasattr(st, "session_state") else 0,
        }

        # Clean up dead references
        dead_refs = [obj_id for obj_id, ref in self._tracked_objects.items() if ref() is None]
        for obj_id in dead_refs:
            del self._tracked_objects[obj_id]

        # Run custom cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"Cleanup callback failed: {e}")

        # Clean up old session state entries
        self._cleanup_session_state()

        # Force garbage collection
        collected = gc.collect()

        cleanup_results.update(
            {
                "objects_after": len(self._tracked_objects),
                "session_state_keys_after": len(st.session_state) if hasattr(st, "session_state") else 0,
                "dead_references_removed": len(dead_refs),
                "garbage_collected": collected,
                "cleanup_time": time.time() - current_time,
            }
        )

        self._last_cleanup = current_time
        logger.info(f"Memory cleanup completed: {cleanup_results}")

        return {"status": "completed", "results": cleanup_results}

    def _cleanup_session_state(self) -> None:
        """Clean up old session state entries."""
        if not hasattr(st, "session_state"):
            return

        # Clean up temporary state entries
        temp_keys = [key for key in st.session_state if key.startswith("temp_")]
        for key in temp_keys:
            if key in st.session_state:
                del st.session_state[key]

        # Clean up old analysis results (keep only last 10)
        if "analysis_history" in st.session_state:
            history = st.session_state.analysis_history
            if len(history) > 10:
                st.session_state.analysis_history = history[-10:]

    def register_cleanup_callback(self, callback: callable) -> None:
        """Register a cleanup callback."""
        self._cleanup_callbacks.append(callback)

    def auto_cleanup_if_needed(self) -> None:
        """Automatically perform cleanup if memory pressure is high."""
        pressure_info = self.check_memory_pressure()

        if pressure_info["cleanup_recommended"]:
            logger.warning(f"Memory pressure detected: {pressure_info['pressure_level']}")
            self.perform_cleanup(force=True)

    def optimize_for_mobile(self) -> dict[str, Any]:
        """Apply mobile-specific memory optimizations."""
        optimizations = []

        # Set lower memory thresholds for mobile
        self._memory_thresholds = {
            "warning": 30 * 1024 * 1024,  # 30MB
            "critical": 60 * 1024 * 1024,  # 60MB
        }
        optimizations.append("Reduced memory thresholds for mobile")

        # More frequent cleanup
        self._cleanup_interval = 15  # seconds
        optimizations.append("Increased cleanup frequency")

        # Force immediate cleanup
        cleanup_result = self.perform_cleanup(force=True)
        optimizations.append("Performed initial cleanup")

        return {"status": "completed", "optimizations": optimizations, "cleanup_result": cleanup_result}


# Global memory manager instance
mobile_memory_manager = MobileMemoryManager()


# Auto-cleanup decorator for components
def auto_cleanup(func) -> Callable:
    """Decorator to automatically check memory pressure after function execution."""

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        mobile_memory_manager.auto_cleanup_if_needed()
        return result

    return wrapper
