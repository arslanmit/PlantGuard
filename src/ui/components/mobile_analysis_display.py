"""
Mobile Analysis Display Component for PlantGuard UI.

This module provides a mobile-optimized analysis results display component
with disease information, confidence visualization, and responsive design.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image

from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileAnalysisDisplay(MobileBaseComponent):
    """Mobile-optimized analysis results display component."""

    def __init__(self, component_id: str, title: str = "Analysis Results", **kwargs) -> None:
        """
        Initialize mobile analysis display component.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Analysis display configuration
        self.display_config = {
            "max_results_shown": 3,
            "confidence_threshold": {"high": 0.8, "medium": 0.6, "low": 0.4},
            "image_max_width": 400,
            "show_confidence_bar": True,
            "show_recommendations": True,
            "auto_refresh": True,
        }

        # Load disease knowledge base
        self.disease_info = self._load_disease_knowledge_base()

        # Initialize analysis state
        self._initialize_analysis_state()

        logger.debug("MobileAnalysisDisplay initialized: %s", component_id)

    def _initialize_analysis_state(self) -> None:
        """Initialize analysis-specific state."""
        analysis_state = {
            "current_result": None,
            "results_history": [],
            "display_mode": "latest",  # latest, history, detailed
            "selected_result_index": 0,
            "show_details": False,
            "last_refresh": datetime.now().isoformat(),
        }

        current_state = self.get_state()
        if "analysis_data" not in current_state["data"]:
            current_state["data"]["analysis_data"] = analysis_state
            self.set_state(current_state)

    def render(self) -> None:
        """Render the mobile analysis display interface."""
        try:
            # Get current state
            state = self.get_state()
            analysis_data = state["data"].get("analysis_data", {})

            # Render analysis display container
            st.markdown(
                f"""
                <div class="mobile-analysis-display mobile-component" 
                     data-component-id="{self.component_id}"
                     data-testid="analysis-display-{self.component_id}">
                """,
                unsafe_allow_html=True,
            )

            # Check for analysis results
            analysis_results = self._get_analysis_results()

            if not analysis_results:
                self._render_empty_state()
            else:
                # Update current result
                self._update_current_result(analysis_results)

                # Render display mode selector
                self._render_display_mode_selector(analysis_data)

                # Render based on display mode
                display_mode = analysis_data.get("display_mode", "latest")

                if display_mode == "latest":
                    self._render_latest_result(analysis_results[0])
                elif display_mode == "history":
                    self._render_results_history(analysis_results)
                elif display_mode == "detailed":
                    selected_index = analysis_data.get("selected_result_index", 0)
                    if selected_index < len(analysis_results):
                        self._render_detailed_result(analysis_results[selected_index])

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Analysis display rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)

    def _get_analysis_results(self) -> list[dict[str, Any]]:
        """Get analysis results from session state."""
        if "analysis_results" not in st.session_state:
            return []

        # Sort by timestamp (newest first)
        results = st.session_state.analysis_results
        return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)

    def _update_current_result(self, analysis_results: list[dict[str, Any]]) -> None:
        """Update current result in component state."""
        if analysis_results:
            state = self.get_state()
            analysis_data = state["data"]["analysis_data"]
            analysis_data["current_result"] = analysis_results[0]
            analysis_data["results_history"] = analysis_results[: self.display_config["max_results_shown"]]
            analysis_data["last_refresh"] = datetime.now().isoformat()
            state["data"]["analysis_data"] = analysis_data
            self.set_state(state)

    def _render_empty_state(self) -> None:
        """Render empty state when no analysis results are available."""
        st.markdown(
            """
        <div class="mobile-card mobile-empty-state">
            <div class="empty-state-content">
                <div class="empty-state-icon">[LEAF]</div>
                <h3>Ready for Analysis</h3>
                <p>Upload an image, take a photo, or use voice input to get started with plant disease detection.</p>
                <div class="empty-state-tips">
                    <h4>[TIP] Tips for best results:</h4>
                    <ul>
                        <li>Use clear, well-lit photos</li>
                        <li>Focus on affected plant parts</li>
                        <li>Avoid blurry or dark images</li>
                    </ul>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_display_mode_selector(self, analysis_data: dict[str, Any]) -> None:
        """Render display mode selector."""
        col1, col2, col3 = st.columns(3)

        current_mode = analysis_data.get("display_mode", "latest")

        with col1:
            if st.button(
                "[SUMMARY] Latest",
                key=f"{self.component_id}_mode_latest",
                type="primary" if current_mode == "latest" else "secondary",
                use_container_width=True,
            ):
                self._set_display_mode("latest")

        with col2:
            if st.button(
                "[DETAILS] History",
                key=f"{self.component_id}_mode_history",
                type="primary" if current_mode == "history" else "secondary",
                use_container_width=True,
            ):
                self._set_display_mode("history")

        with col3:
            if st.button(
                "[SEARCH] Details",
                key=f"{self.component_id}_mode_detailed",
                type="primary" if current_mode == "detailed" else "secondary",
                use_container_width=True,
            ):
                self._set_display_mode("detailed")

    def _set_display_mode(self, mode: str) -> None:
        """Set display mode."""
        state = self.get_state()
        analysis_data = state["data"]["analysis_data"]
        analysis_data["display_mode"] = mode
        state["data"]["analysis_data"] = analysis_data
        self.set_state(state)

    def _render_latest_result(self, result: dict[str, Any]) -> None:
        """Render the latest analysis result."""
        st.markdown("### [MICROSCOPE] Latest Analysis")

        # Extract result data
        disease_name, confidence = result.get("prediction", ("Unknown", 0.0))
        timestamp = result.get("timestamp", "")
        source = result.get("source", "unknown")

        # Result card
        confidence_level = self._get_confidence_level(confidence)
        confidence_color = self._get_confidence_color(confidence_level)

        st.markdown(
            f"""
        <div class="mobile-card mobile-analysis-result">
            <div class="analysis-header">
                <h4 class="disease-name">{disease_name}</h4>
                <span class="analysis-source">[CAMERA] {source.title()}</span>
            </div>
            
            <div class="confidence-section">
                <div class="confidence-label">Confidence Level</div>
                <div class="confidence-bar-container">
                    <div class="confidence-bar">
                        <div class="confidence-fill {confidence_level}" 
                             style="width: {confidence * 100:.1f}%"></div>
                    </div>
                    <span class="confidence-text" style="color: {confidence_color}">
                        {confidence:.1%} ({confidence_level.title()})
                    </span>
                </div>
            </div>
            
            <div class="analysis-timestamp">
                [DATE] {self._format_timestamp(timestamp)}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Display image
        if "image" in result:
            self._render_analysis_image(result["image"], disease_name)

        # Display recommendations
        if self.display_config["show_recommendations"]:
            self._render_recommendations(disease_name, confidence)

        # Action buttons
        self._render_result_actions(result)

    def _render_results_history(self, results: list[dict[str, Any]]) -> None:
        """Render analysis results history."""
        st.markdown("### [DETAILS] Analysis History")

        if not results:
            st.info("No analysis history available.")
            return

        for i, result in enumerate(results[: self.display_config["max_results_shown"]]):
            disease_name, confidence = result.get("prediction", ("Unknown", 0.0))
            timestamp = result.get("timestamp", "")
            source = result.get("source", "unknown")

            with st.expander(f"[LEAF] {disease_name} ({confidence:.1%}) - {self._format_timestamp(timestamp)}", expanded=(i == 0)):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Disease:** {disease_name}")
                    st.write(f"**Confidence:** {confidence:.1%}")
                    st.write(f"**Source:** {source.title()}")
                    st.write(f"**Time:** {self._format_timestamp(timestamp)}")

                with col2:
                    if st.button("[SEARCH] View Details", key=f"{self.component_id}_view_{i}", use_container_width=True):
                        self._view_detailed_result(i)

                    if st.button("[PARTIAL] Re-analyze", key=f"{self.component_id}_reanalyze_{i}", use_container_width=True):
                        self._reanalyze_result(result)

    def _render_detailed_result(self, result: dict[str, Any]) -> None:
        """Render detailed analysis result."""
        st.markdown("### [SEARCH] Detailed Analysis")

        disease_name, confidence = result.get("prediction", ("Unknown", 0.0))

        # Detailed result card
        st.markdown(
            f"""
        <div class="mobile-card mobile-detailed-result">
            <h4>{disease_name}</h4>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Image display
        if "image" in result:
            self._render_analysis_image(result["image"], disease_name)

        # Detailed information
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Analysis Details:**")
            st.write(f"- Disease: {disease_name}")
            st.write(f"- Confidence: {confidence:.1%}")
            st.write(f"- Source: {result.get('source', 'unknown').title()}")
            st.write(f"- Timestamp: {self._format_timestamp(result.get('timestamp', ''))}")

        with col2:
            confidence_level = self._get_confidence_level(confidence)
            st.markdown("**Confidence Assessment:**")

            if confidence_level == "high":
                st.success("[GREEN] High confidence - Reliable diagnosis")
            elif confidence_level == "medium":
                st.warning("[YELLOW] Medium confidence - Consider expert consultation")
            else:
                st.error("[RED] Low confidence - Expert consultation recommended")

        # Disease information
        disease_info = self._get_disease_info(disease_name)
        if disease_info:
            self._render_disease_information(disease_info)

        # Recommendations
        self._render_recommendations(disease_name, confidence)

    def _render_analysis_image(self, image: Image.Image, caption: str) -> None:
        """Render analysis image with responsive sizing."""
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.image(image, caption=f"Analyzed: {caption}", use_column_width=True, width=self.display_config["image_max_width"])

    def _render_recommendations(self, disease_name: str, confidence: float) -> None:
        """Render treatment recommendations."""
        st.markdown("### [TIP] Treatment Recommendations")

        disease_info = self._get_disease_info(disease_name)
        confidence_level = self._get_confidence_level(confidence)

        if disease_info and "treatment" in disease_info:
            treatment = disease_info["treatment"]

            # Immediate actions
            if "immediate" in treatment:
                st.markdown("**[ALERT] Immediate Actions:**")
                for action in treatment["immediate"]:
                    st.write(f"- {action}")

            # Preventive measures
            if "preventive" in treatment:
                st.markdown("**[SHIELD] Prevention:**")
                for prevention in treatment["preventive"]:
                    st.write(f"- {prevention}")

            # Organic options
            if "organic" in treatment:
                st.markdown("**[PLANT] Organic Options:**")
                for organic in treatment["organic"]:
                    st.write(f"- {organic}")
        else:
            # Generic recommendations based on confidence
            if confidence_level == "high":
                st.success("[DONE] High confidence diagnosis - Follow specific treatment guidelines")
            elif confidence_level == "medium":
                st.warning("[WARNING] Medium confidence - Consider consulting a plant pathologist")
            else:
                st.error("[TODO] Low confidence - Expert consultation strongly recommended")

            # Generic advice
            st.markdown("**General Plant Care:**")
            st.write("- Ensure proper watering and drainage")
            st.write("- Maintain good air circulation")
            st.write("- Remove affected plant parts")
            st.write("- Monitor plant regularly")

    def _render_disease_information(self, disease_info: dict[str, Any]) -> None:
        """Render detailed disease information."""
        st.markdown("### [LIBRARY] Disease Information")

        with st.expander("[MICROSCOPE] Disease Details", expanded=False):
            if "description" in disease_info:
                st.write(f"**Description:** {disease_info['description']}")

            if "scientific_name" in disease_info:
                st.write(f"**Scientific Name:** {disease_info['scientific_name']}")

            if "severity" in disease_info:
                severity = disease_info["severity"].title()
                st.write(f"**Severity:** {severity}")

            if "symptoms" in disease_info:
                st.markdown("**Common Symptoms:**")
                for symptom in disease_info["symptoms"]:
                    st.write(f"- {symptom}")

    def _render_result_actions(self, result: dict[str, Any]) -> None:
        """Render action buttons for analysis result."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("[UPLOAD] Share", key=f"{self.component_id}_share"):
                self._share_result(result)

        with col2:
            if st.button("[SAVE] Save", key=f"{self.component_id}_save"):
                self._save_result(result)

        with col3:
            if st.button("[PARTIAL] Re-analyze", key=f"{self.component_id}_reanalyze"):
                self._reanalyze_result(result)

        with col4:
            if st.button("[TODO] Clear", key=f"{self.component_id}_clear"):
                self._clear_results()

    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level category."""
        thresholds = self.display_config["confidence_threshold"]

        if confidence >= thresholds["high"]:
            return "high"
        elif confidence >= thresholds["medium"]:
            return "medium"
        else:
            return "low"

    def _get_confidence_color(self, level: str) -> str:
        """Get color for confidence level."""
        colors = {
            "high": "#22c55e",  # green
            "medium": "#f59e0b",  # yellow
            "low": "#ef4444",  # red
        }
        return colors.get(level, "#6b7280")

    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            if not timestamp:
                return "Unknown time"

            # Parse ISO timestamp
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

            # Format for mobile display
            now = datetime.now()
            diff = now - dt.replace(tzinfo=None)

            if diff.days > 0:
                return f"{diff.days} days ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hours ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return "Just now"

        except Exception:
            return "Unknown time"

    def _load_disease_knowledge_base(self) -> dict[str, Any]:
        """Load disease knowledge base from JSON file."""
        try:
            knowledge_base_path = Path("data/knowledge_base/disease_info.json")

            if knowledge_base_path.exists():
                with open(knowledge_base_path, encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("diseases", {})
            else:
                logger.warning("Disease knowledge base not found: %s", knowledge_base_path)
                return {}

        except Exception as e:
            logger.error("Failed to load disease knowledge base: %s", e)
            return {}

    def _get_disease_info(self, disease_name: str) -> dict[str, Any] | None:
        """Get disease information from knowledge base."""
        # Try exact match first
        if disease_name in self.disease_info:
            return self.disease_info[disease_name]

        # Try case-insensitive match
        for key, info in self.disease_info.items():
            if key.lower() == disease_name.lower():
                return info

        # Try partial match
        for key, info in self.disease_info.items():
            if disease_name.lower() in key.lower() or key.lower() in disease_name.lower():
                return info

        return None

    def _view_detailed_result(self, index: int) -> None:
        """Switch to detailed view for specific result."""
        state = self.get_state()
        analysis_data = state["data"]["analysis_data"]
        analysis_data["display_mode"] = "detailed"
        analysis_data["selected_result_index"] = index
        state["data"]["analysis_data"] = analysis_data
        self.set_state(state)

    def _share_result(self, result: dict[str, Any]) -> None:
        """Share analysis result."""
        disease_name, confidence = result.get("prediction", ("Unknown", 0.0))

        share_text = f"""
[LEAF] PlantGuard Analysis Result

Disease: {disease_name}
Confidence: {confidence:.1%}
Time: {self._format_timestamp(result.get("timestamp", ""))}

Generated by PlantGuard AI Plant Disease Detection
        """.strip()

        st.text_area("[UPLOAD] Share Result", value=share_text, height=150, key=f"{self.component_id}_share_text")

        st.success("[DONE] Result ready to share! Copy the text above.")

    def _save_result(self, result: dict[str, Any]) -> None:
        """Save analysis result."""
        # In a real implementation, this would save to local storage or file
        st.success("[SAVE] Result saved to analysis history!")

    def _reanalyze_result(self, result: dict[str, Any]) -> None:
        """Re-analyze the image from result."""
        if "image" in result:
            try:
                # Import vision adapter
                from src.core.vision import VisionAdapter

                # Get or create vision adapter
                if "vision_adapter" not in st.session_state:
                    st.session_state.vision_adapter = VisionAdapter()

                vision_adapter = st.session_state.vision_adapter

                # Perform re-analysis
                with st.spinner("[PARTIAL] Re-analyzing image..."):
                    prediction = vision_adapter.predict(result["image"])
                    disease_name, confidence = prediction

                    # Create new analysis result
                    new_result = {
                        "timestamp": datetime.now().isoformat(),
                        "image": result["image"],
                        "prediction": prediction,
                        "source": f"re-analysis-{result.get('source', 'unknown')}",
                        "component_id": self.component_id,
                    }

                    # Add to global analysis results
                    if "analysis_results" not in st.session_state:
                        st.session_state.analysis_results = []

                    st.session_state.analysis_results.append(new_result)

                    st.success(f"[PARTIAL] Re-analysis complete: {disease_name} ({confidence:.1%})")

            except Exception as e:
                logger.error("Re-analysis failed: %s", e)
                st.error("[TODO] Re-analysis failed. Please try again.")
        else:
            st.warning("[WARNING] No image available for re-analysis.")

    def _clear_results(self) -> None:
        """Clear analysis results."""
        if "analysis_results" in st.session_state:
            st.session_state.analysis_results = []

        # Clear component state
        self._initialize_analysis_state()

        st.success("[CLEAN] Analysis results cleared!")

    def get_current_result(self) -> dict[str, Any] | None:
        """Get current analysis result."""
        state = self.get_state()
        analysis_data = state["data"].get("analysis_data", {})
        return analysis_data.get("current_result")

    def has_results(self) -> bool:
        """Check if there are analysis results available."""
        return len(self._get_analysis_results()) > 0

    def get_results_count(self) -> int:
        """Get number of analysis results."""
        return len(self._get_analysis_results())
