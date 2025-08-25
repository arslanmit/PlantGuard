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

import streamlit as st
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import mobile components
from ui.components.mobile_layout_manager import MobileLayoutManager
from ui.components.mobile_header import MobileHeader
from ui.components.mobile_input_ribbon import MobileInputRibbon
from ui.components.mobile_content_tabs import MobileContentTabs
from ui.components.mobile_image_analysis import MobileImageAnalysis
from ui.components.mobile_voice_interface import MobileVoiceInterface
from ui.components.mobile_chat_interface import MobileChatInterface
from ui.components.mobile_component_registry import mobile_component_registry
from ui.components.ai_agent_testing import ai_testing_framework

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration for mobile with fixed 428px design - NO SIDEBAR
st.set_page_config(
    page_title="PlantGuard Mobile",
    page_icon="🌿",
    layout="wide",  # Will be constrained to 428px by CSS
    initial_sidebar_state="collapsed",  # Start collapsed
    menu_items={
        'Get Help': 'https://github.com/arslanmit/PlantGuard',
        'Report a bug': 'https://github.com/arslanmit/PlantGuard/issues',
        'About': 'PlantGuard Mobile - AI-powered plant disease detection (Fixed 428px mobile design)'
    }
)

# Hide sidebar completely with CSS
st.markdown("""
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
""", unsafe_allow_html=True)


