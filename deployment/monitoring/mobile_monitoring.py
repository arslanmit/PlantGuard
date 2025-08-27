"""
Mobile PlantGuard Monitoring and Analytics System

Privacy-focused monitoring system that tracks application performance
and usage patterns without collecting personal data.
"""

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import streamlit as st


@dataclass
class MobileMetric:
    """Data class for mobile-specific metrics."""

    timestamp: str
    metric_type: str
    value: float
    metadata: dict[str, Any]
    session_id: str  # Anonymous session identifier


@dataclass
class PerformanceMetric:
    """Performance-specific metrics."""

    component_name: str
    operation: str
    duration_ms: float
    success: bool
    error_type: str | None = None


@dataclass
class UsageMetric:
    """Usage pattern metrics (privacy-compliant)."""

    feature_used: str
    interaction_type: str
    device_type: str  # mobile/tablet/desktop
    browser_type: str
    success: bool


class MobileMonitoringSystem:
    """
    Privacy-focused monitoring system for mobile PlantGuard.

    Features:
    - No personal data collection
    - Session-only tracking
    - Local storage only
    - Performance monitoring
    - Error tracking
    - Usage analytics
    """

    def __init__(self, log_file: str = "logs/mobile_monitoring.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)

        # Initialize logging
        self.logger = self._setup_logging()

        # In-memory storage for current session
        self.metrics: deque = deque(maxlen=1000)
        self.performance_metrics: deque = deque(maxlen=500)
        self.usage_metrics: deque = deque(maxlen=500)
        self.error_metrics: deque = deque(maxlen=100)

        # Session tracking
        self.session_id = self._get_session_id()
        self.session_start = datetime.now()

        # Performance tracking
        self.component_timers: dict[str, float] = {}

        # Usage counters
        self.feature_usage = defaultdict(int)
        self.error_counts = defaultdict(int)

        self.logger.info(f"Mobile monitoring initialized for session {self.session_id}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("mobile_monitoring")
        logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        return logger

    def _get_session_id(self) -> str:
        """Generate anonymous session identifier."""
        if "mobile_session_id" not in st.session_state:
            # Generate anonymous session ID based on timestamp
            st.session_state.mobile_session_id = f"session_{int(time.time())}"
        return st.session_state.mobile_session_id

    def track_performance(self, component_name: str, operation: str, duration_ms: float, success: bool = True, error_type: str | None = None) -> None:
        """Track component performance metrics."""
        metric = PerformanceMetric(
            component_name=component_name, operation=operation, duration_ms=duration_ms, success=success, error_type=error_type
        )

        self.performance_metrics.append(metric)

        # Log performance issues
        if duration_ms > 5000:  # 5 seconds
            self.logger.warning(f"Slow operation: {component_name}.{operation} took {duration_ms}ms")

        if not success:
            self.logger.error(f"Failed operation: {component_name}.{operation} - {error_type}")

    def track_usage(self, feature_used: str, interaction_type: str, success: bool = True) -> None:
        """Track feature usage patterns."""
        # Detect device and browser type from user agent
        device_type, browser_type = self._detect_device_browser()

        metric = UsageMetric(
            feature_used=feature_used, interaction_type=interaction_type, device_type=device_type, browser_type=browser_type, success=success
        )

        self.usage_metrics.append(metric)
        self.feature_usage[feature_used] += 1

        self.logger.info(f"Feature used: {feature_used} ({interaction_type}) - Device: {device_type}, Browser: {browser_type}")

    def track_error(self, component: str, error_type: str, error_message: str, severity: str = "error") -> None:
        """Track application errors."""
        error_metric = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "error_type": error_type,
            "severity": severity,
            "session_id": self.session_id,
        }

        self.error_metrics.append(error_metric)
        self.error_counts[error_type] += 1

        # Log based on severity
        if severity == "critical":
            self.logger.critical(f"{component}: {error_type} - {error_message}")
        elif severity == "error":
            self.logger.error(f"{component}: {error_type} - {error_message}")
        else:
            self.logger.warning(f"{component}: {error_type} - {error_message}")

    def start_timer(self, component_name: str, operation: str) -> str:
        """Start performance timer for an operation."""
        timer_key = f"{component_name}_{operation}_{time.time()}"
        self.component_timers[timer_key] = time.time()
        return timer_key

    def end_timer(self, timer_key: str, success: bool = True, error_type: str | None = None) -> float:
        """End performance timer and record metric."""
        if timer_key not in self.component_timers:
            self.logger.warning(f"Timer key not found: {timer_key}")
            return 0.0

        start_time = self.component_timers.pop(timer_key)
        duration_ms = (time.time() - start_time) * 1000

        # Extract component and operation from timer key
        parts = timer_key.split("_")
        component_name = parts[0]
        operation = parts[1]

        self.track_performance(component_name, operation, duration_ms, success, error_type)
        return duration_ms

    def _detect_device_browser(self) -> tuple[str, str]:
        """Detect device and browser type from user agent."""
        # This would typically use request headers, but in Streamlit
        # we'll use a simplified approach
        device_type = "mobile"  # Default assumption for mobile app
        browser_type = "unknown"

        # In a real implementation, you would parse the user agent
        # For now, return defaults
        return device_type, browser_type

    def get_session_summary(self) -> dict[str, Any]:
        """Get summary of current session metrics."""
        session_duration = (datetime.now() - self.session_start).total_seconds()

        # Performance summary
        perf_metrics = list(self.performance_metrics)
        avg_performance = {}
        if perf_metrics:
            for metric in perf_metrics:
                key = f"{metric.component_name}_{metric.operation}"
                if key not in avg_performance:
                    avg_performance[key] = []
                avg_performance[key].append(metric.duration_ms)

            # Calculate averages
            for key in avg_performance:
                avg_performance[key] = sum(avg_performance[key]) / len(avg_performance[key])

        # Usage summary
        total_interactions = len(self.usage_metrics)
        successful_interactions = sum(1 for m in self.usage_metrics if m.success)
        success_rate = (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0

        # Error summary
        total_errors = len(self.error_metrics)
        error_types = dict(self.error_counts)

        return {
            "session_id": self.session_id,
            "session_duration_seconds": session_duration,
            "total_interactions": total_interactions,
            "success_rate_percent": success_rate,
            "feature_usage": dict(self.feature_usage),
            "average_performance_ms": avg_performance,
            "total_errors": total_errors,
            "error_breakdown": error_types,
            "timestamp": datetime.now().isoformat(),
        }

    def export_session_data(self, file_path: str | None = None) -> str:
        """Export session data to JSON file."""
        if file_path is None:
            file_path = f"logs/session_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        session_data = {
            "summary": self.get_session_summary(),
            "performance_metrics": [asdict(m) for m in self.performance_metrics],
            "usage_metrics": [asdict(m) for m in self.usage_metrics],
            "error_metrics": list(self.error_metrics),
        }

        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=2)

        self.logger.info(f"Session data exported to {file_path}")
        return file_path

    def get_health_status(self) -> dict[str, Any]:
        """Get application health status."""
        recent_errors = [m for m in self.error_metrics if datetime.fromisoformat(m["timestamp"]) > datetime.now() - timedelta(minutes=5)]

        recent_performance = (
            [m for m in self.performance_metrics if datetime.fromisoformat(m.timestamp) > datetime.now() - timedelta(minutes=5)]
            if hasattr(next(iter(self.performance_metrics)) if self.performance_metrics else None, "timestamp")
            else []
        )

        # Calculate health score
        error_penalty = min(len(recent_errors) * 10, 50)  # Max 50% penalty for errors
        performance_penalty = 0

        if recent_performance:
            avg_duration = sum(m.duration_ms for m in recent_performance) / len(recent_performance)
            if avg_duration > 3000:  # 3 seconds
                performance_penalty = min((avg_duration - 3000) / 100, 30)  # Max 30% penalty

        health_score = max(100 - error_penalty - performance_penalty, 0)

        status = "healthy"
        if health_score < 50:
            status = "unhealthy"
        elif health_score < 80:
            status = "degraded"

        return {
            "status": status,
            "health_score": health_score,
            "recent_errors": len(recent_errors),
            "recent_avg_performance_ms": sum(m.duration_ms for m in recent_performance) / len(recent_performance) if recent_performance else 0,
            "timestamp": datetime.now().isoformat(),
        }


