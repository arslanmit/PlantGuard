"""Unit tests for training configuration management."""

from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.training.config import (
    ConfigTemplates,
    DataAugmentationConfig,
    EarlyStoppingConfig,
    SchedulerConfig,
    TrainingConfig,
    create_template_configs,
    load_config,
)


class TestSchedulerConfig:
    """Test SchedulerConfig validation and functionality."""


    def test_valid_scheduler_config(self) -> None:
        """Test valid scheduler configuration."""
        config = SchedulerConfig(type="step", step_size=30, gamma=0.1)
        assert config.type == "step"
        assert config.step_size == 30
        assert config.gamma == 0.1

    def test_invalid_scheduler_type(self) -> None:
        """Test invalid scheduler type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid scheduler type"):
            SchedulerConfig(type="invalid")

    def test_invalid_step_size(self) -> None:
        """Test invalid step size raises ValueError."""
        with pytest.raises(ValueError, match="step_size must be positive"):
            SchedulerConfig(step_size=0)

    def test_invalid_gamma(self) -> None:
        """Test invalid gamma raises ValueError."""
        with pytest.raises(ValueError, match="gamma must be between 0 and 1"):
            SchedulerConfig(gamma=1.5)


class TestEarlyStoppingConfig:
    """Test EarlyStoppingConfig validation and functionality."""

    def test_valid_early_stopping_config(self) -> None:
        """Test valid early stopping configuration."""
        config = EarlyStoppingConfig(enabled=True, patience=10, min_delta=0.001)
        assert config.enabled is True
        assert config.patience == 10
        assert config.min_delta == 0.001

    def test_invalid_patience(self) -> None:
        """Test invalid patience raises ValueError."""
        with pytest.raises(ValueError, match="patience must be positive"):
            EarlyStoppingConfig(patience=0)

    def test_invalid_monitor(self) -> None:
        """Test invalid monitor raises ValueError."""
        with pytest.raises(ValueError, match="Invalid monitor"):
            EarlyStoppingConfig(monitor="invalid")

    def test_invalid_mode(self) -> None:
        """Test invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid mode"):
            EarlyStoppingConfig(mode="invalid")


class TestDataAugmentationConfig:
    """Test DataAugmentationConfig validation and functionality."""

    def test_valid_augmentation_config(self) -> None:
        """Test valid data augmentation configuration."""
        config = DataAugmentationConfig(rotation=15.0, brightness=0.2)
        assert config.rotation == 15.0
        assert config.brightness == 0.2

    def test_invalid_rotation(self) -> None:
        """Test invalid rotation raises ValueError."""
        with pytest.raises(ValueError, match="rotation must be between 0 and 180"):
            DataAugmentationConfig(rotation=200.0)

    def test_invalid_brightness(self) -> None:
        """Test invalid brightness raises ValueError."""
        with pytest.raises(ValueError, match="brightness must be between 0 and 1"):
            DataAugmentationConfig(brightness=1.5)


