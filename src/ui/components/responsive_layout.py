"""Responsive Layout System for PlantGuard Streamlit UI.

Implements adaptive layout components that respond to screen size and device capabilities.
Follows ADHD-friendly design principles with clear visual hierarchy and touch-friendly elements.
"""

import logging
from collections.abc import Callable
from typing import Any, Literal

import streamlit as st
import torch

# Module logger
logger = logging.getLogger(__name__)


class ResponsiveLayout:
    """Responsive layout manager for PlantGuard UI.

    Handles desktop (5/7 column split) and mobile (stacked) layouts with
    proper touch targets and Apple Silicon optimization.
    """

    def __init__(self) -> None:
        self.device = self._get_device()
        self.breakpoints = {"mobile": 768, "tablet": 1024, "desktop": 1200}
        self._initialize_layout_state()

    def _get_device(self) -> torch.device:
        """Get optimal device for Apple Silicon optimization."""
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")

    def _initialize_layout_state(self) -> Any:
        """Initialize layout state in session."""
        if "layout_config" not in st.session_state:
            st.session_state.layout_config = {
                "current_viewport": "desktop",
                "mobile_view": False,
                "sidebar_collapsed": False,
                "touch_mode": False,
            }

    def detect_mobile_viewport(self) -> bool:
        """Detect if user is on mobile viewport.

        Uses JavaScript injection to get viewport width.
        Fallback to user agent detection if JS fails.
        """
        try:
            # Use Streamlit's built-in responsive behavior
            # Check if sidebar is auto-collapsed (mobile indicator)
            if hasattr(st, "get_option"):
                try:
                    initial_sidebar = st.get_option("server.initialSidebarState")
                    if initial_sidebar == "collapsed":
                        return True
                except Exception as e:
                    # Preserve diagnostics; avoid silent pass
                    st.warning(f"Failed to read Streamlit option for sidebar state: {e}")
                    logger = logging.getLogger(__name__)
                    logger.debug("get_option failed: %s", e, exc_info=True)

            # Primary method: check session state for mobile preference
            layout_config = st.session_state.get("layout_config", {})
            if "mobile_view" in layout_config:
                return layout_config["mobile_view"]

            # Fallback: assume desktop if detection fails
            return False

        except Exception as e:
            # Graceful degradation: assume desktop if detection fails, but log
            logger = logging.getLogger(__name__)
            logger.debug("Viewport detection failed: %s", e, exc_info=True)
            return False

    def get_layout_config(self) -> dict[str, list[int] | bool | str | float]:
        """Get current layout configuration based on viewport.

        Returns:
            Dict with layout configuration including columns, stacking, and device info
        """
        is_mobile = self.detect_mobile_viewport()
        st.session_state.layout_config["mobile_view"] = is_mobile

        if is_mobile:
            return {
                "columns": [1],  # Single column for mobile
                "stack_vertically": True,
                "device": str(self.device),
                "viewport": "mobile",
                "touch_targets": True,
                "font_scale": 1.1,  # Larger fonts on mobile
            }
        else:
            return {
                "columns": [5, 7],  # Desktop: chat panel (5), analysis (7)
                "stack_vertically": False,
                "device": str(self.device),
                "viewport": "desktop",
                "touch_targets": False,
                "font_scale": 1.0,
            }

    def render_adaptive_columns(self, left_content=None, right_content=None) -> None:
        """Render adaptive columns based on viewport.

        Args:
            left_content: Content for left column (chat panel)
            right_content: Content for right column (analysis panel)
        """
        config = self.get_layout_config()

        if config["stack_vertically"]:
            # Mobile: Stack vertically
            self._render_mobile_layout(left_content, right_content)
        else:
            # Desktop: Side-by-side columns
            self._render_desktop_layout(left_content, right_content, config["columns"])

    def _render_desktop_layout(self, left_content, right_content, columns: list[int]) -> Any:
        """Render desktop layout with specified column ratios."""
        try:
            col1, col2 = st.columns(columns)

            with col1:
                if left_content:
                    self._render_content_with_error_handling(left_content, "Chat Panel")

            with col2:
                if right_content:
                    self._render_content_with_error_handling(right_content, "Analysis Panel")

        except Exception as e:
            st.error(f"Layout rendering failed: {e}")
            # Fallback: render content sequentially
            if left_content:
                left_content()
            if right_content:
                right_content()

    def _render_mobile_layout(self, left_content, right_content) -> Any:
        """Render mobile layout with stacked components."""
        try:
            # Mobile: Input section first, then results, then chat
            if right_content:
                st.markdown("### [SUMMARY] Analysis Results")
                self._render_content_with_error_handling(right_content, "Analysis Results")

            if left_content:
                st.markdown("### [CHAT] Chat Interface")
                self._render_content_with_error_handling(left_content, "Chat Interface")

        except Exception as e:
            st.error(f"Mobile layout rendering failed: {e}")
            # Fallback: render content sequentially
            if left_content:
                left_content()
            if right_content:
                right_content()

    def _render_content_with_error_handling(self, content_func, section_name: str) -> Any:
        """Render content with proper error handling."""
        try:
            if callable(content_func):
                content_func()
            else:
                st.write(content_func)
        except Exception as e:
            st.error(f"{section_name} failed to render: {e}")
            st.info(f"Please refresh the page to restore {section_name} functionality.")

    def render_responsive_container(self, content, container_type: str = "default") -> None:
        """Render responsive container with appropriate styling.

        Args:
            content: Content to render in container
            container_type: Type of container (card, panel, section)
        """
        config = self.get_layout_config()

        # Apply container-specific styling
        container_class = self._get_container_class(container_type, config)

        with st.container():
            # Add CSS class for styling
            st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)

            try:
                if callable(content):
                    content()
                else:
                    st.write(content)
            except Exception as e:
                st.error(f"Container content failed to render: {e}")
            finally:
                st.markdown("</div>", unsafe_allow_html=True)

    def _get_container_class(self, container_type: str, config: dict) -> str:
        """Get appropriate CSS class for container."""
        base_class = "responsive-container"
        type_class = f"container-{container_type}"
        viewport_class = f"viewport-{config['viewport']}"

        classes = [base_class, type_class, viewport_class]

        if config.get("touch_targets"):
            classes.append("touch-friendly")

        return " ".join(classes)

    def render_touch_friendly_button(self, label: str, key: str | None = None, **kwargs) -> bool:
        """Render touch-friendly button with minimum 44px height.

        Args:
            label: Button label
            key: Unique key for button
            **kwargs: Additional button parameters

        Returns:
            Boolean indicating if button was clicked
        """
        config = self.get_layout_config()

        # Ensure minimum touch target size
        if config.get("touch_targets"):
            kwargs.setdefault("use_container_width", True)

        return st.button(label, key=key, **kwargs)

    def render_responsive_grid(self, items: list, columns_per_row: int = 3) -> None:
        """Render responsive grid that adapts to viewport.

        Args:
            items: List of items to render in grid
            columns_per_row: Number of columns for desktop (auto-adjusts for mobile)
        """
        config = self.get_layout_config()

        # Adjust columns for mobile
        if config["stack_vertically"]:
            columns_per_row = 1  # Single column on mobile
        elif config["viewport"] == "tablet":
            columns_per_row = min(2, columns_per_row)  # Max 2 columns on tablet

        # Render grid
        for i in range(0, len(items), columns_per_row):
            cols = st.columns(columns_per_row)

            for j, item in enumerate(items[i : i + columns_per_row]):
                with cols[j]:
                    try:
                        if callable(item):
                            item()
                        else:
                            st.write(item)
                    except Exception as e:
                        st.error(f"Grid item {i + j} failed to render: {e}")

    def apply_mobile_optimizations(self) -> Any:
        """Apply mobile-specific optimizations."""
        config = self.get_layout_config()

        if config["stack_vertically"]:
            # Inject mobile-specific CSS
            mobile_css = """
            <style>
            /* Mobile optimizations */
            .stButton > button {
                min-height: 48px !important;
                font-size: 18px !important;
                padding: 16px 24px !important;
            }

            .stSelectbox > div > div {
                min-height: 48px !important;
            }

            .stTextInput > div > div > input {
                min-height: 48px !important;
                font-size: 16px !important;
            }

            /* Improve touch targets */
            .stCheckbox > label {
                min-height: 44px !important;
                padding: 8px !important;
            }

            .stRadio > label {
                min-height: 44px !important;
                padding: 8px !important;
            }

            /* Improve readability */
            .stMarkdown {
                font-size: 16px !important;
                line-height: 1.6 !important;
            }

            /* Add spacing for touch scrolling */
            .main > div {
                padding-bottom: 100px !important;
            }
            </style>
            """
            st.markdown(mobile_css, unsafe_allow_html=True)

    def render_mobile_navigation(self, pages: dict[str, Callable]) -> None:
        """Render mobile-friendly navigation.

        Args:
            pages: Dictionary of page names and functions
        """
        config = self.get_layout_config()

        if config["stack_vertically"]:
            # Mobile: Use selectbox for navigation
            selected_page = st.selectbox("Navigate to:", options=list(pages.keys()), key="mobile_nav")
            return selected_page
        else:
            # Desktop: Use regular tabs or navigation
            return st.selectbox("Page:", list(pages.keys()), key="desktop_nav")

    def get_responsive_image_width(self) -> str:
        """Get appropriate image width for current viewport."""
        config = self.get_layout_config()

        if config["stack_vertically"]:
            return "100%"  # Full width on mobile
        else:
            return "auto"  # Auto width on desktop

    # Accessibility controls removed per user request


