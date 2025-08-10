# 🌿 PlantGuard — Streamlit Multimodal MVP

**Early leaf disease detection using Image + Voice + Text modalities**

PlantGuard is a proof-of-concept multimodal AI system for plant disease detection. It combines computer vision (ResNet18), automatic speech recognition (Whisper-tiny), and natural language processing (DistilBERT) in a single Streamlit interface.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/arslanmit/leaf-doctor-ai-bot/blob/main/notebooks/PlantGuard.ipynb)

## Features

- **🖼️ Leaf Image Analysis**: Upload leaf photos for disease classification (powdery_mildew, blight, rust, healthy)
- **🎙️ Voice Input**: Record via microphone or upload audio files for voice-based disease reporting
- **💬 Text Q&A**: Ask questions about plant diseases and get answers from a knowledge base

## Quick Start in Google Colab

### 1. Clone + Install (Method B)

```python
from getpass import getpass
token = getpass("GitHub PAT: ")
!git clone https://{token}:x-oauth-basic@github.com/arslanmit/leaf-doctor-ai-bot.git
%cd leaf-doctor-ai-bot
%pip uninstall -y pydrive2
%pip install -r requirements-colab.txt
%pip check
```

### 2. Start Streamlit (port 8501)

```python
!fuser -k 8501/tcp || true
!nohup streamlit run src/ui/app_streamlit.py --server.address 0.0.0.0 --server.port 8501 >/content/streamlit.log 2>&1 &
```

### 3. Tunnel — Cloudflare (no account)

```python
from pycloudflared import try_cloudflare
print(try_cloudflare(8501))  # prints an https://*.trycloudflare.com URL
```

### 4. (Optional) ngrok

```python
from getpass import getpass
tok = getpass("ngrok authtoken: ")  # paste only the raw token, not the whole command
import os
os.environ["NGROK_AUTHTOKEN"] = tok
from pyngrok import ngrok
try:
    ngrok.kill()
except:
    pass
print(ngrok.connect(8501, bind_tls=True))
```

### 5. Commit back to Git

```python
!git add -A
!git commit -m "streamlit mvp: image/voice/text with mic"
!git push
```

## Architecture

```
src/
├── core/
│   ├── vision.py    # ResNet18-based image classification
│   ├── audio.py     # Whisper-tiny ASR + rule-based classification
│   └── nlp.py       # DistilBERT Q&A pipeline
└── ui/
    └── app_streamlit.py  # Main Streamlit interface
```

## Privacy & Ethics

- **Local Processing**: Whisper-tiny runs locally for voice privacy
- **Confidence Scores**: All predictions show probability distributions
- **Disclaimer**: This tool provides agronomic advice; it is not a professional diagnosis
- **Non-Medical**: Not intended for medical or commercial agricultural decisions

## Technical Details

- **Vision**: ResNet18 with ImageNet pretraining (fine-tuning checkpoint support)
- **Audio**: OpenAI Whisper-tiny for transcription + rule-based disease classification
- **NLP**: DistilBERT for question-answering on plant disease knowledge base
- **UI**: Streamlit with WebRTC for microphone support
- **Deployment**: Cloudflare Quick Tunnel (no account) or ngrok

## Acceptance Criteria

✅ `pip check` shows no conflicts (pydrive2 removed)
✅ Streamlit UI opens with three tabs
✅ Voice tab works with microphone: records, writes mic.wav, Whisper tiny returns text, rule-based class shown
✅ Leaf Image tab returns a probability dict for 4 classes
✅ Text Q&A tab answers with DistilBERT QA
✅ Cloudflare tunnel provides HTTPS URL; browser mic permission works

## Future Enhancements

- Fine-tuned vision model (load checkpoint from `data/*.pt`)
- Hugging Face Hub integration
- Training scripts for custom datasets
- Multi-language support
- Advanced disease knowledge base

## Development

### Code Quality

This project uses comprehensive linting and formatting tools:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style and error checking
- **mypy**: Static type checking
- **bandit**: Security analysis
- **pre-commit**: Automated checks on commit

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Or use the setup script
./scripts/setup_linting.sh
```

### Available Commands

```bash
make lint        # Run all linting checks
make format      # Format code with black and isort
make type-check  # Run mypy type checking
make check       # Run all checks (lint + type + security)
make fix         # Auto-fix formatting issues
make test        # Run tests
```

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit to ensure code quality:
- Trailing whitespace removal
- End-of-file fixing
- YAML validation
- Black formatting
- Import sorting with isort
- flake8 linting
- mypy type checking
- bandit security checks

## License

MIT License - see LICENSE file for details.
