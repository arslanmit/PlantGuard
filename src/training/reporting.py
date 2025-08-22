"""Comprehensive training reporting and analysis for PlantGuard production training.

This module provides detailed training reports, model analysis tools, and training
curve visualization for production training workflows.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from torch import nn

logger = logging.getLogger(__name__)


@dataclass
class ModelAnalysis:
    """Analysis of model architecture and parameters."""

    total_parameters: int
    trainable_parameters: int
    model_size_mb: float
    layer_count: int
    layer_details: dict[str, dict[str, Any]]
    parameter_distribution: dict[str, int]
    gradient_flow: dict[str, float] | None = None


@dataclass
class TrainingCurveAnalysis:
    """Analysis of training curves and convergence."""

    convergence_epoch: int | None
    overfitting_detected: bool
    overfitting_epoch: int | None
    best_epoch: int
    final_gap: float  # Gap between train and validation loss
    learning_stability: float  # Measure of learning stability
    improvement_rate: float  # Rate of improvement per epoch


class ModelAnalyzer:
    """Analyzes PyTorch models for detailed reporting."""

    @staticmethod
    def analyze_model(model: nn.Module) -> ModelAnalysis:
        """Perform comprehensive model analysis.

        Args:
            model: PyTorch model to analyze

        Returns:
            ModelAnalysis with detailed model information
        """
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        # Estimate model size
        param_size = sum(p.numel() * p.element_size() for p in model.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
        model_size_mb = (param_size + buffer_size) / 1024**2

        # Analyze layers
        layer_details: dict[str, dict[str, Any]] = {}
        layer_count: int = 0
        parameter_distribution: dict[str, int] = {}

        for name, module in model.named_modules():
            if len(list(module.children())) == 0:  # Leaf modules only
                layer_count += 1
                module_type = type(module).__name__

                # Count parameters for this layer
                layer_params = sum(p.numel() for p in module.parameters())

                layer_details[name] = {
                    "type": module_type,
                    "parameters": layer_params,
                    "trainable": sum(p.numel() for p in module.parameters() if p.requires_grad),
                }

                # Update parameter distribution
                if module_type in parameter_distribution:
                    parameter_distribution[module_type] += layer_params
                else:
                    parameter_distribution[module_type] = layer_params

        return ModelAnalysis(
            total_parameters=total_params,
            trainable_parameters=trainable_params,
            model_size_mb=model_size_mb,
            layer_count=layer_count,
            layer_details=layer_details,
            parameter_distribution=parameter_distribution,
        )

    @staticmethod
    def analyze_gradient_flow(model: nn.Module) -> dict[str, float]:
        """Analyze gradient flow through the model.

        Args:
            model: PyTorch model with computed gradients

        Returns:
            Dictionary with gradient statistics per layer
        """
        gradient_flow = {}

        for name, param in model.named_parameters():
            if param.grad is not None:
                grad_norm = float(param.grad.norm().item())
                gradient_flow[name] = grad_norm

        return gradient_flow


class TrainingCurveAnalyzer:
    """Analyzes training curves for convergence and overfitting detection."""

    @staticmethod
    def analyze_training_curves(
        train_losses: list[float],
        val_losses: list[float],
        train_accuracies: list[float] | None = None,
        val_accuracies: list[float] | None = None,
    ) -> TrainingCurveAnalysis:
        """Analyze training curves for patterns and issues.

        Args:
            train_losses: Training losses per epoch
            val_losses: Validation losses per epoch
            train_accuracies: Training accuracies per epoch (optional)
            val_accuracies: Validation accuracies per epoch (optional)

        Returns:
            TrainingCurveAnalysis with detailed analysis
        """
        if len(train_losses) != len(val_losses):
            raise ValueError("Training and validation losses must have same length")

        epochs: int = len(train_losses)

        # Find best epoch (lowest validation loss)
        best_epoch: int = int(np.argmin(val_losses))

        # Detect convergence (when validation loss stops improving significantly)
        convergence_epoch = None
        patience = max(5, epochs // 10)  # Adaptive patience
        min_improvement = 0.001

        for i in range(patience, epochs):
            recent_losses = val_losses[i - patience : i]
            if len(recent_losses) >= patience:
                improvement = max(recent_losses) - min(recent_losses)
                if improvement < min_improvement:
                    convergence_epoch = i - patience
                    break

        # Detect overfitting (when validation loss starts increasing while training loss decreases)
        overfitting_detected = False
        overfitting_epoch = None

        if epochs > 10:
            # Look for sustained divergence between train and val loss
            for i in range(10, epochs):
                recent_train = train_losses[i - 5 : i]
                recent_val = val_losses[i - 5 : i]

                # Check if training loss is decreasing while validation loss is increasing
                train_trend = float(np.polyfit(range(len(recent_train)), recent_train, 1)[0])
                val_trend = float(np.polyfit(range(len(recent_val)), recent_val, 1)[0])

                if train_trend < -0.001 and val_trend > 0.001:
                    overfitting_detected = True
                    overfitting_epoch = i - 5
                    break

        # Calculate final gap between train and validation loss
        final_gap: float = float(val_losses[-1]) - float(train_losses[-1])

        # Calculate learning stability (inverse of loss variance)
        train_stability = float(1.0 / (np.var(train_losses[-10:]) + 1e-8)) if epochs >= 10 else 1.0
        val_stability = float(1.0 / (np.var(val_losses[-10:]) + 1e-8)) if epochs >= 10 else 1.0
        learning_stability: float = float(min(train_stability, val_stability))

        # Calculate improvement rate (loss reduction per epoch)
        if epochs > 1:
            initial_loss = float(val_losses[0])
            final_loss = float(val_losses[-1])
            improvement_rate: float = float((initial_loss - final_loss) / epochs)
        else:
            improvement_rate = 0.0

        return TrainingCurveAnalysis(
            convergence_epoch=convergence_epoch,
            overfitting_detected=overfitting_detected,
            overfitting_epoch=overfitting_epoch,
            best_epoch=best_epoch,
            final_gap=final_gap,
            learning_stability=learning_stability,
            improvement_rate=improvement_rate,
        )


class TrainingReportGenerator:
    """Generates comprehensive training reports with visualizations."""

    def __init__(self, output_dir: Path) -> None:
        """Initialize report generator.

        Args:
            output_dir: Directory to save reports and visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_training_curves(
        self,
        train_losses: list[float],
        val_losses: list[float],
        train_accuracies: list[float] | None = None,
        val_accuracies: list[float] | None = None,
        save_path: Path | None = None,
    ) -> Path:
        """Generate training curve visualizations.

        Args:
            train_losses: Training losses per epoch
            val_losses: Validation losses per epoch
            train_accuracies: Training accuracies per epoch (optional)
            val_accuracies: Validation accuracies per epoch (optional)
            save_path: Path to save the plot (optional)

        Returns:
            Path to the saved plot
        """
        if save_path is None:
            save_path = self.output_dir / "training_curves.png"

        # Create subplots
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        epochs = range(1, len(train_losses) + 1)

        # Loss curves
        axes[0].plot(epochs, train_losses, label="Training Loss", color="blue", linewidth=2)
        axes[0].plot(epochs, val_losses, label="Validation Loss", color="red", linewidth=2)
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Loss")
        axes[0].set_title("Training and Validation Loss")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Accuracy curves (if available)
        if train_accuracies and val_accuracies:
            axes[1].plot(epochs, train_accuracies, label="Training Accuracy", color="blue", linewidth=2)
            axes[1].plot(epochs, val_accuracies, label="Validation Accuracy", color="red", linewidth=2)
            axes[1].set_xlabel("Epoch")
            axes[1].set_ylabel("Accuracy")
            axes[1].set_title("Training and Validation Accuracy")
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
        else:
            # Show loss zoomed in if no accuracy data
            axes[1].plot(epochs, train_losses, label="Training Loss", color="blue", linewidth=2)
            axes[1].plot(epochs, val_losses, label="Validation Loss", color="red", linewidth=2)
            axes[1].set_xlabel("Epoch")
            axes[1].set_ylabel("Loss")
            axes[1].set_title("Loss (Zoomed)")
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)

            # Zoom to show details
            if len(train_losses) > 10:
                y_min = min(min(train_losses[-10:]), min(val_losses[-10:]))
                y_max = max(max(train_losses[-10:]), max(val_losses[-10:]))
                margin = (y_max - y_min) * 0.1
                axes[1].set_ylim(y_min - margin, y_max + margin)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"Training curves saved to {save_path}")
        return save_path

    def generate_model_architecture_plot(
        self,
        model_analysis: ModelAnalysis,
        save_path: Path | None = None,
    ) -> Path:
        """Generate model architecture visualization.

        Args:
            model_analysis: Model analysis results
            save_path: Path to save the plot (optional)

        Returns:
            Path to the saved plot
        """
        if save_path is None:
            save_path = self.output_dir / "model_architecture.png"

        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        # Parameter distribution pie chart
        param_dist = model_analysis.parameter_distribution
        if param_dist:
            labels = list(param_dist.keys())
            sizes = list(param_dist.values())

            axes[0].pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
            axes[0].set_title("Parameter Distribution by Layer Type")

        # Layer statistics bar chart
        layer_types: dict[str, int] = {}
        for layer_info in model_analysis.layer_details.values():
            layer_type = layer_info["type"]
            if layer_type in layer_types:
                layer_types[layer_type] += 1
            else:
                layer_types[layer_type] = 1

        if layer_types:
            types = list(layer_types.keys())
            counts = list(layer_types.values())

            axes[1].bar(types, counts, color="skyblue")
            axes[1].set_xlabel("Layer Type")
            axes[1].set_ylabel("Count")
            axes[1].set_title("Layer Count by Type")
            axes[1].tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"Model architecture plot saved to {save_path}")
        return save_path

    def generate_comprehensive_report(
        self,
        experiment_name: str,
        model_analysis: ModelAnalysis,
        curve_analysis: TrainingCurveAnalysis,
        training_metrics: dict[str, Any],
        hyperparameters: dict[str, Any],
        system_info: dict[str, Any] | None = None,
    ) -> Path:
        """Generate comprehensive HTML training report.

        Args:
            experiment_name: Name of the experiment
            model_analysis: Model analysis results
            curve_analysis: Training curve analysis
            training_metrics: Final training metrics
            hyperparameters: Training hyperparameters
            system_info: System information (optional)

        Returns:
            Path to the generated HTML report
        """
        report_path = self.output_dir / "comprehensive_report.html"

        # Generate HTML content
        # Precompute some strings that depend on optional ints to keep mypy happy
        conv_str = (
            "✅ Converged at epoch " + str(curve_analysis.convergence_epoch + 1)
            if curve_analysis.convergence_epoch is not None
            else "❌ No convergence detected"
        )

        overfit_str = (
            "⚠️ Detected at epoch " + str(curve_analysis.overfitting_epoch + 1)
            if curve_analysis.overfitting_detected and curve_analysis.overfitting_epoch is not None
            else "✅ No overfitting detected"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PlantGuard Training Report - {experiment_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #2e7d32; color: white; padding: 20px; border-radius: 8px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; }}
                .warning {{ color: #d32f2f; font-weight: bold; }}
                .success {{ color: #388e3c; font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌿 PlantGuard Training Report</h1>
                <h2>{experiment_name}</h2>
                <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>

            <div class="section">
                <h3>📊 Training Summary</h3>
                <div class="metric">
                    <strong>Best Validation Loss:</strong> {training_metrics.get("best_val_loss", "N/A"):.4f}
                </div>
                <div class="metric">
                    <strong>Best Validation Accuracy:</strong> {training_metrics.get("best_val_accuracy", "N/A"):.3f}
                </div>
                <div class="metric">
                    <strong>Training Duration:</strong> {training_metrics.get("total_duration", 0):.2f} seconds
                </div>
                <div class="metric">
                    <strong>Best Epoch:</strong> {curve_analysis.best_epoch + 1}
                </div>
            </div>

            <div class="section">
                <h3>🔍 Training Analysis</h3>
                <p><strong>Convergence:</strong> {conv_str}</p>
                <p><strong>Overfitting:</strong> {overfit_str}</p>
                <p><strong>Final Train-Val Gap:</strong> {curve_analysis.final_gap:.4f}</p>
                <p><strong>Learning Stability:</strong> {curve_analysis.learning_stability:.2f}</p>
                <p><strong>Improvement Rate:</strong> {curve_analysis.improvement_rate:.4f} loss reduction per epoch</p>
            </div>

            <div class="section">
                <h3>🏗️ Model Architecture</h3>
                <div class="metric">
                    <strong>Total Parameters:</strong> {model_analysis.total_parameters:,}
                </div>
                <div class="metric">
                    <strong>Trainable Parameters:</strong> {model_analysis.trainable_parameters:,}
                </div>
                <div class="metric">
                    <strong>Model Size:</strong> {model_analysis.model_size_mb:.2f} MB
                </div>
                <div class="metric">
                    <strong>Layer Count:</strong> {model_analysis.layer_count}
                </div>
            </div>

            <div class="section">
                <h3>⚙️ Hyperparameters</h3>
                <table>
                    <tr><th>Parameter</th><th>Value</th></tr>
        """

        for key, value in hyperparameters.items():
            html_content += f"<tr><td>{key}</td><td>{value}</td></tr>"

        html_content += """
                </table>
            </div>
        """

        if system_info:
            html_content += """
            <div class="section">
                <h3>💻 System Information</h3>
                <table>
                    <tr><th>Component</th><th>Details</th></tr>
            """
            for key, value in system_info.items():
                html_content += f"<tr><td>{key}</td><td>{value}</td></tr>"

            html_content += "</table></div>"

        html_content += """
            <div class="section">
                <h3>📈 Visualizations</h3>
                <p>Training curves and model architecture plots are available as separate PNG files in the experiment directory.</p>
            </div>
        </body>
        </html>
        """

        # Save HTML report
        with open(report_path, "w") as f:
            f.write(html_content)

        logger.info(f"Comprehensive report saved to {report_path}")
        return report_path


def generate_training_summary(
    experiment_dir: Path,
    model: nn.Module | None = None,
    train_losses: list[float] | None = None,
    val_losses: list[float] | None = None,
    train_accuracies: list[float] | None = None,
    val_accuracies: list[float] | None = None,
    hyperparameters: dict[str, Any] | None = None,
    system_info: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Generate complete training summary with all reports and visualizations.

    Args:
        experiment_dir: Directory to save all outputs
        model: Trained PyTorch model (optional)
        train_losses: Training losses per epoch
        val_losses: Validation losses per epoch
        train_accuracies: Training accuracies per epoch (optional)
        val_accuracies: Validation accuracies per epoch (optional)
        hyperparameters: Training hyperparameters
        system_info: System information

    Returns:
        Dictionary mapping report types to file paths
    """
    experiment_dir = Path(experiment_dir)
    report_generator = TrainingReportGenerator(experiment_dir)

    generated_files = {}

    # Generate training curves if data is available
    if train_losses and val_losses:
        curves_path = report_generator.generate_training_curves(train_losses, val_losses, train_accuracies, val_accuracies)
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
    else:
        model_analysis = None

    # Generate comprehensive report if we have enough data
    if model_analysis and curve_analysis:
        training_metrics = {
            "best_val_loss": float(min(val_losses)) if val_losses else None,
            "best_val_accuracy": float(max(val_accuracies)) if val_accuracies else None,
            "total_duration": 0,  # This should be provided by the caller
        }

        report_path = report_generator.generate_comprehensive_report(
            experiment_name=experiment_dir.name,
            model_analysis=model_analysis,
            curve_analysis=curve_analysis,
            training_metrics=training_metrics,
            hyperparameters=hyperparameters or {},
            system_info=system_info,
        )
        generated_files["comprehensive_report"] = report_path

    logger.info(f"Generated {len(generated_files)} report files in {experiment_dir}")
    return generated_files
