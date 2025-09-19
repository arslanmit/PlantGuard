#!/usr/bin/env python3
"""Script to list all registered models."""

import sys
from pathlib import Path

try:
    from plantguard.training.model_registry import ModelRegistry
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from plantguard.training.model_registry import ModelRegistry


def main() -> None:
    """List all registered models with details."""

    registry = ModelRegistry()
    models = registry.list_models()

    if not models:
        print("No models registered yet")
        print("[TIP] Register models using the ModelRegistry API or train new models")
    else:
        print(f"Found {len(models)} registered models:")
        print()

        for model in models:
            print(f"Model ID: {model.metadata.model_id}")
            print(f"  Version: {model.metadata.version}")
            print(f"  Architecture: {model.metadata.architecture}")
            print(f"  Training Date: {model.metadata.training_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Dataset: {model.metadata.dataset_version}")
            print(f"  File Size: {model.metadata.file_size / (1024 * 1024):.1f} MB")

            if model.metadata.performance_metrics:
                print("  Performance:")
                for metric, value in model.metadata.performance_metrics.items():
                    print(f"    {metric}: {value:.4f}")

            if model.metadata.tags:
                print(f"  Tags: {', '.join(model.metadata.tags)}")

            print(f"  Valid: {'[DONE]' if model.is_valid else '[TODO]'}")
            print()

if __name__ == "__main__":
    main()
