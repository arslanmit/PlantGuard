from typing import Any, Dict, List, Optional, Tuple, Union, Generator
"""Voice and Audio Processing Interface for PlantGuard.

This module provides comprehensive voice and audio processing capabilities
including microphone capture, file upload, transcription, and audio analysis
for the PlantGuard multimodal plant disease detection system.
"""


import logging
import tempfile
from pathlib import Path

import av
import librosa
import numpy as np
import soundfile as sf
import streamlit as st

from utils.error_recovery import ImportErrorRecovery

# Configure logger for this module
logger = logging.getLogger(__name__)

# Safe import of streamlit_webrtc with proper fallbacks
RTCConfiguration = ImportErrorRecovery.safe_import_from(
    "streamlit_webrtc", "RTCConfiguration", fallback=type("RTCConfigurationStub", (dict,), {}), logger_name="voice_interface"
)

WebRtcMode = ImportErrorRecovery.safe_import_from(
    "streamlit_webrtc", "WebRtcMode", fallback=type("WebRtcModeStub", (), {"SENDONLY": "sendonly"}), logger_name="voice_interface"
)

webrtc_streamer = ImportErrorRecovery.safe_import_from(
    "streamlit_webrtc", "webrtc_streamer", fallback=lambda **kwargs: type("_DummyState", (), {"playing": False})(), logger_name="voice_interface"
)


logger = logging.getLogger(__name__)


