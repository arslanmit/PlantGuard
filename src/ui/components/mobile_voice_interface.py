"""
Mobile Voice Interface for PlantGuard

Integrates AudioAdapter with mobile-optimized voice recording UI.
Provides touch-friendly voice recording, transcription, and audio file upload.
"""

import tempfile
import time
from typing import Any

import streamlit as st

# Import existing adapters
try:
    from core.audio import AudioAdapter
    from core.nlp import TextAdapter
except ImportError:
    # Fallback for development/testing
    from src.adapters_compat import AudioAdapter, TextAdapter

from .mobile_component_registry import ComponentMetadata, MobileComponent, register_mobile_component


@register_mobile_component
class MobileVoiceInterface(MobileComponent):
    """Mobile-optimized voice recording and processing interface.

    Features:
    - Touch-friendly recording controls
    - Real-time audio visualization
    - Voice transcription with AudioAdapter
    - Audio file upload support
    - Mobile-optimized playback
    - AI agent testable
    """

    def __init__(self, component_id: str = "mobile_voice_interface", **kwargs):
        super().__init__(component_id, **kwargs)
        self.audio_adapter = None
        self.text_adapter = None
        self.max_recording_duration = kwargs.get("max_recording_duration", 60)  # seconds
        self.supported_audio_formats = ["wav", "mp3", "m4a", "flac"]
        self.auto_transcribe = kwargs.get("auto_transcribe", True)

    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="voice_interface",
            display_name="Mobile Voice Interface",
            description="Mobile interface for voice recording and plant care questions",
            ai_agent_friendly_description=(
                "Voice interface component that provides mobile-optimized voice recording, "
                "audio file upload, transcription, and voice-based plant care assistance"
            ),
            interactive_elements=[
                {
                    "id": "audio_recorder",
                    "type": "audio_recorder",
                    "key": f"{self.component_id}_recorder",
                    "description": "Voice recording widget",
                    "testable": True,
                },
                {
                    "id": "audio_uploader",
                    "type": "file_uploader",
                    "key": f"{self.component_id}_audio_uploader",
                    "description": "Audio file upload widget",
                    "testable": True,
                },
                {
                    "id": "transcribe_button",
                    "type": "button",
                    "key": f"{self.component_id}_transcribe",
                    "description": "Transcription trigger button",
                    "testable": True,
                },
                {
                    "id": "clear_audio_button",
                    "type": "button",
                    "key": f"{self.component_id}_clear_audio",
                    "description": "Clear audio button",
                    "testable": True,
                },
                {
                    "id": "ask_question_button",
                    "type": "button",
                    "key": f"{self.component_id}_ask_question",
                    "description": "Process voice question button",
                    "testable": True,
                },
            ],
            state_dependencies=[
                "recorded_audio",
                "transcribed_text",
                "voice_response",
                "recording_in_progress",
                "transcription_in_progress",
                "audio_adapter_loaded",
            ],
            css_classes=["mobile-voice-interface", "mobile-voice-recorder", "mobile-audio-controls", "mobile-transcription-display"],
            test_scenarios=[
                {
                    "name": "audio_recording",
                    "description": "Test audio recording functionality",
                    "expected_outcome": "Audio records and plays back correctly",
                },
                {"name": "audio_upload", "description": "Test audio file upload", "expected_outcome": "Audio files upload and process correctly"},
                {"name": "transcription", "description": "Test voice transcription", "expected_outcome": "Audio transcribes to text accurately"},
                {
                    "name": "voice_questions",
                    "description": "Test voice-based plant care questions",
                    "expected_outcome": "Voice questions generate appropriate responses",
                },
            ],
            ai_agent_instructions={
                "testing": "Test recording, upload, transcription, question processing",
                "fixing": "Initialize AudioAdapter, handle recording errors, fix transcription issues",
                "monitoring": "Monitor audio quality, transcription accuracy, response times",
            },
            version="1.0.0",
            ai_agent_testable=True,
            auto_fix_enabled=True,
        )

    def initialize_voice_components(self) -> None:
        """Initialize voice processing components."""
        # Initialize session state
        if "recorded_audio" not in st.session_state:
            st.session_state.recorded_audio = None

        if "transcribed_text" not in st.session_state:
            st.session_state.transcribed_text = ""

        if "voice_response" not in st.session_state:
            st.session_state.voice_response = ""

        if "recording_in_progress" not in st.session_state:
            st.session_state.recording_in_progress = False

        if "transcription_in_progress" not in st.session_state:
            st.session_state.transcription_in_progress = False

        if "audio_adapter_loaded" not in st.session_state:
            st.session_state.audio_adapter_loaded = False

        # Initialize AudioAdapter if not already done
        if not self.audio_adapter:
            try:
                self.audio_adapter = AudioAdapter()
                st.session_state.audio_adapter_loaded = True
            except Exception as e:
                st.error(f"Failed to initialize AudioAdapter: {e}")
                st.session_state.audio_adapter_loaded = False

        # Initialize TextAdapter for processing transcribed questions
        if not self.text_adapter:
            try:
                self.text_adapter = TextAdapter()
            except Exception as e:
                st.warning(f"TextAdapter not available: {e}")

    def render_voice_recording_section(self) -> bytes | None:
        """Render voice recording interface.

        Returns:
            bytes: Recorded audio data or None
        """
        st.markdown("### [VOICE] Voice Recording")

        # Create tabs for recording vs upload
        record_tab, upload_tab = st.tabs(["[MICROPHONE]️ Record Voice", "[FOLDER] Upload Audio"])

        recorded_audio = None

        with record_tab:
            st.markdown("**Record your plant care question:**")

            # Audio recorder widget
            audio_data = st.audio_input(
                "Record your question", key=f"{self.component_id}_recorder", help=f"Record up to {self.max_recording_duration} seconds"
            )

            if audio_data:
                recorded_audio = audio_data.read()
                st.session_state.recorded_audio = recorded_audio

                # Show audio preview
                st.audio(recorded_audio, format="audio/wav")

                # Recording info
                st.success("[DONE] Audio recorded successfully!")

        with upload_tab:
            uploaded_audio = st.file_uploader(
                "Upload audio file",
                type=self.supported_audio_formats,
                key=f"{self.component_id}_audio_uploader",
                help="Upload an audio file with your plant care question",
            )

            if uploaded_audio:
                try:
                    recorded_audio = uploaded_audio.read()
                    st.session_state.recorded_audio = recorded_audio

                    # Show audio preview
                    st.audio(recorded_audio, format=f"audio/{uploaded_audio.type.split('/')[1]}")

                    # File info
                    st.success(f"[DONE] Audio file uploaded: {uploaded_audio.name}")

                except Exception as e:
                    st.error(f"Error processing audio file: {e}")

        return recorded_audio

    def render_transcription_section(self, has_audio: bool) -> str:
        """Render transcription controls and results.

        Returns:
            str: Transcribed text
        """
        if not has_audio:
            st.info("[SOUND] Record or upload audio to start transcription")
            return ""

        st.markdown("#### [WRITE] Transcription")

        # Transcription controls
        col1, col2 = st.columns(2)

        with col1:
            transcribe_clicked = st.button(
                "[TEXT] Transcribe Audio",
                key=f"{self.component_id}_transcribe",
                use_container_width=True,
                disabled=st.session_state.get("transcription_in_progress", False),
                type="primary",
            )

        with col2:
            clear_clicked = st.button("[DELETE] Clear Audio", key=f"{self.component_id}_clear_audio", use_container_width=True)

        if clear_clicked:
            self.clear_audio_data()
            st.rerun()

        # Perform transcription if requested
        transcribed_text = st.session_state.get("transcribed_text", "")

        if transcribe_clicked:
            transcribed_text = self.perform_transcription()

        # Show transcription results
        if transcribed_text:
            st.markdown("**Transcribed Text:**")

            # Editable text area for corrections
            corrected_text = st.text_area(
                "Edit transcription if needed:",
                value=transcribed_text,
                height=100,
                key=f"{self.component_id}_transcribed_text",
                help="You can edit the transcription to correct any errors",
            )

            # Update session state with corrected text
            if corrected_text != transcribed_text:
                st.session_state.transcribed_text = corrected_text
                transcribed_text = corrected_text

        return transcribed_text

    def perform_transcription(self) -> str:
        """Perform audio transcription using AudioAdapter.

        Returns:
            str: Transcribed text
        """
        if not self.audio_adapter:
            st.error("Audio adapter not available for transcription")
            return ""

        recorded_audio = st.session_state.get("recorded_audio")
        if not recorded_audio:
            st.error("No audio data available for transcription")
            return ""

        try:
            st.session_state.transcription_in_progress = True

            # Progress indicator
            with st.spinner("Transcribing audio... This may take a moment."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Create temporary file for audio processing
                status_text.text("Preparing audio for processing...")
                progress_bar.progress(20)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(recorded_audio)
                    temp_file_path = temp_file.name

                # Transcribe audio
                status_text.text("Processing speech...")
                progress_bar.progress(60)

                transcribed_text = self.audio_adapter.transcribe(temp_file_path)

                progress_bar.progress(100)
                status_text.text("Transcription complete!")

                # Clean up progress indicators
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()

                # Store result
                st.session_state.transcribed_text = transcribed_text

                if transcribed_text.strip():
                    st.success("[DONE] Transcription completed!")
                else:
                    st.warning("[WARNING] No speech detected in audio")

                return transcribed_text

        except Exception as e:
            st.error(f"Transcription failed: {e}")
            return ""
        finally:
            st.session_state.transcription_in_progress = False
            # Clean up temporary file
            with suppress(Exception):
                from pathlib import Path

                if "temp_file_path" in locals():
                    Path(temp_file_path).unlink()

    def render_voice_question_section(self, transcribed_text: str) -> str:
        """Render voice question processing section.

        Returns:
            str: Generated response
        """
        if not transcribed_text.strip():
            return ""

        st.markdown("#### [THINKING] Plant Care Question")

        # Show the question
        st.markdown("**Your Question:**")
        st.info(f"[CHAT] {transcribed_text}")

        # Ask question button
        ask_clicked = st.button("[PLANT] Get Plant Care Answer", key=f"{self.component_id}_ask_question", use_container_width=True, type="primary")

        response = st.session_state.get("voice_response", "")

        if ask_clicked:
            response = self.process_voice_question(transcribed_text)

        # Show response
        if response:
            st.markdown("**AI Response:**")
            st.markdown(f"[AI] {response}")

        return response

    def process_voice_question(self, question: str) -> str:
        """Process voice question and generate response.

        Args:
            question: Transcribed question text

        Returns:
            str: Generated response
        """
        if not question.strip():
            return ""

        try:
            with st.spinner("Generating response..."):
                if self.text_adapter:
                    # Use TextAdapter for generating response
                    response = self.text_adapter.generate_response(disease_class="general", user_query=question, confidence=0.0)
                else:
                    # Fallback response
                    response = self._generate_fallback_response(question)

                st.session_state.voice_response = response
                return response

        except Exception as e:
            error_response = f"I apologize, but I encountered an error processing your question: {e}"
            st.session_state.voice_response = error_response
            return error_response

    def _generate_fallback_response(self, question: str) -> str:
        """Generate fallback response when TextAdapter is not available."""
        return f"""Thank you for your plant care question: "{question}"

I'd be happy to help! Here are some general plant care tips:

[PLANT] **Watering**: Check soil moisture before watering. Most plants prefer slightly moist soil.

☀️ **Light**: Ensure your plant gets appropriate light for its species.

[LEAF] **Air Circulation**: Good airflow helps prevent fungal issues.

[POT] **Soil**: Use well-draining soil appropriate for your plant type.

For specific advice about your plant's symptoms or care needs, consider consulting with a local plant expert or uploading a photo for visual analysis."""

    def clear_audio_data(self) -> None:
        """Clear all audio-related data."""
        st.session_state.recorded_audio = None
        st.session_state.transcribed_text = ""
        st.session_state.voice_response = ""
        st.session_state.recording_in_progress = False
        st.session_state.transcription_in_progress = False

    def render(self, **kwargs) -> dict[str, Any]:
        """Render the complete mobile voice interface.

        Returns:
            Dict containing voice processing results
        """
        # Initialize components
        self.initialize_voice_components()

        # Main container
        st.markdown('<div class="mobile-voice-interface" data-component="mobile-voice-interface" data-testable="true">', unsafe_allow_html=True)

        # Check if AudioAdapter is available
        if not st.session_state.get("audio_adapter_loaded", False):
            st.warning("[WARNING] Voice processing not available. Please check system configuration.")
            st.markdown("[MOBILE] Voice features require audio processing capabilities.")
            st.markdown("</div>", unsafe_allow_html=True)
            return {"error": "AudioAdapter not loaded", "success": False}

        # Voice recording section
        recorded_audio = self.render_voice_recording_section()

        # Transcription section
        current_audio = recorded_audio or st.session_state.get("recorded_audio")
        transcribed_text = self.render_transcription_section(current_audio is not None)

        # Voice question processing
        current_text = transcribed_text or st.session_state.get("transcribed_text", "")
        response = self.render_voice_question_section(current_text)

        # Usage tips
        with st.expander("[TIP] Voice Assistant Tips"):
            st.markdown("""
            **How to use the Voice Assistant:**
            
            1. **Record**: Tap the record button and speak clearly
            2. **Upload**: Or upload an existing audio file
            3. **Transcribe**: Convert speech to text
            4. **Ask**: Get AI-powered plant care answers
            
            **Best Practices:**
            - Speak clearly and at normal pace
            - Ask specific questions (e.g., "Why are my tomato leaves yellowing?")
            - Minimize background noise
            - Keep questions under 60 seconds
            
            **Example Questions:**
            - "What's wrong with my plant's leaves?"
            - "How often should I water my succulent?"
            - "My plant has brown spots, what should I do?"
            """)

        # Close container
        st.markdown("</div>", unsafe_allow_html=True)

        return {
            "has_audio": current_audio is not None,
            "transcribed_text": current_text,
            "response": response,
            "success": bool(response) if current_text else True,
        }

    def get_voice_status(self) -> dict[str, Any]:
        """Get current voice interface status for AI agent monitoring."""
        return {
            "component_id": self.component_id,
            "audio_adapter_loaded": st.session_state.get("audio_adapter_loaded", False),
            "text_adapter_available": self.text_adapter is not None,
            "has_recorded_audio": st.session_state.get("recorded_audio") is not None,
            "has_transcribed_text": bool(st.session_state.get("transcribed_text", "").strip()),
            "has_voice_response": bool(st.session_state.get("voice_response", "").strip()),
            "recording_in_progress": st.session_state.get("recording_in_progress", False),
            "transcription_in_progress": st.session_state.get("transcription_in_progress", False),
            "supported_audio_formats": self.supported_audio_formats,
            "max_recording_duration": self.max_recording_duration,
            "auto_transcribe": self.auto_transcribe,
        }


# Utility functions
def create_mobile_voice_interface(max_recording_duration: int = 60, auto_transcribe: bool = True) -> MobileVoiceInterface:
    """Create and return a MobileVoiceInterface instance."""
    return MobileVoiceInterface(component_id="mobile_voice_interface", max_recording_duration=max_recording_duration, auto_transcribe=auto_transcribe)


def render_voice_assistant_interface() -> dict[str, Any]:
    """Convenience function to render voice assistant interface."""
    voice_interface = create_mobile_voice_interface()
    return voice_interface.render()
