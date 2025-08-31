#!/usr/bin/env python3
"""Validate that PlantGuard Streamlit applications can start without import errors."""

from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import importlib
import importlib.util
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _is_available(module_name: str) -> bool:
    """Return True if the given module can be imported or discovered via find_spec."""

    try:
        if importlib.util.find_spec(module_name) is None:
            return False
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def validate_main_app() -> bool:
    """Validate main Streamlit app imports."""
    core_modules = [
        "core.audio",
        "core.nlp",
        "core.vision",
        "ui.components",
    ]

    missing = []
    for mod in core_modules:
        if not _is_available(mod):
            missing.append(mod)

    if missing:
        print(f"\u274c Main app missing modules: {missing}")
        return False

    print("\u2705 Main app: Core imports successful")
    return True


def validate_switcher_app() -> bool:
    """Validate model switcher app imports."""
    # Check optional model manager
    manager_spec = importlib.util.find_spec("features.model_switching.model_manager")
    if manager_spec is None:
        print("\u26a0\ufe0f  Switcher app: Model manager not found, but app should still work")
    else:
        try:
            importlib.import_module("features.model_switching.model_manager")
            print("\u2705 Switcher app: Model manager import successful")
        except Exception as e:
            print(f"\u274c Switcher app import error: {e}")
            return False

    # Test basic PIL import which is used in switcher
    try:
        importlib.import_module("PIL.Image")
        print("\u2705 Switcher app: Basic dependencies available")
    except Exception:
        print("\u274c Switcher app: PIL not available")
        return False

    return True


def main() -> None:
    """Run validation checks."""
    print("[SEARCH] Validating PlantGuard applications...")
    print()

    main_ok = validate_main_app()
    switcher_ok = validate_switcher_app()

    print()
    if main_ok and switcher_ok:
        print("[SUCCESS] All applications validated successfully!")
        print("[DONE] Ready to run: make run")
        print("[DONE] Ready to run: make switcher")
        print("[DONE] Ready to run: make run-all")
    else:
        print("[WARNING]  Some applications have import issues")
        if not main_ok:
            print("[TODO] Main app needs attention")
        if not switcher_ok:
            print("[TODO] Switcher app needs attention")
        sys.exit(1)


if __name__ == "__main__":
    main()
