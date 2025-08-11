---
inclusion: always
---

# PlantGuard Technical Guidelines

## Core Architecture

**Multimodal Pipeline**: `User Input → [Vision/Audio/Text Adapter] → Fusion Model → Response`

**Non-Negotiable Tech Stack**:
- **Vision**: ResNet50 (ImageNet-1K pretrained) fine-tuned on PlantVillage
- **Speech**: MFCC → CNN-LSTM (PyTorch) for disease classification
- **ASR**: Whisper-tiny (local only) for transcription
- **Text QA**: DistilBERT fine-tuned on plant-care FAQ
- **Fusion**: ResNet50 penultimate (2048) ⊕ DistilBERT [CLS] (768) → MLP
- **UI**: Streamlit + streamlit-webrtc on Google Colab
- **Tracking**: TensorBoard (required)

## Critical Constraints

- **NO cloud APIs** - All processing must be local-only
- **Privacy-first** - Use `tempfile`, clean up immediately after inference
- **Offline-only** - Local Whisper, no external services
- **Graceful degradation** - Handle adapter failures without crashing

## Required Interfaces

```python
# src/core/vision.py
class VisionAdapter:
    def predict(self, image: PIL.Image) -> Union[Tensor, Tuple[str, float]]
    def load_checkpoint(self, path: str) -> None

# src/core/audio.py
class AudioAdapter:
    def transcribe(self, audio_file) -> str  # Must be offline

# src/core/nlp.py
class TextAdapter:
    def prepare_input(self, text: str) -> ModelInput

class ChatModel:
    def predict(self, text_inputs: str, vision_feat=None, audio_feat=None) -> str
```

## Streamlit Patterns

**Model Loading** (Required):
```python
@st.cache_resource
def load_models():
    return VisionAdapter(), AudioAdapter(), TextAdapter()
```

**Input Validation**:
- Images: Max 200MB, types `["jpg","jpeg","png"]`
- Audio: 1-60 seconds, types `["wav","mp3"]`
- Use `st.session_state` for conversation history

## Training Standards

**TensorBoard Logging** (Required):
```python
writer.add_scalar("Loss/train", loss, step)
writer.add_scalar("Loss/val", val_loss, epoch)
writer.add_scalar("Accuracy/val", val_acc, epoch)
```
- Log directory: `./runs/` with unique subdirectories

**Data Pipeline**:
- Convert all modalities to PyTorch tensors
- Train adapters independently with fixed random seeds
- Use `torchvision.datasets`, `librosa`, `datasets` libraries

## Code Standards

**Error Handling Pattern**:
```python
try:
    result = adapter.process(input_data)
except Exception as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()
```

**Required Patterns**:
- Type hints for all adapter methods
- Docstrings with input/output specifications
- Cache heavy models with `@lru_cache` or module-level singletons
- Delete temp audio files after processing

## File Structure

```
src/core/vision.py      # VisionAdapter implementation
src/core/audio.py       # AudioAdapter implementation
src/core/nlp.py         # TextAdapter + ChatModel fusion
src/ui/app_streamlit.py # Main Streamlit application
```

## Model Checkpoints

- Vision: `data/vision_resnet50.pt` + `data/classes.json`
- Speech: `data/speech_cnn_lstm.pt`
- Text QA: `data/text_qa_model/`
- Fusion: `data/fusion_mlp.pt`

## Privacy & Security

- Process audio locally, delete temp files (`tmp_audio`, `mic.wav`) after inference
- No PII storage, GDPR compliance notice in README
- Use Cloudflare Quick Tunnel for HTTPS in Colab

## Development Checklist

1. Test each adapter independently with sample data
2. Implement fallback functions for critical paths
3. Use `tempfile` for temporary storage, clean up immediately
4. Log all training metrics to TensorBoard
5. Validate inputs (image size, audio duration, text length)
6. Never persist user data beyond session scope