class VoiceInterface:
    """Voice and audio processing interface with real-time capture and file upload."""

    def __init__(self) -> None:
        """Initialize voice interface."""
        self.sample_rate = 16000  # 16 kHz for Whisper
        self.max_duration = 60  # Maximum 60 seconds
        self.min_duration = 1  # Minimum 1 second
        self.supported_formats = ["wav", "mp3", "m4a", "ogg"]

        # Initialize session state
        if "audio_recording" not in st.session_state:
            st.session_state.audio_recording = False
        if "recorded_audio" not in st.session_state:
            st.session_state.recorded_audio = None
        if "audio_transcription" not in st.session_state:
            st.session_state.audio_transcription = ""

    def validate_audio_file(self, audio_file) -> tuple[bool, str]:
        """Validate uploaded audio file.

        Args:
            audio_file: Streamlit uploaded file object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not audio_file:
            return False, "No audio file provided"

        # Check file size (max 50MB)
        if audio_file.size > 50 * 1024 * 1024:
            return False, "Audio file too large (max 50MB)"

        # Check file extension
        file_extension = Path(audio_file.name).suffix.lower().lstrip(".")
        if file_extension not in self.supported_formats:
            return False, f"Unsupported format. Use: {', '.join(self.supported_formats)}"

        return True, ""

    def validate_audio_duration(self, audio_data: np.ndarray, sample_rate: int | float) -> tuple[bool, str]:
        """Validate audio duration.

        Args:
            audio_data: Audio data array
            sample_rate: Sample rate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Allow float sample rates recorded from external sources
        duration = len(audio_data) / float(sample_rate)

        if duration < self.min_duration:
            return False, f"Audio too short (min {self.min_duration}s)"

        if duration > self.max_duration:
            return False, f"Audio too long (max {self.max_duration}s)"

        return True, ""

    def load_audio_file(self, audio_file) -> tuple[np.ndarray | None, int]:
        """Load and process audio file.

        Args:
            audio_file: Streamlit uploaded file object

        Returns:
            Tuple of (audio_data, sample_rate) or (None, 0) if failed
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{Path(audio_file.name).suffix}") as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name

            try:
                # Load audio with librosa
                audio_data, sr = librosa.load(tmp_file_path, sr=int(self.sample_rate), mono=True)
                sr_int = int(sr)  # Ensure sr is int for return type compatibility

                # Validate duration
                is_valid, error_msg = self.validate_audio_duration(audio_data, sr_int)
                if not is_valid:
                    st.toast(error_msg, icon="[WARNING]")
                    return None, 0

                logger.info(f"Loaded audio file: {audio_file.name}, duration: {len(audio_data) / sr_int:.2f}s")
                return audio_data, sr_int

            finally:
                # Clean up temporary file
                Path(tmp_file_path).unlink(missing_ok=True)

        except Exception as e:
            logger.warning(f"Failed to load audio file: {e}")
            st.toast("Failed to load audio file", icon="[WARNING]")
            return None, 0

    def process_audio_frame(self, frame: av.AudioFrame) -> np.ndarray:
        """Process audio frame from WebRTC stream.

        Args:
            frame: Audio frame from WebRTC

        Returns:
            Processed audio data
        """
        try:
            # Convert frame to numpy array
            audio_data = frame.to_ndarray()

            # Handle multi-channel audio (convert to mono)
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Normalize audio
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            return audio_data.astype(np.float32)

        except Exception as e:
            logger.warning(f"Failed to process audio frame: {e}")
            return np.array([])

    def transcribe_audio_local(self, audio_data: np.ndarray) -> str:
        """Transcribe audio using local Whisper model.

        Args:
            audio_data: Audio data to transcribe

        Returns:
            Transcribed text
        """
        try:
            # Import whisper (lazy import to avoid startup delay)
            import whisper

            # Load Whisper model (cached)
            @st.cache_resource
            def load_whisper_model() -> Any:
                return whisper.load_model("tiny")

            model = load_whisper_model()

            # Create temporary audio file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                sf.write(tmp_file.name, audio_data, self.sample_rate)
                tmp_file_path = tmp_file.name

            try:
                # Transcribe with Whisper
                result = model.transcribe(tmp_file_path)
                transcription = result["text"].strip()

                logger.info(f"Transcribed audio: {transcription[:50]}...")
                return transcription

            finally:
                # Clean up temporary file
                Path(tmp_file_path).unlink(missing_ok=True)

        except Exception as e:
            logger.warning(f"Transcription failed: {e}")
            return "Transcription failed. Please try again."

    def render_audio_waveform(self, audio_data: np.ndarray, sample_rate: int) -> None:
        """Render audio waveform visualization.

        Args:
            audio_data: Audio data to visualize
            sample_rate: Sample rate
        """
        try:
            import plotly.graph_objects as go

            # Create time axis
            time_axis = np.linspace(0, len(audio_data) / sample_rate, len(audio_data))

            # Create waveform plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_axis, y=audio_data, mode="lines", name="Waveform", line={"color": "#1f77b4", "width": 1}))

            fig.update_layout(
                title="[SOUND] Audio Waveform",
                xaxis_title="Time (seconds)",
                yaxis_title="Amplitude",
                height=200,
                margin={"l": 0, "r": 0, "t": 30, "b": 0},
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            logger.warning(f"Failed to render waveform: {e}")
            st.info("Audio loaded successfully (waveform visualization unavailable)")

    def render_microphone_interface(self) -> np.ndarray | None:
        """Render microphone capture interface.

        Returns:
            Recorded audio data or None
        """
        st.subheader("[MICROPHONE]️ Microphone Recording")

        # WebRTC configuration
        rtc_configuration = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

        # Audio capture state
        audio_frames: list[np.ndarray] = []

        def audio_frame_callback(frame: av.AudioFrame) -> Any:
            """Callback for processing audio frames."""
            processed_audio = self.process_audio_frame(frame)
            if len(processed_audio) > 0:
                audio_frames.append(processed_audio)
            return frame

        # WebRTC streamer
        webrtc_ctx = webrtc_streamer(
            key="voice_capture",
            mode=WebRtcMode.SENDONLY,
            audio_receiver_size=1024,
            rtc_configuration=rtc_configuration,
            media_stream_constraints={"video": False, "audio": {"sampleRate": int(self.sample_rate)}},
            audio_frame_callback=audio_frame_callback,
        )

        # Recording status
        if getattr(webrtc_ctx, "state", None) is not None and getattr(webrtc_ctx.state, "playing", False):
            st.success("[RED] Recording... Click 'Stop' when finished")
            st.session_state.audio_recording = True
        elif st.session_state.audio_recording:
            st.session_state.audio_recording = False

            # Process recorded audio
            if audio_frames:
                try:
                    # Concatenate audio frames
                    full_audio = np.concatenate(audio_frames)

                    # Validate duration
                    is_valid, error_msg = self.validate_audio_duration(full_audio, self.sample_rate)
                    if is_valid:
                        st.success(f"[DONE] Recording complete! Duration: {len(full_audio) / self.sample_rate:.1f}s")
                        st.session_state.recorded_audio = full_audio
                        return full_audio
                    else:
                        st.error(error_msg)

                except Exception as e:
                    logger.warning(f"Failed to process recorded audio: {e}")
                    st.error("Failed to process recording")

            audio_frames.clear()

        return st.session_state.recorded_audio

    def render_file_upload_interface(self) -> np.ndarray | None:
        """Render audio file upload interface.

        Returns:
            Uploaded audio data or None
        """
        st.subheader("[FOLDER] Audio File Upload")

        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=self.supported_formats,
            help=f"Supported formats: {', '.join(self.supported_formats)}. Max size: 50MB, Duration: 1-60 seconds",
        )

        if uploaded_file:
            # Validate file
            is_valid, error_msg = self.validate_audio_file(uploaded_file)
            if not is_valid:
                st.error(error_msg)
                return None

            # Load and process audio
            with st.status("[SOUND] Processing audio file...", expanded=True) as status:
                st.write("Loading audio file...")
                audio_data, sample_rate = self.load_audio_file(uploaded_file)

                if audio_data is not None:
                    st.write("[DONE] Audio file loaded successfully")
                    status.update(label="[DONE] Audio processing complete!", state="complete")

                    # Show audio info
                    duration = len(audio_data) / sample_rate
                    st.info(f"[SUMMARY] **File:** {uploaded_file.name} | **Duration:** {duration:.1f}s | **Sample Rate:** {sample_rate} Hz")

                    # Render waveform
                    self.render_audio_waveform(audio_data, sample_rate)

                    return audio_data
                else:
                    status.update(label="[TODO] Audio processing failed", state="error")

        return None

    def render_transcription_interface(self, audio_data: np.ndarray) -> str:
        """Render audio transcription interface.

        Args:
            audio_data: Audio data to transcribe

        Returns:
            Transcribed text
        """
        if audio_data is None:
            return ""

        st.subheader("[WRITE] Audio Transcription")

        # Transcription button
        if st.button("[PROGRESS] Transcribe Audio", type="primary"):
            with st.status("[VOICE] Transcribing audio...", expanded=True) as status:
                st.write("Using local Whisper model...")
                transcription = self.transcribe_audio_local(audio_data)

                if transcription and transcription != "Transcription failed. Please try again.":
                    st.session_state.audio_transcription = transcription
                    status.update(label="[DONE] Transcription complete!", state="complete")
                else:
                    status.update(label="[TODO] Transcription failed", state="error")

        # Display transcription
        if st.session_state.audio_transcription:
            st.success("[PROGRESS] Transcription Result:")
            st.text_area(
                "Transcribed Text",
                value=st.session_state.audio_transcription,
                height=100,
                help="Edit the transcription if needed",
            )

            return st.session_state.audio_transcription

        return ""

    def render_processing_status(self, audio_data: np.ndarray) -> None:
        """Render audio processing status and controls.

        Args:
            audio_data: Current audio data
        """
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if audio_data is not None:
                duration = len(audio_data) / self.sample_rate
                st.metric("Duration", f"{duration:.1f}s")

        with col2:
            if st.session_state.audio_transcription:
                word_count = len(st.session_state.audio_transcription.split())
                st.metric("Words", word_count)

        with col3:
            if st.button("[CLEAN] Clear Audio"):
                st.session_state.recorded_audio = None
                st.session_state.audio_transcription = ""
                st.rerun()

    def render_complete_interface(self) -> tuple[np.ndarray | None, str]:
        """Render the complete voice interface.

        Returns:
            Tuple of (audio_data, transcription)
        """
        st.header("[MICROPHONE]️ Voice & Audio Processing")

        # Interface tabs
        tab1, tab2 = st.tabs(["[MICROPHONE]️ Microphone", "[FOLDER] Upload File"])

        audio_data = None

        with tab1:
            audio_data = self.render_microphone_interface()

        with tab2:
            uploaded_audio = self.render_file_upload_interface()
            if uploaded_audio is not None:
                audio_data = uploaded_audio

        # Transcription interface
        transcription = ""
        if audio_data is not None:
            st.markdown("---")
            transcription = self.render_transcription_interface(audio_data)

            # Processing status
            st.markdown("---")
            self.render_processing_status(audio_data)

        return audio_data, transcription


def create_voice_interface() -> VoiceInterface:
    """Create and return a VoiceInterface instance.

    Returns:
        VoiceInterface instance
    """
    return VoiceInterface()


# Example usage and testing
if __name__ == "__main__":
    # Test the voice interface
    st.title("[MICROPHONE]️ PlantGuard Voice Interface Test")

    # Create voice interface
    voice = create_voice_interface()

    # Render interface
    audio_data, transcription = voice.render_complete_interface()

    # Display results
    if audio_data is not None:
        st.success(f"Audio captured: {len(audio_data)} samples")

    if transcription:
        st.success(f"Transcription: {transcription}")
        st.success(f"Transcription: {transcription}")
