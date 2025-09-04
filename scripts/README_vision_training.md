# PlantGuard Vision Training Guide

This guide explains how to train PlantGuard vision models
 using the production training pipeline with ResNet50 architecture and advanced features.                         
## Prerequisites

1. **Dataset**: PlantVillage dataset with train/val split
 (automatic download available)                          2. **Dependencies**: Install requirements from `requireme
nts.txt`                                                 3. **Hardware**: GPU recommended for faster training (CPU
 and Apple Silicon MPS supported)                        4. **Kaggle API**: For automatic dataset download (option
al)                                                      
## Dataset Preparation

### Automated Dataset Management (Recommended)

```bash
# Check dataset status and get guidance
make setup-dataset

# Download PlantVillage dataset automatically (requires K
aggle API)                                               make download-dataset

# Prepare dataset with train/val splits
make prepare-dataset

# Validate dataset integrity
make validate-dataset

# Analyze dataset statistics
make analyze-dataset
```

### Manual Dataset Preparation

```bash
# Split dataset into train/val using DatasetManager
python scripts/prepare_dataset_new.py \
    --source_dir /path/to/plantvillage/raw \
    --output_dir data/processed/plantvillage \
    --train_ratio 0.8

# Validate dataset structure
python scripts/validate_dataset.py \
    --dataset_dir data/processed/plantvillage

# Generate comprehensive dataset analysis
python scripts/analyze_dataset.py \
    --dataset_dir data/processed/plantvillage
```

### Kaggle API Setup (for automatic download)

```bash
# 1. Install Kaggle API
pip install kaggle

# 2. Get API token from https://www.kaggle.com/account
# 3. Place kaggle.json in ~/.kaggle/
mkdir -p ~/.kaggle
cp kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# 4. Test API access
kaggle datasets list

# 5. Download PlantVillage dataset
make download-dataset
```

## Production Training

### Complete Production Pipeline (Recommended)

```bash
# Run complete production training with optimal settings
make train-production

# Monitor training progress in real-time
make monitor-training

# Evaluate trained model
make evaluate-model

# List all available models
make list-models
```

### Advanced Production Training Options

```bash
# Custom configuration
make train-production CONFIG=config/high_performance.json

# Resume from checkpoint
make train-production RESUME=data/checkpoints/latest.pt

# Memory-efficient training
make train-production CONFIG=config/memory_efficient.json
```

### Training Configuration Examples

**High-Performance Training** (`config/high_performance.j
son`):                                                   ```json
{
  "experiment": {
    "name": "plantguard_high_performance",
    "description": "Optimized for maximum training speed"
  },
  "training": {
    "epochs": 100,
    "batch_size": 128,
    "learning_rate": 0.01,
    "optimizer": "adamw",
    "scheduler": {
      "type": "onecycle",
      "max_lr": 0.01
    }
  },
  "resources": {
    "mixed_precision": true,
    "compile_model": true,
    "num_workers": 12
  }
}
```

**Memory-Efficient Training** (`config/memory_efficient.j
son`):                                                   ```json
{
  "training": {
    "batch_size": 16,
    "gradient_accumulation_steps": 8,
    "mixed_precision": true
  },
  "optimization": {
    "gradient_checkpointing": true,
    "memory_efficient": true
  }
}
```

### Legacy Training (Basic)

```bash
# Basic training with original script
python scripts/train_vision_model.py \
    --data_dir data/processed/plantvillage \
    --save_dir data/models \
    --epochs 50 \
    --batch_size 32

# Advanced options
python scripts/train_vision_model_improved.py \
    --data_dir data/processed/plantvillage \
    --save_dir data/models \
    --epochs 100 \
    --batch_size 64 \
    --learning_rate 0.0001 \
    --weight_decay 1e-4 \
    --device cuda \
    --num_workers 8
```

## Training Monitoring & Visualization

### TensorBoard Integration

```bash
# Launch TensorBoard automatically
make monitor-training

# Manual TensorBoard launch
tensorboard --logdir runs --host 0.0.0.0 --port 6006

# View specific experiment
tensorboard --logdir runs/experiment_20240813_103000
```

### Comprehensive Training Metrics

The production training system logs:
- **Training/Validation Loss** per epoch with smoothed cu
rves                                                     - **Accuracy Metrics** including per-class precision, rec
all, F1-score                                            - **Learning Rate Schedule** with automatic adjustment
- **Confusion Matrices** updated each epoch
- **Sample Predictions** with confidence scores and visua
l inspection                                             - **Model Performance** comparison against baseline model
s                                                        - **Resource Utilization** including GPU memory and train
ing speed                                                - **Gradient Statistics** and weight distributions

