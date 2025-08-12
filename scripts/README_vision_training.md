# Vision Model Training Guide

This guide explains how to train the PlantGuard vision model using the ResNet50 architecture.

## Prerequisites

1. **Dataset**: PlantVillage dataset with train/val split
2. **Dependencies**: Install requirements from `requirements.txt`
3. **Hardware**: GPU recommended for faster training (CPU supported)

## Dataset Preparation

### Option 1: Prepare from Raw Dataset

```bash
# Split dataset into train/val
python scripts/prepare_dataset.py \
    --source_dir /path/to/plantvillage/raw \
    --output_dir data/plantvillage \
    --train_ratio 0.8

# Validate dataset structure
python scripts/prepare_dataset.py \
    --output_dir data/plantvillage \
    --validate_only
```

### Option 2: Generate Class Mapping

```bash
# Generate class mapping from dataset
python scripts/generate_class_mapping.py \
    --dataset_dir data/plantvillage \
    --output_path data/knowledge_base/plantvillage_classes.json
```

## Training

### Basic Training

```bash
python scripts/train_vision_model.py \
    --data_dir data/plantvillage \
    --save_dir data/models \
    --epochs 50 \
    --batch_size 32
```

### Advanced Training Options

```bash
python scripts/train_vision_model.py \
    --data_dir data/plantvillage \
    --save_dir data/models \
    --epochs 100 \
    --batch_size 64 \
    --learning_rate 0.0001 \
    --weight_decay 1e-4 \
    --device cuda \
    --num_workers 8
```

## Monitoring Training

### TensorBoard

```bash
# Start TensorBoard (in separate terminal)
tensorboard --logdir runs

# Open browser to http://localhost:6006
```

### Training Metrics

The training script logs:
- Training loss per epoch
- Validation loss per epoch
- Validation accuracy per epoch
- Learning rate schedule
- Model checkpoints (best and latest)

## Model Files

After training, you'll have:

```
data/models/
├── best_model.pt          # Best model checkpoint
├── latest_model.pt        # Latest model checkpoint
└── class_names.json       # Class name mapping
```

## Using Trained Model

```python
from src.core.vision import VisionAdapter
from PIL import Image

# Load model
adapter = VisionAdapter(
    model_path="data/models/best_model.pt",
    device="cpu"
)

# Load class mapping
adapter.load_class_mapping("data/knowledge_base/plantvillage_classes.json")

# Predict
image = Image.open("test_image.jpg")
raw_class, readable_name, confidence, plant_type = adapter.predict_with_readable_name(image)

print(f"Plant: {plant_type}")
print(f"Disease: {readable_name}")
print(f"Confidence: {confidence:.2%}")
```

## Testing

```bash
# Test implementation
python scripts/test_vision_adapter.py
```

## Troubleshooting

### Common Issues

1. **CUDA out of memory**: Reduce batch size
2. **Dataset not found**: Check data directory path
3. **Low accuracy**: Increase epochs or adjust learning rate
4. **Slow training**: Use GPU and increase num_workers

### Performance Tips

1. **Use GPU**: Set `--device cuda` if available
2. **Batch size**: Increase if you have enough memory
3. **Data loading**: Increase `--num_workers` for faster I/O
4. **Mixed precision**: Consider using automatic mixed precision for faster training

## Model Architecture

- **Backbone**: ResNet50 (ImageNet pre-trained)
- **Input size**: 224x224 RGB images
- **Output**: 38 disease classes
- **Preprocessing**: ImageNet normalization
- **Augmentation**: Random crop, flip, rotation, color jitter

## Expected Results

- **Training time**: ~2-4 hours on GPU for 50 epochs
- **Validation accuracy**: >90% on PlantVillage dataset
- **Model size**: ~100MB
- **Inference time**: ~50ms per image on CPU
