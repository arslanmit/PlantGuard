"""
Comprehensive Test Suite for PlantGuard Single Page Application

This test suite covers:
- Unit tests for SPA components
- Integration tests for multimodal workflows
- Error handling and recovery testing
- Performance and memory management testing
- AI agent programmatic interface testing
- Responsive layout and accessibility testing
"""

import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import streamlit as st
from PIL import Image
import numpy as np

# Add src to Python path
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import SPA module
import spa_app
from spa_app import PlantGuardSPA, init_session_state


class TestPlantGuardSPAUnit:
    """Unit tests for PlantGuard SPA core functionality."""
    
    @pytest.fixture
    def spa_instance(self):
        """Create SPA instance for testing."""
        # Mock Streamlit session state
        st.session_state = {}
        init_session_state()
        
        return PlantGuardSPA()
    
    @pytest.fixture
    def sample_image(self):
        """Create sample image for testing."""
        # Create a simple test image
        img = Image.new('RGB', (224, 224), color='green')
        return img
    
    def test_spa_initialization(self, spa_instance):
        """Test SPA initialization."""
        assert spa_instance is not None
        assert hasattr(spa_instance, 'vision_adapter')
        assert hasattr(spa_instance, 'audio_adapter')
        assert hasattr(spa_instance, 'text_adapter')
        assert hasattr(spa_instance, 'models')
        assert 'vision' in spa_instance.models
        assert 'audio' in spa_instance.models
        assert 'text' in spa_instance.models
    
    def test_performance_optimization_setup(self, spa_instance):
        """Test performance optimization setup."""
        assert hasattr(spa_instance, 'device')
        assert hasattr(spa_instance, 'memory_limit')
        assert hasattr(spa_instance, 'batch_size_limit')
        assert spa_instance.device in ['mps', 'cpu']
    
    def test_session_state_initialization(self):
        """Test session state initialization."""
        st.session_state = {}
        init_session_state()
        
        required_keys = [
            'analysis_history',
            'chat_messages',
            'comparison_mode',
            'current_models',
            'processing_state',
            'session_start_time',
            'user_preferences'
        ]
        
        for key in required_keys:
            assert key in st.session_state
    
    def test_get_adapter(self, spa_instance):
        """Test adapter initialization."""
        # Test vision adapter
        vision_adapter = spa_instance.get_adapter('vision')
        assert vision_adapter is not None
        
        # Test audio adapter
        audio_adapter = spa_instance.get_adapter('audio')
        assert audio_adapter is not None
        
        # Test text adapter
        text_adapter = spa_instance.get_adapter('text')
        assert text_adapter is not None
    
    def test_session_state_management(self, spa_instance):
        """Test session state management methods."""
        # Test saving analysis result
        result = {
            'disease': 'Test Disease',
            'confidence': 0.85,
            'recommendations': ['Test recommendation']
        }
        
        spa_instance.save_analysis_result(result, 'test.jpg', 'image')
        
        assert len(st.session_state.analysis_history) == 1
        saved_result = st.session_state.analysis_history[0]
        assert saved_result['disease'] == 'Test Disease'
        assert saved_result['filename'] == 'test.jpg'
        assert 'timestamp' in saved_result
    
    def test_chat_message_management(self, spa_instance):
        """Test chat message management."""
        spa_instance.save_chat_message('user', 'Test message')
        
        assert len(st.session_state.chat_messages) == 1
        message = st.session_state.chat_messages[0]
        assert message['role'] == 'user'
        assert message['content'] == 'Test message'
        assert 'timestamp' in message
    
    def test_processing_state_updates(self, spa_instance):
        """Test processing state management."""
        spa_instance.update_processing_state(
            'processing', 
            'image', 
            {'current': 1, 'total': 5}
        )
        
        assert st.session_state.processing_state == 'processing'
        assert st.session_state.processing_type == 'image'
        assert st.session_state.current_batch_item == 1
        assert st.session_state.total_batch_items == 5
    
    def test_memory_optimization(self, spa_instance):
        """Test memory optimization functionality."""
        # Test memory optimization (should not raise exceptions)
        try:
            memory_percent = spa_instance.optimize_memory_usage()
            # Should return a percentage or None
            assert memory_percent is None or (0 <= memory_percent <= 100)
        except ImportError:
            # psutil not available in test environment
            pass
    
    def test_cache_management(self, spa_instance):
        """Test cache management."""
        # Add some items to cache
        spa_instance.model_cache['cache']['test_model'] = {'dummy': 'data'}
        spa_instance.model_cache['current_size'] = 1
        
        # Clear caches
        spa_instance.clear_caches()
        
        assert len(spa_instance.model_cache['cache']) == 0
        assert spa_instance.model_cache['current_size'] == 0


