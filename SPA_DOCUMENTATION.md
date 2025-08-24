# PlantGuard Single Page Application (SPA) Documentation

## Overview

PlantGuard has been transformed into a **Single Page Application (SPA)** that consolidates ALL functionality into one seamless, AI-agent-friendly interface. No navigation complexity - everything accessible from one unified view.

## 🌟 Key Features

### All-in-One Interface
- **Image Analysis**: Upload and analyze plant images with AI
- **Voice Assistant**: Record audio questions and get responses
- **Chat Interface**: Text-based plant care conversations
- **Model Management**: Switch between AI models inline
- **History Tracking**: Access past analyses contextually
- **Comparison Mode**: Side-by-side image comparison
- **Batch Processing**: Analyze multiple images at once
- **Export Functions**: Download results and data

### AI Agent Optimized
- **No Navigation Required**: All features in single view
- **Contextual UI**: Interface adapts to current task
- **Progressive Disclosure**: Information reveals as needed
- **Immediate Access**: All tools available instantly
- **Simple Interactions**: Streamlined for AI workflow

## 🚀 Quick Start

### Launch Application
```bash
# Primary command (recommended)
make run

# Alternative methods
streamlit run spa_app.py
python -m streamlit run spa_app.py --server.port=8501
```

### Environment Setup
```bash
# Complete setup (first time)
make setup

# Quick dependency install
make deps

# Validate SPA readiness
make validate-spa
```

## 📱 Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    🌿 PlantGuard AI Header                   │
├─────────────────────────────────────────────────────────────┤
│  Main Analysis Area (70%)           │  Context Panel (30%)  │
│  ┌─────────────────────────────────┐ │  ┌─────────────────┐ │
│  │ 📷 Image Upload Zone            │ │  │ ⚙️ Model Select  │ │
│  │ 🎤 Voice Recording              │ │  │ 📊 Quick Status │ │
│  │ 💬 Text Chat Input              │ │  │ 📋 Recent Data  │ │
│  └─────────────────────────────────┘ │  └─────────────────┘ │
│  ┌─────────────────────────────────┐ │  ┌─────────────────┐ │
│  │ 🔬 Dynamic Results Area         │ │  │ 🔧 Quick Actions│ │
│  │ • Analysis Results              │ │  │ • Export        │ │
│  │ • Chat Responses                │ │  │ • Compare       │ │
│  │ • Comparison Views              │ │  │ • History       │ │
│  └─────────────────────────────────┘ │  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🤖 Technical Capabilities Preserved

### Vision Processing
- **Multiple Models**: Vision Transformer (100%), ResNet50 (95%), MobileNet (90%)
- **Hot-Swappable**: Switch models without restart
- **Batch Processing**: Analyze multiple images simultaneously
- **Apple Silicon**: MPS acceleration on Apple devices

### Audio Processing
- **Speech Recognition**: Whisper-based transcription
- **File Support**: WAV, MP3, M4A formats
- **Real-time Recording**: Direct microphone input
- **Question Processing**: Natural language plant queries

### Text Processing
- **Plant Care Chat**: DistilBERT-powered responses
- **Knowledge Base**: Comprehensive plant disease information
- **Conversational**: Multi-turn dialogue support
- **Context Aware**: Responses based on analysis context

### Model Management
- **Dynamic Loading**: Models loaded on demand
- **Memory Optimization**: Efficient resource usage
- **Configuration-Driven**: JSON-based model definitions
- **Compatibility Layer**: Graceful fallbacks for development

## 📊 Usage Examples

### Image Analysis Workflow
1. **Upload Image**: Drag and drop plant photo
2. **Select Model**: Choose AI model (ViT, ResNet50, MobileNet)
3. **Analyze**: Click "🔍 Analyze Plant"
4. **View Results**: See disease detection, confidence, recommendations
5. **Export**: Download results if needed

### Voice Assistant Workflow
1. **Record Audio**: Click "🎙️ Record Question"
2. **Ask Question**: "What disease does my tomato plant have?"
3. **Get Response**: Transcription + AI-generated answer
4. **Follow Up**: Continue conversation in chat

### Batch Processing Workflow
1. **Upload Multiple**: Select multiple plant images
2. **Batch Analyze**: Process all images automatically
3. **Progress Tracking**: Real-time progress indicator
4. **Results Summary**: Comprehensive analysis report
5. **Export All**: Download complete results

### Comparison Workflow
1. **Upload First Image**: Primary plant photo
2. **Enable Compare**: Click "🔄 Compare"
3. **Upload Second**: Comparison plant photo
4. **Side-by-Side**: View analysis results together
5. **Metrics**: Confidence differences, same disease detection

