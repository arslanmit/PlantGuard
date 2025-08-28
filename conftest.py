"""Pytest configuration helpers.

Ensure the repository root and the `src/` package directory are on sys.path
early during test collection so tests that import `src.*` succeed.

This is a minimal, non-invasive helper intended only for the test runtime.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

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
    def mock_streamlit_session():
        """Provide mock Streamlit session state."""
        mock_session = MockStreamlitSession()

        # Initialize with common test data
        mock_session.update({"analysis_results": [], "chat_history": [], "mobile_performance": {}, "adapter_status": "ready", "component_states": {}})

        with patch("streamlit.session_state", mock_session):
            yield mock_session

    @pytest.fixture
    def mock_vision_adapter():
        """Provide mock vision adapter."""
        return MockVisionAdapter()

    @pytest.fixture
    def mock_audio_adapter():
        """Provide mock audio adapter."""
        return MockAudioAdapter()

    @pytest.fixture
    def mock_text_adapter():
        """Provide mock text adapter."""
        return MockTextAdapter()

    @pytest.fixture
    def sample_test_image():
        """Provide sample test image."""
        return Image.new("RGB", (224, 224), color="green")

    @pytest.fixture
    def sample_large_image():
        """Provide sample large image for testing preprocessing."""
        return Image.new("RGB", (2000, 1500), color="blue")

    @pytest.fixture
    def temp_audio_file():
        """Provide temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            audio_file_path = tmp_file.name
            # Write some dummy audio data
            tmp_file.write(b"dummy audio data")

        yield audio_file_path

        # Cleanup
        Path(audio_file_path).unlink(missing_ok=True)

    @pytest.fixture
    def sample_analysis_results():
        """Provide sample analysis results for testing."""
        return [
            TestDataFactory.create_analysis_result(disease_name="Powdery Mildew", confidence=0.92, source="camera", component_id="test_camera"),
            TestDataFactory.create_analysis_result(disease_name="Leaf Spot", confidence=0.87, source="upload", component_id="test_upload"),
        ]

    @pytest.fixture
    def all_mock_adapters(mock_vision_adapter, mock_audio_adapter, mock_text_adapter):
        """Provide all mock adapters with proper patching."""
        adapters = {"vision": mock_vision_adapter, "audio": mock_audio_adapter, "text": mock_text_adapter}

        with (
            patch.multiple("src.core.vision", VisionAdapter=lambda **kwargs: mock_vision_adapter),
            patch.multiple("src.core.audio", AudioAdapter=lambda **kwargs: mock_audio_adapter),
            patch.multiple("src.core.nlp", TextAdapter=lambda **kwargs: mock_text_adapter),
        ):
            yield adapters

    @pytest.fixture
    def mock_mobile_component_registry():
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

        with patch("src.ui.components.mobile_component_registry.mobile_component_registry", mock_registry):
            yield mock_registry
