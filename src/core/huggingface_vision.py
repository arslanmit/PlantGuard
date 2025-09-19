"""Compatibility shim for Hugging Face vision adapter.

This module re-exports the public API from the model switching feature so old
imports continue to work after reorganization.
"""

from plantguard.features.model_switching.huggingface_vision import (
    HuggingFaceVisionAdapter,
)

__all__ = ["HuggingFaceVisionAdapter"]
