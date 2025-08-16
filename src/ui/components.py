def _get_st():
    """Dynamically import streamlit to respect test-time patching.

    Returns the currently loaded 'streamlit' module from sys.modules, so that
    decorators like @patch("streamlit.session_state", {...}) in tests take effect.
    """
    try:
        return importlib.import_module("streamlit")
    except Exception:
        # Fallback to the initially imported stub/mocked module
        return st


"""Reusable UI components for PlantGuard."""

import logging
from typing import Any, Literal

import importlib
import streamlit as st

logger = logging.getLogger(__name__)

# Type aliases
InputMode = Literal["vision", "audio", "text"]
ThemeMode = Literal["light", "dark", "auto"]


class ModeSwitcher:
    """Advanced mode switcher component with state management."""

    def __init__(self, session_key: str = "input_mode", default_mode: InputMode = "vision"):
        """Initialize the mode switcher.

        Args:
            session_key: Session state key for storing the selected mode
            default_mode: Default mode to select
        """
        self.session_key = session_key
        self.default_mode = default_mode

        # Initialize session state if not exists
        try:
            _st = _get_st()
            # Prefer explicit dict handling (used in tests with patched session_state)
            if isinstance(getattr(_st, "session_state", None), dict):
                if self.session_key not in _st.session_state:  # type: ignore[operator]
                    _st.session_state[self.session_key] = default_mode  # type: ignore[index]
            # Fallback for real Streamlit SessionState (mapping-like)
            elif self.session_key not in _st.session_state:  # type: ignore[operator]
                _st.session_state[self.session_key] = default_mode  # type: ignore[index]
        except Exception:
            # In environments where streamlit is heavily mocked, skip initialization
            logger.debug("ModeSwitcher: session_state init skipped (mocked environment)")

    def render(
        self,
        modes: list[dict[str, Any]] | None = None,
        columns: int = 3,
        use_container_width: bool = True,
    ) -> InputMode:
        """Render the mode switcher interface.

        Args:
            modes: List of mode configurations with keys: id, label, icon, description
            columns: Number of columns for button layout
            use_container_width: Whether buttons should use full container width

        Returns:
            Currently selected mode
        """
        if modes is None:
            modes = [
                {
                    "id": "vision",
                    "label": "Vision Mode",
                    "icon": "📷",
                    "description": "Upload plant images for disease detection",
                },
                {
                    "id": "audio",
                    "label": "Audio Mode",
                    "icon": "🎤",
                    "description": "Record voice questions about plant care",
                },
                {
                    "id": "text",
                    "label": "Text Mode",
                    "icon": "💬",
                    "description": "Chat with AI about plant diseases",
                },
            ]

        st.markdown("### 🔄 Input Mode")

        # Create columns for buttons
        cols = st.columns(columns)
        current_mode = st.session_state[self.session_key]

        for i, mode in enumerate(modes):
            col_index = i % columns
            with cols[col_index]:
                button_type = "primary" if current_mode == mode["id"] else "secondary"
                button_label = f"{mode['icon']} {mode['label']}"

                button_type_literal = "primary" if current_mode == mode["id"] else "secondary"
                if st.button(
                    button_label,
                    key=f"mode_btn_{mode['id']}",
                    use_container_width=use_container_width,
                    type=button_type_literal,
                    help=mode.get("description", ""),
                ):
                    st.session_state[self.session_key] = mode["id"]
                    st.rerun()

        return st.session_state[self.session_key]  # type: ignore

    def get_current_mode(self) -> InputMode:
        """Get the currently selected mode."""
        try:
            _st = _get_st()
            state = getattr(_st, "session_state", None)
            # If tests patched session_state to a dict
            if isinstance(state, dict):
                return state.get(self.session_key, self.default_mode)  # type: ignore[return-value]
            # For real Streamlit SessionState (mapping-like with .get)
            return _st.session_state.get(self.session_key, self.default_mode)  # type: ignore[return-value, attr-defined]
        except Exception:
            # When streamlit is a MagicMock without a proper mapping interface
            return self.default_mode

    def set_mode(self, mode: InputMode) -> None:
        """Programmatically set the current mode."""
        try:
            _st = _get_st()
            state = getattr(_st, "session_state", None)
            if isinstance(state, dict):
                state[self.session_key] = mode  # type: ignore[index]
            else:
                _st.session_state[self.session_key] = mode  # type: ignore[index]
        except Exception:
            # Silently ignore in mocked environments
            logger.debug("ModeSwitcher: set_mode skipped (mocked environment)")


