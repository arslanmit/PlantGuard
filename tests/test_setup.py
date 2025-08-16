"""Test basic setup and imports."""

import sys
from pathlib import Path

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import after path setup
from src.utils.config import Config
from src.utils.error_handling import ErrorHandler
from src.utils.file_utils import FileManager
from src.utils.logging import setup_logger


def test_imports() -> None:
    """Test that core modules can be imported."""
    # If we get here, imports worked
    assert True


def test_config_creation() -> None:
    """Test configuration creation."""
    config = Config()
    assert config.num_classes == 38
    assert config.image_size == 224
    assert "jpg" in config.supported_image_formats


def test_logger_setup() -> None:
    """Test logger setup."""
    logger = setup_logger("test_logger")
    assert logger.name == "test_logger"


def test_file_manager() -> None:
    """Test file manager initialization."""
    fm = FileManager()
    assert fm.temp_dir.exists()


def test_error_handler() -> None:
    """Test error handler initialization."""
    eh = ErrorHandler()
    error_msg = eh.handle_vision_error(Exception("test error"))
    assert isinstance(error_msg, str)
    assert len(error_msg) > 0
