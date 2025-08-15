#!/usr/bin/env python3
"""Fix PlantGuard model issues.

This script diagnoses and fixes common model performance issues.
"""

import json
import sys
from pathlib import Path
from typing import Any

import torch
from PIL import Image

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from src.core.vision import VisionAdapter
from src.utils.logging import setup_logger

logger = setup_logger("fix_model", log_file="logs/fix_model.log")


def check_model_file(model_path: str) -> dict[str, Any]:
    """Check model file integrity and contents."""
    logger.info("Checking model file: %s", model_path)

    model_file = Path(model_path)
    if not model_file.exists():
        return {"error": f"Model file not found: {model_path}"}

    try:
        # Load checkpoint to inspect
        checkpoint = torch.load(model_path, map_location="cpu")

        info = {
            "file_size_mb": model_file.stat().st_size / (1024 * 1024),
            "keys": list(checkpoint.keys()),
            "num_classes": checkpoint.get("num_classes", "unknown"),
            "class_names_count": len(checkpoint.get("class_names", [])),
            "has_model_state": "model_state_dict" in checkpoint,
        }

        if "class_names" in checkpoint:
            info["sample_classes"] = checkpoint["class_names"][:5]

        logger.info("Model file info: %s", info)
        return info

    except Exception as e:
        logger.exception("Failed to load model file")
        return {"error": f"Failed to load model: {e}"}


def test_single_prediction(vision_adapter: VisionAdapter, test_image_path: str) -> dict[str, Any]:
    """Test a single prediction to diagnose issues."""
    logger.info("Testing prediction on: %s", test_image_path)

    image_path = Path(test_image_path)
    if not image_path.exists():
        return {"error": f"Test image not found: {test_image_path}"}

    try:
        # Load image
        image = Image.open(image_path)
        logger.info("Image loaded: %s, mode: %s, size: %s", image_path.name, image.mode, image.size)

        # Test preprocessing
        tensor = vision_adapter.preprocess_image(image)
        logger.info("Preprocessing successful, tensor shape: %s", tensor.shape)

        # Test prediction
        predicted_class, confidence = vision_adapter.predict(image)

        result = {
            "image_path": str(image_path),
            "image_mode": image.mode,
            "image_size": image.size,
            "tensor_shape": list(tensor.shape),
            "predicted_class": predicted_class,
            "confidence": confidence,
            "readable_name": vision_adapter.get_readable_name(predicted_class),
            "plant_type": vision_adapter.get_plant_type(predicted_class),
            "is_healthy": vision_adapter.is_healthy(predicted_class),
        }

        logger.info("Prediction result: %s", result)
        return result

    except Exception as e:
        logger.exception("Prediction failed")
        return {"error": f"Prediction failed: {e}"}


def diagnose_low_confidence(vision_adapter: VisionAdapter) -> dict[str, Any]:
    """Diagnose why the model has low confidence scores."""
    logger.info("Diagnosing low confidence issues")

    model_info = vision_adapter.get_model_info()

    # Check if model is properly loaded
    if not model_info["is_loaded"]:
        return {"error": "Model not loaded"}

    # Check class mapping
    has_mapping = model_info["has_readable_mapping"]
    num_classes = model_info["num_classes"]

    diagnosis = {
        "model_loaded": model_info["is_loaded"],
        "num_classes": num_classes,
        "has_class_mapping": has_mapping,
        "device": model_info["device"],
        "class_names_sample": model_info["class_names"][:5] if model_info["class_names"] else [],
    }

    # Check if model architecture matches expected classes
    expected_classes = 38  # PlantVillage dataset standard
    if num_classes != expected_classes:
        diagnosis["warning"] = f"Model has {num_classes} classes, expected {expected_classes}"

    logger.info("Diagnosis: %s", diagnosis)
    return diagnosis


def fix_class_mapping(vision_adapter: VisionAdapter) -> bool:
    """Fix class mapping issues."""
    logger.info("Fixing class mapping")

    mapping_path = "data/knowledge_base/plantvillage_classes.json"
    if not Path(mapping_path).exists():
        logger.error("Class mapping file not found: %s", mapping_path)
        return False

    try:
        vision_adapter.load_class_mapping(mapping_path)
        logger.info("Class mapping loaded successfully")
        return True
    except Exception:
        logger.exception("Failed to load class mapping")
        return False


