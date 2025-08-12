#!/usr/bin/env python3
"""Test Hugging Face pre-trained plant disease models on your test images."""

import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification


def test_model(model_name: str, test_images_dir: str, metadata_path: str) -> dict:
    """Test a Hugging Face model on test images."""
    print(f"🔄 Loading model: {model_name}")

    try:
        # Load model and processor
        processor = AutoImageProcessor.from_pretrained(model_name)
        model = AutoModelForImageClassification.from_pretrained(model_name)

        print("✅ Model loaded successfully")
        print(f"📊 Model has {model.config.num_labels} classes")

        # Get class labels
        if hasattr(model.config, "id2label"):
            class_labels = [model.config.id2label[i] for i in range(model.config.num_labels)]
            print(f"🏷️  Sample classes: {class_labels[:5]}...")
        else:
            class_labels = [f"class_{i}" for i in range(model.config.num_labels)]
            print("⚠️  No class labels found, using indices")

    except Exception as e:
        print(f"❌ Failed to load model {model_name}: {e}")
        return {"error": str(e)}

    # Load test metadata
    with open(metadata_path) as f:
        metadata = json.load(f)

    results = []
    correct_predictions = 0
    plant_correct = 0
    status_correct = 0

    print(f"\n🧪 Testing on {len(metadata['sample_images'])} images:")
    print("-" * 80)

    for sample in metadata["sample_images"]:
        image_path = Path(test_images_dir) / sample["filename"]

        if not image_path.exists():
            continue

        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            inputs = processor(image, return_tensors="pt")

            # Get prediction
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class_id = predictions.argmax().item()
                confidence = predictions.max().item()

            predicted_label = class_labels[predicted_class_id]

            # Ground truth
            gt_plant = sample["plant"]
            gt_disease = sample["disease"]
            gt_status = sample["status"]

            # Analyze prediction
            pred_lower = predicted_label.lower()
            gt_plant_lower = gt_plant.lower()
            gt_disease_lower = gt_disease.lower()

            # Check plant type match
            plant_match = any(plant_word in pred_lower for plant_word in gt_plant_lower.split())

            # Check disease match
            if gt_disease.lower() == "healthy":
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

            if overall_correct:
                correct_predictions += 1
            if plant_match:
                plant_correct += 1
            if status_match:
                status_correct += 1

            # Icons for display
            overall_icon = "✅" if overall_correct else "❌"
            plant_icon = "🌿" if plant_match else "❌"
            status_icon = "💚" if status_match else "💔"

            result = {
                "filename": sample["filename"],
                "ground_truth": f"{gt_plant} - {gt_disease} ({gt_status})",
                "prediction": predicted_label,
                "confidence": confidence,
                "plant_match": plant_match,
                "status_match": status_match,
                "overall_correct": overall_correct,
            }
            results.append(result)

            print(f"{overall_icon} {sample['filename']} {plant_icon}{status_icon}")
            print(f"   GT: {gt_plant} - {gt_disease} ({gt_status})")
            print(f"   Pred: {predicted_label} (conf: {confidence:.3f})")
            print()

        except Exception as e:
            print(f"❌ Failed to process {image_path}: {e}")
            continue

    # Calculate metrics
    total = len(results)
    if total > 0:
        overall_accuracy = correct_predictions / total
        plant_accuracy = plant_correct / total
        status_accuracy = status_correct / total
        avg_confidence = np.mean([r["confidence"] for r in results])

        summary = {
            "model_name": model_name,
            "total_images": total,
            "overall_accuracy": overall_accuracy,
            "plant_accuracy": plant_accuracy,
            "status_accuracy": status_accuracy,
            "average_confidence": avg_confidence,
            "num_classes": model.config.num_labels,
            "results": results,
        }

        return summary
    else:
        return {"error": "No valid predictions made"}


def print_results(results: dict) -> None:
    """Print test results in a readable format."""
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return

    print("=" * 80)
    print(f"🌱 RESULTS FOR {results['model_name']}")
    print("=" * 80)

    print("\n📊 SUMMARY STATISTICS")
    print(f"Total test images: {results['total_images']}")
    print(
        f"Overall accuracy: {results['overall_accuracy']:.1%} ({int(results['overall_accuracy'] * results['total_images'])}/{results['total_images']})"
    )
    print(f"Plant type accuracy: {results['plant_accuracy']:.1%}")
    print(f"Health status accuracy: {results['status_accuracy']:.1%}")
    print(f"Average confidence: {results['average_confidence']:.3f}")
    print(f"Model classes: {results['num_classes']}")


def main():
    """Test multiple Hugging Face models."""
    print("🤗 Testing Hugging Face Plant Disease Models")
    print("=" * 80)

    # Models to test
    models_to_test = [
        "Diginsa/Plant-Disease-Detection-Project",  # Most popular (247K downloads)
        "Abhiram4/PlantDiseaseDetectorVit2",  # Vision Transformer based
    ]

    test_images_dir = "data/pictures"
    metadata_path = "data/pictures/sample_images_metadata.json"

    # Check if files exist
    if not Path(metadata_path).exists():
        print(f"❌ Metadata file not found: {metadata_path}")
        return

    if not Path(test_images_dir).exists():
        print(f"❌ Test images directory not found: {test_images_dir}")
        return

    all_results = []

    for model_name in models_to_test:
        print(f"\n{'=' * 20} TESTING {model_name} {'=' * 20}")

        try:
            results = test_model(model_name, test_images_dir, metadata_path)
            all_results.append(results)
            print_results(results)

        except Exception as e:
            print(f"❌ Failed to test {model_name}: {e}")
            continue

        print("\n" + "=" * 80)

    # Compare models
    if len(all_results) > 1:
        print("\n🏆 MODEL COMPARISON")
        print("=" * 50)

        valid_results = [r for r in all_results if "error" not in r]
        if valid_results:
            for result in valid_results:
                model_name = result["model_name"].split("/")[-1]  # Short name
                print(
                    f"{model_name:30} | Overall: {result['overall_accuracy']:.1%} | Plant: {result['plant_accuracy']:.1%} | Status: {result['status_accuracy']:.1%}"
                )

            # Find best model
            best_model = max(valid_results, key=lambda x: x["overall_accuracy"])
            print(f"\n🥇 Best performing model: {best_model['model_name']}")
            print(f"   Overall accuracy: {best_model['overall_accuracy']:.1%}")

    print("\n💡 NEXT STEPS:")
    print("- Choose the best performing model for your PlantGuard application")
    print("- Integrate it into your src/core/vision.py")
    print("- The model can be loaded directly from Hugging Face in your app")


if __name__ == "__main__":
    main()
