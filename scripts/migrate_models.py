"""Compatibility shim for scripts.migrate_models used by tests.

This module defines a lightweight `scan_for_legacy_models` implementation that
uses the module-level `Path` symbol so tests can patch `scripts.migrate_models.Path`.
It intentionally keeps logic minimal and avoids importing the original
implementation so that tests which patch the shim behave as expected.
"""

from pathlib import Path

# Export Path so tests can patch scripts.migrate_models.Path
__all__ = ["Path", "scan_for_legacy_models"]


def scan_for_legacy_models() -> list[Path]:
    """Scan for legacy model files in common locations.

    This lightweight implementation mirrors the original script's public
    behaviour for tests: it looks in a few standard directories and returns
    any ``*.pt`` files found. Tests may patch the module-level ``Path`` to
    control the search behaviour.
    """
    legacy_paths: list[Path] = []

    search_paths = ["data/models", "models", "checkpoints"]

    for search_path in search_paths:
        search_dir = Path(search_path)
        if not search_dir.exists():
            continue

        for model_file in search_dir.glob("*.pt"):
            legacy_paths.append(model_file)

    return legacy_paths
