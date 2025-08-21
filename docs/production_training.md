# PlantGuard Production Training Guide

## Overview

This guide covers the complete production training pipeline for PlantGuard, including dataset management, training configuration, monitoring, model evaluation, and deployment. The production training system is designed to handle real-world datasets with robust error handling, comprehensive monitoring, and automated model management.

## Quick Start

### Prerequisites

1. **System Requirements**:
   - Python 3.11+
   - CUDA-compatible GPU (recommended) or Apple Silicon with MPS support
   - At least 16GB RAM
   - 50GB+ free disk space for datasets and models

2. **Installation**:
   ```bash
   # Clone and setup PlantGuard
   git clone <repository-url>
   cd plantguard
   make install
   ```

3. **Dataset Setup**:
   ```bash
   # Download and prepare the PlantVillage dataset
   make download-dataset
   make prepare-dataset
   make validate-dataset
   ```

### Basic Training Workflow

```bash
# Complete production training pipeline
make train-production

# Monitor training progress
make monitor-training

# Evaluate trained model
make evaluate-model

# List available models
make list-models
```

## Dataset Management

### Downloading Datasets

The system supports automatic PlantVillage dataset download:

```bash
# Download dataset from Kaggle (requires Kaggle API setup)
make download-dataset

# Check dataset status
make setup-dataset
```

**Kaggle API Setup**:
1. Create account at kaggle.com
2. Go to Account → API → Create New API Token
3. Place `kaggle.json` in `~/.kaggle/`
4. Set permissions: `chmod 600 ~/.kaggle/kaggle.json`

### Dataset Preparation

```bash
# Prepare dataset with train/validation split
make prepare-dataset

# Analyze dataset statistics
make analyze-dataset

# Validate dataset integrity
make validate-dataset
```

**Dataset Structure**:
```
data/processed/plantvillage/
├── train/
│   ├── Apple___Apple_scab/
│   ├── Apple___Black_rot/
│   └── ...
├── val/
│   ├── Apple___Apple_scab/
│   ├── Apple___Black_rot/
│   └── ...
└── dataset_info.json
```

### Dataset Configuration

Create custom dataset configurations in `config/dataset_config.json`:

```json
{
  "name": "plantvillage_custom",
  "train_ratio": 0.8,
  "val_ratio": 0.2,
  "random_seed": 42,
  "min_samples_per_class": 10,
  "image_formats": [".jpg", ".jpeg", ".png"],
  "quality_threshold": 0.95,
  "augmentation": {
    "enabled": true,
    "rotation": 15,
    "brightness": 0.2,
    "contrast": 0.2,
    "horizontal_flip": true
  }
}
```

## Training Configuration

### Basic Configuration

The system uses `config/training_config.json` for training parameters:

```json
{
  "experiment": {
    "name": "plantguard_production_v1",
    "description": "Production training with full PlantVillage dataset",
    "tags": ["production", "resnet50", "plantvillage"]
  },
  "model": {
    "architecture": "resnet50",
    "pretrained": true,
    "num_classes": 38,
    "freeze_backbone": false
  },
  "training": {
    "epochs": 100,
    "batch_size": 64,
    "learning_rate": 0.001,
    "optimizer": "adam",
    "scheduler": {
      "type": "step",
      "step_size": 30,
      "gamma": 0.1
    },
    "early_stopping": {
      "enabled": true,
      "patience": 15,
      "min_delta": 0.001
    }
  },
  "resources": {
    "device": "auto",
    "mixed_precision": true,
    "num_workers": 8,
    "pin_memory": true
  }
}
```

### Advanced Configuration Options

#### Optimizer Settings
```json
"optimizer": {
  "type": "adam",
  "lr": 0.001,
  "weight_decay": 1e-4,
  "betas": [0.9, 0.999]
}
```

#### Learning Rate Schedulers
```json
"scheduler": {
  "type": "cosine",
  "T_max": 100,
  "eta_min": 1e-6
}
```

#### Transfer Learning
```json
"transfer_learning": {
  "freeze_backbone": true,
  "unfreeze_epoch": 20,
  "backbone_lr_multiplier": 0.1
}
```

### Training Scenarios

#### Scenario 1: Quick Prototype Training
```json
{
  "training": {
    "epochs": 20,
    "batch_size": 32,
    "learning_rate": 0.01,
    "early_stopping": {"patience": 5}
  }
}
```

#### Scenario 2: High-Accuracy Production Training
```json
{
  "training": {
    "epochs": 200,
    "batch_size": 64,
    "learning_rate": 0.0001,
    "optimizer": "adamw",
    "scheduler": {"type": "cosine"},
    "early_stopping": {"patience": 25}
  }
}
```

#### Scenario 3: Memory-Constrained Training
```json
{
  "training": {
    "batch_size": 16,
    "gradient_accumulation_steps": 4,
    "mixed_precision": true
  },
  "resources": {
    "num_workers": 2
  }
}
```

## Training Execution

### Production Training Command

```bash
# Run complete production training pipeline
make train-production

# With custom configuration
make train-production CONFIG=config/custom_training.json

# Resume from checkpoint
make train-production RESUME=data/checkpoints/latest.pt
```

