#!/usr/bin/env python3
"""Easy model switcher for PlantGuard - Switch between models with simple commands."""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

try:
    from src.core.model_manager import PlantGuardModelManager

    LEGACY_MODE = False
except ImportError:
    # Fallback to new registry system
    LEGACY_MODE = True
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.core.vision import VisionAdapter
    from src.training.model_registry import ModelRegistry


def list_models_legacy(manager: "PlantGuardModelManager") -> None:
    """List all available models (legacy mode)."""
    models = manager.list_available_models()

    print("🤖 Available PlantGuard Models:")
    print("=" * 60)

    for model in models:
        status = "🟢 CURRENT" if model["is_current"] else "⚪ Available" if model["enabled"] else "🔴 Disabled"
        accuracy = f"{model['accuracy']:.1%}" if model["accuracy"] > 0 else "Unknown"

        print(f"\n📋 {model['id']}")
        print(f"   Name: {model['name']}")
        print(f"   Type: {model['type']}")
        print(f"   Accuracy: {accuracy}")
        print(f"   Status: {status}")
        print(f"   Description: {model['description']}")


def list_models_registry() -> None:
    """List all available models (registry mode)."""
    registry = ModelRegistry()
    models = registry.list_models()

    print("🤖 Available PlantGuard Models (Registry):")
    print("=" * 60)

    if not models:
        print("No models found in registry. Run 'make train-production' to create models.")
        return

    for model in models:
        accuracy = f"{model.performance_metrics.get('accuracy', 0):.1%}" if model.performance_metrics else "Unknown"

        print(f"\n📋 {model.model_id}")
        print(f"   Version: {model.version}")
        print(f"   Architecture: {model.architecture}")
        print(f"   Training Date: {model.training_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Accuracy: {accuracy}")
        print(f"   Dataset: {model.dataset_version}")
        print(f"   File Size: {model.file_size / (1024 * 1024):.1f} MB")


def list_models(manager=None) -> None:
    """List all available models."""
    if LEGACY_MODE:
        list_models_registry()
    else:
        list_models_legacy(manager)


def switch_model_legacy(manager: "PlantGuardModelManager", model_id: str) -> None:
    """Switch to a specific model (legacy mode)."""
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


def switch_model_registry(model_id: str) -> VisionAdapter:
    """Switch to a specific model (registry mode)."""
    print(f"🔄 Loading model from registry: {model_id}")

    try:
        registry = ModelRegistry()
        model_info = registry.get_model(model_id)

        if not model_info:
            print(f"❌ Model not found in registry: {model_id}")
            return None

        # Create vision adapter and load model
        adapter = VisionAdapter()
        adapter.load_from_registry(model_id)

        print(f"✅ Successfully loaded model: {model_id}")

        # Show model info
        print("\n📊 Model Info:")
        print(f"   Version: {model_info.version}")
        print(f"   Architecture: {model_info.architecture}")
        print(f"   Classes: {len(adapter.get_class_names())}")
        print(f"   Training Date: {model_info.training_date.strftime('%Y-%m-%d %H:%M')}")

        if model_info.performance_metrics:
            accuracy = model_info.performance_metrics.get("accuracy", 0)
            print(f"   Accuracy: {accuracy:.1%}")

        return adapter

    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None


def switch_model(manager, model_id: str):
    """Switch to a specific model."""
    if LEGACY_MODE:
        return switch_model_registry(model_id)
    else:
        return switch_model_legacy(manager, model_id)


def test_model_legacy(manager: "PlantGuardModelManager", image_path: str) -> None:
    """Test current model on an image (legacy mode)."""
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


def test_model_registry(adapter: VisionAdapter, image_path: str) -> None:
    """Test model on an image (registry mode)."""
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return

    try:
        image = Image.open(image_path)
        raw_class, readable_name, confidence, plant_type = adapter.predict_with_readable_name(image)

        print(f"🔍 Testing: {Path(image_path).name}")
        print("=" * 50)
        print(f"🌿 Plant Type: {plant_type}")
        print(f"🦠 Disease: {readable_name}")
        print(f"💚 Healthy: {'Yes' if adapter.is_healthy(raw_class) else 'No'}")
        print(f"📊 Confidence: {confidence:.1%}")
        print(f"🤖 Raw Class: {raw_class}")

    except Exception as e:
        print(f"❌ Failed to test image: {e}")


