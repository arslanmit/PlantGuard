"""Data validation and quality checks for PlantGuard dataset.

This module provides utilities for validating image formats, detecting corruption,
analyzing dataset statistics, and ensuring data integrity for the training pipeline.
"""

import json
import logging
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
import pandas as pd
from PIL import Image, ImageFile

# Enable loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)

# Constants
BALANCE_THRESHOLD = 2.0
VALIDATION_RATE_THRESHOLD = 0.95


class ImageValidator:
    """Validator for image files with format checking and corruption detection."""

    SUPPORTED_FORMATS: ClassVar[set[str]] = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    MIN_IMAGE_SIZE = (32, 32)  # Minimum width, height
    MAX_IMAGE_SIZE = (8192, 8192)  # Maximum width, height
    MAX_FILE_SIZE_MB = 200  # Maximum file size in MB

    def __init__(self, strict_mode: bool = False) -> None:
        """Initialize image validator.

        Args:
            strict_mode: If True, raise exceptions on validation failures
        """
        self.strict_mode = strict_mode
        self.validation_results: list[dict[str, str | bool]] = []

    def _raise_if_strict(self, error_message: str) -> None:
        """Raise ValueError if in strict mode."""
        if self.strict_mode:
            raise ValueError(error_message)

    def _check_file_existence(self, image_path: Path, result: dict[str, Any]) -> bool:
        """Check if file exists and update result."""
        if not image_path.exists():
            error_msg = "File does not exist"
            result["error_message"] = error_msg
            self._raise_if_strict(error_msg)
            return False
        return True

    def _check_file_format(self, image_path: Path, result: dict[str, Any]) -> bool:
        """Check if file format is supported."""
        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            error_msg = f"Unsupported format: {image_path.suffix}"
            result["error_message"] = error_msg
            self._raise_if_strict(error_msg)
            return False
        return True

    def _check_image_dimensions(self, img: Image.Image, result: dict[str, Any]) -> bool:
        """Check if image dimensions are within acceptable range."""
        if (
            img.size[0] < self.MIN_IMAGE_SIZE[0]
            or img.size[1] < self.MIN_IMAGE_SIZE[1]
            or img.size[0] > self.MAX_IMAGE_SIZE[0]
            or img.size[1] > self.MAX_IMAGE_SIZE[1]
        ):
            error_msg = f"Invalid dimensions {img.size}, must be between {self.MIN_IMAGE_SIZE} and {self.MAX_IMAGE_SIZE}"
            result["error_message"] = error_msg
            self._raise_if_strict(error_msg)
            return False
        return True

    def _check_file_size(self, image_path: Path, result: dict[str, Any]) -> bool:
        """Check if file size is within acceptable limits."""
        file_size_bytes = image_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        result["file_size_mb"] = int(file_size_mb)

        if file_size_mb > self.MAX_FILE_SIZE_MB:
            error_msg = f"File size {file_size_mb:.1f}MB exceeds limit {self.MAX_FILE_SIZE_MB}MB"
            result["error_message"] = error_msg
            self._raise_if_strict(error_msg)
            return False
        return True

    def _validate_image_content(self, img: Image.Image, result: dict[str, Any]) -> bool:
        """Validate image content and properties."""
        result["readable"] = True
        result["dimensions"] = img.size
        result["mode"] = img.mode

        # Check image dimensions
        if not self._check_image_dimensions(img, result):
            return False

        result["size_valid"] = True

        # Try to load image data to check for corruption
        try:
            img.load()
            # Convert to RGB to ensure compatibility
            if img.mode != "RGB":
                img.convert("RGB")
        except (OSError, ValueError) as e:
            error_msg = f"Image corruption detected: {e}"
            result["error_message"] = error_msg
            self._raise_if_strict(error_msg)
            return False

        return True

    def validate_image_file(self, image_path: str | Path) -> dict[str, Any]:
        """Validate a single image file for format, corruption, and size constraints.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing validation results
        """
        image_path = Path(image_path)
        result = {
            "path": str(image_path),
            "exists": False,
            "valid_format": False,
            "readable": False,
            "size_valid": False,
            "file_size_mb": 0,
            "dimensions": (0, 0),
            "mode": "",
            "error_message": "",
        }

        try:
            # Check if file exists
            if not image_path.exists():
                result["error_message"] = "File does not exist"
                return result

            result["exists"] = True

            # Check file size
            file_size_bytes = image_path.stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)
            result["file_size_mb"] = int(file_size_mb)

            if file_size_mb > self.MAX_FILE_SIZE_MB:
                error_msg = f"File size {file_size_mb:.1f}MB exceeds limit {self.MAX_FILE_SIZE_MB}MB"
                result["error_message"] = error_msg
                self._raise_if_strict(error_msg)

            # Check file extension
            if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
                error_msg = f"Unsupported format: {image_path.suffix}"
                result["error_message"] = error_msg
                self._raise_if_strict(error_msg)
                return result

            result["valid_format"] = True

            # Try to open and validate image
            with Image.open(image_path) as img:
                result["readable"] = True
                result["dimensions"] = img.size
                result["mode"] = img.mode

                # Check image dimensions
                width, height = img.size
                if (
                    width < self.MIN_IMAGE_SIZE[0]
                    or height < self.MIN_IMAGE_SIZE[1]
                    or width > self.MAX_IMAGE_SIZE[0]
                    or height > self.MAX_IMAGE_SIZE[1]
                ):
                    error_msg = f"Invalid dimensions {img.size}, must be between {self.MIN_IMAGE_SIZE} and {self.MAX_IMAGE_SIZE}"
                    result["error_message"] = error_msg
                    self._raise_if_strict(error_msg)
                    return result

                result["size_valid"] = True

                # Try to load image data to check for corruption
                img.load()

                # Convert to RGB to ensure compatibility
                if img.mode != "RGB":
                    img.convert("RGB")

        except (OSError, ValueError) as e:
            result["error_message"] = f"Image validation failed: {e!s}"
            if self.strict_mode:
                raise
            logger.warning("Image validation failed for %s: %s", image_path, e)

        return result

    def validate_dataset_directory(self, data_dir: str | Path) -> dict[str, Any]:
        """Validate all images in a dataset directory structure.

        Args:
            data_dir: Root directory containing class subdirectories

        Returns:
            Dictionary containing comprehensive validation results
        """
        data_dir = Path(data_dir)

        if not data_dir.exists():
            error_msg = f"Dataset directory does not exist: {data_dir}"
            raise FileNotFoundError(error_msg)

        # Find all image files
        image_files: list[Path] = []
        for ext in self.SUPPORTED_FORMATS:
            image_files.extend(data_dir.rglob(f"*{ext}"))
            image_files.extend(data_dir.rglob(f"*{ext.upper()}"))

        logger.info("Found %d image files in %s", len(image_files), data_dir)

        # Validate each image
        valid_images = []
        invalid_images = []
        validation_details = []

        for image_path in image_files:
            result = self.validate_image_file(image_path)
            validation_details.append(result)

            if result["exists"] and result["valid_format"] and result["readable"] and result["size_valid"]:
                valid_images.append(str(image_path))
            else:
                invalid_images.append(str(image_path))

        # Compile summary
        validation_rate = len(valid_images) / len(image_files) if image_files else 0.0
        summary = {
            "total_files": len(image_files),
            "valid_images": len(valid_images),
            "invalid_images": len(invalid_images),
            "validation_rate": validation_rate,
            "valid_image_paths": valid_images,
            "invalid_image_paths": invalid_images,
            "validation_details": validation_details,
        }

        validation_rate_percent: float = validation_rate * 100
        logger.info(
            "Validation complete: %d/%d images valid (%.1f%%)",
            summary["valid_images"],
            summary["total_files"],
            validation_rate_percent,
        )

        return summary


