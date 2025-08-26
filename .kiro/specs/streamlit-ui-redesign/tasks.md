---
inclusion: always
---

# Implementation Plan: Streamlit UI Redesign

## Overview

This implementation plan covers the complete redesign of the PlantGuard Streamlit application following the architecture constraints and technical requirements outlined in the steering documents. All implementations must maintain **strict offline-first operation** with local-only ML inference.

## Critical Constraints

**NEVER violate these rules when implementing**:
- ❌ No external ML APIs (OpenAI, Replicate, cloud vision services)
- ❌ No user data sent to external services
- ❌ No internet-dependent inference
- ✅ All processing must work offline after model downloads
- ✅ Use required adapter interfaces: `VisionAdapter`, `AudioAdapter`, `TextAdapter`
- ✅ Graceful degradation when components fail

## Required Code Interfaces

All implementations must use these exact interfaces:

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

- [ ] 1. Project Structure and Configuration Setup
  - Create new directory structure for redesigned UI with pages/ folder and component modules
  - Update .streamlit/config.toml with ADHD-friendly theme, accessibility settings, and performance optimizations  
  - Create unified assets/styles.css with ADHD-friendly design system and mobile-responsive CSS
  - Update requirements.txt with additional dependencies (plotly, streamlit-webrtc, pandas for exports)
  - **Technical Requirements**: Follow pyproject.toml standards for macOS ML/DL development
  - **Dependencies**: torch>=2.0.0 (MPS backend), streamlit>=1.28.0, streamlit-webrtc>=0.45.0
  - **Current Status**: Mobile components exist but need multi-page architecture with pages/ directory
  - _Requirements: 1.1, 1.2, 10.1, 11.1_

- [ ] 2. Core Navigation System Implementation
  - [ ] 2.1 Create multi-page navigation architecture
    - Create main app.py with st.navigation() setup for Home, Compare, History, Guide, Settings pages
    - Create pages/ directory structure with individual page modules (home.py, compare.py, history.py, guide.py, settings.py)
    - Add consistent header component with PlantGuard branding and navigation links
    - Implement active page highlighting and responsive navigation for mobile devices
    - **Current Status**: Single-page mobile app exists, need to convert to multi-page architecture
    - _Requirements: 1.1, 1.3, 1.4, 3.1, 3.2_

  - [ ] 2.2 Implement page routing and state management
    - Create StateManager class for efficient session state handling across pages
    - Add page transition animations and loading states for smooth navigation
    - Implement breadcrumb navigation and page history tracking
    - Add mobile-friendly hamburger menu for navigation on small screens
    - **Current Status**: Mobile state manager exists, need to adapt for multi-page navigation
    - _Requirements: 1.5, 13.2, 3.3_

- [x] 3. Input Ribbon Interface Development
  - [x] 3.1 Create unified input ribbon component
    - ✅ Implement InputRibbon class with four prominent buttons (Text ⌨️, Voice 🎙️, Camera 📷, Upload 🖼️)
    - ✅ Add visual feedback for active input modes with color-coded button states
    - ✅ Create Clear All functionality that resets all input states and temporary data
    - ✅ Implement responsive button sizing for touch devices (minimum 44px touch targets)
    - ✅ Integrate with required adapter interfaces, implement input validation
    - ✅ Validation: Images max 200MB (JPG/PNG), Audio 1-60s (WAV/MP3), Text max 1000 chars
    - **Status**: Mobile input ribbon exists, needs integration into multi-page architecture
    - _Requirements: 2.1, 2.2, 2.4, 12.4_

  - [x] 3.2 Add input mode state management
    - ✅ Create input mode switching logic with proper state persistence using `st.session_state`
    - ✅ Implement multiple simultaneous input mode support (e.g., image + voice query)
    - ✅ Add input validation and user feedback for each mode activation
    - ✅ Create mode-specific UI components that show/hide based on active modes
    - ✅ Use proper error handling with fallback responses
    - ✅ Error Pattern: `try/except` with graceful degradation, never crash UI
    - **Status**: Mobile state management exists, needs adaptation for multi-page flow
    - _Requirements: 2.3, 2.5, 13.2_