### Training Process

1. **Prerequisite Validation**:
   - Dataset availability and integrity
   - GPU/CPU resources
   - Disk space requirements
   - Configuration validation

2. **Training Initialization**:
   - Model architecture setup
   - Data loader configuration
   - Optimizer and scheduler initialization
   - Checkpoint directory creation

3. **Training Loop**:
   - Epoch-by-epoch training
   - Real-time metrics logging
   - Validation evaluation
   - Checkpoint saving
   - Early stopping monitoring

4. **Post-Training**:
   - Final model evaluation
   - Model registration
   - Training report generation

### Monitoring Training

#### TensorBoard Integration
```bash
# Launch TensorBoard
make monitor-training

# View specific experiment
tensorboard --logdir=runs/experiment_20240813_103000
```

#### Real-time Metrics
- Training/validation loss
- Accuracy per epoch
- Learning rate schedule
- Confusion matrices
- Sample predictions

#### Training Logs
```bash
# View training logs
tail -f logs/training_20240813_103000.log

# Check error logs
tail -f logs/error.log
```

## Model Evaluation

### Automatic Evaluation

After training completion, models are automatically evaluated:

```bash
# Evaluate latest trained model
make evaluate-model

# Evaluate specific model
make evaluate-model MODEL=plantguard_v1.0.0

# Compare multiple models
make compare-models MODELS="v1.0.0,v1.1.0,v1.2.0"
```

### Evaluation Metrics

The system generates comprehensive evaluation reports:

- **Classification Metrics**: Accuracy, Precision, Recall, F1-score per class
- **Confusion Matrix**: Visual representation of classification performance
- **ROC Curves**: Multi-class ROC analysis with AUC scores
- **Sample Predictions**: Visual inspection of model predictions
- **Performance Comparison**: Benchmarking against baseline models

### Evaluation Report Structure

```
reports/evaluation_plantguard_v1.0.0_20240813/
├── metrics.json
├── confusion_matrix.png
├── classification_report.txt
├── roc_curves.png
├── sample_predictions.html
└── performance_comparison.json
```

## Model Management

### Model Registry

The system maintains a versioned model registry:

```bash
# List all models
make list-models

# Get model details
python -m src.training.model_registry info plantguard_v1.0.0

# Delete old models
python -m src.training.model_registry cleanup --keep=5
```

### Model Versioning

Models follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Architecture changes, breaking compatibility
- **MINOR**: Performance improvements, new features
- **PATCH**: Bug fixes, minor improvements

### Model Export

```bash
# Export model for deployment
python -m src.training.model_registry export plantguard_v1.0.0 --format=onnx

# Create deployment package
python -m src.training.model_registry package plantguard_v1.0.0
```

## Integration with PlantGuard

### VisionAdapter Integration

Trained models automatically integrate with the existing VisionAdapter:

```python
from src.core.vision import VisionAdapter

# Load latest production model
adapter = VisionAdapter()
adapter.load_model("plantguard_v1.0.0")

# Make predictions
prediction, confidence = adapter.predict(image)
```

### Model Switching

```bash
# Switch to specific model version
python -m src.ui.model_switcher set plantguard_v1.0.0

# List available models in UI
python -m src.ui.model_switcher list
```

### Backward Compatibility

The system maintains backward compatibility:
- Legacy model format support
- Automatic migration tools
- Graceful fallback mechanisms

## Performance Optimization

### Hardware Optimization

#### GPU Optimization
```json
{
  "resources": {
    "device": "cuda",
    "mixed_precision": true,
    "compile_model": true,
    "channels_last": true
  }
}
```

#### Apple Silicon (MPS) Optimization
```json
{
  "resources": {
    "device": "mps",
    "mixed_precision": false,
    "num_workers": 4
  }
}
```

### Memory Optimization

#### Large Dataset Handling
```json
{
  "training": {
    "batch_size": 16,
    "gradient_accumulation_steps": 4,
    "dataloader_pin_memory": true,
    "dataloader_prefetch_factor": 2
  }
}
```

#### Memory Profiling
```bash
# Profile memory usage during training
python -m src.training.profiler memory --config=config/training_config.json
```

### Training Speed Optimization

#### Data Loading Optimization
```json
{
  "resources": {
    "num_workers": 8,
    "pin_memory": true,
    "persistent_workers": true,
    "prefetch_factor": 4
  }
}
```

