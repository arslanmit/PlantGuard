"""Training pipeline caching system for faster iterations.

This module provides caching mechanisms for training data, model states,
and intermediate results to speed up training iterations and experiments.
"""

import hashlib
import json
import logging
import pickle
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for training cache system."""

    # Cache directories
    cache_root: Path = Path("cache")
    model_cache_dir: Path | None = None
    data_cache_dir: Path | None = None
    feature_cache_dir: Path | None = None

    # Cache policies
    enable_model_caching: bool = True
    enable_data_caching: bool = True
    enable_feature_caching: bool = True
    enable_gradient_caching: bool = False

    # Cache limits
    max_cache_size_gb: float = 10.0
    max_cache_age_days: int = 30
    max_cached_items: int = 1000

    # Cache validation
    validate_cache_integrity: bool = True
    cache_version: str = "1.0"

    # Performance settings
    cache_compression: bool = True
    async_cache_writes: bool = True
    cache_prefetch: bool = True


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""

    key: str
    path: Path
    size_bytes: int
    created_time: float
    last_accessed: float
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str | None = None


class CacheManager:
    """Manages training cache operations and lifecycle."""

    def __init__(self, config: CacheConfig):
        """Initialize cache manager.

        Args:
            config: Cache configuration
        """
        self.config = config
        self.cache_index: dict[str, CacheEntry] = {}

        # Setup cache directories
        self._setup_cache_directories()

        # Load existing cache index
        self._load_cache_index()

        # Cleanup old cache entries
        self._cleanup_cache()

    def _setup_cache_directories(self) -> None:
        """Setup cache directory structure."""
        self.config.cache_root.mkdir(parents=True, exist_ok=True)

        if self.config.model_cache_dir is None:
            self.config.model_cache_dir = self.config.cache_root / "models"

        if self.config.data_cache_dir is None:
            self.config.data_cache_dir = self.config.cache_root / "data"

        if self.config.feature_cache_dir is None:
            self.config.feature_cache_dir = self.config.cache_root / "features"

        # Create subdirectories
        for cache_dir in [self.config.model_cache_dir, self.config.data_cache_dir, self.config.feature_cache_dir]:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_cache_index(self) -> None:
        """Load cache index from disk."""
        index_file = self.config.cache_root / "cache_index.json"

        if index_file.exists():
            try:
                with open(index_file) as f:
                    index_data = json.load(f)

                # Convert to CacheEntry objects
                for key, entry_data in index_data.items():
                    self.cache_index[key] = CacheEntry(
                        key=entry_data["key"],
                        path=Path(entry_data["path"]),
                        size_bytes=entry_data["size_bytes"],
                        created_time=entry_data["created_time"],
                        last_accessed=entry_data["last_accessed"],
                        access_count=entry_data.get("access_count", 0),
                        metadata=entry_data.get("metadata", {}),
                        checksum=entry_data.get("checksum"),
                    )

                logger.info(f"Loaded cache index with {len(self.cache_index)} entries")

            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self.cache_index = {}

    def _save_cache_index(self) -> None:
        """Save cache index to disk."""
        index_file = self.config.cache_root / "cache_index.json"

        try:
            # Convert CacheEntry objects to serializable format
            index_data = {}
            for key, entry in self.cache_index.items():
                index_data[key] = {
                    "key": entry.key,
                    "path": str(entry.path),
                    "size_bytes": entry.size_bytes,
                    "created_time": entry.created_time,
                    "last_accessed": entry.last_accessed,
                    "access_count": entry.access_count,
                    "metadata": entry.metadata,
                    "checksum": entry.checksum,
                }

            with open(index_file, "w") as f:
                json.dump(index_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    def _cleanup_cache(self) -> None:
        """Cleanup old and invalid cache entries."""
        current_time = time.time()
        max_age_seconds = self.config.max_cache_age_days * 24 * 3600

        entries_to_remove = []
        total_size = 0

        # Check for expired and invalid entries
        for key, entry in self.cache_index.items():
            # Check if file still exists
            if not entry.path.exists():
                entries_to_remove.append(key)
                continue

            # Check age
            if current_time - entry.created_time > max_age_seconds:
                entries_to_remove.append(key)
                continue

            # Validate integrity if enabled
            if self.config.validate_cache_integrity and entry.checksum:
                if not self._validate_cache_entry(entry):
                    entries_to_remove.append(key)
                    continue

            total_size += entry.size_bytes

        # Remove invalid entries
        for key in entries_to_remove:
            self._remove_cache_entry(key)

        # Check cache size limits
        if total_size > self.config.max_cache_size_gb * 1024**3:
            self._enforce_cache_size_limit()

        # Check item count limits
        if len(self.cache_index) > self.config.max_cached_items:
            self._enforce_cache_item_limit()

        logger.info(f"Cache cleanup completed: {len(entries_to_remove)} entries removed")

    def _validate_cache_entry(self, entry: CacheEntry) -> bool:
        """Validate cache entry integrity."""
        try:
            current_checksum = self._calculate_checksum(entry.path)
            return current_checksum == entry.checksum
        except Exception:
            return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _remove_cache_entry(self, key: str) -> None:
        """Remove cache entry and associated file."""
        if key in self.cache_index:
            entry = self.cache_index[key]

            # Remove file if it exists
            if entry.path.exists():
                try:
                    if entry.path.is_file():
                        entry.path.unlink()
                    elif entry.path.is_dir():
                        shutil.rmtree(entry.path)
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {entry.path}: {e}")

            # Remove from index
            del self.cache_index[key]

    def _enforce_cache_size_limit(self) -> None:
        """Enforce cache size limits by removing least recently used entries."""
        # Sort by last accessed time (LRU)
        sorted_entries = sorted(self.cache_index.items(), key=lambda x: x[1].last_accessed)

        total_size = sum(entry.size_bytes for _, entry in sorted_entries)
        max_size = self.config.max_cache_size_gb * 1024**3

        # Remove entries until under limit
        for key, entry in sorted_entries:
            if total_size <= max_size:
                break

            self._remove_cache_entry(key)
            total_size -= entry.size_bytes

    def _enforce_cache_item_limit(self) -> None:
        """Enforce cache item count limits."""
        if len(self.cache_index) <= self.config.max_cached_items:
            return

        # Sort by access count and last accessed time
        sorted_entries = sorted(self.cache_index.items(), key=lambda x: (x[1].access_count, x[1].last_accessed))

        # Remove least used entries
        entries_to_remove = len(self.cache_index) - self.config.max_cached_items
        for i in range(entries_to_remove):
            key, _ = sorted_entries[i]
            self._remove_cache_entry(key)

    def get_cache_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate cache key from arguments."""
        # Create a deterministic hash from arguments
        key_data = {
            "args": str(args),
            "kwargs": sorted(kwargs.items()),
            "version": self.config.cache_version,
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def has_cache(self, key: str) -> bool:
        """Check if cache entry exists and is valid."""
        if key not in self.cache_index:
            return False

        entry = self.cache_index[key]

        # Check if file exists
        if not entry.path.exists():
            self._remove_cache_entry(key)
            return False

        # Validate integrity if enabled
        if self.config.validate_cache_integrity and entry.checksum:
            if not self._validate_cache_entry(entry):
                self._remove_cache_entry(key)
                return False

        return True

    def get_from_cache(self, key: str) -> Any:
        """Retrieve item from cache."""
        if not self.has_cache(key):
            raise KeyError(f"Cache key not found: {key}")

        entry = self.cache_index[key]

        try:
            # Load cached data
            if entry.path.suffix == ".pt":
                try:
                    data = torch.load(entry.path, map_location="cpu", weights_only=True)
                except TypeError:
                    # Fallback for older PyTorch versions or legacy models
                    data = torch.load(entry.path, map_location="cpu", weights_only=False)
            elif entry.path.suffix == ".pkl":
                # WARNING: pickle.load can be unsafe with untrusted data
                # Only load from trusted cache files
                with open(entry.path, "rb") as f:
                    data = pickle.load(f)  # nosec B301
            else:
                # Try pickle as fallback
                # WARNING: pickle.load can be unsafe with untrusted data
                # Only load from trusted cache files
                with open(entry.path, "rb") as f:
                    data = pickle.load(f)  # nosec B301

            # Update access statistics
            entry.last_accessed = time.time()
            entry.access_count += 1

            logger.debug(f"Cache hit: {key}")
            return data

        except Exception as e:
            logger.error(f"Failed to load from cache {key}: {e}")
            self._remove_cache_entry(key)
            raise

    def put_in_cache(
        self,
        key: str,
        data: Any,
        cache_type: str = "data",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store item in cache."""
        # Determine cache directory
        if cache_type == "model":
            cache_dir = self.config.model_cache_dir
            file_ext = ".pt"
        elif cache_type == "features":
            cache_dir = self.config.feature_cache_dir
            file_ext = ".pt"
        else:
            cache_dir = self.config.data_cache_dir
            file_ext = ".pkl"

        # Create cache file path
        cache_file = cache_dir / f"{key}{file_ext}"

        try:
            # Save data
            if file_ext == ".pt":
                torch.save(data, cache_file)
            else:
                with open(cache_file, "wb") as f:
                    pickle.dump(data, f)

            # Calculate file size and checksum
            file_size = cache_file.stat().st_size
            checksum = self._calculate_checksum(cache_file) if self.config.validate_cache_integrity else None

            # Create cache entry
            entry = CacheEntry(
                key=key,
                path=cache_file,
                size_bytes=file_size,
                created_time=time.time(),
                last_accessed=time.time(),
                metadata=metadata or {},
                checksum=checksum,
            )

            # Add to index
            self.cache_index[key] = entry

            logger.debug(f"Cached: {key} ({file_size / 1024:.1f} KB)")

        except Exception as e:
            logger.error(f"Failed to cache {key}: {e}")
            # Clean up partial file
            if cache_file.exists():
                cache_file.unlink()
            raise

    def invalidate_cache(self, key: str) -> None:
        """Invalidate specific cache entry."""
        if key in self.cache_index:
            self._remove_cache_entry(key)
            logger.debug(f"Cache invalidated: {key}")

    def clear_cache(self, cache_type: str | None = None) -> None:
        """Clear cache entries."""
        if cache_type is None:
            # Clear all cache
            keys_to_remove = list(self.cache_index.keys())
        else:
            # Clear specific cache type
            if cache_type == "model":
                cache_dir = self.config.model_cache_dir
            elif cache_type == "features":
                cache_dir = self.config.feature_cache_dir
            else:
                cache_dir = self.config.data_cache_dir

            keys_to_remove = [key for key, entry in self.cache_index.items() if entry.path.parent == cache_dir]

        for key in keys_to_remove:
            self._remove_cache_entry(key)

        logger.info(f"Cleared {len(keys_to_remove)} cache entries")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(entry.size_bytes for entry in self.cache_index.values())
        total_items = len(self.cache_index)

        # Group by cache type
        type_stats = {}
        for entry in self.cache_index.values():
            cache_type = entry.path.parent.name
            if cache_type not in type_stats:
                type_stats[cache_type] = {"count": 0, "size_bytes": 0}

            type_stats[cache_type]["count"] += 1
            type_stats[cache_type]["size_bytes"] += entry.size_bytes

        return {
            "total_items": total_items,
            "total_size_mb": total_size / 1024**2,
            "total_size_gb": total_size / 1024**3,
            "cache_hit_ratio": self._calculate_hit_ratio(),
            "type_breakdown": type_stats,
            "oldest_entry": min((e.created_time for e in self.cache_index.values()), default=0),
            "newest_entry": max((e.created_time for e in self.cache_index.values()), default=0),
        }

    def _calculate_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        if not self.cache_index:
            return 0.0

        total_accesses = sum(entry.access_count for entry in self.cache_index.values())
        if total_accesses == 0:
            return 0.0

        # This is a simplified calculation
        # In practice, you'd track hits vs misses separately
        return min(1.0, total_accesses / len(self.cache_index))

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - save cache index."""
        self._save_cache_index()


class ModelStateCache:
    """Specialized cache for model states and checkpoints."""

    def __init__(self, cache_manager: CacheManager):
        """Initialize model state cache.

        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager

    def cache_model_state(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        config_hash: str,
    ) -> str:
        """Cache model state for quick resumption.

        Args:
            model: PyTorch model
            optimizer: Optimizer
            epoch: Current epoch
            config_hash: Hash of training configuration

        Returns:
            Cache key for the stored state
        """
        cache_key = self.cache_manager.get_cache_key(
            "model_state",
            config_hash,
            epoch,
        )

        state_dict = {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "epoch": epoch,
        }

        self.cache_manager.put_in_cache(
            cache_key,
            state_dict,
            cache_type="model",
            metadata={
                "epoch": epoch,
                "config_hash": config_hash,
                "model_type": type(model).__name__,
            },
        )

        return cache_key

    def load_model_state(
        self,
        cache_key: str,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
    ) -> int:
        """Load model state from cache.

        Args:
            cache_key: Cache key
            model: Model to load state into
            optimizer: Optimizer to load state into

        Returns:
            Epoch number from cached state
        """
        state_dict = self.cache_manager.get_from_cache(cache_key)

        model.load_state_dict(state_dict["model_state_dict"])
        optimizer.load_state_dict(state_dict["optimizer_state_dict"])

        return state_dict["epoch"]

    def find_cached_model_state(
        self,
        config_hash: str,
        target_epoch: int | None = None,
    ) -> str | None:
        """Find cached model state matching criteria.

        Args:
            config_hash: Configuration hash
            target_epoch: Target epoch (latest if None)

        Returns:
            Cache key if found, None otherwise
        """
        matching_entries = []

        for key, entry in self.cache_manager.cache_index.items():
            if entry.metadata.get("config_hash") == config_hash and "model_state" in key:
                matching_entries.append((key, entry.metadata.get("epoch", 0)))

        if not matching_entries:
            return None

        if target_epoch is None:
            # Return latest epoch
            return max(matching_entries, key=lambda x: x[1])[0]
        else:
            # Find exact or closest epoch
            best_match = min(
                matching_entries,
                key=lambda x: abs(x[1] - target_epoch),
            )
            return best_match[0]


class DatasetCache:
    """Specialized cache for processed datasets and features."""

    def __init__(self, cache_manager: CacheManager):
        """Initialize dataset cache.

        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager

    def cache_processed_dataset(
        self,
        dataset: Dataset,
        dataset_path: Path,
        preprocessing_config: dict[str, Any],
    ) -> str:
        """Cache processed dataset.

        Args:
            dataset: Processed dataset
            dataset_path: Original dataset path
            preprocessing_config: Preprocessing configuration

        Returns:
            Cache key for the cached dataset
        """
        cache_key = self.cache_manager.get_cache_key(
            "processed_dataset",
            str(dataset_path),
            preprocessing_config,
        )

        self.cache_manager.put_in_cache(
            cache_key,
            dataset,
            cache_type="data",
            metadata={
                "dataset_path": str(dataset_path),
                "preprocessing_config": preprocessing_config,
                "dataset_size": len(dataset),
            },
        )

        return cache_key

    def cache_feature_batch(
        self,
        features: torch.Tensor,
        batch_indices: list[int],
        model_hash: str,
    ) -> str:
        """Cache extracted features for a batch.

        Args:
            features: Extracted features
            batch_indices: Indices of samples in batch
            model_hash: Hash of the model used for extraction

        Returns:
            Cache key for the cached features
        """
        cache_key = self.cache_manager.get_cache_key(
            "feature_batch",
            tuple(batch_indices),
            model_hash,
        )

        self.cache_manager.put_in_cache(
            cache_key,
            features,
            cache_type="features",
            metadata={
                "batch_indices": batch_indices,
                "model_hash": model_hash,
                "feature_shape": list(features.shape),
            },
        )

        return cache_key


def create_cache_config(
    cache_root: str | Path = "cache",
    max_cache_size_gb: float = 10.0,
    enable_all_caching: bool = True,
) -> CacheConfig:
    """Create cache configuration with sensible defaults.

    Args:
        cache_root: Root directory for cache
        max_cache_size_gb: Maximum cache size in GB
        enable_all_caching: Whether to enable all caching features

    Returns:
        CacheConfig instance
    """
    return CacheConfig(
        cache_root=Path(cache_root),
        max_cache_size_gb=max_cache_size_gb,
        enable_model_caching=enable_all_caching,
        enable_data_caching=enable_all_caching,
        enable_feature_caching=enable_all_caching,
    )


def create_training_cache(config: CacheConfig | None = None) -> CacheManager:
    """Create training cache manager with default configuration.

    Args:
        config: Cache configuration (optional)

    Returns:
        CacheManager instance
    """
    if config is None:
        config = create_cache_config()

    return CacheManager(config)
