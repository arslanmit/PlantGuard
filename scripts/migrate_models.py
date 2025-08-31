#!/usr/bin/env python3
"""Migration utility for upgrading PlantGuard models to the new registry format.

This script helps migrate existing PlantGuard models to the new production
training pipeline format with proper versioning and metadata.
"""


import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.vision import VisionAdapter
from src.training.model_registry import ModelRegistry


def scan_for_legacy_models() -> list[Path]:
    """Scan for legacy model files that need migration.

    Returns:
        List of paths to legacy model files
    """
    legacy_paths = []

    # Common locations for legacy models
    search_paths = [
        "data/models",
        "models",
        "checkpoints",
    ]

    for search_path in search_paths:
        search_dir = Path(search_path)
        if not search_dir.exists():
            continue

        # Look for .pt files
        for model_file in search_dir.glob("*.pt"):
            # Skip if already migrated or in registry format
            adapter = VisionAdapter()
            if not adapter.is_compatible_with_registry_format(str(model_file)):
                legacy_paths.append(model_file)

    return legacy_paths


def migrate_model(
    model_path: Path,
    registry: ModelRegistry,
    name: str | None = None,
    description: str | None = None,
    architecture: str = "resnet50",
    dataset_version: str = "unknown",
) -> str | None:
    """Migrate a single model to registry format.

    Args:
        model_path: Path to legacy model file
        registry: ModelRegistry instance
        name: Optional model name (defaults to filename)
        description: Optional model description
        architecture: Model architecture
        dataset_version: Dataset version used for training

    Returns:
        Model ID if successful, None if failed
    """
    try:
        print(f"[PARTIAL] Migrating: {model_path}")

        # Create VisionAdapter for migration
        adapter = VisionAdapter()

        # Generate migrated model path
        migrated_name = name or f"migrated_{model_path.stem}"
        migrated_path = model_path.parent / f"{migrated_name}_registry.pt"

        # Migrate the model file
        adapter.migrate_legacy_model(str(model_path), str(migrated_path))

        # Extract metadata from migrated model
        try:
            checkpoint = adapter._load_checkpoint_metadata(str(migrated_path))
            num_classes = checkpoint.get("num_classes", 38)
            class_names = checkpoint.get("class_names", [])
        except Exception:
            num_classes = 38
            class_names = []

        # Register in registry
        model_id = registry.register_model(
            model_path=migrated_path,
            name=migrated_name,
            architecture=architecture,
            dataset_version=dataset_version,
            hyperparameters={
                "num_classes": num_classes,
                "class_names": class_names,
                "migrated_from": str(model_path),
                "migration_tool": "migrate_models.py",
            },
            performance_metrics={"accuracy": 0.0},  # Unknown accuracy
            description=description or f"Migrated from legacy model: {model_path.name}",
            tags=["migrated", "legacy"],
        )

        print(f"[DONE] Successfully migrated: {model_path} -> {model_id}")
        return model_id

    except Exception as e:
        print(f"[TODO] Failed to migrate {model_path}: {e}")
        return None


def update_model_manager_config(migrated_models: list[str]) -> None:
    """Update model manager configuration with migrated models.

    Args:
        migrated_models: List of migrated model IDs
    """
    try:
        from src.features.model_switching.model_manager import PlantGuardModelManager

        manager = PlantGuardModelManager(autoload_default=False)

        # Sync with registry to pick up new models
        if manager.sync_with_registry():
            print("[DONE] Updated model manager configuration")
        else:
            print("[WARNING]  Could not update model manager configuration")

    except Exception as e:
        print(f"[WARNING]  Could not update model manager: {e}")


def create_migration_report(
    legacy_models: list[Path],
    migrated_models: list[str],
    failed_models: list[Path],
) -> None:
    """Create a migration report.

    Args:
        legacy_models: List of legacy model paths found
        migrated_models: List of successfully migrated model IDs
        failed_models: List of models that failed to migrate
    """
    report = {
        "migration_summary": {
            "total_found": len(legacy_models),
            "successfully_migrated": len(migrated_models),
            "failed": len(failed_models),
        },
        "migrated_models": migrated_models,
        "failed_models": [str(p) for p in failed_models],
        "recommendations": [],
    }

    # Add recommendations
    if migrated_models:
        report["recommendations"].append("Run 'python scripts/model_switching/model_switcher.py --list' to see migrated models")
        report["recommendations"].append(
            "Test migrated models with 'python scripts/model_switching/model_switcher.py --switch MODEL_ID --test IMAGE_PATH'"
        )

    if failed_models:
        report["recommendations"].append("Check failed models manually - they may be corrupted or in an unsupported format")

    # Save report
    report_path = Path("migration_report.json")
    with report_path.open("w") as f:
        json.dump(report, f, indent=2)

    print("\n[DETAILS] Migration Report:")
    print(f"   Total models found: {len(legacy_models)}")
    print(f"   Successfully migrated: {len(migrated_models)}")
    print(f"   Failed migrations: {len(failed_models)}")
    print(f"   Report saved to: {report_path}")


