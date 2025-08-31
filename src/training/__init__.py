from collections.abc import Generator
from typing import Any, Dict, List, Optional, Tuple, Union

"""Training module for PlantGuard production pipeline."""

from .evaluator import ModelEvaluator, ModelMetrics, ValidationResult
from .model_comparison import BenchmarkResult, ModelComparator, ModelRanking
from .model_registry import ModelInfo, ModelMetadata, ModelRegistry
from .model_validator import AutomatedModelValidator, AutomatedValidationResult, ValidationConfig

__all__ = [
    "AutomatedModelValidator",
    "AutomatedValidationResult",
    "BenchmarkResult",
    "ModelComparator",
    "ModelEvaluator",
    "ModelInfo",
    "ModelMetadata",
    "ModelMetrics",
    "ModelRanking",
    "ModelRegistry",
    "ValidationConfig",
    "ValidationResult",
]
