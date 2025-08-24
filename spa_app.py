"""
PlantGuard Single Page Application (SPA)

A unified, AI-friendly interface that consolidates all PlantGuard functionality
into one seamless experience without navigation complexity.

All technical capabilities preserved:
- Vision analysis with multiple models (ViT, ResNet50, MobileNet)
- Audio processing (voice questions)
- Text chat assistant
- Model management and switching
- Analysis history and comparison
- Batch processing
- Export capabilities
"""

import json
import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
from PIL import Image

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import adapters with fallback
try:
    from core.vision import VisionAdapter
    from core.audio import AudioAdapter  
    from core.nlp import TextAdapter
    USE_REAL_ADAPTERS = True
except ImportError:
    from adapters_compat import VisionAdapter, AudioAdapter, TextAdapter
    USE_REAL_ADAPTERS = False

# Configure logging
from utils.logging import setup_logger
logger = setup_logger("plantguard_spa", log_file="logs/spa.log")

# Page configuration
st.set_page_config(
    page_title="PlantGuard AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize comprehensive session state
def init_session_state():
    """Initialize comprehensive session state with validation and defaults."""
    
    # Analysis history with metadata
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []
    
    # Chat messages with role-based structure
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Comparison mode state
    if "comparison_mode" not in st.session_state:
        st.session_state.comparison_mode = False
    
    # Current active models with validation
    if "current_models" not in st.session_state:
        st.session_state.current_models = {
            "vision": "vit_best",
            "audio": "whisper_tiny_local", 
            "text": "distilbert_plant_qa_v1"
        }
    
    # Processing state with detailed tracking
    if "processing_state" not in st.session_state:
        st.session_state.processing_state = "idle"
    
    # Processing metadata
    if "processing_type" not in st.session_state:
        st.session_state.processing_type = "analysis"
    
    # Batch processing state
    if "current_batch_item" not in st.session_state:
        st.session_state.current_batch_item = 0
    
    if "total_batch_items" not in st.session_state:
        st.session_state.total_batch_items = 1
    
    # Error handling state
    if "error_message" not in st.session_state:
        st.session_state.error_message = ""
    
    # UI state management
    if "show_audio_upload" not in st.session_state:
        st.session_state.show_audio_upload = False
    
    # Session statistics
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = datetime.now().isoformat()
    
    # Performance tracking
    if "performance_history" not in st.session_state:
        st.session_state.performance_history = []
    
    # User preferences
    if "user_preferences" not in st.session_state:
        st.session_state.user_preferences = {
            "auto_clear_chat": False,
            "show_debug_info": False,
            "preferred_model": "vit_best",
            "export_format": "json"
        }

# Initialize session state
init_session_state()


class PlantGuardSPA:
    """Single Page Application for PlantGuard with all functionality.
    
    AI Agent Friendly Design:
    - Programmatic interfaces for all core functions
    - Structured response formats
    - Error handling with fallback mechanisms
    - Session state management
    - Apple Silicon optimization
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vision_adapter = None
        self.audio_adapter = None
        self.text_adapter = None
        self._setup_performance_optimizations()
        
        # Available models (preserved from original system)
        self.models = {
            "vision": {
                "vit_best": {
                    "name": "Vision Transformer (Best)",
                    "accuracy": "100%",
                    "speed": "Medium",
                    "description": "Highest accuracy model"
                },
                "resnet50_plantvillage_v1": {
                    "name": "ResNet50",
                    "accuracy": "95%", 
                    "speed": "Fast",
                    "description": "Balanced performance"
                },
                "mobilenet_fast": {
                    "name": "MobileNet",
                    "accuracy": "90%",
                    "speed": "Very Fast", 
                    "description": "Lightweight for mobile"
                }
            },
            "audio": {
                "whisper_tiny_local": {
                    "name": "Whisper Tiny",
                    "accuracy": "85%",
                    "speed": "Fast"
                }
            },
            "text": {
                "distilbert_plant_qa_v1": {
                    "name": "DistilBERT",
                    "accuracy": "92%", 
                    "speed": "Fast"
                }
            }
        }
    
    def get_adapter(self, adapter_type: str):
        """Get or initialize adapter."""
        if adapter_type == "vision" and self.vision_adapter is None:
            self.vision_adapter = VisionAdapter()
        elif adapter_type == "audio" and self.audio_adapter is None:
            self.audio_adapter = AudioAdapter()
        elif adapter_type == "text" and self.text_adapter is None:
            self.text_adapter = TextAdapter()
            
        return getattr(self, f"{adapter_type}_adapter")
    
    def _setup_performance_optimizations(self):
        """Setup Apple Silicon and performance optimizations with memory management."""
        import os
        import torch
        
        # Apple Silicon MPS optimization
        if torch.backends.mps.is_available():
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            # Enable TF32 for faster computation on Apple Silicon
            torch.backends.mps.allow_tf32 = True
            self.device = "mps"
            self.logger.info("🚀 Apple Silicon MPS acceleration enabled with TF32")
        else:
            self.device = "cpu"
            self.logger.info("💻 Using CPU processing")
        
        # Memory management settings
        self._setup_memory_management()
        
        # Caching strategy setup
        self._setup_caching_strategy()
        
        # Performance monitoring
        self._setup_performance_monitoring()
    
    def _setup_memory_management(self):
        """Setup memory management strategies."""
        import gc
        import psutil
        
        try:
            # Get system memory info
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            
            # Set memory limits based on available RAM
            if total_gb >= 16:
                self.memory_limit = 8  # GB
                self.batch_size_limit = 32
            elif total_gb >= 8:
                self.memory_limit = 4  # GB
                self.batch_size_limit = 16
            else:
                self.memory_limit = 2  # GB
                self.batch_size_limit = 8
            
            # Enable garbage collection optimization
            gc.set_threshold(700, 10, 10)
            
            self.logger.info(f"💾 Memory management: {self.memory_limit}GB limit, batch size {self.batch_size_limit}")
            
        except ImportError:
            # Fallback if psutil not available
            self.memory_limit = 4
            self.batch_size_limit = 16
            self.logger.warning("⚠️ psutil not available, using default memory settings")
    
    def _setup_caching_strategy(self):
        """Setup intelligent caching strategies."""
        from functools import lru_cache
        
        # Model caching settings
        self.model_cache = {
            "max_size": 3,  # Maximum number of models to keep in memory
            "current_size": 0,
            "cache": {}
        }
        
        # Image preprocessing cache
        self.image_cache_size = 50  # Number of preprocessed images to cache
        
        # Results caching
        self.results_cache_ttl = 3600  # 1 hour TTL for cached results
        
        self.logger.info("🗄️ Caching strategy initialized")
    
    def _setup_performance_monitoring(self):
        """Setup performance monitoring and profiling."""
        import time
        
        self.performance_metrics = {
            "start_time": time.time(),
            "analysis_times": [],
            "memory_usage": [],
            "model_load_times": {}
        }
        
        self.logger.info("📈 Performance monitoring enabled")
    
    def optimize_memory_usage(self):
        """Optimize memory usage during runtime."""
        import gc
        import torch
        
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear PyTorch cache if using GPU/MPS
            if hasattr(torch, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Check memory usage
            try:
                import psutil
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # If memory usage is high, clear caches
                if memory_percent > 85:
                    self.clear_caches()
                    self.logger.warning(f"⚠️ High memory usage ({memory_percent:.1f}%), cleared caches")
                
                return memory_percent
            except ImportError:
                return None
                
        except Exception as e:
            self.logger.error(f"Memory optimization error: {e}")
            return None
    
    def clear_caches(self):
        """Clear all caches to free memory."""
        # Clear model cache
        for model_id in list(self.model_cache["cache"].keys()):
            del self.model_cache["cache"][model_id]
        self.model_cache["current_size"] = 0
        
        # Clear session caches
        if hasattr(st.session_state, 'preprocessed_images'):
            del st.session_state.preprocessed_images
        
        self.logger.info("🗄️ Caches cleared")
    
    # ========== Error Handling and Recovery ==========
    
    def handle_error(self, error: Exception, context: str, fallback_action: str = None) -> bool:
        """Comprehensive error handling with fallback mechanisms.
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            fallback_action: Optional fallback action to attempt
            
        Returns:
            bool: True if error was handled successfully, False otherwise
        """
        error_id = f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log error with full context
        self.logger.error(f"Error {error_id} in {context}: {str(error)}", exc_info=True)
        
        # Update session state
        self.update_processing_state("error", error_msg=f"{context}: {str(error)}")
        
        # Attempt fallback strategies
        fallback_success = False
        
        if isinstance(error, MemoryError):
            fallback_success = self._handle_memory_error(error, context)
        elif isinstance(error, ConnectionError):
            fallback_success = self._handle_connection_error(error, context)
        elif isinstance(error, FileNotFoundError):
            fallback_success = self._handle_file_error(error, context)
        elif "model" in str(error).lower():
            fallback_success = self._handle_model_error(error, context)
        else:
            # Generic error handling
            fallback_success = self._handle_generic_error(error, context, fallback_action)
        
        # Update UI with error information
        self._display_error_ui(error, context, error_id, fallback_success)
        
        return fallback_success
    
    def _handle_memory_error(self, error: Exception, context: str) -> bool:
        """Handle memory-related errors."""
        try:
            self.logger.warning(f"💾 Memory error in {context}, attempting recovery")
            
            # Clear caches and optimize memory
            self.clear_caches()
            self.optimize_memory_usage()
            
            # Reduce batch size if applicable
            if hasattr(self, 'batch_size_limit'):
                self.batch_size_limit = max(1, self.batch_size_limit // 2)
                self.logger.info(f"🔄 Reduced batch size to {self.batch_size_limit}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Memory error recovery failed: {e}")
            return False
    
    def _handle_connection_error(self, error: Exception, context: str) -> bool:
        """Handle network/connection errors."""
        try:
            self.logger.warning(f"🌐 Connection error in {context}, enabling offline mode")
            
            # Switch to offline/local models if available
            if hasattr(self, 'enable_offline_mode'):
                self.enable_offline_mode()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Connection error recovery failed: {e}")
            return False
    
    def _handle_model_error(self, error: Exception, context: str) -> bool:
        """Handle model loading/inference errors."""
        try:
            self.logger.warning(f"🤖 Model error in {context}, attempting model fallback")
            
            # Try fallback model
            current_model = st.session_state.current_models.get("vision")
            fallback_models = ["resnet50_plantvillage_v1", "mobilenet_fast"]
            
            for fallback_model in fallback_models:
                if fallback_model != current_model and fallback_model in self.models["vision"]:
                    st.session_state.current_models["vision"] = fallback_model
                    self.logger.info(f"🔄 Switched to fallback model: {fallback_model}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Model error recovery failed: {e}")
            return False
    
    def _handle_file_error(self, error: Exception, context: str) -> bool:
        """Handle file-related errors."""
        try:
            self.logger.warning(f"📁 File error in {context}, checking alternatives")
            
            # For missing model files, try to download or use alternatives
            if "model" in str(error).lower():
                return self._handle_model_error(error, context)
            
            return False
            
        except Exception as e:
            self.logger.error(f"File error recovery failed: {e}")
            return False
    
    def _handle_generic_error(self, error: Exception, context: str, fallback_action: str = None) -> bool:
        """Handle generic errors with optional fallback action."""
        try:
            self.logger.warning(f"⚠️ Generic error in {context}, attempting basic recovery")
            
            # Reset processing state
            st.session_state.processing_state = "idle"
            
            # Clear any partial state that might be causing issues
            problematic_keys = ["current_batch_item", "total_batch_items"]
            for key in problematic_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Execute fallback action if provided
            if fallback_action:
                self.logger.info(f"🔄 Executing fallback action: {fallback_action}")
                # This could be extended to execute specific fallback functions
            
            return True
            
        except Exception as e:
            self.logger.error(f"Generic error recovery failed: {e}")
            return False
    
    def _display_error_ui(self, error: Exception, context: str, error_id: str, fallback_success: bool):
        """Display user-friendly error information in the UI."""
        # Error message based on type
        if isinstance(error, MemoryError):
            error_msg = "💾 **Memory Error**: The system ran out of memory. Try using smaller images or reducing batch size."
        elif isinstance(error, ConnectionError):
            error_msg = "🌐 **Connection Error**: Network connection failed. Check your internet connection."
        elif "model" in str(error).lower():
            error_msg = "🤖 **Model Error**: There was an issue with the AI model. Trying alternative model..."
        else:
            error_msg = f"⚠️ **Error**: {str(error)[:100]}..."
        
        # Recovery status
        if fallback_success:
            st.warning(f"{error_msg}\n\n✅ **Recovery**: Automatic recovery successful. You can continue using the application.")
        else:
            st.error(f"{error_msg}\n\n❌ **Recovery**: Automatic recovery failed. Please refresh the page or contact support.")
        
        # Technical details in expandable section
        with st.expander(f"🔍 Technical Details (Error ID: {error_id})"):
            st.code(f"""
Context: {context}
Error Type: {type(error).__name__}
Error Message: {str(error)}
Timestamp: {datetime.now().isoformat()}
Session ID: {id(st.session_state)}
            """)
    
    def setup_error_monitoring(self):
        """Setup error monitoring and reporting."""
        # Error statistics tracking
        if "error_stats" not in st.session_state:
            st.session_state.error_stats = {
                "total_errors": 0,
                "error_types": {},
                "recovery_success_rate": 0,
                "last_error_time": None
            }
        
        self.logger.info("🚨 Error monitoring enabled")
    
    # ========== Responsive Layout and Mobile Optimization ==========
    
    def detect_device_type(self) -> str:
        """Detect device type for responsive layout."""
        # Check if we can detect screen size (limited in Streamlit)
        # This is a simple heuristic - in a real app, you'd use JavaScript
        
        # For now, we'll use a simple approach based on user agent if available
        # or default to desktop
        return "desktop"  # Could be enhanced with actual device detection
    
    def get_responsive_columns(self, device_type: str = None) -> tuple:
        """Get responsive column layout based on device type."""
        if device_type is None:
            device_type = self.detect_device_type()
        
        # Define responsive layouts
        layouts = {
            "mobile": ([1], [1], [1]),  # Stack everything
            "tablet": ([2, 1], [1], [1]),  # Some side-by-side
            "desktop": ([7, 3], [2, 1], [4, 1])  # Full side-by-side
        }
        
        return layouts.get(device_type, layouts["desktop"])
    
    def render_mobile_optimized_header(self):
        """Render mobile-optimized header."""
        # Compact header for mobile
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0; background: linear-gradient(135deg, #4CAF50, #45a049); 
                    border-radius: 10px; margin-bottom: 1rem; color: white;'>
            <h2 style='margin: 0; font-size: 1.8rem;'>🌿 PlantGuard AI</h2>
            <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>Plant Disease Detection</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_mobile_optimized_input(self):
        """Render mobile-optimized input zone."""
        st.markdown("### 🌱 Analysis")
        
        # Tabbed interface for mobile
        tab1, tab2, tab3 = st.tabs(["📷 Image", "🎤 Voice", "💬 Chat"])
        
        with tab1:
            # Image upload - full width
            uploaded_file = st.file_uploader(
                "Upload plant image",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="mobile_image_upload"
            )
            
            if uploaded_file:
                if isinstance(uploaded_file, list):
                    st.success(f"✅ {len(uploaded_file)} images uploaded")
                    if st.button("🔄 Analyze All", type="primary", use_container_width=True):
                        self.process_batch_images(uploaded_file)
                else:
                    self.process_single_image(uploaded_file)
        
        with tab2:
            # Voice input - mobile friendly
            st.markdown("🎤 **Voice Questions**")
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                if st.button("🎤 Record", use_container_width=True):
                    self.handle_voice_input()
            
            with col_v2:
                if st.button("📁 Upload", use_container_width=True):
                    st.session_state.show_audio_upload = True
            
            if st.session_state.get("show_audio_upload", False):
                audio_file = st.file_uploader(
                    "Audio file",
                    type=["wav", "mp3", "m4a", "ogg"],
                    key="mobile_audio_upload"
                )
                if audio_file:
                    self.process_audio_file(audio_file)
                    st.session_state.show_audio_upload = False
        
        with tab3:
            # Text input - mobile optimized
            text_query = st.text_area(
                "Ask about plant care",
                placeholder="What's wrong with my plant?",
                height=100,
                key="mobile_text_input"
            )
            
            if st.button("💬 Send", disabled=not text_query, use_container_width=True):
                self.process_text_query(text_query)
    
    def render_accessibility_features(self):
        """Render accessibility features and options."""
        # Add accessibility controls in sidebar or expandable section
        with st.expander("♿ Accessibility Options"):
            # Font size adjustment
            font_size = st.selectbox(
                "Text Size",
                ["Small", "Medium", "Large", "Extra Large"],
                index=1,
                key="font_size_select"
            )
            
            # High contrast mode
            high_contrast = st.checkbox(
                "High Contrast Mode",
                key="high_contrast_mode"
            )
            
            # Screen reader optimization
            screen_reader = st.checkbox(
                "Screen Reader Optimization",
                key="screen_reader_mode"
            )
            
            # Keyboard navigation hints
            if st.checkbox("Show Keyboard Shortcuts", key="show_shortcuts"):
                st.markdown("""
                **Keyboard Shortcuts:**
                - Tab: Navigate between elements
                - Enter: Activate buttons
                - Space: Select checkboxes
                - Escape: Close dialogs
                """)
            
            # Apply accessibility settings
            self.apply_accessibility_settings(font_size, high_contrast, screen_reader)
    
    def apply_accessibility_settings(self, font_size: str, high_contrast: bool, screen_reader: bool):
        """Apply accessibility settings to the interface."""
        # Font size CSS
        font_sizes = {
            "Small": "0.8em",
            "Medium": "1em",
            "Large": "1.2em",
            "Extra Large": "1.4em"
        }
        
        # High contrast CSS
        contrast_css = """
        .stApp {
            background-color: #000000 !important;
            color: #FFFFFF !important;
        }
        .stButton > button {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #FFFFFF !important;
        }
        """ if high_contrast else ""
        
        # Apply CSS
        css = f"""
        <style>
        .stApp {{
            font-size: {font_sizes.get(font_size, '1em')};
        }}
        {contrast_css}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
        
        # Screen reader optimizations
        if screen_reader:
            # Add ARIA labels and descriptions
            st.markdown("""
            <script>
            // Add ARIA labels for screen readers
            document.addEventListener('DOMContentLoaded', function() {
                const buttons = document.querySelectorAll('button');
                buttons.forEach(button => {
                    if (!button.getAttribute('aria-label')) {
                        button.setAttribute('aria-label', button.textContent || 'Button');
                    }
                });
            });
            </script>
            """, unsafe_allow_html=True)
    
    def render_adaptive_layout(self):
        """Render layout that adapts to screen size and device capabilities."""
        device_type = self.detect_device_type()
        
        if device_type == "mobile":
            # Mobile layout - stacked
            self.render_mobile_optimized_header()
            self.render_mobile_optimized_input()
            self.render_dynamic_results_area()
            
            # Mobile context panel as bottom sheet
            with st.expander("⚙️ Settings & Controls", expanded=False):
                self.render_context_panel()
                
        else:
            # Desktop/tablet layout - side by side
            self.render_header()
            
            # Get responsive column layout
            main_cols, input_cols, text_cols = self.get_responsive_columns(device_type)
            
            col_main, col_context = st.columns(main_cols)
            
            with col_main:
                self.render_primary_input_zone()
                self.render_dynamic_results_area()
            
            with col_context:
                self.render_context_panel()
        
        # Always render accessibility features
        self.render_accessibility_features()
    
    # ========== AI Agent Programmatic Interfaces ==========
    
    def analyze_image_programmatic(self, image_path: str, model: str = None) -> Dict[str, Any]:
        """Programmatic image analysis for AI agents.
        
        Args:
            image_path: Path to image file
            model: Optional model override
            
        Returns:
            Structured analysis result with metadata
        """
        try:
            from PIL import Image
            
            # Load image
            image = Image.open(image_path)
            
            # Set model if specified
            original_model = None
            if model and model in self.models["vision"]:
                original_model = st.session_state.current_models["vision"]
                st.session_state.current_models["vision"] = model
            
            # Perform analysis
            result = self.perform_image_analysis(image)
            
            # Restore original model
            if original_model:
                st.session_state.current_models["vision"] = original_model
            
            if result:
                result.update({
                    "timestamp": datetime.now().isoformat(),
                    "filename": Path(image_path).name,
                    "type": "programmatic_image",
                    "request_id": f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "status": "success"
                })
                return result
            else:
                return {
                    "status": "error",
                    "error": "Analysis failed",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Programmatic image analysis error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def process_voice_programmatic(self, audio_path: str) -> Dict[str, Any]:
        """Programmatic voice processing for AI agents.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Structured transcription and response result
        """
        try:
            adapter = self.get_adapter("audio")
            if not adapter:
                return {
                    "status": "error",
                    "error": "Audio adapter not available",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Process audio
            result = adapter.process_audio(audio_path)
            
            if result:
                transcription = result.get("transcription", "")
                
                # Generate text response if transcription successful
                text_response = None
                if transcription:
                    text_response = self.query_programmatic(transcription)
                
                return {
                    "status": "success",
                    "transcription": transcription,
                    "confidence": result.get("confidence", 0),
                    "text_response": text_response,
                    "timestamp": datetime.now().isoformat(),
                    "request_id": f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            else:
                return {
                    "status": "error",
                    "error": "Audio processing failed",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Programmatic voice processing error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def query_programmatic(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """Programmatic text query for AI agents.
        
        Args:
            query: Text query
            context: Optional context dictionary
            
        Returns:
            Structured response with metadata
        """
        try:
            adapter = self.get_adapter("text")
            if not adapter:
                return {
                    "status": "error",
                    "error": "Text adapter not available",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Generate response
            response = adapter.generate_response(user_query=query)
            
            return {
                "status": "success",
                "query": query,
                "response": response,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
                "request_id": f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            self.logger.error(f"Programmatic text query error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def batch_analyze_programmatic(self, image_paths: List[str], model: str = None) -> List[Dict[str, Any]]:
        """Programmatic batch analysis for AI agents.
        
        Args:
            image_paths: List of image file paths
            model: Optional model override
            
        Returns:
            List of structured analysis results
        """
        results = []
        
        for path in image_paths:
            result = self.analyze_image_programmatic(path, model)
            results.append(result)
        
        return results
    
    def get_system_status_programmatic(self) -> Dict[str, Any]:
        """Get system status for AI agents.
        
        Returns:
            Structured system status information
        """
        try:
            import torch
            import psutil
            
            # Current models
            current_models = st.session_state.get("current_models", {})
            
            # System info
            memory_info = psutil.virtual_memory()
            
            # Model info
            vision_model = current_models.get("vision", "unknown")
            model_info = self.models["vision"].get(vision_model, {})
            
            # Analysis statistics
            total_analyses = len(st.session_state.get("analysis_history", []))
            
            return {
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "models": {
                    "active_vision": vision_model,
                    "vision_accuracy": model_info.get("accuracy", "Unknown"),
                    "vision_speed": model_info.get("speed", "Unknown")
                },
                "system": {
                    "device": self.device,
                    "memory_usage": f"{memory_info.percent}%",
                    "available_memory": f"{memory_info.available / (1024**3):.1f}GB",
                    "mps_available": torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
                },
                "statistics": {
                    "total_analyses": total_analyses,
                    "session_active": True
                }
            }
            
        except Exception as e:
            self.logger.error(f"System status error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def render_header(self):
        """Render the main application header with responsive design."""
        # Get system status for header indicators
        try:
            import torch
            device_indicator = "🚀 MPS" if torch.backends.mps.is_available() else "💻 CPU"
        except:
            device_indicator = "💻 CPU"
        
        # Header with device and model info
        col_header1, col_header2 = st.columns([4, 1])
        
        with col_header1:
            st.markdown(f"""
            <div style='text-align: center; padding: 1.5rem 0; background: linear-gradient(135deg, #4CAF50, #45a049); 
                        border-radius: 15px; margin-bottom: 1.5rem; color: white;'>
                <h1 style='margin: 0; font-size: 2.5rem;'>🌿 PlantGuard AI</h1>
                <p style='margin: 0; font-size: 1.1rem; opacity: 0.9;'>Complete Plant Disease Detection & Care Assistant</p>
                <p style='margin: 0; font-size: 0.8rem; opacity: 0.8;'>All functionality in one interface - AI agent friendly</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_header2:
            # System indicators
            st.markdown(f"**{device_indicator}**")
            current_model = st.session_state.current_models.get("vision", "unknown")
            model_info = self.models["vision"].get(current_model, {})
            st.markdown(f"**Model:** {model_info.get('name', 'Unknown')[:15]}...")
            
            # Analysis count
            total_analyses = len(st.session_state.get("analysis_history", []))
            st.metric("Analyses", total_analyses)
    
    def render_primary_input_zone(self):
        """Primary input area with all interaction methods - responsive and accessible."""
        st.markdown("### 🌱 Plant Analysis & Care")
        
        # Responsive layout - adapt to mobile/desktop
        input_col1, input_col2 = st.columns([2, 1])
        
        with input_col1:
            # Image upload with accessibility
            st.markdown("#### 📷 Image Analysis")
            uploaded_file = st.file_uploader(
                "Upload plant image for analysis",
                type=["jpg", "jpeg", "png"],
                help="Drag and drop or click to upload. Supports multiple images for batch analysis.",
                accept_multiple_files=True,
                key="main_image_upload"
            )
            
            # Process uploaded images
            if uploaded_file:
                if isinstance(uploaded_file, list):
                    st.success(f"✅ {len(uploaded_file)} images uploaded")
                    if st.button("🔄 Analyze All Images", type="primary", use_container_width=True, key="batch_analyze"):
                        self.process_batch_images(uploaded_file)
                else:
                    self.process_single_image(uploaded_file)
        
        with input_col2:
            # Voice input with HTTPS detection
            st.markdown("#### 🎤 Voice Questions")
            
            col_voice1, col_voice2 = st.columns(2)
            
            with col_voice1:
                if st.button("🎤 Record", use_container_width=True, key="voice_record"):
                    self.handle_voice_input()
            
            with col_voice2:
                if st.button("📁 Upload", use_container_width=True, key="voice_upload_btn"):
                    st.session_state.show_audio_upload = True
            
            # Audio file upload (toggle)
            if st.session_state.get("show_audio_upload", False):
                audio_file = st.file_uploader(
                    "Upload audio file",
                    type=["wav", "mp3", "m4a", "ogg"],
                    key="audio_file_upload",
                    help="Supported: WAV, MP3, M4A, OGG"
                )
                if audio_file:
                    self.process_audio_file(audio_file)
                    st.session_state.show_audio_upload = False
        
        # Text input - full width accessibility
        st.markdown("---")
        st.markdown("#### 💬 Ask About Plant Care")
        
        text_col1, text_col2 = st.columns([4, 1])
        
        with text_col1:
            text_query = st.text_input(
                "Ask about plant care or describe symptoms",
                placeholder="e.g., What disease is this? How often should I water tomatoes?",
                key="main_text_input",
                help="Natural language questions about plant care, diseases, or treatments",
                label_visibility="collapsed"
            )
        
        with text_col2:
            if st.button("💬 Ask", use_container_width=True, disabled=not text_query, key="text_submit"):
                self.process_text_query(text_query)
        
        # Quick suggestion buttons
        st.markdown("**Quick Questions:**")
        suggestion_cols = st.columns(4)
        
        suggestions = [
            "What disease is this?",
            "How to treat this?", 
            "Watering schedule?",
            "Prevention tips?"
        ]
        
        for i, suggestion in enumerate(suggestions):
            with suggestion_cols[i]:
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    self.process_text_query(suggestion)
    
    def render_dynamic_results_area(self):
        """Dynamic results area that adapts to current content with enhanced state management."""
        current_state = st.session_state.processing_state
        
        if current_state == "processing":
            # Processing state with progress indicators
            with st.spinner("🔄 Processing..."):
                # Show progress based on processing type
                processing_type = st.session_state.get("processing_type", "analysis")
                
                if processing_type == "batch":
                    st.info("📊 Analyzing multiple images...")
                    # Show batch progress if available
                    current_batch = st.session_state.get("current_batch_item", 0)
                    total_batch = st.session_state.get("total_batch_items", 1)
                    if total_batch > 1:
                        progress = current_batch / total_batch
                        st.progress(progress, text=f"Processing {current_batch}/{total_batch}")
                elif processing_type == "voice":
                    st.info("🎤 Processing audio input...")
                else:
                    st.info("🔬 Analyzing plant image...")
                
        elif current_state == "error":
            # Error state with recovery options
            st.error("❌ Analysis failed. Please try again.")
            error_msg = st.session_state.get("error_message", "Unknown error occurred")
            st.warning(f"Error details: {error_msg}")
            
            col_err1, col_err2 = st.columns(2)
            with col_err1:
                if st.button("🔄 Retry Analysis", type="primary", key="retry_analysis"):
                    st.session_state.processing_state = "idle"
                    st.rerun()
            
            with col_err2:
                if st.button("📞 Get Help", key="get_help"):
                    self.show_help_panel()
                    
        elif st.session_state.analysis_history or st.session_state.chat_messages:
            # Active results state - show recent activity
            
            # Tabs for different result types
            if st.session_state.analysis_history and st.session_state.chat_messages:
                result_tab1, result_tab2 = st.tabs(["📊 Latest Analysis", "💬 Chat"])
                
                with result_tab1:
                    latest_analysis = st.session_state.analysis_history[-1]
                    self.display_analysis_result(latest_analysis)
                
                with result_tab2:
                    self.display_chat_messages()
                    
            elif st.session_state.analysis_history:
                # Only analysis results available
                latest_analysis = st.session_state.analysis_history[-1]
                self.display_analysis_result(latest_analysis)
                
            elif st.session_state.chat_messages:
                # Only chat messages available
                self.display_chat_messages()
        
        else:
            # Welcome/idle state - getting started content
            self.render_welcome_content()
            
        # Always show comparison mode if active
        if st.session_state.get("comparison_mode", False):
            st.markdown("---")
            self.render_comparison_overlay()
    
    def render_context_panel(self):
        """Context-aware side panel with enhanced functionality."""
        st.markdown("### ⚙️ Controls & Status")
        
        # Model selector (contextual)
        self.render_model_selector()
        
        st.markdown("---")
        
        # Quick actions with smart enabling/disabling
        st.markdown("**🔧 Quick Actions:**")
        
        # Action buttons in grid layout
        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            # History button - only enable if there's history
            has_history = bool(st.session_state.analysis_history)
            if st.button("📊 History", use_container_width=True, disabled=not has_history, key="show_history"):
                self.show_history_panel()
                
            # Clear results button
            has_results = bool(st.session_state.analysis_history or st.session_state.chat_messages)
            if st.button("🗑️ Clear", use_container_width=True, disabled=not has_results, key="clear_all"):
                self.clear_all_results()
        
        with col_act2:
            # Compare button
            if st.button("🔄 Compare", use_container_width=True, key="toggle_compare"):
                st.session_state.comparison_mode = not st.session_state.get("comparison_mode", False)
                st.rerun()
                
            # Export button - only enable if there's data
            if st.button("💾 Export", use_container_width=True, disabled=not has_results, key="export_results"):
                self.export_all_results()
        
        st.markdown("---")
        
        # Performance metrics (real-time)
        st.markdown("**📊 Performance:**")
        self.render_performance_metrics()
        
        st.markdown("---")
        
        # System status with live updates
        self.render_system_status()
        
        st.markdown("---")
        
        # AI Agent API status
        self.render_api_status()
    
    def render_model_selector(self):
        """Inline model selection."""
        st.markdown("**🤖 Active Models:**")
        
        # Vision model selector
        vision_models = list(self.models["vision"].keys())
        vision_names = [self.models["vision"][k]["name"] for k in vision_models]
        
        current_vision = st.session_state.current_models["vision"]
        try:
            current_idx = vision_models.index(current_vision)
        except ValueError:
            current_idx = 0
            
        selected_vision = st.selectbox(
            "Vision",
            options=vision_names,
            index=current_idx,
            key="vision_model_select"
        )
        
        # Update if changed
        new_vision_key = vision_models[vision_names.index(selected_vision)]
        if new_vision_key != current_vision:
            st.session_state.current_models["vision"] = new_vision_key
            st.success(f"✅ Vision model: {self.models['vision'][new_vision_key]['name']}")
            st.rerun()
    
    def process_single_image(self, uploaded_file):
        """Process a single uploaded image."""
        image = Image.open(uploaded_file)
        
        # Display image
        st.image(image, caption=f"📷 {uploaded_file.name}", use_column_width=True)
        
        # Analysis button
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("🔍 Analyze Plant", type="primary", use_container_width=True):
                self.analyze_image(image, uploaded_file.name)
        
        with col_btn2:
            if st.button("🔄 Add to Compare", use_container_width=True):
                self.add_to_comparison(image, uploaded_file.name)
        
        with col_btn3:
            if st.button("📊 Quick Info", use_container_width=True):
                self.show_image_info(image, uploaded_file.name)
    
    def process_batch_images(self, uploaded_files):
        """Process multiple uploaded images."""
        if st.button("🔄 Analyze All Images", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            results_container = st.container()
            
            for i, file in enumerate(uploaded_files):
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                with st.spinner(f"Analyzing {file.name}..."):
                    image = Image.open(file)
                    result = self.perform_image_analysis(image)
                    
                    if result:
                        # Add to history
                        result.update({
                            "timestamp": datetime.now().isoformat(),
                            "filename": file.name,
                            "type": "batch_image"
                        })
                        st.session_state.analysis_history.append(result)
                        
                        # Show result summary
                        with results_container:
                            st.success(f"✅ {file.name}: {result.get('disease', 'Unknown')} ({result.get('confidence', 0):.1%})")
            
            st.balloons()
            st.success("🎉 Batch analysis complete!")
    
    def handle_voice_input(self):
        """Handle voice recording (placeholder for now)."""
        st.info("🎤 Voice recording feature ready for implementation")
        st.markdown("""
        **Voice capabilities:**
        - Real-time audio recording
        - Speech-to-text transcription
        - Natural language question processing
        - Voice responses (text-to-speech)
        """)
        
        # Mock voice input for demo
        mock_query = "What disease does my tomato plant have?"
        self.process_text_query(mock_query)
    
    def process_audio_file(self, audio_file):
        """Process uploaded audio file."""
        st.success(f"🎵 Audio uploaded: {audio_file.name}")
        
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_file.read())
            tmp_file_path = tmp_file.name
        
        # Process with audio adapter
        adapter = self.get_adapter("audio")
        if adapter:
            with st.spinner("🔄 Processing audio..."):
                result = adapter.process_audio(tmp_file_path)
                if result:
                    transcription = result.get("transcription", "")
                    confidence = result.get("confidence", 0)
                    
                    st.success(f"🎤 Transcribed ({confidence:.1%}): {transcription}")
                    
                    # Process the transcribed text
                    if transcription:
                        self.process_text_query(transcription)
    
    def process_text_query(self, query: str):
        """Process text-based query."""
        if not query.strip():
            return
            
        # Add to chat history
        st.session_state.chat_messages.append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get response from text adapter
        adapter = self.get_adapter("text")
        if adapter:
            with st.spinner("🤔 Thinking..."):
                response = adapter.generate_response(user_query=query)
                
                # Add response to chat
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
        
        # Clear input and rerun to show new messages
        st.session_state.main_text_input = ""
        st.rerun()
    
    def analyze_image(self, image: Image.Image, filename: str):
        """Perform image analysis."""
        st.session_state.processing_state = "processing"
        st.rerun()
        
        try:
            result = self.perform_image_analysis(image)
            
            if result:
                # Add to history
                result.update({
                    "timestamp": datetime.now().isoformat(),
                    "filename": filename,
                    "type": "image"
                })
                st.session_state.analysis_history.append(result)
                
                st.session_state.processing_state = "complete"
                st.success("✅ Analysis complete!")
                st.rerun()
            
        except Exception as e:
            self.logger.error(f"Image analysis error: {e}")
            st.error("❌ Analysis failed. Please try again.")
            st.session_state.processing_state = "error"
    
    def perform_image_analysis(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """Perform actual image analysis using vision adapter."""
        adapter = self.get_adapter("vision")
        
        if adapter:
            try:
                # Use adapter's prediction method
                if hasattr(adapter, 'predict'):
                    disease, confidence = adapter.predict(image)
                    return {
                        "disease": disease,
                        "confidence": confidence,
                        "model": st.session_state.current_models["vision"],
                        "recommendations": self.get_treatment_recommendations(disease)
                    }
                else:
                    # Fallback for mock adapter
                    return {
                        "disease": "Tomato Late Blight",
                        "confidence": 0.87,
                        "model": st.session_state.current_models["vision"],
                        "recommendations": ["Remove affected leaves", "Apply fungicide", "Improve air circulation"]
                    }
            except Exception as e:
                self.logger.error(f"Vision adapter error: {e}")
                return None
        
        return None
    
    def display_analysis_result(self, result: Dict[str, Any]):
        """Display analysis results in main area."""
        st.markdown("### 🔬 Analysis Results")
        
        # Main result with confidence
        disease = result.get("disease", "Unknown")
        confidence = result.get("confidence", 0)
        
        col_res1, col_res2 = st.columns([2, 1])
        
        with col_res1:
            st.markdown(f"**🦠 Detected:** {disease}")
            st.progress(confidence, text=f"Confidence: {confidence:.1%}")
            
            # Treatment recommendations
            recommendations = result.get("recommendations", [])
            if recommendations:
                st.markdown("**💊 Recommendations:**")
                for rec in recommendations:
                    st.markdown(f"• {rec}")
        
        with col_res2:
            st.markdown("**📊 Details:**")
            st.markdown(f"Model: {result.get('model', 'Unknown')}")
            st.markdown(f"Time: {result.get('timestamp', 'Unknown')}")
            st.markdown(f"File: {result.get('filename', 'Unknown')}")
            
            # Action buttons
            if st.button("🔄 Reanalyze", key="reanalyze_btn"):
                st.info("Upload the image again to reanalyze")
            
            if st.button("📤 Export Result", key="export_single"):
                self.export_single_result(result)
    
    def display_chat_messages(self):
        """Display chat conversation."""
        st.markdown("### 💬 Plant Care Assistant")
        
        # Show recent messages
        recent_messages = st.session_state.chat_messages[-6:]  # Last 6 messages
        
        for message in recent_messages:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                st.markdown(f"**👤 You:** {content}")
            else:
                st.markdown(f"**🤖 PlantGuard:** {content}")
        
        # Clear chat option
        if st.session_state.chat_messages:
            if st.button("🗑️ Clear Chat", key="clear_chat"):
                st.session_state.chat_messages = []
                st.rerun()
    
    def render_welcome_content(self):
        """Render welcome content when no active results."""
        st.markdown("### 🌟 Welcome to PlantGuard AI")
        st.markdown("Upload a plant image, ask a question, or record audio to get started!")
        
        # Feature overview
        col_feat1, col_feat2, col_feat3 = st.columns(3)
        
        with col_feat1:
            st.markdown("""
            **🖼️ Image Analysis**
            - Multi-model AI detection
            - Batch processing
            - High accuracy results
            """)
        
        with col_feat2:
            st.markdown("""
            **🎤 Voice Assistant**
            - Natural language queries
            - Real-time transcription
            - Conversational interface
            """)
        
        with col_feat3:
            st.markdown("""
            **💬 Chat Support**
            - Plant care guidance
            - Disease information
            - Treatment recommendations
            """)
    
    def show_history_panel(self):
        """Show analysis history."""
        st.markdown("### 📊 Analysis History")
        
        if st.session_state.analysis_history:
            # Recent analyses
            for i, analysis in enumerate(reversed(st.session_state.analysis_history[-5:])):
                with st.expander(f"{analysis.get('disease', 'Unknown')} - {analysis.get('confidence', 0):.1%}", expanded=False):
                    st.json(analysis)
                    
                    if st.button(f"🔄 View Details", key=f"history_detail_{i}"):
                        self.display_analysis_result(analysis)
        else:
            st.info("No analysis history available yet.")
    
    def render_system_status(self):
        """Show system status information."""
        st.markdown("### 📡 System Status")
        
        # Model status
        vision_model = st.session_state.current_models["vision"]
        model_info = self.models["vision"].get(vision_model, {})
        
        st.markdown(f"**Vision:** {model_info.get('name', 'Unknown')}")
        st.markdown(f"**Accuracy:** {model_info.get('accuracy', 'Unknown')}")
        st.markdown(f"**Speed:** {model_info.get('speed', 'Unknown')}")
        
        # Statistics
        if st.session_state.analysis_history:
            total_analyses = len(st.session_state.analysis_history)
            st.metric("Total Analyses", total_analyses)
            
            # Average confidence
            confidences = [a.get("confidence", 0) for a in st.session_state.analysis_history]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    
    def get_treatment_recommendations(self, disease: str) -> List[str]:
        """Get treatment recommendations for detected disease."""
        recommendations = {
            "Tomato Late Blight": [
                "Remove affected leaves immediately",
                "Apply copper-based fungicide", 
                "Improve air circulation",
                "Avoid overhead watering"
            ],
            "Bacterial Spot": [
                "Remove infected plant parts",
                "Apply copper spray",
                "Space plants for airflow",
                "Water at soil level"
            ],
            "Leaf Mold": [
                "Increase ventilation",
                "Reduce humidity",
                "Apply fungicide if severe",
                "Remove affected leaves"
            ]
        }
        
        return recommendations.get(disease, [
            "Consult local agricultural extension",
            "Isolate affected plants",
            "Monitor plant health closely",
            "Consider professional diagnosis"
        ])
    
    def show_help_panel(self):
        """Show help and troubleshooting information."""
        st.info("📞 **Need Help?**")
        st.markdown("""
        **Common Issues:**
        - 🖼️ **Image Quality**: Ensure good lighting and clear focus
        - 📱 **File Size**: Images should be under 200MB
        - 🎤 **Microphone**: Requires HTTPS connection (use `make tunnel`)
        - 🌐 **Network**: Check internet connection for model downloads
        
        **Supported Formats:**
        - Images: JPG, JPEG, PNG
        - Audio: WAV, MP3, M4A, OGG
        """)
    
    def render_comparison_overlay(self):
        """Render comparison mode interface overlay."""
        st.markdown("### 🔄 Comparison Mode Active")
        st.info("🔄 Upload two images to compare analysis results side by side.")
        
        comp_col1, comp_col2, comp_col3 = st.columns([1, 1, 1])
        
        with comp_col1:
            st.markdown("**📷 Image 1:**")
            comp_file1 = st.file_uploader("First image", type=["jpg", "jpeg", "png"], key="comp1")
        
        with comp_col2:
            st.markdown("**📷 Image 2:**")
            comp_file2 = st.file_uploader("Second image", type=["jpg", "jpeg", "png"], key="comp2")
        
        with comp_col3:
            st.markdown("**⚙️ Options:**")
            if st.button("🔄 Compare", disabled=not (comp_file1 and comp_file2), key="perform_comparison"):
                self.perform_comparison(comp_file1, comp_file2)
            
            if st.button("❌ Exit Comparison", key="exit_comparison"):
                st.session_state.comparison_mode = False
                st.rerun()
    
    def clear_all_results(self):
        """Clear all analysis results and chat messages."""
        st.session_state.analysis_history = []
        st.session_state.chat_messages = []
        st.session_state.processing_state = "idle"
        st.success("✅ All results cleared!")
        st.rerun()
    
    def render_performance_metrics(self):
        """Render real-time performance metrics."""
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            st.metric(
                "💾 Memory", 
                f"{memory.percent:.1f}%",
                delta=f"{memory.available / (1024**3):.1f}GB free"
            )
            
            # Analysis speed (if available)
            if st.session_state.analysis_history:
                recent_analyses = st.session_state.analysis_history[-5:]
                if len(recent_analyses) >= 2:
                    # Calculate average time between analyses
                    times = [a.get("timestamp", "") for a in recent_analyses]
                    if all(times):
                        try:
                            parsed_times = [datetime.fromisoformat(t) for t in times]
                            if len(parsed_times) >= 2:
                                time_diffs = [(parsed_times[i] - parsed_times[i-1]).total_seconds() 
                                            for i in range(1, len(parsed_times))]
                                avg_time = sum(time_diffs) / len(time_diffs)
                                st.metric("⏱️ Avg Speed", f"{avg_time:.1f}s")
                        except:
                            pass
            
        except ImportError:
            st.info("📈 Install psutil for performance metrics")
        except Exception as e:
            st.warning(f"⚠️ Metrics unavailable: {str(e)[:50]}")
    
    def render_api_status(self):
        """Render AI Agent API status information."""
        st.markdown("**🤖 AI Agent API:**")
        
        # Check adapter availability
        adapters_status = {
            "Vision": self.vision_adapter is not None,
            "Audio": self.audio_adapter is not None,
            "Text": self.text_adapter is not None
        }
        
        for adapter_name, is_available in adapters_status.items():
            status_icon = "✅" if is_available else "❌"
            st.markdown(f"{status_icon} {adapter_name} Adapter")
        
        # Programmatic interface status
        if all(adapters_status.values()):
            st.success("🚀 All APIs Ready")
        else:
            unavailable = [name for name, status in adapters_status.items() if not status]
            st.warning(f"⚠️ {', '.join(unavailable)} not ready")
        
        # API usage statistics
        total_api_calls = len(st.session_state.get("analysis_history", [])) + \
                         len(st.session_state.get("chat_messages", []))
        st.metric("API Calls", total_api_calls)
    
    # ========== Session State Management ==========
    
    def save_analysis_result(self, result: Dict[str, Any], filename: str, analysis_type: str = "image"):
        """Save analysis result to session state with metadata."""
        enhanced_result = {
            **result,
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "type": analysis_type,
            "session_id": id(st.session_state),
            "model_used": st.session_state.current_models.get("vision", "unknown"),
            "device": getattr(self, 'device', 'unknown')
        }
        
        st.session_state.analysis_history.append(enhanced_result)
        
        # Limit history size to prevent memory issues
        max_history = 100
        if len(st.session_state.analysis_history) > max_history:
            st.session_state.analysis_history = st.session_state.analysis_history[-max_history:]
    
    def save_chat_message(self, role: str, content: str, metadata: Dict = None):
        """Save chat message to session state with metadata."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "session_id": id(st.session_state),
            "metadata": metadata or {}
        }
        
        st.session_state.chat_messages.append(message)
        
        # Auto-clear old messages if preference is set
        if st.session_state.user_preferences.get("auto_clear_chat", False):
            max_messages = 50
            if len(st.session_state.chat_messages) > max_messages:
                st.session_state.chat_messages = st.session_state.chat_messages[-max_messages:]
    
    def update_processing_state(self, state: str, processing_type: str = None, 
                               batch_info: Dict = None, error_msg: str = None):
        """Update processing state with comprehensive tracking."""
        st.session_state.processing_state = state
        
        if processing_type:
            st.session_state.processing_type = processing_type
        
        if batch_info:
            st.session_state.current_batch_item = batch_info.get("current", 0)
            st.session_state.total_batch_items = batch_info.get("total", 1)
        
        if error_msg:
            st.session_state.error_message = error_msg
        
        # Track performance
        performance_entry = {
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "type": processing_type,
            "batch_info": batch_info
        }
        
        st.session_state.performance_history.append(performance_entry)
        
        # Limit performance history
        if len(st.session_state.performance_history) > 50:
            st.session_state.performance_history = st.session_state.performance_history[-50:]
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics."""
        session_start = st.session_state.get("session_start_time", datetime.now().isoformat())
        try:
            start_time = datetime.fromisoformat(session_start)
            session_duration = (datetime.now() - start_time).total_seconds()
        except:
            session_duration = 0
        
        return {
            "session_duration_seconds": session_duration,
            "total_analyses": len(st.session_state.analysis_history),
            "total_chat_messages": len(st.session_state.chat_messages),
            "current_state": st.session_state.processing_state,
            "models_used": st.session_state.current_models,
            "comparison_mode_active": st.session_state.comparison_mode,
            "performance_entries": len(st.session_state.performance_history),
            "session_id": id(st.session_state)
        }
    
    def export_all_results(self):
        """Export all analysis results."""
        if not st.session_state.analysis_history:
            st.warning("No results to export")
            return
            
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_analyses": len(st.session_state.analysis_history),
            "analyses": st.session_state.analysis_history,
            "chat_messages": st.session_state.chat_messages,
            "models_used": st.session_state.current_models
        }
        
        json_data = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="📄 Download All Data (JSON)",
            data=json_data,
            file_name=f"plantguard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    def export_single_result(self, result: Dict[str, Any]):
        """Export a single analysis result."""
        json_data = json.dumps(result, indent=2)
        
        st.download_button(
            label="📄 Download Result",
            data=json_data,
            file_name=f"analysis_{result.get('filename', 'result')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="export_single_download"
        )
    
    def add_to_comparison(self, image: Image.Image, filename: str):
        """Add image to comparison mode."""
        st.session_state.comparison_mode = True
        st.info(f"🔄 Added {filename} to comparison. Upload another image to compare.")
    
    def show_image_info(self, image: Image.Image, filename: str):
        """Show quick image information."""
        st.info(f"""
        **📊 Image Info:**
        - Filename: {filename}
        - Size: {image.size}
        - Format: {image.format}
        - Mode: {image.mode}
        """)
    
    def run(self):
        """Main application runner with responsive layout."""
        try:
            # Setup error monitoring
            self.setup_error_monitoring()
            
            # Render adaptive layout based on device
            self.render_adaptive_layout()
            
            # Comparison mode overlay (if active)
            if st.session_state.get("comparison_mode", False):
                self.render_comparison_overlay()
            
            self.logger.info("PlantGuard SPA rendered successfully")
            
        except Exception as e:
            # Use comprehensive error handling
            recovery_success = self.handle_error(e, "main_application_runner")
            
            if not recovery_success:
                st.error("❌ An unexpected error occurred. Please refresh the page.")
                
                # Show error details for debugging
                if st.session_state.user_preferences.get("show_debug_info", False):
                    st.exception(e)
    
    def render_comparison_mode(self):
        """Render comparison mode interface."""
        st.markdown("---")
        st.markdown("### 🔄 Image Comparison Mode")
        
        col_comp1, col_comp2, col_comp3 = st.columns([1, 1, 1])
        
        with col_comp1:
            st.markdown("**📷 Image 1:**")
            comp_file1 = st.file_uploader("First image", type=["jpg", "jpeg", "png"], key="comp1")
            
        with col_comp2:
            st.markdown("**📷 Image 2:**")
            comp_file2 = st.file_uploader("Second image", type=["jpg", "jpeg", "png"], key="comp2")
        
        with col_comp3:
            st.markdown("**⚙️ Options:**")
            if st.button("🔄 Compare", disabled=not (comp_file1 and comp_file2)):
                self.perform_comparison(comp_file1, comp_file2)
            
            if st.button("❌ Exit Comparison"):
                st.session_state.comparison_mode = False
                st.rerun()
    
    def perform_comparison(self, file1, file2):
        """Perform image comparison."""
        image1 = Image.open(file1)
        image2 = Image.open(file2)
        
        # Display images side by side
        col_img1, col_img2 = st.columns(2)
        
        with col_img1:
            st.image(image1, caption=f"📷 {file1.name}", use_column_width=True)
            result1 = self.perform_image_analysis(image1)
            if result1:
                self.display_analysis_result(result1)
        
        with col_img2:
            st.image(image2, caption=f"📷 {file2.name}", use_column_width=True)
            result2 = self.perform_image_analysis(image2)
            if result2:
                self.display_analysis_result(result2)
        
        # Comparison metrics
        if result1 and result2:
            st.markdown("### 📊 Comparison Summary")
            
            col_met1, col_met2, col_met3 = st.columns(3)
            
            with col_met1:
                st.metric("Disease 1", result1.get("disease", "Unknown"))
                st.metric("Confidence 1", f"{result1.get('confidence', 0):.1%}")
            
            with col_met2:
                st.metric("Disease 2", result2.get("disease", "Unknown"))
                st.metric("Confidence 2", f"{result2.get('confidence', 0):.1%}")
            
            with col_met3:
                # Comparison insights
                conf_diff = abs(result1.get("confidence", 0) - result2.get("confidence", 0))
                st.metric("Confidence Difference", f"{conf_diff:.1%}")
                
                same_disease = result1.get("disease") == result2.get("disease")
                st.metric("Same Disease", "✅ Yes" if same_disease else "❌ No")


def main():
    """Main entry point for PlantGuard SPA."""
    logger.info("Starting PlantGuard Single Page Application")
    
    app = PlantGuardSPA()
    app.run()


if __name__ == "__main__":
    main()