def main() -> None:
    """Main migration utility."""
    parser = argparse.ArgumentParser(description="Migrate PlantGuard models to registry format")
    parser.add_argument("--scan", "-s", action="store_true", help="Scan for legacy models")
    parser.add_argument("--migrate", "-m", type=str, help="Migrate specific model file")
    parser.add_argument("--migrate-all", "-a", action="store_true", help="Migrate all found legacy models")
    parser.add_argument("--name", "-n", type=str, help="Name for migrated model")
    parser.add_argument("--description", "-d", type=str, help="Description for migrated model")
    parser.add_argument("--architecture", type=str, default="resnet50", help="Model architecture")
    parser.add_argument("--dataset", type=str, default="unknown", help="Dataset version")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without doing it")

    args = parser.parse_args()

    # Initialize registry
    try:
        registry = ModelRegistry()
    except Exception as e:
        print(f"[TODO] Failed to initialize model registry: {e}")
        return

    if args.scan or args.migrate_all:
        # Scan for legacy models
        print("[SEARCH] Scanning for legacy models...")
        legacy_models = scan_for_legacy_models()

        if not legacy_models:
            print("[DONE] No legacy models found - all models are already in registry format")
            return

        print(f"[DETAILS] Found {len(legacy_models)} legacy models:")
        for model_path in legacy_models:
            print(f"   - {model_path}")

        if args.scan:
            return

        if args.dry_run:
            print("\n[SEARCH] Dry run - would migrate:")
            for model_path in legacy_models:
                print(f"   - {model_path} -> migrated_{model_path.stem}")
            return

        # Migrate all found models
        print(f"\n[LAUNCH] Starting migration of {len(legacy_models)} models...")
        migrated_models = []
        failed_models = []

        for model_path in legacy_models:
            model_id = migrate_model(
                model_path,
                registry,
                architecture=args.architecture,
                dataset_version=args.dataset,
            )

            if model_id:
                migrated_models.append(model_id)
            else:
                failed_models.append(model_path)

        # Update model manager configuration
        if migrated_models:
            update_model_manager_config(migrated_models)

        # Create migration report
        create_migration_report(legacy_models, migrated_models, failed_models)

    elif args.migrate:
        # Migrate specific model
        model_path = Path(args.migrate)

        if not model_path.exists():
            print(f"[TODO] Model file not found: {model_path}")
            return

        if args.dry_run:
            print(f"[SEARCH] Dry run - would migrate: {model_path}")
            return

        model_id = migrate_model(
            model_path,
            registry,
            name=args.name,
            description=args.description,
            architecture=args.architecture,
            dataset_version=args.dataset,
        )

        if model_id:
            update_model_manager_config([model_id])
            print("\n[DONE] Migration completed successfully!")
            print(f"   Model ID: {model_id}")
            print(f"   Test with: python scripts/model_switching/model_switcher.py --switch {model_id}")
        else:
            print("[TODO] Migration failed")

    else:
        # Show help and current status
        parser.print_help()

        print("\n" + "=" * 60)
        print("[TOOL] PlantGuard Model Migration Utility")
        print("=" * 60)

        # Show registry status
        models = registry.list_models()
        print(f"[SUMMARY] Current registry status: {len(models)} models")

        # Quick scan
        legacy_models = scan_for_legacy_models()
        if legacy_models:
            print(f"[WARNING]  Found {len(legacy_models)} legacy models that need migration")
            print("   Run with --migrate-all to migrate them")
        else:
            print("[DONE] No legacy models found")

        print("\n[TIP] Quick Commands:")
        print("  python scripts/migrate_models.py --scan                    # Scan for legacy models")
        print("  python scripts/migrate_models.py --migrate-all             # Migrate all legacy models")
        print("  python scripts/migrate_models.py --migrate MODEL.pt       # Migrate specific model")


if __name__ == "__main__":
    main()
