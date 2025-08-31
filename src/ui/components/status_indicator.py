"""Status Indicator Component for PlantGuard.

Provides visual status indicators for models, system health, and application state.
"""


from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def render_status_indicator(status: object, label: str = "", size: str = "medium") -> None:
    """Render a status indicator with color-coded visual feedback.

    Args:
        status: Status type ("loaded", "loading", "error", "offline", "ready")
        label: Optional label text to display next to indicator
        size: Size of indicator ("small", "medium", "large")
    """
    # Status configurations
    status_config = {
        "loaded": {"color": "#22C55E", "icon": "[GREEN]", "text": "Loaded"},
        "loading": {"color": "#F59E0B", "icon": "[YELLOW]", "text": "Loading"},
        "error": {"color": "#EF4444", "icon": "[RED]", "text": "Error"},
        "offline": {"color": "#64748B", "icon": "⚪", "text": "Offline"},
        "ready": {"color": "#22C55E", "icon": "[DONE]", "text": "Ready"},
        "warning": {"color": "#F59E0B", "icon": "[WARNING]", "text": "Warning"},
        "info": {"color": "#3B82F6", "icon": "i", "text": "Info"},
    }

    # Size configurations
    size_config = {
        "small": {"font_size": "0.8rem", "padding": "0.25rem 0.5rem"},
        "medium": {"font_size": "1rem", "padding": "0.5rem 1rem"},
        "large": {"font_size": "1.2rem", "padding": "0.75rem 1.5rem"},
    }

    # Allow non-str status values from session/state; coerce to str for lookup
    status_key = status if isinstance(status, str) else str(status)
    config = status_config.get(status_key, status_config["offline"])
    size_style = size_config.get(size, size_config["medium"])

    display_text = label if label else config["text"]

    st.markdown(
        f"""
        <div style='
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: {config["color"]}20;
            border: 1px solid {config["color"]};
            border-radius: 20px;
            padding: {size_style["padding"]};
            font-size: {size_style["font_size"]};
            font-weight: 600;
            color: {config["color"]};
        '>
            <span>{config["icon"]}</span>
            <span>{display_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


class StatusIndicator:
    """Advanced status indicator component with multiple display modes."""

    def __init__(self) -> None:
        self.status_history = []

    def render_system_status(self) -> None:
        """Render overall system status dashboard."""
        st.markdown("### [LAUNCH] System Status")

        # Get model status
        model_status = st.session_state.get("model_load_status", {"vision": "loaded", "audio": "loaded", "text": "loaded", "fusion": "loaded"})

        # Create status grid
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("**Vision Model**")
            render_status_indicator(model_status.get("vision", "offline"), "Vision AI")

        with col2:
            st.markdown("**Audio Model**")
            render_status_indicator(model_status.get("audio", "offline"), "Audio AI")

        with col3:
            st.markdown("**Text Model**")
            render_status_indicator(model_status.get("text", "offline"), "Text AI")

        with col4:
            st.markdown("**System Health**")
            # Determine overall health
            statuses = list(model_status.values())
            if all(s == "loaded" for s in statuses):
                render_status_indicator("ready", "All Systems")
            elif any(s == "error" for s in statuses):
                render_status_indicator("error", "System Error")
            elif any(s == "loading" for s in statuses):
                render_status_indicator("loading", "Initializing")
            else:
                render_status_indicator("warning", "Partial")

    def render_model_status_grid(self, models: dict[str, str]) -> None:
        """Render a grid of model statuses."""
        if not models:
            st.info("No models to display")
            return

        # Calculate columns based on number of models
        num_models = len(models)
        cols = st.columns(min(num_models, 4))

        for i, (model_name, status) in enumerate(models.items()):
            with cols[i % len(cols)]:
                st.markdown(f"**{model_name.title()}**")
                render_status_indicator(status, f"{model_name} Model")

    def render_connection_status(self) -> None:
        """Render network/connection status."""
        st.markdown("### [NETWORK] Connection Status")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Local Processing**")
            render_status_indicator("ready", "Offline Mode", "medium")
            st.caption("All processing happens locally")

        with col2:
            st.markdown("**Privacy Protection**")
            render_status_indicator("ready", "Secure", "medium")
            st.caption("No data sent to external services")

    def render_performance_indicators(self) -> None:
        """Render performance status indicators."""
        st.markdown("### [ACTIONS] Performance Status")

        # Mock performance data - in real app this would come from actual metrics
        performance_data = {
            "CPU Usage": {"value": 45, "status": "ready"},
            "Memory Usage": {"value": 60, "status": "warning"},
            "GPU Usage": {"value": 30, "status": "ready"},
            "Response Time": {"value": 250, "status": "ready"},
        }

        cols = st.columns(len(performance_data))

        for i, (metric, data) in enumerate(performance_data.items()):
            with cols[i]:
                st.metric(metric, f"{data['value']}%")
                render_status_indicator(data["status"], "Normal", "small")

    def render_feature_status(self) -> None:
        """Render status of different features."""
        st.markdown("### [PROGRESS] Feature Status")

        features = {
            "Image Analysis": "ready",
            "Voice Processing": "ready",
            "Text Q&A": "ready",
            "Real-time Camera": "ready",
            "Audio Recording": "ready",
            "Model Switching": "ready",
        }

        # Group features in rows of 3
        feature_items = list(features.items())
        for i in range(0, len(feature_items), 3):
            cols = st.columns(3)
            for j, (feature, status) in enumerate(feature_items[i : i + 3]):
                with cols[j]:
                    render_status_indicator(status, feature, "small")

    def render_compact_status_bar(self) -> None:
        """Render a compact status bar for headers."""
        model_status = st.session_state.get("model_load_status", {})
        loaded_count = sum(1 for status in model_status.values() if status == "loaded")
        total_count = len(model_status) if model_status else 4

        if loaded_count == total_count and total_count > 0:
            _status = "ready"
            text = f"[GREEN] Ready ({loaded_count}/{total_count})"
        elif loaded_count > 0:
            _status = "loading"
            text = f"[YELLOW] Loading ({loaded_count}/{total_count})"
        else:
            _status = "offline"
            text = "⚪ Initializing"

        st.markdown(
            f"""
            <div style='
                text-align: right;
                font-size: 0.875rem;
                padding: 0.5rem;
            '>
                <span style='font-weight: 600;'>{text}</span><br>
                <span style='color: #64748B;'>[SECURE] Offline Mode</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def add_status_update(self, component: str, status: str, message: str = "") -> None:
        """Add a status update to history."""
        update = {
            "component": component,
            "status": status,
            "message": message,
            "timestamp": st.session_state.get("current_time", ""),
        }

        self.status_history.append(update)

        # Keep only last 50 updates
        if len(self.status_history) > 50:
            self.status_history = self.status_history[-50:]

        logger.info(f"Status update: {component} -> {status}")

    def render_status_history(self) -> None:
        """Render recent status updates."""
        if not self.status_history:
            st.info("No status updates yet")
            return

        st.markdown("### [SCROLL] Recent Status Updates")

        for update in reversed(self.status_history[-10:]):  # Show last 10
            col1, col2, col3 = st.columns([2, 1, 3])

            with col1:
                st.text(update["component"])

            with col2:
                render_status_indicator(update["status"], "", "small")

            with col3:
                st.caption(update.get("message", ""))

    def get_overall_status(self) -> str:
        """Get overall system status."""
        model_status = st.session_state.get("model_load_status", {})

        if not model_status:
            return "offline"

        statuses = list(model_status.values())

        if all(s == "loaded" for s in statuses):
            return "ready"
        elif any(s == "error" for s in statuses):
            return "error"
        elif any(s == "loading" for s in statuses):
            return "loading"
        else:
            return "warning"

    def render_status_badge(self, status: str, count: int = 0) -> None:
        """Render a status badge with optional count."""
        config = {
            "ready": {"color": "#22C55E", "icon": "[DONE]", "text": "Ready"},
            "loading": {"color": "#F59E0B", "icon": "⏳", "text": "Loading"},
            "error": {"color": "#EF4444", "icon": "[TODO]", "text": "Error"},
            "warning": {"color": "#F59E0B", "icon": "[WARNING]", "text": "Warning"},
        }.get(status, {"color": "#64748B", "icon": "⚪", "text": "Unknown"})

        display_text = f"{config['text']}"
        if count > 0:
            display_text += f" ({count})"

        st.markdown(
            f"""
            <div style='
                display: inline-block;
                background: {config["color"]}20;
                border: 2px solid {config["color"]};
                border-radius: 25px;
                padding: 0.5rem 1rem;
                font-weight: 700;
                color: {config["color"]};
                text-align: center;
                min-width: 100px;
            '>
                {config["icon"]} {display_text}
            </div>
            """,
            unsafe_allow_html=True,
        )
