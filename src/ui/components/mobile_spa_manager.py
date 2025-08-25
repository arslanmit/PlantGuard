"""
Mobile Single Page Application Manager for PlantGuard

This component manages content visibility and switching without page navigation.
It ensures all functionality stays on the same single page without st.rerun() calls.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from .mobile_component_registry import MobileComponent, ComponentMetadata, register_mobile_component


@register_mobile_component 
class MobileSPAManager(MobileComponent):
    """Single Page Application manager for mobile PlantGuard.
    
    Key Features:
    - Content visibility switching without page navigation
    - All content areas rendered simultaneously  
    - No st.rerun() calls that cause page redirects
    - Scroll-based navigation to different content sections
    - Session state management for content focus
    - True SPA behavior where everything stays on same page
    """
    
    def __init__(self, component_id: str = "mobile_spa_manager", **kwargs):
        super().__init__(component_id, **kwargs)
        self.content_areas = {}
        self.content_callbacks = {}
        
    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="spa_content_manager",
            display_name="Mobile SPA Manager",
            description="Manages content visibility and switching without page navigation",
            ai_agent_friendly_description=(
                "Single Page Application manager that controls content visibility "
                "without causing page redirects. All content rendered simultaneously "
                "with focus management for true SPA behavior."
            ),
            interactive_elements=[
                {
                    'id': 'content_focus_buttons',
                    'type': 'content_switcher',
                    'key': f'{self.component_id}_content_focus',
                    'description': 'Content focus buttons that scroll to sections',
                    'testable': True,
                    'no_page_redirect': True
                }
            ],
            state_dependencies=[
                'focused_content',
                'content_areas_initialized',
                'spa_mode_active'
            ],
            css_classes=[
                'mobile-spa-container',
                'mobile-content-section',
                'mobile-focus-indicator'
            ],
            test_scenarios=[
                {
                    'name': 'no_page_redirects',
                    'description': 'Test that no buttons cause page navigation',
                    'expected_outcome': 'All interactions stay on same page'
                },
                {
                    'name': 'content_visibility',
                    'description': 'Test content switching works without reloads',
                    'expected_outcome': 'Content focus changes without page refresh'
                }
            ],
            version="1.0.0",
            ai_agent_testable=True
        )
    
    def initialize_spa_state(self) -> None:
        """Initialize SPA state without causing page redirects."""
        # Content focus management (no page navigation)
        if 'focused_content' not in st.session_state:
            st.session_state.focused_content = 'image_analysis'
        
        # SPA mode activation
        if 'spa_mode_active' not in st.session_state:
            st.session_state.spa_mode_active = True
        
        # Content areas registry 
        if 'content_areas_initialized' not in st.session_state:
            st.session_state.content_areas_initialized = False
        
        # Prevent page navigation flags
        if 'prevent_page_redirects' not in st.session_state:
            st.session_state.prevent_page_redirects = True
    
    def register_content_area(self, area_id: str, title: str, icon: str, callback: Callable) -> None:
        """Register a content area for SPA management."""
        self.content_areas[area_id] = {
            'id': area_id,
            'title': title, 
            'icon': icon,
            'callback': callback,
            'enabled': True
        }
        self.content_callbacks[area_id] = callback
    
    def render_content_focus_bar(self) -> str:
        """Render content focus bar without page navigation."""
        if not self.content_areas:
            return st.session_state.get('focused_content', 'image_analysis')
        
        current_focus = st.session_state.get('focused_content', 'image_analysis')
        
        # Content focus header
        st.markdown("### 🎯 Focus on Content Area")
        st.markdown("**All content available below - click to highlight section**")
        
        # Create focus buttons (no st.rerun calls)
        content_list = list(self.content_areas.values())
        cols = st.columns(len(content_list))
        
        selected_focus = current_focus
        
        for i, content_area in enumerate(content_list):
            area_id = content_area['id']
            
            with cols[i]:
                is_focused = current_focus == area_id
                button_key = f"{self.component_id}_focus_{area_id}"
                
                # Focus button label
                button_label = f"{content_area['icon']} {content_area['title']}"
                if is_focused:
                    button_label += " 🎯"
                
                button_type = "primary" if is_focused else "secondary"
                
                # Render focus button (NO st.rerun() call)
                if st.button(
                    label=button_label,
                    key=button_key,
                    help=f"Focus on {content_area['title']} section",
                    use_container_width=True,
                    type=button_type,
                    disabled=False  # Always interactive
                ):
                    # Update focus WITHOUT page redirect
                    selected_focus = area_id
                    st.session_state.focused_content = selected_focus
                    # NO st.rerun() - this is the key fix!
                
                # Show focus status
                if is_focused:
                    st.success("Focused")
                else:
                    st.info("Available")
        
        return selected_focus
    
    def render_all_content_areas_spa(self) -> None:
        """Render all content areas simultaneously for true SPA experience."""
        if not self.content_areas:
            st.warning("No content areas registered")
            return
        
        current_focus = st.session_state.get('focused_content', 'image_analysis')
        
        st.markdown("### 📋 All PlantGuard Features")
        st.markdown("**Scroll through all features - everything on the same page**")
        
        # Render all content areas in sequence
        for area_id, content_area in self.content_areas.items():
            if not content_area.get('enabled', True):
                continue
            
            is_focused = current_focus == area_id
            
            # Content section container
            st.markdown(f'<div class="mobile-content-section" data-area="{area_id}" data-focused="{is_focused}">', unsafe_allow_html=True)
            
            # Section header with focus indicator
            if is_focused:
                st.markdown(f"## 🎯 {content_area['icon']} {content_area['title']} (Focused)")
                st.markdown('<div class="mobile-focus-indicator">Currently focused section</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"## {content_area['icon']} {content_area['title']}")
            
            # Render content using callback (no lazy loading)
            callback = self.content_callbacks.get(area_id)
            if callback and callable(callback):
                try:
                    callback()
                except Exception as e:
                    st.error(f"Error rendering {area_id} content: {e}")
            else:
                st.info(f"Content for {content_area['title']} is being loaded...")
            
            # Visual separator
            st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render(self) -> str:
        """Render the SPA interface."""
        return self.render_spa_interface()
    
    def render_spa_interface(self) -> str:
        """Render complete SPA interface without page navigation."""
        # Initialize SPA state
        self.initialize_spa_state()
        
        # SPA status indicator
        st.markdown('<div class="mobile-spa-indicator">', unsafe_allow_html=True)
        st.success("✅ Single Page Application - No page navigation!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Render content focus bar (returns focus without page redirect)
        focused_content = self.render_content_focus_bar()
        
        # Render all content areas simultaneously
        self.render_all_content_areas_spa()
        
        return focused_content
    
    def get_spa_status(self) -> Dict[str, Any]:
        """Get SPA status information."""
        return {
            'spa_mode_active': st.session_state.get('spa_mode_active', False),
            'focused_content': st.session_state.get('focused_content', 'image_analysis'),
            'content_areas_count': len(self.content_areas),
            'prevent_page_redirects': st.session_state.get('prevent_page_redirects', True),
            'registered_areas': list(self.content_areas.keys())
        }
    
    def prevent_page_redirect(self, button_callback: Callable) -> Any:
        """Wrapper to prevent button callbacks from causing page redirects."""
        try:
            result = button_callback()
            # Update state but don't call st.rerun()
            return result
        except Exception as e:
            st.error(f"Error in button callback: {e}")
            return None
    
    def safe_button_click(self, button_id: str, action: Callable) -> bool:
        """Safe button click handler that prevents page redirects."""
        button_key = f"{self.component_id}_safe_{button_id}"
        
        # Create button that doesn't cause page redirect
        clicked = st.button(
            label=button_id,
            key=button_key,
            use_container_width=True
        )
        
        if clicked:
            # Execute action WITHOUT st.rerun()
            try:
                action()
                return True
            except Exception as e:
                st.error(f"Error executing action: {e}")
                return False
        
        return False


def create_spa_manager() -> MobileSPAManager:
    """Factory function to create SPA manager."""
    return MobileSPAManager("mobile_spa_manager")


def register_default_content_areas(spa_manager: MobileSPAManager) -> None:
    """Register default PlantGuard content areas."""
    
    def image_analysis_content():
        st.markdown("### 📸 Image Analysis")
        st.file_uploader("Upload plant image", type=['jpg', 'jpeg', 'png'], key="spa_image_upload")
        st.info("Upload an image to analyze your plant's health")
    
    def voice_assistant_content():
        st.markdown("### 🎤 Voice Assistant")
        if st.button("🎙️ Start Recording", key="spa_voice_record"):
            st.info("Voice recording feature")
        st.info("Voice assistant for plant care questions")
    
    def chat_interface_content():
        st.markdown("### 💬 Chat Assistant")
        st.text_input("Ask about plant care", key="spa_chat_input", placeholder="How often should I water my plants?")
        st.info("Chat with AI about plant care")
    
    def history_settings_content():
        st.markdown("### 📊 History & Settings")
        st.info("View your analysis history and adjust settings")
        
        # Settings without page redirect
        if st.checkbox("Enable notifications", key="spa_notifications"):
            st.success("Notifications enabled")
    
    # Register all content areas
    spa_manager.register_content_area('image_analysis', 'Image Analysis', '📸', image_analysis_content)
    spa_manager.register_content_area('voice_assistant', 'Voice Assistant', '🎤', voice_assistant_content)  
    spa_manager.register_content_area('chat_interface', 'Chat Assistant', '💬', chat_interface_content)
    spa_manager.register_content_area('history_settings', 'History & Settings', '📊', history_settings_content)