# PlantGuard Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when using PlantGuard's production training pipeline. Issues are organized by category with symptoms, root causes, and step-by-step solutions.

## Quick Diagnosis

### System Health Check

Run the built-in diagnostic tool to identify common issues:

```bash
# Comprehensive system check
make health-check

# Check specific components
python -m src.utils.diagnostics --component=dataset
python -m src.utils.diagnostics --component=gpu
python -m src.utils.diagnostics --component=models
```

### Log Analysis

Check recent logs for errors:

```bash
# View latest training logs
tail -100 logs/training_$(date +%Y%m%d).log

# Search for errors across all logs
grep -r "ERROR\|CRITICAL" logs/ | tail -20

# Check system resource usage
python -m src.utils.system_monitor
```

## Dataset Issues

### Issue: Dataset Download Fails

**Symptoms**:
- `make download-dataset` fails with authentication errors
- "403 Forbidden" or "401 Unauthorized" messages
- Kaggle API connection timeouts

**Root Causes**:
- Missing or invalid Kaggle API credentials
- Network connectivity issues
- Kaggle dataset access restrictions

**Solutions**:

1. **Setup Kaggle API Credentials**:
   ```bash
   # Create Kaggle account and download API token
   mkdir -p ~/.kaggle
   cp kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   
   # Verify credentials
   kaggle datasets list --user=$(whoami)
   ```

2. **Check Network Connectivity**:
   ```bash
   # Test Kaggle API connection
   curl -H "Authorization: Bearer $(cat ~/.kaggle/kaggle.json | jq -r .key)" \
        https://www.kaggle.com/api/v1/datasets/list
   
   # Check DNS resolution
   nslookup www.kaggle.com
   ```

3. **Alternative Download Methods**:
   ```bash
   # Manual download and placement
   # 1. Download PlantVillage dataset manually from Kaggle
   # 2. Extract to data/raw/plantvillage/
   # 3. Run preparation
   make prepare-dataset
   ```

### Issue: Dataset Validation Fails

**Symptoms**:
- `make validate-dataset` reports corrupted files
- Training fails with "Image cannot be loaded" errors
- Inconsistent class counts

**Root Causes**:
- Corrupted image files during download
- Incomplete dataset extraction
- File permission issues

**Solutions**:

1. **Re-download Corrupted Files**:
   ```bash
   # Check which files are corrupted
   python -m src.data.dataset_validator --verbose
   
   # Re-download specific files
   python -m src.data.dataset_manager --repair-corrupted
   ```

2. **Fix File Permissions**:
   ```bash
   # Fix permissions recursively
   chmod -R 644 data/raw/plantvillage/
   chmod -R 755 data/raw/plantvillage/*/
   ```

3. **Manual Validation and Cleanup**:
   ```bash
   # Remove corrupted images
   find data/raw/plantvillage/ -name "*.jpg" -exec file {} \; | grep -v "JPEG image data" | cut -d: -f1 | xargs rm -f
   
   # Regenerate dataset info
   python -m src.data.dataset_manager --regenerate-info
   ```

### Issue: Insufficient Dataset Size

**Symptoms**:
- Training accuracy remains low
- "Insufficient samples per class" warnings
- Validation set too small

**Root Causes**:
- Dataset split ratios too aggressive
- Some classes have very few samples
- Data augmentation not enabled

**Solutions**:

1. **Adjust Split Ratios**:
   ```json
   // config/dataset_config.json
   {
     "train_ratio": 0.85,
     "val_ratio": 0.15,
     "min_samples_per_class": 5
   }
   ```

2. **Enable Data Augmentation**:
   ```json
   {
     "augmentation": {
       "enabled": true,
       "rotation": 30,
       "brightness": 0.3,
       "contrast": 0.3,
       "horizontal_flip": true,
       "vertical_flip": false,
       "zoom": 0.1
     }
   }
   ```

3. **Class Balancing**:
   ```bash
   # Analyze class distribution
   python -m src.data.class_analyzer --dataset=data/processed/plantvillage/
   
   # Apply class balancing
   python -m src.data.dataset_balancer --method=oversample
   ```

## Training Issues

### Issue: Out of Memory (OOM) Errors

