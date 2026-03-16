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
    from plantguard.utils.error_recovery import ImportErrorRecovery  # noqa: E402
except ModuleNotFoundError as import_error:
    if import_error.name is None or not import_error.name.startswith("plantguard"):
        raise
    _ensure_src_path()
    from core.audio import AudioAdapter  # type: ignore  # noqa: E402
    from core.nlp import TextAdapter  # type: ignore  # noqa: E402
    from core.vision import VisionAdapter  # type: ignore  # noqa: E402
    from utils.error_recovery import ImportErrorRecovery  # type: ignore  # noqa: E402

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

# Global adapter instances for enhanced functionality
def _get_model_config_mtime(config_path: str = "config/models.json") -> float:
    """Return a cache-busting token for model-manager resources."""
    path = Path(config_path)
    if not path.exists():
        return 0.0
    return path.stat().st_mtime


@st.cache_resource
def load_vision_model_manager(config_path: str = "config/models.json", config_mtime: float | None = None) -> Any:
    """Load the shared vision model manager and ensure a usable vision model is active."""
    _ = config_mtime
    try:
        from plantguard.core.model_manager import PlantGuardModelManager
    except ModuleNotFoundError:
        from core.model_manager import PlantGuardModelManager  # type: ignore

    manager = PlantGuardModelManager(config_path=config_path)
    return manager


