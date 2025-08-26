"""
Mobile Component Registry for PlantGuard UI.

This module provides component registration and management system for AI agent
recognition and autonomous testing of mobile interface components.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class MobileComponent(ABC):
    """Abstract base class for mobile components."""

    def __init__(self, component_id: str, title: str):
        """Initialize mobile component."""
        self.component_id = component_id
        self.title = title
        self.component_type = self.__class__.__name__
        self.created_at = datetime.now().isoformat()

    @abstractmethod
    def render(self) -> None:
        """Render the component. Must be implemented by subclasses."""
        pass

    def get_component_info(self) -> dict[str, Any]:
        """Get component information for AI agent recognition."""
        return {
            "component_id": self.component_id,
            "title": self.title,
            "component_type": self.component_type,
            "created_at": self.created_at,
            "css_classes": self.get_css_classes(),
            "ai_agent_metadata": self.get_ai_metadata(),
        }

    def get_css_classes(self) -> list[str]:
        """Get CSS classes used by this component for AI agent recognition."""
        return [f"mobile-{self.component_type.lower()}"]

    def get_ai_metadata(self) -> dict[str, Any]:
        """Get metadata for AI agent understanding."""
        return {"purpose": "Mobile UI component", "interaction_type": "touch", "accessibility": True, "responsive": True}


class MobileStateManager:
    """Centralized state management for mobile components."""

    # State persistence keys
    PERSISTENCE_KEY = "mobile_state_persistence"
    ERROR_RECOVERY_KEY = "mobile_error_recovery"

    @staticmethod
    def get_component_state(component_id: str) -> dict[str, Any]:
        """Get state for a specific component."""
        state_key = f"mobile_{component_id}_state"
        if state_key not in st.session_state:
            st.session_state[state_key] = {
                "initialized": True,
                "last_updated": datetime.now().isoformat(),
                "error": None,
                "data": {},
                "visible": True,
                "loading": False,
                "component_id": component_id,
                "recovery_attempts": 0,
                "last_error": None,
                "persistent_data": {},
            }
        return st.session_state[state_key]

    @staticmethod
    def set_component_state(component_id: str, state: dict[str, Any]) -> None:
        """Set state for a specific component."""
        state_key = f"mobile_{component_id}_state"
        state["last_updated"] = datetime.now().isoformat()
        state["component_id"] = component_id
        st.session_state[state_key] = state

        # Update persistence tracking
        MobileStateManager._update_persistence_tracking(component_id, state)

    @staticmethod
    def update_component_state(component_id: str, updates: dict[str, Any]) -> None:
        """Update specific fields in component state."""
        current_state = MobileStateManager.get_component_state(component_id)
        current_state.update(updates)
        MobileStateManager.set_component_state(component_id, current_state)

    @staticmethod
    def clear_component_state(component_id: str) -> None:
        """Clear state for a specific component."""
        state_key = f"mobile_{component_id}_state"
        if state_key in st.session_state:
            del st.session_state[state_key]

        # Remove from persistence tracking
        MobileStateManager._remove_from_persistence_tracking(component_id)

    @staticmethod
    def get_all_component_states() -> dict[str, dict[str, Any]]:
        """Get all mobile component states for debugging."""
        mobile_states: dict[str, dict[str, Any]] = {}
        for key, value in st.session_state.items():
            if isinstance(key, str) and key.startswith("mobile_") and key.endswith("_state"):
                component_id = key.replace("mobile_", "").replace("_state", "")
                mobile_states[component_id] = value
        return mobile_states

    @staticmethod
    def set_loading_state(component_id: str, loading: bool, message: str = "") -> None:
        """Set loading state for a component."""
        MobileStateManager.update_component_state(
            component_id, {"loading": loading, "loading_message": message, "last_loading_update": datetime.now().isoformat()}
        )

    @staticmethod
    def set_error_state(component_id: str, error: str | Exception | None, recoverable: bool = True) -> None:
        """Set error state for a component with recovery tracking."""
        error_message = str(error) if error else None
        current_state = MobileStateManager.get_component_state(component_id)

        # Track error recovery attempts
        recovery_attempts = current_state.get("recovery_attempts", 0)
        if error:
            recovery_attempts += 1
        else:
            recovery_attempts = 0

        MobileStateManager.update_component_state(
            component_id,
            {
                "error": error_message,
                "last_error": error_message,
                "error_timestamp": datetime.now().isoformat() if error else None,
                "recoverable": recoverable,
                "recovery_attempts": recovery_attempts,
                "loading": False,  # Clear loading state on error
            },
        )

        # Log error for debugging
        if error:
            logger.error(f"Component {component_id} error (attempt {recovery_attempts}): {error_message}")

    @staticmethod
    def clear_error_state(component_id: str) -> None:
        """Clear error state for a component."""
        MobileStateManager.set_error_state(component_id, None)

    @staticmethod
    def is_component_in_error(component_id: str) -> bool:
        """Check if component is in error state."""
        state = MobileStateManager.get_component_state(component_id)
        return state.get("error") is not None

    @staticmethod
    def get_component_errors() -> dict[str, dict[str, Any]]:
        """Get all components currently in error state."""
        errors: dict[str, dict[str, Any]] = {}
        for component_id, state in MobileStateManager.get_all_component_states().items():
            if state.get("error"):
                errors[component_id] = {
                    "error": state["error"],
                    "timestamp": state.get("error_timestamp"),
                    "recovery_attempts": state.get("recovery_attempts", 0),
                    "recoverable": state.get("recoverable", True),
                }
        return errors

    @staticmethod
    def persist_component_data(component_id: str, data: dict[str, Any]) -> None:
        """Persist component data across sessions."""
        state = MobileStateManager.get_component_state(component_id)
        state["persistent_data"].update(data)
        MobileStateManager.set_component_state(component_id, state)

    @staticmethod
    def get_persistent_data(component_id: str) -> dict[str, Any]:
        """Get persistent data for a component."""
        state = MobileStateManager.get_component_state(component_id)
        return state.get("persistent_data", {})

    @staticmethod
    def restore_component_state(component_id: str) -> bool:
        """Restore component state from persistence."""
        try:
            # Check if there's persistent data to restore
            persistent_data = MobileStateManager.get_persistent_data(component_id)
            if persistent_data:
                MobileStateManager.update_component_state(
                    component_id, {"data": persistent_data, "restored": True, "restore_timestamp": datetime.now().isoformat()}
                )
                logger.info(f"Restored state for component {component_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to restore state for component {component_id}: {e}")
            return False

    @staticmethod
    def reset_component_state(component_id: str) -> None:
        """Reset component to initial state while preserving persistent data."""
        persistent_data = MobileStateManager.get_persistent_data(component_id)
        MobileStateManager.clear_component_state(component_id)

        # Recreate with persistent data
        new_state = MobileStateManager.get_component_state(component_id)
        new_state["persistent_data"] = persistent_data
        MobileStateManager.set_component_state(component_id, new_state)

    @staticmethod
    def _update_persistence_tracking(component_id: str, state: dict[str, Any]) -> None:
        """Update persistence tracking for state management."""
        if MobileStateManager.PERSISTENCE_KEY not in st.session_state:
            st.session_state[MobileStateManager.PERSISTENCE_KEY] = {}

        st.session_state[MobileStateManager.PERSISTENCE_KEY][component_id] = {
            "last_updated": state.get("last_updated"),
            "has_persistent_data": bool(state.get("persistent_data")),
            "error_count": state.get("recovery_attempts", 0),
        }

    @staticmethod
    def _remove_from_persistence_tracking(component_id: str) -> None:
        """Remove component from persistence tracking."""
        if MobileStateManager.PERSISTENCE_KEY in st.session_state:
            persistence_data = st.session_state[MobileStateManager.PERSISTENCE_KEY]
            if component_id in persistence_data:
                del persistence_data[component_id]

    @staticmethod
    def get_state_summary() -> dict[str, Any]:
        """Get comprehensive state summary for debugging and monitoring."""
        all_states = MobileStateManager.get_all_component_states()
        errors = MobileStateManager.get_component_errors()

        return {
            "total_components": len(all_states),
            "components_with_errors": len(errors),
            "components_loading": len([s for s in all_states.values() if s.get("loading")]),
            "components_with_persistent_data": len([s for s in all_states.values() if s.get("persistent_data")]),
            "error_summary": errors,
            "persistence_tracking": st.session_state.get(MobileStateManager.PERSISTENCE_KEY, {}),
            "last_updated": datetime.now().isoformat(),
        }

    @staticmethod
    def cleanup_stale_states(max_age_hours: int = 24) -> int:
        """Clean up stale component states older than specified hours."""
        cleaned_count = 0
        current_time = datetime.now()

        for component_id, state in list(MobileStateManager.get_all_component_states().items()):
            try:
                last_updated = datetime.fromisoformat(state.get("last_updated", ""))
                age_hours = (current_time - last_updated).total_seconds() / 3600

                if age_hours > max_age_hours:
                    MobileStateManager.clear_component_state(component_id)
                    cleaned_count += 1
                    logger.info(f"Cleaned up stale state for component {component_id} (age: {age_hours:.1f}h)")

            except (ValueError, TypeError) as e:
                logger.warning(f"Error checking age for component {component_id}: {e}")

        return cleaned_count


class MobileComponentRegistry:
    """Registry for managing mobile components with AI agent support."""

    def __init__(self):
        """Initialize component registry."""
        self._components: dict[str, type[MobileComponent]] = {}
        self._instances: dict[str, MobileComponent] = {}
        self._component_metadata: dict[str, dict[str, Any]] = {}
        self._lifecycle_hooks: dict[str, dict[str, Any]] = {}
        self._ai_navigation_map: dict[str, dict[str, Any]] = {}

        # Register built-in component types
        self._register_builtin_components()
        self._setup_ai_navigation_map()

    def _register_builtin_components(self) -> None:
        """Register built-in mobile component types."""

        # Create placeholder component classes for testing
        class PlaceholderMobileComponent(MobileComponent):
            def render(self) -> None:
                pass

        builtin_components = {
            "camera_input": "MobileCameraInput",
            "upload_input": "MobileUploadInput",
            "voice_input": "MobileVoiceInput",
            "text_input": "MobileTextInput",
            "analysis_display": "MobileAnalysisDisplay",
            "chat_interface": "MobileChatInterface",
            "history_view": "MobileHistoryView",
            "settings_card": "MobileSettingsCard",
        }

        for component_type, class_name in builtin_components.items():
            # Register placeholder component class
            self._components[component_type] = PlaceholderMobileComponent

            # Register metadata
            self._component_metadata[component_type] = {
                "class_name": class_name,
                "module": f"src.ui.mobile_{component_type}",
                "description": f"Mobile-optimized {component_type.replace('_', ' ')} component",
                "ai_agent_compatible": True,
                "touch_optimized": True,
                "status": "placeholder",  # Indicates this is a placeholder implementation
            }

    def register_component(self, component_type: str, component_class: type[MobileComponent], metadata: dict[str, Any] | None = None) -> None:
        """Register a new mobile component type."""
        self._components[component_type] = component_class

        if metadata:
            self._component_metadata[component_type] = metadata

        logger.info(f"Registered mobile component: {component_type}")

    def create_component(self, component_type: str, component_id: str, title: str, **kwargs) -> MobileComponent | None:
        """Create a component instance with lifecycle management."""
        if component_type not in self._components:
            logger.warning(f"Unknown component type: {component_type}")
            return None

        try:
            # Execute pre-creation hooks
            self._execute_lifecycle_hook("pre_create", component_type, component_id)

            component_class = self._components[component_type]
            instance = component_class(component_id, title, **kwargs)

            # Store instance for later reference
            self._instances[component_id] = instance

            # Initialize component state
            MobileStateManager.get_component_state(component_id)

            # Register component in AI navigation map
            self._register_component_for_ai_navigation(component_id, component_type, instance)

            # Execute post-creation hooks
            self._execute_lifecycle_hook("post_create", component_type, component_id, instance=instance)

            logger.info(f"Created mobile component: {component_id} ({component_type})")
            return instance

        except Exception as e:
            logger.error(f"Failed to create component {component_id}: {e}")
            MobileStateManager.set_error_state(component_id, e)
            return None

    def get_component(self, component_id: str) -> MobileComponent | None:
        """Get an existing component instance."""
        return self._instances.get(component_id)

    def get_available_components(self) -> list[str]:
        """Get list of available component types."""
        return list(self._components.keys())

    def get_component_metadata(self, component_type: str) -> dict[str, Any] | None:
        """Get metadata for a component type."""
        return self._component_metadata.get(component_type)

    def get_all_metadata(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all registered components."""
        return self._component_metadata.copy()

    def get_component_instances(self) -> dict[str, MobileComponent]:
        """Get all component instances."""
        return self._instances.copy()

    def remove_component(self, component_id: str) -> bool:
        """Remove a component instance with lifecycle management."""
        if component_id in self._instances:
            instance = self._instances[component_id]

            # Execute pre-removal hooks
            self._execute_lifecycle_hook("pre_remove", instance.component_type, component_id, instance=instance)

            # Remove from instances
            del self._instances[component_id]

            # Clear component state
            MobileStateManager.clear_component_state(component_id)

            # Remove from AI navigation
            if "ai_navigation" in st.session_state and component_id in st.session_state["ai_navigation"]:
                del st.session_state["ai_navigation"][component_id]

            # Execute post-removal hooks
            self._execute_lifecycle_hook("post_remove", instance.component_type, component_id)

            logger.info(f"Removed mobile component: {component_id}")
            return True
        return False

    def clear_all_components(self) -> None:
        """Clear all component instances."""
        for component_id in list(self._instances.keys()):
            self.remove_component(component_id)

    def get_ai_agent_info(self) -> dict[str, Any]:
        """Get information formatted for AI agent understanding."""
        return {
            "registry_info": {
                "total_component_types": len(self._components),
                "total_instances": len(self._instances),
                "available_types": self.get_available_components(),
                "lifecycle_hooks": len(self._lifecycle_hooks),
            },
            "component_metadata": self._component_metadata,
            "active_instances": {component_id: instance.get_component_info() for component_id, instance in self._instances.items()},
            "state_summary": MobileStateManager.get_state_summary(),
            "navigation_info": self.get_ai_navigation_info(),
            "discovery_info": self.discover_components_for_ai(),
            "testing_capabilities": self._get_testing_endpoints(),
        }

    def validate_components(self) -> dict[str, Any]:
        """Validate all registered components for AI agent testing."""
        validation_results: dict[str, Any] = {
            "valid_components": [],
            "invalid_components": [],
            "missing_implementations": [],
            "validation_errors": [],
        }

        for component_type, metadata in self._component_metadata.items():
            try:
                if component_type in self._components:
                    # Component is registered
                    component_class = self._components[component_type]

                    # Check if it's a proper MobileComponent subclass
                    if issubclass(component_class, MobileComponent):
                        validation_results["valid_components"].append(component_type)
                    else:
                        validation_results["invalid_components"].append({"component_type": component_type, "error": "Not a MobileComponent subclass"})
                else:
                    # Component metadata exists but no implementation
                    validation_results["missing_implementations"].append(component_type)

            except Exception as e:
                validation_results["validation_errors"].append({"component_type": component_type, "error": str(e)})

        return validation_results

    def _setup_ai_navigation_map(self) -> None:
        """Setup navigation map for AI agent understanding."""
        self._ai_navigation_map = {
            "input_components": {
                "camera_input": {
                    "purpose": "Capture plant images using device camera",
                    "interaction": "touch_button",
                    "css_selectors": [".mobile-camera-input", "[data-testid='camera-button']"],
                    "ai_description": "Camera input for real-time plant image capture",
                },
                "upload_input": {
                    "purpose": "Upload plant images from device storage",
                    "interaction": "file_picker",
                    "css_selectors": [".mobile-upload-input", "[data-testid='upload-button']"],
                    "ai_description": "File upload for plant image selection",
                },
                "voice_input": {
                    "purpose": "Record voice questions about plants",
                    "interaction": "touch_and_hold",
                    "css_selectors": [".mobile-voice-input", "[data-testid='voice-button']"],
                    "ai_description": "Voice input for plant care questions",
                },
                "text_input": {
                    "purpose": "Type text questions about plants",
                    "interaction": "text_input",
                    "css_selectors": [".mobile-text-input", "[data-testid='text-input']"],
                    "ai_description": "Text input for plant care chat",
                },
            },
            "display_components": {
                "analysis_display": {
                    "purpose": "Show plant disease analysis results",
                    "interaction": "view_only",
                    "css_selectors": [".mobile-analysis-display", "[data-testid='analysis-results']"],
                    "ai_description": "Display area for plant disease predictions",
                },
                "chat_interface": {
                    "purpose": "Display conversation with plant care assistant",
                    "interaction": "scrollable_view",
                    "css_selectors": [".mobile-chat-interface", "[data-testid='chat-history']"],
                    "ai_description": "Chat interface for plant care assistance",
                },
                "history_view": {
                    "purpose": "Show previous plant analyses",
                    "interaction": "scrollable_list",
                    "css_selectors": [".mobile-history-view", "[data-testid='analysis-history']"],
                    "ai_description": "History of plant disease analyses",
                },
            },
            "navigation_patterns": {
                "main_flow": ["input_selection", "analysis_display", "chat_interaction"],
                "alternative_flows": ["history_review", "settings_access"],
                "error_recovery": ["retry_analysis", "clear_error", "reset_component"],
            },
        }

    def _register_component_for_ai_navigation(self, component_id: str, component_type: str, instance: MobileComponent) -> None:
        """Register component in AI navigation system."""
        navigation_info = self._get_navigation_info_for_type(component_type)

        # Store navigation information for AI agent
        if "ai_navigation" not in st.session_state:
            st.session_state["ai_navigation"] = {}

        st.session_state["ai_navigation"][component_id] = {
            "component_type": component_type,
            "component_id": component_id,
            "title": instance.title,
            "navigation_info": navigation_info,
            "css_classes": instance.get_css_classes(),
            "ai_metadata": instance.get_ai_metadata(),
            "registered_at": datetime.now().isoformat(),
            "status": "active",
        }

    def _get_navigation_info_for_type(self, component_type: str) -> dict[str, Any]:
        """Get navigation information for a component type."""
        # Check input components
        for category, components in self._ai_navigation_map.items():
            if isinstance(components, dict) and component_type in components:
                return components[component_type]

        # Return default navigation info
        return {
            "purpose": f"Mobile {component_type.replace('_', ' ')} component",
            "interaction": "touch",
            "css_selectors": [f".mobile-{component_type}"],
            "ai_description": f"Mobile component for {component_type.replace('_', ' ')}",
        }

    def register_lifecycle_hook(self, hook_type: str, component_type: str, callback: Any) -> None:
        """Register lifecycle hook for component management."""
        if hook_type not in self._lifecycle_hooks:
            self._lifecycle_hooks[hook_type] = {}

        if component_type not in self._lifecycle_hooks[hook_type]:
            self._lifecycle_hooks[hook_type][component_type] = []

        self._lifecycle_hooks[hook_type][component_type].append(callback)
        logger.info(f"Registered {hook_type} hook for {component_type}")

    def _execute_lifecycle_hook(self, hook_type: str, component_type: str, component_id: str, **kwargs) -> None:
        """Execute lifecycle hooks for component management."""
        if hook_type in self._lifecycle_hooks and component_type in self._lifecycle_hooks[hook_type]:
            for callback in self._lifecycle_hooks[hook_type][component_type]:
                try:
                    callback(component_id, **kwargs)
                except Exception as e:
                    logger.error(f"Lifecycle hook {hook_type} failed for {component_id}: {e}")

    def get_ai_navigation_info(self) -> dict[str, Any]:
        """Get comprehensive navigation information for AI agents."""
        return {
            "navigation_map": self._ai_navigation_map,
            "active_components": st.session_state.get("ai_navigation", {}),
            "component_discovery": self.discover_components_for_ai(),
            "interaction_patterns": self._get_interaction_patterns(),
            "testing_endpoints": self._get_testing_endpoints(),
        }

    def discover_components_for_ai(self) -> dict[str, Any]:
        """Discover available components for AI agent testing."""
        discovery_info = {
            "available_types": list(self._components.keys()),
            "active_instances": list(self._instances.keys()),
            "component_capabilities": {},
            "testing_methods": {},
        }

        for component_type, metadata in self._component_metadata.items():
            discovery_info["component_capabilities"][component_type] = {
                "description": metadata.get("description", ""),
                "ai_compatible": metadata.get("ai_agent_compatible", False),
                "touch_optimized": metadata.get("touch_optimized", False),
                "testing_available": metadata.get("status") != "placeholder",
            }

            # Add testing methods for each component type
            discovery_info["testing_methods"][component_type] = {
                "create_test": f"registry.create_component('{component_type}', 'test_id', 'Test Component')",
                "state_test": "MobileStateManager.get_component_state('test_id')",
                "render_test": "component.render()",
                "cleanup_test": "registry.remove_component('test_id')",
            }

        return discovery_info

    def _get_interaction_patterns(self) -> dict[str, Any]:
        """Get interaction patterns for AI agent understanding."""
        return {
            "touch_interactions": {
                "tap": "Single touch on interactive elements",
                "long_press": "Hold touch for voice recording",
                "swipe": "Swipe gestures for navigation",
                "scroll": "Vertical scroll for lists and history",
            },
            "input_patterns": {
                "image_input": ["camera_capture", "file_upload"],
                "voice_input": ["record_start", "record_stop", "transcription"],
                "text_input": ["type_message", "send_message"],
            },
            "feedback_patterns": {
                "loading": "Visual loading indicators during processing",
                "error": "Error messages with recovery suggestions",
                "success": "Confirmation of successful operations",
            },
        }

    def _get_testing_endpoints(self) -> dict[str, Any]:
        """Get testing endpoints for AI agent validation."""
        return {
            "component_creation": "registry.create_component(type, id, title)",
            "state_management": "MobileStateManager.get_component_state(id)",
            "error_handling": "MobileStateManager.set_error_state(id, error)",
            "lifecycle_management": "registry.remove_component(id)",
            "validation": "registry.validate_components()",
            "ai_info": "registry.get_ai_agent_info()",
        }

    def test_component_discovery(self) -> dict[str, Any]:
        """Test component discovery for AI agent validation."""
        test_results = {
            "discovery_test": "passed",
            "available_components": len(self._components),
            "registered_instances": len(self._instances),
            "ai_navigation_entries": len(st.session_state.get("ai_navigation", {})),
            "test_timestamp": datetime.now().isoformat(),
            "errors": [],
        }

        try:
            # Test component creation for each type
            for component_type in self._components.keys():
                test_id = f"ai_test_{component_type}"
                component = self.create_component(component_type, test_id, f"AI Test {component_type}")

                if component:
                    # Test state management
                    state = MobileStateManager.get_component_state(test_id)
                    if not state.get("initialized"):
                        test_results["errors"].append(f"State not initialized for {component_type}")

                    # Cleanup test component
                    self.remove_component(test_id)
                else:
                    test_results["errors"].append(f"Failed to create component: {component_type}")

        except Exception as e:
            test_results["discovery_test"] = "failed"
            test_results["errors"].append(f"Discovery test error: {e!s}")

        return test_results

    def get_component_lifecycle_info(self, component_id: str) -> dict[str, Any]:
        """Get lifecycle information for a specific component."""
        if component_id not in self._instances:
            return {"error": "Component not found"}

        instance = self._instances[component_id]
        state = MobileStateManager.get_component_state(component_id)
        navigation_info = st.session_state.get("ai_navigation", {}).get(component_id, {})

        return {
            "component_id": component_id,
            "component_type": instance.component_type,
            "title": instance.title,
            "created_at": instance.created_at,
            "state_summary": {
                "initialized": state.get("initialized"),
                "last_updated": state.get("last_updated"),
                "has_error": state.get("error") is not None,
                "loading": state.get("loading"),
                "visible": state.get("visible"),
            },
            "navigation_info": navigation_info,
            "lifecycle_hooks": len(self._lifecycle_hooks.get("post_create", {}).get(instance.component_type, [])),
            "ai_metadata": instance.get_ai_metadata(),
        }


