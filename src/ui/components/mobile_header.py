"""
Mobile Header Component for PlantGuard

Sticky header with title, model switching, and system status.
Optimized for mobile touch interactions.
"""

from typing import Any

import streamlit as st

from .mobile_component_registry import ComponentMetadata, MobileComponent, register_mobile_component


@register_mobile_component
class MobileHeader(MobileComponent):
    """Mobile header with model management and status display.

    Features:
    - Sticky positioning for mobile
    - Model switching dropdown
    - System status indicator
    - Touch-friendly controls
    - AI agent testable
    """

    def __init__(self, component_id: str = "mobile_header", **kwargs):
        super().__init__(component_id, **kwargs)
        self.title = kwargs.get("title", "PlantGuard AI")
        self.subtitle = kwargs.get("subtitle", "Mobile Plant Disease Detection")
        self.show_model_switcher = kwargs.get("show_model_switcher", True)
        self.show_status = kwargs.get("show_status", True)

    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="header_always_visible",
            display_name="Mobile Header - Always Visible",
            description="Always-visible header with title, model switching, and status",
            ai_agent_friendly_description=(
                "Mobile header component that displays app title, provides model switching "
                "functionality, shows system status, and maintains always-visible positioning for mobile"
            ),
            interactive_elements=[
                {
                    "id": "model_selector",
                    "type": "button_grid",
                    "key": f"{self.component_id}_model_selector",
                    "description": "Always-visible model selection buttons",
                    "always_visible": True,
                    "touch_target": True,
                    "testable": True,
                },
                {
                    "id": "status_indicator",
                    "type": "status",
                    "description": "Always-visible system status display",
                    "always_visible": True,
                    "touch_target": False,
                    "testable": True,
                },
            ],
            state_dependencies=["current_vision_model", "system_status", "model_loading", "header_initialized"],
            css_classes=["mobile-header", "mobile-header-always-visible", "mobile-header-content", "mobile-header-title", "mobile-header-actions"],
            test_scenarios=[
                {
                    "name": "header_rendering",
                    "description": "Test header displays correctly",
                    "expected_outcome": "Header visible with title and actions",
                },
                {"name": "model_switching", "description": "Test model selection works", "expected_outcome": "Model changes when selected"},
                {"name": "status_display", "description": "Test status indicator updates", "expected_outcome": "Status reflects system state"},
            ],
            ai_agent_instructions={
                "testing": "Check header visibility, model switcher functionality, status accuracy",
                "fixing": "Initialize missing state variables, fix key conflicts, ensure responsiveness",
                "monitoring": "Watch for header layout shifts, touch target sizes",
            },
            version="1.0.0",
            ai_agent_testable=True,
            auto_fix_enabled=True,
        )

    def initialize_header_state(self) -> None:
        """Initialize header-related session state."""
        # Initialize model state
        if "current_vision_model" not in st.session_state:
            st.session_state.current_vision_model = "vit_best"

        if "available_models" not in st.session_state:
            st.session_state.available_models = {
                "vit_best": "Vision Transformer (Best)",
                "resnet50_plantvillage_v1": "ResNet50 (Fast)",
                "mobilenet_fast": "MobileNet (Lightweight)",
            }

        # Initialize status state
        if "system_status" not in st.session_state:
            st.session_state.system_status = "ready"

        if "model_loading" not in st.session_state:
            st.session_state.model_loading = False

        if "header_initialized" not in st.session_state:
            st.session_state.header_initialized = True

    def render_title_section(self) -> None:
        """Render the title section of the header."""
        st.markdown(
            f"""
        <div class="mobile-header-title-section">
            <h1 class="mobile-header-title">{self.title}</h1>
            <p class="mobile-header-subtitle">{self.subtitle}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_model_switcher(self) -> None:
        """Render the always-visible model switching controls."""
        if not self.show_model_switcher:
            return

        # Always-visible model switcher - no dropdown, direct buttons
        st.markdown('<div class="mobile-model-switcher-always-visible">', unsafe_allow_html=True)

        model_options = list(st.session_state.available_models.keys())
        current_model = st.session_state.current_vision_model

        # Create inline model buttons (always visible)
        cols = st.columns(len(model_options))

        for i, model_key in enumerate(model_options):
            with cols[i]:
                model_info = self._get_model_info(model_key)
                is_current = model_key == current_model

                # Always-visible model button with visual indication
                button_style = "primary" if is_current else "secondary"
                button_icon = "[DONE]" if is_current else "⚪"

                # Short model name for always-visible display
                short_names = {"vit_best": "ViT", "resnet50_plantvillage_v1": "ResNet", "mobilenet_fast": "Mobile"}
                display_name = short_names.get(model_key, model_key[:6])

                if st.button(
                    f"{button_icon} {display_name}",
                    key=f"{self.component_id}_model_{model_key}",
                    use_container_width=True,
                    type=button_style,
                    disabled=is_current,
                    help=f"{model_info['name']} - {model_info['accuracy']} accuracy",
                ):
                    if not is_current:
                        st.session_state.current_vision_model = model_key
                        self._handle_model_change(model_key)
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    def render_status_indicator(self) -> None:
        """Render always-visible system status indicator."""
        if not self.show_status:
            return

        status = st.session_state.get("system_status", "unknown")
        is_loading = st.session_state.get("model_loading", False)

        # Determine status display - always visible, prominent
        if is_loading:
            status_icon = "[PARTIAL]"
            status_text = "Loading"
            status_class = "mobile-status-loading"
            status_color = "#FFA500"  # Orange
        elif status == "ready":
            status_icon = "[DONE]"
            status_text = "Ready"
            status_class = "mobile-status-ready"
            status_color = "#16A34A"  # Green
        elif status == "error":
            status_icon = "[TODO]"
            status_text = "Error"
            status_class = "mobile-status-error"
            status_color = "#DC2626"  # Red
        else:
            status_icon = "⚪"
            status_text = "Unknown"
            status_class = "mobile-status-unknown"
            status_color = "#6B7280"  # Gray

        # Always-visible status with prominent display
        st.markdown(
            f"""
        <div class="mobile-status-indicator-always-visible {status_class}" 
             style="background-color: {status_color}; color: white; padding: 8px 12px; 
                    border-radius: 16px; text-align: center; font-weight: 600;
                    margin: 4px 0;" 
             data-testable="true">
            <span class="mobile-status-icon">{status_icon}</span>
            <span class="mobile-status-text" style="margin-left: 4px;">{status_text}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_actions_section(self) -> None:
        """Render header actions in always-visible layout."""
        # Always-visible layout: Direct rendering without containers
        if self.show_model_switcher:
            st.markdown("**AI Models:**")
            self.render_model_switcher()

        if self.show_status:
            st.markdown("**Status:**")
            self.render_status_indicator()

    def render(self, **kwargs) -> None:
        """Render the complete always-visible mobile header."""
        # Initialize state
        self.initialize_header_state()

        # Title section - streamlined
        st.markdown(f"## [LEAF] {self.title}")
        st.markdown(f"*{self.subtitle}*")

        # Actions section - direct rendering
        self.render_actions_section()

    def render_compact(self) -> None:
        """Render compact version of header for smaller screens."""
        self.initialize_header_state()

        # Single row layout for compact version
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown(f"### {self.title}")

        with col2:
            if self.show_model_switcher:
                current_model = st.session_state.current_vision_model
                model_name = st.session_state.available_models.get(current_model, current_model)
                if st.button(f"[AI] {model_name}", key=f"{self.component_id}_compact_model", use_container_width=True):
                    self._show_model_switcher_modal()

        with col3:
            if self.show_status:
                self.render_status_indicator()

    def _handle_model_change(self, new_model: str) -> None:
        """Handle model change event."""
        # This would typically trigger model loading through model manager
        st.session_state.model_loading = True
        st.session_state.system_status = "loading"

        # For demo purposes, simulate loading completion
        # In real implementation, this would be handled by the model manager
        st.success(f"Switched to {st.session_state.available_models[new_model]}")

        # Reset loading state (in real app, this would be done by model manager)
        st.session_state.model_loading = False
        st.session_state.system_status = "ready"

    def _show_model_info_inline(self) -> None:
        """Show model information inline - no expandable sections."""
        current_model = st.session_state.current_vision_model
        model_info = self._get_model_info(current_model)

        # Always-visible model info
        st.markdown(
            f"""
        <div class="mobile-model-info-always-visible" 
             style="background: #F0FDF4; border: 1px solid #16A34A; 
                    border-radius: 8px; padding: 12px; margin: 8px 0;">
            <strong>Current Model:</strong> {model_info["name"]}<br>
            <strong>Accuracy:</strong> {model_info["accuracy"]} | 
            <strong>Speed:</strong> {model_info["speed"]}<br>
            <small>{model_info["description"]}</small>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _show_model_switcher_modal(self) -> None:
        """Show model switcher in modal/expander for compact mode."""
        with st.expander("[AI] Select AI Model", expanded=True):
            model_options = list(st.session_state.available_models.keys())

            for model_key in model_options:
                model_info = self._get_model_info(model_key)
                is_current = model_key == st.session_state.current_vision_model

                button_text = f"{'[DONE]' if is_current else '⚪'} {model_info['name']}"

                if st.button(button_text, key=f"{self.component_id}_modal_{model_key}", use_container_width=True, disabled=is_current):
                    if not is_current:
                        st.session_state.current_vision_model = model_key
                        self._handle_model_change(model_key)
                        st.rerun()

    def _get_model_info(self, model_key: str) -> dict[str, str]:
        """Get detailed model information."""
        model_details = {
            "vit_best": {
                "name": "Vision Transformer (Best)",
                "accuracy": "100%",
                "speed": "Medium",
                "description": "Highest accuracy model using transformer architecture",
            },
            "resnet50_plantvillage_v1": {
                "name": "ResNet50 (Fast)",
                "accuracy": "95%",
                "speed": "Fast",
                "description": "Balanced performance with good speed and accuracy",
            },
            "mobilenet_fast": {
                "name": "MobileNet (Lightweight)",
                "accuracy": "90%",
                "speed": "Very Fast",
                "description": "Optimized for mobile devices with fast inference",
            },
        }

        return model_details.get(
            model_key, {"name": "Unknown Model", "accuracy": "N/A", "speed": "N/A", "description": "Model information not available"}
        )

    def get_header_status(self) -> dict[str, Any]:
        """Get header status for AI agent monitoring."""
        return {
            "component_id": self.component_id,
            "initialized": st.session_state.get("header_initialized", False),
            "current_model": st.session_state.get("current_vision_model", None),
            "system_status": st.session_state.get("system_status", "unknown"),
            "model_loading": st.session_state.get("model_loading", False),
            "available_models": len(st.session_state.get("available_models", {})),
            "show_model_switcher": self.show_model_switcher,
            "show_status": self.show_status,
        }

    def update_status(self, new_status: str) -> None:
        """Update system status (called by other components)."""
        st.session_state.system_status = new_status

    def set_loading(self, is_loading: bool) -> None:
        """Set loading state (called by model manager)."""
        st.session_state.model_loading = is_loading


# Utility functions
def create_mobile_header(
    title: str = "PlantGuard AI", subtitle: str = "Mobile Plant Disease Detection", show_model_switcher: bool = True, show_status: bool = True
) -> MobileHeader:
    """Create and return a MobileHeader instance."""
    return MobileHeader(
        component_id="mobile_header", title=title, subtitle=subtitle, show_model_switcher=show_model_switcher, show_status=show_status
    )
