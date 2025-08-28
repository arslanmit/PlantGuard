"""
Shared utilities for PlantGuard multi-page application.

This module provides common functionality that all pages can use,
including adapters, session state management, and styling.
"""

import logging
import sys
from pathlib import Path
from typing import Any

import streamlit as st

# Add src to path for local imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import adapters with compatibility fallback
try:
    from core.audio import AudioAdapter
    from core.nlp import TextAdapter
    from core.vision import VisionAdapter
except ImportError:
    # Use compatibility layer if core adapters not available
    from adapters_compat import TextAdapter, VisionAdapter


class PlantGuardPageUtils:
    """Shared utilities for all PlantGuard pages."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.initialize_session_state()
        self.initialize_adapters()

    def initialize_session_state(self):
        """Initialize session state variables used across pages."""
        if "analysis_history" not in st.session_state:
            st.session_state.analysis_history = []
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        if "current_models" not in st.session_state:
            st.session_state.current_models = {"vision": "resnet50_plantvillage_v1", "audio": "whisper_tiny_local", "text": "distilbert_plant_qa_v1"}

    def initialize_adapters(self):
        """Initialize AI model adapters."""
        try:
            self.vision_adapter = VisionAdapter()
            self.text_adapter = TextAdapter()
            # Audio adapter initialization if available
            try:
                self.audio_adapter = AudioAdapter()
            except Exception:
                self.audio_adapter = None
        except Exception as e:
            self.logger.warning(f"Failed to initialize adapters: {e}")
            self.vision_adapter = None
            self.text_adapter = None
            self.audio_adapter = None

    @property
    def models_config(self) -> dict[str, Any]:
        """Get available models configuration."""
        return {
            "vision": {
                "vit_base_plants": {"name": "Vision Transformer", "accuracy": "100%", "speed": "Medium"},
                "resnet50_plantvillage_v1": {"name": "ResNet50", "accuracy": "95%", "speed": "Fast"},
                "mobilenet_fast": {"name": "MobileNet", "accuracy": "90%", "speed": "Very Fast"},
            },
            "audio": {
                "whisper_tiny_local": {"name": "Whisper Tiny", "accuracy": "85%", "speed": "Fast"},
                "wav2vec2_plant_sounds": {"name": "Wav2Vec2", "accuracy": "80%", "speed": "Medium"},
            },
            "text": {
                "distilbert_plant_qa_v1": {"name": "DistilBERT", "accuracy": "92%", "speed": "Fast"},
                "roberta_plant_care": {"name": "RoBERTa", "accuracy": "95%", "speed": "Medium"},
            },
        }

    def render_page_header(self, title: str, description: str):
        """Render a consistent page header."""
        st.markdown(
            f"""
            <div style='text-align: center; padding: 1.5rem 0; background: linear-gradient(135deg, #4CAF50, #45a049);
                        border-radius: 15px; margin-bottom: 2rem; color: white;'>
                <h1 style='margin: 0; font-size: 2rem;'>[LEAF] {title}</h1>
                <p style='margin: 0; font-size: 1rem; opacity: 0.9;'>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render_model_selector(self, model_type: str = "vision"):
        """Render model selection interface in main content area."""
        st.markdown(f"### {model_type.title()} Model")

        current_model = st.session_state.current_models[model_type]
        model_options = [f"{info['name']} ({info['accuracy']})" for info in self.models_config[model_type].values()]
        model_keys = list(self.models_config[model_type].keys())

        try:
            current_idx = model_keys.index(current_model)
        except ValueError:
            current_idx = 0

        selected_model = st.selectbox(f"Choose {model_type} model:", options=model_options, index=current_idx, key=f"{model_type}_model_select")

        # Update model if changed
        new_model_key = model_keys[model_options.index(selected_model)]
        if new_model_key != current_model:
            st.session_state.current_models[model_type] = new_model_key
            st.success(f"[DONE] Updated to {self.models_config[model_type][new_model_key]['name']}")

    def render_tips_card(self, tips: list):
        """Render a tips card with helpful information."""
        tips_html = "".join([f"<li>{tip}</li>" for tip in tips])
        st.markdown(
            f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #4CAF50;'>
                <h4 style='margin: 0; color: #4CAF50;'>[TIP] Tips for Best Results</h4>
                <ul style='margin: 0.5rem 0; padding-left: 1rem;'>
                    {tips_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def analyze_image(self, image):
        """Analyze an image for plant disease detection."""
        try:
            if self.vision_adapter:
                # Use real adapter if available
                result = self.vision_adapter.predict(image)
            else:
                # Mock result for development
                result = {
                    "disease": "Tomato Late Blight",
                    "confidence": 0.87,
                    "treatment": "Apply copper-based fungicide and improve air circulation",
                    "description": "Late blight is a serious disease affecting tomato plants.",
                    "severity": "High",
                }
            return result
        except Exception as e:
            self.logger.error(f"Image analysis failed: {e}")
            return None

    def process_text_query(self, query: str):
        """Process a text query using the text adapter."""
        try:
            if self.text_adapter:
                response = self.text_adapter.generate_response(query)
            else:
                # Mock response for development
                response = f"This is a helpful response about: {query}. The text processing system is currently in development mode."
            return response
        except Exception as e:
            self.logger.error(f"Text processing failed: {e}")
            return "I'm sorry, I couldn't process your question at the moment."

    def display_analysis_result(self, result: dict[str, Any]):
        """Display analysis results in a consistent format."""
        if not result:
            st.error("Analysis failed. Please try again.")
            return

        # Main result display
        col1, col2 = st.columns([2, 1])

        with col1:
            st.success(f"**Disease Detected:** {result.get('disease', 'Unknown')}")
            st.info(f"**Confidence:** {result.get('confidence', 0):.1%}")

            if "description" in result:
                st.markdown(f"**Description:** {result['description']}")

            if "treatment" in result:
                st.markdown(f"**Recommended Treatment:** {result['treatment']}")

        with col2:
            # Confidence meter
            confidence = result.get("confidence", 0)
            if confidence > 0.8:
                st.success(f"High Confidence\n{confidence:.1%}")
            elif confidence > 0.6:
                st.warning(f"Medium Confidence\n{confidence:.1%}")
            else:
                st.error(f"Low Confidence\n{confidence:.1%}")


# Global instance for easy access
page_utils = PlantGuardPageUtils()
