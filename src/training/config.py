"""Training configuration management for PlantGuard production training pipeline.

This module provides comprehensive training configuration with parameter validation,
resource management, and support for JSON/YAML configuration files.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for learning rate schedulers."""

    type: str = "step"
    step_size: int = 30
    gamma: float = 0.1
    patience: int = 10
    factor: float = 0.5
    T_max: int = 100
    eta_min: float = 0.0

    def __post_init__(self) -> None:
        """Validate scheduler configuration."""
        valid_types = ["step", "exponential", "cosine", "plateau", "linear", "none"]
        if self.type.lower() not in valid_types:
            raise ValueError(f"Invalid scheduler type: {self.type}. Must be one of {valid_types}")

        # Normalize type to lowercase
        self.type = self.type.lower()

        if self.step_size <= 0:
            raise ValueError("step_size must be positive")
        if not 0 < self.gamma <= 1:
            raise ValueError("gamma must be between 0 and 1")
        if self.patience <= 0:
            raise ValueError("patience must be positive")
        if not 0 < self.factor <= 1:
            raise ValueError("factor must be between 0 and 1")


@dataclass
class EarlyStoppingConfig:
    """Configuration for early stopping."""

    enabled: bool = True
    patience: int = 15
    min_delta: float = 0.001
    monitor: str = "val_loss"
    mode: str = "min"

    def __post_init__(self) -> None:
        """Validate early stopping configuration."""
        if self.patience <= 0:
            raise ValueError("patience must be positive")
        if self.min_delta < 0:
            raise ValueError("min_delta must be non-negative")

        valid_monitors = ["val_loss", "val_accuracy", "train_loss", "train_accuracy"]
        if self.monitor not in valid_monitors:
            raise ValueError(f"Invalid monitor: {self.monitor}. Must be one of {valid_monitors}")

        valid_modes = ["min", "max"]
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid mode: {self.mode}. Must be one of {valid_modes}")


@dataclass
class DataAugmentationConfig:
    """Configuration for data augmentation."""

    enabled: bool = True
    rotation: float = 15.0
    brightness: float = 0.2
    contrast: float = 0.2
    horizontal_flip: bool = True
    vertical_flip: bool = False
    normalize: bool = True

    def __post_init__(self) -> None:
        """Validate data augmentation configuration."""
        if not 0 <= self.rotation <= 180:
            raise ValueError("rotation must be between 0 and 180 degrees")
        if not 0 <= self.brightness <= 1:
            raise ValueError("brightness must be between 0 and 1")
        if not 0 <= self.contrast <= 1:
            raise ValueError("contrast must be between 0 and 1")


