"""
Test suite for Mobile Display Components.

This module provides comprehensive testing for the mobile display components
including MobileAnalysisDisplay, MobileRecommendations, and MobileChatInterface.
"""

import logging
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import streamlit as st
from PIL import Image

from .mobile_analysis_display import MobileAnalysisDisplay
from .mobile_chat_interface import MobileChatInterface
from .mobile_recommendations import MobileRecommendations

logger = logging.getLogger(__name__)


class TestMobileAnalysisDisplay:
    """Test suite for MobileAnalysisDisplay component."""

    def setup_method(self):
        """Set up test environment."""
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        # Create test component
        self.component = MobileAnalysisDisplay("test_analysis", "Test Analysis Display")

    def test_component_initialization(self):
        """Test component initialization."""
        assert self.component.component_id == "test_analysis"
        assert self.component.title == "Test Analysis Display"
        assert "analysis_data" in self.component.get_state()["data"]

    def test_empty_state_rendering(self):
        """Test rendering when no analysis results are available."""
        # Ensure no analysis results
        if "analysis_results" in st.session_state:
            del st.session_state["analysis_results"]

        # This should not raise an exception
        try:
            self.component.render()
        except Exception as e:
            pytest.fail(f"Empty state rendering failed: {e}")

    def test_analysis_results_processing(self):
        """Test processing of analysis results."""
        # Create mock analysis results
        mock_image = Image.new("RGB", (100, 100), color="green")

        analysis_results = [
            {
                "timestamp": datetime.now().isoformat(),
                "image": mock_image,
                "prediction": ("Apple Scab", 0.85),
                "source": "upload",
                "component_id": "test_upload",
            },
            {
                "timestamp": datetime.now().isoformat(),
                "image": mock_image,
                "prediction": ("Healthy Plant", 0.92),
                "source": "camera",
                "component_id": "test_camera",
            },
        ]

        st.session_state.analysis_results = analysis_results

        # Test getting results
        results = self.component._get_analysis_results()
        assert len(results) == 2
        assert results[0]["prediction"][0] in ["Apple Scab", "Healthy Plant"]

    def test_confidence_level_calculation(self):
        """Test confidence level categorization."""
        assert self.component._get_confidence_level(0.9) == "high"
        assert self.component._get_confidence_level(0.7) == "medium"
        assert self.component._get_confidence_level(0.3) == "low"

    def test_timestamp_formatting(self):
        """Test timestamp formatting for display."""
        timestamp = datetime.now().isoformat()
        formatted = self.component._format_timestamp(timestamp)
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_disease_info_loading(self):
        """Test disease information loading from knowledge base."""
        # Test with existing disease
        disease_info = self.component._get_disease_info("Apple___Apple_scab")

        # Should either find info or return None gracefully
        assert disease_info is None or isinstance(disease_info, dict)

    def test_display_mode_switching(self):
        """Test display mode switching functionality."""
        # Test setting different display modes
        self.component._set_display_mode("history")
        state = self.component.get_state()
        assert state["data"]["analysis_data"]["display_mode"] == "history"

        self.component._set_display_mode("detailed")
        state = self.component.get_state()
        assert state["data"]["analysis_data"]["display_mode"] == "detailed"

    def test_result_sharing(self):
        """Test result sharing functionality."""
        mock_result = {"prediction": ("Test Disease", 0.75), "timestamp": datetime.now().isoformat(), "source": "test"}

        # This should not raise an exception
        try:
            self.component._share_result(mock_result)
        except Exception as e:
            pytest.fail(f"Result sharing failed: {e}")

    def test_clear_results(self):
        """Test clearing analysis results."""
        # Add some results first
        st.session_state.analysis_results = [{"test": "data"}]

        # Clear results
        self.component._clear_results()

        # Check results are cleared
        assert len(st.session_state.get("analysis_results", [])) == 0


