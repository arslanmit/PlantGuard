"""Page Transitions Component for PlantGuard Redesigned UI.

Handles page transition animations, loading states, and smooth navigation
between different pages in the application.
"""

import logging
import time

import streamlit as st

logger = logging.getLogger(__name__)


class PageTransitionManager:
    """Manages page transitions and loading states."""

    def __init__(self):
        self.transition_duration = 0.3  # seconds
        self.loading_messages = [
            "🌱 Loading PlantGuard...",
            "🔍 Preparing analysis tools...",
            "📊 Setting up interface...",
            "✨ Almost ready...",
        ]

    def render_page_transition(self, from_page: str, to_page: str) -> None:
        """Render page transition animation."""
        # Show transition overlay
        self._render_transition_overlay(from_page, to_page)

        # Simulate transition delay for smooth UX
        time.sleep(0.1)

    def _render_transition_overlay(self, from_page: str, to_page: str) -> None:
        """Render transition overlay with animation."""
        transition_html = f"""
        <div style='
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            animation: fadeIn 0.2s ease-in-out;
        '>
            <div style='
                text-align: center;
                color: #22C55E;
                font-size: 2rem;
                margin-bottom: 1rem;
            '>
                🌿 PlantGuard
            </div>
            <div style='
                color: #64748B;
                font-size: 1rem;
                margin-bottom: 2rem;
            '>
                Navigating from {from_page} to {to_page}...
            </div>
            <div style='
                width: 200px;
                height: 4px;
                background: #1E293B;
                border-radius: 2px;
                overflow: hidden;
            '>
                <div style='
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, #22C55E, #10B981);
                    animation: slideIn 0.3s ease-in-out;
                '></div>
            </div>
        </div>

        <style>
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        @keyframes slideIn {{
            from {{ transform: translateX(-100%); }}
            to {{ transform: translateX(0); }}
        }}
        </style>
    """

        # Note: In a real Streamlit app, we can't inject this kind of overlay
        # This is a conceptual implementation. We'll display the HTML via st.markdown
        # to keep behavior consistent with the original intent.
        st.markdown(transition_html, unsafe_allow_html=True)
        return

    def render_loading_state(self, message: str | None = None) -> None:
        """Render loading state with spinner and message."""
        if message is None:
            import secrets

            message = secrets.choice(self.loading_messages)

        with st.spinner(message):
            # Add a small delay for visual feedback
            time.sleep(0.2)

    def render_page_loading_indicator(self) -> None:
        """Render page loading indicator."""
        from .state_manager import StateManager

        state_manager = StateManager()

        if state_manager.is_page_loading():
            transition_info = state_manager.get_page_transition_info()
            from_page = transition_info.get("from", "Unknown")
            to_page = transition_info.get("to", "Unknown")

            # Show loading bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Animate progress bar
            for i in range(101):
                progress_bar.progress(i)
                if i < 30:
                    status_text.text(f"🔄 Leaving {from_page}...")
                elif i < 70:
                    status_text.text(f"🚀 Navigating to {to_page}...")
                else:
                    status_text.text(f"✨ Loading {to_page}...")

                time.sleep(0.01)  # Small delay for animation

            # Clear loading state
            progress_bar.empty()
            status_text.empty()
            state_manager.complete_page_transition()

    def create_smooth_transition(self, target_page: str) -> None:
        """Create smooth transition to target page."""
        from .state_manager import StateManager

        state_manager = StateManager()
        current_page = state_manager.get_state("current_page", "Home")

        if current_page != target_page:
            # Start transition
            state_manager._track_page_transition(target_page)

            # Show loading indicator
            self.render_loading_state(f"Navigating to {target_page}...")

            # Update page
            state_manager.set_state("current_page", target_page)

            # Complete transition
            state_manager.complete_page_transition()


