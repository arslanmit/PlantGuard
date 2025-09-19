"""
Tests for mobile adapter integration.

This module tests the integration between mobile components and
existing PlantGuard adapters (Vision, Audio, Text) with proper
mock interfaces and dependency injection.
"""

import tempfile
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st
from PIL import Image

from plantguard.ui.components.mobile_adapter_integration import \
    MobileAdapterIntegration
from tests.fixtures.mobile_test_fixtures import (MockAudioAdapter,
                                                 MockTextAdapter,
                                                 MockVisionAdapter,
                                                 TestDataFactory)


class TestMobileAdapterIntegration:
    """Test mobile adapter integration functionality with proper mocking."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.integration = MobileAdapterIntegration()
        
        # Clear session state
        with suppress(AttributeError):
            if hasattr(st, 'session_state'):
                st.session_state.clear()

    def test_vision_adapter_initialization(self, mock_streamlit_session) -> None:
        """Test vision adapter initialization with proper mocking."""
        # Test direct adapter injection (dependency injection pattern)
        mock_adapter = MockVisionAdapter()
        self.integration._vision_adapter = mock_adapter
        
        # Get vision adapter
        adapter = self.integration.vision_adapter
        
        # Verify adapter was injected correctly
        assert adapter is not None
        assert adapter is mock_adapter
        
        # Test adapter functionality
        result = adapter.predict("test")
        assert result == ("Healthy Plant", 0.95)

    def test_audio_adapter_initialization(self, mock_streamlit_session) -> None:
        """Test audio adapter initialization with proper mocking."""
        # Test direct adapter injection (dependency injection pattern)
        mock_adapter = MockAudioAdapter()
        self.integration._audio_adapter = mock_adapter
        
        # Get audio adapter
        adapter = self.integration.audio_adapter
        
        # Verify adapter was injected correctly
        assert adapter is not None
        assert adapter is mock_adapter
        
        # Test adapter functionality
        result = adapter.transcribe("test")
        assert result == "What disease does my plant have?"

    def test_text_adapter_initialization(self, mock_streamlit_session) -> None:
        """Test text adapter initialization with proper mocking."""
        # Test direct adapter injection (dependency injection pattern)
        mock_adapter = MockTextAdapter()
        self.integration._text_adapter = mock_adapter
        
        # Get text adapter
        adapter = self.integration.text_adapter
        
        # Verify adapter was injected correctly
        assert adapter is not None
        assert adapter is mock_adapter
        
        # Test adapter functionality
        result = adapter.generate_response()
        assert "fungal infection" in result.lower()

    def test_preprocess_mobile_image(self) -> None:
        """Test mobile image preprocessing."""
        # Create test image
        test_image = Image.new('RGB', (2000, 1500), color='red')
        
        # Preprocess image
        processed_image = self.integration.preprocess_mobile_image(test_image, "camera")
        
        # Verify image was processed
        assert processed_image is not None
        assert processed_image.mode == "RGB"
        
        # Verify size was reduced (should be within max_size limits)
        max_size = self.integration.mobile_config["image_preprocessing"]["max_size"]
        assert processed_image.size[0] <= max_size[0]
        assert processed_image.size[1] <= max_size[1]

    def test_analyze_image_success(self, mock_streamlit_session, sample_test_image) -> None:
        """Test successful image analysis with proper mocking."""
        # Set up mock adapters
        mock_vision = MockVisionAdapter()
        mock_vision.predict.return_value = ("Healthy Plant", 0.95)
        
        mock_text = MockTextAdapter()
        mock_text.get_disease_info.return_value = {
            "disease_name": "Healthy Plant",
            "description": "Plant appears healthy"
        }
        
        # Inject mock adapters
        self.integration._vision_adapter = mock_vision
        self.integration._text_adapter = mock_text
        
        # Analyze image
        result = self.integration.analyze_image(
            image=sample_test_image,
            source="test",
            component_id="test_component"
        )
        
        # Verify result
        assert result["disease_name"] == "Healthy Plant"
        assert result["confidence"] == 0.95
        assert result["source"] == "test"
        assert result["component_id"] == "test_component"
        assert result["preprocessing_applied"] is True
        assert "disease_info" in result
        
        # Verify adapters were called correctly
        mock_vision.predict.assert_called_once()
        mock_text.get_disease_info.assert_called_once_with("Healthy Plant")

    def test_analyze_image_error(self, mock_streamlit_session, sample_test_image) -> None:
        """Test image analysis error handling with proper mocking."""
        # Set up mock adapter with error
        mock_vision = MockVisionAdapter()
        mock_vision.predict.side_effect = Exception("Vision error")
        
        # Inject mock adapter
        self.integration._vision_adapter = mock_vision
        
        # Analyze image
        result = self.integration.analyze_image(
            image=sample_test_image,
            source="test",
            component_id="test_component"
        )
        
        # Verify error result
        assert result["disease_name"] == "Analysis Error"
        assert result["confidence"] == 0.0
        assert "error" in result
        assert result["error"] == "Vision error"

    def test_transcribe_audio_success(self, mock_streamlit_session, temp_audio_file) -> None:
        """Test successful audio transcription with proper mocking."""
        # Set up mock adapter
        mock_audio = MockAudioAdapter()
        mock_audio.transcribe.return_value = "What disease does my plant have?"
        
        # Inject mock adapter
        self.integration._audio_adapter = mock_audio
        
        # Transcribe audio
        result = self.integration.transcribe_audio(
            audio_file=temp_audio_file,
            source="test",
            component_id="test_component"
        )
        
        # Verify result
        assert result["transcription"] == "What disease does my plant have?"
        assert result["success"] is True
        assert result["source"] == "test"
        assert result["component_id"] == "test_component"
        
        # Verify chat history was updated
        assert "chat_history" in mock_streamlit_session
        assert len(mock_streamlit_session["chat_history"]) == 1
        assert mock_streamlit_session["chat_history"][0]["content"] == "What disease does my plant have?"

    def test_transcribe_audio_error(self, mock_streamlit_session) -> None:
        """Test audio transcription error handling with proper mocking."""
        # Set up mock adapter with error
        mock_audio = MockAudioAdapter()
        mock_audio.transcribe.side_effect = Exception("Audio error")
        
        # Inject mock adapter
        self.integration._audio_adapter = mock_audio
        
        # Transcribe audio
        result = self.integration.transcribe_audio(
            audio_file="nonexistent.wav",
            source="test",
            component_id="test_component"
        )
        
        # Verify error result
        assert result["transcription"] == ""
        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Audio error"

    def test_process_text_query_success(self, mock_streamlit_session) -> None:
        """Test successful text query processing with proper mocking."""
        # Set up mock adapter
        mock_text = MockTextAdapter()
        mock_text.generate_response.return_value = "This appears to be a fungal infection."
        
        # Inject mock adapter
        self.integration._text_adapter = mock_text
        
        # Process text query
        result = self.integration.process_text_query(
            text="What's wrong with my plant?",
            source="test",
            component_id="test_component"
        )
        
        # Verify result
        assert result["query"] == "What's wrong with my plant?"
        assert result["response"] == "This appears to be a fungal infection."
        assert result["source"] == "test"
        assert result["component_id"] == "test_component"
        
        # Verify chat history was updated
        assert "chat_history" in mock_streamlit_session
        assert len(mock_streamlit_session["chat_history"]) == 2  # User + Assistant messages

    def test_process_text_query_with_context(self, mock_streamlit_session, sample_analysis_results) -> None:
        """Test text query processing with analysis context using proper mocking."""
        # Set up analysis results in session state
        mock_streamlit_session["analysis_results"] = sample_analysis_results
        
        # Set up mock adapter
        mock_text = MockTextAdapter()
        mock_text.generate_response.return_value = "Based on the analysis, this is powdery mildew disease."
        
        # Inject mock adapter
        self.integration._text_adapter = mock_text
        
        # Process text query
        result = self.integration.process_text_query(
            text="How do I treat this?",
            source="test",
            component_id="test_component"
        )
        
        # Verify context was used (most recent analysis)
        mock_text.generate_response.assert_called_once()
        call_args = mock_text.generate_response.call_args
        assert call_args[1]["disease_class"] == "Leaf Spot"  # Most recent from sample data
        assert call_args[1]["confidence"] == 0.87

    def test_preprocess_mobile_text(self) -> None:
        """Test mobile text preprocessing."""
        # Test whitespace cleaning
        text = "  What's   wrong   with   my   plant?  "
        processed = self.integration._preprocess_mobile_text(text)
        assert processed == "What's wrong with my plant?"
        
        # Test length truncation
        long_text = "a" * 1500  # Longer than max_length (1000)
        processed = self.integration._preprocess_mobile_text(long_text)
        assert len(processed) <= 1000
        assert processed.endswith("...")

    def test_get_recent_analysis(self, mock_streamlit_session) -> None:
        """Test getting recent analysis results with proper session state mocking."""
        # Set up analysis results
        test_results = [
            {"disease_name": "Disease 1", "timestamp": "2023-01-01"},
            {"disease_name": "Disease 2", "timestamp": "2023-01-02"},
            {"disease_name": "Disease 3", "timestamp": "2023-01-03"},
        ]
        mock_streamlit_session["analysis_results"] = test_results
        
        # Get recent analysis
        recent = self.integration.get_recent_analysis(limit=2)
        
        # Verify results
        assert len(recent) == 2
        assert recent[0]["disease_name"] == "Disease 2"
        assert recent[1]["disease_name"] == "Disease 3"

    def test_clear_analysis_history(self, mock_streamlit_session) -> None:
        """Test clearing analysis history with proper session state mocking."""
        # Set up history
        mock_streamlit_session["analysis_results"] = [{"test": "data"}]
        mock_streamlit_session["chat_history"] = [{"test": "message"}]
        
        # Clear history
        self.integration.clear_analysis_history()
        
        # Verify cleared
        assert mock_streamlit_session["analysis_results"] == []
        assert mock_streamlit_session["chat_history"] == []

    def test_get_adapter_status(self) -> None:
        """Test getting adapter status with proper mock injection."""
        # Inject mock adapters
        self.integration._vision_adapter = MockVisionAdapter()
        self.integration._audio_adapter = MockAudioAdapter()
        self.integration._text_adapter = MockTextAdapter()
        
        status = self.integration.get_adapter_status()
        
        # Verify all adapters are available
        assert status["vision_adapter"] is True
        assert status["audio_adapter"] is True
        assert status["text_adapter"] is True

    def test_adapter_status_with_errors(self) -> None:
        """Test adapter status when adapters fail to initialize."""
        # Create properties that raise exceptions
        def vision_error() -> Any:
            raise Exception("Vision error")
        def audio_error() -> Any:
            raise Exception("Audio error")
        def text_error() -> Any:
            raise Exception("Text error")
            
        # Patch the properties to raise exceptions
        with patch.object(type(self.integration), 'vision_adapter', property(lambda self: vision_error())):
            with patch.object(type(self.integration), 'audio_adapter', property(lambda self: audio_error())):
                with patch.object(type(self.integration), 'text_adapter', property(lambda self: text_error())):
                    
                    status = self.integration.get_adapter_status()
                    
                    # Verify all adapters are unavailable
                    assert status["vision_adapter"] is False
                    assert status["audio_adapter"] is False
                    assert status["text_adapter"] is False

    def test_mobile_config_defaults(self) -> None:
        """Test mobile configuration defaults."""
        config = self.integration.mobile_config
        
        # Verify image preprocessing config
        assert config["image_preprocessing"]["max_size"] == (1920, 1080)
        assert config["image_preprocessing"]["quality"] == 85
        assert config["image_preprocessing"]["auto_orient"] is True
        
        # Verify audio preprocessing config
        assert config["audio_preprocessing"]["sample_rate"] == 16000
        assert config["audio_preprocessing"]["max_duration"] == 60
        
        # Verify text preprocessing config
        assert config["text_preprocessing"]["max_length"] == 1000
        assert config["text_preprocessing"]["clean_whitespace"] is True


class TestMobileAdapterIntegrationIntegration:
    """Integration tests for mobile adapter integration with comprehensive mocking."""

    def test_full_image_analysis_workflow(self, mock_streamlit_session, sample_test_image) -> None:
        """Test complete image analysis workflow with proper dependency injection."""
        integration = MobileAdapterIntegration()
        
        # Set up mock adapters
        mock_vision = MockVisionAdapter()
        mock_vision.predict.return_value = ("Powdery Mildew", 0.87)
        
        mock_text = MockTextAdapter()
        mock_text.get_disease_info.return_value = {
            "disease_name": "Powdery Mildew",
            "description": "A fungal disease affecting leaves"
        }
        
        # Inject mock adapters
        integration._vision_adapter = mock_vision
        integration._text_adapter = mock_text
        
        # Perform analysis
        result = integration.analyze_image(
            image=sample_test_image,
            source="camera",
            component_id="test_camera"
        )
        
        # Verify complete workflow
        assert result["disease_name"] == "Powdery Mildew"
        assert result["confidence"] == 0.87
        assert result["preprocessing_applied"] is True
        assert "disease_info" in result
        
        # Verify adapters were called
        mock_vision.predict.assert_called_once()
        mock_text.get_disease_info.assert_called_once_with("Powdery Mildew")
        
        # Verify session state was updated
        assert len(mock_streamlit_session["analysis_results"]) == 1

    def test_full_text_processing_workflow(self, mock_streamlit_session) -> None:
        """Test complete text processing workflow with proper mocking."""
        integration = MobileAdapterIntegration()
        
        # Set up analysis context
        mock_streamlit_session["analysis_results"] = [{
            "disease_name": "Rust Disease",
            "confidence": 0.92
        }]
        
        # Set up mock adapter
        mock_text = MockTextAdapter()
        mock_text.generate_response.return_value = "For rust disease, apply fungicide spray."
        
        # Inject mock adapter
        integration._text_adapter = mock_text
        
        # Process text query
        result = integration.process_text_query(
            text="How do I treat this disease?",
            source="chat",
            component_id="test_chat"
        )
        
        # Verify workflow
        assert result["response"] == "For rust disease, apply fungicide spray."
        assert result["disease_context"] == "Rust Disease"
        assert result["confidence_context"] == 0.92
        
        # Verify chat history was updated
        assert len(mock_streamlit_session["chat_history"]) == 2  # User + Assistant messages

    def test_full_audio_transcription_workflow(self, mock_streamlit_session, temp_audio_file) -> None:
        """Test complete audio transcription workflow with proper mocking."""
        integration = MobileAdapterIntegration()
        
        # Set up mock adapter
        mock_audio = MockAudioAdapter()
        mock_audio.transcribe.return_value = "My plant leaves are turning yellow"
        
        # Inject mock adapter
        integration._audio_adapter = mock_audio
        
        # Transcribe audio
        result = integration.transcribe_audio(
            audio_file=temp_audio_file,
            source="voice",
            component_id="test_voice"
        )
        
        # Verify workflow
        assert result["transcription"] == "My plant leaves are turning yellow"
        assert result["success"] is True
        assert result["preprocessing_applied"] is True
        
        # Verify chat history was updated
        assert len(mock_streamlit_session["chat_history"]) == 1
        assert mock_streamlit_session["chat_history"][0]["content"] == "My plant leaves are turning yellow"

    def test_end_to_end_multimodal_workflow(self, mock_streamlit_session, sample_test_image, temp_audio_file) -> None:
        """Test end-to-end multimodal workflow with all adapters."""
        integration = MobileAdapterIntegration()
        
        # Set up all mock adapters
        mock_vision = MockVisionAdapter()
        mock_vision.predict.return_value = ("Leaf Blight", 0.91)
        
        mock_audio = MockAudioAdapter()
        mock_audio.transcribe.return_value = "What can I do about this disease?"
        
        mock_text = MockTextAdapter()
        mock_text.get_disease_info.return_value = {"disease_name": "Leaf Blight", "treatment": "Apply copper fungicide"}
        mock_text.generate_response.return_value = "For leaf blight, I recommend applying copper fungicide."
        
        # Inject all mock adapters
        integration._vision_adapter = mock_vision
        integration._audio_adapter = mock_audio
        integration._text_adapter = mock_text
        
        # Step 1: Analyze image
        image_result = integration.analyze_image(
            image=sample_test_image,
            source="camera",
            component_id="test_camera"
        )
        
        # Step 2: Transcribe audio question
        audio_result = integration.transcribe_audio(
            audio_file=temp_audio_file,
            source="voice",
            component_id="test_voice"
        )
        
        # Step 3: Process text query with context
        text_result = integration.process_text_query(
            text=audio_result["transcription"],
            source="voice_to_text",
            component_id="test_chat"
        )
        
        # Verify complete workflow
        assert image_result["disease_name"] == "Leaf Blight"
        assert audio_result["transcription"] == "What can I do about this disease?"
        assert text_result["response"] == "For leaf blight, I recommend applying copper fungicide."
        assert text_result["disease_context"] == "Leaf Blight"
        
        # Verify session state contains all results
        assert len(mock_streamlit_session["analysis_results"]) == 1
        assert len(mock_streamlit_session["chat_history"]) == 3  # Audio transcription + User query + Assistant response