- [x] 4. Responsive Layout System Implementation
  - [x] 4.1 Create adaptive layout components
    - ✅ Implement responsive column system that adapts to screen size (desktop: 5/7 split, mobile: stacked)
    - ✅ Create mobile detection logic and viewport-based layout switching
    - ✅ Add CSS media queries in assets/styles.css for responsive breakpoints
    - ✅ Implement touch-friendly interface elements with minimum 44px touch targets
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 12.4_

  - [x] 4.2 Add mobile-first design patterns
    - ✅ Create collapsible navigation for mobile devices
    - ✅ Implement swipe gestures and touch interactions for mobile users
    - ✅ Add viewport meta tags and responsive image handling
    - ✅ Create mobile-optimized input controls and button layouts
    - _Requirements: 3.5, 12.4, 11.1_

- [x] 5. Enhanced Chat Interface Development
  - [x] 5.1 Implement chat message system
    - ✅ Create ChatInterface class using st.chat_message for user/assistant bubbles
    - ✅ Add st.chat_input for follow-up questions with proper input validation
    - ✅ Implement message history persistence in st.session_state["messages"]
    - ✅ Add message timestamps and metadata tracking for conversation context
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 5.2 Add conversation management features
    - ✅ Create scrollable chat history with newest messages visible
    - ✅ Implement conversation export functionality (CSV/PDF formats)
    - ✅ Add conversation search and filtering capabilities
    - ✅ Create conversation clearing and archiving options
    - _Requirements: 5.5, 9.3, 9.4_

- [x] 6. Voice and Audio Processing Interface
  - [x] 6.1 Implement voice input system
    - ✅ Create VoiceInterface class with streamlit-webrtc microphone capture at 16 kHz mono
    - ✅ Add real-time audio waveform visualization during recording
    - ✅ Implement audio file upload with WAV/MP3 format support (1-60 seconds)
    - ✅ Create temporary file management with immediate cleanup after processing
    - ✅ Use only local Whisper-tiny model (no cloud speech services)
    - ✅ Implement `AudioAdapter.transcribe(audio_file) -> str` interface
    - ✅ Use `tempfile` module, clean up immediately, never persist beyond session
    - _Requirements: 6.1, 6.2, 6.3, 16.4_

  - [x] 6.2 Add audio processing feedback
    - ✅ Implement step-by-step progress indicators using st.status for audio processing
    - ✅ Add audio transcription display with real-time updates
    - ✅ Create error handling for audio processing failures with retry options
    - ✅ Add audio quality validation and format conversion suggestions
    - ✅ Implement graceful degradation with fallback responses
    - ✅ Validation: 1-60 seconds duration, WAV/MP3 formats only
    - _Requirements: 6.4, 6.5, 14.2, 14.3_

- [x] 7. Image Input and Camera Integration
  - [x] 7.1 Create image upload system
    - ✅ Implement multi-file upload using st.file_uploader with JPG/JPEG/PNG support
    - ✅ Add drag-and-drop functionality and file validation (max 200MB per image)
    - ✅ Create image thumbnail previews with zoom and pan capabilities
    - ✅ Implement batch image processing with progress tracking
    - ✅ Use only local ResNet50 model (no cloud vision APIs)
    - ✅ Implement `VisionAdapter.predict(image: PIL.Image.Image) -> tuple[str, float]`
    - ✅ Validation: Max 200MB, formats ["jpg", "jpeg", "png"], use `pathlib.Path` for file ops
    - _Requirements: 7.1, 7.3, 7.4, 13.3_

  - [x] 7.2 Add camera capture functionality
    - ✅ Implement st.camera_input for mobile-friendly photo capture
    - ✅ Add image quality validation and format checking
    - ✅ Create image preprocessing and optimization for analysis
    - ✅ Add error handling for camera access and image processing failures
    - ✅ PIL.Image conversion, proper adapter integration
    - ✅ Graceful degradation when camera access fails
    - _Requirements: 7.2, 7.5, 14.1, 14.4_

