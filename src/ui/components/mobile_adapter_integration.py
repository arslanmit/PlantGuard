"""
Mobile Adapter Integration for PlantGuard UI.

This module provides integration between mobile components and existing
PlantGuard adapters (Vision, Audio, Text) with proper error handling
and mobile-optimized preprocessing.
"""

import logging
from datetime import datetime
from typing import Any

import streamlit as st
from PIL import Image

logger = logging.getLogger(__name__)


class MobileAdapterIntegration:
    """Integration layer between mobile components and PlantGuard adapters."""

    def __init__(self):
        """Initialize mobile adapter integration."""
        self._vision_adapter: Any | None = None
        self._audio_adapter: Any | None = None
        self._text_adapter: Any | None = None
        self._chat_model: Any | None = None

        # Mobile-specific preprocessing settings
        self.mobile_config = {
            "image_preprocessing": {
                "max_size": (1920, 1080),  # Max resolution for mobile
                "quality": 85,  # JPEG quality for mobile optimization
                "format": "JPEG",
                "auto_orient": True,  # Fix orientation from mobile cameras
            },
            "audio_preprocessing": {
                "sample_rate": 16000,  # Optimal for Whisper
                "max_duration": 60,  # 60 seconds max
                "normalize": True,
                "noise_reduction": True,
            },
            "text_preprocessing": {
                "max_length": 1000,  # Max characters for mobile input
                "clean_whitespace": True,
                "remove_emojis": False,  # Keep emojis for mobile users
            },
        }

    @property
    def vision_adapter(self) -> Any | None:
        """Get or create vision adapter instance."""
        if self._vision_adapter is None:
            try:
                from src.core.vision import VisionAdapter

                # Use cached adapter if available in session state
                if "vision_adapter" not in st.session_state:
                    st.session_state.vision_adapter = VisionAdapter(model_path="data/models/vision_resnet50.pt", lazy_load=True)

                self._vision_adapter = st.session_state.vision_adapter
                logger.info("Vision adapter initialized for mobile integration")

            except Exception as e:
                logger.error("Failed to initialize vision adapter: %s", e)
                raise RuntimeError(f"Vision adapter initialization failed: {e}") from e

        return self._vision_adapter

    @vision_adapter.setter
    def vision_adapter(self, adapter: Any | None) -> None:
        """Set vision adapter instance (for testing)."""
        self._vision_adapter = adapter

    @vision_adapter.deleter
    def vision_adapter(self) -> None:
        """Delete vision adapter instance (for testing)."""
        self._vision_adapter = None

    @property
    def audio_adapter(self) -> Any | None:
        """Get or create audio adapter instance."""
        if self._audio_adapter is None:
            try:
                from src.core.audio import AudioAdapter

                # Use cached adapter if available in session state
                if "audio_adapter" not in st.session_state:
                    st.session_state.audio_adapter = AudioAdapter(model_name="openai/whisper-tiny")

                self._audio_adapter = st.session_state.audio_adapter
                logger.info("Audio adapter initialized for mobile integration")

            except Exception as e:
                logger.error("Failed to initialize audio adapter: %s", e)
                raise RuntimeError(f"Audio adapter initialization failed: {e}") from e

        return self._audio_adapter

    @audio_adapter.setter
    def audio_adapter(self, adapter: Any | None) -> None:
        """Set audio adapter instance (for testing)."""
        self._audio_adapter = adapter

    @audio_adapter.deleter
    def audio_adapter(self) -> None:
        """Delete audio adapter instance (for testing)."""
        self._audio_adapter = None

    @property
    def text_adapter(self) -> Any | None:
        """Get or create text adapter instance."""
        if self._text_adapter is None:
            try:
                from src.core.nlp import TextAdapter

                # Use cached adapter if available in session state
                if "text_adapter" not in st.session_state:
                    st.session_state.text_adapter = TextAdapter(knowledge_base_path="data/knowledge_base/disease_info.json")

                self._text_adapter = st.session_state.text_adapter
                logger.info("Text adapter initialized for mobile integration")

            except Exception as e:
                logger.error("Failed to initialize text adapter: %s", e)
                raise RuntimeError(f"Text adapter initialization failed: {e}") from e

        return self._text_adapter

    @text_adapter.setter
    def text_adapter(self, adapter: Any | None) -> None:
        """Set text adapter instance (for testing)."""
        self._text_adapter = adapter

    @text_adapter.deleter
    def text_adapter(self) -> None:
        """Delete text adapter instance (for testing)."""
        self._text_adapter = None

    def preprocess_mobile_image(self, image: Image.Image, source: str = "mobile") -> Image.Image:
        """
        Preprocess image from mobile device for optimal analysis.

        Args:
            image: PIL Image from mobile device
            source: Source of the image (camera, upload, etc.)

        Returns:
            Preprocessed PIL Image
        """
        try:
            logger.debug("Preprocessing mobile image from %s", source)

            # Auto-orient image (fix rotation from mobile cameras)
            if self.mobile_config["image_preprocessing"]["auto_orient"]:
                try:
                    # Use EXIF orientation data to rotate image correctly
                    from PIL import ImageOps

                    image = ImageOps.exif_transpose(image)
                    logger.debug("Applied EXIF orientation correction")
                except Exception as e:
                    logger.warning("EXIF orientation correction failed: %s", e)

            # Resize if too large (preserve aspect ratio)
            max_size = self.mobile_config["image_preprocessing"]["max_size"]
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.debug("Resized image to %s", image.size)

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
                logger.debug("Converted image to RGB mode")

            # Apply mobile-specific enhancements
            image = self._enhance_mobile_image(image, source)

            return image

        except Exception as e:
            logger.error("Mobile image preprocessing failed: %s", e)
            # Return original image as fallback
            return image

    def _enhance_mobile_image(self, image: Image.Image, source: str) -> Image.Image:
        """Apply mobile-specific image enhancements."""
        try:
            from PIL import ImageEnhance

            # Apply different enhancements based on source
            if source == "camera":
                # Camera images might need contrast/brightness adjustment
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.1)  # Slight contrast boost

                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.05)  # Slight sharpness boost

            elif source == "upload":
                # Uploaded images might be from various sources
                enhancer = ImageEnhance.Color(image)
                image = enhancer.enhance(1.05)  # Slight color enhancement

            return image

        except Exception as e:
            logger.warning("Image enhancement failed: %s", e)
            return image

    def analyze_image(self, image: Image.Image, source: str = "mobile", component_id: str = "unknown") -> dict[str, Any]:
        """
        Analyze image using VisionAdapter with mobile optimizations.

        Args:
            image: PIL Image to analyze
            source: Source of the image (camera, upload, etc.)
            component_id: ID of the component requesting analysis

        Returns:
            Analysis result dictionary
        """
        try:
            logger.info("Starting image analysis from %s (component: %s)", source, component_id)

            # Preprocess image for mobile
            processed_image = self.preprocess_mobile_image(image, source)

            # Perform vision analysis
            vision_adapter = self.vision_adapter
            prediction = vision_adapter.predict(processed_image)

            disease_name, confidence = prediction

            # Create analysis result
            analysis_result = {
                "timestamp": datetime.now().isoformat(),
                "image": processed_image,
                "original_image": image,
                "prediction": prediction,
                "disease_name": disease_name,
                "confidence": confidence,
                "source": source,
                "component_id": component_id,
                "preprocessing_applied": True,
                "analysis_type": "vision",
            }

            # Store in global analysis results
            if "analysis_results" not in st.session_state:
                st.session_state.analysis_results = []

            st.session_state.analysis_results.append(analysis_result)

            # Get disease information from text adapter
            try:
                disease_info = self.text_adapter.get_disease_info(disease_name)
                analysis_result["disease_info"] = disease_info
            except Exception as e:
                logger.warning("Failed to get disease info: %s", e)
                analysis_result["disease_info"] = {}

            logger.info("Image analysis completed: %s (%.1%% confidence)", disease_name, confidence * 100)

            return analysis_result

        except Exception as e:
            logger.error("Image analysis failed: %s", e)

            # Return error result
            return {
                "timestamp": datetime.now().isoformat(),
                "image": image,
                "prediction": ("Error", 0.0),
                "disease_name": "Analysis Error",
                "confidence": 0.0,
                "source": source,
                "component_id": component_id,
                "error": str(e),
                "analysis_type": "vision",
            }

    def transcribe_audio(self, audio_file: str | bytes, source: str = "mobile", component_id: str = "unknown") -> dict[str, Any]:
        """
        Transcribe audio using AudioAdapter with mobile optimizations.

        Args:
            audio_file: Path to audio file or audio bytes
            source: Source of the audio (voice, upload, etc.)
            component_id: ID of the component requesting transcription

        Returns:
            Transcription result dictionary
        """
        try:
            logger.info("Starting audio transcription from %s (component: %s)", source, component_id)

            # Preprocess audio if needed
            processed_audio_file = self._preprocess_mobile_audio(audio_file, source)

            # Perform transcription
            audio_adapter = self.audio_adapter
            transcription = audio_adapter.transcribe(processed_audio_file)

            # Create transcription result
            transcription_result = {
                "timestamp": datetime.now().isoformat(),
                "transcription": transcription,
                "source": source,
                "component_id": component_id,
                "preprocessing_applied": True,
                "analysis_type": "audio",
                "success": bool(transcription and transcription.strip()),
            }

            # Store in chat history if successful
            if transcription_result["success"]:
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []

                user_message = {
                    "role": "user",
                    "content": transcription,
                    "timestamp": transcription_result["timestamp"],
                    "source": f"voice_{source}",
                    "component_id": component_id,
                }

                st.session_state.chat_history.append(user_message)

            logger.info("Audio transcription completed: %s characters", len(transcription) if transcription else 0)

            return transcription_result

        except Exception as e:
            logger.error("Audio transcription failed: %s", e)

            # Return error result
            return {
                "timestamp": datetime.now().isoformat(),
                "transcription": "",
                "source": source,
                "component_id": component_id,
                "error": str(e),
                "analysis_type": "audio",
                "success": False,
            }

    def _preprocess_mobile_audio(self, audio_file: str | bytes, source: str) -> str | bytes:
        """Preprocess audio from mobile device."""
        try:
            # For now, return as-is since AudioAdapter handles preprocessing
            # Future enhancements could include noise reduction, normalization, etc.
            return audio_file

        except Exception as e:
            logger.warning("Audio preprocessing failed: %s", e)
            return audio_file

    def process_text_query(
        self, text: str, source: str = "mobile", component_id: str = "unknown", context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Process text query using TextAdapter with mobile optimizations.

        Args:
            text: Text query to process
            source: Source of the text (chat, voice, etc.)
            component_id: ID of the component requesting processing
            context: Optional context (e.g., recent analysis results)

        Returns:
            Text processing result dictionary
        """
        try:
            logger.info("Processing text query from %s (component: %s)", source, component_id)

            # Preprocess text for mobile
            processed_text = self._preprocess_mobile_text(text)

            # Get context from recent analysis if available
            disease_class = ""
            confidence = 0.0

            if context and "recent_analysis" in context:
                recent = context["recent_analysis"]
                disease_class = recent.get("disease_name", "")
                confidence = recent.get("confidence", 0.0)
            elif "analysis_results" in st.session_state and st.session_state.analysis_results:
                # Use most recent analysis result
                recent = st.session_state.analysis_results[-1]
                disease_class = recent.get("disease_name", "")
                confidence = recent.get("confidence", 0.0)

            # Generate response using text adapter
            text_adapter = self.text_adapter
            response = text_adapter.generate_response(disease_class=disease_class, user_query=processed_text, confidence=confidence)

            # Create processing result
            processing_result = {
                "timestamp": datetime.now().isoformat(),
                "query": processed_text,
                "original_query": text,
                "response": response,
                "disease_context": disease_class,
                "confidence_context": confidence,
                "source": source,
                "component_id": component_id,
                "preprocessing_applied": True,
                "analysis_type": "text",
            }

            # Store in chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            # Add user message if not already added
            user_message = {
                "role": "user",
                "content": processed_text,
                "timestamp": processing_result["timestamp"],
                "source": source,
                "component_id": component_id,
            }

            # Add assistant response
            assistant_message = {
                "role": "assistant",
                "content": response,
                "timestamp": processing_result["timestamp"],
                "source": f"response_{source}",
                "component_id": component_id,
                "context": {"disease": disease_class, "confidence": confidence},
            }

            st.session_state.chat_history.extend([user_message, assistant_message])

            logger.info("Text processing completed: %s characters response", len(response))

            return processing_result

        except Exception as e:
            logger.error("Text processing failed: %s", e)

            # Return error result
            return {
                "timestamp": datetime.now().isoformat(),
                "query": text,
                "response": "I apologize, but I encountered an error processing your question. Please try again.",
                "source": source,
                "component_id": component_id,
                "error": str(e),
                "analysis_type": "text",
            }

    def _preprocess_mobile_text(self, text: str) -> str:
        """Preprocess text from mobile input."""
        try:
            config = self.mobile_config["text_preprocessing"]

            # Clean whitespace
            if config["clean_whitespace"]:
                text = " ".join(text.split())

            # Truncate if too long
            if len(text) > config["max_length"]:
                # Reserve 3 characters for "..."
                max_content_length = config["max_length"] - 3
                # Find the last space before max_content_length to avoid cutting words
                truncated = text[:max_content_length]
                last_space = truncated.rfind(" ")
                if last_space > 0:
                    text = truncated[:last_space] + "..."
                else:
                    text = truncated + "..."
                logger.warning("Text truncated to %s characters", config["max_length"])

            return text.strip()

        except Exception as e:
            logger.warning("Text preprocessing failed: %s", e)
            return text

    def get_recent_analysis(self, limit: int = 1) -> list[dict[str, Any]]:
        """Get recent analysis results."""
        if "analysis_results" not in st.session_state:
            return []

        results = st.session_state.analysis_results
        return results[-limit:] if results else []

    def clear_analysis_history(self) -> None:
        """Clear analysis history."""
        if "analysis_results" in st.session_state:
            st.session_state.analysis_results = []

        if "chat_history" in st.session_state:
            st.session_state.chat_history = []

        logger.info("Analysis history cleared")

    def get_adapter_status(self) -> dict[str, bool]:
        """Get status of all adapters."""
        status = {"vision_adapter": False, "audio_adapter": False, "text_adapter": False}

        try:
            # Check vision adapter
            vision_adapter = self.vision_adapter
            status["vision_adapter"] = vision_adapter is not None
        except Exception:
            pass

        try:
            # Check audio adapter
            audio_adapter = self.audio_adapter
            status["audio_adapter"] = audio_adapter is not None
        except Exception:
            pass

        try:
            # Check text adapter
            text_adapter = self.text_adapter
            status["text_adapter"] = text_adapter is not None
        except Exception:
            pass

        return status


# Global instance for mobile components to use
mobile_integration = MobileAdapterIntegration()
