"""Main Streamlit application for PlantGuard."""

import logging
from typing import Literal

import streamlit as st

from .components import ModelSwitcher, ModeSwitcher, render_status_indicator

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
        with st.chat_message("assistant"), st.spinner("Thinking..."):
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
    """Main Streamlit application - now using simplified interface."""
    # Import and run the simplified app
    from .simplified_app import SimplifiedPlantGuardApp
    
    app = SimplifiedPlantGuardApp()
    app.run()


def create_app():
    """Create and configure the Streamlit application.

    Returns:
        function: The main application function
    """
    return main


if __name__ == "__main__":
    main()
