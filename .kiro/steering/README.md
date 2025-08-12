
---
inclusion: always
---

# PlantGuard Development Guidelines

## Core Architecture Constraints

**CRITICAL: All ML inference must be local-only**
- ❌ No external ML APIs (OpenAI, Replicate, cloud vision services)
- ❌ No user data sent to external services
- ❌ No internet-dependent inference
- ✅ All processing must work offline after initial model downloads
- ✅ Graceful degradation when components fail

## Required Tech Stack & Model Locations

**Vision**: ResNet50 fine-tuned on PlantVillage → `data/models/vision_resnet50.pt`
**Audio**: Whisper-tiny (local) + streamlit-webrtc → offline transcription only
**Text**: DistilBERT + fusion layer → `data/models/text_qa_model/`
**UI**: Streamlit with `@st.cache_resource` for model loading

## Code Quality Standards

**Type Annotations** (Mandatory):
```python
def predict(self, image: PIL.Image.Image) -> tuple[str, float]:
    """Always include complete type hints"""
```

**Error Handling** (Required pattern):
```python
try:
    result = adapter.process(input_data)
except (FileNotFoundError, torch.serialization.pickle.UnpicklingError) as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()  # Never crash UI
```

**Code Style Rules**:
- Line length: 100 characters maximum
- Use `logger.info()` instead of `print()` in production code
- Use `pathlib.Path` for all file operations
- Clean up temp files immediately: `tempfile.NamedTemporaryFile(delete=True)`
- Import order: First-party (`src`, `plantguard`) before third-party (`torch`, `streamlit`)

## Required Core Interfaces

```python
# src/core/vision.py
class VisionAdapter:
    def predict(self, image: PIL.Image.Image) -> tuple[str, float]
    def load_checkpoint(self, path: str) -> None

# src/core/audio.py
class AudioAdapter:
    def transcribe(self, audio_file) -> str  # MUST be offline (Whisper-tiny)
    def predict_disease(self, audio_features) -> tuple[str, float]

# src/core/nlp.py
class TextAdapter:
    def extract_features(self, text: str) -> torch.Tensor
    def prepare_input(self, text: str) -> ModelInput

class ChatModel:
    def predict(self, text_inputs: str, vision_feat=None, audio_feat=None) -> str
```

## Streamlit Implementation Patterns

**Model Caching** (Required):
```python
@st.cache_resource
def load_models():
    """Load all models once and cache them"""
    return VisionAdapter(), AudioAdapter(), TextAdapter()
```

**Input Validation**:
- Images: Max 200MB, formats `["jpg","jpeg","png"]`
- Audio: 1-60 seconds, formats `["wav","mp3"]`
- Text: Max 1000 characters for chat input
- Always use `st.session_state` for conversation history

**Error Handling**: Never crash UI - return fallback responses on adapter failures

## Project Structure

```
src/core/vision.py      # VisionAdapter - ResNet50 plant disease detection
src/core/audio.py       # AudioAdapter - Whisper + disease classification
src/core/nlp.py         # TextAdapter + ChatModel - DistilBERT + fusion
src/ui/app_streamlit.py # Main Streamlit UI with multimodal inputs
data/models/            # Model checkpoints (vision_resnet50.pt, etc.)
data/knowledge_base/    # Plant disease information
```

## Privacy & Security Requirements

- Use `tempfile` for temporary storage, clean up immediately
- Delete temp files (`tmp_audio`, `mic.wav`) after processing
- Never persist user data beyond session scope
- No PII storage or external data transmission

## Documentation Updates

Always update `README.md` after generating or modifying code to reflect current functionality and usage patterns.
