"""State Manager for PlantGuard Redesigned UI.

Handles session state management, user preferences, and data persistence
across different pages and components.
"""

import logging
from datetime import datetime
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class StateManager:
    """Manages application state and user preferences."""

    def __init__(self):
        self.session_keys = {
            # Navigation state
            "current_page": "Home",
            "page_history": [],
            # Input state
            "input_modes": {"text": False, "voice": False, "camera": False, "upload": False},
            "active_inputs": {},
            # Chat state
            "messages": [],
            "conversation_id": None,
            # Analysis state
            "analysis_results": [],
            "current_analysis": None,
            # User preferences
            "user_preferences": self._get_default_preferences(),
            # UI state
            "mobile_view": False,
            "sidebar_collapsed": False,
            "theme": "light",
            # Session metadata
            "session_id": self._generate_session_id(),
            "session_start": datetime.now().isoformat(),
            # Error state
            "last_error": None,
            "error_count": 0,
            # Performance tracking
            "page_load_times": {},
            "model_load_status": {
                "vision": "not_loaded",
                "audio": "not_loaded",
                "text": "not_loaded",
                "fusion": "not_loaded",
            },
        }

    def initialize_defaults(self):
        """Initialize session state with default values."""
        for key, default_value in self.session_keys.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                logger.debug(f"Initialized session state key: {key}")

    def _get_default_preferences(self) -> dict[str, Any]:
        """Get default user preferences."""
        return {
            "theme": "light",
            "language": "en",
            "units": "metric",
            "accessibility": {
                "high_contrast": False,
                "large_text": False,
                "reduced_motion": False,
                "screen_reader": False,
            },
            "interface": {
                "simple_mode": False,
                "expert_mode": False,
                "show_confidence": True,
                "show_probabilities": True,
                "auto_analyze": False,
            },
            "models": {
                "vision_model": "resnet50_plantvillage_v1",
                "audio_model": "whisper_tiny_local",
                "text_model": "distilbert_plant_qa_v1",
            },
            "privacy": {"auto_delete_audio": True, "save_history": True, "analytics_consent": False},
        }

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid

        return str(uuid.uuid4())[:8]

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get value from session state."""
        return st.session_state.get(key, default)

    def set_state(self, key: str, value: Any, persist: bool = False):
        """Set value in session state."""
        st.session_state[key] = value

        if persist:
            self._persist_preference(key, value)

        logger.debug(f"Set session state: {key} = {value}")

    def update_state(self, updates: dict[str, Any]):
        """Update multiple state values at once."""
        for key, value in updates.items():
            self.set_state(key, value)

    def clear_state(self, keys: list[str] | None = None):
        """Clear specific keys or all session state."""
        if keys is None:
            # Clear all except essential keys
            essential_keys = ["session_id", "session_start", "user_preferences"]
            for key in list(st.session_state.keys()):
                if key not in essential_keys:
                    del st.session_state[key]
        else:
            for key in keys:
                if key in st.session_state:
                    del st.session_state[key]

        logger.info(f"Cleared session state keys: {keys or 'all'}")

    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference value."""
        preferences = self.get_state("user_preferences", {})

        # Handle nested keys like "accessibility.high_contrast"
        if "." in key:
            keys = key.split(".")
            value = preferences
            for k in keys:
                value = value.get(k, {}) if isinstance(value, dict) else default
            return value if value != {} else default

        return preferences.get(key, default)

    def set_user_preference(self, key: str, value: Any):
        """Set user preference value."""
        preferences = self.get_state("user_preferences", {})

        # Handle nested keys
        if "." in key:
            keys = key.split(".")
            current = preferences
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        else:
            preferences[key] = value

        self.set_state("user_preferences", preferences, persist=True)
        logger.info(f"Updated user preference: {key} = {value}")

    def _persist_preference(self, key: str, value: Any):
        """Persist preference to local storage (placeholder)."""
        # In a real implementation, this would save to local storage
        # For now, we just log it
        logger.debug(f"Would persist preference: {key} = {value}")

    def add_message(self, role: str, content: str, metadata: dict | None = None):
        """Add message to chat history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        messages = self.get_state("messages", [])
        messages.append(message)
        self.set_state("messages", messages)

        logger.debug(f"Added message: {role} - {len(content)} chars")

    def clear_chat_history(self):
        """Clear chat message history."""
        self.set_state("messages", [])
        logger.info("Cleared chat history")

    def add_analysis_result(self, result: dict[str, Any]):
        """Add analysis result to history."""
        result["id"] = f"analysis_{len(self.get_state('analysis_results', []))}"
        result["timestamp"] = datetime.now().isoformat()

        results = self.get_state("analysis_results", [])
        results.append(result)
        self.set_state("analysis_results", results)
        self.set_state("current_analysis", result)

        logger.info(f"Added analysis result: {result['id']}")

    def get_analysis_history(self, limit: int | None = None) -> list[dict]:
        """Get analysis history with optional limit."""
        results = self.get_state("analysis_results", [])
        if limit:
            return results[-limit:]
        return results

    def clear_analysis_history(self):
        """Clear analysis history."""
        self.set_state("analysis_results", [])
        self.set_state("current_analysis", None)
        logger.info("Cleared analysis history")

    def set_input_mode(self, mode: str, active: bool):
        """Set input mode state."""
        input_modes = self.get_state("input_modes", {})
        input_modes[mode] = active
        self.set_state("input_modes", input_modes)

        logger.debug(f"Set input mode {mode}: {active}")

    def get_active_input_modes(self) -> list[str]:
        """Get list of currently active input modes."""
        input_modes = self.get_state("input_modes", {})
        return [mode for mode, active in input_modes.items() if active]

    def clear_all_inputs(self):
        """Clear all input modes and data."""
        self.set_state("input_modes", {"text": False, "voice": False, "camera": False, "upload": False})
        self.set_state("active_inputs", {})
        logger.info("Cleared all input modes")

    def track_page_visit(self, page: str):
        """Track page visit for analytics."""
        page_history = self.get_state("page_history", [])
        page_history.append({"page": page, "timestamp": datetime.now().isoformat()})

        # Keep only last 50 page visits
        if len(page_history) > 50:
            page_history = page_history[-50:]

        self.set_state("page_history", page_history)
        self.set_state("current_page", page)

        # Track page transition for animations
        self._track_page_transition(page)

    def _track_page_transition(self, new_page: str):
        """Track page transition for smooth animations."""
        previous_page = self.get_state("previous_page")

        if previous_page and previous_page != new_page:
            # Set transition state
            self.set_state(
                "page_transition",
                {"from": previous_page, "to": new_page, "timestamp": datetime.now().isoformat(), "in_progress": True},
            )

            # Add loading state
            self.set_state("page_loading", True)

        self.set_state("previous_page", new_page)

    def complete_page_transition(self):
        """Complete page transition and clear loading state."""
        transition = self.get_state("page_transition", {})
        if transition.get("in_progress"):
            transition["in_progress"] = False
            transition["completed_at"] = datetime.now().isoformat()
            self.set_state("page_transition", transition)

        self.set_state("page_loading", False)

    def is_page_loading(self) -> bool:
        """Check if page is currently loading."""
        return self.get_state("page_loading", False)

    def get_page_transition_info(self) -> dict[str, Any]:
        """Get current page transition information."""
        return self.get_state("page_transition", {})

    def get_session_stats(self) -> dict[str, Any]:
        """Get session statistics."""
        return {
            "session_id": self.get_state("session_id"),
            "session_duration": self._calculate_session_duration(),
            "pages_visited": len(self.get_state("page_history", [])),
            "messages_sent": len(self.get_state("messages", [])),
            "analyses_performed": len(self.get_state("analysis_results", [])),
            "errors_encountered": self.get_state("error_count", 0),
            "current_page": self.get_state("current_page"),
            "active_modes": self.get_active_input_modes(),
        }

    def _calculate_session_duration(self) -> str:
        """Calculate session duration."""
        start_time = datetime.fromisoformat(self.get_state("session_start"))
        duration = datetime.now() - start_time

        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"

    def export_session_data(self) -> dict[str, Any]:
        """Export session data for backup/analysis."""
        return {
            "session_info": {
                "id": self.get_state("session_id"),
                "start_time": self.get_state("session_start"),
                "duration": self._calculate_session_duration(),
            },
            "preferences": self.get_state("user_preferences"),
            "statistics": self.get_session_stats(),
            "analysis_history": self.get_analysis_history(),
            "page_history": self.get_state("page_history", []),
        }

    def is_mobile_view(self) -> bool:
        """Check if mobile view is active."""
        return self.get_state("mobile_view", False)

    def set_mobile_view(self, mobile: bool):
        """Set mobile view state."""
        self.set_state("mobile_view", mobile)

    def get_theme(self) -> str:
        """Get current theme."""
        return self.get_user_preference("theme", "light")

    def set_theme(self, theme: str):
        """Set application theme."""
        self.set_user_preference("theme", theme)
        logger.info(f"Theme changed to: {theme}")
