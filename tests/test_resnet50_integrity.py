from __future__ import annotations

import json
import sys
import types
from importlib import import_module
from pathlib import Path

import pytest
import torch
from PIL import Image
from torch import nn
from torchvision import models

from plantguard.core.model_manager import PlantGuardModelManager
from plantguard.core.models import PlantDiseaseResNet50
from plantguard.core.vision import LoadCheckpointError, VisionAdapter, is_runtime_checkpoint_valid
from plantguard.training.model_registry import ModelRegistry


REAL_CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]


def _get_production_workflow_class():
    """Import ProductionWorkflow with a lightweight monitor stub for tests."""
    if "plantguard.training.monitor" not in sys.modules:
        monitor_module = types.ModuleType("plantguard.training.monitor")

        class _StubTrainingMonitor:
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.kwargs = kwargs

            def save_training_report(self, training_result) -> Path:
                return Path("training_report.json")

        monitor_module.TrainingMonitor = _StubTrainingMonitor
        sys.modules["plantguard.training.monitor"] = monitor_module

    if "plantguard.training.production_trainer" not in sys.modules:
        trainer_module = types.ModuleType("plantguard.training.production_trainer")

        class _StubProductionTrainer:
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.kwargs = kwargs

        trainer_module.ProductionTrainer = _StubProductionTrainer
        sys.modules["plantguard.training.production_trainer"] = trainer_module

    workflow_module = import_module("scripts.production.production_training_workflow")
    return workflow_module.ProductionWorkflow


def _write_full_resnet_checkpoint(
    checkpoint_path: Path,
    *,
    class_names: list[str] | None = None,
    num_classes: int = 38,
) -> Path:
    torch.manual_seed(7)
    model = PlantDiseaseResNet50(num_classes=num_classes, pretrained=False)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "num_classes": num_classes,
        "class_names": list(class_names or REAL_CLASS_NAMES[:num_classes]),
        "model_version": "1.0.0",
        "training_metadata": {"accuracy": 0.91, "architecture": "resnet50"},
    }
    torch.save(checkpoint, checkpoint_path)
    return checkpoint_path


def _write_partial_resnet_checkpoint(checkpoint_path: Path, *, class_names: list[str] | None = None) -> Path:
    checkpoint = {
        "model_state_dict": {
            "fc.weight": torch.randn(38, 2048),
            "fc.bias": torch.randn(38),
        },
        "num_classes": 38,
        "class_names": list(class_names or REAL_CLASS_NAMES),
        "model_version": "1.0.0",
        "training_metadata": {"accuracy": 0.85, "architecture": "resnet50"},
    }
    torch.save(checkpoint, checkpoint_path)
    return checkpoint_path


def _write_training_style_resnet_checkpoint(
    checkpoint_path: Path,
    *,
    class_names: list[str] | None = None,
    num_classes: int = 38,
) -> Path:
    torch.manual_seed(11)
    model = models.resnet50(weights=None)
    model.fc = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.fc.in_features, num_classes),
    )
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "epoch": 0,
        "best_val_loss": 0.123,
        "best_val_accuracy": 0.91,
        "config": {
            "num_classes": num_classes,
            "model_architecture": "resnet50",
            "dropout_rate": 0.5,
            "output_dir": checkpoint_path.parent,
        },
        "class_names": list(class_names or REAL_CLASS_NAMES[:num_classes]),
    }
    torch.save(checkpoint, checkpoint_path)
    return checkpoint_path


