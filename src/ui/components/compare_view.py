from typing import Any, Dict, List, Optional, Tuple, Union, Generator
"""Compare View Implementation for PlantGuard.

This module provides comprehensive comparison capabilities including
A/B image viewer, side-by-side analysis comparison, difference highlighting,
and comparative metrics for the PlantGuard plant disease detection system.
"""


import logging
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from .analysis_card import AnalysisResult

logger = logging.getLogger(__name__)


class ComparisonResult:
    """Represents a comparison between two analysis results."""

    def __init__(
        self,
        result_a: AnalysisResult,
        result_b: AnalysisResult,
        image_a: Image.Image | None = None,
        image_b: Image.Image | None = None,
        comparison_type: str = "disease_comparison",
    ):
        """Initialize comparison result.

        Args:
            result_a: First analysis result
            result_b: Second analysis result
            image_a: First image
            image_b: Second image
            comparison_type: Type of comparison being performed
        """
        self.result_a = result_a
        self.result_b = result_b
        self.image_a = image_a
        self.image_b = image_b
        self.comparison_type = comparison_type
        self.timestamp = datetime.now()

    def get_confidence_delta(self) -> float:
        """Get confidence difference between results.

        Returns:
            Confidence delta (result_b - result_a)
        """
        return self.result_b.confidence - self.result_a.confidence

    def get_risk_change(self) -> str:
        """Get risk level change description.

        Returns:
            Risk change description
        """
        risk_a = self.result_a.get_risk_level()
        risk_b = self.result_b.get_risk_level()

        if risk_a == risk_b:
            return "No change"

        risk_order = {"low": 0, "medium": 1, "high": 2}

        if risk_order[risk_b] > risk_order[risk_a]:
            return f"Increased from {risk_a} to {risk_b}"
        else:
            return f"Decreased from {risk_a} to {risk_b}"

    def get_disease_match(self) -> bool:
        """Check if both results predict the same disease.

        Returns:
            True if diseases match
        """
        return self.result_a.prediction.lower() == self.result_b.prediction.lower()


