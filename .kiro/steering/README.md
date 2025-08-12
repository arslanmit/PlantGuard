---
inclusion: always
---

# PlantGuard Development Guidelines

## Core Architecture Principles

**Multimodal Pipeline**: `User Input → [Vision/Audio/Text Adapter] → Fusion Model → Response`

**Critical Constraint**: All ML inference must be **local-only**
- ❌ No external APIs (OpenAI, Replicate, cloud vision services)
- ❌ No user data sent to external services
- ✅ All processing must work offline after initial model downloads
- ✅ Graceful degradation when adapters fail

## Required Tech Stack

**Vision**: ResNet50 (ImageNet pretrained) → fine-tuned on PlantVillage
**Audio**: Whisper-tiny (local) + CNN-LSTM for disease classification
**Text**: DistilBERT fine-tuned on plant-care FAQ dataset
**UI**: Streamlit with streamlit-webrtc for real-time capture

## Code Standards

**Type Annotations**: Mandatory for all functions
```python
def predict(self, image: PIL.Image.Image) -> tuple[str, float]:
```

**Error Handling**: Always provide fallbacks
```python
try:
    result = adapter.process(input_data)
except Exception as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()  # Never crash UI
```

**Model Caching**: Required for Streamlit performance
```python
@st.cache_resource
def load_models():
    return VisionAdapter(), AudioAdapter(), TextAdapter()
```

## File Operations

- Use `pathlib.Path` for all file operations
- Use `tempfile` for temporary storage, clean up immediately
- Delete temp files (`tmp_audio`, `mic.wav`) after processing
- Never persist user data beyond session scope

## Code Quality Requirements

- Line length: 100 characters maximum
- Double quotes for strings
- Import order: First-party (`src`) before third-party (`torch`, `streamlit`)
- Use `logger.info()` instead of `print()` in production
- Specify exception types: `except FileNotFoundError:` not `except:`

## Documentation Updates

- Always update main `README.md` with new features or changes
- Do not create summary documents (like `MAKEFILE_IMPROVEMENTS.md`) for major updates
- Use TensorBoard for training metrics: `./runs/experiment_{timestamp}`

## Required Interfaces

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
    def extract_features(self, text: str) -> torch.Tensor

class ChatModel:
    def predict(self, text_inputs: str, vision_feat=None, audio_feat=None) -> str
```

## Input Validation

- Images: Max 200MB, formats `["jpg","jpeg","png"]`
- Audio: 1-60 seconds, formats `["wav","mp3"]`
- Text: Max 1000 characters for chat input
- Use `st.session_state` for conversation history
