"""
Test script for mobile layout and design system implementation.

This script verifies that the mobile layout manager and design system
are working correctly and can be imported and initialized.
"""
from typing import Any, Dict, List, Optional, Tuple, Union, Generator
import pytest


import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_mobile_imports() -> bool:
    """Test that mobile modules can be imported."""
    import importlib.util

    modules = ["src.ui.mobile_component_registry", "src.ui.mobile_design_system", "src.ui.mobile_layout_manager"]

    try:
        for module_name in modules:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                print(f"[FAIL] Module not found: {module_name}")
                return False

        print("[PASS] All mobile modules found successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False


def test_mobile_layout_manager() -> bool:
    """Test mobile layout manager initialization."""
    try:
        from src.ui.mobile_layout_manager import MobileLayoutManager

        layout_manager = MobileLayoutManager()

        # Test configuration
        assert layout_manager.config["layout_type"] == "single_column"
        assert layout_manager.config["touch_target_size"] == 48
        assert layout_manager.config["spacing_unit"] == 16

        # Test CSS generation
        css = layout_manager._get_mobile_base_css()
        assert "mobile-main-layout" in css
        assert "mobile-input-grid" in css
        assert "--touch-target-min: 48px" in css

        print("[PASS] MobileLayoutManager tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] MobileLayoutManager test failed: {e}")
        return False


def test_mobile_design_system() -> bool:
    """Test mobile design system functionality."""
    try:
        from src.ui.mobile_design_system import ButtonVariant, ComponentSize, MobileDesignSystem

        design_system = MobileDesignSystem()

        # Test design tokens
        tokens = design_system.design_tokens
        assert "colors" in tokens
        assert "spacing" in tokens
        assert "typography" in tokens

        # Test button creation
        button_html = design_system.create_button("Test Button", variant=ButtonVariant.PRIMARY, size=ComponentSize.MEDIUM)
        assert "mobile-button" in button_html
        assert "mobile-button-primary" in button_html

        # Test card creation
        card_html = design_system.create_card("Test content", title="Test Card", elevated=True)
        assert "mobile-card" in card_html
        assert "mobile-card-elevated" in card_html

        print("[PASS] MobileDesignSystem tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] MobileDesignSystem test failed: {e}")
        return False


def test_mobile_component_registry() -> bool:
    """Test mobile component registry functionality."""
    try:
        from src.ui.mobile_component_registry import MobileComponentRegistry, MobileStateManager

        registry = MobileComponentRegistry()

        # Test available components
        components = registry.get_available_components()
        expected_components = [
            "camera_input",
            "upload_input",
            "voice_input",
            "text_input",
            "analysis_display",
            "chat_interface",
            "history_view",
            "settings_card",
        ]

        for component in expected_components:
            assert component in components, f"Missing component: {component}"

        # Test metadata
        metadata = registry.get_all_metadata()
        assert len(metadata) > 0

        # Test state manager
        test_state = MobileStateManager.get_component_state("test_component")
        assert test_state["initialized"]
        assert "data" in test_state

        print("[PASS] MobileComponentRegistry tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] MobileComponentRegistry test failed: {e}")
        return False


def test_css_classes() -> bool:
    """Test that required CSS classes are present."""
    try:
        from src.ui.mobile_design_system import MobileDesignSystem

        design_system = MobileDesignSystem()
        css = design_system._get_design_system_css()

        # Test required CSS classes for AI agent recognition
        required_classes = [
            "mobile-button",
            "mobile-button-primary",
            "mobile-card",
            "mobile-input",
            "mobile-progress",
            "mobile-alert",
            "mobile-badge",
        ]

        for css_class in required_classes:
            assert f".{css_class}" in css, f"Missing CSS class: {css_class}"

        # Test touch optimization
        assert "touch-action: manipulation" in css
        assert "min-height: 48px" in css

        # Test responsive design
        assert "@media (max-width:" in css

        print("[PASS] CSS classes test passed")
        return True
    except Exception as e:
        print(f"[FAIL] CSS classes test failed: {e}")
        return False


def main() -> bool:
    """Run all tests."""
    print("[TEST] Testing Mobile Layout and Design System Implementation")
    print("=" * 60)

    tests = [test_mobile_imports, test_mobile_layout_manager, test_mobile_design_system, test_mobile_component_registry, test_css_classes]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"[INFO] Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All tests passed! Mobile layout and design system implementation is working correctly.")
        return True
    else:
        print("[WARNING] Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
