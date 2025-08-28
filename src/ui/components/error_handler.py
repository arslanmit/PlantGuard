"""Error Handler Component for PlantGuard Redesigned UI.

Provides comprehensive error handling with user-friendly messages,
recovery options, and graceful degradation.
"""

import logging
import traceback
from datetime import datetime
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Comprehensive error handling for PlantGuard UI."""

    def __init__(self):
        self.error_types = {
            "model_error": {"icon": "🤖", "title": "Model Error", "color": "#EF4444"},
            "input_error": {"icon": "📝", "title": "Input Error", "color": "#F59E0B"},
            "network_error": {"icon": "🌐", "title": "Network Error", "color": "#8B5CF6"},
            "file_error": {"icon": "📁", "title": "File Error", "color": "#EF4444"},
            "system_error": {"icon": "⚙️", "title": "System Error", "color": "#64748B"},
            "validation_error": {"icon": "[DONE]", "title": "Validation Error", "color": "#F59E0B"},
        }

    def handle_error(
        self,
        error: Exception,
        error_type: str = "system_error",
        context: dict[str, Any] | None = None,
        show_details: bool = False,
    ) -> dict[str, Any]:
        """Handle an error with user-friendly display and logging."""
        # Log the error
        error_info = self._log_error(error, error_type, context)

        # Display user-friendly error message
        self._display_error_message(error_info, show_details)

        # Provide recovery options
        self._provide_recovery_options(error_type, error_info)

        # Update error tracking
        self._update_error_tracking(error_info)

        return error_info

    def _log_error(self, error: Exception, error_type: str, context: dict[str, Any] | None) -> dict[str, Any]:
        """Log error details and return error information."""
        error_info = {
            "id": self._generate_error_id(),
            "type": error_type,
            "message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "traceback": traceback.format_exc(),
            "user_message": self._get_user_friendly_message(error, error_type),
        }

        # Log with appropriate level
        if error_type in ["system_error", "model_error"]:
            logger.error(f"Error {error_info['id']}: {error_info['message']}")
        else:
            logger.warning(f"Error {error_info['id']}: {error_info['message']}")

        # Log context if available
        if context:
            logger.debug(f"Error context: {context}")

        return error_info

    def _display_error_message(self, error_info: dict[str, Any], show_details: bool):
        """Display user-friendly error message."""
        error_type_info = self.error_types.get(error_info["type"], self.error_types["system_error"])

        # Main error display
        st.error(f"{error_type_info['icon']} **{error_type_info['title']}**: {error_info['user_message']}")

        # Error details in expander
        if show_details or st.session_state.get("debug_mode", False):
            with st.expander("🔍 Error Details", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Error ID:**")
                    st.code(error_info["id"])

                    st.markdown("**Timestamp:**")
                    st.code(error_info["timestamp"])

                    st.markdown("**Type:**")
                    st.code(error_info["type"])

                with col2:
                    st.markdown("**Original Message:**")
                    st.code(error_info["message"])

                    if error_info["context"]:
                        st.markdown("**Context:**")
                        st.json(error_info["context"])

                if st.session_state.get("debug_mode", False):
                    st.markdown("**Traceback:**")
                    st.code(error_info["traceback"])

    def _get_user_friendly_message(self, error: Exception, error_type: str) -> str:
        """Generate user-friendly error message."""
        error_message = str(error).lower()

        # Model-specific errors
        if error_type == "model_error":
            if "out of memory" in error_message or "cuda" in error_message:
                return "The AI model ran out of memory. Try using a smaller image or restart the application."
            elif "model not found" in error_message or "checkpoint" in error_message:
                return "The AI model could not be loaded. Please check your installation or try refreshing the page."
            elif "timeout" in error_message:
                return "The AI model is taking too long to respond. Please try again with a smaller input."
            else:
                return "The AI model encountered an error. Please try again or use a different input method."

        # Input-specific errors
        elif error_type == "input_error":
            if "format" in error_message or "invalid" in error_message:
                return "The input format is not supported. Please check the file type and try again."
            elif "size" in error_message or "large" in error_message:
                return "The input is too large. Please use a smaller file (max 200MB for images, 60 seconds for audio)."
            elif "empty" in error_message or "missing" in error_message:
                return "No input was provided. Please select an image, record audio, or type a message."
            else:
                return "There was a problem with your input. Please check the format and try again."

        # File-specific errors
        elif error_type == "file_error":
            if "permission" in error_message or "access" in error_message:
                return "Cannot access the file. Please check file permissions and try again."
            elif "not found" in error_message or "missing" in error_message:
                return "The file could not be found. Please make sure it exists and try again."
            elif "corrupted" in error_message or "damaged" in error_message:
                return "The file appears to be corrupted. Please try a different file."
            else:
                return "There was a problem reading the file. Please try a different file or format."

        # Network-specific errors
        elif error_type == "network_error":
            return "Network connection issue detected. Don't worry - PlantGuard works offline! Please continue using the application."

        # Validation errors
        elif error_type == "validation_error":
            return f"Input validation failed: {error!s}"

        # Generic system error
        else:
            return "An unexpected error occurred. Please try again or refresh the page if the problem persists."

    def _provide_recovery_options(self, error_type: str, error_info: dict[str, Any]):
        """Provide recovery options based on error type."""
        st.markdown("### [TOOL] Try These Solutions:")

        if error_type == "model_error":
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("[PARTIAL] Retry Analysis", key=f"retry_{error_info['id']}"):
                    st.rerun()

            with col2:
                if st.button("🧹 Clear Cache", key=f"clear_cache_{error_info['id']}"):
                    self._clear_model_cache()
                    st.success("Cache cleared! Please try again.")

            with col3:
                if st.button("[PARTIAL] Restart Session", key=f"restart_{error_info['id']}"):
                    self._restart_session()

        elif error_type == "input_error":
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📝 Try Different Input", key=f"new_input_{error_info['id']}"):
                    self._clear_current_inputs()
                    st.info("Inputs cleared. Please try a different file or input method.")

            with col2:
                if st.button("i Input Guidelines", key=f"guidelines_{error_info['id']}"):
                    self._show_input_guidelines()

        elif error_type == "file_error":
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📁 Try Different File", key=f"new_file_{error_info['id']}"):
                    self._clear_file_inputs()
                    st.info("File inputs cleared. Please select a different file.")

            with col2:
                if st.button("[TOOL] File Format Help", key=f"format_help_{error_info['id']}"):
                    self._show_file_format_help()

        else:
            # Generic recovery options
            col1, col2 = st.columns(2)

            with col1:
                if st.button("[PARTIAL] Try Again", key=f"retry_generic_{error_info['id']}"):
                    st.rerun()

            with col2:
                if st.button("🏠 Go to Home", key=f"home_{error_info['id']}"):
                    st.session_state.current_page = "Home"
                    st.rerun()

    def _clear_model_cache(self):
        """Clear model cache."""
        # Clear Streamlit cache
        st.cache_data.clear()
        st.cache_resource.clear()

        # Reset model load status
        st.session_state.model_load_status = {
            "vision": "not_loaded",
            "audio": "not_loaded",
            "text": "not_loaded",
            "fusion": "not_loaded",
        }

    def _restart_session(self):
        """Restart the session by clearing most session state."""
        from .state_manager import StateManager

        state_manager = StateManager()
        state_manager.clear_state()

        st.success("Session restarted! Please refresh the page.")

    def _clear_current_inputs(self):
        """Clear current input data."""
        input_keys = ["uploaded_images", "camera_image", "recorded_audio", "transcribed_text", "active_inputs"]

        for key in input_keys:
            if key in st.session_state:
                del st.session_state[key]

    def _clear_file_inputs(self):
        """Clear file-related inputs."""
        file_keys = ["uploaded_images", "camera_image", "uploaded_audio"]

        for key in file_keys:
            if key in st.session_state:
                del st.session_state[key]

    def _show_input_guidelines(self):
        """Show input format guidelines."""
        with st.expander("[DETAILS] Input Guidelines", expanded=True):
            st.markdown("""
            **Image Requirements:**
            - Formats: JPG, JPEG, PNG
            - Max size: 200MB
            - Min resolution: 224x224 pixels
            - Clear, well-lit photos work best

            **Audio Requirements:**
            - Formats: WAV, MP3
            - Duration: 1-60 seconds
            - Clear speech in quiet environment

            **Text Requirements:**
            - Max length: 1000 characters
            - Describe symptoms or ask questions
            - Use clear, simple language
            """)

    def _show_file_format_help(self):
        """Show file format help."""
        with st.expander("📁 Supported File Formats", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                **Image Formats:**
                - [DONE] JPEG (.jpg, .jpeg)
                - [DONE] PNG (.png)
                - [TODO] GIF, BMP, TIFF
                - [TODO] RAW formats
                """)

            with col2:
                st.markdown("""
                **Audio Formats:**
                - [DONE] WAV (.wav)
                - [DONE] MP3 (.mp3)
                - [TODO] FLAC, OGG, M4A
                - [TODO] Video files
                """)

    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        import uuid

        return f"ERR_{uuid.uuid4().hex[:8].upper()}"

    def _update_error_tracking(self, error_info: dict[str, Any]):
        """Update error tracking in session state."""
        error_count = st.session_state.get("error_count", 0)
        st.session_state.error_count = error_count + 1
        st.session_state.last_error = error_info

        # Store recent errors (max 10)
        recent_errors = st.session_state.get("recent_errors", [])
        recent_errors.append(error_info)
        if len(recent_errors) > 10:
            recent_errors = recent_errors[-10:]
        st.session_state.recent_errors = recent_errors

    def handle_page_error(self, error: Exception, page_name: str):
        """Handle page-specific errors."""
        context = {"page": page_name, "user_action": "page_navigation"}

        _error_info = self.handle_error(error, error_type="system_error", context=context, show_details=False)

        # Provide content focus options instead of page navigation
        st.markdown("### 🏠 Content Focus Options:")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🏠 Focus on Image Analysis", key="error_focus_home"):
                st.session_state.focused_content = "image_analysis"
                st.success("Focused on Image Analysis - no page refresh!")

        with col2:
            if st.button("[PARTIAL] Refresh Content", key="error_refresh_content"):
                st.success("Content refreshed - staying on same page!")

        with col3:
            if st.button("[SUMMARY] Focus on History", key="error_focus_history"):
                st.session_state.focused_content = "history_settings"
                st.success("Focused on History - no page refresh!")

        with col3:
            if st.button("📚 View History"):
                st.session_state.current_page = "History"
                st.rerun()

    def render_error_summary(self):
        """Render error summary for debugging."""
        if st.session_state.get("debug_mode", False):
            recent_errors = st.session_state.get("recent_errors", [])
            error_count = st.session_state.get("error_count", 0)

            if recent_errors:
                with st.expander(f"🐛 Error Summary ({error_count} total)", expanded=False):
                    for error in recent_errors[-5:]:  # Show last 5 errors
                        st.markdown(f"**{error['timestamp']}** - {error['type']}: {error['user_message']}")

    def validate_input(self, input_data: Any, input_type: str, requirements: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate input data against requirements."""
        try:
            if input_type == "image":
                return self._validate_image_input(input_data, requirements)
            elif input_type == "audio":
                return self._validate_audio_input(input_data, requirements)
            elif input_type == "text":
                return self._validate_text_input(input_data, requirements)
            else:
                return False, f"Unknown input type: {input_type}"

        except Exception as e:
            error_msg = f"Validation error: {e!s}"
            logger.error(error_msg)
            return False, error_msg

    def _validate_image_input(self, image_data: Any, requirements: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate image input."""
        if image_data is None:
            return False, "No image provided"

        # Check file size
        max_size = requirements.get("max_size", 200 * 1024 * 1024)  # 200MB default
        if hasattr(image_data, "size") and image_data.size > max_size:
            return (
                False,
                f"Image too large: {image_data.size / 1024 / 1024:.1f}MB (max: {max_size / 1024 / 1024:.0f}MB)",
            )

        # Check format
        allowed_formats = requirements.get("formats", ["jpg", "jpeg", "png"])
        if hasattr(image_data, "name"):
            file_ext = image_data.name.split(".")[-1].lower()
            if file_ext not in allowed_formats:
                return False, f"Unsupported format: {file_ext} (allowed: {', '.join(allowed_formats)})"

        return True, None

    def _validate_audio_input(self, audio_data: Any, requirements: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate audio input."""
        if audio_data is None:
            return False, "No audio provided"

        # Check format
        allowed_formats = requirements.get("formats", ["wav", "mp3"])
        if hasattr(audio_data, "name"):
            file_ext = audio_data.name.split(".")[-1].lower()
            if file_ext not in allowed_formats:
                return False, f"Unsupported format: {file_ext} (allowed: {', '.join(allowed_formats)})"

        return True, None

    def _validate_text_input(self, text_data: str, requirements: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate text input."""
        if not text_data or not text_data.strip():
            return False, "No text provided"

        # Check length
        max_length = requirements.get("max_length", 1000)
        if len(text_data) > max_length:
            return False, f"Text too long: {len(text_data)} characters (max: {max_length})"

        min_length = requirements.get("min_length", 1)
        if len(text_data.strip()) < min_length:
            return False, f"Text too short: {len(text_data.strip())} characters (min: {min_length})"

        return True, None
