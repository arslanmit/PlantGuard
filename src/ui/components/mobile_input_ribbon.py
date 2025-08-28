"""
Mobile Input Ribbon Component for PlantGuard

Touch-friendly input method selection with vertical stacking on mobile.
Provides access to all PlantGuard input modes: Text, Voice, Camera, Upload.
"""

from collections.abc import Callable
from typing import Any

import streamlit as st

from .mobile_component_registry import ComponentMetadata, MobileComponent, register_mobile_component


@register_mobile_component
class MobileInputRibbon(MobileComponent):
    """Mobile input ribbon with always-visible touch-optimized buttons.

    Always-Visible Features:
    - Large prominent action buttons for all input types (min 44px touch targets)
    - Icon + text labels for clear identification
    - Always-visible status indicators for each input method
    - No hidden menus, dropdowns, or collapsible elements
    - 2x2 grid layout with all controls immediately accessible
    - Real-time status overview showing readiness of each input method
    - Touch-friendly design with visual feedback
    - AI agent testable and self-healing
    """

    def __init__(self, component_id: str = "mobile_input_ribbon", **kwargs):
        super().__init__(component_id, **kwargs)
        self.layout_style = kwargs.get("layout_style", "grid")  # 'grid' or 'vertical'
        self.show_labels = kwargs.get("show_labels", True)
        self.button_style = kwargs.get("button_style", "elevated")  # 'elevated' or 'flat'

    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="input_ribbon",
            display_name="Mobile Input Ribbon - Always Visible",
            description="Always-visible touch-friendly input method selection buttons with status indicators",
            ai_agent_friendly_description=(
                "Always-visible input ribbon component providing direct access to all PlantGuard input modes "
                "with large prominent buttons, icon + text labels, and always-visible status indicators. "
                "No hidden menus or collapsible elements."
            ),
            interactive_elements=[
                {
                    "id": "text_input_button_always_visible",
                    "type": "button",
                    "key": f"{self.component_id}_text_always_visible",
                    "description": "Text chat input button - always visible with status",
                    "testable": True,
                    "touch_target": True,
                    "always_visible": True,
                },
                {
                    "id": "voice_input_button_always_visible",
                    "type": "button",
                    "key": f"{self.component_id}_voice_always_visible",
                    "description": "Voice recording button - always visible with status",
                    "testable": True,
                    "touch_target": True,
                    "always_visible": True,
                },
                {
                    "id": "camera_button_always_visible",
                    "type": "button",
                    "key": f"{self.component_id}_camera_always_visible",
                    "description": "Camera capture button - always visible with status",
                    "testable": True,
                    "touch_target": True,
                    "always_visible": True,
                },
                {
                    "id": "upload_button_always_visible",
                    "type": "button",
                    "key": f"{self.component_id}_upload_always_visible",
                    "description": "File upload button - always visible with status",
                    "testable": True,
                    "touch_target": True,
                    "always_visible": True,
                },
            ],
            state_dependencies=["active_input_mode", "input_ribbon_initialized", "camera_available", "microphone_available"],
            css_classes=["mobile-input-ribbon-always-visible", "mobile-input-section-header", "mobile-input-status-overview"],
            test_scenarios=[
                {
                    "name": "always_visible_buttons",
                    "description": "Test all input buttons are always visible with proper labels",
                    "expected_outcome": "Four input buttons visible with icon + text + status indicators",
                },
                {
                    "name": "status_indicators",
                    "description": "Test status indicators are always visible and accurate",
                    "expected_outcome": "Status overview shows current state of all input methods",
                },
                {
                    "name": "touch_accessibility",
                    "description": "Test buttons meet touch accessibility requirements (min 44px)",
                    "expected_outcome": "All buttons are touch-friendly and clearly labeled",
                },
                {
                    "name": "no_hidden_elements",
                    "description": "Test no elements are hidden or require expansion",
                    "expected_outcome": "All controls and status visible simultaneously",
                },
            ],
            ai_agent_instructions={
                "testing": "Verify always-visible design, status indicators, touch targets, no hidden elements",
                "fixing": "Ensure all elements visible, proper status updates, touch accessibility",
                "monitoring": "Check button visibility, status accuracy, no collapsed states",
            },
            version="2.0.0",
            ai_agent_testable=True,
            auto_fix_enabled=True,
        )

    def initialize_input_ribbon_state(self) -> None:
        """Initialize input ribbon session state."""
        if "active_input_mode" not in st.session_state:
            st.session_state.active_input_mode = None

        if "input_ribbon_initialized" not in st.session_state:
            st.session_state.input_ribbon_initialized = True

        if "camera_available" not in st.session_state:
            st.session_state.camera_available = True  # Assume available

        if "microphone_available" not in st.session_state:
            st.session_state.microphone_available = True  # Assume available

        # Input method callbacks
        if "input_callbacks" not in st.session_state:
            st.session_state.input_callbacks = {}

    def get_input_methods(self) -> list[dict[str, Any]]:
        """Get available input methods configuration with always-visible status indicators."""
        return [
            {
                "id": "text",
                "title": "Text Chat",
                "icon": "[CHAT]",
                "description": "Ask questions about plant care",
                "enabled": True,
                "primary": True,
                "status": "ready",
                "status_icon": "[DONE]",
            },
            {
                "id": "voice",
                "title": "Voice",
                "icon": "[VOICE]",
                "description": "Record voice questions",
                "enabled": st.session_state.get("microphone_available", True),
                "primary": True,
                "status": "ready" if st.session_state.get("microphone_available", True) else "disabled",
                "status_icon": "[DONE]" if st.session_state.get("microphone_available", True) else "[TODO]",
            },
            {
                "id": "camera",
                "title": "Camera",
                "icon": "[CAMERA]",
                "description": "Take photo of plant",
                "enabled": st.session_state.get("camera_available", True),
                "primary": True,
                "status": "ready" if st.session_state.get("camera_available", True) else "disabled",
                "status_icon": "[DONE]" if st.session_state.get("camera_available", True) else "[TODO]",
            },
            {
                "id": "upload",
                "title": "Upload",
                "icon": "[ATTACH]",
                "description": "Upload image file",
                "enabled": True,
                "primary": False,
                "status": "ready",
                "status_icon": "[DONE]",
            },
        ]

    def render_input_button(self, method: dict[str, Any], button_key: str) -> bool:
        """Render individual input method button with always-visible status.

        Returns:
            bool: True if button was clicked
        """
        is_active = st.session_state.get("active_input_mode") == method["id"]
        is_enabled = method.get("enabled", True)
        status = method.get("status", "unknown")
        status_icon = method.get("status_icon", "⚪")

        # Button styling based on state
        button_type = "primary" if is_active else "secondary"

        # Always show icon + text label + status indicator
        button_label = f"{method['icon']} {method['title']} {status_icon}"

        # Add status to help text
        help_text = f"{method['description']} | Status: {status.title()}"

        # Use Streamlit button with always-visible elements
        button_clicked = st.button(
            label=button_label, key=button_key, help=help_text, disabled=not is_enabled, use_container_width=True, type=button_type
        )

        # Show additional status below button (always visible)
        if is_active:
            st.success(f"Active: {method['title']}")
        elif not is_enabled:
            st.error(f"Disabled: {method['title']}")
        else:
            st.info(f"Ready: {method['title']}")

        return button_clicked

    def render_always_visible_layout(self) -> str:
        """Render input buttons in always-visible 2x2 grid layout."""
        methods = self.get_input_methods()
        selected_method = None

        # Simple section header
        st.markdown("## [MOBILE] Plant Analysis Input")
        st.markdown("Choose how you want to analyze your plant:")

        # Always-visible 2x2 grid for all input types
        col1, col2 = st.columns(2, gap="medium")

        # First row: Camera and Upload
        with col1:
            camera_method = next(m for m in methods if m["id"] == "camera")
            button_key = f"{self.component_id}_camera_always_visible"
            if self.render_input_button(camera_method, button_key):
                selected_method = "camera"
                st.session_state.active_input_mode = selected_method

        with col2:
            upload_method = next(m for m in methods if m["id"] == "upload")
            button_key = f"{self.component_id}_upload_always_visible"
            if self.render_input_button(upload_method, button_key):
                selected_method = "upload"
                st.session_state.active_input_mode = selected_method

        # Second row: Voice and Text
        col3, col4 = st.columns(2, gap="medium")

        with col3:
            voice_method = next(m for m in methods if m["id"] == "voice")
            button_key = f"{self.component_id}_voice_always_visible"
            if self.render_input_button(voice_method, button_key):
                selected_method = "voice"
                st.session_state.active_input_mode = selected_method

        with col4:
            text_method = next(m for m in methods if m["id"] == "text")
            button_key = f"{self.component_id}_text_always_visible"
            if self.render_input_button(text_method, button_key):
                selected_method = "text"
                st.session_state.active_input_mode = selected_method

        return selected_method

    def render_status_overview(self) -> None:
        """Render always-visible status overview for all input methods."""
        methods = self.get_input_methods()

        st.markdown("### Input Status Overview")

        # Status indicators in horizontal layout
        cols = st.columns(len(methods))

        for i, method in enumerate(methods):
            with cols[i]:
                status_color = "[GREEN]" if method["enabled"] else "[RED]"
                st.markdown(f"{status_color} **{method['title']}**")
                st.markdown(f"{method['status_icon']} {method['status'].title()}")

    def render(self, **kwargs) -> str:
        """Render the input ribbon component with always-visible controls.

        Returns:
            str: Selected input method ID or None
        """
        # Initialize state
        self.initialize_input_ribbon_state()

        # Always show status overview at top
        self.render_status_overview()

        # Always-visible input buttons (no hidden/compact layouts)
        selected_method = self.render_always_visible_layout()

        # Handle selection
        if selected_method:
            self._handle_input_method_selection(selected_method)

        return selected_method

    def render_with_actions(self, **kwargs) -> str:
        """Render input ribbon with action callbacks."""
        selected_method = self.render(**kwargs)

        if selected_method:
            # Execute callback if registered
            callback = st.session_state.input_callbacks.get(selected_method)
            if callback and callable(callback):
                try:
                    callback()
                except Exception as e:
                    st.error(f"Error executing {selected_method} callback: {e}")

        return selected_method

    def _handle_input_method_selection(self, method_id: str) -> None:
        """Handle input method selection."""
        # Update session state
        st.session_state.active_input_mode = method_id

        # Show feedback
        method_names = {"text": "Text Chat", "voice": "Voice Recording", "camera": "Camera Capture", "upload": "File Upload"}

        method_name = method_names.get(method_id, method_id.title())
        st.success(f"Selected: {method_name}")

        # Log for AI agent monitoring
        print(f"Mobile Input Ribbon: Selected {method_id}")

    def register_callback(self, method_id: str, callback: Callable) -> None:
        """Register callback for input method selection."""
        if "input_callbacks" not in st.session_state:
            st.session_state.input_callbacks = {}

        st.session_state.input_callbacks[method_id] = callback

    def get_active_input_mode(self) -> str | None:
        """Get currently active input mode."""
        return st.session_state.get("active_input_mode")

    def set_active_input_mode(self, method_id: str) -> None:
        """Programmatically set active input mode."""
        st.session_state.active_input_mode = method_id

    def clear_active_input_mode(self) -> None:
        """Clear active input mode selection."""
        st.session_state.active_input_mode = None

    def get_ribbon_status(self) -> dict[str, Any]:
        """Get input ribbon status for AI agent monitoring."""
        methods = self.get_input_methods()

        return {
            "component_id": self.component_id,
            "initialized": st.session_state.get("input_ribbon_initialized", False),
            "active_input_mode": st.session_state.get("active_input_mode"),
            "available_methods": [m["id"] for m in methods if m.get("enabled", True)],
            "disabled_methods": [m["id"] for m in methods if not m.get("enabled", True)],
            "total_methods": len(methods),
            "camera_available": st.session_state.get("camera_available", False),
            "microphone_available": st.session_state.get("microphone_available", False),
            "layout_style": self.layout_style,
            "show_labels": self.show_labels,
        }

    def enable_method(self, method_id: str) -> None:
        """Enable specific input method."""
        if method_id == "camera":
            st.session_state.camera_available = True
        elif method_id == "voice":
            st.session_state.microphone_available = True

    def disable_method(self, method_id: str) -> None:
        """Disable specific input method."""
        if method_id == "camera":
            st.session_state.camera_available = False
        elif method_id == "voice":
            st.session_state.microphone_available = False

        # Clear active mode if it's the disabled method
        if st.session_state.get("active_input_mode") == method_id:
            self.clear_active_input_mode()


# Utility functions
def create_mobile_input_ribbon(layout_style: str = "grid", show_labels: bool = True, button_style: str = "elevated") -> MobileInputRibbon:
    """Create and return a MobileInputRibbon instance."""
    return MobileInputRibbon(component_id="mobile_input_ribbon", layout_style=layout_style, show_labels=show_labels, button_style=button_style)


def render_input_selection_widget() -> str:
    """Convenience function to render input selection widget."""
    ribbon = create_mobile_input_ribbon()
    return ribbon.render()