class CompareView:
    """Compare view component for A/B analysis comparison."""

    def __init__(self) -> None:
        """Initialize compare view."""
        # Initialize session state
        if "comparison_images" not in st.session_state:
            st.session_state.comparison_images = [None, None]
        if "comparison_results" not in st.session_state:
            st.session_state.comparison_results = [None, None]
        if "comparison_sync_zoom" not in st.session_state:
            st.session_state.comparison_sync_zoom = True

    def render_image_selector(self, slot: int, available_images: list[Image.Image], available_results: list[AnalysisResult]) -> None:
        """Render image selector for comparison slot.

        Args:
            slot: Comparison slot (0 or 1)
            available_images: List of available images
            available_results: List of available analysis results
        """
        slot_label = "A" if slot == 0 else "B"

        st.subheader(f"[IMAGE] Image {slot_label}")

        if not available_images:
            st.info("No images available for comparison")
            return

        # Image selection
        image_options = [f"Image {i + 1}" for i in range(len(available_images))]
        selected_index = st.selectbox(
            f"Select image for slot {slot_label}:",
            range(len(available_images)),
            format_func=lambda x: image_options[x],
            key=f"image_selector_{slot}",
        )

        if selected_index is not None:
            st.session_state.comparison_images[slot] = available_images[selected_index]
            if selected_index < len(available_results):
                st.session_state.comparison_results[slot] = available_results[selected_index]

        # Display selected image
        if st.session_state.comparison_images[slot]:
            image = st.session_state.comparison_images[slot]
            st.image(image, caption=f"Image {slot_label}", use_container_width=True)

            # Image info
            st.caption(f"Size: {image.width}x{image.height}")

    def render_synchronized_viewer(self) -> None:
        """Render synchronized A/B image viewer."""
        if not all(st.session_state.comparison_images):
            st.info("Select images for both slots to enable synchronized viewing")
            return

        st.subheader("[SEARCH] Synchronized Viewer")

        # Sync controls
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            sync_zoom = st.checkbox("Sync zoom", value=st.session_state.comparison_sync_zoom)
            st.session_state.comparison_sync_zoom = sync_zoom

        with col2:
            zoom_level = st.slider("Zoom", 0.5, 3.0, 1.0, 0.1, key="sync_zoom")

        with col3:
            if st.button("[PARTIAL] Swap Images"):
                st.session_state.comparison_images.reverse()
                st.session_state.comparison_results.reverse()
                st.rerun()

        # Side-by-side display
        col1, col2 = st.columns(2)

        for i, col in enumerate([col1, col2]):
            with col:
                image = st.session_state.comparison_images[i]

                if sync_zoom and zoom_level != 1.0:
                    # Apply zoom
                    new_size = (int(image.width * zoom_level), int(image.height * zoom_level))
                    zoomed_image = image.resize(new_size, Image.Resampling.LANCZOS)
                    st.image(
                        zoomed_image,
                        caption=f"Image {'A' if i == 0 else 'B'} (Zoom: {zoom_level}x)",
                        use_container_width=True,
                    )
                else:
                    st.image(image, caption=f"Image {'A' if i == 0 else 'B'}", use_container_width=True)

    def render_difference_analysis(self) -> None:
        """Render difference analysis between images."""
        if not all(st.session_state.comparison_images):
            return

        st.subheader("[SUMMARY] Image Difference Analysis")

        try:
            image_a = st.session_state.comparison_images[0]
            image_b = st.session_state.comparison_images[1]

            # Resize images to same size for comparison
            min_width = min(image_a.width, image_b.width)
            min_height = min(image_a.height, image_b.height)

            img_a_resized = image_a.resize((min_width, min_height), Image.Resampling.LANCZOS)
            img_b_resized = image_b.resize((min_width, min_height), Image.Resampling.LANCZOS)

            # Convert to numpy arrays
            arr_a = np.array(img_a_resized)
            arr_b = np.array(img_b_resized)

            # Calculate difference
            diff = np.abs(arr_a.astype(float) - arr_b.astype(float))
            diff_normalized = (diff / diff.max() * 255).astype(np.uint8)

            # Create difference image
            diff_image = Image.fromarray(diff_normalized)

            # Display difference
            col1, col2 = st.columns([2, 1])

            with col1:
                st.image(diff_image, caption="Difference Heatmap", use_container_width=True)

            with col2:
                # Difference statistics
                total_pixels = diff.size
                changed_pixels = np.count_nonzero(diff)
                change_percentage = (changed_pixels / total_pixels) * 100

                st.metric("Changed Pixels", f"{change_percentage:.1f}%")
                st.metric("Avg Difference", f"{diff.mean():.1f}")
                st.metric("Max Difference", f"{diff.max():.1f}")

        except Exception as e:
            logger.warning(f"Difference analysis failed: {e}")
            st.error("Failed to perform difference analysis")

    def render_comparative_metrics(self) -> None:
        """Render comparative metrics table."""
        if not all(st.session_state.comparison_results):
            st.info("Analysis results needed for comparative metrics")
            return

        st.subheader("[CHART] Comparative Analysis Metrics")

        result_a = st.session_state.comparison_results[0]
        result_b = st.session_state.comparison_results[1]

        # Create comparison data
        comparison_data = {
            "Metric": ["Disease Prediction", "Confidence", "Risk Level", "Analysis Time"],
            "Image A": [
                result_a.prediction,
                f"{result_a.confidence:.1%}",
                result_a.get_risk_level().title(),
                result_a.timestamp.strftime("%H:%M:%S"),
            ],
            "Image B": [
                result_b.prediction,
                f"{result_b.confidence:.1%}",
                result_b.get_risk_level().title(),
                result_b.timestamp.strftime("%H:%M:%S"),
            ],
            "Difference": [
                "[DONE] Match" if result_a.prediction.lower() == result_b.prediction.lower() else "[TODO] Different",
                f"{(result_b.confidence - result_a.confidence):+.1%}",
                ComparisonResult(result_a, result_b).get_risk_change(),
                f"{abs((result_b.timestamp - result_a.timestamp).total_seconds()):.1f}s apart",
            ],
        }

        df = pd.DataFrame(comparison_data)

        # Style the dataframe
        styled_df = df.style.apply(
            lambda x: ["background-color: #e8f5e8" if "[DONE]" in str(val) else "background-color: #ffe8e8" if "[TODO]" in str(val) else "" for val in x],
            subset=["Difference"],
        )

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    def render_probability_comparison(self) -> None:
        """Render probability comparison chart."""
        if not all(st.session_state.comparison_results):
            return

        result_a = st.session_state.comparison_results[0]
        result_b = st.session_state.comparison_results[1]

        if not (result_a.probabilities and result_b.probabilities):
            st.info("Detailed probability data not available for comparison")
            return

        st.subheader("[SUMMARY] Probability Comparison")

        # Get all unique diseases
        all_diseases = set(result_a.probabilities.keys()) | set(result_b.probabilities.keys())

        # Create comparison data
        comparison_data = []
        for disease in all_diseases:
            prob_a = result_a.probabilities.get(disease, 0)
            prob_b = result_b.probabilities.get(disease, 0)

            comparison_data.append(
                {
                    "Disease": disease,
                    "Image A": prob_a * 100,
                    "Image B": prob_b * 100,
                    "Difference": (prob_b - prob_a) * 100,
                }
            )

        # Sort by average probability
        comparison_data.sort(key=lambda x: (x["Image A"] + x["Image B"]) / 2, reverse=True)

        # Take top 10
        comparison_data = comparison_data[:10]

        df = pd.DataFrame(comparison_data)

        # Create grouped bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(name="Image A", x=df["Disease"], y=df["Image A"], marker_color="#1f77b4"))

        fig.add_trace(go.Bar(name="Image B", x=df["Disease"], y=df["Image B"], marker_color="#ff7f0e"))

        fig.update_layout(
            title="Disease Probability Comparison",
            xaxis_title="Disease",
            yaxis_title="Confidence (%)",
            barmode="group",
            height=400,
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
        )

        # Rotate x-axis labels for readability
        fig.update_xaxes(tickangle=45)

        st.plotly_chart(fig, use_container_width=True)

    def render_comparison_export(self) -> None:
        """Render comparison export functionality."""
        if not all(st.session_state.comparison_results):
            return

        st.subheader("[UPLOAD] Export Comparison")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("[SUMMARY] Export as CSV"):
                # Create comparison report
                result_a = st.session_state.comparison_results[0]
                result_b = st.session_state.comparison_results[1]

                report_data = {
                    "Comparison_Timestamp": [datetime.now().isoformat()],
                    "Image_A_Prediction": [result_a.prediction],
                    "Image_A_Confidence": [result_a.confidence],
                    "Image_A_Risk": [result_a.get_risk_level()],
                    "Image_B_Prediction": [result_b.prediction],
                    "Image_B_Confidence": [result_b.confidence],
                    "Image_B_Risk": [result_b.get_risk_level()],
                    "Confidence_Delta": [result_b.confidence - result_a.confidence],
                    "Disease_Match": [result_a.prediction.lower() == result_b.prediction.lower()],
                    "Risk_Change": [ComparisonResult(result_a, result_b).get_risk_change()],
                }

                df = pd.DataFrame(report_data)
                csv_content = df.to_csv(index=False)

                st.download_button(
                    "Download CSV Report",
                    data=csv_content,
                    file_name=f"plantguard_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

        with col2:
            if st.button("[DOCUMENT] Export as Report"):
                st.info("PDF report export functionality would be implemented here")

    def render_single_image_guidance(self) -> None:
        """Render guidance for single image scenarios."""
        st.info("""
        [WRITE] **Comparison Mode Tips:**

        - Upload or capture at least 2 images to enable comparison
        - Use different angles of the same plant to track disease progression
        - Compare healthy vs diseased parts of the same plant
        - Compare before/after treatment images
        - Use the synchronized viewer to spot differences easily
        """)

    def render_complete_comparison_interface(
        self, available_images: list[Image.Image] | None = None, available_results: list[AnalysisResult] | None = None
    ) -> None:
        """Render the complete comparison interface.

        Args:
            available_images: List of available images for comparison
            available_results: List of available analysis results
        """
        st.header("[PARTIAL] Compare Analysis Results")

        if not available_images or len(available_images) < 2:
            self.render_single_image_guidance()
            return

        # Image selection
        col1, col2 = st.columns(2)

        with col1:
            self.render_image_selector(0, available_images, available_results or [])

        with col2:
            self.render_image_selector(1, available_images, available_results or [])

        # Comparison views
        if all(st.session_state.comparison_images):
            st.markdown("---")

            # Tabs for different comparison views
            tab1, tab2, tab3, tab4 = st.tabs(["[SEARCH] Viewer", "[SUMMARY] Metrics", "[CHART] Probabilities", "[MICROSCOPE] Difference"])

            with tab1:
                self.render_synchronized_viewer()

            with tab2:
                self.render_comparative_metrics()

            with tab3:
                self.render_probability_comparison()

            with tab4:
                self.render_difference_analysis()

            # Export options
            st.markdown("---")
            self.render_comparison_export()


def create_compare_view() -> CompareView:
    """Create and return a CompareView instance.

    Returns:
        CompareView instance
    """
    return CompareView()


# Example usage and testing
if __name__ == "__main__":
    # Test the compare view
    st.title("[PARTIAL] PlantGuard Compare View Test")

    # Create compare view
    compare_view = create_compare_view()

    # Mock data for testing
    mock_images: list[Image.Image] = []
    mock_results: list[AnalysisResult] = []

    st.info("This is a test interface. In practice, images and results would be provided by the main application.")

    # Render interface
    compare_view.render_complete_comparison_interface(mock_images, mock_results)
