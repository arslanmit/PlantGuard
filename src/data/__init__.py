"""PlantGuard Data Module.

This module contains data loading, preprocessing, and validation utilities.
"""

# Import existing modules (if they exist)
try:
    from .preprocessing import AudioPreprocessor, ImagePreprocessor
except ImportError:
    AudioPreprocessor = None
    ImagePreprocessor = None

# Import new dataset utilities
from .dataset import (
    DataTransforms,
    PlantVillageDataset,
    create_data_loaders,
    create_stratified_split,
    get_dataset_statistics,
)

# Import new validation utilities
from .validation import DataIntegrityChecker, DatasetAnalyzer, ImageValidator, generate_data_report

# Legacy compatibility
get_dataloaders = create_data_loaders
DataValidator = ImageValidator

__all__ = [
    # Legacy exports (if available)
    "AudioPreprocessor",
    "DataIntegrityChecker",
    "DataTransforms",
    "DataValidator",
    "DatasetAnalyzer",
    "ImagePreprocessor",
    # New validation utilities
    "ImageValidator",
    # New dataset utilities
    "PlantVillageDataset",
    "create_data_loaders",
    "create_stratified_split",
    "generate_data_report",
    "get_dataloaders",
    "get_dataset_statistics",
]
