"""
Optimized Mobile Component Loader

Implements lazy loading and caching for better performance.
"""

import logging
import time
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class MobileOptimizedLoader:
    """Optimized loader for mobile components with lazy loading and caching."""

    def __init__(self):
        self._component_cache: dict[str, Any] = {}
        self._load_times: dict[str, float] = {}
        self._performance_metrics = {"total_loads": 0, "cache_hits": 0, "average_load_time": 0.0}

    def load_component(self, component_type: str, component_id: str, **kwargs) -> Any:
        """Load component with caching and performance monitoring."""
        start_time = time.time()

        cache_key = f"{component_type}_{component_id}"

        # Check cache first
        if cache_key in self._component_cache:
            self._performance_metrics["cache_hits"] += 1
            logger.debug(f"Cache hit for {cache_key}")
            return self._component_cache[cache_key]

        # Lazy load component
        try:
            component = self._lazy_load_component(component_type, component_id, **kwargs)

            # Cache the component
            self._component_cache[cache_key] = component

            # Record performance metrics
            load_time = time.time() - start_time
            self._load_times[cache_key] = load_time
            self._performance_metrics["total_loads"] += 1

            # Update average load time
            total_time = sum(self._load_times.values())
            self._performance_metrics["average_load_time"] = total_time / len(self._load_times)

            logger.debug(f"Loaded {cache_key} in {load_time:.3f}s")
            return component

        except Exception as e:
            logger.error(f"Failed to load component {cache_key}: {e}")
            return None

    def _lazy_load_component(self, component_type: str, component_id: str, **kwargs) -> Any:
        """Lazy load component based on type."""
        component_map = {
            "layout_manager": self._load_layout_manager,
            "header": self._load_header,
            "input_ribbon": self._load_input_ribbon,
            "content_tabs": self._load_content_tabs,
            "image_analysis": self._load_image_analysis,
            "voice_interface": self._load_voice_interface,
            "chat_interface": self._load_chat_interface,
            "history_view": self._load_history_view,
            "settings_card": self._load_settings_card,
        }

        loader_func = component_map.get(component_type)
        if not loader_func:
            raise ValueError(f"Unknown component type: {component_type}")

        return loader_func(component_id, **kwargs)

    def _load_layout_manager(self, component_id: str, **kwargs) -> Any:
        """Lazy load layout manager."""
        from ui.components.mobile_layout_manager import MobileLayoutManager

        return MobileLayoutManager(component_id, **kwargs)

    def _load_header(self, component_id: str, **kwargs) -> Any:
        """Lazy load header component."""
        from ui.components.mobile_header import MobileHeader

        title = kwargs.get("title", "PlantGuard")
        subtitle = kwargs.get("subtitle", "AI Plant Care")
        return MobileHeader(component_id, title, subtitle)

    def _load_input_ribbon(self, component_id: str, **kwargs) -> Any:
        """Lazy load input ribbon."""
        from ui.components.mobile_input_ribbon import MobileInputRibbon

        return MobileInputRibbon(component_id, **kwargs)

    def _load_content_tabs(self, component_id: str, **kwargs) -> Any:
        """Lazy load content tabs."""
        from ui.components.mobile_content_tabs import MobileContentTabs

        return MobileContentTabs(component_id, **kwargs)

    def _load_image_analysis(self, component_id: str, **kwargs) -> Any:
        """Lazy load image analysis component."""
        from ui.components.mobile_image_analysis import MobileImageAnalysis

        return MobileImageAnalysis(component_id, **kwargs)

    def _load_voice_interface(self, component_id: str, **kwargs) -> Any:
        """Lazy load voice interface."""
        from ui.components.mobile_voice_interface import MobileVoiceInterface

        return MobileVoiceInterface(component_id, **kwargs)

    def _load_chat_interface(self, component_id: str, **kwargs) -> Any:
        """Lazy load chat interface."""
        from ui.components.mobile_chat_interface import MobileChatInterface

        return MobileChatInterface(component_id, **kwargs)

    def _load_history_view(self, component_id: str, **kwargs) -> Any:
        """Lazy load history view."""
        from ui.components.mobile_history_view import MobileHistoryView

        return MobileHistoryView(component_id, **kwargs)

    def _load_settings_card(self, component_id: str, **kwargs) -> Any:
        """Lazy load settings card."""
        from ui.components.mobile_settings_card import MobileSettingsCard

        return MobileSettingsCard(component_id, **kwargs)

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics."""
        cache_hit_rate = (self._performance_metrics["cache_hits"] / max(self._performance_metrics["total_loads"], 1)) * 100

        return {
            **self._performance_metrics,
            "cache_hit_rate": cache_hit_rate,
            "cached_components": len(self._component_cache),
            "load_times": dict(self._load_times),
        }

    def clear_cache(self) -> None:
        """Clear component cache."""
        self._component_cache.clear()
        self._load_times.clear()
        logger.info("Component cache cleared")

    def preload_components(self, component_types: list) -> None:
        """Preload commonly used components."""
        logger.info(f"Preloading components: {component_types}")

        for component_type in component_types:
            try:
                self.load_component(component_type, f"preload_{component_type}")
            except Exception as e:
                logger.warning(f"Failed to preload {component_type}: {e}")


# Global optimized loader instance
mobile_optimized_loader = MobileOptimizedLoader()


# Streamlit caching for component instances
@st.cache_resource
def get_cached_component(component_type: str, component_id: str, **kwargs) -> Any:
    """Get cached component instance."""
    return mobile_optimized_loader.load_component(component_type, component_id, **kwargs)