class MobileComponentFactory:
    """Factory for creating mobile components with standardized patterns."""

    def __init__(self, registry: MobileComponentRegistry):
        """Initialize component factory."""
        self.registry = registry

    def create_input_component(self, input_type: str, component_id: str, title: str, **kwargs) -> MobileComponent | None:
        """Create an input component (camera, upload, voice, text)."""
        component_type = f"{input_type}_input"
        return self.registry.create_component(component_type, component_id, title, **kwargs)

    def create_display_component(self, display_type: str, component_id: str, title: str, **kwargs) -> MobileComponent | None:
        """Create a display component (analysis, chat, history)."""
        component_type = f"{display_type}_display" if not display_type.endswith("_display") else display_type
        return self.registry.create_component(component_type, component_id, title, **kwargs)

    def create_standard_layout(self) -> dict[str, MobileComponent]:
        """Create a standard mobile layout with all core components."""
        components = {}

        # Input components for 2x2 grid
        input_components = [("camera", "Camera"), ("upload", "Upload"), ("voice", "Voice"), ("text", "Text")]

        for input_type, title in input_components:
            component = self.create_input_component(input_type, f"main_{input_type}_input", f"{title} Input")
            if component:
                components[f"{input_type}_input"] = component

        # Display components
        display_components = [("analysis", "Analysis Results"), ("chat", "Chat Interface"), ("history", "Analysis History")]

        for display_type, title in display_components:
            component = self.create_display_component(display_type, f"main_{display_type}_display", title)
            if component:
                components[f"{display_type}_display"] = component

        return components


# Global registry instance
_mobile_registry: MobileComponentRegistry | None = None


def get_mobile_registry() -> MobileComponentRegistry:
    """Get or create the global mobile component registry."""
    global _mobile_registry
    if _mobile_registry is None:
        _mobile_registry = MobileComponentRegistry()
    return _mobile_registry


def get_mobile_factory() -> MobileComponentFactory:
    """Get mobile component factory."""
    registry = get_mobile_registry()
    return MobileComponentFactory(registry)


def initialize_mobile_components() -> dict[str, Any]:
    """Initialize mobile component system and return status."""
    try:
        registry = get_mobile_registry()
        factory = get_mobile_factory()

        # Validate components
        validation_results = registry.validate_components()

        return {
            "status": "initialized",
            "registry": registry,
            "factory": factory,
            "validation": validation_results,
            "ai_agent_info": registry.get_ai_agent_info(),
        }

    except Exception as e:
        logger.error(f"Failed to initialize mobile components: {e}")
        return {"status": "error", "error": str(e)}
