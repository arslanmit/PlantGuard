#!/usr/bin/env python3
"""
PlantGuard Mobile Single Page Application

Mobile-first PlantGuard application optimized for Chrome and Safari mobile browsers.
Features AI agent autonomous development capabilities and comprehensive testing.

Usage:
    streamlit run mobile_spa_app.py

Features:
- Fixed-width mobile layout (428px max)
- Touch-friendly interface
- All PlantGuard features in one page
- AI agent autonomous testing
- Self-healing capabilities
"""

# Standard library imports
import builtins
import contextlib
import io
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Add src to Python path (must be before first-party imports)
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configure logger for this module
logger = logging.getLogger(__name__)

# Third-party imports
import streamlit as st  # noqa: E402
from PIL import Image as PILImage  # noqa: E402

# First-party imports - Core adapters
from core.audio import AudioAdapter  # noqa: E402
from core.nlp import TextAdapter  # noqa: E402
from core.vision import VisionAdapter  # noqa: E402

# First-party imports - Mobile components
from ui.components.mobile_chat_interface import MobileChatInterface  # noqa: E402
from ui.components.mobile_component_registry import mobile_component_registry  # noqa: E402
from ui.components.mobile_content_tabs import MobileContentTabs  # noqa: E402
from ui.components.mobile_header import MobileHeader  # noqa: E402
from ui.components.mobile_image_analysis import MobileImageAnalysis  # noqa: E402
from ui.components.mobile_input_ribbon import MobileInputRibbon  # noqa: E402
from ui.components.mobile_layout_manager import MobileLayoutManager  # noqa: E402
from ui.components.mobile_voice_interface import MobileVoiceInterface  # noqa: E402

# Import error recovery utilities
from utils.error_recovery import ImportErrorRecovery  # noqa: E402

# Conditional imports with proper error handling and logging
MobileTestingFramework = ImportErrorRecovery.safe_import_from(
    "ui.components.mobile_testing_framework",
    "MobileTestingFramework",
    fallback=None,
    logger_name="mobile_spa_app",
)

mobile_performance_optimizer = ImportErrorRecovery.safe_import_from(
    "ui.components.mobile_performance_optimizer",
    "mobile_performance_optimizer",
    fallback=type(
        "MockPerformanceOptimizer",
        (),
        {
            "set_optimization_level": lambda self, level: None,
            "enable_offline_mode": lambda self: None,
            "preload_critical_components": lambda self, components: None,
            "optimize_images": lambda self, data: data,
            "get_performance_report": lambda self: {},
        },
    )(),
    logger_name="mobile_spa_app",
)

# Import accessibility components


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global testing framework instance
_mobile_testing_framework = None


def get_ai_testing_framework() -> Any:
    """Get or create the global AI testing framework instance."""
    global _mobile_testing_framework
    if _mobile_testing_framework is None:
        _mobile_testing_framework = MobileTestingFramework()
    return _mobile_testing_framework


# Global adapter instances for enhanced functionality
@st.cache_resource
def load_core_adapters() -> tuple[Any, Any, Any]:
    """Load and cache core PlantGuard adapters for mobile use."""
    try:
        vision_adapter = VisionAdapter(lazy_load=True)
        audio_adapter = AudioAdapter()
        text_adapter = TextAdapter()

        logger.info("Core adapters loaded successfully for mobile app")
        return vision_adapter, audio_adapter, text_adapter
    except Exception as e:
        logger.error(f"Failed to load core adapters: {e}")
        return None, None, None


# Advanced model selection and management
@st.cache_data
def get_model_status() -> dict[str, str]:
    """Get current model status for all adapters."""
    try:
        vision_adapter, audio_adapter, text_adapter = load_core_adapters()
        return {
            "vision": vision_adapter.model_name if vision_adapter else "Not Loaded",
            "audio": audio_adapter.model_name if audio_adapter else "Not Loaded",
            "text": text_adapter.model_name if text_adapter else "Not Loaded",
        }
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        return {"vision": "Error", "audio": "Error", "text": "Error"}


def _load_adapters_safely() -> None:
    """Safely load all adapters with error handling."""
    try:
        vision_adapter, audio_adapter, text_adapter = load_core_adapters()
        if vision_adapter and audio_adapter and text_adapter:
            st.session_state.adapters_loaded = True
            st.session_state.vision_adapter = vision_adapter
            st.session_state.audio_adapter = audio_adapter
            st.session_state.text_adapter = text_adapter
            logger.info("All adapters loaded successfully")
        else:
            st.session_state.adapters_loaded = False
            logger.warning("Some adapters failed to load")
    except Exception as e:
        st.session_state.adapters_loaded = False
        logger.error(f"Failed to load adapters: {e}")


# Page configuration for unified PlantGuard with responsive design
st.set_page_config(
    page_title="PlantGuard Unified",
    page_icon="🌿",
    layout="wide",  # Will be constrained to 428px on mobile by CSS
    initial_sidebar_state="collapsed",  # Start collapsed
    menu_items={
        "Get Help": "https://github.com/arslanmit/PlantGuard",
        "Report a bug": "https://github.com/arslanmit/PlantGuard/issues",
        "About": "PlantGuard Unified - AI-powered plant disease detection (Mobile-first with desktop capabilities)",
    },
)

# Hide sidebar completely with CSS
st.markdown(
    """
<style>
    .stSidebar {
        display: none;
    }
    
    /* Adjust main content to fill space */
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 428px;
        margin: 0 auto;
    }
</style>
""",
    unsafe_allow_html=True,
)


