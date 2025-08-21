# PlantGuard Migration Guide

## Overview

This guide helps you migrate from previous versions of PlantGuard to the latest version with production training capabilities. The migration process ensures backward compatibility while enabling access to new features.

## Migration Scenarios

### Scenario 1: Fresh Installation (Recommended)

If you're setting up PlantGuard for the first time or can start fresh:

```bash
# Clone latest version
git clone https://github.com/arslanmit/PlantGuard.git
cd PlantGuard

# Complete setup
make setup

# Download and prepare dataset
make download-dataset
make prepare-dataset

# Run production training
make train-production
```

### Scenario 2: Upgrading Existing Installation

If you have an existing PlantGuard installation with models and data:

#### Step 1: Backup Existing Data

```bash
# Create backup directory
mkdir -p backup/$(date +%Y%m%d)

# Backup existing models
cp -r data/models backup/$(date +%Y%m%d)/models_backup

# Backup configurations
cp -r config backup/$(date +%Y%m%d)/config_backup

# Backup any custom datasets
cp -r data/processed backup/$(date +%Y%m%d)/data_backup
```

#### Step 2: Update Codebase

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run system validation
make validate
```

#### Step 3: Migrate Models

```bash
# Run model migration script
python -m src.training.model_migrator \
    --source=backup/$(date +%Y%m%d)/models_backup \
    --target=data/models

# Validate migrated models
make validate-models

# Update model registry
python -m src.training.model_registry rebuild
```

#### Step 4: Update Configurations

```bash
# Migrate training configurations
python -m src.training.config_migrator \
    --source=backup/$(date +%Y%m%d)/config_backup \
    --target=config

# Update VisionAdapter configuration
python -m src.core.vision_adapter update-config
```

#### Step 5: Validate Migration

```bash
# Test model loading
python -c "from src.core.vision import VisionAdapter; adapter = VisionAdapter(); print('✅ VisionAdapter working')"

# Test UI integration
make run --test-mode

# Run comprehensive validation
make health-check
```

## Version-Specific Migration Instructions

### From v1.0.x to v2.0.x (Production Training Update)

#### Breaking Changes

1. **Model Storage Format**: Models now use versioned registry format
2. **Configuration Schema**: Training configurations use new JSON schema
3. **Dataset Structure**: Enhanced dataset management with validation
4. **Command Interface**: New Makefile commands for production training

#### Migration Steps

1. **Update Model Format**:
   ```bash
   # Convert legacy models to registry format
   python -m src.training.model_migrator --legacy-format

   # Update class mappings
   python -m src.training.class_mapper --update-all
   ```

2. **Update Training Configurations**:
   ```bash
   # Convert old training scripts to new config format
   python -m src.training.config_migrator \
       --legacy-script=scripts/train_vision_model.py \
       --output=config/legacy_migrated.json
   ```

3. **Update Dataset Structure**:
   ```bash
   # Migrate dataset to new structure
   python -m src.data.dataset_migrator \
       --source=data/plantvillage \
       --target=data/processed/plantvillage

   # Validate migrated dataset
   make validate-dataset
   ```

4. **Update UI Integration**:
   ```bash
   # Update model switcher configuration
   python -m src.ui.model_switcher update-config

   # Test UI functionality
   make run --validate
   ```

### From v0.x to v1.x (Model Management Update)

#### Key Changes

1. **Multi-Model Support**: Added Vision Transformer and MobileNet models
2. **Model Switcher**: New UI for model management
3. **Hugging Face Integration**: Automatic model downloading
4. **Enhanced VisionAdapter**: Unified interface for all models

#### Migration Steps

1. **Update Model Configuration**:
   ```bash
   # Create new model configuration
   python -m src.core.model_manager create-config

   # Register existing models
   python -m src.core.model_manager register-legacy-models
   ```

2. **Test Model Switching**:
   ```bash
   # Launch model switcher
   make switcher

   # Test model switching functionality
   python -m src.core.model_manager test-switching
   ```

## Common Migration Issues

### Issue 1: Model Loading Failures

**Symptoms**: "Cannot load model" errors, incompatible model format

**Solution**:
```bash
# Check model compatibility
python -m src.training.model_compatibility --check-all

# Force model migration
python -m src.training.model_migrator --force-migrate

# Rebuild model registry
python -m src.training.model_registry rebuild
```

### Issue 2: Configuration Conflicts

**Symptoms**: Invalid configuration errors, missing parameters

**Solution**:
```bash
# Validate configurations
python -m src.utils.config_validator --check-all

# Reset to default configurations
python -m src.utils.config_manager --reset-defaults

