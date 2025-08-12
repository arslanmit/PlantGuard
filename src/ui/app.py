"""
Main Streamlit application for PlantGuard.
"""

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(
        page_title="🌱 PlantGuard", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed"
    )

    # Header
    st.title("🌱 PlantGuard Assistant")
    st.markdown("""
    **Multimodal Plant Disease Detection System**

    Upload a plant leaf image and optionally ask questions via text or voice
    to get AI-powered disease diagnosis and treatment recommendations.
    """)

    # Placeholder for now - will be implemented in later tasks
    st.info("🚧 **Under Development** - Core functionality will be implemented in upcoming tasks.")

    # Show system status
    with st.expander("System Status", expanded=False):
        st.json(
            {
                "status": "initializing",
                "vision_model": "not_loaded",
                "audio_model": "not_loaded",
                "text_model": "not_loaded",
            }
        )

    # Development info
    st.markdown("---")
    st.markdown("**Development Progress:**")
    st.markdown("✅ Task 1: Environment Setup and Project Structure")
    st.markdown("⏳ Task 2: Data Pipeline Implementation")
    st.markdown("⏳ Task 3: Vision Model Development")
    st.markdown("⏳ Task 4: Audio Processing Implementation")
    st.markdown("⏳ Task 5: Knowledge Base and Text Processing")


if __name__ == "__main__":
    main()
