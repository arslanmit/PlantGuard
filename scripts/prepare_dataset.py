"""
Dataset preparation utilities for PlantGuard.

This script helps prepare the PlantVillage dataset for training.
"""

import argparse
import logging
import shutil
from pathlib import Path

from sklearn.model_selection import train_test_split
from torchvision import datasets

logger = logging.getLogger(__name__)


def split_dataset(
    source_dir: Path,
    output_dir: Path,
    train_ratio: float = 0.8,
    random_state: int = 42,
) -> None:
    """
    Split dataset into train and validation sets.

    Args:
        source_dir: Source directory with class subdirectories
        output_dir: Output directory for train/val split
        train_ratio: Ratio of training samples
        random_state: Random seed for reproducibility
    """
    logger.info("Splitting dataset from %s to %s", source_dir, output_dir)

    # Create output directories
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    # Process each class
    for class_dir in source_dir.iterdir():
        if not class_dir.is_dir():
            continue

        class_name = class_dir.name
        logger.info("Processing class: %s", class_name)

        # Get all image files
        image_files = (
            list(class_dir.glob("*.jpg"))
            + list(class_dir.glob("*.jpeg"))
            + list(class_dir.glob("*.png"))
        )

        if not image_files:
            logger.warning("No images found in %s", class_dir)
            continue

        # Split files
        train_files, val_files = train_test_split(
            image_files,
            train_size=train_ratio,
            random_state=random_state,
            shuffle=True,
        )

        # Create class directories
        train_class_dir = train_dir / class_name
        val_class_dir = val_dir / class_name
        train_class_dir.mkdir(exist_ok=True)
        val_class_dir.mkdir(exist_ok=True)

        # Copy files
        for file_path in train_files:
            shutil.copy2(file_path, train_class_dir / file_path.name)

        for file_path in val_files:
            shutil.copy2(file_path, val_class_dir / file_path.name)

        logger.info(
            "Class %s: %d train, %d val samples",
            class_name,
            len(train_files),
            len(val_files),
        )

    logger.info("Dataset split completed")


def validate_dataset(dataset_dir: Path) -> dict[str, int]:
    """
    Validate dataset structure and count samples.

    Args:
        dataset_dir: Directory containing train/val subdirectories

    Returns:
        Dictionary with dataset statistics
    """
    stats = {}

    for split in ["train", "val"]:
        split_dir = dataset_dir / split
        if not split_dir.exists():
            logger.warning("Split directory %s does not exist", split_dir)
            continue

        try:
            dataset = datasets.ImageFolder(split_dir)
            stats[f"{split}_samples"] = len(dataset)
            stats[f"{split}_classes"] = len(dataset.classes)

            if split == "train":
                stats["class_names"] = dataset.classes

            logger.info("%s: %d samples, %d classes", split, len(dataset), len(dataset.classes))

        except (FileNotFoundError, RuntimeError, ValueError):
            logger.exception("Error loading %s dataset", split)

    return stats


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Prepare PlantVillage dataset")
    parser.add_argument("--source_dir", type=str, required=True, help="Source dataset directory")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    parser.add_argument("--train_ratio", type=float, default=0.8, help="Training set ratio")
    parser.add_argument(
        "--validate_only", action="store_true", help="Only validate existing dataset"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)

    if args.validate_only:
        stats = validate_dataset(output_dir)
        logger.info("Dataset validation completed: %s", stats)
    else:
        split_dataset(source_dir, output_dir, args.train_ratio)
        stats = validate_dataset(output_dir)
        logger.info("Dataset preparation completed: %s", stats)


if __name__ == "__main__":
    main()