class MobileAnalyticsDashboard:
    """
    Privacy-focused analytics dashboard for mobile PlantGuard.
    Displays aggregated, anonymous usage statistics.
    """

    def __init__(self, monitoring_system: MobileMonitoringSystem):
        self.monitoring = monitoring_system

    def render_dashboard(self) -> None:
        """Render the analytics dashboard in Streamlit."""
        st.subheader("📊 Mobile Analytics Dashboard")

        # Session summary
        summary = self.monitoring.get_session_summary()

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Session Duration", f"{summary['session_duration_seconds']:.0f}s")

        with col2:
            st.metric("Total Interactions", summary["total_interactions"])

        with col3:
            st.metric("Success Rate", f"{summary['success_rate_percent']:.1f}%")

        with col4:
            st.metric("Total Errors", summary["total_errors"])

        # Feature usage chart
        if summary["feature_usage"]:
            st.subheader("Feature Usage")
            feature_data = summary["feature_usage"]
            st.bar_chart(feature_data)

        # Performance metrics
        if summary["average_performance_ms"]:
            st.subheader("Average Performance (ms)")
            perf_data = summary["average_performance_ms"]
            st.bar_chart(perf_data)

        # Error breakdown
        if summary["error_breakdown"]:
            st.subheader("Error Breakdown")
            error_data = summary["error_breakdown"]
            st.bar_chart(error_data)

        # Health status
        health = self.monitoring.get_health_status()
        st.subheader("System Health")

        status_color = {"healthy": "green", "degraded": "orange", "unhealthy": "red"}

        st.markdown(f"**Status:** :{status_color[health['status']]}[{health['status'].upper()}] (Score: {health['health_score']:.0f}/100)")

        # Export option
        if st.button("Export Session Data"):
            file_path = self.monitoring.export_session_data()
            st.success(f"Session data exported to {file_path}")


