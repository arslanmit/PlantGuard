"""
Mobile Error Handler for PlantGuard UI.

This module provides comprehensive error handling and recovery mechanisms
for mobile components with graceful degradation capabilities.
"""

import logging
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import streamlit as st

from .mobile_state_manager import MobileStateManager

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling."""

    COMPONENT = "component"
    NETWORK = "network"
    VALIDATION = "validation"
    PERMISSION = "permission"
    RESOURCE = "resource"
    INTEGRATION = "integration"
    USER_INPUT = "user_input"
    SYSTEM = "system"


@dataclass
class ErrorInfo:
    """Structured error information."""

    error_id: str
    component_id: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: str
    stack_trace: str | None = None
    recovery_suggestions: list[str] | None = None
    user_message: str | None = None
    metadata: dict[str, Any] | None = None


class MobileErrorHandler:
    """Centralized error handling for mobile components with graceful degradation."""

    def __init__(self, state_manager: MobileStateManager | None = None):
        """
        Initialize error handler.

        Args:
            state_manager: Optional state manager instance
        """
        self.state_manager = state_manager or MobileStateManager()
        self._error_count = 0
        self._error_history: list[ErrorInfo] = []
        self._recovery_strategies: dict[ErrorCategory, Callable] = {}
        self._fallback_components: dict[str, Callable] = {}

        # Setup default recovery strategies
        self._setup_default_recovery_strategies()

        # Setup default fallback components
        self._setup_default_fallbacks()

    def handle_component_error(
        self,
        component_id: str,
        error: Exception,
        category: ErrorCategory = ErrorCategory.COMPONENT,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: str | None = None,
    ) -> None:
        """
        Handle component-specific errors with recovery.

        Args:
            component_id: Component identifier
            error: Exception that occurred
            category: Error category
            severity: Error severity
            user_message: Custom user-friendly message
        """
        try:
            # Generate error ID
            error_id = f"err_{self._error_count}_{int(datetime.now().timestamp())}"
            self._error_count += 1

            # Create error info
            error_info = ErrorInfo(
                error_id=error_id,
                component_id=component_id,
                message=str(error),
                category=category,
                severity=severity,
                timestamp=datetime.now().isoformat(),
                stack_trace=traceback.format_exc(),
                recovery_suggestions=self._get_recovery_suggestions(category, error),
                user_message=user_message or self._generate_user_message(category, error),
                metadata={"error_type": type(error).__name__},
            )

            # Store error info
            self._error_history.append(error_info)

            # Update state manager
            self.state_manager.set_error_state(
                component_id=component_id,
                error_message=error_info.user_message,
                error_type=category.value,
                recovery_suggestions=error_info.recovery_suggestions,
            )

            # Log error
            log_level = self._get_log_level(severity)
            logger.log(log_level, f"Component error [{component_id}]: {error_info.message}")

            # Attempt recovery
            self._attempt_recovery(error_info)

            # Display user-friendly error
            self._display_error_to_user(error_info)

        except Exception as recovery_error:
            logger.critical(f"Error handler failed: {recovery_error}")
            self._display_critical_error()

    def handle_network_error(self, component_id: str, error: Exception) -> None:
        """Handle network-related errors."""
        self.handle_component_error(
            component_id=component_id,
            error=error,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            user_message="Network connection issue. Some features may be limited.",
        )

    def handle_validation_error(self, component_id: str, error: Exception, field_name: str | None = None) -> None:
        """Handle input validation errors."""
        user_message = "Invalid input"
        if field_name:
            user_message += f" for {field_name}"
        user_message += ". Please check your input and try again."

        self.handle_component_error(
            component_id=component_id, error=error, category=ErrorCategory.VALIDATION, severity=ErrorSeverity.LOW, user_message=user_message
        )

    def handle_permission_error(self, component_id: str, error: Exception, permission_type: str = "access") -> None:
        """Handle permission-related errors."""
        user_message = f"Permission denied for {permission_type}. Please check your browser settings."

        self.handle_component_error(
            component_id=component_id, error=error, category=ErrorCategory.PERMISSION, severity=ErrorSeverity.HIGH, user_message=user_message
        )

    def handle_resource_error(self, component_id: str, error: Exception) -> None:
        """Handle resource-related errors (memory, storage, etc.)."""
        self.handle_component_error(
            component_id=component_id,
            error=error,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            user_message="System resources are limited. Try refreshing the page or closing other tabs.",
        )

    def register_fallback_component(self, component_type: str, fallback_renderer: Callable) -> None:
        """
        Register a fallback component renderer.

        Args:
            component_type: Type of component
            fallback_renderer: Function to render fallback UI
        """
        self._fallback_components[component_type] = fallback_renderer
        logger.debug(f"Registered fallback for component type: {component_type}")

    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable) -> None:
        """
        Register a custom recovery strategy.

        Args:
            category: Error category
            strategy: Recovery function
        """
        self._recovery_strategies[category] = strategy
        logger.debug(f"Registered recovery strategy for category: {category.value}")

    def render_fallback_component(self, component_type: str, component_id: str, error_info: ErrorInfo | None = None) -> None:
        """
        Render fallback component when main component fails.

        Args:
            component_type: Type of component
            component_id: Component identifier
            error_info: Optional error information
        """
        try:
            if component_type in self._fallback_components:
                self._fallback_components[component_type](component_id, error_info)
            else:
                self._render_generic_fallback(component_id, error_info)

        except Exception as e:
            logger.error(f"Fallback component rendering failed: {e}")
            self._render_minimal_fallback(component_id)

    def clear_component_errors(self, component_id: str) -> None:
        """
        Clear all errors for a specific component.

        Args:
            component_id: Component identifier
        """
        # Clear from state manager
        self.state_manager.clear_error_state(component_id)

        # Remove from error history
        self._error_history = [error for error in self._error_history if error.component_id != component_id]

        logger.debug(f"Cleared errors for component: {component_id}")

    def get_component_errors(self, component_id: str) -> list[ErrorInfo]:
        """
        Get all errors for a specific component.

        Args:
            component_id: Component identifier

        Returns:
            List of error information
        """
        return [error for error in self._error_history if error.component_id == component_id]

    def get_error_statistics(self) -> dict[str, Any]:
        """
        Get error statistics for monitoring.

        Returns:
            Error statistics dictionary
        """
        if not self._error_history:
            return {"total_errors": 0, "by_category": {}, "by_severity": {}, "recent_errors": 0}

        # Count by category
        by_category = {}
        for error in self._error_history:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1

        # Count by severity
        by_severity = {}
        for error in self._error_history:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Count recent errors (last hour)
        recent_cutoff = datetime.now().timestamp() - 3600
        recent_errors = sum(1 for error in self._error_history if datetime.fromisoformat(error.timestamp).timestamp() > recent_cutoff)

        return {
            "total_errors": len(self._error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": recent_errors,
            "last_error": self._error_history[-1].timestamp if self._error_history else None,
        }

    def _setup_default_recovery_strategies(self) -> None:
        """Setup default recovery strategies for different error categories."""
        self._recovery_strategies = {
            ErrorCategory.COMPONENT: self._recover_component_error,
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.VALIDATION: self._recover_validation_error,
            ErrorCategory.PERMISSION: self._recover_permission_error,
            ErrorCategory.RESOURCE: self._recover_resource_error,
            ErrorCategory.INTEGRATION: self._recover_integration_error,
            ErrorCategory.USER_INPUT: self._recover_user_input_error,
            ErrorCategory.SYSTEM: self._recover_system_error,
        }

    def _setup_default_fallbacks(self) -> None:
        """Setup default fallback components."""
        self._fallback_components = {
            "input": self._render_input_fallback,
            "display": self._render_display_fallback,
            "interface": self._render_interface_fallback,
            "layout": self._render_layout_fallback,
        }

    def _attempt_recovery(self, error_info: ErrorInfo) -> None:
        """
        Attempt to recover from error using registered strategies.

        Args:
            error_info: Error information
        """
        try:
            if error_info.category in self._recovery_strategies:
                recovery_strategy = self._recovery_strategies[error_info.category]
                recovery_strategy(error_info)
            else:
                logger.warning(f"No recovery strategy for category: {error_info.category.value}")

        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")

    def _display_error_to_user(self, error_info: ErrorInfo) -> None:
        """
        Display user-friendly error message.

        Args:
            error_info: Error information
        """
        severity_colors = {
            ErrorSeverity.LOW: "#FEF3C7",
            ErrorSeverity.MEDIUM: "#FED7AA",
            ErrorSeverity.HIGH: "#FECACA",
            ErrorSeverity.CRITICAL: "#FCA5A5",
        }

        severity_icons = {ErrorSeverity.LOW: "i", ErrorSeverity.MEDIUM: "[WARNING]", ErrorSeverity.HIGH: "[TODO]", ErrorSeverity.CRITICAL: "[ALERT]"}

        color = severity_colors.get(error_info.severity, "#FEF3C7")
        icon = severity_icons.get(error_info.severity, "[WARNING]")

        st.markdown(
            f"""
        <div class="mobile-error" style="background-color: {color}; border-left: 4px solid #EF4444;">
            <div class="mobile-error-header">
                <span style="font-size: 18px;">{icon}</span>
                <strong>Something went wrong</strong>
            </div>
            <p>{error_info.user_message}</p>
            {self._render_recovery_suggestions(error_info.recovery_suggestions)}
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_recovery_suggestions(self, suggestions: list[str] | None) -> str:
        """
        Render recovery suggestions HTML.

        Args:
            suggestions: List of recovery suggestions

        Returns:
            HTML string for suggestions
        """
        if not suggestions:
            return ""

        suggestions_html = "<div class='mobile-error-suggestions'><strong>Try:</strong><ul>"
        for suggestion in suggestions:
            suggestions_html += f"<li>{suggestion}</li>"
        suggestions_html += "</ul></div>"

        return suggestions_html

    def _display_critical_error(self) -> None:
        """Display critical error when error handler itself fails."""
        st.error("[ALERT] Critical system error. Please refresh the page.")

        if st.button("[PARTIAL] Refresh Page", key="critical_error_refresh"):
            st.experimental_rerun()

    def _get_recovery_suggestions(self, category: ErrorCategory, error: Exception) -> list[str]:
        """
        Get recovery suggestions based on error category.

        Args:
            category: Error category
            error: Exception that occurred

        Returns:
            List of recovery suggestions
        """
        suggestions_map = {
            ErrorCategory.COMPONENT: [
                "Try refreshing the component",
                "Check if all required inputs are provided",
                "Clear the component state and try again",
            ],
            ErrorCategory.NETWORK: ["Check your internet connection", "Try again in a few moments", "Use offline features if available"],
            ErrorCategory.VALIDATION: ["Check your input format", "Ensure all required fields are filled", "Try with different input values"],
            ErrorCategory.PERMISSION: ["Check browser permissions", "Allow camera/microphone access if needed", "Try refreshing the page"],
            ErrorCategory.RESOURCE: ["Close other browser tabs", "Refresh the page", "Try with smaller files"],
            ErrorCategory.INTEGRATION: ["Check if all services are available", "Try again later", "Use alternative input methods"],
            ErrorCategory.USER_INPUT: ["Check your input format", "Try with different values", "Clear the input and start over"],
            ErrorCategory.SYSTEM: ["Refresh the page", "Clear browser cache", "Try in a different browser"],
        }

        return suggestions_map.get(category, ["Try refreshing the page"])

    def _generate_user_message(self, category: ErrorCategory, error: Exception) -> str:
        """
        Generate user-friendly error message.

        Args:
            category: Error category
            error: Exception that occurred

        Returns:
            User-friendly error message
        """
        messages_map = {
            ErrorCategory.COMPONENT: "A component encountered an issue. Please try again.",
            ErrorCategory.NETWORK: "Network connection issue. Some features may be limited.",
            ErrorCategory.VALIDATION: "Please check your input and try again.",
            ErrorCategory.PERMISSION: "Permission required. Please check your browser settings.",
            ErrorCategory.RESOURCE: "System resources are limited. Try refreshing the page.",
            ErrorCategory.INTEGRATION: "Service temporarily unavailable. Please try again later.",
            ErrorCategory.USER_INPUT: "Invalid input provided. Please check and try again.",
            ErrorCategory.SYSTEM: "System error occurred. Please refresh the page.",
        }

        return messages_map.get(category, "An unexpected error occurred. Please try again.")

    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """
        Get logging level for error severity.

        Args:
            severity: Error severity

        Returns:
            Logging level
        """
        level_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }

        return level_map.get(severity, logging.WARNING)

    # Recovery strategy implementations
    def _recover_component_error(self, error_info: ErrorInfo) -> None:
        """Recover from component errors."""
        # Reset component state
        self.state_manager.clear_component_state(error_info.component_id)
        logger.info(f"Reset state for component: {error_info.component_id}")

    def _recover_network_error(self, error_info: ErrorInfo) -> None:
        """Recover from network errors."""
        # Set offline mode flag
        self.state_manager.set_global_state("offline_mode", True)
        logger.info("Enabled offline mode due to network error")

    def _recover_validation_error(self, error_info: ErrorInfo) -> None:
        """Recover from validation errors."""
        # Clear invalid input
        component_state = self.state_manager.get_component_state(error_info.component_id)
        if "data" in component_state:
            component_state["data"] = {}
            self.state_manager.set_component_state(error_info.component_id, component_state)

    def _recover_permission_error(self, error_info: ErrorInfo) -> None:
        """Recover from permission errors."""
        # Disable features requiring permissions
        component_state = self.state_manager.get_component_state(error_info.component_id)
        component_state["ui_state"]["disabled"] = True
        self.state_manager.set_component_state(error_info.component_id, component_state)

    def _recover_resource_error(self, error_info: ErrorInfo) -> None:
        """Recover from resource errors."""
        # Enable low-resource mode
        self.state_manager.set_global_state("low_resource_mode", True)
        logger.info("Enabled low-resource mode")

    def _recover_integration_error(self, error_info: ErrorInfo) -> None:
        """Recover from integration errors."""
        # Mark service as unavailable
        self.state_manager.set_global_state(f"service_{error_info.component_id}_available", False)

    def _recover_user_input_error(self, error_info: ErrorInfo) -> None:
        """Recover from user input errors."""
        # Reset input validation state
        component_state = self.state_manager.get_component_state(error_info.component_id)
        component_state["validation"] = {"is_valid": True, "errors": [], "warnings": []}
        self.state_manager.set_component_state(error_info.component_id, component_state)

    def _recover_system_error(self, error_info: ErrorInfo) -> None:
        """Recover from system errors."""
        # Log for debugging and suggest page refresh
        logger.critical(f"System error in component {error_info.component_id}: {error_info.message}")

    # Fallback component renderers
    def _render_input_fallback(self, component_id: str, error_info: ErrorInfo | None) -> None:
        """Render fallback for input components."""
        st.markdown(
            """
        <div class="mobile-card mobile-fallback">
            <h4>[WRITE] Input Unavailable</h4>
            <p>This input method is temporarily unavailable. Please try another input option.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_display_fallback(self, component_id: str, error_info: ErrorInfo | None) -> None:
        """Render fallback for display components."""
        st.markdown(
            """
        <div class="mobile-card mobile-fallback">
            <h4>[SUMMARY] Display Unavailable</h4>
            <p>Content cannot be displayed at the moment. Please try refreshing.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_interface_fallback(self, component_id: str, error_info: ErrorInfo | None) -> None:
        """Render fallback for interface components."""
        st.markdown(
            """
        <div class="mobile-card mobile-fallback">
            <h4>[TOOL] Interface Unavailable</h4>
            <p>This interface is temporarily unavailable. Basic functionality may still work.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_layout_fallback(self, component_id: str, error_info: ErrorInfo | None) -> None:
        """Render fallback for layout components."""
        st.markdown(
            """
        <div class="mobile-card mobile-fallback">
            <h4>[MOBILE] Layout Issue</h4>
            <p>Layout rendering failed. Content may appear differently than expected.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_generic_fallback(self, component_id: str, error_info: ErrorInfo | None) -> None:
        """Render generic fallback component."""
        st.markdown(
            f"""
        <div class="mobile-card mobile-fallback">
            <h4>[WARNING] Component Unavailable</h4>
            <p>Component "{component_id}" is temporarily unavailable.</p>
            <button onclick="window.location.reload()" class="mobile-button mobile-button-secondary">
                [PARTIAL] Refresh Page
            </button>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_minimal_fallback(self, component_id: str) -> None:
        """Render minimal fallback when everything else fails."""
        st.error(f"Component {component_id} is unavailable. Please refresh the page.")
