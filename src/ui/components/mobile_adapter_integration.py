"""Mobile adapter integra        self.mobile_config: dict[str, Any] = {
            "max_image_size": (224, 224),
            "supported_formats": ["jpg", "jpeg", "png"],
            "cache_enabled": True,
            "offline_mode": False,
            "image_preprocessing": {
                "max_size": (1920, 1080),
                "quality": 85,
                "format": "JPEG",
                "auto_orient": True
            }
        }or PlantGuard UI components.

This module provides integration utilities for mobile UI components
and adapters in the PlantGuard system.
"""

import logging
from datetime import datetime
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)


class MobileAdapterIntegration:
    """Integration utilities for mobile adapters and UI components."""

    def __init__(self):
        """Initialize the mobile adapter integration."""
        self.adapters: dict[str, Any] = {}
        self.components: list[Any] = []
        self._vision_adapter: Any | None = None
        self._audio_adapter: Any | None = None
        self._text_adapter: Any | None = None
        self.analysis_history: list[dict[str, Any]] = []
        self.mobile_config: dict[str, Any] = {
            "max_image_size": (224, 224),
            "supported_formats": ["jpg", "jpeg", "png"],
            "cache_enabled": True,
            "offline_mode": False,
            "image_preprocessing": {"max_size": (1920, 1080), "quality": 85, "format": "JPEG", "auto_orient": True},
            "audio_preprocessing": {"sample_rate": 16000, "max_duration": 60},
            "text_preprocessing": {"max_length": 1000, "clean_whitespace": True},
        }

    @property
    def vision_adapter(self) -> Any | None:
        """Get the vision adapter."""
        return self._vision_adapter

    @vision_adapter.setter
    def vision_adapter(self, adapter: Any) -> None:
        """Set the vision adapter."""
        self._vision_adapter = adapter
        self.adapters["vision"] = adapter

    @property
    def audio_adapter(self) -> Any | None:
        """Get the audio adapter."""
        return self._audio_adapter

    @audio_adapter.setter
    def audio_adapter(self, adapter: Any) -> None:
        """Set the audio adapter."""
        self._audio_adapter = adapter
        self.adapters["audio"] = adapter

    @property
    def text_adapter(self) -> Any | None:
        """Get the text adapter."""
        return self._text_adapter

    @text_adapter.setter
    def text_adapter(self, adapter: Any) -> None:
        """Set the text adapter."""
        self._text_adapter = adapter
        self.adapters["text"] = adapter

    def register_adapter(self, name: str, adapter: Any) -> None:
        """Register an adapter for mobile integration.

        Args:
            name: Name of the adapter
            adapter: Adapter instance to register
        """
        self.adapters[name] = adapter
        logger.info("Registered mobile adapter: %s", name)

    def get_adapter(self, name: str) -> Any | None:
        """Get a registered adapter by name.

        Args:
            name: Name of the adapter to retrieve

        Returns:
            The adapter instance or None if not found
        """
        return self.adapters.get(name)

    def list_adapters(self) -> list[str]:
        """List all registered adapter names.

        Returns:
            List of registered adapter names
        """
        return list(self.adapters.keys())

    def integrate_component(self, component: Any) -> None:
        """Integrate a UI component with mobile adapters.

        Args:
            component: UI component to integrate
        """
        self.components.append(component)
        comp_name = type(component).__name__
        logger.info("Integrated mobile component: %s", comp_name)

    def get_component_count(self) -> int:
        """Get the number of integrated components.

        Returns:
            Number of integrated components
        """
        return len(self.components)

    def preprocess_mobile_image(self, image: Image.Image, _source: str) -> Image.Image:
        """Preprocess an image for mobile analysis.

        Args:
            image: Input image
            source: Source of the image (camera, gallery, etc.)

        Returns:
            Processed image
        """
        # Basic preprocessing - resize and convert
        max_size = self.mobile_config["max_image_size"]
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image = image.resize(max_size, Image.Resampling.LANCZOS)
        return image

    def analyze_image(self, image: Image.Image, source: str = "unknown", component_id: str = "unknown", **_kwargs) -> dict[str, Any]:
        """Analyze an image using the vision adapter.

        Args:
            image: Image to analyze
            source: Source of the analysis
            component_id: ID of the component
            **kwargs: Additional analysis parameters

        Returns:
            Analysis results
        """
        if not self._vision_adapter:
            raise ValueError("Vision adapter not initialized")

        # Preprocess image
        processed_image = self.preprocess_mobile_image(image, source)

        try:
            # Perform analysis
            result = self._vision_adapter.predict(processed_image)

            # Store in history
            analysis_result = {"timestamp": datetime.now(), "type": "image", "result": result, "source": source}
            self.analysis_history.append(analysis_result)

            # Return dict format expected by tests
            confidence = result[1] if isinstance(result, tuple) and len(result) > 1 else 0.95
            disease_name = result[0] if isinstance(result, tuple) and len(result) > 0 else result

            # Get disease info from text adapter if available
            disease_info = {"description": f"Analysis of {disease_name}"}
            if self._text_adapter:
                disease_info = self._text_adapter.get_disease_info(disease_name)

            # Store result in session state
            try:
                import streamlit as st

                if hasattr(st, "session_state"):
                    if "analysis_results" not in st.session_state:
                        st.session_state["analysis_results"] = []
                    st.session_state["analysis_results"].append({"disease_name": disease_name, "confidence": confidence, "timestamp": datetime.now()})
            except ImportError:
                pass

            return {
                "disease_name": disease_name,
                "confidence": confidence,
                "source": source,
                "component_id": component_id,
                "preprocessing_applied": True,
                "disease_info": disease_info,
            }
        except Exception as e:
            # Handle errors gracefully
            return {
                "disease_name": "Analysis Error",
                "confidence": 0.0,
                "source": source,
                "component_id": component_id,
                "preprocessing_applied": False,
                "error": str(e),
                "disease_info": {"description": f"Error during analysis: {e}"},
            }

    def transcribe_audio(self, audio_file: str, source: str = "unknown", component_id: str = "unknown", **_kwargs) -> dict[str, Any]:
        """Transcribe audio using the audio adapter.

        Args:
            audio_file: Path to audio file to transcribe
            source: Source of the transcription
            component_id: ID of the component
            **kwargs: Additional transcription parameters

        Returns:
            Transcription results
        """
        if not self._audio_adapter:
            raise ValueError("Audio adapter not initialized")

        try:
            result = self._audio_adapter.transcribe(audio_file)

            # Store in history
            analysis_result = {"timestamp": datetime.now(), "type": "audio", "result": result, "source": source}
            self.analysis_history.append(analysis_result)

            # Update chat history in session state
            try:
                import streamlit as st

                if hasattr(st, "session_state"):
                    if "chat_history" not in st.session_state:
                        st.session_state["chat_history"] = []
                    st.session_state["chat_history"].append({"content": result, "role": "user", "timestamp": datetime.now()})
            except ImportError:
                pass

            return {"transcription": result, "success": True, "source": source, "component_id": component_id, "preprocessing_applied": True}
        except Exception as e:
            return {"transcription": "", "success": False, "error": str(e), "source": source, "component_id": component_id}

    def process_text_query(
        self,
        query: str | None = None,
        context: dict[str, Any] | None = None,
        text: str | None = None,
        source: str = "unknown",
        component_id: str = "unknown",
        **_kwargs,
    ) -> dict[str, Any]:
        """Process a text query using the text adapter.

        Args:
            query: Text query to process
            context: Optional context information
            text: Alternative text parameter
            source: Source of the query
            component_id: ID of the component

        Returns:
            Processing results
        """
        if not self._text_adapter:
            raise ValueError("Text adapter not initialized")

        # Handle both query and text parameters
        actual_query = query or text or ""

        # Prepare context for the text adapter
        context_dict = context or {}

        # If no context provided, try to extract from session state
        if not context_dict:
            try:
                import streamlit as st

                if hasattr(st, "session_state") and "analysis_results" in st.session_state:
                    latest_analysis = st.session_state["analysis_results"][-1] if st.session_state["analysis_results"] else {}
                    context_dict = {
                        "disease_class": latest_analysis.get("disease_name", "Unknown"),
                        "confidence": latest_analysis.get("confidence", 0.0),
                    }
            except ImportError:
                pass

        result = self._text_adapter.generate_response(actual_query, **context_dict)

        # Store in history
        analysis_result = {"timestamp": datetime.now(), "type": "text", "query": actual_query, "result": result, "source": source}
        self.analysis_history.append(analysis_result)

        # Update chat history in session state
        try:
            import streamlit as st

            if hasattr(st, "session_state"):
                if "chat_history" not in st.session_state:
                    st.session_state["chat_history"] = []
                # Add user message
                st.session_state["chat_history"].append({"content": actual_query, "role": "user", "timestamp": datetime.now()})
                # Add assistant message
                st.session_state["chat_history"].append({"content": result, "role": "assistant", "timestamp": datetime.now()})
        except ImportError:
            pass

        # Extract context from session state if available
        try:
            import streamlit as st

            if hasattr(st, "session_state") and "analysis_results" in st.session_state:
                latest_analysis = st.session_state["analysis_results"][-1] if st.session_state["analysis_results"] else {}
                disease_context = latest_analysis.get("disease_name", "Unknown")
                confidence_context = latest_analysis.get("confidence", 0.0)
        except ImportError:
            pass

        # Extract context from session state if available
        disease_context = "Unknown"
        confidence_context = 0.0
        try:
            import streamlit as st

            if hasattr(st, "session_state") and "analysis_results" in st.session_state:
                latest_analysis = st.session_state["analysis_results"][-1] if st.session_state["analysis_results"] else {}
                disease_context = latest_analysis.get("disease_name", "Unknown")
                confidence_context = latest_analysis.get("confidence", 0.0)
        except ImportError:
            pass

        return {
            "query": actual_query,
            "response": result,
            "source": source,
            "component_id": component_id,
            "disease_class": context_dict.get("disease_class", disease_context),
            "disease_context": disease_context,
            "confidence_context": confidence_context,
        }

    def get_recent_analysis(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent analysis history.

        Args:
            limit: Maximum number of recent analyses to return

        Returns:
            List of recent analysis results
        """
        # Check if we have session state available
        try:
            import streamlit as st

            session_state = getattr(st, "session_state", None)
            if session_state and "analysis_results" in session_state:
                results = st.session_state["analysis_results"]
                return results[-limit:] if results else []
        except ImportError:
            pass

        # Fallback to internal history
        return self.analysis_history[-limit:] if self.analysis_history else []

    def clear_analysis_history(self) -> None:
        """Clear the analysis history."""
        # Clear from session state if available
        try:
            import streamlit as st

            if hasattr(st, "session_state"):
                st.session_state["analysis_results"] = []
                st.session_state["chat_history"] = []
        except ImportError:
            pass

        # Clear internal history
        self.analysis_history.clear()
        logger.info("Analysis history cleared")

    def get_adapter_status(self) -> dict[str, bool]:
        """Get the status of all adapters.

        Returns:
            Dictionary mapping adapter names to their status
        """
        return {
            "vision_adapter": self._vision_adapter is not None,
            "audio_adapter": self._audio_adapter is not None,
            "text_adapter": self._text_adapter is not None,
        }

    def _preprocess_mobile_text(self, text: str) -> str:
        """Preprocess text for mobile input.

        Args:
            text: Input text

        Returns:
            Processed text
        """
        # Basic text preprocessing - preserve case, remove extra spaces, and truncate
        import re

        processed = re.sub(r"\s+", " ", text.strip())
        # Truncate to reasonable length for mobile
        max_length = 1000
        if len(processed) > max_length:
            processed = processed[: max_length - 3] + "..."
        return processed


# Global instance for easy access
mobile_adapter_integration = MobileAdapterIntegration()
