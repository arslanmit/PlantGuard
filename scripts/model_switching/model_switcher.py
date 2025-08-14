#!/usr/bin/env python3
"""Easy model switcher for PlantGuard - Switch between models with simple commands."""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from src.core.model_manager import PlantGuardModelManager


def list_models(manager: "PlantGuardModelManager") -> None:
    """List all available models."""
    models = manager.list_available_models()

    print("🤖 Available PlantGuard Models:")
    print("=" * 60)

    for model in models:
        status = (
            "🟢 CURRENT"
            if model["is_current"]
            else "⚪ Available"
            if model["enabled"]
            else "🔴 Disabled"
        )
        accuracy = f"{model['accuracy']:.1%}" if model["accuracy"] > 0 else "Unknown"

        print(f"\n📋 {model['id']}")
        print(f"   Name: {model['name']}")
        print(f"   Type: {model['type']}")
        print(f"   Accuracy: {accuracy}")
        print(f"   Status: {status}")
        print(f"   Description: {model['description']}")


def switch_model(manager: "PlantGuardModelManager", model_id: str) -> None:
    """Switch to a specific model."""
    print(f"🔄 Switching to model: {model_id}")

    if manager.switch_model(model_id):
        print(f"✅ Successfully switched to: {model_id}")

        # Show current model info
        info = manager.get_current_model_info()
        print("\n📊 Current Model Info:")
        print(f"   Name: {info['name']}")
        print(f"   Type: {info['type']}")
        print(f"   Classes: {info['num_classes']}")
        print(f"   Device: {info['device']}")
        print(f"   Accuracy: {info['accuracy']:.1%}")
    else:
        print(f"❌ Failed to switch to model: {model_id}")


def test_model(manager: "PlantGuardModelManager", image_path: str) -> None:
    """Test current model on an image."""
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return

    try:
        image = Image.open(image_path)
        result = manager.get_readable_prediction(image)

        print(f"🔍 Testing: {Path(image_path).name}")
        print("=" * 50)
        print(f"🌿 Plant Type: {result['plant_type']}")
        print(f"🦠 Disease: {result['disease']}")
        print(f"💚 Healthy: {'Yes' if result['is_healthy'] else 'No'}")
        print(f"📊 Confidence: {result['confidence_percentage']}")
        print(f"💡 Recommendation: {result['recommendation']}")
        print(f"🤖 Model: {result['model_info']['model_name']}")

    except Exception as e:
        print(f"❌ Failed to test image: {e}")


def quick_test(manager: "PlantGuardModelManager") -> None:
    """Quick test on sample images."""
    test_images = [
        "data/pictures/apple_scab_sample.jpg",
        "data/pictures/tomato_healthy_sample.jpg",
        "data/pictures/potato_late_blight_sample.jpg",
    ]

    print("🧪 Quick Test on Sample Images")
    print("=" * 50)

    for img_path in test_images:
        if Path(img_path).exists():
            try:
                image = Image.open(img_path)
                result = manager.get_readable_prediction(image)

                print(f"\n📸 {Path(img_path).name}")
                print(f"   Plant: {result['plant_type']}")
                print(f"   Disease: {result['disease']}")
                print(f"   Confidence: {result['confidence_percentage']}")
                print(f"   Healthy: {'Yes' if result['is_healthy'] else 'No'}")

            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"\n📸 {Path(img_path).name} - Not found")