### Real-Time Progress Tracking

```bash
# View training logs in real-time
tail -f logs/training_$(date +%Y%m%d).log

# Monitor GPU usage
watch -n 1 nvidia-smi

# Check training status
python -m src.training.training_status
```

### Performance Profiling

```bash
# Profile training performance
python -m src.training.profiler --mode=performance

# Memory usage analysis
python -m src.training.profiler --mode=memory

# Data loading bottleneck analysis
python -m src.data.dataloader_profiler
```

## Model Management & Registry

### Model Registry Structure

After production training, models are stored in a version
ed registry:                                             
```
data/models/
├── plantguard_v1.0.0.pt           # Versioned model chec
kpoint                                                   ├── plantguard_v1.0.0_config.json  # Training configurati
on                                                       ├── plantguard_v1.0.0_classes.json # Class mapping
├── plantguard_v1.0.0_metadata.json # Performance metrics
 and training details                                    ├── checkpoints/                    # Training checkpoint
s                                                        │   ├── epoch_010.pt
│   ├── epoch_020.pt
│   └── latest.pt
└── registry.json                   # Model registry inde
x                                                        ```

### Model Registry Commands

```bash
# List all models with performance metrics
make list-models

# Get detailed model information
python -m src.training.model_registry info plantguard_v1.
0.0                                                       
# Compare model performance
python -m src.training.model_registry compare plantguard_
v1.0.0 plantguard_v1.1.0                                 
# Export model for deployment
python -m src.training.model_registry export plantguard_v
1.0.0 --format=onnx                                      
# Clean up old models
python -m src.training.model_registry cleanup --keep=5
```

### Model Versioning

Models follow semantic versioning:
- **MAJOR**: Architecture changes, breaking compatibility
- **MINOR**: Performance improvements, new features
- **PATCH**: Bug fixes, minor improvements

Example: `plantguard_v1.2.3`

## Using Trained Models

### VisionAdapter Integration

```python
from src.core.vision import VisionAdapter
from PIL import Image

# Load model from registry (automatic)
adapter = VisionAdapter()
adapter.load_model("plantguard_v1.0.0")

# Or load latest model
adapter.load_latest_model()

# Predict with comprehensive output
image = Image.open("test_image.jpg")
raw_class, readable_name, confidence, plant_type = adapte
r.predict_with_readable_name(image)                      
print(f"Plant: {plant_type}")
print(f"Disease: {readable_name}")
print(f"Confidence: {confidence:.2%}")
print(f"Raw class: {raw_class}")
```

### Model Switching in UI

```python
# Hot model switching in Streamlit
from src.ui.model_switcher import ModelSwitcher

switcher = ModelSwitcher()

# List available models
models = switcher.list_models()

# Switch to specific model
switcher.switch_model("plantguard_v1.1.0")

# Get current model info
current_model = switcher.get_current_model()
print(f"Current model: {current_model['name']} (Accuracy:
 {current_model['accuracy']:.1%})")                      ```

### Batch Prediction

```python
from src.core.vision import VisionAdapter
from pathlib import Path

adapter = VisionAdapter()
adapter.load_model("plantguard_v1.0.0")

# Batch prediction for multiple images
image_paths = list(Path("test_images/").glob("*.jpg"))
results = adapter.predict_batch([Image.open(p) for p in i
mage_paths])                                             
for path, (disease, confidence) in zip(image_paths, resul
ts):                                                         print(f"{path.name}: {disease} ({confidence:.1%})")
```

## Model Evaluation & Testing

### Comprehensive Model Evaluation

```bash
# Evaluate trained model with detailed metrics
make evaluate-model

# Evaluate specific model
make evaluate-model MODEL=plantguard_v1.0.0

# Compare multiple models
make compare-models MODELS="v1.0.0,v1.1.0,v1.2.0"
```

### Testing Scripts

```bash
# Test VisionAdapter implementation
python scripts/test_vision_adapter.py

# Test production training pipeline
python -m src.training.test_production_trainer

# Benchmark model performance
python -m src.training.benchmark_models

# Cross-platform compatibility test
python tests/test_cross_platform_compatibility.py
```

### Evaluation Metrics

The evaluation system provides:
- **Classification Report**: Precision, recall, F1-score 
per class                                                - **Confusion Matrix**: Visual representation of classifi
cation performance                                       - **ROC Curves**: Multi-class ROC analysis with AUC score
s                                                        - **Sample Predictions**: Visual inspection with confiden
ce scores                                                - **Performance Comparison**: Benchmarking against baseli
ne models                                                - **Error Analysis**: Detailed analysis of misclassified 
samples                                                  
## Troubleshooting & Performance Optimization