class DatasetAnalyzer:
    """Analyzer for dataset statistics and class distribution analysis."""

    def __init__(self) -> None:
        """Initialize dataset analyzer."""

    def analyze_class_distribution(self, data_dir: str | Path) -> dict[str, Any]:
        """Analyze class distribution in the dataset directory.

        Args:
            data_dir: Root directory containing class subdirectories

        Returns:
            Dictionary containing class distribution analysis
        """
        data_dir = Path(data_dir)

        if not data_dir.exists():
            msg = f"Dataset directory does not exist: {data_dir}"
            raise FileNotFoundError(msg)

        # Find class directories
        class_dirs = [d for d in data_dir.iterdir() if d.is_dir()]

        if not class_dirs:
            msg = f"No class directories found in {data_dir}"
            raise ValueError(msg)

        # Count images per class
        class_counts: dict[str, int] = {}
        total_images = 0

        validator = ImageValidator(strict_mode=False)

        for class_dir in class_dirs:
            class_name = class_dir.name

            # Find valid images in class directory
            validation_result = validator.validate_dataset_directory(class_dir)
            valid_count = validation_result["valid_images"]
            if not isinstance(valid_count, int):
                valid_count = 0

            class_counts[class_name] = valid_count
            total_images += valid_count

        # Calculate statistics
        counts = list(class_counts.values())
        if not counts:
            msg = "No valid images found in any class directory"
            raise ValueError(msg)

        min_count = min(counts)
        max_count = max(counts)
        mean_count = float(np.mean(counts))
        std_count = float(np.std(counts))
        median_count = float(np.median(counts))

        # Calculate class balance metrics
        imbalance_ratio = max_count / min_count if min_count > 0 else float("inf")

        # Create DataFrame for detailed analysis
        df = pd.DataFrame(
            [
                {
                    "class_name": class_name,
                    "sample_count": count,
                    "percentage": (count / total_images) * 100,
                }
                for class_name, count in class_counts.items()
            ]
        ).sort_values("sample_count", ascending=False)

        analysis = {
            "num_classes": len(class_counts),
            "total_samples": total_images,
            "class_counts": class_counts,
            "min_samples": min_count,
            "max_samples": max_count,
            "mean_samples": mean_count,
            "std_samples": std_count,
            "median_samples": median_count,
            "imbalance_ratio": imbalance_ratio,
            "class_distribution_df": df,
            "is_balanced": imbalance_ratio <= BALANCE_THRESHOLD,
        }

        logger.info(
            "Class distribution analysis: %d classes, %d total samples",
            analysis["num_classes"],
            analysis["total_samples"],
        )
        balance_status = "balanced" if analysis["is_balanced"] else "imbalanced"
        logger.info("Imbalance ratio: %.2f (%s)", imbalance_ratio, balance_status)

        return analysis

    def analyze_image_properties(self, data_dir: str | Path, sample_size: int | None = 1000) -> dict[str, Any]:
        """Analyze image properties like dimensions, file sizes, and color distributions.

        Args:
            data_dir: Root directory containing images
            sample_size: Number of images to sample for analysis (None for all)

        Returns:
            Dictionary containing image property analysis
        """
        data_dir = Path(data_dir)

        # Find all valid images
        validator = ImageValidator(strict_mode=False)
        validation_result = validator.validate_dataset_directory(data_dir)
        valid_image_paths = validation_result["valid_image_paths"]

        if not isinstance(valid_image_paths, list):
            msg = "No valid images found for analysis"
            raise TypeError(msg)

        # Sample images if requested
        if sample_size and len(valid_image_paths) > sample_size:
            indices = np.random.choice(len(valid_image_paths), sample_size, replace=False)
            sampled_images = [valid_image_paths[i] for i in indices]
        else:
            sampled_images = valid_image_paths

        logger.info("Analyzing properties of %d images", len(sampled_images))

        # Collect image properties
        widths: list[int] = []
        heights: list[int] = []
        file_sizes: list[float] = []
        aspect_ratios: list[float] = []
        modes: list[str] = []

        for image_path in sampled_images:
            try:
                path = Path(image_path)

                # File size
                file_size_mb = path.stat().st_size / (1024 * 1024)
                file_sizes.append(file_size_mb)

                # Image properties
                with Image.open(path) as img:
                    width, height = img.size
                    widths.append(width)
                    heights.append(height)
                    aspect_ratios.append(width / height)
                    modes.append(img.mode)

            except (OSError, ValueError) as e:
                logger.warning("Failed to analyze %s: %s", image_path, e)
                continue

        # Calculate statistics
        return {
            "sample_size": len(sampled_images),
            "dimensions": {
                "widths": np.array(widths),
                "heights": np.array(heights),
                "width_stats": {
                    "min": float(np.min(widths)),
                    "max": float(np.max(widths)),
                    "mean": float(np.mean(widths)),
                    "std": float(np.std(widths)),
                    "median": float(np.median(widths)),
                },
                "height_stats": {
                    "min": float(np.min(heights)),
                    "max": float(np.max(heights)),
                    "mean": float(np.mean(heights)),
                    "std": float(np.std(heights)),
                    "median": float(np.median(heights)),
                },
            },
            "file_sizes": {
                "sizes_mb": np.array(file_sizes),
                "stats": {
                    "min": float(np.min(file_sizes)),
                    "max": float(np.max(file_sizes)),
                    "mean": float(np.mean(file_sizes)),
                    "std": float(np.std(file_sizes)),
                    "median": float(np.median(file_sizes)),
                },
            },
            "aspect_ratios": {
                "ratios": np.array(aspect_ratios),
                "stats": {
                    "min": float(np.min(aspect_ratios)),
                    "max": float(np.max(aspect_ratios)),
                    "mean": float(np.mean(aspect_ratios)),
                    "std": float(np.std(aspect_ratios)),
                    "median": float(np.median(aspect_ratios)),
                },
            },
            "color_modes": {
                "mode_counts": pd.Series(modes).value_counts().to_dict(),
            },
        }


