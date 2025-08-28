---
inclusion: always
---

# Requirements Document: Streamlit UI Redesign

## Introduction

This specification covers the complete redesign of the PlantGuard Streamlit application to create a modern, ADHD-friendly, mobile-first multimodal plant disease detection interface. The redesign transforms the existing basic UI into a production-ready application with enhanced user experience, accessibility features, and comprehensive functionality while maintaining all current capabilities (text chat, voice/microphone, camera capture, image upload) and **strict offline-first operation**.

The redesigned interface will provide intuitive navigation, responsive layouts, and comprehensive analysis visualization while ensuring full accessibility compliance and optimal performance across all devices. **CRITICAL CONSTRAINT**: All ML inference must be local-only with no external API dependencies.

## Architecture Context

**Pipeline**: `User Input → [Vision/Audio/Text Adapter] → Fusion Model → Response`

**Core Technology Stack**:
- **Vision**: ResNet50 fine-tuned on PlantVillage dataset
- **Audio**: Whisper-tiny (local) + CNN-LSTM for disease classification  
- **Text**: DistilBERT fine-tuned on plant-care FAQ dataset
- **UI**: Streamlit with streamlit-webrtc for real-time capture
- **Training**: TensorBoard logging to `./runs/experiment_{timestamp}`

**Non-Negotiable Constraints**:
- ❌ No external ML APIs (OpenAI, Replicate, cloud vision services)
- ❌ No user data sent to external services
- ❌ No internet-dependent inference
- ✅ All processing must work offline after initial model downloads
- ✅ Graceful degradation when components fail

## Requirements

### Requirement 1: Multi-Page Navigation Architecture

**User Story:** As a user, I want to navigate between different sections of the application easily, so that I can access specific features like comparison, history, and settings without cluttering the main interface.

#### Acceptance Criteria

1. WHEN the application loads THEN the system SHALL provide multi-page navigation using st.navigation() or pages/ directory structure
2. WHEN navigating between pages THEN the system SHALL include Home/Chat, Compare, History, Guide, and Settings pages
3. WHEN on any page THEN the system SHALL display a consistent header with PlantGuard branding and navigation links
4. WHEN the user accesses the application THEN the system SHALL default to the Home/Chat page
5. IF the user is on a specific page THEN the system SHALL highlight the current page in the navigation

### Requirement 2: Modern Input Ribbon Interface

**User Story:** As a user, I want quick access to all input methods through a prominent ribbon interface, so that I can easily switch between text, voice, camera, and upload modes.

**Technical Context:** Implements unified input interface with proper adapter integration and offline validation.

#### Acceptance Criteria

1. WHEN the main page loads THEN the system SHALL display an input ribbon with four prominent buttons: Text (⌨️), Voice (🎙️), Camera (📷), Upload (🖼️)
2. WHEN a user clicks an input method THEN the system SHALL activate that mode and show appropriate input controls using proper adapter interfaces
3. WHEN multiple inputs are provided THEN the system SHALL allow clearing all inputs with a "Clear All" button that includes temporary file cleanup
4. WHEN an input method is active THEN the system SHALL provide visual feedback showing the selected mode with touch-friendly targets (minimum 44px)
5. IF the user switches input methods THEN the system SHALL preserve any existing inputs until explicitly cleared

**Implementation Requirements:**
- Use required adapter interfaces: `VisionAdapter`, `AudioAdapter`, `TextAdapter`
- Input validation: Images max 200MB (JPG/PNG), Audio 1-60s (WAV/MP3), Text max 1000 chars
- Implement proper error handling with fallback responses
- Use `st.session_state` for input mode persistence

### Requirement 3: Responsive Layout Design

**User Story:** As a user on different devices, I want the interface to adapt to my screen size, so that I can use PlantGuard effectively on desktop, tablet, and mobile devices.

#### Acceptance Criteria

1. WHEN accessing on desktop THEN the system SHALL use a 2-column layout with chat panel (5 units) and analysis cards (7 units)
2. WHEN accessing on mobile THEN the system SHALL stack components vertically in a single-column layout
3. WHEN the screen size changes THEN the system SHALL automatically adjust the layout responsively
4. WHEN displaying content THEN the system SHALL ensure all interactive elements are touch-friendly (minimum 44px)
5. IF the viewport is narrow THEN the system SHALL prioritize content visibility over decorative elements

### Requirement 4: Enhanced Analysis Cards Display

**User Story:** As a user, I want comprehensive analysis results displayed in organized cards, so that I can quickly understand the disease diagnosis, confidence levels, and recommended actions.

#### Acceptance Criteria

