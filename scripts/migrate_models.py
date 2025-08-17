#!/usr/bin/env python3
"""Model Migration Script

This script migrates existing PlantGuard models to the new registry format.
It scans for legacy models and converts them to the new format with proper metadata.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import torch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.vision import VisionAdapter
from training.model_registry import ModelRegistry
from utils.logging_config import setup_logging


class ModelMigrator:
    """Handles migration of legacy models to new registry format."""

    def __init__(self):
        """Initialize model migrator."""
        self.logger = logging.getLogger(__name__)
        self.registry = ModelRegistry()
        self.legacy_paths = [
            "data/models",
            "data/vision_resnet50.pt",
            "data/models/vision_resnet50.pt",
            "data/models/plantguard_model.pt",
        ]

    def find_legacy_models(self) -> list[Path]:
        """Find all legacy model files that need migration.

        Returns:
            List of paths to legacy model files
        """
        legacy_models = []

        for path_str in self.legacy_paths:
            path = Path(path_str)

            if path.is_file() and path.suffix == ".pt":
                # Check if it's a legacy format
                adapter = VisionAdapter()
                if not adapter.is_compatible_with_registry_format(str(path)):
                    legacy_models.append(path)
                    self.logger.info(f"Found legacy model: {path}")

            elif path.is_dir():
                # Scan directory for .pt files
                for model_file in path.glob("*.pt"):
                    adapter = VisionAdapter()
                    if not adapter.is_compatible_with_registry_format(str(model_file)):
                        legacy_models.append(model_file)
                        self.logger.info(f"Found legacy model: {model_file}")

        return legacy_models

    def analyze_legacy_model(self, model_path: Path) -> dict[str, Any]:
        """Analyze a legacy model to extract metadata.

        Args:
            model_path: Path to legacy model

        Returns:
            Dictionary with model metadata
        """
        try:
            # Load checkpoint to analyze
            checkpoint = torch.load(model_path, map_location="cpu")

            metadata = {
                "original_path": str(model_path),
                "file_size": model_path.stat().st_size,
                "modification_time": model_path.stat().st_mtime,
                "architecture": "resnet50",  # Default for PlantGuard
                "num_classes": checkpoint.get("num_classes", 38),
                "class_names": checkpoint.get("class_names", []),
                "training_metadata": {},
            }

            # Try to extract additional info from filename
            filename = model_path.stem
            if "resnet" in filename.lower():
                metadata["architecture"] = "resnet50"
            elif "vit" in filename.lower():
                metadata["architecture"] = "vit"

            # Check for training info in checkpoint
            if "epoch" in checkpoint:
                metadata["training_metadata"]["final_epoch"] = checkpoint["epoch"]
            if "best_accuracy" in checkpoint:
                metadata["training_metadata"]["best_accuracy"] = checkpoint["best_accuracy"]
            if "optimizer_state_dict" in checkpoint:
                metadata["training_metadata"]["has_optimizer_state"] = True

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to analyze model {model_path}: {e}")
            return {}

    def migrate_model(self, model_path: Path, metadata: dict[str, Any]) -> str:
        """Migrate a single legacy model to the new format.

        Args:
            model_path: Path to legacy model
            metadata: Model metadata

        Returns:
            Model ID in registry, or empty string if failed
        """
        try:
            self.logger.info(f"Migrating model: {model_path}")

            # Create migrated model path
            migrated_dir = Path("data/models/migrated")
            migrated_dir.mkdir(parents=True, exist_ok=True)

            timestamp = int(time.time())
            migrated_path = migrated_dir / f"migrated_{model_path.stem}_{timestamp}.pt"

            # Use VisionAdapter to perform migration
            adapter = VisionAdapter()
            adapter.migrate_legacy_model(str(model_path), str(migrated_path))

            # Prepare registry metadata
            registry_metadata = {
                "model_id": f"migrated_{model_path.stem}_{timestamp}",
                "version": "1.0.0",
                "architecture": metadata.get("architecture", "resnet50"),
                "training_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metadata.get("modification_time", time.time()))),
                "dataset_version": "legacy",
                "hyperparameters": metadata.get("training_metadata", {}),
                "performance_metrics": {},
                "migration_info": {
                    "migrated_from": str(model_path),
                    "migration_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "original_size": metadata.get("file_size", 0),
                },
            }

            # Add performance metrics if available
            if "best_accuracy" in metadata.get("training_metadata", {}):
                registry_metadata["performance_metrics"]["accuracy"] = metadata["training_metadata"]["best_accuracy"]

            # Register in model registry
            model_id = self.registry.register_model(migrated_path, registry_metadata)

            self.logger.info(f"✅ Model migrated successfully: {model_id}")
            return model_id

        except Exception as e:
            self.logger.error(f"❌ Failed to migrate model {model_path}: {e}")
            return ""

    def migrate_all_models(self, dry_run: bool = False) -> dict[str, str]:
        """Migrate all found legacy models.

        Args:
            dry_run: If True, only analyze models without migrating

        Returns:
            Dictionary mapping original paths to new model IDs
        """
        legacy_models = self.find_legacy_models()

        if not legacy_models:
            self.logger.info("No legacy models found to migrate")
            return {}

        self.logger.info(f"Found {len(legacy_models)} legacy models to migrate")

        migration_results = {}

        for model_path in legacy_models:
            self.logger.info(f"Processing: {model_path}")

            # Analyze model
            metadata = self.analyze_legacy_model(model_path)
            if not metadata:
                self.logger.warning(f"Skipping {model_path} - analysis failed")
                continue

            # Show analysis results
            self.logger.info(f"  Architecture: {metadata.get('architecture', 'unknown')}")
            self.logger.info(f"  Classes: {metadata.get('num_classes', 'unknown')}")
            self.logger.info(f"  Size: {metadata.get('file_size', 0) / (1024 * 1024):.1f} MB")

            if dry_run:
                self.logger.info("  [DRY RUN] Would migrate to registry")
                migration_results[str(model_path)] = "dry_run"
            else:
                # Perform migration
                model_id = self.migrate_model(model_path, metadata)
                if model_id:
                    migration_results[str(model_path)] = model_id

        return migration_results

    def create_backup(self, model_paths: list[Path]) -> Path:
        """Create backup of legacy models before migration.

        Args:
            model_paths: List of model paths to backup

        Returns:
            Path to backup directory
        """
        backup_dir = Path("data/models/backup") / f"backup_{int(time.time())}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        for model_path in model_paths:
            if model_path.exists():
                backup_path = backup_dir / model_path.name
                backup_path.write_bytes(model_path.read_bytes())
                self.logger.info(f"Backed up: {model_path} -> {backup_path}")

        return backup_dir


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PlantGuard Model Migration Tool")
    parser.add_argument("--dry-run", action="store_true", help="Analyze models without migrating them")
    parser.add_argument("--backup", action="store_true", help="Create backup of legacy models before migration")
    parser.add_argument("--model", type=Path, help="Migrate specific model file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Logging level")

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level)
    logger = logging.getLogger(__name__)

    # Initialize migrator
    migrator = ModelMigrator()

    try:
        if args.model:
            # Migrate specific model
            if not args.model.exists():
                logger.error(f"Model file not found: {args.model}")
                sys.exit(1)

            metadata = migrator.analyze_legacy_model(args.model)
            if not metadata:
                logger.error(f"Failed to analyze model: {args.model}")
                sys.exit(1)

            if args.dry_run:
                logger.info(f"[DRY RUN] Would migrate: {args.model}")
                logger.info(f"  Architecture: {metadata.get('architecture')}")
                logger.info(f"  Classes: {metadata.get('num_classes')}")
            else:
                if args.backup:
                    migrator.create_backup([args.model])

                model_id = migrator.migrate_model(args.model, metadata)
                if model_id:
                    logger.info(f"✅ Migration successful: {model_id}")
                else:
                    logger.error("❌ Migration failed")
                    sys.exit(1)

        else:
            # Migrate all legacy models
            legacy_models = migrator.find_legacy_models()

            if args.backup and legacy_models and not args.dry_run:
                backup_dir = migrator.create_backup(legacy_models)
                logger.info(f"📦 Backup created: {backup_dir}")

            results = migrator.migrate_all_models(dry_run=args.dry_run)

            if results:
                logger.info(f"🎉 Migration completed: {len(results)} models processed")
                for original, model_id in results.items():
                    logger.info(f"  {Path(original).name} -> {model_id}")
            else:
                logger.info("No models were migrated")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
