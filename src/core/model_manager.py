"""Compatibility shim for model manager.

This module re-exports the public API from the model switching feature so old
imports continue to work after reorganization.
"""

# Re-export everything from the new location
from src.features.model_switching.model_manager import PlantGuardModelManager

__all__ = ["PlantGuardModelManager"]
