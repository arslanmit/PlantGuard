"""
Mobile Display Components Demo for PlantGuard UI.

This module demonstrates the mobile display components including
MobileAnalysisDisplay, MobileRecommendations, and MobileChatInterface.
"""

import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

# Import mobile display components
from components.mobile_analysis_display import MobileAnalysisDisplay
from components.mobile_chat_interface import MobileChatInterface
from components.mobile_recommendations import MobileRecommendations
from PIL import Image

logger = logging.getLogger(__name__)


def load_mobile_display_styles():
    """Load mobile display component styles."""
    try:
        styles_path = Path(__file__).parent / "components" / "mobile_display_styles.css"

        if styles_path.exists():
            with open(styles_path, encoding="utf-8") as f:
                css_content = f.read()

            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ Mobile display styles not found. Components may not display correctly.")

    except Exception as e:
        logger.error("Failed to load mobile display styles: %s", e)
        st.error(f"❌ Failed to load styles: {e}")


def create_sample_analysis_results():
    """Create sample analysis results for demonstration."""
    # Create sample images
    sample_image_1 = Image.new("RGB", (300, 200), color="#90EE90")  # Light green
    sample_image_2 = Image.new("RGB", (300, 200), color="#FFB6C1")  # Light pink
    sample_image_3 = Image.new("RGB", (300, 200), color="#87CEEB")  # Sky blue

    # Create sample analysis results
    sample_results = [
        {
            "timestamp": datetime.now().isoformat(),
            "image": sample_image_1,
            "prediction": ("Apple___Apple_scab", 0.87),
            "source": "upload",
            "filename": "apple_leaf_1.jpg",
            "component_id": "demo_upload",
        },
        {
            "timestamp": (datetime.now()).isoformat(),
            "image": sample_image_2,
            "prediction": ("Tomato___Late_blight", 0.73),
            "source": "camera",
            "component_id": "demo_camera",
        },
        {
            "timestamp": (datetime.now()).isoformat(),
            "image": sample_image_3,
            "prediction": ("Healthy_Plant", 0.92),
            "source": "upload",
            "filename": "healthy_plant.jpg",
            "component_id": "demo_upload",
        },
    ]

    return sample_results


def demo_mobile_analysis_display():
    """Demonstrate MobileAnalysisDisplay component."""
    st.markdown("## 🔬 Mobile Analysis Display Demo")

    # Create component
    analysis_display = MobileAnalysisDisplay(component_id="demo_analysis_display", title="Plant Disease Analysis")

    # Demo controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Add Sample Results", key="add_sample_results"):
            sample_results = create_sample_analysis_results()
            if "analysis_results" not in st.session_state:
                st.session_state.analysis_results = []
            st.session_state.analysis_results.extend(sample_results)
            st.success("✅ Sample analysis results added!")

    with col2:
        if st.button("🧹 Clear Results", key="clear_analysis_results"):
            if "analysis_results" in st.session_state:
                st.session_state.analysis_results = []
            st.success("🧹 Analysis results cleared!")

    with col3:
        results_count = len(st.session_state.get("analysis_results", []))
        st.metric("Results", results_count)

    # Render component
    st.markdown("### Component Output:")
    analysis_display.render()

    # Component info
    with st.expander("📋 Component Information", expanded=False):
        st.write(f"**Component ID:** {analysis_display.component_id}")
        st.write(f"**Component Type:** {analysis_display.component_type}")
        st.write(f"**Has Results:** {analysis_display.has_results()}")
        st.write(f"**Results Count:** {analysis_display.get_results_count()}")

        # Show component state
        state = analysis_display.get_state()
        st.json(state["data"]["analysis_data"])