- [x] 8. Analysis Cards and Visualization System
  - [x] 8.1 Create disease prediction cards
    - ✅ Implement AnalysisCard class with disease name and confidence bar visualization
    - ✅ Add color-coded risk badges (green: low, yellow: medium, red: high risk)
    - ✅ Create prediction timestamp and metadata display
    - ✅ Implement confidence interval visualization with progress bars
    - _Requirements: 4.1, 4.4, 4.5_

  - [x] 8.2 Add probability and symptom analysis
    - ✅ Create Top-5 probabilities chart using Plotly Express or st.bar_chart
    - ✅ Implement symptom checklist display with severity indicators
    - ✅ Add action recommendation chips (Isolate plant, Adjust watering, etc.)
    - ✅ Create multiple analysis cards for batch image processing
    - _Requirements: 4.2, 4.3, 4.5_

- [x] 9. Compare View Implementation
  - [x] 9.1 Create comparison interface
    - ✅ Implement CompareView class with A/B image viewer and synchronized zoom/pan
    - ✅ Add side-by-side image display with difference highlighting
    - ✅ Create comparative metrics table showing disease predictions and confidence deltas
    - ✅ Implement image swapping and comparison parameter adjustment
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 9.2 Add difference analysis features
    - ✅ Create delta analysis between two analysis results
    - ✅ Implement disease progression tracking visualization
    - ✅ Add comparison export functionality for reports
    - ✅ Create guidance for single image scenarios with suggestions for second image
    - _Requirements: 8.3, 8.5, 9.3_

- [x] 10. History Management System
  - [x] 10.1 Create history storage and display
    - ✅ Implement HistoryManager class with JSON-based analysis history storage
    - ✅ Create searchable thumbnail grid view of past analyses
    - ✅ Add filtering by date, model type, and disease label
    - ✅ Implement analysis metadata tracking (timestamp, confidence, model version)
    - _Requirements: 9.1, 9.2, 9.4_

  - [x] 10.2 Add export and management features
    - ✅ Create CSV and PDF export functionality for analysis reports
    - ✅ Implement history search with text-based filtering
    - ✅ Add history clearing and selective deletion options
    - ✅ Create guidance display for users with no analysis history
    - _Requirements: 9.3, 9.5_

- [x] 11. Settings and Configuration System
  - [x] 11.1 Implement user preferences
    - ✅ Create Settings page with theme selection (light/dark/system) and persistence
    - ✅ Add language selection and unit preferences (metric/imperial)
    - ✅ Implement model switching interface for different vision, audio, and text models
    - ✅ Create preference storage in st.session_state with session persistence
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 11.2 Add configuration management
    - ✅ Implement immediate settings application without restart requirement
    - ✅ Create settings validation and error handling
    - ✅ Add settings export/import functionality for user profiles
    - ✅ Create settings reset to defaults option
    - _Requirements: 10.5, 14.1, 14.4_

- [x] 12. ADHD-Friendly Design Implementation
  - [x] 12.1 Create cognitive accessibility features
    - ✅ Implement big headings with emoji/icons for clear section identification
    - ✅ Add short sentences and bullet points throughout the interface
    - ✅ Create Simple/Expert toggle for interface complexity management
    - ✅ Implement clear visual hierarchy with consistent spacing and typography
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 12.2 Add progress and feedback systems
    - ✅ Create clear progress indicators and status updates for all processing
    - ✅ Implement prominent workflow prioritization for common tasks
    - ✅ Add visual feedback for all user interactions and state changes
    - ✅ Create distraction-free focused modes for analysis tasks
    - _Requirements: 11.4, 11.5, 13.4_

