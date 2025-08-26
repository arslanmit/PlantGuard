"""
Mobile Voice Input Component for PlantGuard UI.

This module provides a mobile-optimized voice input component with
audio recording using streamlit-webrtc and speech-to-text processing.
"""

import logging
import tempfile
import time
from datetime import datetime
from typing import Any

import streamlit as st
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer

from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileVoiceInput(MobileBaseComponent):
    """Mobile-optimized voice input component with audio recording."""

    def __init__(self, component_id: str, title: str = "Voice Input", **kwargs):
        """
        Initialize mobile voice input component.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Voice recording configuration
        self.voice_config = {
            "audio_constraints": {
                "sampleRate": 16000,  # Optimal for Whisper
                "channelCount": 1,  # Mono audio
                "echoCancellation": True,
                "noiseSuppression": True,
                "autoGainControl": True,
            },
            "max_recording_duration": 60,  # 60 seconds max
            "min_recording_duration": 1,  # 1 second min
            "rtc_configuration": RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
        }

        # Initialize voice state
        self._initialize_voice_state()

        logger.debug("MobileVoiceInput initialized: %s", component_id)

    def _initialize_voice_state(self) -> None:
        """Initialize voice-specific state."""
        voice_state = {
            "recording": False,
            "recording_start_time": None,
            "recording_duration": 0,
            "audio_data": None,
            "transcription": None,
            "last_recording": None,
            "permission_granted": False,
            "microphone_active": False,
            "processing_status": "idle",  # idle, recording, processing, complete, error
        }

        current_state = self.get_state()
        if "voice_data" not in current_state["data"]:
            current_state["data"]["voice_data"] = voice_state
            self.set_state(current_state)

    def render(self) -> None:
        """Render the mobile voice input interface."""
        try:
            # Get current state
            state = self.get_state()
            voice_data = state["data"].get("voice_data", {})

            # Render voice interface container
            st.markdown(
                f"""
                <div class="mobile-voice-input mobile-component" 
                     data-component-id="{self.component_id}"
                     data-testid="voice-input-{self.component_id}">
                """,
                unsafe_allow_html=True,
            )

            # Voice recording interface
            self._render_voice_interface(voice_data)

            # Show recording status
            if voice_data.get("recording"):
                self._render_recording_status(voice_data)

            # Show processing status
            if voice_data.get("processing_status") == "processing":
                self._render_processing_status()

            # Display transcription if available
            if voice_data.get("transcription"):
                self._render_transcription(voice_data["transcription"])

            # Display last recording if available
            if voice_data.get("last_recording"):
                self._render_last_recording(voice_data["last_recording"])

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Voice input rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)

    def _render_voice_interface(self, voice_data: dict[str, Any]) -> None:
        """Render the main voice recording interface."""
        # Voice recording button
        col1, col2 = st.columns([3, 1])

        with col1:
            if voice_data.get("recording"):
                # Stop recording button
                if st.button(
                    "🛑 Stop Recording", key=f"{self.component_id}_stop_btn", help="Stop voice recording", use_container_width=True, type="secondary"
                ):
                    self._stop_recording()
            else:
                # Start recording button
                if st.button(
                    "🎤 Start Recording",
                    key=f"{self.component_id}_start_btn",
                    help="Start voice recording (hold to record)",
                    use_container_width=True,
                    type="primary",
                ):
                    self._start_recording()

        with col2:
            # Settings button
            if st.button("⚙️", key=f"{self.component_id}_voice_settings", help="Voice settings"):
                self._toggle_voice_settings()

        # Render voice settings if expanded
        if voice_data.get("settings_expanded", False):
            self._render_voice_settings()

        # Render recording interface if active
        if voice_data.get("recording"):
            self._render_recording_interface()

    def _render_recording_interface(self) -> None:
        """Render the audio recording interface using streamlit-webrtc."""
        try:
            st.markdown("### 🎤 Recording...")

            # Create WebRTC streamer for audio recording
            webrtc_ctx = webrtc_streamer(
                key=f"{self.component_id}_audio_stream",
                mode=WebRtcMode.SENDONLY,
                rtc_configuration=self.voice_config["rtc_configuration"],
                media_stream_constraints={"video": False, "audio": self.voice_config["audio_constraints"]},
                audio_frame_callback=self._process_audio_frame,
                async_processing=True,
            )

            # Recording controls
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("⏹️ Stop", key=f"{self.component_id}_stop_rec"):
                    self._stop_recording()

            with col2:
                if st.button("⏸️ Pause", key=f"{self.component_id}_pause_rec"):
                    self._pause_recording()

            with col3:
                if st.button("❌ Cancel", key=f"{self.component_id}_cancel_rec"):
                    self._cancel_recording()

            # Display recording status
            if webrtc_ctx.state.playing:
                st.success("🔴 Recording active")
            else:
                st.warning("🟡 Starting recording...")

        except Exception as e:
            logger.error("Recording interface failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.HIGH)
            st.error("❌ Microphone access failed. Please check permissions.")

    def _start_recording(self) -> None:
        """Start voice recording."""
        try:
            state = self.get_state()
            voice_data = state["data"]["voice_data"]

            # Update recording state
            voice_data["recording"] = True
            voice_data["recording_start_time"] = time.time()
            voice_data["processing_status"] = "recording"
            voice_data["audio_data"] = []

            # Update state
            state["data"]["voice_data"] = voice_data
            self.set_state(state)

            st.success("🎤 Recording started! Speak your question about plants.")

        except Exception as e:
            logger.error("Failed to start recording: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)

    def _stop_recording(self) -> None:
        """Stop voice recording and process audio."""
        try:
            state = self.get_state()
            voice_data = state["data"]["voice_data"]

            if not voice_data.get("recording"):
                return

            # Calculate recording duration
            start_time = voice_data.get("recording_start_time", time.time())
            duration = time.time() - start_time

            # Check minimum duration
            if duration < self.voice_config["min_recording_duration"]:
                st.warning(f"⚠️ Recording too short. Minimum: {self.voice_config['min_recording_duration']}s")
                self._cancel_recording()
                return

            # Update state
            voice_data["recording"] = False
            voice_data["recording_duration"] = duration
            voice_data["processing_status"] = "processing"

            state["data"]["voice_data"] = voice_data
            self.set_state(state)

            # Process the recorded audio
            self._process_recorded_audio(voice_data)

            st.success(f"🎤 Recording stopped ({duration:.1f}s). Processing...")

        except Exception as e:
            logger.error("Failed to stop recording: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)

    def _pause_recording(self) -> None:
        """Pause voice recording."""
        # For simplicity, we'll treat pause as stop
        self._stop_recording()

    def _cancel_recording(self) -> None:
        """Cancel voice recording."""
        try:
            state = self.get_state()
            voice_data = state["data"]["voice_data"]

            # Reset recording state
            voice_data["recording"] = False
            voice_data["recording_start_time"] = None
            voice_data["recording_duration"] = 0
            voice_data["audio_data"] = None
            voice_data["processing_status"] = "idle"

            # Update state
            state["data"]["voice_data"] = voice_data
            self.set_state(state)

            st.info("🚫 Recording cancelled")

        except Exception as e:
            logger.error("Failed to cancel recording: %s", e)

    def _process_audio_frame(self, frame) -> None:
        """Process audio frame from recording stream."""
        try:
            state = self.get_state()
            voice_data = state["data"]["voice_data"]

            # Store audio frame data
            if "audio_data" not in voice_data:
                voice_data["audio_data"] = []

            # Convert frame to audio data (simplified)
            if hasattr(frame, "to_ndarray"):
                audio_array = frame.to_ndarray()
                voice_data["audio_data"].append(audio_array)

            # Update state
            state["data"]["voice_data"] = voice_data
            self.set_state(state)

        except Exception as e:
            logger.warning("Audio frame processing failed: %s", e)

    def _process_recorded_audio(self, voice_data: dict[str, Any]) -> None:
        """Process recorded audio and perform speech-to-text."""
        try:
            # Get audio data
            audio_data = voice_data.get("audio_data")
            if not audio_data:
                st.error("❌ No audio data recorded")
                return

            # Save audio to temporary file
            audio_file_path = self._save_audio_to_file(audio_data)

            if audio_file_path:
                # Perform speech-to-text
                transcription = self._transcribe_audio(audio_file_path)

                if transcription:
                    # Store transcription
                    state = self.get_state()
                    voice_data = state["data"]["voice_data"]
                    voice_data["transcription"] = transcription
                    voice_data["last_recording"] = {
                        "transcription": transcription,
                        "duration": voice_data.get("recording_duration", 0),
                        "timestamp": datetime.now().isoformat(),
                        "audio_file": audio_file_path,
                    }
                    voice_data["processing_status"] = "complete"

                    # Update state
                    state["data"]["voice_data"] = voice_data
                    self.set_state(state)

                    # Process the transcribed text
                    self._process_transcribed_text(transcription)

                else:
                    st.error("❌ Speech-to-text failed. Please try again.")
                    voice_data["processing_status"] = "error"

        except Exception as e:
            logger.error("Audio processing failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)

    def _save_audio_to_file(self, audio_data: list) -> str | None:
        """Save audio data to temporary file."""
        try:
            import numpy as np
            import soundfile as sf

            # Combine audio frames
            if not audio_data:
                return None

            # Convert to numpy array
            combined_audio = np.concatenate(audio_data, axis=0)

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                # Save as WAV file
                sf.write(tmp_file.name, combined_audio, samplerate=self.voice_config["audio_constraints"]["sampleRate"])

                return tmp_file.name

        except Exception as e:
            logger.error("Audio file save failed: %s", e)
            return None

    def _transcribe_audio(self, audio_file_path: str) -> str | None:
        """Transcribe audio file using AudioAdapter."""
        try:
            # Import mobile integration
            from .mobile_adapter_integration import mobile_integration

            # Perform transcription using mobile integration
            with st.spinner("🎧 Converting speech to text..."):
                transcription_result = mobile_integration.transcribe_audio(audio_file=audio_file_path, source="voice", component_id=self.component_id)

                # Check for success
                if transcription_result.get("success", False):
                    transcription = transcription_result.get("transcription", "")
                    if transcription and transcription.strip():
                        return transcription.strip()

                # Handle errors
                if "error" in transcription_result:
                    logger.error("Transcription error: %s", transcription_result["error"])

                return None

        except Exception as e:
            logger.error("Audio transcription failed: %s", e)
            return None

    def _process_transcribed_text(self, transcription: str) -> None:
        """Process transcribed text and trigger appropriate actions."""
        try:
            # Store transcription in global chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            # Add user message to chat
            user_message = {
                "role": "user",
                "content": transcription,
                "timestamp": datetime.now().isoformat(),
                "source": "voice",
                "component_id": self.component_id,
            }

            st.session_state.chat_history.append(user_message)

            # Trigger text processing if available
            self._trigger_text_processing(transcription)

            st.success(f'🎧 Speech recognized: "{transcription}"')

        except Exception as e:
            logger.error("Text processing failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.LOW)

    def _trigger_text_processing(self, text: str) -> None:
        """Trigger text processing using TextAdapter."""
        try:
            # Import mobile integration
            from .mobile_adapter_integration import mobile_integration

            # Get recent analysis context if available
            recent_analysis = mobile_integration.get_recent_analysis(limit=1)
            context = {"recent_analysis": recent_analysis[0]} if recent_analysis else None

            # Process text and generate response
            with st.spinner("🤖 Generating response..."):
                processing_result = mobile_integration.process_text_query(text=text, source="voice", component_id=self.component_id, context=context)

                # Check for errors
                if "error" in processing_result:
                    logger.error("Text processing error: %s", processing_result["error"])
                    st.warning("⚠️ Response generation had issues, but here's what I can tell you:")

                # Display response
                response = processing_result.get("response", "")
                if response:
                    st.success("🤖 Response generated!")

                    # Show response in an expandable section
                    with st.expander("🤖 AI Response", expanded=True):
                        st.write(response)
                else:
                    st.warning("⚠️ No response generated. Please try rephrasing your question.")

        except Exception as e:
            logger.error("Text processing failed: %s", e)
            # Don't show error to user for this optional feature

    def _render_recording_status(self, voice_data: dict[str, Any]) -> None:
        """Render recording status indicator."""
        start_time = voice_data.get("recording_start_time", time.time())
        current_duration = time.time() - start_time
        max_duration = self.voice_config["max_recording_duration"]

        # Progress bar for recording duration
        progress = min(current_duration / max_duration, 1.0)

        st.markdown("### 🔴 Recording in Progress")
        st.progress(progress)

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Duration:** {current_duration:.1f}s")
        with col2:
            st.write(f"**Max:** {max_duration}s")

        # Auto-stop if max duration reached
        if current_duration >= max_duration:
            st.warning("⏰ Maximum recording duration reached. Stopping...")
            self._stop_recording()

    def _render_processing_status(self) -> None:
        """Render processing status indicator."""
        st.markdown("### 🎧 Processing Audio")

        with st.spinner("Converting speech to text..."):
            time.sleep(0.1)  # Small delay for UI responsiveness

    def _render_transcription(self, transcription: str) -> None:
        """Render transcription result."""
        st.markdown("### 🎧 Speech Recognition Result")

        # Display transcription in a text area for editing
        edited_transcription = st.text_area(
            "Transcribed Text",
            value=transcription,
            height=100,
            key=f"{self.component_id}_transcription_edit",
            help="Edit the transcription if needed",
        )

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("✅ Use Text", key=f"{self.component_id}_use_transcription"):
                if edited_transcription.strip():
                    self._process_transcribed_text(edited_transcription.strip())

        with col2:
            if st.button("🔄 Re-record", key=f"{self.component_id}_rerecord"):
                self._clear_transcription()

        with col3:
            if st.button("❌ Clear", key=f"{self.component_id}_clear_transcription"):
                self._clear_transcription()

    def _render_last_recording(self, recording_data: dict[str, Any]) -> None:
        """Render information about the last recording."""
        st.markdown("### 🎤 Last Recording")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Duration:** {recording_data.get('duration', 0):.1f}s")
            st.write(f"**Recorded:** {recording_data.get('timestamp', '')[:19]}")

        with col2:
            # Action buttons
            if st.button("🔄 Record Again", key=f"{self.component_id}_record_again"):
                self._clear_voice_state()

            if st.button("❌ Clear", key=f"{self.component_id}_clear_last"):
                self._clear_last_recording()

    def _render_voice_settings(self) -> None:
        """Render voice settings panel."""
        with st.expander("🎤 Voice Settings", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                # Recording duration settings
                max_duration = st.slider(
                    "Max Recording Duration (seconds)",
                    min_value=10,
                    max_value=120,
                    value=self.voice_config["max_recording_duration"],
                    key=f"{self.component_id}_max_duration",
                )

                self.voice_config["max_recording_duration"] = max_duration

            with col2:
                # Audio quality settings
                sample_rate = st.selectbox(
                    "Sample Rate",
                    options=[8000, 16000, 22050, 44100],
                    index=1,  # 16000 Hz default
                    key=f"{self.component_id}_sample_rate",
                )

                self.voice_config["audio_constraints"]["sampleRate"] = sample_rate

    def _toggle_voice_settings(self) -> None:
        """Toggle voice settings panel."""
        state = self.get_state()
        voice_data = state["data"]["voice_data"]
        voice_data["settings_expanded"] = not voice_data.get("settings_expanded", False)
        state["data"]["voice_data"] = voice_data
        self.set_state(state)

    def _clear_transcription(self) -> None:
        """Clear transcription result."""
        state = self.get_state()
        voice_data = state["data"]["voice_data"]
        voice_data["transcription"] = None
        voice_data["processing_status"] = "idle"
        state["data"]["voice_data"] = voice_data
        self.set_state(state)

        st.success("🧹 Transcription cleared")

    def _clear_last_recording(self) -> None:
        """Clear last recording data."""
        state = self.get_state()
        voice_data = state["data"]["voice_data"]
        voice_data["last_recording"] = None
        state["data"]["voice_data"] = voice_data
        self.set_state(state)

        st.success("🗑️ Last recording cleared")

    def _clear_voice_state(self) -> None:
        """Clear all voice state."""
        self._initialize_voice_state()
        st.success("🧹 Voice state cleared")

    def get_last_transcription(self) -> str | None:
        """Get the last transcription result."""
        state = self.get_state()
        voice_data = state["data"].get("voice_data", {})
        return voice_data.get("transcription")

    def get_recording_status(self) -> dict[str, Any]:
        """Get current recording status."""
        state = self.get_state()
        voice_data = state["data"].get("voice_data", {})

        return {
            "recording": voice_data.get("recording", False),
            "processing": voice_data.get("processing_status") == "processing",
            "duration": voice_data.get("recording_duration", 0),
            "has_transcription": bool(voice_data.get("transcription")),
        }
