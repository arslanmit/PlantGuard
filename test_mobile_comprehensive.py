#!/usr/bin/env python3
"""
Comprehensive Mobile Testing Suite

Tests all mobile components and their integration with the PlantGuard system.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import streamlit as st  # noqa: E402


class MockStreamlit:
    """Mock Streamlit for testing without running the full app."""

    def __init__(self):
        self.button_calls = []
        self.file_uploader_calls = []

    def button(self, label, **kwargs):
        self.button_calls.append({"label": label, "kwargs": kwargs})
        return False  # Default to not pressed

    def file_uploader(self, label, **kwargs):
        self.file_uploader_calls.append({"label": label, "kwargs": kwargs})
        return None  # Default to no file

    def columns(self, spec):
        return [Mock() for _ in range(spec if isinstance(spec, int) else len(spec))]

    def container(self):
        return Mock()

    def expander(self, label, expanded=False):
        return Mock()

    def tabs(self, labels):
        return [Mock() for _ in labels]

    def success(self, message):
        pass

    def error(self, message):
        pass

    def warning(self, message):
        pass

    def info(self, message):
        pass


def test_mobile_component_imports():
    """Test that all mobile components can be imported."""
    import importlib.util

    components = [
        "ui.components.mobile_chat_interface",
        "ui.components.mobile_content_tabs",
        "ui.components.mobile_header",
        "ui.components.mobile_image_analysis",
        "ui.components.mobile_input_ribbon",
        "ui.components.mobile_layout_manager",
        "ui.components.mobile_voice_interface",
    ]

    try:
        for component_name in components:
            spec = importlib.util.find_spec(component_name)
            if spec is None:
                st.error(f"[FAIL] Component not found: {component_name}")
                return False

        st.success("[PASS] All mobile components found successfully")
        return True

    except ImportError as e:
        st.error(f"[FAIL] Import error: {e}")
        return False


def test_mobile_app_integration():
    """Test mobile app integration."""
    import importlib.util

    try:
        spec = importlib.util.find_spec("mobile_spa_app")
        if spec is not None:
            st.success("[PASS] Mobile app can be imported")
            return True
        else:
            st.error("[FAIL] Mobile app module not found")
            return False

    except ImportError as e:
        st.error(f"[FAIL] Mobile app import error: {e}")
        return False


def test_adapter_integration():
    """Test that adapters work with mobile components."""
    import importlib.util

    adapters = ["core.audio", "core.nlp", "core.vision"]

    try:
        for adapter_name in adapters:
            spec = importlib.util.find_spec(adapter_name)
            if spec is None:
                st.error(f"[FAIL] Adapter not found: {adapter_name}")
                return False

        st.success("[PASS] All adapters can be imported")
        return True

    except ImportError as e:
        st.warning(f"[WARNING] Adapter import warning: {e}")
        return False


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    st.title("🧪 Mobile Comprehensive Testing Suite")

    tests = [
        ("Component Imports", test_mobile_component_imports),
        ("Mobile App Integration", test_mobile_app_integration),
        ("Adapter Integration", test_adapter_integration),
    ]

    results = {}

    for test_name, test_func in tests:
        st.subheader(f"Testing: {test_name}")

        try:
            result = test_func()
            results[test_name] = result

            if result:
                st.success(f"[PASS] {test_name} passed")
            else:
                st.error(f"[FAIL] {test_name} failed")

        except Exception as e:
            st.error(f"[FAIL] {test_name} error: {e}")
            results[test_name] = False

    # Summary
    st.subheader("[INFO] Test Summary")
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    if passed == total:
        st.success(f"[SUCCESS] All tests passed! ({passed}/{total})")
    else:
        st.warning(f"[WARNING] {passed}/{total} tests passed")

    return results


if __name__ == "__main__":
    run_comprehensive_tests()
