"""Tests for vision module."""

from PIL import Image

from src.core.vision import CLASSES, predict_image


def test_classes_defined() -> None:
    """Test that classes are properly defined."""
    assert len(CLASSES) == 4
    assert "healthy" in CLASSES


def test_predict_image() -> None:
    """Test image prediction function."""
    # Create a dummy RGB image
    img = Image.new("RGB", (224, 224), color="green")

    # Test prediction
    result = predict_image(img)

    # Check result structure
    assert isinstance(result, dict)
    assert len(result) == len(CLASSES)

    # Check all classes are present
    for class_name in CLASSES:
        assert class_name in result
        assert isinstance(result[class_name], float)
        assert 0 <= result[class_name] <= 1

    # Check probabilities sum to approximately 1
    total_prob = sum(result.values())
    assert abs(total_prob - 1.0) < 0.01