def test_model(manager, image_path: str, adapter: VisionAdapter = None) -> None:
    """Test current model on an image."""
    if LEGACY_MODE:
        if adapter is None:
            print("❌ No model loaded. Use --switch to load a model first.")
            return
        test_model_registry(adapter, image_path)
    else:
        test_model_legacy(manager, image_path)


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

    with Path(metadata_path).open() as f:
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
    parser.add_argument("--quick-test", "-q", action="store_true", help="Quick test on sample images")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Benchmark all models")
    parser.add_argument("--current", "-c", action="store_true", help="Show current model info")
    parser.add_argument("--migrate", "-m", type=str, help="Migrate legacy model to registry format")

    args = parser.parse_args()

    # Initialize based on mode
    manager = None
    current_adapter = None

    if not LEGACY_MODE:
        try:
            manager = PlantGuardModelManager()
        except Exception as e:
            print(f"❌ Failed to initialize model manager: {e}")
            return

    # Execute commands
    if args.list:
        list_models(manager)

    elif args.switch:
        result = switch_model(manager, args.switch)
        if LEGACY_MODE and result:
            current_adapter = result

    elif args.test:
        test_model(manager, args.test, current_adapter)

    elif args.migrate and LEGACY_MODE:
        # Migrate legacy model to registry format
        legacy_path = args.migrate
        if not Path(legacy_path).exists():
            print(f"❌ Legacy model not found: {legacy_path}")
            return

        try:
            adapter = VisionAdapter()
            output_path = f"data/models/migrated_{Path(legacy_path).stem}.pt"
            adapter.migrate_legacy_model(legacy_path, output_path)
            print(f"✅ Model migrated successfully: {output_path}")

            # Register in registry
            registry = ModelRegistry()
            metadata = {
                "migrated_from": legacy_path,
                "architecture": "resnet50",
                "num_classes": 38,
            }
            model_id = registry.register_model(Path(output_path), metadata)
            print(f"📝 Model registered with ID: {model_id}")

        except Exception as e:
            print(f"❌ Migration failed: {e}")

    elif args.quick_test:
        if LEGACY_MODE:
            print("❌ Quick test not available in registry mode. Use --test with specific image.")
        else:
            quick_test(manager)

    elif args.benchmark:
        if LEGACY_MODE:
            print("❌ Benchmark not available in registry mode yet.")
        else:
            benchmark_models(manager)

    elif args.current:
        if LEGACY_MODE:
            if current_adapter and current_adapter.is_loaded:
                info = current_adapter.get_model_info()
                print("🤖 Current Model:")
                print("=" * 30)
                print(f"Classes: {info['num_classes']}")
                print(f"Device: {info['device']}")
                print(f"Model Path: {info['model_path']}")
            else:
                print("❌ No model currently loaded")
        else:
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

        mode_str = "Registry Mode" if LEGACY_MODE else "Legacy Mode"
        print(f"🔧 Running in: {mode_str}")

        if not LEGACY_MODE and manager:
            # Show current model if any
            info = manager.get_current_model_info()
            if "error" not in info:
                print(f"🤖 Current Model: {info['name']}")
            else:
                print("🤖 No model currently loaded")

        print("\n💡 Quick Commands:")
        print("  python scripts/model_switching/model_switcher.py --list              # List all models")
        print("  python scripts/model_switching/model_switcher.py --switch MODEL_ID   # Switch to model")
        print("  python scripts/model_switching/model_switcher.py --test IMAGE_PATH   # Test model")
        if LEGACY_MODE:
            print("  python scripts/model_switching/model_switcher.py --migrate PATH     # Migrate legacy model")


if __name__ == "__main__":
    main()