1. WHEN analysis completes THEN the system SHALL display disease prediction with confidence bar visualization
2. WHEN showing results THEN the system SHALL include a Top-5 probabilities chart using Plotly Express or st.bar_chart
3. WHEN a disease is detected THEN the system SHALL show symptom checklist and action chips (Isolate plant, Adjust watering, etc.)
4. WHEN displaying confidence THEN the system SHALL use color-coded risk badges (green: low risk, yellow: medium, red: high)
5. IF multiple images are analyzed THEN the system SHALL create separate analysis cards for each result

### Requirement 5: Chat Interface Enhancement

**User Story:** As a user, I want an intuitive chat interface that maintains conversation history and allows follow-up questions, so that I can have natural interactions with the plant disease detection system.

#### Acceptance Criteria

1. WHEN using text mode THEN the system SHALL provide st.chat_message bubbles for user and assistant messages
2. WHEN entering text THEN the system SHALL use st.chat_input for follow-up questions and responses
3. WHEN a conversation occurs THEN the system SHALL persist chat history in st.session_state["messages"]
4. WHEN displaying messages THEN the system SHALL show clear visual distinction between user and AI responses
5. IF the chat becomes long THEN the system SHALL maintain scrollable history with newest messages visible

### Requirement 6: Voice and Audio Processing Interface

**User Story:** As a user, I want to record voice questions and upload audio files easily, so that I can interact with PlantGuard hands-free while working with plants.

**Technical Context:** Must use local Whisper-tiny only (no cloud speech services) with proper temporary file management.

#### Acceptance Criteria

1. WHEN using voice mode THEN the system SHALL provide streamlit-webrtc microphone capture at 16 kHz mono using `AudioAdapter.transcribe()` method
2. WHEN recording audio THEN the system SHALL save temporary WAV files using `tempfile` and delete them immediately after processing
3. WHEN audio is uploaded THEN the system SHALL accept WAV and MP3 formats with 1-60 second duration limits and validate using `AudioAdapter` constraints
4. WHEN processing audio THEN the system SHALL show step-by-step progress using st.status indicators with offline-only processing
5. IF audio processing fails THEN the system SHALL provide clear error messages and retry options with graceful degradation

**Implementation Requirements:**
- MANDATORY: Use only local Whisper-tiny model (no external APIs)
- Implement `AudioAdapter.transcribe(audio_file) -> str` interface
- Use `tempfile` for temporary storage, clean up immediately
- Error handling pattern: try/except with fallback responses
- Audio validation: 1-60 seconds, WAV/MP3 formats only

### Requirement 7: Image Input and Camera Integration

**User Story:** As a user, I want flexible image input options including file upload and camera capture, so that I can analyze plant images regardless of my device capabilities.

**Technical Context:** Must integrate with local ResNet50 vision model and implement proper PIL.Image handling.

#### Acceptance Criteria

1. WHEN uploading images THEN the system SHALL support st.file_uploader with multiple file selection (JPG, JPEG, PNG) and validate using `VisionAdapter` requirements
2. WHEN using camera mode THEN the system SHALL provide st.camera_input for mobile-friendly photo capture with PIL.Image conversion
3. WHEN images are selected THEN the system SHALL display thumbnail previews with zoom capabilities and validate max 200MB file size
4. WHEN processing images THEN the system SHALL use `VisionAdapter.predict(image: PIL.Image.Image) -> tuple[str, float]` interface
5. IF image processing fails THEN the system SHALL suggest resizing or format conversion options with graceful degradation

**Implementation Requirements:**
- MANDATORY: Use local ResNet50 model only (no cloud vision APIs)
- Implement `VisionAdapter.predict()` interface with PIL.Image input
- Image validation: Max 200MB, formats ["jpg", "jpeg", "png"]
- Error handling with fallback responses
- Use `pathlib.Path` for file operations

### Requirement 8: Compare View Implementation

**User Story:** As a user, I want to compare multiple plant images side-by-side, so that I can analyze differences and track disease progression over time.

#### Acceptance Criteria

1. WHEN accessing Compare page THEN the system SHALL provide A/B image viewer with zoom and pan capabilities
2. WHEN comparing images THEN the system SHALL highlight differences in disease predictions and confidence levels
3. WHEN viewing comparisons THEN the system SHALL show delta analysis between the two results
4. WHEN images are loaded THEN the system SHALL allow swapping positions and adjusting comparison parameters
5. IF only one image is available THEN the system SHALL prompt for a second image or suggest using recent analyses

### Requirement 9: History and Export Functionality

**User Story:** As a user, I want to view my analysis history and export reports, so that I can track plant health over time and share results with experts.

