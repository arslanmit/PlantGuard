"""
Mobile Bundle Optimizer for PlantGuard UI.

This module provides bundle optimization and resource management for mobile devices,
focusing on reducing load times and optimizing resource delivery.

Requirements addressed:
- 6.4: Bundle size and loading performance optimization
- 6.5: Memory management for mobile constraints
"""

import base64
import gzip
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


@dataclass
class BundleResource:
    """Individual resource in a bundle."""

    id: str
    type: str  # 'css', 'js', 'image', 'data'
    content: str | bytes
    size: int
    compressed_size: int
    priority: int  # 1=critical, 2=important, 3=normal, 4=lazy
    dependencies: list[str]
    cache_duration: int  # seconds


@dataclass
class ResourceBundle:
    """Collection of optimized resources."""

    id: str
    name: str
    version: str
    created_at: str
    resources: list[BundleResource]
    total_size: int
    compressed_size: int
    load_order: list[str]
    metadata: dict[str, Any]


class MobileBundleOptimizer:
    """Bundle optimization system for mobile performance."""

    def __init__(self, cache_dir: Path | None = None):
        """
        Initialize bundle optimizer.

        Args:
            cache_dir: Directory for caching bundles
        """
        self.cache_dir = cache_dir or Path("data/cache/bundles")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._bundles: dict[str, ResourceBundle] = {}
        self._resource_registry: dict[str, BundleResource] = {}
        self._dependency_graph: dict[str, set[str]] = {}

        # Initialize session state
        self._initialize_bundle_state()

    def _initialize_bundle_state(self) -> None:
        """Initialize bundle state in session."""
        if "mobile_bundles" not in st.session_state:
            st.session_state.mobile_bundles = {
                "loaded_bundles": set(),
                "loading_queue": [],
                "failed_bundles": set(),
                "bundle_stats": {"total_loaded": 0, "total_size_mb": 0.0, "load_time_ms": 0.0},
            }

    def register_resource(
        self,
        resource_id: str,
        resource_type: str,
        content: str | bytes,
        priority: int = 3,
        dependencies: list[str] | None = None,
        cache_duration: int = 3600,
    ) -> bool:
        """
        Register a resource for bundling.

        Args:
            resource_id: Unique resource identifier
            resource_type: Type of resource (css, js, image, data)
            content: Resource content
            priority: Loading priority (1=critical, 4=lazy)
            dependencies: List of dependency resource IDs
            cache_duration: Cache duration in seconds

        Returns:
            True if registered successfully
        """
        try:
            # Calculate sizes
            if isinstance(content, str):
                content_bytes = content.encode("utf-8")
            else:
                content_bytes = content

            original_size = len(content_bytes)
            compressed_content = gzip.compress(content_bytes)
            compressed_size = len(compressed_content)

            # Create resource
            resource = BundleResource(
                id=resource_id,
                type=resource_type,
                content=content,
                size=original_size,
                compressed_size=compressed_size,
                priority=priority,
                dependencies=dependencies or [],
                cache_duration=cache_duration,
            )

            # Register resource
            self._resource_registry[resource_id] = resource

            # Update dependency graph
            self._dependency_graph[resource_id] = set(dependencies or [])

            logger.debug(f"Registered resource {resource_id}: {original_size} -> {compressed_size} bytes")
            return True

        except Exception as e:
            logger.error(f"Failed to register resource {resource_id}: {e}")
            return False

    def create_bundle(self, bundle_id: str, name: str, resource_ids: list[str], version: str = "1.0.0") -> ResourceBundle | None:
        """
        Create an optimized resource bundle.

        Args:
            bundle_id: Unique bundle identifier
            name: Human-readable bundle name
            resource_ids: List of resource IDs to include
            version: Bundle version

        Returns:
            Created bundle or None if failed
        """
        try:
            # Resolve dependencies and determine load order
            all_resource_ids = self._resolve_dependencies(resource_ids)
            load_order = self._calculate_load_order(all_resource_ids)

            # Collect resources
            bundle_resources = []
            total_size = 0
            compressed_size = 0

            for resource_id in load_order:
                if resource_id in self._resource_registry:
                    resource = self._resource_registry[resource_id]
                    bundle_resources.append(resource)
                    total_size += resource.size
                    compressed_size += resource.compressed_size
                else:
                    logger.warning(f"Resource not found: {resource_id}")

            # Create bundle
            bundle = ResourceBundle(
                id=bundle_id,
                name=name,
                version=version,
                created_at=datetime.now().isoformat(),
                resources=bundle_resources,
                total_size=total_size,
                compressed_size=compressed_size,
                load_order=load_order,
                metadata={
                    "compression_ratio": compressed_size / total_size if total_size > 0 else 0,
                    "resource_count": len(bundle_resources),
                    "critical_resources": len([r for r in bundle_resources if r.priority == 1]),
                    "created_by": "MobileBundleOptimizer",
                },
            )

            # Store bundle
            self._bundles[bundle_id] = bundle

            # Cache bundle to disk
            self._cache_bundle_to_disk(bundle)

            logger.info(f"Created bundle {bundle_id}: {len(bundle_resources)} resources, {total_size} -> {compressed_size} bytes")

            return bundle

        except Exception as e:
            logger.error(f"Failed to create bundle {bundle_id}: {e}")
            return None

    def load_bundle(self, bundle_id: str, force_reload: bool = False) -> bool:
        """
        Load a bundle into the application.

        Args:
            bundle_id: Bundle identifier
            force_reload: Force reload even if already loaded

        Returns:
            True if loaded successfully
        """
        bundle_state = st.session_state.mobile_bundles

        # Check if already loaded
        if not force_reload and bundle_id in bundle_state["loaded_bundles"]:
            return True

        # Check if bundle exists
        bundle = self._bundles.get(bundle_id)
        if not bundle:
            # Try to load from cache
            bundle = self._load_bundle_from_disk(bundle_id)
            if not bundle:
                logger.error(f"Bundle not found: {bundle_id}")
                bundle_state["failed_bundles"].add(bundle_id)
                return False

        try:
            start_time = datetime.now()

            # Load resources in priority order
            critical_resources = [r for r in bundle.resources if r.priority == 1]
            other_resources = [r for r in bundle.resources if r.priority > 1]

            # Load critical resources first
            for resource in critical_resources:
                self._load_resource(resource)

            # Load other resources
            for resource in other_resources:
                self._load_resource(resource)

            # Update bundle state
            load_time = (datetime.now() - start_time).total_seconds() * 1000
            bundle_state["loaded_bundles"].add(bundle_id)
            bundle_state["bundle_stats"]["total_loaded"] += 1
            bundle_state["bundle_stats"]["total_size_mb"] += bundle.compressed_size / (1024 * 1024)
            bundle_state["bundle_stats"]["load_time_ms"] += load_time

            logger.info(f"Loaded bundle {bundle_id} in {load_time:.1f}ms")
            return True

        except Exception as e:
            logger.error(f"Failed to load bundle {bundle_id}: {e}")
            bundle_state["failed_bundles"].add(bundle_id)
            return False

    def preload_critical_bundles(self) -> None:
        """Preload critical bundles for better performance."""
        critical_bundles = ["mobile_core_styles", "mobile_base_components", "mobile_icons"]

        for bundle_id in critical_bundles:
            if bundle_id in self._bundles:
                self.load_bundle(bundle_id)

    def create_css_bundle(self, css_files: dict[str, str], bundle_id: str = "mobile_styles") -> bool:
        """
        Create optimized CSS bundle.

        Args:
            css_files: Dictionary of {file_id: css_content}
            bundle_id: Bundle identifier

        Returns:
            True if created successfully
        """
        try:
            # Register CSS resources
            resource_ids = []
            for file_id, css_content in css_files.items():
                # Minify CSS
                minified_css = self._minify_css(css_content)

                resource_id = f"css_{file_id}"
                self.register_resource(
                    resource_id=resource_id,
                    resource_type="css",
                    content=minified_css,
                    priority=1,  # CSS is critical
                    cache_duration=86400,  # 24 hours
                )
                resource_ids.append(resource_id)

            # Create bundle
            bundle = self.create_bundle(bundle_id=bundle_id, name="Mobile CSS Bundle", resource_ids=resource_ids)

            return bundle is not None

        except Exception as e:
            logger.error(f"Failed to create CSS bundle: {e}")
            return False

    def create_image_bundle(self, images: dict[str, bytes], bundle_id: str = "mobile_images") -> bool:
        """
        Create optimized image bundle.

        Args:
            images: Dictionary of {image_id: image_data}
            bundle_id: Bundle identifier

        Returns:
            True if created successfully
        """
        try:
            resource_ids = []

            for image_id, image_data in images.items():
                # Optimize image
                optimized_data = self._optimize_image(image_data)

                resource_id = f"img_{image_id}"
                self.register_resource(
                    resource_id=resource_id,
                    resource_type="image",
                    content=optimized_data,
                    priority=2,  # Images are important but not critical
                    cache_duration=86400,  # 24 hours
                )
                resource_ids.append(resource_id)

            # Create bundle
            bundle = self.create_bundle(bundle_id=bundle_id, name="Mobile Image Bundle", resource_ids=resource_ids)

            return bundle is not None

        except Exception as e:
            logger.error(f"Failed to create image bundle: {e}")
            return False

    def get_bundle_stats(self) -> dict[str, Any]:
        """Get bundle statistics."""
        bundle_state = st.session_state.mobile_bundles

        total_bundles = len(self._bundles)
        loaded_bundles = len(bundle_state["loaded_bundles"])
        failed_bundles = len(bundle_state["failed_bundles"])

        return {
            "total_bundles": total_bundles,
            "loaded_bundles": loaded_bundles,
            "failed_bundles": failed_bundles,
            "load_success_rate": (loaded_bundles / total_bundles * 100) if total_bundles > 0 else 0,
            "bundle_stats": bundle_state["bundle_stats"].copy(),
            "cache_size_mb": self._get_cache_size_mb(),
        }

    def cleanup_old_bundles(self, max_age_days: int = 7) -> int:
        """
        Clean up old cached bundles.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of bundles cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0

        try:
            for bundle_file in self.cache_dir.glob("*.bundle"):
                if bundle_file.stat().st_mtime < cutoff_date.timestamp():
                    bundle_file.unlink()
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} old bundles")

        except Exception as e:
            logger.error(f"Failed to cleanup old bundles: {e}")

        return cleaned_count

    def _resolve_dependencies(self, resource_ids: list[str]) -> list[str]:
        """Resolve all dependencies for given resources."""
        resolved = set()
        to_process = set(resource_ids)

        while to_process:
            resource_id = to_process.pop()
            if resource_id in resolved:
                continue

            resolved.add(resource_id)

            # Add dependencies
            dependencies = self._dependency_graph.get(resource_id, set())
            to_process.update(dependencies - resolved)

        return list(resolved)

    def _calculate_load_order(self, resource_ids: list[str]) -> list[str]:
        """Calculate optimal load order based on dependencies and priorities."""
        # Topological sort with priority consideration
        in_degree = dict.fromkeys(resource_ids, 0)
        graph = {rid: [] for rid in resource_ids}

        # Build graph and calculate in-degrees
        for resource_id in resource_ids:
            dependencies = self._dependency_graph.get(resource_id, set())
            for dep in dependencies:
                if dep in resource_ids:
                    graph[dep].append(resource_id)
                    in_degree[resource_id] += 1

        # Priority queue (lower priority number = higher priority)
        queue = []
        for resource_id in resource_ids:
            if in_degree[resource_id] == 0:
                resource = self._resource_registry.get(resource_id)
                priority = resource.priority if resource else 999
                queue.append((priority, resource_id))

        queue.sort()  # Sort by priority

        result = []
        while queue:
            _, resource_id = queue.pop(0)
            result.append(resource_id)

            # Update neighbors
            for neighbor in graph[resource_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    resource = self._resource_registry.get(neighbor)
                    priority = resource.priority if resource else 999
                    queue.append((priority, neighbor))
                    queue.sort()  # Re-sort after adding

        return result

    def _load_resource(self, resource: BundleResource) -> None:
        """Load individual resource into application."""
        if resource.type == "css":
            # Inject CSS
            st.markdown(f"<style>{resource.content}</style>", unsafe_allow_html=True)
        elif resource.type == "js":
            # Inject JavaScript
            st.markdown(f"<script>{resource.content}</script>", unsafe_allow_html=True)
        elif resource.type == "image":
            # Store image in session state for later use
            if "mobile_images" not in st.session_state:
                st.session_state.mobile_images = {}

            # Convert bytes to base64 for storage
            if isinstance(resource.content, bytes):
                encoded_content = base64.b64encode(resource.content).decode("utf-8")
                st.session_state.mobile_images[resource.id] = encoded_content
        elif resource.type == "data":
            # Store data in session state
            if "mobile_data" not in st.session_state:
                st.session_state.mobile_data = {}
            st.session_state.mobile_data[resource.id] = resource.content

    def _cache_bundle_to_disk(self, bundle: ResourceBundle) -> None:
        """Cache bundle to disk for persistence."""
        try:
            bundle_file = self.cache_dir / f"{bundle.id}.bundle"

            # Convert bundle to serializable format
            bundle_data = {"bundle": asdict(bundle), "cached_at": datetime.now().isoformat()}

            # Compress and save
            json_data = json.dumps(bundle_data).encode("utf-8")
            compressed_data = gzip.compress(json_data)

            with open(bundle_file, "wb") as f:
                f.write(compressed_data)

            logger.debug(f"Cached bundle {bundle.id} to disk")

        except Exception as e:
            logger.warning(f"Failed to cache bundle {bundle.id}: {e}")

    def _load_bundle_from_disk(self, bundle_id: str) -> ResourceBundle | None:
        """Load bundle from disk cache."""
        try:
            bundle_file = self.cache_dir / f"{bundle_id}.bundle"

            if not bundle_file.exists():
                return None

            # Load and decompress
            with open(bundle_file, "rb") as f:
                compressed_data = f.read()

            json_data = gzip.decompress(compressed_data)
            bundle_data = json.loads(json_data.decode("utf-8"))

            # Reconstruct bundle
            bundle_dict = bundle_data["bundle"]

            # Reconstruct resources
            resources = []
            for resource_dict in bundle_dict["resources"]:
                resource = BundleResource(**resource_dict)
                resources.append(resource)

            bundle_dict["resources"] = resources
            bundle = ResourceBundle(**bundle_dict)

            # Store in memory
            self._bundles[bundle_id] = bundle

            logger.debug(f"Loaded bundle {bundle_id} from disk cache")
            return bundle

        except Exception as e:
            logger.warning(f"Failed to load bundle {bundle_id} from cache: {e}")
            return None

    def _minify_css(self, css_content: str) -> str:
        """Simple CSS minification."""
        # Remove comments
        import re

        css_content = re.sub(r"/\*.*?\*/", "", css_content, flags=re.DOTALL)

        # Remove extra whitespace
        css_content = re.sub(r"\s+", " ", css_content)
        css_content = re.sub(r";\s*}", "}", css_content)
        css_content = re.sub(r"{\s*", "{", css_content)
        css_content = re.sub(r"}\s*", "}", css_content)
        css_content = re.sub(r":\s*", ":", css_content)
        css_content = re.sub(r";\s*", ";", css_content)

        return css_content.strip()

    def _optimize_image(self, image_data: bytes) -> bytes:
        """Optimize image for mobile display."""
        try:
            import io

            from PIL import Image

            # Load image
            image = Image.open(io.BytesIO(image_data))

            # Optimize for mobile (max 800px width, 85% quality)
            if image.width > 800:
                ratio = 800 / image.width
                new_height = int(image.height * ratio)
                image = image.resize((800, new_height), Image.Resampling.LANCZOS)

            # Convert to RGB if necessary
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Save optimized
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)

            return output.getvalue()

        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")
            return image_data

    def _get_cache_size_mb(self) -> float:
        """Get total cache size in MB."""
        try:
            total_size = 0
            for bundle_file in self.cache_dir.glob("*.bundle"):
                total_size += bundle_file.stat().st_size
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0


# Global bundle optimizer instance
mobile_bundle_optimizer = MobileBundleOptimizer()


def create_mobile_css_bundle(css_files: dict[str, str]) -> bool:
    """Create optimized CSS bundle for mobile."""
    return mobile_bundle_optimizer.create_css_bundle(css_files)


def load_mobile_bundle(bundle_id: str) -> bool:
    """Load mobile bundle."""
    return mobile_bundle_optimizer.load_bundle(bundle_id)


def preload_critical_mobile_resources() -> None:
    """Preload critical mobile resources."""
    mobile_bundle_optimizer.preload_critical_bundles()