@st.cache_resource
def load_core_adapters(config_path: str = "config/models.json", config_mtime: float | None = None) -> tuple[Any, Any, Any]:
    """Load and cache core PlantGuard adapters for mobile use."""
    try:
        vision_manager = load_vision_model_manager(config_path=config_path, config_mtime=config_mtime)
        vision_adapter = getattr(vision_manager, "current_adapter", None)
        if vision_adapter is None:
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
        config_mtime = _get_model_config_mtime()
        vision_adapter, audio_adapter, text_adapter = load_core_adapters(config_mtime=config_mtime)
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
        self.vision_model_manager = None

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
        """Initialize the simplified web shell state."""
        if st.session_state.get("mobile_initializing", False):
            return

        st.session_state.mobile_initializing = True
        try:
            self.layout_manager = None
            self.header = None
            self.input_ribbon = None
            self.content_tabs = None
            self.image_analysis = None
            self.voice_interface = None
            self.chat_interface = None

            st.session_state.mobile_app_initialized = True
            logger.info("PlantGuard web shell initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize web shell: {e}")
            st.session_state.mobile_app_initialized = False
        finally:
            st.session_state.mobile_initializing = False

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

        if "preferred_audio_model" not in st.session_state:
            st.session_state.preferred_audio_model = "openai/whisper-tiny"

        if "preferred_text_model" not in st.session_state:
            st.session_state.preferred_text_model = "gpt-3.5-turbo"

        if "current_vision_model" not in st.session_state:
            st.session_state.current_vision_model = None

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

    def _load_core_adapters(self) -> None:
        """Load core PlantGuard adapters for enhanced mobile functionality."""
        try:
            config_mtime = _get_model_config_mtime()
            self.vision_model_manager = load_vision_model_manager(config_mtime=config_mtime)
            # Always fetch (cached) adapters to ensure instance fields are populated
            self.vision_adapter, self.audio_adapter, self.text_adapter = load_core_adapters(config_mtime=config_mtime)
            if self.vision_model_manager and getattr(self.vision_model_manager, "current_adapter", None):
                self.vision_adapter = self.vision_model_manager.current_adapter
                current_model_key_getter = getattr(self.vision_model_manager, "get_current_model_key", None)
                if callable(current_model_key_getter):
                    current_model_key = current_model_key_getter()
                    if current_model_key:
                        st.session_state.current_vision_model = current_model_key

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

    def _get_available_vision_models(self) -> list[dict[str, Any]]:
        """Return enabled vision models for the settings UI."""
        if not self.vision_model_manager:
            return []

        return [
            model
            for model in self.vision_model_manager.list_available_models()
            if model.get("enabled")
        ]

    def _apply_model_settings(self, vision_model: str | None, audio_model: str, text_model: str) -> bool:
        """Apply user-selected settings while keeping only vision model switching live."""
        st.session_state.preferred_audio_model = audio_model
        st.session_state.preferred_text_model = text_model

        if not vision_model:
            st.error("No vision models are currently available.")
            return False

        if not self.vision_model_manager:
            st.error("Vision model manager is unavailable.")
            return False

        vision_updated = self.vision_model_manager.switch_model_for_ui(vision_model)
        if vision_updated and getattr(self.vision_model_manager, "current_adapter", None):
            self.vision_adapter = self.vision_model_manager.current_adapter
            st.session_state.current_vision_model = vision_model
            st.success("Vision model updated. Audio and text preferences saved.")
            return True

        model_config = self.vision_model_manager.get_model_config(vision_model)
        failure_reason = None
        if isinstance(model_config, dict):
            failure_reason = model_config.get("description")

        if vision_model == "local_resnet":
            st.error(
                "Local ResNet50 could not be loaded. Add a valid checkpoint at "
                "**data/models/vision_resnet50.pt** (run production training and promote a model) to use it."
            )
        elif failure_reason:
            st.error(f"Selected vision model is unavailable: {failure_reason}")
        else:
            st.error("Selected vision model could not be loaded.")
        return False

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

    def run(self) -> None:
        """Run the PlantGuard application with performance optimizations."""
        try:            # Run the main app
            self._run_main_app()

        except Exception as e:
            st.error(f"Critical error in mobile app: {e}")
            logger.error(f"Critical error in mobile app: {e}")
            # Prevent page change even on error
            st.session_state.page_change_prevention = True

    def _ui_components_available(self) -> bool:
        """Return True when the simplified web shell has been initialized."""
        return bool(st.session_state.get("mobile_app_initialized", False))

    def _render_web_image_tab(self) -> None:
        """Render the image analysis flow for the simplified web shell."""
        st.markdown("### Upload Plant Image")
        img_file = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"])

        if img_file is None:
            st.info("Upload an image to begin analysis")
            return

        img = PILImage.open(img_file)
        st.image(img, width="stretch")

        if not st.button("Analyze Plant", key="img", type="primary", width="stretch"):
            return

        with st.spinner("Analyzing..."):
            try:
                if not self.vision_adapter:
                    st.error("Vision adapter not available")
                    return

                disease_name, confidence = self.vision_adapter.predict(img)

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
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    def _render_web_audio_tab(self) -> None:
        """Render the voice and audio flow for the simplified web shell."""
        st.markdown("### Voice & Audio")
        audio_file = st.file_uploader("Upload audio", ["wav", "mp3", "m4a"])

        if audio_file is None:
            st.info("Upload audio to transcribe or analyze")
            return

        st.audio(audio_file, format="audio/wav")

        if not st.button("Process Audio", key="file_analyze", type="primary", width="stretch"):
            return

        with st.spinner("Processing..."):
            try:
                if not self.audio_adapter:
                    st.error("Audio adapter not available")
                    return

                text = self.audio_adapter.transcribe(audio_file)
                st.markdown("### Transcription")
                st.text_area("Text:", text, height=100, disabled=True)

                if self.text_adapter:
                    response = self.text_adapter.get_response(text)
                    st.markdown("### AI Response")
                    st.success(response)
            except Exception as e:
                st.error(f"Processing failed: {e}")

    def _render_web_chat_tab(self) -> None:
        """Render the direct chat flow for the simplified web shell."""
        st.markdown("### Chat")
        user_input = st.text_area("Ask about your plant", height=120, key="web_chat_input")

        if st.button("Send", key="send_chat", type="primary", width="stretch"):
            if not user_input.strip():
                st.warning("Enter a question to start the chat")
                return

            if not self.text_adapter:
                st.error("Text adapter not available")
                return

            response = self.process_text_query(user_input)
            st.markdown("### Response")
            st.success(response)

    def _render_web_settings_tab(self) -> None:
        """Render user-facing settings for the simplified web shell."""
        st.markdown("### Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Model Selection")
            available_vision_models = self._get_available_vision_models()
            vision_model_ids = [model["id"] for model in available_vision_models]
            vision_labels = {model["id"]: model.get("name", model["id"]) for model in available_vision_models}
            current_vision_model = st.session_state.get("current_vision_model")
            if current_vision_model not in vision_model_ids and self.vision_model_manager:
                current_model_key_getter = getattr(self.vision_model_manager, "get_current_model_key", None)
                if callable(current_model_key_getter):
                    current_vision_model = current_model_key_getter()

            vision_model = None
            if vision_model_ids:
                default_index = 0
                if current_vision_model in vision_model_ids:
                    default_index = vision_model_ids.index(current_vision_model)
                vision_model = st.selectbox(
                    "Vision Model",
                    vision_model_ids,
                    index=default_index,
                    format_func=lambda model_id: vision_labels.get(model_id, model_id),
                    key="vision_model_select",
                )
            else:
                st.warning("No vision models are currently available.")

            audio_model_options = ["openai/whisper-tiny", "openai/whisper-base", "openai/whisper-small"]
            audio_default = st.session_state.get("preferred_audio_model", audio_model_options[0])
            audio_model = st.selectbox(
                "Audio Model",
                audio_model_options,
                index=audio_model_options.index(audio_default) if audio_default in audio_model_options else 0,
                key="audio_model_select",
            )
            text_model_options = ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]
            text_default = st.session_state.get("preferred_text_model", text_model_options[0])
            text_model = st.selectbox(
                "Text Model",
                text_model_options,
                index=text_model_options.index(text_default) if text_default in text_model_options else 0,
                key="text_model_select",
            )

            if st.button("Apply Models", key="apply_models", width="stretch", disabled=not bool(vision_model_ids)):
                self._apply_model_settings(vision_model, audio_model, text_model)

        with col2:
            st.markdown("#### Preferences")
            perf_mode = st.selectbox(
                "Performance Mode",
                ["Auto", "Minimal", "Balanced", "Aggressive"],
                index=1,
                key="perf_mode_select",
            )
            if st.button("Apply Preferences", key="apply_settings", width="stretch"):
                st.session_state.mobile_performance_mode = perf_mode.lower()
                st.success(f"Performance mode set to {perf_mode}")

    def _run_main_app(self) -> None:
        """Run the simplified PlantGuard web application."""
        # Apply performance optimizations at startup
        with contextlib.suppress(Exception):
            # Load optimized CSS (only if performance optimizer exists and external CSS not loaded)
            if (hasattr(self, 'performance_optimizer') and 
                self.performance_optimizer and 
                not st.session_state.get("mobile_css_loaded", False)):
                st.markdown(self.performance_optimizer.get_optimized_css(), unsafe_allow_html=True)

        if not self._ui_components_available():
            with st.spinner("Initializing PlantGuard..."):
                self.initialize_components()

        if not st.session_state.get("mobile_app_initialized", False):
            st.error("Application failed to initialize")
            return

        try:
            st.markdown(
                """
            <div class="mobile-app-header">
                <h1>PlantGuard</h1>
                <p>AI plant disease detection and support</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            tab_image, tab_audio, tab_chat, tab_settings = st.tabs(
                ["Image Analysis", "Voice & Audio", "Chat", "Settings"]
            )

            with tab_image:
                self._render_web_image_tab()

            with tab_audio:
                self._render_web_audio_tab()

            with tab_chat:
                self._render_web_chat_tab()

            with tab_settings:
                self._render_web_settings_tab()

        except Exception as e:
            st.error(f"Application error: {e}")
            logger.error(f"App content rendering error: {e}")

    def render_app_info_inline(self) -> None:
        """No-op placeholder kept for compatibility while removing developer panels."""
        return None


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
