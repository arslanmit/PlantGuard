"""Input Ribbon Component for PlantGuard Redesigned UI.

Provides unified access to all input modalities (Text, Voice, Camera, Upload)
with clear visual hierarchy and responsive design.
"""

import contextlib
import logging
from pathlib import Path
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class InputRibbon:
    """Input ribbon component with multimodal input support."""

    def __init__(self) -> None:
        self.input_modes = {
            "text": {
                "icon": "⌨️",
                "label": "Text",
                "description": "Type your questions about plant diseases",
                "color": "#22C55E",
                "shortcut": "T",
                "supports_multiple": True,
            },
            "voice": {
                "icon": "[MICROPHONE]️",
                "label": "Voice",
                "description": "Record voice questions or describe symptoms",
                "color": "#10B981",
                "shortcut": "V",
                "supports_multiple": True,
            },
            "camera": {
                "icon": "[CAMERA]",
                "label": "Camera",
                "description": "Take photos directly with your device camera",
                "color": "#0EA5E9",
                "shortcut": "C",
                "supports_multiple": False,
            },
            "upload": {
                "icon": "[IMAGE]",
                "label": "Upload",
                "description": "Upload plant images from your device",
                "color": "#8B5CF6",
                "shortcut": "U",
                "supports_multiple": True,
            },
        }
        self._initialize_state_management()

    def _initialize_state_management(self) -> Any:
        """Initialize state management for input modes."""
        if "input_modes" not in st.session_state:
            st.session_state["input_modes"] = dict.fromkeys(self.input_modes.keys(), False)

        if "active_inputs" not in st.session_state:
            st.session_state["active_inputs"] = {}

        if "input_validation" not in st.session_state:
            st.session_state["input_validation"] = {}

        if "input_mode_settings" not in st.session_state:
            st.session_state["input_mode_settings"] = {
                "allow_multiple_modes": True,
                "auto_validate": True,
                "persist_inputs": True,
                "show_mode_help": True,
            }

        # Ensure messages array exists
        if "messages" not in st.session_state:
            st.session_state["messages"] = []

    def render(self) -> dict[str, bool]:
        """Render input ribbon and return active modes."""
        current_modes = st.session_state.get("input_modes", {})

        # Render ribbon header
        self._render_ribbon_header()

        # Render input mode buttons
        active_modes = self._render_input_buttons(current_modes)

        # Render clear all button
        if any(active_modes.values()):
            self._render_clear_button()

        # Update session state
        st.session_state["input_modes"] = active_modes

        return active_modes

    def _render_ribbon_header(self) -> Any:
        """Render the ribbon header with instructions."""
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 1rem;'>
                <h3 style='color: #22C55E; margin: 0;'>[PROGRESS] Choose Your Input Method</h3>
                <p style='color: #64748B; margin: 0.5rem 0;'>
                    Select one or more ways to interact with PlantGuard
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _render_input_buttons(self, current_modes: dict[str, bool]) -> dict[str, bool]:
        """Render input mode buttons with enhanced visual feedback and color-coded states."""
        if st.session_state.get("mobile_view", False):
            col1, col2 = st.columns(2)
            cols = [col1, col2, col1, col2]
        else:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            cols = [col1, col2, col3, col4]

        active_modes: dict[str, bool] = {}

        for i, (mode_name, mode_info) in enumerate(self.input_modes.items()):
            with cols[i]:
                is_active = current_modes.get(mode_name, False)

                if is_active:
                    button_key = f"input_mode_{mode_name}_active"
                    if st.button(
                        f"Deactivate {mode_info['label']}",
                        key=button_key,
                        help=f"Click to deactivate {mode_info['description']}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        active_modes[mode_name] = False
                        self._handle_mode_activation(mode_name, False)
                    else:
                        active_modes[mode_name] = True
                else:
                    button_key = f"input_mode_{mode_name}_inactive"
                    if st.button(
                        f"{mode_info['icon']} {mode_info['label']}",
                        key=button_key,
                        help=f"{mode_info['description']} (Shortcut: {mode_info['shortcut']})",
                        type="secondary",
                        use_container_width=True,
                    ):
                        active_modes[mode_name] = True
                        self._handle_mode_activation(mode_name, True)
                    else:
                        active_modes[mode_name] = False

        return active_modes

    def _render_clear_button(self) -> Any:
        """Render clear all button with enhanced styling."""
        if st.session_state.get("mobile_view", False):
            st.markdown("---")
            if st.button(
                "Clear All Inputs",
                key="clear_all_inputs_mobile",
                help="Clear all active inputs and reset temporary data",
                type="secondary",
                use_container_width=True,
            ):
                self._clear_all_inputs()
        else:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            with col5:
                if st.button(
                    "Clear",
                    key="clear_all_inputs_desktop",
                    help="Clear all active inputs and reset temporary data",
                    type="secondary",
                    use_container_width=True,
                ):
                    self._clear_all_inputs()

    def _handle_mode_activation(self, mode_name: str, is_active: bool) -> Any:
        """Handle mode activation/deactivation with multiple mode support."""
        current_modes = st.session_state.get("input_modes", {})
        settings = st.session_state.get("input_mode_settings", {})

        if is_active:
            if not settings.get("allow_multiple_modes", True):
                for other_mode in current_modes:
                    if other_mode != mode_name and current_modes[other_mode]:
                        current_modes[other_mode] = False
                        self._clear_mode_data(other_mode)
                        with contextlib.suppress(Exception):
                            st.toast(f"[TODO] {other_mode.title()} mode deactivated (single mode only)", icon="[TODO]")

            current_modes[mode_name] = True
            st.session_state["input_modes"] = current_modes

            self._initialize_mode_data(mode_name)

            if settings.get("allow_multiple_modes", True) and sum(current_modes.values()) > 1:
                with contextlib.suppress(Exception):
                    st.toast(f"[DONE] {mode_name.title()} mode added (multimodal input)", icon="[DONE]")
            else:
                with contextlib.suppress(Exception):
                    st.toast(f"[DONE] {mode_name.title()} mode activated", icon="[DONE]")

            logger.info(f"Activated input mode: {mode_name}")

        else:
            current_modes[mode_name] = False
            st.session_state["input_modes"] = current_modes

            self._clear_mode_data(mode_name)

            with contextlib.suppress(Exception):
                st.toast(f"[TODO] {mode_name.title()} mode deactivated", icon="[TODO]")
            logger.info(f"Deactivated input mode: {mode_name}")

        if settings.get("auto_validate", True):
            self._update_validation_state()

    def _initialize_mode_data(self, mode_name: str) -> Any:
        """Initialize data storage for a specific mode."""
        active_inputs = st.session_state.get("active_inputs", {})

        if mode_name not in active_inputs:
            if mode_name == "text":
                if "messages" not in st.session_state:
                    st.session_state["messages"] = []
            elif mode_name == "voice":
                active_inputs[mode_name] = {"recordings": [], "transcriptions": []}
            elif mode_name == "camera":
                active_inputs[mode_name] = {"images": [], "current_image": None}
            elif mode_name == "upload":
                active_inputs[mode_name] = {"files": [], "processed_images": []}

        st.session_state["active_inputs"] = active_inputs

    def _update_validation_state(self) -> Any:
        """Update validation state for all active modes."""
        validation_state: dict[str, dict] = {}
        active_modes = self.get_active_modes()

        for mode in active_modes:
            validation_state[mode] = {
                "status": self._validate_mode_input(mode),
                "timestamp": st.session_state.get("current_time", ""),
                "has_data": self._has_mode_data(mode),
            }

        st.session_state["input_validation"] = validation_state

    def _has_mode_data(self, mode_name: str) -> bool:
        """Check if mode has any input data."""
        active_inputs = st.session_state.get("active_inputs", {})

        if mode_name == "text":
            messages = st.session_state.get("messages", [])
            return len(messages) > 0 and any(msg.get("role") == "user" for msg in messages)
        elif mode_name == "voice":
            # voice data may be stored under active_inputs['voice'] with 'recordings'
            if mode_name in active_inputs:
                return bool(active_inputs[mode_name].get("recordings") or active_inputs[mode_name].get("uploaded_audio"))
            # or top-level uploaded_audio key
            if "uploaded_audio" in active_inputs:
                return True
            # or check temp audio files
            return bool(st.session_state.get("temp_audio_files"))
        elif mode_name == "camera":
            if st.session_state.get("camera_image"):
                return True
            return bool(active_inputs.get(mode_name, {}).get("images"))
        elif mode_name == "upload":
            # uploads stored under active_inputs['upload']['files']
            if mode_name in active_inputs and active_inputs[mode_name].get("files"):
                return True
            # or check top-level uploaded_images
            return bool(active_inputs.get("uploaded_images"))

        return False

    def _clear_mode_data(self, mode_name: str) -> Any:
        """Clear data for a specific input mode."""
        active_inputs = st.session_state.get("active_inputs", {})
        if mode_name in active_inputs:
            del active_inputs[mode_name]
            st.session_state["active_inputs"] = active_inputs

    def _clear_all_inputs(self) -> Any:
        """Clear all input modes and data."""
        st.session_state["input_modes"] = dict.fromkeys(self.input_modes.keys(), False)
        st.session_state["active_inputs"] = {}

        self._cleanup_temporary_data()

        with contextlib.suppress(Exception):
            st.toast("[CLEAN] All inputs cleared", icon="[CLEAN]")
        logger.info("Cleared all input modes and data")

        # Update state without page refresh
        with contextlib.suppress(Exception):
            st.session_state.inputs_cleared = True

    def _cleanup_temporary_data(self) -> Any:
        """Clean up temporary files and data."""
        temp_audio_files = st.session_state.get("temp_audio_files", [])
        for file_path in temp_audio_files:
            try:
                p = Path(file_path)
                if p.exists():
                    p.unlink()
            except Exception as e:
                logger.warning(f"Could not delete temp file {file_path}: {e}")

        st.session_state["temp_audio_files"] = []

        temp_keys = [
            "uploaded_images",
            "camera_image",
            "recorded_audio",
            "transcribed_text",
            "current_analysis",
            "analysis_requested",
            "analysis_modes",
        ]

        for key in temp_keys:
            if key in st.session_state:
                del st.session_state[key]

    def render_mode_status(self) -> None:
        """Render enhanced status of active input modes with input validation."""
        active_modes = st.session_state.get("input_modes", {})
        active_count = sum(1 for active in active_modes.values() if active)

        if active_count > 0:
            st.markdown("### [SUMMARY] Active Input Modes")

            if st.session_state.get("mobile_view", False):
                for mode_name, is_active in active_modes.items():
                    if is_active:
                        self._render_mode_status_card(mode_name)
            else:
                cols = st.columns(min(active_count, 4))
                col_idx = 0

                for mode_name, is_active in active_modes.items():
                    if is_active:
                        with cols[col_idx % len(cols)]:
                            self._render_mode_status_card(mode_name)
                        col_idx += 1

            self._render_input_validation_status()

    def _render_mode_status_card(self, mode_name: str) -> Any:
        """Render individual mode status card with validation."""
        mode_info = self.input_modes[mode_name]
        validation_status = self._validate_mode_input(mode_name)

        if validation_status == "valid":
            status_color = "#22C55E"
            status_icon = "[DONE]"
            status_text = "Ready"
        elif validation_status == "missing_input":
            status_color = "#F59E0B"
            status_icon = "[WARNING]"
            status_text = "Input Needed"
        else:
            status_color = "#64748B"
            status_icon = "⚪"
            status_text = "Waiting"

        st.markdown(
            f"""
            <div style='
                background: {mode_info["color"]}15;
                border: 2px solid {mode_info["color"]};
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
                margin-bottom: 0.5rem;
                position: relative;
            '>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>{mode_info["icon"]}</div>
                <div style='font-weight: 700; color: {mode_info["color"]}; font-size: 1.1rem;'>
                    {mode_info["label"]}
                </div>
                <div style='
                    font-size: 0.75rem;
                    color: {status_color};
                    font-weight: 600;
                    margin-top: 0.5rem;
                    padding: 0.25rem 0.5rem;
                    background: {status_color}20;
                    border-radius: 20px;
                    display: inline-block;
                '>
                    {status_icon} {status_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _render_input_validation_status(self) -> Any:
        """Render overall input validation status."""
        validation_results: dict[str, str] = {}
        active_modes = self.get_active_modes()

        if not active_modes:
            return

        for mode in active_modes:
            validation_results[mode] = self._validate_mode_input(mode)

        valid_modes = [mode for mode, status in validation_results.items() if status == "valid"]
        invalid_modes = [mode for mode, status in validation_results.items() if status != "valid"]

        if valid_modes and not invalid_modes:
            st.success(f"[DONE] **Ready to analyze:** All {len(valid_modes)} input mode(s) have valid data")
        elif valid_modes and invalid_modes:
            st.warning(f"[WARNING] **Partial input:** {len(valid_modes)} ready, {len(invalid_modes)} need input")
        elif invalid_modes:
            st.info(f"[TIP] **Input needed:** Please provide input for {', '.join(invalid_modes)}")

        if valid_modes:
            if st.button("[LAUNCH] Analyze Now", key="analyze_from_ribbon", type="primary", use_container_width=True):
                self._trigger_analysis(valid_modes)

    def get_active_modes(self) -> list[str]:
        """Get list of currently active input modes."""
        active_modes = st.session_state.get("input_modes", {})
        return [mode for mode, active in active_modes.items() if active]

    def is_mode_active(self, mode_name: str) -> bool:
        """Check if a specific input mode is active."""
        active_modes = st.session_state.get("input_modes", {})
        return active_modes.get(mode_name, False)

    def set_mode_active(self, mode_name: str, active: bool) -> Any:
        """Programmatically set a mode as active/inactive."""
        if mode_name in self.input_modes:
            input_modes = st.session_state.get("input_modes", {})
            input_modes[mode_name] = active
            st.session_state["input_modes"] = input_modes

            self._handle_mode_activation(mode_name, active)

    def render_keyboard_shortcuts(self) -> None:
        """Render keyboard shortcuts help."""
        with st.expander("⌨️ Keyboard Shortcuts", expanded=True):
            st.markdown("**Input Mode Shortcuts:**")

            for mode_info in self.input_modes.values():
                st.markdown(f"- **{mode_info['shortcut']}** - {mode_info['icon']} {mode_info['label']}")

            st.markdown("**Other Shortcuts:**")
            st.markdown("- **Ctrl + K** - Clear all inputs")
            st.markdown("- **Ctrl + Enter** - Analyze (when inputs are ready)")
            st.markdown("- **Esc** - Cancel current operation")

    def render_input_mode_settings(self) -> None:
        """Render input mode settings and configuration options."""
        with st.expander("[SETTINGS] Input Mode Settings", expanded=True):
            settings = st.session_state.get("input_mode_settings", {})

            col1, col2 = st.columns(2)

            with col1:
                allow_multiple = st.checkbox(
                    "Allow Multiple Input Modes",
                    value=settings.get("allow_multiple_modes", True),
                    help="Enable using multiple input methods simultaneously",
                )

                auto_validate = st.checkbox(
                    "Auto-validate Inputs",
                    value=settings.get("auto_validate", True),
                    help="Automatically validate inputs as they're added",
                )

            with col2:
                persist_inputs = st.checkbox(
                    "Persist Inputs",
                    value=settings.get("persist_inputs", True),
                    help="Keep input data when switching between modes",
                )

                show_mode_help = st.checkbox(
                    "Show Mode Help",
                    value=settings.get("show_mode_help", True),
                    help="Display helpful tips for each input mode",
                )

            # Update settings
            new_settings = {
                "allow_multiple_modes": allow_multiple,
                "auto_validate": auto_validate,
                "persist_inputs": persist_inputs,
                "show_mode_help": show_mode_help,
            }

            if new_settings != settings:
                st.session_state["input_mode_settings"] = new_settings

                # Handle multiple mode setting change
                if not allow_multiple and settings.get("allow_multiple_modes", True):
                    self.toggle_multiple_mode_support(False)

    def handle_keyboard_shortcuts(self) -> Any:
        """Handle keyboard shortcuts (placeholder for future implementation)."""
        pass

    def render_input_validation(self) -> dict[str, str]:
        """Render input validation messages and return validation status."""
        validation_results: dict[str, str] = {}
        active_modes = self.get_active_modes()

        if not active_modes:
            st.info("[TIP] **Tip:** Select at least one input method above to get started!")
            return validation_results

        for mode in active_modes:
            validation_results[mode] = self._validate_mode_input(mode)

        valid_modes = [mode for mode, status in validation_results.items() if status == "valid"]
        invalid_modes = [mode for mode, status in validation_results.items() if status != "valid"]

        if invalid_modes:
            st.warning(f"[WARNING] **Input needed:** Please provide input for {', '.join(invalid_modes)}")

        if valid_modes:
            st.success(f"[DONE] **Ready to analyze:** {', '.join(valid_modes)} input(s) available")

        return validation_results

    def _validate_mode_input(self, mode_name: str) -> str:
        """Validate input for a specific mode."""
        active_inputs = st.session_state.get("active_inputs", {})

        if mode_name == "text":
            messages = st.session_state.get("messages", [])
            if messages and messages[-1].get("role") == "user":
                return "valid"
            # Also check if there are any user messages at all
            if any(msg.get("role") == "user" for msg in messages):
                return "valid"
            return "missing_input"

        elif mode_name == "voice":
            # Accept either top-level keys or nested under active_inputs['voice']
            if "recorded_audio" in active_inputs or "uploaded_audio" in active_inputs:
                return "valid"
            if "voice" in active_inputs and active_inputs["voice"].get("recordings"):
                return "valid"
            # Check session state directly for temp audio files
            if st.session_state.get("temp_audio_files"):
                return "valid"
            return "missing_input"

        elif mode_name == "camera":
            if st.session_state.get("camera_image"):
                return "valid"
            if "camera" in active_inputs and active_inputs["camera"].get("images"):
                return "valid"
            return "missing_input"

        elif mode_name == "upload":
            # Accept either active_inputs['upload']['files'] or top-level uploaded_images
            if active_inputs.get("uploaded_images"):
                return "valid"
            if "upload" in active_inputs and active_inputs["upload"].get("files"):
                return "valid"
            return "missing_input"

        return "unknown_mode"

    def can_analyze(self) -> bool:
        """Check if analysis can be performed with current inputs."""
        active_modes = self.get_active_modes()
        if not active_modes:
            return False

        return any(self._validate_mode_input(mode) == "valid" for mode in active_modes)

    def _trigger_analysis(self, valid_modes: list[str]) -> Any:
        """Trigger analysis for valid input modes."""
        st.session_state["analysis_requested"] = True
        st.session_state["analysis_modes"] = valid_modes

        try:
            with contextlib.suppress(Exception):
                st.toast(f"[LAUNCH] Starting analysis with {', '.join(valid_modes)} input(s)", icon="[LAUNCH]")
        except Exception:
            logger.exception("Unexpected error while showing toast")
        logger.info(f"Analysis triggered for modes: {valid_modes}")

        try:
            with contextlib.suppress(Exception):
                # Update state without page refresh
                st.session_state.analysis_triggered = True
        except Exception:
            logger.exception("Unexpected error while updating state")

    def get_input_data(self, mode_name: str) -> dict[str, Any]:
        """Get input data for a specific mode."""
        active_inputs = st.session_state.get("active_inputs", {})

        if mode_name == "text":
            messages = st.session_state.get("messages", [])
            if messages and messages[-1].get("role") == "user":
                return {"type": "text", "content": messages[-1].get("content", "")}
            # Also check for any user message
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    return {"type": "text", "content": msg.get("content", "")}

        elif mode_name == "voice":
            if "recorded_audio" in active_inputs:
                return {"type": "audio", "content": active_inputs["recorded_audio"]}
            elif "uploaded_audio" in active_inputs:
                return {"type": "audio", "content": active_inputs["uploaded_audio"]}
            elif st.session_state.get("temp_audio_files"):
                return {"type": "audio", "content": st.session_state["temp_audio_files"][0]}

        elif mode_name == "camera":
            if st.session_state.get("camera_image"):
                return {"type": "image", "content": st.session_state.get("camera_image")}
            elif active_inputs.get("camera", {}).get("images"):
                return {"type": "image", "content": active_inputs["camera"]["images"][0]}

        elif mode_name == "upload":
            if active_inputs.get("uploaded_images"):
                return {"type": "images", "content": active_inputs.get("uploaded_images")}
            elif active_inputs.get("upload", {}).get("files"):
                return {"type": "images", "content": active_inputs["upload"]["files"]}

        return {}

    def set_input_data(self, mode_name: str, data: Any) -> Any:
        """Set input data for a specific mode."""
        active_inputs = st.session_state.get("active_inputs", {})

        if mode_name == "voice":
            active_inputs["uploaded_audio"] = data
        elif mode_name == "upload":
            active_inputs["uploaded_images"] = data
        elif mode_name == "camera":
            st.session_state["camera_image"] = data

        st.session_state["active_inputs"] = active_inputs

    def toggle_multiple_mode_support(self, allow_multiple: bool) -> Any:
        """Toggle support for multiple simultaneous input modes."""
        settings = st.session_state.get("input_mode_settings", {})
        settings["allow_multiple_modes"] = allow_multiple
        st.session_state["input_mode_settings"] = settings

        if not allow_multiple:
            active_modes = self.get_active_modes()
            if len(active_modes) > 1:
                for mode in active_modes[1:]:
                    self.set_mode_active(mode, False)

                try:
                    with contextlib.suppress(Exception):
                        st.toast(f"[PARTIAL] Multiple modes disabled. Kept {active_modes[0]} mode only.", icon="[PARTIAL]")
                except Exception:
                    logger.exception("Unexpected error while showing toast for multiple mode toggle")

    def get_multimodal_input_summary(self) -> dict[str, Any]:
        """Get summary of all active input modes and their data."""
        active_modes = self.get_active_modes()
        # Use typed locals to keep mypy happy about indexed assignments
        input_data_map: dict[str, Any] = {}
        validation_status_map: dict[str, str] = {}

        summary = {
            "active_modes": active_modes,
            "mode_count": len(active_modes),
            "has_valid_input": False,
            "input_data": input_data_map,
            "validation_status": validation_status_map,
        }

        for mode in active_modes:
            input_data = self.get_input_data(mode)
            if input_data:
                input_data_map[mode] = input_data

            validation_status = self._validate_mode_input(mode)
            validation_status_map[mode] = validation_status

            if validation_status == "valid":
                summary["has_valid_input"] = True

        return summary

    def render_multimodal_input_preview(self) -> None:
        """Render preview of all active input modes and their data."""
        summary = self.get_multimodal_input_summary()

        if summary["mode_count"] == 0:
            return

        st.markdown("### [LINK] Multimodal Input Preview")

        if summary["mode_count"] > 1:
            st.info(f"[PROGRESS] **Multimodal Analysis Ready:** {summary['mode_count']} input modes active")

        for mode in summary["active_modes"]:
            with st.expander(f"{self.input_modes[mode]['icon']} {self.input_modes[mode]['label']} Input", expanded=True):
                self._render_mode_input_preview(mode, summary["input_data"].get(mode, {}))

    def _render_mode_input_preview(self, mode_name: str, input_data: dict) -> Any:
        """Render preview for a specific input mode."""
        if not input_data:
            st.warning(f"No input data for {mode_name} mode")
            return

        if mode_name == "text":
            st.markdown("**Latest Message:**")
            content = input_data.get("content", "No message")
            display_content = content[:200] + "..." if len(content) > 200 else content
            st.code(display_content)

        elif mode_name == "voice":
            st.markdown("**Audio Input:**")
            if "content" in input_data:
                st.audio(input_data["content"])
                st.caption("Audio file ready for transcription")

        elif mode_name == "camera":
            st.markdown("**Camera Image:**")
            if "content" in input_data:
                st.image(input_data["content"], width=200, caption="Captured image")

        elif mode_name == "upload":
            st.markdown("**Uploaded Files:**")
            if "content" in input_data:
                files = input_data["content"]
                if isinstance(files, list):
                    st.write(f"[FOLDER] {len(files)} file(s) uploaded")
                    for i, file in enumerate(files[:3]):
                        st.image(file, width=150, caption=f"Image {i + 1}")
                    if len(files) > 3:
                        st.caption(f"... and {len(files) - 3} more files")

    def validate_all_inputs(self) -> dict[str, str]:
        """Validate all active input modes and return detailed results."""
        active_modes = self.get_active_modes()
        validation_results: dict[str, str] = {}

        for mode in active_modes:
            validation_results[mode] = self._validate_mode_input(mode)

        st.session_state["input_validation"] = validation_results

        return validation_results

    def get_combined_input_for_analysis(self) -> dict[str, Any]:
        """Get combined input data from all valid modes for analysis."""
        validation_results = self.validate_all_inputs()
        valid_modes = [mode for mode, status in validation_results.items() if status == "valid"]

        combined_data_map: dict[str, Any] = {}
        combined_input = {
            "modes": valid_modes,
            "data": combined_data_map,
            "metadata": {
                "timestamp": st.session_state.get("current_time", ""),
                "session_id": st.session_state.get("session_id", ""),
                "multimodal": len(valid_modes) > 1,
            },
        }

        for mode in valid_modes:
            input_data = self.get_input_data(mode)
            if input_data:
                combined_data_map[mode] = input_data

        return combined_input
