---
inclusion: always
---

# PlantGuard Development Guide

## Core Architecture

**Pipeline**: `User Input → [Vision/Audio/Text Adapter] → Fusion Model → Response`

**CRITICAL CONSTRAINT**: All ML inference must be **local-only**
- [TODO] No external APIs (OpenAI, Replicate, cloud ML services)
- [TODO] No user data sent to external services
- [TODO] No internet-dependent inference
- [DONE] Offline capability after model downloads
- [DONE] Graceful degradation when adapters fail

## Required Tech Stack

- **Vision**: ResNet50 fine-tuned on PlantVillage dataset
- **Audio**: Whisper-tiny (local) + CNN-LSTM for disease classification
- **Text**: DistilBERT fine-tuned on plant-care FAQ dataset
- **UI**: Streamlit with streamlit-webrtc for real-time capture
- **Training**: TensorBoard logging to `./runs/experiment_{timestamp}`

## Mandatory Code Interfaces

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

## Required Code Patterns

**Error Handling** (Never crash UI):
```python
try:
    result = adapter.process(input_data)
except Exception as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()
```

**Streamlit Caching** (Required for performance):
```python
@st.cache_resource
def load_models():
    return VisionAdapter(), AudioAdapter(), TextAdapter()
```

**Input Validation** (Always validate):
- Images: Max 200MB, formats `["jpg", "jpeg", "png"]`
- Audio: 1-60 seconds, formats `["wav", "mp3"]`
- Text: Max 1000 characters for chat input

## File Operations & Privacy

**File Handling Rules**:
- Use `pathlib.Path` for all file operations
- Use `tempfile` for temporary storage, clean up immediately
- Delete temp files (`tmp_audio`, `mic.wav`) after processing
- Never persist user data beyond session scope

**Directory Structure**:
- Model checkpoints: `data/models/`
- Training logs: `./runs/experiment_{timestamp}`
- Use `tempfile.mkdtemp()` for temporary files

## Code Quality Standards

**Required Patterns**:
- Type annotations for all public methods
- Line length: 100 characters maximum
- Double quotes for strings
- Import order: First-party (`src`) before third-party
- Use `logger.info()` instead of `print()` in production
- Specific exception handling: `except FileNotFoundError:` not `except:`

**macOS Optimization**:
```python
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
```

## Implementation Rules

**When implementing features**:
1. Test each adapter independently first
2. Implement fallback functions for all critical paths
3. Validate all inputs before processing
4. Use `@lru_cache` for heavy model loading
5. Clean up temporary files immediately
6. Never persist user data beyond current session

**Training Requirements**:
- Fixed random seeds for reproducibility
- Log metrics: loss, accuracy, validation scores
- Use `torch.compile()` for performance optimization

**MCP Integration**:
- [TODO] Never use external APIs for core PlantGuard functionality
- [DONE] Use MCP for: GitHub operations, documentation lookup, file management
- Always test MCP tools before integration

## Project Structure

```
src/core/vision.py      # VisionAdapter - ResNet50 disease detection
src/core/audio.py       # AudioAdapter - Whisper + CNN-LSTM classification
src/core/nlp.py         # TextAdapter + ChatModel - DistilBERT + fusion
src/ui/app_streamlit.py # Main Streamlit UI with multimodal inputs
data/models/            # Model checkpoints and class mappings
config/models.json      # Model configuration registry
```