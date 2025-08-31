"""
Mobile Chat Interface Component for PlantGuard UI.

This module provides a mobile-optimized chat interface component with
message bubbles, scrollable history, typing indicators, and touch optimization.
"""

import logging
from datetime import datetime
from typing import Any

import streamlit as st

from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileChatInterface(MobileBaseComponent):
    """Mobile-optimized chat interface component with conversational interaction."""

    def __init__(self, component_id: str, title: str = "Plant Care Assistant", **kwargs) -> None:
        """
        Initialize mobile chat interface component.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Chat configuration
        self.chat_config = {
            "max_message_length": 1000,
            "max_history_length": 50,
            "show_typing_indicator": True,
            "enable_voice_input": True,
            "enable_image_context": True,
            "auto_scroll": True,
            "message_timestamp": True,
            "user_avatar": "[PERSON]‍[GRAIN]",
            "bot_avatar": "[LEAF]",
        }

        # Initialize chat state
        self._initialize_chat_state()

        logger.debug("MobileChatInterface initialized: %s", component_id)

    def _initialize_chat_state(self) -> None:
        """Initialize chat-specific state."""
        chat_state = {
            "messages": [],
            "current_input": "",
            "is_typing": False,
            "typing_start_time": None,
            "last_message_time": None,
            "chat_session_id": f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "context": {"current_plant": None, "current_disease": None, "analysis_results": []},
        }

        current_state = self.get_state()
        if "chat_data" not in current_state["data"]:
            current_state["data"]["chat_data"] = chat_state
            self.set_state(current_state)

            # Add welcome message
            self._add_welcome_message()

    def render(self) -> None:
        """Render the mobile chat interface."""
        try:
            # Get current state
            state = self.get_state()
            chat_data = state["data"].get("chat_data", {})

            # Render chat interface container
            st.markdown(
                f"""
                <div class="mobile-chat-interface mobile-component" 
                     data-component-id="{self.component_id}"
                     data-testid="chat-interface-{self.component_id}">
                """,
                unsafe_allow_html=True,
            )

            # Update context with current analysis
            self._update_chat_context()

            # Render chat header
            self._render_chat_header()

            # Render chat messages
            self._render_chat_messages(chat_data.get("messages", []))

            # Render typing indicator
            if chat_data.get("is_typing", False):
                self._render_typing_indicator()

            # Render chat input
            self._render_chat_input()

            # Render chat controls
            self._render_chat_controls()

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Chat interface rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)

    def _add_welcome_message(self) -> None:
        """Add welcome message to chat."""
        welcome_message = {
            "id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_welcome",
            "type": "bot",
            "content": "[LEAF] Hello! I'm your PlantGuard assistant. I can help you with plant care questions, disease identification, and treatment advice. How can I help you today?",
            "timestamp": datetime.now().isoformat(),
            "context": None,
        }

        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        chat_data["messages"].append(welcome_message)
        state["data"]["chat_data"] = chat_data
        self.set_state(state)

    def _update_chat_context(self) -> None:
        """Update chat context with current analysis results."""
        # Get current analysis results
        analysis_results = []
        if "analysis_results" in st.session_state and st.session_state.analysis_results:
            analysis_results = st.session_state.analysis_results[-3:]  # Last 3 results

        # Update context
        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        chat_data["context"]["analysis_results"] = analysis_results

        # Set current disease if available
        if analysis_results:
            latest_result = analysis_results[0]
            disease_name, confidence = latest_result.get("prediction", ("Unknown", 0.0))
            chat_data["context"]["current_disease"] = {"name": disease_name, "confidence": confidence, "timestamp": latest_result.get("timestamp")}

        state["data"]["chat_data"] = chat_data
        self.set_state(state)

    def _render_chat_header(self) -> None:
        """Render chat header with title and status."""
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"### {self.chat_config['bot_avatar']} {self.title}")

        with col2:
            # Context indicator
            state = self.get_state()
            chat_data = state["data"]["chat_data"]
            current_disease = chat_data["context"].get("current_disease")

            if current_disease:
                st.markdown(f"<small>[MICROSCOPE] Context: {current_disease['name']}</small>", unsafe_allow_html=True)

        with col3:
            # Chat controls
            if st.button("[CLEAN]", key=f"{self.component_id}_clear", help="Clear chat"):
                self._clear_chat()

    def _render_chat_messages(self, messages: list[dict[str, Any]]) -> None:
        """Render chat messages with mobile-optimized bubbles."""
        if not messages:
            st.info("[CHAT] Start a conversation by typing a message below!")
            return

        # Create scrollable container for messages
        st.markdown(
            """
        <div class="mobile-chat-messages" style="
            max-height: 400px; 
            overflow-y: auto; 
            padding: 10px; 
            border: 1px solid #e0e0e0; 
            border-radius: 10px;
            margin-bottom: 10px;
        ">
        """,
            unsafe_allow_html=True,
        )

        # Render messages
        for message in messages[-20:]:  # Show last 20 messages
            self._render_message_bubble(message)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_message_bubble(self, message: dict[str, Any]) -> None:
        """Render individual message bubble."""
        message_type = message.get("type", "user")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")

        # Format timestamp
        formatted_time = self._format_message_timestamp(timestamp)

        if message_type == "user":
            # User message (right-aligned)
            st.markdown(
                f"""
            <div class="mobile-message mobile-message-user">
                <div class="message-content user-message">
                    <div class="message-avatar">{self.chat_config["user_avatar"]}</div>
                    <div class="message-bubble user-bubble">
                        <p>{content}</p>
                        <small class="message-time">{formatted_time}</small>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            # Bot message (left-aligned)
            st.markdown(
                f"""
            <div class="mobile-message mobile-message-bot">
                <div class="message-content bot-message">
                    <div class="message-avatar">{self.chat_config["bot_avatar"]}</div>
                    <div class="message-bubble bot-bubble">
                        <p>{content}</p>
                        <small class="message-time">{formatted_time}</small>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def _render_typing_indicator(self) -> None:
        """Render typing indicator when bot is responding."""
        st.markdown(
            """
        <div class="mobile-typing-indicator">
            <div class="message-content bot-message">
                <div class="message-avatar">[LEAF]</div>
                <div class="message-bubble bot-bubble typing">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <small>PlantGuard is typing...</small>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_chat_input(self) -> None:
        """Render chat input with send button."""
        st.markdown("### [CHAT] Ask a Question")

        # Input area
        col1, col2 = st.columns([4, 1])

        with col1:
            user_input = st.text_area(
                "Type your plant care question...",
                key=f"{self.component_id}_input",
                height=80,
                max_chars=self.chat_config["max_message_length"],
                placeholder="Ask about plant diseases, care tips, treatments, or anything plant-related!",
                label_visibility="collapsed",
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing

            send_button = st.button(
                "[UPLOAD]\nSend", key=f"{self.component_id}_send", use_container_width=True, type="primary", disabled=not user_input.strip()
            )

            # Voice input button (if enabled)
            if self.chat_config["enable_voice_input"]:
                voice_button = st.button("[VOICE]\nVoice", key=f"{self.component_id}_voice", use_container_width=True, help="Use voice input")

                if voice_button:
                    self._handle_voice_input()

        # Handle send button
        if send_button and user_input.strip():
            self._handle_user_message(user_input.strip())

        # Quick action buttons
        self._render_quick_actions()

    def _render_quick_actions(self) -> None:
        """Render quick action buttons for common questions."""
        st.markdown("**Quick Questions:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("[PLANT] Plant Care", key=f"{self.component_id}_quick_care", use_container_width=True):
                self._handle_user_message("How do I take care of my plant?")

        with col2:
            if st.button("[SEARCH] Symptoms", key=f"{self.component_id}_quick_symptoms", use_container_width=True):
                self._handle_user_message("What do these symptoms mean?")

        with col3:
            if st.button("[TREATMENT] Treatment", key=f"{self.component_id}_quick_treatment", use_container_width=True):
                self._handle_user_message("How should I treat this disease?")

    def _render_chat_controls(self) -> None:
        """Render chat control buttons."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("[DETAILS] History", key=f"{self.component_id}_history", use_container_width=True):
                self._show_chat_history()

        with col2:
            if st.button("[UPLOAD] Export", key=f"{self.component_id}_export", use_container_width=True):
                self._export_chat()

        with col3:
            if st.button("[SETTINGS] Settings", key=f"{self.component_id}_settings", use_container_width=True):
                self._show_chat_settings()

        with col4:
            if st.button("[UNKNOWN] Help", key=f"{self.component_id}_help", use_container_width=True):
                self._show_chat_help()

    def _handle_user_message(self, message: str) -> None:
        """Handle user message and generate bot response."""
        try:
            # Add user message
            user_msg = {
                "id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_user",
                "type": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "context": self._get_current_context(),
            }

            self._add_message(user_msg)

            # Show typing indicator
            self._set_typing(True)

            # Generate bot response
            bot_response = self._generate_bot_response(message)

            # Add bot message
            bot_msg = {
                "id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_bot",
                "type": "bot",
                "content": bot_response,
                "timestamp": datetime.now().isoformat(),
                "context": self._get_current_context(),
            }

            self._add_message(bot_msg)

            # Hide typing indicator
            self._set_typing(False)

            # Clear input
            st.session_state[f"{self.component_id}_input"] = ""

        except Exception as e:
            logger.error("Failed to handle user message: %s", e)
            self._set_typing(False)
            self._add_error_message("Sorry, I encountered an error. Please try again.")

    def _generate_bot_response(self, user_message: str) -> str:
        """Generate bot response using text adapter and context."""
        try:
            # Get current context
            context = self._get_current_context()

            # Import text adapter
            from src.core.nlp import ChatModel, TextAdapter

            # Get or create adapters
            if "text_adapter" not in st.session_state:
                st.session_state.text_adapter = TextAdapter()

            if "chat_model" not in st.session_state:
                st.session_state.chat_model = ChatModel()

            text_adapter = st.session_state.text_adapter
            chat_model = st.session_state.chat_model

            # Prepare context-aware input
            context_prompt = self._build_context_prompt(user_message, context)

            # Generate response
            response = chat_model.predict(context_prompt)

            return response

        except Exception as e:
            logger.error("Bot response generation failed: %s", e)
            return self._get_fallback_response(user_message)

    def _build_context_prompt(self, user_message: str, context: dict[str, Any]) -> str:
        """Build context-aware prompt for the chat model."""
        prompt_parts = []

        # Add system context
        prompt_parts.append("You are PlantGuard, an AI plant care assistant.")

        # Add current disease context if available
        current_disease = context.get("current_disease")
        if current_disease:
            prompt_parts.append(f"Current diagnosis: {current_disease['name']} (confidence: {current_disease['confidence']:.1%})")

        # Add recent analysis results
        analysis_results = context.get("analysis_results", [])
        if analysis_results:
            prompt_parts.append("Recent analysis results:")
            for result in analysis_results[-2:]:  # Last 2 results
                disease_name, confidence = result.get("prediction", ("Unknown", 0.0))
                prompt_parts.append(f"- {disease_name} ({confidence:.1%})")

        # Add user message
        prompt_parts.append(f"User question: {user_message}")

        # Add response guidelines
        prompt_parts.append("Provide helpful, accurate plant care advice. Keep responses concise and mobile-friendly.")

        return "\n".join(prompt_parts)

    def _get_fallback_response(self, user_message: str) -> str:
        """Get fallback response when AI generation fails."""
        # Simple keyword-based responses
        message_lower = user_message.lower()

        if any(word in message_lower for word in ["water", "watering"]):
            return "[WATER] For watering, check the soil moisture first. Most plants prefer soil that's slightly moist but not waterlogged. Water when the top inch of soil feels dry."

        elif any(word in message_lower for word in ["light", "sun", "sunlight"]):
            return "☀️ Most plants need bright, indirect light. Direct sunlight can burn leaves, while too little light causes weak growth. Adjust placement based on your plant's needs."

        elif any(word in message_lower for word in ["disease", "sick", "problem"]):
            return "[SEARCH] If your plant looks sick, first check for common issues: overwatering, pests, or inadequate light. Take a clear photo and use PlantGuard's analysis feature for specific diagnosis."

        elif any(word in message_lower for word in ["fertilizer", "feed", "nutrients"]):
            return "[PLANT] Feed your plants during growing season (spring/summer) with balanced fertilizer. Follow package instructions and don't over-fertilize, which can harm plants."

        else:
            return "[LEAF] I'm here to help with plant care! You can ask about watering, lighting, diseases, fertilizing, or any other plant-related questions. Feel free to be specific about your plant and its symptoms."

    def _get_current_context(self) -> dict[str, Any]:
        """Get current chat context."""
        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        return chat_data.get("context", {})

    def _add_message(self, message: dict[str, Any]) -> None:
        """Add message to chat history."""
        state = self.get_state()
        chat_data = state["data"]["chat_data"]

        # Add message
        chat_data["messages"].append(message)

        # Limit history length
        if len(chat_data["messages"]) > self.chat_config["max_history_length"]:
            chat_data["messages"] = chat_data["messages"][-self.chat_config["max_history_length"] :]

        # Update last message time
        chat_data["last_message_time"] = datetime.now().isoformat()

        # Save state
        state["data"]["chat_data"] = chat_data
        self.set_state(state)

    def _add_error_message(self, error_text: str) -> None:
        """Add error message to chat."""
        error_msg = {
            "id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_error",
            "type": "bot",
            "content": f"[TODO] {error_text}",
            "timestamp": datetime.now().isoformat(),
            "context": None,
        }
        self._add_message(error_msg)

    def _set_typing(self, is_typing: bool) -> None:
        """Set typing indicator state."""
        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        chat_data["is_typing"] = is_typing

        if is_typing:
            chat_data["typing_start_time"] = datetime.now().isoformat()
        else:
            chat_data["typing_start_time"] = None

        state["data"]["chat_data"] = chat_data
        self.set_state(state)

    def _format_message_timestamp(self, timestamp: str) -> str:
        """Format message timestamp for display."""
        try:
            if not timestamp:
                return ""

            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%H:%M")

        except Exception:
            return ""

    def _handle_voice_input(self) -> None:
        """Handle voice input (placeholder for future implementation)."""
        st.info("[VOICE] Voice input feature coming soon! For now, please type your question.")

    def _clear_chat(self) -> None:
        """Clear chat history."""
        # Force reinitialize chat state
        chat_state = {
            "messages": [],
            "current_input": "",
            "is_typing": False,
            "typing_start_time": None,
            "last_message_time": None,
            "chat_session_id": f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "context": {"current_plant": None, "current_disease": None, "analysis_results": []},
        }

        current_state = self.get_state()
        current_state["data"]["chat_data"] = chat_state
        self.set_state(current_state)

        # Add welcome message
        self._add_welcome_message()
        st.success("[CLEAN] Chat cleared!")

    def _show_chat_history(self) -> None:
        """Show chat history in expandable section."""
        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        messages = chat_data.get("messages", [])

        with st.expander("[DETAILS] Chat History", expanded=True):
            if not messages:
                st.info("No chat history available.")
            else:
                st.write(f"**Total messages:** {len(messages)}")
                st.write(f"**Session ID:** {chat_data.get('chat_session_id', 'Unknown')}")

                for i, msg in enumerate(messages[-10:], 1):  # Last 10 messages
                    msg_type = "You" if msg["type"] == "user" else "PlantGuard"
                    timestamp = self._format_message_timestamp(msg["timestamp"])
                    st.write(f"**{i}. {msg_type}** ({timestamp}): {msg['content'][:100]}...")

    def _export_chat(self) -> None:
        """Export chat history."""
        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        messages = chat_data.get("messages", [])

        if not messages:
            st.warning("No chat history to export.")
            return

        # Create export text
        export_text = f"PlantGuard Chat Export\nSession: {chat_data.get('chat_session_id', 'Unknown')}\nExported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        for msg in messages:
            sender = "You" if msg["type"] == "user" else "PlantGuard"
            timestamp = self._format_message_timestamp(msg["timestamp"])
            export_text += f"[{timestamp}] {sender}: {msg['content']}\n\n"

        st.text_area("[UPLOAD] Chat Export", value=export_text, height=200, key=f"{self.component_id}_export_text")

        st.success("[DONE] Chat history ready to export! Copy the text above.")

    def _show_chat_settings(self) -> None:
        """Show chat settings."""
        with st.expander("[SETTINGS] Chat Settings", expanded=True):
            st.write("**Current Settings:**")
            st.write(f"- Max message length: {self.chat_config['max_message_length']} characters")
            st.write(f"- Max history: {self.chat_config['max_history_length']} messages")
            st.write(f"- Voice input: {'Enabled' if self.chat_config['enable_voice_input'] else 'Disabled'}")
            st.write(f"- Image context: {'Enabled' if self.chat_config['enable_image_context'] else 'Disabled'}")

    def _show_chat_help(self) -> None:
        """Show chat help information."""
        with st.expander("[UNKNOWN] Chat Help", expanded=True):
            st.markdown("""
            **How to use PlantGuard Chat:**
            
            [LEAF] **Ask Questions:** Type any plant care question
            [CAMERA] **Use Context:** Chat knows about your recent plant analysis
            [VOICE] **Voice Input:** Use the voice button (coming soon)
            [DETAILS] **Quick Actions:** Use preset question buttons
            
            **Example Questions:**
            - "How often should I water my plant?"
            - "What does this disease mean?"
            - "How do I treat leaf spots?"
            - "Is my plant getting enough light?"
            
            **Tips:**
            - Be specific about your plant type and symptoms
            - Mention recent analysis results for better context
            - Ask follow-up questions for more details
            """)

    def get_message_count(self) -> int:
        """Get number of messages in chat."""
        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        return len(chat_data.get("messages", []))

    def get_last_message(self) -> dict[str, Any] | None:
        """Get the last message in chat."""
        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        messages = chat_data.get("messages", [])
        return messages[-1] if messages else None

    def is_typing(self) -> bool:
        """Check if bot is currently typing."""
        state = self.get_state()
        chat_data = state["data"]["chat_data"]
        return chat_data.get("is_typing", False)
