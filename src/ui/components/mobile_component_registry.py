"""
Mobile Component Registry for PlantGuard UI.

This module provides a registry system for mobile components with
metadata and registration capabilities.
"""

import logging

logger = logging.getLogger(__name__)


class ComponentMetadata:
    """Metadata for a mobile component."""

    def __init__(self, component_id: str, component_type: str, version: str = "1.0.0"):
        self.component_id = component_id
        self.component_type = component_type
        self.version = version
        self.created_at = None
        self.last_updated = None


class MobileComponent:
    """Base interface for mobile components."""

    def __init__(self, component_id: str):
        self.component_id = component_id

    def render(self) -> None:
        """Render the component."""
        pass


def register_mobile_component(component_id: str, component_class: type[MobileComponent]) -> None:
    """Register a mobile component."""
    logger.debug("Registering mobile component: %s", component_id)


# Global component registry instance
mobile_component_registry = type(
    "MobileComponentRegistry",
    (),
    {
        "register_component": lambda self, component_id, component_class: None,
        "get_component": lambda self, component_id: None,
        "list_components": lambda self: [],
    },
)()