**Symptoms**:
- "CUDA out of memory" errors
- Training process killed by system
- GPU memory usage at 100%

**Root Causes**:
- Batch size too large for available GPU memory
- Model too large for GPU
- Memory leaks in training loop

**Solutions**:

1. **Reduce Batch Size**:
   ```json
   // config/training_config.json
   {
     "training": {
       "batch_size": 16,  // Reduce from 64
       "gradient_accumulation_steps": 4  // Maintain effective batch size
     }
   }
   ```

2. **Enable Memory Optimization**:
   ```json
   {
     "resources": {
       "mixed_precision": true,
       "gradient_checkpointing": true,
       "empty_cache_frequency": 10
     }
   }
   ```

3. **Monitor Memory Usage**:
   ```bash
   # Real-time GPU memory monitoring
   watch -n 1 nvidia-smi
   
   # Memory profiling during training
   python -m src.training.memory_profiler --config=config/training_config.json
   ```

4. **Alternative Solutions**:
   ```bash
   # Use CPU training as fallback
   python -m src.training.production_trainer --device=cpu --batch-size=8
   
   # Use model parallelism for large models
   python -m src.training.production_trainer --model-parallel
   ```

### Issue: Training Not Converging

**Symptoms**:
- Loss plateaus at high values
- Validation accuracy remains low
- No improvement over many epochs

**Root Causes**:
- Learning rate too high or too low
- Poor model initialization
- Insufficient training data
- Model architecture mismatch

**Solutions**:

1. **Learning Rate Tuning**:
   ```bash
   # Find optimal learning rate
   python -m src.training.lr_finder --config=config/training_config.json
   
   # Use learning rate scheduler
   ```
   ```json
   {
     "training": {
       "learning_rate": 0.0001,  // Reduce if too high
       "scheduler": {
         "type": "reduce_on_plateau",
         "patience": 10,
         "factor": 0.5
       }
     }
   }
   ```

2. **Optimizer Adjustments**:
   ```json
   {
     "training": {
       "optimizer": "adamw",
       "weight_decay": 0.01,
       "betas": [0.9, 0.999]
     }
   }
   ```

3. **Model Architecture Review**:
   ```bash
   # Validate model architecture
   python -m src.training.model_validator --architecture=resnet50 --num-classes=38
   
   # Try different architectures
   python -m src.training.architecture_search --dataset=plantvillage
   ```

### Issue: Training Speed Too Slow

**Symptoms**:
- Very slow epoch times
- Low GPU utilization
- High CPU usage during training

**Root Causes**:
- Data loading bottleneck
- Inefficient data preprocessing
- Suboptimal hardware utilization

**Solutions**:

1. **Optimize Data Loading**:
   ```json
   {
     "resources": {
       "num_workers": 8,  // Increase based on CPU cores
       "pin_memory": true,
       "persistent_workers": true,
       "prefetch_factor": 4
     }
   }
   ```

2. **Profile Training Performance**:
   ```bash
   # Identify bottlenecks
   python -m src.training.profiler --mode=performance
   
   # Data loading profiling
   python -m src.data.dataloader_profiler
   ```

3. **Hardware Optimization**:
   ```json
   {
     "model": {
       "compile": true,  // PyTorch 2.0+ compilation
       "channels_last": true  // Memory layout optimization
     },
     "resources": {
       "mixed_precision": true,
       "device": "cuda"  // Ensure GPU usage
     }
   }
   ```

### Issue: Checkpoint Loading Failures

**Symptoms**:
- "Cannot load checkpoint" errors
- Training cannot resume from checkpoint
- Model architecture mismatch errors

**Root Causes**:
- Corrupted checkpoint files
- Model architecture changes
- PyTorch version incompatibility

**Solutions**:

1. **Validate Checkpoint Integrity**:
   ```bash
   # Check checkpoint file
   python -c "import torch; print(torch.load('path/to/checkpoint.pt', map_location='cpu').keys())"
   
   # Repair corrupted checkpoint
   python -m src.training.checkpoint_repair --checkpoint=path/to/checkpoint.pt
   ```

