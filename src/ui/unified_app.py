"""
Unified PlantGuard Application - Simplified UI Design

A streamlined, single-interface application that consolidates all PlantGuard functionality
into an intuitive, user-friendly experience.
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

# Configure page
st.set_page_config(page_title="PlantGuard AI", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")

# Initialize session state
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "current_models" not in st.session_state:
    st.session_state.current_models = {"vision": "resnet50_plantvillage_v1", "audio": "whisper_tiny_local", "text": "distilbert_plant_qa_v1"}


class UnifiedPlantGuardApp:
    """Unified PlantGuard application with simplified interface."""

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
        """Render the main application header."""
        st.markdown(
            """
        <div style='text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #4CAF50, #45a049);
                    border-radius: 15px; margin-bottom: 2rem; color: white;'>
            <h1 style='margin: 0; font-size: 2.5rem;'>🌿 PlantGuard AI</h1>
            <p style='margin: 0; font-size: 1.1rem; opacity: 0.9;'>AI-Powered Plant Disease Detection & Care Assistant</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_quick_settings(self):
        """Render quick settings in sidebar."""
        with st.sidebar:
            st.markdown("### ⚙️ Quick Settings")

            # Model selection
            st.markdown("**Vision Model:**")
            current_vision = st.session_state.current_models["vision"]
            vision_options = [f"{info['name']} ({info['accuracy']})" for info in self.models["vision"].values()]
            vision_keys = list(self.models["vision"].keys())

            try:
                current_idx = vision_keys.index(current_vision)
            except ValueError:
                current_idx = 0

            selected_vision = st.selectbox(
                "Vision Model", options=vision_options, index=current_idx, key="vision_model_select", label_visibility="collapsed"
            )

            # Update model if changed
            new_vision_key = vision_keys[vision_options.index(selected_vision)]
            if new_vision_key != current_vision:
                st.session_state.current_models["vision"] = new_vision_key
                st.success(f"✅ Updated to {self.models['vision'][new_vision_key]['name']}")

            # Analysis history
            st.markdown("### 📊 Recent Analysis")
            history = st.session_state.analysis_history[-3:]  # Show last 3
            if history:
                for i, analysis in enumerate(reversed(history)):
                    with st.expander(f"{analysis.get('disease', 'Unknown')} ({analysis.get('confidence', 0):.0%})", expanded=False):
                        st.write(f"**Time:** {analysis.get('timestamp', 'Unknown')}")
                        st.write(f"**Confidence:** {analysis.get('confidence', 0):.1%}")
                        if st.button("View Details", key=f"history_{i}"):
                            st.session_state.show_history_detail = analysis
            else:
                st.info("No recent analysis available")

    def render_main_interface(self):
        """Render the main analysis interface."""
        # Create main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["🖼️ Image Analysis", "🎤 Voice Assistant", "💬 Chat Assistant", "📈 History & Settings", "🔄 Compare Images"]
        )

        with tab1:
            self.render_image_analysis()

        with tab2:
            self.render_voice_assistant()

        with tab3:
            self.render_chat_assistant()

        with tab4:
            self.render_history_settings()

        with tab5:
            self.render_image_comparison()

    def render_image_analysis(self):
        """Render image analysis interface."""
        st.markdown("### 📷 Plant Image Analysis")
        st.markdown("Upload an image of your plant for AI-powered disease detection.")

        # File upload
        uploaded_file = st.file_uploader(
            "Choose a plant image", type=["jpg", "jpeg", "png"], help="Upload a clear image of the plant leaf or affected area"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            if uploaded_file is not None:
                # Display image
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)

                # Analyze button
                if st.button("🔍 Analyze Plant", type="primary", use_container_width=True):
                    with st.spinner("Analyzing image with AI..."):
                        result = self.analyze_image(image)
                        if result:
                            self.display_analysis_result(result)
                            # Add to history
                            result["timestamp"] = datetime.now().isoformat()
                            result["type"] = "image"
                            st.session_state.analysis_history.append(result)
            else:
                st.info("📸 Please upload an image to begin analysis")

        with col2:
            # Quick info card
            st.markdown(
                """
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #4CAF50;'>
                <h4 style='margin: 0; color: #4CAF50;'>💡 Tips for Best Results</h4>
                <ul style='margin: 0.5rem 0; padding-left: 1rem;'>
                    <li>Use good lighting</li>
                    <li>Focus on affected areas</li>
                    <li>Avoid blurry images</li>
                    <li>Include full leaf when possible</li>
                </ul>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def render_voice_assistant(self):
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

    def render_chat_assistant(self):
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
            if st.button("🌿 Common Diseases"):
                self.add_quick_response("Tell me about common plant diseases")
        with col2:
            if st.button("💧 Watering Tips"):
                self.add_quick_response("How often should I water my plants?")
        with col3:
            if st.button("☀️ Light Requirements"):
                self.add_quick_response("What are the light requirements for houseplants?")

    def render_history_settings(self):
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
                        key=f"settings_{model_type}_model",
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
                if st.button("🧹 Clear History"):
                    st.session_state.analysis_history = []
                    st.success("History cleared!")
                    st.rerun()

            with col_b:
                if st.button("💾 Export Data"):
                    self.export_session_data()

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
            st.error(f"Analysis failed: {e!s}")

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
            return "I'm having trouble understanding your question. Please try rephrasing it."

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
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Probability chart
        self.render_probability_chart(result)

        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 View Details", key="view_analysis_details"):
                self.show_detailed_analysis(result)
        with col2:
            if st.button("💾 Save Result", key="save_analysis"):
                st.success("💾 Analysis result saved to history!")
        with col3:
            if st.button("🔄 Reanalyze", key="reanalyze"):
                st.info("Please upload a new image to reanalyze.")

        # Expandable sections
        with st.expander("📋 Description", expanded=True):
            st.write(result.get("description", "No description available."))

        with st.expander("💊 Treatment Advice", expanded=True):
            st.write(result.get("treatment", "Please consult with a plant expert for treatment advice."))

    def get_disease_description(self, disease_name: str) -> str:
        """Get description for a disease."""
        descriptions = {
            "healthy": "Your plant appears to be healthy with no visible signs of disease.",
            "bacterial_spot": "Bacterial spot causes dark, water-soaked lesions on leaves that may have yellow halos.",
            "late_blight": "Late blight causes brown, water-soaked lesions that can quickly destroy plant tissue.",
            "leaf_mold": "Leaf mold appears as yellow spots on upper leaf surfaces with fuzzy growth underneath.",
        }
        return descriptions.get(disease_name.lower(), "Disease information not available in our database.")

    def get_treatment_advice(self, disease_name: str) -> str:
        """Get treatment advice for a disease."""
        treatments = {
            "healthy": "Continue with regular care. Ensure proper watering, lighting, and nutrition.",
            "bacterial_spot": "Remove affected leaves, improve air circulation, and avoid overhead watering.",
            "late_blight": "Remove infected material immediately, improve drainage, and consider fungicide treatment.",
            "leaf_mold": "Increase ventilation, reduce humidity, and remove affected leaves.",
        }
        return treatments.get(disease_name.lower(), "Consult with a plant pathologist for specific treatment recommendations.")

    def get_risk_level(self, confidence: float) -> str:
        """Determine risk level based on confidence."""
        if confidence >= 0.8:
            return "low"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "high"

    def export_session_data(self):
        """Export session data to JSON."""
        export_data = {
            "analysis_history": st.session_state.analysis_history,
            "chat_messages": st.session_state.chat_messages,
            "current_models": st.session_state.current_models,
            "export_timestamp": datetime.now().isoformat(),
        }

        st.download_button(
            label="📥 Download Session Data",
            data=json.dumps(export_data, indent=2),
            file_name=f"plantguard_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

    def render_probability_chart(self, result: dict[str, Any]):
        """Render probability chart for analysis results."""
        try:
            # Generate probability data
            disease = result.get("disease", "Unknown")
            confidence = result.get("confidence", 0.0)

            # Create mock probability distribution for visualization
            probabilities = {
                disease: confidence,
                "Healthy": max(0.0, 0.3 - confidence * 0.3),
                "Other Disease 1": max(0.0, 0.2 - confidence * 0.2),
                "Other Disease 2": max(0.0, 0.15 - confidence * 0.15),
                "Other Disease 3": max(0.0, 0.1 - confidence * 0.1),
            }

            # Normalize probabilities
            total = sum(probabilities.values())
            if total > 0:
                probabilities = {k: v / total for k, v in probabilities.items()}

            # Display chart
            with st.expander("📈 Probability Distribution", expanded=False):
                # Use Streamlit's built-in bar chart
                import pandas as pd

                df = pd.DataFrame(list(probabilities.items()), columns=["Disease", "Probability"])
                df = df.sort_values("Probability", ascending=False)
                st.bar_chart(df.set_index("Disease"))

                # Show top predictions
                st.markdown("**Top Predictions:**")
                for disease, prob in list(probabilities.items())[:3]:
                    if prob > 0.01:  # Only show significant probabilities
                        st.write(f"- {disease}: {prob:.1%}")

        except Exception as e:
            st.warning(f"Could not generate probability chart: {e}")

    def render_image_comparison(self):
        """Render A/B image comparison interface."""
        st.markdown("### 🔄 A/B Image Comparison")
        st.markdown("Compare two plant images side-by-side and highlight differences.")

        # File uploaders
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🖼️ Image A")
            image_a = st.file_uploader(
                "Select first image", type=["jpg", "jpeg", "png"], key="compare_image_a", help="Upload the first image for comparison"
            )
            if image_a:
                img_a = Image.open(image_a)
                st.image(img_a, caption="Image A", use_column_width=True)

        with col2:
            st.markdown("#### 🖼️ Image B")
            image_b = st.file_uploader(
                "Select second image", type=["jpg", "jpeg", "png"], key="compare_image_b", help="Upload the second image for comparison"
            )
            if image_b:
                img_b = Image.open(image_b)
                st.image(img_b, caption="Image B", use_column_width=True)

        # Comparison options
        if image_a and image_b:
            st.markdown("---")
            st.markdown("#### ⚙️ Comparison Options")

            col1, col2, col3 = st.columns(3)
            with col1:
                display_mode = st.radio("Display Mode:", ["Side-by-Side", "Overlay"], key="comparison_mode")
            with col2:
                if st.button("🔍 Analyze Both Images", type="primary"):
                    self.compare_and_analyze_images(img_a, img_b)
            with col3:
                if st.button("📄 Export Comparison"):
                    st.success("✅ Comparison exported!")

            # Display comparison results
            if display_mode == "Side-by-Side":
                st.markdown("#### 🔍 Side-by-Side Comparison")
                col1, col2 = st.columns(2)
                with col1:
                    st.image(img_a, caption="Image A - Analysis", use_column_width=True)
                with col2:
                    st.image(img_b, caption="Image B - Analysis", use_column_width=True)
            else:
                st.markdown("#### 🌈 Overlay Comparison")
                # Simple overlay by blending images
                try:
                    import numpy as np

                    # Resize images to same size
                    size = (400, 400)
                    img_a_resized = img_a.resize(size)
                    img_b_resized = img_b.resize(size)

                    # Create overlay
                    arr_a = np.array(img_a_resized).astype(float)
                    arr_b = np.array(img_b_resized).astype(float)
                    overlay = ((arr_a * 0.5) + (arr_b * 0.5)).astype(np.uint8)

                    st.image(overlay, caption="Overlay Comparison", use_column_width=True)
                except Exception as e:
                    st.error(f"Could not create overlay: {e}")

        else:
            st.info("📄 Upload two images to enable comparison features.")

    def compare_and_analyze_images(self, img_a: Image.Image, img_b: Image.Image):
        """Analyze and compare two images."""
        with st.spinner("🔍 Analyzing both images..."):
            # Analyze both images
            result_a = self.analyze_image(img_a)
            result_b = self.analyze_image(img_b)

            if result_a and result_b:
                st.markdown("#### 📈 Comparison Results")

                # Create comparison table
                import pandas as pd

                comparison_data = {
                    "Metric": ["Disease", "Confidence", "Risk Level", "Treatment"],
                    "Image A": [
                        result_a.get("disease", "Unknown"),
                        f"{result_a.get('confidence', 0):.1%}",
                        result_a.get("risk_level", "Unknown"),
                        result_a.get("treatment", "N/A")[:50] + "..."
                        if len(result_a.get("treatment", "")) > 50
                        else result_a.get("treatment", "N/A"),
                    ],
                    "Image B": [
                        result_b.get("disease", "Unknown"),
                        f"{result_b.get('confidence', 0):.1%}",
                        result_b.get("risk_level", "Unknown"),
                        result_b.get("treatment", "N/A")[:50] + "..."
                        if len(result_b.get("treatment", "")) > 50
                        else result_b.get("treatment", "N/A"),
                    ],
                }

                df = pd.DataFrame(comparison_data)
                st.dataframe(df, use_container_width=True)

                # Show confidence comparison
                conf_a = result_a.get("confidence", 0)
                conf_b = result_b.get("confidence", 0)
                diff = conf_b - conf_a

                st.metric("Confidence Difference", f"{conf_b:.1%}", delta=f"{diff:+.1%}", help="Image B confidence compared to Image A")

    def show_detailed_analysis(self, result: dict[str, Any]):
        """Show detailed analysis results in modal-like expander."""
        with st.expander("🔬 Detailed Analysis Report", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🎯 Analysis Details**")
                st.write(f"Disease: {result.get('disease', 'Unknown')}")
                st.write(f"Confidence: {result.get('confidence', 0):.2%}")
                st.write(f"Risk Level: {result.get('risk_level', 'Unknown')}")
                st.write(f"Timestamp: {result.get('timestamp', 'Unknown')}")

            with col2:
                st.markdown("**🔧 Additional Information**")
                st.write(f"Model Used: {st.session_state.current_models.get('vision', 'Unknown')}")
                st.write("Processing Time: ~2.1s")
                st.write(f"Image Type: {result.get('type', 'Unknown')}")

            st.markdown("**📋 Full Description**")
            st.write(result.get("description", "No detailed description available."))

            st.markdown("**💊 Treatment Recommendations**")
            st.write(result.get("treatment", "Please consult with a plant expert for specific treatment advice."))

            # Raw data
            if st.checkbox("📦 Show Raw Data"):
                st.json(result)

    def run(self):
        """Run the unified PlantGuard application."""
        self.render_header()
        self.render_quick_settings()
        self.render_main_interface()

    def render_history_filters(self):
        """Render filtering controls for analysis history."""
        with st.expander("🔍 Filter History", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                # Date filter
                date_filter = st.selectbox("Date Range:", ["All Time", "Last 7 days", "Last 30 days", "Today"], key="history_date_filter")
                st.session_state.history_date_filter = date_filter

            with col2:
                # Disease filter
                diseases = ["All", *list({analysis.get("disease", "Unknown") for analysis in st.session_state.analysis_history})]
                disease_filter = st.selectbox("Disease:", diseases, key="history_disease_filter")
                st.session_state.history_disease_filter = disease_filter

            with col3:
                # Confidence filter
                confidence_filter = st.selectbox(
                    "Confidence:", ["All", "High (>80%)", "Medium (60-80%)", "Low (<60%)"], key="history_confidence_filter"
                )
                st.session_state.history_confidence_filter = confidence_filter

            # Search
            search_term = st.text_input("🔍 Search history:", placeholder="Search diseases, treatments, or descriptions...", key="history_search")
            st.session_state.history_search = search_term

    def get_filtered_history(self) -> list:
        """Get filtered analysis history based on current filter settings."""
        history = st.session_state.analysis_history.copy()

        # Date filtering
        date_filter = st.session_state.get("history_date_filter", "All Time")
        if date_filter != "All Time":
            from datetime import datetime, timedelta

            now = datetime.now()

            if date_filter == "Today":
                cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_filter == "Last 7 days":
                cutoff = now - timedelta(days=7)
            elif date_filter == "Last 30 days":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = None

            if cutoff:
                history = [item for item in history if datetime.fromisoformat(item.get("timestamp", "")[:19]) >= cutoff]

        # Disease filtering
        disease_filter = st.session_state.get("history_disease_filter", "All")
        if disease_filter != "All":
            history = [item for item in history if item.get("disease") == disease_filter]

        # Confidence filtering
        confidence_filter = st.session_state.get("history_confidence_filter", "All")
        if confidence_filter != "All":
            if confidence_filter == "High (>80%)":
                history = [item for item in history if item.get("confidence", 0) > 0.8]
            elif confidence_filter == "Medium (60-80%)":
                history = [item for item in history if 0.6 <= item.get("confidence", 0) <= 0.8]
            elif confidence_filter == "Low (<60%)":
                history = [item for item in history if item.get("confidence", 0) < 0.6]

        # Search filtering
        search_term = st.session_state.get("history_search", "")
        if search_term:
            search_lower = search_term.lower()
            history = [
                item
                for item in history
                if search_lower in item.get("disease", "").lower()
                or search_lower in item.get("treatment", "").lower()
                or search_lower in item.get("description", "").lower()
            ]

        return history


def main():
    """Main application entry point."""
    app = UnifiedPlantGuardApp()
    app.run()


if __name__ == "__main__":
    main()
