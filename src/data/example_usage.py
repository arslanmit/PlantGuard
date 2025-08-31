"""Example usage of PlantGuard data pipeline utilities.

This script demonstrates how to use the dataset loading, validation,
and analysis utilities for the PlantVillage dataset.
"""


from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import logging
from pathlib import Path

from src.data import (
    DataIntegrityChecker,
    DatasetAnalyzer,
    ImageValidator,
    create_data_loaders,
    generate_data_report,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_dataset_loading(data_dir: str) -> None:
    """Example of loading PlantVillage dataset with train/validation split.

    Args:
        data_dir: Path to dataset directory containing class subdirectories
    """
    logger.info("=== Dataset Loading Example ===")

    try:
        # Create data loaders with stratified split
        train_loader, val_loader, class_names = create_data_loaders(
            data_dir=data_dir,
            batch_size=32,
            train_ratio=0.8,
            num_workers=2,  # Reduce for example
            random_state=42,
        )

        logger.info("Created data loaders:")
        logger.info("  - Training batches: %d", len(train_loader))
        logger.info("  - Validation batches: %d", len(val_loader))
        logger.info("  - Number of classes: %d", len(class_names))
        logger.info("  - Class names: %s", class_names[:5])  # Show first 5

        # Test loading a batch
        train_batch = next(iter(train_loader))
        images, labels = train_batch
        logger.info("Sample batch shape: images=%s, labels=%s", images.shape, labels.shape)

    except (FileNotFoundError, ValueError, RuntimeError):
        logger.exception("Dataset loading failed")


def example_data_validation(data_dir: str) -> None:
    """Example of validating dataset images and structure.

    Args:
        data_dir: Path to dataset directory
    """
    logger.info("=== Data Validation Example ===")

    try:
        # Validate images
        validator = ImageValidator(strict_mode=False)
        validation_results = validator.validate_dataset_directory(data_dir)

        logger.info("Image validation results:")
        logger.info("  - Total files: %d", validation_results.get("total_files", 0))
        logger.info("  - Valid images: %d", validation_results.get("valid_images", 0))
        logger.info("  - Invalid images: %d", validation_results.get("invalid_images", 0))
        validation_rate = validation_results.get("validation_rate", 0.0)
        if isinstance(validation_rate, int | float):
            logger.info("  - Validation rate: %.1f%%", validation_rate * 100)

        # Show some invalid images if any
        invalid_images = validation_results.get("invalid_images", [])
        if invalid_images and isinstance(invalid_images, list):
            logger.warning("Invalid images found: %s", invalid_images[:3])

    except (FileNotFoundError, ValueError, RuntimeError):
        logger.exception("Data validation failed")


def example_dataset_analysis(data_dir: str) -> None:
    """Example of analyzing dataset statistics and class distribution.

    Args:
        data_dir: Path to dataset directory
    """
    logger.info("=== Dataset Analysis Example ===")

    try:
        # Analyze class distribution
        analyzer = DatasetAnalyzer()
        class_analysis = analyzer.analyze_class_distribution(data_dir)

        logger.info("Class distribution analysis:")
        logger.info("  - Number of classes: %d", class_analysis.get("num_classes", 0))
        logger.info("  - Total samples: %d", class_analysis.get("total_samples", 0))
        logger.info("  - Min samples per class: %d", class_analysis.get("min_samples", 0))
        logger.info("  - Max samples per class: %d", class_analysis.get("max_samples", 0))
        logger.info("  - Imbalance ratio: %.2f", class_analysis.get("imbalance_ratio", 0.0))
        logger.info("  - Is balanced: %s", class_analysis.get("is_balanced", False))

        # Show top 5 classes by sample count
        df = class_analysis.get("class_distribution_df")
        if df is not None and hasattr(df, "head"):
            logger.info("Top 5 classes by sample count:")
            for _, row in df.head().iterrows():
                logger.info(
                    "  - %s: %d samples (%.1f%%)",
                    row["class_name"],
                    row["sample_count"],
                    row["percentage"],
                )

        # Analyze image properties (sample)
        image_analysis = analyzer.analyze_image_properties(data_dir, sample_size=100)

        sample_size = image_analysis.get("sample_size", 0)
        logger.info("Image properties analysis (sample of %d):", sample_size)

        dimensions = image_analysis.get("dimensions", {})
        width_stats = dimensions.get("width_stats", {})
        height_stats = dimensions.get("height_stats", {})

        if width_stats and height_stats:
            logger.info(
                "  - Width: %d-%d (mean: %.0f)",
                width_stats.get("min", 0),
                width_stats.get("max", 0),
                width_stats.get("mean", 0),
            )
            logger.info(
                "  - Height: %d-%d (mean: %.0f)",
                height_stats.get("min", 0),
                height_stats.get("max", 0),
                height_stats.get("mean", 0),
            )

        file_sizes = image_analysis.get("file_sizes", {})
        size_stats = file_sizes.get("stats", {})
        if size_stats:
            logger.info(
                "  - File size: %.2f-%.2f MB (mean: %.2f)",
                size_stats.get("min", 0),
                size_stats.get("max", 0),
                size_stats.get("mean", 0),
            )

    except (FileNotFoundError, ValueError, RuntimeError):
        logger.exception("Dataset analysis failed")


def example_integrity_check(data_dir: str) -> None:
    """Example of running data integrity checks.

    Args:
        data_dir: Path to dataset directory
    """
    logger.info("=== Data Integrity Check Example ===")

    try:
        # Run full integrity check
        checker = DataIntegrityChecker()
        integrity_results = checker.run_full_integrity_check(data_dir, min_samples_per_class=10)

        logger.info("Data integrity check results:")
        logger.info("  - Overall valid: %s", integrity_results.get("overall_valid", False))

        structure_check = integrity_results.get("structure_check", {})
        if isinstance(structure_check, dict):
            logger.info("  - Structure valid: %s", structure_check.get("valid_structure", False))
            # Show any issues
            empty_dirs = structure_check.get("empty_directories", [])
            if empty_dirs:
                logger.warning("Empty directories: %s", empty_dirs)

        consistency_check = integrity_results.get("consistency_check", {})
        if isinstance(consistency_check, dict):
            logger.info(
                "  - Classes consistent: %s",
                consistency_check.get("consistent", False),
            )
            insufficient_classes = consistency_check.get("insufficient_classes", [])
            if insufficient_classes:
                logger.warning("Classes with insufficient samples: %s", insufficient_classes)

    except (FileNotFoundError, ValueError, RuntimeError):
        logger.exception("Integrity check failed")


def example_generate_report(data_dir: str, output_path: str | None = None) -> None:
    """Example of generating comprehensive data quality report.

    Args:
        data_dir: Path to dataset directory
        output_path: Optional path to save report
    """
    logger.info("=== Data Quality Report Example ===")

    try:
        # Generate comprehensive report
        report = generate_data_report(data_dir, output_path)

        logger.info("Data quality report generated:")
        logger.info("  - Dataset path: %s", report.get("dataset_path", ""))
        logger.info("  - Report timestamp: %s", report.get("report_timestamp", ""))

        # Validation summary
        val_summary = report.get("validation_summary", {})
        if isinstance(val_summary, dict):
            validation_rate = val_summary.get("validation_rate", 0.0)
            if isinstance(validation_rate, int | float):
                logger.info(
                    "  - Validation: %d/%d files valid (%.1f%%)",
                    val_summary.get("valid_images", 0),
                    val_summary.get("total_files", 0),
                    validation_rate * 100,
                )

        # Class distribution summary
        class_summary = report.get("class_distribution", {})
        if isinstance(class_summary, dict):
            logger.info(
                "  - Classes: %d classes, %d samples",
                class_summary.get("num_classes", 0),
                class_summary.get("total_samples", 0),
            )
            is_balanced = class_summary.get("is_balanced", False)
            balance_status = "balanced" if is_balanced else "imbalanced"
            imbalance_ratio = class_summary.get("imbalance_ratio", 0.0)
            logger.info("  - Balance: %s (ratio: %.2f)", balance_status, imbalance_ratio)

        # Integrity summary
        integrity_summary = report.get("integrity_status", {})
        if isinstance(integrity_summary, dict):
            overall_valid = integrity_summary.get("overall_valid", False)
            integrity_status = "PASS" if overall_valid else "FAIL"
            logger.info("  - Integrity: %s", integrity_status)

        if output_path:
            logger.info("  - Report saved to: %s", output_path)

    except (FileNotFoundError, ValueError, RuntimeError):
        logger.exception("Report generation failed")


def main() -> None:
    """Main function to run all examples.

    Note: Update DATA_DIR to point to your PlantVillage dataset directory.
    """
    # Update this path to your actual dataset directory
    data_dir = "data/PlantVillage"  # Example path

    # Check if data directory exists
    if not Path(data_dir).exists():
        logger.warning("Dataset directory not found: %s", data_dir)
        logger.info("Please update data_dir in this script to point to your PlantVillage dataset")
        logger.info("Expected structure: data_dir/class_name/image_files.jpg")
        return

    # Run examples
    logger.info("Running PlantGuard data pipeline examples...")

    example_data_validation(data_dir)
    example_dataset_analysis(data_dir)
    example_integrity_check(data_dir)
    example_dataset_loading(data_dir)
    example_generate_report(data_dir, "data_quality_report.json")

    logger.info("All examples completed!")


if __name__ == "__main__":
    main()
