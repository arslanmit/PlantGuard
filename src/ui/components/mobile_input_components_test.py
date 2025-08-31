from typing import Any, Dict, List, Optional, Tuple, Union, Generator
"""
Test script for mobile input components.

This script tests the basic functionality of all mobile input components
to ensure they can be instantiated and rendered without errors.
"""


import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

# Import mobile components
from .mobile_camera_input import MobileCameraInput
from .mobile_text_input import MobileTextInput
from .mobile_upload_input import MobileUploadInput
from .mobile_voice_input import MobileVoiceInput

logger = logging.getLogger(__name__)


def test_mobile_input_components() -> None:
    """Test all mobile input components."""
    st.title("[TEST] Mobile Input Components Test")

    st.markdown("---")
    st.markdown("## Testing Mobile Input Components")

    try:
        # Test component creation
        st.markdown("### 1. Component Creation Test")

        # Create components
        camera_input = MobileCameraInput("test_camera", "Test Camera")
        upload_input = MobileUploadInput("test_upload", "Test Upload")
        voice_input = MobileVoiceInput("test_voice", "Test Voice")
        text_input = MobileTextInput("test_text", "Test Text")

        st.success("[DONE] All components created successfully!")

        # Test component metadata
        st.markdown("### 2. Component Metadata Test")

        components = [("Camera Input", camera_input), ("Upload Input", upload_input), ("Voice Input", voice_input), ("Text Input", text_input)]

        for name, component in components:
            metadata = component.get_metadata()
            st.write(f"**{name}:**")
            st.json(
                {
                    "component_id": metadata["component_id"],
                    "component_type": metadata["component_type"],
                    "css_classes": metadata["css_classes"][:3],  # Show first 3 classes
                }
            )

        st.success("[DONE] All component metadata retrieved successfully!")

        # Test component rendering
        st.markdown("### 3. Component Rendering Test")

        # Create tabs for each component
        tab1, tab2, tab3, tab4 = st.tabs(["[CAMERA] Camera", "[FOLDER] Upload", "[VOICE] Voice", "[CHAT] Text"])

        with tab1:
            st.markdown("#### Camera Input Component")
            try:
                camera_input.render()
                st.success("[DONE] Camera component rendered successfully!")
            except Exception as e:
                st.error(f"[TODO] Camera component error: {e}")

        with tab2:
            st.markdown("#### Upload Input Component")
            try:
                upload_input.render()
                st.success("[DONE] Upload component rendered successfully!")
            except Exception as e:
                st.error(f"[TODO] Upload component error: {e}")

        with tab3:
            st.markdown("#### Voice Input Component")
            try:
                voice_input.render()
                st.success("[DONE] Voice component rendered successfully!")
            except Exception as e:
                st.error(f"[TODO] Voice component error: {e}")

        with tab4:
            st.markdown("#### Text Input Component")
            try:
                text_input.render()
                st.success("[DONE] Text component rendered successfully!")
            except Exception as e:
                st.error(f"[TODO] Text component error: {e}")

        # Test state management
        st.markdown("### 4. State Management Test")

        for name, component in components:
            state = component.get_state()
            st.write(f"**{name} State:**")
            st.json({"initialized": state.get("initialized"), "component_id": state.get("component_id"), "has_data": bool(state.get("data"))})

        st.success("[DONE] All component states retrieved successfully!")

        # Component interaction test
        st.markdown("### 5. Component Interaction Test")

        if st.button("[TEST] Test Component Methods"):
            test_results = []

            for name, component in components:
                try:
                    # Test visibility
                    component.set_visible(True)
                    is_visible = component.is_visible()

                    # Test loading state
                    component.set_loading(False)
                    is_loading = component.is_loading()

                    # Test error handling
                    component.clear_error()
                    has_error = component.has_error()

                    test_results.append(
                        {"component": name, "visible": is_visible, "loading": is_loading, "has_error": has_error, "status": "[DONE] Pass"}
                    )

                except Exception as e:
                    test_results.append({"component": name, "error": str(e), "status": "[TODO] Fail"})

            # Display results
            for result in test_results:
                st.write(f"**{result['component']}:** {result['status']}")
                if result.get("error"):
                    st.error(f"Error: {result['error']}")

        st.markdown("---")
        st.success("[SUCCESS] Mobile Input Components Test Complete!")

    except Exception as e:
        st.error(f"[TODO] Test failed: {e}")
        st.exception(e)


if __name__ == "__main__":
    # Configure Streamlit page
    st.set_page_config(page_title="Mobile Input Components Test", page_icon="[TEST]", layout="wide")

    # Run tests
    test_mobile_input_components()
