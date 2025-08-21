"""History page for PlantGuard Streamlit app.

This module provides history management with JSON storage, thumbnail grid view,
filtering capabilities, and export functionality for CSV and PDF formats.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


class HistoryManager:
    """History manager class with JSON-based analysis history storage."""

    def __init__(self):
        self.history_file = Path("data/temp/analysis_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def load_history(self) -> list[dict[str, Any]]:
        """Load analysis history from JSON storage."""
        try:
            if self.history_file.exists():
                with open(self.history_file) as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []

    def save_history(self, history: list[dict[str, Any]]) -> None:
        """Save analysis history to JSON storage."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def add_analysis(self, analysis_data: dict[str, Any]) -> None:
        """Add new analysis to history with metadata tracking."""
        history = self.load_history()

        # Add timestamp and metadata
        analysis_data.update(
            {
                "id": f"analysis_{len(history) + 1}",
                "timestamp": datetime.now().isoformat(),
                "model_version": "v1.0",
                "metadata": {
                    "confidence": analysis_data.get("confidence", 0.0),
                    "processing_time": "2.1s",
                    "image_size": "1024x768",
                },
            }
        )

        history.append(analysis_data)
        self.save_history(history)

    def filter_by_date(self, history: list[dict[str, Any]], date_range: tuple) -> list[dict[str, Any]]:
        """Filter history by date range."""
        start_date, end_date = date_range
        filtered = []

        for item in history:
            try:
                item_date = datetime.fromisoformat(item.get("timestamp", ""))
                if start_date <= item_date.date() <= end_date:
                    filtered.append(item)
            except Exception as e:
                logger.warning(f"Invalid timestamp format in history item: {e}")

        return filtered

    def filter_by_model_type(self, history: list[dict[str, Any]], model_type: str) -> list[dict[str, Any]]:
        """Filter history by model type."""
        if model_type == "All":
            return history

        return [item for item in history if item.get("model_type", "ResNet50") == model_type]

    def filter_by_disease_label(self, history: list[dict[str, Any]], disease: str) -> list[dict[str, Any]]:
        """Filter history by disease label."""
        if disease == "All":
            return history

        return [item for item in history if item.get("disease", "").lower() == disease.lower()]

    def search_history(self, history: list[dict[str, Any]], search_term: str) -> list[dict[str, Any]]:
        """Search history with text-based filtering."""
        if not search_term:
            return history

        search_term = search_term.lower()
        filtered = []

        for item in history:
            # Search in disease name, treatment, and metadata
            searchable_text = " ".join([item.get("disease", ""), item.get("treatment", ""), str(item.get("metadata", {}))]).lower()

            if search_term in searchable_text:
                filtered.append(item)

        return filtered

    def export_to_csv(self, history: list[dict[str, Any]]) -> str:
        """Export analysis history to CSV format."""
        df = pd.DataFrame(history)
        return df.to_csv(index=False)

    def export_to_pdf(self, history: list[dict[str, Any]]) -> str:
        """Export analysis history to PDF format (placeholder)."""
        # PDF export would require reportlab or similar
        return "PDF export functionality placeholder"

    def clear_history(self) -> None:
        """Clear all analysis history."""
        self.save_history([])


def render_history_page() -> None:
    """Render the history page with thumbnail grid and filtering."""
    st.title("📚 Analysis History")

    # Initialize HistoryManager
    history_manager = HistoryManager()

    # Load history
    history = history_manager.load_history()

    if not history:
        render_empty_history_guidance()
        return

    # Render filtering controls
    filtered_history = render_history_filters(history, history_manager)

    # Render thumbnail grid view
    render_thumbnail_grid(filtered_history)

    # Render export options
    render_export_options(filtered_history, history_manager)

    # Render management options
    render_history_management(history_manager)


def render_history_filters(history: list[dict[str, Any]], history_manager: HistoryManager) -> list[dict[str, Any]]:
    """Render filtering controls and return filtered history."""
    st.markdown("### 🔍 Filter & Search")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Date filter
        st.markdown("**📅 Date Range**")
        date_options = ["All Time", "Last 7 days", "Last 30 days", "Custom"]
        date_filter = st.selectbox("Date:", date_options, key="date_filter")

        if date_filter == "Custom":
            from datetime import date, timedelta

            start_date = st.date_input("From:", value=date.today() - timedelta(days=30))
            end_date = st.date_input("To:", value=date.today())
            history = history_manager.filter_by_date(history, (start_date, end_date))
        elif date_filter == "Last 7 days":
            from datetime import date, timedelta

            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            history = history_manager.filter_by_date(history, (start_date, end_date))
        elif date_filter == "Last 30 days":
            from datetime import date, timedelta

            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            history = history_manager.filter_by_date(history, (start_date, end_date))

    with col2:
        # Model type filter
        st.markdown("**🤖 Model Type**")
        model_types = ["All", "ResNet50", "VisionTransformer", "EfficientNet"]
        model_filter = st.selectbox("Model:", model_types, key="model_filter")
        history = history_manager.filter_by_model_type(history, model_filter)

    with col3:
        # Disease label filter
        st.markdown("**🦠 Disease Label**")
        # Use a set comprehension and iterable unpacking to avoid unnecessary generator
        diseases = ["All", *sorted({item.get("disease", "") for item in history if item.get("disease")})]
        disease_filter = st.selectbox("Disease:", diseases, key="disease_filter")
        history = history_manager.filter_by_disease_label(history, disease_filter)

    # Text search
    st.markdown("**🔎 Text Search**")
    search_term = st.text_input("Search in results, treatments, or metadata:", key="search_input")
    history = history_manager.search_history(history, search_term)

    st.markdown(f"**Found {len(history)} result(s)**")

    return history