#### Acceptance Criteria

1. WHEN accessing History page THEN the system SHALL display a searchable grid of past analyses with thumbnails
2. WHEN viewing history THEN the system SHALL provide filters by date, model type, and disease label
3. WHEN exporting data THEN the system SHALL support CSV and PDF report generation
4. WHEN displaying history THEN the system SHALL show analysis metadata including timestamp and confidence scores
5. IF no history exists THEN the system SHALL provide guidance on how to start analyzing plants

### Requirement 10: Settings and Configuration

**User Story:** As a user, I want to customize the application settings including theme, language, and model preferences, so that I can personalize my PlantGuard experience.

#### Acceptance Criteria

1. WHEN accessing Settings THEN the system SHALL provide theme selection (light/dark/system) with persistence
2. WHEN changing settings THEN the system SHALL store preferences in st.session_state for session persistence
3. WHEN available THEN the system SHALL allow model switching between different vision, audio, and text models
4. WHEN configuring THEN the system SHALL provide language selection and unit preferences (metric/imperial)
5. IF settings are changed THEN the system SHALL apply changes immediately without requiring restart

### Requirement 11: ADHD-Friendly Design Implementation

**User Story:** As a user with ADHD, I want a clean, focused interface with clear visual hierarchy, so that I can use the application without cognitive overload.

#### Acceptance Criteria

1. WHEN displaying content THEN the system SHALL use big headings with emoji/icons for section identification
2. WHEN presenting information THEN the system SHALL use short sentences and bullet points for readability
3. WHEN showing options THEN the system SHALL provide Simple/Expert toggle for interface complexity
4. WHEN processing occurs THEN the system SHALL show clear progress indicators and status updates
5. IF multiple actions are available THEN the system SHALL prioritize the most common workflows prominently

### Requirement 12: Accessibility and Mobile Optimization

**User Story:** As a user with accessibility needs, I want the application to support keyboard navigation and screen readers, so that I can use PlantGuard regardless of my abilities.

#### Acceptance Criteria

1. WHEN navigating THEN the system SHALL support full keyboard navigation with proper tab order
2. WHEN displaying content THEN the system SHALL include ARIA labels and alt text for all images
3. WHEN showing charts THEN the system SHALL provide captions and data tables for screen readers
4. WHEN using touch devices THEN the system SHALL ensure all interactive elements meet minimum touch target sizes
5. IF accessibility features are needed THEN the system SHALL maintain WCAG AA compliance standards

### Requirement 13: Performance and State Management

**User Story:** As a user, I want fast, responsive interactions with minimal loading times, so that I can efficiently analyze multiple plants without delays.

**Technical Context:** Must use Streamlit caching patterns with proper adapter initialization and Apple Silicon optimization.

#### Acceptance Criteria

1. WHEN loading models THEN the system SHALL use `@st.cache_resource` for model caching and lazy loading of all adapters
2. WHEN processing requests THEN the system SHALL minimize reruns through proper state management using `st.session_state`
3. WHEN handling multiple images THEN the system SHALL support batch processing with queued progress indicators
4. WHEN using the application THEN the system SHALL maintain responsive interactions under normal load with MPS backend when available
5. IF heavy processing occurs THEN the system SHALL provide progress feedback and allow cancellation

**Implementation Requirements:**
- MANDATORY: Use `@st.cache_resource` pattern for all model loading
- Implement proper adapter interfaces with caching
- Use Apple Silicon MPS backend: `torch.device("mps" if torch.backends.mps.is_available() else "cpu")`
- Error handling with graceful degradation when models fail to load
- Use `tempfile` for temporary storage, clean up immediately

### Requirement 14: Error Handling and User Feedback

**User Story:** As a user, I want clear error messages and helpful guidance when something goes wrong, so that I can resolve issues and continue using the application.

#### Acceptance Criteria

1. WHEN errors occur THEN the system SHALL display friendly error messages using st.toast for non-blocking alerts
2. WHEN validation fails THEN the system SHALL provide specific guidance for fixing input issues (resize, format conversion)
3. WHEN processing fails THEN the system SHALL offer retry options and alternative approaches
4. WHEN showing errors THEN the system SHALL maintain application stability without crashes
5. IF critical errors occur THEN the system SHALL provide fallback functionality and recovery options

### Requirement 15: Privacy and Security Interface

**User Story:** As a privacy-conscious user, I want clear information about data handling and local processing, so that I can trust the application with my plant images and voice recordings.

**Technical Context:** Must enforce local-only processing with no external API calls and proper temporary file management.

#### Acceptance Criteria

