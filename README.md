# 🌿 PlantGuard — Streamlit Multimodal MVP

**Early leaf disease detection using Image + Voice + Text modalities**

PlantGuard is a proof-of-concept multimodal AI system for plant disease detection. It combines computer vision (ResNet18), automatic speech recognition (Whisper-tiny), and natural language processing (DistilBERT) in a single Streamlit interface.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/arslanmit/PlantGuard/blob/main/notebooks/PlantGuard.ipynb)

## Features

- **🖼️ Leaf Image Analysis**: Upload leaf photos for disease classification (powdery_mildew, blight, rust, healthy)
- **🎙️ Voice Input**: Record via microphone or upload audio files for voice-based disease reporting
- **💬 Text Q&A**: Ask questions about plant diseases and get answers from a knowledge base

## Environment Setup

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# GitHub Personal Access Token (for private repository access)
GITHUB_TOKEN=your_github_personal_access_token_here

# Optional: Hugging Face Token (for model downloads)
HF_TOKEN=your_hugging_face_token_here
```

**Note**: This repository is private. You'll need a GitHub Personal Access Token with repository access to clone and use it.

## Quick Start in Google Colab

### 1. Clone + Install (Method B)

```python
from getpass import getpass
token = getpass("GitHub PAT: ")
!git clone https://{token}:x-oauth-basic@github.com/arslanmit/PlantGuard.git
%cd PlantGuard
%pip uninstall -y pydrive2
%pip install -r requirements.txt
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
│   ├── vision.py    # ResNet50-based image classification (PlantVillage dataset)
│   ├── audio.py     # Whisper-tiny ASR for voice input
│   └── nlp.py       # Knowledge base and response generation
├── data/
│   ├── dataset.py   # PlantVillage dataset loading and preprocessing
│   └── preprocessing.py  # Image and audio preprocessing utilities
├── utils/
│   ├── config.py    # Configuration management
│   ├── logging.py   # Logging setup
│   ├── error_handling.py  # Error handling utilities
│   └── file_utils.py      # File management utilities
├── ui/
│   └── app.py       # Main Streamlit interface
└── plantguard_bot.py  # Main orchestration class
```

## Privacy & Ethics

- **Local Processing**: Whisper-tiny runs locally for voice privacy
- **Confidence Scores**: All predictions show probability distributions
- **Disclaimer**: This tool provides agronomic advice; it is not a professional diagnosis
- **Non-Medical**: Not intended for medical or commercial agricultural decisions

## Technical Details

- **Vision**: ResNet50 with ImageNet pretraining, fine-tuned on PlantVillage dataset (38 disease classes)
- **Audio**: OpenAI Whisper-tiny for local speech-to-text transcription
- **NLP**: JSON-based knowledge base with template-based response generation
- **UI**: Streamlit with audio input support for multimodal interaction
- **Privacy**: All processing happens locally, no external API calls
- **Deployment**: Hugging Face Spaces or local deployment

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

## Code Quality

This project uses comprehensive linting and formatting tools:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style and error checking
- **mypy**: Static type checking
- **bandit**: Security analysis
- **bandit**: Security analysis

### Setup Environment

```bash
# Complete setup (recommended)
make setup

# Or install dependencies only
make deps

# All dependencies (production + development) are in requirements.txt
pip install -r requirements.txt
```

### Available Commands

```bash
make lint        # Run linting checks with Ruff
make fmt         # Format code with Ruff
make type        # Run mypy type checking
make test        # Run tests with coverage
make qa          # Run all quality checks (fmt + lint + type + test)
make check       # CI-style checks (no auto-fix)
```

### Code Quality Workflow

Run quality checks manually or via CI:

```bash
make fmt        # Format code with ruff
make lint       # Lint code with ruff  
make type       # Type check with mypy
make security   # Security scan with bandit
make qa         # Run all quality checks
```

## License

MIT License - see LICENSE file for details.
