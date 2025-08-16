"""Comprehensive error handling and recovery system for production training.

This module provides automatic error recovery, graceful fallback mechanisms,
detailed error logging, and troubleshooting suggestions for production training environments.
"""

import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import torch

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of training errors."""

    MEMORY = "memory"
    DEVICE = "device"
    DATA = "data"
    MODEL = "model"
    CHECKPOINT = "checkpoint"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class TrainingError:
    """Represents a training error with context and recovery information."""

    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Exception
    traceback_str: str
    timestamp: float
    epoch: int | None = None
    step: int | None = None
    context: dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_actions: list[str] = field(default_factory=list)
    troubleshooting_suggestions: list[str] = field(default_factory=list)


class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""

    def can_handle(self, error: TrainingError) -> bool:
        """Check if this strategy can handle the given error.

        Args:
            error: Training error to check

        Returns:
            True if this strategy can handle the error
        """
        raise NotImplementedError

    def recover(self, error: TrainingError, context: dict[str, Any]) -> bool:
        """Attempt to recover from the error.

        Args:
            error: Training error to recover from
            context: Training context (model, optimizer, etc.)

        Returns:
            True if recovery was successful
        """
        raise NotImplementedError

    def get_troubleshooting_suggestions(self, error: TrainingError) -> list[str]:
        """Get troubleshooting suggestions for the error.

        Args:
            error: Training error

        Returns:
            List of troubleshooting suggestions
        """
        return []


class MemoryErrorRecovery(ErrorRecoveryStrategy):
    """Recovery strategy for memory-related errors."""

    def can_handle(self, error: TrainingError) -> bool:
        """Check if this is a memory-related error."""
        memory_keywords = [
            "out of memory",
            "cuda out of memory",
            "memory",
            "allocation",
            "insufficient memory",
            "memory error",
        ]

        error_msg = error.message.lower()
        return error.category == ErrorCategory.MEMORY or any(keyword in error_msg for keyword in memory_keywords)

    def recover(self, error: TrainingError, context: dict[str, Any]) -> bool:
        """Attempt to recover from memory errors."""
        logger.info("Attempting memory error recovery...")

        recovery_actions = []

        try:
            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                recovery_actions.append("Cleared CUDA memory cache")

            # Force garbage collection
            import gc

            gc.collect()
            recovery_actions.append("Performed garbage collection")

            # Reduce batch size if possible
            config = context.get("config")
            if config and hasattr(config, "batch_size") and config.batch_size > 1:
                new_batch_size = max(1, config.batch_size // 2)
                config.batch_size = new_batch_size
                recovery_actions.append(f"Reduced batch size to {new_batch_size}")

                # Recreate data loaders with new batch size
                trainer = context.get("trainer")
                if trainer and hasattr(trainer, "_setup_data_loaders"):
                    trainer._setup_data_loaders()
                    recovery_actions.append("Recreated data loaders with reduced batch size")

            # Disable mixed precision if enabled
            if config and hasattr(config, "mixed_precision") and config.mixed_precision:
                config.mixed_precision = False
                recovery_actions.append("Disabled mixed precision training")

            error.recovery_actions = recovery_actions
            logger.info(f"Memory recovery actions: {recovery_actions}")
            return True

        except Exception:
            logger.exception("Memory recovery failed")
            return False

    def get_troubleshooting_suggestions(self, error: TrainingError) -> list[str]:
        """Get memory error troubleshooting suggestions."""
        return [
            "Reduce batch size in training configuration",
            "Disable mixed precision training if enabled",
            "Use gradient accumulation instead of large batch sizes",
            "Close other GPU-intensive applications",
            "Consider using a smaller model architecture",
            "Enable gradient checkpointing to trade compute for memory",
            "Use CPU training if GPU memory is insufficient",
        ]


class DeviceErrorRecovery(ErrorRecoveryStrategy):
    """Recovery strategy for device-related errors."""

    def can_handle(self, error: TrainingError) -> bool:
        """Check if this is a device-related error."""
        device_keywords = [
            "device",
            "cuda",
            "gpu",
            "mps",
            "device-side assert",
            "device unavailable",
            "no cuda",
            "cuda error",
        ]

        error_msg = error.message.lower()
        return error.category == ErrorCategory.DEVICE or any(keyword in error_msg for keyword in device_keywords)

    def recover(self, error: TrainingError, context: dict[str, Any]) -> bool:
        """Attempt to recover from device errors."""
        logger.info("Attempting device error recovery...")

        recovery_actions = []

        try:
            config = context.get("config")
            trainer = context.get("trainer")

            if not config or not trainer:
                return False

            # Try to fallback to CPU
            if hasattr(config, "device") and config.device != "cpu":
                logger.warning("GPU error detected, falling back to CPU training")
                config.device = "cpu"
                trainer.device = torch.device("cpu")

                # Move model to CPU
                model = context.get("model")
                if model:
                    model.cpu()
                    recovery_actions.append("Moved model to CPU")

                # Disable mixed precision (not supported on CPU)
                if hasattr(config, "mixed_precision") and config.mixed_precision:
                    config.mixed_precision = False
                    recovery_actions.append("Disabled mixed precision (CPU fallback)")

                # Adjust batch size for CPU training
                if hasattr(config, "batch_size") and config.batch_size > 32:
                    config.batch_size = min(32, config.batch_size)
                    recovery_actions.append(f"Reduced batch size for CPU training: {config.batch_size}")

                recovery_actions.append("Switched to CPU training")
                error.recovery_actions = recovery_actions
                return True

            return False

        except Exception:
            logger.exception("Device recovery failed")
            return False

    def get_troubleshooting_suggestions(self, error: TrainingError) -> list[str]:
        """Get device error troubleshooting suggestions."""
        return [
            "Check CUDA installation and compatibility",
            "Verify GPU drivers are up to date",
            "Restart the training process to reset GPU state",
            "Use CPU training as fallback",
            "Check for hardware issues with GPU",
            "Ensure PyTorch CUDA version matches installed CUDA",
            "Monitor GPU temperature and power consumption",
        ]


class DataErrorRecovery(ErrorRecoveryStrategy):
    """Recovery strategy for data-related errors."""

    def can_handle(self, error: TrainingError) -> bool:
        """Check if this is a data-related error."""
        data_keywords = [
            "dataloader",
            "dataset",
            "data",
            "batch",
            "image",
            "corrupt",
            "file not found",
            "permission denied",
            "io error",
        ]

        error_msg = error.message.lower()
        return error.category == ErrorCategory.DATA or any(keyword in error_msg for keyword in data_keywords)

    def recover(self, error: TrainingError, context: dict[str, Any]) -> bool:
        """Attempt to recover from data errors."""
        logger.info("Attempting data error recovery...")

        recovery_actions = []

        try:
            config = context.get("config")
            trainer = context.get("trainer")

            if not config or not trainer:
                return False

            # Reduce number of data loading workers
            if hasattr(config, "num_workers") and config.num_workers > 0:
                config.num_workers = max(0, config.num_workers // 2)
                recovery_actions.append(f"Reduced data loading workers to {config.num_workers}")

            # Disable persistent workers
            if hasattr(config, "persistent_workers") and config.persistent_workers:
                config.persistent_workers = False
                recovery_actions.append("Disabled persistent workers")

            # Disable pin memory
            if hasattr(config, "pin_memory") and config.pin_memory:
                config.pin_memory = False
                recovery_actions.append("Disabled pin memory")

            # Try to recreate data loaders
            if hasattr(trainer, "_setup_data_loaders"):
                trainer._setup_data_loaders()
                recovery_actions.append("Recreated data loaders with safer settings")

            error.recovery_actions = recovery_actions
            return True

        except Exception:
            logger.exception("Data recovery failed")
            return False

    def get_troubleshooting_suggestions(self, error: TrainingError) -> list[str]:
        """Get data error troubleshooting suggestions."""
        return [
            "Check dataset integrity and file permissions",
            "Verify dataset path and structure",
            "Reduce number of data loading workers",
            "Disable persistent workers and pin memory",
            "Check available disk space",
            "Validate image files for corruption",
            "Ensure dataset preparation completed successfully",
        ]


class CheckpointErrorRecovery(ErrorRecoveryStrategy):
    """Recovery strategy for checkpoint-related errors."""

    def can_handle(self, error: TrainingError) -> bool:
        """Check if this is a checkpoint-related error."""
        checkpoint_keywords = [
            "checkpoint",
            "save",
            "load",
            "state_dict",
            "pickle",
            "serialization",
            "deserialization",
        ]

        error_msg = error.message.lower()
        return error.category == ErrorCategory.CHECKPOINT or any(keyword in error_msg for keyword in checkpoint_keywords)

    def recover(self, error: TrainingError, context: dict[str, Any]) -> bool:
        """Attempt to recover from checkpoint errors."""
        logger.info("Attempting checkpoint error recovery...")

        recovery_actions: list[str] = []

        try:
            trainer = context.get("trainer")
            if not trainer or not hasattr(trainer, "checkpoint_manager"):
                return False

            # Try checkpoint recovery strategies
            if self._try_checkpoint_recovery(trainer, recovery_actions):
                error.recovery_actions = recovery_actions
                return True

            # Clean up corrupted checkpoints
            self._cleanup_corrupted_checkpoints(trainer, recovery_actions)

            # If all else fails, start fresh training
            recovery_actions.append("Starting fresh training (no valid checkpoints found)")
            error.recovery_actions = recovery_actions
            return True

        except Exception:
            logger.exception("Checkpoint recovery failed")
            return False

    def _try_checkpoint_recovery(self, trainer: Any, recovery_actions: list[str]) -> bool:
        """Try to recover using available checkpoints."""
        # Try latest checkpoint
        if self._try_load_checkpoint(trainer, "latest", recovery_actions):
            return True

        # Try best checkpoint
        return self._try_load_checkpoint(trainer, "best", recovery_actions)

    def _try_load_checkpoint(self, trainer: Any, checkpoint_type: str, recovery_actions: list[str]) -> bool:
        """Try to load a specific type of checkpoint."""
        try:
            if checkpoint_type == "latest":
                checkpoint_path = trainer.checkpoint_manager.find_latest_checkpoint()
                description = "alternative"
            else:  # best
                checkpoint_path = trainer.checkpoint_manager.find_best_checkpoint()
                description = "best"

            if checkpoint_path:
                checkpoint = trainer.checkpoint_manager.load_checkpoint(checkpoint_path)
                if checkpoint:
                    recovery_actions.append(f"Loaded {description} checkpoint: {checkpoint_path}")
                    return True
        except Exception:
            logger.debug(f"Failed to load {checkpoint_type} checkpoint for recovery")

        return False

    def _cleanup_corrupted_checkpoints(self, trainer: Any, recovery_actions: list[str]) -> None:
        """Clean up corrupted checkpoints."""
        corrupted_count = trainer.checkpoint_manager.cleanup_corrupted_checkpoints()
        if corrupted_count > 0:
            recovery_actions.append(f"Cleaned up {corrupted_count} corrupted checkpoints")

    def get_troubleshooting_suggestions(self, error: TrainingError) -> list[str]:
        """Get checkpoint error troubleshooting suggestions."""
        return [
            "Check available disk space for checkpoint saving",
            "Verify file permissions in checkpoint directory",
            "Clean up corrupted checkpoint files",
            "Use checkpoint backup and restore functionality",
            "Start fresh training if all checkpoints are corrupted",
            "Check PyTorch version compatibility with saved checkpoints",
        ]


class TrainingErrorHandler:
    """Comprehensive error handler for production training."""

    def __init__(self, log_dir: Path | None = None, enable_notifications: bool = False) -> None:
        """Initialize error handler.

        Args:
            log_dir: Directory for error logs
            enable_notifications: Whether to enable error notifications
        """
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.enable_notifications = enable_notifications
        self.error_log_file = self.log_dir / "training_errors.log"

        # Error history
        self.error_history: list[TrainingError] = []

        # Recovery strategies
        self.recovery_strategies: list[ErrorRecoveryStrategy] = [
            MemoryErrorRecovery(),
            DeviceErrorRecovery(),
            DataErrorRecovery(),
            CheckpointErrorRecovery(),
        ]

        # Setup error logging
        self._setup_error_logging()

        logger.info(f"TrainingErrorHandler initialized with log directory: {self.log_dir}")

    def _setup_error_logging(self) -> None:
        """Setup dedicated error logging."""
        error_logger = logging.getLogger("training_errors")
        error_logger.setLevel(logging.ERROR)

        # Create file handler for errors
        error_handler = logging.FileHandler(self.error_log_file)
        error_handler.setLevel(logging.ERROR)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        error_handler.setFormatter(formatter)

        error_logger.addHandler(error_handler)

    def handle_error(
        self,
        exception: Exception,
        context: dict[str, Any],
        epoch: int | None = None,
        step: int | None = None,
    ) -> bool:
        """Handle a training error with automatic recovery.

        Args:
            exception: The exception that occurred
            context: Training context (model, optimizer, config, etc.)
            epoch: Current epoch (if available)
            step: Current step (if available)

        Returns:
            True if error was handled and recovery was successful
        """
        # Create error object
        error = self._create_error_object(exception, epoch, step, context)

        # Log the error
        self._log_error(error)

        # Add to history
        self.error_history.append(error)

        # Attempt recovery
        recovery_successful = self._attempt_recovery(error, context)

        # Send notification if enabled
        if self.enable_notifications:
            self._send_error_notification(error)

        return recovery_successful

    def _create_error_object(
        self,
        exception: Exception,
        epoch: int | None,
        step: int | None,
        context: dict[str, Any],
    ) -> TrainingError:
        """Create a TrainingError object from an exception."""
        error_id = f"error_{int(time.time())}_{id(exception)}"

        # Categorize error
        category = self._categorize_error(exception)

        # Determine severity
        severity = self._determine_severity(exception, category)

        # Get traceback
        traceback_str = traceback.format_exc()

        return TrainingError(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(exception),
            exception=exception,
            traceback_str=traceback_str,
            timestamp=time.time(),
            epoch=epoch,
            step=step,
            context={
                "exception_type": type(exception).__name__,
                "module": getattr(exception, "__module__", "unknown"),
            },
        )

    def _categorize_error(self, exception: Exception) -> ErrorCategory:
        """Categorize the error based on exception type and message."""
        error_message = str(exception).lower()

        # Define category mappings
        category_keywords = {
            ErrorCategory.MEMORY: ["memory", "allocation"],
            ErrorCategory.DEVICE: ["cuda", "device", "gpu", "mps"],
            ErrorCategory.DATA: ["dataloader", "dataset", "file not found"],
            ErrorCategory.CHECKPOINT: ["checkpoint", "state_dict", "pickle"],
            ErrorCategory.NETWORK: ["connection", "network", "timeout"],
            ErrorCategory.FILESYSTEM: ["permission", "disk", "space", "io"],
            ErrorCategory.CONFIGURATION: ["config", "parameter", "argument"],
        }

        # Check each category
        for category, keywords in category_keywords.items():
            if any(keyword in error_message for keyword in keywords):
                return category

        return ErrorCategory.UNKNOWN

    def _determine_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity."""
        # Critical errors that should stop training
        critical_types = [SystemExit, KeyboardInterrupt]
        if any(isinstance(exception, t) for t in critical_types):
            return ErrorSeverity.CRITICAL

        # High severity errors
        if category in [ErrorCategory.MEMORY, ErrorCategory.DEVICE]:
            return ErrorSeverity.HIGH

        # Medium severity errors
        if category in [ErrorCategory.DATA, ErrorCategory.CHECKPOINT]:
            return ErrorSeverity.MEDIUM

        # Low severity errors
        return ErrorSeverity.LOW

    def _log_error(self, error: TrainingError) -> None:
        """Log the error with full details."""
        error_logger = logging.getLogger("training_errors")

        log_message = (
            f"Training Error [{error.error_id}]\n"
            f"Category: {error.category.value}\n"
            f"Severity: {error.severity.value}\n"
            f"Message: {error.message}\n"
            f"Epoch: {error.epoch}\n"
            f"Step: {error.step}\n"
            f"Timestamp: {error.timestamp}\n"
            f"Traceback:\n{error.traceback_str}"
        )

        error_logger.error(log_message)

        # Also log to main logger
        logger.error(f"Training error occurred: {error.message} (ID: {error.error_id})")

    def _attempt_recovery(self, error: TrainingError, context: dict[str, Any]) -> bool:
        """Attempt to recover from the error using available strategies."""
        logger.info(f"Attempting recovery for error: {error.error_id}")

        error.recovery_attempted = True

        # Find applicable recovery strategies
        applicable_strategies = [strategy for strategy in self.recovery_strategies if strategy.can_handle(error)]

        if not applicable_strategies:
            logger.warning(f"No recovery strategies available for error: {error.error_id}")
            return False

        # Try each strategy
        for strategy in applicable_strategies:
            try:
                logger.info(f"Trying recovery strategy: {type(strategy).__name__}")

                if strategy.recover(error, context):
                    error.recovery_successful = True
                    error.troubleshooting_suggestions = strategy.get_troubleshooting_suggestions(error)

                    logger.info(f"Recovery successful using {type(strategy).__name__}")
                    return True

            except Exception:
                logger.exception(f"Recovery strategy {type(strategy).__name__} failed")

        # No recovery strategy worked
        logger.error(f"All recovery attempts failed for error: {error.error_id}")

        # Collect troubleshooting suggestions from all applicable strategies
        all_suggestions = []
        for strategy in applicable_strategies:
            all_suggestions.extend(strategy.get_troubleshooting_suggestions(error))

        error.troubleshooting_suggestions = list(set(all_suggestions))  # Remove duplicates

        return False

    def _send_error_notification(self, error: TrainingError) -> None:
        """Send error notification (placeholder for future implementation)."""
        # This could be extended to send notifications via:
        # - Email
        # - Slack
        # - Discord
        # - System notifications
        # - etc.

        logger.info(f"Error notification would be sent for: {error.error_id}")

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of all errors encountered."""
        if not self.error_history:
            return {"total_errors": 0, "errors": []}

        errors_by_category: dict[str, int] = {}
        errors_by_severity: dict[str, int] = {}

        error_summary = {
            "total_errors": len(self.error_history),
            "errors_by_category": errors_by_category,
            "errors_by_severity": errors_by_severity,
            "recovery_success_rate": 0.0,
            "recent_errors": [],
        }

        # Count by category and severity
        for error in self.error_history:
            category = error.category.value
            severity = error.severity.value

            errors_by_category[category] = errors_by_category.get(category, 0) + 1
            errors_by_severity[severity] = errors_by_severity.get(severity, 0) + 1

        # Calculate recovery success rate
        attempted_recoveries = sum(1 for e in self.error_history if e.recovery_attempted)
        successful_recoveries = sum(1 for e in self.error_history if e.recovery_successful)

        if attempted_recoveries > 0:
            error_summary["recovery_success_rate"] = successful_recoveries / attempted_recoveries

        # Recent errors (last 10)
        recent_errors = sorted(self.error_history, key=lambda x: x.timestamp, reverse=True)[:10]
        error_summary["recent_errors"] = [
            {
                "error_id": e.error_id,
                "category": e.category.value,
                "severity": e.severity.value,
                "message": e.message,
                "timestamp": e.timestamp,
                "recovery_successful": e.recovery_successful,
            }
            for e in recent_errors
        ]

        return error_summary

    def export_error_report(self, output_file: Path | str) -> None:
        """Export detailed error report to file."""
        output_file = Path(output_file)

        report = {
            "error_summary": self.get_error_summary(),
            "detailed_errors": [
                {
                    "error_id": e.error_id,
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "message": e.message,
                    "timestamp": e.timestamp,
                    "epoch": e.epoch,
                    "step": e.step,
                    "recovery_attempted": e.recovery_attempted,
                    "recovery_successful": e.recovery_successful,
                    "recovery_actions": e.recovery_actions,
                    "troubleshooting_suggestions": e.troubleshooting_suggestions,
                    "traceback": e.traceback_str,
                }
                for e in self.error_history
            ],
        }

        import json

        with output_file.open("w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Error report exported to: {output_file}")


def create_error_handler(log_dir: Path | None = None, enable_notifications: bool = False) -> TrainingErrorHandler:
    """Create a training error handler.

    Args:
        log_dir: Directory for error logs
        enable_notifications: Whether to enable error notifications

    Returns:
        TrainingErrorHandler instance
    """
    return TrainingErrorHandler(log_dir, enable_notifications)
