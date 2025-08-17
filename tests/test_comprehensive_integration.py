"""Comprehensive integration tests for production training pipeline.

This module provides extensive integration testing coverage for the complete
production training pipeline, including all component interactions.
"""

import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
import torch
from PIL import Image

from src.core.vision import VisionAdapter
from src.features.model_switching.model_manager import PlantGuardModelManager
from src.training.config import TrainingConfig
from src.training.dataset_manager import DatasetManager
from src.training.model_registry import ModelRegistry
from src.training.production_trainer import ProductionTrainer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestComprehensiveIntegration:
    """Comprehensive integration tests for production training pipeline."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for integration tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create workspace structure
            (workspace / "data").mkdir()
            (workspace / "models").mkdir()
            (workspace / "config").mkdir()
            (workspace / "runs").mkdir()

            yield workspace

    @pytest.fixture
    def integration_dataset(self, temp_workspace):
        """Create integration test dataset."""
        dataset_dir = temp_workspace / "data" / "integration_dataset"

        # Create realistic dataset structure
        classes = ["healthy_plant", "diseased_plant_a", "diseased_plant_b", "diseased_plant_c"]

        for split in ["train", "val"]:
            split_dir = dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                # Create sufficient samples for meaningful training
                num_samples = 20 if split == "train" else 5

                for i in range(num_samples):
                    # Create varied test images
                    color = (i * 10 % 255, (i * 15) % 255, (i * 20) % 255)
                    img = Image.new("RGB", (224, 224), color=color)
                    img.save(class_dir / f"sample_{i:03d}.jpg")

        return dataset_dir

    @pytest.fixture
    def production_config(self, integration_dataset, temp_workspace):
        """Create production-like training configuration."""
        return TrainingConfig(
            experiment_name="integration_test_production",
            dataset_path=integration_dataset,
            model_architecture="resnet50",
            num_classes=4,
            epochs=3,  # Short for testing
            batch_size=8,
            learning_rate=0.001,
            optimizer="adam",
            scheduler="step",
            device="cpu",  # Use CPU for consistent testing
            output_dir=temp_workspace / "runs",
            save_every_n_epochs=1,
            mixed_precision=False,  # Disable for compatibility
            early_stopping={"enabled": True, "patience": 10, "min_delta": 0.001},
        )

    def test_complete_training_to_deployment_workflow(self, production_config, temp_workspace):
        """Test complete workflow from training to deployment."""
        logger.info("Testing complete training to deployment workflow...")

        # 1. Initialize components
        dataset_manager = DatasetManager()
        registry = ModelRegistry(temp_workspace / "models")

        # 2. Validate dataset
        validation_result = dataset_manager.validate_dataset(production_config.dataset_path)
        assert validation_result.is_valid, f"Dataset validation failed: {validation_result.errors}"

        # 3. Analyze dataset
        analysis = dataset_manager.analyze_dataset(production_config.dataset_path)
        assert analysis.total_samples > 0, "Dataset analysis failed"
        assert len(analysis.class_distribution) == 4, "Expected 4 classes"

        # 4. Initialize and run production training
        trainer = ProductionTrainer(config=production_config, dataset_manager=dataset_manager, output_dir=production_config.output_dir / "integration_test")

        assert trainer.setup_training(), "Training setup failed"

        # Mock the actual training to avoid long execution times
        with patch.object(trainer, "_train_epoch") as mock_train_epoch:
            mock_train_epoch.return_value = {"train_loss": 0.5, "train_accuracy": 0.8, "val_loss": 0.6, "val_accuracy": 0.75}

            result = trainer.train()
            assert result.success, f"Training failed: {result.error_message}"

        # 5. Register trained model
        model_id = registry.register_model(
            model_path=result.best_model_path,
            name="integration_test_model",
            architecture=production_config.model_architecture,
            dataset_version="integration_v1.0",
            hyperparameters=production_config.to_dict(),
            performance_metrics={"accuracy": result.best_accuracy, "val_loss": result.best_val_loss},
            description="Model from integration test workflow",
            tags=["integration", "test", "production"],
        )

        assert model_id is not None, "Model registration failed"
        logger.info(f"Model registered with ID: {model_id}")

        # 6. Test VisionAdapter integration
        adapter = VisionAdapter()

        # Mock model loading to avoid actual ResNet50 instantiation
        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            adapter.load_from_registry(model_id)
            assert adapter.is_loaded, "VisionAdapter failed to load from registry"
            assert len(adapter.class_names) == 4, "Incorrect number of classes loaded"

        # 7. Test model manager integration
        config_path = temp_workspace / "config" / "models.json"
        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # Sync with registry
        with patch.object(manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_adapter.predict.return_value = ("healthy_plant", 0.95)
            mock_load.return_value = mock_adapter

            success = manager.sync_with_registry()
            assert success, "Model manager sync with registry failed"

        # 8. Test model switching
        models = manager.list_available_models()
        registry_models = [m for m in models if "registry" in m.get("model_id", "")]
        assert len(registry_models) > 0, "No registry models found in manager"

        # 9. Test prediction workflow
        test_image = Image.new("RGB", (224, 224), color="green")

        with patch.object(manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_adapter.predict.return_value = ("healthy_plant", 0.95)
            mock_load.return_value = mock_adapter

            registry_model_id = registry_models[0]["id"]
            success = manager.load_model(registry_model_id)
            assert success, "Failed to load registry model in manager"

            predicted_class, confidence, metadata = manager.predict(test_image)
            assert predicted_class == "healthy_plant"
            assert confidence == 0.95
            assert "model_name" in metadata

        logger.info("✅ Complete training to deployment workflow test passed")

    def test_model_registry_vision_adapter_integration(self, temp_workspace):
        """Test deep integration between ModelRegistry and VisionAdapter."""
        logger.info("Testing ModelRegistry-VisionAdapter integration...")

        registry = ModelRegistry(temp_workspace / "models")

        # Create test model checkpoint with registry format
        model_path = temp_workspace / "test_model.pt"
        checkpoint = {
            "model_state_dict": {
                "conv1.weight": torch.randn(64, 3, 7, 7),
                "bn1.weight": torch.randn(64),
                "bn1.bias": torch.randn(64),
                "fc.weight": torch.randn(4, 2048),
                "fc.bias": torch.randn(4),
            },
            "num_classes": 4,
            "class_names": ["class_0", "class_1", "class_2", "class_3"],
            "model_version": "1.0.0",
            "training_metadata": {"training_date": "2024-08-17", "dataset": "integration_test", "accuracy": 0.92, "architecture": "resnet50"},
        }
        torch.save(checkpoint, model_path)

        # Register model
        model_id = registry.register_model(
            model_path=model_path,
            name="vision_integration_test",
            architecture="resnet50",
            dataset_version="test_v1.0",
            hyperparameters={"num_classes": 4, "pretrained": True},
            performance_metrics={"accuracy": 0.92, "f1_score": 0.90},
            description="Model for VisionAdapter integration testing",
            tags=["integration", "vision", "test"],
        )

        # Test VisionAdapter compatibility detection
        adapter = VisionAdapter()

        model_info = registry.get_model(model_id)
        is_compatible = adapter.is_compatible_with_registry_format(str(model_info.model_path))
        assert is_compatible, "Model should be compatible with registry format"

        # Test loading from registry
        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            adapter.load_from_registry(model_id)
            assert adapter.is_loaded
            assert adapter.current_model_id == model_id
            assert len(adapter.class_names) == 4

        # Test model metadata access
        metadata = adapter.get_model_metadata()
        assert metadata is not None
        assert metadata["model_id"] == model_id
        assert metadata["architecture"] == "resnet50"
        assert metadata["accuracy"] == 0.92

        # Test model switching between registry models
        # Register second model
        model_path_2 = temp_workspace / "test_model_2.pt"
        checkpoint_2 = checkpoint.copy()
        checkpoint_2["training_metadata"]["accuracy"] = 0.95
        torch.save(checkpoint_2, model_path_2)

        model_id_2 = registry.register_model(
            model_path=model_path_2,
            name="vision_integration_test_2",
            architecture="resnet50",
            dataset_version="test_v1.0",
            hyperparameters={"num_classes": 4, "pretrained": True},
            performance_metrics={"accuracy": 0.95, "f1_score": 0.93},
            description="Second model for integration testing",
        )

        # Switch models
        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model_2 = MagicMock()
            mock_create_model.return_value = mock_model_2

            adapter.load_from_registry(model_id_2)
            assert adapter.current_model_id == model_id_2

            # Verify metadata updated
            metadata_2 = adapter.get_model_metadata()
            assert metadata_2["accuracy"] == 0.95

        logger.info("✅ ModelRegistry-VisionAdapter integration test passed")

    def test_model_switching_with_registry_models(self, temp_workspace):
        """Test comprehensive model switching functionality with registry models."""
        logger.info("Testing model switching with registry models...")

        registry = ModelRegistry(temp_workspace / "models")

        # Create multiple test models
        model_configs = [
            {"name": "fast_model", "accuracy": 0.88, "description": "Fast inference model", "tags": ["fast", "production"]},
            {"name": "accurate_model", "accuracy": 0.95, "description": "High accuracy model", "tags": ["accurate", "research"]},
            {"name": "balanced_model", "accuracy": 0.92, "description": "Balanced speed/accuracy model", "tags": ["balanced", "production"]},
        ]

        model_ids = []
        for config in model_configs:
            # Create model checkpoint
            model_path = temp_workspace / f"{config['name']}.pt"
            checkpoint = {
                "model_state_dict": {
                    "fc.weight": torch.randn(4, 2048),
                    "fc.bias": torch.randn(4),
                },
                "num_classes": 4,
                "class_names": ["class_0", "class_1", "class_2", "class_3"],
                "model_version": "1.0.0",
                "training_metadata": {"accuracy": config["accuracy"], "architecture": "resnet50"},
            }
            torch.save(checkpoint, model_path)

            # Register model
            model_id = registry.register_model(
                model_path=model_path,
                name=config["name"],
                architecture="resnet50",
                dataset_version="test_v1.0",
                hyperparameters={"num_classes": 4},
                performance_metrics={"accuracy": config["accuracy"]},
                description=config["description"],
                tags=config["tags"],
            )
            model_ids.append(model_id)

        # Create model manager configuration
        config_path = temp_workspace / "config" / "switching_test_models.json"
        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # Sync with registry
        with patch.object(manager, "_load_local_model") as mock_load:

            def mock_load_func(model_config):
                mock_adapter = MagicMock()
                # Return different predictions based on model
                if "fast" in model_config.get("model_id", ""):
                    mock_adapter.predict.return_value = ("class_0", 0.88)
                elif "accurate" in model_config.get("model_id", ""):
                    mock_adapter.predict.return_value = ("class_1", 0.95)
                else:
                    mock_adapter.predict.return_value = ("class_2", 0.92)
                return mock_adapter

            mock_load.side_effect = mock_load_func

            success = manager.sync_with_registry()
            assert success, "Registry sync failed"

        # Test model listing and filtering
        all_models = manager.list_available_models()
        registry_models = [m for m in all_models if "registry" in m.get("model_id", "")]
        assert len(registry_models) == 3, f"Expected 3 registry models, got {len(registry_models)}"

        # Test filtering by tags
        production_models = manager.filter_models_by_tags(["production"])
        assert len(production_models) >= 2, "Should find production models"

        # Test model switching and prediction consistency
        test_image = Image.new("RGB", (224, 224), color="blue")

        for i, model_id in enumerate(model_ids):
            registry_model_key = f"registry_{model_id}"
            available_ids = [m["id"] for m in registry_models]

            if registry_model_key in available_ids:
                with patch.object(manager, "_load_local_model") as mock_load:
                    mock_adapter = MagicMock()
                    expected_class = f"class_{i}"
                    expected_conf = model_configs[i]["accuracy"]
                    mock_adapter.predict.return_value = (expected_class, expected_conf)
                    mock_load.return_value = mock_adapter

                    success = manager.load_model(registry_model_key)
                    assert success, f"Failed to load model {registry_model_key}"

                    predicted_class, confidence, metadata = manager.predict(test_image)
                    assert predicted_class == expected_class
                    assert confidence == expected_conf
                    assert metadata["model_name"] == model_configs[i]["name"]

        # Test model comparison
        comparison = registry.compare_models(model_ids)
        assert len(comparison.models) == 3

        best_accuracy_model = comparison.get_best_model("accuracy")
        assert best_accuracy_model.metadata.performance_metrics["accuracy"] == 0.95

        logger.info("✅ Model switching with registry models test passed")

    def test_end_to_end_ui_deployment_integration(self, temp_workspace):
        """Test end-to-end integration from training to UI deployment."""
        logger.info("Testing end-to-end UI deployment integration...")

        # 1. Create and register a model (simulating training completion)
        registry = ModelRegistry(temp_workspace / "models")

        model_path = temp_workspace / "ui_test_model.pt"
        checkpoint = {
            "model_state_dict": {
                "fc.weight": torch.randn(4, 2048),
                "fc.bias": torch.randn(4),
            },
            "num_classes": 4,
            "class_names": ["Healthy", "Disease_A", "Disease_B", "Disease_C"],
            "model_version": "1.0.0",
            "training_metadata": {"accuracy": 0.94, "training_date": "2024-08-17", "dataset": "plantvillage_subset"},
        }
        torch.save(checkpoint, model_path)

        model_id = registry.register_model(
            model_path=model_path,
            name="ui_deployment_model",
            architecture="resnet50",
            dataset_version="plantvillage_v1.0",
            hyperparameters={"num_classes": 4, "epochs": 50},
            performance_metrics={"accuracy": 0.94, "f1_score": 0.92},
            description="Model for UI deployment testing",
            tags=["ui", "deployment", "production"],
        )

        # 2. Test model manager integration for UI
        config_path = temp_workspace / "config" / "ui_models.json"
        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # Sync with registry (simulating user running sync command)
        with patch.object(manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_adapter.predict.return_value = ("Healthy", 0.94)
            mock_adapter.get_class_names.return_value = ["Healthy", "Disease_A", "Disease_B", "Disease_C"]
            mock_load.return_value = mock_adapter

            success = manager.sync_with_registry()
            assert success, "UI model sync failed"

        # 3. Test UI model selection and loading
        ui_models = manager.list_available_models()
        ui_registry_models = [m for m in ui_models if "registry" in m.get("model_id", "")]
        assert len(ui_registry_models) > 0, "No registry models available for UI"

        # Select model for UI
        selected_model = ui_registry_models[0]

        with patch.object(manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_adapter.predict.return_value = ("Healthy", 0.94)
            mock_adapter.get_class_names.return_value = ["Healthy", "Disease_A", "Disease_B", "Disease_C"]
            mock_load.return_value = mock_adapter

            success = manager.load_model(selected_model["id"])
            assert success, "Failed to load model for UI"

        # 4. Test UI prediction workflow
        test_images = [
            Image.new("RGB", (224, 224), color="green"),  # Healthy
            Image.new("RGB", (224, 224), color="brown"),  # Disease_A
            Image.new("RGB", (224, 224), color="yellow"),  # Disease_B
            Image.new("RGB", (224, 224), color="red"),  # Disease_C
        ]

        predictions = []
        for i, img in enumerate(test_images):
            with patch.object(manager, "_load_local_model") as mock_load:
                mock_adapter = MagicMock()
                expected_classes = ["Healthy", "Disease_A", "Disease_B", "Disease_C"]
                mock_adapter.predict.return_value = (expected_classes[i], 0.90 + i * 0.01)
                mock_load.return_value = mock_adapter

                predicted_class, confidence, metadata = manager.predict(img)
                predictions.append({"class": predicted_class, "confidence": confidence, "metadata": metadata})

        # Verify predictions
        assert len(predictions) == 4
        for i, pred in enumerate(predictions):
            expected_classes = ["Healthy", "Disease_A", "Disease_B", "Disease_C"]
            assert pred["class"] == expected_classes[i]
            assert pred["confidence"] > 0.90
            assert "model_name" in pred["metadata"]

        # 5. Test model switching in UI context
        # Register second model
        model_path_2 = temp_workspace / "ui_test_model_2.pt"
        checkpoint_2 = checkpoint.copy()
        checkpoint_2["training_metadata"]["accuracy"] = 0.96
        torch.save(checkpoint_2, model_path_2)

        model_id_2 = registry.register_model(
            model_path=model_path_2,
            name="ui_deployment_model_v2",
            architecture="resnet50",
            dataset_version="plantvillage_v1.1",
            hyperparameters={"num_classes": 4, "epochs": 75},
            performance_metrics={"accuracy": 0.96, "f1_score": 0.94},
            description="Improved model for UI deployment",
            tags=["ui", "deployment", "production", "v2"],
        )

        # Re-sync to get new model
        with patch.object(manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_adapter.predict.return_value = ("Healthy", 0.96)
            mock_load.return_value = mock_adapter

            success = manager.sync_with_registry()
            assert success, "Re-sync failed"

        # Test switching to new model
        updated_models = manager.list_available_models()
        v2_models = [m for m in updated_models if "v2" in m.get("name", "")]

        if v2_models:
            with patch.object(manager, "_load_local_model") as mock_load:
                mock_adapter = MagicMock()
                mock_adapter.predict.return_value = ("Healthy", 0.96)
                mock_load.return_value = mock_adapter

                success = manager.load_model(v2_models[0]["id"])
                assert success, "Failed to switch to v2 model"

                # Test prediction with new model
                predicted_class, confidence, metadata = manager.predict(test_images[0])
                assert confidence == 0.96, "New model should have higher confidence"

        logger.info("✅ End-to-end UI deployment integration test passed")

    def test_performance_regression_detection(self, temp_workspace):
        """Test performance regression detection in training pipeline."""
        logger.info("Testing performance regression detection...")

        registry = ModelRegistry(temp_workspace / "models")

        # Create baseline model
        baseline_path = temp_workspace / "baseline_model.pt"
        baseline_checkpoint = {
            "model_state_dict": {"fc.weight": torch.randn(4, 2048), "fc.bias": torch.randn(4)},
            "num_classes": 4,
            "class_names": ["class_0", "class_1", "class_2", "class_3"],
            "model_version": "1.0.0",
            "training_metadata": {"accuracy": 0.95, "f1_score": 0.93, "training_time": 120.5, "inference_time": 0.05},
        }
        torch.save(baseline_checkpoint, baseline_path)

        baseline_id = registry.register_model(
            model_path=baseline_path,
            name="baseline_model",
            architecture="resnet50",
            dataset_version="test_v1.0",
            hyperparameters={"num_classes": 4},
            performance_metrics={"accuracy": 0.95, "f1_score": 0.93, "training_time": 120.5, "inference_time": 0.05},
            description="Baseline model for regression testing",
            tags=["baseline", "regression"],
        )

        # Create new model with potential regression
        new_path = temp_workspace / "new_model.pt"
        new_checkpoint = baseline_checkpoint.copy()
        new_checkpoint["training_metadata"]["accuracy"] = 0.88  # Regression in accuracy
        new_checkpoint["training_metadata"]["training_time"] = 180.0  # Regression in training time
        torch.save(new_checkpoint, new_path)

        new_id = registry.register_model(
            model_path=new_path,
            name="new_model",
            architecture="resnet50",
            dataset_version="test_v1.0",
            hyperparameters={"num_classes": 4},
            performance_metrics={"accuracy": 0.88, "f1_score": 0.86, "training_time": 180.0, "inference_time": 0.05},
            description="New model for regression testing",
            tags=["new", "regression"],
        )

        # Test regression detection
        comparison = registry.compare_models([baseline_id, new_id])

        # Check for performance regression
        baseline_model = comparison.get_model_by_id(baseline_id)
        new_model = comparison.get_model_by_id(new_id)

        accuracy_regression = baseline_model.metadata.performance_metrics["accuracy"] - new_model.metadata.performance_metrics["accuracy"]

        training_time_regression = new_model.metadata.performance_metrics["training_time"] - baseline_model.metadata.performance_metrics["training_time"]

        # Assert regressions are detected
        assert accuracy_regression > 0.05, "Accuracy regression should be detected"
        assert training_time_regression > 30, "Training time regression should be detected"

        # Test regression reporting
        regression_report = comparison.get_regression_report(baseline_id)
        assert regression_report is not None
        assert "accuracy" in regression_report["regressions"]
        assert "training_time" in regression_report["regressions"]

        logger.info("✅ Performance regression detection test passed")

    def test_cross_platform_compatibility(self, temp_workspace):
        """Test cross-platform compatibility of training pipeline."""
        logger.info("Testing cross-platform compatibility...")

        # Test path handling across platforms
        dataset_path = temp_workspace / "data" / "cross_platform_test"
        dataset_path.mkdir(parents=True, exist_ok=True)

        # Create test dataset with various path scenarios
        for split in ["train", "val"]:
            split_dir = dataset_path / split / "test_class"
            split_dir.mkdir(parents=True, exist_ok=True)

            # Create test image
            img = Image.new("RGB", (224, 224), color="blue")
            img.save(split_dir / "test_image.jpg")

        # Test dataset manager with cross-platform paths
        dataset_manager = DatasetManager()
        validation_result = dataset_manager.validate_dataset(dataset_path)
        assert validation_result.is_valid, "Cross-platform dataset validation failed"

        # Test model registry with cross-platform paths
        registry = ModelRegistry(temp_workspace / "models")

        model_path = temp_workspace / "cross_platform_model.pt"
        checkpoint = {"model_state_dict": {"fc.weight": torch.randn(1, 2048), "fc.bias": torch.randn(1)}, "num_classes": 1, "class_names": ["test_class"], "model_version": "1.0.0"}
        torch.save(checkpoint, model_path)

        model_id = registry.register_model(
            model_path=model_path,
            name="cross_platform_test",
            architecture="resnet50",
            dataset_version="test_v1.0",
            hyperparameters={"num_classes": 1},
            performance_metrics={"accuracy": 0.90},
            description="Cross-platform compatibility test model",
        )

        # Verify model can be retrieved and paths work correctly
        model_info = registry.get_model(model_id)
        assert model_info is not None
        assert model_info.model_path.exists()

        # Test VisionAdapter cross-platform compatibility
        adapter = VisionAdapter()
        is_compatible = adapter.is_compatible_with_registry_format(str(model_info.model_path))
        assert is_compatible, "Cross-platform model compatibility check failed"

        logger.info("✅ Cross-platform compatibility test passed")

    def test_concurrent_training_integration(self, temp_workspace):
        """Test integration with concurrent training scenarios."""
        logger.info("Testing concurrent training integration...")

        import queue
        import threading

        registry = ModelRegistry(temp_workspace / "models")
        results_queue = queue.Queue()

        def concurrent_training_worker(worker_id: int):
            """Simulate concurrent training worker."""
            try:
                # Create worker-specific model
                model_path = temp_workspace / f"concurrent_model_{worker_id}.pt"
                checkpoint = {
                    "model_state_dict": {"fc.weight": torch.randn(2, 2048), "fc.bias": torch.randn(2)},
                    "num_classes": 2,
                    "class_names": ["class_0", "class_1"],
                    "model_version": "1.0.0",
                    "training_metadata": {"worker_id": worker_id, "accuracy": 0.85 + worker_id * 0.02},
                }
                torch.save(checkpoint, model_path)

                # Register model (test concurrent registry access)
                model_id = registry.register_model(
                    model_path=model_path,
                    name=f"concurrent_model_{worker_id}",
                    architecture="resnet50",
                    dataset_version="test_v1.0",
                    hyperparameters={"num_classes": 2, "worker_id": worker_id},
                    performance_metrics={"accuracy": 0.85 + worker_id * 0.02},
                    description=f"Model from concurrent worker {worker_id}",
                    tags=["concurrent", f"worker_{worker_id}"],
                )

                results_queue.put({"worker_id": worker_id, "model_id": model_id, "success": True})

            except Exception as e:
                results_queue.put({"worker_id": worker_id, "error": str(e), "success": False})

        # Start concurrent workers
        num_workers = 3
        threads = []

        for i in range(num_workers):
            thread = threading.Thread(target=concurrent_training_worker, args=(i,))
            thread.start()
            threads.append(thread)

        # Wait for completion
        for thread in threads:
            thread.join()

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Verify all workers completed successfully
        assert len(results) == num_workers
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) == num_workers, "Some concurrent workers failed"

        # Verify all models were registered
        all_models = registry.list_models()
        concurrent_models = [m for m in all_models if "concurrent" in m.metadata.tags]
        assert len(concurrent_models) == num_workers, "Not all concurrent models were registered"

        # Test concurrent model access
        for result in successful_results:
            model_info = registry.get_model(result["model_id"])
            assert model_info is not None
            assert model_info.is_valid

        logger.info("✅ Concurrent training integration test passed")

    def test_memory_and_resource_management(self, temp_workspace):
        """Test memory and resource management in integration scenarios."""
        logger.info("Testing memory and resource management...")

        import gc

        import psutil

        # Get baseline memory usage
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Test memory usage during component initialization
        registry = ModelRegistry(temp_workspace / "models")
        dataset_manager = DatasetManager()

        init_memory = process.memory_info().rss / 1024 / 1024
        init_increase = init_memory - baseline_memory

        # Should not use excessive memory for initialization
        assert init_increase < 100, f"Initialization memory usage too high: {init_increase:.1f}MB"

        # Test memory usage during model operations
        model_path = temp_workspace / "memory_test_model.pt"
        checkpoint = {
            "model_state_dict": {"fc.weight": torch.randn(10, 2048), "fc.bias": torch.randn(10)},
            "num_classes": 10,
            "class_names": [f"class_{i}" for i in range(10)],
            "model_version": "1.0.0",
        }
        torch.save(checkpoint, model_path)

        # Register multiple models to test memory scaling
        model_ids = []
        for i in range(5):
            model_id = registry.register_model(
                model_path=model_path,
                name=f"memory_test_model_{i}",
                architecture="resnet50",
                dataset_version="test_v1.0",
                hyperparameters={"num_classes": 10},
                performance_metrics={"accuracy": 0.90 + i * 0.01},
                description=f"Memory test model {i}",
            )
            model_ids.append(model_id)

        registry_memory = process.memory_info().rss / 1024 / 1024
        registry_increase = registry_memory - init_memory

        # Memory should scale reasonably with number of models
        assert registry_increase < 50, f"Registry memory usage too high: {registry_increase:.1f}MB"

        # Test VisionAdapter memory usage
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            # Load and switch between models
            for model_id in model_ids[:3]:  # Test first 3 models
                adapter.load_from_registry(model_id)

                adapter_memory = process.memory_info().rss / 1024 / 1024
                adapter_increase = adapter_memory - registry_memory

                # Should not accumulate memory with each model switch
                assert adapter_increase < 100, f"VisionAdapter memory usage too high: {adapter_increase:.1f}MB"

        # Test memory cleanup
        del adapter
        del registry
        del dataset_manager
        gc.collect()

        cleanup_memory = process.memory_info().rss / 1024 / 1024
        memory_recovered = registry_memory - cleanup_memory

        # Should recover some memory after cleanup
        assert memory_recovered > 0, "No memory recovered after cleanup"

        logger.info(f"Memory usage - Baseline: {baseline_memory:.1f}MB, Peak: {registry_memory:.1f}MB, Recovered: {memory_recovered:.1f}MB")
        logger.info("✅ Memory and resource management test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
