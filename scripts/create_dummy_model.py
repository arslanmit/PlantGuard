#!/usr/bin/env python3
"""Create a dummy model checkpoint for PlantGuard development.

This script creates a mock trained model checkpoint that can be used
for testing the application without requiring actual training.
"""


from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import json
import logging
import sys
from pathlib import Path

import torch

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import PlantDiseaseResNet50

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dummy_model() -> None:
    """Create a dummy model checkpoint for development."""
    # Load class information
    classes_path = Path("data/knowledge_base/plantvillage_classes.json")

    if not classes_path.exists():
        logger.error("Classes file not found: %s", classes_path)
        return

    with classes_path.open() as f:
        class_data = json.load(f)

    class_names = class_data["classes"]
    num_classes = len(class_names)

    logger.info("Creating dummy model with %d classes", num_classes)

    # Create model
    model = PlantDiseaseResNet50(num_classes=num_classes, pretrained=True)

    # Create checkpoint data
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "num_classes": num_classes,
        "class_names": class_names,
        "epoch": 50,
        "train_loss": 0.1234,
        "val_loss": 0.2345,
        "val_accuracy": 0.8765,
        "model_info": {
            "architecture": "ResNet50",
            "dataset": "PlantVillage",
            "training_date": "2024-01-01",
            "notes": "Dummy model for development",
        },
    }

    # Ensure models directory exists
    models_dir = Path("data/models")
    models_dir.mkdir(exist_ok=True)

    # Save checkpoint
    checkpoint_path = models_dir / "vision_resnet50.pt"
    torch.save(checkpoint, checkpoint_path)

    logger.info("Dummy model saved to: %s", checkpoint_path)
    logger.info("Model size: %.2f MB", checkpoint_path.stat().st_size / (1024 * 1024))


if __name__ == "__main__":
    create_dummy_model()
