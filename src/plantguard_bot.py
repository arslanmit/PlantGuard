"""PlantGuard Bot - Main Orchestration Class.

This module contains the main PlantGuardBot class that coordinates all components
for multimodal plant disease detection and response generation.
"""

import logging
from typing import Any

import torch
from PIL import Image

from .core.audio import AudioAdapter
from .core.nlp import TextAdapter
from .core.vision import VisionAdapter
from .utils.config import Config
from .utils.error_handling import ErrorHandler

logger = logging.getLogger(__name__)


class PlantGuardBot:
    """Main orchestration class for PlantGuard multimodal plant disease detection.

    This class coordinates vision, audio, and text processing to provide
    comprehensive plant disease diagnosis and treatment recommendations.
    """

    def __init__(self, config_path: str | None = None, device: str = "cpu") -> None:
        """Initialize PlantGuardBot with all required components.

        Args:
            config_path: Path to configuration file
            device: Device to run models on ("cpu" or "cuda")
        """
        self.device = torch.device(device)
        self.config = Config(config_path) if config_path else Config()
        self.error_handler = ErrorHandler()

        # Initialize adapters (will be loaded lazily)
        self._vision_adapter: VisionAdapter | None = None
        self._audio_adapter: AudioAdapter | None = None
        self._text_adapter: TextAdapter | None = None

        logger.info("PlantGuardBot initialized with device: %s", self.device)

    @property
    def vision_adapter(self) -> VisionAdapter:
        """Lazy loading of vision adapter."""
        if self._vision_adapter is None:
            self._vision_adapter = VisionAdapter(
                model_path=self.config.vision_model_path, device=str(self.device)
            )
        return self._vision_adapter

    @property
    def audio_adapter(self) -> AudioAdapter:
        """Lazy loading of audio adapter."""
        if self._audio_adapter is None:
            self._audio_adapter = AudioAdapter(model_name=self.config.whisper_model_name)
        return self._audio_adapter

    @property
    def text_adapter(self) -> TextAdapter:
        """Lazy loading of text adapter."""
        if self._text_adapter is None:
            self._text_adapter = TextAdapter(knowledge_base_path=self.config.knowledge_base_path)
        return self._text_adapter

    def analyze_plant(
        self, image: Image.Image, audio_path: str | None = None, text_query: str = ""
    ) -> dict[str, Any]:
        """Main analysis method combining all modalities.

        Args:
            image: Plant leaf image (required)
            audio_path: Optional path to audio file
            text_query: Optional text question

        Returns:
            Dictionary with diagnosis, confidence, response, metadata
        """
        try:
            # Process image for disease detection
            disease_class, confidence = self.vision_adapter.predict(image)

            # Process audio if provided
            transcribed_text = ""
            if audio_path:
                transcribed_text = self.audio_adapter.transcribe(audio_path)

            # Combine text inputs
            combined_query = f"{text_query} {transcribed_text}".strip()

            # Generate response
            response = self.text_adapter.generate_response(disease_class, combined_query)

            return {  # noqa: TRY300
                "disease_class": disease_class,
                "confidence": confidence,
                "response": response,
                "user_query": combined_query,
                "transcribed_audio": transcribed_text,
                "success": True,
            }

        except Exception as e:
            logger.exception("Analysis failed")
            return self.error_handler.handle_analysis_error(e, image)

    def get_health_status(self) -> dict[str, str]:
        """Return system health and model status.

        Returns:
            Dictionary with system status information
        """
        return {
            "vision_model": "loaded" if self._vision_adapter else "not_loaded",
            "audio_model": "loaded" if self._audio_adapter else "not_loaded",
            "text_model": "loaded" if self._text_adapter else "not_loaded",
            "device": str(self.device),
            "status": "healthy",
        }
