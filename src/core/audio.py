"""Audio processing module for PlantGuard.

This module contains the AudioAdapter class for speech-to-text processing using Whisper.
"""

import contextlib
import logging
import os
import signal
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import librosa
import soundfile as sf
import streamlit as st

# Disable Streamlit caching during pytest to avoid large in-memory caches
if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:

    def _noop_cache(*args, **kwargs) -> Callable:
        def _wrap(f: Callable) -> Callable:
            return f

        return _wrap

    # Use contextlib.suppress to avoid hiding unexpected errors with a bare except
    with contextlib.suppress(Exception):
        st.cache_resource = _noop_cache  # type: ignore[assignment]
        st.cache_data = _noop_cache  # type: ignore[assignment]
from transformers import Pipeline, pipeline

logger = logging.getLogger("plantguard.core.audio")


@st.cache_resource(show_spinner=False)
def load_whisper_pipeline(model_name: str = "openai/whisper-tiny") -> Pipeline:
    """Load and cache Whisper pipeline for speech-to-text.

    Args:
        model_name: Whisper model name to use

    Returns:
        Loaded Whisper pipeline
    """
    logger.info(f"Loading Whisper pipeline: {model_name}")

    try:
        whisper_pipeline = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device=-1,  # Force CPU for compatibility and consistency
        )

        logger.info("Whisper pipeline loaded successfully")
        return whisper_pipeline

    except Exception as e:
        logger.error(f"Failed to load Whisper pipeline: {e}")
        raise RuntimeError(f"Failed to initialize Whisper model: {e}") from e


@st.cache_data(show_spinner=False, ttl=300)
def get_audio_info(file_path: str) -> tuple[float, int, bool]:
    """Get and cache audio file information.

    Args:
        file_path: Path to audio file

    Returns:
        Tuple of (duration, sample_rate, is_valid)
    """
    try:
        # Quick info check without loading full audio
        import soundfile as sf

        info = sf.info(file_path)
        duration = info.duration
        sample_rate = info.samplerate
        is_valid = duration > 0 and sample_rate > 0

        logger.debug(f"Audio info for {file_path}: {duration}s, {sample_rate}Hz")
        return duration, sample_rate, is_valid

    except Exception as e:
        logger.warning(f"Failed to get audio info for {file_path}: {e}")
        return 0.0, 0, False


