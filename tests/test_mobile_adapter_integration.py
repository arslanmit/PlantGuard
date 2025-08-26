"""
Tests for mobile adapter integration.

This module tests the integration between mobile components and
existing PlantGuard adapters (Vision, Audio, Text).
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st
from PIL import Image

from src.ui.components.mobile_adapter_integration import \
    MobileAdapterIntegration


class TestMobileAdapterIntegration:
    """Test mobile adapter integration functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integration = MobileAdapterIntegration()
        
        # Clear session state
        if hasattr(st, 'session_state'):
            st.session_state.clear()

    def test_vision_adapter_initialization(self):
        """Test vision adapter initialization."""
        with patch('src.ui.components.mobile_adapter_integration.VisionAdapter') as mock_adapter:
            mock_instance = MagicMock()
            mock_adapter.return_value = mock_instance
            
            # Get vision adapter
            adapter = self.integration.vision_adapter
            
            # Verify adapter was created and cached
            assert adapter is not None
            mock_adapter.assert_called_once()
            
            # Verify caching works
            adapter2 = self.integration.vision_adapter
            assert adapter is adapter2

    def test_audio_adapter_initialization(self):
        """Test audio adapter initialization."""
        with patch('src.ui.components.mobile_adapter_integration.AudioAdapter') as mock_adapter:
            mock_instance = MagicMock()
            mock_adapter.return_value = mock_instance
            
            # Get audio adapter
            adapter = self.integration.audio_adapter
            
            # Verify adapter was created and cached
            assert adapter is not None
            mock_adapter.assert_called_once_with(model_name="openai/whisper-tiny")

    def test_text_adapter_initialization(self):
        """Test text adapter initialization."""
        with patch('src.ui.components.mobile_adapter_integration.TextAdapter') as mock_adapter:
            mock_instance = MagicMock()
            mock_adapter.return_value = mock_instance
            
            # Get text adapter
            adapter = self.integration.text_adapter
            
            # Verify adapter was created and cached
            assert adapter is not None
            mock_adapter.assert_called_once()

    def test_preprocess_mobile_image(self):
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

    def test_analyze_image_success(self):
        """Test successful image analysis."""
        test_image = Image.new('RGB', (224, 224), color='green')
        
        with patch.object(self.integration, 'vision_adapter') as mock_vision:
            mock_vision.predict.return_value = ("Healthy Plant", 0.95)
            
            with patch.object(self.integration, 'text_adapter') as mock_text:
                mock_text.get_disease_info.return_value = {
                    "disease_name": "Healthy Plant",
                    "description": "Plant appears healthy"
                }
                
                # Analyze image
                result = self.integration.analyze_image(
                    image=test_image,
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

    def test_analyze_image_error(self):
        """Test image analysis error handling."""
        test_image = Image.new('RGB', (224, 224), color='red')
        
        with patch.object(self.integration, 'vision_adapter') as mock_vision:
            mock_vision.predict.side_effect = Exception("Vision error")
            
            # Analyze image
            result = self.integration.analyze_image(
                image=test_image,
                source="test",
                component_id="test_component"
            )
            
            # Verify error result
            assert result["disease_name"] == "Analysis Error"
            assert result["confidence"] == 0.0
            assert "error" in result

    def test_transcribe_audio_success(self):
        """Test successful audio transcription."""
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            audio_file_path = tmp_file.name
        
        try:
            with patch.object(self.integration, 'audio_adapter') as mock_audio:
                mock_audio.transcribe.return_value = "What disease does my plant have?"
                
                # Transcribe audio
                result = self.integration.transcribe_audio(
                    audio_file=audio_file_path,
                    source="test",
                    component_id="test_component"
                )
                
                # Verify result
                assert result["transcription"] == "What disease does my plant have?"
                assert result["success"] is True
                assert result["source"] == "test"
                assert result["component_id"] == "test_component"
                
        finally:
            # Clean up
            Path(audio_file_path).unlink(missing_ok=True)

    def test_transcribe_audio_error(self):
        """Test audio transcription error handling."""
        with patch.object(self.integration, 'audio_adapter') as mock_audio:
            mock_audio.transcribe.side_effect = Exception("Audio error")
            
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

    def test_process_text_query_success(self):
        """Test successful text query processing."""
        with patch.object(self.integration, 'text_adapter') as mock_text:
            mock_text.generate_response.return_value = "This appears to be a fungal infection."
            
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

    def test_process_text_query_with_context(self):
        """Test text query processing with analysis context."""
        # Set up analysis results in session state
        st.session_state.analysis_results = [{
            "disease_name": "Leaf Spot",
            "confidence": 0.85
        }]
        
        with patch.object(self.integration, 'text_adapter') as mock_text:
            mock_text.generate_response.return_value = "Based on the analysis, this is leaf spot disease."
            
            # Process text query
            result = self.integration.process_text_query(
                text="How do I treat this?",
                source="test",
                component_id="test_component"
            )
            
            # Verify context was used
            mock_text.generate_response.assert_called_once()
            call_args = mock_text.generate_response.call_args
            assert call_args[1]["disease_class"] == "Leaf Spot"
            assert call_args[1]["confidence"] == 0.85

    def test_preprocess_mobile_text(self):
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

    def test_get_recent_analysis(self):
        """Test getting recent analysis results."""
        # Set up analysis results
        st.session_state.analysis_results = [
            {"disease_name": "Disease 1", "timestamp": "2023-01-01"},
            {"disease_name": "Disease 2", "timestamp": "2023-01-02"},
            {"disease_name": "Disease 3", "timestamp": "2023-01-03"},
        ]
        
        # Get recent analysis
        recent = self.integration.get_recent_analysis(limit=2)
        
        # Verify results
        assert len(recent) == 2
        assert recent[0]["disease_name"] == "Disease 2"
        assert recent[1]["disease_name"] == "Disease 3"

    def test_clear_analysis_history(self):
        """Test clearing analysis history."""
        # Set up history
        st.session_state.analysis_results = [{"test": "data"}]
        st.session_state.chat_history = [{"test": "message"}]
        
        # Clear history
        self.integration.clear_analysis_history()
        
        # Verify cleared
        assert st.session_state.analysis_results == []
        assert st.session_state.chat_history == []

    def test_get_adapter_status(self):
        """Test getting adapter status."""
        with patch.object(self.integration, 'vision_adapter', return_value=MagicMock()):
            with patch.object(self.integration, 'audio_adapter', return_value=MagicMock()):
                with patch.object(self.integration, 'text_adapter', return_value=MagicMock()):
                    
                    status = self.integration.get_adapter_status()
                    
                    # Verify all adapters are available
                    assert status["vision_adapter"] is True
                    assert status["audio_adapter"] is True
                    assert status["text_adapter"] is True

    def test_adapter_status_with_errors(self):
        """Test adapter status when adapters fail to initialize."""
        with patch.object(self.integration, 'vision_adapter', side_effect=Exception("Vision error")):
            with patch.object(self.integration, 'audio_adapter', side_effect=Exception("Audio error")):
                with patch.object(self.integration, 'text_adapter', side_effect=Exception("Text error")):
                    
                    status = self.integration.get_adapter_status()
                    
                    # Verify all adapters are unavailable
                    assert status["vision_adapter"] is False
                    assert status["audio_adapter"] is False
                    assert status["text_adapter"] is False

    def test_mobile_config_defaults(self):
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


@pytest.fixture
def mock_streamlit_session():
    """Mock Streamlit session state."""
    with patch('streamlit.session_state', {}):
        yield


class TestMobileAdapterIntegrationIntegration:
    """Integration tests for mobile adapter integration."""

    def test_full_image_analysis_workflow(self, mock_streamlit_session):
        """Test complete image analysis workflow."""
        integration = MobileAdapterIntegration()
        test_image = Image.new('RGB', (500, 400), color='blue')
        
        with patch('src.core.vision.VisionAdapter') as mock_vision_class:
            with patch('src.core.nlp.TextAdapter') as mock_text_class:
                # Set up mocks
                mock_vision = MagicMock()
                mock_vision.predict.return_value = ("Powdery Mildew", 0.87)
                mock_vision_class.return_value = mock_vision
                
                mock_text = MagicMock()
                mock_text.get_disease_info.return_value = {
                    "disease_name": "Powdery Mildew",
                    "description": "A fungal disease affecting leaves"
                }
                mock_text_class.return_value = mock_text
                
                # Perform analysis
                result = integration.analyze_image(
                    image=test_image,
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

    def test_full_text_processing_workflow(self, mock_streamlit_session):
        """Test complete text processing workflow."""
        integration = MobileAdapterIntegration()
        
        # Set up analysis context
        st.session_state.analysis_results = [{
            "disease_name": "Rust Disease",
            "confidence": 0.92
        }]
        
        with patch('src.core.nlp.TextAdapter') as mock_text_class:
            mock_text = MagicMock()
            mock_text.generate_response.return_value = "For rust disease, apply fungicide spray."
            mock_text_class.return_value = mock_text
            
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
            assert len(st.session_state.chat_history) == 2  # User + Assistant messages