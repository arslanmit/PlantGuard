"""Analysis Cards and Visualization System for PlantGuard.

This module provides comprehensive analysis visualization including
disease prediction cards, confidence visualization, probability charts,
and symptom analysis for the PlantGuard plant disease detection system.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

logger = logging.getLogger(__name__)


class AnalysisResult:
    """Represents a single analysis result with prediction and metadata."""

    def __init__(
        self,
        prediction: str,
        confidence: float,
        probabilities: dict[str, float] | None = None,
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ):
        """Initialize analysis result.

        Args:
            prediction: Predicted disease name
            confidence: Confidence score (0-1)
            probabilities: Dictionary of all class probabilities
            metadata: Additional metadata about the analysis
            timestamp: When the analysis was performed
        """
        self.prediction = prediction
        self.confidence = confidence
        self.probabilities = probabilities or {}
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()

    def get_risk_level(self) -> str:
        """Get risk level based on confidence and prediction.

        Returns:
            Risk level string
        """
        if "healthy" in self.prediction.lower():
            return "low"
        elif self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.5:
            return "medium"
        else:
            return "low"

    def get_risk_color(self) -> str:
        """Get color for risk level.

        Returns:
            Hex color string
        """
        risk_colors = {
            "low": "#28a745",  # Green
            "medium": "#ffc107",  # Yellow
            "high": "#dc3545",  # Red
        }
        return risk_colors.get(self.get_risk_level(), "#6c757d")

    def get_top_predictions(self, n: int = 5) -> list[tuple[str, float]]:
        """Get top N predictions sorted by probability.

        Args:
            n: Number of top predictions to return

        Returns:
            List of (prediction, probability) tuples
        """
        if not self.probabilities:
            return [(self.prediction, self.confidence)]

        sorted_probs = sorted(self.probabilities.items(), key=lambda x: x[1], reverse=True)
        return sorted_probs[:n]


class AnalysisCard:
    """Analysis card component for displaying disease prediction results."""

    def __init__(self) -> None:
        """Initialize analysis card."""
        self.disease_info = {
            # Common plant diseases information
            "healthy": {
                "description": "Plant appears healthy with no visible disease symptoms",
                "severity": "None",
                "treatment": "Continue regular care and monitoring",
                "prevention": "Maintain good growing conditions",
            },
            "bacterial_spot": {
                "description": "Bacterial infection causing dark spots on leaves",
                "severity": "Medium to High",
                "treatment": "Apply copper-based fungicide, improve air circulation",
                "prevention": "Avoid overhead watering, ensure proper spacing",
            },
            "early_blight": {
                "description": "Fungal disease causing brown spots with concentric rings",
                "severity": "Medium",
                "treatment": "Remove affected leaves, apply fungicide",
                "prevention": "Crop rotation, avoid wet foliage",
            },
            "late_blight": {
                "description": "Serious fungal disease that can destroy crops quickly",
                "severity": "High",
                "treatment": "Immediate fungicide application, remove affected plants",
                "prevention": "Ensure good drainage, avoid overhead watering",
            },
            "leaf_mold": {
                "description": "Fungal disease causing yellow patches and mold growth",
                "severity": "Medium",
                "treatment": "Improve ventilation, apply fungicide",
                "prevention": "Control humidity, ensure good air circulation",
            },
            "septoria_leaf_spot": {
                "description": "Fungal disease causing small dark spots with light centers",
                "severity": "Medium",
                "treatment": "Remove affected leaves, apply fungicide",
                "prevention": "Avoid overhead watering, mulch around plants",
            },
            "spider_mites": {
                "description": "Tiny pests causing stippling and webbing on leaves",
                "severity": "Medium to High",
                "treatment": "Apply insecticidal soap or miticide",
                "prevention": "Maintain humidity, regular inspection",
            },
            "target_spot": {
                "description": "Fungal disease causing target-like spots on leaves",
                "severity": "Medium",
                "treatment": "Apply fungicide, improve air circulation",
                "prevention": "Avoid wet foliage, practice crop rotation",
            },
            "mosaic_virus": {
                "description": "Viral disease causing mottled yellow-green patterns",
                "severity": "High",
                "treatment": "No cure available, remove infected plants",
                "prevention": "Control insect vectors, use resistant varieties",
            },
            "yellow_leaf_curl": {
                "description": "Viral disease causing leaf yellowing and curling",
                "severity": "High",
                "treatment": "Remove infected plants, control whiteflies",
                "prevention": "Use resistant varieties, control insect vectors",
            },
        }

    def get_disease_info(self, disease_name: str) -> dict[str, str]:
        """Get disease information by name.

        Args:
            disease_name: Name of the disease

        Returns:
            Dictionary with disease information
        """
        # Normalize disease name
        disease_key = disease_name.lower().replace(" ", "_").replace("-", "_")

        # Try exact match first
        if disease_key in self.disease_info:
            return self.disease_info[disease_key]

        # Try partial matches
        for key, info in self.disease_info.items():
            if key in disease_key or disease_key in key:
                return info

        # Default info for unknown diseases
        return {
            "description": "Disease information not available in knowledge base",
            "severity": "Unknown",
            "treatment": "Consult with a plant pathologist or agricultural extension",
            "prevention": "Follow general plant care best practices",
        }

    def render_confidence_bar(self, confidence: float, risk_level: str) -> None:
        """Render confidence bar with color coding and accessibility.

        Args:
            confidence: Confidence score (0-1)
            risk_level: Risk level string
        """
        # Color based on risk level
        color_map = {"low": "#28a745", "medium": "#ffc107", "high": "#dc3545"}
        color = color_map.get(risk_level, "#6c757d")

        confidence_percent = confidence * 100

        # Create progress bar with ARIA attributes
        st.markdown(
            f"""
        <div role="progressbar"
             aria-label="Disease prediction confidence score"
             aria-valuenow="{confidence_percent:.1f}"
             aria-valuemin="0"
             aria-valuemax="100"
             aria-valuetext="{confidence_percent:.1f} percent confidence"
             style="margin-bottom: 8px;">
        """,
            unsafe_allow_html=True,
        )

        st.progress(confidence, text=f"Confidence: {confidence:.1%}")

        st.markdown("</div>", unsafe_allow_html=True)

        # Risk badge with accessibility
        risk_descriptions = {
            "low": "Low risk - minimal concern for plant health",
            "medium": "Medium risk - monitor plant condition closely",
            "high": "High risk - immediate attention and treatment needed",
        }

        risk_description = risk_descriptions.get(risk_level, f"{risk_level} risk level")
        timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

        st.markdown(
            f'<div role="status" '
            f'aria-label="Risk level indicator" '
            f'aria-describedby="risk-desc-{timestamp_id}" '
            f'style="display: inline-block; padding: 4px 8px; '
            f"background-color: {color}; color: white; border-radius: 4px; "
            f'font-size: 12px; font-weight: bold; margin-top: 5px;">'
            f"{risk_level.upper()} RISK</div>"
            f'<div id="risk-desc-{timestamp_id}" class="sr-only">{risk_description}</div>',
            unsafe_allow_html=True,
        )

    def render_disease_prediction_card(self, result: AnalysisResult, image: Image.Image | None = None) -> None:
        """Render main disease prediction card.

        Args:
            result: AnalysisResult object
            image: Optional PIL Image
        """
        # Card container
        with st.container():
            # Header with disease name and timestamp
            col1, col2 = st.columns([3, 1])

            with col1:
                st.subheader(f"[MICROSCOPE] {result.prediction.title()}")

            with col2:
                st.caption(f"[DATE] {result.timestamp.strftime('%H:%M:%S')}")

            # Main content
            col1, col2 = st.columns([2, 1])

            with col1:
                # Disease information
                disease_info = self.get_disease_info(result.prediction)

                st.write("**Description:**")
                st.write(disease_info["description"])

                st.write("**Severity:**")
                st.write(disease_info["severity"])

                # Confidence visualization
                st.write("**Confidence:**")
                self.render_confidence_bar(result.confidence, result.get_risk_level())

            with col2:
                # Image preview
                if image:
                    st.image(image, caption="Analyzed Image", use_container_width=True)

                # Quick stats
                st.metric("Confidence", f"{result.confidence:.1%}")
                st.metric("Risk Level", result.get_risk_level().title())

    def render_treatment_recommendations(self, result: AnalysisResult) -> None:
        """Render treatment recommendations.

        Args:
            result: AnalysisResult object
        """
        disease_info = self.get_disease_info(result.prediction)

        with st.expander("[TREATMENT] Treatment & Prevention", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**[PROGRESS] Treatment:**")
                st.info(disease_info["treatment"])

            with col2:
                st.write("**[SHIELD] Prevention:**")
                st.success(disease_info["prevention"])

    def render_probability_chart(self, result: AnalysisResult, n_classes: int = 5) -> None:
        """Render probability chart for top predictions.

        Args:
            result: AnalysisResult object
            n_classes: Number of top classes to show
        """
        if not result.probabilities:
            st.info("Detailed probability data not available")
            return

        # Get top predictions
        top_predictions = result.get_top_predictions(n_classes)

        if len(top_predictions) <= 1:
            st.info("Only single prediction available")
            return

        # Create DataFrame for plotting
        df = pd.DataFrame(top_predictions, columns=["Disease", "Probability"])
        df["Percentage"] = df["Probability"] * 100

        # Create bar chart
        fig = px.bar(
            df,
            x="Percentage",
            y="Disease",
            orientation="h",
            title=f"Top {len(top_predictions)} Disease Predictions",
            labels={"Percentage": "Confidence (%)", "Disease": "Disease"},
            color="Percentage",
            color_continuous_scale="RdYlGn_r",
        )

        # Update layout
        fig.update_layout(
            height=max(200, len(top_predictions) * 50),
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            coloraxis_showscale=False,
        )

        # Format y-axis labels
        fig.update_yaxis(title="")
        fig.update_xaxis(range=[0, 100])

        st.plotly_chart(fig, use_container_width=True)

    def render_action_chips(self, result: AnalysisResult) -> None:
        """Render action recommendation chips.

        Args:
            result: AnalysisResult object
        """
        # Define action recommendations based on disease type
        action_map = {
            "healthy": ["Monitor regularly", "Continue current care", "Maintain conditions"],
            "bacterial": ["Apply bactericide", "Improve drainage", "Isolate plant"],
            "fungal": ["Apply fungicide", "Increase ventilation", "Remove affected leaves"],
            "viral": ["Remove infected plant", "Control vectors", "Quarantine area"],
            "pest": ["Apply pesticide", "Check neighboring plants", "Improve monitoring"],
        }

        # Determine disease type
        disease_lower = result.prediction.lower()
        if "healthy" in disease_lower:
            actions = action_map["healthy"]
        elif any(word in disease_lower for word in ["bacterial", "bacteria"]):
            actions = action_map["bacterial"]
        elif any(word in disease_lower for word in ["fungal", "fungi", "blight", "spot", "mold"]):
            actions = action_map["fungal"]
        elif any(word in disease_lower for word in ["viral", "virus", "mosaic", "curl"]):
            actions = action_map["viral"]
        elif any(word in disease_lower for word in ["mite", "pest", "insect"]):
            actions = action_map["pest"]
        else:
            actions = ["Consult expert", "Monitor closely", "Research treatment"]

        st.write("**[PROGRESS] Recommended Actions:**")

        # Create action buttons
        cols = st.columns(min(len(actions), 3))
        for i, action in enumerate(actions):
            with cols[i % len(cols)]:
                if st.button(action, key=f"action_{i}_{id(result)}"):
                    st.toast(f"Action noted: {action}", icon="[DONE]")

    def render_metadata_info(self, result: AnalysisResult) -> None:
        """Render analysis metadata information.

        Args:
            result: AnalysisResult object
        """
        if not result.metadata:
            return

        with st.expander("[SUMMARY] Analysis Details", expanded=True):
            for key, value in result.metadata.items():
                if key == "model_version":
                    st.write(f"**Model:** {value}")
                elif key == "processing_time":
                    st.write(f"**Processing Time:** {value:.2f}s")
                elif key == "image_size":
                    st.write(f"**Image Size:** {value}")
                elif key == "preprocessing":
                    st.write(f"**Preprocessing:** {value}")
                else:
                    st.write(f"**{key.title()}:** {value}")

    def render_complete_analysis_card(
        self,
        result: AnalysisResult,
        image: Image.Image | None = None,
        show_chart: bool = True,
        show_actions: bool = True,
        show_metadata: bool = False,
    ) -> None:
        """Render complete analysis card with all components.

        Args:
            result: AnalysisResult object
            image: Optional PIL Image
            show_chart: Whether to show probability chart
            show_actions: Whether to show action chips
            show_metadata: Whether to show metadata
        """
        # Main prediction card
        self.render_disease_prediction_card(result, image)

        # Treatment recommendations
        self.render_treatment_recommendations(result)

        # Probability chart
        if show_chart:
            st.markdown("---")
            st.subheader("[SUMMARY] Prediction Confidence")
            self.render_probability_chart(result)

        # Action chips
        if show_actions:
            st.markdown("---")
            self.render_action_chips(result)

        # Metadata
        if show_metadata:
            st.markdown("---")
            self.render_metadata_info(result)


def create_analysis_card() -> AnalysisCard:
    """Create and return an AnalysisCard instance.

    Returns:
        AnalysisCard instance
    """
    return AnalysisCard()


def create_sample_result() -> AnalysisResult:
    """Create a sample analysis result for testing.

    Returns:
        Sample AnalysisResult
    """
    probabilities = {
        "Early Blight": 0.85,
        "Healthy": 0.08,
        "Late Blight": 0.04,
        "Bacterial Spot": 0.02,
        "Septoria Leaf Spot": 0.01,
    }

    metadata = {
        "model_version": "ResNet50_v1.0",
        "processing_time": 1.2,
        "image_size": "224x224",
        "preprocessing": "resize_and_normalize",
    }

    return AnalysisResult(prediction="Early Blight", confidence=0.85, probabilities=probabilities, metadata=metadata)


# Example usage and testing
if __name__ == "__main__":
    # Test the analysis card
    st.title("[MICROSCOPE] PlantGuard Analysis Card Test")

    # Create analysis card
    card = create_analysis_card()

    # Create sample result
    result = create_sample_result()

    # Render complete card
    card.render_complete_analysis_card(result, show_metadata=True)

    st.markdown("---")
    st.success("Analysis card test completed!")
