#!/usr/bin/env python3
"""Create dummy dataset for testing PlantGuard training pipeline."""

import argparse
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def create_dummy_image(width: int = 224, height: int = 224) -> Image.Image:
    """Create a dummy RGB image with random colors.

    Args:
        width: Image width
        height: Image height

    Returns:
        PIL Image with random colors
    """
    # Create random RGB data
    data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(data, "RGB")


def create_dummy_dataset(
    output_dir: Path,
    num_classes: int = 8,
    samples_per_class: int = 50,
    train_ratio: float = 0.8,
    random_seed: int = 42,
) -> None:
    """Create a dummy dataset with train/val splits.

    Args:
        output_dir: Output directory for the dataset
        num_classes: Number of classes to create
        samples_per_class: Number of samples per class
        train_ratio: Ratio of training samples
        random_seed: Random seed for reproducibility
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    # Plant disease class names for realism
    class_names = [
        "potato_early_blight",
        "potato_healthy",
        "potato_late_blight",
        "tomato_early_blight",
        "tomato_healthy",
        "tomato_late_blight",
        "corn_common_rust",
        "corn_healthy",
        "apple_scab",
        "apple_healthy",
        "grape_black_rot",
        "grape_healthy",
    ]

    # Select the requested number of classes
    selected_classes = class_names[:num_classes]

    # Create output directories
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"

    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating dummy dataset at {output_dir}")
    print(f"Classes: {num_classes}")
    print(f"Samples per class: {samples_per_class}")
    print(f"Train ratio: {train_ratio}")

    for class_name in selected_classes:
        print(f"Creating class: {class_name}")

        # Create class directories
        train_class_dir = train_dir / class_name
        val_class_dir = val_dir / class_name
        train_class_dir.mkdir(exist_ok=True)
        val_class_dir.mkdir(exist_ok=True)

        # Calculate split
        train_samples = int(samples_per_class * train_ratio)
        val_samples = samples_per_class - train_samples

        # Create training images
        for i in range(train_samples):
            img = create_dummy_image()
            img_path = train_class_dir / f"{class_name}_{i:04d}.jpg"
            img.save(img_path, "JPEG", quality=85)

        # Create validation images
        for i in range(val_samples):
            img = create_dummy_image()
            img_path = val_class_dir / f"{class_name}_{i:04d}.jpg"
            img.save(img_path, "JPEG", quality=85)

        print(f"  Created {train_samples} train + {val_samples} val images")

    print(f"✅ Dummy dataset created successfully at {output_dir}")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Create dummy dataset for testing")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/plantvillage_dummy",
        help="Output directory for dummy dataset",
    )
    parser.add_argument("--num_classes", type=int, default=8, help="Number of classes to create")
    parser.add_argument(
        "--samples_per_class",
        type=int,
        default=50,
        help="Number of samples per class",
    )
    parser.add_argument("--train_ratio", type=float, default=0.8, help="Ratio of training samples")
    parser.add_argument(
        "--random_seed", type=int, default=42, help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    try:
        create_dummy_dataset(
            Path(args.output_dir),
            args.num_classes,
            args.samples_per_class,
            args.train_ratio,
            args.random_seed,
        )
    except (OSError, ValueError) as e:
        print(f"❌ Error creating dummy dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
