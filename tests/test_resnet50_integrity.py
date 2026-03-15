from __future__ import annotations

from pathlib import Path

import pytest
import torch
from PIL import Image

from plantguard.core.model_manager import PlantGuardModelManager
from plantguard.core.models import PlantDiseaseResNet50
from plantguard.core.vision import LoadCheckpointError, VisionAdapter
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
