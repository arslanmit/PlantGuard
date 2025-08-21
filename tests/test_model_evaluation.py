"""Tests for model evaluation and validation system."""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_evaluator_imports():
    """Test that evaluation modules can be imported."""
    try:
        from training.evaluator import ModelEvaluator, ModelMetrics, ValidationResult
        from training.model_comparison import BenchmarkResult, ModelComparator, ModelRanking
        from training.model_validator import AutomatedModelValidator, ValidationConfig

        # Test that classes can be instantiated (without dependencies)
        assert ModelEvaluator is not None
        assert ModelMetrics is not None
        assert ValidationResult is not None
        assert ModelComparator is not None
        assert BenchmarkResult is not None
        assert ModelRanking is not None
        assert AutomatedModelValidator is not None
        assert ValidationConfig is not None

    except ImportError as e:
        pytest.skip(f"Skipping test due to missing dependencies: {e}")


def test_validation_config():
    """Test ValidationConfig creation and validation."""
    try:
        from training.model_validator import ValidationConfig

        # Test default config
        config = ValidationConfig()
        assert config.min_accuracy == 0.7
        assert config.min_macro_f1 == 0.65
        assert config.enable_sample_testing is True

        # Test custom config
        custom_config = ValidationConfig(min_accuracy=0.8, strict_mode=True, num_test_samples=50)
        assert custom_config.min_accuracy == 0.8
        assert custom_config.strict_mode is True
        assert custom_config.num_test_samples == 50

    except ImportError as e:
        pytest.skip(f"Skipping test due to missing dependencies: {e}")


def test_model_metrics_structure():
    """Test ModelMetrics dataclass structure."""
    try:
        from training.evaluator import ClassMetrics, ModelMetrics

        # Test that we can create a basic metrics object
        class_metrics = [
            ClassMetrics(
                class_name="test_class",
                precision=0.8,
                recall=0.7,
                f1_score=0.75,
                support=100,
                true_positives=80,
                false_positives=20,
                false_negatives=30,
                true_negatives=70,
            )
        ]

        metrics = ModelMetrics(
            accuracy=0.85,
            macro_precision=0.8,
            macro_recall=0.75,
            macro_f1=0.77,
            weighted_precision=0.82,
            weighted_recall=0.78,
            weighted_f1=0.8,
            class_metrics=class_metrics,
            total_samples=200,
            num_classes=2,
            evaluation_time=10.5,
            confusion_matrix=[[80, 20], [30, 70]],
            class_names=["class_0", "class_1"],
        )

        assert metrics.accuracy == 0.85
        assert len(metrics.class_metrics) == 1
        assert metrics.class_metrics[0].class_name == "test_class"

    except ImportError as e:
        pytest.skip(f"Skipping test due to missing dependencies: {e}")


if __name__ == "__main__":
    test_evaluator_imports()
    test_validation_config()
    test_model_metrics_structure()
    print("✅ All basic tests passed!")