class TestMobileRecommendations:
    """Test suite for MobileRecommendations component."""

    def setup_method(self):
        """Set up test environment."""
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        # Create test component
        self.component = MobileRecommendations("test_recommendations", "Test Recommendations")

    def test_component_initialization(self):
        """Test component initialization."""
        assert self.component.component_id == "test_recommendations"
        assert self.component.title == "Test Recommendations"
        assert "recommendations_data" in self.component.get_state()["data"]

    def test_no_analysis_state(self):
        """Test rendering when no analysis is available."""
        # Ensure no analysis results
        if "analysis_results" in st.session_state:
            del st.session_state["analysis_results"]

        # This should not raise an exception
        try:
            self.component.render()
        except Exception as e:
            pytest.fail(f"No analysis state rendering failed: {e}")

    def test_current_disease_update(self):
        """Test updating current disease in state."""
        self.component._update_current_disease("Test Disease", 0.8)

        state = self.component.get_state()
        recommendations_data = state["data"]["recommendations_data"]

        assert recommendations_data["current_disease"] == "Test Disease"
        assert recommendations_data["current_confidence"] == 0.8

    def test_confidence_warning_levels(self):
        """Test confidence-based warning generation."""
        # Test different confidence levels
        assert self.component._get_confidence_level(0.9) == "high"
        assert self.component._get_confidence_level(0.7) == "medium"
        assert self.component._get_confidence_level(0.3) == "low"

    def test_treatment_templates_loading(self):
        """Test loading of treatment templates."""
        templates = self.component._load_treatment_templates()
        assert isinstance(templates, dict)
        assert "generic_immediate" in templates
        assert "generic_preventive" in templates

    def test_disease_info_retrieval(self):
        """Test disease information retrieval."""
        # Test with non-existent disease
        disease_info = self.component._get_disease_info("NonExistent Disease")
        assert disease_info is None

    def test_recommendations_sharing(self):
        """Test recommendations sharing functionality."""
        # This should not raise an exception
        try:
            self.component._generate_shareable_recommendations("Test Disease", 0.75)
        except Exception as e:
            pytest.fail(f"Recommendations sharing failed: {e}")

    def test_custom_notes_saving(self):
        """Test saving custom notes."""
        test_notes = "These are my test notes about the treatment."
        self.component._save_custom_notes(test_notes)

        state = self.component.get_state()
        recommendations_data = state["data"]["recommendations_data"]
        assert recommendations_data["custom_notes"] == test_notes

    def test_section_expansion_state(self):
        """Test section expansion state management."""
        # Test default expansion states
        assert self.component._is_section_expanded("immediate")
        assert not self.component._is_section_expanded("preventive")

    def test_recommendations_with_analysis_context(self):
        """Test recommendations with analysis context."""
        # Create mock analysis result
        mock_image = Image.new("RGB", (100, 100), color="green")

        analysis_result = {"timestamp": datetime.now().isoformat(), "image": mock_image, "prediction": ("Apple Scab", 0.85), "source": "upload"}

        st.session_state.analysis_results = [analysis_result]

        # Test getting current analysis result
        current_result = self.component._get_current_analysis_result()
        assert current_result is not None
        assert current_result["prediction"][0] == "Apple Scab"


