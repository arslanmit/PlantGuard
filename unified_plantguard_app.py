#!/usr/bin/env python3
"""
Unified PlantGuard Application

Main entry point that provides seamless integration between desktop and mobile interfaces.
Automatically detects device type and switches to appropriate interface.

Usage:
    streamlit run unified_plantguard_app.py

Features:
- Automatic mobile/desktop detection
- Seamless interface switching
- Complete PlantGuard functionality
- AI agent testing capabilities
"""

import logging
import sys
from pathlib import Path

import streamlit as st

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import interface switcher
from ui.mobile_interface_switcher import mobile_interface_switcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def configure_page():
    """Configure Streamlit page with adaptive settings."""
    # Get interface configuration
    config = mobile_interface_switcher.get_interface_config()

    st.set_page_config(
        page_title="PlantGuard - AI Plant Care",
        page_icon="🌿",
        layout=config["layout"],
        initial_sidebar_state=config["sidebar_state"],
        menu_items={
            "Get Help": "https://github.com/plantguard/help",
            "Report a bug": "https://github.com/plantguard/issues",
            "About": "PlantGuard - AI-powered plant disease detection system",
        },
    )


def render_interface_selection() -> str | None:
    """Render interface selection if needed."""
    # Show interface toggle in sidebar or main area
    if mobile_interface_switcher.should_use_mobile_interface():
        # Mobile interface - show toggle in main area
        with st.expander("⚙️ Interface Settings", expanded=False):
            selected = mobile_interface_switcher.render_interface_toggle()
            mobile_interface_switcher.render_interface_info()
            return selected
    else:
        # Desktop interface - show toggle in sidebar
        with st.sidebar:
            st.markdown("### ⚙️ Interface")
            selected = mobile_interface_switcher.render_interface_toggle()
            mobile_interface_switcher.render_interface_info()
            return selected

    return None


def load_mobile_interface():
    """Load and run mobile interface."""
    try:
        # Import mobile app
        from mobile_plantguard_app import MobilePlantGuardApp

        # Apply mobile configuration
        mobile_interface_switcher.apply_interface_config()

        # Create and run mobile app
        mobile_app = MobilePlantGuardApp()
        mobile_app.run()

        logger.info("Mobile interface loaded successfully")

    except ImportError as e:
        st.error(f"❌ Failed to load mobile interface: {e}")
        logger.error(f"Mobile interface import error: {e}")

        # Fallback to basic mobile interface
        render_fallback_mobile_interface()

    except Exception as e:
        st.error(f"❌ Mobile interface error: {e}")
        logger.error(f"Mobile interface error: {e}")

        # Fallback to basic mobile interface
        render_fallback_mobile_interface()


def load_desktop_interface():
    """Load and run desktop interface."""
    try:
        # Import existing SPA app
        from spa_app import main as run_spa_app

        # Apply desktop configuration
        mobile_interface_switcher.apply_interface_config()

        # Run SPA app
        run_spa_app()

        logger.info("Desktop interface loaded successfully")

    except ImportError as e:
        st.error(f"❌ Failed to load desktop interface: {e}")
        logger.error(f"Desktop interface import error: {e}")

        # Fallback to basic desktop interface
        render_fallback_desktop_interface()

    except Exception as e:
        st.error(f"❌ Desktop interface error: {e}")
        logger.error(f"Desktop interface error: {e}")

        # Fallback to basic desktop interface
        render_fallback_desktop_interface()


