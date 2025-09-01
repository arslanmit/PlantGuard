#!/usr/bin/env python3
"""Simple test to verify mobile implementation works."""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_functionality() -> bool:
    """Test basic functionality without Streamlit context."""

    print("Testing mobile layout and design system...")

    try:
        # Test imports
        from src.ui.mobile_component_registry import MobileComponentRegistry
        from src.ui.mobile_design_system import MobileDesignSystem
        from src.ui.mobile_layout_manager import MobileLayoutManager

        print("[OK] Imports successful")

        # Test layout manager
        layout = MobileLayoutManager()
        assert layout.config["touch_target_size"] == 48
        print("[OK] Layout manager initialized")

        # Test design system
        design = MobileDesignSystem()
        css = design._get_design_system_css()
        assert len(css) > 1000
        assert ".mobile-button" in css
        print("[OK] Design system working")

        # Test component registry
        registry = MobileComponentRegistry()
        components = registry.get_available_components()
        assert "camera_input" in components
        print("[OK] Component registry working")

        print("\n[SUCCESS] All basic tests passed!")
        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