def test_load_checkpoint_rejects_empty_file(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "empty_resnet.pt"
    checkpoint_path.write_bytes(b"")

    adapter = VisionAdapter(device="cpu")

    with pytest.raises(LoadCheckpointError):
        adapter.load_checkpoint(str(checkpoint_path))

    assert not adapter.is_loaded
    assert not adapter.check_model_health()


def test_load_checkpoint_rejects_partial_state_dict(tmp_path: Path) -> None:
    checkpoint_path = _write_partial_resnet_checkpoint(tmp_path / "partial_resnet.pt")

    adapter = VisionAdapter(device="cpu")

    with pytest.raises(LoadCheckpointError):
        adapter.load_checkpoint(str(checkpoint_path))

    assert not adapter.is_loaded
    assert not adapter.check_model_health()


def test_check_model_health_rejects_placeholder_class_names(tmp_path: Path) -> None:
    placeholder_names = [f"class_{idx}" for idx in range(38)]
    checkpoint_path = _write_full_resnet_checkpoint(
        tmp_path / "placeholder_resnet.pt",
        class_names=placeholder_names,
    )

    adapter = VisionAdapter(device="cpu")
    adapter.load_checkpoint(str(checkpoint_path))

    assert adapter.is_loaded
    assert not adapter.check_model_health()
    assert not adapter.validate_model()["is_valid"]


def test_load_checkpoint_accepts_valid_full_runtime_checkpoint(tmp_path: Path) -> None:
    checkpoint_path = _write_full_resnet_checkpoint(tmp_path / "valid_runtime_resnet.pt")

    adapter = VisionAdapter(device="cpu")
    adapter.load_checkpoint(str(checkpoint_path))

    model_info = adapter.get_model_info()

    assert adapter.is_loaded
    assert adapter.check_model_health()
    assert adapter.validate_model()["is_valid"]
    assert model_info["integrity_valid"] is True
    assert model_info["class_names_valid"] is True
    assert model_info["num_classes"] == 38
    assert model_info["class_names"] == REAL_CLASS_NAMES


def test_load_checkpoint_accepts_training_style_runtime_checkpoint(tmp_path: Path) -> None:
    checkpoint_path = _write_training_style_resnet_checkpoint(tmp_path / "training_style_resnet.pt")

    adapter = VisionAdapter(device="cpu")
    adapter.load_checkpoint(str(checkpoint_path))

    assert is_runtime_checkpoint_valid(checkpoint_path)
    assert adapter.is_loaded
    assert adapter.check_model_health()
    assert adapter.get_model_info()["num_classes"] == 38


def test_valid_checkpoint_predictions_are_deterministic_across_reloads(tmp_path: Path) -> None:
    checkpoint_path = _write_full_resnet_checkpoint(tmp_path / "full_resnet.pt")
    image = Image.new("RGB", (224, 224), color="green")

    predictions = []
    for _ in range(3):
        adapter = VisionAdapter(device="cpu")
        adapter.load_checkpoint(str(checkpoint_path))
        predictions.append(adapter.predict(image))

    assert predictions[0] == predictions[1] == predictions[2]


def test_model_manager_excludes_invalid_registry_models_from_default_config(tmp_path: Path) -> None:
    registry_dir = tmp_path / "models"
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    registry = ModelRegistry(registry_dir)

    valid_model_path = _write_full_resnet_checkpoint(tmp_path / "valid_registry_model.pt")
    invalid_model_path = _write_partial_resnet_checkpoint(tmp_path / "invalid_registry_model.pt")

    valid_model_id = registry.register_model(
        model_path=valid_model_path,
        name="valid_registry_model",
        architecture="resnet50",
        dataset_version="plantvillage_v1.0",
        hyperparameters={"num_classes": 38},
        performance_metrics={"accuracy": 0.93},
        description="Valid full registry model",
        tags=["production", "resnet50"],
    )
    invalid_model_id = registry.register_model(
        model_path=invalid_model_path,
        name="invalid_registry_model",
        architecture="resnet50",
        dataset_version="plantvillage_v1.0",
        hyperparameters={"num_classes": 38},
        performance_metrics={"accuracy": 0.85},
        description="Invalid partial registry model",
        tags=["test", "resnet50", "production"],
    )

    manager = PlantGuardModelManager(
        config_path=str(config_dir / "models.json"),
        autoload_default=False,
    )
    manager.create_default_config()

    available_model_ids = {model["id"] for model in manager.list_available_models()}
    assert f"registry_{valid_model_id}" in available_model_ids
    assert f"registry_{invalid_model_id}" not in available_model_ids


def test_model_manager_disables_stale_invalid_local_resnet_config(tmp_path: Path) -> None:
    invalid_checkpoint = tmp_path / "vision_resnet50.pt"
    invalid_checkpoint.write_bytes(b"")

    config_path = tmp_path / "models.json"
    config_path.write_text(
        json.dumps(
            {
                "default_model": "local_resnet",
                "models": {
                    "local_resnet": {
                        "name": "Local ResNet50",
                        "type": "local",
                        "model_id": str(invalid_checkpoint),
                        "description": "Stale invalid ResNet config",
                        "accuracy": 0.91,
                        "confidence_threshold": 0.5,
                        "enabled": True,
                        "device": "cpu",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)
    models = {model["id"]: model for model in manager.list_available_models()}

    assert models["local_resnet"]["enabled"] is False


def test_model_manager_autoloads_valid_local_resnet_when_config_defaults_to_it(tmp_path: Path) -> None:
    checkpoint_path = _write_training_style_resnet_checkpoint(tmp_path / "vision_resnet50.pt")
    config_path = tmp_path / "models.json"
    config_path.write_text(
        json.dumps(
            {
                "default_model": "local_resnet",
                "models": {
                    "local_resnet": {
                        "name": "Local ResNet50",
                        "type": "local",
                        "model_id": str(checkpoint_path),
                        "description": "Validated runtime checkpoint",
                        "accuracy": 0.94,
                        "confidence_threshold": 0.5,
                        "enabled": True,
                        "device": "cpu",
                    },
                    "vit_best": {
                        "name": "Vision Transformer",
                        "type": "huggingface",
                        "model_id": "dummy/vit",
                        "description": "Backup model",
                        "accuracy": 0.99,
                        "confidence_threshold": 0.7,
                        "enabled": True,
                        "device": "cpu",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=True)

    assert manager.current_model is not None
    assert manager._get_current_model_key() == "local_resnet"
    assert manager.current_adapter is not None
    assert manager.current_adapter.check_model_health()


def test_production_workflow_promotes_valid_runtime_checkpoint_and_updates_config(tmp_path: Path) -> None:
    ProductionWorkflow = _get_production_workflow_class()
    source_checkpoint = _write_training_style_resnet_checkpoint(tmp_path / "best_model.pt")
    config_path = tmp_path / "config" / "models.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "default_model": "vit_best",
                "models": {
                    "vit_best": {
                        "name": "Vision Transformer (Best Performance)",
                        "type": "huggingface",
                        "model_id": "Abhiram4/PlantDiseaseDetectorVit2",
                        "description": "Vision Transformer model",
                        "accuracy": 1.0,
                        "confidence_threshold": 0.7,
                        "enabled": True,
                        "device": "auto",
                    },
                    "mobilenet_fast": {
                        "name": "MobileNet (Fast & Lightweight)",
                        "type": "huggingface",
                        "model_id": "Diginsa/Plant-Disease-Detection-Project",
                        "description": "MobileNet model",
                        "accuracy": 0.95,
                        "confidence_threshold": 0.6,
                        "enabled": True,
                        "device": "auto",
                    },
                    "local_resnet": {
                        "name": "Local ResNet50",
                        "type": "local",
                        "model_id": "data/models/vision_resnet50.pt",
                        "description": "Local ResNet50 model (requires training)",
                        "accuracy": 0.05,
                        "confidence_threshold": 0.5,
                        "enabled": False,
                        "device": "auto",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    workflow = ProductionWorkflow()
    workflow.runtime_checkpoint_path = tmp_path / "data" / "models" / "vision_resnet50.pt"
    workflow.model_config_path = config_path

    promoted_path = workflow._promote_runtime_checkpoint(source_checkpoint, best_accuracy=0.94)

    assert promoted_path == workflow.runtime_checkpoint_path
    assert promoted_path.exists()
    assert is_runtime_checkpoint_valid(promoted_path)

    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    assert config_data["default_model"] == "local_resnet"
    assert config_data["models"]["local_resnet"]["enabled"] is True
    assert config_data["models"]["local_resnet"]["model_id"] == str(workflow.runtime_checkpoint_path)
    assert config_data["models"]["local_resnet"]["accuracy"] == 0.94
    assert "validated runtime checkpoint" in config_data["models"]["local_resnet"]["description"].lower()


def test_production_workflow_rejects_invalid_runtime_checkpoint_promotion(tmp_path: Path) -> None:
    ProductionWorkflow = _get_production_workflow_class()
    invalid_checkpoint = _write_partial_resnet_checkpoint(tmp_path / "partial_resnet.pt")
    config_path = tmp_path / "config" / "models.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "default_model": "vit_best",
                "models": {
                    "vit_best": {
                        "name": "Vision Transformer (Best Performance)",
                        "type": "huggingface",
                        "model_id": "Abhiram4/PlantDiseaseDetectorVit2",
                        "description": "Vision Transformer model",
                        "accuracy": 1.0,
                        "confidence_threshold": 0.7,
                        "enabled": True,
                        "device": "auto",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    workflow = ProductionWorkflow()
    workflow.runtime_checkpoint_path = tmp_path / "data" / "models" / "vision_resnet50.pt"
    workflow.model_config_path = config_path

    with pytest.raises(ValueError, match="validated runtime checkpoint"):
        workflow._promote_runtime_checkpoint(invalid_checkpoint, best_accuracy=0.82)

    assert not workflow.runtime_checkpoint_path.exists()
    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    assert config_data["default_model"] == "vit_best"


def test_production_workflow_entrypoint_imports_without_optional_training_extras(monkeypatch) -> None:
    for module_name in (
        "scripts.production.production_training_workflow",
        "plantguard.training.monitor",
        "plantguard.training.production_trainer",
        "src.training.production_trainer",
    ):
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    workflow_module = import_module("scripts.production.production_training_workflow")

    assert hasattr(workflow_module, "ProductionWorkflow")
