"""
Mobile Testing Configuration for PlantGuard.

This module provides comprehensive test configuration for mobile components
including fixtures, mocks, and test utilities specifically for mobile testing.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock, Mock, patch

import pytest
import streamlit as st
from PIL import Image

from src.utils.error_recovery import (ExceptionRecovery, FileCleanupRecovery,
                                      SessionStateRecovery)
from tests.fixtures.mobile_test_fixtures import (MockAudioAdapter,
                                                 MockChatModel,
                                                 MockStreamlitComponents,
                                                 MockStreamlitSession,
                                                 MockTextAdapter,
                                                 MockVisionAdapter,
                                                 TestDataFactory)

# Configure logger for this module
logger = logging.getLogger(__name__)


# Global test configuration
@pytest.fixture(scope="session")
def mobile_test_config() -> dict[str, Any]:
    """Global mobile test configuration."""
    return {
        "test_data_dir": Path("tests/data"),
        "temp_dir": Path("tests/temp"),
        "mock_model_dir": Path("tests/mocks/models"),
        "test_timeout": 30,
        "enable_logging": True,
        "cleanup_temp_files": True
    }


# Session-level fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_mobile_test_environment(mobile_test_config: Dict[str, Any]) -> None:
    """Set up mobile test environment."""
    # Create test directories
    for dir_path in [mobile_test_config["test_data_dir"], 
                     mobile_test_config["temp_dir"], 
                     mobile_test_config["mock_model_dir"]]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup
    if mobile_test_config["cleanup_temp_files"]:
        import shutil
        if mobile_test_config["temp_dir"].exists():
            shutil.rmtree(mobile_test_config["temp_dir"])


# Streamlit mocking fixtures
@pytest.fixture
def mock_streamlit_session() -> Any:
    """Provide comprehensive Streamlit session state mock."""
    mock_session = MockStreamlitSession()
    
    # Initialize with common mobile test data
    mock_session.update({
        'analysis_results': [],
        'chat_history': [],
        'mobile_performance': {},
        'adapter_status': 'ready',
        'component_states': {},
        'mobile_settings': {
            'theme': 'light',
            'language': 'en',
            'notifications': True
        },
        'mobile_cache': {},
        'mobile_history': []
    })
    
    with patch('streamlit.session_state', mock_session):
        yield mock_session


@pytest.fixture
def mock_streamlit_components() -> Any:
    """Provide comprehensive Streamlit components mock."""
    components = MockStreamlitComponents()
    
    with patch.multiple(
        'streamlit',
        button=components.button,
        file_uploader=components.file_uploader,
        text_input=components.text_input,
        selectbox=components.selectbox,
        slider=components.slider,
        columns=components.columns,
        container=components.container,
        expander=components.expander,
        tabs=components.tabs,
        success=components.success,
        error=components.error,
        warning=components.warning,
        info=components.info
    ):
        yield components


# Adapter mocking fixtures
@pytest.fixture
def mock_vision_adapter() -> Any:
    """Provide mock vision adapter with comprehensive functionality."""
    adapter = MockVisionAdapter()
    
    # Set up realistic predictions
    adapter.predict.return_value = ("Healthy Plant", 0.95)
    
    # Add additional methods for comprehensive testing
    adapter.get_model_info = MagicMock(return_value={
        "model_name": "ResNet50",
        "version": "1.0.0",
        "classes": ["Healthy", "Disease A", "Disease B"]
    })
    
    adapter.preprocess_image = MagicMock(return_value=Image.new('RGB', (224, 224)))
    
    return adapter


@pytest.fixture
def mock_audio_adapter() -> Any:
    """Provide mock audio adapter with comprehensive functionality."""
    adapter = MockAudioAdapter()
    
    # Set up realistic transcriptions
    adapter.transcribe.return_value = "What disease does my plant have?"
    adapter.predict_disease.return_value = ("Fungal Infection", 0.87)
    
    # Add additional methods
    adapter.get_model_info = MagicMock(return_value={
        "model_name": "Whisper-tiny",
        "version": "1.0.0",
        "supported_formats": ["wav", "mp3", "m4a"]
    })
    
    adapter.preprocess_audio = MagicMock()
    
    return adapter


@pytest.fixture
def mock_text_adapter() -> Any:
    """Provide mock text adapter with comprehensive functionality."""
    adapter = MockTextAdapter()
    
    # Set up realistic responses
    adapter.generate_response.return_value = "Based on the analysis, this appears to be a fungal infection."
    adapter.get_disease_info.return_value = {
        "disease_name": "Fungal Infection",
        "description": "A common plant disease caused by fungi",
        "treatment": "Apply fungicide spray",
        "prevention": "Ensure good air circulation"
    }
    
    # Add additional methods
    adapter.get_model_info = MagicMock(return_value={
        "model_name": "DistilBERT",
        "version": "1.0.0",
        "knowledge_base_size": 1000
    })
    
    return adapter


@pytest.fixture
def mock_chat_model() -> Any:
    """Provide mock chat model with comprehensive functionality."""
    model = MockChatModel()
    
    # Set up realistic responses
    model.predict.return_value = "I can help you identify and treat plant diseases."
    model.generate_response.return_value = "Based on your question, here's what I recommend..."
    
    return model


@pytest.fixture
def all_mock_adapters(mock_vision_adapter: Any, mock_audio_adapter: Any, mock_text_adapter: Any, mock_chat_model: Any) -> Any:
    """Provide all mock adapters without importing actual modules."""
    adapters = {
        'vision': mock_vision_adapter,
        'audio': mock_audio_adapter,
        'text': mock_text_adapter,
        'chat': mock_chat_model
    }
    
    # Return adapters without patching to avoid import issues
    yield adapters


# Test data fixtures
@pytest.fixture
def sample_test_images() -> dict[str, Any]:
    """Provide various test images."""
    return {
        'small': Image.new('RGB', (224, 224), color='green'),
        'large': Image.new('RGB', (2000, 1500), color='blue'),
        'portrait': Image.new('RGB', (600, 800), color='red'),
        'landscape': Image.new('RGB', (800, 600), color='yellow')
    }


@pytest.fixture
def temp_audio_files(mobile_test_config: Dict[str, Any]) -> Any:
    """Provide temporary audio files for testing."""
    audio_files = {}
    
    for format_ext in ['wav', 'mp3', 'm4a']:
        temp_file = mobile_test_config["temp_dir"] / f"test_audio.{format_ext}"
        temp_file.write_bytes(b"dummy audio data for " + format_ext.encode())
        audio_files[format_ext] = str(temp_file)
    
    yield audio_files
    
    # Cleanup handled by session fixture


@pytest.fixture
def temp_model_files(mobile_test_config: Dict[str, Any]) -> Any:
    """Provide temporary model files for testing."""
    model_files = {}
    
    model_dir = mobile_test_config["mock_model_dir"]
    
    # Create mock model files
    for model_name in ['vision_resnet50.pt', 'audio_whisper.pt', 'text_distilbert.pt']:
        model_path = model_dir / model_name
        model_path.write_bytes(b"dummy model data")
        model_files[model_name] = str(model_path)
    
    yield model_files


@pytest.fixture
def sample_analysis_results() -> list[dict[str, Any]]:
    """Provide comprehensive sample analysis results."""
    return [
        TestDataFactory.create_analysis_result(
            disease_name="Powdery Mildew",
            confidence=0.92,
            source="camera",
            component_id="mobile_camera_input"
        ),
        TestDataFactory.create_analysis_result(
            disease_name="Leaf Spot",
            confidence=0.87,
            source="upload",
            component_id="mobile_upload_input"
        ),
        TestDataFactory.create_analysis_result(
            disease_name="Rust Disease",
            confidence=0.89,
            source="camera",
            component_id="mobile_camera_input"
        )
    ]


@pytest.fixture
def sample_chat_history() -> list[dict[str, Any]]:
    """Provide comprehensive sample chat history."""
    return [
        TestDataFactory.create_chat_message(
            role="user",
            content="What's wrong with my plant?",
            source="text_input",
            component_id="mobile_text_input"
        ),
        TestDataFactory.create_chat_message(
            role="assistant",
            content="Based on the analysis, your plant appears to have powdery mildew.",
            source="response_text_input",
            component_id="mobile_text_input"
        ),
        TestDataFactory.create_chat_message(
            role="user",
            content="How do I treat this?",
            source="voice_input",
            component_id="mobile_voice_input"
        ),
        TestDataFactory.create_chat_message(
            role="assistant",
            content="For powdery mildew, I recommend applying a fungicide spray.",
            source="response_voice_input",
            component_id="mobile_voice_input"
        )
    ]


# Mobile component mocking fixtures
@pytest.fixture
def mock_mobile_component_registry() -> Any:
    """Mock mobile component registry with comprehensive components."""
    mock_registry = Mock()
    
    # Define comprehensive component list
    components = {
        "mobile_camera_input": Mock,
        "mobile_upload_input": Mock,
        "mobile_voice_input": Mock,
        "mobile_text_input": Mock,
        "mobile_analysis_display": Mock,
        "mobile_chat_interface": Mock,
        "mobile_history_view": Mock,
        "mobile_settings_card": Mock,
        "mobile_layout_manager": Mock,
        "mobile_state_manager": Mock
    }
    
    mock_registry.get_all_components.return_value = components
    mock_registry.register_component = Mock()
    mock_registry.get_component = Mock()
    mock_registry.component_count = len(components)
    
    # Return mock registry without patching to avoid import issues
    yield mock_registry


@pytest.fixture
def mock_mobile_adapter_integration(mock_streamlit_session: Any, all_mock_adapters: Any) -> Any:
    """Provide mobile adapter integration with all mocks configured."""
    from src.ui.components.mobile_adapter_integration import \
        MobileAdapterIntegration
    
    integration = MobileAdapterIntegration()
    
    # Inject mock adapters
    integration._vision_adapter = all_mock_adapters['vision']
    integration._audio_adapter = all_mock_adapters['audio']
    integration._text_adapter = all_mock_adapters['text']
    integration._chat_model = all_mock_adapters['chat']
    
    return integration


# Testing framework mocking fixtures - moved to end of file to avoid duplication


# Performance testing fixtures
@pytest.fixture
def mobile_performance_config() -> Dict[str, Any]:
    """Configuration for mobile performance testing."""
    return {
        "max_render_time": 200,  # milliseconds
        "max_memory_usage": 100,  # MB
        "max_cpu_usage": 80,     # percentage
        "min_fps": 30,           # frames per second
        "max_load_time": 3000,   # milliseconds
        "target_lighthouse_score": 90
    }


# Error simulation fixtures
@pytest.fixture
def error_simulation() -> Any:
    """Provide error simulation utilities for testing error handling."""
    class ErrorSimulator:
        @staticmethod
        def create_adapter_error(adapter_type: str, error_message: str = None) -> Any:
            """Create an adapter error for testing."""
            if error_message is None:
                error_message = f"{adapter_type} adapter error"
            return Exception(error_message)
        
        @staticmethod
        def create_network_error() -> Any:
            """Create a network error for testing."""
            return ConnectionError("Network connection failed")
        
        @staticmethod
        def create_file_error() -> Any:
            """Create a file error for testing."""
            return FileNotFoundError("Model file not found")
        
        @staticmethod
        def create_memory_error() -> Any:
            """Create a memory error for testing."""
            return MemoryError("Insufficient memory")
    
    return ErrorSimulator()


# Mobile testing framework fixtures
@pytest.fixture
def mock_mobile_testing_framework() -> Any:
    """Mock mobile testing framework with comprehensive functionality."""
    with patch.multiple(
        'src.ui.components.mobile_testing_framework',
        MobileComponentTester=Mock,
        MobileAIAgentTester=Mock,
        MobileSpecificTester=Mock,
        MobileStateManager=Mock
    ) as mocks:
        # Set up realistic return values
        mocks['MobileComponentTester'].return_value.run_component_test_suite.return_value = []
        mocks['MobileComponentTester'].return_value.generate_test_report.return_value = {}
        mocks['MobileComponentTester'].return_value.get_test_statistics.return_value = {}
        
        mocks['MobileAIAgentTester'].return_value.validate_component_health.return_value = Mock(
            status="passed", confidence=0.95
        )
        mocks['MobileAIAgentTester'].return_value.generate_agent_report.return_value = {}
        mocks['MobileAIAgentTester'].return_value.get_agent_statistics.return_value = {}
        
        mocks['MobileSpecificTester'].return_value.run_comprehensive_mobile_tests.return_value = {}
        mocks['MobileSpecificTester'].return_value.generate_mobile_test_report.return_value = {}
        mocks['MobileSpecificTester'].return_value.get_mobile_test_statistics.return_value = {}
        
        mocks['MobileStateManager'].return_value.get_all_component_states.return_value = []
        
        yield mocks


# Mobile test utilities fixture
@pytest.fixture
def mobile_test_utilities() -> Dict[str, Any]:
    """Provide mobile testing utilities."""
    class MobileTestUtils:
        @staticmethod
        def create_mock_component(component_type: str, methods: list[str] = None) -> Any:
            """Create a mock component with specified methods."""
            mock_component = Mock()
            mock_component.component_type = component_type
            
            if methods:
                for method in methods:
                    setattr(mock_component, method, Mock())
            
            return mock_component
        
        @staticmethod
        def assert_session_state_updated(session_state: Any, key: str, expected_length: int = None) -> Any:
            """Assert that session state was updated correctly."""
            assert key in session_state
            if expected_length is not None:
                assert len(session_state[key]) == expected_length
        
        @staticmethod
        def create_test_validation_result(status: str = "passed", confidence: float = 0.95) -> Any:
            """Create a test validation result."""
            return {
                "status": status,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
                "details": f"Test validation with status: {status}"
            }
    
    return MobileTestUtils()


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test(mobile_test_config: Dict[str, Any]) -> None:
    """Cleanup after each test."""
    yield
    
    # Clear any remaining session state with proper error handling
    SessionStateRecovery.safe_session_clear(logger_name="conftest_mobile")
    
    # Clean up any temporary files created during test with proper error handling
    temp_dir = mobile_test_config["temp_dir"]
    if temp_dir.exists():
        temp_files = list(temp_dir.glob("test_*"))
        if temp_files:
            cleanup_results = FileCleanupRecovery.safe_file_cleanup(
                temp_files, 
                logger_name="conftest_mobile"
            )
            failed_cleanups = [path for path, success in cleanup_results.items() if not success]
            if failed_cleanups:
                logger.warning(f"Failed to clean up {len(failed_cleanups)} temporary files")
        else:
            logger.debug("No temporary files to clean up")