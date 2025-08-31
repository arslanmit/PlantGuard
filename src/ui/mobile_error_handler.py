"""
Mobile Error Handler for PlantGuard UI.

This module provides centralized error handling and recovery mechanisms for mobile components,
including component-level error boundaries, user-friendly error messages, and graceful degradation.
"""

import logging
import traceback
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for mobile components."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better error handling."""

    COMPONENT_RENDER = "component_render"
    STATE_MANAGEMENT = "state_management"
    ADAPTER_INTEGRATION = "adapter_integration"
    NETWORK_CONNECTION = "network_connection"
    USER_INPUT = "user_input"
    SYSTEM_RESOURCE = "system_resource"
    UNKNOWN = "unknown"


class MobileErrorHandler:
    """Centralized error handling system for mobile components."""

    # Error tracking keys
    ERROR_LOG_KEY = "mobile_error_log"
    ERROR_STATS_KEY = "mobile_error_stats"
    RECOVERY_ATTEMPTS_KEY = "mobile_recovery_attempts"

    # Recovery configuration
    MAX_RECOVERY_ATTEMPTS = 3
    RECOVERY_COOLDOWN_MINUTES = 5
    ERROR_RETENTION_HOURS = 24

    @staticmethod
    def handle_component_error(
        component_id: str,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.COMPONENT_RENDER,
        recoverable: bool = True,
        recovery_callback: Callable | None = None,
    ) -> dict[str, Any]:
        """
        Handle component-specific errors with comprehensive error management.

        Args:
            component_id: Unique identifier for the component
            error: The exception that occurred
            severity: Severity level of the error
            category: Category of the error for better handling
            recoverable: Whether the error can be recovered from
            recovery_callback: Optional callback function for custom recovery

        Returns:
            Dictionary containing error handling results and recovery information
        """
        error_info = {
            "component_id": component_id,
            "error_message": str(error),
            "error_type": type(error).__name__,
            "severity": severity.value,
            "category": category.value,
            "recoverable": recoverable,
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc(),
            "recovery_attempted": False,
            "recovery_successful": False,
        }

        try:
            # Log the error
            MobileErrorHandler._log_error(error_info)

            # Update component state with error information
            from src.ui.mobile_component_registry import MobileStateManager

            MobileStateManager.set_error_state(component_id, error, recoverable)

            # Display user-friendly error message
            MobileErrorHandler._display_user_error_message(component_id, error_info)

            # Attempt recovery if possible
            if recoverable and MobileErrorHandler._should_attempt_recovery(component_id):
                recovery_result = MobileErrorHandler._attempt_error_recovery(component_id, error_info, recovery_callback)
                error_info.update(recovery_result)

            # Update error statistics
            MobileErrorHandler._update_error_statistics(error_info)

            return error_info

        except Exception as handler_error:
            # Error in error handler - log and return basic info
            logger.critical(f"Error handler failed for component {component_id}: {handler_error}")
            return {
                "component_id": component_id,
                "error_message": str(error),
                "handler_error": str(handler_error),
                "severity": "critical",
                "recoverable": False,
            }

    @staticmethod
    def handle_analysis_error(error: Exception, input_type: str = "unknown", adapter_type: str = "unknown") -> dict[str, Any]:
        """
        Handle analysis-specific errors with specialized recovery mechanisms.

        Args:
            error: The analysis error that occurred
            input_type: Type of input that caused the error (image, audio, text)
            adapter_type: Type of adapter that failed (vision, audio, text)

        Returns:
            Dictionary containing error handling results
        """
        error_mappings = {
            FileNotFoundError: {
                "message": "Model file not found. Please check installation.",
                "recovery_suggestion": "Try restarting the application or contact support.",
                "severity": ErrorSeverity.HIGH,
                "category": ErrorCategory.SYSTEM_RESOURCE,
            },
            ValueError: {
                "message": "Invalid input provided. Please check your data.",
                "recovery_suggestion": "Try uploading a different image or recording new audio.",
                "severity": ErrorSeverity.MEDIUM,
                "category": ErrorCategory.USER_INPUT,
            },
            RuntimeError: {
                "message": "Analysis processing failed. Please try again.",
                "recovery_suggestion": "Wait a moment and retry the analysis.",
                "severity": ErrorSeverity.MEDIUM,
                "category": ErrorCategory.ADAPTER_INTEGRATION,
            },
            MemoryError: {
                "message": "Insufficient memory for analysis. Please try a smaller input.",
                "recovery_suggestion": "Reduce image size or audio length and try again.",
                "severity": ErrorSeverity.HIGH,
                "category": ErrorCategory.SYSTEM_RESOURCE,
            },
            ConnectionError: {
                "message": "Network connection issue detected.",
                "recovery_suggestion": "Check your internet connection and try again.",
                "severity": ErrorSeverity.MEDIUM,
                "category": ErrorCategory.NETWORK_CONNECTION,
            },
        }

        error_type = type(error)
        error_config = error_mappings.get(
            error_type,
            {
                "message": "An unexpected error occurred during analysis.",
                "recovery_suggestion": "Please try again or contact support if the issue persists.",
                "severity": ErrorSeverity.MEDIUM,
                "category": ErrorCategory.UNKNOWN,
            },
        )

        error_info = {
            "error_type": error_type.__name__,
            "error_message": str(error),
            "input_type": input_type,
            "adapter_type": adapter_type,
            "user_message": error_config["message"],
            "recovery_suggestion": error_config["recovery_suggestion"],
            "severity": error_config["severity"].value,
            "category": error_config["category"].value,
            "timestamp": datetime.now().isoformat(),
        }

        # Display error to user
        st.error(error_config["message"])
        st.info(f"[TIP] {error_config['recovery_suggestion']}")

        # Log the analysis error
        MobileErrorHandler._log_error(error_info)

        return error_info

    @staticmethod
    def create_error_boundary(component_id: str, render_function: Callable) -> Callable:
        """
        Create an error boundary wrapper for component render functions.

        Args:
            component_id: Unique identifier for the component
            render_function: The component's render function to wrap

        Returns:
            Wrapped render function with error handling
        """

        def error_boundary_wrapper(*args, **kwargs) -> None:
            try:
                return render_function(*args, **kwargs)
            except Exception as e:
                # Handle the error through the centralized system
                error_result = MobileErrorHandler.handle_component_error(
                    component_id=component_id, error=e, severity=ErrorSeverity.MEDIUM, category=ErrorCategory.COMPONENT_RENDER, recoverable=True
                )

                # Render fallback UI
                MobileErrorHandler._render_error_fallback(component_id, error_result)

                return None

        return error_boundary_wrapper

    @staticmethod
    def get_error_summary() -> dict[str, Any]:
        """
        Get comprehensive error summary for monitoring and debugging.

        Returns:
            Dictionary containing error statistics and recent errors
        """
        error_log = st.session_state.get(MobileErrorHandler.ERROR_LOG_KEY, [])
        error_stats = st.session_state.get(MobileErrorHandler.ERROR_STATS_KEY, {})

        # Calculate recent error statistics
        recent_errors = [error for error in error_log if datetime.fromisoformat(error["timestamp"]) > datetime.now() - timedelta(hours=1)]

        return {
            "total_errors": len(error_log),
            "recent_errors_1h": len(recent_errors),
            "error_by_severity": MobileErrorHandler._count_errors_by_field(error_log, "severity"),
            "error_by_category": MobileErrorHandler._count_errors_by_field(error_log, "category"),
            "error_by_component": MobileErrorHandler._count_errors_by_field(error_log, "component_id"),
            "recovery_success_rate": MobileErrorHandler._calculate_recovery_rate(error_log),
            "error_statistics": error_stats,
            "last_updated": datetime.now().isoformat(),
        }

    @staticmethod
    def clear_error_log(older_than_hours: int = 24) -> int:
        """
        Clear old errors from the error log.

        Args:
            older_than_hours: Clear errors older than this many hours

        Returns:
            Number of errors cleared
        """
        if MobileErrorHandler.ERROR_LOG_KEY not in st.session_state:
            return 0

        error_log = st.session_state[MobileErrorHandler.ERROR_LOG_KEY]
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        original_count = len(error_log)
        st.session_state[MobileErrorHandler.ERROR_LOG_KEY] = [
            error for error in error_log if datetime.fromisoformat(error["timestamp"]) > cutoff_time
        ]

        cleared_count = original_count - len(st.session_state[MobileErrorHandler.ERROR_LOG_KEY])

        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} old errors from error log")

        return cleared_count

    @staticmethod
    def _log_error(error_info: dict[str, Any]) -> None:
        """Log error information to session state and system logger."""
        # Initialize error log if needed
        if MobileErrorHandler.ERROR_LOG_KEY not in st.session_state:
            st.session_state[MobileErrorHandler.ERROR_LOG_KEY] = []

        # Add to error log
        st.session_state[MobileErrorHandler.ERROR_LOG_KEY].append(error_info)

        # Log to system logger based on severity
        severity = error_info.get("severity", "medium")
        message = f"Component {error_info.get('component_id', 'unknown')}: {error_info.get('error_message', 'Unknown error')}"

        if severity == "critical":
            logger.critical(message)
        elif severity == "high":
            logger.error(message)
        elif severity == "medium":
            logger.warning(message)
        else:
            logger.info(message)

        # Cleanup old errors periodically
        if len(st.session_state[MobileErrorHandler.ERROR_LOG_KEY]) > 100:
            MobileErrorHandler.clear_error_log(MobileErrorHandler.ERROR_RETENTION_HOURS)

    @staticmethod
    def _display_user_error_message(component_id: str, error_info: dict[str, Any]) -> None:
        """Display user-friendly error message based on error information."""
        severity = error_info.get("severity", "medium")
        category = error_info.get("category", "unknown")

        # Create user-friendly messages based on category
        category_messages = {
            "component_render": "There was an issue displaying this component.",
            "state_management": "There was an issue saving your data.",
            "adapter_integration": "There was an issue processing your request.",
            "network_connection": "There was a network connectivity issue.",
            "user_input": "There was an issue with the provided input.",
            "system_resource": "The system is experiencing resource constraints.",
            "unknown": "An unexpected issue occurred.",
        }

        base_message = category_messages.get(category, category_messages["unknown"])

        # Display appropriate Streamlit message based on severity
        if severity == "critical":
            st.error(f"[ALERT] Critical Error: {base_message}")
            st.error("Please refresh the page or contact support.")
        elif severity == "high":
            st.error(f"[WARNING] {base_message}")
            st.info("Please try again or use a different approach.")
        elif severity == "medium":
            st.warning(f"[WARNING] {base_message}")
            st.info("Please try again.")
        else:
            st.info(f"i {base_message}")

    @staticmethod
    def _should_attempt_recovery(component_id: str) -> bool:
        """Check if recovery should be attempted for a component."""
        if MobileErrorHandler.RECOVERY_ATTEMPTS_KEY not in st.session_state:
            st.session_state[MobileErrorHandler.RECOVERY_ATTEMPTS_KEY] = {}

        recovery_data = st.session_state[MobileErrorHandler.RECOVERY_ATTEMPTS_KEY]

        if component_id not in recovery_data:
            return True

        component_recovery = recovery_data[component_id]

        # Check attempt count
        if component_recovery.get("attempts", 0) >= MobileErrorHandler.MAX_RECOVERY_ATTEMPTS:
            return False

        # Check cooldown period
        last_attempt = component_recovery.get("last_attempt")
        if last_attempt:
            last_attempt_time = datetime.fromisoformat(last_attempt)
            cooldown_end = last_attempt_time + timedelta(minutes=MobileErrorHandler.RECOVERY_COOLDOWN_MINUTES)
            if datetime.now() < cooldown_end:
                return False

        return True

    @staticmethod
    def _attempt_error_recovery(component_id: str, error_info: dict[str, Any], recovery_callback: Callable | None = None) -> dict[str, Any]:
        """Attempt to recover from an error."""
        recovery_result = {
            "recovery_attempted": True,
            "recovery_successful": False,
            "recovery_method": "unknown",
            "recovery_timestamp": datetime.now().isoformat(),
        }

        try:
            # Update recovery tracking
            MobileErrorHandler._update_recovery_tracking(component_id)

            # Try custom recovery callback first
            if recovery_callback:
                recovery_result["recovery_method"] = "custom_callback"
                recovery_callback(component_id, error_info)
                recovery_result["recovery_successful"] = True
                return recovery_result

            # Try built-in recovery methods based on error category
            category = error_info.get("category", "unknown")

            if category == "component_render":
                recovery_result["recovery_method"] = "component_reset"
                MobileErrorHandler._recover_component_render(component_id)
            elif category == "state_management":
                recovery_result["recovery_method"] = "state_reset"
                MobileErrorHandler._recover_state_management(component_id)
            elif category == "adapter_integration":
                recovery_result["recovery_method"] = "adapter_retry"
                MobileErrorHandler._recover_adapter_integration(component_id)
            else:
                recovery_result["recovery_method"] = "generic_reset"
                MobileErrorHandler._recover_generic(component_id)

            recovery_result["recovery_successful"] = True
            logger.info(f"Successfully recovered component {component_id} using {recovery_result['recovery_method']}")

        except Exception as recovery_error:
            recovery_result["recovery_error"] = str(recovery_error)
            logger.error(f"Recovery failed for component {component_id}: {recovery_error}")

        return recovery_result

    @staticmethod
    def _recover_component_render(component_id: str) -> None:
        """Recover from component rendering errors."""
        from src.ui.mobile_component_registry import MobileStateManager

        # Reset component state to initial values
        MobileStateManager.reset_component_state(component_id)

        # Clear any cached data that might be causing issues
        state = MobileStateManager.get_component_state(component_id)
        state["data"] = {}
        state["loading"] = False
        MobileStateManager.set_component_state(component_id, state)

    @staticmethod
    def _recover_state_management(component_id: str) -> None:
        """Recover from state management errors."""
        from src.ui.mobile_component_registry import MobileStateManager

        # Try to restore from persistent data
        if not MobileStateManager.restore_component_state(component_id):
            # If restoration fails, reset to clean state
            MobileStateManager.reset_component_state(component_id)

    @staticmethod
    def _recover_adapter_integration(component_id: str) -> None:
        """Recover from adapter integration errors."""
        from src.ui.mobile_component_registry import MobileStateManager

        # Clear any cached adapter results
        state = MobileStateManager.get_component_state(component_id)
        state["data"].pop("adapter_result", None)
        state["data"].pop("cached_prediction", None)
        state["loading"] = False
        MobileStateManager.set_component_state(component_id, state)

    @staticmethod
    def _recover_generic(component_id: str) -> None:
        """Generic recovery method for unknown error types."""
        from src.ui.mobile_component_registry import MobileStateManager

        # Reset component to clean state
        MobileStateManager.reset_component_state(component_id)

    @staticmethod
    def _update_recovery_tracking(component_id: str) -> None:
        """Update recovery attempt tracking."""
        if MobileErrorHandler.RECOVERY_ATTEMPTS_KEY not in st.session_state:
            st.session_state[MobileErrorHandler.RECOVERY_ATTEMPTS_KEY] = {}

        recovery_data = st.session_state[MobileErrorHandler.RECOVERY_ATTEMPTS_KEY]

        if component_id not in recovery_data:
            recovery_data[component_id] = {"attempts": 0}

        recovery_data[component_id]["attempts"] += 1
        recovery_data[component_id]["last_attempt"] = datetime.now().isoformat()

    @staticmethod
    def _update_error_statistics(error_info: dict[str, Any]) -> None:
        """Update error statistics for monitoring."""
        if MobileErrorHandler.ERROR_STATS_KEY not in st.session_state:
            st.session_state[MobileErrorHandler.ERROR_STATS_KEY] = {
                "total_errors": 0,
                "by_severity": {},
                "by_category": {},
                "by_component": {},
                "recovery_attempts": 0,
                "recovery_successes": 0,
            }

        stats = st.session_state[MobileErrorHandler.ERROR_STATS_KEY]

        # Update counters
        stats["total_errors"] += 1

        # Update by severity
        severity = error_info.get("severity", "unknown")
        stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

        # Update by category
        category = error_info.get("category", "unknown")
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        # Update by component
        component_id = error_info.get("component_id", "unknown")
        stats["by_component"][component_id] = stats["by_component"].get(component_id, 0) + 1

        # Update recovery statistics
        if error_info.get("recovery_attempted"):
            stats["recovery_attempts"] += 1
            if error_info.get("recovery_successful"):
                stats["recovery_successes"] += 1

    @staticmethod
    def _render_error_fallback(component_id: str, error_info: dict[str, Any]) -> None:
        """Render fallback UI when component fails."""
        st.markdown(
            f"""
        <div class="mobile-card mobile-error-fallback" style="
            border: 2px solid #ff6b6b;
            background-color: #fff5f5;
            padding: 16px;
            border-radius: 12px;
            margin: 8px 0;
        ">
            <h4 style="color: #d63031; margin: 0 0 8px 0;">[WARNING] Component Unavailable</h4>
            <p style="margin: 0 0 8px 0; color: #636e72;">
                The {component_id.replace("_", " ").title()} component is temporarily unavailable.
            </p>
            <p style="margin: 0; font-size: 14px; color: #636e72;">
                Please try refreshing the page or contact support if the issue persists.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _count_errors_by_field(error_log: list[dict], field: str) -> dict[str, int]:
        """Count errors by a specific field."""
        counts = {}
        for error in error_log:
            value = error.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    @staticmethod
    def _calculate_recovery_rate(error_log: list[dict]) -> float:
        """Calculate the recovery success rate."""
        recovery_attempts = sum(1 for error in error_log if error.get("recovery_attempted"))
        recovery_successes = sum(1 for error in error_log if error.get("recovery_successful"))

        if recovery_attempts == 0:
            return 0.0

        return recovery_successes / recovery_attempts


class MobileErrorBoundary:
    """Error boundary component for wrapping mobile components."""

    def __init__(self, component_id: str, fallback_renderer: Callable | None = None) -> None:
        """
        Initialize error boundary.

        Args:
            component_id: ID of the component to protect
            fallback_renderer: Optional custom fallback renderer
        """
        self.component_id = component_id
        self.fallback_renderer = fallback_renderer or self._default_fallback

    def __enter__(self) -> "MobileErrorBoundary":
        """Enter the error boundary context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Handle exceptions that occur within the boundary."""
        if exc_type is not None:
            # Handle the error
            MobileErrorHandler.handle_component_error(
                component_id=self.component_id,
                error=exc_val,
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.COMPONENT_RENDER,
                recoverable=True,
            )

            # Render fallback UI
            self.fallback_renderer(self.component_id, exc_val)

            # Suppress the exception (return True)
            return True

        return False

    def _default_fallback(self, component_id: str, error: Exception) -> None:
        """Default fallback renderer."""
        st.error(f"Component {component_id} encountered an error: {error!s}")
        st.info("Please try refreshing the page.")


# Decorator for easy error boundary usage
def mobile_error_boundary(component_id: str, fallback_renderer: Callable | None = None) -> Callable:
    """
    Decorator to wrap functions with error boundary protection.

    Args:
        component_id: ID of the component being protected
        fallback_renderer: Optional custom fallback renderer
    """

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                MobileErrorHandler.handle_component_error(
                    component_id=component_id, error=e, severity=ErrorSeverity.MEDIUM, category=ErrorCategory.COMPONENT_RENDER, recoverable=True
                )

                if fallback_renderer:
                    fallback_renderer(component_id, e)
                else:
                    st.error(f"Component {component_id} encountered an error.")
                    st.info("Please try again or refresh the page.")

                return None

        return wrapper

    return decorator
