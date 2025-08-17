"""Integration tests for the production training pipeline.

These tests validate the complete training workflow from dataset preparation
to model registration and deployment.
"""

import json
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import torch
from PIL import Image

from src.core.vision import VisionAdapter
from src.training.config import TrainingConfig
from src.training.dataset_manager import DatasetManager
from src.training.model_registry import ModelRegistry
from src.training.monitor import TrainingMonitor
from src.training.production_trainer import ProductionTrainer


class TestProductionTrainingIntegration:
    """Integration tests for production training pipeline."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def dummy_dataset(self, temp_dir):
        """Create a minimal dummy dataset for testing."""
        dataset_dir = temp_dir / "dummy_dataset"

        # Create train and validation directories
        train_dir = dataset_dir / "train"
        val_dir = dataset_dir / "val"

        # Create class directories
        classes = ["healthy", "diseased"]
        for split_dir in [train_dir, val_dir]:
            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                # Create dummy images
                for i in range(5):  # 5 images per class
                    img = Image.new("RGB", (224, 224), color=(i * 50, 100, 150))
                    img.save(class_dir / f"image_{i}.jpg")

        return dataset_dir

    @pytest.fixture
    def training_config(self, dummy_dataset, temp_dir):
        """Create training configuration for tests."""
        return TrainingConfig(
            experiment_name="test_integration",
            dataset_path=dummy_dataset,
            model_architecture="resnet50",
            num_classes=2,
            epochs=2,  # Short training for tests
            batch_size=2,
            learning_rate=0.01,
            device="cpu",  # Use CPU for tests
            output_dir=temp_dir / "models",
        )

    def test_complete_training_pipeline(self, training_config, temp_dir):
        """Test the complete training pipeline from start to finish."""
        # Initialize components
        dataset_manager = DatasetManager()
        model_registry = ModelRegistry(registry_path=temp_dir / "model_registry.json")
        monitor = TrainingMonitor(experiment_name=training_config.experiment_name, log_dir=temp_dir / "runs")

        # Create trainer
        trainer = ProductionTrainer(training_config, dataset_manager)

        # Test setup
        assert trainer.setup_training(), "Training setup should succeed"

        # Test training
        result = trainer.train()
        assert result.success, f"Training should succeed: {result.error_message}"
        assert result.best_model_path.exists(), "Best model should be saved"
        assert result.best_accuracy > 0, "Should have positive accuracy"

        # Test model registration
        metadata = {
            "experiment_name": training_config.experiment_name,
            "dataset_path": str(training_config.dataset_path),
            "final_accuracy": result.best_accuracy,
            "training_time": result.training_time,
        }

        model_id = model_registry.register_model(result.best_model_path, metadata)
        assert model_id, "Model should be registered successfully"

        # Test model loading from registry
        adapter = VisionAdapter()
        adapter.load_from_registry(model_id)
        assert adapter.is_loaded, "Model should load from registry"

        # Test prediction
        test_image = Image.new("RGB", (224, 224), color=(100, 150, 200))
        prediction, confidence = adapter.predict(test_image)
        assert prediction in ["healthy", "diseased"], "Should predict valid class"
        assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"

    def test_training_with_validation(self, training_config, temp_dir):
        """Test training with validation and early stopping."""
        # Enable early stopping
        training_config.early_stopping_patience = 1
        training_config.epochs = 10  # More epochs to test early stopping

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(training_config, dataset_manager)

        # Setup and train
        assert trainer.setup_training()
        result = trainer.train()

        assert result.success
        # Should stop early due to patience
        assert result.final_epoch < training_config.epochs

    def test_checkpoint_resumption(self, training_config, temp_dir):
        """Test training resumption from checkpoint."""
        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(training_config, dataset_manager)

        # First training run (partial)
        training_config.epochs = 3
        assert trainer.setup_training()
        result1 = trainer.train()
        assert result1.success

        # Find checkpoint
        checkpoint_dir = training_config.output_dir / training_config.experiment_name / "checkpoints"
        checkpoints = list(checkpoint_dir.glob("checkpoint_epoch_*.pt"))
        assert len(checkpoints) > 0, "Should have saved checkpoints"

        # Resume training
        training_config.epochs = 5  # Train for more epochs
        training_config.resume_from_checkpoint = checkpoints[-1]  # Latest checkpoint

        trainer2 = ProductionTrainer(training_config, dataset_manager)
        assert trainer2.setup_training()
        result2 = trainer2.train()

        assert result2.success
        assert result2.final_epoch > result1.final_epoch, "Should continue from checkpoint"

    def test_model_evaluation_integration(self, training_config, temp_dir):
        """Test model evaluation after training."""
        from src.training.evaluator import ModelEvaluator

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(training_config, dataset_manager)

        # Train model
        assert trainer.setup_training()
        result = trainer.train()
        assert result.success

        # Evaluate model
        evaluator = ModelEvaluator()
        eval_result = evaluator.evaluate_model(model_path=result.best_model_path, dataset_path=training_config.dataset_path / "val", num_classes=training_config.num_classes)

        assert eval_result.accuracy > 0, "Should have positive accuracy"
        assert len(eval_result.per_class_metrics) == training_config.num_classes
        assert eval_result.confusion_matrix is not None

    def test_model_registry_operations(self, temp_dir):
        """Test model registry CRUD operations."""
        registry = ModelRegistry(registry_path=temp_dir / "test_registry.json")

        # Create dummy model file
        model_path = temp_dir / "test_model.pt"
        torch.save({"model_state_dict": {}, "num_classes": 2}, model_path)

        # Test registration
        metadata = {
            "experiment_name": "test_experiment",
            "accuracy": 0.85,
            "training_date": "2024-01-01",
        }

        model_id = registry.register_model(model_path, metadata)
        assert model_id, "Should register model successfully"

        # Test retrieval
        model_info = registry.get_model(model_id)
        assert model_info is not None, "Should retrieve model info"
        assert model_info.model_path == model_path

        # Test listing
        models = registry.list_models()
        assert len(models) == 1, "Should list one model"
        assert models[0].model_id == model_id

        # Test comparison
        # Register another model
        model_path2 = temp_dir / "test_model2.pt"
        torch.save({"model_state_dict": {}, "num_classes": 2}, model_path2)

        metadata2 = {
            "experiment_name": "test_experiment2",
            "accuracy": 0.90,
            "training_date": "2024-01-02",
        }

        model_id2 = registry.register_model(model_path2, metadata2)

        comparison = registry.compare_models([model_id, model_id2])
        assert len(comparison.models) == 2, "Should compare two models"

    def test_vision_adapter_integration(self, training_config, temp_dir):
        """Test VisionAdapter integration with new model format."""
        # Train a model first
        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(training_config, dataset_manager)

        assert trainer.setup_training()
        result = trainer.train()
        assert result.success

        # Test loading with VisionAdapter
        adapter = VisionAdapter()
        adapter.load_checkpoint(str(result.best_model_path))

        assert adapter.is_loaded, "Adapter should load model successfully"
        assert len(adapter.get_class_names()) == training_config.num_classes

        # Test compatibility check
        assert adapter.is_compatible_with_registry_format(str(result.best_model_path))

        # Test migration (should not be needed for new format)
        migrated_path = temp_dir / "migrated_model.pt"
        adapter.migrate_legacy_model(str(result.best_model_path), str(migrated_path))
        assert migrated_path.exists(), "Migration should create new file"

    def test_error_handling_and_recovery(self, training_config, temp_dir):
        """Test error handling and recovery mechanisms."""
        dataset_manager = DatasetManager()

        # Test with invalid dataset path
        invalid_config = training_config
        invalid_config.dataset_path = temp_dir / "nonexistent"

        trainer = ProductionTrainer(invalid_config, dataset_manager)
        assert not trainer.setup_training(), "Setup should fail with invalid dataset"

        # Test with invalid model architecture
        invalid_config.dataset_path = training_config.dataset_path  # Fix dataset
        invalid_config.model_architecture = "invalid_arch"

        trainer = ProductionTrainer(invalid_config, dataset_manager)
        # Should handle gracefully and fall back to default

    def test_cross_platform_compatibility(self, training_config, temp_dir):
        """Test cross-platform compatibility (macOS, Linux)."""
        import platform

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(training_config, dataset_manager)

        # Test path handling across platforms
        assert trainer.setup_training()

        # Test device detection
        if platform.system() == "Darwin":  # macOS
            # Should detect MPS if available
            if torch.backends.mps.is_available():
                assert "mps" in str(trainer.device) or "cpu" in str(trainer.device)
        elif platform.system() == "Linux":
            # Should detect CUDA if available
            if torch.cuda.is_available():
                assert "cuda" in str(trainer.device) or "cpu" in str(trainer.device)

        # Train should work regardless of platform
        result = trainer.train()
        assert result.success, "Training should work on all platforms"

    def test_performance_benchmarks(self, training_config, temp_dir):
        """Test performance benchmarks and regression testing."""
        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(training_config, dataset_manager)

        # Measure training time
        start_time = time.time()

        assert trainer.setup_training()
        result = trainer.train()

        training_time = time.time() - start_time

        assert result.success
        assert training_time < 300, "Training should complete within 5 minutes for test dataset"
        assert result.training_time > 0, "Should record training time"

        # Test memory usage (basic check)
        import psutil

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Should not use excessive memory for small test dataset
        assert memory_mb < 2000, "Should not use more than 2GB for test dataset"

    def test_end_to_end_validation(self, training_config, temp_dir):
        """Test complete end-to-end validation with sample datasets."""
        # This test validates the entire pipeline with realistic data

        # Create more realistic dummy dataset
        dataset_dir = temp_dir / "realistic_dataset"
        self._create_realistic_dataset(dataset_dir)

        training_config.dataset_path = dataset_dir
        training_config.num_classes = 4  # More classes
        training_config.epochs = 5  # More training

        # Initialize all components
        dataset_manager = DatasetManager()
        model_registry = ModelRegistry(registry_path=temp_dir / "registry.json")
        trainer = ProductionTrainer(training_config, dataset_manager)

        # Validate dataset
        validation_result = dataset_manager.validate_dataset(dataset_dir)
        assert validation_result.is_valid, "Dataset should be valid"

        # Train model
        assert trainer.setup_training()
        result = trainer.train()
        assert result.success
        assert result.best_accuracy > 0.2, "Should achieve reasonable accuracy"

        # Register model
        metadata = {
            "experiment_name": training_config.experiment_name,
            "dataset_classes": training_config.num_classes,
            "final_accuracy": result.best_accuracy,
        }

        model_id = model_registry.register_model(result.best_model_path, metadata)

        # Test model in production-like scenario
        adapter = VisionAdapter()
        adapter.load_from_registry(model_id)

        # Test on various image types
        test_images = self._create_test_images(temp_dir)
        for img_path in test_images:
            image = Image.open(img_path)
            prediction, confidence = adapter.predict(image)
            assert prediction, "Should make prediction"
            assert 0 <= confidence <= 1, "Confidence should be valid"

    def _create_realistic_dataset(self, dataset_dir: Path):
        """Create a more realistic dataset for testing."""
        classes = ["apple_healthy", "apple_scab", "tomato_healthy", "tomato_blight"]

        for split in ["train", "val"]:
            split_dir = dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                # Create more varied images
                num_images = 10 if split == "train" else 5
                for i in range(num_images):
                    # Create images with different colors/patterns
                    if "healthy" in class_name:
                        color = (50 + i * 10, 150 + i * 5, 50 + i * 8)
                    else:
                        color = (100 + i * 15, 50 + i * 3, 30 + i * 5)

                    img = Image.new("RGB", (224, 224), color=color)

                    # Add some noise/variation
                    import numpy as np

                    img_array = np.array(img)
                    noise = np.random.randint(-20, 20, img_array.shape, dtype=np.int16)
                    img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                    img = Image.fromarray(img_array)

                    img.save(class_dir / f"{class_name}_{i:03d}.jpg")

    def _create_test_images(self, temp_dir: Path) -> list[Path]:
        """Create test images for validation."""
        test_dir = temp_dir / "test_images"
        test_dir.mkdir(exist_ok=True)

        test_images = []

        # Create various test images
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        sizes = [(224, 224), (256, 256), (300, 300)]

        for i, (color, size) in enumerate(zip(colors, sizes)):
            img = Image.new("RGB", size, color=color)
            img_path = test_dir / f"test_image_{i}.jpg"
            img.save(img_path)
            test_images.append(img_path)

        return test_images


@pytest.mark.integration
class TestProductionWorkflowScript:
    """Test the production workflow script."""

    def test_workflow_script_execution(self, tmp_path):
        """Test the production workflow script can be executed."""
        # This would test the actual script execution
        # For now, we'll test the main components

        from scripts.production_training_workflow import ProductionWorkflow

        workflow = ProductionWorkflow()

        # Test prerequisite validation
        is_valid, errors = workflow.validate_prerequisites()

        # Should either be valid or have specific error messages
        if not is_valid:
            assert len(errors) > 0, "Should have error messages if invalid"
            assert all(isinstance(error, str) for error in errors), "Errors should be strings"

    def test_resource_validation(self):
        """Test system resource validation."""
        from scripts.production_training_workflow import ProductionWorkflow

        workflow = ProductionWorkflow()

        # Test resource validation
        is_valid, errors = workflow._validate_resources()

        # Should not fail on basic resource checks
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_config_selection(self):
        """Test automatic configuration selection."""
        from scripts.production_training_workflow import ProductionWorkflow

        workflow = ProductionWorkflow()

        # Mock dataset path
        with patch.object(workflow, "_get_best_dataset_path") as mock_dataset:
            mock_dataset.return_value = Path("dummy/path")

            config = workflow.select_optimal_config()

            assert config is not None
            assert config.batch_size > 0
            assert config.epochs > 0
            assert config.learning_rate > 0
