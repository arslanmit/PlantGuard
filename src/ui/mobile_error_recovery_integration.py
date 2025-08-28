"""
Mobile Error Recovery Integration for PlantGuard UI.

This module integrates error handling with offline functionality to provide
comprehensive error recovery and graceful degradation for mobile components.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

import streamlit as st

from src.ui.mobile_error_handler import ErrorCategory, ErrorSeverity, MobileErrorHandler
from src.ui.mobile_offline_manager import MobileOfflineManager, NetworkStatus, OfflineCapability

logger = logging.getLogger(__name__)


class MobileErrorRecoveryIntegration:
    """Integration layer for error handling and offline functionality."""

    @staticmethod
    def initialize_integrated_system() -> None:
        """Initialize the integrated error handling and offline system."""
        try:
            # Initialize offline system first
            MobileOfflineManager.initialize_offline_system()

            # Register error recovery callbacks for network-related errors
            MobileErrorRecoveryIntegration._register_network_error_handlers()

            # Set up periodic maintenance
            MobileErrorRecoveryIntegration._setup_maintenance_tasks()

            logger.info("Integrated error recovery system initialized")

        except Exception as e:
            logger.error(f"Failed to initialize integrated system: {e}")
            st.error("Error recovery system initialization failed")

    @staticmethod
    def handle_network_dependent_operation(
        component_id: str, operation_name: str, operation_func: Callable, fallback_func: Callable | None = None, cache_key: str | None = None
    ) -> Any:
        """
        Handle operations that depend on network connectivity with comprehensive error recovery.

        Args:
            component_id: ID of the component performing the operation
            operation_name: Name of the operation for logging
            operation_func: Function to execute when online
            fallback_func: Optional fallback function for offline mode
            cache_key: Optional key for caching results

        Returns:
            Operation result or cached/fallback data
        """
        try:
            # Check network status
            network_status = MobileOfflineManager.get_network_status()

            if network_status == NetworkStatus.ONLINE:
                return MobileErrorRecoveryIntegration._execute_online_operation(component_id, operation_name, operation_func, cache_key)
            elif network_status == NetworkStatus.LIMITED:
                return MobileErrorRecoveryIntegration._execute_limited_operation(
                    component_id, operation_name, operation_func, fallback_func, cache_key
                )
            else:  # OFFLINE or UNKNOWN
                return MobileErrorRecoveryIntegration._execute_offline_operation(component_id, operation_name, fallback_func, cache_key)

        except Exception as e:
            # Handle the error through the integrated system
            return MobileErrorRecoveryIntegration._handle_operation_error(component_id, operation_name, e, fallback_func, cache_key)

    @staticmethod
    def create_resilient_component_wrapper(
        component_id: str, render_func: Callable, offline_capability: OfflineCapability = OfflineCapability.LIMITED
    ) -> Callable:
        """
        Create a wrapper that makes components resilient to errors and network issues.

        Args:
            component_id: ID of the component
            render_func: Component's render function
            offline_capability: Offline capability level

        Returns:
            Wrapped render function with error recovery and offline support
        """

        def resilient_wrapper(*args, **kwargs):
            try:
                # Register offline capability if not already registered
                if not MobileOfflineManager.can_function_offline(component_id):
                    MobileOfflineManager.register_offline_capability(component_id, offline_capability)

                # Check if component can function in current network state
                if MobileOfflineManager.is_offline() and offline_capability == OfflineCapability.NONE:
                    MobileErrorRecoveryIntegration._render_offline_unavailable_message(component_id)
                    return None

                # Execute the render function with error boundary
                return render_func(*args, **kwargs)

            except Exception as e:
                # Handle error with integrated recovery
                return MobileErrorRecoveryIntegration._handle_component_render_error(component_id, e, offline_capability)

        return resilient_wrapper

    @staticmethod
    def display_system_status() -> None:
        """Display comprehensive system status including errors and offline state."""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🌐 Network Status")
            MobileOfflineManager.display_network_status()

            # Show offline queue if applicable
            if MobileOfflineManager.is_offline():
                offline_status = MobileOfflineManager.get_offline_status_summary()
                queue_info = offline_status["queue_info"]

                if queue_info["total_operations"] > 0:
                    st.info(f"[DETAILS] {queue_info['total_operations']} operations queued")

        with col2:
            st.markdown("### [WARNING] Error Status")
            error_summary = MobileErrorHandler.get_error_summary()

            if error_summary["total_errors"] > 0:
                st.warning(f"🚨 {error_summary['recent_errors_1h']} recent errors")

                # Show error breakdown
                if error_summary["error_by_severity"]:
                    severity_text = ", ".join([f"{count} {severity}" for severity, count in error_summary["error_by_severity"].items()])
                    st.caption(f"Breakdown: {severity_text}")
            else:
                st.success("[DONE] No recent errors")

        # Show recovery actions if needed
        MobileErrorRecoveryIntegration._display_recovery_actions()

    @staticmethod
    def perform_system_maintenance() -> dict[str, Any]:
        """Perform system maintenance tasks."""
        maintenance_results = {
            "timestamp": datetime.now().isoformat(),
            "tasks_performed": [],
            "errors_cleared": 0,
            "cache_cleaned": 0,
            "queue_processed": 0,
        }

        try:
            # Clear old errors
            errors_cleared = MobileErrorHandler.clear_error_log(older_than_hours=24)
            maintenance_results["errors_cleared"] = errors_cleared
            maintenance_results["tasks_performed"].append("error_log_cleanup")

            # Clean up offline data
            cleanup_results = MobileOfflineManager.cleanup_offline_data()
            maintenance_results["cache_cleaned"] = cleanup_results["cache_entries_cleaned"]
            maintenance_results["tasks_performed"].append("offline_data_cleanup")

            # Process offline queue if online
            if MobileOfflineManager.is_online():
                queue_results = MobileOfflineManager.process_offline_queue()
                maintenance_results["queue_processed"] = queue_results["processed"]
                maintenance_results["tasks_performed"].append("offline_queue_processing")

            # Update network status
            MobileOfflineManager.check_network_status()
            maintenance_results["tasks_performed"].append("network_status_check")

            logger.info(f"System maintenance completed: {maintenance_results}")

        except Exception as e:
            logger.error(f"System maintenance failed: {e}")
            maintenance_results["maintenance_error"] = str(e)

        return maintenance_results

    @staticmethod
    def _execute_online_operation(component_id: str, operation_name: str, operation_func: Callable, cache_key: str | None) -> Any:
        """Execute operation when online."""
        try:
            result = operation_func()

            # Cache successful result if cache key provided
            if cache_key:
                MobileOfflineManager.cache_resource(
                    cache_key, result, metadata={"component_id": component_id, "operation_name": operation_name, "cached_from": "online_execution"}
                )

            return result

        except Exception as e:
            # Try retry with backoff for network-related errors
            if MobileErrorRecoveryIntegration._is_network_error(e):
                retry_result = MobileOfflineManager.retry_with_backoff(f"{component_id}_{operation_name}", operation_func)

                if retry_result["success"]:
                    return retry_result["result"]
                else:
                    # Retry failed, handle as error
                    raise e
            else:
                # Non-network error, re-raise
                raise e

    @staticmethod
    def _execute_limited_operation(
        component_id: str, operation_name: str, operation_func: Callable, fallback_func: Callable | None, cache_key: str | None
    ) -> Any:
        """Execute operation with limited connectivity."""
        try:
            # Try the main operation with shorter timeout
            result = operation_func()

            # Cache result if successful
            if cache_key:
                MobileOfflineManager.cache_resource(cache_key, result)

            return result

        except Exception as e:
            # Fall back to cached data or fallback function
            if cache_key:
                cached_result = MobileOfflineManager.get_cached_resource(cache_key)
                if cached_result:
                    st.info("[WARNING] Using cached data due to limited connectivity")
                    return cached_result

            if fallback_func:
                st.info("[WARNING] Using fallback due to limited connectivity")
                return fallback_func()

            # Queue for later if no fallback available
            MobileOfflineManager.queue_offline_operation(
                f"{component_id}_{operation_name}_{datetime.now().timestamp()}", operation_name, {"component_id": component_id}
            )

            raise e

    @staticmethod
    def _execute_offline_operation(component_id: str, operation_name: str, fallback_func: Callable | None, cache_key: str | None) -> Any:
        """Execute operation when offline."""
        # Try cached data first
        if cache_key:
            cached_result = MobileOfflineManager.get_cached_resource(cache_key)
            if cached_result:
                st.info("[MOBILE] Using cached data (offline mode)")
                return cached_result

        # Try fallback function
        if fallback_func:
            st.info("[MOBILE] Using offline functionality")
            return fallback_func()

        # Queue for later execution
        MobileOfflineManager.queue_offline_operation(
            f"{component_id}_{operation_name}_{datetime.now().timestamp()}", operation_name, {"component_id": component_id}
        )

        st.warning("[MOBILE] Operation queued for when connection returns")
        return None

    @staticmethod
    def _handle_operation_error(
        component_id: str, operation_name: str, error: Exception, fallback_func: Callable | None, cache_key: str | None
    ) -> Any:
        """Handle operation errors with integrated recovery."""
        # Determine error category
        if MobileErrorRecoveryIntegration._is_network_error(error):
            category = ErrorCategory.NETWORK_CONNECTION
            severity = ErrorSeverity.MEDIUM
        else:
            category = ErrorCategory.ADAPTER_INTEGRATION
            severity = ErrorSeverity.HIGH

        # Handle through error system
        error_result = MobileErrorHandler.handle_component_error(
            component_id=component_id, error=error, severity=severity, category=category, recoverable=True
        )

        # Try recovery options
        if cache_key:
            cached_result = MobileOfflineManager.get_cached_resource(cache_key)
            if cached_result:
                st.info("[PARTIAL] Using cached data due to error")
                return cached_result

        if fallback_func:
            try:
                st.info("[PARTIAL] Using fallback due to error")
                return fallback_func()
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")

        # Queue for retry if it's a network error
        if category == ErrorCategory.NETWORK_CONNECTION:
            MobileOfflineManager.queue_offline_operation(
                f"{component_id}_{operation_name}_retry_{datetime.now().timestamp()}",
                operation_name,
                {"component_id": component_id, "retry_after_error": True},
            )
            st.info("[PARTIAL] Operation queued for retry")

        return None

    @staticmethod
    def _handle_component_render_error(component_id: str, error: Exception, offline_capability: OfflineCapability) -> None:
        """Handle component rendering errors with recovery."""
        # Handle through error system
        MobileErrorHandler.handle_component_error(
            component_id=component_id, error=error, severity=ErrorSeverity.MEDIUM, category=ErrorCategory.COMPONENT_RENDER, recoverable=True
        )

        # Try to render a fallback based on offline capability
        if offline_capability in [OfflineCapability.FULL, OfflineCapability.LIMITED]:
            MobileErrorRecoveryIntegration._render_degraded_component(component_id, offline_capability)
        else:
            MobileErrorRecoveryIntegration._render_error_component(component_id)

    @staticmethod
    def _render_offline_unavailable_message(component_id: str) -> None:
        """Render message when component is unavailable offline."""
        st.markdown(
            f"""
        <div class="mobile-card mobile-offline-unavailable" style="
            border: 2px solid #ffa726;
            background-color: #fff8e1;
            padding: 16px;
            border-radius: 12px;
            margin: 8px 0;
            text-align: center;
        ">
            <h4 style="color: #f57c00; margin: 0 0 8px 0;">[MOBILE] Offline Mode</h4>
            <p style="margin: 0 0 8px 0; color: #ef6c00;">
                {component_id.replace("_", " ").title()} requires internet connection
            </p>
            <p style="margin: 0; font-size: 14px; color: #bf360c;">
                Please connect to the internet to use this feature
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _render_degraded_component(component_id: str, capability: OfflineCapability) -> None:
        """Render degraded version of component."""
        capability_messages = {
            OfflineCapability.FULL: "Running in offline mode with full functionality",
            OfflineCapability.LIMITED: "Running in offline mode with limited functionality",
            OfflineCapability.CACHED: "Showing cached data only",
        }

        message = capability_messages.get(capability, "Limited offline functionality")

        st.markdown(
            f"""
        <div class="mobile-card mobile-degraded-component" style="
            border: 2px solid #42a5f5;
            background-color: #e3f2fd;
            padding: 16px;
            border-radius: 12px;
            margin: 8px 0;
        ">
            <h4 style="color: #1976d2; margin: 0 0 8px 0;">[MOBILE] {component_id.replace("_", " ").title()}</h4>
            <p style="margin: 0; color: #1565c0;">
                {message}
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _render_error_component(component_id: str) -> None:
        """Render error state for component."""
        st.markdown(
            f"""
        <div class="mobile-card mobile-error-component" style="
            border: 2px solid #ef5350;
            background-color: #ffebee;
            padding: 16px;
            border-radius: 12px;
            margin: 8px 0;
        ">
            <h4 style="color: #d32f2f; margin: 0 0 8px 0;">[WARNING] Component Error</h4>
            <p style="margin: 0 0 8px 0; color: #c62828;">
                {component_id.replace("_", " ").title()} encountered an error
            </p>
            <p style="margin: 0; font-size: 14px; color: #b71c1c;">
                Please try refreshing the page
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _display_recovery_actions() -> None:
        """Display available recovery actions."""
        error_summary = MobileErrorHandler.get_error_summary()
        offline_status = MobileOfflineManager.get_offline_status_summary()

        recovery_actions = []

        # Check for errors that need attention
        if error_summary["recent_errors_1h"] > 0:
            recovery_actions.append("Clear recent errors")

        # Check for offline queue
        if offline_status["queue_info"]["total_operations"] > 0:
            if MobileOfflineManager.is_online():
                recovery_actions.append("Process offline queue")
            else:
                recovery_actions.append("View queued operations")

        # Check for cache issues
        if offline_status["cache_info"]["expired_entries"] > 0:
            recovery_actions.append("Clean expired cache")

        if recovery_actions:
            st.markdown("### [TOOL] Recovery Actions")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🧹 Clean System", help="Clean up errors and cache"):
                    maintenance_results = MobileErrorRecoveryIntegration.perform_system_maintenance()
                    st.success(f"Cleaned {maintenance_results['errors_cleared']} errors, {maintenance_results['cache_cleaned']} cache entries")

            with col2:
                if st.button("[PARTIAL] Retry Failed", help="Retry failed operations"):
                    if MobileOfflineManager.is_online():
                        queue_results = MobileOfflineManager.process_offline_queue()
                        st.success(f"Processed {queue_results['processed']} operations")
                    else:
                        st.warning("Cannot retry while offline")

            with col3:
                if st.button("[SUMMARY] View Details", help="View detailed status"):
                    with st.expander("System Details"):
                        st.json({"error_summary": error_summary, "offline_status": offline_status})

    @staticmethod
    def _register_network_error_handlers() -> None:
        """Register error handlers for network-related issues."""
        # This would register specific handlers for different types of network errors
        # In a real implementation, this would set up callbacks for different error types
        logger.info("Network error handlers registered")

    @staticmethod
    def _setup_maintenance_tasks() -> None:
        """Set up periodic maintenance tasks."""
        # In a real implementation, this would set up background tasks
        # For Streamlit, we'll rely on manual maintenance calls
        logger.info("Maintenance tasks configured")

    @staticmethod
    def _is_network_error(error: Exception) -> bool:
        """Check if an error is network-related."""
        network_error_types = [
            ConnectionError,
            TimeoutError,
            OSError,  # Can include network-related OS errors
        ]

        network_error_messages = ["connection", "network", "timeout", "unreachable", "dns", "socket"]

        # Check error type
        if any(isinstance(error, error_type) for error_type in network_error_types):
            return True

        # Check error message
        error_message = str(error).lower()
        return any(keyword in error_message for keyword in network_error_messages)


# Convenience functions for easy integration


def initialize_mobile_error_recovery():
    """Initialize the complete mobile error recovery system."""
    MobileErrorRecoveryIntegration.initialize_integrated_system()


def create_resilient_mobile_component(component_id: str, offline_capability: OfflineCapability = OfflineCapability.LIMITED):
    """
    Decorator to create resilient mobile components.

    Args:
        component_id: Unique identifier for the component
        offline_capability: Offline capability level
    """

    def decorator(render_func):
        return MobileErrorRecoveryIntegration.create_resilient_component_wrapper(component_id, render_func, offline_capability)

    return decorator


def handle_mobile_operation(component_id: str, operation_name: str, cache_key: str | None = None):
    """
    Decorator to handle mobile operations with error recovery and offline support.

    Args:
        component_id: ID of the component performing the operation
        operation_name: Name of the operation
        cache_key: Optional cache key for results
    """

    def decorator(operation_func):
        def wrapper(*args, **kwargs):
            return MobileErrorRecoveryIntegration.handle_network_dependent_operation(
                component_id=component_id, operation_name=operation_name, operation_func=lambda: operation_func(*args, **kwargs), cache_key=cache_key
            )

        return wrapper

    return decorator
