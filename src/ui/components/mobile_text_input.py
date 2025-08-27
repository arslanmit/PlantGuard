"""
Mobile Text Input Component for PlantGuard UI.

This module provides a mobile-optimized text input component with
virtual keyboard support and chat interface functionality.
"""

import logging
from datetime import datetime
from typing import Any

import streamlit as st

from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileTextInput(MobileBaseComponent):
    """Mobile-optimized text input component with chat interface."""

    def __init__(self, component_id: str, title: str = "Text Input", **kwargs):
        """
        Initialize mobile text input component.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Text input configuration
        self.text_config = {
            "max_length": 1000,
            "min_length": 1,
            "placeholder": "Ask about plant care, diseases, or treatments...",
            "auto_resize": True,
            "enable_suggestions": True,
            "character_limit_warning": 900,
        }

        # Common plant care questions for suggestions
        self.suggestion_categories = {
            "Disease Identification": [
                "What disease does my plant have?",
                "Why are my plant leaves turning yellow?",
                "What are these spots on my plant?",
                "Is my plant infected with something?",
            ],
            "Plant Care": [
                "How often should I water my plant?",
                "What fertilizer should I use?",
                "How much sunlight does my plant need?",
                "When should I repot my plant?",
            ],
            "Treatment": [
                "How do I treat plant fungus?",
                "What pesticide is safe for my plant?",
                "How do I prevent plant diseases?",
                "Can I use home remedies for plant care?",
            ],
        }

        # Initialize text input state
        self._initialize_text_state()

        logger.debug("MobileTextInput initialized: %s", component_id)

    def _initialize_text_state(self) -> None:
        """Initialize text input-specific state."""
        text_state = {
            "current_text": "",
            "text_history": [],
            "suggestions_visible": False,
            "selected_category": None,
            "character_count": 0,
            "validation_status": "valid",
            "last_submission": None,
            "auto_complete_enabled": True,
        }

        current_state = self.get_state()
        if "text_data" not in current_state["data"]:
            current_state["data"]["text_data"] = text_state
            self.set_state(current_state)

    def render(self) -> None:
        """Render the mobile text input interface."""
        try:
            # Get current state
            state = self.get_state()
            text_data = state["data"].get("text_data", {})

            # Render text input container
            st.markdown(
                f"""
                <div class="mobile-text-input mobile-component" 
                     data-component-id="{self.component_id}"
                     data-testid="text-input-{self.component_id}">
                """,
                unsafe_allow_html=True,
            )

            # Main text input interface
            self._render_text_input_interface(text_data)

            # Show suggestions if enabled
            if text_data.get("suggestions_visible", False):
                self._render_suggestions()

            # Show text history if available
            if text_data.get("text_history"):
                self._render_text_history(text_data["text_history"])

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Text input rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)

    def _render_text_input_interface(self, text_data: dict[str, Any]) -> None:
        """Render the main text input interface."""
        # Text input area with mobile optimization
        current_text = st.text_area(
            "💬 Ask your plant care question",
            value=text_data.get("current_text", ""),
            height=120,
            max_chars=self.text_config["max_length"],
            placeholder=self.text_config["placeholder"],
            key=f"{self.component_id}_text_input",
            help="Type your question about plant care, diseases, or treatments",
        )

        # Update current text in state
        if current_text != text_data.get("current_text", ""):
            self._update_current_text(current_text)
            text_data["current_text"] = current_text

        # Character count and validation
        char_count = len(current_text)
        char_limit = self.text_config["max_length"]

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Character count display
            if char_count > self.text_config["character_limit_warning"]:
                st.warning(f"⚠️ {char_count}/{char_limit} characters")
            else:
                st.info(f"📝 {char_count}/{char_limit} characters")

        with col2:
            # Suggestions toggle
            if st.button("💡 Suggestions", key=f"{self.component_id}_suggestions_toggle"):
                self._toggle_suggestions()

        with col3:
            # Clear text button
            if st.button("🧹 Clear", key=f"{self.component_id}_clear_text"):
                self._clear_current_text()

        # Send button and quick actions
        col1, col2 = st.columns([3, 1])

        with col1:
            send_clicked = st.button(
                "📤 Send Message",
                key=f"{self.component_id}_send_btn",
                help="Send your question",
                use_container_width=True,
                type="primary",
                disabled=not self._is_text_valid(current_text),
            )

        with col2:
            # Settings button
            if st.button("⚙️", key=f"{self.component_id}_text_settings", help="Text settings"):
                self._toggle_text_settings()

        # Handle send button click
        if send_clicked and self._is_text_valid(current_text):
            self._handle_text_submission(current_text)

        # Render text settings if expanded
        if text_data.get("settings_expanded", False):
            self._render_text_settings()

        # Input validation feedback
        validation_status = self._validate_text_input(current_text)
        if validation_status["warnings"]:
            for warning in validation_status["warnings"]:
                st.warning(f"⚠️ {warning}")

        if validation_status["errors"]:
            for error in validation_status["errors"]:
                st.error(f"❌ {error}")

    def _render_suggestions(self) -> None:
        """Render text input suggestions."""
        st.markdown("### 💡 Suggested Questions")

        # Category tabs
        categories = list(self.suggestion_categories.keys())
        selected_tab = st.selectbox("Category", options=categories, key=f"{self.component_id}_suggestion_category")

        if selected_tab:
            suggestions = self.suggestion_categories[selected_tab]

            # Display suggestions as clickable buttons
            for i, suggestion in enumerate(suggestions):
                if st.button(suggestion, key=f"{self.component_id}_suggestion_{i}", help="Click to use this suggestion"):
                    self._use_suggestion(suggestion)

        # Quick action buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("❌ Hide Suggestions", key=f"{self.component_id}_hide_suggestions"):
                self._toggle_suggestions()

        with col2:
            if st.button("🔄 More Ideas", key=f"{self.component_id}_more_suggestions"):
                self._generate_more_suggestions()

    def _render_text_history(self, text_history: list[dict[str, Any]]) -> None:
        """Render recent text input history."""
        st.markdown("### 📝 Recent Questions")

        # Show last 3 questions
        recent_history = text_history[-3:] if len(text_history) > 3 else text_history

        for i, entry in enumerate(reversed(recent_history)):
            with st.expander(f"💬 {entry['text'][:50]}...", expanded=(i == 0)):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Question:** {entry['text']}")
                    st.write(f"**Asked:** {entry['timestamp'][:19]}")

                    if entry.get("response"):
                        st.write(f"**Response:** {entry['response'][:100]}...")

                with col2:
                    # Action buttons
                    if st.button("🔄 Ask Again", key=f"{self.component_id}_reask_{i}"):
                        self._reuse_text(entry["text"])

                    if st.button("❌ Remove", key=f"{self.component_id}_remove_{i}"):
                        self._remove_from_history(entry["text"])

    def _render_text_settings(self) -> None:
        """Render text input settings panel."""
        with st.expander("💬 Text Settings", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                # Auto-complete settings
                auto_complete = st.checkbox("Enable Auto-complete", value=True, key=f"{self.component_id}_auto_complete")

                # Suggestions settings
                show_suggestions = st.checkbox("Show Suggestions", value=True, key=f"{self.component_id}_show_suggestions")

            with col2:
                # Character limit settings
                char_limit = st.slider(
                    "Character Limit", min_value=100, max_value=2000, value=self.text_config["max_length"], key=f"{self.component_id}_char_limit"
                )

                self.text_config["max_length"] = char_limit

                # Warning threshold
                warning_threshold = st.slider(
                    "Warning Threshold",
                    min_value=50,
                    max_value=char_limit - 50,
                    value=self.text_config["character_limit_warning"],
                    key=f"{self.component_id}_warning_threshold",
                )

                self.text_config["character_limit_warning"] = warning_threshold

    def _update_current_text(self, text: str) -> None:
        """Update current text in state."""
        state = self.get_state()
        text_data = state["data"]["text_data"]
        text_data["current_text"] = text
        text_data["character_count"] = len(text)
        state["data"]["text_data"] = text_data
        self.set_state(state)

    def _is_text_valid(self, text: str) -> bool:
        """Check if text input is valid for submission."""
        if not text or not text.strip():
            return False

        if len(text) < self.text_config["min_length"]:
            return False

        return not len(text) > self.text_config["max_length"]

    def _validate_text_input(self, text: str) -> dict[str, Any]:
        """Validate text input and return validation results."""
        validation_result = {"is_valid": True, "errors": [], "warnings": []}

        # Check length
        if len(text) > self.text_config["max_length"]:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Text too long (max {self.text_config['max_length']} characters)")

        if text and len(text) < self.text_config["min_length"]:
            validation_result["warnings"].append("Text is very short")

        # Check for character limit warning
        if len(text) > self.text_config["character_limit_warning"]:
            validation_result["warnings"].append("Approaching character limit")

        # Check for common issues
        if text and text.isupper():
            validation_result["warnings"].append("Consider using normal capitalization")

        if text and len(text.split()) < 3:
            validation_result["warnings"].append("Consider providing more detail for better assistance")

        return validation_result

    def _handle_text_submission(self, text: str) -> None:
        """Handle text submission and processing."""
        try:
            if not self._is_text_valid(text):
                st.error("❌ Please enter a valid question")
                return

            # Add to text history
            self._add_to_history(text)

            # Add to global chat history
            self._add_to_chat_history(text)

            # Process the text
            self._process_text_input(text)

            # Clear current text
            self._clear_current_text()

            st.success("📤 Question sent successfully!")

        except Exception as e:
            logger.error("Text submission failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)

    def _add_to_history(self, text: str) -> None:
        """Add text to input history."""
        state = self.get_state()
        text_data = state["data"]["text_data"]

        if "text_history" not in text_data:
            text_data["text_history"] = []

        # Create history entry
        history_entry = {"text": text, "timestamp": datetime.now().isoformat(), "component_id": self.component_id, "response": None}

        text_data["text_history"].append(history_entry)
        text_data["last_submission"] = history_entry

        # Keep only recent history (limit memory usage)
        if len(text_data["text_history"]) > 20:
            text_data["text_history"] = text_data["text_history"][-20:]

        # Update state
        state["data"]["text_data"] = text_data
        self.set_state(state)

    def _add_to_chat_history(self, text: str) -> None:
        """Add text to global chat history."""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Add user message
        user_message = {"role": "user", "content": text, "timestamp": datetime.now().isoformat(), "source": "text", "component_id": self.component_id}

        st.session_state.chat_history.append(user_message)

    def _process_text_input(self, text: str) -> None:
        """Process text input using mobile integration layer."""
        try:
            # Import mobile integration
            from .mobile_adapter_integration import mobile_integration

            # Get recent analysis context if available
            recent_analysis = mobile_integration.get_recent_analysis(limit=1)
            context = {"recent_analysis": recent_analysis[0]} if recent_analysis else None

            # Process text and generate response
            with st.spinner("🤖 Processing your question..."):
                processing_result = mobile_integration.process_text_query(text=text, source="text", component_id=self.component_id, context=context)

                # Extract response
                response = processing_result.get("response", "")

                # Check for errors
                if "error" in processing_result:
                    logger.error("Text processing error: %s", processing_result["error"])
                    st.warning("⚠️ Response generation had issues, but here's what I can tell you:")

                # Update history entry with response
                if response:
                    self._update_history_with_response(text, response)

                    # Display response in an expandable section
                    with st.expander("🤖 AI Response", expanded=True):
                        st.write(response)

                        # Show context if available
                        disease_context = processing_result.get("disease_context")
                        confidence_context = processing_result.get("confidence_context", 0.0)

                        if disease_context and confidence_context > 0:
                            st.info(f"💡 This response is based on your recent analysis: {disease_context} ({confidence_context:.1%} confidence)")

                    st.success("🤖 Response generated!")
                else:
                    st.warning("⚠️ No response generated. Please try rephrasing your question.")

        except Exception as e:
            logger.error("Text processing failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)
            st.error("❌ Failed to process your question. Please try again.")

    def _update_history_with_response(self, text: str, response: str) -> None:
        """Update history entry with generated response."""
        state = self.get_state()
        text_data = state["data"]["text_data"]

        # Find and update the matching history entry
        for entry in reversed(text_data.get("text_history", [])):
            if entry["text"] == text and entry.get("response") is None:
                entry["response"] = response
                break

        # Update state
        state["data"]["text_data"] = text_data
        self.set_state(state)

    def _use_suggestion(self, suggestion: str) -> None:
        """Use a suggestion as current text."""
        state = self.get_state()
        text_data = state["data"]["text_data"]
        text_data["current_text"] = suggestion
        state["data"]["text_data"] = text_data
        self.set_state(state)

        # Hide suggestions
        self._toggle_suggestions()

        st.success(f"💡 Using suggestion: {suggestion[:50]}...")

    def _reuse_text(self, text: str) -> None:
        """Reuse text from history."""
        state = self.get_state()
        text_data = state["data"]["text_data"]
        text_data["current_text"] = text
        state["data"]["text_data"] = text_data
        self.set_state(state)

        st.success("🔄 Text restored from history")

    def _remove_from_history(self, text: str) -> None:
        """Remove entry from text history."""
        state = self.get_state()
        text_data = state["data"]["text_data"]

        # Remove matching entries
        text_data["text_history"] = [entry for entry in text_data.get("text_history", []) if entry["text"] != text]

        # Update state
        state["data"]["text_data"] = text_data
        self.set_state(state)

        st.success("🗑️ Removed from history")

    def _clear_current_text(self) -> None:
        """Clear current text input."""
        state = self.get_state()
        text_data = state["data"]["text_data"]
        text_data["current_text"] = ""
        text_data["character_count"] = 0
        state["data"]["text_data"] = text_data
        self.set_state(state)

    def _toggle_suggestions(self) -> None:
        """Toggle suggestions visibility."""
        state = self.get_state()
        text_data = state["data"]["text_data"]
        text_data["suggestions_visible"] = not text_data.get("suggestions_visible", False)
        state["data"]["text_data"] = text_data
        self.set_state(state)

    def _toggle_text_settings(self) -> None:
        """Toggle text settings panel."""
        state = self.get_state()
        text_data = state["data"]["text_data"]
        text_data["settings_expanded"] = not text_data.get("settings_expanded", False)
        state["data"]["text_data"] = text_data
        self.set_state(state)

    def _generate_more_suggestions(self) -> None:
        """Generate additional suggestions (placeholder for future enhancement)."""
        st.info("💡 More suggestions feature coming soon!")

    def get_current_text(self) -> str:
        """Get current text input."""
        state = self.get_state()
        text_data = state["data"].get("text_data", {})
        return text_data.get("current_text", "")

    def get_text_history(self) -> list[dict[str, Any]]:
        """Get text input history."""
        state = self.get_state()
        text_data = state["data"].get("text_data", {})
        return text_data.get("text_history", [])

    def clear_text_state(self) -> None:
        """Clear all text input state."""
        self._initialize_text_state()
        st.success("🧹 Text input state cleared")
