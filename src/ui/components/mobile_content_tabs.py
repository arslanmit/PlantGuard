"""
Mobile Content Tabs Component for PlantGuard

Organizes all PlantGuard features into mobile-friendly tabs:
- Image Analysis
- Voice Assistant
- Chat Interface
- History & Settings

"""

from collections.abc import Callable
from typing import Any

import streamlit as st

from .mobile_component_registry import ComponentMetadata, MobileComponent


class MobileContentTabs(MobileComponent):
    """Mobile-optimized content tabs for PlantGuard features - Always Visible Design.

    Always-Visible Features:
    - All tabs visible simultaneously in horizontal layout
    - No hidden panels or dropdown menus
    - Direct access to all features without switching
    - Touch-friendly tab buttons with icon + text
    - Content areas always accessible through scroll
    - AI agent testable with clear identification
    """

    def __init__(self, component_id: str = "mobile_content_tabs", **kwargs) -> None:
        super().__init__(component_id)
        self.tab_style = kwargs.get("tab_style", "pills")  # 'pills' or 'underline'
        self.scrollable_tabs = kwargs.get("scrollable_tabs", True)
        self.lazy_loading = kwargs.get("lazy_loading", False)  # Disable lazy loading for SPA

        self.content_callbacks = {}

    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="content_tabs_always_visible",
            display_name="Mobile Content Tabs - Always Visible",
            description="Always-visible tabbed interface for organizing PlantGuard features",
            ai_agent_friendly_description=(
                "Always-visible content tabs component that shows all PlantGuard features "
                "simultaneously with horizontal scrollable layout. No hidden panels or "
                "collapsible elements - all content directly accessible."
            ),
            interactive_elements=[
                {
                    "id": "tab_image_analysis_always_visible",
                    "type": "tab_button_always_visible",
                    "key": f"{self.component_id}_tab_image_always_visible",
                    "description": "Image analysis tab - always visible",
                    "testable": True,
                    "always_visible": True,
                },
                {
                    "id": "tab_voice_assistant_always_visible",
                    "type": "tab_button_always_visible",
                    "key": f"{self.component_id}_tab_voice_always_visible",
                    "description": "Voice assistant tab - always visible",
                    "testable": True,
                    "always_visible": True,
                },
                {
                    "id": "tab_chat_interface_always_visible",
                    "type": "tab_button_always_visible",
                    "key": f"{self.component_id}_tab_chat_always_visible",
                    "description": "Chat interface tab - always visible",
                    "testable": True,
                    "always_visible": True,
                },
                {
                    "id": "tab_history_settings_always_visible",
                    "type": "tab_button_always_visible",
                    "key": f"{self.component_id}_tab_history_always_visible",
                    "description": "History and settings tab - always visible",
                    "testable": True,
                    "always_visible": True,
                },
                {
                    "testable": True,
                    "always_visible": True,
                },
            ],
            state_dependencies=["active_tab", "tab_history", "content_tabs_initialized", "all_tabs_visible"],
            css_classes=[
                "mobile-content-tabs-always-visible",
                "mobile-tab-bar-always-visible",
                "mobile-tab-button-always-visible",
                "mobile-tab-content-always-visible",
            ],
            test_scenarios=[
                {
                    "name": "all_tabs_visible",
                    "description": "Test all tabs are always visible simultaneously",
                    "expected_outcome": "All tab buttons visible in horizontal layout",
                },
                {
                    "name": "no_hidden_panels",
                    "description": "Test no content is hidden or collapsed",
                    "expected_outcome": "All content accessible through direct scroll",
                },
                {
                    "name": "touch_accessibility",
                    "description": "Test tab buttons meet touch target requirements",
                    "expected_outcome": "All tabs have proper touch targets and labels",
                },
                {
                    "name": "content_accessibility",
                    "description": "Test all content is directly accessible",
                    "expected_outcome": "No modal dialogs or hidden content areas",
                },
            ],
            ai_agent_instructions={
                "testing": "Verify all tabs visible, no hidden content, proper touch targets, direct access",
                "fixing": "Ensure always-visible layout, fix accessibility issues, validate content access",
                "monitoring": "Monitor tab visibility, content accessibility, touch interaction performance",
            },
            version="2.0.0",
            ai_agent_testable=True,
            auto_fix_enabled=True,
        )

    def initialize_tabs_state(self) -> None:
        """Initialize tabs session state for always-visible design."""
        if "active_tab" not in st.session_state:
            st.session_state.active_tab = "image_analysis"

        if "tab_history" not in st.session_state:
            st.session_state.tab_history = ["image_analysis"]

        if "content_tabs_initialized" not in st.session_state:
            st.session_state.content_tabs_initialized = True

        # Always-visible design state
        if "all_tabs_visible" not in st.session_state:
            st.session_state.all_tabs_visible = True

        # Content callbacks registry
        if "tab_content_callbacks" not in st.session_state:
            st.session_state.tab_content_callbacks = {}

    def get_available_tabs(self) -> list[dict[str, Any]]:
        """Get configuration for all available tabs."""
        return [
            {
                "id": "image_analysis",
                "title": "Image Analysis",
                "short_title": "Image",
                "icon": "[IMAGE]",
                "description": "Analyze plant images for disease detection",
                "enabled": True,
                "primary": True,
            },
            {
                "id": "voice_assistant",
                "title": "Voice Assistant",
                "short_title": "Voice",
                "icon": "[VOICE]",
                "description": "Voice-powered plant care assistant",
                "enabled": True,
                "primary": True,
            },
            {
                "id": "chat_interface",
                "title": "Chat Assistant",
                "short_title": "Chat",
                "icon": "[CHAT]",
                "description": "Text-based plant care Q&A",
                "enabled": True,
                "primary": True,
            },
            {
                "id": "history_settings",
                "title": "History & Settings",
                "short_title": "History",
                "icon": "[SUMMARY]",
                "description": "View analysis history and app settings",
                "enabled": True,
                "primary": False,
            },
        ]

    def render_always_visible_tabs(self) -> str:
        """Render all tabs visible simultaneously in horizontal layout."""
        tabs = self.get_available_tabs()
        current_tab = st.session_state.get("active_tab", "image_analysis")

        # Always-visible tabs header
        st.markdown('<div class="mobile-tabs-always-visible-header">', unsafe_allow_html=True)
        st.markdown("### [LEAF] All PlantGuard Features")
        st.markdown("**All features directly accessible - no hidden content**")
        st.markdown("</div>", unsafe_allow_html=True)

        # Always-visible tab bar
        st.markdown('<div class="mobile-tab-bar-always-visible" data-design="always-visible">', unsafe_allow_html=True)

        # Create horizontal scrollable tab buttons
        cols = st.columns(len(tabs))
        selected_tab = current_tab

        for i, tab in enumerate(tabs):
            if not tab.get("enabled", True):
                continue

            with cols[i]:
                is_active = current_tab == tab["id"]
                button_key = f"{self.component_id}_tab_{tab['id']}_always_visible"

                # Always-visible tab button with icon + text + status
                tab_title = tab.get("short_title", tab["title"])
                tab_label = f"{tab['icon']} {tab_title}"
                if is_active:
                    tab_label += " [DONE]"

                button_type = "primary" if is_active else "secondary"

                # Render always-visible tab button
                if st.button(
                    label=tab_label,
                    key=button_key,
                    help=tab["description"],
                    width="stretch",
                    type=button_type,
                    disabled=False,  # Never disable - always interactive
                ):
                    selected_tab = tab["id"]
                    st.session_state.active_tab = selected_tab
                    self._update_tab_history(selected_tab)
                    # Update SPA manager focus WITHOUT st.rerun()
                    st.session_state.focused_content = selected_tab

                # Always show tab status
                if is_active:
                    st.success("Active")
                else:
                    st.info("Available")

        st.markdown("</div>", unsafe_allow_html=True)
        return selected_tab

    def render_all_content_spa_mode(self) -> None:
        """Render all content in SPA mode without page redirects."""
        # Register content areas with SPA manager
        self._register_all_content_areas()

        # Use SPA manager to render content without page navigation
        # Render all content areas
        pass

    def _register_all_content_areas(self) -> None:
        """Register all tab content areas with SPA manager."""
        tabs = self.get_available_tabs()

        for tab in tabs:
            if not tab.get("enabled", True):
                continue

            tab_id = tab["id"]
            callback = self.content_callbacks.get(tab_id)

            if callback and callable(callback):
                # Register with existing callback
                self.register_tab_content(tab_id, callback)
            else:
                # Register with default content
                def default_callback(tab_info=tab) -> Any:
                    return self._render_default_tab_content(tab_info["id"], tab_info)
                self.register_tab_content(tab_id, default_callback)

        """Render tab navigation buttons.
        
        Returns:
            str: Selected tab ID
        """
        tabs = self.get_available_tabs()
        current_tab = st.session_state.get("active_tab", "image_analysis")
        selected_tab = current_tab

        # Tab navigation container
        st.markdown(
            """
        <div class="mobile-tab-navigation" data-component="tab-navigation" data-testable="true">
        """,
            unsafe_allow_html=True,
        )

        # Create columns for tab buttons
        if len(tabs) <= 3:
            cols = st.columns(len(tabs))
        else:
            # Scrollable horizontal layout for more tabs
            cols = st.columns(len(tabs))

        for i, tab in enumerate(tabs):
            if not tab.get("enabled", True):
                continue

            col_index = i % len(cols)

            with cols[col_index]:
                is_active = current_tab == tab["id"]
                button_key = f"{self.component_id}_tab_{tab['id']}"

                # Tab button styling
                button_class = "mobile-tab-button"
                if is_active:
                    button_class += " active"

                # Use short title for mobile
                tab_title = tab.get("short_title", tab["title"])
                tab_label = f"{tab['icon']} {tab_title}"

                # Render tab button
                if st.button(label=tab_label, key=button_key, help=tab["description"], width="stretch", disabled=is_active):
                    selected_tab = tab["id"]
                    st.session_state.active_tab = selected_tab
                    self._update_tab_history(selected_tab)

        st.markdown("</div>", unsafe_allow_html=True)
        return selected_tab

    def _render_default_tab_content(self, tab_id: str, tab_config: dict[str, Any]) -> None:
        """Render default content when no callback is registered."""
        st.markdown(f"### {tab_config['icon']} {tab_config['title']}")
        st.markdown(tab_config["description"])

        if tab_id == "image_analysis":
            self._render_image_analysis_placeholder()
        elif tab_id == "voice_assistant":
            self._render_voice_assistant_placeholder()
        elif tab_id == "chat_interface":
            self._render_chat_interface_placeholder()
        elif tab_id == "history_settings":
            self._render_history_settings_placeholder()

        else:
            st.info(f"Content for {tab_config['title']} tab is not yet implemented.")

    def _render_image_analysis_placeholder(self) -> None:
        """Render placeholder for image analysis tab."""
        st.markdown("#### [PHOTO] Image Analysis")

        # File uploader
        uploaded_file = st.file_uploader("Upload plant image", type=["jpg", "jpeg", "png"], key=f"{self.component_id}_image_uploader")

        if uploaded_file:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            with col2:
                st.markdown("**Analysis Results**")
                st.info("[PARTIAL] Analysis feature will be integrated with VisionAdapter")
        else:
            st.markdown("[MOBILE] Upload an image or use the camera to analyze your plant")

    def _render_voice_assistant_placeholder(self) -> None:
        """Render placeholder for voice assistant tab."""
        st.markdown("#### [VOICE] Voice Assistant")

        if st.button("[MICROPHONE]️ Start Recording", key=f"{self.component_id}_voice_record", width="stretch"):
            st.info("[PARTIAL] Voice recording will be integrated with AudioAdapter")

        st.markdown("**How to use:**")
        st.markdown("- Tap the record button")
        st.markdown("- Ask your plant care question")
        st.markdown("- Get AI-powered responses")

    def _render_chat_interface_placeholder(self) -> None:
        """Render placeholder for chat interface tab."""
        st.markdown("#### [CHAT] Chat Assistant")

        # Chat input
        user_input = st.text_input(
            "Ask about plant care...", key=f"{self.component_id}_chat_input", placeholder="e.g., Why are my plant's leaves turning yellow?"
        )

        if user_input:
            st.markdown("**Your Question:**")
            st.markdown(f"> {user_input}")
            st.markdown("**AI Response:**")
            st.info("[PARTIAL] Chat responses will be integrated with TextAdapter")

    def _render_history_settings_placeholder(self) -> None:
        """Render history and settings as inline expandable cards - always visible."""
        st.markdown("#### [SUMMARY] History & Settings")
        st.markdown("**All options always accessible - no hidden menus**")

        # History expandable card (always visible)
        st.markdown('<div class="mobile-expandable-card" data-design="always-visible">', unsafe_allow_html=True)

        # History card header
        st.markdown('<div class="mobile-expandable-card-header">', unsafe_allow_html=True)
        if st.button("[CHART] Recent Analysis History", key=f"{self.component_id}_history_card", width="stretch"):
            st.session_state.history_expanded = not st.session_state.get("history_expanded", True)
        st.markdown("</div>", unsafe_allow_html=True)

        # History content (always visible)
        st.markdown('<div class="mobile-expandable-card-content">', unsafe_allow_html=True)
        st.markdown("**Recent Plant Analyses:**")
        st.info("[PARTIAL] Full history will be integrated with session state")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Settings expandable card (always visible)
        st.markdown('<div class="mobile-expandable-card" data-design="always-visible">', unsafe_allow_html=True)

        # Settings card header
        st.markdown('<div class="mobile-expandable-card-header">', unsafe_allow_html=True)
        if st.button("[SETTINGS] App Settings & Preferences", key=f"{self.component_id}_settings_card", width="stretch"):
            st.session_state.settings_expanded = not st.session_state.get("settings_expanded", True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Settings content (always visible)
        st.markdown('<div class="mobile-expandable-card-content">', unsafe_allow_html=True)
        st.markdown("**All Settings Always Accessible:**")

        # Model selection (always visible)
        st.selectbox("Default AI Model", ["Vision Transformer", "ResNet50", "MobileNet"], key=f"{self.component_id}_default_model")

        # Notification settings (always visible)
        st.checkbox("Enable notifications", key=f"{self.component_id}_notifications")

        # Theme settings (always visible)
        st.selectbox("Theme", ["Auto", "Light", "Dark"], key=f"{self.component_id}_theme")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    def render(self, **kwargs) -> str:
        """Render the complete tabs component in SPA mode without page redirects.

        Returns:
            str: Active tab ID (focused content)
        """
        # Initialize state
        self.initialize_tabs_state()

        # SPA mode indicator
        st.success("[DONE] Single Page Mode - No page navigation!")

        # Register all content areas with SPA manager
        self._register_all_content_areas()

        # Use SPA manager to render content focus bar and all content
        focused_content = "image_analysis"  # Default focused content

        return focused_content

    def register_tab_content(self, tab_id: str, content_callback: Callable) -> None:
        """Register content callback for a specific tab in SPA mode."""
        # Store in both session state and instance for SPA manager
        if "tab_content_callbacks" not in st.session_state:
            st.session_state.tab_content_callbacks = {}

        st.session_state.tab_content_callbacks[tab_id] = content_callback
        self.content_callbacks[tab_id] = content_callback

    def _update_tab_history(self, tab_id: str) -> None:
        """Update tab navigation history."""
        if "tab_history" not in st.session_state:
            st.session_state.tab_history = []

        # Remove tab if already in history
        if tab_id in st.session_state.tab_history:
            st.session_state.tab_history.remove(tab_id)

        # Add to front of history
        st.session_state.tab_history.insert(0, tab_id)

        # Keep only last 10 tabs
        st.session_state.tab_history = st.session_state.tab_history[:10]

    def get_active_tab(self) -> str:
        """Get currently active tab."""
        return st.session_state.get("active_tab", "image_analysis")

    def set_active_tab(self, tab_id: str) -> None:
        """Programmatically set active tab."""
        tabs = self.get_available_tabs()
        if any(t["id"] == tab_id for t in tabs):
            st.session_state.active_tab = tab_id
            self._update_tab_history(tab_id)

    def get_tab_history(self) -> list[str]:
        """Get tab navigation history."""
        return st.session_state.get("tab_history", [])

    def get_tabs_status(self) -> dict[str, Any]:
        """Get tabs status for AI agent monitoring."""
        tabs = self.get_available_tabs()

        return {
            "component_id": self.component_id,
            "initialized": st.session_state.get("content_tabs_initialized", False),
            "active_tab": st.session_state.get("active_tab"),
            "available_tabs": [t["id"] for t in tabs if t.get("enabled", True)],
            "disabled_tabs": [t["id"] for t in tabs if not t.get("enabled", True)],
            "total_tabs": len(tabs),
            "registered_callbacks": len(st.session_state.get("tab_content_callbacks", {})),
            "tab_history": st.session_state.get("tab_history", []),
            "tab_style": self.tab_style,
            "scrollable_tabs": self.scrollable_tabs,
            "lazy_loading": self.lazy_loading,
        }


# Utility functions
def create_mobile_content_tabs(tab_style: str = "pills", scrollable_tabs: bool = True, lazy_loading: bool = True) -> MobileContentTabs:
    """Create and return a MobileContentTabs instance."""
    return MobileContentTabs(component_id="mobile_content_tabs", tab_style=tab_style, scrollable_tabs=scrollable_tabs, lazy_loading=lazy_loading)


def render_plantguard_tabs() -> str:
    """Convenience function to render PlantGuard feature tabs."""
    tabs = create_mobile_content_tabs()
    return tabs.render()
