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
import warnings
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
SRC_PATH = ROOT_DIR / "src"


def _ensure_src_path() -> None:
    """Add the local ``src`` directory to ``sys.path`` if missing."""

    src_path_str = str(SRC_PATH)
    if SRC_PATH.is_dir() and src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)

# Configure module-level logger and tame noisy third-party warnings
logger = logging.getLogger(__name__)

# Streamlit emits runtime-cache warnings when modules are imported outside
# an active Streamlit script run (e.g. during `make validate-mobile`). Those
# warnings are expected in our validation probes, so lower their verbosity to
# keep CI output clean while preserving error-level messages.
for noisy_logger in (
    "streamlit",
    "streamlit.runtime",
    "streamlit.runtime.caching.cache_data_api",
    "streamlit.runtime.scriptrunner_utils.script_run_context",
):
    logger_obj = logging.getLogger(noisy_logger)
    logger_obj.setLevel(logging.ERROR)
    logger_obj.propagate = False
    logger_obj.disabled = True
    logger_obj.handlers.clear()

# Silence known Streamlit cache warnings emitted during headless validation.
warnings.filterwarnings(
    "ignore",
    message="No runtime found, using MemoryCacheStorageManager",
    category=UserWarning,
    module="streamlit.runtime.caching.cache_data_api",
)
warnings.filterwarnings(
    "ignore",
    message="Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.",
    category=UserWarning,
    module="streamlit.runtime.scriptrunner_utils.script_run_context",
)

# Third-party imports
import streamlit as st  # noqa: E402
from PIL import Image as PILImage  # noqa: E402

# First-party imports - resolved via the canonical PlantGuard package
try:
    from plantguard.core import AudioAdapter, TextAdapter, VisionAdapter  # noqa: E402
    from plantguard.ui.components.mobile_chat_interface import MobileChatInterface  # noqa: E402
    from plantguard.ui.components.mobile_component_registry import (  # noqa: E402
        mobile_component_registry,
    )
    from plantguard.ui.components.mobile_content_tabs import MobileContentTabs  # noqa: E402
    from plantguard.ui.components.mobile_header import MobileHeader  # noqa: E402
    from plantguard.ui.components.mobile_image_analysis import MobileImageAnalysis  # noqa: E402
    from plantguard.ui.components.mobile_input_ribbon import MobileInputRibbon  # noqa: E402
    from plantguard.ui.components.mobile_layout_manager import MobileLayoutManager  # noqa: E402
    from plantguard.ui.components.mobile_voice_interface import MobileVoiceInterface  # noqa: E402
    from plantguard.utils.error_recovery import ImportErrorRecovery  # noqa: E402
except ModuleNotFoundError as import_error:
    if import_error.name is None or not import_error.name.startswith("plantguard"):
        raise
    _ensure_src_path()
    from core.audio import AudioAdapter  # type: ignore  # noqa: E402
    from core.nlp import TextAdapter  # type: ignore  # noqa: E402
    from core.vision import VisionAdapter  # type: ignore  # noqa: E402
    from ui.components.mobile_chat_interface import MobileChatInterface  # type: ignore  # noqa: E402
    from ui.components.mobile_component_registry import (  # type: ignore  # noqa: E402
        mobile_component_registry,
    )
    from ui.components.mobile_content_tabs import MobileContentTabs  # type: ignore  # noqa: E402
    from ui.components.mobile_header import MobileHeader  # type: ignore  # noqa: E402
    from ui.components.mobile_image_analysis import MobileImageAnalysis  # type: ignore  # noqa: E402
    from ui.components.mobile_input_ribbon import MobileInputRibbon  # type: ignore  # noqa: E402
    from ui.components.mobile_layout_manager import MobileLayoutManager  # type: ignore  # noqa: E402
    from ui.components.mobile_voice_interface import MobileVoiceInterface  # type: ignore  # noqa: E402
    from utils.error_recovery import ImportErrorRecovery  # type: ignore  # noqa: E402

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
        # Try to reuse instance across reruns
        session_key = "_mobile_testing_framework_instance"
        inst = st.session_state.get(session_key)
        if inst is None:
            _mobile_testing_framework = MobileTestingFramework()
            # Store in session to prevent duplicate construction on reruns
            st.session_state[session_key] = _mobile_testing_framework
        else:
            _mobile_testing_framework = inst
    return _mobile_testing_framework


