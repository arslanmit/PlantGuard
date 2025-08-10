from typing import Any

import numpy as np
import soundfile as sf
import streamlit as st
from PIL import Image
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from src.core.audio import transcribe_and_classify
from src.core.nlp import answer
from src.core.vision import predict_image

st.set_page_config(page_title="PlantGuard", page_icon="🌿")
st.title("🌿 PlantGuard — Streamlit")
st.caption("Image + Voice + Text | Early leaf disease detection (PoC)")

tab1, tab2, tab3 = st.tabs(["Leaf Image", "Voice", "Text Q&A"])

# Leaf Image
with tab1:
    img_file = st.file_uploader("Upload a leaf photo", ["png", "jpg", "jpeg"])
    if img_file:
        img = Image.open(img_file).convert("RGB")
        st.image(img, use_column_width=True, caption="Uploaded image")
        if st.button("Analyze", key="img"):
            probs = predict_image(img)
            st.subheader("Probabilities")
            st.json(probs)

# Voice (Mic + Upload)
with tab2:
    st.write("🎙️ Record via microphone or upload an audio file")

    if "audio_buf" not in st.session_state:
        st.session_state.audio_buf = []

    def audio_frame_callback(frame: Any) -> Any:
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
                text, cls = transcribe_and_classify("mic.wav")
                st.text_area("Transcription", text, height=150)
                st.success(f"Predicted (mic): {cls}")
                st.session_state.audio_buf = []
            else:
                st.warning("Speak into the mic and allow permissions first.")

    with col2:
        aud = st.file_uploader("or upload audio (wav/mp3/m4a)", ["wav", "mp3", "m4a"])
        if aud and st.button("Analyze file"):
            with open("tmp_audio", "wb") as f:
                f.write(aud.read())
            text, cls = transcribe_and_classify("tmp_audio")
            st.text_area("Transcription", text, height=150)
            st.success(f"Predicted (file): {cls}")

# Text Q&A
with tab3:
    q = st.text_input("Ask a question (e.g., 'How to treat powdery mildew?')")
    if q and st.button("Ask", key="qa"):
        st.write(answer(q))

st.divider()
st.markdown(
    "> This tool provides agronomic advice; it is not a professional diagnosis. Probabilities are shown as confidence indicators."
)
