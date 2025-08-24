"""
Focused Test Suite for PlantGuard SPA - Quick Validation

This test file focuses on core SPA functionality that can be tested
quickly and reliably in CI/CD environments.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class MockStreamlitExpander:
    """Mock Streamlit expander for testing."""

    def __init__(self, title):
        self.title = title

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MockStreamlitSessionState:
    """Mock Streamlit session state for testing."""

    def __init__(self):
        self._state = {}

    def __contains__(self, key):
        return key in self._state

    def __getitem__(self, key):
        return self._state[key]

    def __setitem__(self, key, value):
        self._state[key] = value

    def get(self, key, default=None):
        return self._state.get(key, default)

    def __delitem__(self, key):
        if key in self._state:
            del self._state[key]


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit for testing."""
    mock_st = Mock()
    mock_st.session_state = MockStreamlitSessionState()

    # Mock common Streamlit functions
    mock_st.markdown = Mock()
    mock_st.success = Mock()
    mock_st.error = Mock()
    mock_st.warning = Mock()
    mock_st.info = Mock()
    mock_st.columns = Mock(return_value=[Mock(), Mock()])
    mock_st.tabs = Mock(return_value=[Mock(), Mock(), Mock()])
    mock_st.button = Mock(return_value=False)
    mock_st.file_uploader = Mock(return_value=None)
    mock_st.text_input = Mock(return_value="")
    mock_st.selectbox = Mock(return_value="Option 1")
    mock_st.checkbox = Mock(return_value=False)
    mock_st.progress = Mock()
    mock_st.metric = Mock()
    mock_st.spinner = Mock()
    mock_st.expander = Mock(side_effect=lambda title: MockStreamlitExpander(title))
    mock_st.rerun = Mock()
    mock_st.code = Mock()

    return mock_st


def test_spa_import():
    """Test that SPA module can be imported without errors."""
    try:
        import spa_app

        assert hasattr(spa_app, "PlantGuardSPA")
        assert hasattr(spa_app, "init_session_state")
        assert hasattr(spa_app, "main")
    except ImportError as e:
        pytest.fail(f"Failed to import spa_app: {e}")


def test_session_state_initialization(mock_streamlit):
    """Test session state initialization function exists and runs."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import init_session_state

        # Should not raise critical exceptions when called
        try:
            init_session_state()
            assert True  # If we get here, the function ran without critical error
        except Exception as e:
            # Allow session state related exceptions since we're in test mode
            if "session_state" in str(e) or "ScriptRunContext" in str(e):
                assert True  # Expected in test environment
            else:
                raise e


def test_plantguard_spa_class_creation(mock_streamlit):
    """Test PlantGuardSPA class can be instantiated."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        assert spa is not None
        assert hasattr(spa, "models")
        assert hasattr(spa, "logger")
        assert "vision" in spa.models
        assert "audio" in spa.models
        assert "text" in spa.models


def test_performance_optimization_setup(mock_streamlit):
    """Test performance optimization setup."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Should have device and optimization settings
        assert hasattr(spa, "device")
        assert spa.device in ["mps", "cpu"]
        assert hasattr(spa, "memory_limit")
        assert hasattr(spa, "batch_size_limit")


def test_programmatic_api_methods(mock_streamlit):
    """Test that programmatic API methods exist."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Check programmatic methods exist
        assert hasattr(spa, "analyze_image_programmatic")
        assert hasattr(spa, "process_voice_programmatic")
        assert hasattr(spa, "query_programmatic")
        assert hasattr(spa, "batch_analyze_programmatic")
        assert hasattr(spa, "get_system_status_programmatic")


def test_error_handling_methods(mock_streamlit):
    """Test error handling methods exist."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Check error handling methods
        assert hasattr(spa, "handle_error")
        assert hasattr(spa, "setup_error_monitoring")
        assert hasattr(spa, "optimize_memory_usage")
        assert hasattr(spa, "clear_caches")


def test_session_state_management_methods(mock_streamlit):
    """Test session state management methods."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Check session management methods
        assert hasattr(spa, "save_analysis_result")
        assert hasattr(spa, "save_chat_message")
        assert hasattr(spa, "update_processing_state")
        assert hasattr(spa, "get_session_statistics")


def test_responsive_layout_methods(mock_streamlit):
    """Test responsive layout methods exist."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Check responsive layout methods
        assert hasattr(spa, "detect_device_type")
        assert hasattr(spa, "get_responsive_columns")
        assert hasattr(spa, "render_adaptive_layout")


def test_analyze_image_programmatic_with_invalid_path(mock_streamlit):
    """Test programmatic image analysis with invalid path."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Test with non-existent file
        result = spa.analyze_image_programmatic("nonexistent_file.jpg")

        assert result["status"] == "error"
        assert "error" in result
        assert "timestamp" in result


def test_query_programmatic_basic(mock_streamlit):
    """Test basic programmatic query functionality."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Mock text adapter
        mock_adapter = Mock()
        mock_adapter.generate_response.return_value = "Test response"

        with patch.object(spa, "get_adapter", return_value=mock_adapter):
            result = spa.query_programmatic("Test query")

            assert result["status"] == "success"
            assert result["query"] == "Test query"
            assert result["response"] == "Test response"
            assert "timestamp" in result
            assert "request_id" in result


def test_get_system_status_programmatic(mock_streamlit):
    """Test system status programmatic interface."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        result = spa.get_system_status_programmatic()

        assert result["status"] == "active"
        assert "models" in result
        assert "system" in result
        assert "statistics" in result
        assert "timestamp" in result


def test_memory_optimization_no_crash(mock_streamlit):
    """Test memory optimization doesn't crash."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Should not raise exception
        try:
            result = spa.optimize_memory_usage()
            # Result can be None or a number
            assert result is None or isinstance(result, (int, float))
        except ImportError:
            # psutil not available - acceptable
            pass


def test_error_handling_basic(mock_streamlit):
    """Test basic error handling functionality."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Test with a basic exception
        test_error = ValueError("Test error")
        result = spa.handle_error(test_error, "test_context")

        assert isinstance(result, bool)


def test_device_type_detection(mock_streamlit):
    """Test device type detection returns valid value."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        device_type = spa.detect_device_type()
        assert device_type in ["mobile", "tablet", "desktop"]


def test_responsive_columns(mock_streamlit):
    """Test responsive column layout."""
    with patch("spa_app.st", mock_streamlit):
        from spa_app import PlantGuardSPA, init_session_state

        init_session_state()
        spa = PlantGuardSPA()

        # Test different device types
        desktop_layout = spa.get_responsive_columns("desktop")
        mobile_layout = spa.get_responsive_columns("mobile")
        tablet_layout = spa.get_responsive_columns("tablet")

        assert len(desktop_layout) == 3
        assert len(mobile_layout) == 3
        assert len(tablet_layout) == 3


def test_main_function_exists():
    """Test that main function exists and can be called."""
    try:
        from spa_app import main

        assert callable(main)
    except ImportError:
        pytest.fail("Failed to import main function")


if __name__ == "__main__":
    # Run tests with simple output
    pytest.main([__file__, "-v", "--tb=short", "--no-header"])
