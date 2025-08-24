"""PlantGuard - Legacy Entry Point

This is a legacy entry point that redirects to the new Single Page Application (SPA).
The SPA consolidates all functionality into one AI-friendly interface.

For the main application, use: spa_app.py
Or run: make run
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import streamlit as st

# Configure logging
from src.utils.logging import setup_logger

logger = setup_logger("plantguard", log_file="logs/app.log")


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="PlantGuard - Plant Disease Detection",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/plantguard/help",
            "Report a bug": "https://github.com/plantguard/issues",
            "About": "PlantGuard - AI-powered plant disease detection system",
        },
    )

    # Load centralized CSS if available
    ASSETS_PATH = Path(__file__).parent / "assets"
    css_file = ASSETS_PATH / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    # Initialize core session state
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "current_models" not in st.session_state:
        st.session_state.current_models = {"vision": "resnet50_plantvillage_v1", "audio": "whisper_tiny_local", "text": "distilbert_plant_qa_v1"}
    if "session_start" not in st.session_state:
        from datetime import datetime

        st.session_state.session_start = datetime.now().isoformat()


def render_main_header():
    """Render the main application header."""
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #4CAF50, #45a049); 
                    border-radius: 15px; margin-bottom: 2rem; color: white;'>
            <h1 style='margin: 0; font-size: 3rem;'>🌿 PlantGuard</h1>
            <p style='margin: 0; font-size: 1.2rem; opacity: 0.9;'>AI-Powered Plant Disease Detection System</p>
            <p style='margin: 0; font-size: 0.9rem; opacity: 0.8;'>Multi-page interface for comprehensive plant care</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome_content():
    """Render welcome content for the main page."""
    # Quick overview
    st.markdown("### 🌟 Welcome to PlantGuard")
    st.markdown("Select a page from the sidebar to start using PlantGuard's AI-powered plant disease detection system.")

    # Feature overview cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; text-align: center; border-left: 4px solid #4CAF50;'>
                <h3>🖼️ Image Analysis</h3>
                <p>Upload plant images for AI-powered disease detection with detailed analysis and treatment recommendations.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; text-align: center; border-left: 4px solid #2196F3;'>
                <h3>🎤 Voice Assistant</h3>
                <p>Ask questions about plant care using voice input. Get instant answers from our AI assistant.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; text-align: center; border-left: 4px solid #FF9800;'>
                <h3>💬 Chat Assistant</h3>
                <p>Text-based conversational interface for plant care questions and guidance.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Additional features
    st.markdown("---")
    col4, col5 = st.columns(2)

    with col4:
        st.markdown(
            """
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; text-align: center; border-left: 4px solid #9C27B0;'>
                <h3>📈 History & Settings</h3>
                <p>Manage your analysis history, configure models, and adjust accessibility settings for optimal experience.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            """
            <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; text-align: center; border-left: 4px solid #E91E63;'>
                <h3>🔄 Compare Images</h3>
                <p>Side-by-side image comparison with overlay modes and detailed analysis comparison metrics.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Quick stats if there's activity
    if st.session_state.analysis_history or st.session_state.chat_messages:
        st.markdown("---")
        st.markdown("### 📊 Your Activity")

        col_stats1, col_stats2, col_stats3 = st.columns(3)

        with col_stats1:
            st.metric("Total Analyses", len(st.session_state.analysis_history))

        with col_stats2:
            st.metric("Chat Messages", len(st.session_state.chat_messages))

        with col_stats3:
            if st.session_state.analysis_history:
                avg_confidence = sum(item.get("confidence", 0) for item in st.session_state.analysis_history) / len(st.session_state.analysis_history)
                st.metric("Avg Confidence", f"{avg_confidence:.1%}")
            else:
                st.metric("Active Session", "✅")


def main():
    """Main Streamlit application - legacy version with SPA redirect notice."""
    try:
        # Configure page
        configure_page()

        # Initialize session state
        initialize_session_state()

        # SPA Migration Notice
        st.warning("""
        🌟 **PlantGuard has been upgraded to a Single Page Application (SPA)!**
        
        This legacy interface is deprecated. For the best experience with all functionality 
        consolidated into one AI-friendly interface, please use:
        
        **New SPA Interface:** `spa_app.py` or run `make run`
        
        The SPA provides the same powerful features with a simplified, streamlined design.
        """)

        # Option to launch SPA
        if st.button("🚀 Launch New SPA Interface", type="primary"):
            st.info("Please run: `streamlit run spa_app.py` or `make run`")

        # Render main header
        render_main_header()

        # Main welcome content
        render_welcome_content()

        logger.info("PlantGuard legacy page loaded with SPA migration notice")

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("An unexpected error occurred. Please refresh the page.")
        st.exception(e)


if __name__ == "__main__":
    logger.info("Starting PlantGuard multi-page application")
    main()
