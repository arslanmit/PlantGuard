"""
Mobile Audio Processor for PlantGuard UI.

This module provides mobile-optimized audio processing capabilities
including speech-to-text, audio enhancement, and plant sound analysis.
"""

import logging
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from .mobile_adapter_integration import mobile_integration
from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileAudioProcessor(MobileBaseComponent):
    """Mobile-optimized audio processor with speech-to-text and analysis."""

    def __init__(self, component_id: str, title: str = "Audio Processor", **kwargs):
        """
        Initialize mobile audio processor.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Audio processing configuration
        self.audio_config = {
            "supported_formats": [".wav", ".mp3", ".m4a", ".flac", ".ogg"],
            "max_file_size": 50 * 1024 * 1024,  # 50MB max
            "max_duration": 300,  # 5 minutes max
            "min_duration": 0.5,  # 0.5 seconds min
            "sample_rate": 16000,  # Optimal for Whisper
            "quality_threshold": 0.3,  # Minimum audio quality score
        }

        # Initialize audio processing state
        self._initialize_audio_state()

        logger.debug("MobileAudioProcessor initialized: %s", component_id)

    def _initialize_audio_state(self) -> None:
        """Initialize audio processing state."""
        audio_state = {
            "current_audio": None,
            "processing_status": "idle",  # idle, processing, complete, error
            "transcription_history": [],
            "audio_quality_score": 0.0,
            "last_processing_time": 0.0,
            "supported_features": {
                "speech_to_text": True,
                "audio_enhancement": True,
                "quality_analysis": True,
            },
        }

        current_state = self.get_state()
        if "audio_processing" not in current_state["data"]:
            current_state["data"]["audio_processing"] = audio_state
            self.set_state(current_state)

    def render(self) -> None:
        """Render the mobile audio processor interface."""
        try:
            # Get current state
            state = self.get_state()
            audio_data = state["data"].get("audio_processing", {})

            # Render audio processor container
            st.markdown(
                f"""
                <div class="mobile-audio-processor mobile-component" 
                     data-component-id="{self.component_id}"
                     data-testid="audio-processor-{self.component_id}">
                """,
                unsafe_allow_html=True,
            )

            # Audio upload interface
            self._render_audio_upload_interface()

            # Processing status
            if audio_data.get("processing_status") == "processing":
                self._render_processing_status()

            # Transcription history
            if audio_data.get("transcription_history"):
                self._render_transcription_history(audio_data["transcription_history"])

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Audio processor rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)

    def _render_audio_upload_interface(self) -> None:
        """Render audio file upload interface."""
        st.markdown("### 🎵 Audio Upload")

        # File uploader
        uploaded_audio = st.file_uploader(
            "Upload Audio File",
            type=["wav", "mp3", "m4a", "flac", "ogg"],
            key=f"{self.component_id}_audio_uploader",
            help="Upload audio file for speech-to-text conversion",
        )

        if uploaded_audio is not None:
            self._handle_audio_upload(uploaded_audio)

        # Audio processing options
        with st.expander("🔧 Processing Options", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                enhance_audio = st.checkbox(
                    "Enhance Audio Quality", value=True, key=f"{self.component_id}_enhance", help="Apply noise reduction and audio enhancement"
                )

            with col2:
                analyze_quality = st.checkbox(
                    "Analyze Audio Quality", value=True, key=f"{self.component_id}_quality", help="Analyze audio quality and provide feedback"
                )

            # Store options in state
            state = self.get_state()
            audio_data = state["data"]["audio_processing"]
            audio_data["enhance_audio"] = enhance_audio
            audio_data["analyze_quality"] = analyze_quality
            state["data"]["audio_processing"] = audio_data
            self.set_state(state)

    def _handle_audio_upload(self, uploaded_audio) -> None:
        """Handle uploaded audio file processing."""
        try:
            # Validate audio file
            validation_result = self._validate_audio_file(uploaded_audio)

            if not validation_result["is_valid"]:
                for error in validation_result["errors"]:
                    st.error(f"❌ {error}")
                return

            # Show warnings if any
            for warning in validation_result.get("warnings", []):
                st.warning(f"⚠️ {warning}")

            # Update processing status
            self._update_processing_status("processing")

            # Process the audio file
            self._process_audio_file(uploaded_audio)

        except Exception as e:
            logger.error("Audio upload handling failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)
            self._update_processing_status("error")

    def _validate_audio_file(self, uploaded_audio) -> dict[str, Any]:
        """Validate uploaded audio file."""
        validation_result = {"is_valid": True, "errors": [], "warnings": []}

        try:
            # Check file size
            if uploaded_audio.size > self.audio_config["max_file_size"]:
                validation_result["is_valid"] = False
                max_mb = self.audio_config["max_file_size"] // (1024 * 1024)
                validation_result["errors"].append(f"File too large. Maximum size: {max_mb}MB")

            # Check file extension
            file_extension = Path(uploaded_audio.name).suffix.lower()
            if file_extension not in self.audio_config["supported_formats"]:
                validation_result["is_valid"] = False
                supported = ", ".join(self.audio_config["supported_formats"])
                validation_result["errors"].append(f"Unsupported format. Supported: {supported}")

            # Try to get audio info
            try:
                import soundfile as sf

                # Create temporary file to check audio properties
                with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as tmp_file:
                    tmp_file.write(uploaded_audio.read())
                    tmp_file.flush()

                    # Reset file pointer
                    uploaded_audio.seek(0)

                    # Get audio info
                    info = sf.info(tmp_file.name)
                    duration = info.duration
                    sample_rate = info.samplerate

                    # Check duration
                    if duration > self.audio_config["max_duration"]:
                        validation_result["warnings"].append(
                            f"Audio is {duration:.1f}s long. Will be truncated to {self.audio_config['max_duration']}s"
                        )
                    elif duration < self.audio_config["min_duration"]:
                        validation_result["is_valid"] = False
                        validation_result["errors"].append(f"Audio too short ({duration:.1f}s). Minimum: {self.audio_config['min_duration']}s")

                    # Check sample rate
                    if sample_rate < 8000:
                        validation_result["warnings"].append(f"Low sample rate ({sample_rate}Hz). Quality may be poor.")

                    # Clean up temp file
                    Path(tmp_file.name).unlink(missing_ok=True)

            except Exception as audio_error:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Invalid audio file: {audio_error}")

        except Exception as e:
            logger.error("Audio validation failed: %s", e)
            validation_result["is_valid"] = False
            validation_result["errors"].append("Audio validation failed")

        return validation_result

    def _process_audio_file(self, uploaded_audio) -> None:
        """Process uploaded audio file."""
        try:
            start_time = time.time()

            # Save audio to temporary file
            file_extension = Path(uploaded_audio.name).suffix.lower()
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as tmp_file:
                tmp_file.write(uploaded_audio.read())
                tmp_file.flush()
                audio_file_path = tmp_file.name

            # Get processing options
            state = self.get_state()
            audio_data = state["data"]["audio_processing"]
            enhance_audio = audio_data.get("enhance_audio", True)
            analyze_quality = audio_data.get("analyze_quality", True)

            # Analyze audio quality if requested
            quality_score = 1.0
            if analyze_quality:
                quality_score = self._analyze_audio_quality(audio_file_path)

                if quality_score < self.audio_config["quality_threshold"]:
                    st.warning(f"⚠️ Audio quality is low (score: {quality_score:.2f}). Results may be poor.")

            # Enhance audio if requested and quality is low
            processed_audio_path = audio_file_path
            if enhance_audio and quality_score < 0.7:
                processed_audio_path = self._enhance_audio(audio_file_path)

            # Perform transcription using mobile integration
            with st.spinner("🎧 Converting speech to text..."):
                transcription_result = mobile_integration.transcribe_audio(
                    audio_file=processed_audio_path, source="upload", component_id=self.component_id
                )

            # Process results
            processing_time = time.time() - start_time

            if transcription_result.get("success", False):
                transcription = transcription_result.get("transcription", "")

                # Store in transcription history
                history_entry = {
                    "filename": uploaded_audio.name,
                    "transcription": transcription,
                    "timestamp": datetime.now().isoformat(),
                    "quality_score": quality_score,
                    "processing_time": processing_time,
                    "enhanced": enhance_audio and quality_score < 0.7,
                }

                audio_data["transcription_history"].append(history_entry)
                audio_data["last_processing_time"] = processing_time
                state["data"]["audio_processing"] = audio_data
                self.set_state(state)

                # Display success
                st.success(f"✅ Transcription completed in {processing_time:.1f}s")
                st.info(f"📝 **Transcribed Text:** {transcription}")

                # Process the transcribed text for plant-related queries
                self._process_transcribed_text(transcription)

            else:
                error_msg = transcription_result.get("error", "Unknown error")
                st.error(f"❌ Transcription failed: {error_msg}")

            # Clean up temporary files
            Path(audio_file_path).unlink(missing_ok=True)
            if processed_audio_path != audio_file_path:
                Path(processed_audio_path).unlink(missing_ok=True)

            self._update_processing_status("complete")

        except Exception as e:
            logger.error("Audio processing failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)
            self._update_processing_status("error")

    def _analyze_audio_quality(self, audio_file_path: str) -> float:
        """Analyze audio quality and return score (0.0 to 1.0)."""
        try:
            import librosa
            import numpy as np

            # Load audio
            audio, sr = librosa.load(audio_file_path, sr=None)

            # Calculate quality metrics

            # 1. Signal-to-noise ratio estimate
            # Use spectral centroid and rolloff as quality indicators
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]

            # 2. Zero crossing rate (indicates noise level)
            zcr = librosa.feature.zero_crossing_rate(audio)[0]

            # 3. RMS energy (indicates signal strength)
            rms = librosa.feature.rms(y=audio)[0]

            # Combine metrics into quality score
            # Higher spectral centroid and rolloff = better quality
            # Lower zero crossing rate = less noise
            # Higher RMS = stronger signal

            centroid_score = np.clip(np.mean(spectral_centroids) / 4000, 0, 1)
            rolloff_score = np.clip(np.mean(spectral_rolloff) / 8000, 0, 1)
            zcr_score = np.clip(1 - np.mean(zcr), 0, 1)
            rms_score = np.clip(np.mean(rms) * 10, 0, 1)

            # Weighted average
            quality_score = centroid_score * 0.3 + rolloff_score * 0.3 + zcr_score * 0.2 + rms_score * 0.2

            return float(quality_score)

        except Exception as e:
            logger.warning("Audio quality analysis failed: %s", e)
            return 0.5  # Default moderate quality

    def _enhance_audio(self, audio_file_path: str) -> str:
        """Enhance audio quality and return path to enhanced file."""
        try:
            import librosa
            import numpy as np
            import soundfile as sf

            # Load audio
            audio, sr = librosa.load(audio_file_path, sr=16000)  # Resample to 16kHz

            # Apply enhancements

            # 1. Normalize audio
            audio = librosa.util.normalize(audio)

            # 2. Apply simple noise reduction using spectral gating
            # This is a basic implementation - more sophisticated methods exist
            stft = librosa.stft(audio)
            magnitude = np.abs(stft)
            phase = np.angle(stft)

            # Estimate noise floor from first 0.5 seconds
            noise_frames = int(0.5 * sr / 512)  # 512 is default hop_length
            noise_magnitude = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)

            # Apply spectral gating
            gate_threshold = noise_magnitude * 2  # 6dB above noise floor
            mask = magnitude > gate_threshold
            enhanced_magnitude = magnitude * mask

            # Reconstruct audio
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft)

            # Save enhanced audio
            enhanced_path = audio_file_path.replace(".", "_enhanced.")
            sf.write(enhanced_path, enhanced_audio, sr)

            return enhanced_path

        except Exception as e:
            logger.warning("Audio enhancement failed: %s", e)
            return audio_file_path  # Return original if enhancement fails

    def _process_transcribed_text(self, transcription: str) -> None:
        """Process transcribed text for plant-related queries."""
        try:
            # Check if the transcription contains plant-related keywords
            plant_keywords = [
                "plant",
                "leaf",
                "leaves",
                "disease",
                "pest",
                "bug",
                "insect",
                "fungus",
                "mold",
                "spot",
                "yellow",
                "brown",
                "wilting",
                "dying",
                "garden",
                "flower",
                "tree",
                "shrub",
                "crop",
                "vegetable",
                "fruit",
            ]

            transcription_lower = transcription.lower()
            is_plant_related = any(keyword in transcription_lower for keyword in plant_keywords)

            if is_plant_related:
                # Process as plant-related query
                with st.spinner("🤖 Analyzing your plant question..."):
                    processing_result = mobile_integration.process_text_query(
                        text=transcription, source="audio_upload", component_id=self.component_id
                    )

                    response = processing_result.get("response", "")
                    if response:
                        with st.expander("🌿 Plant Care Response", expanded=True):
                            st.write(response)
            else:
                # General transcription - just show the text
                st.info("💬 Transcription completed. If you have plant-related questions, please be more specific.")

        except Exception as e:
            logger.error("Transcribed text processing failed: %s", e)

    def _render_processing_status(self) -> None:
        """Render audio processing status."""
        st.markdown("### 🎵 Processing Audio")

        progress_bar = st.progress(0)
        status_text = st.empty()

        # Simulate processing progress
        for i in range(100):
            progress_bar.progress(i + 1)
            if i < 30:
                status_text.text("Loading audio file...")
            elif i < 60:
                status_text.text("Analyzing audio quality...")
            elif i < 90:
                status_text.text("Converting speech to text...")
            else:
                status_text.text("Finalizing results...")

            time.sleep(0.01)  # Small delay for visual effect

    def _render_transcription_history(self, history: list[dict[str, Any]]) -> None:
        """Render transcription history."""
        st.markdown("### 📝 Transcription History")

        # Show recent transcriptions
        for i, entry in enumerate(reversed(history[-5:])):  # Show last 5
            with st.expander(f"🎵 {entry['filename']} - {entry['timestamp'][:19]}", expanded=(i == 0)):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Transcription:** {entry['transcription']}")

                with col2:
                    st.write(f"**Quality:** {entry['quality_score']:.2f}")
                    st.write(f"**Time:** {entry['processing_time']:.1f}s")
                    if entry.get("enhanced", False):
                        st.write("**Enhanced:** ✅")

                # Action buttons
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("🔄 Reprocess", key=f"{self.component_id}_reprocess_{i}"):
                        st.info("Please upload the audio file again to reprocess.")

                with col2:
                    if st.button("💬 Ask Question", key=f"{self.component_id}_ask_{i}"):
                        self._process_transcribed_text(entry["transcription"])

                with col3:
                    if st.button("❌ Remove", key=f"{self.component_id}_remove_{i}"):
                        self._remove_history_entry(entry["timestamp"])

    def _update_processing_status(self, status: str) -> None:
        """Update processing status."""
        state = self.get_state()
        audio_data = state["data"]["audio_processing"]
        audio_data["processing_status"] = status
        state["data"]["audio_processing"] = audio_data
        self.set_state(state)

    def _remove_history_entry(self, timestamp: str) -> None:
        """Remove entry from transcription history."""
        state = self.get_state()
        audio_data = state["data"]["audio_processing"]

        # Filter out the entry with matching timestamp
        audio_data["transcription_history"] = [entry for entry in audio_data["transcription_history"] if entry["timestamp"] != timestamp]

        state["data"]["audio_processing"] = audio_data
        self.set_state(state)

        st.success("🗑️ History entry removed")

    def get_transcription_history(self) -> list[dict[str, Any]]:
        """Get transcription history."""
        state = self.get_state()
        audio_data = state["data"].get("audio_processing", {})
        return audio_data.get("transcription_history", [])

    def clear_transcription_history(self) -> None:
        """Clear all transcription history."""
        state = self.get_state()
        audio_data = state["data"]["audio_processing"]
        audio_data["transcription_history"] = []
        state["data"]["audio_processing"] = audio_data
        self.set_state(state)

        st.success("🧹 Transcription history cleared")
