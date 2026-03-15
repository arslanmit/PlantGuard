#!/usr/bin/env python3
"""Test different preprocessing approaches on a sample image."""

import json
import sys
from collections.abc import Callable
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plantguard.core.models import PlantDiseaseResNet50
from plantguard.core.vision import VisionAdapter


def _write_valid_resnet_checkpoint(checkpoint_path: Path) -> Path:
    class_names_path = Path(__file__).resolve().parents[1] / "data/models/class_names.json"
    with class_names_path.open(encoding="utf-8") as handle:
        class_names = json.load(handle)

    torch.manual_seed(13)
    model = PlantDiseaseResNet50(num_classes=len(class_names), pretrained=False)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "num_classes": len(class_names),
        "class_names": class_names,
        "model_version": "1.0.0",
        "training_metadata": {"accuracy": 0.91, "architecture": "resnet50"},
    }
    torch.save(checkpoint, checkpoint_path)
    return checkpoint_path


def test_different_preprocessing(tmp_path: Path) -> None:
    """Test different preprocessing approaches."""
    # Test image - replace with an available image path or skip if absent
    test_image_path = "data/raw/<your_image>.jpg"
    if not Path(test_image_path).exists():
        print(f"[WARNING]  Test image not found: {test_image_path} - skipping preprocessing test")
        return

    vision_adapter = VisionAdapter(device="cpu")
    vision_adapter.load_checkpoint(str(_write_valid_resnet_checkpoint(tmp_path / "vision_resnet50.pt")))
    image = Image.open(test_image_path)

    print(f"[SEARCH] Testing preprocessing on: {test_image_path}")
    print(f"Original image size: {image.size}")
    print(f"Original image mode: {image.mode}")
    print()

    # Different preprocessing approaches
    preprocessing_methods: dict[str, Callable[[Image.Image], torch.Tensor]] = {
        "Current (224x224)": transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        ),
        "Larger resize (256->224)": transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        ),
        "No normalization": transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor()]),
        "Different normalization": transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ]
        ),
    }

    for method_name, transform in preprocessing_methods.items():
        try:
            # Apply preprocessing
            rgb_image = image.convert("RGB") if image.mode != "RGB" else image

            tensor = transform(rgb_image)
            input_batch = tensor.unsqueeze(0)

            # Get prediction
            model = vision_adapter.model
            assert model is not None, "Model is not loaded"
            model.eval()
            with torch.no_grad():
                outputs = model(input_batch)
                probabilities = F.softmax(outputs, dim=1)
                confidence, predicted_idx = torch.max(probabilities, 1)

                predicted_class = vision_adapter.class_names[int(predicted_idx.item())]
                confidence_score = float(confidence.item())

            print(f"[SUMMARY] {method_name}:")
            print(f"   Prediction: {predicted_class}")
            print(f"   Confidence: {confidence_score:.4f}")
            print()

        except Exception as e:
            print(f"[TODO] {method_name}: Failed - {e}")
            print()


def show_top_predictions(model_path: str | None = None) -> None:
    """Show top 5 predictions for a sample image."""
    vision_adapter = VisionAdapter(device="cpu")
    if model_path is None:
        raise RuntimeError("show_top_predictions requires a validated checkpoint path")
    vision_adapter.load_checkpoint(model_path)

    test_image_path = "data/raw/<your_image>.jpg"
    if not Path(test_image_path).exists():
        print(f"[WARNING]  Test image not found: {test_image_path} - skipping top predictions")
        return
    image = Image.open(test_image_path)

    # Preprocess
    tensor = vision_adapter.preprocess_image(image)
    input_batch = tensor.unsqueeze(0)

    # Get all predictions
    model = vision_adapter.model
    assert model is not None, "Model is not loaded"
    model.eval()
    with torch.no_grad():
        outputs = model(input_batch)
        probabilities = F.softmax(outputs, dim=1)

        # Get top 5
        top5_prob, top5_idx = torch.topk(probabilities, 5, dim=1)

        print(f"[ACHIEVEMENT] Top 5 predictions for {test_image_path}:")
        print("   (Ground truth: Apple - Apple Scab)")
        print()

        for i in range(5):
            idx = int(top5_idx[0][i].item())
            prob = float(top5_prob[0][i].item())
            class_name = vision_adapter.class_names[idx]
            print(f"   {i + 1}. {class_name} ({prob:.4f})")


def main() -> None:
    print("[TEST] PlantGuard Preprocessing Test")
    print("=" * 60)

    test_different_preprocessing(Path("tmp_preprocessing"))

    print("=" * 60)
    show_top_predictions(str(_write_valid_resnet_checkpoint(Path("tmp_preprocessing") / "vision_resnet50.pt")))


if __name__ == "__main__":
    main()
