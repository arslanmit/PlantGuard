"""
Mobile Components Package for PlantGuard UI.

This package provides mobile-optimized components with AI agent support
and comprehensive error handling for the PlantGuard plant disease detection system.
"""

import logging
from typing import Any

# Version information
__version__ = "1.0.0"
__author__ = "PlantGuard Development Team"

# AI Agent Discovery Information
AI_AGENT_INFO = {
    "package_name": "mobile_components",
    "version": __version__,
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
    "AI_AGENT_INFO",
    "__author__",
    "__version__",
]

# Initialize logging for the mobile components package
logger = logging.getLogger(__name__)
logger.info(f"Mobile Components Package v{__version__} initialized")
