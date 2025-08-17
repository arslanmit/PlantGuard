"""Tests for model registry functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import torch
import torch.nn as nn

from src.training.model_registry import ModelMetadata, ModelRegistry


class SimpleModel(nn.Module):
    """Simple model for testing."""

    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 2)

    def forward(self, x):
        return self.linear(x)


@pytest.fixture
def temp_registry():
    """Create temporary registry for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield ModelRegistry(temp_dir)


@pytest.fixture
def sample_model_file():
    """Create a sample model file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        model = SimpleModel()
        torch.save(model.state_dict(), f.name)
        yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)


def test_model_metadata_serialization():
    """Test ModelMetadata serialization and deserialization."""
    metadata = ModelMetadata(
        model_id="test_v1.0.0",
        version="1.0.0",
        architecture="resnet50",
        training_date=datetime.now(),
        dataset_version="plantvillage_v1",
        hyperparameters={"lr": 0.001, "batch_size": 32},
        performance_metrics={"accuracy": 0.95, "f1_score": 0.94},
        file_size=1024,
        checksum="abc123",
        description="Test model",
        tags=["test", "resnet"],
        author="test_user",
    )

    # Test serialization
    data = metadata.to_dict()
    assert isinstance(data["training_date"], str)
    assert data["model_id"] == "test_v1.0.0"

    # Test deserialization
    restored = ModelMetadata.from_dict(data)
    assert restored.model_id == metadata.model_id
    assert restored.version == metadata.version
    assert restored.training_date == metadata.training_date
    assert restored.hyperparameters == metadata.hyperparameters


def test_registry_initialization(temp_registry):
    """Test registry initialization."""
    assert temp_registry.registry_dir.exists()
    assert temp_registry._registry_data["version"] == "1.0.0"
    assert temp_registry._registry_data["models"] == {}

    # Registry file should be created after first save
    temp_registry._save_registry()
    assert temp_registry.registry_file.exists()


def test_register_model(temp_registry, sample_model_file):
    """Test model registration."""
    model_id = temp_registry.register_model(
        model_path=sample_model_file,
        name="test_model",
        architecture="simple",
        dataset_version="test_v1",
        hyperparameters={"lr": 0.001},
        performance_metrics={"accuracy": 0.95},
        description="Test model",
        tags=["test"],
    )

    assert model_id == "test_model_v1.0.0"
    assert model_id in temp_registry._registry_data["models"]

    # Check files were created
    model_dir = temp_registry.registry_dir / model_id
    assert model_dir.exists()
    assert (model_dir / f"{model_id}.pt").exists()
    assert (model_dir / f"{model_id}_config.json").exists()


def test_list_models(temp_registry, sample_model_file):
    """Test listing models."""
    # Register a model
    temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    models = temp_registry.list_models()
    assert len(models) == 1
    assert models[0].metadata.model_id == "test_model_v1.0.0"
    assert models[0].is_valid


def test_get_model(temp_registry, sample_model_file):
    """Test getting specific model."""
    model_id = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    model_info = temp_registry.get_model(model_id)
    assert model_info is not None
    assert model_info.metadata.model_id == model_id
    assert model_info.is_valid

    # Test non-existent model
    assert temp_registry.get_model("nonexistent") is None


def test_search_models(temp_registry, sample_model_file):
    """Test model search functionality."""
    # Register multiple models
    temp_registry.register_model(
        model_path=sample_model_file,
        name="resnet_model",
        architecture="resnet50",
        dataset_version="test_v1",
        hyperparameters={"lr": 0.001},
        performance_metrics={"accuracy": 0.95},
        tags=["vision", "resnet"],
    )

    temp_registry.register_model(
        model_path=sample_model_file,
        name="vit_model",
        architecture="vit",
        dataset_version="test_v1",
        hyperparameters={"lr": 0.001},
        performance_metrics={"accuracy": 0.90},
        tags=["vision", "transformer"],
    )

    # Search by architecture
    resnet_models = temp_registry.search_models(architecture="resnet50")
    assert len(resnet_models) == 1
    assert resnet_models[0].metadata.architecture == "resnet50"

    # Search by tags
    vision_models = temp_registry.search_models(tags=["vision"])
    assert len(vision_models) == 2

    # Search by minimum accuracy
    high_acc_models = temp_registry.search_models(min_accuracy=0.93)
    assert len(high_acc_models) == 1
    assert high_acc_models[0].metadata.performance_metrics["accuracy"] >= 0.93


def test_model_versioning(temp_registry, sample_model_file):
    """Test model versioning functionality."""
    # Register first version
    model_id_1 = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.90}
    )

    # Register second version (should auto-increment)
    model_id_2 = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    assert model_id_1 == "test_model_v1.0.0"
    assert model_id_2 == "test_model_v1.0.1"

    # Test getting versions
    versions = temp_registry.get_model_versions("test_model")
    assert len(versions) == 2
    assert versions[0].metadata.version == "1.0.1"  # Newest first
    assert versions[1].metadata.version == "1.0.0"

    # Test getting latest
    latest = temp_registry.get_latest_model("test_model")
    assert latest.metadata.version == "1.0.1"


def test_validate_model(temp_registry, sample_model_file):
    """Test model validation."""
    model_id = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    # Should be valid initially
    assert temp_registry.validate_model(model_id)

    # Should be invalid for non-existent model
    assert not temp_registry.validate_model("nonexistent")


def test_update_metadata(temp_registry, sample_model_file):
    """Test metadata updates."""
    model_id = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.90}
    )

    # Update metadata
    success = temp_registry.update_metadata(model_id, performance_metrics={"accuracy": 0.95, "f1_score": 0.94}, description="Updated model", tags=["updated", "test"])

    assert success

    # Verify updates
    model_info = temp_registry.get_model(model_id)
    assert model_info.metadata.performance_metrics["accuracy"] == 0.95
    assert model_info.metadata.performance_metrics["f1_score"] == 0.94
    assert model_info.metadata.description == "Updated model"
    assert "updated" in model_info.metadata.tags


def test_registry_persistence(sample_model_file):
    """Test registry persistence across instances."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create first registry instance
        registry1 = ModelRegistry(temp_dir)
        model_id = registry1.register_model(
            model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
        )

        # Create second registry instance (should load existing data)
        registry2 = ModelRegistry(temp_dir)
        models = registry2.list_models()
        assert len(models) == 1
        assert models[0].metadata.model_id == model_id


