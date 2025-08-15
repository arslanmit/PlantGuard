"""Reusable UI components for PlantGuard."""

import logging
from typing import Any, Literal

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
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = default_mode

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

                if st.button(
                    button_label,
                    key=f"mode_btn_{mode['id']}",
                    use_container_width=use_container_width,
                    type=button_type,
                    help=mode.get("description", ""),
                ):
                    st.session_state[self.session_key] = mode["id"]
                    st.rerun()

        return st.session_state[self.session_key]

    def get_current_mode(self) -> InputMode:
        """Get the currently selected mode."""
        return st.session_state.get(self.session_key, self.default_mode)

    def set_mode(self, mode: InputMode) -> None:
        """Programmatically set the current mode."""
        st.session_state[self.session_key] = mode


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

        return selected


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
        """Render model selection interface.

        Args:
            available_models: Dict mapping model type to list of available models

        Returns:
            Dict of selected models for each type
        """
        st.markdown("#### 🤖 Model Selection")

        current_selection = st.session_state[self.session_key]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Vision Model**")
            vision_models = available_models.get("vision", ["resnet50_plantvillage_v1"])
            current_vision = current_selection.get("vision", vision_models[0])

            selected_vision = st.selectbox(
                "Vision",
                options=vision_models,
                index=vision_models.index(current_vision) if current_vision in vision_models else 0,
                key="vision_model_select",
                label_visibility="collapsed",
            )

        with col2:
            st.markdown("**Audio Model**")
            audio_models = available_models.get("audio", ["whisper_tiny_local"])
            current_audio = current_selection.get("audio", audio_models[0])

            selected_audio = st.selectbox(
                "Audio",
                options=audio_models,
                index=audio_models.index(current_audio) if current_audio in audio_models else 0,
                key="audio_model_select",
                label_visibility="collapsed",
            )

        with col3:
            st.markdown("**Text Model**")
            text_models = available_models.get("text", ["distilbert_plant_qa_v1"])
            current_text = current_selection.get("text", text_models[0])

            selected_text = st.selectbox(
                "Text",
                options=text_models,
                index=text_models.index(current_text) if current_text in text_models else 0,
                key="text_model_select",
                label_visibility="collapsed",
            )

        # Update session state
        new_selection = {"vision": selected_vision, "audio": selected_audio, "text": selected_text}

        if new_selection != current_selection:
            st.session_state[self.session_key] = new_selection
            st.info("🔄 Model selection updated. Models will reload on next inference.")

        return new_selection


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
