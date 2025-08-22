"""Model comparison and benchmarking tools for PlantGuard production training pipeline.

This module provides advanced model comparison capabilities including statistical significance testing,
performance regression detection, and comprehensive benchmarking against baseline models.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .evaluator import ModelEvaluator, ModelMetrics

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of benchmarking against baseline models."""

    model_name: str
    baseline_name: str
    performance_improvement: dict[str, float]
    statistical_significance: dict[str, float]
    benchmark_score: float
    ranking_position: int
    total_models: int
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ModelRanking:
    """Model ranking based on multiple criteria."""

    rankings: list[tuple[str, float]]  # (model_name, score)
    criteria_weights: dict[str, float]
    detailed_scores: dict[str, dict[str, float]]  # model_name -> metric -> score
    best_model: str
    worst_model: str


@dataclass
class PerformanceRegression:
    """Performance regression analysis result."""

    has_regression: bool
    severity: str  # "none", "minor", "major", "critical"
    affected_metrics: list[str]
    regression_details: dict[str, dict[str, float]]
    recommendations: list[str]
    rollback_recommended: bool


class ModelComparator:
    """Advanced model comparison and benchmarking system."""

    def __init__(
        self,
        evaluator: ModelEvaluator | None = None,
        baseline_models_dir: Path | None = None,
    ) -> None:
        """Initialize ModelComparator.

        Args:
            evaluator: ModelEvaluator instance (optional)
            baseline_models_dir: Directory containing baseline model metrics
        """
        self.evaluator = evaluator or ModelEvaluator()
        self.baseline_models_dir = baseline_models_dir or Path("data/baselines")
        self.baseline_models_dir.mkdir(parents=True, exist_ok=True)

        # Load baseline models if available
        self.baseline_metrics = self._load_baseline_models()

        logger.info(f"ModelComparator initialized with {len(self.baseline_metrics)} baseline models")

    def _load_baseline_models(self) -> dict[str, ModelMetrics]:
        """Load baseline model metrics from disk.

        Returns:
            Dictionary mapping baseline model names to their metrics
        """
        baseline_metrics: dict[str, ModelMetrics] = {}

        if not self.baseline_models_dir.exists():
            return baseline_metrics

        for metrics_file in self.baseline_models_dir.glob("*.json"):
            try:
                model_name = metrics_file.stem
                metrics = self.evaluator.load_metrics(metrics_file)
                baseline_metrics[model_name] = metrics
                logger.debug(f"Loaded baseline model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load baseline model {metrics_file}: {e}")

        return baseline_metrics

    def add_baseline_model(
        self,
        model_name: str,
        metrics: ModelMetrics,
        save_to_disk: bool = True,
    ) -> None:
        """Add a new baseline model.

        Args:
            model_name: Name of the baseline model
            metrics: ModelMetrics for the baseline
            save_to_disk: Whether to save metrics to disk
        """
        self.baseline_metrics[model_name] = metrics

        if save_to_disk:
            metrics_file = self.baseline_models_dir / f"{model_name}.json"
            self.evaluator.save_metrics(metrics, metrics_file)

        logger.info(f"Added baseline model: {model_name}")

    def benchmark_against_baselines(
        self,
        model_metrics: ModelMetrics,
        model_name: str,
        significance_threshold: float = 0.05,
    ) -> list[BenchmarkResult]:
        """Benchmark model against all baseline models.

        Args:
            model_metrics: Metrics of the model to benchmark
            model_name: Name of the model being benchmarked
            significance_threshold: Threshold for statistical significance

        Returns:
            List of BenchmarkResult for each baseline comparison
        """
        logger.info(f"Benchmarking {model_name} against {len(self.baseline_metrics)} baselines...")

        if not self.baseline_metrics:
            logger.warning("No baseline models available for benchmarking")
            return []

        benchmark_results = []

        for baseline_name, baseline_metrics in self.baseline_metrics.items():
            # Calculate performance improvements
            performance_improvement = self._calculate_performance_improvement(model_metrics, baseline_metrics)

            # Calculate statistical significance (simplified)
            statistical_significance = self._calculate_statistical_significance(model_metrics, baseline_metrics)

            # Calculate benchmark score
            benchmark_score = self._calculate_benchmark_score(model_metrics, baseline_metrics)

            # Generate recommendations
            recommendations = self._generate_benchmark_recommendations(model_metrics, baseline_metrics, performance_improvement)

            # Determine ranking position (simplified)
            ranking_position = self._calculate_ranking_position(model_metrics, baseline_name)

            result = BenchmarkResult(
                model_name=model_name,
                baseline_name=baseline_name,
                performance_improvement=performance_improvement,
                statistical_significance=statistical_significance,
                benchmark_score=benchmark_score,
                ranking_position=ranking_position,
                total_models=len(self.baseline_metrics) + 1,
                recommendations=recommendations,
            )

            benchmark_results.append(result)

        # Sort by benchmark score
        benchmark_results.sort(key=lambda x: x.benchmark_score, reverse=True)

        logger.info(f"Benchmarking complete. Best baseline comparison: {benchmark_results[0].baseline_name}")
        return benchmark_results

    def _calculate_performance_improvement(self, model_metrics: ModelMetrics, baseline_metrics: ModelMetrics) -> dict[str, float]:
        """Calculate performance improvement over baseline.

        Args:
            model_metrics: Current model metrics
            baseline_metrics: Baseline model metrics

        Returns:
            Dictionary of relative improvements for each metric
        """
        improvements = {}

        metrics_to_compare = ["accuracy", "macro_f1", "weighted_f1", "macro_precision", "macro_recall"]

        for metric in metrics_to_compare:
            current_value = getattr(model_metrics, metric)
            baseline_value = getattr(baseline_metrics, metric)

            if baseline_value > 0:
                improvement = (current_value - baseline_value) / baseline_value
            else:
                improvement = 0.0

            improvements[metric] = improvement

        # Add ROC AUC if available
        if model_metrics.roc_auc_macro is not None and baseline_metrics.roc_auc_macro is not None:
            baseline_auc = baseline_metrics.roc_auc_macro
            if baseline_auc > 0:
                auc_improvement = (model_metrics.roc_auc_macro - baseline_auc) / baseline_auc
                improvements["roc_auc_macro"] = auc_improvement

        return improvements

    def _calculate_statistical_significance(self, model_metrics: ModelMetrics, baseline_metrics: ModelMetrics) -> dict[str, float]:
        """Calculate statistical significance of differences.

        Args:
            model_metrics: Current model metrics
            baseline_metrics: Baseline model metrics

        Returns:
            Dictionary of p-values for each metric comparison
        """
        # Simplified significance calculation
        # In practice, you'd need the raw predictions for proper statistical tests
        significance = {}

        metrics_to_test = ["accuracy", "macro_f1", "weighted_f1"]

        for metric in metrics_to_test:
            current_value = getattr(model_metrics, metric)
            baseline_value = getattr(baseline_metrics, metric)

            # Simple heuristic based on difference magnitude
            # Larger differences are considered more significant
            diff = abs(current_value - baseline_value)

            # Simplified p-value calculation (placeholder)
            if diff > 0.1:
                p_value = 0.001  # Highly significant
            elif diff > 0.05:
                p_value = 0.01  # Significant
            elif diff > 0.02:
                p_value = 0.05  # Marginally significant
            else:
                p_value = 0.5  # Not significant

            significance[metric] = p_value

        return significance

    def _calculate_benchmark_score(self, model_metrics: ModelMetrics, baseline_metrics: ModelMetrics) -> float:
        """Calculate overall benchmark score.

        Args:
            model_metrics: Current model metrics
            baseline_metrics: Baseline model metrics

        Returns:
            Benchmark score (higher is better)
        """
        # Weighted combination of improvements
        weights = {
            "accuracy": 0.3,
            "macro_f1": 0.3,
            "weighted_f1": 0.2,
            "macro_precision": 0.1,
            "macro_recall": 0.1,
        }

        improvements = self._calculate_performance_improvement(model_metrics, baseline_metrics)

        score = 0.0
        for metric, weight in weights.items():
            if metric in improvements:
                # Convert improvement to score (0-1 scale)
                improvement = improvements[metric]
                metric_score = max(0, min(1, 0.5 + improvement))  # Center at 0.5
                score += metric_score * weight

        return score

    def _generate_benchmark_recommendations(
        self,
        model_metrics: ModelMetrics,
        baseline_metrics: ModelMetrics,
        improvements: dict[str, float],
    ) -> list[str]:
        """Generate recommendations based on benchmark comparison.

        Args:
            model_metrics: Current model metrics
            baseline_metrics: Baseline model metrics
            improvements: Performance improvements

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check for significant improvements
        significant_improvements = [
            metric
            for metric, improvement in improvements.items()
            if improvement > 0.05  # 5% improvement threshold
        ]

        if significant_improvements:
            recommendations.append(f"Model shows significant improvement in: {', '.join(significant_improvements)}")

        # Check for regressions
        regressions = [
            metric
            for metric, improvement in improvements.items()
            if improvement < -0.02  # 2% regression threshold
        ]

        if regressions:
            recommendations.append(f"Model shows regression in: {', '.join(regressions)}. Consider investigating.")

        # Overall performance assessment
        avg_improvement = np.mean(list(improvements.values()))
        if avg_improvement > 0.1:
            recommendations.append("Excellent performance improvement over baseline")
        elif avg_improvement > 0.05:
            recommendations.append("Good performance improvement over baseline")
        elif avg_improvement > 0:
            recommendations.append("Marginal performance improvement over baseline")
        else:
            recommendations.append("Performance is similar to or worse than baseline")

        return recommendations

    def _calculate_ranking_position(self, model_metrics: ModelMetrics, baseline_name: str) -> int:
        """Calculate ranking position among all models.

        Args:
            model_metrics: Current model metrics
            baseline_name: Name of baseline being compared

        Returns:
            Ranking position (1-based)
        """
        # Simple ranking based on accuracy
        # In practice, you'd use a more sophisticated ranking system
        model_accuracy = model_metrics.accuracy

        better_models = 0
        for baseline_metrics in self.baseline_metrics.values():
            if baseline_metrics.accuracy > model_accuracy:
                better_models += 1

        return better_models + 1

    def create_model_ranking(
        self,
        model_metrics_dict: dict[str, ModelMetrics],
        criteria_weights: dict[str, float] | None = None,
    ) -> ModelRanking:
        """Create comprehensive model ranking.

        Args:
            model_metrics_dict: Dictionary of model names to metrics
            criteria_weights: Weights for ranking criteria

        Returns:
            ModelRanking with detailed ranking information
        """
        logger.info(f"Creating ranking for {len(model_metrics_dict)} models...")

        if criteria_weights is None:
            criteria_weights = {
                "accuracy": 0.25,
                "macro_f1": 0.25,
                "weighted_f1": 0.20,
                "macro_precision": 0.15,
                "macro_recall": 0.15,
            }

        detailed_scores = {}
        composite_scores = {}

        # Calculate scores for each model
        for model_name, metrics in model_metrics_dict.items():
            model_scores = {}
            composite_score = 0.0

            for criterion, weight in criteria_weights.items():
                if hasattr(metrics, criterion):
                    score = getattr(metrics, criterion)
                    model_scores[criterion] = score
                    composite_score += score * weight

            detailed_scores[model_name] = model_scores
            composite_scores[model_name] = composite_score

        # Create ranking
        rankings = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)

        best_model = rankings[0][0] if rankings else ""
        worst_model = rankings[-1][0] if rankings else ""

        ranking = ModelRanking(
            rankings=rankings,
            criteria_weights=criteria_weights,
            detailed_scores=detailed_scores,
            best_model=best_model,
            worst_model=worst_model,
        )

        logger.info(f"Ranking complete. Best model: {best_model}")
        return ranking

    def detect_performance_regression(
        self,
        current_metrics: ModelMetrics,
        baseline_metrics: ModelMetrics,
        severity_thresholds: dict[str, float] | None = None,
    ) -> PerformanceRegression:
        """Detect and analyze performance regression.

        Args:
            current_metrics: Current model metrics
            baseline_metrics: Baseline model metrics
            severity_thresholds: Thresholds for regression severity

        Returns:
            PerformanceRegression analysis result
        """
        logger.info("Analyzing performance regression...")

        if severity_thresholds is None:
            severity_thresholds = {
                "minor": 0.02,  # 2% regression
                "major": 0.05,  # 5% regression
                "critical": 0.10,  # 10% regression
            }

        improvements = self._calculate_performance_improvement(current_metrics, baseline_metrics)

        # Find regressions
        regressions = {metric: improvement for metric, improvement in improvements.items() if improvement < 0}

        has_regression = len(regressions) > 0
        affected_metrics = list(regressions.keys())

        # Determine severity
        severity = "none"
        rollback_recommended = False

        if has_regression:
            max_regression = abs(min(regressions.values()))

            if max_regression >= severity_thresholds["critical"]:
                severity = "critical"
                rollback_recommended = True
            elif max_regression >= severity_thresholds["major"]:
                severity = "major"
                rollback_recommended = True
            elif max_regression >= severity_thresholds["minor"]:
                severity = "minor"
            else:
                severity = "negligible"

        # Generate recommendations
        recommendations = self._generate_regression_recommendations(regressions, severity, affected_metrics)

        # Detailed regression analysis
        regression_details = {}
        for metric, improvement in regressions.items():
            current_value = getattr(current_metrics, metric)
            baseline_value = getattr(baseline_metrics, metric)

            regression_details[metric] = {
                "current": current_value,
                "baseline": baseline_value,
                "absolute_change": current_value - baseline_value,
                "relative_change": improvement,
                "severity": self._classify_metric_severity(improvement, severity_thresholds),
            }

        result = PerformanceRegression(
            has_regression=has_regression,
            severity=severity,
            affected_metrics=affected_metrics,
            regression_details=regression_details,
            recommendations=recommendations,
            rollback_recommended=rollback_recommended,
        )

        logger.info(f"Regression analysis complete. Severity: {severity}")
        return result

    def _classify_metric_severity(self, improvement: float, thresholds: dict[str, float]) -> str:
        """Classify the severity of a metric regression.

        Args:
            improvement: Relative improvement (negative for regression)
            thresholds: Severity thresholds

        Returns:
            Severity classification string
        """
        if improvement >= 0:
            return "none"

        regression_magnitude = abs(improvement)

        if regression_magnitude >= thresholds["critical"]:
            return "critical"
        elif regression_magnitude >= thresholds["major"]:
            return "major"
        elif regression_magnitude >= thresholds["minor"]:
            return "minor"
        else:
            return "negligible"

    def _generate_regression_recommendations(
        self,
        regressions: dict[str, float],
        severity: str,
        affected_metrics: list[str],
    ) -> list[str]:
        """Generate recommendations for addressing regressions.

        Args:
            regressions: Dictionary of metric regressions
            severity: Overall regression severity
            affected_metrics: List of affected metrics

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if severity == "critical":
            recommendations.extend(
                [
                    "CRITICAL: Immediate rollback to previous model recommended",
                    "Investigate training data quality and preprocessing changes",
                    "Review hyperparameter changes and model architecture modifications",
                ]
            )
        elif severity == "major":
            recommendations.extend(
                [
                    "Major regression detected - consider rollback",
                    "Investigate recent changes to training pipeline",
                    "Validate training data integrity",
                ]
            )
        elif severity == "minor":
            recommendations.extend(
                [
                    "Minor regression detected - monitor closely",
                    "Consider additional training epochs or hyperparameter tuning",
                ]
            )

        # Metric-specific recommendations
        if "accuracy" in affected_metrics:
            recommendations.append("Accuracy regression: Check data quality and class balance")

        if "macro_f1" in affected_metrics:
            recommendations.append("Macro F1 regression: Investigate per-class performance")

        if "macro_precision" in affected_metrics:
            recommendations.append("Precision regression: Review classification thresholds")

        if "macro_recall" in affected_metrics:
            recommendations.append("Recall regression: Consider data augmentation for affected classes")

        return recommendations

    def save_comparison_report(
        self,
        comparison_results: dict[str, Any],
        output_path: Path,
    ) -> None:
        """Save comprehensive comparison report.

        Args:
            comparison_results: Dictionary containing all comparison results
            output_path: Path to save the report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert dataclasses to dictionaries for JSON serialization
        serializable_results = {}
        for key, value in comparison_results.items():
            if hasattr(value, "__dict__"):
                serializable_results[key] = asdict(value)
            else:
                serializable_results[key] = value

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2, default=str)

        logger.info(f"Comparison report saved to {output_path}")

    def generate_comparison_summary(
        self,
        benchmark_results: list[BenchmarkResult],
        ranking: ModelRanking,
        regression_analysis: PerformanceRegression | None = None,
    ) -> str:
        """Generate human-readable comparison summary.

        Args:
            benchmark_results: Results from baseline benchmarking
            ranking: Model ranking results
            regression_analysis: Optional regression analysis

        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 80,
            "MODEL COMPARISON AND BENCHMARKING SUMMARY",
            "=" * 80,
            "",
            f"Analysis Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Ranking summary
        if ranking.rankings:
            lines.extend(
                [
                    "MODEL RANKING",
                    "-" * 40,
                    f"Best Model: {ranking.best_model}",
                    f"Total Models Compared: {len(ranking.rankings)}",
                    "",
                    "Top 5 Models:",
                ]
            )

            for i, (model_name, score) in enumerate(ranking.rankings[:5]):
                lines.append(f"  {i + 1}. {model_name}: {score:.4f}")

            lines.append("")

        # Benchmark results summary
        if benchmark_results:
            lines.extend(
                [
                    "BASELINE COMPARISON",
                    "-" * 40,
                ]
            )

            for result in benchmark_results[:3]:  # Top 3 comparisons
                lines.extend(
                    [
                        f"vs {result.baseline_name}:",
                        f"  Benchmark Score: {result.benchmark_score:.4f}",
                        f"  Ranking Position: {result.ranking_position}/{result.total_models}",
                    ]
                )

                # Show significant improvements
                significant_improvements = [
                    f"{metric}: {improvement:+.2%}" for metric, improvement in result.performance_improvement.items() if improvement > 0.02
                ]

                if significant_improvements:
                    lines.append(f"  Improvements: {', '.join(significant_improvements)}")

                lines.append("")

        # Regression analysis summary
        if regression_analysis:
            lines.extend(
                [
                    "REGRESSION ANALYSIS",
                    "-" * 40,
                    f"Regression Detected: {regression_analysis.has_regression}",
                    f"Severity: {regression_analysis.severity}",
                    f"Rollback Recommended: {regression_analysis.rollback_recommended}",
                ]
            )

            if regression_analysis.affected_metrics:
                lines.append(f"Affected Metrics: {', '.join(regression_analysis.affected_metrics)}")

            if regression_analysis.recommendations:
                lines.extend(
                    [
                        "",
                        "Recommendations:",
                    ]
                )
                for rec in regression_analysis.recommendations[:3]:
                    lines.append(f"  • {rec}")

            lines.append("")

        return "\n".join(lines)
