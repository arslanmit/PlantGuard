# Raw Dataset Directory

This directory contains raw, unprocessed datasets for PlantGuard training.

## PlantVillage Dataset

### Manual Installation
If you have the PlantVillage dataset, place it in `plantvillage/` directory:

```
data/raw/plantvillage/
├── Potato___Early_blight/
├── Potato___Late_blight/
├── Potato___healthy/
├── Tomato___Early_blight/
├── Tomato___Late_blight/
├── Tomato___healthy/
└── ... (other plant disease classes)
```

### Automatic Download
Run `make download-dataset` to download from Kaggle (requires API credentials).

### Dataset Sources
- **PlantVillage**: https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset
- **Original Paper**: https://arxiv.org/abs/1511.08060

### Next Steps
After placing the raw dataset:
1. `make prepare-dataset` - Create train/val splits
2. `make validate-dataset` - Check dataset integrity
3. `make analyze-dataset` - View dataset statistics
4. `make train` - Train models
