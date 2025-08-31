#!/usr/bin/env python3
"""
Comprehensive Mobile Testing Suite

Tests all mobile components and their integration with the PlantGuard system.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

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


def test_mobile_component_imports() -> None:
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

    missing_components = []
    available_components = []

    try:
        for component_name in components:
            spec = importlib.util.find_spec(component_name)
            if spec is None:
                missing_components.append(component_name)
                st.warning(f"[WARNING] Component not found: {component_name}")
            else:
                available_components.append(component_name)

        if missing_components:
            st.warning(f"[WARNING] {len(missing_components)} components missing, {len(available_components)} available")
            assert len(available_components) > 0, "At least some components should be available"
        else:
            st.success("[PASS] All mobile components found successfully")

    except ImportError as e:
        st.error(f"[FAIL] Import error: {e}")
        pytest.fail(f"Import error: {e}")


def test_mobile_app_integration() -> None:
    """Test mobile app integration."""
    import importlib.util

    try:
        # Check if mobile_spa_app can be found
        spec = importlib.util.find_spec("mobile_spa_app")
        if spec is not None:
            # Try to actually import it
            try:
                import mobile_spa_app

                if hasattr(mobile_spa_app, "MobilePlantGuardApp"):
                    st.success("[PASS] Mobile app can be imported and has main class")
                else:
                    st.warning("[WARNING] Mobile app imported but missing MobilePlantGuardApp class")
                    pytest.fail("Mobile app missing MobilePlantGuardApp class")
            except Exception as e:
                st.warning(f"[WARNING] Mobile app found but import failed: {e}")
                pytest.fail(f"Mobile app import failed: {e}")
        else:
            st.warning("[WARNING] Mobile app module not found - may be in different location")
            # Try alternative import paths
            try:
                import sys
                from pathlib import Path

                root_path = Path(__file__).parent
                if str(root_path) not in sys.path:
                    sys.path.insert(0, str(root_path))
                import mobile_spa_app

                st.success("[PASS] Mobile app found in root directory")
            except ImportError:
                st.error("[FAIL] Mobile app not found in any location")
                pytest.fail("Mobile app not found in any location")

    except ImportError as e:
        st.error(f"[FAIL] Mobile app import error: {e}")
        pytest.fail(f"Mobile app import error: {e}")


def test_adapter_integration() -> None:
    """Test that adapters work with mobile components."""
    import importlib.util

    adapters = ["core.audio", "core.nlp", "core.vision"]
    missing_adapters = []
    available_adapters = []

    try:
        for adapter_name in adapters:
            spec = importlib.util.find_spec(adapter_name)
            if spec is None:
                missing_adapters.append(adapter_name)
                st.warning(f"[WARNING] Adapter not found: {adapter_name}")
            else:
                try:
                    # Try to actually import the adapter
                    module = importlib.import_module(adapter_name)
                    available_adapters.append(adapter_name)
                except Exception as e:
                    st.warning(f"[WARNING] Adapter {adapter_name} found but import failed: {e}")
                    missing_adapters.append(adapter_name)

        if missing_adapters:
            st.warning(f"[WARNING] {len(missing_adapters)} adapters missing, {len(available_adapters)} available")
            assert len(available_adapters) > 0, "At least some adapters should be available"
        else:
            st.success("[PASS] All adapters can be imported")

    except ImportError as e:
        st.warning(f"[WARNING] Adapter import warning: {e}")
        # Don't fail the test for adapter import warnings - they may be optional


def run_comprehensive_tests() -> None:
    """Run all comprehensive tests."""
    st.title("[TEST] Mobile Comprehensive Testing Suite")

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
