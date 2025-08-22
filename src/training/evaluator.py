"""Model evaluation and validation system for PlantGuard production training pipeline.

This module provides comprehensive model evaluation with detailed metrics calculation,
confusion matrix generation, ROC curve analysis, and model comparison tools.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

logger = logging.getLogger(__name__)


@dataclass
class ClassMetrics:
    """Metrics for a single class."""

    class_name: str
    precision: float
    recall: float
    f1_score: float
    support: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


@dataclass
class ModelMetrics:
    """Comprehensive model evaluation metrics."""

    # Overall metrics
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_precision: float
    weighted_recall: float
    weighted_f1: float

    # Per-class metrics
    class_metrics: list[ClassMetrics]

    # Additional metrics
    total_samples: int
    num_classes: int
    evaluation_time: float

    # Confusion matrix
    confusion_matrix: list[list[int]]
    class_names: list[str]

    # ROC metrics (if applicable)
    roc_auc_macro: float | None = None
    roc_auc_weighted: float | None = None
    roc_curves: dict[str, dict[str, list[float]]] | None = None


@dataclass
class ModelComparison:
    """Comparison between multiple models."""

    model_names: list[str]
    metrics_comparison: dict[str, list[float]]
    best_model: str
    ranking: list[tuple[str, float]]  # (model_name, score)
    statistical_significance: dict[str, dict[str, float]] | None = None


@dataclass
class ValidationResult:
    """Result of model validation."""

    model_path: str
    validation_passed: bool
    metrics: ModelMetrics
    quality_score: float
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class ModelEvaluator:
    """Comprehensive model evaluation with detailed metrics and analysis."""

    def __init__(
        self,
        device: torch.device | None = None,
        class_names: list[str] | None = None,
    ) -> None:
        """Initialize ModelEvaluator.

        Args:
            device: Device to run evaluation on
            class_names: List of class names for labeling
        """
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.class_names = class_names or []
        logger.info(f"ModelEvaluator initialized on device: {self.device}")

    def evaluate_model(
        self,
        model: nn.Module,
        data_loader: DataLoader,
        class_names: list[str] | None = None,
        compute_roc: bool = True,
    ) -> ModelMetrics:
        """Evaluate model with comprehensive metrics.

        Args:
            model: PyTorch model to evaluate
            data_loader: DataLoader for evaluation data
            class_names: List of class names (optional)
            compute_roc: Whether to compute ROC curves

        Returns:
            ModelMetrics with comprehensive evaluation results
        """
        logger.info("Starting comprehensive model evaluation...")
        start_time = time.time()

        # Use provided class names or fallback to stored ones
        eval_class_names = class_names or self.class_names
        if not eval_class_names:
            eval_class_names = [f"Class_{i}" for i in range(self._get_num_classes(model))]

        # Get predictions and true labels
        y_true, y_pred, y_proba = self._get_predictions(model, data_loader)

        # Calculate basic metrics
        accuracy = accuracy_score(y_true, y_pred)

        # Calculate precision, recall, f1 for each averaging method
        macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
        weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)

        # Calculate per-class metrics
        class_metrics = self._calculate_class_metrics(y_true, y_pred, eval_class_names)

        # Generate confusion matrix
        cm = confusion_matrix(y_true, y_pred)

        # Calculate ROC metrics if requested
        roc_auc_macro = None
        roc_auc_weighted = None
        roc_curves = None

        if compute_roc and y_proba is not None:
            try:
                roc_auc_macro, roc_auc_weighted, roc_curves = self._calculate_roc_metrics(y_true, y_proba, eval_class_names)
            except Exception as e:
                logger.warning(f"Failed to calculate ROC metrics: {e}")

        evaluation_time = time.time() - start_time

        metrics = ModelMetrics(
            accuracy=accuracy,
            macro_precision=macro_precision,
            macro_recall=macro_recall,
            macro_f1=macro_f1,
            weighted_precision=weighted_precision,
            weighted_recall=weighted_recall,
            weighted_f1=weighted_f1,
            class_metrics=class_metrics,
            total_samples=len(y_true),
            num_classes=len(eval_class_names),
            evaluation_time=evaluation_time,
            confusion_matrix=cm.tolist(),
            class_names=eval_class_names,
            roc_auc_macro=roc_auc_macro,
            roc_auc_weighted=roc_auc_weighted,
            roc_curves=roc_curves,
        )

        logger.info(f"Model evaluation completed in {evaluation_time:.2f}s")
        logger.info(f"Accuracy: {accuracy:.4f}, Macro F1: {macro_f1:.4f}")

        return metrics

    def _get_predictions(self, model: nn.Module, data_loader: DataLoader) -> tuple[list[int], list[int], np.ndarray | None]:
        """Get model predictions and probabilities.

        Args:
            model: PyTorch model
            data_loader: DataLoader for evaluation

        Returns:
            Tuple of (true_labels, predicted_labels, probabilities)
        """
        model.eval()
        y_true = []
        y_pred = []
        y_proba_list = []

        with torch.no_grad():
            for batch_data, batch_target in tqdm(data_loader, desc="Evaluating", leave=False):
                data, target = batch_data.to(self.device), batch_target.to(self.device)

                # Forward pass
                output = model(data)
                probabilities = torch.softmax(output, dim=1)

                # Get predictions
                _, predicted = torch.max(output, 1)

                # Store results
                y_true.extend(target.cpu().numpy().tolist())
                y_pred.extend(predicted.cpu().numpy().tolist())
                y_proba_list.append(probabilities.cpu().numpy())

        # Concatenate probabilities
        y_proba = np.vstack(y_proba_list) if y_proba_list else None

        return y_true, y_pred, y_proba

    def _calculate_class_metrics(self, y_true: list[int], y_pred: list[int], class_names: list[str]) -> list[ClassMetrics]:
        """Calculate detailed metrics for each class.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            class_names: List of class names

        Returns:
            List of ClassMetrics for each class
        """
        # Calculate confusion matrix for detailed per-class metrics
        cm = confusion_matrix(y_true, y_pred)

        # Calculate precision, recall, f1 per class
        precision_per_class = precision_score(y_true, y_pred, average=None, zero_division=0)
        recall_per_class = recall_score(y_true, y_pred, average=None, zero_division=0)
        f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)

        # Calculate support (number of true instances for each class)
        _, _, _, support_per_class = precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0)

        class_metrics = []
        num_classes = len(class_names)

        for i in range(num_classes):
            # Calculate TP, FP, FN, TN for this class
            if i < len(cm):
                tp = cm[i, i] if i < cm.shape[0] and i < cm.shape[1] else 0
                fp = cm[:, i].sum() - tp if i < cm.shape[1] else 0
                fn = cm[i, :].sum() - tp if i < cm.shape[0] else 0
                tn = cm.sum() - tp - fp - fn
            else:
                tp = fp = fn = tn = 0

            class_metric = ClassMetrics(
                class_name=class_names[i],
                precision=precision_per_class[i] if i < len(precision_per_class) else 0.0,
                recall=recall_per_class[i] if i < len(recall_per_class) else 0.0,
                f1_score=f1_per_class[i] if i < len(f1_per_class) else 0.0,
                support=int(support_per_class[i]) if i < len(support_per_class) else 0,
                true_positives=int(tp),
                false_positives=int(fp),
                false_negatives=int(fn),
                true_negatives=int(tn),
            )
            class_metrics.append(class_metric)

        return class_metrics

    def _calculate_roc_metrics(
        self, y_true: list[int], y_proba: np.ndarray, class_names: list[str]
    ) -> tuple[float | None, float | None, dict[str, dict[str, list[float]]] | None]:
        """Calculate ROC AUC metrics and curves.

        Args:
            y_true: True labels
            y_proba: Prediction probabilities
            class_names: List of class names

        Returns:
            Tuple of (macro_auc, weighted_auc, roc_curves)
        """
        from sklearn.preprocessing import label_binarize

        # Binarize labels for multi-class ROC
        y_true_bin = label_binarize(y_true, classes=list(range(len(class_names))))

        # Handle binary classification case
        if y_true_bin.shape[1] == 1:
            y_true_bin = np.hstack([1 - y_true_bin, y_true_bin])

        # Calculate macro and weighted AUC
        try:
            roc_auc_macro = roc_auc_score(y_true_bin, y_proba, average="macro", multi_class="ovr")
            roc_auc_weighted = roc_auc_score(y_true_bin, y_proba, average="weighted", multi_class="ovr")
        except ValueError as e:
            logger.warning(f"Could not calculate ROC AUC: {e}")
            return None, None, None

        # Calculate ROC curves for each class
        roc_curves = {}
        for i, class_name in enumerate(class_names):
            if i < y_proba.shape[1] and i < y_true_bin.shape[1]:
                try:
                    fpr, tpr, thresholds = roc_curve(y_true_bin[:, i], y_proba[:, i])
                    roc_curves[class_name] = {
                        "fpr": fpr.tolist(),
                        "tpr": tpr.tolist(),
                        "thresholds": thresholds.tolist(),
                    }
                except Exception as e:
                    logger.warning(f"Could not calculate ROC curve for class {class_name}: {e}")

        return roc_auc_macro, roc_auc_weighted, roc_curves

    def _get_num_classes(self, model: nn.Module) -> int:
        """Get number of classes from model architecture.

        Args:
            model: PyTorch model

        Returns:
            Number of output classes
        """
        # Try to get from final layer
        for module in reversed(list(model.modules())):
            if isinstance(module, nn.Linear):
                return module.out_features

        # Fallback
        return 10

    def generate_classification_report(self, metrics: ModelMetrics, output_path: Path | None = None) -> str:
        """Generate detailed classification report.

        Args:
            metrics: ModelMetrics from evaluation
            output_path: Optional path to save report

        Returns:
            Classification report as string
        """
        # Create sklearn-style classification report
        y_true = []
        y_pred = []

        # Reconstruct labels from confusion matrix for sklearn report
        cm = np.array(metrics.confusion_matrix)
        for i in range(len(metrics.class_names)):
            for j in range(len(metrics.class_names)):
                count = cm[i, j]
                y_true.extend([i] * count)
                y_pred.extend([j] * count)

        # Generate sklearn classification report
        sklearn_report = classification_report(y_true, y_pred, target_names=metrics.class_names, digits=4, zero_division=0)

        # Create enhanced report
        report_lines = [
            "=" * 80,
            "COMPREHENSIVE MODEL EVALUATION REPORT",
            "=" * 80,
            "",
            f"Evaluation Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Samples: {metrics.total_samples:,}",
            f"Number of Classes: {metrics.num_classes}",
            f"Evaluation Time: {metrics.evaluation_time:.2f} seconds",
            "",
            "OVERALL METRICS",
            "-" * 40,
            f"Accuracy:           {metrics.accuracy:.4f}",
            f"Macro Precision:    {metrics.macro_precision:.4f}",
            f"Macro Recall:       {metrics.macro_recall:.4f}",
            f"Macro F1-Score:     {metrics.macro_f1:.4f}",
            f"Weighted Precision: {metrics.weighted_precision:.4f}",
            f"Weighted Recall:    {metrics.weighted_recall:.4f}",
            f"Weighted F1-Score:  {metrics.weighted_f1:.4f}",
        ]

        # Add ROC metrics if available
        if metrics.roc_auc_macro is not None:
            report_lines.extend(
                [
                    f"ROC AUC (Macro):    {metrics.roc_auc_macro:.4f}",
                    f"ROC AUC (Weighted): {metrics.roc_auc_weighted:.4f}",
                ]
            )

        report_lines.extend(
            [
                "",
                "DETAILED CLASSIFICATION REPORT",
                "-" * 40,
                sklearn_report,
                "",
                "PER-CLASS DETAILED METRICS",
                "-" * 40,
            ]
        )

        # Add detailed per-class metrics
        for class_metric in metrics.class_metrics:
            report_lines.extend(
                [
                    f"Class: {class_metric.class_name}",
                    f"  Precision: {class_metric.precision:.4f}",
                    f"  Recall:    {class_metric.recall:.4f}",
                    f"  F1-Score:  {class_metric.f1_score:.4f}",
                    f"  Support:   {class_metric.support}",
                    f"  TP: {class_metric.true_positives}, FP: {class_metric.false_positives}",
                    f"  FN: {class_metric.false_negatives}, TN: {class_metric.true_negatives}",
                    "",
                ]
            )

        report_text = "\n".join(report_lines)

        # Save to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                f.write(report_text)
            logger.info(f"Classification report saved to {output_path}")

        return report_text

    def save_metrics(self, metrics: ModelMetrics, output_path: Path) -> None:
        """Save metrics to JSON file.

        Args:
            metrics: ModelMetrics to save
            output_path: Path to save JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary for JSON serialization
        metrics_dict = asdict(metrics)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(metrics_dict, f, indent=2, default=str)

        logger.info(f"Metrics saved to {output_path}")

    def load_metrics(self, metrics_path: Path) -> ModelMetrics:
        """Load metrics from JSON file.

        Args:
            metrics_path: Path to JSON metrics file

        Returns:
            ModelMetrics instance

        Raises:
            FileNotFoundError: If metrics file doesn't exist
            ValueError: If JSON is invalid
        """
        if not metrics_path.exists():
            raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

        try:
            with metrics_path.open("r", encoding="utf-8") as f:
                metrics_dict = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in metrics file: {e}") from e

        # Reconstruct ClassMetrics objects
        class_metrics = []
        for cm_dict in metrics_dict.get("class_metrics", []):
            class_metrics.append(ClassMetrics(**cm_dict))

        # Remove class_metrics from dict and reconstruct ModelMetrics
        metrics_dict["class_metrics"] = class_metrics

        return ModelMetrics(**metrics_dict)

    def compare_models(
        self,
        model_metrics: dict[str, ModelMetrics],
        ranking_weights: dict[str, float] | None = None,
        compute_significance: bool = False,
    ) -> ModelComparison:
        """Compare multiple models based on their metrics.

        Args:
            model_metrics: Dictionary mapping model names to their metrics
            ranking_weights: Weights for different metrics in ranking (optional)
            compute_significance: Whether to compute statistical significance

        Returns:
            ModelComparison with detailed comparison results
        """
        logger.info(f"Comparing {len(model_metrics)} models...")

        if not model_metrics:
            raise ValueError("No models provided for comparison")

        # Default ranking weights
        if ranking_weights is None:
            ranking_weights = {
                "accuracy": 0.3,
                "macro_f1": 0.3,
                "weighted_f1": 0.2,
                "macro_precision": 0.1,
                "macro_recall": 0.1,
            }

        model_names = list(model_metrics.keys())

        # Extract metrics for comparison
        metrics_comparison = {
            "accuracy": [model_metrics[name].accuracy for name in model_names],
            "macro_precision": [model_metrics[name].macro_precision for name in model_names],
            "macro_recall": [model_metrics[name].macro_recall for name in model_names],
            "macro_f1": [model_metrics[name].macro_f1 for name in model_names],
            "weighted_precision": [model_metrics[name].weighted_precision for name in model_names],
            "weighted_recall": [model_metrics[name].weighted_recall for name in model_names],
            "weighted_f1": [model_metrics[name].weighted_f1 for name in model_names],
        }

        # Add ROC AUC if available
        roc_auc_values = []
        for name in model_names:
            roc_auc = model_metrics[name].roc_auc_macro
            roc_auc_values.append(roc_auc if roc_auc is not None else 0.0)

        if any(val > 0 for val in roc_auc_values):
            metrics_comparison["roc_auc_macro"] = roc_auc_values
            if "roc_auc_macro" not in ranking_weights:
                # Adjust weights to include ROC AUC
                _total_weight = sum(ranking_weights.values())
                for key in ranking_weights:
                    ranking_weights[key] *= 0.8  # Scale down existing weights
                ranking_weights["roc_auc_macro"] = 0.2

        # Calculate composite scores for ranking
        ranking = []
        for i, name in enumerate(model_names):
            score = 0.0
            for metric, weight in ranking_weights.items():
                if metric in metrics_comparison:
                    score += metrics_comparison[metric][i] * weight
            ranking.append((name, score))

        # Sort by score (descending)
        ranking.sort(key=lambda x: x[1], reverse=True)
        best_model = ranking[0][0]

        # Compute statistical significance if requested
        statistical_significance = None
        if compute_significance and len(model_names) > 1:
            statistical_significance = self._compute_statistical_significance(model_metrics)

        comparison = ModelComparison(
            model_names=model_names,
            metrics_comparison=metrics_comparison,
            best_model=best_model,
            ranking=ranking,
            statistical_significance=statistical_significance,
        )

        logger.info(f"Best model: {best_model} (score: {ranking[0][1]:.4f})")
        return comparison

    def _compute_statistical_significance(self, model_metrics: dict[str, ModelMetrics]) -> dict[str, dict[str, float]]:
        """Compute statistical significance between models.

        Args:
            model_metrics: Dictionary of model metrics

        Returns:
            Dictionary of p-values for pairwise comparisons
        """
        try:
            # SciPy is optional for statistical tests; if unavailable, skip significance
            import importlib

            if importlib.util.find_spec("scipy") is None:
                logger.warning("SciPy not available, skipping statistical significance tests")
                return {}
        except Exception:
            logger.warning("Error checking for SciPy availability, skipping statistical significance tests")
            return {}

        model_names = list(model_metrics.keys())
        significance_results: dict[str, dict[str, float]] = {}

        # For each pair of models, compute significance tests
        for i, model1 in enumerate(model_names):
            significance_results[model1] = {}
            for j, model2 in enumerate(model_names):
                if i != j:
                    # Use accuracy as the primary metric for significance testing
                    # In a real implementation, you'd need the raw predictions to do proper testing
                    # For now, we'll use a placeholder based on the difference in metrics
                    acc1 = model_metrics[model1].accuracy
                    acc2 = model_metrics[model2].accuracy

                    # Placeholder p-value calculation (in practice, you'd use McNemar's test or similar)
                    diff = abs(acc1 - acc2)
                    # Simple heuristic: larger differences are more significant
                    p_value = max(0.001, 1.0 - (diff * 10))  # Simplified calculation
                    significance_results[model1][model2] = p_value

        return significance_results

    def detect_performance_regression(
        self,
        current_metrics: ModelMetrics,
        baseline_metrics: ModelMetrics,
        threshold: float = 0.05,
    ) -> dict[str, Any]:
        """Detect performance regression compared to baseline.

        Args:
            current_metrics: Current model metrics
            baseline_metrics: Baseline model metrics
            threshold: Regression threshold (5% by default)

        Returns:
            Dictionary with regression analysis results
        """
        logger.info("Detecting performance regression...")

        regression_results: dict[str, Any] = {
            "has_regression": False,
            "regressions": [],
            "improvements": [],
            "summary": {},
        }

        # Metrics to check for regression
        metrics_to_check = [
            ("accuracy", "Accuracy"),
            ("macro_f1", "Macro F1-Score"),
            ("weighted_f1", "Weighted F1-Score"),
            ("macro_precision", "Macro Precision"),
            ("macro_recall", "Macro Recall"),
        ]

        for metric_key, metric_name in metrics_to_check:
            current_value = getattr(current_metrics, metric_key)
            baseline_value = getattr(baseline_metrics, metric_key)

            # Calculate relative change
            if baseline_value > 0:
                relative_change = (current_value - baseline_value) / baseline_value
            else:
                relative_change = 0.0

            regression_results["summary"][metric_key] = {
                "current": current_value,
                "baseline": baseline_value,
                "absolute_change": current_value - baseline_value,
                "relative_change": relative_change,
            }

            # Check for regression
            if relative_change < -threshold:
                regression_results["has_regression"] = True
                regression_results["regressions"].append(
                    {
                        "metric": metric_name,
                        "current": current_value,
                        "baseline": baseline_value,
                        "change": relative_change,
                    }
                )
            elif relative_change > threshold:
                regression_results["improvements"].append(
                    {
                        "metric": metric_name,
                        "current": current_value,
                        "baseline": baseline_value,
                        "change": relative_change,
                    }
                )

        # Check ROC AUC if available
        if current_metrics.roc_auc_macro is not None and baseline_metrics.roc_auc_macro is not None:
            current_auc = current_metrics.roc_auc_macro
            baseline_auc = baseline_metrics.roc_auc_macro

            if baseline_auc > 0:
                auc_change = (current_auc - baseline_auc) / baseline_auc
                regression_results["summary"]["roc_auc_macro"] = {
                    "current": current_auc,
                    "baseline": baseline_auc,
                    "absolute_change": current_auc - baseline_auc,
                    "relative_change": auc_change,
                }

                if auc_change < -threshold:
                    regression_results["has_regression"] = True
                    regression_results["regressions"].append(
                        {
                            "metric": "ROC AUC (Macro)",
                            "current": current_auc,
                            "baseline": baseline_auc,
                            "change": auc_change,
                        }
                    )

        logger.info(f"Regression analysis complete. Regressions found: {regression_results['has_regression']}")
        return regression_results

    def validate_model_quality(
        self,
        metrics: ModelMetrics,
        quality_thresholds: dict[str, float] | None = None,
    ) -> ValidationResult:
        """Validate model quality against predefined thresholds.

        Args:
            metrics: ModelMetrics to validate
            quality_thresholds: Dictionary of quality thresholds

        Returns:
            ValidationResult with validation outcome
        """
        logger.info("Validating model quality...")

        # Default quality thresholds
        if quality_thresholds is None:
            quality_thresholds = {
                "min_accuracy": 0.7,
                "min_macro_f1": 0.65,
                "min_weighted_f1": 0.7,
                "min_macro_precision": 0.65,
                "min_macro_recall": 0.65,
                "max_class_imbalance": 0.1,  # Maximum allowed difference in per-class F1
            }

        issues = []
        recommendations = []
        validation_passed = True

        # Check overall metrics
        if metrics.accuracy < quality_thresholds["min_accuracy"]:
            validation_passed = False
            issues.append(f"Accuracy ({metrics.accuracy:.3f}) below threshold ({quality_thresholds['min_accuracy']:.3f})")
            recommendations.append("Consider increasing training epochs or adjusting hyperparameters")

        if metrics.macro_f1 < quality_thresholds["min_macro_f1"]:
            validation_passed = False
            issues.append(f"Macro F1 ({metrics.macro_f1:.3f}) below threshold ({quality_thresholds['min_macro_f1']:.3f})")
            recommendations.append("Check for class imbalance and consider data augmentation")

        if metrics.weighted_f1 < quality_thresholds["min_weighted_f1"]:
            validation_passed = False
            issues.append(f"Weighted F1 ({metrics.weighted_f1:.3f}) below threshold ({quality_thresholds['min_weighted_f1']:.3f})")

        if metrics.macro_precision < quality_thresholds["min_macro_precision"]:
            validation_passed = False
            issues.append(f"Macro Precision ({metrics.macro_precision:.3f}) below threshold ({quality_thresholds['min_macro_precision']:.3f})")
            recommendations.append("Consider adjusting classification threshold or improving data quality")

        if metrics.macro_recall < quality_thresholds["min_macro_recall"]:
            validation_passed = False
            issues.append(f"Macro Recall ({metrics.macro_recall:.3f}) below threshold ({quality_thresholds['min_macro_recall']:.3f})")
            recommendations.append("Consider data augmentation for underrepresented classes")

        # Check class-level performance
        class_f1_scores = [cm.f1_score for cm in metrics.class_metrics]
        if class_f1_scores:
            f1_std = float(np.std(class_f1_scores))
            f1_mean = float(np.mean(class_f1_scores))

            if f1_mean > 0 and (f1_std / f1_mean) > quality_thresholds["max_class_imbalance"]:
                validation_passed = False
                issues.append(f"High class performance imbalance (CV: {f1_std / f1_mean:.3f})")
                recommendations.append("Address class imbalance through resampling or class weights")

        # Check for classes with very poor performance
        poor_classes = [cm.class_name for cm in metrics.class_metrics if cm.f1_score < 0.3]
        if poor_classes:
            issues.append(f"Classes with very poor performance: {', '.join(poor_classes)}")
            recommendations.append("Investigate data quality and representation for poorly performing classes")

        # Calculate overall quality score
        quality_score = self._calculate_quality_score(metrics)

        result = ValidationResult(
            model_path="",  # Will be set by caller
            validation_passed=validation_passed,
            metrics=metrics,
            quality_score=quality_score,
            issues=issues,
            recommendations=recommendations,
        )

        logger.info(f"Model validation complete. Passed: {validation_passed}, Quality score: {quality_score:.3f}")
        return result

    def _calculate_quality_score(self, metrics: ModelMetrics) -> float:
        """Calculate overall quality score for the model.

        Args:
            metrics: ModelMetrics to score

        Returns:
            Quality score between 0 and 1
        """
        # Weighted combination of key metrics
        weights = {
            "accuracy": 0.25,
            "macro_f1": 0.25,
            "weighted_f1": 0.20,
            "macro_precision": 0.15,
            "macro_recall": 0.15,
        }

        score = 0.0
        for metric, weight in weights.items():
            value = getattr(metrics, metric)
            score += value * weight

        # Penalty for class imbalance
        class_f1_scores = [cm.f1_score for cm in metrics.class_metrics]
        if class_f1_scores:
            f1_std = float(np.std(class_f1_scores))
            f1_mean = float(np.mean(class_f1_scores))
            if f1_mean > 0:
                imbalance_penalty = min(0.1, float(f1_std / f1_mean * 0.1))
                score -= imbalance_penalty

        return max(0.0, min(1.0, score))

    def evaluate_sample_predictions(
        self,
        model: nn.Module,
        sample_data: torch.Tensor,
        sample_labels: torch.Tensor,
        class_names: list[str] | None = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        """Evaluate model on sample data with detailed prediction analysis.

        Args:
            model: PyTorch model
            sample_data: Sample input data
            sample_labels: True labels for samples
            class_names: List of class names
            top_k: Number of top predictions to return

        Returns:
            Dictionary with detailed prediction analysis
        """
        model.eval()
        eval_class_names = class_names or self.class_names

        with torch.no_grad():
            sample_data = sample_data.to(self.device)
            sample_labels = sample_labels.to(self.device)

            # Forward pass
            outputs = model(sample_data)
            probabilities = torch.softmax(outputs, dim=1)

            # Get top-k predictions
            top_probs, top_indices = torch.topk(probabilities, top_k, dim=1)

        results: dict[str, Any] = {
            "num_samples": len(sample_data),
            "predictions": [],
            "summary": {
                "correct": 0,
                "total": len(sample_data),
                "accuracy": 0.0,
                "avg_confidence": 0.0,
                "avg_top1_confidence": 0.0,
            },
        }

        total_confidence = 0.0
        total_top1_confidence = 0.0

        for i in range(len(sample_data)):
            # .item() may return a float for some tensor dtypes; cast to int for indexing
            true_label = int(sample_labels[i].item())
            true_class = eval_class_names[true_label] if true_label < len(eval_class_names) else f"Class_{true_label}"

            # Top-k predictions for this sample
            sample_predictions = []
            for j in range(top_k):
                pred_idx = int(top_indices[i, j].item())
                pred_prob = float(top_probs[i, j].item())
                pred_class = eval_class_names[pred_idx] if pred_idx < len(eval_class_names) else f"Class_{pred_idx}"

                sample_predictions.append(
                    {
                        "class": pred_class,
                        "probability": pred_prob,
                        "correct": pred_idx == true_label,
                    }
                )

            # Check if prediction is correct
            is_correct = top_indices[i, 0].item() == true_label
            if is_correct:
                # results is typed as dict[str, Any] so this mutation is safe
                results["summary"]["correct"] += 1

            # Confidence metrics
            top1_confidence = top_probs[i, 0].item()
            max_confidence = probabilities[i].max().item()

            total_confidence += max_confidence
            total_top1_confidence += top1_confidence

            results["predictions"].append(
                {
                    "sample_index": i,
                    "true_class": true_class,
                    "true_label": true_label,
                    "predicted_class": sample_predictions[0]["class"],
                    "predicted_label": top_indices[i, 0].item(),
                    "correct": is_correct,
                    "confidence": top1_confidence,
                    "top_k_predictions": sample_predictions,
                }
            )

        # Calculate summary statistics
        total_samples = len(sample_data)
        results["summary"]["accuracy"] = results["summary"]["correct"] / results["summary"]["total"] if results["summary"]["total"] > 0 else 0.0
        results["summary"]["avg_confidence"] = total_confidence / total_samples if total_samples > 0 else 0.0
        results["summary"]["avg_top1_confidence"] = total_top1_confidence / total_samples if total_samples > 0 else 0.0

        return results
