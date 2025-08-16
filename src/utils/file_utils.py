"""File management utilities for PlantGuard."""

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class FileManager:
    """Utility class for secure file operations."""

    def __init__(self, temp_dir: str = "data/temp") -> None:
        """Initialize FileManager.

        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
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

    def __del__(self) -> None:
        """Cleanup temporary files on destruction."""
        self.cleanup_temp_files()