def render_fallback_mobile_interface():
    """Render basic fallback mobile interface."""
    st.markdown("### 🌿 PlantGuard Mobile")
    st.info("📱 Mobile interface is loading...")

    # Basic mobile functionality
    st.markdown("#### 📸 Plant Analysis")

    uploaded_file = st.file_uploader("Upload plant image", type=["jpg", "jpeg", "png"], help="Take a photo or select from gallery")

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

        if st.button("🔍 Analyze Plant", use_container_width=True, type="primary"):
            with st.spinner("Analyzing plant..."):
                st.success("✅ Analysis complete! (Fallback mode)")
                st.info("Full analysis features will be available when all components load.")

    # Basic chat interface
    st.markdown("#### 💬 Plant Care Chat")

    user_input = st.text_input("Ask about plant care:", placeholder="How do I care for my plant?")

    if user_input:
        if st.button("Send", use_container_width=True):
            st.success("Message sent! (Fallback mode)")
            st.info("Full chat features will be available when all components load.")

    # Troubleshooting
    with st.expander("🔧 Troubleshooting", expanded=False):
        st.markdown("""
        **If you're seeing this fallback interface:**
        1. Refresh the page
        2. Check your internet connection
        3. Ensure all dependencies are installed
        4. Try switching to desktop interface
        """)

        if st.button("🔄 Reload Mobile Interface", use_container_width=True):
            st.rerun()


def render_fallback_desktop_interface():
    """Render basic fallback desktop interface."""
    st.markdown("# 🌿 PlantGuard Desktop")
    st.info("💻 Desktop interface is loading...")

    # Basic desktop layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📸 Image Analysis")

        uploaded_file = st.file_uploader("Upload plant image", type=["jpg", "jpeg", "png"])

        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image")

            if st.button("Analyze Plant", type="primary"):
                with st.spinner("Analyzing..."):
                    st.success("Analysis complete! (Fallback mode)")

    with col2:
        st.markdown("### 💬 Plant Care Assistant")

        user_input = st.text_area("Ask about plant care:", height=100)

        if st.button("Get Advice"):
            if user_input:
                st.success("Advice provided! (Fallback mode)")
            else:
                st.warning("Please enter a question first.")

    # Additional features
    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### 📊 Analysis History")
        st.info("History will appear here when full interface loads.")

    with col4:
        st.markdown("### ⚙️ Settings")
        st.info("Settings will appear here when full interface loads.")

    # Troubleshooting
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **If you're seeing this fallback interface:**
        1. Refresh the page
        2. Check console for errors
        3. Ensure all dependencies are installed
        4. Try switching to mobile interface
        """)

        if st.button("🔄 Reload Desktop Interface"):
            st.rerun()


def main():
    """Main application entry point with unified interface switching."""
    try:
        # Configure page
        configure_page()

        # Initialize session state
        if "interface_initialized" not in st.session_state:
            st.session_state.interface_initialized = False

        # Show header
        st.markdown(
            """
        <div style='text-align: center; padding: 1rem 0; background: linear-gradient(135deg, #4CAF50, #45a049); 
                    border-radius: 15px; margin-bottom: 1rem; color: white;'>
            <h1 style='margin: 0; font-size: 2.5rem;'>🌿 PlantGuard</h1>
            <p style='margin: 0; font-size: 1rem; opacity: 0.9;'>AI-Powered Plant Disease Detection</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Render interface selection
        interface_changed = render_interface_selection()

        # Handle interface change
        if interface_changed:
            st.session_state.interface_initialized = False
            st.rerun()

        # Determine which interface to load
        use_mobile = mobile_interface_switcher.should_use_mobile_interface()

        # Show interface indicator
        if use_mobile:
            st.success("📱 Mobile Interface Active")
        else:
            st.info("💻 Desktop Interface Active")

        # Load appropriate interface
        if use_mobile:
            load_mobile_interface()
        else:
            load_desktop_interface()

        # Mark as initialized
        st.session_state.interface_initialized = True

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"❌ Application Error: {e}")

        # Emergency fallback
        st.markdown("### 🚨 Emergency Mode")
        st.markdown("The application encountered an error. Basic functionality is available below.")

        # Basic emergency interface
        uploaded_file = st.file_uploader("Upload plant image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image")
            st.info("Image uploaded successfully. Full analysis requires app restart.")

        if st.button("🔄 Restart Application", type="primary"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()
