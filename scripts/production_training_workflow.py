"""Production Training Workflow for PlantGuard.

This script orchestrates the complete production training pipeline including:
- Prerequisites validation (dataset, resources, disk space)
- Optimal configuration selection based on available resources
- Production training execution with monitoring
- Model registration and evaluation
- Integration with existing PlantGuard components
"""

import argparse
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import torch
from torch.utils.tensorboard import SummaryWriter

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from training.config import TrainingConfig
from training.dataset_manager import DatasetManager
from training.model_registry import ModelRegistry
from training.monitor import TrainingMonitor
from training.production_trainer import ProductionTrainer
from utils.logging_config import setup_logging


class ProductionWorkflow:
    """Production training workflow orchestrator."""

    def __init__(self, config_path: Path | None = None):
        """Initialize production workflow."""
        self.logger = logging.getLogger(__name__)
        self.dataset_manager = DatasetManager()
        self.model_registry = ModelRegistry()
        self.config_path = config_path

        # Minimum requirements
        self.min_disk_space_gb = 10.0  # GB
        self.min_memory_gb = 4.0  # GB
        self.recommended_memory_gb = 8.0  # GB

    def validate_prerequisites(self) -> tuple[bool, list[str]]:
        """Validate all prerequisites for production training.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check dataset availability
        dataset_valid, dataset_errors = self._validate_dataset()
        if not dataset_valid:
            errors.extend(dataset_errors)

        # Check system resources
        resource_valid, resource_errors = self._validate_resources()
        if not resource_valid:
            errors.extend(resource_errors)

        # Check disk space
        disk_valid, disk_errors = self._validate_disk_space()
        if not disk_valid:
            errors.extend(disk_errors)

        return len(errors) == 0, errors

    def _validate_dataset(self) -> tuple[bool, list[str]]:
        """Validate dataset availability and integrity."""
        errors = []

        # Check for processed PlantVillage dataset
        processed_train = Path("data/processed/plantvillage/train")
        processed_val = Path("data/processed/plantvillage/val")

        # Check for legacy PlantVillage dataset
        legacy_train = Path("data/PlantVillage/train")
        legacy_val = Path("data/PlantVillage/val")

        # Check for dummy dataset
        dummy_train = Path("data/plantvillage_dummy_improved/train")
        dummy_val = Path("data/plantvillage_dummy_improved/val")

        if processed_train.exists() and processed_val.exists():
            self.logger.info("✅ Found processed PlantVillage dataset")
            # Validate dataset integrity
            try:
                validation_result = self.dataset_manager.validate_dataset(Path("data/processed/plantvillage"))
                if not validation_result.is_valid:
                    errors.append(f"Dataset validation failed: {validation_result.error_message}")
            except Exception as e:
                errors.append(f"Dataset validation error: {e}")

        elif legacy_train.exists() and legacy_val.exists():
            self.logger.info("✅ Found legacy PlantVillage dataset")

        elif dummy_train.exists() and dummy_val.exists():
            self.logger.warning("⚠️  Using dummy dataset - not recommended for production")

        else:
            errors.append("No suitable dataset found. Please run one of:\n  - make download-dataset && make prepare-dataset (recommended)\n  - make dummy-dataset (testing only)")

        return len(errors) == 0, errors

    def _validate_resources(self) -> tuple[bool, list[str]]:
        """Validate system resources (GPU, memory)."""
        errors = []

        # Check memory
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < self.min_memory_gb:
            errors.append(f"Insufficient memory: {memory_gb:.1f}GB < {self.min_memory_gb}GB required")
        elif memory_gb < self.recommended_memory_gb:
            self.logger.warning(f"⚠️  Low memory: {memory_gb:.1f}GB < {self.recommended_memory_gb}GB recommended")

        # Check GPU availability
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            self.logger.info(f"✅ Found {gpu_count} GPU(s) with {gpu_memory:.1f}GB memory")
        elif torch.backends.mps.is_available():
            self.logger.info("✅ Found Apple Silicon GPU (MPS)")
        else:
            self.logger.warning("⚠️  No GPU found - training will use CPU (slower)")

        return len(errors) == 0, errors

    def _validate_disk_space(self) -> tuple[bool, list[str]]:
        """Validate available disk space."""
        errors = []

        # Check disk space in data directory
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        disk_usage = shutil.disk_usage(data_dir)
        free_gb = disk_usage.free / (1024**3)

        if free_gb < self.min_disk_space_gb:
            errors.append(f"Insufficient disk space: {free_gb:.1f}GB < {self.min_disk_space_gb}GB required")
        else:
            self.logger.info(f"✅ Available disk space: {free_gb:.1f}GB")

        return len(errors) == 0, errors

    def select_optimal_config(self) -> TrainingConfig:
        """Select optimal training configuration based on available resources.

        Returns:
            Optimized TrainingConfig
        """
        # Get system info
        memory_gb = psutil.virtual_memory().total / (1024**3)
        has_gpu = torch.cuda.is_available() or torch.backends.mps.is_available()

        # Determine dataset path
        dataset_path = self._get_best_dataset_path()

        # Base configuration
        config = TrainingConfig(
            experiment_name=f"production_training_{int(time.time())}",
            model_architecture="resnet50",
            num_classes=38,  # PlantVillage has 38 classes
            pretrained=True,
        )

        # Store dataset path separately (will be passed to trainer)
        self.selected_dataset_path = dataset_path

        # Adjust based on resources
        if has_gpu and memory_gb >= 16:
            # High-end configuration
            config.batch_size = 64
            config.num_workers = 8
            config.mixed_precision = True
            config.epochs = 100
            self.logger.info("🚀 Using high-performance configuration")

        elif has_gpu and memory_gb >= 8:
            # Medium configuration
            config.batch_size = 32
            config.num_workers = 4
            config.mixed_precision = True
            config.epochs = 50
            self.logger.info("⚡ Using medium-performance configuration")

        elif has_gpu:
            # Low-end GPU configuration
            config.batch_size = 16
            config.num_workers = 2
            config.mixed_precision = False
            config.epochs = 30
            self.logger.info("🔋 Using low-resource GPU configuration")

        else:
            # CPU-only configuration
            config.batch_size = 8
            config.num_workers = 2
            config.mixed_precision = False
            config.epochs = 20
            config.device = "cpu"
            self.logger.info("💻 Using CPU-only configuration")

        # Enable early stopping for production
        config.early_stopping_patience = max(10, config.epochs // 5)

        return config

    def _get_best_dataset_path(self) -> Path:
        """Get the best available dataset path."""
        # Priority order: processed > legacy > dummy
        candidates = [
            Path("data/processed/plantvillage"),
            Path("data/PlantVillage"),
            Path("data/plantvillage_dummy_improved"),
            Path("data/plantvillage_dummy"),
        ]

        for path in candidates:
            if (path / "train").exists() and (path / "val").exists():
                return path

        raise RuntimeError("No suitable dataset found")

    def _prepare_dataset_for_training(self) -> None:
        """Ensure dataset is available at the expected location for training."""
        expected_path = Path("data/processed/plantvillage")

        # If the expected path already exists, we're good
        if expected_path.exists() and (expected_path / "train").exists() and (expected_path / "val").exists():
            self.logger.info(f"✅ Dataset already available at {expected_path}")
            return

        # Find the best available dataset
        try:
            actual_dataset_path = self.selected_dataset_path
            self.logger.info(f"📂 Preparing dataset from {actual_dataset_path} to {expected_path}")

            # Create the expected directory structure
            expected_path.parent.mkdir(parents=True, exist_ok=True)

            # Create symlink to the actual dataset
            if expected_path.exists():
                expected_path.unlink()  # Remove existing symlink/directory

            expected_path.symlink_to(actual_dataset_path.resolve())
            self.logger.info(f"✅ Created symlink: {expected_path} -> {actual_dataset_path}")

        except Exception as e:
            self.logger.error(f"❌ Failed to prepare dataset: {e}")
            raise RuntimeError(f"Could not prepare dataset for training: {e}")

    def run_production_training(self, config: TrainingConfig) -> bool:
        """Run the complete production training pipeline.

        Args:
            config: Training configuration

        Returns:
            True if training succeeded, False otherwise
        """
        try:
            self.logger.info("🚀 Starting production training pipeline...")

            # Ensure dataset is available at expected location
            self._prepare_dataset_for_training()

            # Initialize components
            monitor = TrainingMonitor(experiment_name=config.experiment_name, log_dir=Path("runs") / config.experiment_name)

            trainer = ProductionTrainer(config, self.dataset_manager)

            # Setup training
            self.logger.info("⚙️  Setting up training environment...")
            if not trainer.setup_training():
                self.logger.error("❌ Training setup failed")
                return False

            # Start training
            self.logger.info("🎯 Starting model training...")
            training_result = trainer.train()

            if training_result.success:
                self.logger.info("✅ Training completed successfully!")

                # Register model
                model_metadata = {
                    "experiment_name": config.experiment_name,
                    "dataset_path": str(config.dataset_path),
                    "final_accuracy": training_result.best_accuracy,
                    "training_time": training_result.training_time,
                    "config": config.to_dict(),
                }

                model_id = self.model_registry.register_model(model_path=training_result.best_model_path, metadata=model_metadata)

                self.logger.info(f"📝 Model registered with ID: {model_id}")

                # Generate training report
                report_path = monitor.save_training_report(training_result)
                self.logger.info(f"📊 Training report saved to: {report_path}")

                return True

            else:
                self.logger.error(f"❌ Training failed: {training_result.error_message}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Production training failed: {e}")
            return False

    def send_notification(self, success: bool, message: str) -> None:
        """Send training completion notification."""
        status = "✅ SUCCESS" if success else "❌ FAILED"
        self.logger.info(f"🔔 NOTIFICATION: {status} - {message}")

        # In a real production environment, you might send:
        # - Email notifications
        # - Slack messages
        # - System notifications
        # For now, we just log the notification

    def run_workflow(self) -> int:
        """Run the complete production training workflow.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            self.logger.info("🌿 PlantGuard Production Training Workflow")
            self.logger.info("=" * 50)

            # Step 1: Validate prerequisites
            self.logger.info("1️⃣  Validating prerequisites...")
            is_valid, errors = self.validate_prerequisites()

            if not is_valid:
                self.logger.error("❌ Prerequisites validation failed:")
                for error in errors:
                    self.logger.error(f"   • {error}")
                self.send_notification(False, "Prerequisites validation failed")
                return 1

            self.logger.info("✅ All prerequisites validated")

            # Step 2: Select optimal configuration
            self.logger.info("2️⃣  Selecting optimal configuration...")
            config = self.select_optimal_config()
            self.logger.info(f"📋 Configuration: {config.batch_size} batch size, {config.epochs} epochs")

            # Step 3: Run production training
            self.logger.info("3️⃣  Running production training...")
            success = self.run_production_training(config)

            if success:
                self.send_notification(True, f"Training completed successfully: {config.experiment_name}")
                self.logger.info("🎉 Production training workflow completed successfully!")
                return 0
            else:
                self.send_notification(False, f"Training failed: {config.experiment_name}")
                self.logger.error("💥 Production training workflow failed!")
                return 1

        except Exception as e:
            self.logger.error(f"💥 Workflow error: {e}")
            self.send_notification(False, f"Workflow error: {e}")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PlantGuard Production Training Workflow")
    parser.add_argument("--config", type=Path, help="Path to custom training configuration file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Logging level")

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level)

    # Run workflow
    workflow = ProductionWorkflow(config_path=args.config)
    exit_code = workflow.run_workflow()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
