"""File management utilities for PlantGuard."""

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class FileManager:
    """Utility class for secure file operations."""

    def __init__(self, temp_dir: str = "data/tmp") -> None:
        """Initialize FileManager.

        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = Path(temp_dir)
        # Ensure the temp directory exists; use a safe default to avoid deleting user data
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If creation fails, fallback to system temp
            self.temp_dir = Path(tempfile.gettempdir())
        self._temp_files: list[str] = []

    def create_temp_file(self, suffix: str = "", prefix: str = "plantguard_") -> str:
        """Create a secure temporary file.

        Args:
            suffix: File suffix (e.g., ".wav", ".jpg")
            prefix: File prefix

        Returns:
            Path to temporary file
        """
        with tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, dir=self.temp_dir, delete=False) as temp_file:
            temp_path = temp_file.name

        self._temp_files.append(temp_path)
        logger.debug("Created temporary file: %s", temp_path)

        return temp_path

    def cleanup_temp_files(self) -> None:
        """Remove all tracked temporary files."""
        for temp_file in self._temp_files:
            try:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    temp_path.unlink()
                    logger.debug("Cleaned up temporary file: %s", temp_file)
            except OSError as e:
                logger.warning("Failed to cleanup %s: %s", temp_file, e)

        self._temp_files.clear()

    def validate_file_size(self, file_path: str, max_size: int) -> bool:
        """Validate file size.

        Args:
            file_path: Path to file
            max_size: Maximum allowed size in bytes

        Returns:
            True if file size is acceptable
        """
        try:
            file_size = Path(file_path).stat().st_size
        except OSError:
            logger.exception("Error checking file size for %s", file_path)
            return False
        else:
            return file_size <= max_size

    def validate_file_format(self, file_path: str, allowed_formats: list[str]) -> bool:
        """Validate file format by extension.

        Args:
            file_path: Path to file
            allowed_formats: List of allowed extensions (without dots)

        Returns:
            True if file format is allowed
        """
        try:
            file_extension = Path(file_path).suffix.lower().lstrip(".")
        except OSError:
            logger.exception("Error checking file format for %s", file_path)
            return False
        else:
            return file_extension in [fmt.lower() for fmt in allowed_formats]

    def ensure_directory(self, directory: str) -> Path:
        """Ensure directory exists, create if necessary.

        Args:
            directory: Directory path

        Returns:
            Path object for the directory
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def check_model_file_availability(self, model_path: str) -> bool:
        """Check if model file exists and is accessible.

        Args:
            model_path: Path to model file

        Returns:
            True if model file is available and accessible
        """
        try:
            path = Path(model_path)
            if not path.exists():
                logger.warning(f"Model file not found: {model_path}")
                return False

            if not path.is_file():
                logger.warning(f"Model path is not a file: {model_path}")
                return False

            # Try to read a small portion to check accessibility
            try:
                with open(path, "rb") as f:
                    f.read(1024)  # Read first 1KB
                return True
            except (OSError, PermissionError) as e:
                logger.warning(f"Model file not accessible: {model_path} - {e}")
                return False

        except Exception as e:
            logger.warning(f"Error checking model file {model_path}: {e}")
            return False

    def get_fallback_model_config(self) -> dict[str, Any]:
        """Get fallback configuration when model files are missing.

        Returns:
            Dictionary with fallback model configuration
        """
        return {
            "vision_model": None,
            "audio_model": None,
            "text_model": None,
            "fallback_mode": True,
            "error_message": "Model files not available - using fallback mode",
        }

    def __del__(self) -> None:
        """Cleanup temporary files on destruction."""
        self.cleanup_temp_files()
