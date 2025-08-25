"""
Mobile Chat Interface for PlantGuard

Integrates TextAdapter with mobile-optimized chat UI.
Provides conversational plant care assistance with chat history.
"""

import streamlit as st
from typing import Any, Dict, List, Optional, Tuple
import time
import json
from datetime import datetime

# Import existing adapters
try:
    from core.nlp import TextAdapter
except ImportError:
    # Fallback for development/testing
    from src.adapters_compat import TextAdapter

from .mobile_component_registry import MobileComponent, ComponentMetadata, register_mobile_component


@register_mobile_component
class MobileChatInterface(MobileComponent):
    """Mobile-optimized chat interface for plant care assistance.
    
    Features:
    - Touch-friendly chat input
    - Conversational message display
    - Chat history management
    - Quick question suggestions
    - Mobile-optimized scrolling
    - AI agent testable
    """
    
    def __init__(self, component_id: str = "mobile_chat_interface", **kwargs):
        super().__init__(component_id, **kwargs)
        self.text_adapter = None
        self.max_chat_history = kwargs.get('max_chat_history', 50)
        self.show_suggestions = kwargs.get('show_suggestions', True)
        self.auto_scroll = kwargs.get('auto_scroll', True)
        
    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="chat_interface",
            display_name="Mobile Chat Interface",
            description="Mobile chat interface for plant care Q&A conversations",
            ai_agent_friendly_description=(
                "Chat interface component that provides mobile-optimized conversational "
                "interface for plant care questions with TextAdapter integration"
            ),
            interactive_elements=[
                {
                    'id': 'chat_input',
                    'type': 'text_input',
                    'key': f'{self.component_id}_chat_input',
                    'description': 'Chat message input field',
                    'testable': True
                },
                {
                    'id': 'send_button',
                    'type': 'button',
                    'key': f'{self.component_id}_send',
                    'description': 'Send message button',
                    'testable': True
                },
                {
                    'id': 'clear_chat_button',
                    'type': 'button',
                    'key': f'{self.component_id}_clear_chat',
                    'description': 'Clear chat history button',
                    'testable': True
                },
                {
                    'id': 'suggestion_buttons',
                    'type': 'button_group',
                    'description': 'Quick question suggestion buttons',
                    'testable': True
                }
            ],
            state_dependencies=[
                'chat_messages',
                'chat_input_text',
                'processing_message',
                'text_adapter_loaded'
            ],
            css_classes=[
                'mobile-chat-interface',
                'mobile-chat-messages',
                'mobile-chat-input',
                'mobile-message-bubble'
            ],
            test_scenarios=[
                {
                    'name': 'message_sending',
                    'description': 'Test sending chat messages',
                    'expected_outcome': 'Messages send and display correctly'
                },
                {
                    'name': 'response_generation',
                    'description': 'Test AI response generation',
                    'expected_outcome': 'AI generates appropriate responses'
                },
                {
                    'name': 'chat_history',
                    'description': 'Test chat history management',
                    'expected_outcome': 'Chat history persists and scrolls properly'
                },
                {
                    'name': 'suggestions',
                    'description': 'Test quick question suggestions',
                    'expected_outcome': 'Suggestion buttons work and populate input'
                }
            ],
            ai_agent_instructions={
                'testing': 'Test message sending, response generation, history management, suggestions',
                'fixing': 'Initialize TextAdapter, handle message errors, fix scrolling issues',
                'monitoring': 'Monitor response quality, chat performance, user engagement'
            },
            version="1.0.0",
            ai_agent_testable=True,
            auto_fix_enabled=True
        )
    
    def initialize_chat_components(self) -> None:
        """Initialize chat interface components."""
        # Initialize session state
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        if 'chat_input_text' not in st.session_state:
            st.session_state.chat_input_text = ""
        
        if 'processing_message' not in st.session_state:
            st.session_state.processing_message = False
        
        if 'text_adapter_loaded' not in st.session_state:
            st.session_state.text_adapter_loaded = False
        
        # Initialize TextAdapter if not already done
        if not self.text_adapter:
            try:
                self.text_adapter = TextAdapter()
                st.session_state.text_adapter_loaded = True
            except Exception as e:
                st.error(f"Failed to initialize TextAdapter: {e}")
                st.session_state.text_adapter_loaded = False
        
        # Add welcome message if chat is empty
        if not st.session_state.chat_messages:
            welcome_message = {
                'role': 'assistant',
                'content': '🌱 Hello! I\'m your PlantGuard AI assistant. Ask me anything about plant care, diseases, or gardening tips!',
                'timestamp': time.time()
            }
            st.session_state.chat_messages.append(welcome_message)
    
    def get_quick_suggestions(self) -> List[str]:
        """Get quick question suggestions for users."""
        return [
            "Why are my plant leaves turning yellow?",
            "How often should I water my plants?",
            "What are these brown spots on leaves?",
            "My plant looks wilted, what should I do?",
            "How much sunlight does my plant need?",
            "What's the best fertilizer for houseplants?"
        ]
    
    def render_chat_messages(self) -> None:
        """Render chat message history."""
        messages = st.session_state.get('chat_messages', [])
        
        if not messages:
            st.info("💬 Start a conversation by asking a plant care question!")
            return
        
        # Create scrollable container for messages
        st.markdown('<div class="mobile-chat-messages" style="max-height: 400px; overflow-y: auto; padding: 1rem; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 1rem;">', 
                   unsafe_allow_html=True)
        
        for i, message in enumerate(messages):
            role = message.get('role', 'user')
            content = message.get('content', '')
            timestamp = message.get('timestamp', time.time())
            
            # Format timestamp
            time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M')
            
            if role == 'user':
                # User message (right-aligned)
                st.markdown(f"""
                <div class="mobile-message-bubble user-message" style="
                    background-color: #16A34A;
                    color: white;
                    padding: 0.75rem;
                    border-radius: 12px 12px 4px 12px;
                    margin: 0.5rem 0 0.5rem 2rem;
                    text-align: left;
                ">
                    <div>{content}</div>
                    <div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.25rem;">{time_str}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message (left-aligned)
                st.markdown(f"""
                <div class="mobile-message-bubble assistant-message" style="
                    background-color: #F0F9F0;
                    color: #1F2937;
                    padding: 0.75rem;
                    border-radius: 12px 12px 12px 4px;
                    margin: 0.5rem 2rem 0.5rem 0;
                    text-align: left;
                    border-left: 3px solid #16A34A;
                ">
                    <div>🤖 {content}</div>
                    <div style="font-size: 0.75rem; opacity: 0.6; margin-top: 0.25rem;">{time_str}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_quick_suggestions(self) -> Optional[str]:
        """Render quick question suggestions.
        
        Returns:
            str: Selected suggestion text or None
        """
        if not self.show_suggestions:
            return None
        
        suggestions = self.get_quick_suggestions()
        selected_suggestion = None
        
        st.markdown("**💡 Quick Questions:**")
        
        # Display suggestions in a compact grid
        cols = st.columns(2)
        
        for i, suggestion in enumerate(suggestions[:4]):  # Show first 4 suggestions
            col_index = i % 2
            
            with cols[col_index]:
                if st.button(
                    suggestion,
                    key=f"{self.component_id}_suggestion_{i}",
                    help="Click to use this question",
                    use_container_width=True
                ):
                    selected_suggestion = suggestion
                    st.session_state.chat_input_text = suggestion
        
        return selected_suggestion
    
    def render_chat_input(self) -> Tuple[str, bool]:
        """Render chat input interface.
        
        Returns:
            Tuple of (input_text, send_clicked)
        """
        # Chat input form
        with st.form(key=f"{self.component_id}_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input(
                    "Ask about plant care...",
                    value=st.session_state.get('chat_input_text', ''),
                    placeholder="e.g., Why are my tomato leaves curling?",
                    label_visibility="collapsed",
                    key=f"{self.component_id}_chat_input"
                )
            
            with col2:
                send_clicked = st.form_submit_button(
                    "📤",
                    help="Send message",
                    use_container_width=True,
                    disabled=st.session_state.get('processing_message', False)
                )
        
        # Clear input text after form submission
        if send_clicked:
            st.session_state.chat_input_text = ""
        
        return user_input, send_clicked
    
    def render_chat_controls(self) -> bool:
        """Render chat control buttons.
        
        Returns:
            bool: True if clear was clicked
        """
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button(
                "🗑️ Clear Chat",
                key=f"{self.component_id}_clear_chat",
                use_container_width=True
            ):
                return True
        
        with col2:
            # Chat statistics
            message_count = len(st.session_state.get('chat_messages', []))
            st.metric("Messages", message_count)
        
        with col3:
            # Processing indicator
            if st.session_state.get('processing_message', False):
                st.markdown("🔄")
        
        return False
    
    def process_user_message(self, user_input: str) -> str:
        """Process user message and generate AI response.
        
        Args:
            user_input: User's message text
            
        Returns:
            str: AI-generated response
        """
        if not user_input.strip():
            return ""
        
        try:
            st.session_state.processing_message = True
            
            # Add user message to chat
            user_message = {
                'role': 'user',
                'content': user_input.strip(),
                'timestamp': time.time()
            }
            st.session_state.chat_messages.append(user_message)
            
            # Generate AI response
            with st.spinner("🤖 Thinking..."):
                if self.text_adapter:
                    response = self.text_adapter.generate_response(
                        disease_class="general",
                        user_query=user_input,
                        confidence=0.0
                    )
                else:
                    response = self._generate_fallback_response(user_input)
            
            # Add AI response to chat
            ai_message = {
                'role': 'assistant',
                'content': response,
                'timestamp': time.time()
            }
            st.session_state.chat_messages.append(ai_message)
            
            # Limit chat history size
            if len(st.session_state.chat_messages) > self.max_chat_history:
                st.session_state.chat_messages = st.session_state.chat_messages[-self.max_chat_history:]
            
            return response
            
        except Exception as e:
            error_response = f"I apologize, but I encountered an error: {e}"
            
            error_message = {
                'role': 'assistant',
                'content': error_response,
                'timestamp': time.time()
            }
            st.session_state.chat_messages.append(error_message)
            
            return error_response
        finally:
            st.session_state.processing_message = False
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """Generate fallback response when TextAdapter is not available."""
        # Simple keyword-based responses
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['yellow', 'yellowing']):
            return """Yellow leaves can indicate several issues:
            
🌱 **Common causes:**
• Overwatering or underwatering
• Nutrient deficiency (especially nitrogen)
• Natural aging of older leaves
• Insufficient light

💡 **Solutions:**
• Check soil moisture before watering
• Ensure proper drainage
• Consider fertilizing if needed
• Evaluate light conditions

If only older, lower leaves are yellowing, this is often normal!"""
        
        elif any(word in user_lower for word in ['water', 'watering']):
            return """Watering tips for healthy plants:
            
💧 **General guidelines:**
• Check soil moisture first - stick finger 1-2 inches deep
• Water when top inch of soil feels dry
• Water thoroughly until it drains from bottom
• Empty saucers after 30 minutes

🌿 **Factors affecting watering:**
• Plant type (succulents need less, ferns need more)
• Season (less in winter, more in growing season)
• Humidity and temperature
• Pot size and drainage

Most houseplants prefer "soak and dry" method!"""
        
        elif any(word in user_lower for word in ['brown', 'spots', 'disease']):
            return """Brown spots could indicate:
            
🍂 **Possible causes:**
• Fungal infections
• Bacterial spots
• Sunburn or heat damage
• Overwatering issues
• Nutrient problems

🔍 **What to do:**
• Remove affected leaves
• Improve air circulation
• Avoid getting leaves wet when watering
• Check for pests
• Consider fungicide if spreading

For accurate diagnosis, try uploading a photo for visual analysis!"""
        
        else:
            return f"""Thank you for your question about: "{user_input}"
            
🌱 I'd be happy to help with plant care advice! Here are some general tips:
            
• **Light**: Most houseplants prefer bright, indirect light
• **Water**: Check soil moisture before watering
• **Air**: Good circulation prevents many issues
• **Soil**: Use well-draining potting mix
• **Observation**: Monitor your plants regularly
            
For specific plant care advice, try asking about:
• Watering schedules
• Light requirements
• Common problems (yellowing, brown spots, etc.)
• Fertilizing tips
            
Or upload a photo for visual plant analysis!"""
    
    def clear_chat_history(self) -> None:
        """Clear all chat messages."""
        st.session_state.chat_messages = []
        st.session_state.processing_message = False
        
        # Add welcome message back
        welcome_message = {
            'role': 'assistant',
            'content': '🌱 Chat cleared! Feel free to ask me anything about plant care.',
            'timestamp': time.time()
        }
        st.session_state.chat_messages.append(welcome_message)
    
    def render(self, **kwargs) -> Dict[str, Any]:
        """Render the complete mobile chat interface.
        
        Returns:
            Dict containing chat session information
        """
        # Initialize components
        self.initialize_chat_components()
        
        # Main container
        st.markdown('<div class="mobile-chat-interface" data-component="mobile-chat-interface" data-testable="true">', 
                   unsafe_allow_html=True)
        
        # Check if TextAdapter is available
        if not st.session_state.get('text_adapter_loaded', False):
            st.warning("⚠️ Text processing not available. Using basic responses.")
        
        # Chat messages display
        self.render_chat_messages()
        
        # Quick suggestions
        if self.show_suggestions and len(st.session_state.get('chat_messages', [])) <= 1:
            selected_suggestion = self.render_quick_suggestions()
        
        # Chat input
        user_input, send_clicked = self.render_chat_input()
        
        # Process message if sent
        if send_clicked and user_input.strip():
            response = self.process_user_message(user_input)
            if response:
                st.rerun()  # Refresh to show new messages
        
        # Chat controls
        clear_clicked = self.render_chat_controls()
        
        if clear_clicked:
            self.clear_chat_history()
            st.rerun()
        
        # Usage tips
        with st.expander("💡 Chat Tips"):
            st.markdown("""
            **How to get the best answers:**
            
            ✅ **Be specific**: "Why are my tomato leaves yellowing?" vs "Plant problem"
            
            ✅ **Include details**: Mention plant type, symptoms, care routine
            
            ✅ **Ask follow-ups**: "What fertilizer should I use for this?"
            
            **Example good questions:**
            • "My fiddle leaf fig has brown spots on lower leaves"
            • "How often should I water my snake plant in winter?"
            • "What's the white powder on my plant leaves?"
            
            **For visual problems**: Try the Image Analysis tab for photo-based diagnosis!
            """)
        
        # Close container
        st.markdown('</div>', unsafe_allow_html=True)
        
        return {
            'message_count': len(st.session_state.get('chat_messages', [])),
            'text_adapter_loaded': st.session_state.get('text_adapter_loaded', False),
            'processing_message': st.session_state.get('processing_message', False),
            'last_message_time': st.session_state.get('chat_messages', [{}])[-1].get('timestamp') if st.session_state.get('chat_messages') else None
        }
    
    def get_chat_status(self) -> Dict[str, Any]:
        """Get current chat status for AI agent monitoring."""
        messages = st.session_state.get('chat_messages', [])
        
        return {
            'component_id': self.component_id,
            'text_adapter_loaded': st.session_state.get('text_adapter_loaded', False),
            'message_count': len(messages),
            'user_message_count': len([m for m in messages if m.get('role') == 'user']),
            'assistant_message_count': len([m for m in messages if m.get('role') == 'assistant']),
            'processing_message': st.session_state.get('processing_message', False),
            'last_activity': messages[-1].get('timestamp') if messages else None,
            'max_chat_history': self.max_chat_history,
            'show_suggestions': self.show_suggestions,
            'auto_scroll': self.auto_scroll
        }
    
    def export_chat_history(self) -> Dict[str, Any]:
        """Export chat history for analysis or backup."""
        return {
            'messages': st.session_state.get('chat_messages', []),
            'export_timestamp': time.time(),
            'component_id': self.component_id,
            'session_info': self.get_chat_status()
        }


# Utility functions
def create_mobile_chat_interface(max_chat_history: int = 50,
                                show_suggestions: bool = True,
                                auto_scroll: bool = True) -> MobileChatInterface:
    """Create and return a MobileChatInterface instance."""
    return MobileChatInterface(
        component_id="mobile_chat_interface",
        max_chat_history=max_chat_history,
        show_suggestions=show_suggestions,
        auto_scroll=auto_scroll
    )


def render_plant_care_chat() -> Dict[str, Any]:
    """Convenience function to render plant care chat interface."""
    chat_interface = create_mobile_chat_interface()
    return chat_interface.render()