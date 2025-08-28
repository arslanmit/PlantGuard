#!/usr/bin/env python3
"""
Test script for Mobile History and Settings Management components.

This script tests the MobileHistoryView and MobileSettingsCard components
to ensure they work correctly with the mobile PlantGuard interface.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from datetime import datetime  # noqa: E402

import streamlit as st  # noqa: E402

from ui.components.mobile_history_view import MobileHistoryView  # noqa: E402
from ui.components.mobile_settings_card import MobileSettingsCard  # noqa: E402

# Page configuration
st.set_page_config(page_title="Mobile History & Settings Test", page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

# Apply mobile CSS
st.markdown(
    """
<style>
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 428px;
        margin: 0 auto;
    }
</style>
""",
    unsafe_allow_html=True,
)


def create_sample_history():
    """Create sample analysis history for testing."""
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = [
            {
                "timestamp": "2024-01-15T10:30:00",
                "prediction": "Tomato Late Blight",
                "confidence": 0.92,
                "source": "camera",
                "metadata": {"model": "resnet50", "processing_time": 1.2},
            },
            {
                "timestamp": "2024-01-15T09:15:00",
                "prediction": "Healthy Plant",
                "confidence": 0.88,
                "source": "upload",
                "metadata": {"model": "resnet50", "processing_time": 0.8},
            },
            {
                "timestamp": "2024-01-14T16:45:00",
                "prediction": "Powdery Mildew",
                "confidence": 0.76,
                "source": "camera",
                "metadata": {"model": "resnet50", "processing_time": 1.5},
            },
            {
                "timestamp": "2024-01-14T14:20:00",
                "prediction": "Leaf Spot Disease",
                "confidence": 0.84,
                "source": "upload",
                "metadata": {"model": "resnet50", "processing_time": 1.1},
            },
            {
                "timestamp": "2024-01-13T11:10:00",
                "prediction": "Bacterial Wilt",
                "confidence": 0.69,
                "source": "voice",
                "metadata": {"model": "resnet50", "processing_time": 2.0},
            },
        ]


def main():
    """Main test application."""
    st.title("🧪 Mobile History & Settings Test")

    # Create sample data
    create_sample_history()

    # Test mode selection
    test_mode = st.selectbox("Select Test Mode", ["History View", "Settings Card", "Both Components"], key="test_mode_select")

    st.markdown("---")

    if test_mode == "History View":
        st.markdown("## 📚 Testing Mobile History View")

        # Create and render history view component
        history_view = MobileHistoryView("test_history_view", "Analysis History")
        history_view.render()

        # Test controls
        st.markdown("### [TOOL] Test Controls")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Add Sample Analysis", key="add_sample"):
                new_analysis = {
                    "timestamp": datetime.now().isoformat(),
                    "prediction": "Test Disease",
                    "confidence": 0.95,
                    "source": "test",
                    "metadata": {"test": True},
                }
                st.session_state.analysis_history.append(new_analysis)
                st.toast("Sample analysis added!", icon="[DONE]")
                st.rerun()

        with col2:
            if st.button("Clear History", key="clear_history"):
                history_view.clear_history()
                st.rerun()

        with col3:
            if st.button("Export JSON", key="export_json"):
                json_data = history_view.export_history_json()
                st.download_button("Download History", data=json_data, file_name="test_history.json", mime="application/json")

    elif test_mode == "Settings Card":
        st.markdown("## ⚙️ Testing Mobile Settings Card")

        # Create and render settings card component
        settings_card = MobileSettingsCard("test_settings_card", "App Settings")
        settings_card.render()

        # Test controls
        st.markdown("### [TOOL] Test Controls")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Show Current Preferences", key="show_prefs"):
                prefs = settings_card.get_current_preferences()
                st.json(prefs)

        with col2:
            if st.button("Show Settings Summary", key="show_summary"):
                summary = settings_card.get_settings_summary()
                st.json(summary)

    else:  # Both Components
        st.markdown("## [PARTIAL] Testing Both Components")

        # Tab interface for both components
        tab1, tab2 = st.tabs(["📚 History", "⚙️ Settings"])

        with tab1:
            history_view = MobileHistoryView("test_history_both", "Analysis History")
            history_view.render()

        with tab2:
            settings_card = MobileSettingsCard("test_settings_both", "App Settings")
            settings_card.render()

    # Component status
    st.markdown("---")
    st.markdown("### [SUMMARY] Component Status")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("History Entries", len(st.session_state.get("analysis_history", [])))

    with col2:
        prefs_count = len(st.session_state.get("user_preferences", {}))
        st.metric("User Preferences", prefs_count)

    # Debug information
    with st.expander("🐛 Debug Information"):
        st.markdown("**Session State Keys:**")
        st.write(list(st.session_state.keys()))

        if st.button("Clear All Session State", key="clear_session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.toast("Session state cleared!", icon="🗑️")
            st.rerun()


if __name__ == "__main__":
    main()
