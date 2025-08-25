"""
Mobile Layout Manager for PlantGuard

Manages the main mobile layout with fixed-width scrollable container,
optimized for Chrome and Safari mobile browsers.

AI Agent Friendly Features:
- Clear component structure
- Predictable layout behavior
- Built-in testing capabilities
- Responsive design patterns
"""

import streamlit as st
from typing import Any, Dict, List, Optional
from .mobile_component_registry import MobileComponent, ComponentMetadata, register_mobile_component


@register_mobile_component
class MobileLayoutManager(MobileComponent):
    """Main layout manager for mobile PlantGuard application.
    
    Features:
    - Fixed-width container (428px max for mobile)
    - Safe area support for notched devices
    - Smooth scrolling optimization
    - CSS framework integration
    - AI agent testable structure
    """
    
    def __init__(self, component_id: str = "mobile_layout_manager", **kwargs):
        super().__init__(component_id, **kwargs)
        self.mobile_css_loaded = False
        self.safe_areas_configured = False
        
    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="layout_manager",
            display_name="Mobile Layout Manager",
            description="Main container managing mobile layout and styling",
            ai_agent_friendly_description=(
                "This component creates the main mobile container with fixed width, "
                "handles CSS loading, manages safe areas, and provides scrollable content area"
            ),
            interactive_elements=[
                {
                    'id': 'mobile_app_container',
                    'type': 'container',
                    'description': 'Main app container',
                    'testable': True
                }
            ],
            state_dependencies=[
                'mobile_css_loaded',
                'mobile_layout_initialized'
            ],
            css_classes=[
                'mobile-app-container',
                'mobile-content-wrapper'
            ],
            test_scenarios=[
                {
                    'name': 'css_loading',
                    'description': 'Test CSS framework loading',
                    'expected_outcome': 'Mobile CSS classes available'
                },
                {
                    'name': 'container_width',
                    'description': 'Test fixed-width container',
                    'expected_outcome': 'Container max-width set to 428px'
                },
                {
                    'name': 'safe_areas',
                    'description': 'Test safe area handling',
                    'expected_outcome': 'Safe area insets applied'
                }
            ],
            ai_agent_instructions={
                'testing': 'Verify CSS loading, container dimensions, and safe area support',
                'fixing': 'Auto-load CSS if missing, initialize layout state variables',
                'monitoring': 'Check for layout shifts, scrolling performance'
            },
            version="1.0.0",
            ai_agent_testable=True,
            auto_fix_enabled=True
        )
    
    def load_mobile_css(self) -> bool:
        """Load mobile CSS framework."""
        try:
            css_path = "assets/mobile_styles.css"
            
            # Read CSS file
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    mobile_css = f.read()
            except FileNotFoundError:
                # Fallback CSS if file not found
                mobile_css = self._get_fallback_css()
            
            # Inject CSS into Streamlit
            st.markdown(f"<style>{mobile_css}</style>", unsafe_allow_html=True)
            
            # Update session state
            st.session_state.mobile_css_loaded = True
            self.mobile_css_loaded = True
            
            return True
            
        except Exception as e:
            st.error(f"Failed to load mobile CSS: {e}")
            return False
    
    def _get_fallback_css(self) -> str:
        """Provide fallback CSS if main file unavailable - Fixed 428px mobile design."""
        return """
        /* Fallback Mobile CSS - Fixed 428px Design for All Screens */
        :root {
            --mobile-max-width: 428px;
            --mobile-space-md: 16px;
            --mobile-primary: #16A34A;
            --mobile-bg-primary: #FFFFFF;
            --mobile-touch-target: 44px;
            --mobile-border-radius: 12px;
        }
        
        .mobile-app-container {
            width: 100%;
            max-width: var(--mobile-max-width); /* Always 428px */
            margin: 0 auto;
            min-height: 100vh;
            padding: var(--mobile-space-md);
            background-color: var(--mobile-bg-primary);
        }
        
        .mobile-content-wrapper {
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: var(--mobile-space-md);
        }
        """
    
    def configure_safe_areas(self) -> None:
        """Configure safe areas for notched devices."""
        safe_area_css = """
        <style>
        .mobile-app-container {
            padding-top: max(env(safe-area-inset-top, 0px), 16px);
            padding-bottom: max(env(safe-area-inset-bottom, 0px), 16px);
            padding-left: max(env(safe-area-inset-left, 0px), 16px);
            padding-right: max(env(safe-area-inset-right, 0px), 16px);
        }
        </style>
        """
        st.markdown(safe_area_css, unsafe_allow_html=True)
        self.safe_areas_configured = True
    
    def initialize_mobile_layout(self) -> None:
        """Initialize mobile layout state and configuration."""
        # Initialize session state variables
        if 'mobile_layout_initialized' not in st.session_state:
            st.session_state.mobile_layout_initialized = False
        
        if 'mobile_css_loaded' not in st.session_state:
            st.session_state.mobile_css_loaded = False
        
        if 'mobile_viewport_configured' not in st.session_state:
            st.session_state.mobile_viewport_configured = False
        
        # Configure viewport for mobile
        if not st.session_state.mobile_viewport_configured:
            self._configure_mobile_viewport()
            st.session_state.mobile_viewport_configured = True
        
        # Load CSS if not already loaded
        if not st.session_state.mobile_css_loaded:
            self.load_mobile_css()
        
        # Configure safe areas
        if not self.safe_areas_configured:
            self.configure_safe_areas()
        
        st.session_state.mobile_layout_initialized = True
    
    def _configure_mobile_viewport(self) -> None:
        """Configure mobile viewport settings."""
        viewport_meta = """
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="theme-color" content="#16A34A">
        """
        # Note: In a real Streamlit app, viewport would be set in page config
        # This is for documentation/testing purposes
    
    def render(self, content: Any = None, **kwargs) -> None:
        """Render the mobile layout container.
        
        Args:
            content: Content to render inside the container
            **kwargs: Additional rendering options
        """
        # Initialize layout if not done
        if not st.session_state.get('mobile_layout_initialized', False):
            self.initialize_mobile_layout()
        
        # Create main mobile container with streamlit container
        with st.container():
            # Render provided content directly
            if content:
                if callable(content):
                    content()
                else:
                    st.write(content)
            elif 'children' in kwargs:
                # Render child components
                for child in kwargs['children']:
                    if hasattr(child, 'render'):
                        child.render()
                    else:
                        st.write(child)
    
    def render_with_header_footer(self, header: Any = None, content: Any = None, footer: Any = None) -> None:
        """Render layout with header, content, and footer sections."""
        self.initialize_mobile_layout()
        
        with st.container():
            # Header section
            if header:
                if callable(header):
                    header()
                else:
                    st.write(header)
            
            # Main content section
            if content:
                if callable(content):
                    content()
                else:
                    st.write(content)
            
            # Footer section
            if footer:
                if callable(footer):
                    footer()
                else:
                    st.write(footer)
    
    def get_layout_status(self) -> Dict[str, Any]:
        """Get current layout status for AI agent monitoring."""
        return {
            'component_id': self.component_id,
            'css_loaded': st.session_state.get('mobile_css_loaded', False),
            'layout_initialized': st.session_state.get('mobile_layout_initialized', False),
            'viewport_configured': st.session_state.get('mobile_viewport_configured', False),
            'safe_areas_configured': self.safe_areas_configured,
            'container_classes': self.metadata.css_classes,
            'status': 'ready' if all([
                st.session_state.get('mobile_css_loaded', False),
                st.session_state.get('mobile_layout_initialized', False)
            ]) else 'initializing'
        }
    
    def debug_layout_info(self) -> Dict[str, Any]:
        """Get debug information for AI agent analysis."""
        return {
            'layout_manager_id': self.component_id,
            'session_state_vars': {
                key: value for key, value in st.session_state.items() 
                if key.startswith('mobile_')
            },
            'component_metadata': {
                'type': self.metadata.component_type,
                'css_classes': self.metadata.css_classes,
                'state_dependencies': self.metadata.state_dependencies
            },
            'layout_status': self.get_layout_status(),
            'ai_agent_context': self.get_ai_agent_context()
        }


# Utility functions for easy usage
def create_mobile_layout(component_id: str = "main_layout") -> MobileLayoutManager:
    """Create and return a MobileLayoutManager instance."""
    return MobileLayoutManager(component_id)


def render_mobile_app(content_function: callable, header: Any = None, footer: Any = None):
    """Convenience function to render mobile app with layout manager."""
    layout_manager = create_mobile_layout()
    
    if header or footer:
        layout_manager.render_with_header_footer(
            header=header,
            content=content_function,
            footer=footer
        )
    else:
        layout_manager.render(content=content_function)
    
    return layout_manager