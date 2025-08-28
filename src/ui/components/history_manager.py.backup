"""History Management System for PlantGuard.

This module provides comprehensive history management including
JSON-based storage, searchable thumbnail grid, export functionality,
and analysis tracking for the PlantGuard plant disease detection system.
"""

import base64
import io
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from PIL import Image

from .analysis_card import AnalysisResult

logger = logging.getLogger(__name__)


class HistoryEntry:
    """Represents a single history entry with analysis and metadata."""

    def __init__(
        self,
        entry_id: str,
        analysis_result: AnalysisResult,
        image_data: str | None = None,
        image_filename: str | None = None,
        tags: list[str] | None = None,
    ):
        """Initialize history entry.

        Args:
            entry_id: Unique identifier for the entry
            analysis_result: AnalysisResult object
            image_data: Base64 encoded image data
            image_filename: Original filename of the image
            tags: List of user-defined tags
        """
        self.entry_id = entry_id
        self.analysis_result = analysis_result
        self.image_data = image_data
        self.image_filename = image_filename
        self.tags = tags or []

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dictionary format for JSON storage."""
        return {
            "entry_id": self.entry_id,
            "analysis_result": self.analysis_result.to_dict()
            if hasattr(self.analysis_result, "to_dict")
            else {
                "prediction": self.analysis_result.prediction,
                "confidence": self.analysis_result.confidence,
                "probabilities": self.analysis_result.probabilities,
                "metadata": self.analysis_result.metadata,
                "timestamp": self.analysis_result.timestamp.isoformat(),
            },
            "image_data": self.image_data,
            "image_filename": self.image_filename,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryEntry":
        """Create entry from dictionary format."""
        # Reconstruct AnalysisResult
        result_data = data["analysis_result"]
        analysis_result = AnalysisResult(
            prediction=result_data["prediction"],
            confidence=result_data["confidence"],
            probabilities=result_data.get("probabilities", {}),
            metadata=result_data.get("metadata", {}),
            timestamp=datetime.fromisoformat(result_data["timestamp"]),
        )

        return cls(
            entry_id=data["entry_id"],
            analysis_result=analysis_result,
            image_data=data.get("image_data"),
            image_filename=data.get("image_filename"),
            tags=data.get("tags", []),
        )

    def get_image(self) -> Image.Image | None:
        """Get PIL Image from stored data."""
        if not self.image_data:
            return None

        try:
            # Decode base64 image data
            image_bytes = base64.b64decode(self.image_data)
            image = Image.open(io.BytesIO(image_bytes))
            return image
        except Exception as e:
            logger.warning(f"Failed to decode image data: {e}")
            return None


class HistoryManager:
    """History management system with JSON storage and search capabilities."""

    def __init__(self, history_file: str = "data/plantguard_history.json"):
        """Initialize history manager.

        Args:
            history_file: Path to JSON history file
        """
        self.history_file = Path(history_file)
        self.max_entries = 1000  # Maximum number of entries to keep
        self.max_image_size = 1024  # Max dimension for stored images

        # Ensure directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize session state
        if "history_entries" not in st.session_state:
            st.session_state.history_entries = self.load_history()
        if "history_search_query" not in st.session_state:
            st.session_state.history_search_query = ""
        if "history_filter_disease" not in st.session_state:
            st.session_state.history_filter_disease = "All"
        if "history_date_range" not in st.session_state:
            st.session_state.history_date_range = "All time"

    def generate_entry_id(self) -> str:
        """Generate unique entry ID."""
        return f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    def encode_image(self, image: Image.Image) -> str:
        """Encode PIL Image to base64 string.

        Args:
            image: PIL Image to encode

        Returns:
            Base64 encoded image string
        """
        try:
            # Resize image if too large
            if max(image.size) > self.max_image_size:
                image = image.copy()
                image.thumbnail((self.max_image_size, self.max_image_size), Image.Resampling.LANCZOS)

            # Convert to bytes
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            image_bytes = buffer.getvalue()

            # Encode to base64
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            return encoded

        except Exception as e:
            logger.warning(f"Failed to encode image: {e}")
            return ""

    def add_entry(
        self,
        analysis_result: AnalysisResult,
        image: Image.Image | None = None,
        image_filename: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Add new entry to history.

        Args:
            analysis_result: AnalysisResult object
            image: PIL Image (optional)
            image_filename: Original filename
            tags: List of tags

        Returns:
            Entry ID
        """
        try:
            entry_id = self.generate_entry_id()

            # Encode image if provided
            image_data = None
            if image:
                image_data = self.encode_image(image)

            # Create entry
            entry = HistoryEntry(
                entry_id=entry_id,
                analysis_result=analysis_result,
                image_data=image_data,
                image_filename=image_filename,
                tags=tags or [],
            )

            # Add to session state
            st.session_state.history_entries.append(entry)

            # Limit number of entries
            if len(st.session_state.history_entries) > self.max_entries:
                st.session_state.history_entries = st.session_state.history_entries[-self.max_entries :]

            # Save to file
            self.save_history()

            logger.info(f"Added history entry: {entry_id}")
            return entry_id

        except Exception as e:
            logger.warning(f"Failed to add history entry: {e}")
            st.toast("Failed to save analysis to history", icon="⚠️")
            return ""

    def load_history(self) -> list[HistoryEntry]:
        """Load history from JSON file.

        Returns:
            List of HistoryEntry objects
        """
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, encoding="utf-8") as f:
                data = json.load(f)

            entries = []
            for entry_data in data.get("entries", []):
                try:
                    entry = HistoryEntry.from_dict(entry_data)
                    entries.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to load history entry: {e}")
                    continue

            logger.info(f"Loaded {len(entries)} history entries")
            return entries

        except Exception as e:
            logger.warning(f"Failed to load history: {e}")
            return []

    def save_history(self) -> None:
        """Save current history to JSON file."""
        try:
            # Prepare data for JSON
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "total_entries": len(st.session_state.history_entries),
                "entries": [entry.to_dict() for entry in st.session_state.history_entries],
            }

            # Write to file
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(st.session_state.history_entries)} entries to history")

        except Exception as e:
            logger.warning(f"Failed to save history: {e}")
            st.toast("Failed to save history to file", icon="⚠️")

    def search_entries(
        self, query: str = "", disease_filter: str = "All", date_range: str = "All time", tags: list[str] | None = None
    ) -> list[HistoryEntry]:
        """Search and filter history entries.

        Args:
            query: Text search query
            disease_filter: Disease type filter
            date_range: Date range filter
            tags: Tag filters

        Returns:
            List of filtered HistoryEntry objects
        """
        entries = st.session_state.history_entries.copy()

        # Text search
        if query:
            query_lower = query.lower()
            filtered_entries = []
            for entry in entries:
                # Search in prediction, filename, and tags
                search_text = f"{entry.analysis_result.prediction} {entry.image_filename or ''} {' '.join(entry.tags)}"
                if query_lower in search_text.lower():
                    filtered_entries.append(entry)
            entries = filtered_entries

        # Disease filter
        if disease_filter != "All":
            entries = [e for e in entries if disease_filter.lower() in e.analysis_result.prediction.lower()]

        # Date range filter
        if date_range != "All time":
            now = datetime.now()
            cutoff_date = now

            if date_range == "Today":
                cutoff_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == "This week":
                cutoff_date = now - timedelta(days=7)
            elif date_range == "This month":
                cutoff_date = now - timedelta(days=30)
            elif date_range == "This year":
                cutoff_date = now - timedelta(days=365)

            entries = [e for e in entries if e.analysis_result.timestamp >= cutoff_date]

        # Tag filter
        if tags:
            entries = [e for e in entries if any(tag in e.tags for tag in tags)]

        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x.analysis_result.timestamp, reverse=True)

        return entries

    def get_disease_types(self) -> list[str]:
        """Get list of unique disease types from history.

        Returns:
            List of disease types
        """
        diseases = set()
        for entry in st.session_state.history_entries:
            diseases.add(entry.analysis_result.prediction)

        return sorted(diseases)

    def get_all_tags(self) -> list[str]:
        """Get list of all unique tags from history.

        Returns:
            List of tags
        """
        tags = set()
        for entry in st.session_state.history_entries:
            tags.update(entry.tags)

        return sorted(tags)

    def delete_entry(self, entry_id: str) -> bool:
        """Delete entry from history.

        Args:
            entry_id: ID of entry to delete

        Returns:
            True if deleted successfully
        """
        try:
            original_count = len(st.session_state.history_entries)
            st.session_state.history_entries = [e for e in st.session_state.history_entries if e.entry_id != entry_id]

            if len(st.session_state.history_entries) < original_count:
                self.save_history()
                logger.info(f"Deleted history entry: {entry_id}")
                return True

            return False

        except Exception as e:
            logger.warning(f"Failed to delete entry: {e}")
            return False

    def clear_history(self) -> None:
        """Clear all history entries."""
        try:
            st.session_state.history_entries = []
            self.save_history()
            logger.info("Cleared all history entries")
            st.toast("History cleared successfully", icon="✅")
        except Exception as e:
            logger.warning(f"Failed to clear history: {e}")
            st.toast("Failed to clear history", icon="⚠️")

    def export_history_csv(self) -> str | None:
        """Export history to CSV format.

        Returns:
            CSV content as string or None if failed
        """
        try:
            if not st.session_state.history_entries:
                st.toast("No history to export", icon="📝")
                return None

            # Prepare data for CSV
            data = []
            for entry in st.session_state.history_entries:
                result = entry.analysis_result
                data.append(
                    {
                        "Entry_ID": entry.entry_id,
                        "Timestamp": result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "Disease_Prediction": result.prediction,
                        "Confidence": f"{result.confidence:.3f}",
                        "Risk_Level": result.get_risk_level(),
                        "Image_Filename": entry.image_filename or "",
                        "Tags": ", ".join(entry.tags),
                        "Metadata": json.dumps(result.metadata) if result.metadata else "",
                    }
                )

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)

            logger.info(f"Exported {len(data)} history entries to CSV")
            return csv_content

        except Exception as e:
            logger.warning(f"CSV export failed: {e}")
            st.toast("Failed to export history to CSV", icon="⚠️")
            return None

    def render_search_interface(self) -> None:
        """Render history search and filter interface."""
        st.subheader("🔍 Search & Filter History")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            search_query = st.text_input(
                "Search history:",
                value=st.session_state.history_search_query,
                placeholder="Search by disease, filename, or tags...",
                key="history_search_input",
            )
            st.session_state.history_search_query = search_query

        with col2:
            disease_types = ["All", *self.get_disease_types()]
            disease_filter = st.selectbox(
                "Disease:",
                disease_types,
                index=disease_types.index(st.session_state.history_filter_disease) if st.session_state.history_filter_disease in disease_types else 0,
                key="history_disease_filter",
            )
            st.session_state.history_filter_disease = disease_filter

        with col3:
            date_options = ["All time", "Today", "This week", "This month", "This year"]
            date_range = st.selectbox(
                "Time period:",
                date_options,
                index=date_options.index(st.session_state.history_date_range) if st.session_state.history_date_range in date_options else 0,
                key="history_date_range_filter",
            )
            st.session_state.history_date_range = date_range

    def render_thumbnail_grid(self, entries: list[HistoryEntry], cols: int = 4) -> None:
        """Render searchable thumbnail grid of history entries.

        Args:
            entries: List of history entries to display
            cols: Number of columns in grid
        """
        if not entries:
            st.info("No history entries found matching your criteria")
            return

        st.subheader(f"📚 History Grid ({len(entries)} entries)")

        # Create grid
        for i in range(0, len(entries), cols):
            row_entries = entries[i : i + cols]
            columns = st.columns(cols)

            for j, entry in enumerate(row_entries):
                with columns[j]:
                    # Get image
                    image = entry.get_image()

                    if image:
                        st.image(image, use_container_width=True)
                    else:
                        # Placeholder for entries without images
                        st.markdown(
                            '<div style="background-color: #f0f0f0; height: 150px; '
                            "display: flex; align-items: center; justify-content: center; "
                            'border-radius: 8px; margin-bottom: 8px;">'
                            '<span style="color: #666;">📊 No Image</span></div>',
                            unsafe_allow_html=True,
                        )

                    # Entry details
                    st.caption(f"**{entry.analysis_result.prediction}**")
                    st.caption(f"Confidence: {entry.analysis_result.confidence:.1%}")
                    st.caption(f"Time: {entry.analysis_result.timestamp.strftime('%m/%d %H:%M')}")

                    # Tags
                    if entry.tags:
                        tag_str = " ".join([f"#{tag}" for tag in entry.tags[:2]])
                        st.caption(f"🏷️ {tag_str}")

                    # Action buttons
                    col_view, col_del = st.columns(2)
                    with col_view:
                        if st.button("👁️", key=f"view_{entry.entry_id}", help="View details"):
                            st.session_state.selected_history_entry = entry

                    with col_del:
                        if st.button("🗑️", key=f"delete_{entry.entry_id}", help="Delete entry"):
                            if self.delete_entry(entry.entry_id):
                                st.toast("Entry deleted", icon="✅")
                                st.rerun()

    def render_history_statistics(self) -> None:
        """Render history statistics and overview."""
        entries = st.session_state.history_entries

        if not entries:
            return

        st.subheader("📊 History Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Analyses", len(entries))

        with col2:
            disease_counts: dict[str, int] = {}
            for entry in entries:
                disease = entry.analysis_result.prediction
                disease_counts[disease] = disease_counts.get(disease, 0) + 1
            most_common = max(disease_counts.items(), key=lambda x: x[1]) if disease_counts else ("None", 0)
            st.metric("Most Common", most_common[0])

        with col3:
            avg_confidence = sum(e.analysis_result.confidence for e in entries) / len(entries)
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")

        with col4:
            # Entries in last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_count = sum(1 for e in entries if e.analysis_result.timestamp >= week_ago)
            st.metric("This Week", recent_count)

    def render_management_controls(self) -> None:
        """Render history management controls."""
        st.subheader("⚙️ History Management")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("📊 Export CSV", help="Export all history to CSV"):
                csv_content = self.export_history_csv()
                if csv_content:
                    st.download_button(
                        "Download History CSV",
                        data=csv_content,
                        file_name=f"plantguard_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )

        with col2:
            if st.button("🔄 Refresh", help="Reload history from file"):
                st.session_state.history_entries = self.load_history()
                st.toast("History refreshed", icon="✅")
                st.rerun()

        with col3:
            if st.button("🗑️ Clear All", help="Delete all history entries"):
                if st.session_state.get("confirm_clear_history", False):
                    self.clear_history()
                    st.session_state.confirm_clear_history = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear_history = True
                    st.warning("Click again to confirm deletion of all history")

    def render_complete_history_interface(self) -> None:
        """Render the complete history management interface."""
        st.header("📚 Analysis History")

        # Check if we have any history
        if not st.session_state.history_entries:
            st.info("""
            📝 **No analysis history yet**

            Your analysis history will appear here after you process plant images.
            History includes:
            - Disease predictions and confidence scores
            - Image thumbnails and metadata
            - Analysis timestamps and trends
            - Export and search capabilities
            """)
            return

        # Statistics overview
        self.render_history_statistics()

        st.markdown("---")

        # Search and filter interface
        self.render_search_interface()

        # Get filtered entries
        filtered_entries = self.search_entries(
            query=st.session_state.history_search_query,
            disease_filter=st.session_state.history_filter_disease,
            date_range=st.session_state.history_date_range,
        )

        st.markdown("---")

        # Thumbnail grid
        self.render_thumbnail_grid(filtered_entries)

        st.markdown("---")

        # Management controls
        self.render_management_controls()


def create_history_manager(history_file: str = "data/plantguard_history.json") -> HistoryManager:
    """Create and return a HistoryManager instance.

    Args:
        history_file: Path to JSON history file

    Returns:
        HistoryManager instance
    """
    return HistoryManager(history_file)


# Example usage and testing
if __name__ == "__main__":
    # Test the history manager
    st.title("📚 PlantGuard History Manager Test")

    # Create history manager
    history_manager = create_history_manager()

    # Render interface
    history_manager.render_complete_history_interface()

    st.markdown("---")
    st.info("This is a test interface. In practice, history entries would be added automatically after analysis.")
