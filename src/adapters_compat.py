"""
Compatibility layer for PlantGuard adapters in the unified interface.

This module provides simplified mock implementations to ensure the unified UI
can run without requiring full adapter implementations.
"""

import logging
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)


class MockVisionAdapter:
    """Mock Vision Adapter for unified interface compatibility."""

    def __init__(self):
        """Initialize mock vision adapter."""
        logger.info("Initialized Mock Vision Adapter")

    def predict(self, image: Image.Image) -> tuple[str, float]:
        """Mock image analysis that returns realistic test results."""
        try:
            # Simulate processing delay
            import time

            time.sleep(1)

            # Return mock prediction results
            return ("Tomato Late Blight", 0.87)

        except Exception as e:
            logger.error(f"Mock vision analysis error: {e}")
            return ("Unknown Disease", 0.0)


class MockAudioAdapter:
    """Mock Audio Adapter for unified interface compatibility."""

    def __init__(self):
        """Initialize mock audio adapter."""
        logger.info("Initialized Mock Audio Adapter")

    def process_audio(self, audio_path: str) -> dict[str, Any] | None:
        """Mock audio processing that returns test transcription."""
        try:
            # Simulate processing
            import time

            time.sleep(2)

            return {
                "transcription": "What disease does my tomato plant have?",
                "confidence": 0.92,
                "model_info": {"name": "Mock Whisper", "version": "tiny"},
            }

        except Exception as e:
            logger.error(f"Mock audio processing error: {e}")
            return None


class MockTextAdapter:
    """Mock Text Adapter for unified interface compatibility."""

    def __init__(self):
        """Initialize mock text adapter."""
        logger.info("Initialized Mock Text Adapter")

        # Mock knowledge base
        self.knowledge_base = {
            "common diseases": "Common plant diseases include late blight, bacterial spot, leaf mold, and powdery mildew. Each has distinct symptoms and treatment approaches.",
            "watering": "Most houseplants need water when the top inch of soil feels dry. Check soil moisture regularly and adjust based on season and humidity.",
            "light": "Most houseplants prefer bright, indirect light. Avoid direct sunlight which can burn leaves. Rotate plants weekly for even growth.",
            "fertilizer": "Feed most houseplants every 2-4 weeks during growing season (spring/summer) with balanced liquid fertilizer diluted to half strength.",
            "pests": "Common pests include aphids, spider mites, and scale. Check plants regularly and treat early with insecticidal soap or neem oil.",
        }

    def generate_response(self, disease_class: str = "general", user_query: str = "", confidence: float = 0.0) -> str:
        """Mock text processing that returns knowledge-based responses."""
        try:
            text_lower = user_query.lower()

            # Simple keyword matching for responses
            response = "I'm here to help with your plant care questions! "

            if any(word in text_lower for word in ["disease", "sick", "problem", "spot", "blight"]):
                response += self.knowledge_base["common diseases"]
            elif any(word in text_lower for word in ["water", "watering", "how often"]):
                response += self.knowledge_base["watering"]
            elif any(word in text_lower for word in ["light", "sun", "lighting"]):
                response += self.knowledge_base["light"]
            elif any(word in text_lower for word in ["fertilizer", "feed", "nutrients"]):
                response += self.knowledge_base["fertilizer"]
            elif any(word in text_lower for word in ["pest", "bug", "insect"]):
                response += self.knowledge_base["pests"]
            else:
                response += "For specific plant care advice, I recommend checking the plant's specific care requirements. Feel free to ask about diseases, watering, lighting, or pests!"

            return response

        except Exception as e:
            logger.error(f"Mock text processing error: {e}")
            return "I apologize, but I'm having trouble processing your question right now. Please try again."


# Always use mock adapters for development and compatibility
# This ensures the unified interface works without requiring full model loading
VisionAdapter = MockVisionAdapter
AudioAdapter = MockAudioAdapter
TextAdapter = MockTextAdapter

logger.info("Using mock adapters for unified interface compatibility")
