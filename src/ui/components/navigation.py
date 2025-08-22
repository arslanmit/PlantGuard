"""Navigation Header Component for PlantGuard Redesigned UI.

Provides multi-page navigation with responsive design and accessibility features.
"""

import contextlib
import logging

import streamlit as st

logger = logging.getLogger(__name__)


class NavigationHeader:
    """Navigation header component with multi-page support."""

    def __init__(self):
        self.pages = {
            "Home": {
                "icon": "🏠",
                "description": "Main analysis interface",
                "keywords": ["chat", "analyze", "main", "home"],
            },
            "Compare": {
                "icon": "🔍",
                "description": "Side-by-side image comparison",
                "keywords": ["compare", "diff", "before", "after"],
            },
            "History": {
                "icon": "📚",
                "description": "Analysis history and exports",
                "keywords": ["history", "past", "export", "results"],
            },
            "Guide": {
                "icon": "📖",
                "description": "Usage guide and help",
                "keywords": ["help", "guide", "tips", "faq"],
            },
            "Settings": {
                "icon": "⚙️",
                "description": "Preferences and configuration",
                "keywords": ["settings", "config", "preferences", "theme"],
            },
            "Accessibility": {
                "icon": "♿",
                "description": "Accessibility testing and validation",
                "keywords": ["accessibility", "a11y", "test", "validation", "adhd"],
            },
        }

    def render(self) -> str:
        """Render navigation header and return selected page."""
        # Get current page from session state
        current_page = st.session_state.get("current_page", "Home")

        # Decide layout based on device (mobile vs desktop)
        if not self._is_mobile_view():
            # Desktop / wide view: show a persistent left navigation column
            left_col, right_col = st.columns([1, 4])

            # Render navigation into the left column
            selected_page = current_page
            with left_col:
                st.markdown("### 🧭 Navigation")

                for page_name, page_info in self.pages.items():
                    button_type = "primary" if page_name == current_page else "secondary"

                    if st.button(
                        f"{page_info['icon']} {page_name}",
                        key=f"sidebar_nav_{page_name}",
                        help=page_info["description"],
                        type=button_type,
                        use_container_width=True,
                    ):
                        selected_page = page_name
                        # Defer actual navigation to avoid race with frontend component messages
                        st.session_state["__nav_pending"] = page_name

                st.markdown("---")

                # Page search
                search_result = self.render_page_search()
                if search_result:
                    selected_page = search_result
                    st.session_state["__nav_pending"] = search_result

                # Session info and status indicator
                nav = NavigationSidebar()
                with contextlib.suppress(Exception):
                    nav._render_session_info()

                try:
                    nav._render_status_indicator()
                except Exception:
                    logger.exception("Failed to render status indicator")

            # Render header and tabs in the right column
            with right_col:
                try:
                    self._render_header()
                except Exception:
                    logger.exception("Header rendering failed, using fallback title")
                    st.title("PlantGuard")

                selected_page = self._render_navigation_tabs(current_page)
        else:
            # Mobile view
            self._render_header()
            self._render_mobile_hamburger_menu()
            selected_page = self.render_collapsible_navigation()

        # Update session state if page changed
        if selected_page != current_page:
            st.session_state.current_page = selected_page
            self._track_page_change(selected_page)

        # Apply any pending navigation deferred during this render
        pending = st.session_state.pop("__nav_pending", None) if "__nav_pending" in st.session_state else None
        if pending and pending != st.session_state.get("current_page"):
            st.session_state.current_page = pending
            self._track_page_change(pending)
            # Use getattr to avoid mypy complaining about optional experimental API
            rerun_fn = getattr(st, "experimental_rerun", None)
            if callable(rerun_fn):
                try:
                    rerun_fn()
                except Exception:
                    try:
                        st.rerun()
                    except Exception:
                        logger.exception("Both experimental_rerun and rerun failed during navigation")
            else:
                try:
                    st.rerun()
                except Exception:
                    logger.exception("Failed to rerun after navigation change")

        return selected_page

    def _render_status_indicator_impl(self) -> None:
        """Internal implementation: render system status indicator."""
        # Check model loading status
        model_status = st.session_state.get("model_load_status", {})
        loaded_models = sum(1 for status in model_status.values() if status == "loaded")
        total_models = len(model_status)

        if total_models == 0:
            status_text = "6aa Initializing"
        elif loaded_models == total_models:
            status_text = "3f2 Ready"
        elif loaded_models > 0:
            status_text = f"3e1 Loading ({loaded_models}/{total_models})"
        else:
            status_text = "6aa Initializing"

        st.markdown(
            f"""
            <div class='status-container'>
                <span class='status-text'>{status_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Backwards-compatible small helpers expected by callers elsewhere
    def _render_header(self) -> None:
        """Lightweight header renderer used by the navigation layout."""
        try:
            st.title("PlantGuard")
        except Exception:
            # Defensive: ignore in headless contexts
            logger.debug("_render_header failed", exc_info=True)

    def _render_status_indicator(self) -> None:
        """Expose status indicator rendering for other components to call."""
        # Delegate to the impl to avoid no-redef/name collisions
        self._render_status_indicator_impl()

    def _render_navigation_tabs(self, current_page: str) -> str:
        """Render navigation tabs and return selected page."""
        # Create tab names from available pages
        tab_names = list(self.pages.keys())

        # Ensure current_page is valid
        try:
            _current_index = tab_names.index(current_page)
        except ValueError:
            _current_index = 0
            current_page = tab_names[0]

        # Render divider
        st.markdown("---")

        # Use columns for tab-like buttons so we can react to clicks immediately
        cols = st.columns(len(tab_names))
        selected_page = current_page

        for i, (page_name, page_info) in enumerate(self.pages.items()):
            with cols[i]:
                button_type = "primary" if page_name == current_page else "secondary"

                if st.button(
                    f"{page_info['icon']} {page_name}",
                    key=f"nav_{page_name}",
                    help=page_info["description"],
                    type=button_type,  # type: ignore[arg-type]
                    use_container_width=True,
                ):
                    selected_page = page_name

        return selected_page

    def _is_mobile_view(self) -> bool:
        """Check if current view is mobile based on viewport width detection."""
        # Initialize mobile detection if not present
        if "mobile_view" not in st.session_state:
            # Default mobile detection (can be enhanced with JavaScript)
            st.session_state.mobile_view = False

        # Check if mobile view was detected (this would be set by JavaScript in real implementation)
        return st.session_state.get("mobile_view", False)

    def _render_mobile_hamburger_menu(self):
        """Render mobile hamburger menu with collapsible navigation."""
        # Initialize hamburger menu state
        if "hamburger_menu_open" not in st.session_state:
            st.session_state.hamburger_menu_open = False

        # Hamburger menu button with enhanced styling
        hamburger_button_html = """
        <div style='
            width: 44px;
            height: 44px;
            border: 2px solid #22C55E;
            border-radius: 8px;
            background: #22C55E15;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 8px;
        '>
            <span style='
                font-size: 18px;
                color: #22C55E;
                font-weight: bold;
            '>☰</span>
        </div>
        """

        st.markdown(hamburger_button_html, unsafe_allow_html=True)

        if st.button("☰ Menu", key="hamburger_menu_btn", help="Open navigation menu", use_container_width=True):
            st.session_state.hamburger_menu_open = not st.session_state.hamburger_menu_open

        # Render collapsible menu if open
        if st.session_state.hamburger_menu_open:
            self._render_collapsible_mobile_menu()

    def _render_collapsible_mobile_menu(self):
        """Render the collapsible mobile navigation menu."""
        current_page = st.session_state.get("current_page", "Home")

        # Mobile menu container with enhanced styling
        menu_html = """
        <div style='
            position: absolute;
            top: 60px;
            left: 0;
            right: 0;
            background: white;
            border: 2px solid #E5E7EB;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            z-index: 1000;
            padding: 16px;
            margin: 8px;
        '>
            <div style='
                text-align: center;
                font-weight: bold;
                color: #22C55E;
                margin-bottom: 16px;
                font-size: 18px;
            '>Navigation Menu</div>
        </div>
        """

        st.markdown(menu_html, unsafe_allow_html=True)

        # Create navigation buttons in mobile menu
        st.markdown("**📱 Mobile Navigation**")

        for page_name, page_info in self.pages.items():
            button_type = "primary" if page_name == current_page else "secondary"

            # Mobile-friendly navigation button
            if st.button(
                f"{page_info['icon']} {page_name}",
                key=f"mobile_nav_{page_name}",
                help=page_info["description"],
                type=button_type,  # type: ignore[arg-type]
                use_container_width=True,
            ):
                # Defer navigation to avoid component unregistration races
                st.session_state["__nav_pending"] = page_name
                st.session_state.hamburger_menu_open = False  # Close menu after selection
                # track later when applying pending navigation

        # Close menu button
        st.markdown("---")
        if st.button("✕ Close Menu", key="close_mobile_menu", use_container_width=True):
            st.session_state.hamburger_menu_open = False

    def render_collapsible_navigation(self) -> str:
        """Render collapsible navigation for mobile devices."""
        current_page = st.session_state.get("current_page", "Home")

        # Initialize collapsible state
        if "nav_collapsed" not in st.session_state:
            st.session_state.nav_collapsed = self._is_mobile_view()

        # Toggle button for collapsible navigation
        col1, col2 = st.columns([1, 4])

        with col1:
            if st.button("☰" if st.session_state.nav_collapsed else "✕", key="nav_toggle", help="Toggle navigation menu"):
                st.session_state.nav_collapsed = not st.session_state.nav_collapsed

        with col2:
            if not st.session_state.nav_collapsed:
                # Show current page name
                current_page_info = self.pages.get(current_page, {})
                st.markdown(f"**{current_page_info.get('icon', '📄')} {current_page}**")

        # Render navigation content if not collapsed
        if not st.session_state.nav_collapsed:
            selected_page = self._render_navigation_tabs(current_page)
            return selected_page
        else:
            # Show compact navigation
            return self._render_compact_navigation(current_page)

    def _render_compact_navigation(self, current_page: str) -> str:
        """Render compact navigation for collapsed state."""
        # Show only current page with dropdown for others
        page_options = list(self.pages.keys())
        page_labels = [f"{self.pages[name]['icon']} {name}" for name in page_options]

        try:
            current_index = page_options.index(current_page)
        except ValueError:
            current_index = 0

        selected_option = st.selectbox("Navigate to:", options=page_labels, index=current_index, key="compact_nav_select")

        # Extract page name from selection
        selected_page = page_options[page_labels.index(selected_option)]

        return selected_page

    def _track_page_change(self, new_page: str):
        """Track page change for analytics."""
        from .state_manager import StateManager

        state_manager = StateManager()
        state_manager.track_page_visit(new_page)

        logger.info(f"Page changed to: {new_page}")

    def render_breadcrumbs(self) -> None:
        """Render breadcrumb navigation."""
        _current_page = st.session_state.get("current_page", "Home")
        page_history = st.session_state.get("page_history", [])

        if len(page_history) > 1:
            # Show last few pages in breadcrumb
            recent_pages = page_history[-3:]  # Last 3 pages

            breadcrumb_items = []
            for i, page_visit in enumerate(recent_pages):
                page_name = page_visit["page"]
                page_icon = self.pages.get(page_name, {}).get("icon", "📄")

                if i == len(recent_pages) - 1:
                    # Current page (not clickable)
                    breadcrumb_items.append(f"**{page_icon} {page_name}**")
                else:
                    # Previous pages (could be made clickable)
                    breadcrumb_items.append(f"{page_icon} {page_name}")

            breadcrumb_text = " → ".join(breadcrumb_items)
            st.caption(f"Navigation: {breadcrumb_text}")

    def render_mobile_navigation(self) -> str:
        """Render mobile-optimized navigation."""
        current_page = st.session_state.get("current_page", "Home")

        # Mobile navigation using selectbox
        page_options = [f"{info['icon']} {name}" for name, info in self.pages.items()]
        page_names = list(self.pages.keys())

        try:
            current_index = page_names.index(current_page)
        except ValueError:
            current_index = 0

        selected_option = st.selectbox("Navigate to:", options=page_options, index=current_index, key="mobile_nav_select")

        # Extract page name from selected option
        selected_page = page_names[page_options.index(selected_option)]

        return selected_page

    def get_page_info(self, page_name: str) -> dict:
        """Get information about a specific page."""
        return self.pages.get(page_name, {})

    def search_pages(self, query: str) -> list[str]:
        """Search pages by name, description, or keywords."""
        query = query.lower().strip()
        if not query:
            return list(self.pages.keys())

        matching_pages = []

        for page_name, page_info in self.pages.items():
            # Check page name
            if query in page_name.lower():
                matching_pages.append(page_name)
                continue

            # Check description
            if query in page_info.get("description", "").lower():
                matching_pages.append(page_name)
                continue

            # Check keywords
            keywords = page_info.get("keywords", [])
            if any(query in keyword.lower() for keyword in keywords):
                matching_pages.append(page_name)

        return matching_pages

    def render_page_search(self) -> str | None:
        """Render page search functionality."""
        with st.expander("🔍 Search Pages", expanded=False):
            search_query = st.text_input("Search for a page:", placeholder="Type page name, description, or keyword...", key="page_search")

            if search_query:
                matching_pages = self.search_pages(search_query)

                if matching_pages:
                    st.write("**Matching pages:**")

                    for page_name in matching_pages:
                        page_info = self.pages[page_name]

                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.write(f"{page_info['icon']} **{page_name}**")
                            st.caption(page_info["description"])

                        with col2:
                            if st.button("Go", key=f"search_go_{page_name}"):
                                return page_name
                else:
                    st.info("No matching pages found.")

        return None


class NavigationSidebar:
    """Sidebar navigation component."""

    def __init__(self):
        self.nav_header = NavigationHeader()

    def render(self, container=None):
        """Render sidebar navigation into a provided container (left column) or fallback to a left column.

        This avoids relying on Streamlit's `st.sidebar` DOM and keeps the sidebar static.
        """
        # If no container provided, create a left column to act as the static sidebar
        if container is None:
            left_col, _ = st.columns([1, 4])
            container = left_col

        with container:
            st.markdown("### 🧭 Navigation")

            # Quick navigation buttons
            current_page = st.session_state.get("current_page", "Home")

            for page_name, page_info in self.nav_header.pages.items():
                button_type = "primary" if page_name == current_page else "secondary"

                if st.button(
                    f"{page_info['icon']} {page_name}",
                    key=f"sidebar_nav_{page_name}",
                    help=page_info["description"],
                    type=button_type,  # type: ignore[arg-type]
                    use_container_width=True,
                ):
                    st.session_state.current_page = page_name
                    st.rerun()

            st.markdown("---")

            # Page search
            search_result = self.nav_header.render_page_search()
            if search_result:
                st.session_state.current_page = search_result
                st.rerun()

            # Session info
            self._render_session_info()
            # Status indicator
            # Use header's status indicator to render centrally
            try:
                self.nav_header._render_status_indicator()
            except Exception:
                # Fallback to a minimal indicator
                st.markdown("<div class='status-container'>Status</div>", unsafe_allow_html=True)

    def _render_status_indicator(self) -> None:
        """Expose a sidebar-level status indicator for callers."""
        try:
            self.nav_header._render_status_indicator()
        except Exception:
            st.markdown("<div class='status-container'>Status</div>", unsafe_allow_html=True)

    def _render_session_info(self):
        """Render session information in sidebar."""
        from .state_manager import StateManager

        state_manager = StateManager()
        stats = state_manager.get_session_stats()

        with st.expander("📊 Session Info", expanded=False):
            st.metric("Session Duration", stats["session_duration"])
            st.metric("Pages Visited", stats["pages_visited"])
            st.metric("Analyses Done", stats["analyses_performed"])

            if stats["active_modes"]:
                st.write("**Active Input Modes:**")
                for mode in stats["active_modes"]:
                    st.write(f"• {mode.title()}")

            st.caption(f"Session ID: {stats['session_id']}")
