#!/usr/bin/env python3
"""
PlantGuard Unified Application Entry Point

Simplified single-interface application that replaces the complex dual-port system
with a streamlined, user-friendly experience.
"""

import sys
from pathlib import Path

# Ensure we can import from src
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def main():
    """Launch the unified PlantGuard application."""
    try:
        # Import and run the simplified app without sidebar
        from ui.simplified_app import main as run_simplified_app

        run_simplified_app()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Application Error: {e}")
        print("Please check the logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
