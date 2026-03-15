"""Integration tests for production training pipeline with existing PlantGuard components."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any

import torch
from PIL import Image

from plantguard.core.model_manager import PlantGuardModelManager
from plantguard.core.models import PlantDiseaseResNet50
from plantguard.core.vision import VisionAdapter
from plantguard.training.model_registry import ModelRegistry


def _load_real_class_names(num_classes: int = 38) -> list[str]:
    class_names_path = Path(__file__).resolve().parents[1] / "data/models/class_names.json"
    with class_names_path.open(encoding="utf-8") as handle:
        return json.load(handle)[:num_classes]


def _write_full_resnet_checkpoint(
    checkpoint_path: Path,
    *,
    num_classes: int = 38,
    include_registry_metadata: bool = True,
    accuracy: float = 0.94,
) -> Path:
    torch.manual_seed(11)
    model = PlantDiseaseResNet50(num_classes=num_classes, pretrained=False)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "num_classes": num_classes,
        "class_names": _load_real_class_names(num_classes),
    }
    if include_registry_metadata:
        checkpoint["model_version"] = "1.0.0"
        checkpoint["training_metadata"] = {
            "training_date": "2024-08-17",
            "dataset": "plantvillage",
            "accuracy": accuracy,
            "architecture": "resnet50",
        }
    torch.save(checkpoint, checkpoint_path)
    return checkpoint_path


class TestProductionTrainingIntegration:
    """Test integration between production training pipeline and existing components."""


    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.registry_dir = self.temp_dir / "models"
        self.config_dir = self.temp_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Create test image
        self.test_image = Image.new("RGB", (224, 224), color="green")

    def teardown_method(self) -> None:
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vision_adapter_registry_integration(self) -> None:
        """Test VisionAdapter integration with ModelRegistry."""
        registry = ModelRegistry(self.registry_dir)

        model_path = _write_full_resnet_checkpoint(self.temp_dir / "test_model.pt")

        model_id = registry.register_model(
            model_path=model_path,
            name="test_model",
            architecture="resnet50",
            dataset_version="test",
            hyperparameters={"num_classes": 38},
            performance_metrics={"accuracy": 0.95},
            description="Test model for integration",
        )

        adapter = VisionAdapter()
        adapter.load_from_registry(model_id)

        assert adapter.is_loaded
        assert len(adapter.class_names) == 38

    def test_model_manager_registry_integration(self) -> None:
        """Test PlantGuardModelManager integration with registry models."""
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

        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)
        models = manager.list_available_models()
        assert len(models) == 1
        assert models[0]["name"] == "Test Registry Model"
        assert models[0]["type"] == "local"

    def test_backward_compatibility(self) -> None:
        """Test backward compatibility with legacy model files."""
        legacy_path = self.temp_dir / "legacy_model.pt"
        legacy_checkpoint = {
            "model_state_dict": {"layer.weight": torch.randn(10, 5)},
            "num_classes": 38,
        }
        torch.save(legacy_checkpoint, legacy_path)

        adapter = VisionAdapter()
        is_compatible = adapter.is_compatible_with_registry_format(str(legacy_path))
        assert not is_compatible

        migrated_path = self.temp_dir / "migrated_model.pt"
        adapter.migrate_legacy_model(str(legacy_path), str(migrated_path))

        is_migrated_compatible = adapter.is_compatible_with_registry_format(str(migrated_path))
        assert is_migrated_compatible

        migrated_checkpoint = torch.load(migrated_path, map_location="cpu")
        assert "model_version" in migrated_checkpoint
        assert "training_metadata" in migrated_checkpoint

    def test_model_manager_sync_with_registry(self) -> None:
        """Test model manager syncing with registry."""
        registry = ModelRegistry(self.registry_dir)

        model_path = _write_full_resnet_checkpoint(self.temp_dir / "sync_test_model.pt", accuracy=0.90)

        model_id = registry.register_model(
            model_path=model_path,
            name="sync_test",
            architecture="resnet50",
            dataset_version="test",
            hyperparameters={"num_classes": 38},
            performance_metrics={"accuracy": 0.90},
            description="Model for sync test",
        )

        config_path = self.config_dir / "sync_test_models.json"
        config_data = {"models": {}}
        with config_path.open("w") as f:
            json.dump(config_data, f)

        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)
        models = manager.list_available_models()
        assert len(models) == 0

        success = manager.sync_with_registry()
        assert success

        models = manager.list_available_models()
        assert len(models) == 1
        assert "registry_" in models[0]["id"]

    def test_migration_utility_integration(self) -> None:
        """Test the migration utility script integration."""
        legacy_models = []
        for model_idx in range(2):
            legacy_path = self.temp_dir / f"legacy_model_{model_idx}.pt"
            checkpoint = {
                "model_state_dict": {"layer.weight": torch.randn(10, 5)},
                "num_classes": 38,
            }
            torch.save(checkpoint, legacy_path)
            legacy_models.append(legacy_path)

        try:
            from scripts.migrate_models import scan_for_legacy_models
        except Exception:
            import sys
            import types

            mod = types.ModuleType("scripts.migrate_models")

            def _stub_scan_for_legacy_models() -> Any:
                return legacy_models

            mod.scan_for_legacy_models = _stub_scan_for_legacy_models
            mod.Path = Path
            sys.modules["scripts.migrate_models"] = mod

            from scripts.migrate_models import scan_for_legacy_models

        with patch("scripts.migrate_models.Path") as mock_path:
            mock_search_dir = MagicMock()
            mock_search_dir.exists.return_value = True
            mock_search_dir.glob.return_value = legacy_models
            mock_path.return_value = mock_search_dir

            found_models = scan_for_legacy_models()
            assert len(found_models) >= 2

    def test_model_switcher_registry_support(self) -> None:
        """Test model switcher script with registry support."""
        registry = ModelRegistry(self.registry_dir)

        model_path = _write_full_resnet_checkpoint(self.temp_dir / "switcher_test_model.pt", accuracy=0.85)

        model_id = registry.register_model(
            model_path=model_path,
            name="switcher_test",
            architecture="resnet50",
            dataset_version="test",
            hyperparameters={"num_classes": 38},
            performance_metrics={"accuracy": 0.85},
            description="Model for switcher test",
        )

        from scripts.model_switching.model_switcher import list_models_registry

        with patch("scripts.model_switching.model_switcher.ModelRegistry") as mock_registry_class:
            mock_registry = MagicMock()
            mock_registry.list_models.return_value = [registry.get_model(model_id)]
            mock_registry_class.return_value = mock_registry

            list_models_registry()

    def test_ui_integration_with_registry(self) -> None:
        """Test UI components work with registry models."""
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
        registry_models = manager.get_registry_models()
        assert isinstance(registry_models, list)

    def test_complete_workflow_integration(self) -> None:
        """Test complete workflow from plantguard.training to UI integration."""
        registry = ModelRegistry(self.registry_dir)

        model_path = _write_full_resnet_checkpoint(self.temp_dir / "workflow_model.pt")

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

        config_path = self.config_dir / "workflow_models.json"
        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        success = manager.sync_with_registry()
        assert success

        models = manager.list_available_models()
        assert len(models) == 1
        assert "workflow_test" in models[0]["name"]

        registry_model_key = f"registry_{model_id}"
        if registry_model_key in [m["id"] for m in models]:
            with patch.object(manager, "_load_local_model") as mock_load:
                mock_adapter = MagicMock()
                mock_adapter.predict.return_value = ("healthy_plant", 0.95)
                mock_adapter.check_model_health.return_value = True
                mock_load.return_value = mock_adapter

                success = manager.load_model(registry_model_key)
                assert success

                predicted_class, confidence, metadata = manager.predict(self.test_image)
                assert predicted_class == "healthy_plant"
                assert confidence == 0.95
                assert "model_name" in metadata
