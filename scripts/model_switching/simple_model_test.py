#!/usr/bin/env python3
"""Simple test of PlantGuard vision model on sample images."""

import json
import sys
from pathlib import Path

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from PIL import Image

from src.core.vision import VisionAdapter


def main():
    """Test the model on sample images."""
    print("🌱 PlantGuard Model Test")
    print("=" * 50)

    # Load model
    model_path = "data/models/vision_resnet50.pt"
    vision_adapter = VisionAdapter(device="cpu")

    try:
        vision_adapter.load_checkpoint(model_path)
        print("✅ Model loaded successfully")
        print(f"📊 Model has {len(vision_adapter.class_names)} classes")
        print()
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    # Load test metadata
    with open("data/pictures/sample_images_metadata.json") as f:
        metadata = json.load(f)

    # Test each image
    correct_exact = 0
    correct_plant = 0
    correct_status = 0
    total = 0

    print("🔍 Testing images:")
    print("-" * 80)

    for sample in metadata["sample_images"]:
        image_path = Path("data/pictures") / sample["filename"]

        if not image_path.exists():
            continue

        # Load and predict
        image = Image.open(image_path)
        predicted_class, confidence = vision_adapter.predict(image)

        # Ground truth
        gt_plant = sample["plant"]
        gt_disease = sample["disease"]
        gt_status = sample["status"]

        # Extract plant from prediction
        if "___" in predicted_class:
            pred_plant = predicted_class.split("___")[0]
            pred_disease = predicted_class.split("___")[1]
        else:
            pred_plant = "Unknown"
            pred_disease = predicted_class

        # Check correctness
        plant_correct = pred_plant.lower().replace("_", " ").replace(",", "") in gt_plant.lower()
        status_correct = ("healthy" in pred_disease.lower()) == (gt_status == "healthy")

        # For exact match, we need to be more flexible
        exact_correct = False
        if gt_disease == "Healthy":
            exact_correct = "healthy" in pred_disease.lower()
        else:
            # Check if disease names match (allowing for variations)
            disease_keywords = gt_disease.lower().replace(" ", "_").split("_")
            pred_lower = pred_disease.lower()
            exact_correct = any(
                keyword in pred_lower for keyword in disease_keywords if len(keyword) > 2
            )

        # Update counters
        total += 1
        if exact_correct and plant_correct:
            correct_exact += 1
        if plant_correct:
            correct_plant += 1
        if status_correct:
            correct_status += 1

        # Status icons
        plant_icon = "🌿" if plant_correct else "❌"
        status_icon = "💚" if status_correct else "💔"
        exact_icon = "✅" if (exact_correct and plant_correct) else "❌"

        print(f"{exact_icon} {sample['filename']}")
        print(f"   GT: {gt_plant} - {gt_disease} ({gt_status})")
        print(
            f"   Pred: {pred_plant} - {pred_disease} (conf: {confidence:.3f}) {plant_icon}{status_icon}"
        )
        print()

    # Summary
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total images tested: {total}")
    print(f"Exact matches: {correct_exact}/{total} ({correct_exact / total:.1%})")
    print(f"Plant type correct: {correct_plant}/{total} ({correct_plant / total:.1%})")
    print(f"Health status correct: {correct_status}/{total} ({correct_status / total:.1%})")
    print()

    # Show available classes
    print("🏷️  Available model classes:")
    for i, class_name in enumerate(vision_adapter.class_names):
        print(f"  {i:2d}: {class_name}")


if __name__ == "__main__":
    main()