class MobilePlantGuardApp:
    """Main mobile PlantGuard application class.
    
    Integrates all mobile components into a unified SPA experience.
    Provides AI agent testing and autonomous development capabilities.
    """
    
    def __init__(self):
        self.layout_manager = None
        self.header = None
        self.input_ribbon = None
        self.content_tabs = None
        self.image_analysis = None
        self.voice_interface = None
        self.chat_interface = None
        
        # Initialize session state
        self.initialize_app_state()
        
    def initialize_app_state(self) -> None:
        """Initialize essential application-wide session state only."""
        # Core app state
        if 'mobile_app_initialized' not in st.session_state:
            st.session_state.mobile_app_initialized = False
        
        # Navigation essentials
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = 'image_analysis'
        
        # App start time
        if 'app_start_time' not in st.session_state:
            import time
            st.session_state.app_start_time = time.time()
        
        # Mobile-specific essentials
        if 'mobile_viewport_width' not in st.session_state:
            st.session_state.mobile_viewport_width = 428  # Always 428px
        
        if 'fixed_mobile_design' not in st.session_state:
            st.session_state.fixed_mobile_design = True
        
        # Initialize component-specific state
        self._initialize_component_states()
    
    def initialize_components(self) -> None:
        """Initialize all mobile components."""
        try:
            # Initialize layout manager
            self.layout_manager = MobileLayoutManager("main_layout")
            
            # Initialize header
            self.header = MobileHeader(
                "mobile_header",
                title="PlantGuard",
                subtitle="AI Plant Care Assistant"
            )
            
            # Initialize input ribbon
            self.input_ribbon = MobileInputRibbon(
                "mobile_input_ribbon",
                layout_style='grid'
            )
            
            # Initialize content tabs
            self.content_tabs = MobileContentTabs(
                "mobile_content_tabs",
                tab_style='pills'
            )
            
            # Initialize feature components
            self.image_analysis = MobileImageAnalysis("mobile_image_analysis")
            self.voice_interface = MobileVoiceInterface("mobile_voice_interface")
            self.chat_interface = MobileChatInterface("mobile_chat_interface")
            
            # Register tab content callbacks
            self.register_tab_content()
            
            # Initialize advanced state management
            self._setup_state_persistence()
            self._setup_state_validation()
            
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
            if not hasattr(self, 'layout_manager') or not self.layout_manager:
                self.layout_manager = MobileLayoutManager("fallback_layout")
            
            # Create fallback content function
            def render_fallback_content():
                st.markdown("### 🌿 PlantGuard Mobile - Loading...")
                st.info("Some components are still initializing. Please refresh if issues persist.")
                
                if st.button("🔄 Refresh App", use_container_width=True):
                    # Clear initialization state to force re-init
                    st.session_state.mobile_app_initialized = False
                    st.rerun()
            
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
        if 'mobile_css_loaded' not in st.session_state:
            st.session_state.mobile_css_loaded = False
        
        if 'mobile_layout_initialized' not in st.session_state:
            st.session_state.mobile_layout_initialized = False
        
        # MobileHeader state
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = 'default'
        
        if 'system_status' not in st.session_state:
            st.session_state.system_status = 'ready'
        
        # MobileImageAnalysis state
        if 'uploaded_image' not in st.session_state:
            st.session_state.uploaded_image = None
        
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        
        if 'analysis_in_progress' not in st.session_state:
            st.session_state.analysis_in_progress = False
        
        # MobileVoiceInterface state
        if 'recorded_audio' not in st.session_state:
            st.session_state.recorded_audio = None
        
        if 'transcribed_text' not in st.session_state:
            st.session_state.transcribed_text = ""
        
        if 'voice_response' not in st.session_state:
            st.session_state.voice_response = ""
        
        # MobileChatInterface state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'current_chat_input' not in st.session_state:
            st.session_state.current_chat_input = ""
    
    def _setup_state_persistence(self) -> None:
        """Setup state persistence for mobile session continuity."""
        # Create state backup for critical data
        critical_state_keys = [
            'analysis_history',
            'user_preferences',
            'feature_usage_stats',
            'ai_agent_test_results'
        ]
        
        if 'state_backup' not in st.session_state:
            st.session_state.state_backup = {}
        
        # Backup critical state
        for key in critical_state_keys:
            if key in st.session_state:
                st.session_state.state_backup[key] = st.session_state[key]
    
    def _setup_state_validation(self) -> None:
        """Setup state validation for data integrity."""
        # Validate analysis history structure
        if 'analysis_history' in st.session_state:
            valid_history = []
            for item in st.session_state.analysis_history:
                if isinstance(item, dict) and 'timestamp' in item:
                    valid_history.append(item)
            st.session_state.analysis_history = valid_history
        
        # Validate user preferences
        if 'user_preferences' in st.session_state:
            default_prefs = {
                'theme': 'auto',
                'notifications': True,
                'auto_clear_chat': False,
                'voice_auto_transcribe': True,
                'image_auto_analysis': False
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
        import time
        
        if st.session_state.current_tab != new_tab:
            # Update previous tab
            st.session_state.previous_tab = st.session_state.current_tab
            
            # Add to tab history
            st.session_state.tab_history.append({
                'from_tab': st.session_state.current_tab,
                'to_tab': new_tab,
                'timestamp': time.time()
            })
            
            # Limit history size
            if len(st.session_state.tab_history) > 50:
                st.session_state.tab_history = st.session_state.tab_history[-50:]
            
            # Update current tab
            st.session_state.current_tab = new_tab
            
            # Update feature usage
            self.update_feature_usage(new_tab)
    
    def save_analysis_result(self, result: Dict[str, Any], analysis_type: str = 'unknown') -> None:
        """Save analysis result to history with metadata."""
        import time
        
        analysis_record = {
            'timestamp': time.time(),
            'analysis_type': analysis_type,
            'result': result,
            'session_id': f"session_{int(st.session_state.app_start_time)}",
            'tab_context': st.session_state.current_tab
        }
        
        st.session_state.analysis_history.append(analysis_record)
        
        # Limit history size (keep last 100 analyses)
        if len(st.session_state.analysis_history) > 100:
            st.session_state.analysis_history = st.session_state.analysis_history[-100:]
    
    def get_session_analytics(self) -> Dict[str, Any]:
        """Get comprehensive session analytics."""
        import time
        
        current_time = time.time()
        session_duration = current_time - st.session_state.app_start_time
        
        return {
            'session_duration': session_duration,
            'interactions': st.session_state.interaction_count,
            'touch_interactions': st.session_state.touch_interactions,
            'feature_usage': st.session_state.feature_usage_stats.copy(),
            'analyses_performed': len(st.session_state.analysis_history),
            'tab_switches': len(st.session_state.tab_history),
            'current_tab': st.session_state.current_tab,
            'ai_agent_active': st.session_state.ai_agent_active,
            'component_errors': len(st.session_state.component_error_log)
        }
    
    def register_tab_content(self) -> None:
        """Register content callbacks for each tab."""
        # Register image analysis tab
        self.content_tabs.register_tab_content(
            'image_analysis',
            self.render_image_analysis_tab
        )
        
        # Register voice assistant tab
        self.content_tabs.register_tab_content(
            'voice_assistant',
            self.render_voice_assistant_tab
        )
        
        # Register chat interface tab
        self.content_tabs.register_tab_content(
            'chat_interface',
            self.render_chat_interface_tab
        )
        
        # Register history & settings tab
        self.content_tabs.register_tab_content(
            'history_settings',
            self.render_history_settings_tab
        )
        
        # Register comparison tab
        self.content_tabs.register_tab_content(
            'comparison',
            self.render_comparison_tab
        )
    
    def render_image_analysis_tab(self) -> None:
        """Render image analysis tab content."""
        self.image_analysis.render()
    
    def render_voice_assistant_tab(self) -> None:
        """Render voice assistant tab content."""
        self.voice_interface.render()
    
    def render_chat_interface_tab(self) -> None:
        """Render chat interface tab content."""
        self.chat_interface.render()
    
    def render_history_settings_tab(self) -> None:
        """Render history and settings tab content."""
        st.markdown("### 📊 Analysis History")
        
        # Analysis history
        history = st.session_state.get('analysis_history', [])
        if history:
            for i, analysis in enumerate(history[-5:]):
                with st.expander(f"Analysis {len(history) - i}", expanded=False):
                    st.json(analysis)
        else:
            st.info("No analysis history yet. Analyze some plants to see results here!")
        
        st.markdown("### ⚙️ Settings")
        
        # App settings
        col1, col2 = st.columns(2)
        
        with col1:
            # AI Agent controls
            st.markdown("**🤖 AI Agent**")
            
            if st.button("Run Component Tests", use_container_width=True):
                with st.spinner("Running AI agent tests..."):
                    test_results = ai_testing_framework.test_all_components()
                    if test_results:
                        st.success(f"Tests completed: {test_results.get('components_tested', 0)} components tested")
                        st.json(test_results)
            
            # Health monitoring
            if st.button("Check Component Health", use_container_width=True):
                health_report = ai_testing_framework.get_component_health_report()
                st.json(health_report)
        
        with col2:
            # App preferences
            st.markdown("**📱 Preferences**")
            
            # Theme selection (placeholder)
            theme = st.selectbox(
                "Theme",
                ["Auto", "Light", "Dark"],
                key="mobile_theme_select"
            )
            
            # Notification settings
            notifications = st.checkbox(
                "Enable notifications",
                key="mobile_notifications"
            )
            
            # Auto-clear chat
            auto_clear = st.checkbox(
                "Auto-clear chat after analysis",
                key="mobile_auto_clear_chat"
            )
        
        # App information
        st.markdown("### ℹ️ App Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Session Duration", self.get_session_duration())
        
        with col2:
            component_count = len(mobile_component_registry.get_all_components())
            st.metric("Components", component_count)
        
        with col3:
            active_tab = st.session_state.get('current_tab', 'unknown')
            st.metric("Active Tab", active_tab.replace('_', ' ').title())
    
    def render_comparison_tab(self) -> None:
        """Render comparison tab content."""
        st.markdown("### ⚖️ Plant Comparison")
        
        st.info("🚧 Advanced comparison features coming soon!")
        
        # Placeholder comparison interface
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Plant A**")
            img1 = st.file_uploader(
                "Upload first image",
                type=['jpg', 'jpeg', 'png'],
                key="comparison_img1"
            )
            if img1:
                st.image(img1, use_column_width=True)
        
        with col2:
            st.markdown("**Plant B**")
            img2 = st.file_uploader(
                "Upload second image",
                type=['jpg', 'jpeg', 'png'],
                key="comparison_img2"
            )
            if img2:
                st.image(img2, use_column_width=True)
        
        if img1 and img2:
            if st.button("Compare Plants", use_container_width=True, type="primary"):
                st.success("Comparison feature will analyze both images and show differences!")
    
    def get_session_duration(self) -> str:
        """Get formatted session duration."""
        import time
        start_time = st.session_state.get('app_start_time', time.time())
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
            input_to_tab_mapping = {
                'text': 'chat_interface',
                'voice': 'voice_assistant',
                'camera': 'image_analysis',
                'upload': 'image_analysis'
            }
            
            target_tab = input_to_tab_mapping.get(selected_input)
            if target_tab:
                # Track tab navigation
                self.track_tab_navigation(target_tab)
                
                # Update input mode timestamp
                import time
                st.session_state.current_input_mode = selected_input
                st.session_state.last_input_timestamp = time.time()
                
                # Set active tab and focus content WITHOUT st.rerun()
                st.session_state.focused_content = target_tab
                self.content_tabs.set_active_tab(target_tab)
    
    def render_ai_agent_status(self) -> None:
        """Render AI agent status indicator in main content without page redirects."""
        # Move AI agent status to main content instead of sidebar
        with st.expander("🤖 AI Agent Status", expanded=False):
            if st.session_state.get('ai_agent_active', False):
                st.success("🤖 AI Agent Active")
                
                if st.button("Run Tests", use_container_width=True, key="spa_ai_tests"):
                    with st.spinner("AI Agent running tests..."):
                        results = ai_testing_framework.test_all_components()
                        st.json(results)
            else:
                if st.button("Activate AI Agent", use_container_width=True, key="spa_activate_ai"):
                    st.session_state.ai_agent_active = True
                    st.success("AI Agent activated - no page refresh needed!")
    
    def run(self) -> None:
        """Run the mobile PlantGuard application."""
        # Initialize components if not done
        if not st.session_state.get('mobile_app_initialized', False):
            self.initialize_components()
        
        # Check initialization status with detailed feedback
        if not st.session_state.get('mobile_app_initialized', False):
            st.error("❌ Application failed to initialize properly")
            
            # Show fallback content
            st.markdown("### 🌿 PlantGuard Mobile - Initialization Error")
            st.markdown("The mobile app components failed to initialize. Please try refreshing the page.")
            
            # Basic troubleshooting
            if st.button("🔄 Try to Reinitialize", use_container_width=True, key="spa_reinitialize"):
                st.session_state.mobile_app_initialized = False
                st.success("Reinitializing - page will refresh once for full restart")
                st.rerun()
            
            # Show minimal functionality
            st.markdown("#### 🔧 Basic Functionality")
            st.info("For full functionality, please refresh the page or check console logs.")
            return
        
        # Render AI agent status in main content instead of sidebar
        self.render_ai_agent_status()
        
        # Load mobile CSS first
        if self.layout_manager and not st.session_state.get('mobile_css_loaded', False):
            self.layout_manager.load_mobile_css()
        
        # Render app content directly
        try:
            # Header
            if self.header:
                self.header.render()
            else:
                st.markdown("### 🌿 PlantGuard Mobile")
            
            # Input ribbon with tab integration
            if self.input_ribbon:
                self.render_input_ribbon_integration()
            else:
                st.info("Input ribbon component not available")
            
            # Content tabs with SPA navigation tracking - no page redirects
            if self.content_tabs:
                focused_content = self.content_tabs.render()
                
                # Track tab changes WITHOUT st.rerun()
                if focused_content != st.session_state.get('focused_content', 'image_analysis'):
                    self.track_tab_navigation(focused_content)
                    st.session_state.focused_content = focused_content
            else:
                # Basic functionality as fallback
                st.markdown("**Basic Plant Analysis:**")
                uploaded_file = st.file_uploader("Upload plant image", type=['jpg', 'jpeg', 'png'])
                if uploaded_file:
                    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
                    st.info("Full analysis features will be available when all components are loaded.")
        
        except Exception as e:
            st.error(f"❌ Error rendering app content: {e}")
            logger.error(f"App content rendering error: {e}")
            
            # Show emergency fallback
            st.markdown("### 🌿 PlantGuard Mobile - Emergency Mode")
            st.markdown("The app is running in emergency mode. Some features may not be available.")
            
            if st.button("🔄 Try Full Restart", use_container_width=True, key="spa_full_restart"):
                # Clear all mobile app state
                keys_to_clear = [k for k in st.session_state.keys() if k.startswith('mobile_')]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.success("Full restart initiated - page will refresh once")
                st.rerun()
        
        # Add app info and component status inline
        self.render_app_info_inline()

    def render_app_info_inline(self) -> None:
        """Render app info and component status inline in main content."""
        # App info in expandable section
        with st.expander("📱 PlantGuard Mobile Info", expanded=False):
            st.markdown("**Version:** 1.0.0-mobile")
            st.markdown("📱 **Mobile:** Chrome & Safari Optimized")
            st.markdown("💻 **Desktop:** Fixed 428px Mobile View")
            st.markdown("🎯 **Design:** Always 428px width (mobile-first)")
            
            # Fixed mobile design indicator
            st.success("✨ **Always-Visible Design** - No hidden menus!")
            st.info("📐 **Fixed Width:** 428px on all screens")
        
        # Component status in expandable section
        with st.expander("🔧 Component Status", expanded=False):
            components_status = {
                "Layout Manager": self.layout_manager.get_layout_status().get('status', 'unknown') if self.layout_manager else "not_loaded",
                "Header": "ready" if self.header else "not_loaded",
                "Input Ribbon": "ready" if self.input_ribbon else "not_loaded",
                "Content Tabs": "ready" if self.content_tabs else "not_loaded",
            }
            
            for component, status in components_status.items():
                if status == "ready":
                    st.success(f"✅ {component}")
                elif status == "initializing":
                    st.warning(f"🔄 {component}")
                else:
                    st.error(f"❌ {component}")
        
        # Quick actions in expandable section
        with st.expander("⚡ Quick Actions", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Refresh Components", use_container_width=True, key="spa_refresh_components"):
                    st.session_state.mobile_app_initialized = False
                    st.success("Refreshing components - page will reload once")
                    st.rerun()
            
            with col2:
                if st.button("🧪 Run AI Tests", use_container_width=True, key="spa_run_tests"):
                    with st.spinner("Testing all components..."):
                        test_results = ai_testing_framework.test_all_components()
                        if test_results.get('components_tested', 0) > 0:
                            st.success(f"✅ Tested {test_results['components_tested']} components")
                            if test_results.get('tests_failed', 0) > 0:
                                st.warning(f"⚠️ {test_results['tests_failed']} tests failed")
                        else:
                            st.error("❌ No components found to test")


def main():
    """Main application entry point."""
    try:
        # Create and run the mobile app
        app = MobilePlantGuardApp()
        app.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"Application Error: {e}")
        st.markdown("### 🔧 Troubleshooting")
        st.markdown("""
        1. **Refresh the page** - Sometimes a simple reload fixes issues
        2. **Check browser compatibility** - Use Chrome or Safari mobile
        3. **Clear browser cache** - Old cached files can cause problems
        4. **Check console logs** - Look for JavaScript errors in browser dev tools
        """)
        
        # Show debug information in expander
        with st.expander("🐛 Debug Information"):
            st.markdown(f"**Error:** {str(e)}")
            st.markdown(f"**Session State Keys:** {list(st.session_state.keys())}")
            st.markdown(f"**Python Path:** {sys.path[:3]}...")


if __name__ == "__main__":
    main()