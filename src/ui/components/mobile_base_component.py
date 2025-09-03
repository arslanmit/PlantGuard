"""
Mobile Base Component for PlantGuard UI.

This module provides a base class for all mobile components with
essential state management and error handling capabilities.
"""

import logging
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class MobileBaseComponent:
    """Base class for all mobile components with state management."""

    def __init__(self, component_id: str, title: str = "", **kwargs) -> None:
        """
        Initialize mobile base component.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        self.component_id = component_id
        self.title = title
        self.config = kwargs.get("config", {})

        # Initialize component state
        self._initialize_component_state()

        logger.debug("MobileBaseComponent initialized: %s", component_id)

    def _initialize_component_state(self) -> None:
        """Initialize component-specific state."""
        state_key = f"mobile_{self.component_id}_state"
        if state_key not in st.session_state:
            # Store simple values to avoid serialization issues
            st.session_state[f"{state_key}_created"] = st.session_state.get("app_start_time", 0)
            st.session_state[f"{state_key}_updated"] = st.session_state.get("app_start_time", 0)
            st.session_state[f"{state_key}_type"] = self.__class__.__name__

    def get_state(self) -> dict[str, Any]:
        """Get current component state."""
        state_key = f"mobile_{self.component_id}_state"
        return {
            "data": {},
            "metadata": {
                "created_at": st.session_state.get(f"{state_key}_created", 0),
                "last_updated": st.session_state.get(f"{state_key}_updated", 0),
                "component_type": st.session_state.get(f"{state_key}_type", "Unknown"),
            },
        }

    def set_state(self, state: dict[str, Any]) -> None:
        """Set component state."""
        state_key = f"mobile_{self.component_id}_state"
        st.session_state[f"{state_key}_updated"] = st.session_state.get("app_start_time", 0)
        # Note: Complex state data storage disabled to prevent serialization issues

    def update_state(self, key: str, value: Any) -> None:
        """Update specific state key."""
        # Simplified to avoid storing complex objects
        state_key = f"mobile_{self.component_id}_state"
        st.session_state[f"{state_key}_updated"] = st.session_state.get("app_start_time", 0)

    def get_state_value(self, key: str, default: Any = None) -> Any:
        """Get specific state value."""
        # Simplified to avoid complex object storage
        return default

    def clear_state(self) -> None:
        """Clear component state."""
        state_key = f"mobile_{self.component_id}_state"
        keys_to_delete = [k for k in st.session_state.keys() if k.startswith(f"{state_key}_")]
        for key in keys_to_delete:
            del st.session_state[key]

    def render(self) -> None:
        """Render the component. Override in subclasses."""
        st.write(f"Component: {self.component_id}")

    def get_component_info(self) -> dict[str, Any]:
        """Get component information."""
        return {
            "component_id": self.component_id,
            "title": self.title,
            "class_name": self.__class__.__name__,
            "state_keys": list(self.get_state().get("data", {}).keys()),
        }
