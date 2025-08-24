"""PlantGuard Streamlit application for multimodal plant disease detection."""
# ruff: noqa: E402

import json
import logging
import platform
import subprocess  # nosec B404: subprocess is required for
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import soundfile as sf
import streamlit as st
from PIL import Image
from streamlit_webrtc import WebRtcMode, webrtc_streamer

if TYPE_CHECKING:
    AudioFrame = Any  # Placeholder for type checking
else:
    AudioFrame = Any

# Ensure src is on sys.path for local imports before importing project modules
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from typing import Optional

from core.audio import AudioAdapter
from core.nlp import TextAdapter
from core.vision import VisionAdapter
from ui.components import ModelSwitcher

# Module logger
logger = logging.getLogger(__name__)

# Get current selections
st.set_page_config(page_title="PlantGuard", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for improved UI
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }

    .model-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 1rem;
    }

    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-loaded { background-color: #4CAF50; }
    .status-loading { background-color: #ff9800; }
    .status-error { background-color: #f44336; }

    .confidence-high { color: #4CAF50; font-weight: bold; }
    .confidence-medium { color: #ff9800; font-weight: bold; }
    .confidence-low { color: #f44336; font-weight: bold; }

    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }

    /* Enhanced Dropdown Styling */
    .stSelectbox > div > div {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .stSelectbox > div > div:hover {
        border-color: #4CAF50;
        box-shadow: 0 4px 8px rgba(76, 175, 80, 0.15);
        transform: translateY(-1px);
    }

    .stSelectbox > div > div:focus-within {
        border-color: #4CAF50;
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.2);
    }

    /* Dropdown arrow styling */
    .stSelectbox svg {
        color: #4CAF50;
        transition: transform 0.2s ease;
    }

    .stSelectbox:hover svg {
        transform: scale(1.1) rotate(180deg);
    }

    /* Sidebar enhancements */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0px 24px;
        background-color: #f8f9fa;
        border-radius: 8px 8px 0px 0px;
        border: 2px solid #dee2e6;
        color: #495057;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
        border-color: #4CAF50;
        transform: translateY(-2px);
    }

    /* Button enhancements */
    .stButton > button {
        border-radius: 8px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        font-weight: 500;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    /* File uploader styling */
    .stFileUploader > div > div {
        border: 2px dashed #4CAF50;
        border-radius: 8px;
        background: #f8f9fa;
        transition: all 0.3s ease;
    }

    .stFileUploader:hover > div > div {
        border-color: #45a049;
        background: #e8f5e8;
        transform: scale(1.02);
    }
</style>
""",
    unsafe_allow_html=True,
)


# Header
st.markdown(
    """
<div class="main-header">
    <h1>🌿 PlantGuard AI</h1>
    <p>Advanced Multimodal Plant Disease Detection System</p>
</div>
""",
    unsafe_allow_html=True,
)


# Initialize model switcher
model_switcher = ModelSwitcher()

# Try to initialize Model Manager early so we can autoload the configured default model
try:
    from src.features.model_switching.model_manager import PlantGuardModelManager

    try:
        model_manager: Optional["PlantGuardModelManager"] = PlantGuardModelManager(autoload_default=True)
    except Exception as exc:
        logger.exception("Failed to initialize PlantGuardModelManager: %s", exc)
        model_manager = None
except Exception as exc:
    logger.exception("Failed to import PlantGuardModelManager: %s", exc)
    model_manager = None


# Initialize adapters (cached for performance)
@st.cache_resource
def load_adapters() -> tuple[VisionAdapter, AudioAdapter, TextAdapter]:
    """Load and cache the ML adapters."""
    # Preferred behavior: use the ModelManager's autoloaded adapter when available
    vision = None
    try:
        if model_manager and getattr(model_manager, "current_adapter", None):
            # Use the autoloaded adapter (usually a Hugging Face model by default)
            vision = model_manager.current_adapter
    except Exception:
        vision = None

    # Fallback to local checkpoint adapter when no manager/adapter is available
    if vision is None:
        vision_model_path = "data/models/vision_resnet50.pt"
        try:
            if Path(vision_model_path).exists():
                vision = VisionAdapter(model_path=vision_model_path, lazy_load=False)
            else:
                # No local checkpoint: create adapter without a checkpoint so UI uses model manager or empty adapter
                vision = VisionAdapter(model_path=None)
        except Exception:
            # Fall back to a bare adapter; predict calls will surface errors if not loaded
            vision = VisionAdapter(model_path=None)

    # Load class mapping
    classes_path = "data/knowledge_base/plantvillage_classes.json"
    if Path(classes_path).exists():
        try:
            # Only call load_class_mapping when the adapter exposes it and vision is not None
            if hasattr(vision, "load_class_mapping") and vision is not None:
                vision.load_class_mapping(classes_path)
        except Exception as exc:
            logger.exception("Failed to load class mapping for vision adapter: %s", exc)

    audio = AudioAdapter()
    text = TextAdapter()
    return vision, audio, text


@st.cache_data
def get_model_status() -> dict[str, str]:
    """Get current model loading status."""
    return {"vision": "loaded", "audio": "loaded", "text": "loaded"}


# Initialize adapters at module level so later code can reference them safely
try:
    vision_adapter, audio_adapter, text_adapter = load_adapters()
except Exception:
    vision_adapter = None  # type: ignore[assignment]
    audio_adapter = None  # type: ignore[assignment]
    text_adapter = None  # type: ignore[assignment]


# Available models configuration
available_models = {
    "vision": ["vit_base_plants", "resnet50_plantvillage_v1", "mobilenet_fast"],
    "audio": ["whisper_tiny_local", "wav2vec2_plant_sounds"],
    "text": ["distilbert_plant_qa_v1", "roberta_plant_care", "t5_small_plant_qa"],
}

# Main Model Selection Area (moved from sidebar)
st.markdown("## 🚀 Advanced Model Selection")
st.markdown("*Choose the optimal AI models for your plant analysis workflow*")
st.markdown("---")

# Add enhanced dropdown CSS
st.markdown(
    """
    <style>
    .model-dropdown-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #dee2e6;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .model-dropdown-container:hover {
        border-color: #4CAF50;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15);
        transform: translateY(-2px);
    }

    .model-type-header {
        display: flex;
        align-items: center;
        margin-bottom: 0.75rem;
        font-weight: 600;
        color: #2c3e50;
    }

    .model-icon {
        font-size: 1.5em;
        margin-right: 0.75rem;
    }

    .model-description {
        font-size: 0.85em;
        color: #6c757d;
        font-style: italic;
    }

    .performance-badge {
        text-align: center;
        margin-top: 0.75rem;
        padding: 0.5rem;
        border-radius: 6px;
        font-weight: bold;
        font-size: 1.1em;
    }

    .badge-green {
        background: rgba(76, 175, 80, 0.1);
        border-left: 4px solid #4CAF50;
        color: #4CAF50;
    }

    .badge-blue {
        background: rgba(33, 150, 243, 0.1);
        border-left: 4px solid #2196F3;
        color: #2196F3;
    }

    .badge-orange {
        background: rgba(255, 152, 0, 0.1);
        border-left: 4px solid #FF9800;
        color: #FF9800;
    }

    .badge-purple {
        background: rgba(156, 39, 176, 0.1);
        border-left: 4px solid #9C27B0;
        color: #9C27B0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Model configurations with rich display names
model_configs = {
    "vision": {
        "icon": "👁️",
        "title": "Vision Model",
        "description": "AI model for plant image analysis",
        "options": {
            "vit_base_plants": "🏆 Vision Transformer (Best - 100%)",
            "resnet50_plantvillage_v1": "🔬 ResNet50 (Balanced - 95%)",
            "mobilenet_fast": "⚡ MobileNet (Fast - 90%)",
        },
        "badges": {
            "vit_base_plants": ("🏆", "100%", "badge-green"),
            "mobilenet_fast": ("⚡", "90%", "badge-orange"),
        },
    },
    "audio": {
        "icon": "🎤",
        "title": "Audio Model",
        "description": "AI model for voice processing",
        "options": {
            "whisper_tiny_local": "🎯 Whisper Tiny (Local)",
            "wav2vec2_plant_sounds": "🌿 Wav2Vec2 (Plant Sounds)",
        },
        "badges": {
            "whisper_tiny_local": ("🎯", "Local", "badge-green"),
            "wav2vec2_plant_sounds": ("🌿", "Beta", "badge-orange"),
        },
    },
    "text": {
        "icon": "💬",
        "title": "Text Model",
        "description": "AI model for plant care questions",
        "options": {
            "distilbert_plant_qa_v1": "🧠 DistilBERT (Plant Q&A)",
            "roberta_plant_care": "🌱 RoBERTa (Advanced)",
            "t5_small_plant_qa": "📝 T5 Small (Creative)",
        },
        "badges": {
            "distilbert_plant_qa_v1": ("🧠", "Stable", "badge-green"),
            "roberta_plant_care": ("🌱", "Advanced", "badge-blue"),
            "t5_small_plant_qa": ("📝", "Creative", "badge-purple"),
        },
    },
}

# Get current selections
current_selections = st.session_state.get(
    "selected_models", {"vision": "vit_base_plants", "audio": "whisper_tiny_local", "text": "distilbert_plant_qa_v1"}
)

col1, col2, col3 = st.columns(3)
columns = [col1, col2, col3]
selected_models = {}

for i, (model_type, config) in enumerate(model_configs.items()):
    with columns[i]:
        # Enhanced container
        st.markdown(
            f"""
            <div class="model-dropdown-container">
                <div class="model-type-header">
                    <span class="model-icon">{config["icon"]}</span>
                    <div>
                        <strong>{config["title"]}</strong>
                        <div class="model-description">{config["description"]}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Get available models and normalize to lists for proper typing
        # available_models entries may be lists or collections; prefer explicit handling
        raw_avail = available_models.get(model_type)
        options_raw = config.get("options", {})
        # Determine fallback keys from config options safely
        if isinstance(options_raw, dict):
            fallback_keys = list(options_raw.keys())
        else:
            fallback_keys = list(options_raw) if options_raw is not None else []

        # Normalize available models into a concrete list[str]
        available_for_type: list[str]
        if raw_avail is None:
            available_for_type = fallback_keys
        elif isinstance(raw_avail, dict):
            available_for_type = list(raw_avail.keys())
        else:
            available_for_type = list(raw_avail)

        current_model = current_selections.get(model_type, available_for_type[0] if available_for_type else "")

        # Create display options and parallel key list
        display_options: list[str] = []
        model_keys: list[str] = []
        options_map = config.get("options", {})
        for key in available_for_type:
            if isinstance(options_map, dict) and key in options_map:
                display_options.append(options_map[key])
                model_keys.append(key)

        # Find current index
        current_index = 0
        if current_model in model_keys:
            current_index = model_keys.index(current_model)

        # Ensure help text uses a string
        help_text = f"Choose the best {str(config['title']).lower()} for your needs"

        # Selectbox: options is a Sequence[str]
        selected_display = st.selectbox(
            f"{config['icon']} Select {config['title']}",
            options=display_options,
            index=current_index,
            key=f"enhanced_{model_type}_select",
            help=help_text,
            label_visibility="collapsed",
        )

        # Map back to model key
        selected_key = model_keys[display_options.index(selected_display)]
        selected_models[model_type] = selected_key

        # Performance badge (guard against Collection typing and missing keys)
        badges = config.get("badges", {})
        if isinstance(badges, dict) and selected_key in badges:
            icon, metric, badge_class = badges[selected_key]
            st.markdown(
                f"""
                <div class="performance-badge {badge_class}">
                    {icon} {metric}
                </div>
                """,
                unsafe_allow_html=True,
            )

# Main content separator
st.markdown("---")

# Current Model Status & Quick Actions (moved from sidebar)
st.markdown("## 🚀 Current Model Status & Quick Actions")
st.markdown("*Monitor your active models and perform quick actions*")

# Get selected models from session state
current_models = st.session_state.get(
    "selected_models", {"vision": "vit_base_plants", "audio": "whisper_tiny_local", "text": "distilbert_plant_qa_v1"}
)

# Model status display
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🌱 Vision Model")
    st.info(f"**Active:** {current_models.get('vision', 'Unknown')}")
    st.metric("Status", "🟢 Loaded", "Ready")

with col2:
    st.markdown("### 🎤 Audio Model")
    st.info(f"**Active:** {current_models.get('audio', 'Unknown')}")
    st.metric("Status", "🟢 Loaded", "Ready")

with col3:
    st.markdown("### 💬 Text Model")
    st.info(f"**Active:** {current_models.get('text', 'Unknown')}")
    st.metric("Status", "🟢 Loaded", "Ready")

# Quick actions row
st.markdown("---")
st.markdown("### ⚡ Quick Actions")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    if st.button("🔄 Reload Models", use_container_width=True, help="Reload all model adapters"):
        st.cache_resource.clear()
        st.success("✅ Models reloaded successfully!")
        st.rerun()

with action_col2:
    if st.button("📊 Quick Test", use_container_width=True, help="Test current models on sample data"):
        st.info("💡 Use the Model Management tab for comprehensive testing and benchmarking!")

with action_col3:
    if st.button("🔧 Settings", use_container_width=True, help="Access advanced model settings"):
        st.info("💡 Model configuration is available in the Model Management tab!")

with action_col4:
    if st.button("📈 Performance", use_container_width=True, help="View model performance metrics"):
        st.info("💡 Detailed performance analysis available in the Model Management tab!")

st.markdown("---")
st.markdown("## 🌿 Plant Analysis Tools")
st.markdown("*Use the tools below to analyze your plants with AI-powered detection*")

# Main content tabs with improved design
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🖼️ Vision Analysis", "🎤 Audio Processing", "💬 Text Q&A", "📚 Training", "🔧 Model Management"])

# Vision Analysis Tab
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📤 Upload Plant Image")
        img_file = st.file_uploader(
            "Choose a leaf photo for analysis",
            ["png", "jpg", "jpeg"],
            help="Upload clear images of plant leaves for best results",
        )

    with col2:
        if img_file:
            # Load and display image
            if isinstance(img_file, Path):
                img = Image.open(img_file).convert("RGB")
                img_name = img_file.name
            else:
                img = Image.open(img_file).convert("RGB")
                img_name = img_file.name

            st.image(img, use_container_width=True, caption=f"Image: {img_name}")

            # Analysis button with improved styling
            if st.button("🔍 Analyze Plant", key="img", type="primary", use_container_width=True):
                with st.spinner("🤖 AI is analyzing your plant..."):
                    try:
                        raw_class, readable_name, confidence, plant_type = vision_adapter.predict_with_readable_name(img)

                        # Results in a styled card
                        st.markdown(
                            """
                        <div class="result-card">
                            <h3>🔬 Analysis Results</h3>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Metrics in columns
                        metric_col1, metric_col2, metric_col3 = st.columns(3)

                        with metric_col1:
                            st.metric("🌱 Plant Type", plant_type)

                        with metric_col2:
                            st.metric("🦠 Condition", readable_name)

                        with metric_col3:
                            # Color-coded confidence
                            conf_class = "confidence-high" if confidence > 0.8 else "confidence-medium" if confidence > 0.5 else "confidence-low"
                            st.markdown(f'<p class="{conf_class}">📊 Confidence: {confidence:.1%}</p>', unsafe_allow_html=True)

                        # Health status with better styling
                        if vision_adapter.is_healthy(raw_class):
                            st.success("✅ Plant appears healthy!")
                            st.balloons()
                        else:
                            st.warning("⚠️ Disease detected - consider treatment")

                            # Treatment recommendations
                            with st.expander("💡 Treatment Recommendations"):
                                st.info("Consult with agricultural experts for proper treatment plans.")

                        # Technical details
                        with st.expander("🔧 Technical Details"):
                            st.json(
                                {
                                    "raw_prediction": raw_class,
                                    "confidence_score": float(confidence),
                                    "model_used": selected_models["vision"],
                                }
                            )

                    except Exception as e:
                        st.error(f"❌ Analysis failed: {e!s}")
        else:
            st.info("👆 Upload an image or select a sample to begin analysis")

# Audio Processing Tab
with tab2:
    st.subheader("🎤 Voice & Audio Analysis")
    st.info("💡 Ask questions about plant care or describe symptoms using voice or audio files")

    # Audio input methods
    audio_col1, audio_col2 = st.columns([1, 1])

    with audio_col1:
        st.markdown("### 🎙️ Live Recording")

        if "audio_buf" not in st.session_state:
            st.session_state.audio_buf = []

        def audio_frame_callback(frame: "AudioFrame") -> "AudioFrame":
            """Process audio frame from microphone input."""
            data = frame.to_ndarray()  # (samples, channels), int16
            mono = data.mean(axis=1).astype(np.float32) / 32768.0
            st.session_state.audio_buf.append(mono)
            return frame

        # WebRTC streamer with better styling
        st.markdown("**Click 'START' to begin recording:**")
        webrtc_streamer(
            key="mic",
            mode=WebRtcMode.SENDRECV,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={"audio": True, "video": False},
        )

        # Recording controls
        if st.button("🎯 Process Recording", key="mic_analyze", type="primary", use_container_width=True):
            if st.session_state.audio_buf:
                with st.spinner("🎧 Processing audio..."):
                    try:
                        audio_data = np.concatenate(st.session_state.audio_buf, axis=0)
                        sf.write("mic.wav", audio_data, 48000)
                        text = audio_adapter.transcribe("mic.wav")

                        st.markdown("### 📝 Transcription Results")
                        st.text_area("What you said:", text, height=100, disabled=True)

                        # Generate response if it's a question
                        if text.strip():
                            response = text_adapter.generate_response("general", text)
                            st.markdown("### 🤖 AI Response")
                            st.success(response)

                        st.session_state.audio_buf = []

                        # Clean up temp file
                        Path("mic.wav").unlink(missing_ok=True)

                    except Exception as e:
                        st.error(f"❌ Audio processing failed: {e!s}")
            else:
                st.warning("⚠️ No audio detected. Please record something first!")

    with audio_col2:
        st.markdown("### 📁 File Upload")

        audio_file = st.file_uploader("Upload audio file", ["wav", "mp3", "m4a"], help="Supported formats: WAV, MP3, M4A")

        if audio_file:
            st.audio(audio_file, format="audio/wav")

            if st.button("🎯 Process File", key="file_analyze", type="primary", use_container_width=True):
                with st.spinner("🎧 Processing uploaded audio..."):
                    try:
                        # Save uploaded file temporarily
                        tmp_path = Path("tmp_audio")
                        tmp_path.write_bytes(audio_file.read())

                        # Transcribe
                        text = audio_adapter.transcribe(str(tmp_path))

                        st.markdown("### 📝 Transcription Results")
                        st.text_area("Transcribed text:", text, height=100, disabled=True)

                        # Generate response if it's a question
                        if text.strip():
                            response = text_adapter.generate_response("general", text)
                            st.markdown("### 🤖 AI Response")
                            st.success(response)

                        # Clean up temp file
                        tmp_path.unlink(missing_ok=True)

                    except Exception as e:
                        st.error(f"❌ Audio processing failed: {e!s}")
        else:
            st.info("👆 Upload an audio file to begin processing")

# Text Q&A Tab
with tab3:
    st.subheader("💬 Plant Care Assistant")
    st.info("💡 Ask questions about plant diseases, treatments, or general plant care")

    # Chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Question input
    question_col1, question_col2 = st.columns([4, 1])

    # Sample questions (placed BEFORE the input to allow prefill without state mutation errors)
    st.markdown("### 🔍 Sample Questions")
    sample_questions = [
        "How to treat powdery mildew?",
        "What causes yellow leaves in plants?",
        "How to prevent fungal diseases?",
        "Best practices for plant watering?",
        "Signs of nutrient deficiency in plants",
    ]

    sample_cols = st.columns(len(sample_questions))
    for i, sample_q in enumerate(sample_questions):
        with sample_cols[i]:
            if st.button(f"💡 {sample_q}", key=f"sample_{i}", help="Click to use this question"):
                # Set preset value and rerun BEFORE input is instantiated
                st.session_state["preset_user_question"] = sample_q
                st.rerun()

    # Determine default value for the text input
    default_q = st.session_state.pop("preset_user_question", None)
    if default_q is None:
        # Handle clearing the input via flag on rerun
        if st.session_state.pop("clear_user_question", False):
            default_q = ""
        else:
            default_q = st.session_state.get("user_question", "")

    with question_col1:
        user_question = st.text_input(
            "Ask your question:",
            value=default_q,
            placeholder="e.g., 'How to treat powdery mildew?' or 'What causes leaf spots?'",
            key="user_question",
        )

    with question_col2:
        ask_button = st.button("🚀 Ask", key="qa", type="primary", use_container_width=True)

    # Process question
    if (ask_button and user_question.strip()) or (user_question and st.session_state.get("auto_submit", False)):
        with st.spinner("🤖 AI is thinking..."):
            try:
                response = text_adapter.generate_response("general", user_question)

                # Add to chat history
                st.session_state.chat_history.append({"question": user_question, "answer": response, "timestamp": "now"})

                # Clear input safely on next run
                st.session_state["clear_user_question"] = True
                st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to generate response: {e!s}")

    # Display chat history
    if st.session_state.chat_history:
        st.markdown("### 💬 Conversation History")

        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
            with st.expander(
                f"Q: {chat['question'][:50]}..." if len(chat["question"]) > 50 else f"Q: {chat['question']}",
                expanded=(i == 0),
            ):
                st.markdown(f"**❓ Question:** {chat['question']}")
                st.markdown(f"**🤖 Answer:** {chat['answer']}")

        # Clear history button
        if st.button("🗑️ Clear History", help="Clear conversation history"):
            st.session_state.chat_history = []
            st.rerun()

    # Sample questions moved above

# Training Tab
with tab4:
    st.subheader("📚 Training Runs & Reports")
    st.info("Select a training run to view its artifacts, metrics, and open TensorBoard.")

    # Base runs directory
    default_runs_dir = Path("runs")
    runs_dir_str = st.text_input("Runs directory", value=str(default_runs_dir), help="Directory where TrainingMonitor stores experiment runs")
    runs_dir = Path(runs_dir_str)

    # Discover runs: directories containing training_report.json
    def discover_runs(base: Path) -> list[Path]:
        if not base.exists():
            return []
        candidates = [p for p in base.iterdir() if p.is_dir() and (p / "training_report.json").exists()]
        # Sort by modification time (newest first)
        return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)

    runs = discover_runs(runs_dir)
    if not runs:
        st.warning("No training runs found yet. After running training with TrainingMonitor, artifacts will appear here.")
    else:
        run_names = [r.name for r in runs]
        selected_index = 0
        selected_run_name = st.selectbox("Select a run", run_names, index=selected_index)
        selected_run = runs[run_names.index(selected_run_name)]

        # Load report
        report_path = selected_run / "training_report.json"
        report = {}
        try:
            report = json.loads(report_path.read_text()) if report_path.exists() else {}
        except Exception as e:
            st.error(f"Failed to read training_report.json: {e!s}")

        # Paths to artifacts
        curves_path = selected_run / "training_curves.png"
        arch_path = selected_run / "model_architecture.png"
        html_report_path = selected_run / "comprehensive_report.html"
        text_summary_path = selected_run / "training_summary.txt"

        # Summary metrics
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Best Val Acc", f"{report.get('best_metrics', {}).get('Accuracy/Validation', 'N/A')}")
        with col_b:
            st.metric("Best Val Loss", f"{report.get('best_metrics', {}).get('Loss/Validation', 'N/A')}")
        with col_c:
            duration = report.get("total_duration", None)
            st.metric("Duration", f"{duration:.1f}s" if isinstance(duration, int | float) else "N/A")

        # Visualizations
        vis_col1, vis_col2 = st.columns(2)
        with vis_col1:
            st.markdown("### 📈 Training Curves")
            if curves_path.exists():
                st.image(str(curves_path), use_container_width=True)
            else:
                st.info("training_curves.png not found for this run")

        with vis_col2:
            st.markdown("### 🧠 Model Architecture")
            if arch_path.exists():
                st.image(str(arch_path), use_container_width=True)
            else:
                st.info("model_architecture.png not found for this run")

        # Downloads
        st.markdown("### 📄 Reports & Downloads")
        dl_cols = st.columns(4)
        with dl_cols[0]:
            if report_path.exists():
                st.download_button("Download JSON", data=report_path.read_bytes(), file_name=report_path.name, mime="application/json")
        with dl_cols[1]:
            if text_summary_path.exists():
                st.download_button(
                    "Download Summary",
                    data=text_summary_path.read_bytes(),
                    file_name=text_summary_path.name,
                    mime="text/plain",
                )
        with dl_cols[2]:
            if html_report_path.exists():
                st.download_button(
                    "Download HTML",
                    data=html_report_path.read_bytes(),
                    file_name=html_report_path.name,
                    mime="text/html",
                )
        with dl_cols[3]:
            if curves_path.exists():
                st.download_button("Download Curves", data=curves_path.read_bytes(), file_name=curves_path.name, mime="image/png")

        st.markdown("---")
        st.markdown("### 📊 TensorBoard")
        st.caption("Launch TensorBoard to view detailed logs, histograms, and confusion matrices.")
        tb_col1, tb_col2, tb_col3 = st.columns([2, 1, 2])
        with tb_col1:
            tb_port = st.number_input("Port", min_value=1024, max_value=65535, value=6006, step=1)
        with tb_col2:
            launch_tb = st.button("🚀 Launch TensorBoard", use_container_width=True)
        with tb_col3:
            st.markdown(f"[Open http://localhost:{6006}](http://localhost:{6006})")

        if launch_tb:
            # Add this function definition before the main code
            def launch_tensorboard(runs_dir, tb_port):
                """Launch TensorBoard with the specified log directory and port."""
                try:
                    # Using shlex.quote to properly escape paths and arguments
                    import shlex
                    import shutil

                    # Get full path to tensorboard executable
                    tensorboard_path = shutil.which("tensorboard")
                    if not tensorboard_path:
                        st.error("TensorBoard not found in PATH")
                        return False

                    cmd = [
                        tensorboard_path,
                        "--logdir",
                        shlex.quote(str(runs_dir)),
                        "--port",
                        str(int(tb_port)),
                        "--reload_interval",
                        "1",
                    ]

                    # Use full path and proper argument handling
                    subprocess.Popen(  # nosec B603: shell=False, inputs are sanitized
                        cmd,
                        shell=False,  # Safer than shell=True
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    st.success(f"TensorBoard launched at http://localhost:{int(tb_port)}")
                    st.markdown(f"[Open TensorBoard](http://localhost:{int(tb_port)})")
                    return True
                except FileNotFoundError:
                    st.error("TensorBoard not found. Install with: pip install tensorboard")
                    return False


# Model Management Tab (Merged from Model Switcher)
with tab5:
    st.subheader("🔧 Model Management & Configuration")
    st.info("Switch between different plant disease detection models, benchmark performance, and manage configurations.")

    # Initialize model manager
    try:
        from src.features.model_switching.model_manager import PlantGuardModelManager

        model_manager = PlantGuardModelManager(autoload_default=False)
    except ImportError:
        st.error("❌ Model Manager not available. Please check your installation.")
        st.stop()

    # Two-column layout for model management
    mgmt_col1, mgmt_col2 = st.columns([1, 1])

    with mgmt_col1:
        st.markdown("### 🤖 Model Selection & Switching")

        # Get available models
        try:
            models = model_manager.list_available_models()
            enabled_models = [m for m in models if m["enabled"]]

            if not enabled_models:
                st.warning("⚠️ No enabled models found")
            else:
                # Model selection dropdown
                # Preserve ordering from enabled_models and build parallel lists for labels and ids
                model_option_items = [(f"{m['name']} ({m['accuracy']:.1%})", m["id"]) for m in enabled_models]
                option_labels = [label for label, _ in model_option_items]
                option_ids = [mid for _, mid in model_option_items]

                current_model_info = model_manager.get_current_model_info()
                current_model_name = current_model_info.get("name", "None")

                # Determine default index by checking the is_current flag on the enabled_models list
                default_index = 0
                for i, model in enumerate(enabled_models):
                    if model.get("is_current"):
                        default_index = i
                        break

                selected_display = st.selectbox(
                    "Choose Model:",
                    options=option_labels,
                    index=default_index,
                    help="Select a model to switch to",
                    key="model_switcher_select",
                )

                selected_model_id = option_ids[option_labels.index(selected_display)]

                # Switch model button
                if st.button("🔄 Switch Model", type="primary", use_container_width=True, key="switch_model_btn"):
                    with st.spinner(f"Loading model: {selected_model_id}"):
                        if model_manager.switch_model(selected_model_id):
                            st.success(f"✅ Switched to: {selected_model_id}")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to switch to: {selected_model_id}")

                # Current model info
                st.markdown("---")
                st.markdown("### 📊 Current Model")

                if "error" not in current_model_info:
                    st.info(f"""
                    **Name:** {current_model_info["name"]}

                    **Type:** {current_model_info["type"]}

                    **Accuracy:** {current_model_info["accuracy"]:.1%}

                    **Classes:** {current_model_info["num_classes"]}

                    **Device:** {current_model_info["device"]}
                    """)
                else:
                    st.warning("No model loaded")

        except Exception as e:
            st.error(f"❌ Error loading models: {e}")

    with mgmt_col2:
        st.markdown("### 📊 Model Comparison & Benchmarking")

        # Show all models in a table
        try:
            if models:
                model_data = []
                for model in models:
                    status = "🟢 Current" if model["is_current"] else "⚪ Available" if model["enabled"] else "🔴 Disabled"
                    model_data.append(
                        {
                            "Model": model["name"],
                            "Type": model["type"],
                            "Accuracy": f"{model['accuracy']:.1%}" if model["accuracy"] > 0 else "Unknown",
                            "Status": status,
                        }
                    )

                st.dataframe(model_data, use_container_width=True)
            else:
                st.info("No models available for comparison")

        except Exception as e:
            st.error(f"❌ Error comparing models: {e}")

    # Model testing section
    st.markdown("---")
    st.markdown("### 🔍 Test Current Model")

    test_col1, test_col2 = st.columns([1, 1])

    with test_col1:
        # Image upload for testing
        test_image = st.file_uploader(
            "Upload plant image for testing",
            type=["jpg", "jpeg", "png"],
            help="Upload an image of a plant leaf to test the current model",
            key="test_image_uploader",
        )

    # Sample image selection for testing
    st.markdown("**Or choose a sample image:**")
    st.info("Sample image selection is disabled. Upload an image or provide images under `data/raw/` to test the model.")

    with test_col2:
        if test_image:
            # Display test image
            if isinstance(test_image, Path):
                img = Image.open(test_image).convert("RGB")
                img_name = test_image.name
            else:
                img = Image.open(test_image).convert("RGB")
                img_name = test_image.name

            st.image(img, caption=f"Testing: {img_name}", use_container_width=True)

            # Test button
            if st.button("🧪 Test Model", type="primary", use_container_width=True, key="test_model_btn"):
                if "error" not in current_model_info:
                    with st.spinner("Analyzing image..."):
                        try:
                            result = model_manager.get_readable_prediction(img)

                            # Display results
                            st.markdown("### 📋 Test Results")

                            col_a, col_b = st.columns(2)

                            with col_a:
                                st.metric("🌿 Plant Type", result["plant_type"])
                                st.metric("🦠 Disease", result["disease"])

                            with col_b:
                                st.metric("📊 Confidence", result["confidence_percentage"])
                                health_status = "Healthy ✅" if result["is_healthy"] else "Diseased ⚠️"
                                st.metric("💚 Health Status", health_status)

                            # Additional info
                            st.info(f"💡 **Recommendation:** {result['recommendation']}")

                            # Raw prediction details
                            with st.expander("🔧 Technical Details"):
                                st.json(
                                    {
                                        "raw_prediction": result["raw_prediction"],
                                        "confidence_score": result["confidence"],
                                        "model_info": result["model_info"],
                                    }
                                )

                        except Exception as e:
                            st.error(f"❌ Testing failed: {e}")
                else:
                    st.error("❌ No model loaded for testing")
        else:
            st.info("👆 Upload an image or select a sample to test the current model")

    # Configuration management
    st.markdown("---")
    st.markdown("### ⚙️ Configuration Management")

    config_col1, config_col2 = st.columns([1, 1])

    with config_col1:
        st.markdown("**Current Configuration File:** `config/models.json`")

        if st.button("📝 View Config", help="Display current model configuration"):
            try:
                with open("config/models.json") as f:
                    config_content = f.read()
                st.json(json.loads(config_content))
            except Exception as e:
                st.error(f"❌ Error reading config: {e}")

        if st.button("🔄 Reload Config", help="Reload model configuration from file"):
            try:
                model_manager.load_model_configs()
                st.success("✅ Configuration reloaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error reloading config: {e}")

    with config_col2:
        st.markdown("**Configuration Options:**")
        st.markdown("""
        You can edit the configuration file to:
        - Add new models
        - Change model settings
        - Enable/disable models
        - Set confidence thresholds
        - Configure device preferences
        """)

        if st.button("📁 Open Config Folder", help="View configuration folder information"):
            config_dir = Path("config")
            if config_dir.exists():
                st.success("✅ Configuration folder found!")
                st.info(f"**Configuration Directory:** `{config_dir.absolute()}`")

                # Show folder contents
                st.markdown("**📁 Folder Contents:**")
                try:
                    config_files = list(config_dir.glob("*.json"))
                    if config_files:
                        for config_file in config_files:
                            st.markdown(f"- `{config_file.name}`")
                    else:
                        st.markdown("- No JSON configuration files found")
                except Exception as e:
                    st.warning(f"Could not list folder contents: {e}")

                # Platform-specific instructions
                st.markdown("**💡 To open the folder manually:**")
                if platform.system() == "Windows":
                    st.markdown("- Press `Win + R`, type `explorer` and the path above, then press Enter")
                elif platform.system() == "Darwin":  # macOS
                    st.markdown("- Press `Cmd + Shift + G` in Finder, paste the path above, then press Enter")
                else:  # Linux
                    st.markdown("- Use your file manager to navigate to the path above")

            else:
                st.error("❌ Configuration folder not found")
                st.info("The `config/` directory should be created automatically when needed")
