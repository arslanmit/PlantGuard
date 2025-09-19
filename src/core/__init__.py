"""Public entry points for the core PlantGuard adapters.

Historically this module imported the audio, text, and vision adapters eagerly
so consumers could rely on ``plantguard.core`` behaving like a flat namespace.
That eager import caused test collection to fail whenever optional runtime
dependencies (notably ``librosa`` for the audio stack) were missing.  To keep
the nice import ergonomics without forcing heavy dependencies to be installed
up front we now resolve adapters lazily the first time they are accessed.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__version__ = "0.1.0"
__author__ = "PlantGuard Team"

__all__ = ["AudioAdapter", "TextAdapter", "VisionAdapter"]


def _load(name: str, module: str, attr: str) -> Any:
    """Import ``attr`` from ``module`` and memoise it on first access."""

    value = globals().get(name)
    if value is not None:
        return value

    try:
        module_obj = import_module(f"{__name__}.{module}")
        value = getattr(module_obj, attr)
        globals()[name] = value
        return value
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised via import path
        missing_pkg = getattr(exc, "name", None)
        if missing_pkg and missing_pkg not in {f"{__name__}.{module}", module}:
            # Re-raise when a real dependency is absent (e.g. librosa).
            raise ModuleNotFoundError(
                f"{attr} requires optional dependency '{missing_pkg}'. Install the extra"
                " runtime packages or avoid importing that adapter when not needed."
            ) from exc
        raise


def __getattr__(name: str) -> Any:
    if name == "AudioAdapter":
        return _load(name, "audio", "AudioAdapter")
    if name == "TextAdapter":
        return _load(name, "nlp", "TextAdapter")
    if name == "VisionAdapter":
        return _load(name, "vision", "VisionAdapter")
    raise AttributeError(name)


def __dir__() -> list[str]:
    # Include lazily exported adapter names while preserving standard module attrs
    return sorted({*globals(), *__all__})
