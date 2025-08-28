---
inclusion: always
---

# PlantGuard Technical Guidelines

## Architecture Overview

PlantGuard is a **multimodal plant disease detection system** with strict offline requirements:
- **Pipeline**: `User Input → [Vision/Audio/Text Adapter] → Fusion Model → Response`
- **Core Principle**: All ML inference must be local-only (no cloud APIs)
- **Target Environment**: Google Colab with Streamlit UI

## Required Tech Stack

When implementing or modifying PlantGuard components, use these exact technologies:

**Vision Processing**:
- ResNet50 (ImageNet-1K pretrained) fine-tuned on PlantVillage dataset
- Input: PIL.Image, Output: disease classification + confidence

**Audio Processing**:
- MFCC feature extraction → CNN-LSTM (PyTorch) for disease classification
- Whisper-tiny for speech-to-text (local only, never cloud)
- Input: audio files (wav/mp3), Output: transcription + disease prediction

**Text Processing**:
- DistilBERT fine-tuned on plant-care FAQ dataset
- Fusion layer: ResNet50 features (2048) + DistilBERT [CLS] (768) → MLP

**UI & Deployment**:
- Streamlit with streamlit-webrtc for real-time audio/video
- TensorBoard for training metrics visualization

## Critical Constraints

**NEVER violate these rules when working on PlantGuard**:
- ❌ No external APIs (OpenAI, Replicate, cloud vision services)
- ❌ No user data sent to external services
- ❌ No internet-dependent inference
- ✅ All processing must work offline
- ✅ Use `tempfile` for temporary storage, clean up immediately
- ✅ Graceful degradation when adapters fail

## Required Code Interfaces

When implementing or modifying core components, follow these exact interfaces:

```python
# src/core/vision.py
class VisionAdapter:
    def predict(self, image: PIL.Image) -> Union[Tensor, Tuple[str, float]]
    def load_checkpoint(self, path: str) -> None

# src/core/audio.py
class AudioAdapter:
    def transcribe(self, audio_file) -> str  # MUST be offline (Whisper-tiny)
    def predict_disease(self, audio_features) -> Tuple[str, float]

# src/core/nlp.py
class TextAdapter:
    def prepare_input(self, text: str) -> ModelInput
    def extract_features(self, text: str) -> Tensor  # DistilBERT [CLS]

class ChatModel:
    def predict(self, text_inputs: str, vision_feat=None, audio_feat=None) -> str
```

## Streamlit Implementation Patterns

**Model Caching** (Required for performance):
```python
@st.cache_resource
def load_models():
    """Load all models once and cache them"""
    return VisionAdapter(), AudioAdapter(), TextAdapter()
```

**Input Validation Rules**:
- Images: Max 200MB, formats `["jpg","jpeg","png"]`
- Audio: 1-60 seconds, formats `["wav","mp3"]`
- Text: Max 1000 characters for chat input
- Always use `st.session_state` for conversation history

## Code Quality Standards

**Error Handling** (Required pattern):
```python
try:
    result = adapter.process(input_data)
except Exception as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()  # Never crash the UI
```

**Code Requirements**:
- Type hints for all public methods
- Docstrings with input/output specifications
- Use `@lru_cache` or module-level singletons for heavy models
- Always clean up temporary files (especially audio)

**Privacy & Security**:
- Use `tempfile` for temporary storage
- Delete temp files (`tmp_audio`, `mic.wav`) immediately after processing
- Never persist user data beyond session scope
- No PII storage or external data transmission

## Training & Logging Standards

**TensorBoard Integration** (Required):
```python
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter(f'./runs/experiment_{timestamp}')
writer.add_scalar("Loss/train", loss, step)
writer.add_scalar("Loss/val", val_loss, epoch)
writer.add_scalar("Accuracy/val", val_acc, epoch)
```

**Data Pipeline Rules**:
- Convert all modalities to PyTorch tensors
- Train adapters independently with fixed random seeds
- Use standard libraries: `torchvision.datasets`, `librosa`, `datasets`
- Log directory: `./runs/` with unique timestamped subdirectories

## Project Structure

**Core Implementation Files**:
```
src/core/vision.py      # VisionAdapter - ResNet50 plant disease detection
src/core/audio.py       # AudioAdapter - Whisper + CNN-LSTM disease classification
src/core/nlp.py         # TextAdapter + ChatModel - DistilBERT + fusion layer
src/ui/app_streamlit.py # Main Streamlit UI with multimodal inputs
```

**Model Checkpoint Locations**:
- Vision: `data/vision_resnet50.pt` + `data/classes.json`
- Speech: `data/speech_cnn_lstm.pt`
- Text QA: `data/text_qa_model/` (DistilBERT checkpoint)
- Fusion: `data/fusion_mlp.pt`

## Implementation Guidelines

**When implementing new features**:
1. Test each adapter independently with sample data first
2. Implement fallback functions for all critical paths
3. Validate all inputs (image size, audio duration, text length)
4. Log training metrics to TensorBoard with unique run names
5. Use `tempfile` for temporary storage, clean up immediately
6. Never persist user data beyond the current session

**When debugging issues**:
- Check model checkpoint paths and file existence
- Verify input formats match expected types (PIL.Image, audio arrays, strings)
- Ensure graceful degradation when models fail to load
- Test offline functionality (disconnect internet during testing)

**Deployment Notes**:
- Use Cloudflare Quick Tunnel for HTTPS in Google Colab
- Include GDPR compliance notice in README for EU users
- Test memory usage with large inputs (200MB images, 60s audio)
