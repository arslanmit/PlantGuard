"""Real-time training progress tracking and display for PlantGuard production training.

This module provides progress tracking, real-time metrics display, and user-friendly
progress bars for monitoring training progress in real-time.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

import torch
from tqdm import tqdm

logger = logging.getLogger(__name__)


@dataclass
class ProgressMetrics:
    """Container for real-time progress metrics."""

    current_epoch: int = 0
    total_epochs: int = 0
    current_step: int = 0
    total_steps: int = 0
    train_loss: float = 0.0
    val_loss: float | None = None
    train_accuracy: float | None = None
    val_accuracy: float | None = None
    learning_rate: float | None = None
    batch_time: float = 0.0
    data_time: float = 0.0
    eta: float = 0.0  # Estimated time remaining
    samples_per_second: float = 0.0
    memory_usage: float | None = None


@dataclass
class BatchMetrics:
    """Metrics for a single batch."""

    loss: float
    accuracy: float | None = None
    batch_size: int = 0
    processing_time: float = 0.0
    data_loading_time: float = 0.0


class ProgressTracker:
    """Real-time progress tracking with detailed statistics and ETA calculation."""

    def __init__(self, total_epochs: int, steps_per_epoch: int) -> None:
        """Initialize progress tracker.

        Args:
            total_epochs: Total number of training epochs
            steps_per_epoch: Number of steps (batches) per epoch
        """
        self.total_epochs = total_epochs
        self.steps_per_epoch = steps_per_epoch
        self.total_steps = total_epochs * steps_per_epoch

        # Progress state
        self.current_epoch = 0
        self.current_step = 0
        self.global_step = 0

        # Timing
        self.start_time = time.time()
        self.epoch_start_time = time.time()
        self.batch_times: list[float] = []
        self.data_times: list[float] = []

        # Metrics tracking
        self.epoch_losses: list[float] = []
        self.epoch_accuracies: list[float] = []
        self.best_val_loss = float("inf")
        self.best_val_accuracy = 0.0

        # Progress bars
        self.epoch_pbar: tqdm | None = None
        self.batch_pbar: tqdm | None = None

    def start_epoch(self, epoch: int) -> None:
        """Start tracking a new epoch.

        Args:
            epoch: Current epoch number (0-indexed)
        """
        self.current_epoch = epoch
        self.current_step = 0
        self.epoch_start_time = time.time()
        self.epoch_losses.clear()
        self.epoch_accuracies.clear()

        # Create epoch progress bar
        if self.epoch_pbar is None:
            self.epoch_pbar = tqdm(
                total=self.total_epochs,
                desc="Training Progress",
                unit="epoch",
                position=0,
                leave=True,
            )

        # Create batch progress bar for this epoch
        self.batch_pbar = tqdm(
            total=self.steps_per_epoch,
            desc=f"Epoch {epoch + 1}/{self.total_epochs}",
            unit="batch",
            position=1,
            leave=False,
        )

    def update_batch(self, batch_metrics: BatchMetrics) -> ProgressMetrics:
        """Update progress with batch metrics.

        Args:
            batch_metrics: Metrics from the current batch

        Returns:
            Current progress metrics
        """
        self.current_step += 1
        self.global_step += 1

        # Track metrics
        self.epoch_losses.append(batch_metrics.loss)
        if batch_metrics.accuracy is not None:
            self.epoch_accuracies.append(batch_metrics.accuracy)

        # Track timing
        self.batch_times.append(batch_metrics.processing_time)
        self.data_times.append(batch_metrics.data_loading_time)

        # Keep only recent timing data for accurate ETA
        if len(self.batch_times) > 100:
            self.batch_times = self.batch_times[-100:]
            self.data_times = self.data_times[-100:]

        # Calculate current metrics
        avg_loss = sum(self.epoch_losses) / len(self.epoch_losses)
        avg_accuracy = sum(self.epoch_accuracies) / len(self.epoch_accuracies) if self.epoch_accuracies else None
        avg_batch_time = sum(self.batch_times) / len(self.batch_times)
        avg_data_time = sum(self.data_times) / len(self.data_times)

        # Calculate ETA
        remaining_steps = self.total_steps - self.global_step
        eta = remaining_steps * avg_batch_time

        # Calculate samples per second
        samples_per_second = batch_metrics.batch_size / avg_batch_time if avg_batch_time > 0 else 0

        # Get memory usage if available
        memory_usage = None
        if torch.cuda.is_available():
            memory_usage = torch.cuda.memory_allocated() / 1024**3  # GB

        # Update batch progress bar
        if self.batch_pbar:
            self.batch_pbar.set_postfix(
                {
                    "loss": f"{batch_metrics.loss:.4f}",
                    "avg_loss": f"{avg_loss:.4f}",
                    "acc": f"{batch_metrics.accuracy:.3f}" if batch_metrics.accuracy else "N/A",
                    "lr": f"{batch_metrics.processing_time:.3f}s",
                }
            )
            self.batch_pbar.update(1)

        # Create progress metrics
        progress_metrics = ProgressMetrics(
            current_epoch=self.current_epoch,
            total_epochs=self.total_epochs,
            current_step=self.current_step,
            total_steps=self.steps_per_epoch,
            train_loss=avg_loss,
            train_accuracy=avg_accuracy,
            batch_time=avg_batch_time,
            data_time=avg_data_time,
            eta=eta,
            samples_per_second=samples_per_second,
            memory_usage=memory_usage,
        )

        return progress_metrics

    def finish_epoch(
        self,
        val_loss: float | None = None,
        val_accuracy: float | None = None,
        learning_rate: float | None = None,
    ) -> ProgressMetrics:
        """Finish the current epoch and update validation metrics.

        Args:
            val_loss: Validation loss for the epoch
            val_accuracy: Validation accuracy for the epoch
            learning_rate: Current learning rate

        Returns:
            Final progress metrics for the epoch
        """
        # Close batch progress bar
        if self.batch_pbar:
            self.batch_pbar.close()
            self.batch_pbar = None

        # Calculate epoch metrics
        epoch_duration = time.time() - self.epoch_start_time
        avg_train_loss = sum(self.epoch_losses) / len(self.epoch_losses) if self.epoch_losses else 0.0
        avg_train_accuracy = sum(self.epoch_accuracies) / len(self.epoch_accuracies) if self.epoch_accuracies else None

        # Update best metrics
        if val_loss is not None and val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
        if val_accuracy is not None and val_accuracy > self.best_val_accuracy:
            self.best_val_accuracy = val_accuracy

        # Update epoch progress bar
        if self.epoch_pbar:
            postfix = {
                "train_loss": f"{avg_train_loss:.4f}",
                "val_loss": f"{val_loss:.4f}" if val_loss else "N/A",
                "val_acc": f"{val_accuracy:.3f}" if val_accuracy else "N/A",
                "best_val": f"{self.best_val_accuracy:.3f}",
                "time": f"{epoch_duration:.1f}s",
            }
            self.epoch_pbar.set_postfix(postfix)
            self.epoch_pbar.update(1)

        # Calculate remaining time
        elapsed_time = time.time() - self.start_time
        remaining_epochs = self.total_epochs - (self.current_epoch + 1)
        avg_epoch_time = elapsed_time / (self.current_epoch + 1)
        eta = remaining_epochs * avg_epoch_time

        # Create final progress metrics
        progress_metrics = ProgressMetrics(
            current_epoch=self.current_epoch,
            total_epochs=self.total_epochs,
            current_step=self.steps_per_epoch,
            total_steps=self.steps_per_epoch,
            train_loss=avg_train_loss,
            val_loss=val_loss,
            train_accuracy=avg_train_accuracy,
            val_accuracy=val_accuracy,
            learning_rate=learning_rate,
            batch_time=sum(self.batch_times) / len(self.batch_times) if self.batch_times else 0.0,
            data_time=sum(self.data_times) / len(self.data_times) if self.data_times else 0.0,
            eta=eta,
        )

        return progress_metrics

    def finish_training(self) -> dict[str, Any]:
        """Finish training and return summary statistics.

        Returns:
            Dictionary with training summary statistics
        """
        # Close progress bars
        if self.batch_pbar:
            self.batch_pbar.close()
        if self.epoch_pbar:
            self.epoch_pbar.close()

        total_time = time.time() - self.start_time

        summary = {
            "total_training_time": total_time,
            "total_epochs": self.current_epoch + 1,
            "total_steps": self.global_step,
            "best_val_loss": self.best_val_loss if self.best_val_loss != float("inf") else None,
            "best_val_accuracy": self.best_val_accuracy if self.best_val_accuracy > 0 else None,
            "avg_epoch_time": total_time / (self.current_epoch + 1),
            "avg_batch_time": sum(self.batch_times) / len(self.batch_times) if self.batch_times else 0.0,
        }

        logger.info(f"Training completed in {total_time:.2f} seconds ({total_time / 3600:.2f} hours)")
        return summary


class MetricsCollector:
    """Collects and aggregates training metrics in real-time."""

    def __init__(self, window_size: int = 100) -> None:
        """Initialize metrics collector.

        Args:
            window_size: Size of the moving window for averaging metrics
        """
        self.window_size = window_size
        self.reset()

    def reset(self) -> None:
        """Reset all collected metrics."""
        self.losses: list[float] = []
        self.accuracies: list[float] = []
        self.batch_times: list[float] = []
        self.data_times: list[float] = []
        self.learning_rates: list[float] = []
        self.memory_usage: list[float] = []

    def add_batch_metrics(
        self,
        loss: float,
        accuracy: float | None = None,
        batch_time: float = 0.0,
        data_time: float = 0.0,
        learning_rate: float | None = None,
    ) -> None:
        """Add metrics from a single batch.

        Args:
            loss: Batch loss
            accuracy: Batch accuracy (optional)
            batch_time: Time to process the batch
            data_time: Time to load the batch data
            learning_rate: Current learning rate (optional)
        """
        self.losses.append(loss)
        if accuracy is not None:
            self.accuracies.append(accuracy)
        self.batch_times.append(batch_time)
        self.data_times.append(data_time)
        if learning_rate is not None:
            self.learning_rates.append(learning_rate)

        # Add memory usage if GPU is available
        if torch.cuda.is_available():
            memory_gb = torch.cuda.memory_allocated() / 1024**3
            self.memory_usage.append(memory_gb)

        # Keep only recent data within window
        if len(self.losses) > self.window_size:
            self.losses = self.losses[-self.window_size :]
            self.accuracies = self.accuracies[-self.window_size :]
            self.batch_times = self.batch_times[-self.window_size :]
            self.data_times = self.data_times[-self.window_size :]
            self.learning_rates = self.learning_rates[-self.window_size :]
            self.memory_usage = self.memory_usage[-self.window_size :]

    def get_current_metrics(self) -> dict[str, float]:
        """Get current averaged metrics.

        Returns:
            Dictionary of current metrics
        """
        metrics = {}

        if self.losses:
            metrics["avg_loss"] = sum(self.losses) / len(self.losses)
            metrics["recent_loss"] = self.losses[-1]

        if self.accuracies:
            metrics["avg_accuracy"] = sum(self.accuracies) / len(self.accuracies)
            metrics["recent_accuracy"] = self.accuracies[-1]

        if self.batch_times:
            metrics["avg_batch_time"] = sum(self.batch_times) / len(self.batch_times)
            metrics["samples_per_second"] = 1.0 / metrics["avg_batch_time"] if metrics["avg_batch_time"] > 0 else 0

        if self.data_times:
            metrics["avg_data_time"] = sum(self.data_times) / len(self.data_times)

        if self.learning_rates:
            metrics["current_lr"] = self.learning_rates[-1]

        if self.memory_usage:
            metrics["gpu_memory_gb"] = self.memory_usage[-1]
            metrics["avg_memory_gb"] = sum(self.memory_usage) / len(self.memory_usage)

        return metrics


def format_time(seconds: float) -> str:
    """Format time in seconds to human-readable string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string (e.g., "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_memory(bytes_value: float) -> str:
    """Format memory usage in bytes to human-readable string.

    Args:
        bytes_value: Memory in bytes

    Returns:
        Formatted memory string (e.g., "1.2 GB")
    """
    if bytes_value < 1024**2:
        return f"{bytes_value / 1024:.1f} KB"
    elif bytes_value < 1024**3:
        return f"{bytes_value / 1024**2:.1f} MB"
    else:
        return f"{bytes_value / 1024**3:.1f} GB"
