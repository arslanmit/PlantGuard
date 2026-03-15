from __future__ import annotations

import json
import sys
import types
from importlib import import_module
from pathlib import Path

import pytest
import torch
from torch import nn
from torchvision import models

from plantguard.core.model_manager import PlantGuardModelManager
from plantguard.core.models import PlantDiseaseResNet50
from plantguard.core import vision as vision_module
from plantguard.core.vision import is_runtime_checkpoint_valid


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


class _UnsafeConfigMarker:
    def __init__(self, value: str) -> None:
        self.value = value


def _write_full_resnet_checkpoint(checkpoint_path: Path, *, num_classes: int = 38) -> Path:
    torch.manual_seed(7)
    model = PlantDiseaseResNet50(num_classes=num_classes, pretrained=False)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "num_classes": num_classes,
        "class_names": list(REAL_CLASS_NAMES[:num_classes]),
        "model_version": "1.0.0",
        "training_metadata": {"accuracy": 0.91, "architecture": "resnet50"},
    }
    torch.save(checkpoint, checkpoint_path)
    return checkpoint_path


def _write_training_style_resnet_checkpoint(
    checkpoint_path: Path,
    *,
    num_classes: int = 38,
    unsafe_marker: object | None = None,
) -> Path:
    torch.manual_seed(11)
    model = models.resnet50(weights=None)
    model.fc = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.fc.in_features, num_classes),
    )
    config = {
        "num_classes": num_classes,
        "model_architecture": "resnet50",
        "dropout_rate": 0.5,
        "output_dir": checkpoint_path.parent,
    }
    if unsafe_marker is not None:
        config["unsafe_marker"] = unsafe_marker
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "epoch": 0,
        "best_val_loss": 0.123,
        "best_val_accuracy": 0.91,
        "config": config,
        "class_names": list(REAL_CLASS_NAMES[:num_classes]),
    }
    torch.save(checkpoint, checkpoint_path)
    return checkpoint_path


def _get_production_workflow_class(monkeypatch: pytest.MonkeyPatch):
    """Import ProductionWorkflow with scoped stubs so tests do not leak modules."""
    monkeypatch.delitem(sys.modules, "scripts.production.production_training_workflow", raising=False)

    if "plantguard.training.monitor" not in sys.modules:
        monitor_module = types.ModuleType("plantguard.training.monitor")

        class _StubTrainingMonitor:
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.kwargs = kwargs

            def save_training_report(self, training_result) -> Path:
                return Path("training_report.json")

        monitor_module.TrainingMonitor = _StubTrainingMonitor
        monkeypatch.setitem(sys.modules, "plantguard.training.monitor", monitor_module)

    if "plantguard.training.production_trainer" not in sys.modules:
        trainer_module = types.ModuleType("plantguard.training.production_trainer")

        class _StubProductionTrainer:
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.kwargs = kwargs

        trainer_module.ProductionTrainer = _StubProductionTrainer
        monkeypatch.setitem(sys.modules, "plantguard.training.production_trainer", trainer_module)

    workflow_module = import_module("scripts.production.production_training_workflow")
    return workflow_module.ProductionWorkflow


def test_runtime_checkpoint_validation_rejects_unsafe_deserialization_payload(tmp_path: Path) -> None:
    checkpoint_path = _write_training_style_resnet_checkpoint(
        tmp_path / "unsafe_runtime_checkpoint.pt",
        unsafe_marker=_UnsafeConfigMarker("unsafe"),
    )

    assert not is_runtime_checkpoint_valid(checkpoint_path)


def test_runtime_checkpoint_validation_never_uses_weights_only_false(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.pt"
    checkpoint_path.write_bytes(b"checkpoint")
    load_calls: list[bool] = []

    def _fake_torch_load(path, map_location="cpu", weights_only=True):  # type: ignore[no-untyped-def]
        load_calls.append(bool(weights_only))
        if weights_only:
            raise RuntimeError("unsupported validation payload")
        return {
            "model_state_dict": PlantDiseaseResNet50(num_classes=38, pretrained=False).state_dict(),
            "num_classes": 38,
            "class_names": list(REAL_CLASS_NAMES),
        }

    monkeypatch.setattr(vision_module.torch, "load", _fake_torch_load)

    assert not vision_module.is_runtime_checkpoint_valid(checkpoint_path)
    assert False not in load_calls


def test_model_manager_falls_back_to_first_enabled_model_when_default_is_invalid(tmp_path: Path) -> None:
    invalid_checkpoint = tmp_path / "invalid_runtime_checkpoint.pt"
    invalid_checkpoint.write_bytes(b"")
    fallback_checkpoint = _write_full_resnet_checkpoint(tmp_path / "fallback_runtime_checkpoint.pt")
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
                        "description": "Invalid default runtime checkpoint",
                        "accuracy": 0.0,
                        "confidence_threshold": 0.5,
                        "enabled": True,
                        "device": "cpu",
                    },
                    "fallback_local": {
                        "name": "Fallback Local Model",
                        "type": "local",
                        "model_id": str(fallback_checkpoint),
                        "description": "Valid fallback checkpoint",
                        "accuracy": 0.91,
                        "confidence_threshold": 0.5,
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
    assert manager.current_adapter is not None
    assert manager.get_current_model_key() == "fallback_local"
    assert manager.current_adapter.check_model_health()


def test_production_workflow_promotes_valid_runtime_checkpoint_and_updates_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workflow_class = _get_production_workflow_class(monkeypatch)
    workflow = workflow_class()
    workflow.runtime_checkpoint_path = tmp_path / "runtime" / "vision_resnet50.pt"
    workflow.model_config_path = tmp_path / "config" / "models.json"

    source_checkpoint = _write_full_resnet_checkpoint(tmp_path / "best_model.pt")
    promoted_checkpoint = workflow._promote_runtime_checkpoint(source_checkpoint, best_accuracy=0.928)

    config_data = json.loads(workflow.model_config_path.read_text(encoding="utf-8"))

    assert promoted_checkpoint == workflow.runtime_checkpoint_path
    assert is_runtime_checkpoint_valid(promoted_checkpoint)
    assert config_data["default_model"] == "local_resnet"
    assert config_data["models"]["local_resnet"]["enabled"] is True
    assert config_data["models"]["local_resnet"]["model_id"] == str(workflow.runtime_checkpoint_path)


def test_production_workflow_rejects_invalid_runtime_checkpoint_promotion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workflow_class = _get_production_workflow_class(monkeypatch)
    workflow = workflow_class()
    workflow.runtime_checkpoint_path = tmp_path / "runtime" / "vision_resnet50.pt"
    workflow.model_config_path = tmp_path / "config" / "models.json"

    invalid_checkpoint = tmp_path / "invalid_model.pt"
    invalid_checkpoint.write_bytes(b"")

    with pytest.raises(ValueError, match="not deployable"):
        workflow._promote_runtime_checkpoint(invalid_checkpoint, best_accuracy=0.0)

    assert not workflow.runtime_checkpoint_path.exists()
    assert not workflow.model_config_path.exists()


def test_training_monitor_json_safe_handles_circular_references() -> None:
    from training.monitor import _json_safe

    parent: dict[str, object] = {}
    child = {"parent": parent}
    parent["child"] = child

    serialized = _json_safe(parent)

    assert serialized["child"]["parent"] == "<circular-reference>"
