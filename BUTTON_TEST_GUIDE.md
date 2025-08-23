# 🌿 PlantGuard Web Application - Button Testing Guide

## 📋 Overview
This document provides a comprehensive list of all interactive buttons and elements in the PlantGuard AI plant disease detection system for manual testing purposes.

**Application URL**: http://localhost:8501  
**Total Interactive Buttons**: 24  
**Last Updated**: 2025-08-23

---

## 🚀 Quick Actions Section (4 buttons)

Located at the top of the main interface for quick access to common operations.

| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `🔄 Reload Models` | Reloads all model adapters | Clears cache and reloads models, shows success message | ⬜ |
| `📊 Quick Test` | Tests current models on sample data | Shows info about Model Management tab | ⬜ |
| `🔧 Settings` | Access advanced model settings | Shows info about Model Management tab | ⬜ |
| `📈 Performance` | View model performance metrics | Shows info about Model Management tab | ⬜ |

---

## 🖼️ Vision Analysis Tab (1 button)

Primary tab for image-based plant disease detection.

| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `🔍 Analyze Plant` | Primary button to analyze uploaded plant image | Processes uploaded image and displays disease detection results | ⬜ |

**Prerequisites**: Must upload an image file (PNG, JPG, JPEG) before button becomes active.

---

## 🎤 Audio Processing Tab (4 buttons)

Tab for voice and audio-based plant disease detection and Q&A.

### Live Recording Section
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `START` | Start microphone recording (WebRTC) | Begins live audio recording from microphone | ⬜ |
| `STOP` | Stop microphone recording (WebRTC) | Ends live audio recording | ⬜ |
| `🎯 Process Recording` | Process recorded audio | Transcribes audio and generates AI response | ⬜ |

### File Upload Section
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `🎯 Process File` | Process uploaded audio file | Transcribes uploaded audio file and generates response | ⬜ |

**Prerequisites**: Must upload an audio file (WAV, MP3, M4A) before Process File button becomes active.

---

## 💬 Text Q&A Tab (7 buttons)

Tab for text-based plant care questions and AI assistance.

### Sample Questions (5 buttons)
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `💡 How to treat powdery mildew?` | Pre-filled sample question | Fills question input field and triggers auto-submit | ⬜ |
| `💡 What causes yellow leaves in plants?` | Pre-filled sample question | Fills question input field and triggers auto-submit | ⬜ |
| `💡 How to prevent fungal diseases?` | Pre-filled sample question | Fills question input field and triggers auto-submit | ⬜ |
| `💡 Best practices for plant watering?` | Pre-filled sample question | Fills question input field and triggers auto-submit | ⬜ |
| `💡 Signs of nutrient deficiency in plants` | Pre-filled sample question | Fills question input field and triggers auto-submit | ⬜ |

### Chat Interface (2 buttons)
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `🚀 Ask` | Submit question to AI assistant | Processes user question and generates AI response | ⬜ |
| `🗑️ Clear History` | Clear conversation history | Removes all previous chat history | ⬜ |

---

## 📚 Training Tab (5 buttons)

Tab for viewing training runs, reports, and launching TensorBoard.

### Download Reports (4 buttons)
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `Download JSON` | Download training report JSON | Downloads training_report.json file | ⬜ |
| `Download Summary` | Download text summary | Downloads training_summary.txt file | ⬜ |
| `Download HTML` | Download HTML report | Downloads comprehensive_report.html file | ⬜ |
| `Download Curves` | Download training curves image | Downloads training_curves.png file | ⬜ |

### TensorBoard (1 button)
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `🚀 Launch TensorBoard` | Launch TensorBoard interface | Starts TensorBoard server on specified port | ⬜ |

**Prerequisites**: Must have training runs in the specified runs directory.

---

## 🔧 Model Management Tab (3 buttons)

Tab for model selection, testing, and configuration management.

### Model Selection (1 button)
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `🔄 Switch Model` | Switch to selected model | Changes active model to selected option | ⬜ |

### Model Testing (1 button)
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `🧪 Test Model` | Test current model with uploaded image | Analyzes test image with current model and shows results | ⬜ |

**Prerequisites**: Must upload a test image before button becomes active.

### Configuration Management (1 button)
| Button | Description | Expected Behavior | Test Status |
|--------|-------------|-------------------|-------------|
| `📝 View Config` | Display current model configuration | Shows JSON configuration in expandable format | ⬜ |
| `🔄 Reload Config` | Reload configuration from file | Reloads model configuration and shows success message | ⬜ |
| `📁 Open Config Folder` | View configuration folder information | Shows config folder path and contents | ⬜ |

---

## 📊 Interactive Elements (Non-Button)

Additional interactive elements that enhance user experience:

### Dropdowns
- **Vision Model Selector** - Choose between Vision Transformer, ResNet50, MobileNet
- **Audio Model Selector** - Choose between Whisper Tiny, Wav2Vec2
- **Text Model Selector** - Choose between DistilBERT, RoBERTa, T5
- **Training Run Selector** - Select training run for analysis
- **Model Selection Dropdown** - Choose model in Model Management tab

### File Uploaders
- **Plant Image Upload** - Drag & drop or browse for plant images
- **Audio File Upload** - Upload audio files for processing
- **Test Image Upload** - Upload images for model testing

### Input Fields
- **Question Text Input** - Type questions for AI assistant
- **Runs Directory Input** - Specify directory for training runs
- **TensorBoard Port Input** - Set port number for TensorBoard

### Navigation
- **5 Main Tabs** - Vision Analysis, Audio Processing, Text Q&A, Training, Model Management

---

## 🧪 Testing Checklist

### Pre-Testing Setup
- [ ] Ensure PlantGuard application is running at http://localhost:8501
- [ ] Verify all models are loaded successfully
- [ ] Prepare test images (plant leaf photos)
- [ ] Prepare test audio files (if testing audio features)

### Testing Workflow
1. **Quick Actions** - Test all 4 buttons in sequence
2. **Vision Analysis** - Upload image and test analyze button
3. **Audio Processing** - Test both live recording and file upload
4. **Text Q&A** - Test all 5 sample questions and custom questions
5. **Training** - Test download buttons and TensorBoard launch
6. **Model Management** - Test model switching and configuration

### Test Status Legend
- ⬜ Not Tested
- ✅ Passed
- ❌ Failed
- ⚠️ Issues Found

---

## 🔧 Troubleshooting

### Common Issues
- **Button Not Responding**: Check browser console for JavaScript errors
- **Model Loading Errors**: Verify model files are present and accessible
- **Audio Not Working**: Check microphone permissions and browser compatibility
- **File Upload Issues**: Verify file format and size limitations

### Browser Compatibility
- **Recommended**: Chrome, Firefox, Safari (latest versions)
- **WebRTC Support**: Required for audio recording functionality
- **JavaScript**: Must be enabled for full functionality

---

## 📝 Test Results Summary

**Total Buttons Tested**: ___/24  
**Passed**: ___  
**Failed**: ___  
**Issues Found**: ___

### Critical Issues
- [ ] None identified

### Minor Issues
- [ ] None identified

### Recommendations
- [ ] None identified

---

## 📞 Support

For issues or questions about testing:
- Check application logs in terminal
- Verify all dependencies are installed correctly
- Ensure proper Python environment is activated
- Review PlantGuard documentation

**Documentation**: See project README.md for detailed setup instructions  
**Application Status**: http://localhost:8501

---

*Generated on 2025-08-23 for PlantGuard AI Plant Disease Detection System*