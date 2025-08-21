"""Enhanced Chat Interface for PlantGuard.

This module provides a comprehensive chat interface with message history,
conversation management, and export functionality for the PlantGuard
multimodal plant disease detection system.
"""

import json
import logging
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


class ChatMessage:
    """Represents a single chat message with metadata."""

    def __init__(self, role: str, content: str, timestamp: datetime | None = None, metadata: dict | None = None):
        """Initialize a chat message.

        Args:
            role: The role of the message sender ("user" or "assistant")
            content: The content of the message
            timestamp: When the message was created (defaults to now)
            metadata: Additional metadata about the message
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMessage":
        """Create message from dictionary format."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


class ChatInterface:
    """Enhanced chat interface with message history and conversation management."""

    def __init__(self, session_key: str = "messages"):
        """Initialize chat interface.

        Args:
            session_key: Key for storing messages in session state
        """
        self.session_key = session_key
        self.max_message_length = 1000

        # Initialize session state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = []

    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Add a new message to the conversation.

        Args:
            role: The role of the message sender ("user" or "assistant")
            content: The content of the message
            metadata: Additional metadata about the message
        """
        try:
            message = ChatMessage(role, content, metadata=metadata)
            st.session_state[self.session_key].append(message.to_dict())
            logger.info(f"Added {role} message to conversation")
        except Exception as e:
            logger.warning(f"Failed to add message: {e}")
            st.toast("Failed to add message to conversation", icon="⚠️")

    def get_messages(self) -> list[dict[str, Any]]:
        """Get all messages in the conversation."""
        return st.session_state.get(self.session_key, [])

    def clear_conversation(self) -> None:
        """Clear all messages from the conversation."""
        try:
            st.session_state[self.session_key] = []
            logger.info("Conversation cleared")
            st.toast("Conversation cleared", icon="🧹")
        except Exception as e:
            logger.warning(f"Failed to clear conversation: {e}")
            st.toast("Failed to clear conversation", icon="⚠️")

    def render_chat_history(self) -> None:
        """Render the chat history using st.chat_message with scrollable container."""
        messages = self.get_messages()

        if not messages:
            st.info("💬 Start a conversation by typing a message below!")
            return

        # Create scrollable chat container
        chat_container_html = """
        <div style='
            max-height: 600px;
            overflow-y: auto;
            padding: 16px;
            border: 2px solid #E5E7EB;
            border-radius: 12px;
            background: #F9FAFB;
            margin-bottom: 16px;
            scroll-behavior: smooth;
        ' id='chat-history-container'>
        """
        st.markdown(chat_container_html, unsafe_allow_html=True)

        # Display messages within the scrollable container
        for i, message_data in enumerate(messages):
            try:
                message = ChatMessage.from_dict(message_data)

                with st.chat_message(message.role):
                    st.write(message.content)

                    # Show timestamp in expander
                    with st.expander("📅 Message Details", expanded=False):
                        st.caption(f"Time: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        if message.metadata:
                            st.caption(f"Metadata: {message.metadata}")

            except Exception as e:
                logger.warning(f"Failed to render message: {e}")
                st.error("Failed to display message")

        # Close chat container
        st.markdown("</div>", unsafe_allow_html=True)

        # Auto-scroll to bottom for new messages
        if messages:
            auto_scroll_js = """
            <script>
            setTimeout(function() {
                var container = document.getElementById('chat-history-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }, 100);
            </script>
            """
            st.markdown(auto_scroll_js, unsafe_allow_html=True)

    def validate_input(self, text: str) -> tuple[bool, str]:
        """Validate chat input text.

        Args:
            text: The input text to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Message cannot be empty"

        if len(text) > self.max_message_length:
            return False, f"Message too long (max {self.max_message_length} characters)"

        return True, ""

    def render_chat_input(self, placeholder: str = "Ask about plant diseases...") -> str | None:
        """Render chat input with validation.

        Args:
            placeholder: Placeholder text for the input

        Returns:
            User input if valid, None otherwise
        """
        chat_input = st.chat_input(placeholder, max_chars=self.max_message_length)

        if chat_input:
            is_valid, error_msg = self.validate_input(chat_input)
            if not is_valid:
                st.toast(error_msg, icon="⚠️")
                return None
            return chat_input.strip()

        return None

    def search_messages(self, query: str) -> list[dict[str, Any]]:
        """Search messages by content.

        Args:
            query: Search query

        Returns:
            List of matching messages
        """
        if not query:
            return self.get_messages()

        try:
            messages = self.get_messages()
            query_lower = query.lower()

            matching_messages = []
            for message_data in messages:
                if query_lower in message_data["content"].lower():
                    matching_messages.append(message_data)

            return matching_messages

        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return []

    def export_conversation_csv(self) -> str | None:
        """Export conversation to CSV format.

        Returns:
            CSV content as string or None if failed
        """
        try:
            messages = self.get_messages()
            if not messages:
                st.toast("No messages to export", icon="📝")
                return None

            # Create DataFrame
            data = []
            for message_data in messages:
                message = ChatMessage.from_dict(message_data)
                data.append(
                    {
                        "Role": message.role,
                        "Content": message.content,
                        "Timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "Metadata": json.dumps(message.metadata) if message.metadata else "",
                    }
                )

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)

            logger.info(f"Exported {len(messages)} messages to CSV")
            return csv_content

        except Exception as e:
            logger.warning(f"CSV export failed: {e}")
            st.toast("Failed to export conversation to CSV", icon="⚠️")
            return None

    def export_conversation_pdf(self) -> bytes | None:
        """Export conversation to PDF format.

        Returns:
            PDF content as bytes or None if failed
        """
        try:
            messages = self.get_messages()
            if not messages:
                st.toast("No messages to export", icon="📝")
                return None

            # Create PDF
            from io import BytesIO

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=16, spaceAfter=30, textColor=colors.darkgreen)

            story = []

            # Title
            story.append(Paragraph("🌿 PlantGuard Conversation Export", title_style))
            story.append(Paragraph(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
            story.append(Spacer(1, 20))

            # Messages
            for i, message_data in enumerate(messages, 1):
                message = ChatMessage.from_dict(message_data)

                # Role header
                role_color = colors.blue if message.role == "user" else colors.green
                role_style = ParagraphStyle(f"Role{i}", parent=styles["Heading3"], fontSize=12, textColor=role_color, spaceAfter=5)

                story.append(Paragraph(f"{message.role.title()}: {message.timestamp.strftime('%H:%M:%S')}", role_style))
                story.append(Paragraph(message.content, styles["Normal"]))
                story.append(Spacer(1, 15))

            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()

            logger.info(f"Exported {len(messages)} messages to PDF")
            return pdf_content

        except Exception as e:
            logger.warning(f"PDF export failed: {e}")
            st.toast("Failed to export conversation to PDF", icon="⚠️")
            return None

    def render_conversation_controls(self) -> None:
        """Render conversation management controls."""
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            if st.button("🧹 Clear Chat", help="Clear all messages"):
                self.clear_conversation()
                st.rerun()

        with col2:
            messages = self.get_messages()
            if messages:
                csv_content = self.export_conversation_csv()
                if csv_content:
                    st.download_button(
                        "📊 Export CSV",
                        data=csv_content,
                        file_name=f"plantguard_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        help="Export conversation to CSV",
                    )

        with col3:
            messages = self.get_messages()
            if messages:
                pdf_content = self.export_conversation_pdf()
                if pdf_content:
                    st.download_button(
                        "📄 Export PDF",
                        data=pdf_content,
                        file_name=f"plantguard_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        help="Export conversation to PDF",
                    )

        with col4:
            message_count = len(self.get_messages())
            st.metric("Messages", message_count)

    def render_search_interface(self) -> None:
        """Render conversation search interface."""
        st.subheader("🔍 Search Conversation")

        search_query = st.text_input("Search messages:", placeholder="Enter search terms...", help="Search through conversation history")

        if search_query:
            matching_messages = self.search_messages(search_query)

            if matching_messages:
                st.success(f"Found {len(matching_messages)} matching messages:")

                for message_data in matching_messages:
                    try:
                        message = ChatMessage.from_dict(message_data)

                        with st.expander(f"{message.role.title()} - {message.timestamp.strftime('%H:%M:%S')}", expanded=False):
                            st.write(message.content)

                    except Exception as e:
                        logger.warning(f"Failed to display search result: {e}")
                        st.error("Failed to display message")
            else:
                st.info("No messages found matching your search.")

    def render_complete_interface(self, show_search: bool = True, show_controls: bool = True) -> str | None:
        """Render the complete chat interface.

        Args:
            show_search: Whether to show search interface
            show_controls: Whether to show conversation controls

        Returns:
            User input if provided, None otherwise
        """
        # Chat history
        self.render_chat_history()

        # Conversation controls
        if show_controls:
            st.markdown("---")
            self.render_conversation_controls()

        # Search interface (in sidebar or collapsible section)
        if show_search and self.get_messages():
            with st.expander("🔍 Search & Manage", expanded=False):
                self.render_search_interface()

        # Chat input
        st.markdown("---")
        return self.render_chat_input()


def create_chat_interface(session_key: str = "messages") -> ChatInterface:
    """Create and return a ChatInterface instance.

    Args:
        session_key: Key for storing messages in session state

    Returns:
        ChatInterface instance
    """
    return ChatInterface(session_key)


# Example usage and testing
if __name__ == "__main__":
    # Test the chat interface
    st.title("🌿 PlantGuard Chat Interface Test")

    # Create chat interface
    chat = create_chat_interface()

    # Render interface
    user_input = chat.render_complete_interface()

    # Handle user input
    if user_input:
        # Add user message
        chat.add_message("user", user_input)

        # Add assistant response (placeholder)
        response = f"Thank you for your message: '{user_input}'. This is a test response from the PlantGuard assistant."
        chat.add_message("assistant", response, metadata={"type": "test_response"})

        # Rerun to show new messages
        st.rerun()
