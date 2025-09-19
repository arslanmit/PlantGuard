from __future__ import annotations

import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from PIL import Image

"""Pytest configuration helpers.

Ensure the repository root and the `src/` package directory are on sys.path
early during test collection so tests that import `plantguard.*` succeed.

This is a minimal, non-invasive helper intended only for the test runtime.
"""

# Import mobile test fixtures
try:
    from tests.fixtures.mobile_test_fixtures import MockAudioAdapter, MockStreamlitSession, MockTextAdapter, MockVisionAdapter, TestDataFactory

    MOBILE_FIXTURES_AVAILABLE = True
except ImportError:
    MOBILE_FIXTURES_AVAILABLE = False


def pytest_sessionstart(session) -> None:
    """During pytest collection, ensure repo root and src/ are on sys.path.

    pluggy/pytest expect the parameter name to be exactly `session`.
    Mark it used to avoid unused-argument linters.
    """
    # Mark the session as used for linters
    _ = session

    # Keep tests isolated: we only modify sys.path at collection time.
    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"

    # Prepend repo root and src/ to sys.path if not already present. Prepending
    # keeps test-local modules first and mirrors how many CI setups run tests.
    repo_root_str = str(repo_root)
    src_dir_str = str(src_dir)

    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    if src_dir.exists() and src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)


# Mobile test fixtures (only if mobile fixtures are available)
if MOBILE_FIXTURES_AVAILABLE:

    @pytest.fixture
    def mock_streamlit_session() -> Generator[Any, None, None]:
        """Provide mock Streamlit session state."""
        mock_session = MockStreamlitSession()

        # Initialize with common test data
        mock_session.update({"analysis_results": [], "chat_history": [], "mobile_performance": {}, "adapter_status": "ready", "component_states": {}})

        with patch("streamlit.session_state", mock_session):
            yield mock_session

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
    def sample_test_image() -> Any:
        """Provide sample test image."""
        return Image.new("RGB", (224, 224), color="green")

    @pytest.fixture
    def sample_large_image() -> Any:
        """Provide sample large image for testing preprocessing."""
        return Image.new("RGB", (2000, 1500), color="blue")

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
    def sample_analysis_results() -> list[Any]:
        """Provide sample analysis results for testing."""
        return [
            TestDataFactory.create_analysis_result(disease_name="Powdery Mildew", confidence=0.92, source="camera", component_id="test_camera"),
            TestDataFactory.create_analysis_result(disease_name="Leaf Spot", confidence=0.87, source="upload", component_id="test_upload"),
        ]

    @pytest.fixture
    def mock_chat_model() -> Any:
        """Provide mock chat model."""
        from tests.fixtures.mobile_test_fixtures import MockChatModel

        return MockChatModel()

    @pytest.fixture
    def all_mock_adapters(mock_vision_adapter, mock_audio_adapter, mock_text_adapter, mock_chat_model) -> Any:
        """Provide all mock adapters without importing actual modules."""
        adapters = {"vision": mock_vision_adapter, "audio": mock_audio_adapter, "text": mock_text_adapter, "chat": mock_chat_model}

        # Return adapters without patching to avoid import issues
        return adapters

    @pytest.fixture
    def mock_mobile_component_registry() -> Any:
        """Mock mobile component registry for testing."""
        mock_registry = Mock()
        mock_registry.get_all_components.return_value = {
            "mobile_camera_input": Mock,
            "mobile_upload_input": Mock,
            "mobile_voice_input": Mock,
            "mobile_text_input": Mock,
            "mobile_analysis_display": Mock,
        }
        mock_registry.register_component = Mock()
        mock_registry.get_component = Mock()

        # Return mock registry without patching to avoid import issues
        return mock_registry

    @pytest.fixture
    def error_simulation() -> Any:
        """Provide error simulation utilities for testing error handling."""

        class ErrorSimulator:
            @staticmethod
            def create_adapter_error(adapter_type: str, error_message: str | None = None) -> Any:
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

    @pytest.fixture
    def mock_mobile_testing_framework() -> Any:
        """Mock mobile testing framework with comprehensive functionality."""
        # Create mock objects without trying to patch the actual modules
        mock_component_tester = Mock()
        mock_component_tester.run_component_test_suite.return_value = []
        mock_component_tester.generate_test_report.return_value = {}
        mock_component_tester.get_test_statistics.return_value = {}

        mock_ai_agent_tester = Mock()
        mock_ai_agent_tester.validate_component_health.return_value = Mock(status="passed", confidence=0.95)
        mock_ai_agent_tester.generate_agent_report.return_value = {}
        mock_ai_agent_tester.get_agent_statistics.return_value = {}

        mock_mobile_specific_tester = Mock()
        mock_mobile_specific_tester.run_comprehensive_mobile_tests.return_value = {}
        mock_mobile_specific_tester.generate_mobile_test_report.return_value = {}
        mock_mobile_specific_tester.get_mobile_test_statistics.return_value = {}

        mock_state_manager = Mock()
        mock_state_manager.get_all_component_states.return_value = []

        mocks = {
            "MobileComponentTester": mock_component_tester,
            "MobileAIAgentTester": mock_ai_agent_tester,
            "MobileSpecificTester": mock_mobile_specific_tester,
            "MobileStateManager": mock_state_manager,
        }

        return mocks

    @pytest.fixture
    def mobile_test_utilities() -> dict[str, Any]:
        """Provide mobile testing utilities."""

        class MobileTestUtils:
            @staticmethod
            def create_mock_component(component_type: str, methods: list[str] | None = None) -> Any:
                """Create a mock component with specified methods."""
                mock_component = Mock()
                mock_component.component_type = component_type

                if methods:
                    for method in methods:
                        setattr(mock_component, method, Mock())

                return mock_component

            @staticmethod
            def assert_session_state_updated(session_state, key: str, expected_length: int | None = None) -> Any:
                """Assert that session state was updated correctly."""
                assert key in session_state
                if expected_length is not None:
                    assert len(session_state[key]) == expected_length

            @staticmethod
            def create_test_validation_result(status: str = "passed", confidence: float = 0.95) -> Any:
                """Create a test validation result."""
                from datetime import datetime

                return {
                    "status": status,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat(),
                    "details": f"Test validation with status: {status}",
                }

        return MobileTestUtils()

    @pytest.fixture
    def mobile_performance_config() -> dict[str, Any]:
        """Configuration for mobile performance testing."""
        return {
            "max_render_time": 200,  # milliseconds
            "max_memory_usage": 100,  # MB
            "max_cpu_usage": 80,  # percentage
            "min_fps": 30,  # frames per second
            "max_load_time": 3000,  # milliseconds
            "target_lighthouse_score": 90,
        }
