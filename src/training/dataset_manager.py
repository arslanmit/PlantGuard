"""Dataset management for PlantGuard production training pipeline."""

import json
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

# Constants for image validation
MIN_IMAGE_SIZE = 32
MAX_IMAGE_SIZE = 4096
MIN_SAMPLES_PER_CLASS = 10


@dataclass
class DatasetConfig:
    """Configuration for dataset preparation."""

    train_ratio: float = 0.8
    val_ratio: float = 0.2
    random_seed: int = 42
    min_samples_per_class: int = 10
    image_formats: list[str] = field(default_factory=lambda: [".jpg", ".jpeg", ".png"])
    quality_threshold: float = 0.95


@dataclass
class DatasetInfo:
    """Information about a dataset."""

    name: str
    version: str
    total_samples: int
    num_classes: int
    class_distribution: dict[str, int] | dict[str, dict[str, int]]
    train_samples: int
    val_samples: int
    dataset_size_mb: float
    corrupted_files: list[str] = field(default_factory=list)


@dataclass
class DatasetValidationResult:
    """Result of dataset validation."""

    is_valid: bool
    total_files: int
    valid_files: int
    corrupted_files: list[str]
    missing_classes: list[str]
    class_counts: dict[str, int]
    errors: list[str]
    warnings: list[str]


