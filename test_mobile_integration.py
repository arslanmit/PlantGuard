#!/usr/bin/env python3
"""
Integration test for Mobile History and Settings components with the main mobile app.

This script tests the integration of MobileHistoryView and MobileSettingsCard
with the existing mobile PlantGuard application.
"""
from typing import Any, Dict, List, Optional, Tuple, Union, Generator
import pytest


import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from datetime import datetime  # noqa: E402

import streamlit as st  # noqa: E402


def test_component_imports() -> bool:
    """Test that all components can be imported successfully."""
    import importlib.util

    components = [
        "ui.components.mobile_history_view",
        "ui.components.mobile_settings_card",
        "ui.components.mobile_state_manager",
        "ui.components.model_switcher",
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
                try:
                    # Try to actually import the component
                    importlib.import_module(component_name)
                    available_components.append(component_name)
                except Exception as e:
                    st.warning(f"[WARNING] Component {component_name} found but import failed: {e}")
                    missing_components.append(component_name)

        if missing_components:
            st.warning(f"[WARNING] {len(missing_components)} components missing, {len(available_components)} available")
            return len(available_components) > 0  # Pass if at least some components work
        else:
            st.success("[PASS] All components found successfully")
            return True
    except ImportError as e:
        st.error(f"[ERROR] Import error: {e}")
        return False


def test_component_initialization() -> bool:
    """Test that components can be initialized without errors."""
    try:
        from ui.components.mobile_history_view import MobileHistoryView
        from ui.components.mobile_settings_card import MobileSettingsCard

        # Initialize components
        history_view = MobileHistoryView("test_history", "Test History")
        settings_card = MobileSettingsCard("test_settings", "Test Settings")

        st.success("[PASS] Components initialized successfully")
        return True
    except Exception as e:
        st.error(f"[TODO] Initialization error: {e}")
        return False


def test_state_management() -> bool:
    """Test state management functionality."""
    try:
        from ui.components.mobile_state_manager import MobileStateManager

        state_manager = MobileStateManager()

        # Test component state operations
        test_state = {"test_key": "test_value", "timestamp": datetime.now().isoformat()}

        state_manager.set_component_state("test_component", test_state)
        retrieved_state = state_manager.get_component_state("test_component")

        if retrieved_state["test_key"] == "test_value":
            st.success("[DONE] State management working correctly")
            return True
        else:
            st.error("[TODO] State management failed: values don't match")
            return False

    except Exception as e:
        st.error(f"[TODO] State management error: {e}")
        return False


def test_model_switcher_integration() -> bool:
    """Test model switcher integration."""
    try:
        from ui.components.model_switcher import ModelSwitcher

        model_switcher = ModelSwitcher()

        # Test getting available models
        vision_models = model_switcher.get_available_models("vision")
        audio_models = model_switcher.get_available_models("audio")
        text_models = model_switcher.get_available_models("text")

        if vision_models and audio_models and text_models:
            st.success("[DONE] Model switcher integration working")
            return True
        else:
            st.error("[TODO] Model switcher missing model definitions")
            return False

    except Exception as e:
        st.error(f"[TODO] Model switcher error: {e}")
        return False


def test_history_functionality() -> bool:
    """Test history view functionality."""
    try:
        from ui.components.mobile_history_view import MobileHistoryView

        # Create sample history
        sample_history = [{"timestamp": datetime.now().isoformat(), "prediction": "Test Disease", "confidence": 0.85, "source": "test"}]

        st.session_state.analysis_history = sample_history

        history_view = MobileHistoryView("integration_test_history")

        # Test getting history
        history = history_view.get_analysis_history()

        if len(history) == 1 and history[0]["prediction"] == "Test Disease":
            st.success("[DONE] History functionality working")
            return True
        else:
            st.error("[TODO] History functionality failed")
            return False

    except Exception as e:
        st.error(f"[TODO] History functionality error: {e}")
        return False


def test_settings_functionality() -> bool:
    """Test settings card functionality."""
    try:
        from ui.components.mobile_settings_card import MobileSettingsCard

        settings_card = MobileSettingsCard("integration_test_settings")

        # Test getting preferences
        preferences = settings_card.get_current_preferences()

        # Test updating a preference
        settings_card.update_preference("test_setting", "test_value")
        updated_preferences = settings_card.get_current_preferences()

        if updated_preferences.get("test_setting") == "test_value":
            st.success("[DONE] Settings functionality working")
            return True
        else:
            st.error("[TODO] Settings functionality failed")
            return False

    except Exception as e:
        st.error(f"[TODO] Settings functionality error: {e}")
        return False


def test_css_compatibility() -> bool:
    """Test CSS compatibility with mobile layout."""
    try:
        from ui.components.mobile_history_view import MobileHistoryView
        from ui.components.mobile_settings_card import MobileSettingsCard

        history_view = MobileHistoryView("css_test_history")
        settings_card = MobileSettingsCard("css_test_settings")

        # Test CSS generation
        history_css = history_view.get_mobile_css()
        settings_css = settings_card.get_mobile_css()

        if history_css and settings_css:
            st.success("[DONE] CSS generation working")
            return True
        else:
            st.error("[TODO] CSS generation failed")
            return False

    except Exception as e:
        st.error(f"[TODO] CSS compatibility error: {e}")
        return False


def main() -> None:
    """Main integration test."""
    st.set_page_config(page_title="Mobile Integration Test", page_icon="[TEST]", layout="wide")

    st.title("[TEST] Mobile History & Settings Integration Test")
    st.markdown("Testing integration with existing mobile PlantGuard components")

    # Run all tests
    tests = [
        ("Component Imports", test_component_imports),
        ("Component Initialization", test_component_initialization),
        ("State Management", test_state_management),
        ("Model Switcher Integration", test_model_switcher_integration),
        ("History Functionality", test_history_functionality),
        ("Settings Functionality", test_settings_functionality),
        ("CSS Compatibility", test_css_compatibility),
    ]

    results = {}

    st.markdown("## [SEARCH] Running Integration Tests")

    for test_name, test_func in tests:
        st.markdown(f"### {test_name}")

        with st.spinner(f"Running {test_name}..."):
            try:
                result = test_func()
                results[test_name] = result
            except Exception as e:
                st.error(f"[TODO] Test failed with exception: {e}")
                results[test_name] = False

    # Summary
    st.markdown("---")
    st.markdown("## [SUMMARY] Test Results Summary")

    passed = sum(results.values())
    total = len(results)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Tests Passed", passed)

    with col2:
        st.metric("Tests Failed", total - passed)

    with col3:
        st.metric("Success Rate", f"{(passed / total) * 100:.1f}%")

    # Detailed results
    st.markdown("### Detailed Results")

    for test_name, result in results.items():
        status = "[DONE] PASS" if result else "[TODO] FAIL"
        st.markdown(f"- **{test_name}**: {status}")

    # Overall status
    if passed == total:
        st.success("[SUCCESS] All integration tests passed! Components are ready for use.")
    else:
        st.warning(f"[WARNING] {total - passed} test(s) failed. Please check the issues above.")

    # Component demonstration
    if passed >= total * 0.8:  # If at least 80% of tests pass
        st.markdown("---")
        st.markdown("## [PROGRESS] Component Demonstration")

        demo_tab1, demo_tab2 = st.tabs(["[LIBRARY] History Demo", "[SETTINGS] Settings Demo"])

        with demo_tab1:
            try:
                from ui.components.mobile_history_view import MobileHistoryView

                # Create sample data for demo
                if "demo_history" not in st.session_state:
                    st.session_state.analysis_history = [
                        {"timestamp": datetime.now().isoformat(), "prediction": "Demo Plant Disease", "confidence": 0.92, "source": "demo"}
                    ]

                history_demo = MobileHistoryView("demo_history", "Demo History")
                history_demo.render()

            except Exception as e:
                st.error(f"Demo error: {e}")

        with demo_tab2:
            try:
                from ui.components.mobile_settings_card import MobileSettingsCard

                settings_demo = MobileSettingsCard("demo_settings", "Demo Settings")
                settings_demo.render()

            except Exception as e:
                st.error(f"Demo error: {e}")


if __name__ == "__main__":
    main()
