"""
Mobile State Manager for PlantGuard UI.

This module provides state management capabilities for mobile components.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MobileStateManager:
    """State manager for mobile components."""

    def __init__(self):
        self.state = {}

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        return self.state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """Set state value."""
        self.state[key] = value

    def clear_state(self) -> None:
        """Clear all state."""
        self.state.clear()
