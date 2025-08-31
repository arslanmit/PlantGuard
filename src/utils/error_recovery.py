"""
Error Recovery and Safe Type Conversion Utilities.

This module provides comprehensive error recovery mechanisms and safe type conversion
utilities to replace silent exception handling throughout the PlantGuard codebase.
"""

import importlib
import logging
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

# Configure logger for this module
logger = logging.getLogger(__name__)

T = TypeVar("T")


class SafeTypeConverter:
    """Safe type conversion utilities with proper error handling and logging."""

    @staticmethod
    def safe_int(value: Any, default: int = 0, logger_name: str | None = None) -> int:
        """
        Safely convert value to integer with logging.

        Args:
            value: Value to convert
            default: Default value if conversion fails
            logger_name: Optional logger name for context

        Returns:
            Converted integer or default value
        """
        try:
            if isinstance(value, int):
                return value
            if isinstance(value, float | str):
                return int(value)
            return default
        except (ValueError, TypeError, OverflowError) as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Safe int conversion failed for value '{value}': {e}")
            return default

    @staticmethod
    def safe_float(value: Any, default: float = 0.0, logger_name: str | None = None) -> float:
        """
        Safely convert value to float with logging.

        Args:
            value: Value to convert
            default: Default value if conversion fails
            logger_name: Optional logger name for context

        Returns:
            Converted float or default value
        """
        try:
            if isinstance(value, float):
                return value
            if isinstance(value, int | str):
                return float(value)
            return default
        except (ValueError, TypeError, OverflowError) as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Safe float conversion failed for value '{value}': {e}")
            return default

    @staticmethod
    def safe_str(value: Any, default: str = "", logger_name: str | None = None) -> str:
        """
        Safely convert value to string with logging.

        Args:
            value: Value to convert
            default: Default value if conversion fails
            logger_name: Optional logger name for context

        Returns:
            Converted string or default value
        """
        try:
            if isinstance(value, str):
                return value
            return str(value)
        except (ValueError, TypeError) as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Safe str conversion failed for value '{value}': {e}")
            return default

    @staticmethod
    def safe_bool(value: Any, default: bool = False, logger_name: str | None = None) -> bool:
        """
        Safely convert value to boolean with logging.

        Args:
            value: Value to convert
            default: Default value if conversion fails
            logger_name: Optional logger name for context

        Returns:
            Converted boolean or default value
        """
        try:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        except (ValueError, TypeError) as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Safe bool conversion failed for value '{value}': {e}")
            return default


class ImportErrorRecovery:
    """Import error recovery mechanisms with proper fallback handling."""

    @staticmethod
    def safe_import(module_name: str, logger_name: str | None = None) -> types.ModuleType | None:
        """
        Safely import a module with proper error logging.

        Args:
            module_name: Name of module to import
            logger_name: Optional logger name for context

        Returns:
            Imported module or None if import fails
        """
        try:
            return importlib.import_module(module_name)
        except ImportError as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.debug(f"{log_context}Optional import failed: {module_name} - {e}")
            return None
        except Exception as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Unexpected error importing {module_name}: {e}")
            return None

    @staticmethod
    def safe_import_from(module_name: str, attr_name: str, fallback: Any | None = None, logger_name: str | None = None) -> Any | None:
        """
        Safely import an attribute from a module with fallback.

        Args:
            module_name: Name of module to import from
            attr_name: Name of attribute to import
            fallback: Fallback value if import fails
            logger_name: Optional logger name for context

        Returns:
            Imported attribute, fallback value, or None
        """
        try:
            module = importlib.import_module(module_name)
            return getattr(module, attr_name)
        except ImportError as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.debug(f"{log_context}Optional import failed: {module_name}.{attr_name} - {e}")
            return fallback
        except AttributeError as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Attribute {attr_name} not found in {module_name}: {e}")
            return fallback
        except Exception as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Unexpected error importing {module_name}.{attr_name}: {e}")
            return fallback

    @staticmethod
    def create_import_fallback(module_name: str, fallback_class: type[T], logger_name: str | None = None) -> types.ModuleType | T:
        """
        Create a fallback class if module import fails.

        Args:
            module_name: Name of module to try importing
            fallback_class: Fallback class to use if import fails
            logger_name: Optional logger name for context

        Returns:
            Imported module or fallback class instance
        """
        module = ImportErrorRecovery.safe_import(module_name, logger_name)
        if module is not None:
            return module

        log_context = f"[{logger_name}] " if logger_name else ""
        logger.info(f"{log_context}Using fallback for {module_name}")
        return fallback_class()


class ExceptionRecovery:
    """Exception recovery mechanisms with proper logging and fallback handling."""

    @staticmethod
    def safe_execute(func: Callable[[], T], fallback: T | None = None, logger_name: str | None = None, operation_name: str | None = None) -> T | None:
        """
        Safely execute a function with proper error logging and fallback.

        Args:
            func: Function to execute
            fallback: Fallback value if execution fails
            logger_name: Optional logger name for context
            operation_name: Optional operation name for logging

        Returns:
            Function result or fallback value
        """
        try:
            return func()
        except Exception as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            op_context = f" during {operation_name}" if operation_name else ""
            logger.warning(f"{log_context}Safe execution failed{op_context}: {e}")
            return fallback

    @staticmethod
    def safe_file_operation(
        file_path: str | Path, operation: Callable[[Path], T], fallback: T | None = None, logger_name: str | None = None
    ) -> T | None:
        """
        Safely perform file operations with proper error handling.

        Args:
            file_path: Path to file
            operation: File operation to perform
            fallback: Fallback value if operation fails
            logger_name: Optional logger name for context

        Returns:
            Operation result or fallback value
        """
        try:
            path = Path(file_path)
            return operation(path)
        except (FileNotFoundError, PermissionError, OSError) as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}File operation failed for {file_path}: {e}")
            return fallback
        except Exception as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.error(f"{log_context}Unexpected error in file operation for {file_path}: {e}")
            return fallback

    @staticmethod
    def safe_cleanup(cleanup_func: Callable[[], None], logger_name: str | None = None, resource_name: str | None = None) -> bool:
        """
        Safely perform cleanup operations with proper error logging.

        Args:
            cleanup_func: Cleanup function to execute
            logger_name: Optional logger name for context
            resource_name: Optional resource name for logging

        Returns:
            True if cleanup succeeded, False otherwise
        """
        try:
            cleanup_func()
            return True
        except Exception as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            resource_context = f" for {resource_name}" if resource_name else ""
            logger.warning(f"{log_context}Cleanup failed{resource_context}: {e}")
            return False


