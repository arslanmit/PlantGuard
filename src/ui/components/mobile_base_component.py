"""
Base Mobile Component for PlantGuard UI.

This module provides the base class for all mobile components with
standardized interfaces for AI agent understanding and interaction.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import streamlit as st

from .mobile_error_handler import ErrorCategory, ErrorSeverity, MobileErrorHandler
from .mobile_state_manager import MobileStateManager

logger = logging.getLogger(__name__)


class MobileBaseComponent(ABC):
    """
    Base class for all mobile components.

    Provides standardized interface for AI agent understanding and
    consistent error handling across all mobile components.
    """

    def __init__(self, component_id: str, title: str, **kwargs) -> None:
        """
        Initialize base mobile component.

        Args:
            component_id: Unique identifier for this component instance
            title: Display title for the component
            **kwargs: Additional component-specific arguments
        """
        self.component_id = component_id
        self.title = title
        self.component_type = self.__class__.__name__.lower()

        # Initialize managers
        self.state_manager = MobileStateManager()
        self.error_handler = MobileErrorHandler(self.state_manager)

        # Component metadata for AI agent discovery
        self._component_metadata = {
            "component_id": component_id,
            "component_type": self.component_type,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "ai_discoverable": True,
            "css_classes": self._generate_css_classes(),
            "state_key": f"mobile_{component_id}_state",
            "error_key": f"mobile_error_{component_id}",
            **kwargs,
        }

        # Initialize component state
        self._initialize_component_state()

        # Register with error handler
        self._register_error_handlers()

        logger.debug(f"Initialized mobile component: {self.component_type}[{component_id}]")

    @abstractmethod
    def render(self) -> None:
        """
        Render the component UI.

        This method must be implemented by all mobile components.
        """
        pass

    def get_state(self) -> dict[str, Any]:
        """
        Get current component state.

        Returns:
            Component state dictionary
        """
        return self.state_manager.get_component_state(self.component_id)

    def set_state(self, state: dict[str, Any]) -> None:
        """
        Set component state.

        Args:
            state: State dictionary to set
        """
        self.state_manager.set_component_state(self.component_id, state)

    def update_state(self, updates: dict[str, Any]) -> None:
        """
        Update specific fields in component state.

        Args:
            updates: Dictionary of fields to update
        """
        self.state_manager.update_component_state(self.component_id, updates)

    def clear_state(self) -> None:
        """Clear component state."""
        self.state_manager.clear_component_state(self.component_id)

    def get_ui_state(self) -> dict[str, Any]:
        """
        Get UI-specific state (visibility, loading, etc.).

        Returns:
            UI state dictionary
        """
        state = self.get_state()
        return state.get("ui_state", {})

    def set_ui_state(self, ui_updates: dict[str, Any]) -> None:
        """
        Update UI-specific state.

        Args:
            ui_updates: UI state updates
        """
        current_state = self.get_state()
        if "ui_state" not in current_state:
            current_state["ui_state"] = {}

        current_state["ui_state"].update(ui_updates)
        self.set_state(current_state)

    def is_visible(self) -> bool:
        """Check if component is visible."""
        ui_state = self.get_ui_state()
        return ui_state.get("visible", True)

    def set_visible(self, visible: bool) -> None:
        """Set component visibility."""
        self.set_ui_state({"visible": visible})

    def is_loading(self) -> bool:
        """Check if component is in loading state."""
        ui_state = self.get_ui_state()
        return ui_state.get("loading", False)

    def set_loading(self, loading: bool) -> None:
        """Set component loading state."""
        self.set_ui_state({"loading": loading})

    def is_disabled(self) -> bool:
        """Check if component is disabled."""
        ui_state = self.get_ui_state()
        return ui_state.get("disabled", False)

    def set_disabled(self, disabled: bool) -> None:
        """Set component disabled state."""
        self.set_ui_state({"disabled": disabled})

    def has_error(self) -> bool:
        """Check if component has an error."""
        state = self.get_state()
        return state.get("error") is not None

    def get_error(self) -> str | None:
        """Get current error message."""
        state = self.get_state()
        return state.get("error")

    def clear_error(self) -> None:
        """Clear component error."""
        self.error_handler.clear_component_errors(self.component_id)

    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.COMPONENT,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: str | None = None,
    ) -> None:
        """
        Handle component error with recovery.

        Args:
            error: Exception that occurred
            category: Error category
            severity: Error severity
            user_message: Custom user message
        """
        self.error_handler.handle_component_error(
            component_id=self.component_id, error=error, category=category, severity=severity, user_message=user_message
        )

    def validate_input(self, input_data: Any) -> dict[str, Any]:
        """
        Validate component input.

        Args:
            input_data: Input data to validate

        Returns:
            Validation result dictionary
        """
        validation_result = {"is_valid": True, "errors": [], "warnings": []}

        # Basic validation - can be overridden by subclasses
        if input_data is None:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Input cannot be empty")

        return validation_result

    def render_with_error_handling(self) -> None:
        """
        Render component with error handling wrapper.

        This method wraps the render() method with error handling
        and provides fallback rendering if the main render fails.
        """
        try:
            # Check if component should be visible
            if not self.is_visible():
                return

            # Check if component has errors
            if self.has_error():
                self._render_error_state()
                return

            # Check if component is loading
            if self.is_loading():
                self._render_loading_state()
                return

            # Render main component
            self.render()

        except Exception as e:
            logger.error(f"Component rendering failed [{self.component_id}]: {e}")
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)
            self._render_fallback()

    def get_css_classes(self) -> list[str]:
        """
        Get CSS classes for this component.

        Returns:
            List of CSS classes
        """
        return self._component_metadata["css_classes"]

    def get_css_selector(self) -> str:
        """
        Get CSS selector for this component.

        Returns:
            CSS selector string
        """
        classes = self.get_css_classes()
        return "." + ".".join(classes)

    def get_metadata(self) -> dict[str, Any]:
        """
        Get component metadata for AI agent discovery.

        Returns:
            Component metadata dictionary
        """
        return self._component_metadata.copy()

    def update_metadata(self, updates: dict[str, Any]) -> None:
        """
        Update component metadata.

        Args:
            updates: Metadata updates
        """
        self._component_metadata.update(updates)

    def _initialize_component_state(self) -> None:
        """Initialize component state with default values."""
        default_state = {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "initialized": True,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "error": None,
            "data": {},
            "ui_state": {"visible": True, "loading": False, "disabled": False, "expanded": False},
            "validation": {"is_valid": True, "errors": [], "warnings": []},
            "metadata": self._component_metadata,
        }

        # Only set if state doesn't exist
        existing_state = self.state_manager.get_component_state(self.component_id)
        if not existing_state.get("initialized"):
            self.state_manager.set_component_state(self.component_id, default_state)

    def _generate_css_classes(self) -> list[str]:
        """
        Generate CSS classes for AI agent recognition.

        Returns:
            List of CSS classes
        """
        base_type = self.component_type.replace("_", "-")
        safe_id = self.component_id.replace("_", "-")

        css_classes = [
            "mobile-component",
            f"mobile-{base_type}",
            f"mobile-{base_type}-{safe_id}",
            "ai-discoverable",
            f"component-type-{base_type}",
            f"component-id-{safe_id}",
        ]

        return css_classes

    def _register_error_handlers(self) -> None:
        """Register component-specific error handlers."""
        # Register fallback renderer for this component type
        self.error_handler.register_fallback_component(self.component_type, self._render_fallback)

    def _render_loading_state(self) -> None:
        """Render loading state."""
        css_classes = " ".join([*self.get_css_classes(), "loading"])

        st.markdown(
            f"""
        <div class="{css_classes}">
            <div class="mobile-loading">
                <div class="mobile-spinner"></div>
                <span>Loading {self.title}...</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_error_state(self) -> None:
        """Render error state."""
        error_message = self.get_error()
        css_classes = " ".join([*self.get_css_classes(), "error"])

        st.markdown(
            f"""
        <div class="{css_classes}">
            <div class="mobile-error">
                <div class="mobile-error-title">[WARNING] {self.title} Error</div>
                <p>{error_message}</p>
                <button onclick="window.location.reload()" class="mobile-button mobile-button-secondary">
                    [PARTIAL] Retry
                </button>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_fallback(self) -> None:
        """Render fallback UI when main rendering fails."""
        css_classes = " ".join([*self.get_css_classes(), "fallback"])

        st.markdown(
            f"""
        <div class="{css_classes}">
            <div class="mobile-card mobile-fallback">
                <h4>[WARNING] {self.title} Unavailable</h4>
                <p>This component is temporarily unavailable. Please try refreshing the page.</p>
                <button onclick="window.location.reload()" class="mobile-button mobile-button-primary">
                    [PARTIAL] Refresh Page
                </button>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def __str__(self) -> str:
        """String representation of component."""
        return f"{self.component_type}[{self.component_id}]"

    def __repr__(self) -> str:
        """Detailed string representation of component."""
        return f"{self.__class__.__name__}(component_id='{self.component_id}', title='{self.title}')"
