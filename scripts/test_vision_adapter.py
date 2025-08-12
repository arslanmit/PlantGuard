"""
Test script for VisionAdapter implementation.

This script tests the VisionAdapter functionality without requiring a trained model.
"""

import logging
import sys
from pathlib import Path

import torch
from PIL import Image

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.models import PlantDiseaseResNet50
from core.vision import VisionAdapter

logger = logging.getLogger(__name__)


def test_model_creation() -> None:
    """Test model creation."""
    logger.info("Testing model creation...")

    model = PlantDiseaseResNet50(num_classes=38, pretrained=False)
    assert model.num_classes == 38

    # Test forward pass with dummy input
    dummy_input = torch.randn(1, 3, 224, 224)
    output = model(dummy_input)
    assert output.shape == (1, 38)

    logger.info("✓ Model creation test passed")


def test_vision_adapter_init() -> None:
    """Test VisionAdapter initialization."""
    logger.info("Testing VisionAdapter initialization...")

    adapter = VisionAdapter(device="cpu")
    assert adapter.device.type == "cpu"
    assert not adapter.is_loaded
    assert len(adapter.class_names) == 0

    logger.info("✓ VisionAdapter initialization test passed")


def test_class_mapping() -> None:
    """Test class mapping functionality."""
    logger.info("Testing class mapping...")

    adapter = VisionAdapter(device="cpu")

    # Test loading class mapping
    mapping_path = Path("data/knowledge_base/plantvillage_classes.json")
    if mapping_path.exists():
        adapter.load_class_mapping(str(mapping_path))
        assert len(adapter.class_names) == 38

        # Test readable name conversion
        test_class = "Apple___Apple_scab"
        readable = adapter.get_readable_name(test_class)
        assert readable == "Apple Scab"

        # Test plant type extraction
        plant_type = adapter.get_plant_type(test_class)
        assert plant_type == "Apple"

        # Test healthy detection
        assert adapter.is_healthy("Apple___healthy")
        assert not adapter.is_healthy("Apple___Apple_scab")

        logger.info("✓ Class mapping test passed")
    else:
        logger.warning("Class mapping file not found, skipping test")


def test_image_preprocessing() -> None:
    """Test image preprocessing."""
    logger.info("Testing image preprocessing...")

    adapter = VisionAdapter(device="cpu")

    # Create dummy image
    dummy_image = Image.new("RGB", (256, 256), color="green")

    # Test preprocessing
    tensor = adapter.preprocess_image(dummy_image)
    assert tensor.shape == (3, 224, 224)
    assert tensor.dtype == torch.float32

    logger.info("✓ Image preprocessing test passed")


def main() -> None:
    """Run all tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting VisionAdapter tests...")

    try:
        test_model_creation()
        test_vision_adapter_init()
        test_class_mapping()
        test_image_preprocessing()

        logger.info("🎉 All tests passed!")

    except Exception:
        logger.exception("Test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