# Context manager for performance tracking
class PerformanceTracker:
    """Context manager for tracking operation performance."""

    def __init__(self, monitoring: MobileMonitoringSystem, component: str, operation: str):
        self.monitoring = monitoring
        self.component = component
        self.operation = operation
        self.timer_key = None

    def __enter__(self):
        self.timer_key = self.monitoring.start_timer(self.component, self.operation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        error_type = exc_type.__name__ if exc_type else None
        self.monitoring.end_timer(self.timer_key, success, error_type)


# Decorator for automatic performance tracking
def track_performance(component: str, operation: str):
    """Decorator for automatic performance tracking."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get monitoring system from session state
            if "mobile_monitoring" not in st.session_state:
                st.session_state.mobile_monitoring = MobileMonitoringSystem()

            monitoring = st.session_state.mobile_monitoring

            with PerformanceTracker(monitoring, component, operation):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Usage tracking decorator
def track_usage(feature: str, interaction: str):
    """Decorator for automatic usage tracking."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get monitoring system from session state
            if "mobile_monitoring" not in st.session_state:
                st.session_state.mobile_monitoring = MobileMonitoringSystem()

            monitoring = st.session_state.mobile_monitoring

            try:
                result = func(*args, **kwargs)
                monitoring.track_usage(feature, interaction, success=True)
                return result
            except Exception as e:
                monitoring.track_usage(feature, interaction, success=False)
                monitoring.track_error(feature, type(e).__name__, str(e))
                raise

        return wrapper

    return decorator


# Initialize monitoring system
def get_monitoring_system() -> MobileMonitoringSystem:
    """Get or create monitoring system instance."""
    if "mobile_monitoring" not in st.session_state:
        st.session_state.mobile_monitoring = MobileMonitoringSystem()
    return st.session_state.mobile_monitoring


# Health check endpoint
def health_check() -> dict[str, Any]:
    """Health check endpoint for monitoring."""
    monitoring = get_monitoring_system()
    return monitoring.get_health_status()
