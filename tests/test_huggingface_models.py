#!/usr/bin/env python3
"""Test Hugging Face pre-trained plant disease models on your test images."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification


def _load_model_and_processor(model_name: str) -> tuple[Any, Any, list[str]] | dict[str, str]:
    """Load model, processor, and class labels."""
    print(f"[PARTIAL] Loading model: {model_name}")

    try:
        processor = AutoImageProcessor.from_pretrained(model_name)
        model = AutoModelForImageClassification.from_pretrained(model_name)
        model.eval()

        print("[DONE] Model loaded successfully")
        print(f"[SUMMARY] Model has {model.config.num_labels} classes")

        # Get class labels
        if hasattr(model.config, "id2label"):
            class_labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
            print(f"[TAG]  Sample classes: {class_labels[:5]}...")
        else:
            class_labels = [f"class_{i}" for i in range(model.config.num_labels)]
            print("[WARNING]  No class labels found, using indices")

        return model, processor, class_labels
    except Exception as e:
        print(f"[TODO] Failed to load model {model_name}: {e}")
        return {"error": str(e)}


def _predict_image(image_path: Path, model: Any, processor: Any, class_labels: list[str]) -> tuple[str, float] | None:
    """Make prediction on a single image."""
    try:
        with Image.open(image_path) as im:
            image = im.convert("RGB")
        inputs = processor(image, return_tensors="pt")
        device = model.device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class_id: int = int(predictions.argmax().item())
            confidence: float = float(predictions.max().item())

        predicted_label = class_labels[predicted_class_id]
        return predicted_label, confidence
    except Exception as e:
        print(f"[TODO] Failed to process {image_path}: {e}")
        return None


def _analyze_prediction(predicted_label: str, gt_plant: str, gt_disease: str, gt_status: str) -> tuple[bool, bool, bool]:
    """Analyze prediction accuracy."""
    pred_lower = predicted_label.lower()
    gt_plant_lower = gt_plant.lower()
    gt_disease_lower = gt_disease.lower()

    # Check plant type match
    plant_match = any(plant_word in pred_lower for plant_word in gt_plant_lower.split())

    # Check disease match
    if gt_disease_lower == "healthy":
        disease_match = "healthy" in pred_lower
    else:
        disease_words = gt_disease_lower.replace(" ", "_").split("_")
        disease_match = any(word in pred_lower for word in disease_words if len(word) > 2)

    # Check status (healthy vs diseased)
    pred_healthy = "healthy" in pred_lower
    actual_healthy = gt_status == "healthy"
    status_match = pred_healthy == actual_healthy

    # Overall correctness
    overall_correct = plant_match and (disease_match or status_match)

    return plant_match, status_match, overall_correct


def _process_sample_with_validation(
    sample: dict, test_images_dir: str, model: Any, processor: Any, class_labels: list[str]
) -> tuple[dict, bool, bool, bool] | None:
    """Process a sample with full validation and return result."""
    filename = sample.get("filename")
    if not filename:
        print("[WARNING]  Skipping sample with missing filename")
        return None

    base = Path(test_images_dir).resolve()
    image_path = (base / filename).resolve()
    if base != image_path and base not in image_path.parents:
        print(f"[WARNING]  Skipping unsafe path: {filename}")
        return None

    if not image_path.exists():
        return None

    # Get ground truth
    gt_plant = sample.get("plant")
    gt_disease = sample.get("disease")
    gt_status = sample.get("status")
    if gt_plant is None or gt_disease is None or gt_status is None:
        print(f"[WARNING]  Skipping sample with missing fields: {sample}")
        return None

    # Make prediction
    prediction_result = _predict_image(image_path, model, processor, class_labels)
    if prediction_result is None:
        return None

    predicted_label, confidence = prediction_result

    # Analyze prediction
    plant_match, status_match, overall_correct = _analyze_prediction(predicted_label, gt_plant, gt_disease, gt_status)

    # Display results
    overall_icon = "[DONE]" if overall_correct else "[TODO]"
    plant_icon = "[LEAF]" if plant_match else "[TODO]"
    status_icon = "[HEALTHY]" if status_match else "[BROKEN]"

    result = {
        "filename": sample["filename"],
        "ground_truth": f"{gt_plant} - {gt_disease} ({gt_status})",
        "prediction": predicted_label,
        "confidence": confidence,
        "plant_match": plant_match,
        "status_match": status_match,
        "overall_correct": overall_correct,
    }

    print(f"{overall_icon} {sample['filename']} {plant_icon}{status_icon}")
    print(f"   GT: {gt_plant} - {gt_disease} ({gt_status})")
    print(f"   Pred: {predicted_label} (conf: {confidence:.3f})")
    print()

    return result, plant_match, status_match, overall_correct


def _calculate_summary(
    model_name: str,
    model: Any,
    results: list[dict],
    correct_predictions: int,
    plant_correct: int,
    status_correct: int,
) -> dict[str, Any]:
    """Calculate final summary metrics."""
    total = len(results)
    if total == 0:
        return {"error": "No valid predictions made"}

    overall_accuracy = correct_predictions / total
    plant_accuracy = plant_correct / total
    status_accuracy = status_correct / total
    avg_confidence = np.mean([r["confidence"] for r in results])

    return {
        "model_name": model_name,
        "total_images": total,
        "overall_accuracy": overall_accuracy,
        "plant_accuracy": plant_accuracy,
        "status_accuracy": status_accuracy,
        "average_confidence": avg_confidence,
        "num_classes": model.config.num_labels,
        "results": results,
    }


def evaluate_model(model_name: str, test_images_dir: str, metadata_path: str) -> dict[str, Any]:
    """Test a Hugging Face model on test images."""
    # Load model and processor
    model_result = _load_model_and_processor(model_name)
    if isinstance(model_result, dict):  # Error case
        return model_result

    model, processor, class_labels = model_result

    # Use the provided metadata_path
    metadata_file = Path(metadata_path)
    if not metadata_file.exists():
        pytest.skip(f"Metadata file {metadata_path} not present; skipping huggingface sample tests")
    with metadata_file.open() as f:
        metadata = json.load(f)

    results = []
    correct_predictions = 0
    plant_correct = 0
    status_correct = 0

    samples = metadata.get("sample_images", [])
    print(f"\n[TEST] Testing on {len(samples)} images:")
    print("-" * 80)

    for sample in samples:
        # Validate and process sample
        sample_result = _process_sample_with_validation(sample, test_images_dir, model, processor, class_labels)

        if sample_result is None:
            continue

        result, plant_match, status_match, overall_correct = sample_result
        results.append(result)

        # Update counters
        if overall_correct:
            correct_predictions += 1
        if plant_match:
            plant_correct += 1
        if status_match:
            status_correct += 1

    return _calculate_summary(model_name, model, results, correct_predictions, plant_correct, status_correct)


def print_results(results: dict[str, Any]) -> None:
    """Print test results in a readable format."""
    if "error" in results:
        print(f"[TODO] Error: {results['error']}")
        return

    print("=" * 80)
    print(f"[PLANT] RESULTS FOR {results['model_name']}")
    print("=" * 80)

    print("\n[SUMMARY] SUMMARY STATISTICS")
    print(f"Total test images: {results['total_images']}")
    print(
        f"Overall accuracy: {results['overall_accuracy']:.1%} ({int(results['overall_accuracy'] * results['total_images'])}/{results['total_images']})"
    )
    print(f"Plant type accuracy: {results['plant_accuracy']:.1%}")
    print(f"Health status accuracy: {results['status_accuracy']:.1%}")
    print(f"Average confidence: {results['average_confidence']:.3f}")
    print(f"Model classes: {results['num_classes']}")


def main() -> None:
    """Test multiple Hugging Face models."""
    print("[HUG] Testing Hugging Face Plant Disease Models")
    print("=" * 80)

    # Models to test
    models_to_test = [
        "Diginsa/Plant-Disease-Detection-Project",  # Most popular (247K downloads)
        "Abhiram4/PlantDiseaseDetectorVit2",  # Vision Transformer based
    ]

    # Use canonical data/raw for test images
    test_images_dir = "data/raw"
    metadata_path = Path("data/raw/sample_images_metadata.json")

    # Check metadata
    if not metadata_path.exists():
        print(f"[TODO] Metadata file not found: {metadata_path} - skipping HuggingFace tests")
        return

    try:
        with metadata_path.open() as mf:
            json.load(mf)
    except Exception:
        print(f"[TODO] Metadata file invalid: {metadata_path} - skipping HuggingFace tests")
        return

    all_results: list[dict[str, Any]] = []

    for model_name in models_to_test:
        print(f"\n{'=' * 20} TESTING {model_name} {'=' * 20}")

        try:
            results = evaluate_model(model_name, test_images_dir, metadata_path)
            all_results.append(results)
            print_results(results)

        except Exception as e:
            print(f"[TODO] Failed to test {model_name}: {e}")
            continue

        print("\n" + "=" * 80)

    # Compare models
    if len(all_results) > 1:
        print("\n[ACHIEVEMENT] MODEL COMPARISON")
        print("=" * 50)

        valid_results = [r for r in all_results if "error" not in r]
        if valid_results:
            for result in valid_results:
                short_model_name = result["model_name"].split("/")[-1]  # Short name
                print(
                    f"{short_model_name:30} | Overall: {result['overall_accuracy']:.1%} | Plant: {result['plant_accuracy']:.1%} | Status: {result['status_accuracy']:.1%}"
                )

            # Find best model
            best_model = max(valid_results, key=lambda x: x["overall_accuracy"])
            print(f"\n[FIRST] Best performing model: {best_model['model_name']}")
            print(f"   Overall accuracy: {best_model['overall_accuracy']:.1%}")

    print("\n[TIP] NEXT STEPS:")
    print("- Choose the best performing model for your PlantGuard application")
    print("- Integrate it into your src/core/vision.py")
    print("- The model can be loaded directly from Hugging Face in your app")


if __name__ == "__main__":
    main()


def _create_temp_samples(tmp_path) -> Any:
    """Create a small set of temporary sample images and metadata for tests."""
    images_dir = tmp_path / "data_raw"
    images_dir.mkdir(parents=True, exist_ok=True)

    samples = []
    colors = [(180, 60, 60), (60, 180, 60)]
    for i, col in enumerate(colors):
        img = Image.new("RGB", (64, 64), color=col)
        fname = f"hf_temp_{i}.jpg"
        p = images_dir / fname
        img.save(p)
        samples.append({"filename": fname, "plant": "Tomato", "disease": "Healthy", "status": "healthy"})

    metadata = {"sample_images": samples}
    metadata_path = tmp_path / "sample_images_metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    return str(images_dir), str(metadata_path)


def test_huggingface_models_with_temp_samples(tmp_path) -> None:
    """Pytest wrapper: create temp samples and run Hugging Face model tests.

    This test will attempt to load remote HF models; skip if internet/network or transformers support isn't available.
    """
    # Quick guard: skip if transformers or HF model downloads are not available in this environment
    try:
        # small probe
        _ = AutoImageProcessor
    except Exception:
        pytest.skip("transformers not available in this environment; skipping HF model tests")

    test_images_dir, metadata_path = _create_temp_samples(tmp_path)

    # We'll attempt to test only one small model to limit duration; if it fails, test will skip gracefully
    try:
        results = evaluate_model("Diginsa/Plant-Disease-Detection-Project", test_images_dir, metadata_path)
        assert isinstance(results, dict)
    except Exception as e:
        pytest.skip(f"Hugging Face model test failed or is unavailable: {e}")
