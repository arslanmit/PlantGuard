"""Simple/Expert Interface Toggle for ADHD-Friendly Design.

This module provides a toggle component that switches between
simplified and expert interface modes to reduce cognitive load
for users with ADHD while providing full functionality for power users.
"""

import logging
from typing import Literal

import streamlit as st

logger = logging.getLogger(__name__)

InterfaceMode = Literal["simple", "expert"]


class InterfaceToggle:
    """Simple/Expert interface toggle component."""

    def __init__(self):
        """Initialize the interface toggle."""
        # Initialize session state
        if "interface_mode" not in st.session_state:
            st.session_state.interface_mode = "simple"
        if "show_mode_explanation" not in st.session_state:
            st.session_state.show_mode_explanation = True

    def get_current_mode(self) -> InterfaceMode:
        """Get the current interface mode.

        Returns:
            Current interface mode
        """
        return st.session_state.interface_mode

    def set_mode(self, mode: InterfaceMode) -> None:
        """Set the interface mode.

        Args:
            mode: Interface mode to set
        """
        if mode in ["simple", "expert"]:
            st.session_state.interface_mode = mode
            logger.info(f"Interface mode changed to: {mode}")
        else:
            logger.warning(f"Invalid interface mode: {mode}")

    def is_simple_mode(self) -> bool:
        """Check if currently in simple mode.

        Returns:
            True if in simple mode
        """
        return self.get_current_mode() == "simple"

    def is_expert_mode(self) -> bool:
        """Check if currently in expert mode.

        Returns:
            True if in expert mode
        """
        return self.get_current_mode() == "expert"

    def render_toggle(self, position: str = "top-right") -> None:
        """Render the interface toggle control.

        Args:
            position: Position of the toggle ("top-right", "sidebar", "inline")
        """
        current_mode = self.get_current_mode()

        if position == "top-right":
            # Fixed position toggle (requires custom CSS)
            st.markdown(
                """
            <div class="interface-toggle-container">
                <div class="interface-toggle">
                    <span>🧠</span>
                    <span style="color: var(--text-light); font-size: 0.8rem;">Interface:</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Render toggle controls into a container to avoid relying on st.sidebar
            # Fallback to a left column if no explicit container is available
            left_col, right_col = st.columns([1, 4])
            with left_col:
                st.markdown("### 🧠 Interface Mode")
                new_mode = st.radio(
                    "Choose your interface:",
                    options=["simple", "expert"],
                    index=0 if current_mode == "simple" else 1,
                    format_func=lambda x: "🎯 Simple Mode" if x == "simple" else "⚙️ Expert Mode",
                    key="interface_mode_radio",
                )

                if new_mode != current_mode:
                    self.set_mode(new_mode)
                    st.rerun()

        elif position == "sidebar":
            # Use left column as a static sidebar instead of Streamlit's st.sidebar
            left_col, _ = st.columns([1, 4])
            with left_col:
                st.markdown("### 🧠 Interface Mode")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "🎯 Simple",
                        key="simple_mode_btn",
                        help="Simplified interface with reduced cognitive load",
                        use_container_width=True,
                    ):
                        self.set_mode("simple")
                        st.rerun()

                with col2:
                    if st.button(
                        "⚙️ Expert",
                        key="expert_mode_btn",
                        help="Full-featured interface with all options",
                        use_container_width=True,
                    ):
                        self.set_mode("expert")
                        st.rerun()

                # Current mode indicator
                mode_emoji = "🎯" if current_mode == "simple" else "⚙️"
                mode_name = "Simple" if current_mode == "simple" else "Expert"
                st.info(f"{mode_emoji} Current Mode: **{mode_name}**")

        elif position == "inline":
            st.markdown("#### 🧠 Interface Mode")
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button(
                    "🎯 Simple",
                    key="inline_simple_btn",
                    type="primary" if current_mode == "simple" else "secondary",
                    help="Reduced complexity, focused on essentials",
                ):
                    self.set_mode("simple")
                    st.rerun()

            with col2:
                if st.button(
                    "⚙️ Expert",
                    key="inline_expert_btn",
                    type="primary" if current_mode == "expert" else "secondary",
                    help="Full functionality with detailed controls",
                ):
                    self.set_mode("expert")
                    st.rerun()

            with col3:
                if current_mode == "simple":
                    st.success("🎯 **Simple Mode Active** - Streamlined interface")
                else:
                    st.info("⚙️ **Expert Mode Active** - Full functionality")

    def render_mode_explanation(self) -> None:
        """Render explanation of current mode."""
        if not st.session_state.show_mode_explanation:
            return

        current_mode = self.get_current_mode()

        if current_mode == "simple":
            with st.expander("🎯 **Simple Mode Features**", expanded=False):
                st.markdown("""
                **Perfect for quick analysis and reduced cognitive load:**

                ✅ **Streamlined Interface**
                - Larger buttons and clearer labels
                - Essential features only
                - Reduced visual clutter

                ✅ **Simplified Workflow**
                - Step-by-step guidance
                - Automatic best settings
                - Clear progress indicators

                ✅ **ADHD-Friendly Design**
                - Big headings with emojis
                - Color-coded status indicators
                - Focused attention areas
                """)
        else:
            with st.expander("⚙️ **Expert Mode Features**", expanded=False):
                st.markdown("""
                **Full functionality for power users:**

                ⚙️ **Advanced Controls**
                - All configuration options
                - Detailed metrics and charts
                - Batch processing capabilities

                ⚙️ **Comprehensive Analysis**
                - Multiple model comparisons
                - Detailed probability breakdowns
                - Advanced visualization options

                ⚙️ **Professional Tools**
                - Export in multiple formats
                - Custom analysis parameters
                - Integration options
                """)

        # Option to hide explanations
        if st.button("🙈 Hide Mode Explanations", key="hide_explanations"):
            st.session_state.show_mode_explanation = False
            st.rerun()

    def apply_mode_styles(self) -> None:
        """Apply CSS styles based on current mode."""
        current_mode = self.get_current_mode()

        # Apply mode-specific CSS class to the container
        css_class = f"interface-{current_mode}"

        st.markdown(
            f"""
        <script>
        // Apply interface mode class to body
        document.body.className = document.body.className.replace(/interface-\\w+/g, '');
        document.body.classList.add('{css_class}');
        </script>
        """,
            unsafe_allow_html=True,
        )

    def should_show_feature(self, feature_type: str) -> bool:
        """Check if a feature should be shown in current mode.

        Args:
            feature_type: Type of feature ("advanced", "simple", "expert-only", etc.)

        Returns:
            True if feature should be shown
        """
        current_mode = self.get_current_mode()

        feature_map = {
            "expert-only": lambda: current_mode == "expert",
            "simple-only": lambda: current_mode == "simple",
            "advanced": lambda: current_mode == "expert",
            "basic": lambda: True,
        }

        checker = feature_map.get(feature_type)
        return checker() if checker is not None else True

    def render_adhd_heading(self, text: str, emoji: str = "🌱", level: str = "primary") -> None:
        """Render ADHD-friendly heading with emoji.

        Args:
            text: Heading text
            emoji: Emoji to display
            level: Heading level ("primary", "section")
        """
        css_class = f"adhd-heading {level}"

        st.markdown(
            f"""
        <div class="{css_class}">
            <span class="emoji">{emoji}</span>
            {text}
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_section_heading(self, text: str, emoji: str = "📊") -> None:
        """Render section heading with emoji.

        Args:
            text: Section heading text
            emoji: Emoji to display
        """
        st.markdown(
            f"""
        <div class="section-heading">
            <span class="emoji">{emoji}</span>
            {text}
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_progress_steps(self, steps: list[tuple[str, str, str]]) -> None:
        """Render progress steps visualization.

        Args:
            steps: List of (emoji, label, status) tuples
                  status can be: "completed", "active", "pending"
        """
        if not self.should_show_feature("basic"):
            return

        steps_html = []
        for emoji, label, status in steps:
            steps_html.append(f"""
            <div class="progress-step {status}">
                <div class="emoji">{emoji}</div>
                <div class="label">{label}</div>
            </div>
            """)

        st.markdown(
            f"""
        <div class="progress-steps">
            {"".join(steps_html)}
        </div>
        """,
            unsafe_allow_html=True,
        )

    def wrap_with_cognitive_indicator(self, content_func, complexity: str = "low"):
        """Wrap content with cognitive load indicator.

        Args:
            content_func: Function that renders content
            complexity: Cognitive complexity ("low", "medium", "high")
        """
        css_class = f"cognitive-indicator cognitive-{complexity}"

        with st.container():
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            content_func()
            st.markdown("</div>", unsafe_allow_html=True)


def create_interface_toggle() -> InterfaceToggle:
    """Create and return an InterfaceToggle instance.

    Returns:
        InterfaceToggle instance
    """
    return InterfaceToggle()


# Example usage
if __name__ == "__main__":
    st.title("🧠 Interface Toggle Test")

    # Create toggle
    toggle = create_interface_toggle()

    # Apply mode styles
    toggle.apply_mode_styles()

    # Render toggle control
    toggle.render_toggle(position="inline")

    # Render mode explanation
    toggle.render_mode_explanation()

    # Test ADHD-friendly headings
    toggle.render_adhd_heading("Plant Disease Detection", "🌱", "primary")
    toggle.render_section_heading("Analysis Results", "📊")

    # Test progress steps
    if toggle.should_show_feature("basic"):
        toggle.render_progress_steps(
            [
                ("📷", "Upload", "completed"),
                ("🔍", "Analyze", "active"),
                ("📋", "Results", "pending"),
                ("💾", "Save", "pending"),
            ]
        )

    # Test feature visibility
    if toggle.should_show_feature("expert-only"):
        st.info("⚙️ This is an expert-only feature!")

    if toggle.should_show_feature("simple-only"):
        st.success("🎯 This is a simple-mode feature!")

    # Test cognitive load wrapper
    def complex_content():
        st.write("This is complex content that might cause cognitive overload")
        st.slider("Complex parameter", 0, 100, 50)

    toggle.wrap_with_cognitive_indicator(complex_content, "medium")
