#!/usr/bin/env python3
"""Validate that PlantGuard Streamlit applications can start without import errors."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def validate_main_app() -> bool:
    """Validate main Streamlit app imports."""
    try:
        # Test core imports
        from core.audio import AudioAdapter
        from core.nlp import TextAdapter
        from core.vision import VisionAdapter
        from ui.components import ModelSwitcher, render_status_indicator

        print("✅ Main app: Core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Main app import error: {e}")
        return False


def validate_switcher_app() -> bool:
    """Validate model switcher app imports."""
    try:
        # Test model manager import - check if it exists
        switcher_path = Path(__file__).parent.parent / "src" / "features" / "model_switching" / "model_manager.py"
        if switcher_path.exists():
            from features.model_switching.model_manager import PlantGuardModelManager

            print("✅ Switcher app: Model manager import successful")
        else:
            print("⚠️  Switcher app: Model manager not found, but app should still work")

        # Test basic PIL import which is used in switcher
        from PIL import Image

        print("✅ Switcher app: Basic dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Switcher app import error: {e}")
        return False


def main() -> None:
    """Run validation checks."""
    print("🔍 Validating PlantGuard applications...")
    print()

    main_ok = validate_main_app()
    switcher_ok = validate_switcher_app()

    print()
    if main_ok and switcher_ok:
        print("🎉 All applications validated successfully!")
        print("✅ Ready to run: make run")
        print("✅ Ready to run: make switcher")
        print("✅ Ready to run: make run-all")
    else:
        print("⚠️  Some applications have import issues")
        if not main_ok:
            print("❌ Main app needs attention")
        if not switcher_ok:
            print("❌ Switcher app needs attention")
        sys.exit(1)


if __name__ == "__main__":
    main()
