"""
Mobile Offline Manager for PlantGuard UI.

This module provides offline functionality and network error handling for mobile components,
including offline detection, cached resource management, and network retry mechanisms.
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class NetworkStatus(Enum):
    """Network connectivity status."""

    ONLINE = "online"
    OFFLINE = "offline"
    LIMITED = "limited"
    UNKNOWN = "unknown"


class OfflineCapability(Enum):
    """Offline capability levels for different features."""

    FULL = "full"  # Fully functional offline
    LIMITED = "limited"  # Basic functionality offline
    NONE = "none"  # Requires network connection
    CACHED = "cached"  # Works with cached data only


class MobileOfflineManager:
    """Manager for offline functionality and network error handling."""

    # Session state keys
    NETWORK_STATUS_KEY = "mobile_network_status"
    OFFLINE_CACHE_KEY = "mobile_offline_cache"
    OFFLINE_QUEUE_KEY = "mobile_offline_queue"
    NETWORK_RETRY_KEY = "mobile_network_retry"
    OFFLINE_CAPABILITIES_KEY = "mobile_offline_capabilities"

    # Configuration
    NETWORK_CHECK_INTERVAL = 30  # seconds
    MAX_RETRY_ATTEMPTS = 5
    RETRY_BACKOFF_BASE = 2  # exponential backoff base
    CACHE_EXPIRY_HOURS = 24
    MAX_CACHE_SIZE_MB = 50

    @staticmethod
    def initialize_offline_system() -> None:
        """Initialize the offline management system."""
        # Initialize session state
        if MobileOfflineManager.NETWORK_STATUS_KEY not in st.session_state:
            st.session_state[MobileOfflineManager.NETWORK_STATUS_KEY] = {
                "status": NetworkStatus.UNKNOWN.value,
                "last_check": datetime.now().isoformat(),
                "check_count": 0,
                "connection_quality": "unknown",
            }

        if MobileOfflineManager.OFFLINE_CACHE_KEY not in st.session_state:
            st.session_state[MobileOfflineManager.OFFLINE_CACHE_KEY] = {}

        if MobileOfflineManager.OFFLINE_QUEUE_KEY not in st.session_state:
            st.session_state[MobileOfflineManager.OFFLINE_QUEUE_KEY] = []

        if MobileOfflineManager.NETWORK_RETRY_KEY not in st.session_state:
            st.session_state[MobileOfflineManager.NETWORK_RETRY_KEY] = {}

        if MobileOfflineManager.OFFLINE_CAPABILITIES_KEY not in st.session_state:
            st.session_state[MobileOfflineManager.OFFLINE_CAPABILITIES_KEY] = {}

        # Register offline capabilities for PlantGuard components
        MobileOfflineManager._register_default_capabilities()

        # Perform initial network check
        MobileOfflineManager.check_network_status()

        logger.info("Mobile offline system initialized")

    @staticmethod
    def check_network_status() -> NetworkStatus:
        """
        Check current network connectivity status.

        Returns:
            Current network status
        """
        try:
            # Update check timestamp and count
            network_info = st.session_state[MobileOfflineManager.NETWORK_STATUS_KEY]
            network_info["last_check"] = datetime.now().isoformat()
            network_info["check_count"] += 1

            # For Streamlit apps, we assume online unless explicitly detected otherwise
            # In a real implementation, this would use JavaScript or other methods
            # to detect actual network connectivity
            current_status = NetworkStatus.ONLINE

            # Check if we have any pending network operations that failed
            retry_info = st.session_state[MobileOfflineManager.NETWORK_RETRY_KEY]
            if retry_info and any(info.get("failed_attempts", 0) > 0 for info in retry_info.values()):
                current_status = NetworkStatus.LIMITED

            # Update network status
            network_info["status"] = current_status.value
            network_info["connection_quality"] = MobileOfflineManager._assess_connection_quality()

            # Log status changes
            if network_info.get("previous_status") != current_status.value:
                logger.info(f"Network status changed to: {current_status.value}")
                network_info["previous_status"] = current_status.value
                network_info["status_change_time"] = datetime.now().isoformat()

            return current_status

        except Exception as e:
            logger.error(f"Error checking network status: {e}")
            st.session_state[MobileOfflineManager.NETWORK_STATUS_KEY]["status"] = NetworkStatus.UNKNOWN.value
            return NetworkStatus.UNKNOWN

    @staticmethod
    def is_online() -> bool:
        """Check if the device is currently online."""
        status = MobileOfflineManager.get_network_status()
        return status in [NetworkStatus.ONLINE, NetworkStatus.LIMITED]

    @staticmethod
    def is_offline() -> bool:
        """Check if the device is currently offline."""
        return not MobileOfflineManager.is_online()

    @staticmethod
    def get_network_status() -> NetworkStatus:
        """Get the current network status."""
        network_info = st.session_state.get(MobileOfflineManager.NETWORK_STATUS_KEY, {})
        status_str = network_info.get("status", NetworkStatus.UNKNOWN.value)

        try:
            return NetworkStatus(status_str)
        except ValueError:
            return NetworkStatus.UNKNOWN

    @staticmethod
    def display_network_status() -> None:
        """Display current network status to the user."""
        status = MobileOfflineManager.get_network_status()
        network_info = st.session_state[MobileOfflineManager.NETWORK_STATUS_KEY]

        status_messages = {
            NetworkStatus.ONLINE: ("[GREEN]", "Online", "All features available"),
            NetworkStatus.LIMITED: ("[YELLOW]", "Limited Connection", "Some features may be slower"),
            NetworkStatus.OFFLINE: ("[RED]", "Offline", "Using cached data only"),
            NetworkStatus.UNKNOWN: ("⚪", "Unknown", "Checking connection..."),
        }

        icon, title, description = status_messages[status]

        # Display status in a compact format
        st.markdown(
            f"""
        <div class="mobile-network-status" style="
            display: flex;
            align-items: center;
            padding: 8px 12px;
            background-color: #f8f9fa;
            border-radius: 8px;
            margin: 4px 0;
            font-size: 14px;
        ">
            <span style="margin-right: 8px;">{icon}</span>
            <span style="font-weight: 600; margin-right: 8px;">{title}</span>
            <span style="color: #6c757d;">{description}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Show additional info if offline
        if status == NetworkStatus.OFFLINE:
            offline_queue = st.session_state[MobileOfflineManager.OFFLINE_QUEUE_KEY]
            if offline_queue:
                st.info(f"[DETAILS] {len(offline_queue)} operations queued for when connection returns")

    @staticmethod
    def cache_resource(key: str, data: Any, expiry_hours: int | None = None, metadata: dict | None = None) -> bool:
        """
        Cache a resource for offline use.

        Args:
            key: Unique identifier for the cached resource
            data: Data to cache (must be JSON serializable)
            expiry_hours: Hours until cache expires (default: 24)
            metadata: Additional metadata about the cached resource

        Returns:
            True if caching was successful, False otherwise
        """
        try:
            if expiry_hours is None:
                expiry_hours = MobileOfflineManager.CACHE_EXPIRY_HOURS

            cache = st.session_state[MobileOfflineManager.OFFLINE_CACHE_KEY]

            # Check cache size limits
            if MobileOfflineManager._get_cache_size_mb() > MobileOfflineManager.MAX_CACHE_SIZE_MB:
                MobileOfflineManager._cleanup_cache()

            # Create cache entry
            cache_entry = {
                "data": data,
                "cached_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
                "access_count": 0,
                "last_accessed": datetime.now().isoformat(),
                "metadata": metadata or {},
                "size_estimate": len(str(data)),  # Rough size estimate
            }

            cache[key] = cache_entry

            logger.info(f"Cached resource: {key} (expires in {expiry_hours}h)")
            return True

        except Exception as e:
            logger.error(f"Failed to cache resource {key}: {e}")
            return False

    @staticmethod
    def get_cached_resource(key: str) -> Any | None:
        """
        Retrieve a cached resource.

        Args:
            key: Unique identifier for the cached resource

        Returns:
            Cached data if available and not expired, None otherwise
        """
        try:
            cache = st.session_state[MobileOfflineManager.OFFLINE_CACHE_KEY]

            if key not in cache:
                return None

            cache_entry = cache[key]

            # Check if expired
            expires_at = datetime.fromisoformat(cache_entry["expires_at"])
            if datetime.now() > expires_at:
                del cache[key]
                logger.info(f"Removed expired cache entry: {key}")
                return None

            # Update access statistics
            cache_entry["access_count"] += 1
            cache_entry["last_accessed"] = datetime.now().isoformat()

            logger.debug(f"Retrieved cached resource: {key}")
            return cache_entry["data"]

        except Exception as e:
            logger.error(f"Failed to retrieve cached resource {key}: {e}")
            return None

    @staticmethod
    def queue_offline_operation(
        operation_id: str, operation_type: str, operation_data: dict, retry_callback: Callable | None = None, priority: int = 1
    ) -> bool:
        """
        Queue an operation for execution when network becomes available.

        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation (e.g., 'analysis', 'upload')
            operation_data: Data needed to execute the operation
            retry_callback: Function to call when retrying the operation
            priority: Priority level (1=high, 5=low)

        Returns:
            True if queuing was successful, False otherwise
        """
        try:
            queue = st.session_state[MobileOfflineManager.OFFLINE_QUEUE_KEY]

            # Check if operation already queued
            existing_op = next((op for op in queue if op["operation_id"] == operation_id), None)
            if existing_op:
                logger.warning(f"Operation {operation_id} already queued")
                return False

            # Create queue entry
            queue_entry = {
                "operation_id": operation_id,
                "operation_type": operation_type,
                "operation_data": operation_data,
                "queued_at": datetime.now().isoformat(),
                "priority": priority,
                "retry_count": 0,
                "last_retry": None,
                "status": "queued",
                "retry_callback": retry_callback.__name__ if retry_callback else None,
            }

            queue.append(queue_entry)

            # Sort by priority
            queue.sort(key=lambda x: x["priority"])

            logger.info(f"Queued offline operation: {operation_id} ({operation_type})")
            return True

        except Exception as e:
            logger.error(f"Failed to queue operation {operation_id}: {e}")
            return False

    @staticmethod
    def process_offline_queue() -> dict[str, Any]:
        """
        Process queued operations when network becomes available.

        Returns:
            Dictionary with processing results
        """
        if MobileOfflineManager.is_offline():
            return {"status": "offline", "processed": 0, "failed": 0}

        queue = st.session_state[MobileOfflineManager.OFFLINE_QUEUE_KEY]

        if not queue:
            return {"status": "empty", "processed": 0, "failed": 0}

        processed = 0
        failed = 0
        completed_operations = []

        for operation in queue[:]:  # Copy to avoid modification during iteration
            try:
                result = MobileOfflineManager._execute_queued_operation(operation)

                if result["success"]:
                    processed += 1
                    completed_operations.append(operation["operation_id"])
                    queue.remove(operation)
                    logger.info(f"Processed queued operation: {operation['operation_id']}")
                else:
                    failed += 1
                    operation["retry_count"] += 1
                    operation["last_retry"] = datetime.now().isoformat()
                    operation["status"] = "failed"

                    # Remove if too many retries
                    if operation["retry_count"] > MobileOfflineManager.MAX_RETRY_ATTEMPTS:
                        queue.remove(operation)
                        logger.warning(f"Removed failed operation after max retries: {operation['operation_id']}")

            except Exception as e:
                logger.error(f"Error processing queued operation {operation['operation_id']}: {e}")
                failed += 1

        return {
            "status": "processed",
            "processed": processed,
            "failed": failed,
            "completed_operations": completed_operations,
            "remaining_in_queue": len(queue),
        }

    @staticmethod
    def retry_with_backoff(
        operation_id: str, operation_func: Callable, max_attempts: int | None = None, backoff_base: float | None = None
    ) -> dict[str, Any]:
        """
        Retry an operation with exponential backoff.

        Args:
            operation_id: Unique identifier for the operation
            operation_func: Function to retry
            max_attempts: Maximum retry attempts
            backoff_base: Base for exponential backoff calculation

        Returns:
            Dictionary with retry results
        """
        if max_attempts is None:
            max_attempts = MobileOfflineManager.MAX_RETRY_ATTEMPTS

        if backoff_base is None:
            backoff_base = MobileOfflineManager.RETRY_BACKOFF_BASE

        retry_info = st.session_state[MobileOfflineManager.NETWORK_RETRY_KEY]

        if operation_id not in retry_info:
            retry_info[operation_id] = {"attempts": 0, "last_attempt": None, "failed_attempts": 0, "success_count": 0}

        operation_retry = retry_info[operation_id]

        # Check if we've exceeded max attempts
        if operation_retry["failed_attempts"] >= max_attempts:
            return {"success": False, "error": "Max retry attempts exceeded", "attempts": operation_retry["attempts"]}

        # Calculate backoff delay
        delay = backoff_base ** operation_retry["failed_attempts"]

        # Check if we need to wait for backoff
        if operation_retry["last_attempt"]:
            last_attempt_time = datetime.fromisoformat(operation_retry["last_attempt"])
            time_since_last = (datetime.now() - last_attempt_time).total_seconds()

            if time_since_last < delay:
                return {"success": False, "error": "Backoff period not elapsed", "wait_time": delay - time_since_last}

        # Attempt the operation
        try:
            operation_retry["attempts"] += 1
            operation_retry["last_attempt"] = datetime.now().isoformat()

            result = operation_func()

            # Success
            operation_retry["success_count"] += 1
            operation_retry["failed_attempts"] = 0  # Reset failed attempts on success

            logger.info(f"Retry successful for operation {operation_id} after {operation_retry['attempts']} attempts")

            return {"success": True, "result": result, "attempts": operation_retry["attempts"]}

        except Exception as e:
            operation_retry["failed_attempts"] += 1

            logger.warning(f"Retry failed for operation {operation_id}: {e} (attempt {operation_retry['attempts']})")

            return {
                "success": False,
                "error": str(e),
                "attempts": operation_retry["attempts"],
                "next_retry_in": backoff_base ** operation_retry["failed_attempts"],
            }

    @staticmethod
    def register_offline_capability(
        component_id: str, capability_level: OfflineCapability, cached_resources: list[str] | None = None, fallback_data: dict | None = None
    ) -> None:
        """
        Register offline capability for a component.

        Args:
            component_id: Unique identifier for the component
            capability_level: Level of offline capability
            cached_resources: List of resources that should be cached
            fallback_data: Fallback data to use when offline
        """
        capabilities = st.session_state[MobileOfflineManager.OFFLINE_CAPABILITIES_KEY]

        capabilities[component_id] = {
            "capability_level": capability_level.value,
            "cached_resources": cached_resources or [],
            "fallback_data": fallback_data or {},
            "registered_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }

        logger.info(f"Registered offline capability for {component_id}: {capability_level.value}")

    @staticmethod
    def get_offline_capability(component_id: str) -> OfflineCapability:
        """Get the offline capability level for a component."""
        capabilities = st.session_state[MobileOfflineManager.OFFLINE_CAPABILITIES_KEY]

        if component_id not in capabilities:
            return OfflineCapability.NONE

        capability_str = capabilities[component_id]["capability_level"]

        try:
            return OfflineCapability(capability_str)
        except ValueError:
            return OfflineCapability.NONE

    @staticmethod
    def can_function_offline(component_id: str) -> bool:
        """Check if a component can function offline."""
        capability = MobileOfflineManager.get_offline_capability(component_id)
        return capability in [OfflineCapability.FULL, OfflineCapability.LIMITED, OfflineCapability.CACHED]

    @staticmethod
    def get_offline_status_summary() -> dict[str, Any]:
        """Get comprehensive offline status summary."""
        network_info = st.session_state[MobileOfflineManager.NETWORK_STATUS_KEY]
        cache = st.session_state[MobileOfflineManager.OFFLINE_CACHE_KEY]
        queue = st.session_state[MobileOfflineManager.OFFLINE_QUEUE_KEY]
        capabilities = st.session_state[MobileOfflineManager.OFFLINE_CAPABILITIES_KEY]

        return {
            "network_status": network_info,
            "cache_info": {
                "total_entries": len(cache),
                "cache_size_mb": MobileOfflineManager._get_cache_size_mb(),
                "expired_entries": MobileOfflineManager._count_expired_cache_entries(),
            },
            "queue_info": {
                "total_operations": len(queue),
                "queued_operations": len([op for op in queue if op["status"] == "queued"]),
                "failed_operations": len([op for op in queue if op["status"] == "failed"]),
            },
            "capability_info": {
                "total_components": len(capabilities),
                "fully_offline": len([c for c in capabilities.values() if c["capability_level"] == "full"]),
                "limited_offline": len([c for c in capabilities.values() if c["capability_level"] == "limited"]),
                "cached_only": len([c for c in capabilities.values() if c["capability_level"] == "cached"]),
            },
            "last_updated": datetime.now().isoformat(),
        }

    @staticmethod
    def cleanup_offline_data(force: bool = False) -> dict[str, int]:
        """
        Clean up offline data (expired cache, old queue items, etc.).

        Args:
            force: If True, clean up all data regardless of expiry

        Returns:
            Dictionary with cleanup statistics
        """
        cleaned_cache = MobileOfflineManager._cleanup_cache(force)
        cleaned_queue = MobileOfflineManager._cleanup_queue(force)
        cleaned_retry = MobileOfflineManager._cleanup_retry_data(force)

        logger.info(f"Offline cleanup: {cleaned_cache} cache, {cleaned_queue} queue, {cleaned_retry} retry entries")

        return {
            "cache_entries_cleaned": cleaned_cache,
            "queue_entries_cleaned": cleaned_queue,
            "retry_entries_cleaned": cleaned_retry,
            "cleanup_timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def _register_default_capabilities() -> None:
        """Register default offline capabilities for PlantGuard components."""
        # Vision analysis - can work offline with cached models
        MobileOfflineManager.register_offline_capability(
            "camera_input",
            OfflineCapability.FULL,
            cached_resources=["vision_model", "class_mappings"],
            fallback_data={"message": "Using offline vision model"},
        )

        MobileOfflineManager.register_offline_capability(
            "upload_input",
            OfflineCapability.FULL,
            cached_resources=["vision_model", "class_mappings"],
            fallback_data={"message": "Using offline vision model"},
        )

        # Audio analysis - can work offline with Whisper
        MobileOfflineManager.register_offline_capability(
            "voice_input",
            OfflineCapability.FULL,
            cached_resources=["whisper_model", "audio_model"],
            fallback_data={"message": "Using offline speech recognition"},
        )

        # Text chat - limited offline (cached responses only)
        MobileOfflineManager.register_offline_capability(
            "text_input",
            OfflineCapability.LIMITED,
            cached_resources=["text_model", "knowledge_base"],
            fallback_data={"message": "Limited offline functionality - using cached responses"},
        )

        # Display components - can show cached data
        MobileOfflineManager.register_offline_capability(
            "analysis_display",
            OfflineCapability.CACHED,
            cached_resources=["previous_results"],
            fallback_data={"message": "Showing cached analysis results"},
        )

        MobileOfflineManager.register_offline_capability(
            "history_view", OfflineCapability.CACHED, cached_resources=["analysis_history"], fallback_data={"message": "Showing cached history"}
        )

        MobileOfflineManager.register_offline_capability(
            "chat_interface",
            OfflineCapability.LIMITED,
            cached_resources=["chat_history", "common_responses"],
            fallback_data={"message": "Limited chat functionality offline"},
        )

    @staticmethod
    def _assess_connection_quality() -> str:
        """Assess connection quality based on recent performance."""
        # In a real implementation, this would measure latency, bandwidth, etc.
        # For now, return a placeholder assessment
        retry_info = st.session_state[MobileOfflineManager.NETWORK_RETRY_KEY]

        total_failures = sum(info.get("failed_attempts", 0) for info in retry_info.values())

        if total_failures == 0:
            return "excellent"
        elif total_failures < 3:
            return "good"
        elif total_failures < 10:
            return "fair"
        else:
            return "poor"

    @staticmethod
    def _execute_queued_operation(operation: dict) -> dict[str, Any]:
        """Execute a queued operation."""
        try:
            operation_type = operation["operation_type"]
            operation_data = operation["operation_data"]

            # Handle different operation types
            if operation_type == "analysis":
                return MobileOfflineManager._execute_analysis_operation(operation_data)
            elif operation_type == "upload":
                return MobileOfflineManager._execute_upload_operation(operation_data)
            elif operation_type == "sync":
                return MobileOfflineManager._execute_sync_operation(operation_data)
            else:
                return {"success": False, "error": f"Unknown operation type: {operation_type}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _execute_analysis_operation(operation_data: dict) -> dict[str, Any]:
        """Execute a queued analysis operation."""
        # Placeholder for analysis operation execution
        # In a real implementation, this would call the appropriate adapter
        logger.info(f"Executing queued analysis operation: {operation_data}")
        return {"success": True, "result": "Analysis completed"}

    @staticmethod
    def _execute_upload_operation(operation_data: dict) -> dict[str, Any]:
        """Execute a queued upload operation."""
        # Placeholder for upload operation execution
        logger.info(f"Executing queued upload operation: {operation_data}")
        return {"success": True, "result": "Upload completed"}

    @staticmethod
    def _execute_sync_operation(operation_data: dict) -> dict[str, Any]:
        """Execute a queued sync operation."""
        # Placeholder for sync operation execution
        logger.info(f"Executing queued sync operation: {operation_data}")
        return {"success": True, "result": "Sync completed"}

    @staticmethod
    def _get_cache_size_mb() -> float:
        """Calculate approximate cache size in MB."""
        cache = st.session_state[MobileOfflineManager.OFFLINE_CACHE_KEY]

        total_size = 0
        for entry in cache.values():
            total_size += entry.get("size_estimate", 0)

        return total_size / (1024 * 1024)  # Convert to MB

    @staticmethod
    def _count_expired_cache_entries() -> int:
        """Count expired cache entries."""
        cache = st.session_state[MobileOfflineManager.OFFLINE_CACHE_KEY]

        expired_count = 0
        current_time = datetime.now()

        for entry in cache.values():
            try:
                expires_at = datetime.fromisoformat(entry["expires_at"])
                if current_time > expires_at:
                    expired_count += 1
            except (ValueError, KeyError):
                expired_count += 1  # Count malformed entries as expired

        return expired_count

    @staticmethod
    def _cleanup_cache(force: bool = False) -> int:
        """Clean up expired cache entries."""
        cache = st.session_state[MobileOfflineManager.OFFLINE_CACHE_KEY]

        cleaned_count = 0
        current_time = datetime.now()

        for key in list(cache.keys()):
            entry = cache[key]
            should_remove = force

            if not should_remove:
                try:
                    expires_at = datetime.fromisoformat(entry["expires_at"])
                    should_remove = current_time > expires_at
                except (ValueError, KeyError):
                    should_remove = True  # Remove malformed entries

            if should_remove:
                del cache[key]
                cleaned_count += 1

        return cleaned_count

    @staticmethod
    def _cleanup_queue(force: bool = False) -> int:
        """Clean up old queue entries."""
        queue = st.session_state[MobileOfflineManager.OFFLINE_QUEUE_KEY]

        if force:
            cleaned_count = len(queue)
            queue.clear()
            return cleaned_count

        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=24)  # Remove entries older than 24 hours

        for operation in queue[:]:  # Copy to avoid modification during iteration
            try:
                queued_at = datetime.fromisoformat(operation["queued_at"])
                if queued_at < cutoff_time:
                    queue.remove(operation)
                    cleaned_count += 1
            except (ValueError, KeyError):
                queue.remove(operation)  # Remove malformed entries
                cleaned_count += 1

        return cleaned_count

    @staticmethod
    def _cleanup_retry_data(force: bool = False) -> int:
        """Clean up old retry data."""
        retry_info = st.session_state[MobileOfflineManager.NETWORK_RETRY_KEY]

        if force:
            cleaned_count = len(retry_info)
            retry_info.clear()
            return cleaned_count

        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=12)  # Remove retry data older than 12 hours

        for operation_id in list(retry_info.keys()):
            operation_retry = retry_info[operation_id]

            try:
                if operation_retry.get("last_attempt"):
                    last_attempt = datetime.fromisoformat(operation_retry["last_attempt"])
                    if last_attempt < cutoff_time:
                        del retry_info[operation_id]
                        cleaned_count += 1
            except (ValueError, KeyError):
                del retry_info[operation_id]  # Remove malformed entries
                cleaned_count += 1

        return cleaned_count


# Utility functions for easy integration


def with_offline_support(operation_id: str, operation_func: Callable, fallback_func: Callable | None = None, cache_result: bool = True) -> Callable:
    """
    Decorator to add offline support to operations.

    Args:
        operation_id: Unique identifier for the operation
        operation_func: Function to execute when online
        fallback_func: Function to execute when offline
        cache_result: Whether to cache the result for offline use
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if MobileOfflineManager.is_online():
                try:
                    result = operation_func(*args, **kwargs)

                    if cache_result:
                        MobileOfflineManager.cache_resource(
                            f"{operation_id}_result", result, metadata={"operation_id": operation_id, "cached_from": "online_execution"}
                        )

                    return result

                except Exception as e:
                    logger.warning(f"Online operation failed, trying offline: {e}")

                    if fallback_func:
                        return fallback_func(*args, **kwargs)
                    else:
                        # Try to get cached result
                        cached_result = MobileOfflineManager.get_cached_resource(f"{operation_id}_result")
                        if cached_result:
                            st.info("Using cached result (offline mode)")
                            return cached_result
                        else:
                            raise e
            else:
                # Offline mode
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                else:
                    # Try to get cached result
                    cached_result = MobileOfflineManager.get_cached_resource(f"{operation_id}_result")
                    if cached_result:
                        st.info("Using cached result (offline mode)")
                        return cached_result
                    else:
                        # Queue for later execution
                        MobileOfflineManager.queue_offline_operation(operation_id, "deferred_execution", {"args": args, "kwargs": kwargs})
                        st.warning("Operation queued for when connection returns")
                        return None

        return wrapper

    return decorator


def ensure_offline_capability(component_id: str, required_resources: list[str] | None = None) -> Callable:
    """
    Ensure a component has the necessary offline capabilities.

    Args:
        component_id: Unique identifier for the component
        required_resources: List of resources required for offline operation
    """
    if not MobileOfflineManager.can_function_offline(component_id):
        st.warning(f"[WARNING] {component_id.replace('_', ' ').title()} requires internet connection")
        return False

    if required_resources:
        missing_resources = []
        for resource in required_resources:
            if not MobileOfflineManager.get_cached_resource(resource):
                missing_resources.append(resource)

        if missing_resources:
            st.warning(f"[WARNING] Missing offline resources: {', '.join(missing_resources)}")
            return False

    return True
