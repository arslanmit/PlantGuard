"""
Mobile Recommendations Component for PlantGuard UI.

This module provides a mobile-optimized treatment recommendations component
with expandable sections, sharing functionality, and disease knowledge integration.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileRecommendations(MobileBaseComponent):
    """Mobile-optimized treatment recommendations component."""

    def __init__(self, component_id: str, title: str = "Treatment Recommendations", **kwargs) -> None:
        """
        Initialize mobile recommendations component.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Recommendations configuration
        self.recommendations_config = {
            "max_recommendations": 5,
            "show_severity_warnings": True,
            "enable_sharing": True,
            "show_prevention_tips": True,
            "confidence_based_advice": True,
            "expandable_sections": True,
        }

        # Load disease knowledge base
        self.disease_info = self._load_disease_knowledge_base()
        self.treatment_templates = self._load_treatment_templates()

        # Initialize recommendations state
        self._initialize_recommendations_state()

        logger.debug("MobileRecommendations initialized: %s", component_id)

    def _initialize_recommendations_state(self) -> None:
        """Initialize recommendations-specific state."""
        recommendations_state = {
            "current_disease": None,
            "current_confidence": 0.0,
            "expanded_sections": {"immediate": True, "preventive": False, "organic": False, "detailed": False},
            "shared_recommendations": [],
            "custom_notes": "",
            "last_updated": datetime.now().isoformat(),
        }

        current_state = self.get_state()
        if "recommendations_data" not in current_state["data"]:
            current_state["data"]["recommendations_data"] = recommendations_state
            self.set_state(current_state)

    def render(self) -> None:
        """Render the mobile recommendations interface."""
        try:
            # Get current state
            state = self.get_state()
            recommendations_data = state["data"].get("recommendations_data", {})

            # Render recommendations container
            st.markdown(
                f"""
                <div class="mobile-recommendations mobile-component" 
                     data-component-id="{self.component_id}"
                     data-testid="recommendations-{self.component_id}">
                """,
                unsafe_allow_html=True,
            )

            # Get current analysis result
            current_result = self._get_current_analysis_result()

            if not current_result:
                self._render_no_analysis_state()
            else:
                disease_name, confidence = current_result.get("prediction", ("Unknown", 0.0))

                # Update current disease in state
                self._update_current_disease(disease_name, confidence)

                # Render recommendations header
                self._render_recommendations_header(disease_name, confidence)

                # Render confidence-based warning
                if self.recommendations_config["confidence_based_advice"]:
                    self._render_confidence_warning(confidence)

                # Get disease information
                disease_info = self._get_disease_info(disease_name)

                if disease_info:
                    # Render treatment recommendations
                    self._render_treatment_recommendations(disease_info, confidence)

                    # Render prevention tips
                    if self.recommendations_config["show_prevention_tips"]:
                        self._render_prevention_tips(disease_info)

                    # Render disease details
                    self._render_disease_details(disease_info)
                else:
                    # Render generic recommendations
                    self._render_generic_recommendations(disease_name, confidence)

                # Render sharing and notes section
                if self.recommendations_config["enable_sharing"]:
                    self._render_sharing_section(disease_name, confidence)

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Recommendations rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)

    def _get_current_analysis_result(self) -> dict[str, Any] | None:
        """Get current analysis result from session state."""
        if "analysis_results" not in st.session_state or not st.session_state.analysis_results:
            return None

        # Get the most recent result
        results = st.session_state.analysis_results
        return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)[0]

    def _update_current_disease(self, disease_name: str, confidence: float) -> None:
        """Update current disease in component state."""
        state = self.get_state()
        recommendations_data = state["data"]["recommendations_data"]
        recommendations_data["current_disease"] = disease_name
        recommendations_data["current_confidence"] = confidence
        recommendations_data["last_updated"] = datetime.now().isoformat()
        state["data"]["recommendations_data"] = recommendations_data
        self.set_state(state)

    def _render_no_analysis_state(self) -> None:
        """Render state when no analysis is available."""
        st.markdown(
            """
        <div class="mobile-card mobile-empty-recommendations">
            <div class="empty-state-content">
                <div class="empty-state-icon">[TIP]</div>
                <h3>No Analysis Available</h3>
                <p>Perform a plant disease analysis to get personalized treatment recommendations.</p>
                <div class="general-tips">
                    <h4>[PLANT] General Plant Care Tips:</h4>
                    <ul>
                        <li>Ensure proper watering (not too much, not too little)</li>
                        <li>Provide adequate sunlight for your plant type</li>
                        <li>Maintain good air circulation around plants</li>
                        <li>Remove dead or diseased plant material promptly</li>
                        <li>Use well-draining soil appropriate for your plant</li>
                    </ul>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_recommendations_header(self, disease_name: str, confidence: float) -> None:
        """Render recommendations header with disease info."""
        confidence_level = self._get_confidence_level(confidence)
        confidence_color = self._get_confidence_color(confidence_level)

        st.markdown(
            f"""
        <div class="mobile-card recommendations-header">
            <h3>[TIP] Treatment for {disease_name}</h3>
            <div class="confidence-indicator">
                <span style="color: {confidence_color}">
                    {confidence:.1%} Confidence ({confidence_level.title()})
                </span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_confidence_warning(self, confidence: float) -> None:
        """Render confidence-based warning message."""
        confidence_level = self._get_confidence_level(confidence)

        if confidence_level == "low":
            st.error("""
            [WARNING] **Low Confidence Warning**
            
            The AI diagnosis has low confidence. Please consider:
            - Consulting a plant pathologist or expert
            - Taking additional photos with better lighting
            - Checking for other symptoms not visible in the image
            """)
        elif confidence_level == "medium":
            st.warning("""
            [WARNING] **Medium Confidence Notice**
            
            The diagnosis is moderately confident. Consider:
            - Monitoring the plant closely after treatment
            - Consulting an expert if symptoms persist
            - Taking preventive measures as recommended
            """)
        else:
            st.success("""
            [DONE] **High Confidence Diagnosis**
            
            The AI is confident in this diagnosis. Follow the recommended treatments below.
            """)

    def _render_treatment_recommendations(self, disease_info: dict[str, Any], confidence: float) -> None:
        """Render treatment recommendations with expandable sections."""
        treatment = disease_info.get("treatment", {})

        if not treatment:
            self._render_generic_treatment_advice(confidence)
            return

        # Immediate actions
        if "immediate" in treatment:
            expanded = self._is_section_expanded("immediate")
            with st.expander("[ALERT] Immediate Actions", expanded=expanded):
                self._render_treatment_section(treatment["immediate"], "Take these actions right away:", "immediate")

        # Preventive measures
        if "preventive" in treatment:
            expanded = self._is_section_expanded("preventive")
            with st.expander("[SHIELD] Preventive Measures", expanded=expanded):
                self._render_treatment_section(treatment["preventive"], "To prevent future occurrences:", "preventive")

        # Organic treatments
        if "organic" in treatment:
            expanded = self._is_section_expanded("organic")
            with st.expander("[PLANT] Organic Treatment Options", expanded=expanded):
                self._render_treatment_section(treatment["organic"], "Natural and organic solutions:", "organic")

        # Chemical treatments (if available)
        if "chemical" in treatment:
            expanded = self._is_section_expanded("chemical")
            with st.expander("⚗️ Chemical Treatment Options", expanded=expanded):
                st.warning("[WARNING] Always follow label instructions and safety precautions")
                self._render_treatment_section(treatment["chemical"], "Chemical treatment options:", "chemical")

    def _render_treatment_section(self, treatments: list[str], description: str, section_type: str) -> None:
        """Render individual treatment section."""
        st.markdown(f"**{description}**")

        for i, treatment in enumerate(treatments):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"- {treatment}")

            with col2:
                if st.button("✓", key=f"{self.component_id}_{section_type}_{i}", help="Mark as done"):
                    st.success("[DONE] Marked as completed!")

    def _render_prevention_tips(self, disease_info: dict[str, Any]) -> None:
        """Render prevention tips."""
        prevention = disease_info.get("prevention", [])

        if prevention:
            expanded = self._is_section_expanded("prevention")
            with st.expander("[SECURE] Prevention Tips", expanded=expanded):
                st.markdown("**To prevent this disease in the future:**")

                for tip in prevention:
                    st.write(f"- {tip}")
        else:
            # Generic prevention tips
            with st.expander("[SECURE] General Prevention Tips", expanded=False):
                st.markdown("""
                **General disease prevention:**
                - Maintain proper plant spacing for air circulation
                - Water at soil level, avoid wetting leaves
                - Remove infected plant debris promptly
                - Rotate crops if applicable
                - Use disease-resistant plant varieties when possible
                """)

    def _render_disease_details(self, disease_info: dict[str, Any]) -> None:
        """Render detailed disease information."""
        expanded = self._is_section_expanded("detailed")
        with st.expander("[LIBRARY] Disease Information", expanded=expanded):
            # Basic information
            if "description" in disease_info:
                st.markdown(f"**Description:** {disease_info['description']}")

            if "scientific_name" in disease_info:
                st.markdown(f"**Scientific Name:** *{disease_info['scientific_name']}*")

            if "severity" in disease_info:
                severity = disease_info["severity"].title()
                severity_color = self._get_severity_color(disease_info["severity"])
                st.markdown(f"**Severity:** <span style='color: {severity_color}'>{severity}</span>", unsafe_allow_html=True)

            # Symptoms
            if "symptoms" in disease_info:
                st.markdown("**Common Symptoms:**")
                for symptom in disease_info["symptoms"]:
                    st.write(f"- {symptom}")

            # Additional information
            if "causes" in disease_info:
                st.markdown("**Common Causes:**")
                for cause in disease_info["causes"]:
                    st.write(f"- {cause}")

    def _render_generic_recommendations(self, disease_name: str, confidence: float) -> None:
        """Render generic recommendations when specific info is not available."""
        st.markdown("### [TIP] General Treatment Recommendations")

        confidence_level = self._get_confidence_level(confidence)

        # Generic advice based on confidence
        if confidence_level == "high":
            st.success(f"""
            **For {disease_name}:**
            
            While specific treatment information is not available, here are general recommendations:
            """)
        else:
            st.warning(f"""
            **Possible {disease_name}:**
            
            Due to {confidence_level} confidence, consider these general approaches:
            """)

        # Generic treatment steps
        with st.expander("[TOOL] General Treatment Steps", expanded=True):
            st.markdown("""
            **Immediate Actions:**
            - Remove affected plant parts (leaves, branches, fruits)
            - Isolate the plant if possible to prevent spread
            - Improve air circulation around the plant
            - Adjust watering practices (avoid overwatering)
            
            **Monitoring:**
            - Check the plant daily for changes
            - Take photos to track progress
            - Note any new symptoms that develop
            
            **When to Seek Help:**
            - If symptoms worsen despite treatment
            - If the disease spreads to other plants
            - If you're unsure about the diagnosis
            """)

    def _render_generic_treatment_advice(self, confidence: float) -> None:
        """Render generic treatment advice when no specific treatment is available."""
        confidence_level = self._get_confidence_level(confidence)

        st.info(f"""
        **Treatment information not available for this disease.**
        
        Confidence Level: {confidence:.1%} ({confidence_level.title()})
        """)

        with st.expander("[PLANT] General Plant Care", expanded=True):
            st.markdown("""
            **Basic Plant Health Measures:**
            - Ensure proper drainage to prevent root rot
            - Provide appropriate lighting for your plant type
            - Maintain consistent watering schedule
            - Remove dead or diseased plant material
            - Consider applying a balanced fertilizer
            - Monitor for pests and other issues
            
            **Recommended Next Steps:**
            - Consult a local plant expert or extension service
            - Research the specific disease online
            - Consider taking the plant to a garden center
            - Monitor the plant closely for changes
            """)

    def _render_sharing_section(self, disease_name: str, confidence: float) -> None:
        """Render sharing and notes section."""
        st.markdown("### [UPLOAD] Share & Notes")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("[UPLOAD] Share Recommendations", key=f"{self.component_id}_share", use_container_width=True):
                self._generate_shareable_recommendations(disease_name, confidence)

        with col2:
            if st.button("[SAVE] Save to Notes", key=f"{self.component_id}_save", use_container_width=True):
                self._save_recommendations_to_notes(disease_name, confidence)

        # Custom notes section
        with st.expander("[WRITE] Personal Notes", expanded=False):
            state = self.get_state()
            current_notes = state["data"]["recommendations_data"].get("custom_notes", "")

            notes = st.text_area(
                "Add your own notes about this treatment:",
                value=current_notes,
                height=100,
                key=f"{self.component_id}_notes",
                placeholder="Record your observations, treatment progress, or additional notes...",
            )

            if notes != current_notes:
                self._save_custom_notes(notes)

    def _generate_shareable_recommendations(self, disease_name: str, confidence: float) -> None:
        """Generate shareable recommendations text."""
        disease_info = self._get_disease_info(disease_name)

        share_text = f"""[LEAF] PlantGuard Treatment Recommendations

Disease: {disease_name}
Confidence: {confidence:.1%}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

"""

        if disease_info and "treatment" in disease_info:
            treatment = disease_info["treatment"]

            if "immediate" in treatment:
                share_text += "[ALERT] IMMEDIATE ACTIONS:\n"
                for action in treatment["immediate"]:
                    share_text += f"- {action}\n"
                share_text += "\n"

            if "preventive" in treatment:
                share_text += "[SHIELD] PREVENTION:\n"
                for prevention in treatment["preventive"]:
                    share_text += f"- {prevention}\n"
                share_text += "\n"

            if "organic" in treatment:
                share_text += "[PLANT] ORGANIC OPTIONS:\n"
                for organic in treatment["organic"]:
                    share_text += f"- {organic}\n"
                share_text += "\n"

        share_text += "Generated by PlantGuard AI Plant Disease Detection"

        st.text_area("[UPLOAD] Shareable Recommendations", value=share_text, height=200, key=f"{self.component_id}_share_text")

        st.success("[DONE] Recommendations ready to share! Copy the text above.")

    def _save_recommendations_to_notes(self, disease_name: str, confidence: float) -> None:
        """Save recommendations to personal notes."""
        # In a real implementation, this would save to persistent storage
        timestamp = datetime.now().isoformat()

        state = self.get_state()
        recommendations_data = state["data"]["recommendations_data"]

        if "saved_recommendations" not in recommendations_data:
            recommendations_data["saved_recommendations"] = []

        saved_rec = {"disease": disease_name, "confidence": confidence, "timestamp": timestamp, "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M")}

        recommendations_data["saved_recommendations"].append(saved_rec)
        state["data"]["recommendations_data"] = recommendations_data
        self.set_state(state)

        st.success("[SAVE] Recommendations saved to your notes!")

    def _save_custom_notes(self, notes: str) -> None:
        """Save custom notes to component state."""
        state = self.get_state()
        recommendations_data = state["data"]["recommendations_data"]
        recommendations_data["custom_notes"] = notes
        state["data"]["recommendations_data"] = recommendations_data
        self.set_state(state)

    def _is_section_expanded(self, section: str) -> bool:
        """Check if a section should be expanded by default."""
        state = self.get_state()
        recommendations_data = state["data"]["recommendations_data"]
        expanded_sections = recommendations_data.get("expanded_sections", {})
        return expanded_sections.get(section, False)

    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level category."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
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

    def _get_severity_color(self, severity: str) -> str:
        """Get color for disease severity."""
        colors = {
            "low": "#22c55e",  # green
            "medium": "#f59e0b",  # yellow
            "high": "#ef4444",  # red
            "critical": "#dc2626",  # dark red
        }
        return colors.get(severity.lower(), "#6b7280")

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

    def _load_treatment_templates(self) -> dict[str, Any]:
        """Load treatment templates for generic recommendations."""
        return {
            "generic_immediate": [
                "Remove affected plant parts immediately",
                "Isolate the plant to prevent spread",
                "Improve air circulation around the plant",
                "Adjust watering practices",
            ],
            "generic_preventive": [
                "Maintain proper plant spacing",
                "Water at soil level, avoid wetting leaves",
                "Remove plant debris regularly",
                "Use disease-resistant varieties when possible",
            ],
            "generic_organic": [
                "Apply neem oil spray",
                "Use baking soda solution (1 tsp per quart water)",
                "Try copper-based fungicide",
                "Improve soil drainage",
            ],
        }

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

    def get_current_disease(self) -> str | None:
        """Get current disease being displayed."""
        state = self.get_state()
        recommendations_data = state["data"].get("recommendations_data", {})
        return recommendations_data.get("current_disease")

    def get_current_confidence(self) -> float:
        """Get current confidence level."""
        state = self.get_state()
        recommendations_data = state["data"].get("recommendations_data", {})
        return recommendations_data.get("current_confidence", 0.0)

    def has_recommendations(self) -> bool:
        """Check if recommendations are available."""
        current_disease = self.get_current_disease()
        return current_disease is not None

    def clear_recommendations(self) -> None:
        """Clear current recommendations."""
        self._initialize_recommendations_state()
        st.success("[CLEAN] Recommendations cleared!")
