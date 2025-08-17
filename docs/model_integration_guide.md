# PlantGuard Model Integration Guide

## Overview

This guide explains how the new production training pipeline integrates with existing PlantGuard components, providing seamless model management and backward compatibility.

## Integration Components

### 1. VisionAdapter Integration

The `VisionAdapter` class now supports loading models from the new registry format:

```python
from src.core.vision import VisionAdapter

# Load from registry
adapter = VisionAdapter()
adapter.load_from_registry("plantguard_v1.0.0")

# Check compatibility
is_compatible = adapter.is_compatible_with_registry_format("model.pt")

# Migrate legacy model
adapter.migrate_legacy_model("legacy.pt", "migrated.pt")
```

### 2. Model Manager Integration

The `PlantGuardModelManager` automatically syncs with the registry:

```python
from src.features.model_switching.model_manager import PlantGuardModelManager

manager = PlantGuardModelManager()

# Sync with registry
manager.sync_with_registry()

# Get registry models
registry_models = manager.get_registry_models()

# Migrate legacy models
migrated = manager.migrate_legacy_models()
```

### 3. Model Switcher Updates

The model switcher script now supports registry models:

```bash
# List all models (including registry)
python scripts/model_switching/model_switcher.py --list

# Switch to registry model
python scripts/model_switching/model_switcher.py --switch plantguard_v1.0.0

# Sync configuration
python scripts/model_switching/model_switcher.py --sync
```

## Migration Process

### Automatic Migration

Use the migration utility to upgrade legacy models:

```bash
# Scan for legacy models
python scripts/migrate_models.py --scan

# Migrate all legacy models
python scripts/migrate_models.py --migrate-all

# Migrate specific model
python scripts/migrate_models.py --migrate path/to/model.pt
```

### Manual Migration

For custom migration scenarios:

```python
from src.core.vision import VisionAdapter
from src.training.model_registry import ModelRegistry

adapter = VisionAdapter()
registry = ModelRegistry()

# Migrate model file
adapter.migrate_legacy_model("legacy.pt", "migrated.pt")

# Register in registry
model_id = registry.register_model(
    model_path="migrated.pt",
    name="migrated_model",
    architecture="resnet50",
    dataset_version="legacy",
    hyperparameters={},
    performance_metrics={"accuracy": 0.0},
    description="Migrated legacy model"
)
```

## Makefile Commands

New commands for model management:

```bash
# Migration and sync
make migrate-models    # Migrate all legacy models
make sync-models      # Sync configuration with registry
make switch-model MODEL_ID=model_name  # Switch to specific model

# Aliases
make mm               # migrate-models
make sm               # sync-models
```

## Backward Compatibility

The integration maintains full backward compatibility:

1. **Legacy Models**: Existing model files continue to work
2. **Configuration**: Old model configurations are preserved
3. **UI Components**: Existing UI components work with new models
4. **API Compatibility**: All existing APIs remain unchanged

## Configuration Format

Registry models in model manager configuration:

```json
{
  "models": {
    "registry_model": {
      "name": "Production Model v1.0.0",
      "type": "local",
      "model_id": "registry:plantguard_v1.0.0",
      "description": "Production model from registry",
      "accuracy": 0.95,
      "confidence_threshold": 0.7,
      "enabled": true,
      "device": "auto"
    }
  }
}
```

## Best Practices

1. **Always migrate legacy models** before using new features
2. **Sync regularly** to pick up new registry models
3. **Use registry models** for production deployments
4. **Test migrations** in development environment first
5. **Backup models** before migration

## Troubleshooting

### Common Issues

1. **Model not found**: Run `make sync-models` to update configuration
2. **Migration fails**: Check model file integrity and format
3. **Loading errors**: Verify model compatibility and dependencies
4. **Performance issues**: Use registry models for better optimization

### Debug Commands

```bash
# Check model status
python scripts/model_switching/model_switcher.py --current

# List all models
make list-models

# Test model loading
python scripts/model_switching/model_switcher.py --test image.jpg
```