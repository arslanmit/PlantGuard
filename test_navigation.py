#!/usr/bin/env python3
"""Simple navigation test for PlantGuard sidebar.

This script tests the sidebar navigation functionality.
"""

import sys
from pathlib import Path

import streamlit as st

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_navigation():
    """Test navigation functionality."""
    st.set_page_config(page_title="Navigation Test", page_icon="🧪", layout="wide", initial_sidebar_state="expanded")

    # Add navigation styling
    st.markdown(
        """
    <style>
    .stSidebar .stButton > button {
        width: 100%;
        border-radius: 8px;
        margin: 2px 0;
        transition: all 0.2s ease;

    .nav-active {
    .nav-active {
        background: rgba(162, 181, 215, 0.25) !important;
        color: rgb(248, 250, 252) !important;
        font-weight: 600 !important;
        border: 2px solid rgba(162, 181, 215, 0.5) !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("🧪 Navigation Test")
    st.write("Testing sidebar navigation functionality.")

    # Initialize current page
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    # Sidebar navigation rendered into a static left column for the test
    left_col, _ = st.columns([1, 4])
    with left_col:
        st.markdown("### 🧭 Test Navigation")

        pages = {
            "Home": {"icon": "🏠", "description": "Home page test"},
            "Compare": {"icon": "🔍", "description": "Compare page test"},
            "History": {"icon": "📚", "description": "History page test"},
            "Guide": {"icon": "📖", "description": "Guide page test"},
            "Settings": {"icon": "⚙️", "description": "Settings page test"},
        }

        current_page = st.session_state.current_page

        st.write(f"**Current Page:** {current_page}")
        st.markdown("---")

        for page_name, page_info in pages.items():
            # Create container for each button
            container = st.container()

            with container:
                if page_name == current_page:
                    # Active page - show with custom styling
                    st.markdown(
                        f"""
                    <div style="
                        background: rgba(162, 181, 215, 0.25);
                        color: rgb(248, 250, 252);
                        padding: 8px 12px;
                        border-radius: 8px;
                        margin: 2px 0;
                        font-weight: 600;
                        text-align: center;
                        border: 2px solid rgba(162, 181, 215, 0.5);
                    ">
                        {page_info["icon"]} {page_name} ✓
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                # Inactive page - clickable button
                elif st.button(
                    f"{page_info['icon']} {page_name}",
                    key=f"nav_{page_name}",
                    help=page_info["description"],
                    use_container_width=True,
                ):
                    st.session_state.current_page = page_name
                    st.rerun()

        st.markdown("---")
        st.markdown("**Navigation Status:**")
        if st.session_state.current_page:
            st.success(f"✅ Currently on: {st.session_state.current_page}")
        else:
            st.error("❌ No page selected")

    # Main content area
    st.markdown("---")

    current_page = st.session_state.current_page
    page_info = pages.get(current_page, {"icon": "❓", "description": "Unknown page"})

    st.header(f"{page_info['icon']} {current_page} Page")
    st.write(f"You are currently viewing the **{current_page}** page.")
    st.info(f"Description: {page_info['description']}")

    # Test buttons in main area
    st.markdown("### Quick Navigation Test")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("🏠 Go Home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()

    with col2:
        if st.button("🔍 Compare", use_container_width=True):
            st.session_state.current_page = "Compare"
            st.rerun()

    with col3:
        if st.button("📚 History", use_container_width=True):
            st.session_state.current_page = "History"
            st.rerun()

    with col4:
        if st.button("📖 Guide", use_container_width=True):
            st.session_state.current_page = "Guide"
            st.rerun()

    with col5:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = "Settings"
            st.rerun()

    # Debug information
    with st.expander("🔧 Debug Information", expanded=False):
        st.json(
            {
                "current_page": st.session_state.current_page,
                "session_state_keys": list(st.session_state.keys()),
                "page_count": len(pages),
            }
        )


if __name__ == "__main__":
    test_navigation()