def create_test_report(model_path: str, test_images_dir: str) -> dict[str, Any]:
    """Create comprehensive test report."""
    logger.info("Creating test report")

    report = {
        "timestamp": str(Path().cwd()),
        "model_path": model_path,
        "test_images_dir": test_images_dir,
    }

    # Check model file
    report["model_check"] = check_model_file(model_path)
    if "error" in report["model_check"]:
        return report

    # Initialize vision adapter
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        vision_adapter = VisionAdapter(device=device)
        vision_adapter.load_checkpoint(model_path)

        # Fix class mapping
        mapping_fixed = fix_class_mapping(vision_adapter)
        report["class_mapping_fixed"] = mapping_fixed

        # Diagnose issues
        report["diagnosis"] = diagnose_low_confidence(vision_adapter)

        # Test on sample images
        test_images = [
            "data/pictures/apple_healthy_sample.jpg",
            "data/pictures/tomato_bacterial_spot_sample.jpg",
            "data/pictures/corn_common_rust_sample.jpg",
        ]

        report["sample_predictions"] = []
        for test_image in test_images:
            if Path(test_image).exists():
                result = test_single_prediction(vision_adapter, test_image)
                report["sample_predictions"].append(result)

        # Model info
        report["model_info"] = vision_adapter.get_model_info()

    except Exception as e:
        logger.exception("Failed to create test report")
        report["error"] = f"Failed to initialize model: {e}"

    return report


def print_report(report: dict[str, Any]) -> None:
    """Print diagnostic report."""
    print("\n🔍 PLANTGUARD MODEL DIAGNOSTIC REPORT")
    print("=" * 50)

    # Model file check
    model_check = report.get("model_check", {})
    if "error" in model_check:
        print(f"❌ Model File: {model_check['error']}")
        return
    else:
        print(f"✅ Model File: {model_check['file_size_mb']:.1f}MB, {model_check['num_classes']} classes")

    # Class mapping
    mapping_fixed = report.get("class_mapping_fixed", False)
    print(f"{'✅' if mapping_fixed else '❌'} Class Mapping: {'Fixed' if mapping_fixed else 'Failed'}")

    # Diagnosis
    diagnosis = report.get("diagnosis", {})
    if diagnosis:
        print("📊 Model Status:")
        print(f"   - Loaded: {diagnosis.get('model_loaded', False)}")
        print(f"   - Classes: {diagnosis.get('num_classes', 'unknown')}")
        print(f"   - Device: {diagnosis.get('device', 'unknown')}")
        print(f"   - Has Mapping: {diagnosis.get('has_class_mapping', False)}")

        if "warning" in diagnosis:
            print(f"   ⚠️  {diagnosis['warning']}")

    # Sample predictions
    predictions = report.get("sample_predictions", [])
    if predictions:
        print("\n🧪 Sample Predictions:")
        for pred in predictions:
            if "error" in pred:
                print(f"   ❌ {Path(pred.get('image_path', 'unknown')).name}: {pred['error']}")
            else:
                name = Path(pred["image_path"]).name
                confidence = pred["confidence"]
                predicted = pred["predicted_class"]
                print(f"   {'✅' if confidence > 0.5 else '⚠️ '} {name}: {predicted} ({confidence:.3f})")


def main() -> None:
    """Main diagnostic function."""
    print("🔧 Starting PlantGuard model diagnostics...")

    # Paths
    model_path = "data/models/vision_resnet50.pt"
    test_images_dir = "data/pictures"

    # Check if model exists
    if not Path(model_path).exists():
        print(f"❌ Model file not found: {model_path}")
        print("   Run 'make setup' to download the model")
        return

    # Create diagnostic report
    report = create_test_report(model_path, test_images_dir)

    # Print report
    print_report(report)

    # Save report
    report_file = "model_diagnostic_report.json"
    with Path(report_file).open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📄 Full report saved to: {report_file}")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if "error" in report.get("model_check", {}):
        print("   1. Re-download the model with 'make setup'")
    elif not report.get("class_mapping_fixed", False):
        print("   1. Check class mapping file exists")
    else:
        predictions = report.get("sample_predictions", [])
        low_confidence = any(pred.get("confidence", 0) < 0.5 for pred in predictions if "confidence" in pred)
        if low_confidence:
            print("   1. Model may need retraining")
            print("   2. Check if model architecture matches training data")
            print("   3. Verify preprocessing pipeline")


if __name__ == "__main__":
    main()
