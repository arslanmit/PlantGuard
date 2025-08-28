#!/usr/bin/env python3
from __future__ import annotations

"""Easy model switcher for PlantGuard - Switch between models with simple commands."""

import argparse
import sys
from pathlib import Path

from PIL import Image

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

# Always try to expose ModelRegistry and VisionAdapter for tests/CLI re-exports
try:  # soft import, may fail in pure-legacy setups
    from src.training.model_registry import ModelRegistry  # type: ignore
except Exception:  # pragma: no cover - optional
    ModelRegistry = None  # type: ignore

try:  # soft import; adapter may be needed by tests
    from src.core.vision import VisionAdapter  # type: ignore
except Exception:  # pragma: no cover - optional
    VisionAdapter = None  # type: ignore

try:
    from src.core.model_manager import PlantGuardModelManager

    LEGACY_MODE = False
except ImportError:
    # Fallback to new registry system
    LEGACY_MODE = True
    # Ensure re-exports are available in legacy mode too
    if VisionAdapter is None:
        from src.core.vision import VisionAdapter  # type: ignore
    if ModelRegistry is None:
        from src.training.model_registry import ModelRegistry  # type: ignore


def list_models_legacy(manager: PlantGuardModelManager) -> None:
    """List all available models (legacy mode)."""
    models = manager.list_available_models()

    print("[AI] Available PlantGuard Models:")
    print("=" * 60)

    for model in models:
        status = "[GREEN] CURRENT" if model["is_current"] else "⚪ Available" if model["enabled"] else "[RED] Disabled"
        accuracy = f"{model['accuracy']:.1%}" if model["accuracy"] > 0 else "Unknown"

        print(f"\n[DETAILS] {model['id']}")
        print(f"   Name: {model['name']}")
        print(f"   Type: {model['type']}")
        print(f"   Accuracy: {accuracy}")
        print(f"   Status: {status}")
        print(f"   Description: {model['description']}")


def list_models_registry() -> None:
    """List all available models (registry mode)."""
    registry = ModelRegistry()
    models = registry.list_models()

    print("[AI] Available PlantGuard Models (Registry):")
    print("=" * 60)

    if not models:
        print("No models found in registry. Run 'make train-production' to create models.")
        return

    for model in models:
        accuracy = f"{model.metadata.performance_metrics.get('accuracy', 0):.1%}" if model.metadata.performance_metrics else "Unknown"

        print(f"\n[DETAILS] {model.metadata.model_id}")
        print(f"   Version: {model.metadata.version}")
        print(f"   Architecture: {model.metadata.architecture}")
        print(f"   Training Date: {model.metadata.training_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Accuracy: {accuracy}")
        print(f"   Dataset: {model.metadata.dataset_version}")
        print(f"   File Size: {model.metadata.file_size / (1024 * 1024):.1f} MB")


def list_models(manager=None) -> None:
    """List all available models."""
    if LEGACY_MODE:
        list_models_registry()
    else:
        list_models_legacy(manager)


def switch_model_legacy(manager: PlantGuardModelManager, model_id: str) -> None:
    """Switch to a specific model (legacy mode)."""
    print(f"[PARTIAL] Switching to model: {model_id}")

    if manager.switch_model(model_id):
        print(f"[DONE] Successfully switched to: {model_id}")

        # Show current model info
        info = manager.get_current_model_info()
        print("\n[SUMMARY] Current Model Info:")
        print(f"   Name: {info['name']}")
        print(f"   Type: {info['type']}")
        print(f"   Classes: {info['num_classes']}")
        print(f"   Device: {info['device']}")
        print(f"   Accuracy: {info['accuracy']:.1%}")
    else:
        print(f"[TODO] Failed to switch to model: {model_id}")


