"""
Mobile Settings Card Component for PlantGuard UI.

This module provides a mobile-optimized settings card component with
inline settings display, model switching interface, theme and accessibility
settings, and settings persistence and restoration.
"""

import json
import logging
from datetime import datetime
from typing import Any

import streamlit as st

from .mobile_state_manager import MobileStateManager
from .model_switcher import ModelSwitcher

logger = logging.getLogger(__name__)


class MobileSettingsCard:
    """Mobile-optimized settings card component."""

    def __init__(self, component_id: str, title: str = "Settings"):
        """Initialize mobile settings card component.

        Args:
            component_id: Unique identifier for the component
            title: Display title for the component
        """
        self.component_id = component_id
        self.title = title
        self.state_manager = MobileStateManager()
        self.model_switcher = ModelSwitcher()
        self._initialize_settings_state()

    def _initialize_settings_state(self) -> None:
        """Initialize settings-specific state."""
        # Initialize user preferences if not exists
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = self._get_default_preferences()

        # Initialize settings card state
        state = self.state_manager.get_component_state(self.component_id)
        if "settings_card" not in state["data"]:
            state["data"]["settings_card"] = {
                "active_section": "models",  # 'models', 'appearance', 'accessibility', 'advanced'
                "expanded_sections": ["models"],
                "settings_changed": False,
                "last_saved": None,
                "backup_preferences": None,
            }
            self.state_manager.set_component_state(self.component_id, state)

    def _get_default_preferences(self) -> dict[str, Any]:
        """Get default user preferences."""
        return {
            # Appearance settings
            "theme": "auto",  # 'light', 'dark', 'auto'
            "color_scheme": "green",  # 'green', 'blue', 'purple'
            "font_size": "medium",  # 'small', 'medium', 'large', 'extra_large'
            "compact_mode": False,
            "animations_enabled": True,
            # Accessibility settings
            "high_contrast": False,
            "reduce_motion": False,
            "screen_reader_mode": False,
            "voice_feedback": False,
            "large_touch_targets": False,
            # Functionality settings
            "auto_analysis": False,
            "save_history": True,
            "notifications_enabled": True,
            "sound_enabled": True,
            "haptic_feedback": True,
            # Privacy settings
            "analytics_enabled": False,
            "crash_reporting": True,
            "data_sharing": False,
            # Advanced settings
            "developer_mode": False,
            "debug_logging": False,
            "performance_mode": "balanced",  # 'performance', 'balanced', 'battery'
            "cache_size": "medium",  # 'small', 'medium', 'large'
            # Model preferences
            "preferred_vision_model": "resnet50_plantvillage_v1",
            "preferred_audio_model": "whisper_tiny_local",
            "preferred_text_model": "distilbert_plant_qa_v1",
            "auto_model_switching": False,
            # Backup and sync
            "auto_backup": False,
            "backup_frequency": "weekly",  # 'daily', 'weekly', 'monthly'
            "sync_across_devices": False,
        }

    def get_mobile_css(self) -> str:
        """Get mobile-specific CSS for settings card."""
        return """
        <style>
        .mobile-settings-card {
            background: white;
            border-radius: 12px;
            padding: 0;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .mobile-settings-header {
            background: linear-gradient(135deg, #16a34a, #22c55e);
            color: white;
            padding: 16px;
            margin: 0;
        }

        .mobile-settings-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
        }

        .mobile-settings-subtitle {
            font-size: 14px;
            opacity: 0.9;
            margin: 4px 0 0 0;
        }

        .mobile-settings-content {
            padding: 0;
        }

        .mobile-settings-section {
            border-bottom: 1px solid #e5e7eb;
        }

        .mobile-settings-section:last-child {
            border-bottom: none;
        }

        .mobile-settings-section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px;
            background: #f9fafb;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }

        .mobile-settings-section-header:hover {
            background: #f3f4f6;
        }

        .mobile-settings-section-header.active {
            background: #ecfdf5;
            border-left: 4px solid #16a34a;
        }

        .mobile-settings-section-title {
            font-weight: 600;
            font-size: 16px;
            color: #1f2937;
            margin: 0;
        }

        .mobile-settings-section-icon {
            font-size: 18px;
            margin-right: 12px;
        }

        .mobile-settings-section-toggle {
            font-size: 14px;
            color: #6b7280;
        }

        .mobile-settings-section-body {
            padding: 16px;
            background: white;
        }

        .mobile-settings-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f3f4f6;
        }

        .mobile-settings-item:last-child {
            border-bottom: none;
        }

        .mobile-settings-item-info {
            flex: 1;
        }

        .mobile-settings-item-title {
            font-weight: 500;
            font-size: 14px;
            color: #1f2937;
            margin: 0 0 4px 0;
        }

        .mobile-settings-item-description {
            font-size: 12px;
            color: #6b7280;
            margin: 0;
        }

        .mobile-settings-item-control {
            margin-left: 16px;
        }

        .mobile-settings-toggle {
            position: relative;
            width: 44px;
            height: 24px;
            background: #d1d5db;
            border-radius: 12px;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }

        .mobile-settings-toggle.active {
            background: #16a34a;
        }

        .mobile-settings-toggle-handle {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            transition: transform 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }

        .mobile-settings-toggle.active .mobile-settings-toggle-handle {
            transform: translateX(20px);
        }

        .mobile-settings-select {
            min-width: 120px;
            padding: 6px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background: white;
            font-size: 14px;
        }

        .mobile-settings-model-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
        }

        .mobile-settings-model-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .mobile-settings-model-name {
            font-weight: 600;
            font-size: 14px;
            color: #1e293b;
        }

        .mobile-settings-model-accuracy {
            font-size: 12px;
            color: #16a34a;
            font-weight: 500;
        }

        .mobile-settings-model-description {
            font-size: 12px;
            color: #64748b;
            margin-bottom: 8px;
        }

        .mobile-settings-model-metrics {
            display: flex;
            gap: 12px;
        }

        .mobile-settings-model-metric {
            font-size: 11px;
            color: #64748b;
        }

        .mobile-settings-actions {
            padding: 16px;
            background: #f9fafb;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 8px;
        }

        .mobile-settings-action-btn {
            flex: 1;
            padding: 10px 16px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            background: white;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }

        .mobile-settings-action-btn.primary {
            background: #16a34a;
            color: white;
            border-color: #16a34a;
        }

        .mobile-settings-action-btn.secondary {
            background: #6b7280;
            color: white;
            border-color: #6b7280;
        }

        .mobile-settings-action-btn:hover {
            opacity: 0.9;
        }

        .mobile-settings-status {
            padding: 12px 16px;
            background: #ecfdf5;
            border-left: 4px solid #16a34a;
            margin: 16px;
            border-radius: 0 8px 8px 0;
        }

        .mobile-settings-status.warning {
            background: #fef3c7;
            border-left-color: #f59e0b;
        }

        .mobile-settings-status.error {
            background: #fee2e2;
            border-left-color: #dc2626;
        }

        @media (max-width: 480px) {
            .mobile-settings-header {
                padding: 12px;
            }

            .mobile-settings-section-header {
                padding: 12px;
            }

            .mobile-settings-section-body {
                padding: 12px;
            }

            .mobile-settings-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }

            .mobile-settings-item-control {
                margin-left: 0;
                align-self: flex-end;
            }

            .mobile-settings-actions {
                flex-direction: column;
            }
        }
        </style>
        """

    def render_section_header(self, section_id: str, title: str, icon: str, is_expanded: bool) -> bool:
        """Render section header and return if it should be expanded."""
        state = self.state_manager.get_component_state(self.component_id)
        settings_data = state["data"]["settings_card"]

        header_class = "mobile-settings-section-header"
        if settings_data["active_section"] == section_id:
            header_class += " active"

        toggle_icon = "▼" if is_expanded else "▶"

        if st.button(f"{icon} {title}", key=f"{self.component_id}_section_{section_id}", use_container_width=True, help=f"Toggle {title} section"):
            # Toggle section expansion
            if section_id in settings_data["expanded_sections"]:
                settings_data["expanded_sections"].remove(section_id)
            else:
                settings_data["expanded_sections"].append(section_id)

            settings_data["active_section"] = section_id
            state["data"]["settings_card"] = settings_data
            self.state_manager.set_component_state(self.component_id, state)
            st.rerun()

        return section_id in settings_data["expanded_sections"]

    def render_toggle_setting(self, key: str, title: str, description: str, section: str = "general") -> None:
        """Render a toggle setting."""
        current_value = st.session_state.user_preferences.get(key, False)

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(
                f"""
            <div class="mobile-settings-item-info">
                <div class="mobile-settings-item-title">{title}</div>
                <div class="mobile-settings-item-description">{description}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            new_value = st.checkbox("", value=current_value, key=f"{self.component_id}_{key}", label_visibility="collapsed")

            if new_value != current_value:
                st.session_state.user_preferences[key] = new_value
                self._mark_settings_changed()

    def render_select_setting(self, key: str, title: str, description: str, options: list[str], labels: list[str] | None = None) -> None:
        """Render a select setting."""
        current_value = st.session_state.user_preferences.get(key, options[0] if options else "")
        display_labels = labels or options

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(
                f"""
            <div class="mobile-settings-item-info">
                <div class="mobile-settings-item-title">{title}</div>
                <div class="mobile-settings-item-description">{description}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            try:
                current_index = options.index(current_value) if current_value in options else 0
            except ValueError:
                current_index = 0

            new_value = st.selectbox(
                "",
                options=options,
                format_func=lambda x: display_labels[options.index(x)] if labels else x,
                index=current_index,
                key=f"{self.component_id}_{key}",
                label_visibility="collapsed",
            )

            if new_value != current_value:
                st.session_state.user_preferences[key] = new_value
                self._mark_settings_changed()

    def render_model_section(self) -> None:
        """Render model switching section."""
        st.markdown("### 🤖 AI Models")

        # Vision model
        st.markdown("#### 👁️ Vision Model")
        available_vision = self.model_switcher.get_available_models("vision")
        current_vision = self.model_switcher.get_current_model("vision")

        for model_id, model_info in available_vision.items():
            is_selected = model_id == current_vision

            card_style = "mobile-settings-model-card"
            if is_selected:
                card_style += " selected"

            st.markdown(
                f'''
            <div class="{card_style}">
                <div class="mobile-settings-model-header">
                    <div class="mobile-settings-model-name">{model_info.get("name", model_id)}</div>
                    <div class="mobile-settings-model-accuracy">{model_info.get("accuracy", 0)}%</div>
                </div>
                <div class="mobile-settings-model-description">{model_info.get("description", "")}</div>
                <div class="mobile-settings-model-metrics">
                    <span class="mobile-settings-model-metric">Speed: {model_info.get("speed", "N/A")}</span>
                    <span class="mobile-settings-model-metric">Memory: {model_info.get("memory", "N/A")}</span>
                </div>
            </div>
            ''',
                unsafe_allow_html=True,
            )

            if st.button(
                "✅ Selected" if is_selected else "Select",
                key=f"{self.component_id}_vision_{model_id}",
                disabled=is_selected,
                use_container_width=True,
            ):
                self.model_switcher.set_model("vision", model_id)
                st.session_state.user_preferences["preferred_vision_model"] = model_id
                self._mark_settings_changed()
                st.toast(f"Vision model changed to {model_info.get('name', model_id)}", icon="👁️")
                st.rerun()

        # Audio model
        st.markdown("#### 🎤 Audio Model")
        available_audio = self.model_switcher.get_available_models("audio")
        current_audio = self.model_switcher.get_current_model("audio")

        for model_id, model_info in available_audio.items():
            is_selected = model_id == current_audio

            st.markdown(
                f"""
            <div class="mobile-settings-model-card">
                <div class="mobile-settings-model-header">
                    <div class="mobile-settings-model-name">{model_info.get("name", model_id)}</div>
                    <div class="mobile-settings-model-accuracy">{model_info.get("accuracy", 0)}%</div>
                </div>
                <div class="mobile-settings-model-description">{model_info.get("description", "")}</div>
                <div class="mobile-settings-model-metrics">
                    <span class="mobile-settings-model-metric">Speed: {model_info.get("speed", "N/A")}</span>
                    <span class="mobile-settings-model-metric">Memory: {model_info.get("memory", "N/A")}</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button(
                "✅ Selected" if is_selected else "Select",
                key=f"{self.component_id}_audio_{model_id}",
                disabled=is_selected,
                use_container_width=True,
            ):
                self.model_switcher.set_model("audio", model_id)
                st.session_state.user_preferences["preferred_audio_model"] = model_id
                self._mark_settings_changed()
                st.toast(f"Audio model changed to {model_info.get('name', model_id)}", icon="🎤")
                st.rerun()

        # Text model
        st.markdown("#### 💬 Text Model")
        available_text = self.model_switcher.get_available_models("text")
        current_text = self.model_switcher.get_current_model("text")

        for model_id, model_info in available_text.items():
            is_selected = model_id == current_text

            st.markdown(
                f"""
            <div class="mobile-settings-model-card">
                <div class="mobile-settings-model-header">
                    <div class="mobile-settings-model-name">{model_info.get("name", model_id)}</div>
                    <div class="mobile-settings-model-accuracy">{model_info.get("accuracy", 0)}%</div>
                </div>
                <div class="mobile-settings-model-description">{model_info.get("description", "")}</div>
                <div class="mobile-settings-model-metrics">
                    <span class="mobile-settings-model-metric">Speed: {model_info.get("speed", "N/A")}</span>
                    <span class="mobile-settings-model-metric">Memory: {model_info.get("memory", "N/A")}</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button(
                "✅ Selected" if is_selected else "Select", key=f"{self.component_id}_text_{model_id}", disabled=is_selected, use_container_width=True
            ):
                self.model_switcher.set_model("text", model_id)
                st.session_state.user_preferences["preferred_text_model"] = model_id
                self._mark_settings_changed()
                st.toast(f"Text model changed to {model_info.get('name', model_id)}", icon="💬")
                st.rerun()

        # Auto model switching
        self.render_toggle_setting("auto_model_switching", "Auto Model Switching", "Automatically switch to optimal models based on analysis type")

    def render_appearance_section(self) -> None:
        """Render appearance settings section."""
        st.markdown("### 🎨 Appearance")

        # Theme setting
        self.render_select_setting(
            "theme", "Theme", "Choose your preferred color theme", ["auto", "light", "dark"], ["Auto (System)", "Light", "Dark"]
        )

        # Color scheme
        self.render_select_setting(
            "color_scheme",
            "Color Scheme",
            "Select the accent color for the interface",
            ["green", "blue", "purple"],
            ["Green (Default)", "Blue", "Purple"],
        )

        # Font size
        self.render_select_setting(
            "font_size",
            "Font Size",
            "Adjust text size for better readability",
            ["small", "medium", "large", "extra_large"],
            ["Small", "Medium", "Large", "Extra Large"],
        )

        # Compact mode
        self.render_toggle_setting("compact_mode", "Compact Mode", "Use smaller spacing and components to fit more content")

        # Animations
        self.render_toggle_setting("animations_enabled", "Animations", "Enable smooth transitions and animations")

    def render_accessibility_section(self) -> None:
        """Render accessibility settings section."""
        st.markdown("### ♿ Accessibility")

        # High contrast
        self.render_toggle_setting("high_contrast", "High Contrast", "Increase contrast for better visibility")

        # Reduce motion
        self.render_toggle_setting("reduce_motion", "Reduce Motion", "Minimize animations and transitions")

        # Screen reader mode
        self.render_toggle_setting("screen_reader_mode", "Screen Reader Mode", "Optimize interface for screen readers")

        # Voice feedback
        self.render_toggle_setting("voice_feedback", "Voice Feedback", "Provide audio feedback for actions")

        # Large touch targets
        self.render_toggle_setting("large_touch_targets", "Large Touch Targets", "Make buttons and controls larger for easier tapping")

    def render_functionality_section(self) -> None:
        """Render functionality settings section."""
        st.markdown("### ⚙️ Functionality")

        # Auto analysis
        self.render_toggle_setting("auto_analysis", "Auto Analysis", "Automatically analyze images when uploaded")

        # Save history
        self.render_toggle_setting("save_history", "Save History", "Keep a record of your plant analyses")

        # Notifications
        self.render_toggle_setting("notifications_enabled", "Notifications", "Show notifications for analysis results and updates")

        # Sound
        self.render_toggle_setting("sound_enabled", "Sound Effects", "Play sounds for actions and notifications")

        # Haptic feedback
        self.render_toggle_setting("haptic_feedback", "Haptic Feedback", "Vibrate on touch interactions (mobile devices)")

    def render_advanced_section(self) -> None:
        """Render advanced settings section."""
        st.markdown("### 🔧 Advanced")

        # Performance mode
        self.render_select_setting(
            "performance_mode",
            "Performance Mode",
            "Balance between performance and battery life",
            ["performance", "balanced", "battery"],
            ["High Performance", "Balanced", "Battery Saver"],
        )

        # Cache size
        self.render_select_setting(
            "cache_size",
            "Cache Size",
            "Amount of data to cache for offline use",
            ["small", "medium", "large"],
            ["Small (50MB)", "Medium (200MB)", "Large (500MB)"],
        )

        # Developer mode
        self.render_toggle_setting("developer_mode", "Developer Mode", "Enable advanced debugging features")

        # Debug logging
        self.render_toggle_setting("debug_logging", "Debug Logging", "Enable detailed logging for troubleshooting")

        # Analytics
        self.render_toggle_setting("analytics_enabled", "Usage Analytics", "Help improve the app by sharing anonymous usage data")

        # Crash reporting
        self.render_toggle_setting("crash_reporting", "Crash Reporting", "Automatically report crashes to help fix bugs")

    def _mark_settings_changed(self) -> None:
        """Mark settings as changed."""
        state = self.state_manager.get_component_state(self.component_id)
        state["data"]["settings_card"]["settings_changed"] = True
        self.state_manager.set_component_state(self.component_id, state)

    def _save_settings(self) -> None:
        """Save current settings."""
        try:
            # Save to session state (already done automatically)
            # Could also save to local storage or file here

            state = self.state_manager.get_component_state(self.component_id)
            state["data"]["settings_card"]["settings_changed"] = False
            state["data"]["settings_card"]["last_saved"] = datetime.now().isoformat()
            self.state_manager.set_component_state(self.component_id, state)

            st.toast("Settings saved successfully!", icon="💾")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            st.toast("Failed to save settings", icon="❌")

    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        try:
            # Backup current settings
            state = self.state_manager.get_component_state(self.component_id)
            state["data"]["settings_card"]["backup_preferences"] = st.session_state.user_preferences.copy()

            # Reset to defaults
            st.session_state.user_preferences = self._get_default_preferences()

            # Reset model selections
            self.model_switcher.reset_to_defaults()

            # Mark as changed
            self._mark_settings_changed()

            st.toast("Settings reset to defaults!", icon="🔄")
            st.rerun()

        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            st.toast("Failed to reset settings", icon="❌")

    def _export_settings(self) -> str:
        """Export settings as JSON."""
        try:
            export_data = {
                "user_preferences": st.session_state.user_preferences,
                "model_configuration": self.model_switcher.export_configuration(),
                "export_timestamp": datetime.now().isoformat(),
                "app_version": "1.0.0",
            }

            return json.dumps(export_data, indent=2)

        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return "{}"

    def _import_settings(self, settings_json: str) -> bool:
        """Import settings from JSON."""
        try:
            import_data = json.loads(settings_json)

            # Validate structure
            if "user_preferences" not in import_data:
                st.error("Invalid settings file: missing user preferences")
                return False

            # Import user preferences
            imported_prefs = import_data["user_preferences"]
            default_prefs = self._get_default_preferences()

            # Merge with defaults to ensure all keys exist
            for key, default_value in default_prefs.items():
                if key not in imported_prefs:
                    imported_prefs[key] = default_value

            st.session_state.user_preferences = imported_prefs

            # Import model configuration if available
            if "model_configuration" in import_data:
                self.model_switcher.import_configuration(import_data["model_configuration"])

            self._mark_settings_changed()
            st.toast("Settings imported successfully!", icon="📥")
            st.rerun()
            return True

        except json.JSONDecodeError:
            st.error("Invalid JSON format in settings file")
            return False
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            st.error(f"Failed to import settings: {e}")
            return False

    def render(self) -> None:
        """Render the mobile settings card component."""
        try:
            # Apply mobile CSS
            st.markdown(self.get_mobile_css(), unsafe_allow_html=True)

            # Main container
            with st.container():
                st.markdown('<div class="mobile-settings-card">', unsafe_allow_html=True)

                # Header
                st.markdown(
                    f"""
                <div class="mobile-settings-header">
                    <div class="mobile-settings-title">⚙️ {self.title}</div>
                    <div class="mobile-settings-subtitle">Customize your PlantGuard experience</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Content sections
                st.markdown('<div class="mobile-settings-content">', unsafe_allow_html=True)

                state = self.state_manager.get_component_state(self.component_id)
                settings_data = state["data"]["settings_card"]

                # Model section
                if self.render_section_header("models", "AI Models", "🤖", "models" in settings_data["expanded_sections"]):
                    with st.container():
                        self.render_model_section()

                # Appearance section
                if self.render_section_header("appearance", "Appearance", "🎨", "appearance" in settings_data["expanded_sections"]):
                    with st.container():
                        self.render_appearance_section()

                # Accessibility section
                if self.render_section_header("accessibility", "Accessibility", "♿", "accessibility" in settings_data["expanded_sections"]):
                    with st.container():
                        self.render_accessibility_section()

                # Functionality section
                if self.render_section_header("functionality", "Functionality", "⚙️", "functionality" in settings_data["expanded_sections"]):
                    with st.container():
                        self.render_functionality_section()

                # Advanced section
                if self.render_section_header("advanced", "Advanced", "🔧", "advanced" in settings_data["expanded_sections"]):
                    with st.container():
                        self.render_advanced_section()

                st.markdown("</div>", unsafe_allow_html=True)

                # Actions footer
                st.markdown('<div class="mobile-settings-actions">', unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("💾 Save", key=f"{self.component_id}_save", use_container_width=True):
                        self._save_settings()

                with col2:
                    if st.button("🔄 Reset", key=f"{self.component_id}_reset", use_container_width=True):
                        self._reset_settings()

                with col3, st.expander("📤 Export/Import"):
                    # Export
                    if st.button("📤 Export Settings", key=f"{self.component_id}_export", use_container_width=True):
                        settings_json = self._export_settings()
                        st.download_button(
                            "💾 Download Settings",
                            data=settings_json,
                            file_name=f"plantguard_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key=f"{self.component_id}_download",
                            use_container_width=True,
                        )

                    # Import
                    uploaded_file = st.file_uploader(
                        "📥 Import Settings", type=["json"], key=f"{self.component_id}_import", help="Upload a previously exported settings file"
                    )

                    if uploaded_file is not None:
                        try:
                            settings_content = uploaded_file.read().decode("utf-8")
                            if st.button("📥 Apply Imported Settings", key=f"{self.component_id}_apply_import", use_container_width=True):
                                self._import_settings(settings_content)
                        except Exception as e:
                            st.error(f"Error reading settings file: {e}")

                st.markdown("</div>", unsafe_allow_html=True)

                # Status indicator
                if settings_data["settings_changed"]:
                    st.markdown(
                        """
                    <div class="mobile-settings-status warning">
                        ⚠️ You have unsaved changes. Don't forget to save your settings!
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                elif settings_data["last_saved"]:
                    with suppress(Exception):
                        last_saved = datetime.fromisoformat(settings_data["last_saved"])
                        time_str = last_saved.strftime("%H:%M")
                        st.markdown(
                            f"""
                        <div class="mobile-settings-status">
                            ✅ Settings saved at {time_str}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                st.markdown("</div>", unsafe_allow_html=True)

                # Update component state
                state = self.state_manager.get_component_state(self.component_id)
                state["ui_state"]["loading"] = False
                state["error"] = None
                self.state_manager.set_component_state(self.component_id, state)

        except Exception as e:
            logger.error(f"Error rendering mobile settings card: {e}")
            self.state_manager.set_error_state(
                self.component_id, str(e), "rendering_error", ["Check browser console", "Refresh the page", "Reset settings to defaults"]
            )
            st.error(f"Error displaying settings: {e}")

    def get_current_preferences(self) -> dict[str, Any]:
        """Get current user preferences."""
        return st.session_state.user_preferences.copy()

    def update_preference(self, key: str, value: Any) -> None:
        """Update a specific preference."""
        st.session_state.user_preferences[key] = value
        self._mark_settings_changed()

    def get_settings_summary(self) -> dict[str, Any]:
        """Get summary of current settings."""
        prefs = st.session_state.user_preferences
        models = self.model_switcher.export_configuration()

        return {
            "theme": prefs.get("theme", "auto"),
            "accessibility_features": sum(
                [
                    prefs.get("high_contrast", False),
                    prefs.get("large_touch_targets", False),
                    prefs.get("screen_reader_mode", False),
                    prefs.get("voice_feedback", False),
                ]
            ),
            "current_models": {
                "vision": self.model_switcher.get_current_model("vision"),
                "audio": self.model_switcher.get_current_model("audio"),
                "text": self.model_switcher.get_current_model("text"),
            },
            "performance_mode": prefs.get("performance_mode", "balanced"),
            "privacy_settings": {
                "analytics": prefs.get("analytics_enabled", False),
                "crash_reporting": prefs.get("crash_reporting", True),
                "data_sharing": prefs.get("data_sharing", False),
            },
        }