- [x] 13. Accessibility and Mobile Optimization
  - [x] 13.1 Implement accessibility compliance
    - ✅ Add full keyboard navigation support with proper tab order
    - ✅ Implement ARIA labels and alt text for all images and interactive elements
    - ✅ Create captions and data tables for charts to support screen readers
    - ✅ Ensure WCAG AA compliance standards throughout the application
    - _Requirements: 12.1, 12.2, 12.3, 12.5_

  - [x] 13.2 Add mobile-specific optimizations
    - ✅ Implement touch-friendly interface elements with minimum 44px touch targets
    - ✅ Add mobile gesture support (swipe, pinch-to-zoom) for image viewing
    - ✅ Create mobile-optimized input methods and keyboard handling
    - ✅ Implement responsive typography and spacing for mobile devices
    - _Requirements: 12.4, 3.4, 3.5_

- [x] 14. Performance and Caching System
  - [x] 14.1 Implement model caching and optimization
    - ✅ Create model loading with `@st.cache_resource` for VisionAdapter, AudioAdapter, TextAdapter
    - ✅ Implement lazy loading for models to improve startup performance
    - ✅ Add model cache management with memory usage monitoring
    - ✅ Create fallback mechanisms when models fail to load
    - ✅ Use proper caching pattern with `@st.cache_resource`
    - ✅ Apple Silicon: Use MPS backend when available
    - _Requirements: 13.1, 17.1, 17.2, 17.5_

  - [x] 14.2 Add performance monitoring and optimization
    - ✅ Implement efficient state management to minimize Streamlit reruns using `st.session_state`
    - ✅ Create batch processing support with queued progress indicators
    - ✅ Add performance metrics tracking and display for processing times
    - ✅ Implement cancellation support for long-running operations
    - ✅ Proper state management, avoid unnecessary reruns
    - ✅ Use `tempfile` for temporary storage, clean up immediately
    - _Requirements: 13.2, 13.3, 13.4, 13.5_

- [x] 15. Error Handling and User Feedback
  - [x] 15.1 Create comprehensive error handling
    - ✅ Implement friendly error messages using st.toast for non-blocking alerts
    - ✅ Add specific validation guidance for input issues (resize, format conversion)
    - ✅ Create retry mechanisms and alternative approaches for processing failures
    - ✅ Ensure application stability without crashes during error conditions
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [x] 15.2 Add fallback and recovery systems
    - ✅ Create fallback functionality for critical errors
    - ✅ Implement graceful degradation when components fail
    - ✅ Add error logging and diagnostic information for troubleshooting
    - ✅ Create user-friendly error recovery workflows
    - _Requirements: 14.5, 16.3, 17.5_

- [x] 16. Privacy and Security Implementation
  - [x] 16.1 Add privacy interface and compliance
    - ✅ Create clear privacy disclaimers about local processing throughout the UI
    - ✅ Implement confirmation displays for temporary file deletion after audio processing
    - ✅ Add comprehensive privacy information and GDPR compliance to Guide page
    - ✅ Create confirmation messages that no data is sent to external services
    - ✅ Display clear local-only processing confirmations
    - ✅ No external API calls, all processing local-only
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 16.2 Implement offline-first architecture compliance
    - ✅ Ensure all model loading uses local files without external API calls
    - ✅ Create proper temporary file cleanup with immediate deletion after processing
    - ✅ Add offline capability verification and status indicators
    - ✅ Implement detailed information display about offline-first operation
    - ✅ All adapters must use local models only (ResNet50, Whisper-tiny, DistilBERT)
    - ✅ Use `tempfile` module, never persist user data beyond session
    - ✅ Model paths: `data/models/` directory with proper checkpoint validation
    - _Requirements: 15.5, 16.1, 16.2, 16.4_

- [ ] 17. Multi-Page Architecture Implementation
  - [ ] 17.1 Create main app.py with navigation
    - Implement main app.py using st.navigation() for Home, Compare, History, Guide, Settings pages
    - Create pages/ directory structure with individual page modules
    - Integrate existing mobile components into multi-page architecture
    - Add consistent header and navigation across all pages
    - **Current Status**: Need to convert single-page mobile app to multi-page structure
    - _Requirements: 1.1, 1.3, 1.4_

  - [ ] 17.2 Migrate existing components to pages
    - Move mobile image analysis to pages/home.py
    - Create pages/compare.py using existing comparison components
    - Implement pages/history.py with mobile history manager
    - Create pages/guide.py with privacy and usage information
    - Build pages/settings.py with mobile settings components
    - **Implementation**: Reuse existing mobile components in new page structure
    - _Requirements: All page-specific requirements_

