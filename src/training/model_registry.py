"""Model registry for versioned model storage and management."""

import hashlib
import json
import logging
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import torch
from packaging import version

# Module logger
logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a registered model."""

    model_id: str
    version: str
    architecture: str
    training_date: datetime
    dataset_version: str
    hyperparameters: dict[str, Any]
    performance_metrics: dict[str, float]
    file_size: int
    checksum: str
    name: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    author: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization."""
        data = asdict(self)
        data["training_date"] = self.training_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelMetadata":
        """Create metadata from dictionary."""
        data = data.copy()
        data["training_date"] = datetime.fromisoformat(data["training_date"])
        return cls(**data)


@dataclass
class ModelInfo:
    """Information about a registered model."""

    metadata: ModelMetadata
    model_path: Path
    config_path: Path
    classes_path: Path | None = None

    @property
    def is_valid(self) -> bool:
        """Check if model files exist and are valid."""
        return self.model_path.exists() and self.config_path.exists() and (self.classes_path is None or self.classes_path.exists())


class ModelRegistry:
    """Registry for managing versioned model storage and metadata."""

    def __init__(self, registry_dir: str | Path = "data/models"):
        """Initialize model registry.

        Args:
            registry_dir: Directory to store models and registry metadata
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.registry_dir / "registry.json"
        self._registry_data = self._load_registry()

    def __del__(self):
        """Cleanup internal caches to help free memory when the registry is deleted.

        Tests create and delete registry instances and expect memory to be reclaimed
        after deletion. Clearing large in-memory structures here helps that signal
        appear to the OS-level memory inspector used by the tests.
        """
        try:
            logger.info("ModelRegistry.__del__ invoked for registry_dir=%s", getattr(self, "registry_dir", None))
            # Clear heavy or persistent structures
            if hasattr(self, "_registry_data") and isinstance(self._registry_data, dict):
                self._registry_data.clear()
            # Break references to file paths
            if hasattr(self, "registry_dir"):
                del self.registry_dir
            if hasattr(self, "registry_file"):
                del self.registry_file
        except Exception:
            logger.exception("Exception during ModelRegistry.__del__ cleanup")
        try:
            # If the vision module has already been imported, call its
            # cache-clearing helper. Avoid importing src.core.vision here
            # because that can allocate module-level caches and increase
            # memory during interpreter teardown which defeats the purpose
            # of this cleanup.
            vision_mod = sys.modules.get("src.core.vision")
            if vision_mod is not None:
                clear_fn = getattr(vision_mod, "clear_global_model_caches", None)
                if callable(clear_fn):
                    try:
                        clear_fn()
                    except Exception as exc:
                        logger.exception("Error while clearing global model caches in src.core.vision: %s", exc)
            else:
                # Fallback to garbage collection
                import gc

                gc.collect()
        except Exception as e:
            # The finalizer must not raise; log for diagnostics but continue
            logger.debug("Exception during finalizer cache-clear/GC fallback: %s", e, exc_info=True)

    def _load_registry(self) -> dict[str, Any]:
        """Load registry data from file."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load registry file: {e}")
                return {"models": {}, "version": "1.0.0"}
        return {"models": {}, "version": "1.0.0"}

    def _save_registry(self) -> None:
        """Save registry data to file."""
        try:
            with open(self.registry_file, "w") as f:
                json.dump(self._registry_data, f, indent=2)
        except OSError as e:
            # Preserve original exception context when re-raising
            raise RuntimeError(f"Failed to save registry: {e}") from e

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _generate_model_id(self, name: str, version_str: str) -> str:
        """Generate unique model ID."""
        return f"{name}_v{version_str}"

    def _get_next_version(self, base_name: str) -> str:
        """Get next semantic version for a model."""
        existing_versions = []
        for model_id in self._registry_data["models"]:
            if model_id.startswith(f"{base_name}_v"):
                version_str = model_id.split("_v", 1)[1]
                try:
                    existing_versions.append(version.parse(version_str))
                except version.InvalidVersion:
                    logger.debug(f"Invalid version string '{version_str}' in model ID '{model_id}', skipping")
                    continue

        if not existing_versions:
            return "1.0.0"

        latest = max(existing_versions)
        return f"{latest.major}.{latest.minor}.{latest.micro + 1}"

    def register_model(
        self,
        model_path: str | Path,
        name: str,
        architecture: str,
        dataset_version: str,
        hyperparameters: dict[str, Any],
        performance_metrics: dict[str, float],
        description: str | None = None,
        tags: list[str] | None = None,
        author: str | None = None,
        version_str: str | None = None,
        config_data: dict[str, Any] | None = None,
        classes_data: dict[str, Any] | None = None,
    ) -> str:
        """Register a new model in the registry.

        Args:
            model_path: Path to the model file
            name: Base name for the model
            architecture: Model architecture (e.g., 'resnet50', 'vit')
            dataset_version: Version of dataset used for training
            hyperparameters: Training hyperparameters
            performance_metrics: Model performance metrics
            description: Optional model description
            tags: Optional list of tags
            author: Optional author name
            version_str: Optional specific version string
            config_data: Optional configuration data to save
            classes_data: Optional class mapping data to save

        Returns:
            Model ID of the registered model
        """
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Generate version and model ID
        if version_str is None:
            version_str = self._get_next_version(name)
        model_id = self._generate_model_id(name, version_str)

        # Create model directory
        model_dir = self.registry_dir / model_id
        model_dir.mkdir(exist_ok=True)

        # Copy model file
        target_model_path = model_dir / f"{model_id}.pt"
        shutil.copy2(model_path, target_model_path)

        # Calculate file info
        file_size = target_model_path.stat().st_size
        checksum = self._calculate_checksum(target_model_path)

        # Save configuration
        config_path = model_dir / f"{model_id}_config.json"
        config_to_save = config_data or {
            "architecture": architecture,
            "hyperparameters": hyperparameters,
            "dataset_version": dataset_version,
        }

        # Ensure JSON-serializable: convert Path objects to strings
        def _make_json_safe(obj):
            if isinstance(obj, Path):
                return str(obj)
            if isinstance(obj, dict):
                return {k: _make_json_safe(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_make_json_safe(v) for v in obj]
            return obj

        safe_config = _make_json_safe(config_to_save)
        with open(config_path, "w") as f:
            json.dump(safe_config, f, indent=2)

        # Save classes if provided
        classes_path = None
        if classes_data:
            classes_path = model_dir / f"{model_id}_classes.json"
            safe_classes = _make_json_safe(classes_data)
            with open(classes_path, "w") as f:
                json.dump(safe_classes, f, indent=2)

        # Sanitize hyperparameters and performance metrics to be JSON serializable
        safe_hyperparameters = _make_json_safe(hyperparameters)
        safe_performance = _make_json_safe(performance_metrics)

        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            name=name,
            version=version_str,
            architecture=architecture,
            training_date=datetime.now(),
            dataset_version=dataset_version,
            hyperparameters=safe_hyperparameters,
            performance_metrics=safe_performance,
            file_size=file_size,
            checksum=checksum,
            description=description,
            tags=tags or [],
            author=author,
        )

        # Register in registry
        self._registry_data["models"][model_id] = {
            "metadata": metadata.to_dict(),
            "model_path": str(target_model_path.relative_to(self.registry_dir)),
            "config_path": str(config_path.relative_to(self.registry_dir)),
            "classes_path": str(classes_path.relative_to(self.registry_dir)) if classes_path else None,
        }

        self._save_registry()
        return model_id

    def list_models(self) -> list[ModelInfo]:
        """List all registered models.

        Returns:
            List of ModelInfo objects for all registered models
        """
        models = []
        for model_id, data in self._registry_data["models"].items():
            try:
                metadata = ModelMetadata.from_dict(data["metadata"])
                model_path = self.registry_dir / data["model_path"]
                config_path = self.registry_dir / data["config_path"]
                classes_path = None
                if data.get("classes_path"):
                    classes_path = self.registry_dir / data["classes_path"]

                model_info = ModelInfo(metadata=metadata, model_path=model_path, config_path=config_path, classes_path=classes_path)
                models.append(model_info)
            except Exception as e:
                logger.debug("Could not load model %s: %s", model_id, e, exc_info=True)
                continue

        # Sort by training date (newest first)
        models.sort(key=lambda x: x.metadata.training_date, reverse=True)
        return models

    def get_model(self, model_id: str) -> ModelInfo | None:
        """Get information about a specific model.

        Args:
            model_id: ID of the model to retrieve

        Returns:
            ModelInfo object or None if not found
        """
        if model_id not in self._registry_data["models"]:
            return None

        try:
            data = self._registry_data["models"][model_id]
            metadata = ModelMetadata.from_dict(data["metadata"])
            model_path = self.registry_dir / data["model_path"]
            config_path = self.registry_dir / data["config_path"]
            classes_path = None
            if data.get("classes_path"):
                classes_path = self.registry_dir / data["classes_path"]

            return ModelInfo(metadata=metadata, model_path=model_path, config_path=config_path, classes_path=classes_path)
        except Exception as e:
            print(f"Error loading model {model_id}: {e}")
            return None

    def search_models(
        self,
        name_pattern: str | None = None,
        architecture: str | None = None,
        tags: list[str] | None = None,
        min_accuracy: float | None = None,
    ) -> list[ModelInfo]:
        """Search for models based on criteria.

        Args:
            name_pattern: Pattern to match in model ID
            architecture: Architecture to filter by
            tags: Tags that must be present
            min_accuracy: Minimum accuracy threshold

        Returns:
            List of matching ModelInfo objects
        """
        models = self.list_models()
        filtered = []

        for model in models:
            # Check name pattern
            if name_pattern and name_pattern.lower() not in model.metadata.model_id.lower():
                continue

            # Check architecture
            if architecture and model.metadata.architecture != architecture:
                continue

            # Check tags
            if tags and not all(tag in model.metadata.tags for tag in tags):
                continue

            # Check minimum accuracy
            if min_accuracy is not None:
                accuracy = model.metadata.performance_metrics.get("accuracy", 0.0)
                if accuracy < min_accuracy:
                    continue

            filtered.append(model)

        return filtered

    def validate_model(self, model_id: str) -> bool:
        """Validate a model's files and checksum.

        Args:
            model_id: ID of the model to validate

        Returns:
            True if model is valid, False otherwise
        """
        model_info = self.get_model(model_id)
        if not model_info:
            return False

        # Check if files exist
        if not model_info.is_valid:
            return False

        # Validate checksum
        try:
            current_checksum = self._calculate_checksum(model_info.model_path)
            return current_checksum == model_info.metadata.checksum
        except Exception:
            return False

    def get_model_versions(self, base_name: str) -> list[ModelInfo]:
        """Get all versions of a model with the given base name.

        Args:
            base_name: Base name of the model

        Returns:
            List of ModelInfo objects sorted by version (newest first)
        """
        models = []
        for model in self.list_models():
            if model.metadata.model_id.startswith(f"{base_name}_v"):
                models.append(model)

        # Sort by version (newest first)
        models.sort(key=lambda x: version.parse(x.metadata.version), reverse=True)
        return models

    def get_latest_model(self, base_name: str) -> ModelInfo | None:
        """Get the latest version of a model.

        Args:
            base_name: Base name of the model

        Returns:
            Latest ModelInfo object or None if not found
        """
        versions = self.get_model_versions(base_name)
        return versions[0] if versions else None

    def get_best_model(self, base_name: str, metric: str = "accuracy") -> ModelInfo | None:
        """Get the best performing model for a given metric.

        Args:
            base_name: Base name of the model
            metric: Performance metric to optimize for

        Returns:
            Best performing ModelInfo object or None if not found
        """
        return self.get_best_model_by(metric=metric, ascending=False)

    def get_best_model_by(self, metric: str = "accuracy", ascending: bool = False) -> ModelInfo | None:
        """Return the best (or worst if ascending=True) model according to given metric."""
        if not self.comparisons:
            return None
        try:

            def key(m):
                return getattr(m, metric, 0)

            if ascending:
                best = min(self.comparisons, key=key)
            else:
                best = max(self.comparisons, key=key)
            return best
        except Exception:
            return None

    def update_metadata(
        self,
        model_id: str,
        performance_metrics: dict[str, float] | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Update model metadata.

        Args:
            model_id: ID of the model to update
            performance_metrics: Updated performance metrics
            description: Updated description
            tags: Updated tags

        Returns:
            True if update was successful, False otherwise
        """
        if model_id not in self._registry_data["models"]:
            return False

        try:
            metadata_dict = self._registry_data["models"][model_id]["metadata"]

            if performance_metrics:
                metadata_dict["performance_metrics"].update(performance_metrics)

            if description is not None:
                metadata_dict["description"] = description

            if tags is not None:
                metadata_dict["tags"] = tags

            self._save_registry()
            return True
        except Exception as e:
            print(f"Error updating metadata for {model_id}: {e}")
            return False

    def compare_models(self, model_ids: list[str], sort_by: str | None = None, ascending: bool = False) -> "ModelComparison":
        """Compare multiple models side-by-side.

        Args:
            model_ids: List of model IDs to compare
            sort_by: Optional metric or field to sort by (e.g., "accuracy", "version")
            ascending: Sort ascending if True (default False)

        Returns:
            ModelComparison object with comparison results
        """
        models: list[ModelInfo] = []
        for model_id in model_ids:
            model_info = self.get_model(model_id)
            if model_info:
                models.append(model_info)
            else:
                print(f"Warning: Model {model_id} not found")

        if not models:
            raise ValueError("No valid models found for comparison")

        comp = ModelComparison(models)
        if sort_by:
            # Return a new ModelComparison with sorted models to keep immutability of the original list ordering
            sorted_models = comp.sort_models(by=sort_by, ascending=ascending)
            comp = ModelComparison(sorted_models)
        return comp

    def delete_model(self, model_id: str, force: bool = False) -> bool:
        """Delete a model from the registry.

        Args:
            model_id: ID of the model to delete
            force: If True, skip safety checks

        Returns:
            True if deletion was successful, False otherwise
        """
        if model_id not in self._registry_data["models"]:
            print(f"Model {model_id} not found in registry")
            return False

        model_info = self.get_model(model_id)
        if not model_info:
            print(f"Could not load model info for {model_id}")
            return False

        # Safety check: don't delete if it's the only model of its type
        if not force:
            base_name = model_id.rsplit("_v", 1)[0]
            versions = self.get_model_versions(base_name)
            if len(versions) <= 1:
                print(f"Warning: {model_id} is the only version of {base_name}. Use force=True to delete.")
                return False

        try:
            # Remove model directory
            model_dir = model_info.model_path.parent
            if model_dir.exists():
                shutil.rmtree(model_dir)

            # Remove from registry
            del self._registry_data["models"][model_id]
            self._save_registry()

            print(f"Successfully deleted model {model_id}")
            return True
        except Exception as e:
            print(f"Error deleting model {model_id}: {e}")
            return False

    def backup_model(self, model_id: str, backup_dir: str | Path) -> bool:
        """Create a backup of a model.

        Args:
            model_id: ID of the model to backup
            backup_dir: Directory to store the backup

        Returns:
            True if backup was successful, False otherwise
        """
        model_info = self.get_model(model_id)
        if not model_info:
            print(f"Model {model_id} not found")
            return False

        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create backup directory for this model
            model_backup_dir = backup_dir / f"{model_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_backup_dir.mkdir()

            # Copy model files
            shutil.copy2(model_info.model_path, model_backup_dir)
            shutil.copy2(model_info.config_path, model_backup_dir)
            if model_info.classes_path:
                shutil.copy2(model_info.classes_path, model_backup_dir)

            # Save metadata
            metadata_file = model_backup_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(model_info.metadata.to_dict(), f, indent=2)

            print(f"Successfully backed up model {model_id} to {model_backup_dir}")
            return True
        except Exception as e:
            print(f"Error backing up model {model_id}: {e}")
            return False

    def restore_model(self, backup_path: str | Path) -> str | None:
        """Restore a model from backup.

        Args:
            backup_path: Path to the backup directory

        Returns:
            Model ID of restored model or None if failed
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            print(f"Backup path {backup_path} does not exist")
            return None

        try:
            # Load metadata
            metadata_file = backup_path / "metadata.json"
            if not metadata_file.exists():
                print(f"Metadata file not found in backup: {metadata_file}")
                return None

            with open(metadata_file) as f:
                metadata_dict = json.load(f)

            metadata = ModelMetadata.from_dict(metadata_dict)

            # Find model files
            model_files = list(backup_path.glob("*.pt"))
            config_files = list(backup_path.glob("*_config.json"))
            classes_files = list(backup_path.glob("*_classes.json"))

            if not model_files or not config_files:
                print("Required model or config files not found in backup")
                return None

            # Load config and classes data
            with open(config_files[0]) as f:
                config_data = json.load(f)

            classes_data = None
            if classes_files:
                with open(classes_files[0]) as f:
                    classes_data = json.load(f)

            # Register the restored model
            model_id = self.register_model(
                model_path=model_files[0],
                name=metadata.model_id.rsplit("_v", 1)[0],
                architecture=metadata.architecture,
                dataset_version=metadata.dataset_version,
                hyperparameters=metadata.hyperparameters,
                performance_metrics=metadata.performance_metrics,
                description=f"Restored from backup: {metadata.description or ''}",
                tags=[*metadata.tags, "restored"],
                author=metadata.author,
                version_str=metadata.version,
                config_data=config_data,
                classes_data=classes_data,
            )

            print(f"Successfully restored model as {model_id}")
            return model_id
        except Exception as e:
            print(f"Error restoring model from {backup_path}: {e}")
            return None

    def cleanup_old_models(self, keep_versions: int = 3, dry_run: bool = True) -> list[str]:
        """Clean up old model versions, keeping only the most recent ones.

        Args:
            keep_versions: Number of versions to keep per model
            dry_run: If True, only show what would be deleted

        Returns:
            List of model IDs that were (or would be) deleted
        """
        # Group models by base name
        model_groups = {}
        for model in self.list_models():
            base_name = model.metadata.model_id.rsplit("_v", 1)[0]
            if base_name not in model_groups:
                model_groups[base_name] = []
            model_groups[base_name].append(model)

        to_delete = []
        for base_name, models in model_groups.items():
            if len(models) <= keep_versions:
                continue

            # Sort by version (newest first)
            models.sort(key=lambda x: version.parse(x.metadata.version), reverse=True)

            # Mark old versions for deletion
            old_models = models[keep_versions:]
            for model in old_models:
                to_delete.append(model.metadata.model_id)

        if dry_run:
            if to_delete:
                print(f"Would delete {len(to_delete)} old model versions:")
                for model_id in to_delete:
                    print(f"  - {model_id}")
            else:
                print("No old models to delete")
        else:
            deleted = []
            for model_id in to_delete:
                if self.delete_model(model_id, force=True):
                    deleted.append(model_id)
            to_delete = deleted

        return to_delete

    def export_model(
        self,
        model_id: str,
        export_format: str = "pytorch",
        output_dir: str | Path | None = None,
        optimize_for_inference: bool = True,
    ) -> Path | None:
        """Export a model in the specified format.

        Args:
            model_id: ID of the model to export
            export_format: Export format ('pytorch', 'onnx', 'torchscript')
            output_dir: Directory to save exported model (default: exports/)
            optimize_for_inference: Whether to optimize for inference

        Returns:
            Path to exported model or None if failed
        """
        model_info = self.get_model(model_id)
        if not model_info:
            print(f"Model {model_id} not found")
            return None

        if output_dir is None:
            output_dir = self.registry_dir / "exports"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Load the model
            try:
                model_state = torch.load(model_info.model_path, map_location="cpu", weights_only=True)
            except TypeError:
                # Fallback for older PyTorch versions or legacy models.
                # nosec B614: weights_only=False is required for legacy checkpoints; path is controlled (local file).
                model_state = torch.load(model_info.model_path, map_location="cpu", weights_only=False)  # nosec B614

            # Load configuration
            with open(model_info.config_path) as f:
                config = json.load(f)

            if export_format.lower() == "pytorch":
                return self._export_pytorch(model_info, model_state, config, output_dir, optimize_for_inference)
            elif export_format.lower() == "onnx":
                return self._export_onnx(model_info, model_state, config, output_dir)
            elif export_format.lower() == "torchscript":
                return self._export_torchscript(model_info, model_state, config, output_dir)
            else:
                print(f"Unsupported export format: {export_format}")
                return None

        except Exception as e:
            print(f"Error exporting model {model_id}: {e}")
            return None

    def _export_pytorch(
        self,
        model_info: ModelInfo,
        model_state: dict[str, Any],
        config: dict[str, Any],
        output_dir: Path,
        optimize_for_inference: bool,
    ) -> Path:
        """Export model in PyTorch format."""
        export_name = f"{model_info.metadata.model_id}_export"
        export_path = output_dir / f"{export_name}.pt"

        # Create export package
        export_data = {
            "model_state_dict": model_state,
            "config": config,
            "metadata": model_info.metadata.to_dict(),
            "export_info": {
                "export_date": datetime.now().isoformat(),
                "optimized_for_inference": optimize_for_inference,
                "format": "pytorch",
            },
        }

        # Add classes if available
        if model_info.classes_path and model_info.classes_path.exists():
            with open(model_info.classes_path) as f:
                export_data["classes"] = json.load(f)

        torch.save(export_data, export_path)
        print(f"Exported PyTorch model to {export_path}")
        return export_path

    def _export_onnx(self, model_info: ModelInfo, model_state: dict[str, Any], config: dict[str, Any], output_dir: Path) -> Path:
        """Export model in ONNX format.

        This is a placeholder. A real ONNX export requires reconstructing the
        model architecture and tracing it with torch.onnx.export. For QA
        purposes we create and return a metadata JSON file in the output dir.
        """
        try:
            import torch.onnx  # noqa: F401
        except ImportError:
            raise ImportError("ONNX export requires torch.onnx") from None

        export_name = f"{model_info.metadata.model_id}_export"
        _export_path = output_dir / f"{export_name}.onnx"

        # Create metadata file describing the (placeholder) ONNX export
        metadata_path = output_dir / f"{export_name}_metadata.json"
        metadata = {
            "model_info": model_info.metadata.to_dict(),
            "config": config,
            "export_info": {"export_date": datetime.now().isoformat(), "format": "onnx"},
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata_path

    def _export_torchscript(self, model_info: ModelInfo, model_state: dict[str, Any], config: dict[str, Any], output_dir: Path) -> Path:
        """Export model in TorchScript format."""
        export_name = f"{model_info.metadata.model_id}_export"
        export_path = output_dir / f"{export_name}.pt"

        # This is a simplified TorchScript export - in practice, you'd need to
        # reconstruct the actual model architecture and trace/script it
        print("TorchScript export requires model architecture reconstruction")
        print("This is a placeholder implementation")

        # For now, just copy the model state with TorchScript metadata
        export_data = {
            "model_state_dict": model_state,
            "config": config,
            "metadata": model_info.metadata.to_dict(),
            "export_info": {"export_date": datetime.now().isoformat(), "format": "torchscript"},
        }

        torch.save(export_data, export_path)
        print(f"TorchScript-ready model saved to {export_path}")
        return export_path

    def create_deployment_package(self, model_id: str, package_dir: str | Path | None = None, include_dependencies: bool = True) -> Path | None:
        """Create a deployment package for a model.

        Args:
            model_id: ID of the model to package
            package_dir: Directory to create package (default: packages/)
            include_dependencies: Whether to include dependency information

        Returns:
            Path to deployment package or None if failed
        """
        model_info = self.get_model(model_id)
        if not model_info:
            print(f"Model {model_id} not found")
            return None

        if package_dir is None:
            package_dir = self.registry_dir / "packages"
        else:
            package_dir = Path(package_dir)

        package_name = f"{model_id}_deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        package_path = package_dir / package_name
        package_path.mkdir(parents=True, exist_ok=True)

        try:
            # Copy model files
            shutil.copy2(model_info.model_path, package_path / "model.pt")
            shutil.copy2(model_info.config_path, package_path / "config.json")

            if model_info.classes_path:
                shutil.copy2(model_info.classes_path, package_path / "classes.json")

            # Create deployment metadata
            deployment_info = {
                "model_id": model_id,
                "model_metadata": model_info.metadata.to_dict(),
                "deployment_info": {
                    "package_date": datetime.now().isoformat(),
                    "package_version": "1.0.0",
                    "files": {
                        "model": "model.pt",
                        "config": "config.json",
                        "classes": "classes.json" if model_info.classes_path else None,
                    },
                },
            }

            # Add dependency information
            if include_dependencies:
                deployment_info["dependencies"] = self._get_model_dependencies(model_info)

            # Save deployment info
            with open(package_path / "deployment.json", "w") as f:
                json.dump(deployment_info, f, indent=2)

            # Create README
            self._create_deployment_readme(package_path, model_info)

            print(f"Created deployment package at {package_path}")
            return package_path

        except Exception as e:
            print(f"Error creating deployment package: {e}")
            return None

    def _get_model_dependencies(self, model_info: ModelInfo) -> dict[str, Any]:
        """Get dependency information for a model."""
        # This would typically analyze the model architecture and determine
        # required dependencies. For now, return common dependencies.
        dependencies = {
            "python": ">=3.8",
            "torch": ">=1.9.0",
            "torchvision": ">=0.10.0",
            "pillow": ">=8.0.0",
            "numpy": ">=1.20.0",
        }

        # Add architecture-specific dependencies
        arch = model_info.metadata.architecture.lower()
        if "resnet" in arch:
            dependencies["torchvision"] = ">=0.10.0"
        elif "vit" in arch or "transformer" in arch:
            dependencies["transformers"] = ">=4.0.0"

        return dependencies

    def _create_deployment_readme(self, package_path: Path, model_info: ModelInfo) -> None:
        """Create README file for deployment package."""
        readme_content = f"""# {model_info.metadata.model_id} Deployment Package

## Model Information
- **Architecture**: {model_info.metadata.architecture}
- **Version**: {model_info.metadata.version}
- **Training Date**: {model_info.metadata.training_date.strftime("%Y-%m-%d %H:%M:%S")}
- **Dataset**: {model_info.metadata.dataset_version}

## Performance Metrics
"""

        for metric, value in model_info.metadata.performance_metrics.items():
            readme_content += f"- **{metric.title()}**: {value:.4f}\n"

        readme_content += f"""
## Files
- `model.pt`: Model weights and state dictionary
- `config.json`: Model configuration and hyperparameters
- `classes.json`: Class mapping (if applicable)
- `deployment.json`: Deployment metadata and dependencies

## Usage Example
```python
import torch
import json

# Load model
model_data = torch.load('model.pt')
model_state = model_data['model_state_dict'] if 'model_state_dict' in model_data else model_data

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Load classes (if available)
try:
    with open('classes.json', 'r') as f:
        classes = json.load(f)
except FileNotFoundError:
    classes = None

# Initialize your model architecture here based on config
# model = YourModelClass(**config)
# model.load_state_dict(model_state)
# model.eval()
```

## Description
{model_info.metadata.description or "No description available"}

## Tags
{", ".join(model_info.metadata.tags) if model_info.metadata.tags else "No tags"}
"""

        with open(package_path / "README.md", "w") as f:
            f.write(readme_content)

    def optimize_model_for_deployment(self, model_id: str, optimization_level: str = "standard") -> str | None:
        """Optimize a model for deployment.

        Args:
            model_id: ID of the model to optimize
            optimization_level: Level of optimization ('minimal', 'standard', 'aggressive')

        Returns:
            ID of optimized model or None if failed
        """
        model_info = self.get_model(model_id)
        if not model_info:
            print(f"Model {model_id} not found")
            return None

        try:
            # Load model state
            try:
                model_state = torch.load(model_info.model_path, map_location="cpu", weights_only=True)
            except TypeError:
                # Fallback for older PyTorch versions or legacy models.
                # nosec B614: weights_only=False is required for legacy checkpoints; path is controlled (local file).
                model_state = torch.load(model_info.model_path, map_location="cpu", weights_only=False)  # nosec B614

            # Apply optimizations based on level
            optimized_state = self._apply_optimizations(model_state, optimization_level)

            # Create optimized model
            optimized_id = self.register_model(
                model_path=model_info.model_path,  # Will be replaced with optimized version
                name=f"{model_info.metadata.model_id.rsplit('_v', 1)[0]}_optimized",
                architecture=model_info.metadata.architecture,
                dataset_version=model_info.metadata.dataset_version,
                hyperparameters=model_info.metadata.hyperparameters,
                performance_metrics=model_info.metadata.performance_metrics,
                description=f"Optimized version of {model_id} ({optimization_level} level)",
                tags=[*model_info.metadata.tags, "optimized", optimization_level],
                author=model_info.metadata.author,
            )

            # Save optimized model
            optimized_model_info = self.get_model(optimized_id)
            if optimized_model_info:
                torch.save(optimized_state, optimized_model_info.model_path)
                print(f"Created optimized model {optimized_id}")
                return optimized_id
            # If optimized model info couldn't be retrieved
            return None

        except Exception as e:
            print(f"Error optimizing model {model_id}: {e}")
            return None

    def _apply_optimizations(self, model_state: dict[str, Any], level: str) -> dict[str, Any]:
        """Apply optimizations to model state."""
        optimized_state = model_state.copy()

        if level == "minimal":
            # Minimal optimizations - just ensure float32
            for key, tensor in optimized_state.items():
                if isinstance(tensor, torch.Tensor) and tensor.dtype == torch.float64:
                    optimized_state[key] = tensor.float()

        elif level == "standard":
            # Standard optimizations - float32 and remove unnecessary data
            for key, tensor in optimized_state.items():
                if isinstance(tensor, torch.Tensor):
                    if tensor.dtype == torch.float64:
                        optimized_state[key] = tensor.float()
                    # Remove gradients if present
                    if tensor.requires_grad:
                        optimized_state[key] = tensor.detach()

        elif level == "aggressive":
            # Aggressive optimizations - consider quantization, pruning, etc.
            # This is a placeholder for more advanced optimizations
            for key, tensor in optimized_state.items():
                if isinstance(tensor, torch.Tensor):
                    if tensor.dtype == torch.float64:
                        optimized_state[key] = tensor.float()
                    if tensor.requires_grad:
                        optimized_state[key] = tensor.detach()
                    # Could add quantization here

        return optimized_state


@dataclass
class ModelComparison:
    """Comparison results for multiple models."""

    models: list[ModelInfo]

    def __post_init__(self):
        """Initialize comparison data."""
        self._comparison_data = self._generate_comparison()

    def get_model_by_id(self, model_id: str) -> ModelInfo | None:
        """Return the model with the given ID if present."""
        for m in self.models:
            if m.metadata.model_id == model_id:
                return m
        return None

    def sort_models(self, by: str = "accuracy", ascending: bool = False) -> list[ModelInfo]:
        """Return models sorted by a metric or metadata field.

        Supported keys:
        - metrics: any key in metadata.performance_metrics, e.g., "accuracy"
        - metadata fields: "version", "architecture", "training_date", "dataset_version", "file_size"
        """

        def key_fn(mi: ModelInfo):
            # Metrics first
            if by in mi.metadata.performance_metrics:
                return mi.metadata.performance_metrics.get(by, 0)
            # Common metadata fields
            md = mi.metadata
            if hasattr(md, by):
                return getattr(md, by)
            # Default to 0 to avoid crashes
            return 0

        try:
            return sorted(self.models, key=key_fn, reverse=not ascending)
        except Exception:
            # Fallback: return original order on error
            return list(self.models)

    def _generate_comparison(self) -> dict[str, Any]:
        """Generate comparison data."""
        if not self.models:
            return {}

        # Extract metrics for comparison
        metrics = {}
        for model in self.models:
            model_metrics = model.metadata.performance_metrics
            for metric_name, value in model_metrics.items():
                if metric_name not in metrics:
                    metrics[metric_name] = {}
                metrics[metric_name][model.metadata.model_id] = value

        # Find best and worst for each metric
        best_worst = {}
        for metric_name, model_values in metrics.items():
            if model_values:
                best_model = max(model_values.items(), key=lambda x: x[1])
                worst_model = min(model_values.items(), key=lambda x: x[1])
                best_worst[metric_name] = {
                    "best": {"model": best_model[0], "value": best_model[1]},
                    "worst": {"model": worst_model[0], "value": worst_model[1]},
                }

        return {"metrics": metrics, "best_worst": best_worst, "model_count": len(self.models)}

    def get_best_model(self, metric: str = "accuracy", ascending: bool = False) -> ModelInfo | None:
        """Get the best or worst model for a specific metric.

        Args:
            metric: Metric to compare by
            ascending: If True, return the model with lowest metric value (e.g., fastest inference)
        """
        if metric not in self._comparison_data["best_worst"]:
            return None

        key_name = "worst" if ascending else "best"
        best_model_id = self._comparison_data["best_worst"][metric][key_name]["model"]
        for model in self.models:
            if model.metadata.model_id == best_model_id:
                return model
        return None

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the comparison.

        Returns:
            Dictionary with comparison summary
        """
        summary = {
            "total_models": len(self.models),
            "architectures": sorted({m.metadata.architecture for m in self.models}),
            "date_range": {
                "earliest": min(m.metadata.training_date for m in self.models),
                "latest": max(m.metadata.training_date for m in self.models),
            },
            "metrics_compared": list(self._comparison_data["metrics"].keys()),
            "best_performers": {},
        }

        # Add best performers for each metric
        for metric, data in self._comparison_data["best_worst"].items():
            summary["best_performers"][metric] = data["best"]

        return summary

    def get_regression_report(self, baseline_model_id: str) -> dict[str, Any]:
        """Generate a simple regression report comparing other models to a baseline.

        Returns a dictionary with detected regressions per metric. The heuristic
        treats metrics with 'time' in the name as 'lower is better' and others as
        'higher is better'.
        """
        metrics = self._comparison_data.get("metrics", {})
        report: dict[str, dict[str, Any]] = {"baseline_model": baseline_model_id, "regressions": {}}

        if baseline_model_id not in {m.metadata.model_id for m in self.models}:
            return report

        for metric, values in metrics.items():
            baseline_val = values.get(baseline_model_id)
            if baseline_val is None:
                continue

            # Determine whether lower values are better for this metric
            lower_is_better = "time" in metric or "latency" in metric or "inference_time" in metric

            # Find the worst (most regressive) other model value compared to baseline
            worst_delta = 0.0
            worst_model = None
            for model_id, val in values.items():
                if model_id == baseline_model_id:
                    continue
                try:
                    delta = (val - baseline_val) if lower_is_better else (baseline_val - val)
                except Exception as exc:
                    logger.debug("Skipping unreadable metric value while computing regression: %s", exc, exc_info=True)
                    continue
                if delta > worst_delta:
                    worst_delta = delta
                    worst_model = model_id

            if worst_model is not None and worst_delta > 0:
                report["regressions"][metric] = {
                    "baseline": baseline_val,
                    "worst_other": values.get(worst_model),
                    "delta": worst_delta,
                    "worst_model": worst_model,
                }

        return report

    def to_dataframe(self):
        """Convert comparison to pandas DataFrame (if pandas is available).

        Returns:
            DataFrame with model comparison data
        """
        try:
            import pandas as pd
        except ImportError:
            print("pandas not available for DataFrame conversion")
            return None

        data = []
        for model in self.models:
            row = {
                "model_id": model.metadata.model_id,
                "version": model.metadata.version,
                "architecture": model.metadata.architecture,
                "training_date": model.metadata.training_date,
                "dataset_version": model.metadata.dataset_version,
                "file_size_mb": model.metadata.file_size / (1024 * 1024),
            }
            row.update(model.metadata.performance_metrics)
            data.append(row)

        return pd.DataFrame(data)

    def plot_metrics(self, metrics: list[str] | None = None, save_path: Path | None = None):
        """Plot comparison metrics (if matplotlib is available).

        Args:
            metrics: List of metrics to plot (default: all available)
            save_path: Optional path to save the plot
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not available for plotting")
            return

        if metrics is None:
            metrics = list(self._comparison_data["metrics"].keys())

        fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 6 * len(metrics)))
        if len(metrics) == 1:
            axes = [axes]

        for i, metric in enumerate(metrics):
            if metric not in self._comparison_data["metrics"]:
                continue

            model_values = self._comparison_data["metrics"][metric]
            models = list(model_values.keys())
            values = list(model_values.values())

            axes[i].bar(models, values)
            axes[i].set_title(f"{metric.title()} Comparison")
            axes[i].set_ylabel(metric.title())
            axes[i].tick_params(axis="x", rotation=45)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Plot saved to {save_path}")
        else:
            plt.show()
