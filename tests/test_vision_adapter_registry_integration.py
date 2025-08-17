"""Specialized integration tests for VisionAdapter with ModelRegistry.

This module focuses specifically on testing the deep integration between
VisionAdapter and ModelRegistry components.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch
from PIL import Image

from src.core.vision import VisionAdapter
from src.training.model_registry import ModelRegistry


class TestVisionAdapterRegistryIntegration:
    """Test VisionAdapter integration with ModelRegistry."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "models").mkdir()
            yield workspace

    @pytest.fixture
    def registry(self, temp_workspace):
        """Create ModelRegistry instance."""
        return ModelRegistry(temp_workspace / "models")

    @pytest.fixture
    def sample_registry_model(self, temp_workspace, registry):
        """Create a sample model in registry format."""
        model_path = temp_workspace / "sample_model.pt"
        checkpoint = {
            "model_state_dict": {
                "conv1.weight": torch.randn(64, 3, 7, 7),
                "bn1.weight": torch.randn(64),
                "bn1.bias": torch.randn(64),
                "fc.weight": torch.randn(38, 2048),
                "fc.bias": torch.randn(38),
            },
            "num_classes": 38,
            "class_names": [f"class_{i}" for i in range(38)],
            "model_version": "1.0.0",
            "training_metadata": {"training_date": "2024-08-17", "dataset": "plantvillage", "accuracy": 0.94, "architecture": "resnet50", "epochs": 50},
        }
        torch.save(checkpoint, model_path)

        model_id = registry.register_model(
            model_path=model_path,
            name="sample_plantguard_model",
            architecture="resnet50",
            dataset_version="plantvillage_v1.0",
            hyperparameters={"num_classes": 38, "epochs": 50, "batch_size": 32},
            performance_metrics={"accuracy": 0.94, "f1_score": 0.92, "precision": 0.93},
            description="Sample PlantGuard model for testing",
            tags=["plantguard", "resnet50", "production"],
        )

        return model_id

    def test_registry_format_detection(self, temp_workspace, registry):
        """Test VisionAdapter can detect registry vs legacy format."""
        adapter = VisionAdapter()

        # Create registry format model
        registry_path = temp_workspace / "registry_model.pt"
        registry_checkpoint = {
            "model_state_dict": {"fc.weight": torch.randn(38, 2048), "fc.bias": torch.randn(38)},
            "num_classes": 38,
            "class_names": [f"class_{i}" for i in range(38)],
            "model_version": "1.0.0",
            "training_metadata": {"training_date": "2024-08-17", "accuracy": 0.94},
        }
        torch.save(registry_checkpoint, registry_path)

        # Create legacy format model
        legacy_path = temp_workspace / "legacy_model.pt"
        legacy_checkpoint = {
            "model_state_dict": {"fc.weight": torch.randn(38, 2048), "fc.bias": torch.randn(38)},
            "num_classes": 38,
            # Missing registry metadata
        }
        torch.save(legacy_checkpoint, legacy_path)

        # Test detection
        assert adapter.is_compatible_with_registry_format(str(registry_path))
        assert not adapter.is_compatible_with_registry_format(str(legacy_path))

    def test_load_from_registry_by_id(self, registry, sample_registry_model):
        """Test loading model from registry by ID."""
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            # Load model from registry
            adapter.load_from_registry(sample_registry_model)

            # Verify adapter state
            assert adapter.is_loaded
            assert adapter.current_model_id == sample_registry_model
            assert len(adapter.class_names) == 38
            assert adapter.num_classes == 38

            # Verify model creation was called with correct parameters
            mock_create_model.assert_called_once_with(num_classes=38)

    def test_load_from_registry_by_name(self, registry, sample_registry_model):
        """Test loading model from registry by name."""
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            # Load model by name
            adapter.load_from_registry_by_name("sample_plantguard_model")

            assert adapter.is_loaded
            assert adapter.current_model_id == sample_registry_model

    def test_load_latest_version(self, registry, temp_workspace):
        """Test loading latest version of a model."""
        adapter = VisionAdapter()

        # Create multiple versions of the same model
        model_ids = []
        for version in ["1.0.0", "1.0.1", "1.1.0"]:
            model_path = temp_workspace / f"model_{version.replace('.', '_')}.pt"
            checkpoint = {
                "model_state_dict": {"fc.weight": torch.randn(38, 2048), "fc.bias": torch.randn(38)},
                "num_classes": 38,
                "class_names": [f"class_{i}" for i in range(38)],
                "model_version": version,
                "training_metadata": {"accuracy": 0.90 + float(version.split(".")[1]) * 0.01},
            }
            torch.save(checkpoint, model_path)

            model_id = registry.register_model(
                model_path=model_path,
                name="versioned_model",
                architecture="resnet50",
                dataset_version="test_v1.0",
                hyperparameters={"num_classes": 38},
                performance_metrics={"accuracy": checkpoint["training_metadata"]["accuracy"]},
                description=f"Version {version} of test model",
            )
            model_ids.append(model_id)

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            # Load latest version
            adapter.load_latest_from_registry("versioned_model")

            # Should load the highest version (1.1.0)
            assert adapter.is_loaded
            assert adapter.current_model_id == model_ids[-1]  # Latest version

    def test_model_metadata_access(self, registry, sample_registry_model):
        """Test accessing model metadata through VisionAdapter."""
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            adapter.load_from_registry(sample_registry_model)

            # Test metadata access
            metadata = adapter.get_model_metadata()
            assert metadata is not None
            assert metadata["model_id"] == sample_registry_model
            assert metadata["architecture"] == "resnet50"
            assert metadata["accuracy"] == 0.94
            assert metadata["num_classes"] == 38
            assert "plantguard" in metadata["tags"]

            # Test specific metadata queries
            assert adapter.get_model_accuracy() == 0.94
            assert adapter.get_model_architecture() == "resnet50"
            assert adapter.get_dataset_version() == "plantvillage_v1.0"

    def test_model_switching_between_registry_models(self, registry, temp_workspace):
        """Test switching between different registry models."""
        adapter = VisionAdapter()

        # Create two different models
        model_configs = [
            {"name": "fast_model", "num_classes": 10, "accuracy": 0.88, "tags": ["fast", "inference"]},
            {"name": "accurate_model", "num_classes": 38, "accuracy": 0.95, "tags": ["accurate", "production"]},
        ]

        model_ids = []
        for config in model_configs:
            model_path = temp_workspace / f"{config['name']}.pt"
            checkpoint = {
                "model_state_dict": {"fc.weight": torch.randn(config["num_classes"], 2048), "fc.bias": torch.randn(config["num_classes"])},
                "num_classes": config["num_classes"],
                "class_names": [f"class_{i}" for i in range(config["num_classes"])],
                "model_version": "1.0.0",
                "training_metadata": {"accuracy": config["accuracy"], "architecture": "resnet50"},
            }
            torch.save(checkpoint, model_path)

            model_id = registry.register_model(
                model_path=model_path,
                name=config["name"],
                architecture="resnet50",
                dataset_version="test_v1.0",
                hyperparameters={"num_classes": config["num_classes"]},
                performance_metrics={"accuracy": config["accuracy"]},
                description=f"Test model: {config['name']}",
                tags=config["tags"],
            )
            model_ids.append(model_id)

        with patch.object(adapter, "_create_model") as mock_create_model:

            def mock_create_model_func(num_classes):
                mock_model = MagicMock()
                mock_model.num_classes = num_classes
                return mock_model

            mock_create_model.side_effect = mock_create_model_func

            # Load first model
            adapter.load_from_registry(model_ids[0])
            assert adapter.num_classes == 10
            assert adapter.get_model_accuracy() == 0.88

            # Switch to second model
            adapter.load_from_registry(model_ids[1])
            assert adapter.num_classes == 38
            assert adapter.get_model_accuracy() == 0.95

            # Verify model switching worked
            assert adapter.current_model_id == model_ids[1]

    def test_prediction_with_registry_model(self, registry, sample_registry_model):
        """Test prediction workflow with registry-loaded model."""
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()

            # Mock prediction output
            mock_output = torch.randn(1, 38)
            mock_output[0, 5] = 10.0  # Make class 5 have highest score
            mock_model.return_value = mock_output
            mock_model.eval.return_value = mock_model

            mock_create_model.return_value = mock_model

            adapter.load_from_registry(sample_registry_model)

            # Test prediction
            test_image = Image.new("RGB", (224, 224), color="green")

            with patch.object(adapter, "_preprocess_image") as mock_preprocess:
                mock_tensor = torch.randn(1, 3, 224, 224)
                mock_preprocess.return_value = mock_tensor

                predicted_class, confidence = adapter.predict(test_image)

                assert predicted_class == "class_5"  # Should match highest score
                assert isinstance(confidence, float)
                assert 0.0 <= confidence <= 1.0

    def test_batch_prediction_with_registry_model(self, registry, sample_registry_model):
        """Test batch prediction with registry-loaded model."""
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()

            # Mock batch prediction output
            batch_size = 3
            mock_output = torch.randn(batch_size, 38)
            for i in range(batch_size):
                mock_output[i, i] = 10.0  # Different class for each image

            mock_model.return_value = mock_output
            mock_model.eval.return_value = mock_model

            mock_create_model.return_value = mock_model

            adapter.load_from_registry(sample_registry_model)

            # Test batch prediction
            test_images = [Image.new("RGB", (224, 224), color="red"), Image.new("RGB", (224, 224), color="green"), Image.new("RGB", (224, 224), color="blue")]

            with patch.object(adapter, "_preprocess_batch") as mock_preprocess:
                mock_tensor = torch.randn(batch_size, 3, 224, 224)
                mock_preprocess.return_value = mock_tensor

                results = adapter.predict_batch(test_images)

                assert len(results) == batch_size
                for i, (predicted_class, confidence) in enumerate(results):
                    assert predicted_class == f"class_{i}"
                    assert isinstance(confidence, float)

    def test_model_validation_and_health_check(self, registry, sample_registry_model):
        """Test model validation and health checks."""
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            adapter.load_from_registry(sample_registry_model)

            # Test model health check
            is_healthy = adapter.check_model_health()
            assert is_healthy

            # Test model validation
            validation_result = adapter.validate_model()
            assert validation_result["is_valid"]
            assert validation_result["num_classes"] == 38
            assert validation_result["architecture"] == "resnet50"

            # Test with corrupted model
            adapter.model = None
            is_healthy = adapter.check_model_health()
            assert not is_healthy

    def test_legacy_model_migration(self, temp_workspace, registry):
        """Test migration of legacy models to registry format."""
        adapter = VisionAdapter()

        # Create legacy model
        legacy_path = temp_workspace / "legacy_model.pt"
        legacy_checkpoint = {
            "model_state_dict": {"fc.weight": torch.randn(38, 2048), "fc.bias": torch.randn(38)},
            "num_classes": 38,
            # Missing registry metadata
        }
        torch.save(legacy_checkpoint, legacy_path)

        # Test migration
        migrated_path = temp_workspace / "migrated_model.pt"
        adapter.migrate_legacy_model(str(legacy_path), str(migrated_path))

        # Verify migration
        assert migrated_path.exists()

        migrated_checkpoint = torch.load(migrated_path, map_location="cpu")
        assert "model_version" in migrated_checkpoint
        assert "training_metadata" in migrated_checkpoint
        assert "class_names" in migrated_checkpoint

        # Test that migrated model is registry compatible
        assert adapter.is_compatible_with_registry_format(str(migrated_path))

        # Test loading migrated model
        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            adapter.load_checkpoint(str(migrated_path))
            assert adapter.is_loaded
            assert len(adapter.class_names) == 38

    def test_model_comparison_through_adapter(self, registry, temp_workspace):
        """Test model comparison functionality through VisionAdapter."""
        adapter = VisionAdapter()

        # Create multiple models for comparison
        model_ids = []
        accuracies = [0.88, 0.92, 0.95]

        for i, accuracy in enumerate(accuracies):
            model_path = temp_workspace / f"comparison_model_{i}.pt"
            checkpoint = {
                "model_state_dict": {"fc.weight": torch.randn(38, 2048), "fc.bias": torch.randn(38)},
                "num_classes": 38,
                "class_names": [f"class_{j}" for j in range(38)],
                "model_version": "1.0.0",
                "training_metadata": {"accuracy": accuracy},
            }
            torch.save(checkpoint, model_path)

            model_id = registry.register_model(
                model_path=model_path,
                name=f"comparison_model_{i}",
                architecture="resnet50",
                dataset_version="test_v1.0",
                hyperparameters={"num_classes": 38},
                performance_metrics={"accuracy": accuracy},
                description=f"Comparison model {i}",
            )
            model_ids.append(model_id)

        # Test getting available models for comparison
        available_models = adapter.get_available_registry_models()
        assert len(available_models) >= 3

        # Test model comparison
        comparison_result = adapter.compare_registry_models(model_ids)
        assert comparison_result is not None
        assert len(comparison_result["models"]) == 3

        # Test finding best model
        best_model_id = adapter.find_best_registry_model(metric="accuracy")
        assert best_model_id == model_ids[2]  # Highest accuracy model

    def test_model_export_through_adapter(self, registry, sample_registry_model, temp_workspace):
        """Test model export functionality through VisionAdapter."""
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            adapter.load_from_registry(sample_registry_model)

            # Test export for deployment
            export_path = temp_workspace / "exported_model.pt"
            success = adapter.export_for_deployment(str(export_path))
            assert success
            assert export_path.exists()

            # Verify export format
            exported_data = torch.load(export_path, map_location="cpu")
            assert "model_state_dict" in exported_data
            assert "deployment_info" in exported_data
            assert "class_names" in exported_data
            assert exported_data["deployment_info"]["optimized"] is True

    def test_error_handling_and_recovery(self, registry, temp_workspace):
        """Test error handling and recovery in registry integration."""
        adapter = VisionAdapter()

        # Test loading non-existent model
        with pytest.raises(ValueError, match="Model not found"):
            adapter.load_from_registry("non_existent_model")

        # Test loading corrupted model
        corrupted_path = temp_workspace / "corrupted_model.pt"
        torch.save({"invalid": "data"}, corrupted_path)

        corrupted_id = registry.register_model(
            model_path=corrupted_path,
            name="corrupted_model",
            architecture="resnet50",
            dataset_version="test_v1.0",
            hyperparameters={"num_classes": 38},
            performance_metrics={"accuracy": 0.90},
            description="Corrupted model for testing",
        )

        with pytest.raises(RuntimeError):  # Should raise model creation error
            with patch.object(adapter, "_create_model") as mock_create_model:
                mock_create_model.side_effect = RuntimeError("Model creation failed")
                adapter.load_from_registry(corrupted_id)

        # Test recovery after error
        assert not adapter.is_loaded
        assert adapter.current_model_id is None

        # Should be able to load valid model after error
        valid_path = temp_workspace / "valid_model.pt"
        valid_checkpoint = {
            "model_state_dict": {"fc.weight": torch.randn(38, 2048), "fc.bias": torch.randn(38)},
            "num_classes": 38,
            "class_names": [f"class_{i}" for i in range(38)],
            "model_version": "1.0.0",
            "training_metadata": {"accuracy": 0.90},
        }
        torch.save(valid_checkpoint, valid_path)

        valid_id = registry.register_model(
            model_path=valid_path,
            name="valid_model",
            architecture="resnet50",
            dataset_version="test_v1.0",
            hyperparameters={"num_classes": 38},
            performance_metrics={"accuracy": 0.90},
            description="Valid model for recovery testing",
        )

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            adapter.load_from_registry(valid_id)
            assert adapter.is_loaded

    def test_performance_monitoring_integration(self, registry, sample_registry_model):
        """Test performance monitoring integration."""
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            adapter.load_from_registry(sample_registry_model)

            # Test performance monitoring
            adapter.enable_performance_monitoring()

            # Simulate predictions to generate performance data
            test_image = Image.new("RGB", (224, 224), color="green")

            with patch.object(adapter, "_preprocess_image") as mock_preprocess:
                mock_tensor = torch.randn(1, 3, 224, 224)
                mock_preprocess.return_value = mock_tensor

                with patch.object(adapter.model, "__call__") as mock_forward:
                    mock_output = torch.randn(1, 38)
                    mock_forward.return_value = mock_output

                    # Make multiple predictions
                    for _ in range(10):
                        adapter.predict(test_image)

            # Get performance statistics
            perf_stats = adapter.get_performance_stats()
            assert perf_stats is not None
            assert "avg_inference_time" in perf_stats
            assert "total_predictions" in perf_stats
            assert perf_stats["total_predictions"] == 10

            # Test performance comparison with registry
            perf_comparison = adapter.compare_performance_with_registry()
            assert perf_comparison is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
