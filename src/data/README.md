# PlantGuard Data Pipeline

This module provides comprehensive data loading, preprocessing, validation, and analysis utilities for the PlantGuard multimodal plant disease detection system.

## Overview

The data pipeline is designed to handle the PlantVillage dataset with the following key features:

- **Dataset Loading**: ImageFolder-based loading with automatic class discovery
- **Data Preprocessing**: Configurable transforms for training, validation, and inference
- **Stratified Splitting**: Maintains class distribution across train/validation splits
- **Data Validation**: Comprehensive image format and corruption detection
- **Quality Analysis**: Dataset statistics and class distribution analysis
- **Integrity Checking**: Ensures data pipeline reliability

## Key Components

### 1. Dataset Loading (`dataset.py`)

#### `PlantVillageDataset`
Custom PyTorch dataset class for loading PlantVillage images with labels.

```python
from plantguard.data import PlantVillageDataset, DataTransforms

# Create dataset with transforms
dataset = PlantVillageDataset(
    root_dir="data/PlantVillage",
    transform=DataTransforms.get_train_transforms()
)

# Access samples
image, label = dataset[0]  # Returns (torch.Tensor, int)
print(f"Classes: {dataset.classes}")
print(f"Distribution: {dataset.get_class_distribution()}")
```

#### `DataTransforms`
Predefined transformation pipelines for different use cases:

```python
# Training transforms (with augmentation)
train_transforms = DataTransforms.get_train_transforms()

# Validation transforms (no augmentation)
val_transforms = DataTransforms.get_val_transforms()

# Inference transforms (single image)
inference_transforms = DataTransforms.get_inference_transforms()
```

#### `create_data_loaders()`
One-stop function to create train/validation data loaders:

```python
from plantguard.data import create_data_loaders

train_loader, val_loader, class_names = create_data_loaders(
    data_dir="data/PlantVillage",
    batch_size=32,
    train_ratio=0.8,
    num_workers=4,
    random_state=42
)
```

### 2. Data Validation (`validation.py`)

#### `ImageValidator`
Validates image files for format, corruption, and size constraints:

```python
from plantguard.data import ImageValidator

validator = ImageValidator(strict_mode=False)

# Validate single image
result = validator.validate_image_file("path/to/image.jpg")
print(f"Valid: {result['readable'] and result['size_valid']}")

# Validate entire dataset
dataset_results = validator.validate_dataset_directory("data/PlantVillage")
print(f"Validation rate: {dataset_results['validation_rate']:.1%}")
```

#### `DatasetAnalyzer`
Analyzes dataset statistics and properties:

```python
from plantguard.data import DatasetAnalyzer

analyzer = DatasetAnalyzer()

# Analyze class distribution
class_analysis = analyzer.analyze_class_distribution("data/PlantVillage")
print(f"Classes: {class_analysis['num_classes']}")
print(f"Imbalance ratio: {class_analysis['imbalance_ratio']:.2f}")

# Analyze image properties
image_analysis = analyzer.analyze_image_properties("data/PlantVillage")
print(f"Average dimensions: {image_analysis['dimensions']['width_stats']['mean']:.0f}x{image_analysis['dimensions']['height_stats']['mean']:.0f}")
```

#### `DataIntegrityChecker`
Ensures data pipeline integrity:

```python
from plantguard.data import DataIntegrityChecker

checker = DataIntegrityChecker()

# Run comprehensive integrity check
results = checker.run_full_integrity_check("data/PlantVillage")
print(f"Overall valid: {results['overall_valid']}")
```

### 3. Comprehensive Reporting

#### `generate_data_report()`
Creates detailed data quality reports:

```python
from plantguard.data import generate_data_report

# Generate and save comprehensive report
report = generate_data_report(
    data_dir="data/PlantVillage",
    output_path="data_quality_report.json"
)

print(f"Dataset: {report['validation_summary']['total_files']} files")
print(f"Quality: {report['validation_summary']['validation_rate']:.1%} valid")
print(f"Balance: {'balanced' if report['class_distribution']['is_balanced'] else 'imbalanced'}")
```