class ThemeSwitcher:
    """Theme switcher component for UI customization."""

    def __init__(self, session_key: str = "theme_mode", default_theme: ThemeMode = "auto"):
        """Initialize the theme switcher.

        Args:
            session_key: Session state key for storing the selected theme
            default_theme: Default theme to select
        """
        self.session_key = session_key
        self.default_theme = default_theme

        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = default_theme

    def render(self, location: str = "sidebar") -> ThemeMode:
        """Render the theme switcher.

        Args:
            location: Where to render ("sidebar", "main", "expander")

        Returns:
            Currently selected theme
        """
        themes = {"light": "☀️ Light", "dark": "🌙 Dark", "auto": "🔄 Auto"}

        if location == "sidebar":
            with st.sidebar:
                selected = st.selectbox(
                    "Theme",
                    options=list(themes.keys()),
                    format_func=lambda x: themes[x],
                    index=list(themes.keys()).index(st.session_state[self.session_key]),
                )
        elif location == "expander":
            with st.expander("🎨 Theme Settings"):
                selected = st.radio(
                    "Select Theme",
                    options=list(themes.keys()),
                    format_func=lambda x: themes[x],
                    index=list(themes.keys()).index(st.session_state[self.session_key]),
                    horizontal=True,
                )
        else:  # main
            selected = st.selectbox(
                "🎨 Theme",
                options=list(themes.keys()),
                format_func=lambda x: themes[x],
                index=list(themes.keys()).index(st.session_state[self.session_key]),
            )

        if selected != st.session_state[self.session_key]:
            st.session_state[self.session_key] = selected
            st.rerun()

        return selected  # type: ignore


