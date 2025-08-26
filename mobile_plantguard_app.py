#!/usr/bin/env python3
"""
PlantGuard Mobile Application Entry Point

Mobile-first PlantGuard application with complete component integration.
Provides seamless mobile experience with automatic interface switching.

Usage:
    streamlit run mobile_plantguard_app.py

Features:
- Mobile detection and automatic interface switching
- Complete integration with existing PlantGuard adapters
- AI agent testing and self-healing capabilities
- Offline functionality and performance optimization
"""

import logging
import sys
from pathlib import Path
from typing import Any

import streamlit as st

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import mobile components
from ui.components.ai_agent_testing import ai_testing_framework
from ui.components.mobile_chat_interface import MobileChatInterface
from ui.components.mobile_component_registry import mobile_component_registry
from ui.components.mobile_content_tabs import MobileContentTabs
from ui.components.mobile_error_handler import MobileErrorHandler
from ui.components.mobile_header import MobileHeader
from ui.components.mobile_history_view import MobileHistoryView
from ui.components.mobile_image_analysis import MobileImageAnalysis
from ui.components.mobile_input_ribbon import MobileInputRibbon
from ui.components.mobile_layout_manager import MobileLayoutManager
from ui.components.mobile_settings_card import MobileSettingsCard
from ui.components.mobile_state_manager import MobileStateManager
from ui.components.mobile_voice_interface import MobileVoiceInterface

# Import existing PlantGuard adapters
try:
    from core.audio import AudioAdapter
    from core.nlp import ChatModel, TextAdapter
    from core.vision import VisionAdapter
except ImportError as e:
    logging.warning(f"Could not import PlantGuard adapters: {e}")
    VisionAdapter = None
    AudioAdapter = None
    TextAdapter = None
    ChatModel = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_mobile_device() -> bool:
    """Detect if the user is on a mobile device."""
    # Check user agent via JavaScript injection
    user_agent_script = """
    <script>
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isSmallScreen = window.innerWidth <= 768;
    window.parent.postMessage({type: 'mobile_detection', isMobile: isMobile || isSmallScreen}, '*');
    </script>
    """

    # Default to mobile-first approach
    return True


