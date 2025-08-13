"""Unit tests for DatasetManager."""

import json
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from src.training.dataset_manager import (
    DatasetConfig,
    DatasetInfo,
    DatasetManager,
    DatasetValidationResult,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def dataset_manager(temp_dir: Path) -> DatasetManager:
    """Create a DatasetManager instance for testing."""
    return DatasetManager(base_data_dir=temp_dir)


@pytest.fixture
def sample_dataset(temp_dir: Path) -> Path:
    """Create a sample dataset structure for testing."""
    dataset_dir = temp_dir / "sample_dataset"

    # Create class directories
    class1_dir = dataset_dir / "healthy"
    class2_dir = dataset_dir / "diseased"

    class1_dir.mkdir(parents=True)
    class2_dir.mkdir(parents=True)

    # Create sample images
    for i in range(5):
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(class1_dir / f"image_{i}.jpg")

        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        img.save(class2_dir / f"image_{i}.jpg")

    return dataset_dir


class TestDatasetConfig:
    """Test DatasetConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = DatasetConfig()

        assert config.train_ratio == 0.8
        assert config.val_ratio == 0.2
        assert config.random_seed == 42
        assert config.min_samples_per_class == 10
        assert config.image_formats == [".jpg", ".jpeg", ".png"]
        assert config.quality_threshold == 0.95

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = DatasetConfig(
            train_ratio=0.7, val_ratio=0.3, random_seed=123, min_samples_per_class=5
        )

        assert config.train_ratio == 0.7
        assert config.val_ratio == 0.3
        assert config.random_seed == 123
        assert config.min_samples_per_class == 5


class TestDatasetManager:
    """Test DatasetManager class."""

    def test_init(self, temp_dir: Path) -> None:
        """Test DatasetManager initialization."""
        manager = DatasetManager(base_data_dir=temp_dir)

        assert manager.base_data_dir == temp_dir
        assert manager.raw_data_dir == temp_dir / "raw"
        assert manager.processed_data_dir == temp_dir / "processed"
        assert manager.temp_dir == temp_dir / "temp"

        # Check directories are created
        assert manager.raw_data_dir.exists()
        assert manager.processed_data_dir.exists()
        assert manager.temp_dir.exists()

    def test_download_plantvillage_success(self, dataset_manager: DatasetManager) -> None:
        """Test successful PlantVillage dataset download."""
        # Mock kaggle module
        mock_kaggle = Mock()
        mock_kaggle.api.dataset_download_files = Mock()

        with patch.dict("sys.modules", {"kaggle": mock_kaggle}):
            result = dataset_manager.download_plantvillage()

        assert result is True
        mock_kaggle.api.dataset_download_files.assert_called_once()

    def test_validate_dataset_nonexistent(self, dataset_manager: DatasetManager) -> None:
        """Test dataset validation with non-existent directory."""
        result = dataset_manager.validate_dataset(Path("/nonexistent"))

        assert result.is_valid is False
        assert result.total_files == 0
        assert result.valid_files == 0
        assert len(result.errors) > 0

    def test_validate_dataset_valid(
        self, dataset_manager: DatasetManager, sample_dataset: Path
    ) -> None:
        """Test dataset validation with valid dataset."""
        result = dataset_manager.validate_dataset(sample_dataset)

        assert result.is_valid is True
        assert result.total_files == 10
        assert result.valid_files == 10
        assert len(result.corrupted_files) == 0
        assert "healthy" in result.class_counts
        assert "diseased" in result.class_counts
        assert result.class_counts["healthy"] == 5
        assert result.class_counts["diseased"] == 5

    def test_validate_dataset_with_corrupted_file(
        self, dataset_manager: DatasetManager, temp_dir: Path
    ) -> None:
        """Test dataset validation with corrupted files."""
        dataset_dir = temp_dir / "corrupted_dataset"
        class_dir = dataset_dir / "test_class"
        class_dir.mkdir(parents=True)

        # Create a valid image
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(class_dir / "valid.jpg")

        # Create a corrupted file
        with open(class_dir / "corrupted.jpg", "w") as f:
            f.write("not an image")

        result = dataset_manager.validate_dataset(dataset_dir)

        assert result.total_files == 2
        assert result.valid_files == 1
        assert len(result.corrupted_files) == 1
        assert "corrupted.jpg" in str(result.corrupted_files[0])

    def test_prepare_dataset(
        self, dataset_manager: DatasetManager, sample_dataset: Path, temp_dir: Path
    ) -> None:
        """Test dataset preparation with train/val split."""
        output_dir = temp_dir / "prepared"
        config = DatasetConfig(train_ratio=0.8, random_seed=42)

        result = dataset_manager.prepare_dataset(sample_dataset, output_dir, config)

        assert result is True
        assert (output_dir / "train").exists()
        assert (output_dir / "val").exists()
        assert (output_dir / "train" / "healthy").exists()
        assert (output_dir / "train" / "diseased").exists()
        assert (output_dir / "val" / "healthy").exists()
        assert (output_dir / "val" / "diseased").exists()

        # Check configuration file was saved
        config_file = output_dir / "dataset_config.json"
        assert config_file.exists()

        with open(config_file) as f:
            saved_config = json.load(f)
        assert saved_config["train_ratio"] == 0.8
        assert saved_config["random_seed"] == 42

    def test_prepare_dataset_nonexistent_source(
        self, dataset_manager: DatasetManager, temp_dir: Path
    ) -> None:
        """Test dataset preparation with non-existent source."""
        output_dir = temp_dir / "prepared"
        config = DatasetConfig()

        result = dataset_manager.prepare_dataset(Path("/nonexistent"), output_dir, config)

        assert result is False

    def test_analyze_dataset(self, dataset_manager: DatasetManager, sample_dataset: Path) -> None:
        """Test dataset analysis."""
        info = dataset_manager.analyze_dataset(sample_dataset)

        assert info.name == "sample_dataset"
        assert info.total_samples == 10
        assert info.num_classes == 2
        assert "healthy" in info.class_distribution
        assert "diseased" in info.class_distribution
        assert info.class_distribution["healthy"] == 5
        assert info.class_distribution["diseased"] == 5
        assert info.dataset_size_mb > 0

    def test_analyze_dataset_with_splits(
        self, dataset_manager: DatasetManager, temp_dir: Path
    ) -> None:
        """Test dataset analysis with train/val splits."""
        dataset_dir = temp_dir / "split_dataset"
        train_dir = dataset_dir / "train" / "healthy"
        val_dir = dataset_dir / "val" / "healthy"

        train_dir.mkdir(parents=True)
        val_dir.mkdir(parents=True)

        # Create images in train and val
        for i in range(3):
            img = Image.new("RGB", (100, 100), color=(255, 0, 0))
            img.save(train_dir / f"train_{i}.jpg")

        for i in range(2):
            img = Image.new("RGB", (100, 100), color=(255, 0, 0))
            img.save(val_dir / f"val_{i}.jpg")

        info = dataset_manager.analyze_dataset(dataset_dir)

        assert info.total_samples == 5
        assert info.train_samples == 3
        assert info.val_samples == 2
        assert info.num_classes == 1
        assert "healthy" in info.class_distribution
        # For split datasets, the class_distribution is flattened to total counts
        assert info.class_distribution["healthy"] == 5

    def test_analyze_dataset_nonexistent(self, dataset_manager: DatasetManager) -> None:
        """Test dataset analysis with non-existent directory."""
        info = dataset_manager.analyze_dataset(Path("/nonexistent"))

        assert info.name == "unknown"
        assert info.total_samples == 0
        assert info.num_classes == 0
        assert info.class_distribution == {}

    def test_get_dataset_info(self, dataset_manager: DatasetManager, sample_dataset: Path) -> None:
        """Test get_dataset_info method."""
        info = dataset_manager.get_dataset_info(sample_dataset)

        # Should be same as analyze_dataset
        assert info.name == "sample_dataset"
        assert info.total_samples == 10
        assert info.num_classes == 2


class TestDatasetValidationResult:
    """Test DatasetValidationResult dataclass."""

    def test_creation(self) -> None:
        """Test creating DatasetValidationResult."""
        result = DatasetValidationResult(
            is_valid=True,
            total_files=100,
            valid_files=95,
            corrupted_files=["bad1.jpg", "bad2.jpg"],
            missing_classes=[],
            class_counts={"healthy": 50, "diseased": 45},
            errors=[],
            warnings=["Some warning"],
        )

        assert result.is_valid is True
        assert result.total_files == 100
        assert result.valid_files == 95
        assert len(result.corrupted_files) == 2
        assert len(result.warnings) == 1


class TestDatasetInfo:
    """Test DatasetInfo dataclass."""

    def test_creation(self) -> None:
        """Test creating DatasetInfo."""
        info = DatasetInfo(
            name="test_dataset",
            version="1.0.0",
            total_samples=1000,
            num_classes=10,
            class_distribution={"class1": 100, "class2": 200},
            train_samples=800,
            val_samples=200,
            dataset_size_mb=500.5,
        )

        assert info.name == "test_dataset"
        assert info.version == "1.0.0"
        assert info.total_samples == 1000
        assert info.num_classes == 10
        assert info.train_samples == 800
        assert info.val_samples == 200
        assert info.dataset_size_mb == 500.5
        assert len(info.corrupted_files) == 0  # Default empty list