def test_checksum_calculation(temp_registry, sample_model_file):
    """Test checksum calculation and validation."""
    model_id = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    model_info = temp_registry.get_model(model_id)
    assert model_info.metadata.checksum
    assert len(model_info.metadata.checksum) == 64  # SHA256 hex length

    # Validation should pass
    assert temp_registry.validate_model(model_id)


def test_compare_models(temp_registry, sample_model_file):
    """Test model comparison functionality."""
    # Register multiple models
    model_id_1 = temp_registry.register_model(
        model_path=sample_model_file, name="model_a", architecture="resnet50", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.90, "f1_score": 0.88}
    )

    model_id_2 = temp_registry.register_model(
        model_path=sample_model_file, name="model_b", architecture="vit", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95, "f1_score": 0.92}
    )

    # Compare models
    comparison = temp_registry.compare_models([model_id_1, model_id_2])

    assert comparison.models
    assert len(comparison.models) == 2

    # Test best model selection
    best_accuracy = comparison.get_best_model("accuracy")
    assert best_accuracy.metadata.model_id == model_id_2

    # Test summary
    summary = comparison.get_summary()
    assert summary["total_models"] == 2
    assert "resnet50" in summary["architectures"]
    assert "vit" in summary["architectures"]
    assert summary["best_performers"]["accuracy"]["model"] == model_id_2


def test_delete_model(temp_registry, sample_model_file):
    """Test model deletion functionality."""
    # Register multiple versions
    model_id_1 = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.90}
    )

    model_id_2 = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    # Verify we have 2 versions
    versions = temp_registry.get_model_versions("test_model")
    assert len(versions) == 2

    # Should be able to delete when there are multiple versions
    success = temp_registry.delete_model(model_id_1)  # Should succeed
    assert success
    assert temp_registry.get_model(model_id_1) is None

    # Now we have only one version left, should not delete without force
    success = temp_registry.delete_model(model_id_2)  # Should fail
    assert not success
    assert temp_registry.get_model(model_id_2) is not None

    # Should delete with force
    success = temp_registry.delete_model(model_id_2, force=True)
    assert success
    assert temp_registry.get_model(model_id_2) is None


def test_backup_and_restore_model(temp_registry, sample_model_file):
    """Test model backup and restoration."""
    import tempfile

    # Register a model
    model_id = temp_registry.register_model(
        model_path=sample_model_file,
        name="test_model",
        architecture="simple",
        dataset_version="test_v1",
        hyperparameters={"lr": 0.001},
        performance_metrics={"accuracy": 0.95},
        description="Original model",
        tags=["test"],
    )

    with tempfile.TemporaryDirectory() as backup_dir:
        # Backup the model
        success = temp_registry.backup_model(model_id, backup_dir)
        assert success

        # Check backup files exist
        backup_path = Path(backup_dir)
        backup_dirs = list(backup_path.glob(f"{model_id}_backup_*"))
        assert len(backup_dirs) == 1

        backup_model_dir = backup_dirs[0]
        assert (backup_model_dir / "metadata.json").exists()
        assert len(list(backup_model_dir.glob("*.pt"))) == 1
        assert len(list(backup_model_dir.glob("*_config.json"))) == 1

        # Delete the original model
        temp_registry.delete_model(model_id, force=True)
        assert temp_registry.get_model(model_id) is None

        # Restore the model
        restored_id = temp_registry.restore_model(backup_model_dir)
        assert restored_id is not None

        # Verify restored model
        restored_model = temp_registry.get_model(restored_id)
        assert restored_model is not None
        assert restored_model.metadata.architecture == "simple"
        assert "restored" in restored_model.metadata.tags


