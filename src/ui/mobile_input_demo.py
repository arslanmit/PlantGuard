"""
Mobile Input Components Demo App.

This demo showcases all mobile input components in a unified interface
to demonstrate their functionality and integration.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# Import mobile components
from ui.components.mobile_camera_input import MobileCameraInput
from ui.components.mobile_text_input import MobileTextInput
from ui.components.mobile_upload_input import MobileUploadInput
from ui.components.mobile_voice_input import MobileVoiceInput

logger = logging.getLogger(__name__)


def load_mobile_css():
    """Load mobile-optimized CSS styles."""
    css = """
    <style>
    /* Mobile-first responsive design */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* Mobile component styling */
    .mobile-component {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    .mobile-input-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .mobile-button {
        min-height: 48px;
        min-width: 48px;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
        touch-action: manipulation;
    }
    
    .mobile-upload-dropzone {
        border: 2px dashed #ccc;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 16px 0;
        background: #f9f9f9;
    }
    
    .upload-icon {
        font-size: 48px;
        margin-bottom: 10px;
    }
    
    .upload-hint {
        color: #666;
        font-size: 14px;
    }
    
    /* Touch optimization */
    @media (max-width: 768px) {
        .mobile-input-grid {
            grid-template-columns: 1fr;
            gap: 8px;
        }
        
        .main .block-container {
            padding: 0.5rem;
        }
        
        .mobile-component {
            padding: 12px;
            margin-bottom: 12px;
        }
    }
    
    /* Loading animations */
    .mobile-spinner {
        border: 3px solid #f3f3f3;
        border-top: 3px solid #16A34A;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        animation: spin 1s linear infinite;
        display: inline-block;
        margin-right: 8px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active { background-color: #22C55E; }
    .status-inactive { background-color: #9CA3AF; }
    .status-error { background-color: #EF4444; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_demo_header():
    """Render demo application header."""
    st.markdown(
        """
        <div style="text-align: center; padding: 20px 0;">
            <h1>🌿 PlantGuard Mobile Input Demo</h1>
            <p style="color: #666; font-size: 18px;">
                Experience mobile-optimized plant care assistance
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_input_grid():
    """Render the main input grid with all components."""
    st.markdown("### [MOBILE] Choose Your Input Method")

    # Create 2x2 grid for input methods
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📷 Camera\nTake Photo", key="camera_grid_btn", help="Use device camera to capture plant images", use_container_width=True):
            st.session_state.selected_input = "camera"

        if st.button("🎤 Voice\nAsk Question", key="voice_grid_btn", help="Record voice question about plant care", use_container_width=True):
            st.session_state.selected_input = "voice"

    with col2:
        if st.button("📁 Upload\nSelect Image", key="upload_grid_btn", help="Upload plant image from device storage", use_container_width=True):
            st.session_state.selected_input = "upload"

        if st.button("💬 Text\nType Message", key="text_grid_btn", help="Type your plant care question", use_container_width=True):
            st.session_state.selected_input = "text"


def render_selected_component():
    """Render the selected input component."""
    selected = st.session_state.get("selected_input")

    if not selected:
        st.info("👆 Select an input method above to get started")
        return

    st.markdown("---")

    # Initialize components if not already done
    if "mobile_components" not in st.session_state:
        st.session_state.mobile_components = {
            "camera": MobileCameraInput("demo_camera", "Camera Input"),
            "upload": MobileUploadInput("demo_upload", "Upload Input"),
            "voice": MobileVoiceInput("demo_voice", "Voice Input"),
            "text": MobileTextInput("demo_text", "Text Input"),
        }

    components = st.session_state.mobile_components

    # Render selected component
    if selected == "camera":
        st.markdown("### 📷 Camera Input")
        components["camera"].render()

    elif selected == "upload":
        st.markdown("### 📁 Upload Input")
        components["upload"].render()

    elif selected == "voice":
        st.markdown("### 🎤 Voice Input")
        components["voice"].render()

    elif selected == "text":
        st.markdown("### 💬 Text Input")
        components["text"].render()


def render_analysis_results():
    """Render analysis results if available."""
    if "analysis_results" in st.session_state and st.session_state.analysis_results:
        st.markdown("---")
        st.markdown("### 🔍 Analysis Results")

        # Show latest result
        latest_result = st.session_state.analysis_results[-1]

        col1, col2 = st.columns([1, 2])

        with col1:
            if "image" in latest_result:
                st.image(latest_result["image"], caption="Analyzed Image", use_column_width=True)

        with col2:
            disease_name, confidence = latest_result["prediction"]

            st.markdown(f"**Disease:** {disease_name}")
            st.markdown(f"**Confidence:** {confidence:.1%}")
            st.markdown(f"**Source:** {latest_result['source']}")
            st.markdown(f"**Time:** {latest_result['timestamp'][:19]}")

            # Confidence indicator
            if confidence > 0.7:
                st.success("🟢 High confidence result")
            elif confidence > 0.5:
                st.warning("🟡 Medium confidence result")
            else:
                st.error("🔴 Low confidence result")


def render_chat_history():
    """Render chat history if available."""
    if "chat_history" in st.session_state and st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### 💬 Chat History")

        # Show recent messages
        recent_messages = st.session_state.chat_history[-5:]  # Last 5 messages

        for message in recent_messages:
            role = message["role"]
            content = message["content"]
            timestamp = message["timestamp"][:19]

            if role == "user":
                st.markdown(
                    f"""
                    <div style="background: #E3F2FD; padding: 10px; border-radius: 10px; margin: 5px 0;">
                        <strong>You ({timestamp}):</strong><br>
                        {content}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background: #F1F8E9; padding: 10px; border-radius: 10px; margin: 5px 0;">
                        <strong>PlantGuard ({timestamp}):</strong><br>
                        {content}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_demo_footer():
    """Render demo footer with additional information."""
    st.markdown("---")

    with st.expander("i About This Demo", expanded=False):
        st.markdown("""
        **PlantGuard Mobile Input Demo** showcases the mobile-optimized input components:
        
        - **📷 Camera Input**: Real-time camera access for plant image capture
        - **📁 Upload Input**: File selection with drag-and-drop support
        - **🎤 Voice Input**: Audio recording with speech-to-text processing
        - **💬 Text Input**: Chat interface with suggestions and validation
        
        **Features:**
        - Touch-optimized interface with 48px minimum touch targets
        - Responsive design that works on all mobile devices
        - Offline-capable plant disease detection
        - Real-time audio/video processing with streamlit-webrtc
        - Comprehensive error handling and recovery
        
        **Technical Stack:**
        - Streamlit for UI framework
        - streamlit-webrtc for real-time media
        - PIL for image processing
        - Whisper for speech-to-text
        - ResNet50 for plant disease detection
        """)

    # Component status
    with st.expander("[TOOL] Component Status", expanded=False):
        if "mobile_components" in st.session_state:
            components = st.session_state.mobile_components

            for name, component in components.items():
                state = component.get_state()
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**{name.title()}:**")

                with col2:
                    if component.has_error():
                        st.markdown("🔴 Error")
                    elif component.is_loading():
                        st.markdown("🟡 Loading")
                    else:
                        st.markdown("🟢 Ready")

                with col3:
                    st.write(f"ID: {component.component_id}")


def main():
    """Main demo application."""
    # Configure Streamlit page
    st.set_page_config(page_title="PlantGuard Mobile Input Demo", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")

    # Load mobile CSS
    load_mobile_css()

    # Initialize session state
    if "selected_input" not in st.session_state:
        st.session_state.selected_input = None

    # Render demo interface
    render_demo_header()
    render_input_grid()
    render_selected_component()
    render_analysis_results()
    render_chat_history()
    render_demo_footer()


if __name__ == "__main__":
    main()
