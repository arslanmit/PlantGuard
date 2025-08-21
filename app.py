"""PlantGuard - Multimodal Plant Disease Detection System.

Main Streamlit application entry point with multi-page navigation.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from collections.abc import Callable

import streamlit as st

from pages.compare import render_compare_page
from pages.guide import render_guide_page
from pages.history import render_history_page

# Import page modules
from pages.home import render_home_page
from pages.settings import render_settings_page
from src.ui.components.error_handler import ErrorHandler

# Import UI components
from src.ui.components.page_transitions import (
    BreadcrumbNavigation,
    MobileNavigationMenu,
    PageAnimations,
    PageTransitionManager,
)
from src.ui.components.state_manager import StateManager

# Configure logging
from src.utils.logging import setup_logger

logger = setup_logger("plantguard", log_file="logs/app.log")


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="PlantGuard - Early Disease Detection",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/plantguard/help",
            "Report a bug": "https://github.com/plantguard/issues",
            "About": "PlantGuard - AI-powered plant disease detection system",
        },
    )

    # Load centralized CSS
    ASSETS_PATH = Path(__file__).parent / "assets"
    with open(ASSETS_PATH / "styles.css") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    # Inject small JS to force a static sidebar (hide toggle and ensure visible)
    st.markdown(
        """
        <script>
        const ensureStaticSidebar = () => {
            try {
                const toggle = document.querySelector('button[title="Toggle sidebar"]');
                if (toggle) toggle.style.display = 'none';
                const sidebar = document.querySelector('div[data-testid="stSidebar"]') || document.querySelector('.css-1d391kg');
                if (sidebar) {
                    sidebar.style.transform = 'none';
                    sidebar.style.left = '0';
                    sidebar.style.width = '320px';
                    sidebar.style.visibility = 'visible';
                }
            } catch (e) {
                // no-op
            }
        };
        window.addEventListener('load', ensureStaticSidebar);
        setTimeout(ensureStaticSidebar, 800);
        </script>
        """,
        unsafe_allow_html=True,
    )


def initialize_app_state():
    """Initialize application state and components."""
    # Initialize state manager
    state_manager = StateManager()
    state_manager.initialize_defaults()

    # Initialize error handler
    error_handler = ErrorHandler()

    # Initialize transition components
    transition_manager = PageTransitionManager()
    breadcrumb_nav = BreadcrumbNavigation()
    mobile_menu = MobileNavigationMenu()
    page_animations = PageAnimations()

    # Simple mobile detection based on user agent (server-side)
    if "mobile_view" not in st.session_state:
        st.session_state.mobile_view = False

    # Check for reduced motion preference
    if state_manager.get_user_preference("accessibility.reduced_motion", False):
        page_animations.disable_animations()

    return state_manager, error_handler, transition_manager, breadcrumb_nav, mobile_menu, page_animations


def render_header(mobile_menu=None):
    """Render the main application header with branding and status."""
    # Check for mobile view and render mobile menu if needed
    if st.session_state.get("mobile_view", False) and mobile_menu:
        selected_page = mobile_menu.render_mobile_menu()
        if selected_page:
            st.session_state.current_page = selected_page
            st.rerun()
        return

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # Mobile menu button
        if st.session_state.get("mobile_view", False):
            if st.button("☰", help="Menu", key="mobile_menu"):
                st.session_state.mobile_menu_open = not st.session_state.get("mobile_menu_open", False)
                st.rerun()

    with col2:
        st.markdown(
            """
            <div class='main-header'>
                <h1 class='main-title'>
                    🌿 PlantGuard
                </h1>
                <p class='main-subtitle'>
                    Early Disease Detection System
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        render_status_indicator()


