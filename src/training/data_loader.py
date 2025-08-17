"""Optimized data loading and preprocessing pipeline for production training.

This module provides efficient data loading with multi-processing, prefetching,
memory-mapped dataset loading, and data loading profiling capabilities.
"""

import logging
import multiprocessing as mp
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.datasets import ImageFolder

logger = logging.getLogger(__name__)


@dataclass
class DataLoadingConfig:
    """Configuration for optimized data loading."""

    # Multi-processing settings
    num_workers: int = 0  # Will be auto-detected
    pin_memory: bool = True
    persistent_workers: bool = True
    prefetch_factor: int = 2

    # Memory optimization
    use_memory_mapping: bool = False
    memory_map_threshold_gb: float = 1.0  # Use memory mapping for datasets > 1GB

    # Profiling settings
    enable_profiling: bool = False
    profile_batches: int = 10

    # Data augmentation optimization
    cache_augmented_data: bool = False
    augmentation_workers: int = 2


@dataclass
class DataLoadingProfile:
    """Profiling results for data loading performance."""

    avg_batch_time: float = 0.0
    min_batch_time: float = float("inf")
    max_batch_time: float = 0.0
    total_time: float = 0.0
    batches_profiled: int = 0
    throughput_samples_per_sec: float = 0.0
    memory_usage_mb: float = 0.0
    bottlenecks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class MemoryMappedImageFolder(Dataset):
    """Memory-mapped version of ImageFolder for large datasets."""

    def __init__(
        self,
        root: str | Path,
        transform: Callable | None = None,
        target_transform: Callable | None = None,
    ) -> None:
        """Initialize memory-mapped image folder.

        Args:
            root: Root directory path
            transform: Transform to apply to images
            target_transform: Transform to apply to targets
        """
        self.root = Path(root)
        self.transform = transform
        self.target_transform = target_transform

        # Build file index
        self.samples: list[tuple[Path, int]] = []
        self.class_to_idx: dict[str, int] = {}
        self.classes: list[str] = []

        self._build_index()

        # Memory map files if beneficial
        self._setup_memory_mapping()

    def _build_index(self) -> None:
        """Build index of all image files."""
        logger.info("Building dataset index...")

        # Get all class directories
        class_dirs = [d for d in self.root.iterdir() if d.is_dir()]
        class_dirs.sort()

        self.classes = [d.name for d in class_dirs]
        self.class_to_idx = {cls_name: idx for idx, cls_name in enumerate(self.classes)}

        # Index all image files
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

        for class_dir in class_dirs:
            class_idx = self.class_to_idx[class_dir.name]

            for img_path in class_dir.iterdir():
                if img_path.suffix.lower() in image_extensions:
                    self.samples.append((img_path, class_idx))

        logger.info(f"Indexed {len(self.samples)} samples from {len(self.classes)} classes")

    def _setup_memory_mapping(self) -> None:
        """Setup memory mapping for large datasets."""
        # Calculate total dataset size
        total_size = sum(sample[0].stat().st_size for sample in self.samples)
        total_size_gb = total_size / (1024**3)

        logger.info(f"Dataset size: {total_size_gb:.2f} GB")

        # For now, we'll use standard file loading
        # Memory mapping can be implemented for very large datasets
        self.use_memory_mapping = False

    def __len__(self) -> int:
        """Return number of samples."""
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[Any, int]:
        """Get sample at index."""
        img_path, target = self.samples[index]

        # Load image
        try:
            with Image.open(img_path) as img:
                img = img.convert("RGB")

                if self.transform is not None:
                    img = self.transform(img)

                if self.target_transform is not None:
                    target = self.target_transform(target)

                return img, target

        except Exception as e:
            logger.warning(f"Failed to load image {img_path}: {e}")
            # Return a black image as fallback
            if self.transform is not None:
                fallback_img = self.transform(Image.new("RGB", (224, 224), (0, 0, 0)))
            else:
                fallback_img = transforms.ToTensor()(Image.new("RGB", (224, 224), (0, 0, 0)))

            return fallback_img, target


