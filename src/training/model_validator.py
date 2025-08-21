"""Automated model validation and testing system for PlantGuard production training pipeline.

This module provides automated model validation, sample image testing, and quality assessment
with configurable performance thresholds and detailed reporting.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from .evaluator import ModelEvaluator, ModelMetrics, ValidationResult
from .model_comparison import ModelComparator

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for automated model validation."""

    # Quality thresholds
    min_accuracy: float = 0.7
    min_macro_f1: float = 0.65
    min_weighted_f1: float = 0.7
    min_macro_precision: float = 0.65
    min_macro_recall: float = 0.65
    max_class_imbalance: float = 0.1

    # Confidence thresholds
    min_avg_confidence: float = 0.6
    min_high_confidence_ratio: float = 0.5  # Ratio of predictions with >0.8 confidence

    # Sample testing
    num_test_samples: int = 100
    confidence_threshold: float = 0.8
    top_k_predictions: int = 3

    # Validation modes
    strict_mode: bool = False  # Stricter thresholds for production
    enable_regression_check: bool = True
    enable_sample_testing: bool = True


@dataclass
class SampleTestResult:
    """Result of sample image testing."""

    sample_path: str
    true_class: str
    predicted_class: str
    confidence: float
    correct: bool
    top_k_predictions: list[dict[str, Any]]
    issues: list[str] = field(default_factory=list)


@dataclass
class AutomatedValidationResult:
    """Result of automated model validation."""

    model_path: str
    validation_passed: bool
    overall_score: float

    # Component results
    metrics_validation: ValidationResult
    sample_test_results: list[SampleTestResult] = field(default_factory=list)
    regression_analysis: dict[str, Any] | None = None

    # Summary statistics
    sample_accuracy: float = 0.0
    avg_confidence: float = 0.0
    high_confidence_ratio: float = 0.0

    # Issues and recommendations
    critical_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Metadata
    validation_time: float = 0.0
    timestamp: str = ""


class SampleDataset(Dataset):
    """Dataset for sample image testing."""

    def __init__(
        self,
        image_paths: list[Path],
        labels: list[int],
        transform: transforms.Compose | None = None,
    ) -> None:
        """Initialize SampleDataset.

        Args:
            image_paths: List of image file paths
            labels: List of corresponding labels
            transform: Optional image transforms
        """
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform or self._get_default_transform()

    def __len__(self) -> int:
        """Get dataset length."""
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        """Get dataset item.

        Args:
            idx: Item index

        Returns:
            Tuple of (image_tensor, label)
        """
        image_path = self.image_paths[idx]
        label = self.labels[idx]

        try:
            image = Image.open(image_path).convert("RGB")
            if self.transform:
                image = self.transform(image)
        except Exception as e:
            logger.warning(f"Failed to load image {image_path}: {e}")
            # Return a dummy image
            image = torch.zeros(3, 224, 224)

        return image, label

    def _get_default_transform(self) -> transforms.Compose:
        """Get default image transforms."""
        return transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )


