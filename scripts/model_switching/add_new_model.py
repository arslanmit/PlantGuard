#!/usr/bin/env python3
"""Add new models to PlantGuard configuration easily."""

import argparse
import json
from pathlib import Path


def add_huggingface_model(model_id: str, name: str | None = None, description: str | None = None) -> bool:
    """Add a new Hugging Face model to the configuration."""

    config_path = Path("config/models.json")

    if not config_path.exists():
        print("[TODO] Configuration file not found. Run model_switcher.py first to create it.")
        return False

    # Load current config
    with config_path.open() as f:
        config = json.load(f)

    # Generate model key
    model_key = model_id.split("/")[-1].lower().replace("-", "_")

    # Check if model already exists
    if model_key in config["models"]:
        print(f"[WARNING]  Model {model_key} already exists in configuration")
        return False

    # Create model configuration
    model_config = {
        "name": name or f"Custom Model ({model_id})",
        "type": "huggingface",
        "model_id": model_id,
        "description": description or f"Custom Hugging Face model: {model_id}",
        "accuracy": 0.0,  # Unknown until tested
        "confidence_threshold": 0.6,
        "enabled": True,
        "device": "auto",
    }

    # Add to config
    config["models"][model_key] = model_config

    # Save updated config
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)

    print(f"[DONE] Added model: {model_key}")
    print(f"   Name: {model_config['name']}")
    print(f"   Model ID: {model_id}")
    print("   Status: Enabled")

    return True

def list_huggingface_plant_models() -> None:
    """Show some popular plant disease models from Hugging Face."""
    models = [
        {
            "id": "Abhiram4/PlantDiseaseDetectorVit2",
            "name": "Vision Transformer v2",
            "description": "Vision Transformer model with excellent accuracy",
        },
        {
            "id": "Diginsa/Plant-Disease-Detection-Project",
            "name": "MobileNet Plant Disease",
            "description": "Lightweight MobileNet model for plant disease detection",
        },
        {
            "id": "marwaALzaabi/plant-disease-detection-vit",
            "name": "ViT Large Plant Disease",
            "description": "Large Vision Transformer for plant disease detection",
        },
        {
            "id": "susnato/plant_disease_detection-beans",
            "name": "Bean Disease Detector",
            "description": "Specialized model for bean plant diseases",
        },
        {
            "id": "Abhiram4/PlantDiseaseDetectorSwinv2",
            "name": "Swin Transformer v2",
            "description": "Swin Transformer model for plant disease detection",
        },
    ]

    print("[HUG] Popular Plant Disease Models on Hugging Face:")
    print("=" * 60)

    for model in models:
        print(f"\n[DETAILS] {model['id']}")
        print(f"   Name: {model['name']}")
        print(f"   Description: {model['description']}")
        print(f"   Add with: python add_new_model.py --add {model['id']}")

def remove_model(model_key: str) -> bool:
    """Remove a model from the configuration."""
    config_path = Path("config/models.json")

    if not config_path.exists():
        print("[TODO] Configuration file not found")
        return False

    # Load current config
    with config_path.open() as f:
        config = json.load(f)

    if model_key not in config["models"]:
        print(f"[TODO] Model {model_key} not found in configuration")
        return False

    # Remove model
    removed_model = config["models"].pop(model_key)

    # Update default if necessary
    if config.get("default_model") == model_key:
        remaining_models = [k for k, v in config["models"].items() if v.get("enabled", True)]
        if remaining_models:
            config["default_model"] = remaining_models[0]
            print(f"[PARTIAL] Updated default model to: {remaining_models[0]}")
        else:
            config["default_model"] = None
            print("[WARNING]  No default model set (no enabled models remaining)")

    # Save updated config
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)

    print(f"[DONE] Removed model: {model_key}")
    print(f"   Name: {removed_model['name']}")

    return True

def enable_disable_model(model_key: str, enable: bool) -> bool:
    """Enable or disable a model."""
    config_path = Path("config/models.json")

    if not config_path.exists():
        print("[TODO] Configuration file not found")
        return False

    # Load current config
    with config_path.open() as f:
        config = json.load(f)

    if model_key not in config["models"]:
        print(f"[TODO] Model {model_key} not found in configuration")
        return False

    # Update enabled status
    config["models"][model_key]["enabled"] = enable

    # Save updated config
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)

    status = "enabled" if enable else "disabled"
    print(f"[DONE] Model {model_key} {status}")

    return True

def set_default_model(model_key: str) -> bool:
    """Set the default model."""
    config_path = Path("config/models.json")

    if not config_path.exists():
        print("[TODO] Configuration file not found")
        return False

    # Load current config
    with config_path.open() as f:
        config = json.load(f)

    if model_key not in config["models"]:
        print(f"[TODO] Model {model_key} not found in configuration")
        return False

    if not config["models"][model_key].get("enabled", True):
        print(f"[WARNING]  Model {model_key} is disabled. Enable it first.")
        return False

    # Set as default
    config["default_model"] = model_key

    # Save updated config
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)

    print(f"[DONE] Set default model to: {model_key}")
    print(f"   Name: {config['models'][model_key]['name']}")

    return True

def show_config() -> None:
    """Show current configuration."""
    config_path = Path("config/models.json")

    if not config_path.exists():
        print("[TODO] Configuration file not found")
        return

    with config_path.open() as f:
        config = json.load(f)

    print("[SETTINGS]  Current PlantGuard Model Configuration:")
    print("=" * 50)

    print(f"Default Model: {config.get('default_model', 'None')}")
    print(f"Total Models: {len(config.get('models', {}))}")

    print("\n[DETAILS] Models:")
    for model_key, model_config in config.get("models", {}).items():
        status = "[GREEN] Enabled" if model_config.get("enabled", True) else "[RED] Disabled"
        default = " (DEFAULT)" if model_key == config.get("default_model") else ""

        print(f"\n  {model_key}{default}")
        print(f"    Name: {model_config['name']}")
        print(f"    Type: {model_config['type']}")
        print(f"    Model ID: {model_config['model_id']}")
        print(f"    Accuracy: {model_config.get('accuracy', 0):.1%}")
        print(f"    Status: {status}")

def main() -> None:
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="PlantGuard Model Configuration Manager")
    parser.add_argument("--add", type=str, help="Add Hugging Face model by ID")
    parser.add_argument("--name", type=str, help="Custom name for the model")
    parser.add_argument("--description", type=str, help="Custom description for the model")
    parser.add_argument("--remove", type=str, help="Remove model by key")
    parser.add_argument("--enable", type=str, help="Enable model by key")
    parser.add_argument("--disable", type=str, help="Disable model by key")
    parser.add_argument("--default", type=str, help="Set default model by key")
    parser.add_argument("--list-popular", action="store_true", help="List popular HF models")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")

    args = parser.parse_args()

    if args.add:
        add_huggingface_model(args.add, args.name, args.description)

    elif args.remove:
        remove_model(args.remove)

    elif args.enable:
        enable_disable_model(args.enable, True)

    elif args.disable:
        enable_disable_model(args.disable, False)

    elif args.default:
        set_default_model(args.default)

    elif args.list_popular:
        list_huggingface_plant_models()

    elif args.show_config:
        show_config()

    else:
        parser.print_help()
        print("\n" + "=" * 50)
        print("[TIP] Quick Examples:")
        print("  python add_new_model.py --show-config")
        print("  python add_new_model.py --list-popular")
        print("  python add_new_model.py --add Abhiram4/PlantDiseaseDetectorVit2")
        print("  python add_new_model.py --enable vit_best")
        print("  python add_new_model.py --default vit_best")

if __name__ == "__main__":
    main()