class TestMobileChatInterface:
    """Test suite for MobileChatInterface component."""

    def setup_method(self):
        """Set up test environment."""
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        # Create test component
        self.component = MobileChatInterface("test_chat", "Test Chat")

    def test_component_initialization(self):
        """Test component initialization."""
        assert self.component.component_id == "test_chat"
        assert self.component.title == "Test Chat"
        assert "chat_data" in self.component.get_state()["data"]

        # Check welcome message was added
        state = self.component.get_state()
        messages = state["data"]["chat_data"]["messages"]
        assert len(messages) > 0
        assert messages[0]["type"] == "bot"

    def test_message_addition(self):
        """Test adding messages to chat."""
        test_message = {"id": "test_msg_1", "type": "user", "content": "Test message", "timestamp": datetime.now().isoformat(), "context": None}

        self.component._add_message(test_message)

        state = self.component.get_state()
        messages = state["data"]["chat_data"]["messages"]

        # Should have welcome message + test message
        assert len(messages) >= 2
        assert any(msg["content"] == "Test message" for msg in messages)

    def test_typing_indicator(self):
        """Test typing indicator functionality."""
        # Set typing
        self.component._set_typing(True)
        assert self.component.is_typing()

        # Clear typing
        self.component._set_typing(False)
        assert not self.component.is_typing()

    def test_context_building(self):
        """Test chat context building."""
        # Add mock analysis results
        mock_image = Image.new("RGB", (100, 100), color="green")

        analysis_results = [{"timestamp": datetime.now().isoformat(), "image": mock_image, "prediction": ("Apple Scab", 0.85), "source": "upload"}]

        st.session_state.analysis_results = analysis_results

        # Update context
        self.component._update_chat_context()

        context = self.component._get_current_context()
        assert "analysis_results" in context
        assert len(context["analysis_results"]) > 0

    def test_fallback_responses(self):
        """Test fallback response generation."""
        # Test water-related question
        response = self.component._get_fallback_response("How often should I water my plant?")
        assert "water" in response.lower()

        # Test light-related question
        response = self.component._get_fallback_response("Does my plant need more sunlight?")
        assert "light" in response.lower()

        # Test disease-related question
        response = self.component._get_fallback_response("My plant looks sick")
        assert "disease" in response.lower() or "sick" in response.lower()

    def test_message_timestamp_formatting(self):
        """Test message timestamp formatting."""
        timestamp = datetime.now().isoformat()
        formatted = self.component._format_message_timestamp(timestamp)
        assert isinstance(formatted, str)
        # Should be in HH:MM format
        assert ":" in formatted

    def test_chat_clearing(self):
        """Test chat clearing functionality."""
        # Add some messages first
        test_message = {"id": "test_msg", "type": "user", "content": "Test", "timestamp": datetime.now().isoformat(), "context": None}

        self.component._add_message(test_message)

        # Clear chat
        self.component._clear_chat()

        # Should only have welcome message
        state = self.component.get_state()
        messages = state["data"]["chat_data"]["messages"]
        assert len(messages) == 1
        assert messages[0]["type"] == "bot"

    def test_message_history_limits(self):
        """Test message history length limits."""
        # Add many messages
        for i in range(60):  # More than max_history_length (50)
            test_message = {
                "id": f"test_msg_{i}",
                "type": "user",
                "content": f"Test message {i}",
                "timestamp": datetime.now().isoformat(),
                "context": None,
            }
            self.component._add_message(test_message)

        # Check history is limited
        state = self.component.get_state()
        messages = state["data"]["chat_data"]["messages"]
        assert len(messages) <= self.component.chat_config["max_history_length"]

    @patch("src.core.nlp.TextAdapter")
    def test_bot_response_generation(self, mock_text_adapter):
        """Test bot response generation with mocked adapters."""
        # Mock the text adapter
        mock_text_instance = Mock()
        mock_text_instance.generate_response.return_value = "This is a test response from the bot."
        mock_text_adapter.return_value = mock_text_instance

        # Test response generation
        response = self.component._generate_bot_response("Test question")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_context_prompt_building(self):
        """Test context-aware prompt building."""
        context = {"current_disease": {"name": "Apple Scab", "confidence": 0.85}, "analysis_results": [{"prediction": ("Apple Scab", 0.85)}]}

        prompt = self.component._build_context_prompt("How do I treat this?", context)
        assert "Apple Scab" in prompt
        assert "0.85" in prompt or "85%" in prompt or "85.0%" in prompt
        assert "How do I treat this?" in prompt


