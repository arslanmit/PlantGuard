#!/usr/bin/env python3
"""
Integration test for Mobile History and Settings components with the main mobile app.

This script tests the integration of MobileHistoryView and MobileSettingsCard
with the existing mobile PlantGuard application.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from datetime import datetime  # noqa: E402

import streamlit as st  # noqa: E402


def test_component_imports():
    """Test that all components can be imported successfully."""
    import importlib.util

    components = [
        "ui.components.mobile_history_view",
        "ui.components.mobile_settings_card",
        "ui.components.mobile_state_manager",
        "ui.components.model_switcher",
    ]

    try:
        for component_name in components:
            spec = importlib.util.find_spec(component_name)
            if spec is None:
                st.error(f"❌ Component not found: {component_name}")
                return False

        st.success("✅ All components found successfully")
        return True
    except ImportError as e:
        st.error(f"❌ Import error: {e}")
        return False


def test_component_initialization():
    """Test that components can be initialized without errors."""
    try:
        from ui.components.mobile_history_view import MobileHistoryView
        from ui.components.mobile_settings_card import MobileSettingsCard

        # Initialize components
        history_view = MobileHistoryView("test_history", "Test History")
        settings_card = MobileSettingsCard("test_settings", "Test Settings")

        st.success("✅ Components initialized successfully")
        return True
    except Exception as e:
        st.error(f"❌ Initialization error: {e}")
        return False


def test_state_management():
    """Test state management functionality."""
    try:
        from ui.components.mobile_state_manager import MobileStateManager

        state_manager = MobileStateManager()

        # Test component state operations
        test_state = {"test_key": "test_value", "timestamp": datetime.now().isoformat()}

        state_manager.set_component_state("test_component", test_state)
        retrieved_state = state_manager.get_component_state("test_component")

        if retrieved_state["test_key"] == "test_value":
            st.success("✅ State management working correctly")
            return True
        else:
            st.error("❌ State management failed: values don't match")
            return False

    except Exception as e:
        st.error(f"❌ State management error: {e}")
        return False


def test_model_switcher_integration():
    """Test model switcher integration."""
    try:
        from ui.components.model_switcher import ModelSwitcher

        model_switcher = ModelSwitcher()

        # Test getting available models
        vision_models = model_switcher.get_available_models("vision")
        audio_models = model_switcher.get_available_models("audio")
        text_models = model_switcher.get_available_models("text")

        if vision_models and audio_models and text_models:
            st.success("✅ Model switcher integration working")
            return True
        else:
            st.error("❌ Model switcher missing model definitions")
            return False

    except Exception as e:
        st.error(f"❌ Model switcher error: {e}")
        return False


def test_history_functionality():
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
            st.success("✅ History functionality working")
            return True
        else:
            st.error("❌ History functionality failed")
            return False

    except Exception as e:
        st.error(f"❌ History functionality error: {e}")
        return False


def test_settings_functionality():
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
            st.success("✅ Settings functionality working")
            return True
        else:
            st.error("❌ Settings functionality failed")
            return False

    except Exception as e:
        st.error(f"❌ Settings functionality error: {e}")
        return False


def test_css_compatibility():
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
            st.success("✅ CSS generation working")
            return True
        else:
            st.error("❌ CSS generation failed")
            return False

    except Exception as e:
        st.error(f"❌ CSS compatibility error: {e}")
        return False


def main():
    """Main integration test."""
    st.set_page_config(page_title="Mobile Integration Test", page_icon="🧪", layout="wide")

    st.title("🧪 Mobile History & Settings Integration Test")
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

    st.markdown("## 🔍 Running Integration Tests")

    for test_name, test_func in tests:
        st.markdown(f"### {test_name}")

        with st.spinner(f"Running {test_name}..."):
            try:
                result = test_func()
                results[test_name] = result
            except Exception as e:
                st.error(f"❌ Test failed with exception: {e}")
                results[test_name] = False

    # Summary
    st.markdown("---")
    st.markdown("## 📊 Test Results Summary")

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
        status = "✅ PASS" if result else "❌ FAIL"
        st.markdown(f"- **{test_name}**: {status}")

    # Overall status
    if passed == total:
        st.success("🎉 All integration tests passed! Components are ready for use.")
    else:
        st.warning(f"⚠️ {total - passed} test(s) failed. Please check the issues above.")

    # Component demonstration
    if passed >= total * 0.8:  # If at least 80% of tests pass
        st.markdown("---")
        st.markdown("## 🎯 Component Demonstration")

        demo_tab1, demo_tab2 = st.tabs(["📚 History Demo", "⚙️ Settings Demo"])

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