def demo_mobile_recommendations():
    """Demonstrate MobileRecommendations component."""
    st.markdown("## 💡 Mobile Recommendations Demo")

    # Create component
    recommendations = MobileRecommendations(component_id="demo_recommendations", title="Treatment Recommendations")

    # Demo controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🌿 Add Disease Context", key="add_disease_context"):
            # Add sample analysis result for context
            sample_image = Image.new("RGB", (200, 200), color="#90EE90")

            disease_result = {
                "timestamp": datetime.now().isoformat(),
                "image": sample_image,
                "prediction": ("Apple___Apple_scab", 0.85),
                "source": "demo",
                "component_id": "demo_context",
            }

            if "analysis_results" not in st.session_state:
                st.session_state.analysis_results = []
            st.session_state.analysis_results.append(disease_result)
            st.success("✅ Disease context added!")

    with col2:
        if st.button("🧹 Clear Context", key="clear_recommendations_context"):
            if "analysis_results" in st.session_state:
                st.session_state.analysis_results = []
            st.success("🧹 Context cleared!")

    with col3:
        has_context = recommendations.has_recommendations()
        st.metric("Has Context", "Yes" if has_context else "No")

    # Render component
    st.markdown("### Component Output:")
    recommendations.render()

    # Component info
    with st.expander("📋 Component Information", expanded=False):
        st.write(f"**Component ID:** {recommendations.component_id}")
        st.write(f"**Component Type:** {recommendations.component_type}")
        st.write(f"**Current Disease:** {recommendations.get_current_disease()}")
        st.write(f"**Current Confidence:** {recommendations.get_current_confidence():.1%}")

        # Show component state
        state = recommendations.get_state()
        st.json(state["data"]["recommendations_data"])


def demo_mobile_chat_interface():
    """Demonstrate MobileChatInterface component."""
    st.markdown("## 💬 Mobile Chat Interface Demo")

    # Create component
    chat_interface = MobileChatInterface(component_id="demo_chat_interface", title="Plant Care Assistant")

    # Demo controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💬 Add Sample Messages", key="add_sample_messages"):
            # Add some sample messages
            sample_messages = [
                {
                    "id": "sample_user_1",
                    "type": "user",
                    "content": "How often should I water my apple tree?",
                    "timestamp": datetime.now().isoformat(),
                    "context": None,
                },
                {
                    "id": "sample_bot_1",
                    "type": "bot",
                    "content": "Apple trees typically need deep watering once or twice a week, depending on weather conditions. Check the soil moisture by inserting your finger 2-3 inches deep. If it's dry, it's time to water!",
                    "timestamp": datetime.now().isoformat(),
                    "context": None,
                },
                {
                    "id": "sample_user_2",
                    "type": "user",
                    "content": "What about the disease I found on the leaves?",
                    "timestamp": datetime.now().isoformat(),
                    "context": None,
                },
                {
                    "id": "sample_bot_2",
                    "type": "bot",
                    "content": "Based on your recent analysis showing Apple Scab with 85% confidence, I recommend removing affected leaves immediately and applying a fungicide. Improve air circulation around the tree and avoid overhead watering.",
                    "timestamp": datetime.now().isoformat(),
                    "context": None,
                },
            ]

            # Add messages to component state
            state = chat_interface.get_state()
            chat_data = state["data"]["chat_data"]
            chat_data["messages"].extend(sample_messages)
            state["data"]["chat_data"] = chat_data
            chat_interface.set_state(state)

            st.success("✅ Sample messages added!")

    with col2:
        if st.button("🧹 Clear Chat", key="clear_chat_demo"):
            chat_interface._clear_chat()
            st.success("🧹 Chat cleared!")

    with col3:
        message_count = chat_interface.get_message_count()
        st.metric("Messages", message_count)

    # Render component
    st.markdown("### Component Output:")
    chat_interface.render()

    # Component info
    with st.expander("📋 Component Information", expanded=False):
        st.write(f"**Component ID:** {chat_interface.component_id}")
        st.write(f"**Component Type:** {chat_interface.component_type}")
        st.write(f"**Message Count:** {chat_interface.get_message_count()}")
        st.write(f"**Is Typing:** {chat_interface.is_typing()}")

        # Show last message
        last_message = chat_interface.get_last_message()
        if last_message:
            st.write("**Last Message:**")
            st.json(last_message)