def switch_model_registry(model_id: str) -> VisionAdapter | None:
    """Switch to a specific model (registry mode)."""
    print(f"[PARTIAL] Loading model from registry: {model_id}")

    try:
        registry = ModelRegistry()
        model_info = registry.get_model(model_id)

        if not model_info:
            print(f"[TODO] Model not found in registry: {model_id}")
            return None

        # Create vision adapter and load model
        adapter = VisionAdapter()
        adapter.load_from_registry(model_id)

        print(f"[DONE] Successfully loaded model: {model_id}")

        # Show model info
        print("\n[SUMMARY] Model Info:")
        print(f"   Version: {getattr(model_info.metadata, 'version', 'unknown')}")
        print(f"   Architecture: {getattr(model_info.metadata, 'architecture', 'unknown')}")
        print(f"   Classes: {len(adapter.get_class_names())}")
        td = getattr(model_info.metadata, "training_date", None)
        if td is not None:
            try:
                print(f"   Training Date: {td.strftime('%Y-%m-%d %H:%M')}")
            except Exception:
                print(f"   Training Date: {td}")
        else:
            print("   Training Date: Unknown")

        if getattr(model_info.metadata, "performance_metrics", None):
            accuracy = model_info.metadata.performance_metrics.get("accuracy", 0)
            print(f"   Accuracy: {accuracy:.1%}")

        return adapter

    except Exception as e:
        print(f"[TODO] Failed to load model: {e}")
        return None


def switch_model(manager, model_id: str) -> VisionAdapter | None:
    """Switch to a specific model."""
    if LEGACY_MODE:
        return switch_model_registry(model_id)
    else:
        return switch_model_legacy(manager, model_id)


def test_model_legacy(manager: PlantGuardModelManager, image_path: str) -> None:
    """Test current model on an image (legacy mode)."""
    if not Path(image_path).exists():
        print(f"[TODO] Image not found: {image_path}")
        return

    try:
        image = Image.open(image_path)
        result = manager.get_readable_prediction(image)

        print(f"[SEARCH] Testing: {Path(image_path).name}")
        print("=" * 50)
        print(f"[LEAF] Plant Type: {result['plant_type']}")
        print(f"[VIRUS] Disease: {result['disease']}")
        print(f"[HEALTHY] Healthy: {'Yes' if result['is_healthy'] else 'No'}")
        print(f"[SUMMARY] Confidence: {result['confidence_percentage']}")
        print(f"[TIP] Recommendation: {result['recommendation']}")
        print(f"[AI] Model: {result['model_info']['model_name']}")

    except Exception as e:
        print(f"[TODO] Failed to test image: {e}")


def test_model_registry(adapter: VisionAdapter, image_path: str) -> None:
    """Test model on an image (registry mode)."""
    if not Path(image_path).exists():
        print(f"[TODO] Image not found: {image_path}")
        return

    try:
        image = Image.open(image_path)
        raw_class, readable_name, confidence, plant_type = adapter.predict_with_readable_name(image)

        print(f"[SEARCH] Testing: {Path(image_path).name}")
        print("=" * 50)
        print(f"[LEAF] Plant Type: {plant_type}")
        print(f"[VIRUS] Disease: {readable_name}")
        print(f"[HEALTHY] Healthy: {'Yes' if adapter.is_healthy(raw_class) else 'No'}")
        print(f"[SUMMARY] Confidence: {confidence:.1%}")
        print(f"[AI] Raw Class: {raw_class}")

    except Exception as e:
        print(f"[TODO] Failed to test image: {e}")


def run_test_model(manager, image_path: str, adapter: VisionAdapter = None) -> None:
    """Test current model on an image."""
    if LEGACY_MODE:
        if adapter is None:
            print("[TODO] No model loaded. Use --switch to load a model first.")
            return
        test_model_registry(adapter, image_path)
    else:
        test_model_legacy(manager, image_path)


def quick_test(manager: PlantGuardModelManager) -> None:
    """Quick test disabled.

    Sample-image based quick tests have been disabled in this repository per project
    policy. Use --test IMAGE_PATH to test with your own images placed under
    data/raw/ or provide a custom path.
    """
    print("[TODO] Quick test on sample images is disabled in this repository.")


def benchmark_models(manager: PlantGuardModelManager) -> None:
    """Benchmark all available models on test images."""
    models = manager.list_available_models()
    enabled_models = [m for m in models if m["enabled"]]

    if not enabled_models:
        print("[TODO] No enabled models found")
        return

    # Benchmark disabled for sample-based dataset
    print("[TODO] Benchmarking on bundled sample images is disabled in this repository.")
    print("Use your own validation dataset and the evaluator APIs to benchmark models.")


