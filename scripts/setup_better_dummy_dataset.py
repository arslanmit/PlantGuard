#!/usr/bin/env python3
"""Create improved dummy dataset with learnable patterns for testing PlantGuard training pipeline."""
# ruff: noqa: S311

import argparse
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def create_synthetic_plant_image(class_id: int, width: int = 224, height: int = 224, seed: int | None = None) -> Image.Image:
    """Create a synthetic plant image with distinguishable patterns for each class.

    Args:
        class_id: Class identifier (0-based)
        width: Image width
        height: Image height
        seed: Random seed for reproducibility

    Returns:
        PIL Image with synthetic plant-like patterns
    """

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Create base image with plant-like background
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Define class-specific color schemes and patterns
    class_patterns = [
        # Healthy plants - green dominant
        {"bg": (34, 139, 34), "pattern": (0, 100, 0), "spots": (255, 255, 0)},  # Forest green
        {"bg": (50, 205, 50), "pattern": (0, 128, 0), "spots": (255, 255, 255)},  # Lime green
        # Diseased plants - brown/yellow dominant
        {"bg": (139, 69, 19), "pattern": (160, 82, 45), "spots": (255, 0, 0)},  # Saddle brown
        {"bg": (218, 165, 32), "pattern": (184, 134, 11), "spots": (128, 0, 0)},  # Golden rod
        # Rust diseases - orange/red dominant
        {"bg": (255, 140, 0), "pattern": (255, 69, 0), "spots": (139, 0, 0)},  # Dark orange
        {"bg": (205, 92, 92), "pattern": (178, 34, 34), "spots": (255, 255, 0)},  # Indian red
        # Blight diseases - dark/purple dominant
        {"bg": (75, 0, 130), "pattern": (138, 43, 226), "spots": (255, 255, 255)},  # Indigo
        {"bg": (72, 61, 139), "pattern": (106, 90, 205), "spots": (255, 215, 0)},  # Dark slate blue
    ]

    # Select pattern based on class_id
    pattern = class_patterns[class_id % len(class_patterns)]

    # Fill background
    draw.rectangle([0, 0, width, height], fill=pattern["bg"])

    # Add leaf-like shapes with class-specific patterns
    num_leaves = random.randint(3, 8)
    for _ in range(num_leaves):
        # Random leaf position and size
        x = random.randint(20, width - 60)
        y = random.randint(20, height - 60)
        leaf_width = random.randint(30, 80)
        leaf_height = random.randint(20, 60)

        # Draw leaf shape (ellipse)
        draw.ellipse(
            [x, y, x + leaf_width, y + leaf_height],
            fill=pattern["pattern"],
            outline=(0, 0, 0),
            width=2,
        )

        # Add class-specific disease spots or healthy patterns
        if class_id % 2 == 0:  # Even classes = diseased
            # Add disease spots
            num_spots = random.randint(2, 6)
            for _ in range(num_spots):
                spot_x = x + random.randint(5, leaf_width - 10)
                spot_y = y + random.randint(5, leaf_height - 10)
                spot_size = random.randint(3, 8)
                draw.ellipse(
                    [spot_x, spot_y, spot_x + spot_size, spot_y + spot_size],
                    fill=pattern["spots"],
                )
        else:  # Odd classes = healthy
            # Add healthy vein patterns
            vein_x = x + leaf_width // 2
            draw.line(
                [vein_x, y + 5, vein_x, y + leaf_height - 5],
                fill=pattern["spots"],
                width=2,
            )

    # Add some texture noise for realism
    noise_array = np.array(img)
    noise = np.random.normal(0, 10, noise_array.shape).astype(np.int16)
    noise_array = np.clip(noise_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(noise_array)

def create_improved_dummy_dataset(
    output_dir: Path,
    num_classes: int = 8,
    samples_per_class: int = 50,
    train_ratio: float = 0.8,
    random_seed: int = 42,
) -> None:
    """Create an improved dummy dataset with learnable synthetic patterns.

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

    print(f"Creating improved dummy dataset at {output_dir}")
    print(f"Classes: {num_classes}")
    print(f"Samples per class: {samples_per_class}")
    print(f"Train ratio: {train_ratio}")
    print("[LEAF] Using synthetic plant patterns with learnable features")

    for class_idx, class_name in enumerate(selected_classes):
        print(f"Creating class {class_idx}: {class_name}")

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
            img = create_synthetic_plant_image(class_idx, seed=random_seed + i)
            img_path = train_class_dir / f"{class_name}_{i:04d}.jpg"
            img.save(img_path, "JPEG", quality=85)

        # Create validation images
        for i in range(val_samples):
            img = create_synthetic_plant_image(class_idx, seed=random_seed + train_samples + i)
            img_path = val_class_dir / f"{class_name}_{i:04d}.jpg"
            img.save(img_path, "JPEG", quality=85)

        print(f"  [DONE] Created {train_samples} train + {val_samples} val images")

    print(f"[DONE] Improved dummy dataset created successfully at {output_dir}")
    print("[PROGRESS] This dataset has learnable patterns and should achieve >80% accuracy")

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Create improved dummy dataset for testing")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/plantvillage_dummy_improved",
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
    parser.add_argument("--random_seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    try:
        create_improved_dummy_dataset(
            Path(args.output_dir),
            args.num_classes,
            args.samples_per_class,
            args.train_ratio,
            args.random_seed,
        )
    except (OSError, ValueError) as e:
        print(f"[TODO] Error creating improved dummy dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