class OptimizedDataAugmentation:
    """Optimized data augmentation pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize optimized augmentation.

        Args:
            config: Augmentation configuration
        """
        self.config = config
        self.cache_enabled = config.get("cache_augmented_data", False)
        self.augmentation_cache: dict[str, Any] = {}

    def get_train_transforms(self) -> transforms.Compose:
        """Get optimized training transforms."""
        transform_list = []

        # Efficient resize and crop
        transform_list.extend(
            [
                transforms.Resize(256, interpolation=transforms.InterpolationMode.BILINEAR),
                transforms.RandomCrop(224),
            ]
        )

        # Optimized augmentations
        if self.config.get("enabled", True):
            # Use faster augmentations first
            if self.config.get("horizontal_flip", True):
                transform_list.append(transforms.RandomHorizontalFlip(p=0.5))

            if self.config.get("vertical_flip", False):
                transform_list.append(transforms.RandomVerticalFlip(p=0.5))

            # More expensive augmentations
            if self.config.get("rotation", 0) > 0:
                transform_list.append(transforms.RandomRotation(self.config["rotation"], interpolation=transforms.InterpolationMode.BILINEAR))

            if self.config.get("brightness", 0) > 0 or self.config.get("contrast", 0) > 0:
                transform_list.append(
                    transforms.ColorJitter(
                        brightness=self.config.get("brightness", 0),
                        contrast=self.config.get("contrast", 0),
                        saturation=self.config.get("saturation", 0),
                        hue=self.config.get("hue", 0),
                    )
                )

        # Convert to tensor (most efficient at the end)
        transform_list.append(transforms.ToTensor())

        # Normalization
        if self.config.get("normalize", True):
            transform_list.append(
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                )
            )

        return transforms.Compose(transform_list)

    def get_val_transforms(self) -> transforms.Compose:
        """Get validation transforms (no augmentation)."""
        transform_list = [
            transforms.Resize(256, interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
        ]

        if self.config.get("normalize", True):
            transform_list.append(
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                )
            )

        return transforms.Compose(transform_list)


class DataLoadingProfiler:
    """Profiler for data loading performance analysis."""

    def __init__(self, config: DataLoadingConfig) -> None:
        """Initialize profiler.

        Args:
            config: Data loading configuration
        """
        self.config = config
        self.profile_results: list[float] = []
        self.memory_usage: list[float] = []

    def profile_data_loader(
        self,
        data_loader: DataLoader,
        num_batches: int | None = None,
    ) -> DataLoadingProfile:
        """Profile data loader performance.

        Args:
            data_loader: DataLoader to profile
            num_batches: Number of batches to profile (None for all)

        Returns:
            DataLoadingProfile with performance metrics
        """
        logger.info("Starting data loader profiling...")

        if num_batches is None:
            num_batches = self.config.profile_batches

        batch_times = []
        total_samples = 0
        start_time = time.time()

        # Profile data loading
        for batch_idx, (data, targets) in enumerate(data_loader):
            if batch_idx >= num_batches:
                break

            batch_start = time.time()

            # Simulate processing (move to device)
            if torch.cuda.is_available():
                data = data.cuda(non_blocking=True)
                targets = targets.cuda(non_blocking=True)

            batch_time = time.time() - batch_start
            batch_times.append(batch_time)
            total_samples += len(data)

            # Memory usage tracking
            if torch.cuda.is_available():
                memory_mb = torch.cuda.memory_allocated() / 1024**2
                self.memory_usage.append(memory_mb)

        total_time = time.time() - start_time

        # Calculate metrics
        avg_batch_time = np.mean(batch_times) if batch_times else 0.0
        min_batch_time = np.min(batch_times) if batch_times else 0.0
        max_batch_time = np.max(batch_times) if batch_times else 0.0
        throughput = total_samples / total_time if total_time > 0 else 0.0
        avg_memory = np.mean(self.memory_usage) if self.memory_usage else 0.0

        # Analyze bottlenecks and generate recommendations
        bottlenecks, recommendations = self._analyze_performance(batch_times, avg_batch_time, data_loader)

        profile = DataLoadingProfile(
            avg_batch_time=avg_batch_time,
            min_batch_time=min_batch_time,
            max_batch_time=max_batch_time,
            total_time=total_time,
            batches_profiled=len(batch_times),
            throughput_samples_per_sec=throughput,
            memory_usage_mb=avg_memory,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
        )

        self._log_profile_results(profile)
        return profile

    def _analyze_performance(
        self,
        batch_times: list[float],
        avg_batch_time: float,
        data_loader: DataLoader,
    ) -> tuple[list[str], list[str]]:
        """Analyze performance and identify bottlenecks."""
        bottlenecks = []
        recommendations = []

        if not batch_times:
            return bottlenecks, recommendations

        # Check for high variance in batch times
        std_batch_time = np.std(batch_times)
        if std_batch_time > avg_batch_time * 0.5:
            bottlenecks.append("High variance in batch loading times")
            recommendations.append("Consider increasing num_workers or using persistent_workers")

        # Check if batch times are too high
        if avg_batch_time > 0.1:  # 100ms per batch
            bottlenecks.append("Slow batch loading")
            if data_loader.num_workers == 0:
                recommendations.append("Enable multi-processing with num_workers > 0")
            else:
                recommendations.append("Consider increasing num_workers or optimizing transforms")

        # Check memory usage
        if self.memory_usage and np.mean(self.memory_usage) > 8000:  # 8GB
            bottlenecks.append("High memory usage")
            recommendations.append("Consider reducing batch_size or using gradient accumulation")

        # Check num_workers efficiency
        if data_loader.num_workers > 0 and avg_batch_time > 0.05:
            recommendations.append("Try adjusting num_workers (current: {})".format(data_loader.num_workers))

        return bottlenecks, recommendations

    def _log_profile_results(self, profile: DataLoadingProfile) -> None:
        """Log profiling results."""
        logger.info("Data Loading Profile Results:")
        logger.info(f"  Average batch time: {profile.avg_batch_time:.4f}s")
        logger.info(f"  Min/Max batch time: {profile.min_batch_time:.4f}s / {profile.max_batch_time:.4f}s")
        logger.info(f"  Throughput: {profile.throughput_samples_per_sec:.1f} samples/sec")
        logger.info(f"  Memory usage: {profile.memory_usage_mb:.1f} MB")

        if profile.bottlenecks:
            logger.warning("Identified bottlenecks:")
            for bottleneck in profile.bottlenecks:
                logger.warning(f"  - {bottleneck}")

        if profile.recommendations:
            logger.info("Recommendations:")
            for recommendation in profile.recommendations:
                logger.info(f"  - {recommendation}")


