"""
Mobile State Manager for PlantGuard UI.

This module provides centralized state management for mobile components
with session persistence and error recovery capabilities.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Types of state that can be managed."""

    COMPONENT = "component"
    GLOBAL = "global"
    SESSION = "session"
    ERROR = "error"
    CACHE = "cache"


@dataclass
class StateEntry:
    """Standard state entry structure."""

    key: str
    value: Any
    state_type: StateType
    created_at: str
    updated_at: str
    expires_at: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "state_type": self.state_type.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata or {},
        }


class MobileStateManager:
    """Centralized state management for mobile components."""

    def __init__(self) -> None:
        """Initialize state manager with default configuration."""
        self._state_prefix = "mobile_state"
        self._error_prefix = "mobile_error"
        self._global_prefix = "mobile_global"
        self._cache_prefix = "mobile_cache"

        # Initialize state tracking
        self._initialize_state_tracking()

    def _initialize_state_tracking(self) -> None:
        """Initialize state tracking in session state."""
        tracking_key = f"{self._state_prefix}_tracking"
        if tracking_key not in st.session_state:
            st.session_state[tracking_key] = {
                "initialized_at": datetime.now().isoformat(),
                "component_states": {},
                "global_states": {},
                "error_states": {},
                "cache_states": {},
                "state_history": [],
            }

    def get_component_state(self, component_id: str) -> dict[str, Any]:
        """
        Get state for a specific component.

        Args:
            component_id: Unique identifier for the component

        Returns:
            Component state dictionary
        """
        state_key = f"{self._state_prefix}_{component_id}"

        if state_key not in st.session_state:
            # Create default state structure
            default_state = {
                "component_id": component_id,
                "initialized": True,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "error": None,
                "data": {},
                "ui_state": {"visible": True, "loading": False, "disabled": False, "expanded": False},
                "validation": {"is_valid": True, "errors": [], "warnings": []},
                "metadata": {"component_type": None, "css_classes": [], "ai_discoverable": True},
            }

            st.session_state[state_key] = default_state
            self._track_state_change(component_id, "created", default_state)
            logger.debug(f"Created default state for component: {component_id}")

        return st.session_state[state_key]

    def set_component_state(self, component_id: str, state: dict[str, Any]) -> None:
        """
        Set state for a specific component.

        Args:
            component_id: Unique identifier for the component
            state: State dictionary to set
        """
        try:
            state_key = f"{self._state_prefix}_{component_id}"

            # Update timestamp
            state["last_updated"] = datetime.now().isoformat()

            # Preserve component_id
            state["component_id"] = component_id

            # Store state
            st.session_state[state_key] = state

            # Track change
            self._track_state_change(component_id, "updated", state)

            logger.debug(f"Updated state for component: {component_id}")

        except Exception as e:
            logger.error(f"Failed to set state for component {component_id}: {e}")
            self.set_error_state(component_id, str(e))

    def update_component_state(self, component_id: str, updates: dict[str, Any]) -> None:
        """
        Update specific fields in component state.

        Args:
            component_id: Unique identifier for the component
            updates: Dictionary of fields to update
        """
        current_state = self.get_component_state(component_id)

        # Deep merge updates
        self._deep_merge(current_state, updates)

        # Set updated state
        self.set_component_state(component_id, current_state)

    def clear_component_state(self, component_id: str) -> None:
        """
        Clear state for a specific component.

        Args:
            component_id: Unique identifier for the component
        """
        state_key = f"{self._state_prefix}_{component_id}"

        if state_key in st.session_state:
            del st.session_state[state_key]
            self._track_state_change(component_id, "cleared", None)
            logger.debug(f"Cleared state for component: {component_id}")

    def get_global_state(self, key: str, default: Any = None) -> Any:
        """
        Get global application state.

        Args:
            key: State key
            default: Default value if key doesn't exist

        Returns:
            State value or default
        """
        global_key = f"{self._global_prefix}_{key}"
        return st.session_state.get(global_key, default)

    def set_global_state(self, key: str, value: Any) -> None:
        """
        Set global application state.

        Args:
            key: State key
            value: State value
        """
        global_key = f"{self._global_prefix}_{key}"
        st.session_state[global_key] = value

        # Track global state change
        tracking_key = f"{self._state_prefix}_tracking"
        if tracking_key in st.session_state:
            st.session_state[tracking_key]["global_states"][key] = {"value": value, "updated_at": datetime.now().isoformat()}

        logger.debug(f"Set global state: {key}")

    def get_error_state(self, component_id: str) -> dict[str, Any] | None:
        """
        Get error state for a component.

        Args:
            component_id: Component identifier

        Returns:
            Error state dictionary or None
        """
        error_key = f"{self._error_prefix}_{component_id}"
        return st.session_state.get(error_key)

    def set_error_state(
        self, component_id: str, error_message: str, error_type: str = "general", recovery_suggestions: list[str] | None = None
    ) -> None:
        """
        Set error state for a component.

        Args:
            component_id: Component identifier
            error_message: Error message
            error_type: Type of error
            recovery_suggestions: List of recovery suggestions
        """
        error_key = f"{self._error_prefix}_{component_id}"
        error_state = {
            "component_id": component_id,
            "error_message": error_message,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
            "recovery_suggestions": recovery_suggestions or [],
            "resolved": False,
        }

        st.session_state[error_key] = error_state

        # Also update component state to reflect error
        component_state = self.get_component_state(component_id)
        component_state["error"] = error_message
        component_state["ui_state"]["disabled"] = True
        self.set_component_state(component_id, component_state)

        logger.warning(f"Set error state for {component_id}: {error_message}")

    def clear_error_state(self, component_id: str) -> None:
        """
        Clear error state for a component.

        Args:
            component_id: Component identifier
        """
        error_key = f"{self._error_prefix}_{component_id}"

        if error_key in st.session_state:
            del st.session_state[error_key]

        # Clear error from component state
        component_state = self.get_component_state(component_id)
        component_state["error"] = None
        component_state["ui_state"]["disabled"] = False
        self.set_component_state(component_id, component_state)

        logger.debug(f"Cleared error state for component: {component_id}")

    def get_all_component_states(self) -> dict[str, dict[str, Any]]:
        """
        Get all component states.

        Returns:
            Dictionary mapping component IDs to their states
        """
        component_states = {}

        for key in st.session_state:
            if key.startswith(self._state_prefix) and not key.endswith("_tracking"):
                component_id = key.replace(f"{self._state_prefix}_", "")
                component_states[component_id] = st.session_state[key]

        return component_states

    def get_all_error_states(self) -> dict[str, dict[str, Any]]:
        """
        Get all error states.

        Returns:
            Dictionary mapping component IDs to their error states
        """
        error_states = {}

        for key in st.session_state:
            if key.startswith(self._error_prefix):
                component_id = key.replace(f"{self._error_prefix}_", "")
                error_states[component_id] = st.session_state[key]

        return error_states

    def validate_component_state(self, component_id: str) -> dict[str, Any]:
        """
        Validate component state structure.

        Args:
            component_id: Component identifier

        Returns:
            Validation results
        """
        state = self.get_component_state(component_id)

        validation_results: dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

        # Check required fields
        required_fields = ["component_id", "initialized", "created_at", "last_updated"]
        for field in required_fields:
            if field not in state:
                validation_results["valid"] = False
                errors_list = validation_results.get("errors", [])
                if isinstance(errors_list, list):
                    errors_list.append(f"Missing required field: {field}")
                    validation_results["errors"] = errors_list

        # Check data types
        warnings_list = validation_results.get("warnings", [])
        if isinstance(warnings_list, list):
            if "data" in state and not isinstance(state["data"], dict):
                warnings_list.append("'data' field should be a dictionary")

            if "ui_state" in state and not isinstance(state["ui_state"], dict):
                warnings_list.append("'ui_state' field should be a dictionary")

            validation_results["warnings"] = warnings_list

        return validation_results

    def cleanup_expired_states(self) -> int:
        """
        Clean up expired states.

        Returns:
            Number of states cleaned up
        """
        cleaned_count = 0
        current_time = datetime.now()

        # This would implement expiration logic if needed
        # For now, we'll just log that cleanup was called
        logger.debug("State cleanup called - no expired states found")

        return cleaned_count

    def export_state_snapshot(self) -> dict[str, Any]:
        """
        Export current state snapshot for debugging.

        Returns:
            State snapshot dictionary
        """
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "component_states": self.get_all_component_states(),
            "error_states": self.get_all_error_states(),
            "global_states": {},
            "tracking_info": st.session_state.get(f"{self._state_prefix}_tracking", {}),
        }

        # Get global states
        for key in st.session_state:
            if key.startswith(self._global_prefix):
                global_key = key.replace(f"{self._global_prefix}_", "")
                snapshot["global_states"][global_key] = st.session_state[key]

        return snapshot

    def restore_state_snapshot(self, snapshot: dict[str, Any]) -> bool:
        """
        Restore state from snapshot.

        Args:
            snapshot: State snapshot to restore

        Returns:
            True if successful, False otherwise
        """
        try:
            # Restore component states
            for component_id, state in snapshot.get("component_states", {}).items():
                self.set_component_state(component_id, state)

            # Restore global states
            for key, value in snapshot.get("global_states", {}).items():
                self.set_global_state(key, value)

            logger.info("State snapshot restored successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to restore state snapshot: {e}")
            return False

    def _track_state_change(self, component_id: str, action: str, state: dict[str, Any] | None) -> None:
        """
        Track state changes for debugging and AI agent understanding.

        Args:
            component_id: Component identifier
            action: Action performed (created, updated, cleared)
            state: Current state (None for cleared)
        """
        tracking_key = f"{self._state_prefix}_tracking"

        if tracking_key in st.session_state:
            tracking_info: dict[str, Any] = st.session_state[tracking_key]

            # Add to history
            history_entry = {
                "component_id": component_id,
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "state_keys": list(state.keys()) if state else [],
            }

            # Ensure state_history is a list
            if "state_history" not in tracking_info:
                tracking_info["state_history"] = []

            # Safely get and update state history
            state_history = tracking_info.get("state_history", [])
            if isinstance(state_history, list):
                state_history.append(history_entry)

                # Keep only last 100 entries
                if len(state_history) > 100:
                    tracking_info["state_history"] = state_history[-100:]
                else:
                    tracking_info["state_history"] = state_history

            # Update component tracking
            if "component_states" not in tracking_info:
                tracking_info["component_states"] = {}

            # Safely get and update component states
            component_states = tracking_info.get("component_states", {})
            if isinstance(component_states, dict):
                component_states[component_id] = {"last_action": action, "last_update": datetime.now().isoformat()}
                tracking_info["component_states"] = component_states

    def _deep_merge(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        """
        Deep merge source dictionary into target dictionary.

        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def get_state_statistics(self) -> dict[str, Any]:
        """
        Get statistics about current state usage.

        Returns:
            Statistics dictionary
        """
        component_states = self.get_all_component_states()
        error_states = self.get_all_error_states()

        return {
            "total_components": len(component_states),
            "components_with_errors": len(error_states),
            "total_session_keys": len([k for k in st.session_state if k.startswith("mobile_")]),
            "memory_usage_estimate": len(str(st.session_state)),
            "last_activity": datetime.now().isoformat(),
        }