class TestTrainingConfig:
    """Test TrainingConfig validation and functionality."""

    def test_default_config(self) -> None:
        """Test default configuration is valid."""
        config = TrainingConfig()
        assert config.experiment_name == "plantguard_production"
        assert config.model_architecture == "resnet50"
        assert config.epochs == 100
        assert config.batch_size == 32
        assert config.learning_rate == 0.001

    def test_invalid_architecture(self) -> None:
        """Test invalid architecture raises ValueError."""
        with pytest.raises(ValueError, match="Invalid architecture"):
            TrainingConfig(model_architecture="invalid")

    def test_invalid_epochs(self) -> None:
        """Test invalid epochs raises ValueError."""
        with pytest.raises(ValueError, match="epochs must be positive"):
            TrainingConfig(epochs=0)

    def test_invalid_batch_size(self) -> None:
        """Test invalid batch size raises ValueError."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            TrainingConfig(batch_size=0)

    def test_invalid_learning_rate(self) -> None:
        """Test invalid learning rate raises ValueError."""
        with pytest.raises(ValueError, match="learning_rate must be positive"):
            TrainingConfig(learning_rate=0)

    def test_invalid_optimizer(self) -> None:
        """Test invalid optimizer raises ValueError."""
        with pytest.raises(ValueError, match="Invalid optimizer"):
            TrainingConfig(optimizer="invalid")

    def test_invalid_device(self) -> None:
        """Test invalid device raises ValueError."""
        with pytest.raises(ValueError, match="Invalid device"):
            TrainingConfig(device="invalid")

    def test_invalid_train_ratio(self) -> None:
        """Test invalid train ratio raises ValueError."""
        with pytest.raises(ValueError, match="train_ratio must be between 0 and 1"):
            TrainingConfig(train_ratio=1.5)

    def test_invalid_ratio_sum(self) -> None:
        """Test invalid ratio sum raises ValueError."""
        with pytest.raises(ValueError, match="train_ratio \\+ val_ratio must equal 1.0"):
            TrainingConfig(train_ratio=0.7, val_ratio=0.4)

    def test_effective_batch_size(self) -> None:
        """Test effective batch size calculation."""
        config = TrainingConfig(batch_size=32, gradient_accumulation_steps=2)
        assert config.get_effective_batch_size() == 64

    def test_compatibility_warnings(self) -> None:
        """Test configuration compatibility warnings."""
        config = TrainingConfig(mixed_precision=True, device="cpu", batch_size=1024, learning_rate=0.1)
        warnings = config.validate_compatibility()
        assert len(warnings) > 0
        assert any("Mixed precision" in warning for warning in warnings)

    def test_to_dict(self) -> None:
        """Test configuration to dictionary conversion."""
        config = TrainingConfig(experiment_name="test", epochs=50)
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["experiment_name"] == "test"
        assert config_dict["epochs"] == 50

    def test_from_dict(self) -> None:
        """Test configuration from dictionary creation."""
        config_dict = {
            "experiment_name": "test",
            "epochs": 50,
            "batch_size": 16,
            "scheduler": {"type": "cosine", "T_max": 50},
        }
        config = TrainingConfig.from_dict(config_dict)
        assert config.experiment_name == "test"
        assert config.epochs == 50
        assert config.scheduler.type == "cosine"

    def test_json_serialization(self) -> None:
        """Test JSON serialization and deserialization."""
        config = TrainingConfig(experiment_name="test", epochs=50)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config.to_json(f.name)
            json_path = Path(f.name)

        try:
            loaded_config = TrainingConfig.from_json(json_path)
            assert loaded_config.experiment_name == "test"
            assert loaded_config.epochs == 50
        finally:
            json_path.unlink()

    @patch("src.training.config.YAML_AVAILABLE", True)
    def test_yaml_serialization(self) -> None:
        """Test YAML serialization and deserialization."""
        config = TrainingConfig(experiment_name="test", epochs=50)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config.to_yaml(f.name)
            yaml_path = Path(f.name)

        try:
            loaded_config = TrainingConfig.from_yaml(yaml_path)
            assert loaded_config.experiment_name == "test"
            assert loaded_config.epochs == 50
        finally:
            yaml_path.unlink()

    def test_yaml_not_available(self) -> None:
        """Test YAML operations when PyYAML is not available."""
        with patch("src.training.config.YAML_AVAILABLE", False):
            config = TrainingConfig()

            with pytest.raises(ImportError, match="PyYAML is required"):
                config.to_yaml("test.yaml")

            with pytest.raises(ImportError, match="PyYAML is required"):
                TrainingConfig.from_yaml("test.yaml")

    def test_file_not_found(self) -> None:
        """Test loading from non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            TrainingConfig.from_json("nonexistent.json")

    def test_invalid_json(self) -> None:
        """Test loading invalid JSON raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            json_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                TrainingConfig.from_json(json_path)
        finally:
            json_path.unlink()

    def test_auto_optimize_resources(self) -> None:
        """Test auto resource optimization method exists and returns TrainingConfig."""
        config = TrainingConfig(experiment_name="test", device="auto", epochs=50)

        # Test that the method exists and returns a TrainingConfig
        optimized = config.auto_optimize_resources()
        assert isinstance(optimized, TrainingConfig)
        assert optimized.experiment_name == "test"
        assert optimized.epochs == 50


class TestConfigTemplates:
    """Test configuration templates."""

    def test_quick_test_template(self) -> None:
        """Test quick test template."""
        config = ConfigTemplates.quick_test()
        assert config.experiment_name == "plantguard_quick_test"
        assert config.epochs == 5
        assert config.batch_size == 16
        assert config.early_stopping.enabled is False

    def test_production_training_template(self) -> None:
        """Test production training template."""
        config = ConfigTemplates.production_training()
        assert config.experiment_name == "plantguard_production"
        assert config.epochs == 100
        assert config.batch_size == 64
        assert config.mixed_precision is True

    def test_fine_tuning_template(self) -> None:
        """Test fine-tuning template."""
        config = ConfigTemplates.fine_tuning()
        assert config.experiment_name == "plantguard_fine_tuning"
        assert config.learning_rate == 0.0001
        assert config.freeze_backbone is True
        assert config.scheduler.type == "cosine"

    def test_memory_efficient_template(self) -> None:
        """Test memory-efficient template."""
        config = ConfigTemplates.memory_efficient()
        assert config.experiment_name == "plantguard_memory_efficient"
        assert config.batch_size == 16
        assert config.gradient_accumulation_steps == 4
        assert config.get_effective_batch_size() == 64

    def test_auto_optimized_template(self) -> None:
        """Test auto-optimized template."""
        config = ConfigTemplates.auto_optimized()
        assert config.experiment_name == "plantguard_auto_optimized"
        assert config.device == "auto"
        assert config.mixed_precision is True
        assert config.epochs == 100


class TestUtilityFunctions:
    """Test utility functions."""

    def test_load_config_json(self) -> None:
        """Test loading configuration from JSON file."""
        config = TrainingConfig(experiment_name="test")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config.to_json(f.name)
            json_path = Path(f.name)

        try:
            loaded_config = load_config(json_path)
            assert loaded_config.experiment_name == "test"
        finally:
            json_path.unlink()

    def test_load_config_unsupported_format(self) -> None:
        """Test loading configuration with unsupported format."""
        with pytest.raises(ValueError, match="Unsupported configuration format"):
            load_config("config.txt")

    def test_create_template_configs(self) -> None:
        """Test creating template configuration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            create_template_configs(output_dir)

            # Check that template files were created
            expected_files = [
                "quick_test.json",
                "production_training.json",
                "fine_tuning.json",
                "memory_efficient.json",
                "auto_optimized.json",
            ]

            for filename in expected_files:
                file_path = output_dir / filename
                assert file_path.exists()

                # Verify the file can be loaded
                config = TrainingConfig.from_json(file_path)
                assert isinstance(config, TrainingConfig)


if __name__ == "__main__":
    pytest.main([__file__])
