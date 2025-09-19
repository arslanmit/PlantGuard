from typing import Any, Dict, List, Optional, Tuple, Union, Generator
"""Tests for PlantGuard data pipeline utilities.

This module contains unit tests for dataset loading, validation,
and analysis functionality.
"""


import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from plantguard.data import (
    DataIntegrityChecker,
    DatasetAnalyzer,
    DataTransforms,
    ImageValidator,
    PlantVillageDataset,
    create_stratified_split,
)


@pytest.fixture
def temp_dataset_dir() -> Generator[Path]:
    """Create a temporary dataset directory with sample images for testing.

    Yields:
        Path to temporary dataset directory
    """
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create class directories
        class_names = ["healthy", "diseased", "pest_damage"]

        for class_name in class_names:
            class_dir = temp_dir / class_name
            class_dir.mkdir()

            # Create sample images for each class
            num_images = 15 if class_name == "healthy" else 10  # Slight imbalance

            for i in range(num_images):
                # Create a simple colored image
                if class_name == "healthy":
                    color = (0, 255, 0)  # Green
                elif class_name == "diseased":
                    color = (255, 255, 0)  # Yellow
                else:
                    color = (255, 0, 0)  # Red

                # Create image with some variation
                img_array = np.full((224, 224, 3), color, dtype=np.uint8)
                noise = np.random.randint(-20, 20, img_array.shape, dtype=np.int16)
                img_array_int = img_array.astype(np.int16) + noise
                img_array = np.clip(img_array_int, 0, 255).astype(np.uint8)

                img = Image.fromarray(img_array)
                img_path = class_dir / f"{class_name}_{i:03d}.jpg"
                img.save(img_path, "JPEG")

        # Create one corrupted file
        corrupted_file = temp_dir / "healthy" / "corrupted.jpg"
        with corrupted_file.open("w") as f:
            f.write("This is not an image")

        yield temp_dir

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


class TestPlantVillageDataset:
    """Test cases for PlantVillageDataset class."""

    def test_dataset_initialization(self, temp_dataset_dir: Path) -> None:
        """Test dataset initialization and basic properties."""
        dataset = PlantVillageDataset(temp_dataset_dir)

        assert len(dataset) > 0
        assert len(dataset.classes) == 3
        assert "healthy" in dataset.classes
        assert "diseased" in dataset.classes
        assert "pest_damage" in dataset.classes

    def test_dataset_getitem(self, temp_dataset_dir: Path) -> None:
        """Test dataset item retrieval."""
        transforms = DataTransforms.get_inference_transforms()
        dataset = PlantVillageDataset(temp_dataset_dir, transform=transforms)

        image, label = dataset[0]

        assert isinstance(image, torch.Tensor)
        assert image.shape == (3, 224, 224)  # C, H, W
        assert isinstance(label, int)
        assert 0 <= label < len(dataset.classes)

    def test_class_distribution(self, temp_dataset_dir: Path) -> None:
        """Test class distribution calculation."""
        dataset = PlantVillageDataset(temp_dataset_dir)
        distribution = dataset.get_class_distribution()

        assert isinstance(distribution, dict)
        assert len(distribution) == 3
        assert distribution["healthy"] == 16  # Including corrupted file
        assert distribution["diseased"] == 10
        assert distribution["pest_damage"] == 10


class TestDataTransforms:
    """Test cases for DataTransforms class."""

    def test_train_transforms(self) -> None:
        """Test training transforms."""
        transforms = DataTransforms.get_train_transforms()

        # Create a sample image
        img = Image.new("RGB", (256, 256), color="red")
        transformed = transforms(img)

        assert isinstance(transformed, torch.Tensor)
        assert transformed.shape == (3, 224, 224)
        assert transformed.dtype == torch.float32

    def test_val_transforms(self) -> None:
        """Test validation transforms."""
        transforms = DataTransforms.get_val_transforms()

        # Create a sample image
        img = Image.new("RGB", (300, 200), color="blue")
        transformed = transforms(img)

        assert isinstance(transformed, torch.Tensor)
        assert transformed.shape == (3, 224, 224)
        assert transformed.dtype == torch.float32

    def test_inference_transforms(self) -> None:
        """Test inference transforms."""
        transforms = DataTransforms.get_inference_transforms()

        # Create a sample image
        img = Image.new("RGB", (100, 150), color="green")
        transformed = transforms(img)

        assert isinstance(transformed, torch.Tensor)
        assert transformed.shape == (3, 224, 224)
        assert transformed.dtype == torch.float32


class TestStratifiedSplit:
    """Test cases for stratified dataset splitting."""

    def test_stratified_split(self, temp_dataset_dir: Path) -> None:
        """Test stratified train/validation split."""
        dataset = PlantVillageDataset(temp_dataset_dir)
        train_dataset, val_dataset = create_stratified_split(dataset, train_ratio=0.8, random_state=42)

        # Check split sizes
        total_size = len(dataset)
        expected_train_size = int(total_size * 0.8)

        assert len(train_dataset) == expected_train_size  # type: ignore[arg-type]
        assert len(val_dataset) == total_size - expected_train_size  # type: ignore[arg-type]
        assert len(train_dataset) + len(val_dataset) == total_size  # type: ignore[arg-type]