@dataclass
class TrainingConfig:
    """Comprehensive training configuration with validation and resource management.

    This class provides a complete configuration system for production training
    with parameter validation, automatic resource detection, and support for
    multiple optimizers and schedulers.
    """

    # Experiment metadata
    experiment_name: str = "plantguard_production"
    experiment_description: str = "Production training with PlantVillage dataset"
    tags: list[str] = field(default_factory=lambda: ["production", "resnet50"])

    # Model parameters
    model_architecture: str = "resnet50"
    num_classes: int = 38
    pretrained: bool = True
    freeze_backbone: bool = False
    dropout_rate: float = 0.5

    # Training parameters
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    weight_decay: float = 1e-4
    optimizer: str = "adam"
    momentum: float = 0.9  # For SGD

    # Scheduler configuration
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)

    # Early stopping configuration
    early_stopping: EarlyStoppingConfig = field(default_factory=EarlyStoppingConfig)

    # Data augmentation configuration
    data_augmentation: DataAugmentationConfig = field(default_factory=DataAugmentationConfig)

    # Advanced training options
    mixed_precision: bool = True
    gradient_accumulation_steps: int = 1
    gradient_clip_norm: float | None = 1.0

    # Resource management
    device: str = "auto"
    num_workers: int = 4
    pin_memory: bool = True
    persistent_workers: bool = True

    # Dataset configuration
    train_ratio: float = 0.8
    val_ratio: float = 0.2
    random_seed: int = 42

    # Checkpointing and logging
    save_every_n_epochs: int = 10
    log_every_n_steps: int = 100
    max_checkpoints_to_keep: int = 5

    def __post_init__(self) -> None:
        """Validate all configuration parameters."""
        self._validate_model_params()
        self._validate_training_params()
        self._validate_resource_params()
        self._validate_dataset_params()
        self._validate_logging_params()

    def _validate_model_params(self) -> None:
        """Validate model-related parameters."""
        valid_architectures = ["resnet50", "resnet18", "resnet34", "resnet101", "resnet152"]
        if self.model_architecture not in valid_architectures:
            raise ValueError(
                f"Invalid architecture: {self.model_architecture}. "
                f"Must be one of {valid_architectures}"
            )

        if self.num_classes <= 0:
            raise ValueError("num_classes must be positive")

        if not 0 <= self.dropout_rate <= 1:
            raise ValueError("dropout_rate must be between 0 and 1")

    def _validate_training_params(self) -> None:
        """Validate training-related parameters."""
        if self.epochs <= 0:
            raise ValueError("epochs must be positive")

        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")

        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")

        if self.weight_decay < 0:
            raise ValueError("weight_decay must be non-negative")

        valid_optimizers = ["adam", "sgd", "adamw", "rmsprop"]
        if self.optimizer.lower() not in valid_optimizers:
            raise ValueError(
                f"Invalid optimizer: {self.optimizer}. Must be one of {valid_optimizers}"
            )

        if not 0 <= self.momentum <= 1:
            raise ValueError("momentum must be between 0 and 1")

        if self.gradient_accumulation_steps <= 0:
            raise ValueError("gradient_accumulation_steps must be positive")

        if self.gradient_clip_norm is not None and self.gradient_clip_norm <= 0:
            raise ValueError("gradient_clip_norm must be positive or None")

    def _validate_resource_params(self) -> None:
        """Validate resource-related parameters."""
        valid_devices = ["auto", "cpu", "cuda", "mps"]
        if self.device not in valid_devices and not self.device.startswith("cuda:"):
            raise ValueError(
                f"Invalid device: {self.device}. Must be one of {valid_devices} or 'cuda:N'"
            )

        if self.num_workers < 0:
            raise ValueError("num_workers must be non-negative")

    def _validate_dataset_params(self) -> None:
        """Validate dataset-related parameters."""
        if not 0 < self.train_ratio < 1:
            raise ValueError("train_ratio must be between 0 and 1")

        if not 0 < self.val_ratio < 1:
            raise ValueError("val_ratio must be between 0 and 1")

        if abs(self.train_ratio + self.val_ratio - 1.0) > 1e-6:
            raise ValueError("train_ratio + val_ratio must equal 1.0")

        if self.random_seed < 0:
            raise ValueError("random_seed must be non-negative")

    def _validate_logging_params(self) -> None:
        """Validate logging and checkpointing parameters."""
        if self.save_every_n_epochs <= 0:
            raise ValueError("save_every_n_epochs must be positive")

        if self.log_every_n_steps <= 0:
            raise ValueError("log_every_n_steps must be positive")

        if self.max_checkpoints_to_keep <= 0:
            raise ValueError("max_checkpoints_to_keep must be positive")

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "TrainingConfig":
        """Create TrainingConfig from dictionary.

        Args:
            config_dict: Dictionary containing configuration parameters

        Returns:
            TrainingConfig instance

        Raises:
            ValueError: If configuration is invalid
        """
        # Handle nested configurations
        if "scheduler" in config_dict and isinstance(config_dict["scheduler"], dict):
            config_dict["scheduler"] = SchedulerConfig(**config_dict["scheduler"])

        if "early_stopping" in config_dict and isinstance(config_dict["early_stopping"], dict):
            config_dict["early_stopping"] = EarlyStoppingConfig(**config_dict["early_stopping"])

        if "data_augmentation" in config_dict and isinstance(
            config_dict["data_augmentation"], dict
        ):
            config_dict["data_augmentation"] = DataAugmentationConfig(
                **config_dict["data_augmentation"]
            )

        return cls(**config_dict)

    @classmethod
    def from_json(cls, json_path: str | Path) -> "TrainingConfig":
        """Load configuration from JSON file.

        Args:
            json_path: Path to JSON configuration file

        Returns:
            TrainingConfig instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid or configuration is invalid
        """
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {json_path}")

        try:
            with open(json_path, encoding="utf-8") as f:
                config_dict = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_path}: {e}")

        return cls.from_dict(config_dict)

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "TrainingConfig":
        """Load configuration from YAML file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            TrainingConfig instance

        Raises:
            ImportError: If PyYAML is not installed
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid or configuration is invalid
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML support. Install with: pip install PyYAML"
            )

        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        try:
            with open(yaml_path, encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {yaml_path}: {e}")

        return cls.from_dict(config_dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return asdict(self)

    def to_json(self, json_path: str | Path, indent: int = 2) -> None:
        """Save configuration to JSON file.

        Args:
            json_path: Path to save JSON file
            indent: JSON indentation level
        """
        json_path = Path(json_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent, default=str)

        logger.info(f"Configuration saved to {json_path}")

    def to_yaml(self, yaml_path: str | Path) -> None:
        """Save configuration to YAML file.

        Args:
            yaml_path: Path to save YAML file

        Raises:
            ImportError: If PyYAML is not installed
        """
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required for YAML support. Install with: pip install PyYAML"
            )

        yaml_path = Path(yaml_path)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)

        logger.info(f"Configuration saved to {yaml_path}")

    def get_effective_batch_size(self) -> int:
        """Get effective batch size considering gradient accumulation.

        Returns:
            Effective batch size
        """
        return self.batch_size * self.gradient_accumulation_steps

    def validate_compatibility(self) -> list[str]:
        """Validate configuration compatibility and return warnings.

        Returns:
            List of warning messages
        """
        warnings = []

        # Check mixed precision compatibility
        if self.mixed_precision and self.device == "cpu":
            warnings.append("Mixed precision training is not supported on CPU, will be disabled")

        # Check batch size vs gradient accumulation
        effective_batch_size = self.get_effective_batch_size()
        if effective_batch_size > 512:
            warnings.append(
                f"Large effective batch size ({effective_batch_size}) may hurt performance"
            )

        # Check learning rate vs batch size
        if self.learning_rate > 0.01 and self.batch_size < 64:
            warnings.append("High learning rate with small batch size may cause instability")

        # Check early stopping vs epochs
        if self.early_stopping.enabled and self.early_stopping.patience >= self.epochs:
            warnings.append(
                "Early stopping patience is >= total epochs, early stopping may not trigger"
            )

        return warnings

    def auto_optimize_resources(self) -> "TrainingConfig":
        """Auto-optimize configuration based on available system resources.

        Returns:
            New TrainingConfig instance with optimized settings
        """
        try:
            from .resource_manager import get_resource_manager

            resource_manager = get_resource_manager()
            config_dict = self.to_dict()

            # Mark fields for auto-optimization if they have default values
            if self.device == "auto":
                config_dict["device"] = "auto"
            if hasattr(self, "_auto_batch_size") or self.batch_size == 32:  # Default batch size
                config_dict["batch_size"] = "auto"
            if self.num_workers == 4:  # Default num_workers
                config_dict["num_workers"] = "auto"

            optimized_dict = resource_manager.optimize_training_config(config_dict)
            return self.from_dict(optimized_dict)

        except ImportError:
            logger.warning("Resource manager not available, skipping auto-optimization")
            return self


# Configuration templates for different training scenarios
class ConfigTemplates:
    """Pre-defined configuration templates for common training scenarios."""

    @staticmethod
    def quick_test() -> TrainingConfig:
        """Configuration for quick testing and debugging."""
        return TrainingConfig(
            experiment_name="plantguard_quick_test",
            experiment_description="Quick test configuration for debugging",
            tags=["test", "debug"],
            epochs=5,
            batch_size=16,
            learning_rate=0.01,
            num_workers=2,
            save_every_n_epochs=1,
            log_every_n_steps=10,
            early_stopping=EarlyStoppingConfig(enabled=False),
        )

    @staticmethod
    def production_training() -> TrainingConfig:
        """Configuration for production training with optimal settings."""
        return TrainingConfig(
            experiment_name="plantguard_production",
            experiment_description="Production training with full PlantVillage dataset",
            tags=["production", "resnet50", "plantvillage"],
            epochs=100,
            batch_size=64,
            learning_rate=0.001,
            optimizer="adam",
            scheduler=SchedulerConfig(type="step", step_size=30, gamma=0.1),
            early_stopping=EarlyStoppingConfig(enabled=True, patience=15),
            mixed_precision=True,
            num_workers=8,
            gradient_accumulation_steps=1,
        )

    @staticmethod
    def fine_tuning() -> TrainingConfig:
        """Configuration for fine-tuning pre-trained models."""
        return TrainingConfig(
            experiment_name="plantguard_fine_tuning",
            experiment_description="Fine-tuning pre-trained ResNet50",
            tags=["fine_tuning", "transfer_learning"],
            epochs=50,
            batch_size=32,
            learning_rate=0.0001,  # Lower learning rate for fine-tuning
            optimizer="adam",
            freeze_backbone=True,  # Start with frozen backbone
            scheduler=SchedulerConfig(type="cosine", T_max=50),
            early_stopping=EarlyStoppingConfig(enabled=True, patience=10),
            mixed_precision=True,
        )

    @staticmethod
    def memory_efficient() -> TrainingConfig:
        """Configuration for training with limited memory."""
        return TrainingConfig(
            experiment_name="plantguard_memory_efficient",
            experiment_description="Memory-efficient training configuration",
            tags=["memory_efficient", "gradient_accumulation"],
            epochs=100,
            batch_size=16,  # Smaller batch size
            gradient_accumulation_steps=4,  # Effective batch size = 64
            learning_rate=0.001,
            mixed_precision=True,
            num_workers=2,  # Fewer workers to save memory
            pin_memory=False,  # Disable pin_memory to save memory
            persistent_workers=False,
        )

    @staticmethod
    def auto_optimized() -> TrainingConfig:
        """Configuration that auto-optimizes based on available resources."""
        return TrainingConfig(
            experiment_name="plantguard_auto_optimized",
            experiment_description="Auto-optimized configuration based on system resources",
            tags=["auto_optimized", "resource_aware"],
            epochs=100,
            batch_size=32,  # Will be auto-optimized
            learning_rate=0.001,
            optimizer="adam",
            device="auto",  # Will be auto-detected
            num_workers=4,  # Will be auto-optimized
            mixed_precision=True,  # Will be validated against device capabilities
            scheduler=SchedulerConfig(type="step", step_size=30, gamma=0.1),
            early_stopping=EarlyStoppingConfig(enabled=True, patience=15),
        )


def load_config(config_path: str | Path) -> TrainingConfig:
    """Load training configuration from file.

    Automatically detects file format based on extension.

    Args:
        config_path: Path to configuration file (.json or .yaml/.yml)

    Returns:
        TrainingConfig instance

    Raises:
        ValueError: If file format is not supported
    """
    config_path = Path(config_path)
    suffix = config_path.suffix.lower()

    if suffix == ".json":
        return TrainingConfig.from_json(config_path)
    elif suffix in [".yaml", ".yml"]:
        return TrainingConfig.from_yaml(config_path)
    else:
        raise ValueError(
            f"Unsupported configuration format: {suffix}. Supported formats: .json, .yaml, .yml"
        )


def create_template_configs(output_dir: str | Path) -> None:
    """Create template configuration files for different scenarios.

    Args:
        output_dir: Directory to save template files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    templates = {
        "quick_test.json": ConfigTemplates.quick_test(),
        "production_training.json": ConfigTemplates.production_training(),
        "fine_tuning.json": ConfigTemplates.fine_tuning(),
        "memory_efficient.json": ConfigTemplates.memory_efficient(),
        "auto_optimized.json": ConfigTemplates.auto_optimized(),
    }

    for filename, config in templates.items():
        config.to_json(output_dir / filename)

    logger.info(f"Created {len(templates)} template configurations in {output_dir}")
