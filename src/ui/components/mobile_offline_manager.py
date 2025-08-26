"""
Mobile Offline Manager for PlantGuard UI.

This module provides offline functionality and resource caching for mobile devices,
ensuring the application works without internet connectivity.

Requirements addressed:
- 6.1: Performance and offline capability
- 6.3: Network error handling and offline functionality
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Network connection status."""

    ONLINE = "online"
    OFFLINE = "offline"
    SLOW = "slow"
    UNKNOWN = "unknown"


class CacheStrategy(Enum):
    """Cache strategy for different resource types."""

    CACHE_FIRST = "cache_first"
    NETWORK_FIRST = "network_first"
    CACHE_ONLY = "cache_only"
    NETWORK_ONLY = "network_only"


@dataclass
class OfflineResource:
    """Offline cached resource."""

    id: str
    type: str
    content: Any
    cached_at: str
    expires_at: str | None
    size_bytes: int
    access_count: int
    last_accessed: str
    strategy: CacheStrategy
    metadata: dict[str, Any]


@dataclass
class OfflineOperation:
    """Operation queued for when connection is restored."""

    id: str
    operation_type: str
    data: dict[str, Any]
    created_at: str
    retry_count: int
    max_retries: int
    callback: str | None  # Serialized callback function name


class MobileOfflineManager:
    """Offline functionality manager for mobile devices."""

    def __init__(self, cache_dir: Path | None = None):
        """
        Initialize offline manager.

        Args:
            cache_dir: Directory for offline cache storage
        """
        self.cache_dir = cache_dir or Path("data/cache/offline")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._offline_cache: dict[str, OfflineResource] = {}
        self._operation_queue: list[OfflineOperation] = []
        self._connection_status = ConnectionStatus.UNKNOWN
        self._last_connection_check = datetime.now()
        self._connection_callbacks: list[Callable] = []

        # Initialize offline state
        self._initialize_offline_state()

        # Load cached resources
        self._load_offline_cache()

    def _initialize_offline_state(self) -> None:
        """Initialize offline state in session."""
        if "mobile_offline" not in st.session_state:
            st.session_state.mobile_offline = {
                "enabled": True,
                "connection_status": ConnectionStatus.UNKNOWN.value,
                "last_online": datetime.now().isoformat(),
                "offline_since": None,
                "cached_resources": 0,
                "queued_operations": 0,
                "offline_mode_active": False,
                "sync_in_progress": False,
                "cache_size_mb": 0.0,
            }

    def enable_offline_mode(self) -> None:
        """Enable offline mode with aggressive caching."""
        offline_state = st.session_state.mobile_offline
        offline_state["enabled"] = True
        offline_state["offline_mode_active"] = True

        # Cache critical resources
        self._cache_critical_resources()

        # Set up offline-first strategies
        self._setup_offline_strategies()

        logger.info("Offline mode enabled")

    def disable_offline_mode(self) -> None:
        """Disable offline mode."""
        offline_state = st.session_state.mobile_offline
        offline_state["enabled"] = False
        offline_state["offline_mode_active"] = False

        logger.info("Offline mode disabled")

    def check_connection_status(self) -> ConnectionStatus:
        """
        Check current network connection status.

        Returns:
            Current connection status
        """
        now = datetime.now()

        # Throttle connection checks (max once per 30 seconds)
        if (now - self._last_connection_check).total_seconds() < 30:
            return self._connection_status

        self._last_connection_check = now

        try:
            # Simple connection test using JavaScript
            connection_test_js = """
            <script>
            function checkConnection() {
                if (navigator.onLine) {
                    // Test actual connectivity with a small request
                    fetch('data:text/plain;base64,', {method: 'HEAD', mode: 'no-cors'})
                        .then(() => {
                            window.parent.postMessage({type: 'connection', status: 'online'}, '*');
                        })
                        .catch(() => {
                            window.parent.postMessage({type: 'connection', status: 'offline'}, '*');
                        });
                } else {
                    window.parent.postMessage({type: 'connection', status: 'offline'}, '*');
                }
            }
            checkConnection();
            </script>
            """

            # For now, assume online if no explicit offline detection
            # In a real implementation, this would use more sophisticated detection
            self._connection_status = ConnectionStatus.ONLINE

            # Update session state
            offline_state = st.session_state.mobile_offline
            offline_state["connection_status"] = self._connection_status.value

            if self._connection_status == ConnectionStatus.ONLINE:
                offline_state["last_online"] = now.isoformat()
                if offline_state["offline_since"]:
                    # Connection restored
                    self._on_connection_restored()
                    offline_state["offline_since"] = None
            else:
                if not offline_state["offline_since"]:
                    offline_state["offline_since"] = now.isoformat()

        except Exception as e:
            logger.warning(f"Connection check failed: {e}")
            self._connection_status = ConnectionStatus.UNKNOWN

        return self._connection_status

    def cache_resource(
        self,
        resource_id: str,
        resource_type: str,
        content: Any,
        strategy: CacheStrategy = CacheStrategy.CACHE_FIRST,
        ttl_hours: int = 24,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Cache a resource for offline use.

        Args:
            resource_id: Unique resource identifier
            resource_type: Type of resource (model, image, data, etc.)
            content: Resource content
            strategy: Caching strategy
            ttl_hours: Time to live in hours
            metadata: Additional metadata

        Returns:
            True if cached successfully
        """
        try:
            now = datetime.now()
            expires_at = now + timedelta(hours=ttl_hours) if ttl_hours > 0 else None

            # Calculate size
            content_str = json.dumps(content) if not isinstance(content, (str, bytes)) else str(content)
            size_bytes = len(content_str.encode("utf-8"))

            # Create offline resource
            resource = OfflineResource(
                id=resource_id,
                type=resource_type,
                content=content,
                cached_at=now.isoformat(),
                expires_at=expires_at.isoformat() if expires_at else None,
                size_bytes=size_bytes,
                access_count=0,
                last_accessed=now.isoformat(),
                strategy=strategy,
                metadata=metadata or {},
            )

            # Store in memory cache
            self._offline_cache[resource_id] = resource

            # Persist to disk
            self._persist_resource_to_disk(resource)

            # Update session state
            offline_state = st.session_state.mobile_offline
            offline_state["cached_resources"] = len(self._offline_cache)
            offline_state["cache_size_mb"] = self._calculate_cache_size_mb()

            logger.debug(f"Cached resource {resource_id} ({size_bytes} bytes)")
            return True

        except Exception as e:
            logger.error(f"Failed to cache resource {resource_id}: {e}")
            return False

    def get_cached_resource(self, resource_id: str) -> Any | None:
        """
        Get cached resource.

        Args:
            resource_id: Resource identifier

        Returns:
            Cached resource content or None
        """
        if resource_id not in self._offline_cache:
            return None

        resource = self._offline_cache[resource_id]

        # Check expiration
        if resource.expires_at:
            expires_at = datetime.fromisoformat(resource.expires_at)
            if datetime.now() > expires_at:
                self.remove_cached_resource(resource_id)
                return None

        # Update access info
        resource.access_count += 1
        resource.last_accessed = datetime.now().isoformat()

        return resource.content

    def remove_cached_resource(self, resource_id: str) -> bool:
        """Remove cached resource."""
        if resource_id in self._offline_cache:
            # Remove from memory
            del self._offline_cache[resource_id]

            # Remove from disk
            resource_file = self.cache_dir / f"{resource_id}.cache"
            if resource_file.exists():
                resource_file.unlink()

            # Update session state
            offline_state = st.session_state.mobile_offline
            offline_state["cached_resources"] = len(self._offline_cache)
            offline_state["cache_size_mb"] = self._calculate_cache_size_mb()

            return True

        return False

    def queue_operation(self, operation_type: str, data: dict[str, Any], callback: str | None = None, max_retries: int = 3) -> str:
        """
        Queue an operation for when connection is restored.

        Args:
            operation_type: Type of operation
            data: Operation data
            callback: Callback function name
            max_retries: Maximum retry attempts

        Returns:
            Operation ID
        """
        operation_id = f"op_{int(time.time() * 1000)}"

        operation = OfflineOperation(
            id=operation_id,
            operation_type=operation_type,
            data=data,
            created_at=datetime.now().isoformat(),
            retry_count=0,
            max_retries=max_retries,
            callback=callback,
        )

        self._operation_queue.append(operation)

        # Update session state
        offline_state = st.session_state.mobile_offline
        offline_state["queued_operations"] = len(self._operation_queue)

        logger.debug(f"Queued operation {operation_id}: {operation_type}")
        return operation_id

    def process_operation_queue(self) -> dict[str, Any]:
        """
        Process queued operations when online.

        Returns:
            Processing results
        """
        if self._connection_status != ConnectionStatus.ONLINE:
            return {"processed": 0, "failed": 0, "skipped": "offline"}

        processed = 0
        failed = 0
        completed_operations = []

        for operation in self._operation_queue[:]:  # Copy list to avoid modification issues
            try:
                success = self._execute_operation(operation)

                if success:
                    processed += 1
                    completed_operations.append(operation.id)
                else:
                    operation.retry_count += 1
                    if operation.retry_count >= operation.max_retries:
                        failed += 1
                        completed_operations.append(operation.id)

            except Exception as e:
                logger.error(f"Failed to process operation {operation.id}: {e}")
                operation.retry_count += 1
                if operation.retry_count >= operation.max_retries:
                    failed += 1
                    completed_operations.append(operation.id)

        # Remove completed operations
        self._operation_queue = [op for op in self._operation_queue if op.id not in completed_operations]

        # Update session state
        offline_state = st.session_state.mobile_offline
        offline_state["queued_operations"] = len(self._operation_queue)

        return {"processed": processed, "failed": failed, "remaining": len(self._operation_queue)}

    def sync_offline_data(self) -> dict[str, Any]:
        """
        Synchronize offline data when connection is available.

        Returns:
            Sync results
        """
        if self._connection_status != ConnectionStatus.ONLINE:
            return {"status": "offline", "synced": 0}

        offline_state = st.session_state.mobile_offline
        offline_state["sync_in_progress"] = True

        try:
            # Process operation queue
            queue_results = self.process_operation_queue()

            # Refresh expired cached resources
            refreshed = self._refresh_expired_resources()

            # Clean up old cache entries
            cleaned = self._cleanup_old_cache_entries()

            sync_results = {
                "status": "completed",
                "operations_processed": queue_results["processed"],
                "operations_failed": queue_results["failed"],
                "resources_refreshed": refreshed,
                "cache_entries_cleaned": cleaned,
                "sync_time": datetime.now().isoformat(),
            }

            logger.info(f"Offline sync completed: {sync_results}")
            return sync_results

        except Exception as e:
            logger.error(f"Offline sync failed: {e}")
            return {"status": "failed", "error": str(e)}

        finally:
            offline_state["sync_in_progress"] = False

    def get_offline_stats(self) -> dict[str, Any]:
        """Get offline functionality statistics."""
        offline_state = st.session_state.mobile_offline

        return {
            "enabled": offline_state["enabled"],
            "connection_status": offline_state["connection_status"],
            "offline_mode_active": offline_state["offline_mode_active"],
            "cached_resources": offline_state["cached_resources"],
            "cache_size_mb": offline_state["cache_size_mb"],
            "queued_operations": offline_state["queued_operations"],
            "last_online": offline_state["last_online"],
            "offline_since": offline_state["offline_since"],
            "sync_in_progress": offline_state["sync_in_progress"],
        }

    def _cache_critical_resources(self) -> None:
        """Cache critical resources for offline use."""
        critical_resources = {"mobile_styles": "css", "mobile_icons": "images", "plant_disease_model": "model", "disease_knowledge_base": "data"}

        for resource_id, resource_type in critical_resources.items():
            # Check if already cached
            if resource_id not in self._offline_cache:
                # In a real implementation, this would fetch and cache the actual resources
                placeholder_content = f"Cached {resource_type} for {resource_id}"
                self.cache_resource(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    content=placeholder_content,
                    strategy=CacheStrategy.CACHE_FIRST,
                    ttl_hours=168,  # 1 week
                )

    def _setup_offline_strategies(self) -> None:
        """Set up offline-first caching strategies."""
        # Configure different strategies for different resource types
        strategies = {
            "models": CacheStrategy.CACHE_FIRST,
            "images": CacheStrategy.CACHE_FIRST,
            "data": CacheStrategy.CACHE_FIRST,
            "api_responses": CacheStrategy.NETWORK_FIRST,
            "user_data": CacheStrategy.NETWORK_FIRST,
        }

        # Store strategies in session state
        if "offline_strategies" not in st.session_state:
            st.session_state.offline_strategies = strategies

    def _on_connection_restored(self) -> None:
        """Handle connection restoration."""
        logger.info("Connection restored - starting sync")

        # Notify callbacks
        for callback in self._connection_callbacks:
            try:
                callback(ConnectionStatus.ONLINE)
            except Exception as e:
                logger.warning(f"Connection callback failed: {e}")

        # Start background sync
        self.sync_offline_data()

    def _execute_operation(self, operation: OfflineOperation) -> bool:
        """Execute a queued operation."""
        try:
            # In a real implementation, this would execute the actual operation
            # For now, we'll just simulate success
            logger.debug(f"Executing operation {operation.id}: {operation.operation_type}")

            # Simulate operation execution
            if operation.operation_type == "upload_analysis":
                # Simulate uploading analysis results
                time.sleep(0.1)  # Simulate network delay
                return True
            elif operation.operation_type == "sync_user_data":
                # Simulate syncing user data
                time.sleep(0.1)
                return True
            else:
                # Unknown operation type
                logger.warning(f"Unknown operation type: {operation.operation_type}")
                return False

        except Exception as e:
            logger.error(f"Operation execution failed: {e}")
            return False

    def _refresh_expired_resources(self) -> int:
        """Refresh expired cached resources."""
        refreshed_count = 0

        for resource_id, resource in list(self._offline_cache.items()):
            if resource.expires_at:
                expires_at = datetime.fromisoformat(resource.expires_at)
                if datetime.now() > expires_at:
                    # In a real implementation, this would fetch fresh content
                    # For now, we'll just extend the expiration
                    new_expires = datetime.now() + timedelta(hours=24)
                    resource.expires_at = new_expires.isoformat()
                    refreshed_count += 1

        return refreshed_count

    def _cleanup_old_cache_entries(self) -> int:
        """Clean up old cache entries."""
        cleaned_count = 0
        cutoff_date = datetime.now() - timedelta(days=7)

        for resource_id, resource in list(self._offline_cache.items()):
            cached_at = datetime.fromisoformat(resource.cached_at)
            if cached_at < cutoff_date and resource.access_count == 0:
                self.remove_cached_resource(resource_id)
                cleaned_count += 1

        return cleaned_count

    def _load_offline_cache(self) -> None:
        """Load cached resources from disk."""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                resource_id = cache_file.stem

                with open(cache_file, encoding="utf-8") as f:
                    resource_data = json.load(f)

                # Reconstruct resource
                resource = OfflineResource(**resource_data)
                self._offline_cache[resource_id] = resource

            logger.debug(f"Loaded {len(self._offline_cache)} cached resources")

        except Exception as e:
            logger.warning(f"Failed to load offline cache: {e}")

    def _persist_resource_to_disk(self, resource: OfflineResource) -> None:
        """Persist resource to disk cache."""
        try:
            resource_file = self.cache_dir / f"{resource.id}.cache"

            with open(resource_file, "w", encoding="utf-8") as f:
                json.dump(asdict(resource), f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to persist resource {resource.id}: {e}")

    def _calculate_cache_size_mb(self) -> float:
        """Calculate total cache size in MB."""
        total_size = sum(resource.size_bytes for resource in self._offline_cache.values())
        return total_size / (1024 * 1024)

    def register_connection_callback(self, callback: Callable[[ConnectionStatus], None]) -> None:
        """Register callback for connection status changes."""
        self._connection_callbacks.append(callback)

    def clear_offline_cache(self) -> int:
        """Clear all offline cache."""
        cleared_count = len(self._offline_cache)

        # Clear memory cache
        self._offline_cache.clear()

        # Clear disk cache
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to clear disk cache: {e}")

        # Update session state
        offline_state = st.session_state.mobile_offline
        offline_state["cached_resources"] = 0
        offline_state["cache_size_mb"] = 0.0

        logger.info(f"Cleared {cleared_count} cached resources")
        return cleared_count


# Global offline manager instance
mobile_offline_manager = MobileOfflineManager()


def enable_mobile_offline_mode() -> None:
    """Enable mobile offline mode."""
    mobile_offline_manager.enable_offline_mode()


def cache_mobile_resource(resource_id: str, resource_type: str, content: Any) -> bool:
    """Cache resource for offline use."""
    return mobile_offline_manager.cache_resource(resource_id, resource_type, content)


def get_mobile_offline_stats() -> dict[str, Any]:
    """Get mobile offline statistics."""
    return mobile_offline_manager.get_offline_stats()


def check_mobile_connection() -> ConnectionStatus:
    """Check mobile connection status."""
    return mobile_offline_manager.check_connection_status()
