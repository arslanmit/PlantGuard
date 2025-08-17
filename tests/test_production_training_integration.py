"""Integration tests for production training pipeline with existing PlantGuard components."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import torch
from PIL import Image

from src.core.vision import VisionAdapter
from src.features.model_switching.model_manager import PlantGuardModelManager
from src.training.model_registry import ModelRegistry


class TestProductionTrainingIntegration(unittest.TestCase):
    """Test integration between production training pipeline and existing components."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.registry_dir = self.temp_dir / "models"
        self.config_dir = self.temp_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Create test image
        self.test_image = Image.new("RGB", (224, 224), color="green")

    def tearDown(self) -> None:
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vision_adapter_registry_integration(self) -> None:
        """Test VisionAdapter integration with ModelRegistry."""
        # Create registry
        registry = ModelRegistry(self.registry_dir)

        # Create a mock model checkpoint
        model_path = self.temp_dir / "test_model.pt"
        checkpoint = {
            "model_state_dict": {"layer.weight": torch.randn(10, 5)},
            "num_classes": 38,
            "class_names": [f"class_{i}" for i in range(38)],
        }
        torch.save(checkpoint, model_path)

        # Register model
        model_id = registry.register_model(
            model_path=model_path,
            name="test_model",
            architecture="resnet50",
            dataset_version="test",
            hyperparameters={"num_classes": 38},
            performance_metrics={"accuracy": 0.95},
            description="Test model for integration",
        )

        # Test VisionAdapter can load from registry
        adapter = VisionAdapter()

        # Mock the model loading to avoid actual ResNet50 instantiation
        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            # This should work without errors
            adapter.load_from_registry(model_id)

            self.assertTrue(adapter.is_loaded)
            self.assertEqual(len(adapter.class_names), 38)

    def test_model_manager_registry_integration(self) -> None:
        """Test PlantGuardModelManager integration with registry models."""
        # Create config file
        config_path = self.config_dir / "models.json"
        config_data = {
            "default_model": "test_registry_model",
            "models": {
                "test_registry_model": {
                    "name": "Test Registry Model",
                    "type": "local",
                    "model_id": "registry:test_model_v1.0.0",
                    "description": "Test model from registry",
                    "accuracy": 0.95,
                    "confidence_threshold": 0.7,
                    "enabled": True,
                    "device": "cpu",
                }
            },
        }

        with config_path.open("w") as f:
            json.dump(config_data, f)

        # Create model manager
        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # Test listing models
        models = manager.list_available_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "Test Registry Model")
        self.assertEqual(models[0]["type"], "local")

    def test_backward_compatibility(self) -> None:
        """Test backward compatibility with legacy model files."""
        # Create a legacy model file
        legacy_path = self.temp_dir / "legacy_model.pt"
        legacy_checkpoint = {
            "model_state_dict": {"layer.weight": torch.randn(10, 5)},
            "num_classes": 38,
            # No class_names or registry metadata
        }
        torch.save(legacy_checkpoint, legacy_path)

        # Test VisionAdapter can detect it's not registry format
        adapter = VisionAdapter()
        is_compatible = adapter.is_compatible_with_registry_format(str(legacy_path))
        self.assertFalse(is_compatible)

        # Test migration
        migrated_path = self.temp_dir / "migrated_model.pt"
        adapter.migrate_legacy_model(str(legacy_path), str(migrated_path))

        # Check migrated model has registry format
        is_migrated_compatible = adapter.is_compatible_with_registry_format(str(migrated_path))
        self.assertTrue(is_migrated_compatible)

        # Load migrated checkpoint and verify metadata
        migrated_checkpoint = torch.load(migrated_path, map_location="cpu")
        self.assertIn("model_version", migrated_checkpoint)
        self.assertIn("training_metadata", migrated_checkpoint)

    def test_model_manager_sync_with_registry(self) -> None:
        """Test model manager syncing with registry."""
        # Create registry with a model
        registry = ModelRegistry(self.registry_dir)

        model_path = self.temp_dir / "sync_test_model.pt"
        checkpoint = {
            "model_state_dict": {"layer.weight": torch.randn(10, 5)},
            "num_classes": 38,
            "class_names": [f"class_{i}" for i in range(38)],
        }
        torch.save(checkpoint, model_path)

        model_id = registry.register_model(
            model_path=model_path,
            name="sync_test",
            architecture="resnet50",
            dataset_version="test",
            hyperparameters={"num_classes": 38},
            performance_metrics={"accuracy": 0.90},
            description="Model for sync test",
        )

        # Create model manager with empty config
        config_path = self.config_dir / "sync_test_models.json"
        config_data = {"models": {}}
        with config_path.open("w") as f:
            json.dump(config_data, f)

        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # Initially no models
        models = manager.list_available_models()
        self.assertEqual(len(models), 0)

        # Sync with registry
        with patch.object(manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_load.return_value = mock_adapter

            success = manager.sync_with_registry()
            self.assertTrue(success)

        # Should now have the registry model
        models = manager.list_available_models()
        self.assertEqual(len(models), 1)
        self.assertIn("registry_", models[0]["id"])

    def test_migration_utility_integration(self) -> None:
        """Test the migration utility script integration."""
        # Create legacy models
        legacy_models = []
        for i in range(2):
            legacy_path = self.temp_dir / f"legacy_model_{i}.pt"
            checkpoint = {
                "model_state_dict": {"layer.weight": torch.randn(10, 5)},
                "num_classes": 38,
            }
            torch.save(checkpoint, legacy_path)
            legacy_models.append(legacy_path)

        # Test scanning for legacy models
        from scripts.migrate_models import scan_for_legacy_models

        with patch("scripts.migrate_models.Path") as mock_path:
            # Mock the search paths to return our temp directory
            mock_search_dir = MagicMock()
            mock_search_dir.exists.return_value = True
            mock_search_dir.glob.return_value = legacy_models
            mock_path.return_value = mock_search_dir

            found_models = scan_for_legacy_models()
            self.assertEqual(len(found_models), 2)

    def test_model_switcher_registry_support(self) -> None:
        """Test model switcher script with registry support."""
        # Create registry with model
        registry = ModelRegistry(self.registry_dir)

        model_path = self.temp_dir / "switcher_test_model.pt"
        checkpoint = {
            "model_state_dict": {"layer.weight": torch.randn(10, 5)},
            "num_classes": 38,
            "class_names": [f"class_{i}" for i in range(38)],
        }
        torch.save(checkpoint, model_path)

        model_id = registry.register_model(
            model_path=model_path,
            name="switcher_test",
            architecture="resnet50",
            dataset_version="test",
            hyperparameters={"num_classes": 38},
            performance_metrics={"accuracy": 0.85},
            description="Model for switcher test",
        )

        # Test listing models in registry mode
        from scripts.model_switching.model_switcher import list_models_registry

        with patch("scripts.model_switching.model_switcher.ModelRegistry") as mock_registry_class:
            mock_registry = MagicMock()
            mock_registry.list_models.return_value = [registry.get_model(model_id)]
            mock_registry_class.return_value = mock_registry

            # This should not raise an exception
            list_models_registry()

    def test_ui_integration_with_registry(self) -> None:
        """Test UI components work with registry models."""
        # Create model manager with registry model
        config_path = self.config_dir / "ui_test_models.json"
        config_data = {
            "models": {
                "ui_test_model": {
                    "name": "UI Test Model",
                    "type": "local",
                    "model_id": "registry:ui_test_v1.0.0",
                    "description": "Model for UI testing",
                    "accuracy": 0.92,
                    "confidence_threshold": 0.7,
                    "enabled": True,
                    "device": "cpu",
                }
            }
        }

        with config_path.open("w") as f:
            json.dump(config_data, f)

        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # Test getting registry models for UI
        registry_models = manager.get_registry_models()
        # Should return empty list if no registry exists, but not crash
        self.assertIsInstance(registry_models, list)

    def test_complete_workflow_integration(self) -> None:
        """Test complete workflow from training to UI integration."""
        # 1. Create a "trained" model (simulate production training output)
        registry = ModelRegistry(self.registry_dir)

        model_path = self.temp_dir / "workflow_model.pt"
        checkpoint = {
            "model_state_dict": {"layer.weight": torch.randn(10, 5)},
            "num_classes": 38,
            "class_names": [f"class_{i}" for i in range(38)],
            "model_version": "1.0.0",
            "training_metadata": {
                "training_date": "2024-08-17",
                "dataset": "plantvillage",
                "accuracy": 0.94,
            },
        }
        torch.save(checkpoint, model_path)

        # 2. Register model (simulate production training registration)
        model_id = registry.register_model(
            model_path=model_path,
            name="workflow_test",
            architecture="resnet50",
            dataset_version="plantvillage_v1.0",
            hyperparameters={"num_classes": 38, "epochs": 100},
            performance_metrics={"accuracy": 0.94, "f1_score": 0.93},
            description="Complete workflow test model",
            tags=["production", "plantvillage"],
        )

        # 3. Create model manager config
        config_path = self.config_dir / "workflow_models.json"
        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # 4. Sync with registry (simulate user running make sync-models)
        with patch.object(manager, "_load_local_model") as mock_load:
            mock_adapter = MagicMock()
            mock_adapter.predict.return_value = ("test_class", 0.95)
            mock_adapter.get_class_names.return_value = [f"class_{i}" for i in range(38)]
            mock_load.return_value = mock_adapter

            success = manager.sync_with_registry()
            self.assertTrue(success)

        # 5. Test model is available in manager
        models = manager.list_available_models()
        self.assertEqual(len(models), 1)
        self.assertIn("workflow_test", models[0]["name"])

        # 6. Test loading and prediction
        registry_model_key = f"registry_{model_id}"
        if registry_model_key in [m["id"] for m in models]:
            with patch.object(manager, "_load_local_model") as mock_load:
                mock_adapter = MagicMock()
                mock_adapter.predict.return_value = ("healthy_plant", 0.95)
                mock_load.return_value = mock_adapter

                success = manager.load_model(registry_model_key)
                self.assertTrue(success)

                # Test prediction
                predicted_class, confidence, metadata = manager.predict(self.test_image)
                self.assertEqual(predicted_class, "healthy_plant")
                self.assertEqual(confidence, 0.95)
                self.assertIn("model_name", metadata)


if __name__ == "__main__":
    unittest.main()