def benchmark_models(manager: "PlantGuardModelManager") -> None:
    """Benchmark all available models on test images."""
    models = manager.list_available_models()
    enabled_models = [m for m in models if m["enabled"]]

    if not enabled_models:
        print("❌ No enabled models found")
        return

    # Load test metadata
    metadata_path = "data/pictures/sample_images_metadata.json"
    if not Path(metadata_path).exists():
        print(f"❌ Test metadata not found: {metadata_path}")
        return

    with open(metadata_path) as f:
        metadata = json.load(f)

    print("🏁 Benchmarking Models on Test Dataset")
    print("=" * 60)

    results = {}

    for model_info in enabled_models:
        model_id = model_info["id"]
        print(f"\n🔄 Testing model: {model_info['name']}")

        if not manager.switch_model(model_id):
            print(f"❌ Failed to load model: {model_id}")
            continue

        correct = 0
        total = 0
        confidences = []

        for sample in metadata["sample_images"][:5]:  # Test first 5 for speed
            image_path = Path("data/pictures") / sample["filename"]

            if not image_path.exists():
                continue

            try:
                image = Image.open(image_path)
                result = manager.get_readable_prediction(image)

                # Simple accuracy check (plant type match)
                gt_plant = sample["plant"].lower()
                pred_plant = result["plant_type"].lower()

                if gt_plant in pred_plant or pred_plant in gt_plant:
                    correct += 1

                total += 1
                confidences.append(result["confidence"])

            except Exception as e:
                print(f"   ❌ Error processing {sample['filename']}: {e}")

        if total > 0:
            accuracy = correct / total
            avg_confidence = sum(confidences) / len(confidences)

            results[model_id] = {
                "name": model_info["name"],
                "accuracy": accuracy,
                "avg_confidence": avg_confidence,
                "total_tested": total,
            }

            print(f"   ✅ Accuracy: {accuracy:.1%} ({correct}/{total})")
            print(f"   📊 Avg Confidence: {avg_confidence:.1%}")

    # Show comparison
    if results:
        print("\n🏆 MODEL COMPARISON")
        print("=" * 60)

        sorted_results = sorted(results.items(), key=lambda x: x[1]["accuracy"], reverse=True)

        for i, (_, result) in enumerate(sorted_results):
            rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i + 1}."
            print(f"{rank} {result['name']}")
            print(f"    Accuracy: {result['accuracy']:.1%}")
            print(f"    Confidence: {result['avg_confidence']:.1%}")
            print()


def main() -> None:
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="PlantGuard Model Switcher")
    parser.add_argument("--list", "-l", action="store_true", help="List available models")
    parser.add_argument("--switch", "-s", type=str, help="Switch to model by ID")
    parser.add_argument("--test", "-t", type=str, help="Test current model on image")
    parser.add_argument(
        "--quick-test", "-q", action="store_true", help="Quick test on sample images"
    )
    parser.add_argument("--benchmark", "-b", action="store_true", help="Benchmark all models")
    parser.add_argument("--current", "-c", action="store_true", help="Show current model info")

    args = parser.parse_args()

    # Initialize model manager
    try:
        manager = PlantGuardModelManager()
    except Exception as e:
        print(f"❌ Failed to initialize model manager: {e}")
        return

    # Execute commands
    if args.list:
        list_models(manager)

    elif args.switch:
        switch_model(manager, args.switch)

    elif args.test:
        test_model(manager, args.test)

    elif args.quick_test:
        quick_test(manager)

    elif args.benchmark:
        benchmark_models(manager)

    elif args.current:
        info = manager.get_current_model_info()
        if "error" not in info:
            print("🤖 Current Model:")
            print("=" * 30)
            print(f"Name: {info['name']}")
            print(f"Type: {info['type']}")
            print(f"Model ID: {info['model_id']}")
            print(f"Accuracy: {info['accuracy']:.1%}")
            print(f"Classes: {info['num_classes']}")
            print(f"Device: {info['device']}")
        else:
            print("❌ No model currently loaded")

    else:
        # Default: show help and current status
        parser.print_help()
        print("\n" + "=" * 50)

        # Show current model if any
        info = manager.get_current_model_info()
        if "error" not in info:
            print(f"🤖 Current Model: {info['name']}")
        else:
            print("🤖 No model currently loaded")

        print("\n💡 Quick Commands:")
        print(
            "  python scripts/model_switching/model_switcher.py --list              "
            "# List all models"
        )
        print(
            "  python scripts/model_switching/model_switcher.py --switch vit_best   "
            "# Switch to best model"
        )
        print(
            "  python scripts/model_switching/model_switcher.py --quick-test        "
            "# Test current model"
        )
        print(
            "  python scripts/model_switching/model_switcher.py --benchmark         "
            "# Compare all models"
        )


if __name__ == "__main__":
    main()
