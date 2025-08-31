"""
Mobile Test Fixtures for PlantGuard Testing Infrastructure.

This module provides comprehensive mock interfaces and test fixtures
for mobile component testing, including proper adapter mocking and
Streamlit session state management.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
import streamlit as st
from PIL import Image


class MockVisionAdapter:
    """Mock Vision Adapter for testing."""

    def __init__(self, model_path: Optional[str] = None, lazy_load: bool = True) -> None:
        """Initialize mock vision adapter."""
        self.model_path = model_path
        self.lazy_load = lazy_load
        self.is_loaded = not lazy_load
        self.predict = MagicMock(return_value=("Healthy Plant", 0.95))
        self.load_checkpoint = MagicMock()
        self.preprocess_image = MagicMock()
        
    def load_model(self) -> None:
        """Mock model loading."""
        self.is_loaded = True


class MockAudioAdapter:
    """Mock Audio Adapter for testing."""

    def __init__(self, model_name: str = "openai/whisper-tiny") -> None:
        """Initialize mock audio adapter."""
        self.model_name = model_name
        self.is_loaded = True
        self.transcribe = MagicMock(return_value="What disease does my plant have?")
        self.predict_disease = MagicMock(return_value=("Fungal Infection", 0.87))
        self.preprocess_audio = MagicMock()


class MockTextAdapter:
    """Mock Text Adapter for testing."""

    def __init__(self, knowledge_base_path: Optional[str] = None) -> None:
        """Initialize mock text adapter."""
        self.knowledge_base_path = knowledge_base_path
        self.is_loaded = True
        self.generate_response = MagicMock(return_value="Based on the analysis, this appears to be a fungal infection.")
        self.get_disease_info = MagicMock(return_value={
            "disease_name": "Fungal Infection",
            "description": "A common plant disease caused by fungi",
            "treatment": "Apply fungicide spray",
            "prevention": "Ensure good air circulation"
        })
        self.extract_features = MagicMock()
        self.prepare_input = MagicMock()


class MockChatModel:
    """Mock Chat Model for testing."""

    def __init__(self) -> None:
        """Initialize mock chat model."""
        self.is_loaded = True
        self.predict = MagicMock(return_value="I can help you identify and treat plant diseases.")
        self.generate_response = MagicMock(return_value="Based on your question, here's what I recommend...")


class MockStreamlitSession:
    """Mock Streamlit session state for testing."""

    def __init__(self) -> None:
        """Initialize mock session state."""
        self._state: Dict[str, Any] = {}
        self.analysis_results: List[Dict[str, Any]] = []
        self.chat_history: List[Dict[str, Any]] = []
        self.mobile_performance: Dict[str, Any] = {}
        self.adapter_status: str = "ready"
        self.component_states: Dict[str, Any] = {}

    def __getitem__(self, key: str) -> Any:
        """Get item from session state."""
        return self._state.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item in session state."""
        self._state[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if key exists in session state."""
        return key in self._state

    def get(self, key: str, default: Any = None) -> Any:
        """Get item with default value."""
        return self._state.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        """Update session state with dictionary."""
        self._state.update(data)

    def clear(self) -> None:
        """Clear session state."""
        self._state.clear()

    def keys(self) -> Any:
        """Get session state keys."""
        return self._state.keys()

    def values(self) -> Any:
        """Get session state values."""
        return self._state.values()

    def items(self) -> Any:
        """Get session state items."""
        return self._state.items()


class MockStreamlitComponents:
    """Mock Streamlit UI components for testing."""

    def __init__(self) -> None:
        """Initialize mock components."""
        self.button_calls: List[Dict[str, Any]] = []
        self.file_uploader_calls: List[Dict[str, Any]] = []
        self.text_input_calls: List[Dict[str, Any]] = []
        self.selectbox_calls: List[Dict[str, Any]] = []
        self.slider_calls: List[Dict[str, Any]] = []

    def button(self, label: str, **kwargs) -> bool:
        """Mock button component."""
        self.button_calls.append({"label": label, "kwargs": kwargs})
        return kwargs.get("mock_pressed", False)

    def file_uploader(self, label: str, **kwargs) -> Optional[Any]:
        """Mock file uploader component."""
        self.file_uploader_calls.append({"label": label, "kwargs": kwargs})
        return kwargs.get("mock_file", None)

    def text_input(self, label: str, **kwargs) -> str:
        """Mock text input component."""
        self.text_input_calls.append({"label": label, "kwargs": kwargs})
        return kwargs.get("mock_value", "")

    def selectbox(self, label: str, options: List[Any], **kwargs) -> Any:
        """Mock selectbox component."""
        self.selectbox_calls.append({"label": label, "options": options, "kwargs": kwargs})
        return kwargs.get("mock_selection", options[0] if options else None)

    def slider(self, label: str, **kwargs) -> Any:
        """Mock slider component."""
        self.slider_calls.append({"label": label, "kwargs": kwargs})
        return kwargs.get("mock_value", kwargs.get("value", 0))

    def columns(self, spec) -> List[Mock]:
        """Mock columns layout."""
        return [Mock() for _ in range(spec if isinstance(spec, int) else len(spec))]

    def container(self) -> Mock:
        """Mock container."""
        return Mock()

    def expander(self, label: str, expanded: bool = False) -> Mock:
        """Mock expander."""
        return Mock()

    def tabs(self, labels: List[str]) -> List[Mock]:
        """Mock tabs."""
        return [Mock() for _ in labels]

    def success(self, message: str) -> None:
        """Mock success message."""
        pass

    def error(self, message: str) -> None:
        """Mock error message."""
        pass

    def warning(self, message: str) -> None:
        """Mock warning message."""
        pass

    def info(self, message: str) -> None:
        """Mock info message."""
        pass


# Test Fixtures

@pytest.fixture
def mock_vision_adapter() -> Any:
    """Provide mock vision adapter."""
    return MockVisionAdapter()


@pytest.fixture
def mock_audio_adapter() -> Any:
    """Provide mock audio adapter."""
    return MockAudioAdapter()


@pytest.fixture
def mock_text_adapter() -> Any:
    """Provide mock text adapter."""
    return MockTextAdapter()


@pytest.fixture
def mock_chat_model() -> Any:
    """Provide mock chat model."""
    return MockChatModel()


@pytest.fixture
def mock_streamlit_session() -> Generator[Any, None, None]:
    """Provide mock Streamlit session state."""
    mock_session = MockStreamlitSession()
    
    # Initialize with common test data
    mock_session.update({
        'analysis_results': [],
        'chat_history': [],
        'mobile_performance': {},
        'adapter_status': 'ready',
        'component_states': {}
    })
    
    with patch('streamlit.session_state', mock_session):
        yield mock_session


@pytest.fixture
def mock_streamlit_components() -> Any:
    """Provide mock Streamlit components."""
    return MockStreamlitComponents()


@pytest.fixture
def mock_all_adapters(mock_vision_adapter, mock_audio_adapter, mock_text_adapter) -> Generator[Any, None, None]:
    """Provide all mock adapters with proper patching."""
    with patch.multiple(
        'src.ui.components.mobile_adapter_integration',
        VisionAdapter=lambda **kwargs: mock_vision_adapter,
        AudioAdapter=lambda **kwargs: mock_audio_adapter,
        TextAdapter=lambda **kwargs: mock_text_adapter
    ):
        yield {
            'vision': mock_vision_adapter,
            'audio': mock_audio_adapter,
            'text': mock_text_adapter
        }


@pytest.fixture
def sample_test_image() -> Any:
    """Provide sample test image."""
    return Image.new('RGB', (224, 224), color='green')


@pytest.fixture
def sample_large_image() -> Any:
    """Provide sample large image for testing preprocessing."""
    return Image.new('RGB', (2000, 1500), color='blue')


@pytest.fixture
def temp_audio_file() -> Generator[Any, None, None]:
    """Provide temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        audio_file_path = tmp_file.name
        # Write some dummy audio data
        tmp_file.write(b"dummy audio data")
    
    yield audio_file_path
    
    # Cleanup
    Path(audio_file_path).unlink(missing_ok=True)


@pytest.fixture
def temp_model_file() -> Generator[Any, None, None]:
    """Provide temporary model file for testing."""
    temp_path = Path("data/models/test_vision_model.pt")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.touch()
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_analysis_results() -> List[Any]:
    """Provide sample analysis results for testing."""
    return [
        {
            "timestamp": datetime.now().isoformat(),
            "disease_name": "Powdery Mildew",
            "confidence": 0.92,
            "source": "camera",
            "component_id": "test_camera",
            "analysis_type": "vision"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "disease_name": "Leaf Spot",
            "confidence": 0.87,
            "source": "upload",
            "component_id": "test_upload",
            "analysis_type": "vision"
        }
    ]


@pytest.fixture
def sample_chat_history() -> List[Any]:
    """Provide sample chat history for testing."""
    return [
        {
            "role": "user",
            "content": "What's wrong with my plant?",
            "timestamp": datetime.now().isoformat(),
            "source": "text_input",
            "component_id": "test_chat"
        },
        {
            "role": "assistant",
            "content": "Based on the analysis, your plant appears to have powdery mildew.",
            "timestamp": datetime.now().isoformat(),
            "source": "response_text_input",
            "component_id": "test_chat",
            "context": {"disease": "Powdery Mildew", "confidence": 0.92}
        }
    ]


@pytest.fixture
def mobile_adapter_integration_with_mocks(mock_streamlit_session, mock_all_adapters) -> Any:
    """Provide MobileAdapterIntegration with all mocks configured."""
    from src.ui.components.mobile_adapter_integration import \
        MobileAdapterIntegration
    
    integration = MobileAdapterIntegration()
    
    # Set mock adapters
    integration._vision_adapter = mock_all_adapters['vision']
    integration._audio_adapter = mock_all_adapters['audio']
    integration._text_adapter = mock_all_adapters['text']
    
    return integration


@pytest.fixture
def mock_mobile_component_registry() -> Generator[Any, None, None]:
    """Mock mobile component registry for testing."""
    mock_registry = Mock()
    mock_registry.get_all_components.return_value = {
        "mobile_camera_input_test": Mock,
        "mobile_upload_input_test": Mock,
        "mobile_voice_input_test": Mock,
        "mobile_text_input_test": Mock,
        "mobile_analysis_display_test": Mock,
    }
    mock_registry.register_component = Mock()
    mock_registry.get_component = Mock()
    
    with patch('src.ui.components.mobile_component_registry.mobile_component_registry', mock_registry):
        yield mock_registry


@pytest.fixture
def mock_mobile_testing_framework_dependencies() -> Generator[Any, None, None]:
    """Mock all dependencies for MobileTestingFramework."""
    with patch.multiple(
        'src.ui.components.mobile_testing_framework',
        MobileComponentTester=Mock,
        MobileAIAgentTester=Mock,
        MobileSpecificTester=Mock,
        MobileStateManager=Mock
    ):
        yield


@pytest.fixture(autouse=True)
def setup_test_environment() -> None:
    """Set up test environment with proper logging and cleanup."""
    import logging

    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
    
    yield
    
    # Cleanup after test
    if hasattr(st, 'session_state'):
        st.session_state.clear()


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_analysis_result(
        disease_name: str = "Test Disease",
        confidence: float = 0.85,
        source: str = "test",
        component_id: str = "test_component"
    ) -> Dict[str, Any]:
        """Create analysis result for testing."""
        return {
            "timestamp": datetime.now().isoformat(),
            "disease_name": disease_name,
            "confidence": confidence,
            "source": source,
            "component_id": component_id,
            "analysis_type": "vision",
            "preprocessing_applied": True
        }
    
    @staticmethod
    def create_chat_message(
        role: str = "user",
        content: str = "Test message",
        source: str = "test",
        component_id: str = "test_component"
    ) -> Dict[str, Any]:
        """Create chat message for testing."""
        return {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "component_id": component_id
        }
    
    @staticmethod
    def create_transcription_result(
        transcription: str = "Test transcription",
        source: str = "test",
        component_id: str = "test_component",
        success: bool = True
    ) -> Dict[str, Any]:
        """Create transcription result for testing."""
        return {
            "timestamp": datetime.now().isoformat(),
            "transcription": transcription,
            "source": source,
            "component_id": component_id,
            "analysis_type": "audio",
            "success": success,
            "preprocessing_applied": True
        }


# Utility functions for tests

def assert_mock_called_with_pattern(mock_obj, pattern: str) -> bool:
    """Assert that mock was called with arguments matching pattern."""
    for call in mock_obj.call_args_list:
        args, kwargs = call
        for arg in args:
            if isinstance(arg, str) and pattern in arg:
                return True
        for value in kwargs.values():
            if isinstance(value, str) and pattern in value:
                return True
    return False


def create_mock_component_with_methods(methods: List[str]) -> Mock:
    """Create mock component with specified methods."""
    mock_component = Mock()
    for method in methods:
        setattr(mock_component, method, Mock())
    return mock_component