class SessionStateRecovery:
    """Session state recovery mechanisms for Streamlit applications."""

    @staticmethod
    def safe_session_clear(logger_name: str | None = None) -> bool:
        """
        Safely clear Streamlit session state with proper error handling.

        Args:
            logger_name: Optional logger name for context

        Returns:
            True if clearing succeeded, False otherwise
        """
        try:
            import streamlit as st

            if hasattr(st, "session_state"):
                st.session_state.clear()
                return True
            return False
        except ImportError as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.debug(f"{log_context}Streamlit not available for session clearing: {e}")
            return False
        except Exception as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Session state clearing failed: {e}")
            return False

    @staticmethod
    def safe_session_get(key: str, default: Any = None, logger_name: str | None = None) -> Any:
        """
        Safely get value from Streamlit session state.

        Args:
            key: Session state key
            default: Default value if key not found
            logger_name: Optional logger name for context

        Returns:
            Session state value or default
        """
        try:
            import streamlit as st

            if hasattr(st, "session_state") and key in st.session_state:
                return st.session_state[key]
            return default
        except ImportError as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.debug(f"{log_context}Streamlit not available for session access: {e}")
            return default
        except Exception as e:
            log_context = f"[{logger_name}] " if logger_name else ""
            logger.warning(f"{log_context}Session state access failed for key '{key}': {e}")
            return default


class FileCleanupRecovery:
    """File cleanup recovery mechanisms with proper error handling."""

    @staticmethod
    def safe_file_cleanup(file_paths: str | Path | list[str | Path], logger_name: str | None = None) -> dict[str, bool]:
        """
        Safely clean up temporary files with proper error logging.

        Args:
            file_paths: Single file path or list of file paths to clean up
            logger_name: Optional logger name for context

        Returns:
            Dictionary mapping file paths to cleanup success status
        """
        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        results: dict[str, bool] = {}
        log_context = f"[{logger_name}] " if logger_name else ""

        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    results[str(file_path)] = True
                    logger.debug(f"{log_context}Successfully cleaned up file: {file_path}")
                else:
                    results[str(file_path)] = True  # File doesn't exist, consider it cleaned
                    logger.debug(f"{log_context}File already cleaned or doesn't exist: {file_path}")
            except (PermissionError, OSError) as e:
                results[str(file_path)] = False
                logger.warning(f"{log_context}Failed to clean up file {file_path}: {e}")
            except Exception as e:
                results[str(file_path)] = False
                logger.error(f"{log_context}Unexpected error cleaning up file {file_path}: {e}")

        return results

    @staticmethod
    def safe_directory_cleanup(directory_path: str | Path, pattern: str = "temp_*", logger_name: str | None = None) -> dict[str, bool]:
        """
        Safely clean up files in a directory matching a pattern.

        Args:
            directory_path: Directory to clean up
            pattern: File pattern to match (default: "temp_*")
            logger_name: Optional logger name for context

        Returns:
            Dictionary mapping file paths to cleanup success status
        """
        results: dict[str, bool] = {}
        log_context = f"[{logger_name}] " if logger_name else ""

        try:
            directory = Path(directory_path)
            if not directory.exists():
                logger.debug(f"{log_context}Directory doesn't exist: {directory_path}")
                return results

            matching_files = list(directory.glob(pattern))
            if not matching_files:
                logger.debug(f"{log_context}No files matching pattern '{pattern}' in {directory_path}")
                return results

            for file_path in matching_files:
                try:
                    file_path.unlink()
                    results[str(file_path)] = True
                    logger.debug(f"{log_context}Successfully cleaned up: {file_path}")
                except (PermissionError, OSError) as e:
                    results[str(file_path)] = False
                    logger.warning(f"{log_context}Failed to clean up {file_path}: {e}")
                except Exception as e:
                    results[str(file_path)] = False
                    logger.error(f"{log_context}Unexpected error cleaning up {file_path}: {e}")

        except Exception as e:
            logger.error(f"{log_context}Failed to access directory {directory_path}: {e}")

        return results


# Convenience functions for common use cases
def safe_int(value: Any, default: int = 0) -> int:
    """Convenience function for safe integer conversion."""
    return SafeTypeConverter.safe_int(value, default)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convenience function for safe float conversion."""
    return SafeTypeConverter.safe_float(value, default)


def safe_str(value: Any, default: str = "") -> str:
    """Convenience function for safe string conversion."""
    return SafeTypeConverter.safe_str(value, default)


def safe_import(module_name: str) -> types.ModuleType | None:
    """Convenience function for safe module import."""
    return ImportErrorRecovery.safe_import(module_name)


def safe_cleanup(*file_paths: str | Path) -> bool:
    """Convenience function for safe file cleanup."""
    results = FileCleanupRecovery.safe_file_cleanup(list(file_paths))
    return all(results.values())