## 🛠️ Configuration

### Model Configuration (`config/models.json`)
```json
{
  "vision": {
    "vit_best": {
      "name": "Vision Transformer (Best)",
      "accuracy": "100%",
      "speed": "Medium"
    },
    "resnet50_plantvillage_v1": {
      "name": "ResNet50",
      "accuracy": "95%",
      "speed": "Fast"
    },
    "mobilenet_fast": {
      "name": "MobileNet", 
      "accuracy": "90%",
      "speed": "Very Fast"
    }
  }
}
```

### Environment Variables
```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1    # Apple Silicon
export TORCH_DEVICE=mps                 # Apple Silicon
export PLANTGUARD_UI_MODE=spa           # SPA mode
```

## 🔧 Development

### File Structure
```
PlantGuard/
├── spa_app.py                    # Main SPA application
├── src/
│   ├── core/                     # Vision, audio, text adapters
│   ├── adapters_compat.py        # Compatibility layer
│   └── utils/                    # Utilities and logging
├── config/                       # Model and training configs
├── Makefile                      # Simplified SPA commands
└── requirements.txt              # Dependencies
```

### Key Classes
- **`PlantGuardSPA`**: Main application class
- **`VisionAdapter`**: Image analysis processing
- **`AudioAdapter`**: Voice/audio processing
- **`TextAdapter`**: Chat and Q&A processing

### Testing
```bash
# Validate SPA setup
make validate-spa

# Run tests
make test

# Check code quality
make qa
```

## 📱 Mobile & Accessibility

### Mobile Optimization
- **Responsive Design**: Works on phones and tablets
- **Touch Friendly**: Large buttons and touch targets
- **Optimized Layout**: Single column on small screens

### HTTPS for Microphone
```bash
# Create secure tunnel for microphone access
make tunnel

# Using Cloudflare (recommended)
brew install cloudflared
cloudflared tunnel --url http://localhost:8501

# Using ngrok (alternative)
pip install pyngrok
```

## 🚨 Troubleshooting

### Common Issues
1. **SPA Won't Start**: Run `make validate-spa`
2. **Import Errors**: Run `make deps`
3. **Model Loading**: Check `config/models.json`
4. **Audio Issues**: Use HTTPS tunnel (`make tunnel`)

### Performance Optimization
- **Apple Silicon**: MPS acceleration enabled automatically
- **Memory**: Efficient model loading and caching
- **Batch Size**: Optimized for device capabilities

## 📈 Benefits vs Legacy Multi-Page

### SPA Advantages
- ✅ **No Navigation**: All features in one view
- ✅ **AI Agent Friendly**: Simple, predictable interface
- ✅ **Faster Workflow**: No page switching delays
- ✅ **Better Context**: Related features together
- ✅ **Mobile Optimized**: Single interface works everywhere

### Legacy Limitations (Removed)
- ❌ Complex navigation between pages
- ❌ Lost context when switching features
- ❌ Separate interfaces for related functions
- ❌ Mobile navigation challenges

## 🔄 Migration from Legacy

### For Users
- **Same Features**: All functionality preserved
- **Better Experience**: Streamlined interface
- **No Relearning**: Intuitive single-page design

### For Developers
- **Simplified Codebase**: Single application file
- **Easier Maintenance**: No multi-page complexity
- **Better Testing**: Single interface to validate

## 🌐 API Reference

### Core Methods
```python
# Image Analysis
app.analyze_image(image, filename)
app.process_batch_images(uploaded_files)

# Audio Processing  
app.handle_voice_input()
app.process_audio_file(audio_file)

# Text Processing
app.process_text_query(query)

# Model Management
app.get_adapter(adapter_type)
app.render_model_selector()

# Results & Export
app.display_analysis_result(result)
app.export_all_results()
```

### Session State Variables
```python
st.session_state.analysis_history    # Analysis results
st.session_state.chat_messages       # Chat conversation
st.session_state.current_models      # Active models
st.session_state.comparison_mode     # Comparison state
st.session_state.processing_state    # Current processing
```

## 📚 Additional Resources

### Documentation
- Technical architecture preserved from original system
- Complete model management documentation
- Training pipeline documentation maintained

### Support
- GitHub Issues: Technical problems and bug reports
- Development: Follow standard contribution guidelines
- Testing: Use `make test` and `make qa` before commits

---

**🌟 The PlantGuard SPA provides the complete plant disease detection experience in one unified, AI-agent-friendly interface!**