class TestPlantGuardSPAProgrammaticAPI:
    """Test AI agent programmatic interfaces."""
    
    @pytest.fixture
    def spa_instance(self):
        """Create SPA instance for testing."""
        st.session_state = {}
        init_session_state()
        return PlantGuardSPA()
    
    @pytest.fixture
    def sample_image_file(self):
        """Create sample image file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (224, 224), color='green')
            img.save(f.name, 'JPEG')
            yield f.name
        os.unlink(f.name)
    
    def test_analyze_image_programmatic(self, spa_instance, sample_image_file):
        """Test programmatic image analysis."""
        # Mock the perform_image_analysis method
        mock_result = {
            'disease': 'Test Disease',
            'confidence': 0.85,
            'model': 'vit_best',
            'recommendations': ['Test recommendation']
        }
        
        with patch.object(spa_instance, 'perform_image_analysis', return_value=mock_result):
            result = spa_instance.analyze_image_programmatic(sample_image_file)
            
            assert result['status'] == 'success'
            assert result['disease'] == 'Test Disease'
            assert result['confidence'] == 0.85
            assert 'timestamp' in result
            assert 'request_id' in result
    
    def test_analyze_image_programmatic_error(self, spa_instance):
        """Test programmatic image analysis error handling."""
        result = spa_instance.analyze_image_programmatic('nonexistent_file.jpg')
        
        assert result['status'] == 'error'
        assert 'error' in result
        assert 'timestamp' in result
    
    def test_query_programmatic(self, spa_instance):
        """Test programmatic text query."""
        # Mock the text adapter
        mock_adapter = Mock()
        mock_adapter.generate_response.return_value = "Test response"
        
        with patch.object(spa_instance, 'get_adapter', return_value=mock_adapter):
            result = spa_instance.query_programmatic("Test query")
            
            assert result['status'] == 'success'
            assert result['query'] == 'Test query'
            assert result['response'] == 'Test response'
            assert 'timestamp' in result
            assert 'request_id' in result
    
    def test_get_system_status_programmatic(self, spa_instance):
        """Test programmatic system status."""
        result = spa_instance.get_system_status_programmatic()
        
        assert result['status'] == 'active'
        assert 'models' in result
        assert 'system' in result
        assert 'statistics' in result
        assert 'timestamp' in result
    
    def test_batch_analyze_programmatic(self, spa_instance, sample_image_file):
        """Test programmatic batch analysis."""
        # Create multiple test files
        test_files = [sample_image_file]
        
        # Mock the single image analysis
        mock_result = {
            'status': 'success',
            'disease': 'Test Disease',
            'confidence': 0.85
        }
        
        with patch.object(spa_instance, 'analyze_image_programmatic', return_value=mock_result):
            results = spa_instance.batch_analyze_programmatic(test_files)
            
            assert len(results) == 1
            assert all(r['status'] == 'success' for r in results)


class TestPlantGuardSPAErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    @pytest.fixture
    def spa_instance(self):
        """Create SPA instance for testing."""
        st.session_state = {}
        init_session_state()
        return PlantGuardSPA()
    
    def test_memory_error_handling(self, spa_instance):
        """Test memory error handling."""
        memory_error = MemoryError("Out of memory")
        
        with patch.object(spa_instance, 'clear_caches') as mock_clear:
            with patch.object(spa_instance, 'optimize_memory_usage') as mock_optimize:
                result = spa_instance.handle_error(memory_error, "test_context")
                
                mock_clear.assert_called_once()
                mock_optimize.assert_called_once()
                assert isinstance(result, bool)
    
    def test_connection_error_handling(self, spa_instance):
        """Test connection error handling."""
        connection_error = ConnectionError("Network unreachable")
        
        result = spa_instance.handle_error(connection_error, "test_context")
        assert isinstance(result, bool)
    
    def test_model_error_handling(self, spa_instance):
        """Test model error handling with fallback."""
        model_error = Exception("Model loading failed")
        
        # Set current model
        st.session_state.current_models['vision'] = 'vit_best'
        
        result = spa_instance.handle_error(model_error, "model_loading")
        assert isinstance(result, bool)
    
    def test_generic_error_handling(self, spa_instance):
        """Test generic error handling."""
        generic_error = ValueError("Generic error")
        
        result = spa_instance.handle_error(generic_error, "test_context")
        assert isinstance(result, bool)
    
    def test_error_monitoring_setup(self, spa_instance):
        """Test error monitoring setup."""
        spa_instance.setup_error_monitoring()
        
        assert 'error_stats' in st.session_state
        assert 'total_errors' in st.session_state.error_stats
        assert 'error_types' in st.session_state.error_stats


class TestPlantGuardSPAResponsiveLayout:
    """Test responsive layout and accessibility features."""
    
    @pytest.fixture
    def spa_instance(self):
        """Create SPA instance for testing."""
        st.session_state = {}
        init_session_state()
        return PlantGuardSPA()
    
    def test_device_type_detection(self, spa_instance):
        """Test device type detection."""
        device_type = spa_instance.detect_device_type()
        assert device_type in ['mobile', 'tablet', 'desktop']
    
    def test_responsive_columns(self, spa_instance):
        """Test responsive column layout."""
        # Test desktop layout
        desktop_layout = spa_instance.get_responsive_columns('desktop')
        assert len(desktop_layout) == 3
        
        # Test mobile layout
        mobile_layout = spa_instance.get_responsive_columns('mobile')
        assert len(mobile_layout) == 3
    
    def test_accessibility_settings(self, spa_instance):
        """Test accessibility settings application."""
        # Should not raise exceptions
        spa_instance.apply_accessibility_settings(
            font_size='Large',
            high_contrast=True,
            screen_reader=True
        )


class TestPlantGuardSPAIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def spa_instance(self):
        """Create SPA instance for testing."""
        st.session_state = {}
        init_session_state()
        return PlantGuardSPA()
    
    @pytest.fixture
    def sample_image_file(self):
        """Create sample image file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (224, 224), color='green')
            img.save(f.name, 'JPEG')
            yield f.name
        os.unlink(f.name)
    
    def test_complete_image_analysis_workflow(self, spa_instance, sample_image_file):
        """Test complete image analysis workflow."""
        # Mock adapters
        mock_vision_adapter = Mock()
        mock_vision_adapter.predict.return_value = ("Test Disease", 0.85)
        
        with patch.object(spa_instance, 'get_adapter', return_value=mock_vision_adapter):
            # Simulate image upload and analysis
            image = Image.open(sample_image_file)
            result = spa_instance.perform_image_analysis(image)
            
            assert result is not None
            assert result['disease'] == 'Test Disease'
            assert result['confidence'] == 0.85
            assert 'recommendations' in result
    
    def test_complete_chat_workflow(self, spa_instance):
        """Test complete chat workflow."""
        # Mock text adapter
        mock_text_adapter = Mock()
        mock_text_adapter.generate_response.return_value = "Test response"
        
        with patch.object(spa_instance, 'get_adapter', return_value=mock_text_adapter):
            # Simulate text query
            query = "What's wrong with my plant?"
            spa_instance.process_text_query(query)
            
            # Check that messages were saved
            assert len(st.session_state.chat_messages) >= 2  # User + assistant
            assert any(msg['role'] == 'user' for msg in st.session_state.chat_messages)
            assert any(msg['role'] == 'assistant' for msg in st.session_state.chat_messages)
    
    def test_session_statistics(self, spa_instance):
        """Test session statistics generation."""
        # Add some test data
        spa_instance.save_analysis_result({'disease': 'Test'}, 'test.jpg')
        spa_instance.save_chat_message('user', 'Test message')
        
        stats = spa_instance.get_session_statistics()
        
        assert 'session_duration_seconds' in stats
        assert 'total_analyses' in stats
        assert 'total_chat_messages' in stats
        assert stats['total_analyses'] >= 1
        assert stats['total_chat_messages'] >= 1