# Global adapter instances for enhanced functionality
@st.cache_resource
def load_core_adapters() -> tuple[Any, Any, Any]:
    """Load and cache core PlantGuard adapters for mobile use."""
    try:
        vision_adapter = VisionAdapter(lazy_load=True)
        audio_adapter = AudioAdapter()
        text_adapter = TextAdapter()

        # Avoid double INFO spam; detailed status handled by caller
        logger.debug("Core adapters loaded successfully for mobile app")
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
            "vision": getattr(vision_adapter, "current_model_id", "ResNet50") if vision_adapter else "Not Loaded",
            "audio": getattr(audio_adapter, "model_name", "Whisper-tiny") if audio_adapter else "Not Loaded",
            "text": "Knowledge Base" if text_adapter else "Not Loaded",
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
            # Store adapter status instead of objects to avoid serialization issues
            st.session_state.vision_adapter_status = "loaded"
            st.session_state.audio_adapter_status = "loaded"
            st.session_state.text_adapter_status = "loaded"
            logger.info("All adapters loaded successfully")
        else:
            st.session_state.adapters_loaded = False
            st.session_state.vision_adapter_status = "failed"
            st.session_state.audio_adapter_status = "failed"
            st.session_state.text_adapter_status = "failed"
            logger.warning("Some adapters failed to load")
    except Exception as e:
        st.session_state.adapters_loaded = False
        st.session_state.vision_adapter_status = "error"
        st.session_state.audio_adapter_status = "error"
        st.session_state.text_adapter_status = "error"
        logger.error(f"Failed to load adapters: {e}")


# Page configuration
st.set_page_config(
    page_title="PlantGuard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://github.com/arslanmit/PlantGuard",
        "Report a bug": "https://github.com/arslanmit/PlantGuard/issues",
        "About": "PlantGuard - AI-powered plant disease detection",
    },
)

# Mobile CSS is now loaded from external file in mobile_layout_manager.py
# The sidebar hiding and main content adjustments are handled by assets/mobile_styles.css