class BreadcrumbNavigation:
    """Handles breadcrumb navigation and page history."""

    def __init__(self):
        self.max_breadcrumb_items = 5

    def render_breadcrumbs(self) -> None:
        """Render breadcrumb navigation."""
        from .state_manager import StateManager

        state_manager = StateManager()
        page_history = state_manager.get_state("page_history", [])

        if len(page_history) <= 1:
            return

        # Get recent pages for breadcrumb
        recent_pages = self._get_breadcrumb_pages(page_history)

        if not recent_pages:
            return

        # Render breadcrumb
        breadcrumb_html = self._create_breadcrumb_html(recent_pages)
        st.markdown(breadcrumb_html, unsafe_allow_html=True)

    def _get_breadcrumb_pages(self, page_history: list) -> list:
        """Get pages for breadcrumb display."""
        if len(page_history) <= 1:
            return []

        # Get unique pages in order, keeping only the most recent visit to each page
        seen_pages = set()
        unique_pages = []

        # Process in reverse to keep most recent visits
        for page_visit in reversed(page_history):
            page_name = page_visit["page"]
            if page_name not in seen_pages:
                unique_pages.append(page_visit)
                seen_pages.add(page_name)

        # Reverse back to chronological order and limit
        unique_pages.reverse()
        return unique_pages[-self.max_breadcrumb_items :]

    def _create_breadcrumb_html(self, pages: list) -> str:
        """Create HTML for breadcrumb navigation."""
        page_icons = {"Home": "🏠", "Compare": "🔍", "History": "📚", "Guide": "📖", "Settings": "⚙️"}

        breadcrumb_items = []

        for i, page_visit in enumerate(pages):
            page_name = page_visit["page"]
            page_icon = page_icons.get(page_name, "📄")

            if i == len(pages) - 1:
                # Current page (highlighted)
                breadcrumb_items.append(f'<span style="color: #22C55E; font-weight: 600;">{page_icon} {page_name}</span>')
            else:
                # Previous pages (clickable would require JavaScript)
                breadcrumb_items.append(f'<span style="color: #64748B;">{page_icon} {page_name}</span>')

        breadcrumb_text = ' <span style="color: #64748B;">→</span> '.join(breadcrumb_items)

        return f"""
        <div style='
            background: #1E293B;
            border: 1px solid #22C55E30;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            margin: 0.5rem 0;
            font-size: 0.875rem;
        '>
            <span style="color: #64748B;">📍 Navigation:</span> {breadcrumb_text}
        </div>
        """

    def render_page_history_sidebar(self) -> None:
        """Render page history in sidebar."""
        from .state_manager import StateManager

        state_manager = StateManager()
        page_history = state_manager.get_state("page_history", [])

        if not page_history:
            return

        with st.expander("📚 Page History", expanded=False):
            # Show last 10 page visits
            recent_visits = page_history[-10:]

            for visit in reversed(recent_visits):
                page_name = visit["page"]
                timestamp = visit["timestamp"]

                # Format timestamp
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M:%S")
                except (ValueError, TypeError):
                    time_str = timestamp[:8]

                # Create clickable history item (conceptual - would need JavaScript)
                col1, col2 = st.columns([3, 1])

                with col1:
                    page_icons = {"Home": "🏠", "Compare": "🔍", "History": "📚", "Guide": "📖", "Settings": "⚙️"}
                    icon = page_icons.get(page_name, "📄")
                    st.markdown(f"{icon} {page_name}")

                with col2:
                    st.caption(time_str)


