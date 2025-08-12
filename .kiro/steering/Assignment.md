---
inclusion: always
---

# PlantGuard Project Guidelines

## Project Overview

PlantGuard is a multimodal plant disease detection system that combines computer vision, speech recognition, and natural language processing. The system operates as: **Image → Vision Model → Disease Detection → User Query (Voice/Text) → ASR → NLP Response → Answer**.

## Core Constraints

**CRITICAL: All ML inference must be local-only**

- ❌ No external ML APIs (OpenAI, Replicate, cloud vision services)
- ❌ No user data sent to external services
- ❌ No internet-dependent inference
- ✅ All processing must work offline after initial model downloads
- ✅ Graceful degradation when components fail

## Required Technology Stack

### Vision Processing

- **ResNet-50** fine-tuned on PlantVillage dataset
- Input: PIL.Image → Output: disease classification + confidence
- Model checkpoint: `data/models/vision_resnet50.pt`

### Audio Processing

- **Whisper-tiny** for speech-to-text (local only)
- **streamlit-webrtc** for browser audio capture
- **librosa** for audio preprocessing
- Input: audio files (wav/mp3) → Output: transcription

### Text Processing

- **DistilBERT** fine-tuned on plant-care FAQ dataset
- **Transformers** library for model loading
- Fusion layer: Vision features + Text embeddings → Response

### UI Framework

- **Streamlit** with real-time audio/video capabilities
- **pyngrok** for external access in Colab environments

## Required Code Interfaces

```python
# src/core/vision.py
class VisionAdapter:
    def predict(self, image: PIL.Image.Image) -> tuple[str, float]
    def load_checkpoint(self, path: str) -> None

# src/core/audio.py  
class AudioAdapter:
    def transcribe(self, audio_file) -> str  # MUST be offline
    def predict_disease(self, audio_features) -> tuple[str, float]

# src/core/nlp.py
class TextAdapter:
    def prepare_input(self, text: str) -> ModelInput
    def extract_features(self, text: str) -> torch.Tensor

class ChatModel:
    def predict(self, text_inputs: str, vision_feat=None, audio_feat=None) -> str
```

## Streamlit Implementation Patterns

**Model Caching (Required)**:

```python
@st.cache_resource
def load_models():
    return VisionAdapter(), AudioAdapter(), TextAdapter()
```

**Input Validation**:

- Images: Max 200MB, formats `["jpg","jpeg","png"]`
- Audio: 1-60 seconds, formats `["wav","mp3"]`
- Text: Max 1000 characters
- Use `st.session_state` for conversation history

## Project Structure

```
src/core/vision.py      # VisionAdapter - ResNet50 plant disease detection
src/core/audio.py       # AudioAdapter - Whisper + disease classification  
src/core/nlp.py         # TextAdapter + ChatModel - DistilBERT + fusion
src/ui/app_streamlit.py # Main Streamlit UI
data/models/            # Model checkpoints
data/knowledge_base/    # Plant disease information
```

## Error Handling Pattern

```python
try:
    result = adapter.process(input_data)
except Exception as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()  # Never crash the UI
```

## Training & Monitoring

- **TensorBoard** for training metrics: `./runs/experiment_{timestamp}`
- **PlantVillage dataset** for vision model training
- Log all training metrics: loss, accuracy, validation scores
- Use `tempfile` for temporary storage, clean up immediately

## Privacy & Security

- No PII storage or external data transmission
- Delete temp files (`tmp_audio`, `mic.wav`) immediately after processing
- Never persist user data beyond session scope
- Use `pathlib.Path` for file operations

## Development Environment

- **Google Colab** with GPU acceleration
- **Jupyter notebooks** for interactive development
- **pyngrok** for external access during development
- All dependencies installable via `pip install -r requirements.txt`