def test_cleanup_old_models(temp_registry, sample_model_file):
    """Test cleanup of old model versions."""
    # Register multiple versions
    model_ids = []
    for i in range(5):
        model_id = temp_registry.register_model(
            model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.90 + i * 0.01}
        )
        model_ids.append(model_id)

    # Dry run cleanup (keep 3 versions)
    to_delete = temp_registry.cleanup_old_models(keep_versions=3, dry_run=True)
    assert len(to_delete) == 2  # Should delete 2 oldest versions

    # Verify models still exist
    for model_id in model_ids:
        assert temp_registry.get_model(model_id) is not None

    # Actual cleanup
    deleted = temp_registry.cleanup_old_models(keep_versions=3, dry_run=False)
    assert len(deleted) == 2

    # Verify only 3 versions remain
    remaining_models = temp_registry.get_model_versions("test_model")
    assert len(remaining_models) == 3

    # Verify newest versions were kept
    versions = [m.metadata.version for m in remaining_models]
    assert "1.0.4" in versions  # Newest
    assert "1.0.3" in versions
    assert "1.0.2" in versions
    assert "1.0.1" not in versions  # Should be deleted
    assert "1.0.0" not in versions  # Should be deleted


def test_model_comparison_dataframe(temp_registry, sample_model_file):
    """Test DataFrame conversion for model comparison."""
    # Register models
    model_id_1 = temp_registry.register_model(
        model_path=sample_model_file, name="model_a", architecture="resnet50", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.90, "f1_score": 0.88}
    )

    model_id_2 = temp_registry.register_model(
        model_path=sample_model_file, name="model_b", architecture="vit", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95, "f1_score": 0.92}
    )

    comparison = temp_registry.compare_models([model_id_1, model_id_2])

    # Test DataFrame conversion (will skip if pandas not available)
    df = comparison.to_dataframe()
    if df is not None:
        assert len(df) == 2
        assert "model_id" in df.columns
        assert "accuracy" in df.columns
        assert "f1_score" in df.columns


def test_export_model_pytorch(temp_registry, sample_model_file):
    """Test PyTorch model export."""
    import tempfile

    # Register a model
    model_id = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    with tempfile.TemporaryDirectory() as export_dir:
        # Export model
        export_path = temp_registry.export_model(model_id=model_id, export_format="pytorch", output_dir=export_dir)

        assert export_path is not None
        assert export_path.exists()
        assert export_path.suffix == ".pt"

        # Verify export contents
        export_data = torch.load(export_path)
        assert "model_state_dict" in export_data
        assert "config" in export_data
        assert "metadata" in export_data
        assert "export_info" in export_data
        assert export_data["export_info"]["format"] == "pytorch"


def test_create_deployment_package(temp_registry, sample_model_file):
    """Test deployment package creation."""
    import tempfile

    # Register a model
    model_id = temp_registry.register_model(
        model_path=sample_model_file,
        name="test_model",
        architecture="simple",
        dataset_version="test_v1",
        hyperparameters={"lr": 0.001},
        performance_metrics={"accuracy": 0.95},
        description="Test deployment model",
    )

    with tempfile.TemporaryDirectory() as package_dir:
        # Create deployment package
        package_path = temp_registry.create_deployment_package(model_id=model_id, package_dir=package_dir)

        assert package_path is not None
        assert package_path.exists()

        # Verify package contents
        assert (package_path / "model.pt").exists()
        assert (package_path / "config.json").exists()
        assert (package_path / "deployment.json").exists()
        assert (package_path / "README.md").exists()

        # Verify deployment metadata
        with open(package_path / "deployment.json") as f:
            deployment_info = json.load(f)

        assert deployment_info["model_id"] == model_id
        assert "model_metadata" in deployment_info
        assert "deployment_info" in deployment_info
        assert "dependencies" in deployment_info


def test_optimize_model_for_deployment(temp_registry, sample_model_file):
    """Test model optimization for deployment."""
    # Register a model
    model_id = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    # Optimize model
    optimized_id = temp_registry.optimize_model_for_deployment(model_id=model_id, optimization_level="standard")

    assert optimized_id is not None
    assert optimized_id != model_id
    assert "optimized" in optimized_id

    # Verify optimized model exists
    optimized_model = temp_registry.get_model(optimized_id)
    assert optimized_model is not None
    assert "optimized" in optimized_model.metadata.tags
    assert "standard" in optimized_model.metadata.tags


def test_export_unsupported_format(temp_registry, sample_model_file):
    """Test export with unsupported format."""
    # Register a model
    model_id = temp_registry.register_model(
        model_path=sample_model_file, name="test_model", architecture="simple", dataset_version="test_v1", hyperparameters={"lr": 0.001}, performance_metrics={"accuracy": 0.95}
    )

    # Try to export with unsupported format
    export_path = temp_registry.export_model(model_id=model_id, export_format="unsupported")

    assert export_path is None


def test_export_nonexistent_model(temp_registry):
    """Test export of non-existent model."""
    export_path = temp_registry.export_model(model_id="nonexistent_model", export_format="pytorch")

    assert export_path is None
