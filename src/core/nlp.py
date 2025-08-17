"""Natural language processing module for PlantGuard.

This module contains the TextAdapter class for knowledge base management
and response generation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TextAdapter:
    """Text adapter for knowledge base management and response generation.

    This class handles disease information retrieval and response formatting
    based on user queries and disease predictions.
    """

    def __init__(self, knowledge_base_path: str = "data/knowledge_base/disease_info.json") -> None:
        """Initialize TextAdapter.

        Args:
            knowledge_base_path: Path to disease information JSON file
        """
        self.knowledge_base_path = knowledge_base_path
        self.disease_info: dict[str, Any] = {}
        self.response_templates: dict[str, str] = {}
        self.confidence_thresholds: dict[str, float] = {}

        # Load knowledge base
        self._load_knowledge_base()

        logger.info("TextAdapter initialized with knowledge base: %s", knowledge_base_path)

    def _load_knowledge_base(self) -> None:
        """Load disease information from JSON file."""
        try:
            kb_path = Path(self.knowledge_base_path)
            if not kb_path.exists():
                logger.error("Knowledge base file not found: %s", self.knowledge_base_path)
                return

            with open(kb_path, encoding="utf-8") as f:
                kb_data = json.load(f)

            self.disease_info = kb_data.get("diseases", {})
            self.response_templates = kb_data.get("usage_guidelines", {}).get("response_templates", {})
            self.confidence_thresholds = kb_data.get("usage_guidelines", {}).get("confidence_thresholds", {})

            logger.info("Loaded knowledge base with %d diseases", len(self.disease_info))

        except Exception as e:
            logger.error("Failed to load knowledge base: %s", e)
            self.disease_info = {}
            self.response_templates = {}
            self.confidence_thresholds = {}

    def get_disease_info(self, disease_class: str) -> dict[str, Any]:
        """Get disease information from knowledge base with fallback handling.

        Args:
            disease_class: Disease class name from vision model

        Returns:
            Dictionary with disease info (name, description, treatment, etc.)
        """
        try:
            if disease_class in self.disease_info:
                disease_data = self.disease_info[disease_class].copy()
                logger.info("Retrieved disease info for: %s", disease_class)
                return disease_data
            else:
                logger.warning("Disease class not found in knowledge base: %s", disease_class)
                # Fallback response for unknown diseases
                return {
                    "disease_name": "Unknown Disease",
                    "scientific_name": None,
                    "plant_type": "Unknown",
                    "severity": "unknown",
                    "description": "This disease is not in our current knowledge base. Please consult with a plant pathologist or agricultural extension service for proper identification and treatment.",
                    "symptoms": ["Unidentified symptoms"],
                    "treatment": {
                        "immediate": ["Consult a plant pathologist", "Isolate affected plants", "Document symptoms with photos"],
                        "preventive": ["Regular monitoring", "Good cultural practices", "Proper sanitation"],
                        "organic": ["Consult organic farming experts", "Use general organic treatments cautiously"],
                    },
                    "prevention": ["Regular plant health monitoring", "Good cultural practices", "Professional consultation"],
                    "affected_parts": ["Unknown"],
                    "season": ["Unknown"],
                    "economic_impact": "Unknown - seek professional assessment",
                }
        except Exception as e:
            logger.error("Error retrieving disease info for %s: %s", disease_class, e)
            return {
                "disease_name": "Error",
                "description": "An error occurred while retrieving disease information.",
                "treatment": {"immediate": ["Consult a professional"], "preventive": [], "organic": []},
                "prevention": ["Seek professional help"],
            }

    def generate_response(self, disease_class: str, user_query: str = "", confidence: float = 0.0) -> str:
        """Generate response with template-based formatting and medical disclaimers.

        Args:
            disease_class: Predicted disease from vision model
            user_query: Optional user question (from text/voice)
            confidence: Confidence score of the prediction

        Returns:
            Formatted response with diagnosis and advice
        """
        try:
            logger.info("Generating response for disease: %s, query: %s, confidence: %.2f", disease_class, user_query, confidence)

            # Get disease information
            disease_info = self.get_disease_info(disease_class)
            disease_name = disease_info.get("disease_name", "Unknown Disease")
            plant_type = disease_info.get("plant_type", "plant")

            # Analyze query intent
            intent_keywords = self.analyze_query_intent(user_query)

            # Build response based on confidence and intent
            response_parts = []

            # Add confidence-based diagnosis
            if "healthy" in disease_class.lower():
                response_parts.append(f"Great news! Your {plant_type.lower()} appears to be healthy with no signs of disease.")
            elif confidence >= self.confidence_thresholds.get("high", 0.8):
                response_parts.append(f"Based on the image analysis, your plant appears to have {disease_name} with high confidence ({confidence:.1%}).")
            elif confidence >= self.confidence_thresholds.get("medium", 0.6):
                response_parts.append(f"Based on the image analysis, your plant may have {disease_name} with moderate confidence ({confidence:.1%}).")
            else:
                response_parts.append(
                    f"I'm not entirely certain about this diagnosis. The image suggests it might be {disease_name}, but with low confidence ({confidence:.1%}). Consider consulting with a plant pathologist."
                )

            # Add disease description if not healthy
            if "healthy" not in disease_class.lower():
                description = disease_info.get("description", "")
                if description:
                    response_parts.append(f"\n**About {disease_name}:** {description}")

            # Add treatment advice based on query intent
            treatment_info = disease_info.get("treatment", {})
            if any(keyword in intent_keywords for keyword in ["treatment", "cure", "fix", "help", "what", "how"]):
                if "healthy" not in disease_class.lower():
                    immediate_treatment = treatment_info.get("immediate", [])
                    if immediate_treatment:
                        response_parts.append("\n**Immediate Treatment:**")
                        for i, treatment in enumerate(immediate_treatment[:3], 1):
                            response_parts.append(f"{i}. {treatment}")

                    # Add organic treatment if requested
                    if any(keyword in user_query.lower() for keyword in ["organic", "natural", "eco"]):
                        organic_treatment = treatment_info.get("organic", [])
                        if organic_treatment:
                            response_parts.append("\n**Organic Treatment Options:**")
                            for i, treatment in enumerate(organic_treatment[:3], 1):
                                response_parts.append(f"{i}. {treatment}")
                else:
                    # Healthy plant maintenance advice
                    preventive = treatment_info.get("preventive", [])
                    if preventive:
                        response_parts.append("\n**To maintain plant health:**")
                        for i, tip in enumerate(preventive[:3], 1):
                            response_parts.append(f"{i}. {tip}")

            # Add prevention advice if requested
            if any(keyword in intent_keywords for keyword in ["prevent", "prevention", "avoid", "stop"]):
                prevention = disease_info.get("prevention", [])
                if prevention and "healthy" not in disease_class.lower():
                    response_parts.append("\n**Prevention Tips:**")
                    for i, tip in enumerate(prevention[:3], 1):
                        response_parts.append(f"{i}. {tip}")

            # Add medical disclaimer for disease cases
            if "healthy" not in disease_class.lower():
                response_parts.append(
                    "\n**Important:** This is an automated analysis for educational purposes only. For serious plant health issues or if symptoms persist, please consult with a qualified plant pathologist or agricultural extension service."
                )

            return "\n".join(response_parts)

        except Exception as e:
            logger.error("Error generating response: %s", e)
            return "I apologize, but I encountered an error while analyzing your plant. Please try again or consult with a plant care professional."

    def analyze_query_intent(self, query: str) -> list[str]:
        """Extract intent keywords from user query using keyword matching.

        Args:
            query: User query text

        Returns:
            List of intent keywords found in the query
        """
        if not query:
            return []

        query_lower = query.lower()
        intent_keywords = []

        # Define intent keyword categories
        intent_patterns = {
            "treatment": ["treat", "cure", "fix", "heal", "remedy", "medicine", "fungicide", "spray"],
            "symptoms": ["symptom", "sign", "look", "appear", "spot", "lesion", "discolor", "wilt"],
            "prevention": ["prevent", "avoid", "stop", "protect", "resistant", "immunity"],
            "identification": ["what", "identify", "diagnose", "disease", "problem", "wrong"],
            "care": ["care", "maintain", "grow", "water", "fertilize", "prune", "plant"],
            "organic": ["organic", "natural", "eco", "chemical-free", "biological"],
            "severity": ["serious", "severe", "bad", "dangerous", "urgent", "emergency"],
            "timing": ["when", "how long", "season", "time", "frequency"],
            "cause": ["why", "cause", "reason", "how", "spread", "infection"],
        }

        # Find matching intent keywords
        for intent_category, keywords in intent_patterns.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent_keywords.append(intent_category)
                    break  # Only add each category once

        # Add specific treatment-related intents
        if any(word in query_lower for word in ["how to", "what should", "can i", "should i"]):
            intent_keywords.append("treatment")

        # Add question-type intents
        if query_lower.startswith(("what", "how", "why", "when", "where", "which")):
            intent_keywords.append("question")

        logger.debug("Extracted intent keywords for query '%s': %s", query, intent_keywords)
        return intent_keywords

    def format_treatment_advice(self, disease_info: dict[str, Any], intent_keywords: list[str]) -> str:
        """Format treatment advice with appropriate medical disclaimers.

        Args:
            disease_info: Disease information dictionary
            intent_keywords: List of intent keywords from query analysis

        Returns:
            Formatted treatment advice string
        """
        treatment_parts = []
        treatment_data = disease_info.get("treatment", {})

        # Add immediate treatment if requested
        if "treatment" in intent_keywords or "urgent" in intent_keywords:
            immediate = treatment_data.get("immediate", [])
            if immediate:
                treatment_parts.append("**Immediate Actions:**")
                for i, action in enumerate(immediate[:4], 1):
                    treatment_parts.append(f"{i}. {action}")

        # Add organic treatment if requested
        if "organic" in intent_keywords:
            organic = treatment_data.get("organic", [])
            if organic:
                treatment_parts.append("\n**Organic Treatment Options:**")
                for i, option in enumerate(organic[:3], 1):
                    treatment_parts.append(f"{i}. {option}")

        # Add preventive measures if requested
        if "prevention" in intent_keywords:
            preventive = treatment_data.get("preventive", [])
            if preventive:
                treatment_parts.append("\n**Preventive Measures:**")
                for i, measure in enumerate(preventive[:3], 1):
                    treatment_parts.append(f"{i}. {measure}")

        # Add medical disclaimer
        if treatment_parts:
            treatment_parts.append("\n**⚠️ Disclaimer:** This advice is for educational purposes only. Always follow product labels and consult with agricultural professionals for severe cases.")

        return "\n".join(treatment_parts) if treatment_parts else ""
