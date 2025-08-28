"""
Mobile Navigation System

Provides mobile-optimized navigation and routing for PlantGuard mobile interface.
Includes touch-friendly navigation, deep linking, and state management.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class NavigationMode(Enum):
    """Navigation display modes."""

    TABS = "tabs"
    PILLS = "pills"
    BOTTOM_NAV = "bottom_nav"
    SIDEBAR = "sidebar"


@dataclass
class NavigationItem:
    """Navigation item configuration."""

    id: str
    title: str
    icon: str
    description: str
    render_function: Callable | None = None
    enabled: bool = True
    badge_count: int = 0
    requires_auth: bool = False


class MobileNavigationManager:
    """Manages mobile navigation and routing."""

    def __init__(self, navigation_id: str):
        self.navigation_id = navigation_id
        self.navigation_items: dict[str, NavigationItem] = {}
        self.current_route = "home"
        self.navigation_mode = NavigationMode.TABS
        self.navigation_history: list[str] = []

        # Initialize default navigation items
        self._initialize_default_navigation()

    def _initialize_default_navigation(self) -> None:
        """Initialize default navigation items for PlantGuard."""
        default_items = [
            NavigationItem(id="image_analysis", title="Image Analysis", icon="[PHOTO]", description="Analyze plant images for disease detection"),
            NavigationItem(id="voice_assistant", title="Voice Assistant", icon="[VOICE]", description="Voice-powered plant care assistance"),
            NavigationItem(id="chat_interface", title="Chat", icon="[CHAT]", description="Text-based plant care chat"),
            NavigationItem(id="history_settings", title="History & Settings", icon="[SUMMARY]", description="View analysis history and app settings"),
        ]

        for item in default_items:
            self.add_navigation_item(item)

    def add_navigation_item(self, item: NavigationItem) -> None:
        """Add a navigation item."""
        self.navigation_items[item.id] = item
        logger.info(f"Added navigation item: {item.id}")

    def remove_navigation_item(self, item_id: str) -> None:
        """Remove a navigation item."""
        if item_id in self.navigation_items:
            del self.navigation_items[item_id]
            logger.info(f"Removed navigation item: {item_id}")

    def set_navigation_mode(self, mode: NavigationMode) -> None:
        """Set navigation display mode."""
        self.navigation_mode = mode
        logger.info(f"Navigation mode set to: {mode.value}")

    def get_current_route(self) -> str:
        """Get current navigation route."""
        return st.session_state.get(f"{self.navigation_id}_current_route", "image_analysis")

    def set_current_route(self, route: str) -> None:
        """Set current navigation route."""
        if route in self.navigation_items:
            # Add to history
            current = self.get_current_route()
            if current != route:
                self.navigation_history.append(current)
                # Limit history size
                if len(self.navigation_history) > 10:
                    self.navigation_history = self.navigation_history[-10:]

            # Set new route
            st.session_state[f"{self.navigation_id}_current_route"] = route
            self.current_route = route
            logger.info(f"Navigation route changed to: {route}")

    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return len(self.navigation_history) > 0

    def go_back(self) -> str | None:
        """Navigate back to previous route."""
        if self.can_go_back():
            previous_route = self.navigation_history.pop()
            self.set_current_route(previous_route)
            return previous_route
        return None

    def render_navigation(self) -> str | None:
        """Render navigation based on current mode."""
        if self.navigation_mode == NavigationMode.TABS:
            return self._render_tab_navigation()
        elif self.navigation_mode == NavigationMode.PILLS:
            return self._render_pill_navigation()
        elif self.navigation_mode == NavigationMode.BOTTOM_NAV:
            return self._render_bottom_navigation()
        elif self.navigation_mode == NavigationMode.SIDEBAR:
            return self._render_sidebar_navigation()
        else:
            return self._render_tab_navigation()  # Default fallback

    def _render_tab_navigation(self) -> str | None:
        """Render tab-style navigation."""
        current_route = self.get_current_route()

        # Create tab labels
        tab_labels = []
        tab_items = []

        for item_id, item in self.navigation_items.items():
            if item.enabled:
                label = f"{item.icon} {item.title}"
                if item.badge_count > 0:
                    label += f" ({item.badge_count})"
                tab_labels.append(label)
                tab_items.append(item_id)

        # Render tabs
        if tab_labels:
            # Find current tab index
            try:
                current_index = tab_items.index(current_route)
            except ValueError:
                current_index = 0

            selected_tab = st.tabs(tab_labels)[current_index]

            # Handle tab selection
            with selected_tab:
                selected_item_id = tab_items[current_index]
                if selected_item_id != current_route:
                    self.set_current_route(selected_item_id)

                return selected_item_id

        return None

    def _render_pill_navigation(self) -> str | None:
        """Render pill-style navigation."""
        current_route = self.get_current_route()

        # Create navigation pills
        st.markdown(
            """
        <style>
        .nav-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 0.5rem;
            background: #f0f2f6;
            border-radius: 12px;
            margin-bottom: 1rem;
        }
        .nav-pill {
            flex: 1;
            min-width: 120px;
            text-align: center;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            background: transparent;
            border: none;
            font-size: 0.9rem;
        }
        .nav-pill.active {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: #4CAF50;
            font-weight: 600;
        }
        .nav-pill:hover {
            background: rgba(255,255,255,0.5);
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Render pills
        cols = st.columns(len(self.navigation_items))

        selected_route = None

        for i, (item_id, item) in enumerate(self.navigation_items.items()):
            if item.enabled:
                with cols[i]:
                    is_active = item_id == current_route
                    button_type = "primary" if is_active else "secondary"

                    label = f"{item.icon} {item.title}"
                    if item.badge_count > 0:
                        label += f" ({item.badge_count})"

                    if st.button(label, key=f"nav_pill_{item_id}", type=button_type, use_container_width=True, help=item.description):
                        selected_route = item_id

        if selected_route and selected_route != current_route:
            self.set_current_route(selected_route)

        return current_route

    def _render_bottom_navigation(self) -> str | None:
        """Render bottom navigation bar."""
        current_route = self.get_current_route()

        # Bottom navigation CSS
        st.markdown(
            """
        <style>
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-around;
            padding: 0.5rem 0;
            z-index: 1000;
            box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
        }
        .bottom-nav-item {
            flex: 1;
            text-align: center;
            padding: 0.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .bottom-nav-item.active {
            color: #4CAF50;
        }
        .bottom-nav-icon {
            font-size: 1.5rem;
            display: block;
        }
        .bottom-nav-label {
            font-size: 0.7rem;
            margin-top: 0.25rem;
        }
        /* Add bottom padding to main content */
        .main .block-container {
            padding-bottom: 80px;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Render bottom navigation items
        nav_html = '<div class="bottom-nav">'

        for item_id, item in self.navigation_items.items():
            if item.enabled:
                active_class = "active" if item_id == current_route else ""
                badge_html = f'<span class="badge">{item.badge_count}</span>' if item.badge_count > 0 else ""

                nav_html += f"""
                <div class="bottom-nav-item {active_class}" onclick="selectNavItem('{item_id}')">
                    <div class="bottom-nav-icon">{item.icon}</div>
                    <div class="bottom-nav-label">{item.title}{badge_html}</div>
                </div>
                """

        nav_html += "</div>"

        # Add JavaScript for navigation
        nav_html += """
        <script>
        function selectNavItem(itemId) {
            // Send message to Streamlit
            window.parent.postMessage({
                type: 'navigation_change',
                route: itemId
            }, '*');
        }
        </script>
        """

        st.components.v1.html(nav_html, height=0)

        return current_route

    def _render_sidebar_navigation(self) -> str | None:
        """Render sidebar navigation."""
        current_route = self.get_current_route()

        with st.sidebar:
            st.markdown("### [COMPASS] Navigation")

            selected_route = None

            for item_id, item in self.navigation_items.items():
                if item.enabled:
                    is_active = item_id == current_route

                    label = f"{item.icon} {item.title}"
                    if item.badge_count > 0:
                        label += f" ({item.badge_count})"

                    if st.button(
                        label,
                        key=f"sidebar_nav_{item_id}",
                        type="primary" if is_active else "secondary",
                        use_container_width=True,
                        help=item.description,
                    ):
                        selected_route = item_id

            # Back button
            if self.can_go_back():
                if st.button("← Back", use_container_width=True):
                    selected_route = self.go_back()

        if selected_route and selected_route != current_route:
            self.set_current_route(selected_route)

        return current_route

    def render_breadcrumbs(self) -> None:
        """Render navigation breadcrumbs."""
        current_route = self.get_current_route()
        current_item = self.navigation_items.get(current_route)

        if current_item:
            breadcrumb_html = f"""
            <div style='padding: 0.5rem 0; color: #666; font-size: 0.9rem;'>
                [HOME] Home > {current_item.icon} {current_item.title}
            </div>
            """
            st.markdown(breadcrumb_html, unsafe_allow_html=True)

    def render_route_content(self) -> None:
        """Render content for current route."""
        current_route = self.get_current_route()
        current_item = self.navigation_items.get(current_route)

        if current_item and current_item.render_function:
            try:
                current_item.render_function()
            except Exception as e:
                st.error(f"Error rendering {current_item.title}: {e}")
                logger.error(f"Error rendering route {current_route}: {e}")
        else:
            st.warning(f"No content available for {current_route}")

    def set_badge_count(self, item_id: str, count: int) -> None:
        """Set badge count for navigation item."""
        if item_id in self.navigation_items:
            self.navigation_items[item_id].badge_count = count

    def get_navigation_state(self) -> dict[str, Any]:
        """Get current navigation state."""
        return {
            "current_route": self.get_current_route(),
            "navigation_mode": self.navigation_mode.value,
            "history": self.navigation_history.copy(),
            "items": {
                item_id: {"title": item.title, "enabled": item.enabled, "badge_count": item.badge_count}
                for item_id, item in self.navigation_items.items()
            },
        }


# Global navigation manager instance
mobile_navigation_manager = MobileNavigationManager("mobile_nav")