class DatasetManager:
    """Manages dataset download, validation, and preparation for production training."""

    def __init__(self, base_data_dir: Path = Path("data")):
        """Initialize DatasetManager.

        Args:
            base_data_dir: Base directory for storing datasets
        """
        self.base_data_dir = Path(base_data_dir)
        self.raw_data_dir = self.base_data_dir / "raw"
        self.processed_data_dir = self.base_data_dir / "processed"
        self.temp_dir = self.base_data_dir / "temp"

        # Create directories if they don't exist
        for dir_path in [self.raw_data_dir, self.processed_data_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def download_plantvillage(self, target_dir: Path | None = None) -> bool:
        """Download PlantVillage dataset from Kaggle.

        Args:
            target_dir: Directory to download dataset to. If None, uses raw_data_dir.

        Returns:
            True if download successful, False otherwise
        """
        if target_dir is None:
            target_dir = self.raw_data_dir / "plantvillage"

        target_dir = Path(target_dir)

        # Check if dataset already exists
        if target_dir.exists() and self._is_valid_plantvillage_dataset(target_dir):
            logger.info("PlantVillage dataset already exists at %s", target_dir)
            logger.info("✅ PlantVillage dataset already exists at %s", target_dir)
            logger.info("📊 Validating existing dataset...")

            # Quick validation
            validation_result = self.validate_dataset(target_dir)
            if validation_result.is_valid:
                logger.info(
                    "✅ Dataset is valid: %s files, %s total",
                    validation_result.valid_files,
                    validation_result.total_files,
                )
                logger.info("🔄 Skipping download. Use --force to re-download.")
                return True
            else:
                logger.warning("⚠️  Existing dataset appears corrupted. Proceeding with download...")

        try:
            # Check if kaggle is available
            import kaggle

            logger.info("Starting PlantVillage dataset download...")

            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Download dataset using Kaggle API
            kaggle.api.dataset_download_files(
                "abdallahalidev/plantvillage-dataset", path=str(target_dir), unzip=True
            )

            logger.info("PlantVillage dataset downloaded to %s", target_dir)
            return True

        except ImportError:
            logger.exception("Kaggle API not available. Please install with: pip install kaggle")
            logger.exception("Also ensure you have configured Kaggle API credentials.")
            return False
        except Exception:
            logger.exception("Failed to download PlantVillage dataset")
            return False

    def _is_valid_plantvillage_dataset(self, dataset_dir: Path) -> bool:
        """Check if directory contains a valid PlantVillage dataset structure.

        Args:
            dataset_dir: Directory to check

        Returns:
            True if appears to be a valid PlantVillage dataset
        """
        if not dataset_dir.exists():
            return False

        # Check for common PlantVillage class directories
        expected_classes = [
            "Potato___Early_blight",
            "Potato___Late_blight",
            "Potato___healthy",
            "Tomato___Early_blight",
            "Tomato___Late_blight",
            "Tomato___healthy",
        ]

        # Look for class directories (either directly or in subdirectories)
        found_classes = 0

        # Check direct structure
        for class_dir in dataset_dir.iterdir():
            if class_dir.is_dir() and any(
                expected in class_dir.name for expected in expected_classes
            ):
                found_classes += 1

        # Check if there are subdirectories that might contain the classes
        if found_classes == 0:
            for subdir in dataset_dir.iterdir():
                if subdir.is_dir():
                    for class_dir in subdir.iterdir():
                        if class_dir.is_dir() and any(
                            expected in class_dir.name for expected in expected_classes
                        ):
                            found_classes += 1

        # Consider valid if we found at least 3 expected classes
        return found_classes >= 3

    def _validate_image_file(self, image_file: Path) -> tuple[bool, list[str]]:
        """Validate a single image file.

        Args:
            image_file: Path to image file

        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings = []
        try:
            # Try to open and validate image
            with Image.open(image_file) as img:
                # Basic validation - ensure image can be loaded
                img.verify()

            # Re-open for size check (verify() closes the image)
            with Image.open(image_file) as img:
                width, height = img.size

                # Check minimum size requirements
                if width < MIN_IMAGE_SIZE or height < MIN_IMAGE_SIZE:
                    warnings.append(f"Small image: {image_file} ({width}x{height})")

                # Check if image is too large
                if width > MAX_IMAGE_SIZE or height > MAX_IMAGE_SIZE:
                    warnings.append(f"Large image: {image_file} ({width}x{height})")

        except OSError as e:
            logger.warning("Corrupted image %s: %s", image_file, e)
            return False, warnings
        else:
            return True, warnings

    def _validate_split_dataset(
        self, dataset_dir: Path
    ) -> tuple[int, int, list[str], dict[str, int], list[str]]:
        """Validate dataset with train/val split structure.

        Returns:
            Tuple of (total_files, valid_files, corrupted_files, class_counts, warnings)
        """
        corrupted_files = []
        class_counts = {}
        total_files = 0
        valid_files = 0
        warnings = []

        # Supported image formats
        supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

        for split_name in ["train", "val"]:
            split_dir = dataset_dir / split_name
            if not split_dir.exists():
                continue

            for class_dir in split_dir.iterdir():
                if not class_dir.is_dir():
                    continue

                class_name = class_dir.name
                if class_name not in class_counts:
                    class_counts[class_name] = 0

                for image_file in class_dir.iterdir():
                    if image_file.suffix.lower() not in supported_formats:
                        continue

                    total_files += 1
                    is_valid, file_warnings = self._validate_image_file(image_file)

                    if is_valid:
                        valid_files += 1
                        class_counts[class_name] += 1
                        warnings.extend(file_warnings)
                    else:
                        corrupted_files.append(str(image_file))

        return total_files, valid_files, corrupted_files, class_counts, warnings

    def _validate_single_dataset(
        self, dataset_dir: Path
    ) -> tuple[int, int, list[str], dict[str, int], list[str]]:
        """Validate dataset with single directory structure.

        Returns:
            Tuple of (total_files, valid_files, corrupted_files, class_counts, warnings)
        """
        corrupted_files = []
        class_counts = {}
        total_files = 0
        valid_files = 0
        warnings = []

        # Supported image formats
        supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

        for class_dir in dataset_dir.iterdir():
            if not class_dir.is_dir():
                continue

            class_name = class_dir.name
            class_counts[class_name] = 0

            for image_file in class_dir.iterdir():
                if image_file.suffix.lower() not in supported_formats:
                    continue

                total_files += 1
                is_valid, file_warnings = self._validate_image_file(image_file)

                if is_valid:
                    valid_files += 1
                    class_counts[class_name] += 1
                    warnings.extend(file_warnings)
                else:
                    corrupted_files.append(str(image_file))

        return total_files, valid_files, corrupted_files, class_counts, warnings

    def validate_dataset(self, dataset_dir: Path) -> DatasetValidationResult:
        """Validate dataset integrity and quality.

        Args:
            dataset_dir: Path to dataset directory

        Returns:
            DatasetValidationResult with validation details
        """
        dataset_dir = Path(dataset_dir)

        if not dataset_dir.exists():
            return DatasetValidationResult(
                is_valid=False,
                total_files=0,
                valid_files=0,
                corrupted_files=[],
                missing_classes=[],
                class_counts={},
                errors=[f"Dataset directory does not exist: {dataset_dir}"],
                warnings=[],
            )

        logger.info("Validating dataset at %s", dataset_dir)

        errors = []

        # Check if this is a split dataset (has train/val structure)
        has_splits = (dataset_dir / "train").exists() and (dataset_dir / "val").exists()

        if has_splits:
            total_files, valid_files, corrupted_files, class_counts, warnings = (
                self._validate_split_dataset(dataset_dir)
            )
        else:
            total_files, valid_files, corrupted_files, class_counts, warnings = (
                self._validate_single_dataset(dataset_dir)
            )

        # Check for classes with too few samples
        for class_name, count in class_counts.items():
            if count < MIN_SAMPLES_PER_CLASS:
                warnings.append(
                    f"Class '{class_name}' has only {count} samples "
                    f"(minimum: {MIN_SAMPLES_PER_CLASS})"
                )

        # Check if we have any classes at all
        if not class_counts:
            errors.append("No valid classes found in dataset")

        is_valid = len(errors) == 0 and valid_files > 0

        logger.info("Dataset validation complete: %d/%d valid files", valid_files, total_files)

        return DatasetValidationResult(
            is_valid=is_valid,
            total_files=total_files,
            valid_files=valid_files,
            corrupted_files=corrupted_files,
            missing_classes=[],  # Will be populated if we have expected classes
            class_counts=class_counts,
            errors=errors,
            warnings=warnings,
        )

    def prepare_dataset(self, source_dir: Path, output_dir: Path, config: DatasetConfig) -> bool:
        """Prepare dataset with train/validation splits.

        Args:
            source_dir: Source dataset directory
            output_dir: Output directory for prepared dataset
            config: Dataset configuration

        Returns:
            True if preparation successful, False otherwise
        """
        import random

        source_dir = Path(source_dir)
        output_dir = Path(output_dir)

        if not source_dir.exists():
            logger.error("Source directory does not exist: %s", source_dir)
            return False

        # Set random seed for reproducibility
        random.seed(config.random_seed)

        # Create output directories
        train_dir = output_dir / "train"
        val_dir = output_dir / "val"

        train_dir.mkdir(parents=True, exist_ok=True)
        val_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Preparing dataset from %s to %s", source_dir, output_dir)

        try:
            # Process each class directory
            for class_dir in source_dir.iterdir():
                if not class_dir.is_dir():
                    continue

                class_name = class_dir.name
                logger.info("Processing class: %s", class_name)

                # Create class directories in train and val
                (train_dir / class_name).mkdir(exist_ok=True)
                (val_dir / class_name).mkdir(exist_ok=True)

                # Get all valid image files
                image_files: list[Path] = []
                for ext in config.image_formats:
                    image_files.extend(class_dir.glob(f"*{ext}"))
                    image_files.extend(class_dir.glob(f"*{ext.upper()}"))

                # Filter out corrupted files
                valid_files = []
                for img_file in image_files:
                    try:
                        with Image.open(img_file) as img:
                            img.verify()
                        valid_files.append(img_file)
                    except OSError:
                        logger.warning("Skipping corrupted file: %s", img_file)

                if len(valid_files) < config.min_samples_per_class:
                    logger.warning(
                        "Class '%s' has only %d samples (minimum: %d)",
                        class_name,
                        len(valid_files),
                        config.min_samples_per_class,
                    )

                # Shuffle files
                random.shuffle(valid_files)

                # Split into train and validation
                split_idx = int(len(valid_files) * config.train_ratio)
                train_files = valid_files[:split_idx]
                val_files = valid_files[split_idx:]

                # Copy files to respective directories
                for img_file in train_files:
                    shutil.copy2(img_file, train_dir / class_name / img_file.name)

                for img_file in val_files:
                    shutil.copy2(img_file, val_dir / class_name / img_file.name)

                logger.info(
                    "Class '%s': %d train, %d val", class_name, len(train_files), len(val_files)
                )

            # Save dataset configuration
            config_file = output_dir / "dataset_config.json"
            with config_file.open("w") as f:
                json.dump(
                    {
                        "train_ratio": config.train_ratio,
                        "val_ratio": config.val_ratio,
                        "random_seed": config.random_seed,
                        "min_samples_per_class": config.min_samples_per_class,
                        "image_formats": config.image_formats,
                        "quality_threshold": config.quality_threshold,
                    },
                    f,
                    indent=2,
                )

            logger.info("Dataset preparation complete. Configuration saved to %s", config_file)
            return True

        except Exception:
            logger.exception("Failed to prepare dataset")
            return False

    def _analyze_split_dataset(
        self, dataset_dir: Path
    ) -> tuple[dict[str, dict[str, int]], int, int, int, list[str]]:
        """Analyze dataset with train/val split structure.

        Returns:
            Tuple of (class_distribution, total_samples, train_samples, val_samples,
                     corrupted_files)
        """
        class_distribution: dict[str, dict[str, int]] = {}
        train_samples = 0
        val_samples = 0
        dataset_size_bytes = 0
        corrupted_files = []

        for split_name in ["train", "val"]:
            split_dir = dataset_dir / split_name
            if not split_dir.exists():
                continue

            for class_dir in split_dir.iterdir():
                if not class_dir.is_dir():
                    continue

                class_name = class_dir.name
                if class_name not in class_distribution:
                    class_distribution[class_name] = {"train": 0, "val": 0}

                # Count files in this class
                class_count = 0
                for img_file in class_dir.iterdir():
                    if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"]:
                        try:
                            # Verify image can be opened
                            with Image.open(img_file) as img:
                                img.verify()
                            class_count += 1
                            dataset_size_bytes += img_file.stat().st_size
                        except OSError:
                            corrupted_files.append(str(img_file))

                class_distribution[class_name][split_name] = class_count

                if split_name == "train":
                    train_samples += class_count
                else:
                    val_samples += class_count

        total_samples = train_samples + val_samples
        return class_distribution, total_samples, train_samples, val_samples, corrupted_files

    def _analyze_single_dataset(self, dataset_dir: Path) -> tuple[dict[str, int], int, list[str]]:
        """Analyze dataset with single directory structure.

        Returns:
            Tuple of (class_distribution, total_samples, corrupted_files)
        """
        class_distribution: dict[str, int] = {}
        total_samples = 0
        corrupted_files = []

        for class_dir in dataset_dir.iterdir():
            if not class_dir.is_dir():
                continue

            class_name = class_dir.name
            class_count = 0

            for img_file in class_dir.iterdir():
                if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"]:
                    try:
                        with Image.open(img_file) as img:
                            img.verify()
                        class_count += 1
                    except OSError:
                        corrupted_files.append(str(img_file))

            class_distribution[class_name] = class_count
            total_samples += class_count

        return class_distribution, total_samples, corrupted_files

    def analyze_dataset(self, dataset_dir: Path) -> DatasetInfo:
        """Analyze dataset and generate statistics.

        Args:
            dataset_dir: Path to dataset directory

        Returns:
            DatasetInfo with analysis results
        """
        dataset_dir = Path(dataset_dir)

        if not dataset_dir.exists():
            logger.error("Dataset directory does not exist: %s", dataset_dir)
            return DatasetInfo(
                name="unknown",
                version="unknown",
                total_samples=0,
                num_classes=0,
                class_distribution={},
                train_samples=0,
                val_samples=0,
                dataset_size_mb=0.0,
            )

        logger.info("Analyzing dataset at %s", dataset_dir)

        # Check if this is a split dataset (has train/val dirs)
        has_splits = (dataset_dir / "train").exists() and (dataset_dir / "val").exists()

        if has_splits:
            split_class_distribution, total_samples, train_samples, val_samples, corrupted_files = (
                self._analyze_split_dataset(dataset_dir)
            )
            # Convert nested dict to flat dict by summing train and val
            flat_class_distribution: dict[str, int] = {}
            for class_name, counts in split_class_distribution.items():
                flat_class_distribution[class_name] = counts.get("train", 0) + counts.get("val", 0)
        else:
            flat_class_distribution, total_samples, corrupted_files = self._analyze_single_dataset(
                dataset_dir
            )
            train_samples = 0
            val_samples = 0

        # Calculate dataset size (simplified - we'll estimate based on file count)
        dataset_size_mb = total_samples * 0.5  # Rough estimate of 0.5MB per image

        logger.info(
            "Dataset analysis complete: %d samples, %d classes",
            total_samples,
            len(flat_class_distribution),
        )

        return DatasetInfo(
            name=dataset_dir.name,
            version="1.0.0",  # Default version
            total_samples=total_samples,
            num_classes=len(flat_class_distribution),
            class_distribution=flat_class_distribution,
            train_samples=train_samples,
            val_samples=val_samples,
            dataset_size_mb=dataset_size_mb,
            corrupted_files=corrupted_files,
        )

    def get_dataset_info(self, dataset_dir: Path) -> DatasetInfo:
        """Get basic dataset information.

        Args:
            dataset_dir: Path to dataset directory

        Returns:
            DatasetInfo with basic information
        """
        return self.analyze_dataset(dataset_dir)
