"""
Mobile Components Package for PlantGuard UI.

This package provides mobile-optimized components with AI agent support
and comprehensive error handling for the PlantGuard plant disease detection system.
"""

# Core infrastructure components
# Base component class
from .mobile_base_component import MobileBaseComponent
from .mobile_component_registry import MobileComponentRegistry
from .mobile_error_handler import ErrorCategory, ErrorInfo, ErrorSeverity, MobileErrorHandler
from .mobile_layout_manager import MobileLayoutManager
from .mobile_state_manager import MobileStateManager, StateEntry, StateType

# Test component for validation
from .mobile_test_component import MobileTestComponent

# Version information
__version__ = "1.0.0"
__author__ = "PlantGuard Development Team"

# Component registry for AI agent discovery
MOBILE_COMPONENT_TYPES = {
    "layout_manager": MobileLayoutManager,
    "test_component": MobileTestComponent,
}

# AI Agent Discovery Information
AI_AGENT_INFO = {
    "package_name": "mobile_components",
    "version": __version__,
    "component_base_class": "MobileBaseComponent",
    "state_manager": "MobileStateManager",
    "error_handler": "MobileErrorHandler",
    "css_naming_convention": "mobile-{component-type}-{element}",
    "state_key_pattern": "mobile_{component_id}_state",
    "error_key_pattern": "mobile_error_{component_id}",
    "required_methods": ["render", "get_state", "set_state"],
    "optional_methods": ["validate_input", "handle_error", "clear_state"],
    "css_classes_pattern": [
        "mobile-component",
        "mobile-{component-type}",
        "mobile-{component-type}-{component-id}",
        "ai-discoverable",
        "component-type-{component-type}",
        "component-id-{component-id}",
    ],
}

# Export all public components and utilities
__all__ = [
    # Core infrastructure
    "MobileLayoutManager",
    "MobileComponentRegistry",
    "MobileStateManager",
    "MobileErrorHandler",
    # Base classes
    "MobileBaseComponent",
    # Test components
    "MobileTestComponent",
    # Enums and data classes
    "StateType",
    "StateEntry",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorInfo",
    # Registry and discovery
    "MOBILE_COMPONENT_TYPES",
    "AI_AGENT_INFO",
    # Version info
    "__version__",
    "__author__",
]


def create_mobile_app() -> MobileLayoutManager:
    """
    Create and configure a mobile PlantGuard application.

    Returns:
        Configured MobileLayoutManager instance
    """
    # Create layout manager
    layout_manager = MobileLayoutManager()

    # Register available components
    for component_type, component_class in MOBILE_COMPONENT_TYPES.items():
        layout_manager.register_component(component_type, component_class)

    return layout_manager


def get_component_registry() -> MobileComponentRegistry:
    """
    Get a configured component registry.

    Returns:
        MobileComponentRegistry with all available components
    """
    registry = MobileComponentRegistry()

    # Register all available components
    for component_type, component_class in MOBILE_COMPONENT_TYPES.items():
        registry.register_component(component_type, component_class)

    return registry


def validate_mobile_infrastructure() -> dict:
    """
    Validate mobile infrastructure for AI agent testing.

    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "infrastructure_available": True,
        "components_registered": len(MOBILE_COMPONENT_TYPES),
        "base_class_available": MobileBaseComponent is not None,
        "state_manager_available": MobileStateManager is not None,
        "error_handler_available": MobileErrorHandler is not None,
        "layout_manager_available": MobileLayoutManager is not None,
        "component_registry_available": MobileComponentRegistry is not None,
        "ai_discovery_info_available": bool(AI_AGENT_INFO),
        "css_system_available": True,  # CSS is embedded in layout manager
        "test_component_available": MobileTestComponent is not None,
    }

    # Check if all core components are properly imported
    try:
        # Test instantiation of core components
        state_manager = MobileStateManager()
        error_handler = MobileErrorHandler()
        registry = MobileComponentRegistry()

        validation_results["core_components_functional"] = True

    except Exception as e:
        validation_results["core_components_functional"] = False
        validation_results["error"] = str(e)

    return validation_results


# Initialize logging for the mobile components package
import logging

logger = logging.getLogger(__name__)
logger.info(f"Mobile Components Package v{__version__} initialized")
logger.debug(f"Available component types: {list(MOBILE_COMPONENT_TYPES.keys())}")