### Common Issues & Solutions

1. **CUDA out of memory**:
   - Use `CONFIG=config/memory_efficient.json`
   - Enable gradient accumulation: `"gradient_accumulatio
n_steps": 4`                                                - Reduce batch size: `"batch_size": 16`

2. **Dataset not found**:
   - Run `make setup-dataset` for status and guidance
   - Use `make download-dataset` for automatic download

3. **Low accuracy**:
   - Increase epochs: `"epochs": 200`
   - Use learning rate scheduler: `"scheduler": {"type": 
"cosine"}`                                                  - Enable transfer learning: `"freeze_backbone": true`

4. **Slow training**:
   - Enable mixed precision: `"mixed_precision": true`
   - Use model compilation: `"compile_model": true`
   - Increase workers: `"num_workers": 8`

### Performance Optimization

**Hardware-Specific Optimization**:
```bash
# NVIDIA GPU optimization
make train-production CONFIG=config/nvidia_optimized.json

# Apple Silicon (MPS) optimization
make train-production CONFIG=config/apple_silicon.json

# CPU optimization
make train-production CONFIG=config/cpu_optimized.json
```

**Memory Optimization**:
- **Gradient Checkpointing**: Trades compute for memory
- **Mixed Precision**: 50% memory reduction with minimal 
accuracy loss                                            - **Dynamic Batch Size**: Automatic adjustment based on a
available memory                                          - **Memory Profiling**: Identify and resolve memory bottl
enecks                                                   
**Speed Optimization**:
- **Model Compilation**: PyTorch 2.0+ compilation for 20-
30% speedup                                              - **Data Loading**: Multi-process loading with prefetchin
g                                                        - **Transfer Learning**: Progressive unfreezing for faste
r convergence                                            - **Learning Rate Scheduling**: OneCycle for faster train
ing                                                      
## Model Architecture

- **Backbone**: ResNet50 (ImageNet pre-trained)
- **Input size**: 224x224 RGB images
- **Output**: 38 disease classes
- **Preprocessing**: ImageNet normalization
- **Augmentation**: Random crop, flip, rotation, color ji
tter                                                     
## Expected Results & Performance Benchmarks

### Training Performance

**Hardware-Specific Training Times** (100 epochs, PlantVi
llage dataset):                                          - **NVIDIA RTX 4090**: ~75 minutes (45s/epoch, batch_size
=128)                                                    - **NVIDIA RTX 3080**: ~125 minutes (75s/epoch, batch_siz
e=64)                                                    - **Apple M2 Max (MPS)**: ~200 minutes (120s/epoch, batch
_size=32)                                                - **CPU (16-core)**: ~25 hours (15min/epoch, batch_size=1
6)                                                       
### Model Performance

**Accuracy Expectations**:
- **Production Training**: 94-97% validation accuracy
- **Transfer Learning**: 92-95% with frozen backbone
- **From Scratch**: 85-92% without pre-training
- **Cross-Validation**: ±2% variance across folds

**Model Specifications**:
- **Model Size**: ~97.8MB (ResNet50 architecture)
- **Parameters**: ~25.6M trainable parameters
- **Input Size**: 224×224 RGB images
- **Output Classes**: 38 PlantVillage disease classes

### Inference Performance

**Prediction Speed**:
- **GPU (CUDA)**: ~5ms per image
- **Apple Silicon (MPS)**: ~15ms per image
- **CPU**: ~50ms per image
- **Batch Inference**: 10-20x speedup for multiple images

## Migration from Legacy Training

### Upgrading Existing Models

```bash
# Migrate old model format to registry
python -m src.training.model_migrator \
    --source=data/models/best_model.pt \
    --target=plantguard_v1.0.0

# Update VisionAdapter configuration
python -m src.core.vision_adapter update-config

# Validate migration
make validate-models
```

### Configuration Migration

```bash
# Convert old training scripts to new configuration
python -m src.training.config_migrator \
    --legacy-script=scripts/train_vision_model.py \
    --output=config/migrated_config.json

# Test migrated configuration
make train-production CONFIG=config/migrated_config.json 
--dry-run                                                ```

For detailed troubleshooting and advanced optimization te
chniques, see the [Production Training Guide](../docs/production_training.md) and [Performance Optimization Guide](../docs/performance_optimization.md).
