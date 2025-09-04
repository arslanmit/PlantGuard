"""Package shim for ``scripts.model_switching``.

This module re-exports the small public surface from
``scripts.models.model_switcher`` for backward compatibility. Using
explicit names lets static tools (ruff/mypy) detect undefined names and
keeps the API surface clear.
"""

from scripts.models.model_switcher import ModelRegistry, get_current_model, list_models_registry, switch_model

__all__ = [
    "ModelRegistry",
    "get_current_model",
    "list_models_registry",
    "switch_model",
]