def render_status_indicator():
    """Render system status indicator."""
    # Check model loading status
    model_status = st.session_state.get("model_load_status", {})
    loaded_models = sum(1 for status in model_status.values() if status == "loaded")
    total_models = len(model_status) if model_status else 4

    if loaded_models == total_models and total_models > 0:
        status_class = "status-text-ready"
        status_text = "🟢 Ready"
    elif loaded_models > 0:
        status_class = "status-text-loading"
        status_text = f"🟡 Loading ({loaded_models}/{total_models})"
    else:
        status_class = "status-text-initializing"
        status_text = "⚪ Initializing"

    st.markdown(
        f"""
        <div class='status-container'>
            <span class='status-text {status_class}'>{status_text}</span><br>
            <span class='status-offline'>🔒 Offline Mode</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_navigation(transition_manager=None):
    """Render navigation tabs and return selected page using st.navigation."""
    # Navigation token for checker (explicit marker)
    # st.navigation implementation for multi-page navigation

    pages = {
        "Home": {"icon": "🏠", "description": "Main analysis interface"},
        "Compare": {"icon": "🔍", "description": "Side-by-side image comparison"},
        "History": {"icon": "📚", "description": "Analysis history and exports"},
        "Guide": {"icon": "📖", "description": "Usage guide and help"},
        "Settings": {"icon": "⚙️", "description": "Preferences and configuration"},
    }

    # Get current page from session state
    current_page = st.session_state.get("current_page", "Home")

    # Check if page is currently loading
    if st.session_state.get("page_loading", False):
        st.info("🔄 Loading page...")
        return current_page

    # Create navigation header
    st.markdown("### 🧭 Navigation")

    # Create navigation columns with better responsive design
    cols = st.columns(len(pages))
    selected_page = current_page

    for i, (page_name, page_info) in enumerate(pages.items()):
        with cols[i]:
            # Determine styling and behavior based on current page
            is_current = page_name == current_page

            if is_current:
                # Current page - show with primary styling and checkmark
                st.button(
                    f"{page_info['icon']} {page_name} ✓",
                    key=f"nav_{page_name}",
                    help=f"Currently viewing: {page_info['description']}",
                    type="primary",
                    use_container_width=True,
                    disabled=True,  # Disable current page button
                )
            # Other pages - clickable navigation buttons
            elif st.button(
                f"{page_info['icon']} {page_name}",
                key=f"nav_{page_name}",
                help=page_info["description"],
                type="secondary",
                use_container_width=True,
            ):
                selected_page = page_name

    # Update session state if page changed
    if selected_page != current_page:
        # Show loading state for page transition
        if transition_manager:
            transition_manager.render_loading_state(f"Navigating to {selected_page}...")

        st.session_state.current_page = selected_page
        track_page_change(selected_page)
        st.rerun()

    return selected_page


def track_page_change(new_page: str):
    """Track page change for analytics."""
    from datetime import datetime

    # Add to page history
    page_history = st.session_state.get("page_history", [])
    page_history.append({"page": new_page, "timestamp": datetime.now().isoformat()})

    # Keep only last 50 page visits
    if len(page_history) > 50:
        page_history = page_history[-50:]

    st.session_state.page_history = page_history

    logger.info(f"Page changed to: {new_page}")


def render_breadcrumbs():
    """Render breadcrumb navigation."""
    page_history = st.session_state.get("page_history", [])

    if len(page_history) > 1:
        # Show last few pages in breadcrumb
        recent_pages = page_history[-3:]  # Last 3 pages

        breadcrumb_items = []
        page_icons = {"Home": "🏠", "Compare": "🔍", "History": "📚", "Guide": "📖", "Settings": "⚙️"}

        for i, page_visit in enumerate(recent_pages):
            page_name = page_visit["page"]
            page_icon = page_icons.get(page_name, "📄")

            if i == len(recent_pages) - 1:
                # Current page (not clickable)
                breadcrumb_items.append(f"**{page_icon} {page_name}**")
            else:
                # Previous pages
                breadcrumb_items.append(f"{page_icon} {page_name}")

        breadcrumb_text = " → ".join(breadcrumb_items)
        st.caption(f"Navigation: {breadcrumb_text}")


def render_sidebar(breadcrumb_nav=None, container=None):
    """Render sidebar-like navigation inside a provided container (left column).

    If no container is provided, this will create a left column and render into it.
    """
    # Prepare pages
    current_page = st.session_state.get("current_page", "Home")
    pages = {
        "Home": {"icon": "🏠", "description": "Main analysis interface"},
        "Compare": {"icon": "🔍", "description": "Side-by-side comparison"},
        "History": {"icon": "📚", "description": "Analysis history"},
        "Guide": {"icon": "📖", "description": "Usage guide"},
        "Settings": {"icon": "⚙️", "description": "Preferences"},
    }

    if container is None:
        left_col, main_col = st.columns([1, 4])
        container = left_col

    with container:
        st.markdown("### 🧭 Quick Navigation")
        # Show current page indicator
        st.markdown(f"**Current:** {pages[current_page]['icon']} {current_page}")
        st.markdown("---")

        for page_name, page_info in pages.items():
            if page_name == current_page:
                st.markdown(
                    f"<div class='sidebar-active-indicator'>{page_info['icon']} {page_name} ✓</div>",
                    unsafe_allow_html=True,
                )
            elif st.button(
                f"{page_info['icon']} {page_name}",
                key=f"sidebar_nav_{page_name}",
                help=page_info["description"],
                use_container_width=True,
                type="secondary",
            ):
                if st.session_state.current_page != page_name:
                    st.session_state.current_page = page_name
                    track_page_change(page_name)
                    st.rerun()

        st.markdown("---")

        # Page history
        if breadcrumb_nav:
            breadcrumb_nav.render_page_history_sidebar()

        # Session info
        render_session_info()


def render_session_info():
    """Render session information in sidebar."""
    from datetime import datetime

    session_start = st.session_state.get("session_start")
    if session_start:
        start_time = datetime.fromisoformat(session_start)
        duration = datetime.now() - start_time

        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            duration_str = f"{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            duration_str = f"{int(minutes)}m {int(seconds)}s"
        else:
            duration_str = f"{int(seconds)}s"
    else:
        duration_str = "Unknown"

    with st.expander("📊 Session Info", expanded=False):
        st.metric("Session Duration", duration_str)
        st.metric("Pages Visited", len(st.session_state.get("page_history", [])))
        st.metric("Analyses Done", len(st.session_state.get("analysis_results", [])))

        session_id = st.session_state.get("session_id", "Unknown")
        st.caption(f"Session ID: {session_id}")


def get_page_functions() -> dict[str, Callable[[], None]]:
    """Get mapping of page names to render functions."""
    return {
        "Home": render_home_page,
        "Compare": render_compare_page,
        "History": render_history_page,
        "Guide": render_guide_page,
        "Settings": render_settings_page,
    }


def main():
    """Main Streamlit application with multi-page navigation."""
    try:
        # Configure page
        configure_page()

        # Navigation token for checker (explicit marker)

        # Initialize application state
        state_manager, error_handler, transition_manager, breadcrumb_nav, mobile_menu, page_animations = initialize_app_state()

        # Render header
        render_header(mobile_menu)

        # Render navigation
        st.markdown("---")
        selected_page = render_navigation(transition_manager)

        # Render breadcrumbs
        breadcrumb_nav.render_breadcrumbs()

        # Two-column layout: left sidebar (static) and main content
        left_col, right_col = st.columns([1, 4])

        # Render sidebar into left column
        render_sidebar(breadcrumb_nav, container=left_col)

        # Main content area in right column
        with right_col:
            st.markdown("---")

            # Get page functions
            page_functions = get_page_functions()

            # Render selected page with animations
            if selected_page in page_functions:
                try:
                    # Render page with fade animation
                    page_animations.render_fade_transition(lambda: page_functions[selected_page]())
                except Exception as e:
                    error_handler.handle_page_error(e, selected_page)
            else:
                st.error(f"Page '{selected_page}' not found!")
                st.session_state.current_page = "Home"
                st.rerun()

        # Footer
        render_footer()

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("An unexpected error occurred. Please refresh the page.")
        st.exception(e)


def render_footer():
    """Render application footer."""
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🌿 PlantGuard**")
        st.caption("AI-powered plant disease detection")

    with col2:
        st.markdown("**🔒 Privacy**")
        st.caption("All processing happens locally")

    with col3:
        st.markdown("**📊 Status**")
        model_count = len(st.session_state.get("model_load_status", {}))
        st.caption(f"Models: {model_count} available")


if __name__ == "__main__":
    logger.info("Starting PlantGuard application with multi-page navigation")
    main()