class DataIntegrityChecker:
    """Checker for data integrity issues in the training pipeline."""

    def __init__(self) -> None:
        """Initialize data integrity checker."""

    def check_directory_structure(self, data_dir: str | Path) -> dict[str, Any]:
        """Check if dataset directory follows expected structure.

        Args:
            data_dir: Root directory to check

        Returns:
            Dictionary containing structure validation results
        """
        data_dir = Path(data_dir)

        class_directories: list[str] = []
        empty_directories: list[str] = []
        non_directory_files: list[str] = []

        result = {
            "valid_structure": False,
            "class_directories": class_directories,
            "empty_directories": empty_directories,
            "non_directory_files": non_directory_files,
            "error_message": "",
        }

        if not data_dir.exists():
            result["error_message"] = f"Directory does not exist: {data_dir}"
            return result

        if not data_dir.is_dir():
            result["error_message"] = f"Path is not a directory: {data_dir}"
            return result

        # Check for class directories
        items = list(data_dir.iterdir())

        for item in items:
            if item.is_dir():
                class_directories.append(item.name)

                # Check if directory is empty
                if not any(item.iterdir()):
                    empty_directories.append(item.name)
            else:
                non_directory_files.append(item.name)

        # Validate structure
        if not class_directories:
            result["error_message"] = "No class directories found"
        elif empty_directories:
            result["error_message"] = f"Empty class directories found: {empty_directories}"
        else:
            result["valid_structure"] = True

        return result

    def check_class_consistency(self, data_dir: str | Path, min_samples_per_class: int = 10) -> dict[str, Any]:
        """Check consistency of classes and minimum sample requirements.

        Args:
            data_dir: Root directory containing class subdirectories
            min_samples_per_class: Minimum number of samples required per class

        Returns:
            Dictionary containing class consistency results
        """
        analyzer = DatasetAnalyzer()

        try:
            class_analysis = analyzer.analyze_class_distribution(data_dir)
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            return {
                "consistent": False,
                "insufficient_classes": [],
                "class_counts": {},
                "min_samples_required": min_samples_per_class,
                "error_message": str(e),
            }

        class_counts_raw = class_analysis.get("class_counts", {})
        if not isinstance(class_counts_raw, dict):
            return {
                "consistent": False,
                "insufficient_classes": [],
                "class_counts": {},
                "min_samples_required": min_samples_per_class,
                "error_message": "Invalid class counts format",
            }

        class_counts = dict(class_counts_raw)
        insufficient_classes = [class_name for class_name, count in class_counts.items() if count < min_samples_per_class]

        result = {
            "consistent": len(insufficient_classes) == 0,
            "insufficient_classes": insufficient_classes,
            "class_counts": class_counts,
            "min_samples_required": min_samples_per_class,
            "error_message": "",
        }

        if insufficient_classes:
            result["error_message"] = f"Classes with insufficient samples: {insufficient_classes}"

        return result

    def run_full_integrity_check(self, data_dir: str | Path, min_samples_per_class: int = 10) -> dict[str, Any]:
        """Run comprehensive data integrity check.

        Args:
            data_dir: Root directory to check
            min_samples_per_class: Minimum samples required per class

        Returns:
            Dictionary containing full integrity check results
        """
        logger.info("Running full integrity check on %s", data_dir)

        # Check directory structure
        structure_check = self.check_directory_structure(data_dir)

        # Check image validation
        validator = ImageValidator(strict_mode=False)
        validation_check = validator.validate_dataset_directory(data_dir) if structure_check.get("valid_structure", False) else {}

        # Check class consistency
        consistency_check = self.check_class_consistency(data_dir, min_samples_per_class) if structure_check.get("valid_structure", False) else {}

        # Overall integrity status
        validation_rate = validation_check.get("validation_rate", 0)
        if isinstance(validation_rate, int | float):
            validation_rate_ok = validation_rate > VALIDATION_RATE_THRESHOLD
        else:
            validation_rate_ok = False

        overall_valid = (
            bool(structure_check.get("valid_structure", False)) and validation_rate_ok and bool(consistency_check.get("consistent", False))
        )

        result = {
            "overall_valid": overall_valid,
            "structure_check": structure_check,
            "validation_check": validation_check,
            "consistency_check": consistency_check,
        }

        if overall_valid:
            logger.info("Data integrity check passed")
        else:
            logger.warning("Data integrity check failed - see detailed results")

        return result


