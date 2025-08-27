"""
Mobile Lazy Loading Utilities

Implements lazy loading for better performance on mobile devices.
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class MobileLazyLoader:
    """Lazy loading utilities for mobile components."""

    def __init__(self):
        self._loaded_components: dict[str, Any] = {}
        self._deferred_operations: dict[str, Callable] = {}
        self._loading_states: dict[str, bool] = {}

    def lazy_component(self, component_id: str, loader_func: Callable, **kwargs) -> Any:
        """Lazy load a component."""
        if component_id in self._loaded_components:
            return self._loaded_components[component_id]

        # Show loading state
        self._loading_states[component_id] = True

        try:
            # Load component
            component = loader_func(**kwargs)
            self._loaded_components[component_id] = component
            self._loading_states[component_id] = False

            logger.debug(f"Lazy loaded component: {component_id}")
            return component

        except Exception as e:
            self._loading_states[component_id] = False
            logger.error(f"Failed to lazy load {component_id}: {e}")
            return None

    def is_loading(self, component_id: str) -> bool:
        """Check if component is currently loading."""
        return self._loading_states.get(component_id, False)

    def defer_operation(self, operation_id: str, operation: Callable, delay: float = 0.1) -> None:
        """Defer an operation to improve perceived performance."""
        self._deferred_operations[operation_id] = operation

        # Use Streamlit's rerun mechanism for deferred execution
        if delay > 0:
            time.sleep(delay)

        try:
            result = operation()
            logger.debug(f"Executed deferred operation: {operation_id}")
            return result
        except Exception as e:
            logger.error(f"Deferred operation {operation_id} failed: {e}")
            return None

    def lazy_image_loader(self, image_key: str, image_source: Any, placeholder: str = "Loading...") -> Any:
        """Lazy load images with placeholder."""
        if f"image_{image_key}" in self._loaded_components:
            return self._loaded_components[f"image_{image_key}"]

        # Show placeholder first
        placeholder_container = st.empty()
        placeholder_container.text(placeholder)

        try:
            # Load image
            if hasattr(image_source, "read"):
                # File-like object
                image_data = image_source.read()
            else:
                # Assume it's already image data
                image_data = image_source

            # Cache loaded image
            self._loaded_components[f"image_{image_key}"] = image_data

            # Replace placeholder with actual image
            placeholder_container.image(image_data, use_column_width=True)

            return image_data

        except Exception as e:
            placeholder_container.error(f"Failed to load image: {e!s}")
            logger.error(f"Failed to lazy load image {image_key}: {e}")
            return None

    def create_loading_placeholder(self, container_key: str, message: str = "Loading...") -> Any:
        """Create a loading placeholder."""
        container = st.empty()

        # Create loading animation
        loading_html = f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            text-align: center;
        ">
            <div style="
                width: 32px;
                height: 32px;
                border: 3px solid #E5E7EB;
                border-top: 3px solid #16A34A;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 1rem;
            "></div>
            <span style="color: #6B7280;">{message}</span>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """

        container.markdown(loading_html, unsafe_allow_html=True)
        return container

    def replace_loading_placeholder(self, container: Any, content: Any) -> None:
        """Replace loading placeholder with actual content."""
        container.empty()
        if callable(content):
            content()
        else:
            container.write(content)

    def batch_load_components(self, component_specs: list) -> dict[str, Any]:
        """Load multiple components in batch for better performance."""
        results = {}

        for spec in component_specs:
            component_id = spec.get("id")
            loader_func = spec.get("loader")
            kwargs = spec.get("kwargs", {})

            if component_id and loader_func:
                results[component_id] = self.lazy_component(component_id, loader_func, **kwargs)

        return results

    def preload_critical_components(self, critical_components: list) -> None:
        """Preload critical components for better user experience."""
        logger.info(f"Preloading critical components: {critical_components}")

        for component_spec in critical_components:
            try:
                component_id = component_spec.get("id")
                loader_func = component_spec.get("loader")
                kwargs = component_spec.get("kwargs", {})

                if component_id and loader_func:
                    self.lazy_component(component_id, loader_func, **kwargs)

            except Exception as e:
                logger.warning(f"Failed to preload component {component_spec}: {e}")

    def clear_cache(self) -> None:
        """Clear lazy loading cache."""
        self._loaded_components.clear()
        self._deferred_operations.clear()
        self._loading_states.clear()
        logger.info("Lazy loading cache cleared")


# Global lazy loader instance
mobile_lazy_loader = MobileLazyLoader()


# Decorators for lazy loading
def lazy_load(component_id: str):
    """Decorator for lazy loading components."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return mobile_lazy_loader.lazy_component(component_id, func, *args, **kwargs)

        return wrapper

    return decorator


def defer_execution(operation_id: str, delay: float = 0.1):
    """Decorator for deferring operation execution."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def operation():
                return func(*args, **kwargs)

            return mobile_lazy_loader.defer_operation(operation_id, operation, delay)

        return wrapper

    return decorator


# Streamlit component helpers
def lazy_streamlit_component(component_func: Callable, component_id: str, *args, **kwargs):
    """Helper for lazy loading Streamlit components."""
    return mobile_lazy_loader.lazy_component(component_id, lambda: component_func(*args, **kwargs))


def create_lazy_tabs(tab_specs: list) -> dict[str, Any]:
    """Create lazy-loaded tabs."""
    tab_names = [spec["name"] for spec in tab_specs]
    tabs = st.tabs(tab_names)

    lazy_tabs = {}
    for i, (tab, spec) in enumerate(zip(tabs, tab_specs, strict=False)):
        tab_id = spec.get("id", f"tab_{i}")
        content_func = spec.get("content")

        with tab:
            if content_func:
                lazy_tabs[tab_id] = mobile_lazy_loader.lazy_component(f"tab_content_{tab_id}", content_func)

    return lazy_tabs
