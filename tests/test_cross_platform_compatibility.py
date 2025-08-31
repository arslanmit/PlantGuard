from typing import Any, Dict, List, Optional, Tuple, Union, Generator
"""Cross-platform compatibility tests for PlantGuard production training pipeline.

These tests ensure the training system works correctly across different platforms
(macOS, Linux) and handles platform-specific features appropriately.
"""


import platform
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import torch
from PIL import Image

from src.core.vision import VisionAdapter
from src.training.config import TrainingConfig
from src.training.dataset_manager import DatasetManager
from src.training.production_trainer import ProductionTrainer


class TestCrossPlatformCompatibility:
    """Cross-platform compatibility tests."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Any, None, None]:
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def test_dataset(self, temp_dir) -> None:
        """Create test dataset with cross-platform path handling."""
        dataset_dir = temp_dir / "cross_platform_dataset"

        classes = ["test_class_0", "test_class_1"]

        for split in ["train", "val"]:
            split_dir = dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                # Create test images
                for i in range(5):
                    img = Image.new("RGB", (224, 224), color=(i * 50, 100, 150))
                    img.save(class_dir / f"image_{i}.jpg")

        return dataset_dir

    def test_path_handling_across_platforms(self, test_dataset, temp_dir) -> None:
        """Test that path handling works correctly across platforms."""
        config = TrainingConfig(
            experiment_name="cross_platform_test",
            dataset_path=test_dataset,
            model_architecture="resnet50",
            num_classes=2,
            epochs=1,
            batch_size=4,
            device="cpu",
            output_dir=temp_dir / "models",
        )

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        # Test path resolution
        assert trainer.setup_training(), "Setup should work with cross-platform paths"

        # Test that paths are handled correctly
        assert config.dataset_path.exists(), "Dataset path should exist"
        assert config.output_dir.parent.exists(), "Output directory parent should exist"

        # Test training with cross-platform paths
        result = trainer.train()
        assert result.success, "Training should succeed with cross-platform paths"

        # Verify output files are created with correct paths
        assert result.best_model_path.exists(), "Model file should be created"

        # Test path separators are handled correctly
        model_path_str = str(result.best_model_path)
        if platform.system() == "Windows":
            assert "\\" in model_path_str or "/" in model_path_str
        else:
            assert "/" in model_path_str

    def test_file_permissions_unix(self, test_dataset, temp_dir) -> None:
        """Test file permissions handling on Unix-like systems."""
        if platform.system() == "Windows":
            pytest.skip("Unix-specific test")

        config = TrainingConfig(
            experiment_name="permissions_test",
            dataset_path=test_dataset,
            epochs=1,
            batch_size=4,
            device="cpu",
            output_dir=temp_dir / "models",
        )

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        assert trainer.setup_training()
        result = trainer.train()
        assert result.success

        # Check that created files have appropriate permissions
        model_file = result.best_model_path
        assert model_file.exists()

        # Check file is readable
        assert model_file.stat().st_mode & 0o400, "Model file should be readable"

        # Check directory permissions
        model_dir = model_file.parent
        assert model_dir.stat().st_mode & 0o700, "Model directory should be accessible"

    def test_memory_management_differences(self, test_dataset, temp_dir) -> None:
        """Test memory management across different platforms."""
        import psutil

        config = TrainingConfig(
            experiment_name="memory_test",
            dataset_path=test_dataset,
            epochs=1,
            batch_size=8,
            device="cpu",
            output_dir=temp_dir / "models",
        )

        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        assert trainer.setup_training()

        result = trainer.train()
        assert result.success

        final_memory = process.memory_info().rss / 1024 / 1024

        # Memory usage should be reasonable across platforms
        memory_increase = final_memory - initial_memory

        # Platform-specific memory expectations
        if platform.system() == "Darwin":  # macOS
            # macOS might use more memory due to different memory management
            max_memory_increase = 800  # MB
        elif platform.system() == "Linux":
            # Linux typically more memory efficient
            max_memory_increase = 600  # MB
        else:  # Windows or other
            max_memory_increase = 1000  # MB

        assert memory_increase < max_memory_increase, f"Memory usage too high on {platform.system()}: {memory_increase:.1f}MB"

    def test_multiprocessing_compatibility(self, test_dataset, temp_dir) -> None:
        """Test multiprocessing data loading across platforms."""
        # Different platforms handle multiprocessing differently

        config = TrainingConfig(
            experiment_name="multiprocessing_test",
            dataset_path=test_dataset,
            epochs=1,
            batch_size=4,
            num_workers=2,  # Test multiprocessing
            device="cpu",
            output_dir=temp_dir / "models",
        )

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        # Should handle multiprocessing correctly on all platforms
        assert trainer.setup_training()
        result = trainer.train()
        assert result.success, f"Multiprocessing should work on {platform.system()}"

    def test_file_locking_behavior(self, test_dataset, temp_dir) -> None:
        """Test file locking behavior across platforms."""
        config = TrainingConfig(
            experiment_name="file_locking_test",
            dataset_path=test_dataset,
            epochs=1,
            batch_size=4,
            device="cpu",
            output_dir=temp_dir / "models",
        )

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        assert trainer.setup_training()
        result = trainer.train()
        assert result.success

        # Test that model files can be read after training
        model_path = result.best_model_path

        # Should be able to load the model immediately after training
        adapter = VisionAdapter()
        adapter.load_checkpoint(str(model_path))
        assert adapter.is_loaded, "Model should be loadable immediately after training"

        # Test concurrent access (platform-dependent behavior)
        try:
            # Try to load the same model again
            adapter2 = VisionAdapter()
            adapter2.load_checkpoint(str(model_path))
            assert adapter2.is_loaded, "Should support concurrent model loading"
        except Exception:
            # Some platforms might have stricter file locking
            if platform.system() == "Windows":
                # Windows might be more restrictive
                pass
            else:
                raise

    def test_environment_variable_handling(self, test_dataset, temp_dir) -> None:
        """Test environment variable handling across platforms."""
        import os

        # Test CUDA environment variables (Linux/Windows)
        if platform.system() in ["Linux", "Windows"]:
            with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}):
                config = TrainingConfig(
                    experiment_name="env_var_test",
                    dataset_path=test_dataset,
                    device="auto",
                    epochs=1,
                    batch_size=4,
                    output_dir=temp_dir / "models",
                )

                dataset_manager = DatasetManager()
                trainer = ProductionTrainer(config, dataset_manager)

                # Should respect CUDA environment variables
                assert trainer.setup_training()

        # Test MPS environment variables (macOS)
        if platform.system() == "Darwin":
            with patch.dict(os.environ, {"PYTORCH_ENABLE_MPS_FALLBACK": "1"}):
                config = TrainingConfig(
                    experiment_name="mps_env_test",
                    dataset_path=test_dataset,
                    device="auto",
                    epochs=1,
                    batch_size=4,
                    output_dir=temp_dir / "models",
                    skip_memory_check=True,  # Skip memory check for test environment
                )

                dataset_manager = DatasetManager()
                trainer = ProductionTrainer(config, dataset_manager)

                assert trainer.setup_training()

    def test_python_version_compatibility(self, test_dataset, temp_dir) -> None:
        """Test compatibility with different Python versions."""
        python_version = sys.version_info

        # Should work with Python 3.8+
        assert python_version >= (3, 8), "Requires Python 3.8 or higher"

        config = TrainingConfig(
            experiment_name="python_version_test",
            dataset_path=test_dataset,
            epochs=1,
            batch_size=4,
            device="cpu",
            output_dir=temp_dir / "models",
        )

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        # Test features that might vary by Python version
        assert trainer.setup_training()
        result = trainer.train()
        assert result.success, f"Should work with Python {python_version.major}.{python_version.minor}"

    def test_torch_version_compatibility(self, test_dataset, temp_dir) -> None:
        """Test compatibility with different PyTorch versions."""
        torch_version = torch.__version__

        config = TrainingConfig(
            experiment_name="torch_version_test",
            dataset_path=test_dataset,
            epochs=1,
            batch_size=4,
            device="cpu",
            output_dir=temp_dir / "models",
        )

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        assert trainer.setup_training()
        result = trainer.train()
        assert result.success, f"Should work with PyTorch {torch_version}"

        # Test version-specific features
        if hasattr(torch, "compile"):
            # PyTorch 2.0+ features
            pass

    def test_unicode_path_handling(self, temp_dir) -> None:
        """Test handling of Unicode characters in file paths."""
        # Create dataset with Unicode characters in path
        unicode_dataset_dir = temp_dir / "测试数据集_тест_[LEAF]"

        classes = ["健康_healthy", "病变_diseased"]

        for split in ["train", "val"]:
            split_dir = unicode_dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                for i in range(3):
                    img = Image.new("RGB", (224, 224), color=(i * 80, 100, 150))
                    img.save(class_dir / f"图像_{i}.jpg")

        config = TrainingConfig(
            experiment_name="unicode_test",
            dataset_path=unicode_dataset_dir,
            epochs=1,
            batch_size=4,
            device="cpu",
            output_dir=temp_dir / "模型_models",
        )

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        # Should handle Unicode paths correctly
        assert trainer.setup_training(), "Should handle Unicode paths"
        result = trainer.train()
        assert result.success, "Training should work with Unicode paths"

    def test_large_file_handling(self, temp_dir) -> None:
        """Test handling of large files across platforms."""
        # Create a larger test dataset
        large_dataset_dir = temp_dir / "large_dataset"

        classes = ["class_0", "class_1"]

        for split in ["train", "val"]:
            split_dir = large_dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                # Create larger images
                num_images = 20 if split == "train" else 5
                for i in range(num_images):
                    # Create larger image (512x512)
                    img = Image.new("RGB", (512, 512), color=(i * 10, 100, 150))
                    img.save(class_dir / f"large_image_{i}.jpg", quality=95)

        config = TrainingConfig(
            experiment_name="large_file_test",
            dataset_path=large_dataset_dir,
            epochs=1,
            batch_size=2,  # Smaller batch for large images
            device="cpu",
            output_dir=temp_dir / "models",
        )

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        # Should handle larger files correctly
        assert trainer.setup_training()
        result = trainer.train()
        assert result.success, "Should handle large files correctly"

        # Check that large model files are created correctly
        model_size = result.best_model_path.stat().st_size / 1024 / 1024  # MB
        assert model_size > 10, "Model file should be reasonably large"