2. **Architecture Compatibility**:
   ```bash
   # Check model compatibility
   python -m src.training.model_compatibility --checkpoint=path/to/checkpoint.pt --config=config/training_config.json
   
   # Force architecture update
   python -m src.training.checkpoint_migrator --checkpoint=path/to/checkpoint.pt --target-arch=resnet50
   ```

3. **Manual Recovery**:
   ```bash
   # Extract model weights only
   python -m src.training.weight_extractor --checkpoint=path/to/checkpoint.pt --output=weights_only.pt
   
   # Start fresh training with pretrained weights
   python -m src.training.production_trainer --pretrained-weights=weights_only.pt
   ```

## Model Issues

### Issue: Model Loading Failures

**Symptoms**:
- "Model file not found" errors
- VisionAdapter initialization failures
- Incompatible model format errors

**Root Causes**:
- Missing model files
- Incorrect model paths
- Version compatibility issues

**Solutions**:

1. **Verify Model Files**:
   ```bash
   # List available models
   make list-models
   
   # Check model file integrity
   python -m src.training.model_registry validate --model=plantguard_v1.0.0
   ```

2. **Fix Model Paths**:
   ```bash
   # Update model registry
   python -m src.training.model_registry update-paths
   
   # Regenerate model index
   python -m src.training.model_registry reindex
   ```

3. **Model Migration**:
   ```bash
   # Migrate old model format
   python -m src.training.model_migrator --source=data/models/old_format/ --target=data/models/
   
   # Update VisionAdapter configuration
   python -m src.core.vision_adapter update-config
   ```

### Issue: Poor Model Performance

**Symptoms**:
- Low accuracy on validation set
- High false positive/negative rates
- Inconsistent predictions

**Root Causes**:
- Insufficient training data
- Poor data quality
- Suboptimal hyperparameters
- Model overfitting

**Solutions**:

1. **Data Quality Analysis**:
   ```bash
   # Analyze dataset quality
   python -m src.data.quality_analyzer --dataset=data/processed/plantvillage/
   
   # Remove low-quality images
   python -m src.data.quality_filter --threshold=0.8
   ```

2. **Hyperparameter Optimization**:
   ```bash
   # Automated hyperparameter tuning
   python -m src.training.hyperopt --trials=50 --metric=val_accuracy
   
   # Manual parameter sweep
   python -m src.training.param_sweep --param=learning_rate --values="0.001,0.0001,0.00001"
   ```

3. **Model Evaluation and Debugging**:
   ```bash
   # Detailed model evaluation
   make evaluate-model MODEL=plantguard_v1.0.0
   
   # Confusion matrix analysis
   python -m src.training.confusion_analyzer --model=plantguard_v1.0.0
   
   # Prediction confidence analysis
   python -m src.training.confidence_analyzer --model=plantguard_v1.0.0
   ```

## System Issues

### Issue: GPU Not Detected

**Symptoms**:
- Training falls back to CPU
- "CUDA not available" warnings
- Slow training performance

**Root Causes**:
- CUDA drivers not installed
- PyTorch CPU-only version installed
- GPU hardware issues

**Solutions**:

1. **Verify GPU and CUDA**:
   ```bash
   # Check GPU status
   nvidia-smi
   
   # Check CUDA installation
   nvcc --version
   
   # Test PyTorch CUDA support
   python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.device_count())"
   ```

2. **Install CUDA Support**:
   ```bash
   # Install CUDA-enabled PyTorch
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   
   # Verify installation
   python -c "import torch; print(torch.version.cuda)"
   ```

3. **Apple Silicon (MPS) Support**:
   ```bash
   # Check MPS availability
   python -c "import torch; print(torch.backends.mps.is_available())"
   
   # Configure for MPS
   export PYTORCH_ENABLE_MPS_FALLBACK=1
   ```

### Issue: Disk Space Errors

**Symptoms**:
- "No space left on device" errors
- Training stops unexpectedly
- Cannot save checkpoints

**Root Causes**:
- Insufficient disk space
- Large checkpoint files accumulating
- Log files growing too large

**Solutions**:

1. **Check Disk Usage**:
   ```bash
   # Check available space
   df -h
   
   # Find large files
   du -sh data/* logs/* runs/*
   
   # Identify space usage by component
   python -m src.utils.disk_analyzer
   ```