class ModelSwitcher:
    """Model switcher for switching between different trained models."""

    def __init__(self, session_key: str = "selected_models"):
        """Initialize the model switcher.

        Args:
            session_key: Session state key for storing selected models
        """
        self.session_key = session_key

        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                "vision": "resnet50_plantvillage_v1",
                "audio": "whisper_tiny_local",
                "text": "distilbert_plant_qa_v1",
            }

    def render(self, available_models: dict[str, list[str]]) -> dict[str, str]:
        """Render enhanced model selection interface with improved dropdowns.

        Args:
            available_models: Dict mapping model type to list of available models

        Returns:
            Dict of selected models for each type
        """
        # Enhanced CSS for better dropdown styling
        st.markdown(
            """
        <style>
        .model-dropdown-container {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 1rem;
            border-radius: 12px;
            border: 2px solid #dee2e6;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }

        .model-dropdown-container:hover {
            border-color: #4CAF50;
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15);
        }

        .model-type-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #2c3e50;
        }

        .model-icon {
            font-size: 1.2em;
            margin-right: 0.5rem;
        }

        .model-description {
            font-size: 0.85em;
            color: #6c757d;
            margin-bottom: 0.5rem;
            font-style: italic;
        }

        /* Custom selectbox styling */
        .stSelectbox > div > div {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            transition: all 0.2s ease;
        }

        .stSelectbox > div > div:hover {
            border-color: #4CAF50;
        }

        .stSelectbox > div > div:focus-within {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 🤖 Advanced Model Selection")
        st.markdown("*Choose the best AI models for your plant analysis needs*")

        current_selection = st.session_state[self.session_key]

        # Model configurations with metadata
        model_configs = {
            "vision": {
                "icon": "👁️",
                "title": "Vision Model",
                "description": "AI model for plant image analysis",
                "models": {"vit_base_plants": "🏆 Vision Transformer (Best Accuracy)", "resnet50_plantvillage_v1": "🔬 ResNet50 (Balanced)", "mobilenet_fast": "⚡ MobileNet (Fastest)"},
            },
            "audio": {
                "icon": "🎤",
                "title": "Audio Model",
                "description": "AI model for voice and audio processing",
                "models": {"whisper_tiny_local": "🎯 Whisper Tiny (Local)", "wav2vec2_plant_sounds": "🌿 Wav2Vec2 (Plant Sounds)"},
            },
            "text": {
                "icon": "💬",
                "title": "Text Model",
                "description": "AI model for plant care questions",
                "models": {"distilbert_plant_qa_v1": "🧠 DistilBERT (Plant Q&A)", "roberta_plant_care": "🌱 RoBERTa (Plant Care)", "t5_small_plant_qa": "📝 T5 Small (Text Generation)"},
            },
        }

        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]

        selected_models = {}

        for i, (model_type, config) in enumerate(model_configs.items()):
            with columns[i]:
                # Enhanced model container
                st.markdown(
                    f"""
                <div class="model-dropdown-container">
                    <div class="model-type-header">
                        <span class="model-icon">{config["icon"]}</span>
                        <strong>{config["title"]}</strong>
                    </div>
                    <div class="model-description">{config["description"]}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Get available models for this type
                available_for_type = available_models.get(model_type, list(config["models"].keys()))
                current_model = current_selection.get(model_type, available_for_type[0])

                # Create display options with enhanced formatting
                display_options = []
                model_keys = []

                for model_key in available_for_type:
                    display_name = config["models"].get(model_key, model_key)
                    display_options.append(display_name)
                    model_keys.append(model_key)

                # Find current index
                current_index = 0
                if current_model in model_keys:
                    current_index = model_keys.index(current_model)

                # Enhanced selectbox
                selected_display = st.selectbox(
                    f"{config['icon']} {config['title']}",
                    options=display_options,
                    index=current_index,
                    key=f"{model_type}_model_select",
                    help=f"Select the {config['title'].lower()} for {config['description'].lower()}",
                    label_visibility="collapsed",
                )

                # Map back to model key
                selected_key = model_keys[display_options.index(selected_display)]
                selected_models[model_type] = selected_key

                # Model performance indicator
                performance_indicators = {
                    "vit_base_plants": ("🏆", "100%", "#4CAF50"),
                    "resnet50_plantvillage_v1": ("🔬", "95%", "#2196F3"),
                    "mobilenet_fast": ("⚡", "90%", "#FF9800"),
                    "whisper_tiny_local": ("🎯", "Local", "#4CAF50"),
                    "wav2vec2_plant_sounds": ("🌿", "Beta", "#FF9800"),
                    "distilbert_plant_qa_v1": ("🧠", "Stable", "#4CAF50"),
                    "roberta_plant_care": ("🌱", "Advanced", "#2196F3"),
                    "t5_small_plant_qa": ("📝", "Creative", "#9C27B0"),
                }

                if selected_key in performance_indicators:
                    icon, metric, color = performance_indicators[selected_key]
                    st.markdown(
                        f"""
                    <div style="text-align: center; margin-top: 0.5rem;">
                        <span style="color: {color}; font-weight: bold;">
                            {icon} {metric}
                        </span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Update session state with new selections
        if selected_models != current_selection:
            st.session_state[self.session_key] = selected_models

            # Enhanced notification with model details
            st.markdown(
                """
            <div style="background: linear-gradient(90deg, #4CAF50, #45a049);
                        color: white; padding: 1rem; border-radius: 8px;
                        text-align: center; margin: 1rem 0;">
                <strong>🔄 Model Configuration Updated!</strong><br>
                <small>New models will be loaded on next inference</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Show what changed
            changes = []
            for model_type, new_model in selected_models.items():
                old_model = current_selection.get(model_type, "")
                if new_model != old_model:
                    changes.append(f"**{model_type.title()}**: {old_model} → {new_model}")

            if changes:
                with st.expander("📋 View Changes", expanded=False):
                    for change in changes:
                        st.markdown(f"• {change}")

        return selected_models


def render_status_indicator(status: str, label: str = "") -> None:
    """Render a status indicator with appropriate styling.

    Args:
        status: Status value ("loaded", "loading", "error", "not_loaded")
        label: Optional label to display
    """
    status_config = {
        "loaded": {"icon": "✅", "color": "green"},
        "loading": {"icon": "⏳", "color": "orange"},
        "error": {"icon": "❌", "color": "red"},
        "not_loaded": {"icon": "⚪", "color": "gray"},
    }

    config = status_config.get(status, status_config["not_loaded"])

    if label:
        st.markdown(f"{config['icon']} **{label}**: {status}")
    else:
        st.markdown(f"{config['icon']} {status}")


def render_progress_bar(progress: float, label: str = "") -> None:
    """Render a progress bar with label.

    Args:
        progress: Progress value between 0.0 and 1.0
        label: Optional label to display above the progress bar
    """
    if label:
        st.markdown(f"**{label}**")

    st.progress(progress)
    st.markdown(f"{progress:.1%} complete")
