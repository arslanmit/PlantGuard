#!/usr/bin/env python3
"""Simple test of PlantGuard vision model on sample images."""

from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import json
import logging
import sys
from pathlib import Path

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from PIL import Image

from src.core.vision import VisionAdapter

logger = logging.getLogger(__name__)


def _load_model() -> VisionAdapter | None:
    """Load the vision model."""

    model_path = "data/models/vision_resnet50.pt"
    vision_adapter = VisionAdapter(device="cpu")

    try:
        vision_adapter.load_checkpoint(model_path)
        logger.info("[DONE] Model loaded successfully")
        # Use explicit formatting to avoid logging-format interpretation issues
        logger.info(f"[SUMMARY] Model has {len(vision_adapter.class_names)} classes")
        logger.info("")
        return vision_adapter
    except Exception as e:
        logger.error("[TODO] Failed to load model: %s", e)
        return None


def _parse_prediction(predicted_class: str) -> tuple[str, str]:
    """Parse prediction into plant and disease components."""
    if "___" in predicted_class:
        pred_plant = predicted_class.split("___")[0]
        pred_disease = predicted_class.split("___")[1]
    else:
        pred_plant = "Unknown"
        pred_disease = predicted_class
    return pred_plant, pred_disease


def _check_correctness(pred_plant: str, pred_disease: str, gt_plant: str, gt_disease: str, gt_status: str) -> tuple[bool, bool, bool]:
    """Check prediction correctness."""
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
        exact_correct = any(keyword in pred_lower for keyword in disease_keywords if len(keyword) > 2)

    return plant_correct, status_correct, exact_correct


def _print_results(
    total: int,
    correct_exact: int,
    correct_plant: int,
    correct_status: int,
    vision_adapter: VisionAdapter,
) -> None:
    """Print test results summary."""
    logger.info("[SUMMARY] RESULTS SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total images tested: {total}")
    # Use f-strings with explicit float formatting and percent sign
    pct_exact = (correct_exact / total * 100) if total else 0.0
    pct_plant = (correct_plant / total * 100) if total else 0.0
    pct_status = (correct_status / total * 100) if total else 0.0
    logger.info(f"Exact matches: {correct_exact}/{total} ({pct_exact:.1f}%)")
    logger.info(f"Plant type correct: {correct_plant}/{total} ({pct_plant:.1f}%)")
    logger.info(f"Health status correct: {correct_status}/{total} ({pct_status:.1f}%)")
    logger.info("")

    # Show available classes
    logger.info("[TAG]  Available model classes:")
    for i, class_name in enumerate(vision_adapter.class_names):
        logger.info("  %2d: %s", i, class_name)


def main() -> None:
    """Test the model on sample images."""
    logging.basicConfig(level=logging.INFO)
    logger.info("[PLANT] PlantGuard Model Test")
    logger.info("=" * 50)

    # Load model
    vision_adapter = _load_model()
    if vision_adapter is None:
        return

    # Load test metadata (guarded). Exit if metadata not present.
    metadata = {"sample_images": []}
    metadata_path = Path("data/raw/sample_images_metadata.json")
    if not metadata_path.exists():
        logger.warning("sample_images_metadata.json not found; skipping sample image tests.")
        return
    try:
        with metadata_path.open(encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception:
        logger.warning("Failed to read sample_images_metadata.json; skipping sample image tests.")
        return

    # Test each image
    correct_exact = 0
    correct_plant = 0
    correct_status = 0
    total = 0

    logger.info("[SEARCH] Testing images:")
    logger.info("-" * 80)

    for sample in metadata.get("sample_images", []):
        # Prefer canonical data/raw location for images
        image_path = Path("data/raw") / sample.get("filename", "")

        if not image_path.exists():
            continue

        # Load and predict
        image = Image.open(image_path)
        predicted_class, confidence = vision_adapter.predict(image)

        # Ground truth
        gt_plant = sample["plant"]
        gt_disease = sample["disease"]
        gt_status = sample["status"]

        # Parse prediction
        pred_plant, pred_disease = _parse_prediction(predicted_class)

        # Check correctness
        plant_correct, status_correct, exact_correct = _check_correctness(pred_plant, pred_disease, gt_plant, gt_disease, gt_status)

        # Update counters
        total += 1
        if exact_correct and plant_correct:
            correct_exact += 1
        if plant_correct:
            correct_plant += 1
        if status_correct:
            correct_status += 1

        # Status icons
        plant_icon = "[LEAF]" if plant_correct else "[TODO]"
        status_icon = "[HEALTHY]" if status_correct else "[BROKEN]"
        exact_icon = "[DONE]" if (exact_correct and plant_correct) else "[TODO]"

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

    _print_results(total, correct_exact, correct_plant, correct_status, vision_adapter)


if __name__ == "__main__":
    main()