class OptimizedDataLoader:
    """Factory for creating optimized data loaders."""

    def __init__(self, config: DataLoadingConfig) -> None:
        """Initialize optimized data loader factory.

        Args:
            config: Data loading configuration
        """
        self.config = config
        self.profiler = DataLoadingProfiler(config) if config.enable_profiling else None

    def create_data_loaders(
        self,
        dataset_dir: Path,
        batch_size: int,
        augmentation_config: dict[str, Any],
        validation_split: float = 0.2,
    ) -> tuple[DataLoader, DataLoader, list[str]]:
        """Create optimized train and validation data loaders.

        Args:
            dataset_dir: Path to dataset directory
            batch_size: Batch size for data loaders
            augmentation_config: Data augmentation configuration
            validation_split: Validation split ratio (if no val dir exists)

        Returns:
            Tuple of (train_loader, val_loader, class_names)
        """
        logger.info("Creating optimized data loaders...")

        # Auto-detect optimal num_workers if not set
        if self.config.num_workers == 0:
            self.config.num_workers = self._get_optimal_num_workers()

        # Setup data augmentation
        augmentation = OptimizedDataAugmentation(augmentation_config)
        train_transform = augmentation.get_train_transforms()
        val_transform = augmentation.get_val_transforms()

        # Check dataset structure
        train_dir = dataset_dir / "train"
        val_dir = dataset_dir / "val"

        if train_dir.exists() and val_dir.exists():
            # Use existing train/val split
            train_dataset, val_dataset, class_names = self._create_split_datasets(train_dir, val_dir, train_transform, val_transform)
        else:
            # Create train/val split from single directory
            train_dataset, val_dataset, class_names = self._create_datasets_with_split(dataset_dir, train_transform, val_transform, validation_split)

        # Create data loaders with optimized settings
        train_loader = self._create_optimized_loader(train_dataset, batch_size, shuffle=True, drop_last=True)

        val_loader = self._create_optimized_loader(val_dataset, batch_size, shuffle=False, drop_last=False)

        logger.info(f"Created data loaders: {len(train_dataset)} train, {len(val_dataset)} val samples")
        logger.info(f"Batch size: {batch_size}, Num workers: {self.config.num_workers}")

        # Profile data loaders if enabled
        if self.profiler:
            logger.info("Profiling train data loader...")
            train_profile = self.profiler.profile_data_loader(train_loader)

            logger.info("Profiling validation data loader...")
            val_profile = self.profiler.profile_data_loader(val_loader)

        return train_loader, val_loader, class_names

    def _get_optimal_num_workers(self) -> int:
        """Determine optimal number of workers for data loading."""
        # Get number of CPU cores
        cpu_count = mp.cpu_count()

        # Use 75% of available cores, but cap at 8 for most cases
        optimal_workers = min(max(1, int(cpu_count * 0.75)), 8)

        logger.info(f"Auto-detected optimal num_workers: {optimal_workers} (CPU cores: {cpu_count})")
        return optimal_workers

    def _create_split_datasets(
        self,
        train_dir: Path,
        val_dir: Path,
        train_transform: transforms.Compose,
        val_transform: transforms.Compose,
    ) -> tuple[Dataset, Dataset, list[str]]:
        """Create datasets from existing train/val split."""
        if self.config.use_memory_mapping:
            train_dataset = MemoryMappedImageFolder(train_dir, transform=train_transform)
            val_dataset = MemoryMappedImageFolder(val_dir, transform=val_transform)
        else:
            train_dataset = ImageFolder(train_dir, transform=train_transform)
            val_dataset = ImageFolder(val_dir, transform=val_transform)

        class_names = train_dataset.classes
        return train_dataset, val_dataset, class_names

    def _create_datasets_with_split(
        self,
        dataset_dir: Path,
        train_transform: transforms.Compose,
        val_transform: transforms.Compose,
        validation_split: float,
    ) -> tuple[Dataset, Dataset, list[str]]:
        """Create datasets with train/val split from single directory."""
        from torch.utils.data import random_split

        if self.config.use_memory_mapping:
            full_dataset = MemoryMappedImageFolder(dataset_dir, transform=None)
        else:
            full_dataset = ImageFolder(dataset_dir, transform=None)

        # Calculate split sizes
        total_size = len(full_dataset)
        val_size = int(total_size * validation_split)
        train_size = total_size - val_size

        # Split dataset
        train_indices, val_indices = random_split(range(total_size), [train_size, val_size], generator=torch.Generator().manual_seed(42))

        # Create subset datasets with transforms
        from torch.utils.data import Subset

        # Apply transforms to subsets
        train_dataset = Subset(full_dataset, train_indices.indices)
        val_dataset = Subset(full_dataset, val_indices.indices)

        # Set transforms
        train_dataset.dataset.transform = train_transform
        val_dataset.dataset.transform = val_transform

        class_names = full_dataset.classes
        return train_dataset, val_dataset, class_names

    def _create_optimized_loader(
        self,
        dataset: Dataset,
        batch_size: int,
        shuffle: bool,
        drop_last: bool,
    ) -> DataLoader:
        """Create optimized data loader with best settings."""
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=self.config.num_workers,
            pin_memory=self.config.pin_memory,
            drop_last=drop_last,
            persistent_workers=self.config.persistent_workers and self.config.num_workers > 0,
            prefetch_factor=self.config.prefetch_factor if self.config.num_workers > 0 else 2,
            # Enable multiprocessing context for better performance
            multiprocessing_context="spawn" if self.config.num_workers > 0 else None,
        )


def create_optimized_data_loaders(
    dataset_dir: Path,
    batch_size: int,
    augmentation_config: dict[str, Any],
    data_loading_config: DataLoadingConfig | None = None,
    validation_split: float = 0.2,
) -> tuple[DataLoader, DataLoader, list[str]]:
    """Create optimized data loaders with performance profiling.

    Args:
        dataset_dir: Path to dataset directory
        batch_size: Batch size for data loaders
        augmentation_config: Data augmentation configuration
        data_loading_config: Data loading configuration (optional)
        validation_split: Validation split ratio if no val dir exists

    Returns:
        Tuple of (train_loader, val_loader, class_names)
    """
    if data_loading_config is None:
        data_loading_config = DataLoadingConfig()

    loader_factory = OptimizedDataLoader(data_loading_config)
    return loader_factory.create_data_loaders(dataset_dir, batch_size, augmentation_config, validation_split)