class AudioAdapter:
    """Audio adapter for speech-to-text processing using Whisper.

    This class handles audio file processing and transcription
    using OpenAI's Whisper model for local, offline speech-to-text conversion.
    """

    def __init__(self, model_name: str = "openai/whisper-tiny") -> None:
        """Initialize AudioAdapter with Whisper-tiny model.

        Args:
            model_name: Whisper model name to use (default: openai/whisper-tiny)
        """
        self.model_name = model_name
        self.pipeline: Pipeline | None = None  # Will be loaded lazily
        self.temp_files: list[str] = []  # Track temporary files for cleanup
        self.max_duration = 60  # Maximum audio duration in seconds
        self.min_duration = 1  # Minimum audio duration in seconds
        self.supported_formats = [".wav", ".mp3", ".m4a", ".flac"]
        self.processing_timeout = 30  # Maximum processing time in seconds

        logger.info("AudioAdapter initialized with model: %s", self.model_name)

    def _load_pipeline(self) -> None:
        """Load Whisper pipeline using cached function."""
        if self.pipeline is None:
            try:
                # Use cached pipeline loading for better performance
                self.pipeline = load_whisper_pipeline(self.model_name)
                logger.info("Whisper pipeline loaded successfully")
            except Exception as e:
                logger.error("Failed to load Whisper pipeline: %s", e)
                raise RuntimeError(f"Failed to initialize Whisper model: {e}") from e

    def _timeout_handler(self, signum: int, frame: Any) -> None:
        """Handle processing timeout."""
        raise TimeoutError("Audio processing timeout exceeded")

    def _is_audio_corrupted(self, audio_path: str) -> bool:
        """Check if audio file is corrupted or empty using cached info.

        Args:
            audio_path: Path to audio file

        Returns:
            True if file appears corrupted, False otherwise
        """
        try:
            # Use cached audio info function
            duration, sample_rate, is_valid = get_audio_info(audio_path)

            if not is_valid:
                logger.warning("Audio file appears invalid: %s", audio_path)
                return True

            # Check file size
            if Path(audio_path).stat().st_size == 0:
                logger.warning("Audio file is empty: %s", audio_path)
                return True

            # Check duration
            if duration <= 0:
                logger.warning("Audio file has no duration: %s", audio_path)
                return True

            return False

        except Exception as e:
            logger.warning("Audio file appears corrupted: %s - %s", audio_path, e)
            return True

    def _validate_audio_format(self, file_path: str) -> bool:
        """Validate audio file format.

        Args:
            file_path: Path to audio file

        Returns:
            True if format is supported, False otherwise
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_formats

    def _validate_audio_duration(self, audio_data, sample_rate: int) -> tuple[bool, float]:
        """Validate audio duration is within acceptable limits.

        Args:
            audio_data: Audio data array
            sample_rate: Sample rate of audio

        Returns:
            Tuple of (is_valid, duration_seconds)
        """
        duration = len(audio_data) / sample_rate
        is_valid = self.min_duration <= duration <= self.max_duration
        return is_valid, duration

    def _preprocess_audio(self, audio_path: str) -> str:
        """Preprocess audio file for Whisper processing.

        Args:
            audio_path: Path to input audio file

        Returns:
            Path to preprocessed audio file
        """
        try:
            # Load audio file
            audio_data, sample_rate = librosa.load(audio_path, sr=16000)  # Whisper expects 16kHz

            # Validate duration
            is_valid, duration = self._validate_audio_duration(audio_data, int(sample_rate))
            if not is_valid:
                if duration > self.max_duration:
                    logger.warning("Audio duration %.2fs exceeds maximum %ds, truncating", duration, self.max_duration)
                    # Truncate to max duration
                    max_samples = int(self.max_duration * sample_rate)
                    audio_data = audio_data[:max_samples]
                elif duration < self.min_duration:
                    logger.warning("Audio duration %.2fs below minimum %ds", duration, self.min_duration)
                    return audio_path  # Return original, let Whisper handle it

            # Create temporary preprocessed file
            temp_fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="plantguard_audio_")
            os.close(temp_fd)  # Close file descriptor, we'll write with soundfile

            # Save preprocessed audio
            sf.write(temp_path, audio_data, sample_rate)
            self.temp_files.append(temp_path)

            logger.debug("Audio preprocessed: %s -> %s (%.2fs)", audio_path, temp_path, duration)
            return temp_path

        except Exception as e:
            logger.error("Audio preprocessing failed: %s", e)
            return audio_path  # Return original file as fallback

    def transcribe(self, audio_file: str | bytes) -> str:
        """Transcribe audio file to text using Whisper-tiny.

        Args:
            audio_file: Path to audio file or audio bytes

        Returns:
            Transcribed text string

        Raises:
            RuntimeError: If transcription fails
        """
        try:
            # Load pipeline if not already loaded
            self._load_pipeline()

            # Handle bytes input
            if isinstance(audio_file, bytes):
                return self.process_audio_bytes(audio_file)

            # Validate file exists
            if not Path(audio_file).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")

            # Check for corrupted or empty files
            if self._is_audio_corrupted(audio_file):
                logger.error("Audio file is corrupted or empty: %s", audio_file)
                return ""

            # Validate file format
            if not self._validate_audio_format(audio_file):
                logger.warning("Unsupported audio format: %s", audio_file)
                # Try to process anyway, librosa might handle it

            # Preprocess audio
            processed_path = self._preprocess_audio(audio_file)

            logger.info("Transcribing audio file: %s", audio_file)
            start_time = time.time()

            # Perform transcription with timeout handling
            try:
                # Set up timeout signal (Unix-like systems only)
                if hasattr(signal, "SIGALRM"):
                    signal.signal(signal.SIGALRM, self._timeout_handler)
                    signal.alarm(self.processing_timeout)

                if self.pipeline is None:
                    raise RuntimeError("Pipeline not initialized")

                result = self.pipeline(processed_path)
                transcription = result.get("text", "").strip()

                # Cancel timeout
                if hasattr(signal, "SIGALRM"):
                    signal.alarm(0)

                processing_time = time.time() - start_time
                logger.info("Transcription completed in %.2fs: '%s'", processing_time, transcription[:100])

                # Handle empty transcription
                if not transcription:
                    logger.warning("No speech detected in audio file")
                    return ""

                return transcription

            except TimeoutError:
                logger.error("Audio processing timeout after %ds", self.processing_timeout)
                return ""
            except Exception as e:
                logger.error("Whisper transcription failed: %s", e)
                # Don't raise, return empty string for graceful degradation
                return ""
            finally:
                # Ensure timeout is cancelled
                if hasattr(signal, "SIGALRM"):
                    signal.alarm(0)

        except Exception as e:
            logger.error("Audio transcription error: %s", e)
            # Return empty string for graceful degradation
            return ""
        finally:
            # Clean up temporary files
            self.cleanup_temp_files()

    def process_audio_bytes(self, audio_bytes: bytes) -> str:
        """Process in-memory audio data from Streamlit.

        Args:
            audio_bytes: Audio data as bytes

        Returns:
            Transcribed text string
        """
        temp_path = None
        try:
            # Create temporary file for audio bytes
            temp_fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="plantguard_bytes_")
            self.temp_files.append(temp_path)

            # Write bytes to temporary file
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)

            logger.debug("Audio bytes written to temporary file: %s", temp_path)

            # Process the temporary file
            return self.transcribe(temp_path)

        except Exception as e:
            logger.error("Failed to process audio bytes: %s", e)
            return ""
        finally:
            # Cleanup will be handled by transcribe() method
            pass

    def cleanup_temp_files(self) -> None:
        """Remove temporary audio files with error handling."""
        for temp_file in self.temp_files:
            try:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    temp_path.unlink()
                    logger.debug("Cleaned up temporary file: %s", temp_file)
            except Exception as e:
                logger.warning("Failed to cleanup temporary file %s: %s", temp_file, e)

        # Clear the list
        self.temp_files.clear()

    def __del__(self) -> None:
        """Cleanup temporary files when object is destroyed."""
        self.cleanup_temp_files()