class MobileNavigationMenu:
    """Handles mobile-friendly navigation menu."""

    def __init__(self):
        self.is_mobile = self._detect_mobile_view()

    def _detect_mobile_view(self) -> bool:
        """Detect if user is on mobile device."""
        # In a real implementation, this would use JavaScript to detect screen size
        # For now, we'll use a session state flag
        return st.session_state.get("mobile_view", False)

    def render_mobile_menu(self) -> str | None:
        """Render mobile hamburger menu."""
        if not self.is_mobile:
            return None

        # Mobile menu toggle
        menu_open = st.session_state.get("mobile_menu_open", False)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("☰", key="mobile_menu_toggle", help="Menu"):
                st.session_state.mobile_menu_open = not menu_open
                st.rerun()

        with col2:
            st.markdown(
                """
                <div style='text-align: center;'>
                    <h2 style='margin: 0; color: #22C55E;'>🌿 PlantGuard</h2>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Mobile menu overlay
        if st.session_state.get("mobile_menu_open", False):
            return self._render_mobile_menu_overlay()

        return None

    def _render_mobile_menu_overlay(self) -> str | None:
        """Render mobile menu overlay."""
        pages = {
            "Home": {"icon": "🏠", "description": "Main analysis interface"},
            "Compare": {"icon": "🔍", "description": "Side-by-side comparison"},
            "History": {"icon": "📚", "description": "Analysis history"},
            "Guide": {"icon": "📖", "description": "Usage guide"},
            "Settings": {"icon": "⚙️", "description": "Preferences"},
        }

        st.markdown("### 📱 Navigation Menu")

        selected_page = None

        for page_name, page_info in pages.items():
            if st.button(
                f"{page_info['icon']} {page_name}",
                key=f"mobile_nav_{page_name}",
                help=page_info["description"],
                use_container_width=True,
            ):
                selected_page = page_name
                st.session_state.mobile_menu_open = False

        # Close menu button
        if st.button("❌ Close Menu", key="close_mobile_menu", use_container_width=True):
            st.session_state.mobile_menu_open = False
            st.rerun()

        return selected_page

    def render_mobile_navigation_bar(self) -> str | None:
        """Render mobile bottom navigation bar."""
        if not self.is_mobile:
            return None

        pages = ["Home", "Compare", "History", "Guide", "Settings"]
        page_icons = {"Home": "🏠", "Compare": "🔍", "History": "📚", "Guide": "📖", "Settings": "⚙️"}

        current_page = st.session_state.get("current_page", "Home")

        # Create bottom navigation
        cols = st.columns(len(pages))
        selected_page = None

        for i, page_name in enumerate(pages):
            with cols[i]:
                icon = page_icons.get(page_name, "📄")
                button_type = "primary" if page_name == current_page else "secondary"

                if st.button(
                    icon,
                    key=f"mobile_bottom_nav_{page_name}",
                    help=page_name,
                    type=button_type,  # type: ignore[arg-type]
                    use_container_width=True,
                ):
                    selected_page = page_name

        return selected_page


class PageAnimations:
    """Handles page transition animations and effects."""

    def __init__(self):
        self.animation_enabled = True

    def render_fade_transition(self, content_func, duration: float = 0.3):
        """Render content with fade transition."""
        if not self.animation_enabled:
            content_func()
            return

        # Conceptual fade animation
        # In practice, Streamlit doesn't support CSS animations directly
        # This would be implemented with custom CSS/JavaScript

        fade_css = f"""
        <style>
        .fade-in {{
            animation: fadeIn {duration}s ease-in-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        </style>
        """

        st.markdown(fade_css, unsafe_allow_html=True)

        # Wrap content in fade container
        with st.container():
            st.markdown('<div class="fade-in">', unsafe_allow_html=True)
            content_func()
            st.markdown("</div>", unsafe_allow_html=True)

    def render_slide_transition(self, content_func, direction: str = "left"):
        """Render content with slide transition."""
        if not self.animation_enabled:
            content_func()
            return

        # Conceptual slide animation
        slide_css = f"""
        <style>
        .slide-in-{direction} {{
            animation: slideIn{direction.title()} 0.3s ease-in-out;
        }}

        @keyframes slideIn{direction.title()} {{
            from {{
                opacity: 0;
                transform: translateX({"-100%" if direction == "left" else "100%"});
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        </style>
        """

        st.markdown(slide_css, unsafe_allow_html=True)

        with st.container():
            st.markdown(f'<div class="slide-in-{direction}">', unsafe_allow_html=True)
            content_func()
            st.markdown("</div>", unsafe_allow_html=True)

    def disable_animations(self):
        """Disable animations for accessibility."""
        self.animation_enabled = False

    def enable_animations(self):
        """Enable animations."""
        self.animation_enabled = True