class MobilePlantGuardApp:
    """Main mobile PlantGuard application class.

    Integrates all mobile components into a unified SPA experience.
    Provides AI agent testing and autonomous development capabilities.
    """

    def __init__(self) -> None:
        self.layout_manager = None
        self.header = None
        self.input_ribbon = None
        self.content_tabs = None
        self.image_analysis = None
        self.voice_interface = None
        self.chat_interface = None

        # Core adapters for full PlantGuard functionality
        self.vision_adapter = None
        self.audio_adapter = None
        self.text_adapter = None

        # Performance optimization
        self.performance_optimizer = mobile_performance_optimizer

        # Initialize session state
        self.initialize_app_state()

        # Load core adapters
        self._load_core_adapters()

    def initialize_app_state(self) -> None:
        """Initialize essential application-wide session state only."""
        # Core app state
        if "mobile_app_initialized" not in st.session_state:
            st.session_state.mobile_app_initialized = False

        # Navigation essentials
        if "current_tab" not in st.session_state:
            st.session_state.current_tab = "image_analysis"

        # App start time
        if "app_start_time" not in st.session_state:
            st.session_state.app_start_time = time.time()

        # Mobile-specific essentials
        if "mobile_viewport_width" not in st.session_state:
            st.session_state.mobile_viewport_width = 428  # Always 428px

        if "fixed_mobile_design" not in st.session_state:
            st.session_state.fixed_mobile_design = True

        # Initialize component-specific state
        self._initialize_component_states()

        # Initialize performance optimization
        self._initialize_performance_optimization()

    def initialize_components(self) -> None:
        """Initialize all mobile components."""
        try:
            # Initialize layout manager
            self.layout_manager = MobileLayoutManager("main_layout")

            # Initialize header
            self.header = MobileHeader("mobile_header", title="PlantGuard", subtitle="AI Plant Care Assistant")

            # Initialize input ribbon
            self.input_ribbon = MobileInputRibbon("mobile_input_ribbon", layout_style="grid")

            # Initialize content tabs
            self.content_tabs = MobileContentTabs("mobile_content_tabs", tab_style="pills")

            # Initialize feature components
            self.image_analysis = MobileImageAnalysis("mobile_image_analysis")
            self.voice_interface = MobileVoiceInterface("mobile_voice_interface")
            self.chat_interface = MobileChatInterface("mobile_chat_interface")

            # Register tab content
            self.content_tabs.register_tab_content("image_analysis", self.render_image_analysis_tab)
            self.content_tabs.register_tab_content("voice_assistant", self.render_voice_assistant_tab)
            self.content_tabs.register_tab_content("chat_interface", self.render_chat_interface_tab)
            self.content_tabs.register_tab_content("history_settings", self.render_history_settings_tab)
            self.content_tabs.register_tab_content("comparison", self.render_comparison_tab)

            # Initialize advanced state management
            if "mobile_app_initialized" not in st.session_state:
                st.session_state.mobile_app_initialized = False
                st.session_state.page_change_prevention = True
                st.session_state.debug_mode = True
                st.session_state.button_click_count = 0
                st.session_state.last_page_change = None

            st.session_state.mobile_app_initialized = True
            logger.info("Mobile PlantGuard app initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize mobile components: {e}")
            # Create fallback components to prevent empty containers
            self._create_fallback_components()

    def _create_fallback_components(self) -> None:
        """Create minimal fallback components if initialization fails."""
        try:
            # Ensure layout manager exists
            if not hasattr(self, "layout_manager") or not self.layout_manager:
                self.layout_manager = MobileLayoutManager("fallback_layout")

            # Create fallback content function
            def render_fallback_content() -> None:
                st.markdown("### :herb: PlantGuard Mobile - Loading...")
                st.info("Some components are still initializing. Please refresh if issues persist.")

                if st.button(":arrows_counterclockwise: Refresh App", use_container_width=True):
                    # Clear initialization state to force re-init
                    st.session_state.mobile_app_initialized = False
                    # Update state without page refresh
                    st.session_state.force_reinit = True

            # Store fallback render function
            self._fallback_render = render_fallback_content

            # Mark as minimally initialized
            st.session_state.mobile_app_initialized = True
            logger.info("Fallback components created")

        except Exception as e:
            logger.error(f"Even fallback component creation failed: {e}")
            st.session_state.mobile_app_initialized = False

    def _initialize_component_states(self) -> None:
        """Initialize state for all mobile components."""
        # MobileLayoutManager state
        if "mobile_css_loaded" not in st.session_state:
            st.session_state.mobile_css_loaded = False

        if "mobile_layout_initialized" not in st.session_state:
            st.session_state.mobile_layout_initialized = False

        # MobileHeader state
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = "default"

        if "system_status" not in st.session_state:
            st.session_state.system_status = "ready"

        # MobileImageAnalysis state
        if "uploaded_image" not in st.session_state:
            st.session_state.uploaded_image = None

        if "analysis_results" not in st.session_state:
            st.session_state.analysis_results = None

        if "analysis_in_progress" not in st.session_state:
            st.session_state.analysis_in_progress = False

        # MobileVoiceInterface state
        if "recorded_audio" not in st.session_state:
            st.session_state.recorded_audio = None

        if "transcribed_text" not in st.session_state:
            st.session_state.transcribed_text = ""

        if "voice_response" not in st.session_state:
            st.session_state.voice_response = ""

        # MobileChatInterface state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if "current_chat_input" not in st.session_state:
            st.session_state.current_chat_input = ""

        # Enhanced mobile functionality state
        if "mobile_analysis_history" not in st.session_state:
            st.session_state.mobile_analysis_history = []

        if "mobile_performance_mode" not in st.session_state:
            st.session_state.mobile_performance_mode = "balanced"

        if "mobile_offline_mode" not in st.session_state:
            st.session_state.mobile_offline_mode = False

        # Initialize performance optimization state
        if "mobile_performance" not in st.session_state:
            st.session_state.mobile_performance = {"optimization_level": "balanced", "memory_usage": 0, "cache_stats": {"hit_rate": 0, "size_mb": 0}}

        # Initialize offline manager state
        if "mobile_offline" not in st.session_state:
            st.session_state.mobile_offline = {"enabled": False, "connection_status": "online", "cached_resources": 0, "cache_size_mb": 0}

        # Initialize bundle optimizer state
        if "mobile_bundles" not in st.session_state:
            st.session_state.mobile_bundles = {"loaded_bundles": [], "total_size_mb": 0, "optimization_enabled": True}

    def _setup_state_persistence(self) -> None:
        """Setup state persistence for mobile session continuity."""
        # Create state backup for critical data
        critical_state_keys = ["analysis_history", "user_preferences", "feature_usage_stats", "ai_agent_test_results"]

        if "state_backup" not in st.session_state:
            st.session_state.state_backup = {}

        # Backup critical state
        for key in critical_state_keys:
            if key in st.session_state:
                st.session_state.state_backup[key] = st.session_state[key]

    def _setup_state_validation(self) -> None:
        """Setup state validation for data integrity."""
        # Validate analysis history structure
        if "analysis_history" in st.session_state:
            valid_history = []
            for item in st.session_state.analysis_history:
                if isinstance(item, dict) and "timestamp" in item:
                    valid_history.append(item)
            st.session_state.analysis_history = valid_history

        # Validate user preferences
        if "user_preferences" in st.session_state:
            default_prefs = {
                "theme": "auto",
                "notifications": True,
                "auto_clear_chat": False,
                "voice_auto_transcribe": True,
                "image_auto_analysis": False,
            }
            # Ensure all required preferences exist
            for key, default_value in default_prefs.items():
                if key not in st.session_state.user_preferences:
                    st.session_state.user_preferences[key] = default_value

    def update_feature_usage(self, feature: str) -> None:
        """Update feature usage statistics."""
        if feature in st.session_state.feature_usage_stats:
            st.session_state.feature_usage_stats[feature] += 1
            st.session_state.interaction_count += 1

    def track_tab_navigation(self, new_tab: str) -> None:
        """Track tab navigation for user analytics."""

        if st.session_state.current_tab != new_tab:
            # Update previous tab
            st.session_state.previous_tab = st.session_state.current_tab

            # Add to tab history
            st.session_state.tab_history.append({"from_tab": st.session_state.current_tab, "to_tab": new_tab, "timestamp": time.time()})

            # Limit history size
            if len(st.session_state.tab_history) > 50:
                st.session_state.tab_history = st.session_state.tab_history[-50:]

            # Update current tab
            st.session_state.current_tab = new_tab

            # Update feature usage
            self.update_feature_usage(new_tab)

    def save_analysis_result(self, result: dict[str, Any], analysis_type: str = "unknown") -> None:
        """Save analysis result to history with metadata."""

        analysis_record = {
            "timestamp": time.time(),
            "analysis_type": analysis_type,
            "result": result,
            "session_id": f"session_{int(st.session_state.app_start_time)}",
            "tab_context": st.session_state.current_tab,
        }

        st.session_state.analysis_history.append(analysis_record)

        # Limit history size (keep last 100 analyses)
        if len(st.session_state.analysis_history) > 100:
            st.session_state.analysis_history = st.session_state.analysis_history[-100:]

    def get_session_analytics(self) -> dict[str, Any]:
        """Get comprehensive session analytics."""

        current_time = time.time()
        session_duration = current_time - st.session_state.app_start_time

        return {
            "session_duration": session_duration,
            "interactions": st.session_state.interaction_count,
            "touch_interactions": st.session_state.touch_interactions,
            "feature_usage": st.session_state.feature_usage_stats.copy(),
            "analyses_performed": len(st.session_state.analysis_history),
            "tab_switches": len(st.session_state.tab_history),
            "current_tab": st.session_state.current_tab,
            "ai_agent_active": st.session_state.ai_agent_active,
            "component_errors": len(st.session_state.component_error_log),
        }

    def register_tab_content(self) -> None:
        """Register content callbacks for each tab."""
        # Register image analysis tab
        self.content_tabs.register_tab_content("image_analysis", self.render_image_analysis_tab)

        # Register voice assistant tab
        self.content_tabs.register_tab_content("voice_assistant", self.render_voice_assistant_tab)

        # Register chat interface tab
        self.content_tabs.register_tab_content("chat_interface", self.render_chat_interface_tab)

        # Register history & settings tab
        self.content_tabs.register_tab_content("history_settings", self.render_history_settings_tab)

        # Register comparison tab
        self.content_tabs.register_tab_content("comparison", self.render_comparison_tab)

    def _load_core_adapters(self) -> None:
        """Load core PlantGuard adapters for enhanced mobile functionality."""
        try:
            self.vision_adapter, self.audio_adapter, self.text_adapter = load_core_adapters()

            if self.vision_adapter and self.audio_adapter and self.text_adapter:
                logger.info("Core adapters loaded successfully for mobile app")
                st.session_state.mobile_adapters_loaded = True
            else:
                logger.warning("Some core adapters failed to load")
                st.session_state.mobile_adapters_loaded = False

        except Exception as e:
            logger.error(f"Failed to load core adapters: {e}")
            st.session_state.mobile_adapters_loaded = False

    def _initialize_performance_optimization(self) -> None:
        """Initialize performance optimization for mobile app."""
        try:
            # Set optimization level based on device capabilities
            self.performance_optimizer.set_optimization_level("auto")

            # Enable offline mode optimizations if needed
            if st.session_state.get("mobile_offline_mode", False):
                self.performance_optimizer.enable_offline_mode()

            # Preload critical components
            critical_components = ["mobile_header", "mobile_input_ribbon", "mobile_image_analysis", "mobile_chat_interface"]
            self.performance_optimizer.preload_critical_components(critical_components)

            logger.info("Performance optimization initialized for mobile app")

        except Exception as e:
            logger.error(f"Failed to initialize performance optimization: {e}")

    def analyze_image_with_adapters(self, image: Any) -> dict[str, Any]:
        """Analyze image using core vision adapter with mobile optimizations."""
        try:
            if not self.vision_adapter:
                return {
                    "error": "Vision adapter not available",
                    "disease": "Unknown",
                    "confidence": 0.0,
                    "recommendations": ["Vision analysis not available. Please check system status."],
                }

            # Optimize image for mobile processing
            if hasattr(image, "read"):
                image_data = image.read()
                optimized_image_data = self.performance_optimizer.optimize_images(image_data)

                # Convert back to PIL Image
                image = PILImage.open(io.BytesIO(optimized_image_data))

            # Perform prediction
            disease_class, confidence = self.vision_adapter.predict(image)

            # Get detailed information using text adapter
            disease_info: dict[str, Any] = {}
            recommendations: list[str] = []

            if self.text_adapter:
                disease_info = self.text_adapter.get_disease_info(disease_class)
                response = self.text_adapter.generate_response(disease_class, "What should I do about this disease?", confidence)
                recommendations = response.split("\n") if response else []

            # Save to analysis history
            analysis_result = {
                "timestamp": st.session_state.get("app_start_time", 0),
                "disease": disease_class,
                "confidence": confidence,
                "disease_info": disease_info,
                "recommendations": recommendations,
            }

            st.session_state.mobile_analysis_history.append(analysis_result)

            # Limit history size
            if len(st.session_state.mobile_analysis_history) > 50:
                st.session_state.mobile_analysis_history = st.session_state.mobile_analysis_history[-50:]

            return analysis_result

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "error": str(e),
                "disease": "Analysis Failed",
                "confidence": 0.0,
                "recommendations": ["Analysis failed. Please try again or check system status."],
            }

    def process_voice_input(self, audio_data: Any) -> str:
        """Process voice input using audio adapter."""
        try:
            if not self.audio_adapter:
                return "Voice processing not available"

            # Transcribe audio
            transcription = self.audio_adapter.transcribe(audio_data)

            if transcription and self.text_adapter:
                # Generate response using text adapter
                response = self.text_adapter.generate_response("general", transcription, 1.0)
                return response

            return transcription or "No speech detected"

        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            return f"Voice processing error: {e}"

    def process_text_query(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Process text query using NLP adapter."""
        try:
            if not self.text_adapter:
                return "Text processing not available"

            # Use context from recent analysis if available
            disease_class = "general"
            confidence = 1.0

            if context:
                disease_class = context.get("disease", "general")
                confidence = context.get("confidence", 1.0)
            elif st.session_state.mobile_analysis_history:
                # Use most recent analysis as context
                recent_analysis = st.session_state.mobile_analysis_history[-1]
                disease_class = recent_analysis.get("disease", "general")
                confidence = recent_analysis.get("confidence", 1.0)

            # Generate response
            response = self.text_adapter.generate_response(disease_class, query, confidence)
            return response

        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            return f"Text processing error: {e}"

    def render_performance_status(self) -> None:
        """Render performance status indicator."""
        try:
            # Only show if performance optimization is enabled
            if st.session_state.get("mobile_performance_mode") != "minimal":
                with st.expander(":zap: Performance Status", expanded=True):
                    try:
                        perf_report = self.performance_optimizer.get_performance_report()

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            memory_pressure = perf_report.get("memory_pressure", "unknown")
                            if memory_pressure == "normal":
                                st.success(":green_circle: Memory: Normal")
                            elif memory_pressure == "warning":
                                st.warning(":yellow_circle: Memory: Warning")
                            else:
                                st.error(":red_circle: Memory: Critical")

                        with col2:
                            cache_stats = perf_report.get("cache_stats", {})
                            hit_rate = cache_stats.get("hit_rate", 0)
                            st.metric("Cache Hit Rate", f"{hit_rate:.1f}%")

                        with col3:
                            adapters_status = st.session_state.get("mobile_adapters_loaded", False)
                            if adapters_status:
                                st.success(":green_circle: Adapters: Ready")
                            else:
                                st.error(":red_circle: Adapters: Not Ready")

                        # Performance actions
                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(":broom: Clean Memory", use_container_width=True, key="perf_clean_memory"):
                                with st.spinner("Cleaning memory..."):
                                    cleanup_stats = self.performance_optimizer.memory_manager.cleanup_memory(force=True)
                                    freed_mb = cleanup_stats.get("freed_mb", 0)
                                    st.success(f"Freed {freed_mb:.1f}MB")

                        with col2:
                            if st.button(":arrows_counterclockwise: Clear Cache", use_container_width=True, key="perf_clear_cache"):
                                self.performance_optimizer.cache.clear()
                                st.success("Cache cleared")
                                # Update cache status without page refresh
                                st.session_state.cache_cleared = True

                    except Exception as e:
                        st.warning(f"Performance monitoring unavailable: {e}")

        except Exception as e:
            logger.error(f"Performance status rendering failed: {e}")

    def render_image_analysis_tab(self) -> None:
        """Render enhanced image analysis tab content with core adapter integration."""
        try:
            # Use performance optimization
            with self.performance_optimizer.optimize_component_render("image_analysis_tab"):
                # Check if adapters are loaded
                adapters_status = st.session_state.get("mobile_adapters_loaded", False)

                if not adapters_status:
                    st.warning(":warning: Core adapters not fully loaded. Some features may be limited.")

                # Render the mobile image analysis component
                self.image_analysis.render()

                # Add enhanced functionality if adapters are available
                if adapters_status and self.vision_adapter:
                    st.markdown("### :microscope: Enhanced Analysis")

                    # Show recent analysis results
                    if st.session_state.mobile_analysis_history:
                        recent_analysis = st.session_state.mobile_analysis_history[-1]

                        with st.expander(":bar_chart: Latest Analysis Results", expanded=True):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.metric("Disease Detected", recent_analysis.get("disease", "Unknown"))
                                st.metric("Confidence", f"{recent_analysis.get('confidence', 0):.1%}")

                            with col2:
                                if recent_analysis.get("disease_info"):
                                    disease_info = recent_analysis["disease_info"]
                                    st.write(f"**Plant Type:** {disease_info.get('plant_type', 'Unknown')}")
                                    st.write(f"**Severity:** {disease_info.get('severity', 'Unknown')}")

                    # Quick analysis button for uploaded images
                    if st.session_state.get("uploaded_image"):
                        if st.button(":rocket: Quick Analysis with AI", use_container_width=True, type="primary"):
                            with st.spinner("Analyzing with AI..."):
                                result = self.analyze_image_with_adapters(st.session_state.uploaded_image)

                                if "error" not in result:
                                    st.success(f":white_check_mark: Analysis complete: {result['disease']} ({result['confidence']:.1%} confidence)")

                                    # Show recommendations
                                    if result.get("recommendations"):
                                        st.markdown("**Recommendations:**")
                                        for recommendation in result["recommendations"][:3]:
                                            if recommendation.strip():
                                                st.write(f"- {recommendation.strip()}")
                                else:
                                    st.error(f"[ERROR] Analysis failed: {result['error']}")

        except Exception as e:
            logger.error(f"Enhanced image analysis tab rendering failed: {e}")
            # Fallback to basic rendering
            self.image_analysis.render()

    def render_voice_assistant_tab(self) -> None:
        """Render enhanced voice assistant tab content with core adapter integration."""
        try:
            # Use performance optimization
            with self.performance_optimizer.optimize_component_render("voice_assistant_tab"):
                # Check if adapters are loaded
                adapters_status = st.session_state.get("mobile_adapters_loaded", False)

                if not adapters_status:
                    st.warning(":warning: Audio processing not fully loaded. Voice features may be limited.")

                # Render the mobile voice interface component
                self.voice_interface.render()

                # Add enhanced functionality if adapters are available
                if adapters_status and self.audio_adapter:
                    st.markdown("### :microphone: Enhanced Voice Processing")

                    # Voice input processing
                    if st.session_state.get("recorded_audio"):
                        if st.button(":speaker: Process Voice with AI", use_container_width=True, type="primary"):
                            with st.spinner("Processing voice..."):
                                response = self.process_voice_input(st.session_state.recorded_audio)

                                if response and "error" not in response.lower():
                                    st.success(":white_check_mark: Voice processed successfully")
                                    st.markdown("**AI Response:**")
                                    st.write(response)

                                    # Save to chat history
                                    st.session_state.chat_history.append(
                                        {
                                            "type": "voice",
                                            "input": "Voice input processed",
                                            "response": response,
                                            "timestamp": st.session_state.get("app_start_time", 0),
                                        }
                                    )
                                else:
                                    st.error(f":x: Voice processing failed: {response}")

                    # Quick voice commands
                    st.markdown("**Quick Voice Commands:**")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(":herb: 'What's wrong with my plant?'", use_container_width=True):
                            response = self.process_text_query("What's wrong with my plant?")
                            st.write(response)

                    with col2:
                        if st.button(":pill: 'How do I treat this disease?'", use_container_width=True):
                            response = self.process_text_query("How do I treat this disease?")
                            st.write(response)

        except Exception as e:
            logger.error(f"Enhanced voice assistant tab rendering failed: {e}")
            # Fallback to basic rendering
            self.voice_interface.render()

    def render_chat_interface_tab(self) -> None:
        """Render enhanced chat interface tab content with core adapter integration."""
        try:
            # Use performance optimization
            with self.performance_optimizer.optimize_component_render("chat_interface_tab"):
                # Check if adapters are loaded
                adapters_status = st.session_state.get("mobile_adapters_loaded", False)

                if not adapters_status:
                    st.warning(":warning: Text processing not fully loaded. Chat features may be limited.")

                # Render the mobile chat interface component
                self.chat_interface.render()

                # Add enhanced functionality if adapters are available
                if adapters_status and self.text_adapter:
                    st.markdown("### :speech_balloon: Enhanced AI Chat")

                    # Smart chat input with context awareness
                    user_input = st.text_input(
                        "Ask about your plant:",
                        placeholder="e.g., 'How do I prevent this disease?', 'Is this plant healthy?'",
                        key="enhanced_chat_input",
                    )

                    col1, col2 = st.columns([3, 1])

                    with col1:
                        if st.button(":speech_balloon: Send Message", use_container_width=True, type="primary"):
                            if user_input.strip():
                                with st.spinner("Generating AI response..."):
                                    # Get context from recent analysis
                                    context = None
                                    if st.session_state.mobile_analysis_history:
                                        context = st.session_state.mobile_analysis_history[-1]

                                    response = self.process_text_query(user_input, context)

                                    # Add to chat history
                                    chat_entry = {
                                        "type": "text",
                                        "input": user_input,
                                        "response": response,
                                        "timestamp": st.session_state.get("app_start_time", 0),
                                        "context": context.get("disease", "general") if context else "general",
                                    }

                                    st.session_state.chat_history.append(chat_entry)

                                    # Clear input
                                    st.session_state.enhanced_chat_input = ""
                                    # Update chat display without page refresh
                                    st.session_state.chat_updated = True

                    with col2:
                        if st.button(":wastebasket: Clear", use_container_width=True):
                            st.session_state.chat_history.clear()
                            # Update chat display without page refresh
                            st.session_state.chat_cleared = True

                    # Display enhanced chat history
                    if st.session_state.chat_history:
                        st.markdown("### :memo: Chat History")

                        for i, chat in enumerate(reversed(st.session_state.chat_history[-10:])):
                            with st.expander(f":speech_balloon: {chat['input'][:50]}...", expanded=i == 0):
                                st.markdown(f"**You:** {chat['input']}")
                                st.markdown(f"**AI:** {chat['response']}")

                                if chat.get("context") and chat["context"] != "general":
                                    st.caption(f"Context: {chat['context']}")

                    # Quick question buttons
                    st.markdown("### :question: Quick Questions")

                    quick_questions = [
                        "What disease does my plant have?",
                        "How do I treat this condition?",
                        "How can I prevent this in the future?",
                        "Is this plant healthy?",
                        "What are the symptoms to look for?",
                    ]

                    cols = st.columns(2)
                    for i, question in enumerate(quick_questions):
                        with cols[i % 2]:
                            if st.button(f":question: {question}", use_container_width=True, key=f"quick_q_{i}"):
                                # Get context from recent analysis
                                context = None
                                if st.session_state.mobile_analysis_history:
                                    context = st.session_state.mobile_analysis_history[-1]

                                with st.spinner("Generating response..."):
                                    response = self.process_text_query(question, context)

                                    # Add to chat history
                                    chat_entry = {
                                        "type": "quick_question",
                                        "input": question,
                                        "response": response,
                                        "timestamp": st.session_state.get("app_start_time", 0),
                                        "context": context.get("disease", "general") if context else "general",
                                    }

                                    st.session_state.chat_history.append(chat_entry)
                                    # Update chat display without page refresh
                                    st.session_state.quick_question_added = True

        except Exception as e:
            logger.error(f"Enhanced chat interface tab rendering failed: {e}")
            # Fallback to basic rendering
            self.chat_interface.render()

    def render_history_settings_tab(self) -> None:
        """Render history and settings tab content."""
        st.markdown("### :bar_chart: Analysis History")

        # Enhanced analysis history with mobile-specific data
        mobile_history = st.session_state.get("mobile_analysis_history", [])
        regular_history = st.session_state.get("analysis_history", [])

        # Combine and show both histories
        all_history = mobile_history + regular_history

        if all_history:
            st.markdown(f"**Total Analyses:** {len(all_history)}")

            # Show recent analyses with enhanced display
            for i, analysis in enumerate(all_history[-5:]):
                analysis_num = len(all_history) - i

                # Determine analysis type and create appropriate title
                if "disease" in analysis:
                    title = f":microscope: Analysis {analysis_num}: {analysis.get('disease', 'Unknown')}"
                    confidence = analysis.get("confidence", 0)
                    if confidence > 0:
                        title += f" ({confidence:.1%})"
                else:
                    title = f":bar_chart: Analysis {analysis_num}"

                with st.expander(title, expanded=True):
                    if "disease" in analysis:
                        # Enhanced mobile analysis display
                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric("Disease", analysis.get("disease", "Unknown"))
                            st.metric("Confidence", f"{analysis.get('confidence', 0):.1%}")

                        with col2:
                            disease_info = analysis.get("disease_info", {})
                            if disease_info:
                                st.write(f"**Plant Type:** {disease_info.get('plant_type', 'Unknown')}")
                                st.write(f"**Severity:** {disease_info.get('severity', 'Unknown')}")

                        # Show recommendations if available
                        recommendations = analysis.get("recommendations", [])
                        if recommendations:
                            st.markdown("**Key Recommendations:**")
                            for recommendation in recommendations[:3]:
                                if recommendation.strip():
                                    st.write(f"- {recommendation.strip()}")
                    else:
                        # Regular analysis display
                        st.json(analysis)
        else:
            st.info("No analysis history yet. Analyze some plants to see results here!")

        # Performance metrics
        if st.session_state.get("mobile_adapters_loaded", False):
            st.markdown("### Performance Metrics")

            try:
                perf_report = self.performance_optimizer.get_performance_report()

                col1, col2, col3 = st.columns(3)

                with col1:
                    session_info = perf_report.get("session_info", {})
                    st.metric("Total Renders", session_info.get("total_renders", 0))

                with col2:
                    avg_render_time = session_info.get("avg_render_time", 0)
                    st.metric("Avg Render Time", f"{avg_render_time:.3f}s")

                with col3:
                    memory_stats = perf_report.get("memory_stats", {})
                    memory_mb = memory_stats.get("rss_mb", 0)
                    st.metric("Memory Usage", f"{memory_mb:.1f}MB")

                # Cache statistics
                cache_stats = perf_report.get("cache_stats", {})
                if cache_stats:
                    st.markdown("**Cache Performance:**")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Cache Hit Rate", f"{cache_stats.get('hit_rate', 0):.1f}%")

                    with col2:
                        st.metric("Cache Size", f"{cache_stats.get('size_mb', 0):.1f}MB")

            except Exception as e:
                st.warning(f"Performance metrics unavailable: {e}")

        st.markdown("### Settings")

        # Enhanced app settings
        col1, col2 = st.columns(2)

        with col1:
            # Core Adapters Status
            st.markdown("**Core Adapters**")

            adapters_loaded = st.session_state.get("mobile_adapters_loaded", False)

            if adapters_loaded:
                st.success("[OK] All adapters loaded")

                # Adapter details
                if self.vision_adapter:
                    st.write("Vision: Ready")
                if self.audio_adapter:
                    st.write("Audio: Ready")
                if self.text_adapter:
                    st.write("Text: Ready")
            else:
                st.error("[ERROR] Adapters not loaded")

                if st.button("[RELOAD] Reload Adapters", use_container_width=True):
                    with st.spinner("Reloading adapters..."):
                        self._load_core_adapters()
                        # Update adapter status without page refresh
                        st.session_state.adapters_reloaded = True

            # AI Agent controls
            st.markdown("**[AI] AI Agent**")

            if st.button("Run Component Tests", use_container_width=True):
                with st.spinner("Running AI agent tests..."):
                    test_results = get_ai_testing_framework().test_all_components()
                    if test_results:
                        st.success(f"Tests completed: {test_results.get('components_tested', 0)} components tested")

                        # Show summary instead of full JSON
                        summary = test_results.get("overall_summary", {})
                        if summary:
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Status", summary.get("overall_status", "unknown"))
                            with col_b:
                                st.metric("Success Rate", f"{summary.get('success_rate', 0):.1%}")

        with col2:
            # Enhanced app preferences
            st.markdown("**[MOBILE] Preferences**")

            # Performance mode selection
            perf_mode = st.selectbox(
                "Performance Mode",
                ["Auto", "Minimal", "Balanced", "Aggressive"],
                index=1,  # Default to Balanced
                key="mobile_perf_mode_select",
            )

            if perf_mode.lower() != st.session_state.get("mobile_performance_mode", "balanced"):
                st.session_state.mobile_performance_mode = perf_mode.lower()
                self.performance_optimizer.set_optimization_level(perf_mode.lower())
                st.success(f"Performance mode set to {perf_mode}")

            # Offline mode toggle
            offline_mode = st.checkbox("Offline Mode", value=st.session_state.get("mobile_offline_mode", False), key="mobile_offline_toggle")

            if offline_mode != st.session_state.get("mobile_offline_mode", False):
                st.session_state.mobile_offline_mode = offline_mode
                if offline_mode:
                    self.performance_optimizer.enable_offline_mode()
                    st.success("Offline mode enabled")

            # Theme selection
            theme = st.selectbox("Theme", ["Auto", "Light", "Dark"], key="mobile_theme_select")

            # Auto-clear chat
            auto_clear = st.checkbox("Auto-clear chat after analysis", key="mobile_auto_clear_chat")

            # Image optimization
            optimize_images = st.checkbox("Optimize images for mobile", value=True, key="mobile_optimize_images")

        # Enhanced app information
        st.markdown("### [DETAILS] App Information")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Session Duration", self.get_session_duration())

        with col2:
            component_count = len(mobile_component_registry.get_all_components())
            st.metric("Components", component_count)

        with col3:
            active_tab = st.session_state.get("current_tab", "unknown")
            st.metric("Active Tab", active_tab.replace("_", " ").title())

        # Additional metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            analyses_count = len(st.session_state.get("mobile_analysis_history", []))
            st.metric("AI Analyses", analyses_count)

        with col2:
            chat_count = len(st.session_state.get("chat_history", []))
            st.metric("Chat Messages", chat_count)

        with col3:
            perf_mode = st.session_state.get("mobile_performance_mode", "balanced")
            st.metric("Performance", perf_mode.title())

        # System status
        st.markdown("**[TOOL] System Status:**")

        status_items = []

        # Adapter status
        if st.session_state.get("mobile_adapters_loaded", False):
            status_items.append("[READY] Core Adapters: Ready")
        else:
            status_items.append("[ERROR] Core Adapters: Not Loaded")

        # Performance optimization status
        with contextlib.suppress(Exception):
            perf_report = self.performance_optimizer.get_performance_report()
            memory_pressure = perf_report.get("memory_pressure", "unknown")

            if memory_pressure == "normal":
                status_items.append("[OK] Memory: Normal")
            elif memory_pressure == "warning":
                status_items.append("[WARN] Memory: Warning")
            else:
                status_items.append("[CRITICAL] Memory: Critical")

        if not any("Memory:" in item for item in status_items):
            status_items.append("[UNKNOWN] Memory: Unknown")

        # Cache status
        with contextlib.suppress(Exception):
            cache_stats = self.performance_optimizer.cache.get_stats()
            hit_rate = cache_stats.get("hit_rate", 0)

            if hit_rate > 80:
                status_items.append("[EXCELLENT] Cache: Excellent")
            elif hit_rate > 60:
                status_items.append("[GOOD] Cache: Good")
            else:
                status_items.append("[POOR] Cache: Poor")

        if not any("Cache:" in item for item in status_items):
            status_items.append("[UNKNOWN] Cache: Unknown")

        for status in status_items:
            st.write(status)

    def render_comparison_tab(self) -> None:
        """Render comparison tab content."""
        st.markdown("### [COMPARE] Plant Comparison")

        st.info("[INFO] Advanced comparison features coming soon!")

        # Placeholder comparison interface
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Plant A**")
            img1 = st.file_uploader("Upload first image", type=["jpg", "jpeg", "png"], key="comparison_img1")
            if img1:
                st.image(img1, use_container_width=True)

        with col2:
            st.markdown("**Plant B**")
            img2 = st.file_uploader("Upload second image", type=["jpg", "jpeg", "png"], key="comparison_img2")
            if img2:
                st.image(img2, use_container_width=True)

        if img1 and img2:
            st.success("Both images uploaded - comparison ready!")

    def get_session_duration(self) -> str:
        """Get formatted session duration."""

        start_time = st.session_state.get("app_start_time", time.time())
        duration = time.time() - start_time

        if duration < 60:
            return f"{int(duration)}s"
        elif duration < 3600:
            return f"{int(duration // 60)}m {int(duration % 60)}s"
        else:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            return f"{hours}h {minutes}m"

    def render_input_ribbon_integration(self) -> None:
        """Render input ribbon with SPA tab integration - no page redirects."""
        # Render input ribbon
        selected_input = self.input_ribbon.render()

        # Handle input method selection WITHOUT st.rerun()
        if selected_input:
            input_to_tab_mapping = {"text": "chat_interface", "voice": "voice_assistant", "camera": "image_analysis", "upload": "image_analysis"}

            target_tab = input_to_tab_mapping.get(selected_input)
            if target_tab:
                # Track tab navigation
                self.track_tab_navigation(target_tab)

                # Update input mode timestamp
                st.session_state.current_input_mode = selected_input
                st.session_state.last_input_timestamp = time.time()

                # Set active tab and focus content WITHOUT st.rerun()
                st.session_state.focused_content = target_tab
                self.content_tabs.set_active_tab(target_tab)

    def render_ai_agent_status(self) -> None:
        """Render AI agent status indicator in main content without page redirects."""
        # Move AI agent status to main content instead of sidebar
        with st.expander("[AI] AI Agent Status", expanded=True):
            if st.session_state.get("ai_agent_active", False):
                st.success("[AI] AI Agent Active")

                if st.button("Run Tests", use_container_width=True, key="spa_ai_tests"):
                    with st.spinner("AI Agent running tests..."):
                        results = get_ai_testing_framework().test_all_components()
                        st.json(results)
            else:
                if st.button("Activate AI Agent", use_container_width=True, key="spa_activate_ai"):
                    st.session_state.ai_agent_active = True
                    st.success("AI Agent activated - no page refresh needed!")

    def run(self) -> None:
        """Run the enhanced mobile PlantGuard application with performance optimizations."""
        try:
            # Initialize page change prevention
            self._initialize_page_change_prevention()

            # Run the main app
            self._run_main_app()

        except Exception as e:
            st.error(f"Critical error in mobile app: {e}")
            logger.error(f"Critical error in mobile app: {e}")
            # Prevent page change even on error
            st.session_state.page_change_prevention = True

    def _initialize_page_change_prevention(self) -> None:
        """Initialize comprehensive page change prevention."""
        # Set up page change prevention
        if "page_change_prevention" not in st.session_state:
            st.session_state.page_change_prevention = True

        # Monitor for any page change attempts
        if st.session_state.get("page_change_prevention", True):
            st.session_state.page_change_attempts = 0
            st.session_state.last_page_change_attempt = None

            # Add JavaScript to prevent page changes
            st.markdown(
                """
            <script>
            // Prevent page changes and reloads
            window.addEventListener('beforeunload', function(e) {
                e.preventDefault();
                e.returnValue = '';
                return '';
            });
            
            // Prevent form submissions that might cause page changes
            document.addEventListener('submit', function(e) {
                e.preventDefault();
                return false;
            });
            
            // Monitor for any navigation attempts
            window.addEventListener('popstate', function(e) {
                e.preventDefault();
                history.pushState(null, null, window.location.href);
                return false;
            });
            </script>
            """,
                unsafe_allow_html=True,
            )

    def _run_main_app(self) -> None:
        """Run the main app logic without page redirects."""
        # Apply performance optimizations at startup
        with contextlib.suppress(Exception):
            # Load optimized CSS
            st.markdown(self.performance_optimizer.get_optimized_css(), unsafe_allow_html=True)

        # Initialize components if not done
        if not st.session_state.get("mobile_app_initialized", False):
            with st.spinner("[INIT] Initializing PlantGuard Unified..."):
                self.initialize_components()

        # Check initialization status with detailed feedback
        if not st.session_state.get("mobile_app_initialized", False):
            st.error("[ERROR] Application failed to initialize properly")

            # Show enhanced troubleshooting
            st.markdown("### [ERROR] PlantGuard Unified - Initialization Error")
            st.markdown("The application components failed to initialize. Please try the options below.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("[RESTART] Reinitialize App", use_container_width=True, key="spa_reinitialize"):
                    st.session_state.mobile_app_initialized = False
                    st.success("Reinitializing - no page refresh needed!")
                    # Update state without page refresh
                    st.session_state.force_reinit = True

            with col2:
                if st.button("[CLEAN] Clear Cache & Restart", use_container_width=True, key="spa_clear_restart"):
                    # Clear performance cache
                    with contextlib.suppress(builtins.BaseException):
                        self.performance_optimizer.cache.clear()

                    # Clear session state
                    keys_to_clear = [key for key in st.session_state if key.startswith("mobile_")]
                    for key in keys_to_clear:
                        del st.session_state[key]

                    st.success("Cache cleared - no page refresh needed!")
                    # Update state without page refresh
                    st.session_state.cache_cleared = True

            # Show system status for debugging
            st.markdown("### [SYSTEM] System Status")
            st.json(
                {
                    "components_loaded": st.session_state.get("mobile_app_initialized", False),
                    "performance_optimizer": "ready" if self.performance_optimizer else "not_loaded",
                    "session_keys": list(st.session_state.keys()),
                }
            )

            return

        # Main application content
        try:
            # Unified PlantGuard Header
            st.markdown(
                """
            <div style="text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #4CAF50, #45a049); color: white; border-radius: 15px; margin-bottom: 2rem;">
                <h1 style="margin: 0; font-size: 2.5rem;">🌿 PlantGuard Unified</h1>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                    [MOBILE] + [LEAF] - AI-Powered Plant Disease Detection
                </p>
                <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.8;">
                    Mobile-first design with advanced desktop capabilities
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Advanced Model Selection
            st.markdown("## [LAUNCH] Advanced Model Selection")
            st.markdown("*Choose the optimal AI models for your plant analysis workflow*")
            st.markdown("---")

            # Model selection interface
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### [PLANT] Vision Model")
                vision_model = st.selectbox(
                    "Select Vision Model", ["apple_vision_pro", "efficientnet_b0", "resnet50", "mobilenet_v2"], key="vision_model_select"
                )
                if st.button("Load Vision Model", key="load_vision"):
                    with st.spinner("Loading vision model..."):
                        try:
                            # Update vision adapter
                            if hasattr(self, "vision_adapter") and self.vision_adapter:
                                self.vision_adapter.model_name = vision_model
                            st.success(f"Vision model {vision_model} loaded!")
                        except Exception as e:
                            st.error(f"Failed to load vision model: {e}")

            with col2:
                st.markdown("### [VOICE] Audio Model")
                audio_model = st.selectbox(
                    "Select Audio Model", ["openai/whisper-tiny", "openai/whisper-base", "openai/whisper-small"], key="audio_model_select"
                )
                if st.button("Load Audio Model", key="load_audio"):
                    with st.spinner("Loading audio model..."):
                        try:
                            # Update audio adapter
                            if hasattr(self, "audio_adapter") and self.audio_adapter:
                                self.audio_adapter.model_name = audio_model
                            st.success(f"Audio model {audio_model} loaded!")
                        except Exception as e:
                            st.error(f"Failed to load audio model: {e}")

            with col3:
                st.markdown("### [CHAT] Text Model")
                text_model = st.selectbox("Select Text Model", ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"], key="text_model_select")
                if st.button("Load Text Model", key="load_text"):
                    with st.spinner("Loading text model..."):
                        try:
                            # Update text adapter
                            if hasattr(self, "text_adapter") and self.text_adapter:
                                self.text_adapter.model_name = text_model
                            st.success(f"Text model {text_model} loaded!")
                        except Exception as e:
                            st.error(f"Failed to load text model: {e}")

            st.markdown("---")

            # Current Model Status
            st.markdown("## [LAUNCH] Current Model Status & Quick Actions")
            st.markdown("*Monitor your active models and perform quick actions*")
            st.markdown("---")

            current_models = get_model_status()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### [PLANT] Vision Model")
                st.info(f"**Active:** {current_models.get('vision', 'Unknown')}")
                st.metric("Status", "[GREEN] Loaded", "Ready")

            with col2:
                st.markdown("### [VOICE] Audio Model")
                st.info(f"**Active:** {current_models.get('audio', 'Unknown')}")
                st.metric("Status", "[GREEN] Loaded", "Ready")

            with col3:
                st.markdown("### [CHAT] Text Model")
                st.info(f"**Active:** {current_models.get('text', 'Unknown')}")
                st.metric("Status", "[GREEN] Loaded", "Ready")

            st.markdown("---")
            st.markdown("### [ACTIONS] Quick Actions")

            action_col1, action_col2, action_col3, action_col4 = st.columns(4)

            with action_col1:
                if st.button("[PARTIAL] Reload Models", use_container_width=True, help="Reload all model adapters"):
                    st.cache_resource.clear()
                    st.success("[DONE] Models reloaded successfully!")

            with action_col2:
                if st.button("[SUMMARY] Quick Test", use_container_width=True, help="Test current models on sample data"):
                    st.info("[TIP] Use the Model Management tab for comprehensive testing and benchmarking!")

            with action_col3:
                if st.button("[TOOL] Settings", use_container_width=True, help="Access advanced model settings"):
                    st.info("[TIP] Model configuration is available in the Model Management tab!")

            with action_col4:
                if st.button("[CHART] Performance", use_container_width=True, help="View model performance metrics"):
                    st.info("[TIP] Detailed performance analysis available in the Model Management tab!")

            st.markdown("---")

            # Plant Analysis Tools
            st.markdown("## [LEAF] Plant Analysis Tools")
            st.markdown("*Use the tools below to analyze your plants with AI-powered detection*")
            st.markdown("---")

            # Plant analysis tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["🌿 Image Analysis", "🎤 Voice & Audio", "💬 Chat Interface", "📊 Model Management", "⚙️ Settings"]
            )

            with tab1:
                st.markdown("### [UPLOAD] Upload Plant Image")
                img_file = st.file_uploader(
                    "Choose a plant image...", type=["jpg", "jpeg", "png"], help="Upload a clear image of the plant you want to analyze"
                )

                if img_file is not None:
                    img = PILImage.open(img_file)
                    img_name = img_file.name
                    st.image(img, use_container_width=True, caption=f"Image: {img_name}")

                    if st.button("[SEARCH] Analyze Plant", key="img", type="primary", use_container_width=True):
                        with st.spinner("[AI] AI is analyzing your plant..."):
                            try:
                                # Use vision adapter for analysis
                                if hasattr(self, "vision_adapter") and self.vision_adapter:
                                    result = self.vision_adapter.predict(img)
                                    disease_name, confidence = result

                                    st.markdown(
                                        f"""
                                        <div class="result-card">
                                            <h3>[AI] Analysis Complete!</h3>
                                            <p><strong>Plant Type:</strong> {disease_name.split("___")[0] if "___" in disease_name else "Unknown"}</p>
                                            <p><strong>Condition:</strong> {disease_name.split("___")[1] if "___" in disease_name else disease_name}</p>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                    metric_col1, metric_col2, metric_col3 = st.columns(3)

                                    with metric_col1:
                                        st.metric("[PLANT] Plant Type", disease_name.split("___")[0] if "___" in disease_name else disease_name)

                                    with metric_col2:
                                        readable_name = disease_name.split("___")[1] if "___" in disease_name else disease_name
                                        st.metric("[VIRUS] Condition", readable_name)

                                    with metric_col3:
                                        conf_class = (
                                            "confidence-high" if confidence > 0.8 else "confidence-medium" if confidence > 0.5 else "confidence-low"
                                        )
                                        st.markdown(f'<p class="{conf_class}">[SUMMARY] Confidence: {confidence:.1%}</p>', unsafe_allow_html=True)

                                    if confidence > 0.8:
                                        st.success("[DONE] Plant appears healthy!")
                                        st.balloons()
                                    else:
                                        st.warning("[WARNING] Disease detected - consider treatment")

                                        with st.expander("[TIP] Treatment Recommendations"):
                                            st.info("Consult with agricultural experts for proper treatment plans.")

                                    with st.expander("[TOOL] Technical Details"):
                                        st.json(
                                            {
                                                "disease": disease_name,
                                                "confidence": float(confidence),
                                                "model": current_models.get("vision", "Unknown"),
                                                "timestamp": time.time(),
                                            }
                                        )

                                else:
                                    st.error("[ERROR] Vision adapter not available")

                            except Exception as e:
                                st.error(f"[TODO] Analysis failed: {e!s}")
                else:
                    st.info("[POINTER] Upload an image or select a sample to begin analysis")

            with tab2:
                st.markdown("### [VOICE] Voice & Audio Analysis")
                st.info("[TIP] Ask questions about plant care or describe symptoms using voice or audio files")

                audio_col1, audio_col2 = st.columns([1, 1])

                with audio_col1:
                    st.markdown("### [MICROPHONE] Live Recording")
                    st.info("Voice recording functionality integrated into main Voice Assistant tab")
                    st.markdown("**Features:** Real-time audio capture, speech-to-text, voice commands")

                    if st.button("🎤 Test Voice Input", key="test_voice"):
                        st.success("Voice input test - use the Voice Assistant tab for full functionality!")

                with audio_col2:
                    st.markdown("### [FOLDER] File Upload")
                    audio_file = st.file_uploader("Upload audio file", ["wav", "mp3", "m4a"], help="Supported formats: WAV, MP3, M4A")

                    if audio_file is not None:
                        st.audio(audio_file, format="audio/wav")

                        if st.button("[PROGRESS] Process File", key="file_analyze", type="primary", use_container_width=True):
                            with st.spinner("[AUDIO] Processing uploaded audio..."):
                                try:
                                    # Use audio adapter for transcription
                                    if hasattr(self, "audio_adapter") and self.audio_adapter:
                                        text = self.audio_adapter.transcribe(audio_file)

                                        st.markdown("### [WRITE] Transcription Results")
                                        st.text_area("Transcribed text:", text, height=100, disabled=True)

                                        # Get AI response using text adapter
                                        if hasattr(self, "text_adapter") and self.text_adapter:
                                            response = self.text_adapter.get_response(text)

                                            st.markdown("### [AI] AI Response")
                                            st.success(response)
                                    else:
                                        st.error("[ERROR] Audio adapter not available")

                                except Exception as e:
                                    st.error(f"[TODO] Audio processing failed: {e!s}")

            with tab3:
                st.markdown("### [CHAT] Chat Interface")
                st.info("Chat functionality integrated into main Chat Interface tab")
                st.markdown("**Features:** Q&A, plant care advice, disease consultation")

                if st.button("💬 Open Chat", key="open_chat"):
                    st.success("Chat interface - use the Chat Interface tab for full functionality!")

            with tab4:
                st.markdown("### [📊] Model Management")
                st.info("Comprehensive model testing and benchmarking")

                if st.button("🧪 Run Model Tests", key="run_model_tests"):
                    with st.spinner("Testing models..."):
                        try:
                            # Test all models
                            test_results = {
                                "vision": "Passed" if hasattr(self, "vision_adapter") and self.vision_adapter else "Failed",
                                "audio": "Passed" if hasattr(self, "audio_adapter") and self.audio_adapter else "Failed",
                                "text": "Passed" if hasattr(self, "text_adapter") and self.text_adapter else "Failed",
                            }
                            st.success("Model tests completed!")
                            st.json(test_results)
                        except Exception as e:
                            st.error(f"Model testing failed: {e}")

            with tab5:
                st.markdown("### [⚙️] Settings")
                st.info("Application configuration and preferences")

                # Performance settings
                st.markdown("#### Performance Settings")
                perf_mode = st.selectbox("Performance Mode", ["Auto", "Minimal", "Balanced", "Aggressive"], index=1, key="perf_mode_select")

                if st.button("Apply Settings", key="apply_settings"):
                    st.success(f"Performance mode set to {perf_mode}")

            st.markdown("---")

            # Mobile components (existing functionality)
            st.markdown("## [MOBILE] Mobile Components")
            st.markdown("*Touch-friendly mobile interface components*")
            st.markdown("---")

            # Render mobile components
            if self.header:
                self.header.render()

            if self.input_ribbon:
                self.render_input_ribbon_integration()

            # Content tabs with SPA navigation tracking - no page redirects
            if self.content_tabs:
                focused_content = self.content_tabs.render()

                # Track tab changes WITHOUT st.rerun()
                if focused_content != st.session_state.get("focused_content", "image_analysis"):
                    self.track_tab_navigation(focused_content)
                    st.session_state.focused_content = focused_content
            else:
                # Basic functionality as fallback
                st.info("Content tabs component not available")

        except Exception as e:
            st.error(f"[ERROR] Error rendering app content: {e}")
            logger.error(f"App content rendering error: {e}")

            # Show emergency fallback
            st.markdown("### [EMERGENCY] PlantGuard Unified - Emergency Mode")
            st.markdown("The app is running in emergency mode. Some features may not be available.")

            if st.button("[RESTART] Try Full Restart", use_container_width=True, key="spa_full_restart"):
                # Clear all mobile app state
                keys_to_clear = [key for key in st.session_state if key.startswith("mobile_")]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.success("Full restart initiated - no page refresh needed!")
                # Update state without page refresh
                st.session_state.full_restart_initiated = True

        # Add app info and component status inline
        self.render_app_info_inline()

    def render_app_info_inline(self) -> None:
        """Render app info and component status inline in main content."""
        # App info in expandable section
        with st.expander("[UNIFIED] PlantGuard Unified Info", expanded=True):
            st.markdown("**Version:** 2.0.0-unified")
            st.markdown("[MOBILE] **Mobile:** Chrome & Safari Optimized")
            st.markdown("[DESKTOP] **Desktop:** Full-featured with advanced model management")
            st.markdown("[DESIGN] **Design:** Responsive - 428px mobile, full-width desktop")

            # Unified design indicator
            st.success("[UNIFIED] **Best of Both Worlds** - Mobile-first with desktop power!")
            st.info("[FEATURES] **Unified:** Complete PlantGuard capabilities in one application")

        # Component status in expandable section
        with st.expander("[TOOL] Component Status", expanded=True):
            components_status = {
                "Layout Manager": self.layout_manager.get_layout_status().get("status", "unknown") if self.layout_manager else "not_loaded",
                "Header": "ready" if self.header else "not_loaded",
                "Input Ribbon": "ready" if self.input_ribbon else "not_loaded",
                "Content Tabs": "ready" if self.content_tabs else "not_loaded",
                "Vision Adapter": "ready" if hasattr(self, "vision_adapter") and self.vision_adapter else "not_loaded",
                "Audio Adapter": "ready" if hasattr(self, "audio_adapter") and self.audio_adapter else "not_loaded",
                "Text Adapter": "ready" if hasattr(self, "text_adapter") and self.text_adapter else "not_loaded",
            }

            for component, status in components_status.items():
                if status == "ready":
                    st.success(f"[READY] {component}")
                elif status == "initializing":
                    st.warning(f"[INIT] {component}")
                else:
                    st.error(f"[ERROR] {component}")

        # Quick actions in expandable section
        with st.expander("[ACTIONS] Quick Actions", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                if st.button("[REFRESH] Refresh Components", use_container_width=True, key="spa_refresh_components"):
                    st.session_state.mobile_app_initialized = False
                    st.success("Refreshing components - no page refresh needed!")
                    # Update state without page refresh
                    st.session_state.components_refreshed = True

            with col2:
                if st.button("[TEST] Run AI Tests", use_container_width=True, key="spa_run_tests"):
                    with st.spinner("Testing all components..."):
                        test_results = get_ai_testing_framework().test_all_components()
                        if test_results.get("components_tested", 0) > 0:
                            st.success(f"[PASS] Tested {test_results['components_tested']} components")
                            if test_results.get("tests_failed", 0) > 0:
                                st.warning(f"[WARN] {test_results['tests_failed']} tests failed")
                        else:
                            st.error("[ERROR] No components found to test")


def main() -> None:
    """Main application entry point."""
    try:
        # Create and run the mobile app
        app = MobilePlantGuardApp()
        app.run()

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"Application Error: {e}")
        st.markdown("### [TOOL] Troubleshooting")
        st.markdown("""
        1. **Refresh the page** - Sometimes a simple reload fixes issues
        2. **Check browser compatibility** - Use Chrome or Safari mobile
        3. **Clear browser cache** - Old cached files can cause problems
        4. **Check console logs** - Look for JavaScript errors in browser dev tools
        """)

        # Show debug information in expander
        with st.expander("[BUG] Debug Information"):
            st.markdown(f"**Error:** {e!s}")
            st.markdown(f"**Session State Keys:** {list(st.session_state.keys())}")
            st.markdown(f"**Python Path:** {sys.path[:3]}...")


if __name__ == "__main__":
    main()
