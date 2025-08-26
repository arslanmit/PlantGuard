"""PlantGuard Data Module.

This module contains data loading, preprocessing, and validation utilities.
"""

import importlib
from typing import Any

# Import new dataset and validation utilities at module import time
from .dataset import DataTransforms, PlantVillageDataset, create_data_loaders, create_stratified_split, get_dataset_statistics
from .validation import DataIntegrityChecker, DatasetAnalyzer, ImageValidator, generate_data_report

# Import existing modules (if they exist) dynamically
AudioPreprocessor: Any | None
ImagePreprocessor: Any | None
try:
    preprocessing = importlib.import_module(f"{__package__}.preprocessing")
    AudioPreprocessor = getattr(preprocessing, "AudioPreprocessor", None)
    ImagePreprocessor = getattr(preprocessing, "ImagePreprocessor", None)
except (ImportError, AttributeError):
    AudioPreprocessor = None
    ImagePreprocessor = None

__all__: list[str] = [
    # Core exports
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
    "get_dataset_statistics",
]
