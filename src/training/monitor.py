"""Training monitoring and visualization system for PlantGuard production training.

This module provides the TrainingMonitor class that implements comprehensive training
monitoring with TensorBoard integration, real-time metrics logging, and visualization.
"""

import json
import logging
import subprocess  # nosec B404: subprocess is required for TensorBoard integration
import sys
import threading
import time
import webbrowser
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
import torch.nn.functional as F
from sklearn.metrics import confusion_matrix
from torch.utils.tensorboard import SummaryWriter

from .progress import MetricsCollector, ProgressTracker
from .reporting import ModelAnalyzer, TrainingCurveAnalyzer, TrainingReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Container for training metrics at a specific step/epoch."""

    step: int
    epoch: int
    train_loss: float
    val_loss: float | None = None
    train_accuracy: float | None = None
    val_accuracy: float | None = None
    learning_rate: float | None = None
    batch_time: float | None = None
    data_time: float | None = None
    memory_usage: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TrainingReport:
    """Comprehensive training report with final metrics and analysis."""

    experiment_name: str
    start_time: datetime
    end_time: datetime
    total_duration: float
    final_metrics: dict[str, float]
    best_metrics: dict[str, float]
    training_history: list[TrainingMetrics]
    model_info: dict[str, Any]
    dataset_info: dict[str, Any]
    hyperparameters: dict[str, Any]
    system_info: dict[str, Any]


class TrainingMonitor:
    """Comprehensive training monitoring with TensorBoard integration.

    Provides real-time metrics logging, visualization, progress tracking,
    and comprehensive training reports for production training workflows.
    """

    def __init__(
        self,
        experiment_name: str,
        log_dir: Path | str,
        auto_launch_tensorboard: bool = False,
        tensorboard_port: int = 6006,
    ) -> None:
        """Initialize training monitor.

        Args:
            experiment_name: Name of the training experiment
            log_dir: Directory for TensorBoard logs and reports
            auto_launch_tensorboard: Whether to automatically launch TensorBoard
            tensorboard_port: Port for TensorBoard server
        """
        self.experiment_name = experiment_name
        self.log_dir = Path(log_dir)
        self.tensorboard_port = tensorboard_port

        # Create timestamped experiment directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.experiment_dir = self.log_dir / f"{experiment_name}_{timestamp}"
        self.experiment_dir.mkdir(parents=True, exist_ok=True)

        # Initialize TensorBoard writer
        self.writer = SummaryWriter(log_dir=str(self.experiment_dir))

        # Training state
        self.start_time = datetime.now()
        self.metrics_history: list[TrainingMetrics] = []
        self.best_metrics: dict[str, float] = {}
        self.tensorboard_process: subprocess.Popen | None = None

        # Progress tracking and metrics collection
        self.progress_tracker: ProgressTracker | None = None
        self.metrics_collector = MetricsCollector()

        # Auto-launch TensorBoard if requested
        if auto_launch_tensorboard:
            self.launch_tensorboard()

        logger.info(f"Training monitor initialized: {self.experiment_dir}")

    def log_metrics(
        self,
        metrics: dict[str, float],
        step: int,
        epoch: int | None = None,
    ) -> None:
        """Log training metrics to TensorBoard and internal history.

        Args:
            metrics: Dictionary of metric names and values
            step: Current training step
            epoch: Current epoch (optional)
        """
        # Log to TensorBoard
        _metrics = metrics
        for name, value in _metrics.items():
            if value is not None:
                self.writer.add_scalar(name, value, step)

        # Create metrics object for history
        training_metrics = TrainingMetrics(
            step=step,
            epoch=epoch or 0,
            train_loss=metrics.get("Loss/Train", 0.0),
            val_loss=metrics.get("Loss/Validation"),
            train_accuracy=metrics.get("Accuracy/Train"),
            val_accuracy=metrics.get("Accuracy/Validation"),
            learning_rate=metrics.get("Learning_Rate"),
            batch_time=metrics.get("Time/Batch"),
            data_time=metrics.get("Time/Data"),
            memory_usage=metrics.get("Memory/GPU_Usage"),
        )

        self.metrics_history.append(training_metrics)

        # Update best metrics
        for name, value in _metrics.items():
            if value is not None:
                if ("Loss" in name and (name not in self.best_metrics or value < self.best_metrics[name])) or (
                    "Accuracy" in name and (name not in self.best_metrics or value > self.best_metrics[name])
                ):
                    self.best_metrics[name] = value

        logger.debug(f"Logged metrics for step {step}: {metrics}")

    def log_images(
        self,
        images: torch.Tensor,
        tag: str,
        step: int,
        max_images: int = 8,
    ) -> None:
        """Log images to TensorBoard.

        Args:
            images: Tensor of images (B, C, H, W)
            tag: Tag for the images in TensorBoard
            step: Current training step
            max_images: Maximum number of images to log
        """
        if images.dim() != 4:
            logger.warning(f"Expected 4D tensor for images, got {images.dim()}D")
            return

        # Limit number of images
        if images.size(0) > max_images:
            images = images[:max_images]

        # Normalize images to [0, 1] if needed
        if images.min() < 0 or images.max() > 1:
            images = (images - images.min()) / (images.max() - images.min())

        self.writer.add_images(tag, images, step)
        logger.debug(f"Logged {images.size(0)} images with tag '{tag}' at step {step}")

    def log_confusion_matrix(
        self,
        y_true: list[int] | np.ndarray,
        y_pred: list[int] | np.ndarray,
        class_names: list[str],
        step: int,
        normalize: bool = True,
    ) -> None:
        """Generate and log confusion matrix to TensorBoard.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            class_names: Names of the classes
            step: Current training step
            normalize: Whether to normalize the confusion matrix
        """
        # Compute confusion matrix
        cm = confusion_matrix(y_true, y_pred)

        if normalize:
            cm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(
            cm,
            annot=True,
            fmt=".2f" if normalize else "d",
            cmap="Blues",
            xticklabels=class_names,
            yticklabels=class_names,
            ax=ax,
        )
        ax.set_xlabel("Predicted Label")
        ax.set_ylabel("True Label")
        ax.set_title(f"Confusion Matrix - Step {step}")

        # Log to TensorBoard
        self.writer.add_figure("Confusion_Matrix", fig, step)
        plt.close(fig)

        logger.debug(f"Logged confusion matrix at step {step}")

    def log_model_graph(self, model: torch.nn.Module, input_tensor: torch.Tensor) -> None:
        """Log model graph to TensorBoard.

        Args:
            model: PyTorch model
            input_tensor: Sample input tensor for the model
        """
        try:
            self.writer.add_graph(model, input_tensor)
            logger.info("Model graph logged to TensorBoard")
        except Exception as e:
            logger.warning(f"Failed to log model graph: {e}")

    def log_histograms(
        self,
        model: torch.nn.Module,
        step: int,
        log_gradients: bool = True,
    ) -> None:
        """Log model parameter and gradient histograms.

        Args:
            model: PyTorch model
            step: Current training step
            log_gradients: Whether to log gradient histograms
        """
        for name, param in model.named_parameters():
            if param is not None:
                # Log parameter values
                self.writer.add_histogram(f"Parameters/{name}", param.data, step)

                # Log gradients if available and requested
                if log_gradients and param.grad is not None:
                    self.writer.add_histogram(f"Gradients/{name}", param.grad.data, step)

        logger.debug(f"Logged parameter histograms at step {step}")

    def log_learning_rate(self, optimizer: torch.optim.Optimizer, step: int) -> None:
        """Log current learning rate(s) to TensorBoard.

        Args:
            optimizer: PyTorch optimizer
            step: Current training step
        """
        for i, param_group in enumerate(optimizer.param_groups):
            lr = param_group["lr"]
            tag = f"Learning_Rate/Group_{i}" if len(optimizer.param_groups) > 1 else "Learning_Rate"
            self.writer.add_scalar(tag, lr, step)

    def log_sample_predictions(
        self,
        images: torch.Tensor,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        class_names: list[str],
        step: int,
        num_samples: int = 8,
    ) -> None:
        """Log sample predictions with confidence scores to TensorBoard.

        Args:
            images: Batch of input images (B, C, H, W)
            predictions: Model predictions (B, num_classes)
            targets: True labels (B,)
            class_names: List of class names
            step: Current training step
            num_samples: Number of samples to log
        """
        num_samples = min(num_samples, images.size(0))

        # Get probabilities and predicted classes
        probs = F.softmax(predictions, dim=1)
        pred_classes = torch.argmax(predictions, dim=1)

        # Select samples to log
        indices = torch.randperm(images.size(0))[:num_samples]
        sample_images = images[indices]
        sample_probs = probs[indices]
        sample_preds = pred_classes[indices]
        sample_targets = targets[indices]

        # Create figure with predictions
        fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        axes = axes.flatten()

        for i in range(num_samples):
            ax = axes[i]

            # Convert image to displayable format
            img = sample_images[i].cpu()
            if img.dim() == 3 and img.size(0) == 3:  # RGB
                img = img.permute(1, 2, 0)
            elif img.dim() == 3 and img.size(0) == 1:  # Grayscale
                img = img.squeeze(0)

            # Normalize to [0, 1] if needed
            if img.min() < 0 or img.max() > 1:
                img = (img - img.min()) / (img.max() - img.min())

            ax.imshow(img, cmap="gray" if img.dim() == 2 else None)

            # Add prediction info
            pred_idx = sample_preds[i].item()
            target_idx = sample_targets[i].item()
            confidence = sample_probs[i, pred_idx].item()

            pred_name = class_names[pred_idx] if pred_idx < len(class_names) else f"Class_{pred_idx}"
            target_name = class_names[target_idx] if target_idx < len(class_names) else f"Class_{target_idx}"

            # Color code: green for correct, red for incorrect
            color = "green" if pred_idx == target_idx else "red"

            ax.set_title(
                f"Pred: {pred_name}\nTrue: {target_name}\nConf: {confidence:.3f}",
                color=color,
                fontsize=10,
            )
            ax.axis("off")

        # Hide unused subplots
        for i in range(num_samples, len(axes)):
            axes[i].axis("off")

        plt.tight_layout()
        self.writer.add_figure("Sample_Predictions", fig, step)
        plt.close(fig)

        logger.debug(f"Logged {num_samples} sample predictions at step {step}")

    def setup_progress_tracking(self, total_epochs: int, steps_per_epoch: int) -> None:
        """Setup progress tracking for training.

        Args:
            total_epochs: Total number of training epochs
            steps_per_epoch: Number of steps per epoch
        """
        self.progress_tracker = ProgressTracker(total_epochs, steps_per_epoch)
        logger.info(f"Progress tracking setup: {total_epochs} epochs, {steps_per_epoch} steps/epoch")

    def start_epoch_tracking(self, epoch: int) -> None:
        """Start tracking for a new epoch.

        Args:
            epoch: Current epoch number
        """
        if self.progress_tracker:
            self.progress_tracker.start_epoch(epoch)
        self.metrics_collector.reset()

    def update_batch_progress(
        self,
        loss: float,
        accuracy: float | None = None,
        batch_time: float = 0.0,
        data_time: float = 0.0,
        learning_rate: float | None = None,
        batch_size: int = 32,
    ) -> dict[str, float]:
        """Update progress with batch metrics.

        Args:
            loss: Batch loss
            accuracy: Batch accuracy
            batch_time: Time to process batch
            data_time: Time to load data
            learning_rate: Current learning rate
            batch_size: Batch size

        Returns:
            Current aggregated metrics
        """
        # Update metrics collector
        self.metrics_collector.add_batch_metrics(
            loss=loss,
            accuracy=accuracy,
            batch_time=batch_time,
            data_time=data_time,
            learning_rate=learning_rate,
        )

        # Update progress tracker if available
        if self.progress_tracker:
            from .progress import BatchMetrics

            batch_metrics = BatchMetrics(
                loss=loss,
                accuracy=accuracy,
                batch_size=batch_size,
                processing_time=batch_time,
                data_loading_time=data_time,
            )
            self.progress_tracker.update_batch(batch_metrics)

        return self.metrics_collector.get_current_metrics()

    def finish_epoch_tracking(
        self,
        val_loss: float | None = None,
        val_accuracy: float | None = None,
        learning_rate: float | None = None,
    ) -> dict[str, float]:
        """Finish epoch tracking and return summary.

        Args:
            val_loss: Validation loss
            val_accuracy: Validation accuracy
            learning_rate: Current learning rate

        Returns:
            Epoch summary metrics
        """
        if self.progress_tracker:
            progress_metrics = self.progress_tracker.finish_epoch(
                val_loss=val_loss,
                val_accuracy=val_accuracy,
                learning_rate=learning_rate,
            )

            # Safely get attributes with defaults and return a summary dict
            metrics: dict[str, float | None] = {
                "epoch": getattr(progress_metrics, "epoch", 0.0),
                "train_loss": getattr(progress_metrics, "train_loss", 0.0),
                "val_loss": val_loss,
                "val_accuracy": val_accuracy,
                "learning_rate": learning_rate,
                "eta": getattr(progress_metrics, "eta", 0.0),
            }

            return metrics

        return {}

    def analyze_model_layers(self, model: torch.nn.Module) -> dict[str, Any]:
        """Analyze model layers and generate layer-wise statistics.

        Args:
            model: PyTorch model to analyze

        Returns:
            Dictionary with layer-wise analysis results
        """
        from .reporting import ModelAnalyzer

        model_analysis = ModelAnalyzer.analyze_model(model)

        # Log layer statistics to TensorBoard
        layer_stats = {}
        for layer_name, layer_info in model_analysis.layer_details.items():
            layer_stats[f"Layers/{layer_name}/Parameters"] = layer_info["parameters"]
            layer_stats[f"Layers/{layer_name}/Trainable"] = layer_info["trainable"]

        # Log parameter distribution
        for layer_type, param_count in model_analysis.parameter_distribution.items():
            layer_stats[f"Parameter_Distribution/{layer_type}"] = param_count

        # Log overall model statistics
        layer_stats["Model/Total_Parameters"] = model_analysis.total_parameters
        layer_stats["Model/Trainable_Parameters"] = model_analysis.trainable_parameters
        layer_stats["Model/Size_MB"] = model_analysis.model_size_mb
        layer_stats["Model/Layer_Count"] = model_analysis.layer_count

        # Log to TensorBoard
        for name, value in layer_stats.items():
            self.writer.add_scalar(name, value, 0)  # Step 0 for model analysis

        logger.info(f"Model analysis complete: {model_analysis.total_parameters:,} parameters, {model_analysis.model_size_mb:.2f} MB")

        return {
            "model_analysis": model_analysis,
            "layer_statistics": layer_stats,
        }

    def save_training_report(
        self,
        model: torch.nn.Module | None = None,
        model_info: dict[str, Any] | None = None,
        dataset_info: dict[str, Any] | None = None,
        hyperparameters: dict[str, Any] | None = None,
        system_info: dict[str, Any] | None = None,
    ) -> dict[str, Path]:
        """Generate and save comprehensive training report with visualizations.

        Args:
            model: Trained PyTorch model for analysis (optional)
            model_info: Information about the model
            dataset_info: Information about the dataset
            hyperparameters: Training hyperparameters
            system_info: System and hardware information

        Returns:
            Dictionary mapping report types to file paths
        """
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        # Get final metrics from last entry
        final_metrics = {}
        if self.metrics_history:
            last_metrics = self.metrics_history[-1]
            final_metrics = {
                "train_loss": last_metrics.train_loss,
                "val_loss": last_metrics.val_loss,
                "train_accuracy": last_metrics.train_accuracy,
                "val_accuracy": last_metrics.val_accuracy,
            }
            # Remove None values
            final_metrics = {k: v for k, v in final_metrics.items() if v is not None}

        # Create training report
        report = TrainingReport(
            experiment_name=self.experiment_name,
            start_time=self.start_time,
            end_time=end_time,
            total_duration=total_duration,
            final_metrics=final_metrics,
            best_metrics=self.best_metrics,
            training_history=self.metrics_history,
            model_info=model_info or {},
            dataset_info=dataset_info or {},
            hyperparameters=hyperparameters or {},
            system_info=system_info or {},
        )

        # Save basic JSON report
        report_path = self.experiment_dir / "training_report.json"
        with open(report_path, "w") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        # Generate human-readable summary
        summary_path = self.experiment_dir / "training_summary.txt"
        self._generate_summary_text(report, summary_path)

        generated_files = {
            "json_report": report_path,
            "text_summary": summary_path,
        }

        # Generate comprehensive reports with visualizations if we have training data
        if self.metrics_history:
            # Extract training curves
            train_losses = [m.train_loss for m in self.metrics_history if m.train_loss is not None]
            val_losses = [m.val_loss for m in self.metrics_history if m.val_loss is not None]
            train_accuracies = [m.train_accuracy for m in self.metrics_history if m.train_accuracy is not None]
            val_accuracies = [m.val_accuracy for m in self.metrics_history if m.val_accuracy is not None]

            # Use reporting system for comprehensive analysis
            report_generator = TrainingReportGenerator(self.experiment_dir)

            # Generate training curves
            if train_losses and val_losses:
                curves_path = report_generator.generate_training_curves(
                    train_losses=train_losses,
                    val_losses=val_losses,
                    train_accuracies=train_accuracies if train_accuracies else None,
                    val_accuracies=val_accuracies if val_accuracies else None,
                )
                generated_files["training_curves"] = curves_path

                # Analyze training curves
                curve_analysis = TrainingCurveAnalyzer.analyze_training_curves(train_losses, val_losses, train_accuracies, val_accuracies)
            else:
                curve_analysis = None

            # Analyze model if provided
            if model:
                model_analysis = ModelAnalyzer.analyze_model(model)

                # Generate model architecture plot
                arch_path = report_generator.generate_model_architecture_plot(model_analysis)
                generated_files["model_architecture"] = arch_path

                # Generate comprehensive HTML report
                if curve_analysis:
                    training_metrics = {
                        "best_val_loss": min(val_losses) if val_losses else None,
                        "best_val_accuracy": max(val_accuracies) if val_accuracies else None,
                        "total_duration": total_duration,
                    }

                    html_report_path = report_generator.generate_comprehensive_report(
                        experiment_name=self.experiment_name,
                        model_analysis=model_analysis,
                        curve_analysis=curve_analysis,
                        training_metrics=training_metrics,
                        hyperparameters=hyperparameters or {},
                        system_info=system_info,
                    )
                    generated_files["html_report"] = html_report_path

        logger.info(f"Training reports generated: {list(generated_files.keys())}")
        return generated_files

    def _generate_summary_text(self, report: TrainingReport, output_path: Path) -> None:
        """Generate human-readable training summary."""
        with open(output_path, "w") as f:
            f.write("PlantGuard Training Report\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Experiment: {report.experiment_name}\n")
            f.write(f"Start Time: {report.start_time}\n")
            f.write(f"End Time: {report.end_time}\n")
            f.write(f"Duration: {report.total_duration:.2f} seconds ({report.total_duration / 3600:.2f} hours)\n\n")

            f.write("Final Metrics:\n")
            for name, value in report.final_metrics.items():
                f.write(f"  {name}: {value:.4f}\n")
            f.write("\n")

            f.write("Best Metrics:\n")
            for name, value in report.best_metrics.items():
                f.write(f"  {name}: {value:.4f}\n")
            f.write("\n")

            if report.model_info:
                f.write("Model Information:\n")
                for key, value in report.model_info.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")

            if report.hyperparameters:
                f.write("Hyperparameters:\n")
                for key, value in report.hyperparameters.items():
                    f.write(f"  {key}: {value}\n")

    def launch_tensorboard(self, open_browser: bool = True) -> bool:
        """Launch TensorBoard server.

        Args:
            open_browser: Whether to automatically open browser

        Returns:
            True if TensorBoard was launched successfully
        """
        try:
            # Check if TensorBoard is already running
            if self.tensorboard_process and self.tensorboard_process.poll() is None:
                logger.info(f"TensorBoard already running on port {self.tensorboard_port}")
                if open_browser:
                    webbrowser.open(f"http://localhost:{self.tensorboard_port}")
                return True

            # Launch TensorBoard
            cmd = [
                sys.executable,
                "-m",
                "tensorboard.main",
                "tensorboard",
                "--logdir",
                str(self.log_dir),
                "--port",
                str(self.tensorboard_port),
                "--reload_interval",
                "1",
            ]

            self.tensorboard_process = subprocess.Popen(  # nosec B603: shell=False, inputs are sanitized
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,  # Safer than shell=True
                start_new_session=True,  # Prevents signals from being sent to the parent process
            )

            # Wait a moment for TensorBoard to start
            time.sleep(2)

            # Check if process is still running
            if self.tensorboard_process.poll() is None:
                logger.info(f"TensorBoard launched on http://localhost:{self.tensorboard_port}")

                if open_browser:
                    # Open browser in a separate thread to avoid blocking
                    def open_browser_delayed():
                        time.sleep(1)
                        webbrowser.open(f"http://localhost:{self.tensorboard_port}")

                    threading.Thread(target=open_browser_delayed, daemon=True).start()

                return True
            else:
                logger.error("TensorBoard failed to start")
                return False

        except FileNotFoundError:
            logger.error("TensorBoard not found. Install with: pip install tensorboard")
            return False
        except Exception as e:
            logger.error(f"Failed to launch TensorBoard: {e}")
            return False

    def stop_tensorboard(self) -> None:
        """Stop TensorBoard server if running."""
        if self.tensorboard_process and self.tensorboard_process.poll() is None:
            self.tensorboard_process.terminate()
            self.tensorboard_process.wait()
            logger.info("TensorBoard server stopped")

    def close(self) -> None:
        """Close the monitor and cleanup resources."""
        if self.writer:
            self.writer.close()

        self.stop_tensorboard()
        logger.info("Training monitor closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_training_monitor(
    experiment_name: str,
    log_dir: Path | str = "runs",
    auto_launch_tensorboard: bool = False,
) -> TrainingMonitor:
    """Factory function to create a TrainingMonitor instance.

    Args:
        experiment_name: Name of the training experiment
        log_dir: Directory for logs (default: "runs")
        auto_launch_tensorboard: Whether to auto-launch TensorBoard

    Returns:
        Configured TrainingMonitor instance
    """
    return TrainingMonitor(
        experiment_name=experiment_name,
        log_dir=log_dir,
        auto_launch_tensorboard=auto_launch_tensorboard,
    )