def render_thumbnail_grid(history: list[dict[str, Any]]) -> None:
    """Render searchable thumbnail grid view with progressive loading."""
    st.markdown("### 🖼️ Analysis Results")

    if not history:
        st.info("No results match your filters.")
        return

    # Progressive loading implementation
    items_per_page = 9
    total_pages = (len(history) + items_per_page - 1) // items_per_page

    if total_pages > 1:
        page = st.selectbox("Page:", range(1, total_pages + 1), key="history_page")
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        history_subset = history[start_idx:end_idx]

        st.caption(f"Showing {start_idx + 1}-{min(end_idx, len(history))} of {len(history)} results (progressive loading)")
    else:
        history_subset = history

    # Display in grid format
    cols_per_row = 3

    for i in range(0, len(history_subset), cols_per_row):
        cols = st.columns(cols_per_row)

        for j, analysis in enumerate(history_subset[i : i + cols_per_row]):
            with cols[j]:
                render_analysis_thumbnail(analysis, start_idx + i + j if "start_idx" in locals() else i + j)


def render_analysis_thumbnail(analysis: dict[str, Any], index: int) -> None:
    """Render individual analysis thumbnail."""
    with st.container():
        # Thumbnail placeholder (would be actual image thumbnail in real implementation)
        st.markdown(
            """
            <div style='
                background: linear-gradient(135deg, #22C55E, #16A34A);
                height: 120px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 2rem;
                margin-bottom: 0.5rem;
            '>
                🌿
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Analysis details
        disease = analysis.get("disease", "Unknown")
        confidence = analysis.get("confidence", 0.0)
        timestamp = analysis.get("timestamp", "")[:10]  # Date only

        st.markdown(f"**{disease}**")
        st.progress(confidence)
        st.caption(f"📊 {confidence:.1%} confidence")
        st.caption(f"📅 {timestamp}")

        # View details button
        if st.button("👁️ View", key=f"view_analysis_{index}", use_container_width=True):
            show_analysis_details(analysis)


def render_export_options(history: list[dict[str, Any]], history_manager: HistoryManager) -> None:
    """Render CSV and PDF export functionality."""
    if not history:
        return

    st.markdown("### 📥 Export Options")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Export as CSV", use_container_width=True):
            csv_data = history_manager.export_to_csv(history)
            st.download_button(
                "📥 Download CSV",
                data=csv_data,
                file_name=f"plantguard_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

    with col2:
        if st.button("📄 Export as PDF", use_container_width=True):
            pdf_data = history_manager.export_to_pdf(history)
            st.download_button(
                "📥 Download PDF",
                data=pdf_data,
                file_name=f"plantguard_history_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
            )


def render_history_management(history_manager: HistoryManager) -> None:
    """Render history clearing and selective deletion options."""
    st.markdown("### 🗑️ History Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear All History", type="secondary", use_container_width=True):
            if st.button("⚠️ Confirm Clear All", type="primary", key="confirm_clear"):
                history_manager.clear_history()
                st.success("✅ History cleared!")
                st.rerun()

    with col2:
        st.markdown("**Selective Deletion**")
        st.info("Select items above and use 'Delete Selected' (coming soon)")


def render_empty_history_guidance() -> None:
    """Render guidance display for users with no analysis history."""
    st.markdown(
        """
        <div class='empty-state'>
            <div class='empty-state-icon'>📚</div>
            <h3 class='empty-state-title'>No Analysis History Yet</h3>
            <p class='empty-state-description'>
                Your analysis results will appear here after you start using PlantGuard.
            </p>
            <p class='empty-state-hint'>
                💡 Visit the Home page to analyze your first plant image!
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_analysis_details(analysis: dict[str, Any]) -> None:
    """Show detailed analysis results in modal or expander."""
    with st.expander("🔬 Detailed Analysis", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Analysis Results:**")
            st.json(
                {
                    "disease": analysis.get("disease"),
                    "confidence": analysis.get("confidence"),
                    "treatment": analysis.get("treatment"),
                }
            )

        with col2:
            st.markdown("**Metadata:**")
            st.json(analysis.get("metadata", {}))


def create_sample_history() -> list[dict[str, Any]]:
    """Create sample history for testing."""
    return [
        {
            "id": "analysis_1",
            "disease": "Healthy Plant",
            "confidence": 0.92,
            "timestamp": "2025-01-27T10:30:00",
            "treatment": "Continue regular care",
            "model_version": "v1.0",
            "metadata": {"processing_time": "1.8s", "image_size": "1024x768"},
        },
        {
            "id": "analysis_2",
            "disease": "Leaf Spot",
            "confidence": 0.78,
            "timestamp": "2025-01-26T14:15:00",
            "treatment": "Apply fungicide spray",
            "model_version": "v1.0",
            "metadata": {"processing_time": "2.3s", "image_size": "800x600"},
        },
    ]


if __name__ == "__main__":
    # Local run for manual testing
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = create_sample_history()
    render_history_page()
