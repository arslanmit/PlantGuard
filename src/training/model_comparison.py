"""Model comparison utilities for PlantGuard training pipeline.

This module provides benchmarking and comparison functionality for different
models in the PlantGuard training system.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a model benchmark comparison."""

    model_name: str
    accuracy: float
    loss: float
    inference_time: float
    memory_usage: float
    parameters: int

    def to_dict(self) -> dict[str, Any]:
        """Convert benchmark result to dictionary."""
        return {
            "model_name": self.model_name,
            "accuracy": self.accuracy,
            "loss": self.loss,
            "inference_time": self.inference_time,
            "memory_usage": self.memory_usage,
            "parameters": self.parameters,
        }


class ModelComparator:
    """Compare different models based on various metrics."""

    def __init__(self):
        """Initialize the model comparator."""
        self.results: list[BenchmarkResult] = []

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result to the comparison."""
        self.results.append(result)
        logger.info("Added benchmark result for %s", result.model_name)

    def get_best_model(self, metric: str = "accuracy") -> BenchmarkResult | None:
        """Get the best model based on the specified metric."""
        if not self.results:
            return None

        if metric == "accuracy":
            return max(self.results, key=lambda x: x.accuracy)
        elif metric == "inference_time":
            return min(self.results, key=lambda x: x.inference_time)
        elif metric == "memory_usage":
            return min(self.results, key=lambda x: x.memory_usage)
        else:
            logger.warning("Unknown metric: %s", metric)
            return None

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all benchmark results."""
        if not self.results:
            return {"total_models": 0, "results": []}

        return {
            "total_models": len(self.results),
            "results": [result.to_dict() for result in self.results],
            "best_accuracy": self.get_best_model("accuracy"),
            "fastest_inference": self.get_best_model("inference_time"),
            "lowest_memory": self.get_best_model("memory_usage"),
        }


class ModelRanking:
    """Rank models based on multiple criteria."""

    def __init__(self, weights: dict[str, float] | None = None):
        """Initialize model ranking with optional weights.

        Args:
            weights: Dictionary of metric weights for ranking
        """
        self.weights = weights or {
            "accuracy": 0.5,
            "inference_time": 0.3,
            "memory_usage": 0.2,
        }

    def rank_models(self, comparator: ModelComparator) -> list[BenchmarkResult]:
        """Rank models based on weighted criteria."""
        if not comparator.results:
            return []

        def calculate_score(result: BenchmarkResult) -> float:
            """Calculate weighted score for a model."""
            # Normalize metrics (higher is better for accuracy,
            # lower for others)
            accuracy_score = result.accuracy
            # Inverse for lower is better
            inference_score = 1.0 / (1.0 + result.inference_time)
            # Inverse for lower is better
            memory_score = 1.0 / (1.0 + result.memory_usage)

            return (
                self.weights["accuracy"] * accuracy_score
                + self.weights["inference_time"] * inference_score
                + self.weights["memory_usage"] * memory_score
            )

        ranked = sorted(comparator.results, key=calculate_score, reverse=True)
        logger.info("Ranked %d models by composite score", len(ranked))
        return ranked