## Usage Examples

### Basic Dataset Loading

```python
from plantguard.data import create_data_loaders

# Create data loaders for training
train_loader, val_loader, classes = create_data_loaders(
    data_dir="data/PlantVillage",
    batch_size=32,
    train_ratio=0.8
)

# Training loop
for batch_idx, (images, labels) in enumerate(train_loader):
    # images: torch.Tensor of shape (batch_size, 3, 224, 224)
    # labels: torch.Tensor of shape (batch_size,)
    pass
```

### Data Quality Assessment

```python
from plantguard.data import ImageValidator, DatasetAnalyzer

# Quick validation check
validator = ImageValidator()
results = validator.validate_dataset_directory("data/PlantVillage")

if results['validation_rate'] < 0.95:
    print(f"Warning: Only {results['validation_rate']:.1%} of images are valid")
    print(f"Invalid images: {len(results['invalid_image_paths'])}")

# Detailed analysis
analyzer = DatasetAnalyzer()
analysis = analyzer.analyze_class_distribution("data/PlantVillage")

if not analysis['is_balanced']:
    print(f"Dataset is imbalanced (ratio: {analysis['imbalance_ratio']:.2f})")
    print("Consider using weighted sampling or data augmentation")
```

### Complete Pipeline Setup

```python
from plantguard.data import (
    create_data_loaders,
    generate_data_report,
    DataIntegrityChecker
)

# 1. Check data integrity
checker = DataIntegrityChecker()
integrity = checker.run_full_integrity_check("data/PlantVillage")

if not integrity['overall_valid']:
    print("Data integrity issues found!")
    # Handle issues...

# 2. Generate quality report
report = generate_data_report("data/PlantVillage", "quality_report.json")

# 3. Create data loaders
train_loader, val_loader, classes = create_data_loaders(
    data_dir="data/PlantVillage",
    batch_size=32,
    train_ratio=0.8,
    num_workers=4
)

print(f"Ready for training: {len(classes)} classes, {len(train_loader)} batches")
```

## Configuration Options

### Image Validation Settings

```python
# Strict validation (raises exceptions on errors)
validator = ImageValidator(strict_mode=True)

# Custom size limits
validator.MIN_IMAGE_SIZE = (64, 64)
validator.MAX_IMAGE_SIZE = (4096, 4096)
validator.MAX_FILE_SIZE_MB = 100
```

### Transform Customization

```python
# Custom training transforms
custom_transforms = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomCrop(224),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ColorJitter(brightness=0.3, contrast=0.3),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

dataset = PlantVillageDataset("data/PlantVillage", transform=custom_transforms)
```

## Requirements Satisfied

This implementation satisfies the following requirements from the PlantGuard specification:

- **Requirement 1.2**: Image preprocessing pipeline with resize, normalization, and augmentation
- **Requirement 1.1**: Image format validation and corruption detection
- **Requirement 1.5**: Data integrity checks for training pipeline
- **Requirement 8.2**: Train/validation split functionality with stratified sampling

## Testing

Run the test suite to verify functionality:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run data pipeline tests
python -m pytest tests/test_data_pipeline.py -v

# Test specific functionality
python src/data/example_usage.py
```

## File Structure

```
src/data/
├── __init__.py          # Module exports
├── dataset.py           # Dataset loading and preprocessing
├── validation.py        # Data validation and quality checks
├── example_usage.py     # Usage examples
└── README.md           # This documentation

tests/
└── test_data_pipeline.py # Unit tests
```

## Next Steps

This data pipeline is ready for integration with:

1. **Vision Model Training** (Task 3): Use `create_data_loaders()` for model training
2. **Model Evaluation** (Task 8): Use validation utilities for performance assessment
3. **Streamlit UI** (Task 7): Use `DataTransforms.get_inference_transforms()` for user uploads

The pipeline ensures data quality and provides comprehensive validation, making it suitable for production use in the PlantGuard system.