# Merge custom configurations
python -m src.utils.config_manager --merge-custom
```

### Issue 3: Dataset Structure Mismatch

**Symptoms**: Dataset not found, invalid structure errors

**Solution**:
```bash
# Check dataset structure
make setup-dataset

# Migrate dataset structure
python -m src.data.dataset_migrator --auto-detect

# Regenerate dataset metadata
python -m src.data.dataset_manager --regenerate-metadata
```

### Issue 4: UI Integration Problems

**Symptoms**: Model switcher not working, UI crashes

**Solution**:
```bash
# Clear Streamlit cache
streamlit cache clear

# Update UI configurations
python -m src.ui.config_updater --update-all

# Restart UI services
make restart
```

## Post-Migration Validation

### Comprehensive System Check

```bash
# Run full system validation
make health-check

# Test all major components
python -m src.utils.system_tester --comprehensive

# Validate model performance
make evaluate-model --all-models
```

### Performance Benchmarking

```bash
# Benchmark training performance
python -m src.training.benchmark --compare-with-baseline

# Benchmark inference performance
python -m src.core.inference_benchmark --all-models

# Generate performance report
python -m src.utils.performance_reporter --migration-report
```

### Feature Testing

```bash
# Test production training pipeline
make train-production --test-run

# Test model management
make list-models
make switcher --test-mode

# Test dataset management
make validate-dataset
make analyze-dataset
```

## Rollback Procedures

### Emergency Rollback

If migration fails and you need to rollback:

```bash
# Stop all services
make stop

# Restore from backup
cp -r backup/$(date +%Y%m%d)/models_backup data/models
cp -r backup/$(date +%Y%m%d)/config_backup config
cp -r backup/$(date +%Y%m%d)/data_backup data/processed

# Checkout previous version
git checkout v1.0.0  # Replace with your previous version

# Reinstall dependencies
pip install -r requirements.txt

# Validate rollback
make validate
```

### Selective Rollback

To rollback specific components:

```bash
# Rollback models only
python -m src.training.model_migrator --rollback \
    --backup=backup/$(date +%Y%m%d)/models_backup

# Rollback configurations only
python -m src.utils.config_manager --rollback \
    --backup=backup/$(date +%Y%m%d)/config_backup

# Rollback dataset structure only
python -m src.data.dataset_migrator --rollback \
    --backup=backup/$(date +%Y%m%d)/data_backup
```

## Best Practices for Migration

### Pre-Migration Checklist

- [ ] **Backup all data**: Models, configurations, datasets
- [ ] **Document current setup**: Note custom configurations and modifications
- [ ] **Test in development**: Use a separate environment for testing
- [ ] **Check disk space**: Ensure sufficient space for migration
- [ ] **Update dependencies**: Ensure all requirements are met

### During Migration

- [ ] **Follow steps sequentially**: Don't skip validation steps
- [ ] **Monitor for errors**: Check logs for any issues
- [ ] **Test incrementally**: Validate each component after migration
- [ ] **Keep backups accessible**: Don't delete backups until validation complete

### Post-Migration

- [ ] **Comprehensive testing**: Test all major features
- [ ] **Performance validation**: Ensure performance meets expectations
- [ ] **Documentation update**: Update any custom documentation
- [ ] **Team training**: Ensure team knows about new features
- [ ] **Monitor production**: Watch for any issues in production use

## Getting Help

### Migration Support Resources

1. **Documentation**: Check the [Production Training Guide](production_training.md)
2. **Troubleshooting**: See the [Troubleshooting Guide](troubleshooting.md)
3. **GitHub Issues**: Report migration-specific issues
4. **Community Forum**: Ask questions about migration process

### Diagnostic Information

When reporting migration issues, include:

```bash
# System information
python -m src.utils.system_info > migration_system_info.txt

# Migration logs
tar -czf migration_logs.tar.gz logs/

# Configuration state
python -m src.utils.config_exporter > migration_config_state.json

# Model registry state
python -m src.training.model_registry export > migration_model_state.json
```

### Professional Migration Services

For complex migrations or production environments:
- **Migration consulting**: Expert guidance for complex setups
- **Custom migration scripts**: Tailored migration tools for specific needs
- **Production migration support**: Supervised migration for critical systems
- **Training and onboarding**: Team training on new features

## Conclusion

This migration guide provides comprehensive instructions for upgrading PlantGuard installations. The migration process is designed to be safe and reversible, with extensive validation and rollback procedures.

For most users, the automated migration tools will handle the upgrade process smoothly. However, complex custom setups may require manual intervention or professional support.

Remember to always backup your data before starting the migration process, and test thoroughly in a development environment before applying changes to production systems.