class AutomatedModelValidator:
    """Automated model validation and testing system."""

    def __init__(
        self,
        config: ValidationConfig | None = None,
        device: torch.device | None = None,
        baseline_models_dir: Path | None = None,
    ) -> None:
        """Initialize AutomatedModelValidator.

        Args:
            config: Validation configuration
            device: Device for model evaluation
            baseline_models_dir: Directory containing baseline models
        """
        self.config = config or ValidationConfig()
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize components
        self.evaluator = ModelEvaluator(device=self.device)
        self.comparator = ModelComparator(
            evaluator=self.evaluator,
            baseline_models_dir=baseline_models_dir,
        )

        logger.info(f"AutomatedModelValidator initialized on device: {self.device}")

    def validate_model(
        self,
        model_path: Path,
        validation_data_loader: DataLoader,
        class_names: list[str] | None = None,
        baseline_model_name: str | None = None,
    ) -> AutomatedValidationResult:
        """Perform comprehensive automated model validation.

        Args:
            model_path: Path to the model file
            validation_data_loader: DataLoader for validation data
            class_names: List of class names
            baseline_model_name: Name of baseline model for comparison

        Returns:
            AutomatedValidationResult with comprehensive validation results
        """
        logger.info(f"Starting automated validation for model: {model_path}")
        start_time = time.time()

        # Load model
        model = self._load_model(model_path)
        if model is None:
            return self._create_failed_result(str(model_path), "Failed to load model", start_time)

        # Get class names
        eval_class_names = class_names or self._extract_class_names(model_path)

        # 1. Evaluate model metrics
        logger.info("Evaluating model metrics...")
        try:
            model_metrics = self.evaluator.evaluate_model(model, validation_data_loader, eval_class_names)
        except Exception as e:
            logger.exception("Failed to evaluate model metrics")
            return self._create_failed_result(str(model_path), f"Metrics evaluation failed: {e}", start_time)

        # 2. Validate metrics against thresholds
        logger.info("Validating metrics against quality thresholds...")
        metrics_validation = self.evaluator.validate_model_quality(model_metrics, self._get_quality_thresholds())
        metrics_validation.model_path = str(model_path)

        # 3. Sample testing (if enabled)
        sample_test_results = []
        sample_accuracy = 0.0
        avg_confidence = 0.0
        high_confidence_ratio = 0.0

        if self.config.enable_sample_testing:
            logger.info("Performing sample image testing...")
            try:
                sample_test_results, sample_stats = self._perform_sample_testing(model, validation_data_loader, eval_class_names)
                sample_accuracy = sample_stats["accuracy"]
                avg_confidence = sample_stats["avg_confidence"]
                high_confidence_ratio = sample_stats["high_confidence_ratio"]
            except Exception as e:
                logger.warning(f"Sample testing failed: {e}")

        # 4. Regression analysis (if enabled and baseline available)
        regression_analysis = None
        if self.config.enable_regression_check and baseline_model_name:
            logger.info("Performing regression analysis...")
            try:
                regression_analysis = self._perform_regression_analysis(model_metrics, baseline_model_name)
            except Exception as e:
                logger.warning(f"Regression analysis failed: {e}")

        # 5. Compile results and determine overall validation status
        validation_time = time.time() - start_time

        result = self._compile_validation_result(
            model_path=str(model_path),
            metrics_validation=metrics_validation,
            sample_test_results=sample_test_results,
            regression_analysis=regression_analysis,
            sample_accuracy=sample_accuracy,
            avg_confidence=avg_confidence,
            high_confidence_ratio=high_confidence_ratio,
            validation_time=validation_time,
        )

        logger.info(f"Automated validation complete. Passed: {result.validation_passed}")
        logger.info(f"Overall score: {result.overall_score:.3f}")

        return result

    def _load_model(self, model_path: Path) -> nn.Module | None:
        """Load PyTorch model from file.

        Args:
            model_path: Path to model file

        Returns:
            Loaded model or None if failed
        """
        try:
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return None

            # Load checkpoint
            try:
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
            except TypeError:
                # Fallback for older PyTorch versions or legacy models.
                # nosec B614: weights_only=False is required for legacy checkpoints; path is controlled (local file).
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)  # nosec B614

            # Extract model architecture info
            if isinstance(checkpoint, dict) and "config" in checkpoint:
                config = checkpoint["config"]
                num_classes = config.get("num_classes", 38)
                architecture = config.get("model_architecture", "resnet50")
            else:
                # Fallback defaults
                num_classes = 38
                architecture = "resnet50"

            # Create model
            model = self._create_model(architecture, num_classes)

            # Load state dict
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                model.load_state_dict(checkpoint["model_state_dict"])
            else:
                model.load_state_dict(checkpoint)

            model = model.to(self.device)
            model.eval()

            logger.info(f"Successfully loaded model: {architecture} with {num_classes} classes")
            return model

        except Exception as e:
            logger.exception(f"Failed to load model from {model_path}: {e}")
            return None

    def _create_model(self, architecture: str, num_classes: int) -> nn.Module:
        """Create model based on architecture.

        Args:
            architecture: Model architecture name
            num_classes: Number of output classes

        Returns:
            Created model
        """
        from torchvision import models

        if architecture == "resnet50":
            model = models.resnet50(pretrained=False)
            model.fc = nn.Linear(model.fc.in_features, num_classes)
        elif architecture == "resnet18":
            model = models.resnet18(pretrained=False)
            model.fc = nn.Linear(model.fc.in_features, num_classes)
        else:
            raise ValueError(f"Unsupported architecture: {architecture}")

        return model

    def _extract_class_names(self, model_path: Path) -> list[str]:
        """Extract class names from model directory or use defaults.

        Args:
            model_path: Path to model file

        Returns:
            List of class names
        """
        # Try to find class_to_idx.json in the same directory
        model_dir = model_path.parent
        class_file = model_dir / "class_to_idx.json"

        if class_file.exists():
            try:
                with class_file.open("r") as f:
                    class_to_idx = json.load(f)
                # Sort by index to get correct order
                class_names = [name for name, _ in sorted(class_to_idx.items(), key=lambda x: x[1])]
                return class_names
            except Exception as e:
                logger.warning(f"Failed to load class names from {class_file}: {e}")

        # Fallback to default PlantVillage classes
        return self._get_default_class_names()

    def _get_default_class_names(self) -> list[str]:
        """Get default PlantVillage class names.

        Returns:
            List of default class names
        """
        # Load from knowledge base if available
        knowledge_base_file = Path("data/knowledge_base/plantvillage_classes.json")
        if knowledge_base_file.exists():
            try:
                with knowledge_base_file.open("r") as f:
                    data = json.load(f)
                return list(data.keys())
            except Exception as e:
                logger.warning(f"Failed to load default class names: {e}")

        # Ultimate fallback
        return [f"Class_{i}" for i in range(38)]

    def _get_quality_thresholds(self) -> dict[str, float]:
        """Get quality thresholds based on configuration.

        Returns:
            Dictionary of quality thresholds
        """
        thresholds = {
            "min_accuracy": self.config.min_accuracy,
            "min_macro_f1": self.config.min_macro_f1,
            "min_weighted_f1": self.config.min_weighted_f1,
            "min_macro_precision": self.config.min_macro_precision,
            "min_macro_recall": self.config.min_macro_recall,
            "max_class_imbalance": self.config.max_class_imbalance,
        }

        # Apply stricter thresholds in strict mode
        if self.config.strict_mode:
            for key in thresholds:
                if key.startswith("min_"):
                    thresholds[key] += 0.05  # Increase minimum thresholds by 5%
                elif key.startswith("max_"):
                    thresholds[key] -= 0.02  # Decrease maximum thresholds by 2%

        return thresholds

    def _perform_sample_testing(
        self,
        model: nn.Module,
        data_loader: DataLoader,
        class_names: list[str],
    ) -> tuple[list[SampleTestResult], dict[str, float]]:
        """Perform sample image testing with detailed analysis.

        Args:
            model: Model to test
            data_loader: DataLoader for test data
            class_names: List of class names

        Returns:
            Tuple of (sample_results, summary_statistics)
        """
        model.eval()
        sample_results = []

        # Collect samples
        samples_collected = 0
        all_data = []
        all_labels = []

        with torch.no_grad():
            for batch_data, batch_labels in data_loader:
                batch_size = batch_data.size(0)
                if samples_collected + batch_size > self.config.num_test_samples:
                    # Take only what we need
                    needed = self.config.num_test_samples - samples_collected
                    batch_data = batch_data[:needed]
                    batch_labels = batch_labels[:needed]

                all_data.append(batch_data)
                all_labels.append(batch_labels)
                samples_collected += batch_data.size(0)

                if samples_collected >= self.config.num_test_samples:
                    break

        if not all_data:
            return [], {"accuracy": 0.0, "avg_confidence": 0.0, "high_confidence_ratio": 0.0}

        # Concatenate all samples
        test_data = torch.cat(all_data, dim=0).to(self.device)
        test_labels = torch.cat(all_labels, dim=0).to(self.device)

        # Get predictions
        outputs = model(test_data)
        probabilities = torch.softmax(outputs, dim=1)
        top_probs, top_indices = torch.topk(probabilities, self.config.top_k_predictions, dim=1)

        # Analyze each sample
        correct_predictions = 0
        total_confidence = 0.0
        high_confidence_count = 0

        for i in range(len(test_data)):
            true_label = test_labels[i].item()
            true_class = class_names[true_label] if true_label < len(class_names) else f"Class_{true_label}"

            predicted_label = top_indices[i, 0].item()
            predicted_class = class_names[predicted_label] if predicted_label < len(class_names) else f"Class_{predicted_label}"

            confidence = top_probs[i, 0].item()
            is_correct = predicted_label == true_label

            if is_correct:
                correct_predictions += 1

            total_confidence += confidence
            if confidence >= self.config.confidence_threshold:
                high_confidence_count += 1

            # Create top-k predictions
            top_k_preds = []
            for j in range(self.config.top_k_predictions):
                pred_idx = top_indices[i, j].item()
                pred_prob = top_probs[i, j].item()
                pred_class = class_names[pred_idx] if pred_idx < len(class_names) else f"Class_{pred_idx}"

                top_k_preds.append(
                    {
                        "class": pred_class,
                        "probability": pred_prob,
                        "correct": pred_idx == true_label,
                    }
                )

            # Identify issues
            issues = []
            if not is_correct:
                issues.append("Incorrect prediction")
            if confidence < self.config.min_avg_confidence:
                issues.append("Low confidence prediction")

            sample_result = SampleTestResult(
                sample_path=f"sample_{i}",  # Placeholder path
                true_class=true_class,
                predicted_class=predicted_class,
                confidence=confidence,
                correct=is_correct,
                top_k_predictions=top_k_preds,
                issues=issues,
            )

            sample_results.append(sample_result)

        # Calculate summary statistics
        sample_accuracy = correct_predictions / len(test_data)
        avg_confidence = total_confidence / len(test_data)
        high_confidence_ratio = high_confidence_count / len(test_data)

        summary_stats = {
            "accuracy": sample_accuracy,
            "avg_confidence": avg_confidence,
            "high_confidence_ratio": high_confidence_ratio,
        }

        return sample_results, summary_stats

    def _perform_regression_analysis(self, model_metrics: ModelMetrics, baseline_model_name: str) -> dict[str, Any]:
        """Perform regression analysis against baseline.

        Args:
            model_metrics: Current model metrics
            baseline_model_name: Name of baseline model

        Returns:
            Regression analysis results
        """
        if baseline_model_name not in self.comparator.baseline_metrics:
            logger.warning(f"Baseline model {baseline_model_name} not found")
            return {"error": f"Baseline model {baseline_model_name} not found"}

        baseline_metrics = self.comparator.baseline_metrics[baseline_model_name]

        regression_result = self.comparator.detect_performance_regression(model_metrics, baseline_metrics)

        return asdict(regression_result)

    def _compile_validation_result(
        self,
        model_path: str,
        metrics_validation: ValidationResult,
        sample_test_results: list[SampleTestResult],
        regression_analysis: dict[str, Any] | None,
        sample_accuracy: float,
        avg_confidence: float,
        high_confidence_ratio: float,
        validation_time: float,
    ) -> AutomatedValidationResult:
        """Compile comprehensive validation result.

        Args:
            model_path: Path to the model
            metrics_validation: Metrics validation result
            sample_test_results: Sample testing results
            regression_analysis: Regression analysis results
            sample_accuracy: Sample testing accuracy
            avg_confidence: Average prediction confidence
            high_confidence_ratio: Ratio of high-confidence predictions
            validation_time: Total validation time

        Returns:
            Compiled AutomatedValidationResult
        """
        critical_issues = []
        warnings = []
        recommendations = []

        # Check metrics validation
        metrics_passed = metrics_validation.validation_passed
        if not metrics_passed:
            critical_issues.extend(metrics_validation.issues)
            recommendations.extend(metrics_validation.recommendations)

        # Check sample testing results
        sample_passed = True
        if sample_test_results:
            if sample_accuracy < self.config.min_accuracy:
                sample_passed = False
                critical_issues.append(f"Sample accuracy ({sample_accuracy:.3f}) below threshold")

            if avg_confidence < self.config.min_avg_confidence:
                sample_passed = False
                warnings.append(f"Average confidence ({avg_confidence:.3f}) below threshold")

            if high_confidence_ratio < self.config.min_high_confidence_ratio:
                warnings.append(f"Low high-confidence ratio ({high_confidence_ratio:.3f})")

        # Check regression analysis
        regression_passed = True
        if regression_analysis and not regression_analysis.get("error"):
            if regression_analysis.get("has_regression", False):
                severity = regression_analysis.get("severity", "unknown")
                if severity in ["major", "critical"]:
                    regression_passed = False
                    critical_issues.append(f"Performance regression detected: {severity}")
                else:
                    warnings.append("Minor performance regression detected")

                if regression_analysis.get("rollback_recommended", False):
                    critical_issues.append("Model rollback recommended due to regression")

                recommendations.extend(regression_analysis.get("recommendations", []))

        # Determine overall validation status
        overall_passed = metrics_passed and sample_passed and regression_passed

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            metrics_validation.quality_score,
            sample_accuracy,
            avg_confidence,
            regression_analysis,
        )

        return AutomatedValidationResult(
            model_path=model_path,
            validation_passed=overall_passed,
            overall_score=overall_score,
            metrics_validation=metrics_validation,
            sample_test_results=sample_test_results,
            regression_analysis=regression_analysis,
            sample_accuracy=sample_accuracy,
            avg_confidence=avg_confidence,
            high_confidence_ratio=high_confidence_ratio,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations,
            validation_time=validation_time,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def _calculate_overall_score(
        self,
        metrics_score: float,
        sample_accuracy: float,
        avg_confidence: float,
        regression_analysis: dict[str, Any] | None,
    ) -> float:
        """Calculate overall validation score.

        Args:
            metrics_score: Quality score from metrics validation
            sample_accuracy: Sample testing accuracy
            avg_confidence: Average prediction confidence
            regression_analysis: Regression analysis results

        Returns:
            Overall score between 0 and 1
        """
        # Base score from metrics
        score = metrics_score * 0.5

        # Add sample testing score
        if sample_accuracy > 0:
            score += sample_accuracy * 0.3

        # Add confidence score
        if avg_confidence > 0:
            confidence_score = min(1.0, avg_confidence / self.config.min_avg_confidence)
            score += confidence_score * 0.1

        # Regression penalty
        if regression_analysis and not regression_analysis.get("error"):
            if regression_analysis.get("has_regression", False):
                severity = regression_analysis.get("severity", "none")
                if severity == "critical":
                    score *= 0.5  # 50% penalty
                elif severity == "major":
                    score *= 0.7  # 30% penalty
                elif severity == "minor":
                    score *= 0.9  # 10% penalty

        # Remaining weight for overall quality
        score += 0.1  # Base quality bonus

        return max(0.0, min(1.0, score))

    def _create_failed_result(self, model_path: str, error_message: str, start_time: float) -> AutomatedValidationResult:
        """Create a failed validation result.

        Args:
            model_path: Path to the model
            error_message: Error message
            start_time: Validation start time

        Returns:
            Failed AutomatedValidationResult
        """
        validation_time = time.time() - start_time

        # Create dummy metrics validation
        from .evaluator import ModelMetrics

        dummy_metrics = ModelMetrics(
            accuracy=0.0,
            macro_precision=0.0,
            macro_recall=0.0,
            macro_f1=0.0,
            weighted_precision=0.0,
            weighted_recall=0.0,
            weighted_f1=0.0,
            class_metrics=[],
            total_samples=0,
            num_classes=0,
            evaluation_time=0.0,
            confusion_matrix=[],
            class_names=[],
        )

        metrics_validation = ValidationResult(
            model_path=model_path,
            validation_passed=False,
            metrics=dummy_metrics,
            quality_score=0.0,
            issues=[error_message],
            recommendations=["Fix model loading issues before validation"],
        )

        return AutomatedValidationResult(
            model_path=model_path,
            validation_passed=False,
            overall_score=0.0,
            metrics_validation=metrics_validation,
            critical_issues=[error_message],
            validation_time=validation_time,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def save_validation_report(self, result: AutomatedValidationResult, output_path: Path) -> None:
        """Save comprehensive validation report.

        Args:
            result: Validation result to save
            output_path: Path to save the report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary for JSON serialization
        result_dict = asdict(result)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, default=str)

        logger.info(f"Validation report saved to {output_path}")

    def generate_validation_summary(self, result: AutomatedValidationResult) -> str:
        """Generate human-readable validation summary.

        Args:
            result: Validation result

        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 80,
            "AUTOMATED MODEL VALIDATION REPORT",
            "=" * 80,
            "",
            f"Model: {result.model_path}",
            f"Validation Date: {result.timestamp}",
            f"Validation Time: {result.validation_time:.2f} seconds",
            "",
            f"OVERALL RESULT: {'PASSED' if result.validation_passed else 'FAILED'}",
            f"Overall Score: {result.overall_score:.3f}/1.000",
            "",
        ]

        # Metrics summary
        lines.extend(
            [
                "METRICS VALIDATION",
                "-" * 40,
                f"Accuracy: {result.metrics_validation.metrics.accuracy:.4f}",
                f"Macro F1: {result.metrics_validation.metrics.macro_f1:.4f}",
                f"Quality Score: {result.metrics_validation.quality_score:.3f}",
                f"Passed: {'Yes' if result.metrics_validation.validation_passed else 'No'}",
                "",
            ]
        )

        # Sample testing summary
        if result.sample_test_results:
            lines.extend(
                [
                    "SAMPLE TESTING",
                    "-" * 40,
                    f"Samples Tested: {len(result.sample_test_results)}",
                    f"Sample Accuracy: {result.sample_accuracy:.4f}",
                    f"Average Confidence: {result.avg_confidence:.4f}",
                    f"High Confidence Ratio: {result.high_confidence_ratio:.4f}",
                    "",
                ]
            )

        # Regression analysis
        if result.regression_analysis and not result.regression_analysis.get("error"):
            lines.extend(
                [
                    "REGRESSION ANALYSIS",
                    "-" * 40,
                    f"Regression Detected: {result.regression_analysis.get('has_regression', False)}",
                    f"Severity: {result.regression_analysis.get('severity', 'N/A')}",
                    f"Rollback Recommended: {result.regression_analysis.get('rollback_recommended', False)}",
                    "",
                ]
            )

        # Issues and recommendations
        if result.critical_issues:
            lines.extend(
                [
                    "CRITICAL ISSUES",
                    "-" * 40,
                ]
            )
            for issue in result.critical_issues:
                lines.append(f"• {issue}")
            lines.append("")

        if result.warnings:
            lines.extend(
                [
                    "WARNINGS",
                    "-" * 40,
                ]
            )
            for warning in result.warnings:
                lines.append(f"• {warning}")
            lines.append("")

        if result.recommendations:
            lines.extend(
                [
                    "RECOMMENDATIONS",
                    "-" * 40,
                ]
            )
            for rec in result.recommendations:
                lines.append(f"• {rec}")
            lines.append("")

        return "\n".join(lines)