2. **Clean Up Files**:
   ```bash
   # Clean old checkpoints
   python -m src.training.checkpoint_cleaner --keep=5
   
   # Clean old logs
   find logs/ -name "*.log" -mtime +30 -delete
   
   # Clean TensorBoard runs
   python -m src.training.tensorboard_cleaner --keep-days=30
   ```

3. **Configure Storage Limits**:
   ```json
   {
     "storage": {
       "max_checkpoints": 5,
       "checkpoint_frequency": 10,
       "log_rotation": true,
       "max_log_size": "100MB"
     }
   }
   ```

### Issue: Permission Errors

**Symptoms**:
- "Permission denied" errors
- Cannot write to directories
- Model files cannot be accessed

**Root Causes**:
- Incorrect file permissions
- Ownership issues
- Read-only file systems

**Solutions**:

1. **Fix Permissions**:
   ```bash
   # Fix data directory permissions
   chmod -R 755 data/
   chmod -R 644 data/**/*.json data/**/*.pt
   
   # Fix log directory permissions
   chmod -R 755 logs/
   chmod -R 644 logs/*.log
   ```

2. **Check Ownership**:
   ```bash
   # Check file ownership
   ls -la data/ logs/
   
   # Fix ownership if needed
   sudo chown -R $(whoami):$(whoami) data/ logs/
   ```

## Integration Issues

### Issue: VisionAdapter Integration Failures

**Symptoms**:
- Model switching doesn't work
- Predictions return errors
- UI cannot load models

**Root Causes**:
- Model format incompatibility
- Missing class mappings
- Configuration mismatches

**Solutions**:

1. **Validate Integration**:
   ```bash
   # Test VisionAdapter with new model
   python -c "from src.core.vision import VisionAdapter; adapter = VisionAdapter(); adapter.load_model('plantguard_v1.0.0')"
   
   # Test prediction pipeline
   python -m src.core.vision_adapter test --model=plantguard_v1.0.0 --image=test_image.jpg
   ```

2. **Update Class Mappings**:
   ```bash
   # Regenerate class mappings
   python -m src.training.class_mapper --model=plantguard_v1.0.0
   
   # Validate class consistency
   python -m src.training.class_validator --model=plantguard_v1.0.0
   ```

3. **Configuration Sync**:
   ```bash
   # Sync model configurations
   python -m src.training.config_sync --model=plantguard_v1.0.0
   
   # Update UI model list
   python -m src.ui.model_updater
   ```

### Issue: Streamlit UI Problems

**Symptoms**:
- UI crashes when loading models
- Slow prediction responses
- Memory leaks in UI

**Root Causes**:
- Model caching issues
- Memory management problems
- Session state corruption

**Solutions**:

1. **Clear Streamlit Cache**:
   ```bash
   # Clear Streamlit cache
   streamlit cache clear
   
   # Restart Streamlit server
   pkill -f streamlit
   streamlit run app.py
   ```

2. **Fix Memory Issues**:
   ```python
   # In Streamlit app, add memory management
   import gc
   
   @st.cache_resource
   def load_models():
       return VisionAdapter()
   
   # Clear memory after predictions
   if st.button("Clear Memory"):
       gc.collect()
       torch.cuda.empty_cache()
   ```

3. **Session State Management**:
   ```python
   # Reset session state
   if st.button("Reset Session"):
       for key in st.session_state.keys():
           del st.session_state[key]
       st.experimental_rerun()
   ```

## Performance Issues

### Issue: Slow Inference Speed

**Symptoms**:
- Long prediction times
- UI becomes unresponsive
- High CPU usage during inference

**Root Causes**:
- Model not optimized for inference
- Inefficient preprocessing
- CPU-only inference

**Solutions**:

1. **Model Optimization**:
   ```bash
   # Optimize model for inference
   python -m src.training.model_optimizer --model=plantguard_v1.0.0 --target=inference
   
   # Convert to TorchScript
   python -m src.training.torchscript_converter --model=plantguard_v1.0.0
   ```

2. **Preprocessing Optimization**:
   ```python
   # Optimize image preprocessing
   from torchvision import transforms
   
   transform = transforms.Compose([
       transforms.Resize((224, 224)),
       transforms.ToTensor(),
       transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                          std=[0.229, 0.224, 0.225])
   ])
   ```

