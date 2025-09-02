#!/usr/bin/env python3
"""Simple test to verify mobile implementation works."""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_functionality() -> None:
    """Test basic functionality without Streamlit context."""

    print("Testing mobile layout and design system...")

    try:
        # Test imports
        from src.ui.components.mobile_component_registry import \
            mobile_component_registry as MobileComponentRegistry
        from src.ui.components.mobile_layout_manager import MobileLayoutManager

        print("[OK] Imports successful")

        # Test layout manager
        layout = MobileLayoutManager()
        assert layout.config["touch_target_size"] == 48
        print("[OK] Layout manager initialized")

        # Test component registry
        from src.ui.components.mobile_component_registry import \
            mobile_component_registry
        components = mobile_component_registry.list_components()
        assert isinstance(components, list)  # Should return a list
        print("[OK] Component registry working")

        print("\n[SUCCESS] All basic tests passed!")

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        traceback.print_exc()
        raise  # Re-raise the exception to make the test fail

if __name__ == "__main__":
    test_basic_functionality()
    print("Test completed successfully!")