def demo_components_integration():
    """Demonstrate integration between display components."""
    st.markdown("## 🔗 Components Integration Demo")

    st.info("""
    This section demonstrates how the mobile display components work together:
    
    1. **Analysis Display** shows disease detection results
    2. **Recommendations** provides treatment advice based on analysis
    3. **Chat Interface** uses analysis context for intelligent responses
    """)

    # Integration controls
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Setup Full Integration", key="setup_integration"):
            # Create comprehensive analysis result
            sample_image = Image.new("RGB", (300, 200), color="#FFB6C1")

            integration_result = {
                "timestamp": datetime.now().isoformat(),
                "image": sample_image,
                "prediction": ("Apple___Apple_scab", 0.87),
                "source": "integration_demo",
                "filename": "apple_scab_sample.jpg",
                "component_id": "integration_demo",
            }

            # Set analysis results
            st.session_state.analysis_results = [integration_result]

            st.success("✅ Integration context setup complete!")
            st.info("Now all components will share this analysis context.")

    with col2:
        if st.button("🧹 Clear Integration", key="clear_integration"):
            if "analysis_results" in st.session_state:
                st.session_state.analysis_results = []
            st.success("🧹 Integration context cleared!")

    # Show integration status
    has_context = "analysis_results" in st.session_state and len(st.session_state.analysis_results) > 0

    if has_context:
        st.success("✅ **Integration Active** - All components share analysis context")

        latest_result = st.session_state.analysis_results[0]
        disease_name, confidence = latest_result.get("prediction", ("Unknown", 0.0))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Disease", disease_name.replace("___", " - "))
        with col2:
            st.metric("Confidence", f"{confidence:.1%}")
        with col3:
            st.metric("Source", latest_result.get("source", "Unknown").title())
    else:
        st.warning("⚠️ **No Integration Context** - Click 'Setup Full Integration' to connect components")


def main():
    """Main demo application."""
    st.set_page_config(page_title="Mobile Display Components Demo", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")

    # Load styles
    load_mobile_display_styles()

    # Main header
    st.markdown("""
    # 🌿 PlantGuard Mobile Display Components Demo
    
    This demo showcases the mobile-optimized display components for plant disease analysis,
    treatment recommendations, and conversational interaction.
    """)

    # Navigation
    demo_option = st.selectbox(
        "Choose Demo Section:", ["🔬 Analysis Display", "💡 Recommendations", "💬 Chat Interface", "🔗 Integration Demo", "📊 All Components"]
    )

    st.markdown("---")

    # Render selected demo
    if demo_option == "🔬 Analysis Display":
        demo_mobile_analysis_display()

    elif demo_option == "💡 Recommendations":
        demo_mobile_recommendations()

    elif demo_option == "💬 Chat Interface":
        demo_mobile_chat_interface()

    elif demo_option == "🔗 Integration Demo":
        demo_components_integration()

    elif demo_option == "📊 All Components":
        st.markdown("## 📊 All Components Demo")
        st.info("This section shows all components together in a unified interface.")

        # Setup integration context
        if st.button("🚀 Setup Demo Context", key="setup_all_demo"):
            sample_results = create_sample_analysis_results()
            st.session_state.analysis_results = sample_results
            st.success("✅ Demo context setup for all components!")

        # Render all components
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🔬 Analysis Display")
            analysis_display = MobileAnalysisDisplay("all_demo_analysis")
            analysis_display.render()

            st.markdown("### 💡 Recommendations")
            recommendations = MobileRecommendations("all_demo_recommendations")
            recommendations.render()

        with col2:
            st.markdown("### 💬 Chat Interface")
            chat_interface = MobileChatInterface("all_demo_chat")
            chat_interface.render()

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        🌿 PlantGuard Mobile Display Components Demo<br>
        Built with Streamlit • Optimized for Mobile • AI-Powered Plant Care
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
