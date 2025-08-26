"""
Mobile Demo App for PlantGuard UI.

This module demonstrates the mobile layout manager and design system
with a complete mobile interface implementation.
"""

import logging
from typing import Any

import streamlit as st

from .mobile_component_registry import initialize_mobile_components
from .mobile_design_system import MobileDesignSystem, get_mobile_design_system
from .mobile_layout_manager import initialize_mobile_layout

logger = logging.getLogger(__name__)


def main():
    """Main mobile demo application."""
    st.set_page_config(page_title="PlantGuard Mobile", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")

    # Initialize mobile systems
    layout_manager = initialize_mobile_layout()
    design_system = get_mobile_design_system()
    component_info = initialize_mobile_components()

    # Apply mobile layout
    layout_manager.render_mobile_layout()

    # Demo content
    render_mobile_demo_content(design_system, component_info)


def render_mobile_demo_content(design_system: MobileDesignSystem, component_info: dict[str, Any]):
    """Render mobile demo content showcasing the design system."""

    # Input Grid Section
    st.markdown(
        """
    <div class="mobile-section">
        <h2 class="mobile-subtitle">Input Methods</h2>
        <p class="mobile-text">Touch-optimized input components in 2x2 grid layout</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Create 2x2 input grid
    st.markdown('<div class="mobile-input-grid">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📷 Camera", key="demo_camera", use_container_width=True, type="primary"):
            st.success("Camera input activated!")

        if st.button("🎤 Voice", key="demo_voice", use_container_width=True):
            st.info("Voice input ready!")

    with col2:
        if st.button("📁 Upload", key="demo_upload", use_container_width=True):
            st.info("File upload ready!")

        if st.button("💬 Text", key="demo_text", use_container_width=True):
            st.info("Text input ready!")

    st.markdown("</div>", unsafe_allow_html=True)

    # Design System Demo
    st.markdown(
        """
    <div class="mobile-section">
        <h2 class="mobile-subtitle">Design System Components</h2>
        <p class="mobile-text">Mobile-optimized components with touch targets</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Button variants demo
    st.markdown("### Button Variants")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(design_system.create_button("Primary", variant=design_system.ButtonVariant.PRIMARY), unsafe_allow_html=True)
        st.markdown(design_system.create_button("Success", variant=design_system.ButtonVariant.SUCCESS), unsafe_allow_html=True)

    with col2:
        st.markdown(design_system.create_button("Secondary", variant=design_system.ButtonVariant.SECONDARY), unsafe_allow_html=True)
        st.markdown(design_system.create_button("Warning", variant=design_system.ButtonVariant.WARNING), unsafe_allow_html=True)

    # Card components demo
    st.markdown("### Card Components")

    card_content = """
    <p class="mobile-text">This is a mobile-optimized card with proper spacing and touch-friendly design.</p>
    <div class="mobile-badge mobile-badge-success">Active</div>
    """

    st.markdown(
        design_system.create_card(content=card_content, title="Sample Card", subtitle="Mobile-optimized design", elevated=True),
        unsafe_allow_html=True,
    )

    # Progress bar demo
    st.markdown("### Progress Indicators")

    progress_value = st.slider("Progress", 0.0, 1.0, 0.7, key="demo_progress")
    st.markdown(design_system.create_progress_bar(progress_value, "Analysis Progress"), unsafe_allow_html=True)

    # Alert components demo
    st.markdown("### Alert Components")

    st.markdown(design_system.create_alert("This is an info alert", "info"), unsafe_allow_html=True)

    st.markdown(design_system.create_alert("Analysis completed successfully!", "success"), unsafe_allow_html=True)

    st.markdown(design_system.create_alert("Please check your input", "warning"), unsafe_allow_html=True)

    # Component Registry Info
    if st.checkbox("Show Component Registry Info", key="show_registry"):
        st.markdown(
            """
        <div class="mobile-section">
            <h2 class="mobile-subtitle">Component Registry Status</h2>
            <p class="mobile-text">AI Agent-compatible component information</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if component_info["status"] == "initialized":
            registry_info = component_info["ai_agent_info"]

            st.json(
                {
                    "Available Components": registry_info["registry_info"]["available_types"],
                    "Total Component Types": registry_info["registry_info"]["total_component_types"],
                    "Active Instances": registry_info["registry_info"]["total_instances"],
                }
            )

            # Validation results
            validation = component_info["validation"]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Valid Components:**")
                for component in validation["valid_components"]:
                    st.markdown(f"✅ {component}")

            with col2:
                st.markdown("**Missing Implementations:**")
                for component in validation["missing_implementations"]:
                    st.markdown(f"⚠️ {component}")
        else:
            st.error(f"Component system error: {component_info.get('error', 'Unknown error')}")

    # Mobile Layout Info
    if st.checkbox("Show Mobile Layout Info", key="show_layout"):
        st.markdown(
            """
        <div class="mobile-section">
            <h2 class="mobile-subtitle">Mobile Layout Configuration</h2>
            <p class="mobile-text">Current mobile layout settings</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        layout_manager = st.session_state.get("mobile_layout_manager")
        if layout_manager:
            st.json(layout_manager.config)

    # CSS Classes Reference
    if st.checkbox("Show CSS Classes Reference", key="show_css"):
        st.markdown(
            """
        <div class="mobile-section">
            <h2 class="mobile-subtitle">CSS Classes Reference</h2>
            <p class="mobile-text">Available CSS classes for AI agent recognition</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        css_classes = {
            "Layout": ["mobile-main-layout", "mobile-container", "mobile-section", "mobile-input-grid"],
            "Components": [
                "mobile-button",
                "mobile-button-primary",
                "mobile-button-secondary",
                "mobile-card",
                "mobile-card-elevated",
                "mobile-input",
                "mobile-progress",
            ],
            "Typography": ["mobile-title", "mobile-subtitle", "mobile-text", "mobile-text-primary", "mobile-text-secondary"],
            "Utilities": ["mobile-flex", "mobile-w-full", "mobile-mt-md", "mobile-mb-lg", "mobile-p-md"],
        }

        for category, classes in css_classes.items():
            st.markdown(f"**{category}:**")
            for css_class in classes:
                st.code(css_class)

    # Footer
    st.markdown(
        """
    <div class="mobile-section mobile-text-center">
        <p class="mobile-text-muted">PlantGuard Mobile UI Demo</p>
        <p class="mobile-text-muted">Touch-optimized • AI Agent Compatible • Responsive Design</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