1. WHEN using the application THEN the system SHALL display clear privacy disclaimers about local processing with no external API usage
2. WHEN processing audio THEN the system SHALL show confirmation of temporary file deletion after analysis using `tempfile` cleanup
3. WHEN accessing the Guide page THEN the system SHALL provide comprehensive privacy information and GDPR compliance details
4. WHEN uploading files THEN the system SHALL confirm that no data is sent to external services (all processing local-only)
5. IF privacy concerns arise THEN the system SHALL provide detailed information about offline-first operation and local model usage

**Implementation Requirements:**
- CRITICAL: Enforce no external API calls for ML inference
- Use only local models: ResNet50, Whisper-tiny, DistilBERT
- Implement proper temporary file cleanup with `tempfile` module
- Never persist user data beyond session scope
- Display clear local-only processing confirmations

### Requirement 16: Offline-First Architecture Compliance

**User Story:** As a user in areas with limited internet connectivity, I want the application to function completely offline after initial setup, so that I can analyze plants without depending on internet access.

**Technical Context:** Must ensure all ML models are local with proper adapter interfaces and no external dependencies.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL load all models locally without external API calls using proper adapter interfaces
2. WHEN processing any input type THEN the system SHALL use only local ML models (ResNet50, Whisper-tiny, DistilBERT) via required adapters
3. WHEN models fail to load THEN the system SHALL provide clear error messages and fallback options with graceful degradation
4. WHEN temporary files are created THEN the system SHALL clean them up immediately after processing using `tempfile` module
5. IF internet connectivity is lost THEN the system SHALL continue functioning without degradation

**Implementation Requirements:**
- MANDATORY: All adapters must use local models only
- Required interfaces: `VisionAdapter`, `AudioAdapter`, `TextAdapter`, `ChatModel`
- Model locations: `data/models/` directory with proper checkpoint paths
- Error handling: try/except with fallback responses, never crash UI
- File operations: Use `pathlib.Path` and `tempfile` for temporary storage

### Requirement 17: Model Integration and Caching

**User Story:** As a user, I want fast model loading and efficient resource usage, so that I can analyze plants quickly without waiting for models to reload.

**Technical Context:** Must implement proper Streamlit caching with required adapter interfaces and Apple Silicon optimization.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL use `@st.cache_resource` for all model loading with proper adapter initialization
2. WHEN switching between input modes THEN the system SHALL reuse cached models without reloading using singleton pattern
3. WHEN processing multiple inputs THEN the system SHALL maintain model instances in memory efficiently with MPS backend support
4. WHEN memory usage is high THEN the system SHALL provide options to clear model cache gracefully
5. IF model loading fails THEN the system SHALL provide specific error messages and retry mechanisms with fallback responses

**Implementation Requirements:**
- MANDATORY: Use `@st.cache_resource` for all adapter loading
- Required caching pattern:
  ```python
  @st.cache_resource
  def load_models():
      return VisionAdapter(), AudioAdapter(), TextAdapter()
  ```
- Apple Silicon optimization: Use MPS backend when available
- Error handling: Graceful degradation when adapters fail to load
- Model paths: `data/models/` with proper checkpoint validation

## Code Quality Standards

### Required Patterns

All implementations must follow these mandatory patterns from the steering documents:

**Error Handling Pattern:**
```python
try:
    result = adapter.process(input_data)
except Exception as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()  # Never crash the UI
```

**Input Validation:**
- Images: Max 200MB, formats `["jpg", "jpeg", "png"]`
- Audio: 1-60 seconds, formats `["wav", "mp3"]`
- Text: Max 1000 characters for chat input
- Use `st.session_state` for conversation history

**File Operations:**
- Use `pathlib.Path` for all file operations
- Use `tempfile` for temporary storage, clean up immediately
- Delete temp files (`tmp_audio`, `mic.wav`) after processing
- Never persist user data beyond session scope

**Code Style:**
- Type annotations for all public methods
- Line length: 100 characters maximum
- Double quotes for strings
- Import order: First-party (`src`) before third-party
- Use `logger.info()` instead of `print()` in production
- Specific exception handling: `except FileNotFoundError:` not `except:`

## Dependencies and Configuration

### Required Dependencies (pyproject.toml)

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
plotly = ">=5.0.0"  # For visualization charts
```

### Streamlit Configuration (.streamlit/config.toml)

```toml
[global]
developmentMode = false
showWarningOnDirectExecution = false

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
showErrorDetails = false

[theme]
primaryColor = "#22C55E"
backgroundColor = "#0F172A"
secondaryBackgroundColor = "#1E293B"
textColor = "#F8FAFC"
font = "sans serif"
```