class ResponsiveLayoutManager:
    """Singleton manager for responsive layout across the application."""

    _instance = None

    def __init__(self) -> None:
        """Initialize the layout manager."""
        if not hasattr(self, "layout"):
            self.layout: ResponsiveLayout = ResponsiveLayout()

    def __new__(cls) -> Any:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.layout = ResponsiveLayout()
        return cls._instance

    def get_layout(self) -> ResponsiveLayout:
        """Get the responsive layout instance."""
        return self.layout

    def configure_page_layout(
        self,
        page_title: str = "PlantGuard",
        layout: Literal["centered", "wide"] = "wide",
        initial_sidebar_state: Literal["auto", "expanded", "collapsed"] = "auto",
    ):
        """Configure Streamlit page layout with responsive settings.

        Args:
            page_title: Page title
            layout: Streamlit layout mode
            initial_sidebar_state: Initial sidebar state
        """
        try:
            # Force a static sidebar: always expanded when 'auto' is used.
            # This removes the expanded/collapsed toggle behavior so the
            # sidebar remains visible across viewports.
            if initial_sidebar_state == "auto":
                initial_sidebar_state = "expanded"

            st.set_page_config(
                page_title=page_title,
                page_icon="[LEAF]",
                layout=layout,
                initial_sidebar_state=initial_sidebar_state,
                menu_items={"About": ("PlantGuard - AI-powered plant disease detection with offline processing")},
            )

            # Apply mobile optimizations if needed
            self.layout.apply_mobile_optimizations()

        except Exception as e:
            # Graceful degradation if page config fails
            st.warning(f"Layout configuration failed: {e}")


# Convenience functions for easy import
def get_responsive_layout() -> ResponsiveLayout:
    """Get responsive layout instance."""
    return ResponsiveLayoutManager().get_layout()


def configure_responsive_page(**kwargs) -> Any:
    """Configure responsive page layout."""
    return ResponsiveLayoutManager().configure_page_layout(**kwargs)


def render_adaptive_layout(left_content=None, right_content=None) -> None:
    """Render adaptive layout with provided content."""
    layout = get_responsive_layout()
    return layout.render_adaptive_columns(left_content, right_content)