3. **Hardware Acceleration**:
   ```bash
   # Ensure GPU inference
   python -c "from src.core.vision import VisionAdapter; adapter = VisionAdapter(); print(adapter.device)"
   
   # Enable mixed precision inference
   python -m src.core.vision_adapter --enable-amp
   ```

## Monitoring and Logging

### Issue: Missing Training Logs

**Symptoms**:
- No training logs generated
- TensorBoard shows no data
- Cannot track training progress

**Root Causes**:
- Logging configuration issues
- Permission problems
- Disk space issues

**Solutions**:

1. **Check Logging Configuration**:
   ```python
   # Verify logging setup
   import logging
   logger = logging.getLogger('plantguard')
   print(logger.handlers)
   print(logger.level)
   ```

2. **Fix Log Directory**:
   ```bash
   # Create log directories
   mkdir -p logs runs
   chmod 755 logs runs
   
   # Test logging
   python -c "import logging; logging.basicConfig(filename='logs/test.log', level=logging.INFO); logging.info('Test message')"
   ```

3. **TensorBoard Issues**:
   ```bash
   # Check TensorBoard logs
   ls -la runs/
   
   # Launch TensorBoard with specific logdir
   tensorboard --logdir=runs --host=0.0.0.0 --port=6006
   
   # Clear corrupted TensorBoard data
   rm -rf runs/corrupted_experiment/
   ```

## Emergency Procedures

### Complete System Reset

If multiple issues persist, perform a complete reset:

```bash
# 1. Backup important data
cp -r data/models data/models_backup_$(date +%Y%m%d)
cp -r config config_backup_$(date +%Y%m%d)

# 2. Clean all generated files
make clean-all

# 3. Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 4. Re-download and prepare dataset
make download-dataset
make prepare-dataset

# 5. Validate system
make health-check

# 6. Run basic training test
make train-test
```

### Recovery from Corrupted State

```bash
# 1. Stop all training processes
pkill -f "python.*training"

# 2. Clear temporary files
rm -rf /tmp/plantguard_*
rm -rf data/temp/*

# 3. Reset model registry
python -m src.training.model_registry reset

# 4. Rebuild dataset index
python -m src.data.dataset_manager rebuild-index

# 5. Validate and restart
make validate-system
```

## Getting Additional Help

### Diagnostic Information Collection

When reporting issues, collect this diagnostic information:

```bash
# System information
python -m src.utils.system_info > system_info.txt

# Training logs
tar -czf training_logs.tar.gz logs/

# Configuration files
tar -czf configs.tar.gz config/

# Model registry state
python -m src.training.model_registry export > model_registry.json
```

### Community Resources

1. **GitHub Issues**: Report bugs and feature requests
2. **Documentation**: Check latest documentation updates
3. **Community Forum**: Ask questions and share solutions
4. **Stack Overflow**: Search for similar issues with `plantguard` tag

### Professional Support

For production deployments requiring professional support:
- Enterprise support packages available
- Custom training and optimization services
- On-site deployment assistance
- Performance tuning consultations

## Preventive Measures

### Regular Maintenance

```bash
# Weekly maintenance script
#!/bin/bash
# Clean old logs
find logs/ -name "*.log" -mtime +7 -delete

# Clean old checkpoints
python -m src.training.checkpoint_cleaner --keep=10

# Validate system health
make health-check

# Update model registry
python -m src.training.model_registry cleanup
```

### Monitoring Setup

```bash
# Setup automated monitoring
python -m src.utils.monitor_setup --alerts=email --threshold=disk:80%,memory:90%

# Schedule regular health checks
echo "0 2 * * * cd /path/to/plantguard && make health-check" | crontab -
```

### Backup Strategy

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backup/plantguard/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup models
cp -r data/models $BACKUP_DIR/
# Backup configurations
cp -r config $BACKUP_DIR/
# Backup training logs
cp -r logs $BACKUP_DIR/

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

This troubleshooting guide should help resolve most common issues encountered with PlantGuard's production training pipeline. Keep this guide updated as new issues and solutions are discovered.