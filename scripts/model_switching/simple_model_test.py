#!/usr/bin/env python3
"""Simple test of PlantGuard vision model on sample images."""

import json
import logging
import sys
from pathlib import Path

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from PIL import Image

from src.core.vision import VisionAdapter

logger = logging.getLogger(__name__)


def main() -> None:
    """Test the model on sample images."""
    logging.basicConfig(level=logging.INFO)
    logger.info("🌱 PlantGuard Model Test")
    logger.info("=" * 50)

    # Load model
    model_path = "data/models/vision_resnet50.pt"
    vision_adapter = VisionAdapter(device="cpu")

    try:
        vision_adapter.load_checkpoint(model_path)
        logger.info("✅ Model loaded successfully")
        logger.info("📊 Model has %s classes", len(vision_adapter.class_names))
        logger.info("")
    except Exception as e:
        logger.error("❌ Failed to load model: %s", e)
        return

    # Load test metadata
    with open("data/pictures/sample_images_metadata.json") as f:
        metadata = json.load(f)

    # Test each image
    correct_exact = 0
    correct_plant = 0
    correct_status = 0
    total = 0

    logger.info("🔍 Testing images:")
    logger.info("-" * 80)

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

        logger.info("%s %s", exact_icon, sample["filename"])
        logger.info("   GT: %s - %s (%s)", gt_plant, gt_disease, gt_status)
        logger.info(
            "   Pred: %s - %s (conf: %.3f) %s%s",
            pred_plant,
            pred_disease,
            confidence,
            plant_icon,
            status_icon,
        )
        logger.info("")

    # Summary
    logger.info("📊 RESULTS SUMMARY")
    logger.info("=" * 50)
    logger.info("Total images tested: %s", total)
    logger.info("Exact matches: %s/%s (%.1%%)", correct_exact, total, correct_exact / total * 100)
    logger.info(
        "Plant type correct: %s/%s (%.1%%)", correct_plant, total, correct_plant / total * 100
    )
    logger.info(
        "Health status correct: %s/%s (%.1%%)", correct_status, total, correct_status / total * 100
    )
    logger.info("")

    # Show available classes
    logger.info("🏷️  Available model classes:")
    for i, class_name in enumerate(vision_adapter.class_names):
        logger.info("  %2d: %s", i, class_name)


if __name__ == "__main__":
    main()
