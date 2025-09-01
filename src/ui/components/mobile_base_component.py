"""
Mobile Base Component for PlantGuard UI.

This module provides a base class for all mobile components with
essential state management and error handling capabilities.
"""

import logging
from typing import Any, Dict, Optional

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
        if f"mobile_{self.component_id}_state" not in st.session_state:
            st.session_state[f"mobile_{self.component_id}_state"] = {
                "data": {},
                "metadata": {
                    "created_at": st.session_state.get("app_start_time", 0),
                    "last_updated": st.session_state.get("app_start_time", 0),
                    "component_type": self.__class__.__name__,
                }
            }

    def get_state(self) -> Dict[str, Any]:
        """Get current component state."""
        return st.session_state.get(f"mobile_{self.component_id}_state", {"data": {}, "metadata": {}})

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set component state."""
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["last_updated"] = st.session_state.get("app_start_time", 0)
        st.session_state[f"mobile_{self.component_id}_state"] = state

    def update_state(self, key: str, value: Any) -> None:
        """Update specific state key."""
        current_state = self.get_state()
        if "data" not in current_state:
            current_state["data"] = {}
        current_state["data"][key] = value
        self.set_state(current_state)

    def get_state_value(self, key: str, default: Any = None) -> Any:
        """Get specific state value."""
        state = self.get_state()
        return state.get("data", {}).get(key, default)

    def clear_state(self) -> None:
        """Clear component state."""
        if f"mobile_{self.component_id}_state" in st.session_state:
            del st.session_state[f"mobile_{self.component_id}_state"]

    def render(self) -> None:
        """Render the component. Override in subclasses."""
        st.write(f"Component: {self.component_id}")

    def get_component_info(self) -> Dict[str, Any]:
        """Get component information."""
        return {
            "component_id": self.component_id,
            "title": self.title,
            "class_name": self.__class__.__name__,
            "state_keys": list(self.get_state().get("data", {}).keys()),
        }
