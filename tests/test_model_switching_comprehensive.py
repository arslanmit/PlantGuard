"""Comprehensive tests for model switching with registry models.

This module provides extensive testing for model switching functionality,
including integration with the model registry and UI components.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch
from PIL import Image

from src.features.model_switching.model_manager import PlantGuardModelManager
from src.training.model_registry import ModelRegistry


class TestModelSwitchingComprehensive:
    """Comprehensive tests for model switching functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "models").mkdir()
            (workspace / "config").mkdir()
            yield workspace

    @pytest.fixture
    def registry_with_models(self, temp_workspace):
        """Create registry with multiple test models."""
        registry = ModelRegistry(temp_workspace / "models")

        # Model configurations for testing
        model_configs = [
            {
                "name": "plantguard_base",
                "accuracy": 0.88,
                "f1_score": 0.86,
                "inference_time": 0.05,
                "model_size": 25.2,
                "description": "Base PlantGuard model",
                "tags": ["base", "production", "fast"],
            },
            {
                "name": "plantguard_accurate",
                "accuracy": 0.95,
                "f1_score": 0.94,
                "inference_time": 0.12,
                "model_size": 87.5,
                "description": "High accuracy PlantGuard model",
                "tags": ["accurate", "research", "slow"],
            },
            {
                "name": "plantguard_balanced",
                "accuracy": 0.92,
                "f1_score": 0.91,
                "inference_time": 0.08,
                "model_size": 45.8,
                "description": "Balanced PlantGuard model",
                "tags": ["balanced", "production", "medium"],
            },
            {
                "name": "plantguard_mobile",
                "accuracy": 0.85,
                "f1_score": 0.83,
                "inference_time": 0.02,
                "model_size": 12.1,
                "description": "Mobile-optimized PlantGuard model",
                "tags": ["mobile", "edge", "fast", "small"],
            },
        ]

        model_ids = []
        for i, config in enumerate(model_configs):
            # Create model checkpoint
            model_path = temp_workspace / f"{config['name']}.pt"
            checkpoint = {
                "model_state_dict": {
                    "conv1.weight": torch.randn(64, 3, 7, 7),
                    "bn1.weight": torch.randn(64),
                    "bn1.bias": torch.randn(64),
                    "fc.weight": torch.randn(38, 2048),
                    "fc.bias": torch.randn(38),
                },
                "num_classes": 38,
                "class_names": [f"plant_class_{j}" for j in range(38)],
                "model_version": f"1.{i}.0",
                "training_metadata": {
                    "training_date": f"2024-08-{17 + i:02d}",
                    "dataset": "plantvillage_v1.0",
                    "accuracy": config["accuracy"],
                    "f1_score": config["f1_score"],
                    "architecture": "resnet50",
                    "epochs": 50 + i * 10,
                },
            }
            torch.save(checkpoint, model_path)

            # Register model
            model_id = registry.register_model(
                model_path=model_path,
                name=config["name"],
                architecture="resnet50",
                dataset_version="plantvillage_v1.0",
                hyperparameters={"num_classes": 38, "epochs": 50 + i * 10, "batch_size": 32, "learning_rate": 0.001},
                performance_metrics={
                    "accuracy": config["accuracy"],
                    "f1_score": config["f1_score"],
                    "inference_time": config["inference_time"],
                    "model_size_mb": config["model_size"],
                },
                description=config["description"],
                tags=config["tags"],
            )
            model_ids.append(model_id)

        return registry, model_ids, model_configs

    @pytest.fixture
    def model_manager(self, temp_workspace):
        """Create PlantGuardModelManager instance."""
        config_path = temp_workspace / "config" / "models.json"
        return PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

    def test_registry_sync_and_model_discovery(self, registry_with_models, model_manager):
        """Test syncing with registry and discovering models."""
        registry, model_ids, model_configs = registry_with_models

        # Initially no models in manager
        models = model_manager.list_available_models()
        assert len(models) == 0

        # Sync with registry
        with patch.object(model_manager, "_load_local_model") as mock_load:

            def mock_load_func(model_config):
                mock_adapter = MagicMock()
                # Return predictions based on model accuracy
                accuracy = float(model_config.get("accuracy", 0.9))
                mock_adapter.predict.return_value = ("plant_class_0", accuracy)
                mock_adapter.get_class_names.return_value = [f"plant_class_{i}" for i in range(38)]
                return mock_adapter

            mock_load.side_effect = mock_load_func

            success = model_manager.sync_with_registry()
            assert success, "Registry sync should succeed"

        # Should now have registry models
        models = model_manager.list_available_models()
        registry_models = [m for m in models if "registry" in m.get("model_id", "")]
        assert len(registry_models) == 4, f"Expected 4 registry models, got {len(registry_models)}"

        # Verify model properties
        for model in registry_models:
            assert "name" in model
            assert "accuracy" in model
            assert "model_id" in model
            assert model["type"] == "local"
            assert model["enabled"] is True

    def test_model_filtering_and_selection(self, registry_with_models, model_manager):
        """Test model filtering and selection capabilities."""
        registry, model_ids, model_configs = registry_with_models

        # Sync with registry first
        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_load.return_value = mock_adapter
            model_manager.sync_with_registry()

        # Test filtering by accuracy
        high_accuracy_models = model_manager.filter_models_by_accuracy(min_accuracy=0.90)
        assert len(high_accuracy_models) >= 2  # accurate and balanced models

        # Test filtering by tags
        production_models = model_manager.filter_models_by_tags(["production"])
        assert len(production_models) >= 2  # base and balanced models

        fast_models = model_manager.filter_models_by_tags(["fast"])
        assert len(fast_models) >= 2  # base and mobile models

        # Test filtering by performance criteria
        fast_inference_models = model_manager.filter_models_by_performance(max_inference_time=0.06)
        assert len(fast_inference_models) >= 2  # base and mobile models

        # Test combined filtering
        production_fast_models = model_manager.filter_models_by_tags(["production", "fast"])
        assert len(production_fast_models) >= 1  # base model

    def test_model_switching_workflow(self, registry_with_models, model_manager):
        """Test complete model switching workflow."""
        registry, model_ids, model_configs = registry_with_models

        # Sync with registry
        with patch.object(model_manager, "_load_local_model") as mock_load:

            def mock_load_func(model_config):
                mock_adapter = MagicMock()
                # Different predictions based on model name
                model_name = model_config.get("name", "unknown")
                if "base" in model_name:
                    mock_adapter.predict.return_value = ("plant_class_base", 0.88)
                elif "accurate" in model_name:
                    mock_adapter.predict.return_value = ("plant_class_accurate", 0.95)
                elif "balanced" in model_name:
                    mock_adapter.predict.return_value = ("plant_class_balanced", 0.92)
                elif "mobile" in model_name:
                    mock_adapter.predict.return_value = ("plant_class_mobile", 0.85)
                else:
                    mock_adapter.predict.return_value = ("plant_class_unknown", 0.80)
                return mock_adapter

            mock_load.side_effect = mock_load_func
            model_manager.sync_with_registry()

        models = model_manager.list_available_models()
        registry_models = [m for m in models if "registry" in m.get("model_id", "")]

        # Test switching between models
        test_image = Image.new("RGB", (224, 224), color="green")

        for model in registry_models:
            model_id = model["id"]
            expected_name = model["name"]

            with patch.object(model_manager, "_load_local_model") as mock_load:
                mock_adapter = MagicMock()
                if "base" in expected_name:
                    mock_adapter.predict.return_value = ("plant_class_base", 0.88)
                elif "accurate" in expected_name:
                    mock_adapter.predict.return_value = ("plant_class_accurate", 0.95)
                elif "balanced" in expected_name:
                    mock_adapter.predict.return_value = ("plant_class_balanced", 0.92)
                elif "mobile" in expected_name:
                    mock_adapter.predict.return_value = ("plant_class_mobile", 0.85)
                mock_load.return_value = mock_adapter

                # Load model
                success = model_manager.load_model(model_id)
                assert success, f"Failed to load model {model_id}"

                # Test prediction
                predicted_class, confidence, metadata = model_manager.predict(test_image)

                # Verify prediction matches expected model behavior
                if "base" in expected_name:
                    assert predicted_class == "plant_class_base"
                    assert confidence == 0.88
                elif "accurate" in expected_name:
                    assert predicted_class == "plant_class_accurate"
                    assert confidence == 0.95
                elif "balanced" in expected_name:
                    assert predicted_class == "plant_class_balanced"
                    assert confidence == 0.92
                elif "mobile" in expected_name:
                    assert predicted_class == "plant_class_mobile"
                    assert confidence == 0.85

                assert metadata["model_name"] == expected_name

    def test_model_comparison_and_benchmarking(self, registry_with_models, model_manager):
        """Test model comparison and benchmarking features."""
        registry, model_ids, model_configs = registry_with_models

        # Test registry-level comparison
        comparison = registry.compare_models(model_ids)
        assert len(comparison.models) == 4

        # Test best model selection by different metrics
        best_accuracy = comparison.get_best_model("accuracy")
        assert best_accuracy.metadata.performance_metrics["accuracy"] == 0.95

        best_speed = comparison.get_best_model("inference_time", ascending=True)
        assert best_speed.metadata.performance_metrics["inference_time"] == 0.02

        # Test model manager comparison
        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_load.return_value = mock_adapter
            model_manager.sync_with_registry()

        models = model_manager.list_available_models()
        registry_models = [m for m in models if "registry" in m.get("model_id", "")]

        # Test performance comparison
        comparison_result = model_manager.compare_models([m["id"] for m in registry_models[:3]])
        assert comparison_result is not None
        assert len(comparison_result["models"]) == 3

        # Test recommendation system
        recommendation = model_manager.recommend_model(criteria={"min_accuracy": 0.90, "max_inference_time": 0.10})
        assert recommendation is not None
        assert recommendation["accuracy"] >= 0.90
        assert recommendation["inference_time"] <= 0.10

    def test_model_switching_performance_impact(self, registry_with_models, model_manager):
        """Test performance impact of model switching."""
        registry, model_ids, model_configs = registry_with_models

        import time

        # Sync with registry
        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_load.return_value = mock_adapter
            model_manager.sync_with_registry()

        models = model_manager.list_available_models()
        registry_models = [m for m in models if "registry" in m.get("model_id", "")]

        # Measure model switching time
        switching_times = []

        for model in registry_models[:3]:  # Test first 3 models
            with patch.object(model_manager, "_load_local_model") as mock_load:
                mock_adapter = MagicMock()
                mock_load.return_value = mock_adapter

                start_time = time.time()
                success = model_manager.load_model(model["id"])
                switch_time = time.time() - start_time

                assert success
                switching_times.append(switch_time)

        # Model switching should be reasonably fast
        avg_switch_time = sum(switching_times) / len(switching_times)
        assert avg_switch_time < 1.0, f"Model switching too slow: {avg_switch_time:.3f}s"

        # Test prediction performance after switching
        test_image = Image.new("RGB", (224, 224), color="blue")
        prediction_times = []

        for model in registry_models[:3]:
            with patch.object(model_manager, "_load_local_model") as mock_load:
                mock_adapter = MagicMock()
                mock_adapter.predict.return_value = ("test_class", 0.90)
                mock_load.return_value = mock_adapter

                model_manager.load_model(model["id"])

                start_time = time.time()
                predicted_class, confidence, metadata = model_manager.predict(test_image)
                prediction_time = time.time() - start_time

                prediction_times.append(prediction_time)

        # Predictions should be fast
        avg_prediction_time = sum(prediction_times) / len(prediction_times)
        assert avg_prediction_time < 0.5, f"Predictions too slow: {avg_prediction_time:.3f}s"

    def test_model_configuration_persistence(self, registry_with_models, model_manager, temp_workspace):
        """Test model configuration persistence across sessions."""
        registry, model_ids, model_configs = registry_with_models

        # Sync with registry and configure models
        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_load.return_value = mock_adapter
            model_manager.sync_with_registry()

        models = model_manager.list_available_models()
        registry_models = [m for m in models if "registry" in m.get("model_id", "")]

        # Modify model configurations
        for model in registry_models[:2]:
            model_manager.update_model_config(
                model["id"],
                {"confidence_threshold": 0.8, "enabled": True, "custom_setting": f"test_value_{model['id']}"},
            )

        # Save configuration
        model_manager.save_config()

        # Create new manager instance (simulate restart)
        config_path = temp_workspace / "config" / "models.json"
        new_manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # Verify configuration persisted
        new_models = new_manager.list_available_models()
        persisted_models = [m for m in new_models if "registry" in m.get("model_id", "")]

        assert len(persisted_models) >= 2

        for model in persisted_models[:2]:
            config = new_manager.get_model_config(model["id"])
            assert config["confidence_threshold"] == 0.8
            assert config["enabled"] is True
            assert config["custom_setting"] == f"test_value_{model['id']}"

    def test_model_switching_error_handling(self, registry_with_models, model_manager):
        """Test error handling in model switching scenarios."""
        registry, model_ids, model_configs = registry_with_models

        # Test switching to non-existent model
        success = model_manager.load_model("non_existent_model")
        assert not success

        # Test switching with corrupted model
        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_load.side_effect = RuntimeError("Model loading failed")

            success = model_manager.load_model("registry_" + model_ids[0])
            assert not success

        # Test recovery after error
        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_adapter.predict.return_value = ("recovery_class", 0.90)
            mock_load.return_value = mock_adapter

            model_manager.sync_with_registry()
            models = model_manager.list_available_models()
            registry_models = [m for m in models if "registry" in m.get("model_id", "")]

            if registry_models:
                success = model_manager.load_model(registry_models[0]["id"])
                assert success, "Should recover and load valid model"

    def test_ui_integration_scenarios(self, registry_with_models, model_manager):
        """Test model switching scenarios specific to UI integration."""
        registry, model_ids, model_configs = registry_with_models

        # Sync with registry
        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_load.return_value = mock_adapter
            model_manager.sync_with_registry()

        # Test getting models for UI dropdown
        ui_models = model_manager.get_models_for_ui()
        assert len(ui_models) >= 4

        for model in ui_models:
            assert "display_name" in model
            assert "description" in model
            assert "accuracy" in model
            assert "tags" in model

        # Test model switching from UI perspective
        test_image = Image.new("RGB", (224, 224), color="purple")

        # Simulate UI model selection
        selected_model = ui_models[0]

        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_adapter.predict.return_value = ("ui_test_class", 0.92)
            mock_load.return_value = mock_adapter

            success = model_manager.switch_model_for_ui(selected_model["id"])
            assert success

            # Test prediction from UI
            result = model_manager.predict_for_ui(test_image)
            assert result["predicted_class"] == "ui_test_class"
            assert result["confidence"] == 0.92
            assert "model_info" in result
            assert result["model_info"]["name"] == selected_model["display_name"]

    def test_batch_model_operations(self, registry_with_models, model_manager):
        """Test batch operations on multiple models."""
        registry, model_ids, model_configs = registry_with_models

        # Sync with registry
        with patch.object(model_manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_load.return_value = mock_adapter
            model_manager.sync_with_registry()

        models = model_manager.list_available_models()
        registry_models = [m for m in models if "registry" in m.get("model_id", "")]

        # Test batch model validation
        model_ids_to_validate = [m["id"] for m in registry_models[:3]]
        validation_results = model_manager.validate_models_batch(model_ids_to_validate)

        assert len(validation_results) == 3
        for result in validation_results:
            assert "model_id" in result
            assert "is_valid" in result
            assert "validation_details" in result

        # Test batch model update
        update_config = {"confidence_threshold": 0.75, "enabled": True, "batch_updated": True}

        success = model_manager.update_models_batch(model_ids_to_validate, update_config)
        assert success

        # Verify batch update
        for model_id in model_ids_to_validate:
            config = model_manager.get_model_config(model_id)
            assert config["confidence_threshold"] == 0.75
            assert config["batch_updated"] is True

    def test_model_switching_with_different_architectures(self, temp_workspace, model_manager):
        """Test model switching between different architectures."""
        registry = ModelRegistry(temp_workspace / "models")

        # Create models with different architectures
        architectures = ["resnet50", "efficientnet", "vit"]
        model_ids = []

        for i, arch in enumerate(architectures):
            model_path = temp_workspace / f"{arch}_model.pt"

            # Different model structures for different architectures
            if arch == "resnet50":
                state_dict = {
                    "conv1.weight": torch.randn(64, 3, 7, 7),
                    "fc.weight": torch.randn(38, 2048),
                    "fc.bias": torch.randn(38),
                }
            elif arch == "efficientnet":
                state_dict = {
                    "features.0.0.weight": torch.randn(32, 3, 3, 3),
                    "classifier.1.weight": torch.randn(38, 1280),
                    "classifier.1.bias": torch.randn(38),
                }
            else:  # vit
                state_dict = {
                    "patch_embed.proj.weight": torch.randn(768, 3, 16, 16),
                    "head.weight": torch.randn(38, 768),
                    "head.bias": torch.randn(38),
                }

            checkpoint = {
                "model_state_dict": state_dict,
                "num_classes": 38,
                "class_names": [f"class_{j}" for j in range(38)],
                "model_version": "1.0.0",
                "training_metadata": {"architecture": arch, "accuracy": 0.88 + i * 0.02},
            }
            torch.save(checkpoint, model_path)

            model_id = registry.register_model(
                model_path=model_path,
                name=f"{arch}_plantguard",
                architecture=arch,
                dataset_version="plantvillage_v1.0",
                hyperparameters={"num_classes": 38, "architecture": arch},
                performance_metrics={"accuracy": 0.88 + i * 0.02},
                description=f"PlantGuard model with {arch} architecture",
                tags=[arch, "multi_arch"],
            )
            model_ids.append(model_id)

        # Test switching between different architectures
        with patch.object(model_manager, "_load_local_model") as mock_load:

            def mock_load_func(model_config):
                mock_adapter = MagicMock()
                arch = model_config.get("architecture", "unknown")
                mock_adapter.predict.return_value = (f"{arch}_prediction", 0.90)
                mock_adapter.get_architecture.return_value = arch
                return mock_adapter

            mock_load.side_effect = mock_load_func
            model_manager.sync_with_registry()

        models = model_manager.list_available_models()
        arch_models = [m for m in models if "multi_arch" in m.get("tags", [])]

        test_image = Image.new("RGB", (224, 224), color="orange")

        # Test switching between architectures
        for model in arch_models:
            with patch.object(model_manager, "_load_local_model") as mock_load:
                mock_adapter = MagicMock()
                arch = model["architecture"]
                mock_adapter.predict.return_value = (f"{arch}_prediction", 0.90)
                mock_adapter.get_architecture.return_value = arch
                mock_load.return_value = mock_adapter

                success = model_manager.load_model(model["id"])
                assert success, f"Failed to load {arch} model"

                predicted_class, confidence, metadata = model_manager.predict(test_image)
                assert predicted_class == f"{arch}_prediction"
                assert metadata["architecture"] == arch


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
