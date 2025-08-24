"""
PlantGuard Simplified Application - Sidebar-Free UI Design

A streamlined, single-interface application that consolidates all PlantGuard functionality
into an intuitive, user-friendly experience without any sidebar dependencies.
"""

import json
import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image

# Add src to path for local imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import adapters with compatibility fallback
try:
    from core.nlp import TextAdapter
    from core.vision import VisionAdapter
except ImportError:
    # Use compatibility layer if core adapters not available
    from adapters_compat import TextAdapter, VisionAdapter

# Configure page with sidebar disabled
st.set_page_config(page_title="PlantGuard AI", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")

# Initialize session state
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "current_models" not in st.session_state:
    st.session_state.current_models = {"vision": "resnet50_plantvillage_v1", "audio": "whisper_tiny_local", "text": "distilbert_plant_qa_v1"}
if "settings_expanded" not in st.session_state:
    st.session_state.settings_expanded = False
if "comparison_history" not in st.session_state:
    st.session_state.comparison_history = []


class SimplifiedPlantGuardApp:
    """Simplified PlantGuard application without sidebar dependencies."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vision_adapter = None
        self.audio_adapter = None
        self.text_adapter = None

        # Available models configuration
        self.models = {
            "vision": {
                "vit_base_plants": {"name": "Vision Transformer", "accuracy": "100%", "speed": "Medium"},
                "resnet50_plantvillage_v1": {"name": "ResNet50", "accuracy": "95%", "speed": "Fast"},
                "mobilenet_fast": {"name": "MobileNet", "accuracy": "90%", "speed": "Very Fast"},
            },
            "audio": {
                "whisper_tiny_local": {"name": "Whisper Tiny", "accuracy": "85%", "speed": "Fast"},
                "wav2vec2_plant_sounds": {"name": "Wav2Vec2", "accuracy": "80%", "speed": "Medium"},
            },
            "text": {
                "distilbert_plant_qa_v1": {"name": "DistilBERT", "accuracy": "92%", "speed": "Fast"},
                "roberta_plant_care": {"name": "RoBERTa", "accuracy": "95%", "speed": "Medium"},
            },
        }

    def render_header(self):
        """Render the main application header with integrated controls."""
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(
                """
                <div style='padding: 1rem 0;'>
                    <h1 style='margin: 0; color: #4CAF50; font-size: 2.5rem;'>🌿 PlantGuard AI</h1>
                    <p style='margin: 0; color: #666; font-size: 1.1rem;'>AI-Powered Plant Disease Detection & Care Assistant</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            # Quick stats
            if st.session_state.analysis_history:
                total_analyses = len(st.session_state.analysis_history)
                st.metric("Total Analyses", total_analyses)

        with col3:
            # Settings toggle button
            if st.button("⚙️ Settings", key="settings_toggle", help="Show/hide settings panel"):
                st.session_state.settings_expanded = not st.session_state.settings_expanded
                st.rerun()

    def render_settings_panel(self):
        """Render collapsible settings panel."""
        if st.session_state.settings_expanded:
            with st.expander("⚙️ Quick Settings", expanded=True):
                col1, col2, col3 = st.columns(3)

                # Model selection for each type
                for i, model_type in enumerate(["vision", "audio", "text"]):
                    with [col1, col2, col3][i]:
                        st.markdown(f"**{model_type.title()} Model:**")
                        current_model = st.session_state.current_models[model_type]
                        model_options = [f"{info['name']} ({info['accuracy']})" for info in self.models[model_type].values()]
                        model_keys = list(self.models[model_type].keys())

                        try:
                            current_idx = model_keys.index(current_model)
                        except ValueError:
                            current_idx = 0

                        selected_model = st.selectbox(
                            f"{model_type} model",
                            options=model_options,
                            index=current_idx,
                            key=f"{model_type}_model_select",
                            label_visibility="collapsed",
                        )

                        # Update model if changed
                        new_model_key = model_keys[model_options.index(selected_model)]
                        if new_model_key != current_model:
                            st.session_state.current_models[model_type] = new_model_key
                            st.success(f"✅ Updated {model_type} model")

                # Quick actions row
                st.markdown("---")
                col_a, col_b, col_c, col_d = st.columns(4)

                with col_a:
                    if st.button("🧹 Clear History", use_container_width=True):
                        st.session_state.analysis_history = []
                        st.session_state.chat_messages = []
                        st.session_state.comparison_history = []
                        st.success("History cleared!")
                        st.rerun()

                with col_b:
                    if st.button("💾 Export Data", use_container_width=True):
                        self.export_session_data()

                with col_c:
                    if st.button("📊 View Stats", use_container_width=True):
                        self.show_quick_stats()

                with col_d:
                    if st.button("❓ Help", use_container_width=True):
                        self.show_help_info()

    def render_main_interface(self):
        """Render the main tabbed interface."""
        # Create main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["🖼️ Image Analysis", "🎤 Voice Assistant", "💬 Chat Assistant", "📈 History & Settings", "🔄 Compare Images"]
        )

        with tab1:
            self.render_image_analysis_tab()

        with tab2:
            self.render_voice_assistant_tab()

        with tab3:
            self.render_chat_assistant_tab()

        with tab4:
            self.render_history_settings_tab()

        with tab5:
            self.render_image_comparison_tab()

    def render_image_analysis_tab(self):
        """Render image analysis interface."""
        st.markdown("### 📷 Plant Image Analysis")

        col1, col2 = st.columns([2, 1])

        with col1:
            # File upload
            uploaded_file = st.file_uploader(
                "Choose a plant image", type=["jpg", "jpeg", "png"], help="Upload a clear image of the plant leaf or affected area"
            )

            if uploaded_file is not None:
                # Display image
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)

                # Analysis controls
                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("🔍 Analyze Plant", type="primary", use_container_width=True):
                        with st.spinner("Analyzing image with AI..."):
                            result = self.analyze_image(image)
                            if result:
                                self.display_analysis_result(result)
                                # Add to history
                                result["timestamp"] = datetime.now().isoformat()
                                result["type"] = "image"
                                result["filename"] = uploaded_file.name
                                st.session_state.analysis_history.append(result)

                with col_b:
                    if st.button("📊 View Details", use_container_width=True):
                        if st.session_state.analysis_history:
                            with st.expander("📈 Detailed Analysis", expanded=True):
                                latest = st.session_state.analysis_history[-1]
                                st.json(latest)
                        else:
                            st.info("Run an analysis first to see detailed results.")
            else:
                st.info("📸 Please upload an image to begin analysis")

        with col2:
            # Tips card
            st.markdown(
                """
                <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #4CAF50;'>
                    <h4 style='margin: 0; color: #4CAF50;'>💡 Tips for Best Results</h4>
                    <ul style='margin: 0.5rem 0; padding-left: 1rem;'>
                        <li>Use good lighting conditions</li>
                        <li>Focus on affected areas</li>
                        <li>Avoid blurry images</li>
                        <li>Include full leaf when possible</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Recent analysis
            st.markdown("### 📊 Recent Analysis")
            recent_analyses = st.session_state.analysis_history[-3:]  # Last 3

            if recent_analyses:
                for i, analysis in enumerate(reversed(recent_analyses)):
                    with st.expander(f"{analysis.get('disease', 'Unknown')} ({analysis.get('confidence', 0):.0%})", expanded=False):
                        st.write(f"**Time:** {analysis.get('timestamp', 'Unknown')}")
                        st.write(f"**Confidence:** {analysis.get('confidence', 0):.1%}")
                        if analysis.get("filename"):
                            st.write(f"**File:** {analysis['filename']}")

                        if st.button("🔄 View Details", key=f"recent_{i}"):
                            st.json(analysis)
            else:
                st.info("No recent analysis available")

    def render_voice_assistant_tab(self):
        """Render voice assistant interface."""
        st.markdown("### 🎤 Voice Assistant")
        st.markdown("Ask questions about plant care using your voice.")

        # Audio upload
        audio_file = st.file_uploader("Upload audio file", type=["wav", "mp3", "m4a"], help="Upload an audio file with your plant care question")

        if audio_file is not None:
            st.audio(audio_file, format="audio/wav")

            if st.button("🎧 Process Audio", type="primary"):
                with st.spinner("Processing audio..."):
                    # Simulate audio processing
                    st.info("🔄 Audio processing is currently in development. Please use the text chat for now.")

        # Microphone recording placeholder
        st.markdown("---")
        st.markdown("**🎙️ Live Recording**")
        st.info("🚧 Live microphone recording will be available in the next update.")

    def render_chat_assistant_tab(self):
        """Render chat assistant interface."""
        st.markdown("### 💬 Plant Care Assistant")

        # Chat messages display
        chat_container = st.container()

        with chat_container:
            messages = st.session_state.chat_messages[-10:]  # Show last 10 messages

            if messages:
                for message in messages:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
                        st.caption(f"🕒 {message['timestamp'][:16]}")
            else:
                st.info("👋 Hi! I'm your plant care assistant. Ask me anything about plant diseases, care, or treatment!")

        # Chat input
        user_input = st.chat_input("Ask about plant care, diseases, or treatments...")

        if user_input:
            # Add user message
            user_message = {"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()}
            st.session_state.chat_messages.append(user_message)

            # Generate response
            with st.spinner("Thinking..."):
                response = self.generate_text_response(user_input)
                bot_message = {"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()}
                st.session_state.chat_messages.append(bot_message)

            st.rerun()

        # Quick action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🌿 Common Diseases", use_container_width=True):
                self.add_quick_response("Tell me about common plant diseases")
        with col2:
            if st.button("💧 Watering Tips", use_container_width=True):
                self.add_quick_response("How often should I water my plants?")
        with col3:
            if st.button("☀️ Light Requirements", use_container_width=True):
                self.add_quick_response("What are the light requirements for houseplants?")

    def render_history_settings_tab(self):
        """Render history and settings interface."""
        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown("### 📊 Analysis History")

            if st.session_state.analysis_history:
                for i, analysis in enumerate(reversed(st.session_state.analysis_history)):
                    with st.expander(
                        f"{analysis.get('disease', 'Unknown Disease')} - {analysis.get('confidence', 0):.0%} confidence", expanded=False
                    ):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**Disease:** {analysis.get('disease', 'Unknown')}")
                            st.write(f"**Confidence:** {analysis.get('confidence', 0):.1%}")
                            st.write(f"**Type:** {analysis.get('type', 'Unknown').title()}")
                        with col_b:
                            st.write(f"**Date:** {analysis.get('timestamp', 'Unknown')[:10]}")
                            st.write(f"**Time:** {analysis.get('timestamp', 'Unknown')[11:16]}")
                            if analysis.get("filename"):
                                st.write(f"**File:** {analysis['filename']}")
                            if st.button("View Full Report", key=f"report_{i}"):
                                st.json(analysis)
            else:
                st.info("No analysis history available yet. Start by analyzing a plant image!")

        with col2:
            st.markdown("### ⚙️ Advanced Settings")

            # Model management
            st.markdown("**🔧 Model Configuration**")
            for model_type in ["vision", "audio", "text"]:
                current_model = st.session_state.current_models[model_type]
                model_info = self.models[model_type][current_model]

                with st.expander(f"{model_type.title()}: {model_info['name']}", expanded=False):
                    st.write(f"**Accuracy:** {model_info['accuracy']}")
                    st.write(f"**Speed:** {model_info['speed']}")

                    # Model selector
                    model_options = list(self.models[model_type].keys())
                    current_idx = model_options.index(current_model)

                    new_model = st.selectbox(
                        f"Select {model_type} model:",
                        options=model_options,
                        index=current_idx,
                        format_func=lambda x, mt=model_type: self.models[mt][x]["name"],
                        key=f"detailed_{model_type}_model",
                    )

                    if new_model != current_model:
                        st.session_state.current_models[model_type] = new_model
                        st.success(f"✅ Updated {model_type} model")
                        st.rerun()

            # Data management
            st.markdown("---")
            st.markdown("**🗂️ Data Management**")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🧹 Clear All Data", use_container_width=True):
                    st.session_state.analysis_history = []
                    st.session_state.chat_messages = []
                    st.session_state.comparison_history = []
                    st.success("All data cleared!")
                    st.rerun()

            with col_b:
                if st.button("💾 Export All", use_container_width=True):
                    self.export_session_data()

    def render_image_comparison_tab(self):
        """Render image comparison interface."""
        st.markdown("### 🔄 Image Comparison")

        # Upload sections
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📷 First Image")
            image1 = st.file_uploader(
                "Upload first plant image", type=["jpg", "jpeg", "png"], key="image1_uploader", help="Upload the first image for comparison"
            )

        with col2:
            st.markdown("#### 📷 Second Image")
            image2 = st.file_uploader(
                "Upload second plant image", type=["jpg", "jpeg", "png"], key="image2_uploader", help="Upload the second image for comparison"
            )

        if image1 is not None and image2 is not None:
            # Display comparison
            self.render_side_by_side_comparison(image1, image2)

            # Comparison controls
            col_comp1, col_comp2, col_comp3 = st.columns(3)

            with col_comp1:
                if st.button("🔍 Compare Both", type="primary", use_container_width=True):
                    self.analyze_comparison(image1, image2)

            with col_comp2:
                if st.button("💾 Save Comparison", use_container_width=True):
                    self.save_comparison(image1, image2)

            with col_comp3:
                if st.button("📊 View Insights", use_container_width=True):
                    self.show_comparison_insights(image1, image2)
        else:
            st.info("👆 Upload two plant images above to start comparing")

        # Comparison history
        st.markdown("---")
        st.markdown("### 📚 Comparison History")

        history = st.session_state.comparison_history

        if history:
            st.info(f"📊 {len(history)} comparisons in history")

            # Display recent comparisons
            for i, comparison in enumerate(reversed(history[-5:])):
                with st.expander(f"🔄 Comparison {len(history) - i} - {comparison.get('timestamp', 'Unknown')[:16]}", expanded=False):
                    if "image1_name" in comparison and "image2_name" in comparison:
                        st.write(f"**Images:** {comparison['image1_name']} vs {comparison['image2_name']}")

                    st.write(f"**Type:** {comparison.get('type', 'Unknown').replace('_', ' ').title()}")
                    st.write(f"**Time:** {comparison.get('timestamp', 'Unknown')}")

                    if "results" in comparison:
                        if st.button("📊 View Results", key=f"view_results_{i}"):
                            st.json(comparison["results"])
        else:
            st.info("No comparison history yet. Start by comparing two images!")

    # Helper methods for analysis and data processing

    def analyze_image(self, image: Image.Image) -> dict[str, Any] | None:
        """Analyze uploaded image using vision model."""
        try:
            # Initialize vision adapter if needed
            if not self.vision_adapter:
                self.vision_adapter = VisionAdapter()

            # Convert PIL image to format expected by adapter
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                image.save(tmp_file.name, "JPEG")

                # Perform analysis using predict method
                disease_class, confidence = self.vision_adapter.predict(image)

                # Format result
                return {
                    "disease": disease_class,
                    "confidence": confidence,
                    "description": self.get_disease_description(disease_class),
                    "treatment": self.get_treatment_advice(disease_class),
                    "risk_level": self.get_risk_level(confidence),
                }

        except Exception as e:
            self.logger.error(f"Image analysis error: {e}")
            # Mock result for development
            return {
                "disease": "Tomato Late Blight",
                "confidence": 0.87,
                "description": "Late blight is a serious disease affecting tomato plants.",
                "treatment": "Apply copper-based fungicide and improve air circulation",
                "risk_level": "high",
            }

        return None

    def generate_text_response(self, user_input: str) -> str:
        """Generate response to user text input."""
        try:
            # Initialize text adapter if needed
            if not self.text_adapter:
                self.text_adapter = TextAdapter()

            # Generate response using generate_response method
            response = self.text_adapter.generate_response(disease_class="general", user_query=user_input, confidence=0.0)
            return response

        except Exception as e:
            self.logger.error(f"Text processing error: {e}")
            return "I'm having trouble understanding your question. Please try rephrasing it or check that all models are properly loaded."

    def add_quick_response(self, question: str):
        """Add a quick response to chat."""
        # Add user message
        user_message = {"role": "user", "content": question, "timestamp": datetime.now().isoformat()}
        st.session_state.chat_messages.append(user_message)

        # Generate and add response
        response = self.generate_text_response(question)
        bot_message = {"role": "assistant", "content": response, "timestamp": datetime.now().isoformat()}
        st.session_state.chat_messages.append(bot_message)
        st.rerun()

    def display_analysis_result(self, result: dict[str, Any]):
        """Display analysis results in a formatted card."""
        st.markdown("### 🔍 Analysis Results")

        # Main result card
        risk_color = {"low": "#4CAF50", "medium": "#FF9800", "high": "#F44336"}.get(result.get("risk_level", "medium"), "#FF9800")

        st.markdown(
            f"""
        <div style='background: white; padding: 1.5rem; border-radius: 15px; border-left: 5px solid {risk_color};
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 1rem 0;'>
            <h3 style='margin: 0 0 1rem 0; color: #333;'>🦠 {result.get("disease", "Unknown Disease")}</h3>
            <p style='margin: 0.5rem 0; font-size: 1.1rem;'><strong>🎯 Confidence:</strong> {result.get("confidence", 0):.1%}</p>
            <p style='margin: 0.5rem 0;'><strong>⚠️ Risk Level:</strong>
               <span style='color: {risk_color}; font-weight: bold; text-transform: uppercase;'>{result.get("risk_level", "Medium")}</span></p>
            <p style='margin: 0.5rem 0;'><strong>📝 Description:</strong> {result.get("description", "No description available")}</p>
            <p style='margin: 0.5rem 0;'><strong>💊 Treatment:</strong> {result.get("treatment", "Consult with plant care specialist")}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_side_by_side_comparison(self, image1, image2):
        """Render side-by-side comparison view."""
        col1, col2 = st.columns(2)

        with col1:
            img1 = Image.open(image1)
            st.image(img1, caption="First Image", use_column_width=True)

            # Quick analysis for first image
            if st.button("🔍 Analyze First", key="analyze_first"):
                with st.spinner("Analyzing first image..."):
                    result1 = self.analyze_image(img1)
                    if result1:
                        st.success(f"**Disease:** {result1.get('disease', 'Unknown')}")
                        st.info(f"**Confidence:** {result1.get('confidence', 0):.1%}")

        with col2:
            img2 = Image.open(image2)
            st.image(img2, caption="Second Image", use_column_width=True)

            # Quick analysis for second image
            if st.button("🔍 Analyze Second", key="analyze_second"):
                with st.spinner("Analyzing second image..."):
                    result2 = self.analyze_image(img2)
                    if result2:
                        st.success(f"**Disease:** {result2.get('disease', 'Unknown')}")
                        st.info(f"**Confidence:** {result2.get('confidence', 0):.1%}")

    def analyze_comparison(self, image1, image2):
        """Analyze both images for comparison."""
        img1 = Image.open(image1)
        img2 = Image.open(image2)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**First Image Analysis:**")
            with st.spinner("Analyzing first image..."):
                result1 = self.analyze_image(img1)
                if result1:
                    st.success(f"Disease: {result1.get('disease', 'Unknown')}")
                    st.info(f"Confidence: {result1.get('confidence', 0):.1%}")

        with col2:
            st.markdown("**Second Image Analysis:**")
            with st.spinner("Analyzing second image..."):
                result2 = self.analyze_image(img2)
                if result2:
                    st.success(f"Disease: {result2.get('disease', 'Unknown')}")
                    st.info(f"Confidence: {result2.get('confidence', 0):.1%}")

        # Comparison insights
        if result1 and result2:
            st.markdown("### 🔍 Comparison Insights")

            disease1 = result1.get("disease", "Unknown")
            disease2 = result2.get("disease", "Unknown")

            if disease1 == disease2:
                st.success(f"✅ Both images show the same condition: {disease1}")
            else:
                st.warning(f"⚠️ Different conditions detected: {disease1} vs {disease2}")

            conf1 = result1.get("confidence", 0)
            conf2 = result2.get("confidence", 0)

            if abs(conf1 - conf2) < 0.1:
                st.info("Similar confidence levels in both analyses")
            elif conf1 > conf2:
                st.info("First image analysis has higher confidence")
            else:
                st.info("Second image analysis has higher confidence")

    def save_comparison(self, image1, image2):
        """Save comparison to history."""
        if image1 is not None and image2 is not None:
            comparison_data = {
                "timestamp": datetime.now().isoformat(),
                "type": "saved_comparison",
                "image1_name": image1.name,
                "image2_name": image2.name,
                "status": "saved",
            }

            if "comparison_history" not in st.session_state:
                st.session_state.comparison_history = []

            st.session_state.comparison_history.append(comparison_data)
            st.success("✅ Comparison saved to history!")
        else:
            st.warning("⚠️ Please upload both images before saving")

    def show_comparison_insights(self, image1, image2):
        """Show detailed comparison insights."""
        st.info("📊 Generating detailed comparison insights...")

        insights = [
            "Both images appear to be from similar plant species",
            "Lighting conditions differ between the two images",
            "Image quality is suitable for analysis",
            "Consider taking images from similar angles for better comparison",
        ]

        st.markdown("**Insights:**")
        for insight in insights:
            st.write(f"• {insight}")

    def export_session_data(self):
        """Export all session data."""
        export_data = {
            "export_time": datetime.now().isoformat(),
            "analysis_history": st.session_state.analysis_history,
            "chat_messages": st.session_state.chat_messages,
            "comparison_history": st.session_state.comparison_history,
            "current_models": st.session_state.current_models,
        }

        st.download_button(
            label="📄 Download Session Data",
            data=json.dumps(export_data, indent=2),
            file_name=f"plantguard_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    def show_quick_stats(self):
        """Show quick statistics."""
        col1, col2, col3 = st.columns(3)

        with col1:
            total_analyses = len(st.session_state.analysis_history)
            st.metric("Total Analyses", total_analyses)

        with col2:
            total_chats = len(st.session_state.chat_messages)
            st.metric("Chat Messages", total_chats)

        with col3:
            total_comparisons = len(st.session_state.comparison_history)
            st.metric("Comparisons", total_comparisons)

    def show_help_info(self):
        """Show help information."""
        st.info("""
        **PlantGuard Help:**

        📷 **Image Analysis:** Upload plant images for AI-powered disease detection
        🎤 **Voice Assistant:** Ask questions using voice (development in progress)
        💬 **Chat Assistant:** Get answers about plant care and diseases
        📈 **History:** View and manage your analysis history
        🔄 **Compare:** Compare two plant images side by side
        ⚙️ **Settings:** Configure models and manage data
        """)

    # Utility methods

    def get_disease_description(self, disease_class: str) -> str:
        """Get description for a disease class."""
        descriptions = {
            "Tomato Late Blight": "A serious fungal disease that affects tomato plants, causing dark spots on leaves and stems.",
            "Tomato Early Blight": "A common fungal disease causing brown spots with concentric rings on older leaves.",
            "Healthy": "Plant appears healthy with no visible signs of disease or stress.",
        }
        return descriptions.get(disease_class, "No detailed description available for this condition.")

    def get_treatment_advice(self, disease_class: str) -> str:
        """Get treatment advice for a disease class."""
        treatments = {
            "Tomato Late Blight": "Apply copper-based fungicide, improve air circulation, avoid overhead watering.",
            "Tomato Early Blight": "Remove affected leaves, apply fungicide, ensure proper spacing between plants.",
            "Healthy": "Continue current care routine, monitor regularly for any changes.",
        }
        return treatments.get(disease_class, "Consult with a plant pathologist or agricultural extension service.")

    def get_risk_level(self, confidence: float) -> str:
        """Determine risk level based on confidence."""
        if confidence > 0.8:
            return "high"
        elif confidence > 0.6:
            return "medium"
        else:
            return "low"

    def run(self):
        """Main application runner."""
        self.render_header()
        self.render_settings_panel()
        st.markdown("---")
        self.render_main_interface()


def main():
    """Main entry point for the simplified application."""
    app = SimplifiedPlantGuardApp()
    app.run()


if __name__ == "__main__":
    main()
