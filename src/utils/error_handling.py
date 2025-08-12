"""
Error handling utilities for PlantGuard.
"""

import logging
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for PlantGuard system."""

    def handle_vision_error(self, error: Exception, image: Image.Image | None = None) -> str:
        """
        Handle vision processing errors.

        Args:
            error: The exception that occurred
            image: The image that caused the error (optional)

        Returns:
            User-friendly error message
        """
        logger.error("Vision processing error: %s", error)

        if "CUDA" in str(error) or "GPU" in str(error):
            return (
                "Unable to process image due to GPU memory issues. "
                "Please try with a smaller image or contact support."
            )

        if "format" in str(error).lower() or "PIL" in str(error):
            return (
                "The uploaded image format is not supported. Please use JPG, PNG, or JPEG format."
            )

        return (
            "Unable to analyze the plant image. Please ensure the image "
            "shows a clear view of a plant leaf and try again."
        )

    def handle_audio_error(self, error: Exception, audio_data: bytes | None = None) -> str:
        """
        Handle audio processing errors.

        Args:
            error: The exception that occurred
            audio_data: The audio data that caused the error (optional)

        Returns:
            User-friendly error message
        """
        logger.error("Audio processing error: %s", error)

        if "whisper" in str(error).lower() or "speech" in str(error).lower():
            return (
                "Unable to transcribe audio. Please ensure you spoke clearly "
                "and try recording again."
            )

        if "format" in str(error).lower() or "codec" in str(error).lower():
            return "Audio format not supported. Please use WAV or MP3 format."

        return "Unable to process audio recording. Please try recording again with clear speech."

    def handle_system_error(self, error: Exception) -> dict[str, str | bool]:
        """
        Handle system-wide errors.

        Args:
            error: The exception that occurred

        Returns:
            Dictionary with error information
        """
        logger.error("System error: %s", error)

        return {
            "error": True,
            "message": "A system error occurred. Please try again later.",
            "details": str(error)
            if logger.level <= logging.DEBUG
            else "Contact support if the issue persists.",
        }

    def handle_analysis_error(
        self, error: Exception, image: Image.Image | None = None
    ) -> dict[str, Any]:
        """
        Handle errors during plant analysis.

        Args:
            error: The exception that occurred
            image: The image being analyzed (optional)

        Returns:
            Error response dictionary
        """
        logger.error("Analysis error: %s", error)

        return {
            "disease_class": "unknown",
            "confidence": 0.0,
            "response": (
                "I'm sorry, I couldn't analyze your plant image. "
                "Please ensure the image shows a clear view of a plant leaf "
                "and try again. If the problem persists, consider consulting "
                "a plant expert or agricultural extension service."
            ),
            "user_query": "",
            "transcribed_audio": "",
            "success": False,
            "error": str(error),
        }