def main() -> None:
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="PlantGuard Model Switcher")
    parser.add_argument("--list", "-l", action="store_true", help="List available models")
    parser.add_argument("--switch", "-s", type=str, help="Switch to model by ID")
    parser.add_argument("--test", "-t", type=str, help="Test current model on image")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Benchmark all models")
    parser.add_argument("--current", "-c", action="store_true", help="Show current model info")
    parser.add_argument("--migrate", "-m", type=str, help="Migrate legacy model to registry format")
    parser.add_argument("--sync", action="store_true", help="Sync model configuration with registry")
    parser.add_argument("--migrate-all", action="store_true", help="Migrate all legacy models to registry")

    args = parser.parse_args()

    # Initialize based on mode
    manager = None
    current_adapter = None

    if not LEGACY_MODE:
        try:
            manager = PlantGuardModelManager()
        except Exception as e:
            print(f"[TODO] Failed to initialize model manager: {e}")
            return

    # Execute commands
    if args.list:
        list_models(manager)

    elif args.switch:
        result = switch_model(manager, args.switch)
        if LEGACY_MODE and result:
            current_adapter = result

    elif args.test:
        run_test_model(manager, args.test, current_adapter)

    elif args.migrate and LEGACY_MODE:
        # Migrate legacy model to registry format
        legacy_path = args.migrate
        if not Path(legacy_path).exists():
            print(f"[TODO] Legacy model not found: {legacy_path}")
            return

        try:
            adapter = VisionAdapter()
            output_path = f"data/models/migrated_{Path(legacy_path).stem}.pt"
            adapter.migrate_legacy_model(legacy_path, output_path)
            print(f"[DONE] Model migrated successfully: {output_path}")

            # Register in registry
            registry = ModelRegistry()
            metadata = {
                "migrated_from": legacy_path,
                "architecture": "resnet50",
                "num_classes": 38,
            }
            model_id = registry.register_model(Path(output_path), metadata)
            print(f"[WRITE] Model registered with ID: {model_id}")

        except Exception as e:
            print(f"[TODO] Migration failed: {e}")

    elif args.sync:
        # Sync configuration with registry
        if not LEGACY_MODE:
            if manager.sync_with_registry():
                print("[DONE] Successfully synced configuration with registry")
            else:
                print("[TODO] Failed to sync with registry")
        else:
            print("[TODO] Sync only available with model manager")

    elif args.migrate_all:
        # Migrate all legacy models
        if not LEGACY_MODE:
            migrated = manager.migrate_legacy_models()
            if migrated:
                print(f"[DONE] Successfully migrated {len(migrated)} models:")
                for model_id in migrated:
                    print(f"  - {model_id}")
            else:
                print("No legacy models found to migrate")
        else:
            print("[TODO] Bulk migration only available with model manager")

    # --quick-test flag removed: sample-based quick tests disabled per project policy

    elif args.benchmark:
        if LEGACY_MODE:
            print("[TODO] Benchmark not available in registry mode yet.")
        else:
            benchmark_models(manager)

    elif args.current:
        if LEGACY_MODE:
            if current_adapter and current_adapter.is_loaded:
                info = current_adapter.get_model_info()
                print("[AI] Current Model:")
                print("=" * 30)
                print(f"Classes: {info['num_classes']}")
                print(f"Device: {info['device']}")
                print(f"Model Path: {info['model_path']}")
            else:
                print("[TODO] No model currently loaded")
        else:
            info = manager.get_current_model_info()
            if "error" not in info:
                print("[AI] Current Model:")
                print("=" * 30)
                print(f"Name: {info['name']}")
                print(f"Type: {info['type']}")
                print(f"Model ID: {info['model_id']}")
                print(f"Accuracy: {info['accuracy']:.1%}")
                print(f"Classes: {info['num_classes']}")
                print(f"Device: {info['device']}")
            else:
                print("[TODO] No model currently loaded")

    else:
        # Default: show help and current status
        parser.print_help()
        print("\n" + "=" * 50)

        mode_str = "Registry Mode" if LEGACY_MODE else "Legacy Mode"
        print(f"[TOOL] Running in: {mode_str}")

        if not LEGACY_MODE and manager:
            # Show current model if any
            info = manager.get_current_model_info()
            if "error" not in info:
                print(f"[AI] Current Model: {info['name']}")
            else:
                print("[AI] No model currently loaded")

        print("\n[TIP] Quick Commands:")
        print("  python scripts/model_switching/model_switcher.py --list              # List all models")
        print("  python scripts/model_switching/model_switcher.py --switch MODEL_ID   # Switch to model")
        print("  python scripts/model_switching/model_switcher.py --test IMAGE_PATH   # Test model")
        if LEGACY_MODE:
            print("  python scripts/model_switching/model_switcher.py --migrate PATH     # Migrate legacy model")


if __name__ == "__main__":
    main()
