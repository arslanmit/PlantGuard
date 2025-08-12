"""Dataset loading utilities for PlantGuard multimodal system.

This module provides utilities for loading and preprocessing the PlantVillage dataset
with support for stratified train/validation splits and data augmentation.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import transforms
from torchvision.datasets import ImageFolder

logger = logging.getLogger(__name__)


class NoReadableSamplesError(RuntimeError):
    """Raised when no readable samples can be loaded from the dataset."""


class PlantVillageDataset(Dataset):
    """Custom dataset class for PlantVillage plant disease detection.

    Supports loading images with labels and applying transformations.
    """

    def __init__(
        self,
        root_dir: str | Path,
        transform: Callable[[Image.Image], torch.Tensor] | None = None,
        target_transform: Callable[[int], int] | None = None,
    ) -> None:
        """Initialize PlantVillage dataset.

        Args:
            root_dir: Root directory containing class subdirectories
            transform: Optional transform to apply to images
            target_transform: Optional transform to apply to targets
        """
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.target_transform = target_transform

        # Use ImageFolder for automatic class discovery
        self.dataset = ImageFolder(
            root=str(self.root_dir),
            transform=None,  # We'll apply transforms manually
            target_transform=target_transform,
        )

        self.classes = self.dataset.classes
        self.class_to_idx = self.dataset.class_to_idx
        self.samples = self.dataset.samples

        logger.info(
            "Loaded dataset with %d samples and %d classes", len(self.samples), len(self.classes)
        )

    def __len__(self) -> int:
        """Return the total number of samples."""
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        """Get a sample from the dataset, skipping corrupted files if needed.

        Args:
            idx: Index of the sample

        Returns:
            Tuple of (image_tensor, label)
        """
        num_samples = len(self.samples)
        attempts = 0

        while attempts < num_samples:
            image_path, label = self.samples[idx]
            try:
                # Load image
                with Image.open(image_path) as pil_image:
                    rgb_image = pil_image.convert("RGB")

                # Apply transforms
                if self.transform:
                    image_tensor = self.transform(rgb_image)
                else:
                    image_tensor = transforms.ToTensor()(rgb_image)
            except (OSError, ValueError, RuntimeError):
                # Skip corrupted/unreadable file and try next
                idx = (idx + 1) % num_samples
                attempts += 1
            else:
                return image_tensor, label

        # If all attempts failed, raise a specific error
        raise NoReadableSamplesError()

    def get_class_distribution(self) -> dict[str, int]:
        """Get the distribution of classes in the dataset.

        Returns:
            Dictionary mapping class names to sample counts
        """
        class_counts: dict[str, int] = {}
        for _, label in self.samples:
            class_name = self.classes[label]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        return class_counts


class DataTransforms:
    """Predefined data transformations for training and validation."""

    @staticmethod
    def get_train_transforms(
        image_size: int = 224,
        mean: tuple[float, float, float] = (0.485, 0.456, 0.406),
        std: tuple[float, float, float] = (0.229, 0.224, 0.225),
    ) -> Callable[[Image.Image], torch.Tensor]:
        """Get training transformations with data augmentation.

        Args:
            image_size: Target image size (square)
            mean: ImageNet normalization mean
            std: ImageNet normalization std

        Returns:
            Composed transforms for training
        """
        composed = transforms.Compose(
            [
                # Slightly larger for random crop
                transforms.Resize((image_size + 32, image_size + 32)),
                transforms.RandomCrop(image_size),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=15),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
                transforms.ToTensor(),
                transforms.Normalize(mean=mean, std=std),
            ]
        )
        return cast(Callable[[Image.Image], torch.Tensor], composed)

    @staticmethod
    def get_val_transforms(
        image_size: int = 224,
        mean: tuple[float, float, float] = (0.485, 0.456, 0.406),
        std: tuple[float, float, float] = (0.229, 0.224, 0.225),
    ) -> Callable[[Image.Image], torch.Tensor]:
        """Get validation transformations without augmentation.

        Args:
            image_size: Target image size (square)
            mean: ImageNet normalization mean
            std: ImageNet normalization std

        Returns:
            Composed transforms for validation
        """
        composed = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=mean, std=std),
            ]
        )
        return cast(Callable[[Image.Image], torch.Tensor], composed)

    @staticmethod
    def get_inference_transforms(
        image_size: int = 224,
        mean: tuple[float, float, float] = (0.485, 0.456, 0.406),
        std: tuple[float, float, float] = (0.229, 0.224, 0.225),
    ) -> Callable[[Image.Image], torch.Tensor]:
        """Get inference transformations for single image prediction.

        Args:
            image_size: Target image size (square)
            mean: ImageNet normalization mean
            std: ImageNet normalization std

        Returns:
            Composed transforms for inference
        """
        composed = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=mean, std=std),
            ]
        )
        return cast(Callable[[Image.Image], torch.Tensor], composed)


def create_stratified_split(
    dataset: PlantVillageDataset,
    train_ratio: float = 0.8,
    random_state: int = 42,
) -> tuple[Dataset, Dataset]:
    """Create stratified train/validation split maintaining class distribution.

    Args:
        dataset: PlantVillage dataset to split
        train_ratio: Ratio of data to use for training (0.0 to 1.0)
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (train_dataset, val_dataset)
    """
    # Extract labels for stratification
    labels = [label for _, label in dataset.samples]
    indices = list(range(len(dataset)))

    # Perform stratified split
    train_indices, val_indices = train_test_split(
        indices,
        test_size=1 - train_ratio,
        stratify=labels,
        random_state=random_state,
    )

    # Create subset datasets
    train_dataset = torch.utils.data.Subset(dataset, train_indices)
    val_dataset = torch.utils.data.Subset(dataset, val_indices)

    logger.info(
        "Created stratified split: %d train, %d val samples",
        len(train_dataset),
        len(val_dataset),
    )

    return train_dataset, val_dataset


def create_data_loaders(
    data_dir: str | Path,
    batch_size: int = 32,
    train_ratio: float = 0.8,
    num_workers: int = 4,
    pin_memory: bool = True,
    random_state: int = 42,
) -> tuple[DataLoader, DataLoader, list[str]]:
    """Create train and validation data loaders with stratified splitting.

    Args:
        data_dir: Root directory containing class subdirectories
        batch_size: Batch size for data loaders
        train_ratio: Ratio of data to use for training
        num_workers: Number of worker processes for data loading
        pin_memory: Whether to pin memory for faster GPU transfer
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (train_loader, val_loader, class_names)
    """
    # Create datasets with appropriate transforms
    train_dataset = PlantVillageDataset(
        root_dir=data_dir,
        transform=DataTransforms.get_train_transforms(),
    )

    val_dataset = PlantVillageDataset(
        root_dir=data_dir,
        transform=DataTransforms.get_val_transforms(),
    )

    # Create stratified split
    train_subset, val_subset = create_stratified_split(
        train_dataset, train_ratio=train_ratio, random_state=random_state
    )

    # Update validation dataset to use validation subset indices
    if isinstance(val_subset, Subset):
        val_dataset.samples = [train_dataset.samples[i] for i in val_subset.indices]

    # Create data loaders
    train_loader = DataLoader(
        train_subset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=True,
    )

    val_loader = DataLoader(
        val_subset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=False,
    )

    class_names = train_dataset.classes

    logger.info(
        "Created data loaders: train_batches=%d, val_batches=%d",
        len(train_loader),
        len(val_loader),
    )

    return train_loader, val_loader, class_names


def get_dataset_statistics(dataset: PlantVillageDataset) -> dict[str, Any]:
    """Calculate comprehensive dataset statistics.

    Args:
        dataset: PlantVillage dataset to analyze

    Returns:
        Dictionary containing dataset statistics
    """
    class_distribution = dataset.get_class_distribution()
    total_samples = len(dataset)
    num_classes = len(dataset.classes)

    # Calculate class balance metrics
    class_counts = list(class_distribution.values())
    min_samples = min(class_counts)
    max_samples = max(class_counts)
    mean_samples = np.mean(class_counts)
    std_samples = np.std(class_counts)

    # Calculate imbalance ratio
    imbalance_ratio = max_samples / min_samples if min_samples > 0 else float("inf")

    return {
        "total_samples": total_samples,
        "num_classes": num_classes,
        "class_distribution": class_distribution,
        "min_samples_per_class": min_samples,
        "max_samples_per_class": max_samples,
        "mean_samples_per_class": float(mean_samples),
        "std_samples_per_class": float(std_samples),
        "imbalance_ratio": imbalance_ratio,
        "class_names": dataset.classes,
    }
