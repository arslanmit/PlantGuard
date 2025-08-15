"""Main Streamlit application for PlantGuard."""

import logging
from typing import Literal

import streamlit as st

from .components import ModelSwitcher, ModeSwitcher, ThemeSwitcher, render_status_indicator

logger = logging.getLogger(__name__)

# Type alias for input modes
InputMode = Literal["vision", "audio", "text"]


def render_mode_switcher() -> InputMode:
    """Render the mode switcher and return selected mode."""
    st.markdown("### 🔄 Input Mode")

    # Create three columns for the mode buttons
    col1, col2, col3 = st.columns(3)

    # Initialize session state for mode if not exists
    if "input_mode" not in st.session_state:
        st.session_state.input_mode = "vision"

    with col1:
        if st.button(
            "📷 Vision Mode",
            use_container_width=True,
            type="primary" if st.session_state.input_mode == "vision" else "secondary",
        ):
            st.session_state.input_mode = "vision"

    with col2:
        if st.button(
            "🎤 Audio Mode",
            use_container_width=True,
            type="primary" if st.session_state.input_mode == "audio" else "secondary",
        ):
            st.session_state.input_mode = "audio"

    with col3:
        if st.button(
            "💬 Text Mode",
            use_container_width=True,
            type="primary" if st.session_state.input_mode == "text" else "secondary",
        ):
            st.session_state.input_mode = "text"

    return st.session_state.input_mode


def render_vision_mode() -> None:
    """Render the vision input interface."""
    st.markdown("#### 📷 Plant Image Analysis")
    st.markdown("Upload a clear image of a plant leaf to detect diseases and get treatment recommendations.")

    uploaded_file = st.file_uploader(
        "Choose a plant image...",
        type=["jpg", "jpeg", "png"],
        help="Supported formats: JPG, JPEG, PNG (max 200MB)",
    )

    if uploaded_file is not None:
        # Display the uploaded image
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

        with col2:
            st.markdown("**Analysis Results:**")
            with st.spinner("Analyzing image..."):
                # Placeholder for vision model inference
                st.info("🚧 Vision model integration pending")
                st.markdown("""
                **Detected Disease:** *Analysis in progress*
                **Confidence:** *Calculating...*
                **Recommendations:** *Loading...*
                """)


def render_audio_mode() -> None:
    """Render the audio input interface."""
    st.markdown("#### 🎤 Voice Input")
    st.markdown("Record your voice to ask questions about plant care or describe symptoms.")

    # Audio recording placeholder
    st.info("🚧 Audio recording functionality will be implemented with streamlit-webrtc")

    # File upload as alternative
    st.markdown("**Or upload an audio file:**")
    audio_file = st.file_uploader(
        "Choose an audio file...",
        type=["wav", "mp3"],
        help="Supported formats: WAV, MP3 (1-60 seconds)",
    )

    if audio_file is not None:
        st.audio(audio_file, format="audio/wav")
        with st.spinner("Processing audio..."):
            st.info("🚧 Audio processing integration pending")
            st.markdown("""
            **Transcription:** *Processing...*
            **Response:** *Generating...*
            """)


def render_text_mode() -> None:
    """Render the text input interface."""
    st.markdown("#### 💬 Text Chat")
    st.markdown("Ask questions about plant diseases, care tips, or treatment recommendations.")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about plant diseases, symptoms, or care tips..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Placeholder for text model inference
                response = "🚧 Text processing model integration pending. Your question has been received!"
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})


def render_system_status() -> None:
    """Render system status information."""
    with st.expander("🔧 System Status", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Model Status:**")
            render_status_indicator("not_loaded", "Vision Model")
            render_status_indicator("not_loaded", "Audio Model")
            render_status_indicator("not_loaded", "Text Model")
            render_status_indicator("not_loaded", "Fusion Model")

        with col2:
            st.markdown("**System Info:**")
            render_status_indicator("loading", "GPU Detection")
            render_status_indicator("loaded", "Offline Mode")
            st.markdown("🔄 **Memory Usage**: Monitoring...")
            st.markdown("🌐 **Network**: Offline-first")


def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(page_title="🌱 PlantGuard", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

    # Header
    st.title("🌱 PlantGuard Assistant")
    st.markdown("""
    **Multimodal Plant Disease Detection System**

    Choose your preferred input method below to get AI-powered plant disease diagnosis
    and treatment recommendations.
    """)

    # Initialize switchers
    mode_switcher = ModeSwitcher()
    theme_switcher = ThemeSwitcher()
    model_switcher = ModelSwitcher()

    # Render theme switcher in sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        theme_switcher.render(location="sidebar")

        # Model switcher
        st.markdown("---")
        available_models = {
            "vision": ["resnet50_plantvillage_v1", "efficientnet_b0_plants", "vit_base_plants"],
            "audio": ["whisper_tiny_local", "wav2vec2_plant_sounds"],
            "text": ["distilbert_plant_qa_v1", "roberta_plant_care", "t5_small_plant_qa"],
        }
        model_switcher.render(available_models)

    # Mode switcher
    selected_mode = mode_switcher.render()

    st.markdown("---")

    # Render the appropriate interface based on selected mode
    if selected_mode == "vision":
        render_vision_mode()
    elif selected_mode == "audio":
        render_audio_mode()
    elif selected_mode == "text":
        render_text_mode()

    # System status
    st.markdown("---")
    render_system_status()

    # Development progress
    st.markdown("---")
    st.markdown("**🚀 Development Progress:**")
    progress_col1, progress_col2 = st.columns(2)

    with progress_col1:
        st.markdown("✅ Environment Setup")
        st.markdown("✅ Mode Switcher UI")
        st.markdown("⏳ Vision Model Integration")
        st.markdown("⏳ Audio Processing")

    with progress_col2:
        st.markdown("⏳ Text Processing")
        st.markdown("⏳ Model Fusion")
        st.markdown("⏳ Knowledge Base")
        st.markdown("⏳ Real-time Processing")


if __name__ == "__main__":
    main()