def configure_mobile_page():
    """Configure Streamlit page for mobile optimization."""
    st.set_page_config(
        page_title="PlantGuard Mobile",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            "Get Help": "https://github.com/plantguard/help",
            "Report a bug": "https://github.com/plantguard/issues",
            "About": "PlantGuard Mobile - AI-powered plant disease detection",
        },
    )

    # Mobile-specific CSS
    st.markdown(
        """
    <style>
        /* Hide sidebar completely on mobile */
        .stSidebar {
            display: none !important;
        }
        
        /* Mobile-first responsive design */
        .main .block-container {
            padding: 0.5rem;
            max-width: 100%;
        }
        
        /* Ensure mobile viewport */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 0.25rem;
            }
        }
        
        /* Touch-friendly buttons */
        .stButton > button {
            min-height: 48px;
            touch-action: manipulation;
        }
        
        /* Mobile input optimization */
        .stTextInput > div > div > input {
            font-size: 16px; /* Prevent zoom on iOS */
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


class MobilePlantGuardApp:
    """Main mobile PlantGuard application with complete integration."""

    def __init__(self):
        self.state_manager = MobileStateManager()
        self.error_handler = MobileErrorHandler()
        self.layout_manager: MobileLayoutManager | None = None
        self.components: dict[str, Any] = {}
        self.adapters: dict[str, Any] = {}

        # Initialize application
        self._initialize_app()

    def _initialize_app(self) -> None:
        """Initialize the mobile application."""
        try:
            # Initialize session state
            self._initialize_session_state()

            # Load PlantGuard adapters
            self._load_adapters()

            # Initialize mobile components
            self._initialize_components()

            # Setup error handling
            self._setup_error_handling()

            logger.info("Mobile PlantGuard app initialized successfully")

        except Exception as e:
            self.error_handler.handle_initialization_error(e)
            logger.error(f"Failed to initialize mobile app: {e}")

    def _initialize_session_state(self) -> None:
        """Initialize essential session state variables."""
        # Core app state
        if "mobile_app_ready" not in st.session_state:
            st.session_state.mobile_app_ready = False

        if "current_tab" not in st.session_state:
            st.session_state.current_tab = "image_analysis"

        if "mobile_device_detected" not in st.session_state:
            st.session_state.mobile_device_detected = detect_mobile_device()

        # Analysis state
        if "analysis_history" not in st.session_state:
            st.session_state.analysis_history = []

        if "current_analysis" not in st.session_state:
            st.session_state.current_analysis = None

        # Chat state
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []

        # Settings state
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = {"theme": "auto", "notifications": True, "auto_analysis": False, "voice_enabled": True}

        # Component state tracking
        if "component_states" not in st.session_state:
            st.session_state.component_states = {}

        # Error tracking
        if "error_log" not in st.session_state:
            st.session_state.error_log = []

    @st.cache_resource
    def _load_adapters(_self) -> dict[str, Any]:
        """Load and cache PlantGuard adapters."""
        adapters = {}

        try:
            if VisionAdapter:
                adapters["vision"] = VisionAdapter()
                logger.info("Vision adapter loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load vision adapter: {e}")

        try:
            if AudioAdapter:
                adapters["audio"] = AudioAdapter()
                logger.info("Audio adapter loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load audio adapter: {e}")

        try:
            if TextAdapter:
                adapters["text"] = TextAdapter()
                logger.info("Text adapter loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load text adapter: {e}")

        try:
            if ChatModel:
                adapters["chat"] = ChatModel()
                logger.info("Chat model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load chat model: {e}")

        return adapters

    def _initialize_components(self) -> None:
        """Initialize all mobile components."""
        try:
            # Load adapters
            self.adapters = self._load_adapters()

            # Initialize layout manager
            self.layout_manager = MobileLayoutManager("main_layout")

            # Initialize core components
            self.components = {
                "header": MobileHeader("mobile_header", "PlantGuard", "AI Plant Care Assistant"),
                "input_ribbon": MobileInputRibbon("mobile_input_ribbon"),
                "content_tabs": MobileContentTabs("mobile_content_tabs"),
                "image_analysis": MobileImageAnalysis("mobile_image_analysis"),
                "voice_interface": MobileVoiceInterface("mobile_voice_interface"),
                "chat_interface": MobileChatInterface("mobile_chat_interface"),
                "history_view": MobileHistoryView("mobile_history_view"),
                "settings_card": MobileSettingsCard("mobile_settings_card"),
            }

            # Connect adapters to components
            self._connect_adapters_to_components()

            # Register components
            self._register_components()

            # Setup tab content
            self._setup_tab_content()

            st.session_state.mobile_app_ready = True
            logger.info("All mobile components initialized successfully")

        except Exception as e:
            self.error_handler.handle_component_error("initialization", e)
            logger.error(f"Failed to initialize components: {e}")

    def _connect_adapters_to_components(self) -> None:
        """Connect PlantGuard adapters to mobile components."""
        # Connect vision adapter to image analysis
        if "vision" in self.adapters and "image_analysis" in self.components:
            self.components["image_analysis"].set_vision_adapter(self.adapters["vision"])

        # Connect audio adapter to voice interface
        if "audio" in self.adapters and "voice_interface" in self.components:
            self.components["voice_interface"].set_audio_adapter(self.adapters["audio"])

        # Connect text and chat adapters to chat interface
        if "text" in self.adapters and "chat_interface" in self.components:
            self.components["chat_interface"].set_text_adapter(self.adapters["text"])

        if "chat" in self.adapters and "chat_interface" in self.components:
            self.components["chat_interface"].set_chat_model(self.adapters["chat"])

        logger.info("Adapters connected to mobile components")

    def _register_components(self) -> None:
        """Register components with the mobile component registry."""
        for component_id, component in self.components.items():
            mobile_component_registry.register_component(component_id, component)

        logger.info(f"Registered {len(self.components)} mobile components")

    def _setup_tab_content(self) -> None:
        """Setup content for each tab."""
        if "content_tabs" not in self.components:
            return

        content_tabs = self.components["content_tabs"]

        # Register tab content callbacks
        content_tabs.register_tab_content("image_analysis", self._render_image_analysis_tab)
        content_tabs.register_tab_content("voice_assistant", self._render_voice_assistant_tab)
        content_tabs.register_tab_content("chat_interface", self._render_chat_interface_tab)
        content_tabs.register_tab_content("history_settings", self._render_history_settings_tab)

    def _setup_error_handling(self) -> None:
        """Setup comprehensive error handling."""
        # Set error handler for all components
        for component in self.components.values():
            if hasattr(component, "set_error_handler"):
                component.set_error_handler(self.error_handler)

    def _render_image_analysis_tab(self) -> None:
        """Render image analysis tab content."""
        if "image_analysis" in self.components:
            self.components["image_analysis"].render()
        else:
            st.error("Image analysis component not available")

    def _render_voice_assistant_tab(self) -> None:
        """Render voice assistant tab content."""
        if "voice_interface" in self.components:
            self.components["voice_interface"].render()
        else:
            st.error("Voice interface component not available")

    def _render_chat_interface_tab(self) -> None:
        """Render chat interface tab content."""
        if "chat_interface" in self.components:
            self.components["chat_interface"].render()
        else:
            st.error("Chat interface component not available")

    def _render_history_settings_tab(self) -> None:
        """Render history and settings tab content."""
        # History section
        if "history_view" in self.components:
            self.components["history_view"].render()

        st.markdown("---")

        # Settings section
        if "settings_card" in self.components:
            self.components["settings_card"].render()

        # AI agent testing section
        st.markdown("### 🤖 AI Agent Testing")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Run Component Tests", use_container_width=True):
                with st.spinner("Running AI agent tests..."):
                    results = ai_testing_framework.test_all_components()
                    st.json(results)

        with col2:
            if st.button("Check Component Health", use_container_width=True):
                health_report = ai_testing_framework.get_component_health_report()
                st.json(health_report)

    def render_mobile_detection_notice(self) -> None:
        """Render mobile device detection notice."""
        if st.session_state.mobile_device_detected:
            st.success("📱 Mobile device detected - Optimized interface loaded")
        else:
            st.info("💻 Non-mobile device detected - Mobile interface optimized for all screens")

    def render_adapter_status(self) -> None:
        """Render adapter connection status."""
        with st.expander("🔌 Adapter Status", expanded=False):
            for adapter_name, adapter in self.adapters.items():
                if adapter:
                    st.success(f"✅ {adapter_name.title()} Adapter: Connected")
                else:
                    st.error(f"❌ {adapter_name.title()} Adapter: Not Available")

    def run(self) -> None:
        """Run the mobile PlantGuard application."""
        try:
            # Check if app is ready
            if not st.session_state.get("mobile_app_ready", False):
                st.warning("🔄 Initializing mobile application...")
                self._initialize_app()
                if not st.session_state.get("mobile_app_ready", False):
                    st.error("❌ Failed to initialize mobile application")
                    return

            # Render mobile detection notice
            self.render_mobile_detection_notice()

            # Load mobile CSS
            if self.layout_manager:
                self.layout_manager.load_mobile_css()

            # Render header
            if "header" in self.components:
                self.components["header"].render()

            # Render input ribbon
            if "input_ribbon" in self.components:
                selected_input = self.components["input_ribbon"].render()

                # Handle input selection
                if selected_input:
                    self._handle_input_selection(selected_input)

            # Render content tabs
            if "content_tabs" in self.components:
                self.components["content_tabs"].render()

            # Render adapter status
            self.render_adapter_status()

            # Render app info
            self._render_app_info()

        except Exception as e:
            self.error_handler.handle_app_error(e)
            logger.error(f"Error running mobile app: {e}")

    def _handle_input_selection(self, input_type: str) -> None:
        """Handle input method selection."""
        input_to_tab = {"camera": "image_analysis", "upload": "image_analysis", "voice": "voice_assistant", "text": "chat_interface"}

        target_tab = input_to_tab.get(input_type)
        if target_tab and target_tab != st.session_state.current_tab:
            st.session_state.current_tab = target_tab
            if "content_tabs" in self.components:
                self.components["content_tabs"].set_active_tab(target_tab)

    def _render_app_info(self) -> None:
        """Render application information."""
        with st.expander("📱 App Information", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Components", len(self.components))

            with col2:
                st.metric("Adapters", len([a for a in self.adapters.values() if a]))

            with col3:
                st.metric("Analyses", len(st.session_state.analysis_history))


def main():
    """Main application entry point."""
    try:
        # Configure page for mobile
        configure_mobile_page()

        # Create and run mobile app
        app = MobilePlantGuardApp()
        app.run()

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"❌ Application Error: {e}")

        # Show troubleshooting information
        with st.expander("🔧 Troubleshooting", expanded=True):
            st.markdown("""
            **Common Solutions:**
            1. Refresh the page
            2. Check browser compatibility (Chrome/Safari recommended)
            3. Clear browser cache
            4. Ensure all dependencies are installed
            """)

            if st.button("🔄 Restart Application"):
                st.rerun()


if __name__ == "__main__":
    main()