#### Model Compilation (PyTorch 2.0+)
```json
{
  "model": {
    "compile": true,
    "compile_mode": "default"
  }
}
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Out of Memory (OOM) Errors
**Symptoms**: CUDA out of memory, training crashes
**Solutions**:
1. Reduce batch size: `"batch_size": 16`
2. Enable gradient accumulation: `"gradient_accumulation_steps": 4`
3. Use mixed precision: `"mixed_precision": true`
4. Reduce number of workers: `"num_workers": 2`

#### Issue: Slow Training Speed
**Symptoms**: Low GPU utilization, slow epoch times
**Solutions**:
1. Increase number of workers: `"num_workers": 8`
2. Enable pin memory: `"pin_memory": true`
3. Use persistent workers: `"persistent_workers": true`
4. Enable model compilation: `"compile": true`

#### Issue: Model Not Converging
**Symptoms**: Loss not decreasing, poor validation accuracy
**Solutions**:
1. Adjust learning rate: `"learning_rate": 0.0001`
2. Change optimizer: `"optimizer": "adamw"`
3. Add learning rate scheduler: `"scheduler": {"type": "cosine"}`
4. Increase training epochs: `"epochs": 200`

#### Issue: Dataset Loading Errors
**Symptoms**: File not found, corrupted images
**Solutions**:
1. Validate dataset: `make validate-dataset`
2. Re-download dataset: `make download-dataset`
3. Check file permissions and paths
4. Verify Kaggle API configuration

#### Issue: Checkpoint Loading Failures
**Symptoms**: Cannot resume training, model loading errors
**Solutions**:
1. Check checkpoint file integrity
2. Verify model architecture compatibility
3. Use `--force-resume` flag if necessary
4. Start fresh training if checkpoint is corrupted

### Debugging Tools

#### Training Logs
```bash
# View detailed training logs
tail -f logs/training_$(date +%Y%m%d).log

# Search for specific errors
grep -i "error\|exception" logs/training_*.log
```

#### Model Debugging
```bash
# Test model loading
python -c "from src.training.production_trainer import ProductionTrainer; trainer = ProductionTrainer.load_checkpoint('path/to/checkpoint.pt')"

# Validate model architecture
python -m src.training.model_validator --model=plantguard_v1.0.0
```

#### Performance Profiling
```bash
# Profile training performance
python -m src.training.profiler performance --config=config/training_config.json

# Memory usage analysis
python -m src.training.profiler memory --duration=10
```

### Getting Help

1. **Check Logs**: Always start by examining training and error logs
2. **Validate Configuration**: Ensure all configuration parameters are valid
3. **Test Components**: Test individual components (dataset, model, optimizer)
4. **Community Support**: Check GitHub issues and discussions
5. **Documentation**: Refer to this guide and API documentation

## Best Practices

### Training Best Practices

1. **Start Small**: Begin with a subset of data to validate the pipeline
2. **Monitor Early**: Watch training metrics from the first epoch
3. **Save Frequently**: Use automatic checkpointing every few epochs
4. **Validate Regularly**: Run validation evaluation throughout training
5. **Document Experiments**: Keep detailed records of configurations and results

### Model Management Best Practices

1. **Version Everything**: Models, datasets, configurations
2. **Test Before Deploy**: Comprehensive evaluation before production use
3. **Backup Models**: Keep copies of best-performing models
4. **Monitor Performance**: Track model performance over time
5. **Plan Rollbacks**: Have rollback procedures for failed deployments

### Performance Best Practices

1. **Profile First**: Identify bottlenecks before optimizing
2. **Optimize Data Loading**: Often the biggest performance bottleneck
3. **Use Mixed Precision**: Significant memory and speed improvements
4. **Batch Size Tuning**: Find optimal batch size for your hardware
5. **Regular Cleanup**: Remove old checkpoints and logs

## Advanced Topics

### Custom Model Architectures

To add custom model architectures:

1. **Define Architecture**:
   ```python
   # src/training/models/custom_model.py
   class CustomModel(nn.Module):
       def __init__(self, num_classes):
           super().__init__()
           # Define your architecture
   ```

2. **Register Model**:
   ```python
   # src/training/model_factory.py
   MODEL_REGISTRY["custom_model"] = CustomModel
   ```

3. **Update Configuration**:
   ```json
   {
     "model": {
       "architecture": "custom_model",
       "num_classes": 38
     }
   }
   ```

### Custom Loss Functions

```python
# src/training/losses/custom_loss.py
class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, inputs, targets):
        # Implement focal loss
        pass
```

### Distributed Training

For multi-GPU training:

```json
{
  "distributed": {
    "enabled": true,
    "backend": "nccl",
    "world_size": 4,
    "rank": 0
  }
}
```

### Hyperparameter Optimization

Using Optuna for automated hyperparameter tuning:

```bash
# Run hyperparameter optimization
python -m src.training.hyperopt --trials=100 --config=config/hyperopt_config.json
```

## Migration Guide

### From Legacy Training System

1. **Backup Existing Models**:
   ```bash
   cp -r data/models data/models_backup
   ```

2. **Run Migration Script**:
   ```bash
   python -m src.training.migrate_models --source=data/models_backup
   ```

3. **Validate Migration**:
   ```bash
   make validate-models
   ```

4. **Update Configurations**:
   - Convert old config files to new format
   - Update model paths in application code

### Updating from Previous Versions

1. **Check Compatibility**:
   ```bash
   python -m src.training.compatibility_check
   ```

2. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Migrate Configurations**:
   ```bash
   python -m src.training.config_migrator --version=1.0.0
   ```

## Conclusion

This production training guide provides comprehensive coverage of PlantGuard's training pipeline. For additional support, refer to the API documentation, check the troubleshooting section, or consult the community resources.

Remember to always validate your setup, monitor training progress, and maintain proper model versioning for successful production deployments.