def generate_data_report(data_dir: str | Path, output_path: str | Path | None = None) -> dict[str, Any]:
    """Generate comprehensive data quality report.

    Args:
        data_dir: Root directory containing dataset
        output_path: Optional path to save report as JSON

    Returns:
        Dictionary containing comprehensive data report
    """
    logger.info("Generating data quality report for %s", data_dir)

    # Initialize components
    validator = ImageValidator(strict_mode=False)
    analyzer = DatasetAnalyzer()
    integrity_checker = DataIntegrityChecker()

    # Run all checks
    try:
        validation_results = validator.validate_dataset_directory(data_dir)
        class_analysis = analyzer.analyze_class_distribution(data_dir)
        image_analysis = analyzer.analyze_image_properties(data_dir, sample_size=500)
        integrity_results = integrity_checker.run_full_integrity_check(data_dir)

        # Extract file size stats safely
        file_sizes_data = image_analysis.get("file_sizes", {})
        if isinstance(file_sizes_data, dict):
            file_size_stats = file_sizes_data.get("stats", {})
        else:
            file_size_stats = {}

        # Extract aspect ratio stats safely
        aspect_ratios_data = image_analysis.get("aspect_ratios", {})
        if isinstance(aspect_ratios_data, dict):
            aspect_ratio_stats = aspect_ratios_data.get("stats", {})
        else:
            aspect_ratio_stats = {}

        # Extract structure check safely
        structure_check = integrity_results.get("structure_check", {})
        structure_valid = False
        if isinstance(structure_check, dict):
            structure_valid = bool(structure_check.get("valid_structure", False))

        # Extract consistency check safely
        consistency_check = integrity_results.get("consistency_check", {})
        classes_consistent = False
        if isinstance(consistency_check, dict):
            classes_consistent = bool(consistency_check.get("consistent", False))

        report = {
            "dataset_path": str(data_dir),
            "report_timestamp": pd.Timestamp.now().isoformat(),
            "validation_summary": {
                "total_files": validation_results.get("total_files", 0),
                "valid_images": validation_results.get("valid_images", 0),
                "validation_rate": validation_results.get("validation_rate", 0.0),
            },
            "class_distribution": {
                "num_classes": class_analysis.get("num_classes", 0),
                "total_samples": class_analysis.get("total_samples", 0),
                "imbalance_ratio": class_analysis.get("imbalance_ratio", 0.0),
                "is_balanced": class_analysis.get("is_balanced", False),
            },
            "image_properties": {
                "sample_size": image_analysis.get("sample_size", 0),
                "dimension_stats": image_analysis.get("dimensions", {}),
                "file_size_stats": file_size_stats,
                "aspect_ratio_stats": aspect_ratio_stats,
            },
            "integrity_status": {
                "overall_valid": integrity_results.get("overall_valid", False),
                "structure_valid": structure_valid,
                "classes_consistent": classes_consistent,
            },
        }

        # Save report if output path provided
        if output_path:
            output_path = Path(output_path)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info("Data report saved to %s", output_path)

        return report

    except Exception:
        logger.exception("Failed to generate data report")
        raise
