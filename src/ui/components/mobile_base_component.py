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
        # Ensure top-level component_states dict exists for structured storage
        if "component_states" not in st.session_state:
            st.session_state["component_states"] = {}

        if state_key not in st.session_state["component_states"]:
            # Initialize structured state with metadata and empty data dict
            st.session_state["component_states"][state_key] = {
                "data": {},
                "metadata": {
                    "created_at": st.session_state.get("app_start_time", 0),
                    "last_updated": st.session_state.get("app_start_time", 0),
                    "component_type": self.__class__.__name__,
                },
            }

    def get_state(self) -> dict[str, Any]:
        """Get current component state."""
        state_key = f"mobile_{self.component_id}_state"

        # Prefer structured storage under component_states
        comp_states = st.session_state.get("component_states", {})
        return comp_states.get(state_key, {"data": {}, "metadata": {}})

    def set_state(self, state: dict[str, Any]) -> None:
        """Set component state."""
        state_key = f"mobile_{self.component_id}_state"
        # Ensure structured storage exists
        if "component_states" not in st.session_state:
            st.session_state["component_states"] = {}

        # Normalize incoming state
        stored = {
            "data": state.get("data", {}) if isinstance(state, dict) else {},
            "metadata": state.get("metadata", {}),
        }
        # Update metadata timestamps
        stored["metadata"]["last_updated"] = st.session_state.get("app_start_time", 0)

        st.session_state["component_states"][state_key] = stored

    def update_state(self, key: str, value: Any) -> None:
        """Update specific state key."""
        state_key = f"mobile_{self.component_id}_state"
        if "component_states" not in st.session_state:
            st.session_state["component_states"] = {}

        if state_key not in st.session_state["component_states"]:
            self._initialize_component_state()

        st.session_state["component_states"][state_key]["data"][key] = value
        st.session_state["component_states"][state_key]["metadata"]["last_updated"] = st.session_state.get("app_start_time", 0)

    def get_state_value(self, key: str, default: Any = None) -> Any:
        """Get specific state value."""
        state_key = f"mobile_{self.component_id}_state"
        comp_states = st.session_state.get("component_states", {})
        if state_key in comp_states:
            return comp_states[state_key].get("data", {}).get(key, default)

        # Backwards compatibility: check legacy flat keys
        legacy_key = f"{state_key}_{key}"
        return st.session_state.get(legacy_key, default)

    def clear_state(self) -> None:
        """Clear component state."""
        state_key = f"mobile_{self.component_id}_state"
        # Remove structured component state if present
        if "component_states" in st.session_state and state_key in st.session_state["component_states"]:
            del st.session_state["component_states"][state_key]

        # Also remove legacy flat keys for backward compatibility
        keys_to_delete = [k for k in list(st.session_state.keys()) if k.startswith(f"{state_key}_")]
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
            "state_keys": list(self.get_state().get("data", {})),
        }
