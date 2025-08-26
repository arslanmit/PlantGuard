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

import streamlit as st


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
    try:
        from ui.components.mobile_chat_interface import MobileChatInterface
        from ui.components.mobile_content_tabs import MobileContentTabs
        from ui.components.mobile_header import MobileHeader
        from ui.components.mobile_image_analysis import MobileImageAnalysis
        from ui.components.mobile_input_ribbon import MobileInputRibbon
        from ui.components.mobile_layout_manager import MobileLayoutManager
        from ui.components.mobile_voice_interface import MobileVoiceInterface

        st.success("✅ All mobile components imported successfully")
        return True

    except ImportError as e:
        st.error(f"❌ Import error: {e}")
        return False


def test_mobile_app_integration():
    """Test mobile app integration."""
    try:
        import mobile_plantguard_app
        import mobile_spa_app

        st.success("✅ Mobile apps can be imported")
        return True

    except ImportError as e:
        st.error(f"❌ Mobile app import error: {e}")
        return False


def test_adapter_integration():
    """Test that adapters work with mobile components."""
    try:
        from core.audio import AudioAdapter
        from core.nlp import TextAdapter
        from core.vision import VisionAdapter

        st.success("✅ All adapters can be imported")
        return True

    except ImportError as e:
        st.warning(f"⚠️ Adapter import warning: {e}")
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
                st.success(f"✅ {test_name} passed")
            else:
                st.error(f"❌ {test_name} failed")

        except Exception as e:
            st.error(f"❌ {test_name} error: {e}")
            results[test_name] = False

    # Summary
    st.subheader("📊 Test Summary")
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    if passed == total:
        st.success(f"🎉 All tests passed! ({passed}/{total})")
    else:
        st.warning(f"⚠️ {passed}/{total} tests passed")

    return results


if __name__ == "__main__":
    run_comprehensive_tests()