class TestMobileDisplayComponentsIntegration:
    """Integration tests for mobile display components."""

    def setup_method(self):
        """Set up test environment."""
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    def test_components_integration(self):
        """Test integration between display components."""
        # Create all components
        analysis_display = MobileAnalysisDisplay("test_analysis")
        recommendations = MobileRecommendations("test_recommendations")
        chat_interface = MobileChatInterface("test_chat")

        # Create mock analysis result
        mock_image = Image.new("RGB", (100, 100), color="green")

        analysis_result = {"timestamp": datetime.now().isoformat(), "image": mock_image, "prediction": ("Apple Scab", 0.85), "source": "upload"}

        st.session_state.analysis_results = [analysis_result]

        # Test that all components can access the shared analysis results
        assert analysis_display.has_results()
        assert recommendations.has_recommendations()

        # Test chat context includes analysis results
        chat_interface._update_chat_context()
        context = chat_interface._get_current_context()
        assert len(context["analysis_results"]) > 0

    def test_css_class_generation(self):
        """Test CSS class generation for AI agent discovery."""
        analysis_display = MobileAnalysisDisplay("test_analysis")

        css_classes = analysis_display.get_css_classes()
        assert "mobile-component" in css_classes
        assert "mobile-mobileanalysisdisplay" in css_classes
        assert "ai-discoverable" in css_classes

    def test_error_handling_integration(self):
        """Test error handling across components."""
        analysis_display = MobileAnalysisDisplay("test_analysis")

        # Test error handling doesn't crash
        try:
            analysis_display.handle_error(Exception("Test error"), category=ErrorCategory.COMPONENT, severity=ErrorSeverity.MEDIUM)
        except Exception as e:
            pytest.fail(f"Error handling failed: {e}")

    def test_state_management_integration(self):
        """Test state management across components."""
        analysis_display = MobileAnalysisDisplay("test_analysis")
        recommendations = MobileRecommendations("test_recommendations")

        # Test state isolation
        analysis_state = analysis_display.get_state()
        recommendations_state = recommendations.get_state()

        assert analysis_state["component_id"] != recommendations_state["component_id"]
        assert "analysis_data" in analysis_state["data"]
        assert "recommendations_data" in recommendations_state["data"]


def run_mobile_display_tests() -> None:
    """Run all mobile display component tests."""
    print("[TEST] Running Mobile Display Components Tests...")

    try:
        # Test MobileAnalysisDisplay
        print("Testing MobileAnalysisDisplay...")
        test_analysis = TestMobileAnalysisDisplay()
        test_analysis.setup_method()
        test_analysis.test_component_initialization()
        test_analysis.test_empty_state_rendering()
        test_analysis.test_confidence_level_calculation()
        print("[DONE] MobileAnalysisDisplay tests passed")

        # Test MobileRecommendations
        print("Testing MobileRecommendations...")
        test_recommendations = TestMobileRecommendations()
        test_recommendations.setup_method()
        test_recommendations.test_component_initialization()
        test_recommendations.test_no_analysis_state()
        test_recommendations.test_confidence_warning_levels()
        print("[DONE] MobileRecommendations tests passed")

        # Test MobileChatInterface
        print("Testing MobileChatInterface...")
        test_chat = TestMobileChatInterface()
        test_chat.setup_method()
        test_chat.test_component_initialization()
        test_chat.test_message_addition()
        test_chat.test_typing_indicator()
        test_chat.test_fallback_responses()
        print("[DONE] MobileChatInterface tests passed")

        # Test Integration
        print("Testing Integration...")
        test_integration = TestMobileDisplayComponentsIntegration()
        test_integration.setup_method()
        test_integration.test_components_integration()
        test_integration.test_css_class_generation()
        print("[DONE] Integration tests passed")

        print("[SUCCESS] All Mobile Display Components tests passed!")
        return True

    except Exception as e:
        print(f"[TODO] Tests failed: {e}")
        return False


if __name__ == "__main__":
    run_mobile_display_tests()
