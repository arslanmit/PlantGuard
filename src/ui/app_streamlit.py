"""PlantGuard Streamlit application for multimodal plant disease detection."""

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

# Import the actual classes and methods that exist
from src.core.audio import AudioAdapter
from src.core.nlp import TextAdapter
from src.core.vision import VisionAdapter

st.set_page_config(page_title="PlantGuard", page_icon="🌿")
st.title("🌿 PlantGuard — Streamlit")
st.caption("Image + Voice + Text | Early leaf disease detection (PoC)")


# Initialize adapters (cached for performance)
@st.cache_resource
def load_adapters() -> tuple[VisionAdapter, AudioAdapter, TextAdapter]:
    """Load and cache the ML adapters."""
    # Load vision model with checkpoint
    vision_model_path = "data/models/vision_resnet50.pt"
    vision = VisionAdapter(model_path=vision_model_path)

    # Load class mapping
    classes_path = "data/knowledge_base/plantvillage_classes.json"
    if Path(classes_path).exists():
        vision.load_class_mapping(classes_path)

    audio = AudioAdapter()
    text = TextAdapter()
    return vision, audio, text


vision_adapter, audio_adapter, text_adapter = load_adapters()

tab1, tab2, tab3 = st.tabs(["Leaf Image", "Voice", "Text Q&A"])

# Leaf Image
with tab1:
    img_file = st.file_uploader("Upload a leaf photo", ["png", "jpg", "jpeg"])
    if img_file:
        img = Image.open(img_file).convert("RGB")
        st.image(img, use_container_width=True, caption="Uploaded image")
        if st.button("Analyze", key="img"):
            raw_class, readable_name, confidence, plant_type = (
                vision_adapter.predict_with_readable_name(img)
            )
            st.subheader("Analysis Results")
            st.success(f"Plant Type: {plant_type}")
            st.success(f"Condition: {readable_name}")
            st.info(f"Confidence: {confidence:.2%}")

            # Show health status
            if vision_adapter.is_healthy(raw_class):
                st.success("✅ Plant appears healthy!")
            else:
                st.warning("⚠️ Disease detected - consider treatment")

# Voice (Mic + Upload)
with tab2:
    st.write("🎙️ Record via microphone or upload an audio file")

    if "audio_buf" not in st.session_state:
        st.session_state.audio_buf = []

    def audio_frame_callback(frame: "AudioFrame") -> "AudioFrame":
        """Process audio frame from microphone input."""
        data = frame.to_ndarray()  # (samples, channels), int16
        mono = data.mean(axis=1).astype(np.float32) / 32768.0
        st.session_state.audio_buf.append(mono)
        return frame

    webrtc_streamer(
        key="mic",
        mode=WebRtcMode.SENDRECV,
        audio_frame_callback=audio_frame_callback,
        media_stream_constraints={"audio": True, "video": False},
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Analyze microphone"):
            if st.session_state.audio_buf:
                audio = np.concatenate(st.session_state.audio_buf, axis=0)
                sf.write("mic.wav", audio, 48000)
                text = audio_adapter.transcribe("mic.wav")
                st.text_area("Transcription", text, height=150)
                st.success("Audio transcribed successfully")
                st.session_state.audio_buf = []
            else:
                st.warning("Speak into the mic and allow permissions first.")

    with col2:
        aud = st.file_uploader("or upload audio (wav/mp3/m4a)", ["wav", "mp3", "m4a"])
        if aud and st.button("Analyze file"):
            tmp_path = Path("tmp_audio")
            tmp_path.write_bytes(aud.read())
            text = audio_adapter.transcribe(str(tmp_path))
            st.text_area("Transcription", text, height=150)
            st.success("Audio file transcribed successfully")

# Text Q&A
with tab3:
    q = st.text_input("Ask a question (e.g., 'How to treat powdery mildew?')")
    if q and st.button("Ask", key="qa"):
        response = text_adapter.generate_response("general", q)
        st.write(response)

st.divider()
st.markdown(
    "> This tool provides agronomic advice; it is not a professional diagnosis. "
    "Probabilities are shown as confidence indicators."
)
