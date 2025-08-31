"""
Mobile History View Component for PlantGuard UI.

This module provides a mobile-optimized history view component with
scrollable history list, filtering, search functionality, and history
item actions (view, delete, share) optimized for touch interaction.
"""

import contextlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import streamlit as st
from PIL import Image

from .mobile_state_manager import MobileStateManager

logger = logging.getLogger(__name__)


class MobileHistoryView:
    """Mobile-optimized history view component."""

    def __init__(self, component_id: str, title: str = "Analysis History") -> None:
        """Initialize mobile history view component.

        Args:
            component_id: Unique identifier for the component
            title: Display title for the component
        """
        self.component_id = component_id
        self.title = title
        self.state_manager = MobileStateManager()
        self._initialize_history_state()

    def _initialize_history_state(self) -> None:
        """Initialize history-specific state."""
        # Initialize analysis history if not exists
        if "analysis_history" not in st.session_state:
            st.session_state.analysis_history = []

        # Initialize history view state
        state = self.state_manager.get_component_state(self.component_id)
        if "history_view" not in state["data"]:
            state["data"]["history_view"] = {
                "search_query": "",
                "filter_disease": "All",
                "filter_date": "All time",
                "sort_order": "newest_first",
                "selected_items": [],
                "view_mode": "cards",  # 'cards' or 'list'
                "items_per_page": 10,
                "current_page": 1,
            }
            self.state_manager.set_component_state(self.component_id, state)

    def get_mobile_css(self) -> str:
        """Get mobile-specific CSS for history view."""
        return """
        <style>
        .mobile-history-view {
            padding: 0;
            margin: 0;
        }

        .mobile-history-search {
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .mobile-history-filters {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            overflow-x: auto;
            padding-bottom: 8px;
        }

        .mobile-filter-chip {
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 14px;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .mobile-filter-chip.active {
            background: #0ea5e9;
            color: white;
        }

        .mobile-history-card {
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #16a34a;
            position: relative;
        }

        .mobile-history-card.error {
            border-left-color: #dc2626;
        }

        .mobile-history-card.warning {
            border-left-color: #f59e0b;
        }

        .mobile-history-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }

        .mobile-history-disease {
            font-weight: 600;
            font-size: 16px;
            color: #1f2937;
            margin: 0;
        }

        .mobile-history-confidence {
            font-size: 14px;
            color: #6b7280;
            margin: 4px 0;
        }

        .mobile-history-timestamp {
            font-size: 12px;
            color: #9ca3af;
            text-align: right;
        }

        .mobile-history-image {
            width: 60px;
            height: 60px;
            border-radius: 8px;
            object-fit: cover;
            margin-right: 12px;
            float: left;
        }

        .mobile-history-content {
            overflow: hidden;
        }

        .mobile-history-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e5e7eb;
        }

        .mobile-history-action-btn {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            background: white;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }

        .mobile-history-action-btn:hover {
            background: #f9fafb;
            border-color: #9ca3af;
        }

        .mobile-history-action-btn.primary {
            background: #16a34a;
            color: white;
            border-color: #16a34a;
        }

        .mobile-history-action-btn.danger {
            background: #dc2626;
            color: white;
            border-color: #dc2626;
        }

        .mobile-history-empty {
            text-align: center;
            padding: 40px 20px;
            color: #6b7280;
        }

        .mobile-history-empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }

        .mobile-history-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }

        .mobile-history-stat {
            background: white;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .mobile-history-stat-value {
            font-size: 18px;
            font-weight: 600;
            color: #1f2937;
            margin: 0;
        }

        .mobile-history-stat-label {
            font-size: 12px;
            color: #6b7280;
            margin: 4px 0 0 0;
        }

        .mobile-history-pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-top: 20px;
            padding: 16px;
        }

        .mobile-history-page-btn {
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            background: white;
            cursor: pointer;
            min-width: 44px;
            text-align: center;
        }

        .mobile-history-page-btn.active {
            background: #16a34a;
            color: white;
            border-color: #16a34a;
        }

        .mobile-history-page-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        @media (max-width: 480px) {
            .mobile-history-card {
                padding: 12px;
                margin-bottom: 8px;
            }

            .mobile-history-image {
                width: 50px;
                height: 50px;
            }

            .mobile-history-actions {
                flex-direction: column;
            }

            .mobile-history-action-btn {
                margin-bottom: 4px;
            }
        }
        </style>
        """

    def get_analysis_history(self) -> list[dict[str, Any]]:
        """Get analysis history from session state."""
        return st.session_state.get("analysis_history", [])

    def filter_history(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter history based on current filters."""
        state = self.state_manager.get_component_state(self.component_id)
        filters = state["data"]["history_view"]

        filtered = history.copy()

        # Search filter
        if filters["search_query"]:
            query = filters["search_query"].lower()
            filtered = [
                item
                for item in filtered
                if query in item.get("prediction", "").lower()
                or query in item.get("source", "").lower()
                or query in str(item.get("metadata", {})).lower()
            ]

        # Disease filter
        if filters["filter_disease"] != "All":
            filtered = [item for item in filtered if filters["filter_disease"].lower() in item.get("prediction", "").lower()]

        # Date filter
        if filters["filter_date"] != "All time":
            now = datetime.now()
            cutoff_date = now

            if filters["filter_date"] == "Today":
                cutoff_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif filters["filter_date"] == "This week":
                cutoff_date = now - timedelta(days=7)
            elif filters["filter_date"] == "This month":
                cutoff_date = now - timedelta(days=30)

            filtered = [item for item in filtered if datetime.fromisoformat(item.get("timestamp", now.isoformat())) >= cutoff_date]

        # Sort
        if filters["sort_order"] == "newest_first":
            filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        elif filters["sort_order"] == "oldest_first":
            filtered.sort(key=lambda x: x.get("timestamp", ""))
        elif filters["sort_order"] == "confidence_high":
            filtered.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        elif filters["sort_order"] == "confidence_low":
            filtered.sort(key=lambda x: x.get("confidence", 0))

        return filtered

    def get_unique_diseases(self, history: list[dict[str, Any]]) -> list[str]:
        """Get unique disease types from history."""
        diseases = set()
        for item in history:
            if "prediction" in item:
                diseases.add(item["prediction"])
        return sorted(diseases)

    def render_search_interface(self) -> None:
        """Render search and filter interface."""
        state = self.state_manager.get_component_state(self.component_id)
        filters = state["data"]["history_view"]

        with st.container():
            st.markdown('<div class="mobile-history-search">', unsafe_allow_html=True)

            # Search input
            search_query = st.text_input(
                "Search history",
                value=filters["search_query"],
                placeholder="Search by disease, source, or details...",
                key=f"{self.component_id}_search",
                label_visibility="collapsed",
            )

            if search_query != filters["search_query"]:
                filters["search_query"] = search_query
                state["data"]["history_view"] = filters
                self.state_manager.set_component_state(self.component_id, state)

            st.markdown("</div>", unsafe_allow_html=True)

    def render_filter_chips(self) -> None:
        """Render filter chips for quick filtering."""
        state = self.state_manager.get_component_state(self.component_id)
        filters = state["data"]["history_view"]
        history = self.get_analysis_history()

        st.markdown('<div class="mobile-history-filters">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            # Disease filter
            diseases = ["All", *self.get_unique_diseases(history)]
            disease_filter = st.selectbox(
                "Disease",
                diseases,
                index=diseases.index(filters["filter_disease"]) if filters["filter_disease"] in diseases else 0,
                key=f"{self.component_id}_disease_filter",
            )

            if disease_filter != filters["filter_disease"]:
                filters["filter_disease"] = disease_filter
                state["data"]["history_view"] = filters
                self.state_manager.set_component_state(self.component_id, state)

        with col2:
            # Date filter
            date_options = ["All time", "Today", "This week", "This month"]
            date_filter = st.selectbox(
                "Time",
                date_options,
                index=date_options.index(filters["filter_date"]) if filters["filter_date"] in date_options else 0,
                key=f"{self.component_id}_date_filter",
            )

            if date_filter != filters["filter_date"]:
                filters["filter_date"] = date_filter
                state["data"]["history_view"] = filters
                self.state_manager.set_component_state(self.component_id, state)

        with col3:
            # Sort order
            sort_options = ["newest_first", "oldest_first", "confidence_high", "confidence_low"]
            sort_labels = ["Newest First", "Oldest First", "High Confidence", "Low Confidence"]
            sort_index = sort_options.index(filters["sort_order"]) if filters["sort_order"] in sort_options else 0

            sort_order = st.selectbox(
                "Sort",
                sort_options,
                format_func=lambda x: sort_labels[sort_options.index(x)],
                index=sort_index,
                key=f"{self.component_id}_sort_order",
            )

            if sort_order != filters["sort_order"]:
                filters["sort_order"] = sort_order
                state["data"]["history_view"] = filters
                self.state_manager.set_component_state(self.component_id, state)

        st.markdown("</div>", unsafe_allow_html=True)

    def render_history_stats(self, history: list[dict[str, Any]]) -> None:
        """Render history statistics."""
        if not history:
            return

        st.markdown('<div class="mobile-history-stats">', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                f"""
            <div class="mobile-history-stat">
                <div class="mobile-history-stat-value">{len(history)}</div>
                <div class="mobile-history-stat-label">Total</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            # Most common disease
            diseases = {}
            for item in history:
                disease = item.get("prediction", "Unknown")
                diseases[disease] = diseases.get(disease, 0) + 1
            most_common = max(diseases.items(), key=lambda x: x[1])[0] if diseases else "None"
            most_common_short = most_common[:8] + "..." if len(most_common) > 8 else most_common

            st.markdown(
                f"""
            <div class="mobile-history-stat">
                <div class="mobile-history-stat-value">{most_common_short}</div>
                <div class="mobile-history-stat-label">Common</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            # Average confidence
            confidences = [item.get("confidence", 0) for item in history if "confidence" in item]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            st.markdown(
                f"""
            <div class="mobile-history-stat">
                <div class="mobile-history-stat-value">{avg_confidence:.0%}</div>
                <div class="mobile-history-stat-label">Avg Conf</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col4:
            # Recent analyses (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_count = sum(1 for item in history if datetime.fromisoformat(item.get("timestamp", datetime.now().isoformat())) >= week_ago)

            st.markdown(
                f"""
            <div class="mobile-history-stat">
                <div class="mobile-history-stat-value">{recent_count}</div>
                <div class="mobile-history-stat-label">This Week</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    def render_history_card(self, item: dict[str, Any], index: int) -> None:
        """Render individual history card."""
        # Determine card class based on confidence
        confidence = item.get("confidence", 0)
        card_class = "mobile-history-card"
        if confidence < 0.5:
            card_class += " error"
        elif confidence < 0.7:
            card_class += " warning"

        # Format timestamp
        timestamp = item.get("timestamp", datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%m/%d %H:%M")
        except Exception:
            time_str = "Unknown"

        # Get prediction and confidence
        prediction = item.get("prediction", "Unknown Disease")
        confidence_pct = f"{confidence:.1%}" if confidence else "N/A"
        source = item.get("source", "unknown")

        st.markdown(
            f'''
        <div class="{card_class}">
            <div class="mobile-history-header">
                <div>
                    <div class="mobile-history-disease">{prediction}</div>
                    <div class="mobile-history-confidence">Confidence: {confidence_pct}</div>
                    <div class="mobile-history-confidence">Source: {source}</div>
                </div>
                <div class="mobile-history-timestamp">{time_str}</div>
            </div>
        </div>
        ''',
            unsafe_allow_html=True,
        )

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("[VISION] View", key=f"{self.component_id}_view_{index}", use_container_width=True):
                self._handle_view_item(item, index)

        with col2:
            if st.button("[UPLOAD] Share", key=f"{self.component_id}_share_{index}", use_container_width=True):
                self._handle_share_item(item, index)

        with col3:
            if st.button("[DELETE] Delete", key=f"{self.component_id}_delete_{index}", use_container_width=True):
                self._handle_delete_item(item, index)

    def render_empty_state(self) -> None:
        """Render empty state when no history is available."""
        st.markdown(
            """
        <div class="mobile-history-empty">
            <div class="mobile-history-empty-icon">[SUMMARY]</div>
            <h3>No Analysis History</h3>
            <p>Your plant analysis history will appear here after you analyze some plants.</p>
            <p>Try uploading an image or using the camera to get started!</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_pagination(self, total_items: int) -> None:
        """Render pagination controls."""
        state = self.state_manager.get_component_state(self.component_id)
        filters = state["data"]["history_view"]

        items_per_page = filters["items_per_page"]
        current_page = filters["current_page"]
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

        if total_pages <= 1:
            return

        st.markdown('<div class="mobile-history-pagination">', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if st.button("⏮️", key=f"{self.component_id}_first_page", disabled=current_page <= 1):
                filters["current_page"] = 1
                state["data"]["history_view"] = filters
                self.state_manager.set_component_state(self.component_id, state)

        with col2:
            if st.button("◀️", key=f"{self.component_id}_prev_page", disabled=current_page <= 1):
                filters["current_page"] = max(1, current_page - 1)
                state["data"]["history_view"] = filters
                self.state_manager.set_component_state(self.component_id, state)

        with col3:
            st.markdown(f'<div style="text-align: center; padding: 8px;">Page {current_page} of {total_pages}</div>', unsafe_allow_html=True)

        with col4:
            if st.button("▶️", key=f"{self.component_id}_next_page", disabled=current_page >= total_pages):
                filters["current_page"] = min(total_pages, current_page + 1)
                state["data"]["history_view"] = filters
                self.state_manager.set_component_state(self.component_id, state)

        with col5:
            if st.button("⏭️", key=f"{self.component_id}_last_page", disabled=current_page >= total_pages):
                filters["current_page"] = total_pages
                state["data"]["history_view"] = filters
                self.state_manager.set_component_state(self.component_id, state)

        st.markdown("</div>", unsafe_allow_html=True)

    def _handle_view_item(self, item: dict[str, Any], index: int) -> None:
        """Handle viewing a history item."""
        # Store selected item in session state for detailed view
        st.session_state[f"{self.component_id}_selected_item"] = item
        st.session_state[f"{self.component_id}_view_mode"] = "detail"

        # Show item details in expandable section
        with st.expander(f"[SUMMARY] Analysis Details - {item.get('prediction', 'Unknown')}", expanded=True):
            col1, col2 = st.columns([1, 1])

            with col1:
                st.write("**Prediction:**", item.get("prediction", "Unknown"))
                st.write("**Confidence:**", f"{item.get('confidence', 0):.1%}")
                st.write("**Source:**", item.get("source", "unknown"))

            with col2:
                timestamp = item.get("timestamp", datetime.now().isoformat())
                try:
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    formatted_time = "Unknown"
                st.write("**Timestamp:**", formatted_time)

            # Show metadata if available
            if item.get("metadata"):
                st.write("**Metadata:**")
                st.json(item["metadata"])

            # Show image if available
            if item.get("image"):
                st.write("**Image:**")
                try:
                    if isinstance(item["image"], str):
                        # Assume it's a base64 encoded image
                        import base64
                        import io

                        image_data = base64.b64decode(item["image"])
                        image = Image.open(io.BytesIO(image_data))
                        st.image(image, use_container_width=True)
                    elif hasattr(item["image"], "show"):
                        # PIL Image object
                        st.image(item["image"], use_container_width=True)
                except Exception as e:
                    st.error(f"Could not display image: {e}")

        st.toast(f"Viewing analysis: {item.get('prediction', 'Unknown')}", icon="[VISION]")

    def _handle_share_item(self, item: dict[str, Any], index: int) -> None:
        """Handle sharing a history item."""
        # Create shareable text
        prediction = item.get("prediction", "Unknown Disease")
        confidence = item.get("confidence", 0)
        timestamp = item.get("timestamp", datetime.now().isoformat())

        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            formatted_time = "Unknown time"

        share_text = f"""[LEAF] PlantGuard Analysis Result

Disease: {prediction}
Confidence: {confidence:.1%}
Analyzed: {formatted_time}

Generated by PlantGuard Mobile App"""

        # Show share options
        with st.expander(f"[UPLOAD] Share Analysis - {prediction}", expanded=True):
            st.text_area("Share this analysis:", value=share_text, height=150, key=f"{self.component_id}_share_text_{index}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("[DETAILS] Copy to Clipboard", key=f"{self.component_id}_copy_{index}", use_container_width=True):
                    # Note: Actual clipboard functionality would require JavaScript
                    st.toast("Text ready to copy!", icon="[DETAILS]")

            with col2:
                # Create downloadable JSON
                json_data = json.dumps(item, indent=2, default=str)
                st.download_button(
                    "[SAVE] Download JSON",
                    data=json_data,
                    file_name=f"plantguard_analysis_{formatted_time.replace(':', '-')}.json",
                    mime="application/json",
                    key=f"{self.component_id}_download_{index}",
                    use_container_width=True,
                )

        st.toast(f"Sharing options for: {prediction}", icon="[UPLOAD]")

    def _handle_delete_item(self, item: dict[str, Any], index: int) -> None:
        """Handle deleting a history item."""
        prediction = item.get("prediction", "Unknown")

        # Confirm deletion
        confirm_key = f"{self.component_id}_confirm_delete_{index}"
        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False

        if not st.session_state[confirm_key]:
            st.session_state[confirm_key] = True
            st.warning(f"Are you sure you want to delete the analysis for '{prediction}'?")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("[DONE] Yes, Delete", key=f"{self.component_id}_confirm_yes_{index}", use_container_width=True):
                    # Remove item from history
                    history = st.session_state.get("analysis_history", [])
                    if index < len(history):
                        removed_item = history.pop(index)
                        st.session_state.analysis_history = history
                        st.toast(f"Deleted analysis: {removed_item.get('prediction', 'Unknown')}", icon="[DELETE]")
                        st.session_state[confirm_key] = False

            with col2:
                if st.button("[TODO] Cancel", key=f"{self.component_id}_confirm_no_{index}", use_container_width=True):
                    st.session_state[confirm_key] = False

    def render(self) -> None:
        """Render the mobile history view component."""
        try:
            # Apply mobile CSS
            st.markdown(self.get_mobile_css(), unsafe_allow_html=True)

            # Main container
            with st.container():
                st.markdown('<div class="mobile-history-view">', unsafe_allow_html=True)

                # Component header
                st.markdown(f"### [LIBRARY] {self.title}")

                # Clear history
                if st.button("Clear History", key=f"{self.component_id}_clear_history", use_container_width=True):
                    st.session_state.analysis_history = []
                    # Update state without page refresh
                    st.session_state.history_cleared = True

                # Get history data
                history = self.get_analysis_history()

                if not history:
                    self.render_empty_state()
                    st.markdown("</div>", unsafe_allow_html=True)
                    return

                # Render statistics
                self.render_history_stats(history)

                # Render search interface
                self.render_search_interface()

                # Render filter chips
                self.render_filter_chips()

                # Filter and paginate history
                filtered_history = self.filter_history(history)

                if not filtered_history:
                    st.info("No history items match your current filters.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return

                # Pagination
                state = self.state_manager.get_component_state(self.component_id)
                filters = state["data"]["history_view"]
                items_per_page = filters["items_per_page"]
                current_page = filters["current_page"]

                start_idx = (current_page - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_items = filtered_history[start_idx:end_idx]

                # Render history cards
                for i, item in enumerate(page_items):
                    self.render_history_card(item, start_idx + i)

                # Render pagination controls
                self.render_pagination(len(filtered_history))

                st.markdown("</div>", unsafe_allow_html=True)

                # Update component state
                state = self.state_manager.get_component_state(self.component_id)
                state["ui_state"]["loading"] = False
                state["error"] = None
                self.state_manager.set_component_state(self.component_id, state)

        except Exception as e:
            logger.error(f"Error rendering mobile history view: {e}")
            self.state_manager.set_error_state(
                self.component_id, str(e), "rendering_error", ["Check browser console", "Refresh the page", "Clear browser cache"]
            )
            st.error(f"Error displaying history: {e}")

    def clear_history(self) -> None:
        """Clear all analysis history."""
        st.session_state.analysis_history = []
        st.toast("History cleared successfully", icon="[DELETE]")

    def export_history_json(self) -> str:
        """Export history as JSON string."""
        history = self.get_analysis_history()
        return json.dumps(history, indent=2, default=str)

    def get_history_summary(self) -> dict[str, Any]:
        """Get summary statistics of history."""
        history = self.get_analysis_history()

        if not history:
            return {"total_analyses": 0, "unique_diseases": 0, "average_confidence": 0, "most_common_disease": None, "date_range": None}

        # Calculate statistics
        diseases = {}
        confidences = []
        timestamps = []

        for item in history:
            # Count diseases
            disease = item.get("prediction", "Unknown")
            diseases[disease] = diseases.get(disease, 0) + 1

            # Collect confidences
            if "confidence" in item:
                confidences.append(item["confidence"])

            # Collect timestamps
            if "timestamp" in item:
                with contextlib.suppress(Exception):
                    timestamps.append(datetime.fromisoformat(item["timestamp"]))

        most_common_disease = max(diseases.items(), key=lambda x: x[1])[0] if diseases else None
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        date_range = None
        if timestamps:
            timestamps.sort()
            date_range = {"earliest": timestamps[0].isoformat(), "latest": timestamps[-1].isoformat()}

        return {
            "total_analyses": len(history),
            "unique_diseases": len(diseases),
            "average_confidence": avg_confidence,
            "most_common_disease": most_common_disease,
            "date_range": date_range,
            "disease_counts": diseases,
        }
