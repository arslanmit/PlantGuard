"""
Mobile Component Registry for PlantGuard UI.

This module provides component registration and factory functionality
for AI agent navigation and dynamic component creation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


@dataclass
class ComponentMetadata:
    """Metadata for mobile components to support AI agent understanding."""

    component_id: str
    component_type: str
    display_name: str
    description: str
    ai_agent_friendly_description: str
    interactive_elements: list[dict[str, Any]]
    state_dependencies: list[str]
    css_classes: list[str]
    test_scenarios: list[dict[str, Any]]
    ai_agent_instructions: dict[str, str]
    version: str
    ai_agent_testable: bool = True
    auto_fix_enabled: bool = True


class MobileComponent:
    """Base class for all mobile components with AI agent support."""

    def __init__(self, component_id: str, **kwargs):
        """Initialize mobile component with AI agent support."""
        self.component_id = component_id
        self.kwargs = kwargs
        self._initialized = False
        self._state_key = f"mobile_{component_id}_state"

    def render(self, **kwargs) -> None:
        """Render the component. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement render method")

    def get_state(self) -> dict[str, Any]:
        """Get component state from session state."""
        return st.session_state.get(self._state_key, {})

    def set_state(self, state: dict[str, Any]) -> None:
        """Set component state in session state."""
        st.session_state[self._state_key] = state

    def clear_state(self) -> None:
        """Clear component state."""
        if self._state_key in st.session_state:
            del st.session_state[self._state_key]

    def _get_component_metadata(self) -> ComponentMetadata:
        """Get component metadata. Should be overridden by subclasses."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="base_component",
            display_name="Base Mobile Component",
            description="Base class for mobile components",
            ai_agent_friendly_description="Base mobile component class",
            interactive_elements=[],
            state_dependencies=[],
            css_classes=["mobile-component"],
            test_scenarios=[],
            ai_agent_instructions={},
            version="1.0.0",
        )


def register_mobile_component(component_class):
    """Decorator to register a mobile component class."""

    def wrapper(*args, **kwargs):
        # Get the global registry instance
        if not hasattr(register_mobile_component, "_registry"):
            register_mobile_component._registry = MobileComponentRegistry()

        registry = register_mobile_component._registry

        # Register the component class
        component_type = component_class.__name__.lower().replace("mobile", "").replace("component", "")
        if component_type.startswith("_"):
            component_type = component_type[1:]

        registry.register_component(component_type, component_class)

        return component_class(*args, **kwargs)

    # Store the original class for direct access
    wrapper._component_class = component_class
    return wrapper


class MobileComponentRegistry:
    """Registry for managing mobile components with AI agent support."""

    def __init__(self):
        """Initialize component registry with base components."""
        self._components: dict[str, type] = {}
        self._component_metadata: dict[str, dict[str, Any]] = {}
        self._initialization_order: list[str] = []
        self._ai_agent_patterns: dict[str, dict[str, Any]] = {}

        # Initialize with base component patterns for AI agent recognition
        self._setup_ai_agent_patterns()

    def register_component(self, component_type: str, component_class: type, metadata: dict[str, Any] | None = None) -> None:
        """
        Register a new mobile component type.

        Args:
            component_type: Unique identifier for the component type
            component_class: Class implementing the component
            metadata: Optional metadata for AI agent understanding
        """
        try:
            if component_type in self._components:
                logger.warning(f"Component type '{component_type}' already registered, overwriting")

            self._components[component_type] = component_class
            self._initialization_order.append(component_type)

            # Store metadata for AI agent navigation
            self._component_metadata[component_type] = {
                "class_name": component_class.__name__,
                "module": component_class.__module__,
                "registered_at": datetime.now().isoformat(),
                "ai_discoverable": True,
                "css_prefix": f"mobile-{component_type.replace('_', '-')}",
                **(metadata or {}),
            }

            logger.info(f"Registered mobile component: {component_type}")

        except Exception as e:
            logger.error(f"Failed to register component {component_type}: {e}")
            raise

    def create_component(self, component_type: str, component_id: str, title: str, **kwargs) -> Any:
        """
        Create a component instance using the factory pattern.

        Args:
            component_type: Type of component to create
            component_id: Unique identifier for this instance
            title: Display title for the component
            **kwargs: Additional arguments for component initialization

        Returns:
            Component instance

        Raises:
            ValueError: If component type is not registered
        """
        if component_type not in self._components:
            available_types = list(self._components.keys())
            raise ValueError(f"Unknown component type: {component_type}. Available types: {available_types}")

        try:
            component_class = self._components[component_type]

            # Create component with standard interface
            component = component_class(component_id=component_id, title=title, **kwargs)

            # Add AI agent discoverable attributes
            component._component_type = component_type
            component._registry_metadata = self._component_metadata[component_type]
            component._css_classes = self._generate_css_classes(component_type, component_id)

            logger.debug(f"Created component: {component_type}[{component_id}]")
            return component

        except Exception as e:
            logger.error(f"Failed to create component {component_type}[{component_id}]: {e}")
            raise

    def get_available_components(self) -> list[str]:
        """Get list of available component types."""
        return list(self._components.keys())

    def get_component_metadata(self, component_type: str) -> dict[str, Any]:
        """Get metadata for a specific component type."""
        if component_type not in self._component_metadata:
            raise ValueError(f"Component type not found: {component_type}")
        return self._component_metadata[component_type].copy()

    def get_all_metadata(self) -> dict[str, dict[str, Any]]:
        """Get metadata for all registered components."""
        return self._component_metadata.copy()

    def get_initialization_order(self) -> list[str]:
        """Get the order in which components were registered."""
        return self._initialization_order.copy()

    def discover_components_for_ai_agent(self) -> dict[str, Any]:
        """
        Provide component discovery information for AI agents.

        Returns:
            Dictionary with component discovery information
        """
        discovery_info = {
            "available_components": self.get_available_components(),
            "component_patterns": self._ai_agent_patterns,
            "css_naming_convention": "mobile-{component-type}-{element}",
            "standard_interface": {
                "constructor": "(component_id: str, title: str, **kwargs)",
                "required_methods": ["render()", "get_state()", "set_state()"],
                "css_classes": "mobile-{type}, mobile-{type}-{id}",
                "state_key_pattern": "mobile_{component_id}_state",
            },
            "metadata": self.get_all_metadata(),
        }

        return discovery_info

    def validate_component_interface(self, component_type: str) -> dict[str, bool]:
        """
        Validate that a component follows the expected interface.

        Args:
            component_type: Component type to validate

        Returns:
            Dictionary with validation results
        """
        if component_type not in self._components:
            return {"valid": False, "error": "Component type not registered"}

        component_class = self._components[component_type]
        validation_results = {
            "valid": True,
            "has_render_method": hasattr(component_class, "render"),
            "has_constructor": hasattr(component_class, "__init__"),
            "follows_naming_convention": component_type.startswith("mobile_") or "mobile" in component_type.lower(),
            "has_metadata": component_type in self._component_metadata,
        }

        # Check if all required methods exist
        required_methods = ["render"]
        for method in required_methods:
            if not hasattr(component_class, method):
                validation_results["valid"] = False
                validation_results[f"missing_{method}"] = True

        return validation_results

    def _setup_ai_agent_patterns(self) -> None:
        """Setup patterns for AI agent component recognition."""
        self._ai_agent_patterns = {
            "input_components": {
                "pattern": "mobile_*_input",
                "description": "Components that handle user input",
                "css_pattern": ".mobile-input-*",
                "expected_methods": ["render", "handle_input", "validate_input"],
            },
            "display_components": {
                "pattern": "mobile_*_display",
                "description": "Components that display information",
                "css_pattern": ".mobile-display-*",
                "expected_methods": ["render", "update_content", "clear_content"],
            },
            "interface_components": {
                "pattern": "mobile_*_interface",
                "description": "Components that provide user interfaces",
                "css_pattern": ".mobile-interface-*",
                "expected_methods": ["render", "handle_interaction", "get_state"],
            },
            "layout_components": {
                "pattern": "mobile_*_layout",
                "description": "Components that manage layout and structure",
                "css_pattern": ".mobile-layout-*",
                "expected_methods": ["render", "add_child", "remove_child"],
            },
        }

    def _generate_css_classes(self, component_type: str, component_id: str) -> list[str]:
        """
        Generate standardized CSS classes for AI agent recognition.

        Args:
            component_type: Type of the component
            component_id: Unique identifier for the component instance

        Returns:
            List of CSS classes
        """
        base_type = component_type.replace("_", "-")
        safe_id = component_id.replace("_", "-")

        css_classes = ["mobile-component", f"mobile-{base_type}", f"mobile-{base_type}-{safe_id}", "ai-discoverable", f"component-type-{base_type}"]

        return css_classes

    def get_component_by_css_class(self, css_class: str) -> str | None:
        """
        Find component type by CSS class for AI agent navigation.

        Args:
            css_class: CSS class to search for

        Returns:
            Component type if found, None otherwise
        """
        for component_type, metadata in self._component_metadata.items():
            css_prefix = metadata.get("css_prefix", "")
            if css_class.startswith(css_prefix):
                return component_type

        return None

    def get_components_by_pattern(self, pattern: str) -> list[str]:
        """
        Get components matching a pattern for AI agent discovery.

        Args:
            pattern: Pattern to match (supports * wildcards)

        Returns:
            List of matching component types
        """
        import fnmatch

        matching_components = []
        for component_type in self._components:
            if fnmatch.fnmatch(component_type, pattern):
                matching_components.append(component_type)

        return matching_components

    def clear_registry(self) -> None:
        """Clear all registered components (for testing)."""
        self._components.clear()
        self._component_metadata.clear()
        self._initialization_order.clear()
        logger.info("Component registry cleared")

    def get_registry_stats(self) -> dict[str, Any]:
        """Get statistics about the component registry."""
        return {
            "total_components": len(self._components),
            "component_types": list(self._components.keys()),
            "registration_order": self._initialization_order,
            "ai_patterns_count": len(self._ai_agent_patterns),
            "last_registration": self._initialization_order[-1] if self._initialization_order else None,
        }

    def get_all_components(self) -> dict[str, type]:
        """Get all registered components."""
        return self._components.copy()


# Global registry instance
mobile_component_registry = MobileComponentRegistry()