class TestImageValidator:
    """Test cases for ImageValidator class."""

    def test_validate_valid_image(self, temp_dataset_dir: Path) -> None:
        """Test validation of valid images."""
        validator = ImageValidator(strict_mode=False)

        # Find a valid image
        valid_image = next((temp_dataset_dir / "healthy").glob("*.jpg"))
        result = validator.validate_image_file(valid_image)

        assert result["exists"] is True
        assert result["valid_format"] is True
        assert result["readable"] is True
        assert result["size_valid"] is True
        assert result["error_message"] == ""

    def test_validate_corrupted_image(self, temp_dataset_dir: Path) -> None:
        """Test validation of corrupted images."""
        validator = ImageValidator(strict_mode=False)

        # Find the corrupted file
        corrupted_file = temp_dataset_dir / "healthy" / "corrupted.jpg"
        result = validator.validate_image_file(corrupted_file)

        assert result["exists"] is True
        assert result["valid_format"] is True
        assert result["readable"] is False
        assert result["error_message"] != ""

    def test_validate_dataset_directory(self, temp_dataset_dir: Path) -> None:
        """Test validation of entire dataset directory."""
        validator = ImageValidator(strict_mode=False)
        result = validator.validate_dataset_directory(temp_dataset_dir)

        assert result["total_files"] > 0
        assert result["valid_images"] > 0
        assert result["invalid_images"] > 0  # Due to corrupted file
        assert result["validation_rate"] < 1.0  # Due to corrupted file


class TestDatasetAnalyzer:
    """Test cases for DatasetAnalyzer class."""

    def test_analyze_class_distribution(self, temp_dataset_dir: Path) -> None:
        """Test class distribution analysis."""
        analyzer = DatasetAnalyzer()
        analysis = analyzer.analyze_class_distribution(temp_dataset_dir)

        assert analysis["num_classes"] == 3
        assert analysis["total_samples"] > 0
        assert "class_counts" in analysis
        assert "imbalance_ratio" in analysis
        assert "is_balanced" in analysis
        assert "class_distribution_df" in analysis

    def test_analyze_image_properties(self, temp_dataset_dir: Path) -> None:
        """Test image properties analysis."""
        analyzer = DatasetAnalyzer()
        analysis = analyzer.analyze_image_properties(temp_dataset_dir, sample_size=10)

        assert analysis["sample_size"] <= 10
        assert "dimensions" in analysis
        assert "file_sizes" in analysis
        assert "aspect_ratios" in analysis
        assert "color_modes" in analysis


class TestDataIntegrityChecker:
    """Test cases for DataIntegrityChecker class."""

    def test_check_directory_structure(self, temp_dataset_dir: Path) -> None:
        """Test directory structure validation."""
        checker = DataIntegrityChecker()
        result = checker.check_directory_structure(temp_dataset_dir)

        assert result["valid_structure"] is True
        assert len(result["class_directories"]) == 3
        assert len(result["empty_directories"]) == 0

    def test_check_class_consistency(self, temp_dataset_dir: Path) -> None:
        """Test class consistency validation."""
        checker = DataIntegrityChecker()
        result = checker.check_class_consistency(temp_dataset_dir, min_samples_per_class=5)

        assert result["consistent"] is True
        assert len(result["insufficient_classes"]) == 0
        assert len(result["class_counts"]) == 3

    def test_run_full_integrity_check(self, temp_dataset_dir: Path) -> None:
        """Test full integrity check."""
        checker = DataIntegrityChecker()
        result = checker.run_full_integrity_check(temp_dataset_dir, min_samples_per_class=5)

        assert "overall_valid" in result
        assert "structure_check" in result
        assert "validation_check" in result
        assert "consistency_check" in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_nonexistent_directory(self) -> None:
        """Test handling of nonexistent directories."""
        validator = ImageValidator()

        with pytest.raises(FileNotFoundError):
            validator.validate_dataset_directory("/nonexistent/path")

    def test_empty_directory(self) -> None:
        """Test handling of empty directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = ImageValidator()
            result = validator.validate_dataset_directory(temp_dir)

            assert result["total_files"] == 0
            assert result["valid_images"] == 0
            assert result["validation_rate"] == 0.0

    def test_invalid_image_format(self) -> None:
        """Test handling of invalid image formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a text file with image extension
            invalid_file = Path(temp_dir) / "invalid.jpg"
            with invalid_file.open("w") as f:
                f.write("This is not an image")

            validator = ImageValidator(strict_mode=False)
            result = validator.validate_image_file(invalid_file)

            assert result["exists"] is True
            assert result["valid_format"] is True
            assert result["readable"] is False
            assert result["error_message"] != ""