class TestPlantGuardSPAPerformance:
    """Performance and stress tests."""
    
    @pytest.fixture
    def spa_instance(self):
        """Create SPA instance for testing."""
        st.session_state = {}
        init_session_state()
        return PlantGuardSPA()
    
    def test_large_history_management(self, spa_instance):
        """Test handling of large analysis history."""
        # Add many analysis results
        for i in range(150):  # More than max_history (100)
            spa_instance.save_analysis_result(
                {'disease': f'Disease_{i}', 'confidence': 0.8},
                f'test_{i}.jpg'
            )
        
        # Should be limited to max_history
        assert len(st.session_state.analysis_history) <= 100
    
    def test_large_chat_history_management(self, spa_instance):
        """Test handling of large chat history with auto-clear."""
        # Enable auto-clear
        st.session_state.user_preferences['auto_clear_chat'] = True
        
        # Add many messages
        for i in range(60):  # More than max_messages (50)
            spa_instance.save_chat_message('user', f'Message {i}')
        
        # Should be limited when auto-clear is enabled
        assert len(st.session_state.chat_messages) <= 50
    
    def test_performance_tracking(self, spa_instance):
        """Test performance tracking functionality."""
        # Update processing state multiple times
        for i in range(10):
            spa_instance.update_processing_state('processing', 'test')
            spa_instance.update_processing_state('complete', 'test')
        
        # Should track performance history
        assert len(st.session_state.performance_history) > 0
        assert len(st.session_state.performance_history) <= 50  # Should be limited


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])