- [ ] 18. Enhanced Chat Interface Integration
  - [ ] 18.1 Implement chat interface across pages
    - Integrate mobile chat interface into home page
    - Add chat history persistence across page navigation
    - Implement context-aware responses based on current page
    - Create chat export functionality for history page
    - **Current Status**: Mobile chat exists, needs multi-page integration
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 18.2 Add multimodal chat capabilities
    - Connect chat interface to vision, audio, and text adapters
    - Implement image + text query combinations
    - Add voice transcription integration with chat
    - Create analysis result integration with chat responses
    - **Implementation**: Use existing adapter integration from mobile components
    - _Requirements: Multimodal interaction requirements_

- [ ] 19. Final Integration and Testing
  - [ ] 19.1 Complete system integration
    - Test all pages with existing adapter integrations
    - Validate navigation flow and state persistence
    - Ensure mobile responsiveness across all pages
    - Test offline functionality and error handling
    - **Focus**: Leverage existing mobile testing framework
    - _Requirements: All integration requirements_

  - [ ] 19.2 Performance optimization and polish
    - Optimize page loading with existing performance components
    - Add loading animations and transitions between pages
    - Implement accessibility features across all pages
    - Create comprehensive user testing scenarios
    - **Implementation**: Use existing mobile performance optimizations
    - _Requirements: Performance and accessibility requirements_

## Current Implementation Status

### ✅ Completed Components (Available for Reuse)
- **Mobile Components**: Comprehensive mobile UI components in `src/ui/components/mobile_*`
- **Core Adapters**: VisionAdapter, AudioAdapter, TextAdapter with local model support
- **Mobile SPA**: Full single-page application in `mobile_spa_app.py`
- **Styling**: Mobile-first CSS framework in `assets/mobile_styles.css`
- **Performance**: Mobile performance optimization and caching systems
- **Testing**: Mobile testing framework and component validation

### 🔄 Needs Adaptation
- **Multi-Page Architecture**: Convert single-page mobile app to multi-page navigation
- **Page Structure**: Create pages/ directory with individual page modules
- **Navigation Integration**: Implement st.navigation() with existing mobile components
- **State Management**: Adapt mobile state management for multi-page flow
- **Component Integration**: Integrate existing mobile components into page-based structure

### 📋 Implementation Strategy
The redesign should **reuse existing mobile components** and **adapt them for multi-page architecture** rather than rebuilding from scratch. Focus on:
1. Creating pages/ directory structure
2. Implementing main app.py with st.navigation()
3. Migrating existing mobile components to appropriate pages
4. Ensuring state persistence across page navigation
5. Maintaining existing adapter integrations and performance optimizations

## Implementation Standards

### Mandatory Error Handling Pattern

All implementations must use this exact pattern:

```python
try:
    result = adapter.process(input_data)
except Exception as e:
    logger.warning(f"Adapter failed: {e}")
    return fallback_response()  # Never crash the UI
```

### Required Input Validation

- Images: Max 200MB, formats `["jpg", "jpeg", "png"]`
- Audio: 1-60 seconds, formats `["wav", "mp3"]`
- Text: Max 1000 characters for chat input
- Use `st.session_state` for conversation history

### Mandatory File Operations

- Use `pathlib.Path` for all file operations
- Use `tempfile` for temporary storage, clean up immediately
- Delete temp files (`tmp_audio`, `mic.wav`) after processing
- Never persist user data beyond session scope

### Required Code Style

- Type annotations for all public methods
- Line length: 100 characters maximum
- Double quotes for strings
- Import order: First-party (`src`) before third-party
- Use `logger.info()` instead of `print()` in production
- Specific exception handling: `except FileNotFoundError:` not `except:`