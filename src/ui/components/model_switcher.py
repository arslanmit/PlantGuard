"""Model Switcher Component for PlantGuard.

Provides functionality to switch between different AI models for vision, audio, and text processing.
"""

import logging
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class ModelSwitcher:
    """Component for managing and switching between different AI models."""

    def __init__(self) -> None:
        self.session_key = "selected_models"
        self.available_models = {
            "vision": {
                "vit_base_plants": {
                    "name": "Vision Transformer (Best)",
                    "description": "State-of-the-art transformer model for plant disease detection",
                    "accuracy": 100,
                    "speed": "Medium",
                    "memory": "High",
                },
                "resnet50_plantvillage_v1": {
                    "name": "ResNet50 (Balanced)",
                    "description": "Balanced performance model for general plant disease detection",
                    "accuracy": 95,
                    "speed": "Fast",
                    "memory": "Medium",
                },
                "mobilenet_fast": {
                    "name": "MobileNet (Fast)",
                    "description": "Lightweight model optimized for mobile and edge devices",
                    "accuracy": 90,
                    "speed": "Very Fast",
                    "memory": "Low",
                },
            },
            "audio": {
                "whisper_tiny_local": {
                    "name": "Whisper Tiny (Local)",
                    "description": "Local speech-to-text processing with privacy protection",
                    "accuracy": 85,
                    "speed": "Fast",
                    "memory": "Low",
                },
                "wav2vec2_plant_sounds": {
                    "name": "Wav2Vec2 (Plant Sounds)",
                    "description": "Specialized model for plant-related audio analysis",
                    "accuracy": 80,
                    "speed": "Medium",
                    "memory": "Medium",
                },
            },
            "text": {
                "distilbert_plant_qa_v1": {
                    "name": "DistilBERT (Plant Q&A)",
                    "description": "Optimized model for plant care question answering",
                    "accuracy": 92,
                    "speed": "Fast",
                    "memory": "Medium",
                },
                "roberta_plant_care": {
                    "name": "RoBERTa (Advanced)",
                    "description": "Advanced language model for complex plant care queries",
                    "accuracy": 95,
                    "speed": "Medium",
                    "memory": "High",
                },
                "t5_small_plant_qa": {
                    "name": "T5 Small (Creative)",
                    "description": "Generative model for creative plant care solutions",
                    "accuracy": 88,
                    "speed": "Medium",
                    "memory": "Medium",
                },
            },
        }

        # Initialize default selections
        if "selected_models" not in st.session_state:
            st.session_state.selected_models = {
                "vision": "resnet50_plantvillage_v1",
                "audio": "whisper_tiny_local",
                "text": "distilbert_plant_qa_v1",
            }

    def get_available_models(self, model_type: str) -> dict[str, dict[str, Any]]:
        """Get available models for a specific type."""
        return self.available_models.get(model_type, {})

    def get_current_model(self, model_type: str) -> str:
        """Get currently selected model for a type."""
        return st.session_state.selected_models.get(model_type, "")

    def set_model(self, model_type: str, model_id: str) -> bool:
        """Set the active model for a specific type."""
        if model_type in self.available_models and model_id in self.available_models[model_type]:
            st.session_state.selected_models[model_type] = model_id
            logger.info(f"Switched {model_type} model to {model_id}")
            return True
        return False

    def get_model_info(self, model_type: str, model_id: str) -> dict[str, Any]:
        """Get detailed information about a specific model."""
        return self.available_models.get(model_type, {}).get(model_id, {})

    def render_model_selector(self, model_type: str, key_suffix: str = "") -> str:
        """Render a model selector widget for a specific type."""
        available = self.get_available_models(model_type)
        if not available:
            st.error(f"No models available for {model_type}")
            return ""

        current = self.get_current_model(model_type)

        # Create display options
        options = []
        model_keys = []
        for model_id, info in available.items():
            display_name = f"{info['name']} ({info['accuracy']}%)"
            options.append(display_name)
            model_keys.append(model_id)

        # Find current index
        current_index = 0
        if current in model_keys:
            current_index = model_keys.index(current)

        # Render selector
        selected_display = st.selectbox(
            f"Select {model_type.title()} Model",
            options=options,
            index=current_index,
            key=f"model_selector_{model_type}_{key_suffix}",
            help=f"Choose the {model_type} model for analysis",
        )

        # Get selected model ID
        selected_id = model_keys[options.index(selected_display)]

        # Update if changed
        if selected_id != current:
            self.set_model(model_type, selected_id)
            st.success(f"[DONE] {model_type.title()} model updated to {selected_id}")

        return selected_id

    def render_model_status(self) -> None:
        """Render current model status display."""
        st.markdown("### [LAUNCH] Current Model Configuration")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### [VISION] Vision")
            current_vision = self.get_current_model("vision")
            if current_vision:
                info = self.get_model_info("vision", current_vision)
                st.info(f"**{info.get('name', current_vision)}**")
                st.caption(f"Accuracy: {info.get('accuracy', 'N/A')}%")
            else:
                st.warning("No vision model selected")

        with col2:
            st.markdown("#### [VOICE] Audio")
            current_audio = self.get_current_model("audio")
            if current_audio:
                info = self.get_model_info("audio", current_audio)
                st.info(f"**{info.get('name', current_audio)}**")
                st.caption(f"Speed: {info.get('speed', 'N/A')}")
            else:
                st.warning("No audio model selected")

        with col3:
            st.markdown("#### [CHAT] Text")
            current_text = self.get_current_model("text")
            if current_text:
                info = self.get_model_info("text", current_text)
                st.info(f"**{info.get('name', current_text)}**")
                st.caption(f"Accuracy: {info.get('accuracy', 'N/A')}%")
            else:
                st.warning("No text model selected")

    def render_model_comparison(self) -> None:
        """Render model comparison table."""
        st.markdown("### [SUMMARY] Model Comparison")

        for model_type, models in self.available_models.items():
            st.markdown(f"#### {model_type.title()} Models")

            # Create comparison data
            comparison_data = []
            for model_id, info in models.items():
                comparison_data.append(
                    {
                        "Model": info.get("name", model_id),
                        "Accuracy": f"{info.get('accuracy', 'N/A')}%",
                        "Speed": info.get("speed", "N/A"),
                        "Memory": info.get("memory", "N/A"),
                        "Description": info.get("description", ""),
                    }
                )

            st.table(comparison_data)

    def render(self, available_models: dict | None = None) -> None:
        """Compatibility render method used by legacy callers.

        If `available_models` is provided, use it to populate selectors; otherwise
        fall back to the internal `available_models` mapping.
        """
        models_to_use = available_models or self.available_models
        # Render simple selectors for each type
        for model_type in ("vision", "audio", "text"):
            # Use provided mapping if present
            if model_type in models_to_use:
                # If mapping gives dicts, update internal available_models for display
                if isinstance(models_to_use[model_type], dict):
                    # nothing to do exactly; use existing render_model_selector
                    self.render_model_selector(model_type)
                else:
                    # Provided a list of ids; create a temporary mapping
                    tmp_map = {mid: {"name": mid, "accuracy": 0} for mid in models_to_use[model_type]}
                    # Temporarily override for selector
                    old = self.available_models.get(model_type)
                    self.available_models[model_type] = tmp_map
                    try:
                        self.render_model_selector(model_type)
                    finally:
                        # Restore
                        if old is not None:
                            self.available_models[model_type] = old

    def get_model_performance_metrics(self, model_type: str, model_id: str) -> dict[str, Any]:
        """Get performance metrics for a specific model."""
        info = self.get_model_info(model_type, model_id)
        return {
            "accuracy": info.get("accuracy", 0),
            "speed": info.get("speed", "Unknown"),
            "memory_usage": info.get("memory", "Unknown"),
            "model_size": info.get("size", "Unknown"),
        }

    def validate_model_selection(self) -> dict[str, bool]:
        """Validate that all required models are selected."""
        validation = {}
        for model_type in ["vision", "audio", "text"]:
            current = self.get_current_model(model_type)
            validation[model_type] = bool(current and current in self.available_models.get(model_type, {}))
        return validation

    def reset_to_defaults(self) -> None:
        """Reset model selection to defaults."""
        st.session_state.selected_models = {
            "vision": "resnet50_plantvillage_v1",
            "audio": "whisper_tiny_local",
            "text": "distilbert_plant_qa_v1",
        }
        st.success("[PARTIAL] Model selection reset to defaults")

    def export_configuration(self) -> dict[str, Any]:
        """Export current model configuration."""
        return {
            "selected_models": st.session_state.selected_models.copy(),
            "available_models": self.available_models,
            "timestamp": st.session_state.get("current_time", ""),
        }

    def import_configuration(self, config: dict[str, Any]) -> bool:
        """Import model configuration."""
        try:
            if "selected_models" in config:
                # Validate configuration
                for model_type, model_id in config["selected_models"].items():
                    if model_type not in self.available_models:
                        return False
                    if model_id not in self.available_models[model_type]:
                        return False

                # Apply configuration
                st.session_state.selected_models = config["selected_models"]
                return True
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
        return False
