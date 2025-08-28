
---
inclusion: always
---

# PlantGuard macOS ML/DL Development Standards

## pyproject.toml Configuration

When updating `pyproject.toml` for macOS machine learning and deep learning projects:

### Core ML Dependencies
```toml
[project.dependencies]
torch = ">=2.0.0"  # Use MPS backend for Apple Silicon GPU acceleration
torchvision = ">=0.15.0"
transformers = ">=4.20.0"  # DistilBERT and model loading
streamlit = ">=1.28.0"
streamlit-webrtc = ">=0.45.0"  # Real-time audio/video capture
librosa = ">=0.10.0"  # Audio processing and MFCC extraction
openai-whisper = ">=20230314"  # Local speech-to-text (offline only)
Pillow = ">=9.0.0"  # Image processing
numpy = ">=1.24.0"
pandas = ">=2.0.0"
```

### Development Tools
```toml
[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",  # Linting and formatting
    "mypy>=1.5.0",  # Type checking (strict mode)
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",  # Coverage reporting
    "tensorboard>=2.13.0",  # Training visualization
]

[tool.ruff]
line-length = 200
target-version = "py311"

[tool.mypy]
strict = true
python_version = "3.11"
```

### macOS-Specific Considerations
- Use PyTorch MPS backend: `torch.backends.mps.is_available()`
- Install dependencies via Homebrew when needed: `brew install portaudio` for audio processing
- Configure environment variables for Apple Silicon optimization

## Architecture Constraints

**CRITICAL**: All ML inference must be local-only
- [TODO] No external APIs (OpenAI Vision, Replicate, cloud services)
- [TODO] No user data transmission to external services
- [DONE] Offline capability after initial model downloads
- [DONE] Graceful degradation when components fail
- [DONE] Use Apple Silicon MPS acceleration when available

## Code Quality Standards

**Type Annotations** (Mandatory):
```python
def predict(self, image: PIL.Image.Image) -> tuple[str, float]:
    """Process image and return (disease_name, confidence)."""
```

**Error Handling Pattern**:
```python
try:
    result = adapter.process(input_data)
except Exception as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()  # Never crash UI
```

**Streamlit Model Caching**:
```python
@st.cache_resource
def load_models():
    return VisionAdapter(), AudioAdapter(), TextAdapter()
```

## Required Interfaces

**Core Adapters**:
- `VisionAdapter.predict(image: PIL.Image.Image) -> tuple[str, float]`
- `AudioAdapter.transcribe(audio_file) -> str` (offline Whisper only)
- `TextAdapter.extract_features(text: str) -> torch.Tensor`
- `ChatModel.predict(text: str, vision_feat=None, audio_feat=None) -> str`

## File Operations

- Use `pathlib.Path` for all file operations
- Use `tempfile` for temporary storage, clean up immediately
- Delete temp files (`tmp_audio`, `mic.wav`) after processing
- Never persist user data beyond session scope
- Model checkpoints in `data/models/` directory

## Input Validation

- Images: Max 200MB, formats `["jpg", "jpeg", "png"]`
- Audio: 1-60 seconds, formats `["wav", "mp3"]`
- Text: Max 1000 characters for chat input
- Use `st.session_state` for conversation history

## Training Standards

- Use TensorBoard: `./runs/experiment_{timestamp}`
- Log metrics: loss, accuracy, validation scores
- Fixed random seeds for reproducibility
- Leverage MPS backend for Apple Silicon acceleration
- Use `torch.compile()` for performance optimization on macOS

## Code Style

- Line length: 100 characters maximum
- Double quotes for strings
- Import order: First-party (`src`) before third-party
- Use `logger.info()` instead of `print()` in production
- Specific exception handling: `except FileNotFoundError:` not `except:`
- Use `pathlib.Path` instead of `os.path` for file operations 