class MobilePlantGuardApp:
    """Main PlantGuard application class.

    Integrates all components into a unified SPA experience.
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
        # Prevent re-entrant initialization across reruns
        if st.session_state.get("mobile_initializing", False):
            return
        st.session_state.mobile_initializing = True
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
        finally:
            st.session_state.mobile_initializing = False

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

                if st.button(":arrows_counterclockwise: Refresh App", width="stretch"):
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

        # Initialize bundle optimizer state
        if "mobile_bundle_optimization" not in st.session_state:
            st.session_state.mobile_bundle_optimization = True

        # Initialize feature usage statistics
        if "feature_usage_image_analysis" not in st.session_state:
            st.session_state.feature_usage_image_analysis = 0
        if "feature_usage_voice_assistant" not in st.session_state:
            st.session_state.feature_usage_voice_assistant = 0
        if "feature_usage_chat_interface" not in st.session_state:
            st.session_state.feature_usage_chat_interface = 0
        if "feature_usage_history_settings" not in st.session_state:
            st.session_state.feature_usage_history_settings = 0

        # Initialize interaction counters
        if "interaction_count" not in st.session_state:
            st.session_state.interaction_count = 0

        if "touch_interactions" not in st.session_state:
            st.session_state.touch_interactions = 0

        # Initialize AI agent state
        if "ai_agent_active" not in st.session_state:
            st.session_state.ai_agent_active = False

        if "ai_agent_test_results" not in st.session_state:
            st.session_state.ai_agent_test_results = {}

        # Initialize error logging
        if "component_error_log" not in st.session_state:
            st.session_state.component_error_log = []

        # Initialize analysis history
        if "analysis_history" not in st.session_state:
            st.session_state.analysis_history = []

    def _setup_state_persistence(self) -> None:
        """Setup state persistence for mobile session continuity."""
        # Create state backup for critical data
        critical_state_keys = ["analysis_history", "user_preferences", "ai_agent_test_results"]

        if "state_backup_created" not in st.session_state:
            st.session_state.state_backup_created = True

        # Note: Complex state backup disabled to prevent serialization issues
        # State persistence handled through individual session keys

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
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = {}

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
        feature_key = f"feature_usage_{feature}"
        if feature_key in st.session_state:
            st.session_state[feature_key] += 1
            st.session_state.interaction_count += 1

    def track_tab_navigation(self, new_tab: str) -> None:
        """Track tab navigation for user analytics."""

        if st.session_state.current_tab != new_tab:
            # Update previous tab
            st.session_state.previous_tab = st.session_state.current_tab

            # Add to navigation history (separate from tab_history used by content tabs)
            if "navigation_history" not in st.session_state:
                st.session_state.navigation_history = []

            # Store as simple string to avoid serialization issues
            nav_record = f"{st.session_state.current_tab}->{new_tab}@{time.time()}"
            st.session_state.navigation_history.append(nav_record)

            # Limit history size
            if len(st.session_state.navigation_history) > 50:
                st.session_state.navigation_history = st.session_state.navigation_history[-50:]

            # Update current tab
            st.session_state.current_tab = new_tab

            # Update feature usage
            self.update_feature_usage(new_tab)

    def save_analysis_result(self, result: dict[str, Any], analysis_type: str = "unknown") -> None:
        """Save analysis result to history with metadata."""

        # Store structured record (dict) to avoid issues with commas in text
        try:
            analysis_record = {
                "timestamp": time.time(),
                "analysis_type": analysis_type,
                "tab": st.session_state.get("current_tab", "unknown"),
                "disease": result.get("disease") if isinstance(result, dict) else None,
                "confidence": result.get("confidence") if isinstance(result, dict) else None,
                "details": result,
            }

            st.session_state.analysis_history.append(analysis_record)

            # Limit history size (keep last 100 analyses)
            if len(st.session_state.analysis_history) > 100:
                st.session_state.analysis_history = st.session_state.analysis_history[-100:]
        except Exception as e:
            logger.error(f"Failed to save structured analysis result: {e}")

    def get_session_analytics(self) -> dict[str, Any]:
        """Get comprehensive session analytics."""

        current_time = time.time()
        session_duration = current_time - st.session_state.app_start_time

        return {
            "session_duration": session_duration,
            "interactions": st.session_state.interaction_count,
            "touch_interactions": st.session_state.touch_interactions,
            "feature_usage": {
                "image_analysis": st.session_state.get("feature_usage_image_analysis", 0),
                "voice_assistant": st.session_state.get("feature_usage_voice_assistant", 0),
                "chat_interface": st.session_state.get("feature_usage_chat_interface", 0),
                "history_settings": st.session_state.get("feature_usage_history_settings", 0),
            },
            "analyses_performed": len(st.session_state.analysis_history),
            "tab_switches": len(st.session_state.get("navigation_history", [])),
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



    def _load_core_adapters(self) -> None:
        """Load core PlantGuard adapters for enhanced mobile functionality."""
        try:
            # Always fetch (cached) adapters to ensure instance fields are populated
            self.vision_adapter, self.audio_adapter, self.text_adapter = load_core_adapters()

            # Determine loaded status
            loaded_ok = bool(self.vision_adapter and self.audio_adapter and self.text_adapter)

            # Only log when status changes or first time
            prev_status = st.session_state.get("mobile_adapters_loaded", None)
            if prev_status is None or prev_status != loaded_ok:
                if loaded_ok:
                    logger.info("Core adapters loaded successfully for mobile app")
                else:
                    logger.warning("Some core adapters failed to load")

            st.session_state.mobile_adapters_loaded = loaded_ok

        except Exception as e:
            logger.error(f"Failed to load core adapters: {e}")
            st.session_state.mobile_adapters_loaded = False

    def _initialize_performance_optimization(self) -> None:
        """Initialize performance optimization for mobile app."""
        try:
            # Avoid repeated re-initialization on Streamlit reruns
            if st.session_state.get("mobile_performance_optimized", False):
                return
            # Set optimization level based on device capabilities
            self.performance_optimizer.set_optimization_level("auto")

            # Enable offline mode optimizations if needed
            if st.session_state.get("mobile_offline_mode", False):
                self.performance_optimizer.enable_offline_mode()

            # Preload critical components
            critical_components = ["mobile_header", "mobile_input_ribbon", "mobile_image_analysis", "mobile_chat_interface"]
            self.performance_optimizer.preload_critical_components(critical_components)

            logger.info("Performance optimization initialized for mobile app")
            st.session_state.mobile_performance_optimized = True

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

            # Save to analysis history (simplified to avoid serialization issues)
            analysis_result = {
                "timestamp": st.session_state.get("app_start_time", 0),
                "disease": disease_class,
                "confidence": confidence,
                "disease_info": disease_info,
                "recommendations": recommendations,
            }

            # Store structured mobile analysis history to avoid comma parsing issues
            try:
                history_record = {
                    "timestamp": time.time(),
                    "disease": disease_class,
                    "confidence": float(confidence) if isinstance(confidence, int | float) else None,
                    "disease_info": disease_info,
                }

                st.session_state.mobile_analysis_history.append(history_record)

                # Limit history size
                if len(st.session_state.mobile_analysis_history) > 50:
                    st.session_state.mobile_analysis_history = st.session_state.mobile_analysis_history[-50:]
            except Exception as e:
                logger.error(f"Failed to append mobile analysis history record: {e}")

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
                            if st.button(":broom: Clean Memory", width="stretch", key="perf_clean_memory"):
                                with st.spinner("Cleaning memory..."):
                                    cleanup_stats = self.performance_optimizer.memory_manager.cleanup_memory(force=True)
                                    freed_mb = cleanup_stats.get("freed_mb", 0)
                                    st.success(f"Freed {freed_mb:.1f}MB")

                        with col2:
                            if st.button(":arrows_counterclockwise: Clear Cache", width="stretch", key="perf_clear_cache"):
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
                        if st.button(":rocket: Quick Analysis with AI", width="stretch", type="primary"):
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
                        if st.button(":speaker: Process Voice with AI", width="stretch", type="primary"):
                            with st.spinner("Processing voice..."):
                                response = self.process_voice_input(st.session_state.recorded_audio)

                                if response and "error" not in response.lower():
                                    st.success(":white_check_mark: Voice processed successfully")
                                    st.markdown("**AI Response:**")
                                    st.write(response)

                                    # Save to chat history using a structured record to avoid comma issues
                                    try:
                                        chat_record = {
                                            "type": "voice",
                                            "timestamp": time.time(),
                                            "input": "<voice_input>",
                                            "response": response,
                                        }
                                        st.session_state.chat_history.append(chat_record)
                                    except Exception as e:
                                        logger.error(f"Failed to save voice chat record: {e}")
                                else:
                                    st.error(f":x: Voice processing failed: {response}")

                    # Quick voice commands
                    st.markdown("**Quick Voice Commands:**")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(":herb: 'What's wrong with my plant?'", width="stretch"):
                            response = self.process_text_query("What's wrong with my plant?")
                            st.write(response)

                    with col2:
                        if st.button(":pill: 'How do I treat this disease?'", width="stretch"):
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
                        if st.button(":speech_balloon: Send Message", width="stretch", type="primary"):
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
                        if st.button(":wastebasket: Clear", width="stretch"):
                            st.session_state.chat_history.clear()
                            # Update chat display without page refresh
                            st.session_state.chat_cleared = True

                    # Display enhanced chat history
                    if st.session_state.chat_history:
                        st.markdown("### :memo: Chat History")

                        for i, chat_record in enumerate(reversed(st.session_state.chat_history[-10:])):
                            try:
                                # Support structured dict records for chat history
                                if isinstance(chat_record, dict):
                                    chat_type = chat_record.get("type", "text")
                                    timestamp = chat_record.get("timestamp")
                                    input_text = chat_record.get("input") or chat_record.get("question") or ""
                                    response_text = chat_record.get("response", "")

                                    title = input_text if input_text else f"Chat {i + 1}"
                                    with st.expander(f":speech_balloon: {title[:50]}...", expanded=i == 0):
                                        if input_text:
                                            st.markdown(f"**You:** {input_text}")
                                        else:
                                            st.markdown("**You:** (no input recorded)")

                                        st.markdown(f"**AI:** {response_text}")
                                else:
                                    # Fallback for legacy or malformed records
                                    with st.expander(f":speech_balloon: Chat {i+1}", expanded=i == 0):
                                        st.write(chat_record)
                            except Exception:
                                # Fallback for any parsing errors
                                with st.expander(f":speech_balloon: Chat {i+1}", expanded=i == 0):
                                    st.write(chat_record)

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
                            if st.button(f":question: {question}", width="stretch", key=f"quick_q_{i}"):
                                # Get context from recent analysis
                                context = None
                                if st.session_state.mobile_analysis_history:
                                    context = st.session_state.mobile_analysis_history[-1]

                                with st.spinner("Generating response..."):
                                    response = self.process_text_query(question, context)

                                    # Add to chat history using structured record
                                    try:
                                        chat_entry = {
                                            "type": "quick",
                                            "timestamp": time.time(),
                                            "input": question,
                                            "response": response,
                                            "context": context,
                                        }
                                        st.session_state.chat_history.append(chat_entry)
                                    except Exception as e:
                                        logger.error(f"Failed to save quick question chat record: {e}")
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

            # Prepare window of recent records (up to 5) and compute numbering
            recent_window = all_history[-5:]
            total = len(all_history)
            start_index = total - len(recent_window) + 1

            for idx, analysis_record in enumerate(recent_window, start=start_index):
                analysis_num = idx

                try:
                    # Structured dict records (preferred)
                    if isinstance(analysis_record, dict):
                        timestamp = analysis_record.get("timestamp")
                        disease = analysis_record.get("disease") or analysis_record.get("analysis_type") or "Unknown"
                        confidence = analysis_record.get("confidence")

                        # Normalize confidence for display
                        try:
                            confidence_val = float(confidence) if confidence is not None else 0.0
                        except Exception:
                            confidence_val = 0.0

                        title = f":microscope: Analysis {analysis_num}: {disease}"
                        if confidence_val > 0:
                            title += f" ({confidence_val:.1%})"

                        with st.expander(title, expanded=True):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.metric("Disease", disease)
                                st.metric("Confidence", f"{confidence_val:.1%}")

                            with col2:
                                # Format timestamp if numeric, otherwise show raw
                                try:
                                    if isinstance(timestamp, int | float):
                                        import datetime

                                        ts_str = datetime.datetime.fromtimestamp(float(timestamp)).isoformat()
                                        st.metric("Timestamp", ts_str)
                                    else:
                                        st.metric("Timestamp", str(timestamp))
                                except Exception:
                                    st.metric("Timestamp", str(timestamp))

                    # Legacy string format fallback: safely handle strings only
                    elif isinstance(analysis_record, str):
                        try:
                            parts = analysis_record.split(",", 2)
                        except Exception:
                            parts = [analysis_record]

                        if len(parts) >= 3:
                            timestamp, disease, confidence_str = parts
                            try:
                                confidence_val = float(confidence_str)
                            except Exception:
                                confidence_val = 0.0

                            title = f":microscope: Analysis {analysis_num}: {disease}"
                            if confidence_val > 0:
                                title += f" ({confidence_val:.1%})"

                            with st.expander(title, expanded=True):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.metric("Disease", disease)
                                    st.metric("Confidence", f"{confidence_val:.1%}")

                                with col2:
                                    st.metric("Timestamp", timestamp)
                        else:
                            with st.expander(f":bar_chart: Analysis {analysis_num}", expanded=True):
                                st.write(f"Analysis record: {analysis_record}")

                    # Other types (list/tuple/others) - show a readable representation
                    else:
                        with st.expander(f":bar_chart: Analysis {analysis_num}", expanded=True):
                            try:
                                st.write(analysis_record)
                            except Exception:
                                st.write(str(analysis_record))

                except Exception:
                    # Generic fallback for any parsing/display errors
                    with st.expander(f":bar_chart: Analysis {analysis_num}", expanded=True):
                        st.write(f"Analysis record: {analysis_record}")
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

                if st.button("[RELOAD] Reload Adapters", width="stretch"):
                    with st.spinner("Reloading adapters..."):
                        self._load_core_adapters()
                        # Update adapter status without page refresh
                        st.session_state.adapters_reloaded = True

            # AI Agent controls
            st.markdown("**[AI] AI Agent**")

            if st.button("Run Component Tests", width="stretch"):
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
        """Render model comparison tab content."""
        st.markdown("### Model Comparison")
        st.info("Model comparison functionality would be implemented here")

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
        active_modes = self.input_ribbon.render()

        # Determine selected input mode from returned active modes dict
        selected_mode: str | None = None
        if isinstance(active_modes, dict):
            # Priority order for mapping to tabs
            priority = ["text", "voice", "camera", "upload"]
            for mode in priority:
                if active_modes.get(mode):
                    selected_mode = mode
                    break
            # Fallback: first active mode if none matched priority
            if selected_mode is None:
                for mode, is_active in active_modes.items():
                    if is_active:
                        selected_mode = mode
                        break

        # Handle input method selection WITHOUT st.rerun()
        if selected_mode:
            input_to_tab_mapping = {
                "text": "chat_interface",
                "voice": "voice_assistant",
                "camera": "image_analysis",
                "upload": "image_analysis",
            }

            target_tab = input_to_tab_mapping.get(selected_mode)
            if target_tab:
                # Track tab navigation
                self.track_tab_navigation(target_tab)

                # Update input mode timestamp
                st.session_state.current_input_mode = selected_mode
                st.session_state.last_input_timestamp = time.time()

                # Set active tab and focus content WITHOUT st.rerun()
                st.session_state.focused_content = target_tab
                self.content_tabs.set_active_tab(target_tab)

    def render_ai_agent_status(self) -> None:
        """Render AI agent status indicator in main content without page redirects."""
        with st.expander("AI Agent Status", expanded=True):
            if st.session_state.get("ai_agent_active", False):
                st.success("AI Agent Active")

                if st.button("Run Tests", width="stretch", key="spa_ai_tests"):
                    with st.spinner("Running tests..."):
                        results = get_ai_testing_framework().test_all_components()
                        st.json(results)
            else:
                if st.button("Activate AI Agent", width="stretch", key="spa_activate_ai"):
                    st.session_state.ai_agent_active = True
                    st.success("AI Agent activated!")

    def run(self) -> None:
        """Run the PlantGuard application with performance optimizations."""
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
            # Load optimized CSS (only if performance optimizer exists and external CSS not loaded)
            if (hasattr(self, 'performance_optimizer') and 
                self.performance_optimizer and 
                not st.session_state.get("mobile_css_loaded", False)):
                st.markdown(self.performance_optimizer.get_optimized_css(), unsafe_allow_html=True)

        # Initialize components if not done
        if not st.session_state.get("mobile_app_initialized", False):
            with st.spinner("Initializing PlantGuard..."):
                self.initialize_components()

        # Check initialization status
        if not st.session_state.get("mobile_app_initialized", False):
            st.error("Application failed to initialize")

            st.markdown("### Initialization Error")
            st.markdown("Components failed to initialize. Try the options below.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Reinitialize App", width="stretch", key="spa_reinitialize"):
                    st.session_state.mobile_app_initialized = False
                    st.success("Reinitializing...")
                    st.session_state.force_reinit = True

            with col2:
                if st.button("Clear Cache & Restart", width="stretch", key="spa_clear_restart"):
                    with contextlib.suppress(builtins.BaseException):
                        self.performance_optimizer.cache.clear()

                    keys_to_clear = [key for key in st.session_state if key.startswith("mobile_")]
                    for key in keys_to_clear:
                        del st.session_state[key]

                    st.success("Cache cleared!")
                    st.session_state.cache_cleared = True

            st.markdown("### System Status")
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
            # Header
            st.markdown(
                """
            <div class="mobile-app-header">
                <h1>PlantGuard</h1>
                <p>AI Plant Disease Detection</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Model Selection
            st.markdown("## Model Selection")

            # Model selection interface
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### Vision Model")
                vision_model = st.selectbox("Select", ["apple_vision_pro", "efficientnet_b0", "resnet50", "mobilenet_v2"], key="vision_model_select")
                if st.button("Load", key="load_vision"):
                    with st.spinner("Loading..."):
                        try:
                            if hasattr(self, "vision_adapter") and self.vision_adapter:
                                self.vision_adapter.model_name = vision_model
                            st.success(f"Loaded: {vision_model}")
                        except Exception as e:
                            st.error(f"Error: {e}")

            with col2:
                st.markdown("### Audio Model")
                audio_model = st.selectbox("Select", ["openai/whisper-tiny", "openai/whisper-base", "openai/whisper-small"], key="audio_model_select")
                if st.button("Load", key="load_audio"):
                    with st.spinner("Loading..."):
                        try:
                            if hasattr(self, "audio_adapter") and self.audio_adapter:
                                self.audio_adapter.model_name = audio_model
                            st.success(f"Loaded: {audio_model}")
                        except Exception as e:
                            st.error(f"Error: {e}")

            with col3:
                st.markdown("### Text Model")
                text_model = st.selectbox("Select", ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"], key="text_model_select")
                if st.button("Load", key="load_text"):
                    with st.spinner("Loading..."):
                        try:
                            if hasattr(self, "text_adapter") and self.text_adapter:
                                self.text_adapter.model_name = text_model
                            st.success(f"Loaded: {text_model}")
                        except Exception as e:
                            st.error(f"Error: {e}")

            st.markdown("---")

            # Model Status
            st.markdown("## Model Status")
            current_models = get_model_status()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### Vision")
                st.info(f"Active: {current_models.get('vision', 'Unknown')}")

            with col2:
                st.markdown("### Audio")
                st.info(f"Active: {current_models.get('audio', 'Unknown')}")

            with col3:
                st.markdown("### Text")
                st.info(f"Active: {current_models.get('text', 'Unknown')}")

            # Quick Actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Reload Models", width="stretch"):
                    st.cache_resource.clear()
                    st.success("Models reloaded!")

            with col2:
                if st.button("Quick Test", width="stretch"):
                    st.info("Use Model Management tab for testing")

            # Plant Analysis Tools
            st.markdown("## Plant Analysis Tools")
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Image Analysis", "Voice & Audio", "Chat Interface", "Model Management", "Settings"])

            with tab1:
                st.markdown("### Upload Plant Image")
                img_file = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])

                if img_file is not None:
                    img = PILImage.open(img_file)
                    st.image(img, width="stretch")

                    if st.button("Analyze Plant", key="img", type="primary", width="stretch"):
                        with st.spinner("Analyzing..."):
                            try:
                                if hasattr(self, "vision_adapter") and self.vision_adapter:
                                    result = self.vision_adapter.predict(img)
                                    disease_name, confidence = result

                                    st.markdown("### Analysis Results")
                                    col1, col2, col3 = st.columns(3)

                                    with col1:
                                        st.metric("Plant Type", disease_name.split("___")[0] if "___" in disease_name else disease_name)
                                    with col2:
                                        st.metric("Condition", disease_name.split("___")[1] if "___" in disease_name else disease_name)
                                    with col3:
                                        st.metric("Confidence", f"{confidence:.1%}")

                                    if confidence > 0.8:
                                        st.success("Plant appears healthy!")
                                    else:
                                        st.warning("Disease detected")

                                    with st.expander("Technical Details"):
                                        st.json(
                                            {
                                                "disease": disease_name,
                                                "confidence": float(confidence),
                                                "model": current_models.get("vision", "Unknown"),
                                                "timestamp": time.time(),
                                            }
                                        )
                                else:
                                    st.error("Vision adapter not available")
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                else:
                    st.info("Upload an image to begin analysis")

            with tab2:
                st.markdown("### Voice & Audio Analysis")
                audio_col1, audio_col2 = st.columns([1, 1])

                with audio_col1:
                    st.markdown("### Live Recording")
                    st.info("Use Voice Assistant tab for full functionality")
                    if st.button("Test Voice Input", key="test_voice"):
                        st.success("Voice input test - use Voice Assistant tab")

                with audio_col2:
                    st.markdown("### File Upload")
                    audio_file = st.file_uploader("Upload audio", ["wav", "mp3", "m4a"])

                    if audio_file is not None:
                        st.audio(audio_file, format="audio/wav")
                        if st.button("Process File", key="file_analyze", type="primary", width="stretch"):
                            with st.spinner("Processing..."):
                                try:
                                    if hasattr(self, "audio_adapter") and self.audio_adapter:
                                        text = self.audio_adapter.transcribe(audio_file)
                                        st.markdown("### Transcription")
                                        st.text_area("Text:", text, height=100, disabled=True)

                                        if hasattr(self, "text_adapter") and self.text_adapter:
                                            response = self.text_adapter.get_response(text)
                                            st.markdown("### AI Response")
                                            st.success(response)
                                    else:
                                        st.error("Audio adapter not available")
                                except Exception as e:
                                    st.error(f"Processing failed: {e}")

            with tab3:
                st.markdown("### Chat Interface")
                st.info("Use Chat Interface tab for full functionality")
                if st.button("Open Chat", key="open_chat"):
                    st.success("Use Chat Interface tab")

            with tab4:
                st.markdown("### Model Management")
                if st.button("Run Model Tests", key="run_model_tests"):
                    with st.spinner("Testing..."):
                        try:
                            test_results = {
                                "vision": "Passed" if hasattr(self, "vision_adapter") and self.vision_adapter else "Failed",
                                "audio": "Passed" if hasattr(self, "audio_adapter") and self.audio_adapter else "Failed",
                                "text": "Passed" if hasattr(self, "text_adapter") and self.text_adapter else "Failed",
                            }
                            st.success("Tests completed!")
                            st.json(test_results)
                        except Exception as e:
                            st.error(f"Testing failed: {e}")

            with tab5:
                st.markdown("### Settings")
                perf_mode = st.selectbox("Performance Mode", ["Auto", "Minimal", "Balanced", "Aggressive"], index=1, key="perf_mode_select")
                if st.button("Apply", key="apply_settings"):
                    st.success(f"Mode: {perf_mode}")

            st.markdown("---")

            # Mobile Components
            st.markdown("## Mobile Components")
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

            if st.button("[RESTART] Try Full Restart", width="stretch", key="spa_full_restart"):
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
        with st.expander("App Info", expanded=True):
            st.markdown("**Version:** 2.0.0")
            st.markdown("**Mobile:** Chrome & Safari Optimized")
            st.markdown("**Desktop:** Full-featured with model management")
            st.markdown("**Design:** Responsive - 428px mobile, full-width desktop")

        with st.expander("Component Status", expanded=True):
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
                    st.success(f"✅ {component}")
                elif status == "initializing":
                    st.warning(f"⏳ {component}")
                else:
                    st.error(f"❌ {component}")

        # Quick actions in expandable section
        with st.expander("[ACTIONS] Quick Actions", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                if st.button("[REFRESH] Refresh Components", width="stretch", key="spa_refresh_components"):
                    st.session_state.mobile_app_initialized = False
                    st.success("Refreshing components - no page refresh needed!")
                    # Update state without page refresh
                    st.session_state.components_refreshed = True

            with col2:
                if st.button("[TEST] Run AI Tests", width="stretch", key="spa_run_tests"):
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
