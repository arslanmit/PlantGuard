#!/usr/bin/env python3
"""Test model switching functionality with registry-managed models.

This script tests the integration between the model registry, VisionAdapter,
and model switching functionality to ensure models can be loaded and switched correctly.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict

import torch
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_test_model(model_path: Path, num_classes: int = 38, model_name: str = "test_model") -> None:
    """Create a test model checkpoint."""
    # Create a simple ResNet50-like state dict structure
    state_dict = {
        "conv1.weight": torch.randn(64, 3, 7, 7),
        "bn1.weight": torch.randn(64),
        "bn1.bias": torch.randn(64),
        "fc.weight": torch.randn(num_classes, 2048),
        "fc.bias": torch.randn(num_classes),
    }

    checkpoint = {
        "model_state_dict": state_dict,
        "num_classes": num_classes,
        "class_names": [f"class_{i}" for i in range(num_classes)],
        "model_version": "1.0.0",
        "training_metadata": {"training_date": "2024-08-17", "dataset": "test_dataset", "accuracy": 0.95, "model_name": model_name},
    }

    torch.save(checkpoint, model_path)
    logger.info(f"Created test model: {model_path}")


def test_model_switching_integration() -> bool:
    """Test complete model switching integration."""
    logger.info("Testing model switching integration...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # 1. Create test models in registry
            from src.training.model_registry import ModelRegistry

            registry = ModelRegistry(temp_path / "models")

            # Create multiple test models
            model_paths = []
            model_ids = []

            for i, model_name in enumerate(["plantguard_base", "plantguard_improved"]):
                model_path = temp_path / f"{model_name}.pt"
                create_test_model(model_path, num_classes=38, model_name=model_name)
                model_paths.append(model_path)

                # Register in registry
                model_id = registry.register_model(
                    model_path=model_path,
                    name=model_name,
                    architecture="resnet50",
                    dataset_version="plantvillage_v1.0",
                    hyperparameters={"num_classes": 38, "epochs": 50 + i * 25},
                    performance_metrics={"accuracy": 0.90 + i * 0.05, "f1_score": 0.88 + i * 0.04},
                    description=f"Test model {i + 1} for switching integration",
                    tags=["test", "integration", f"model_{i + 1}"],
                )
                model_ids.append(model_id)
                logger.info(f"Registered model: {model_id}")

            # 2. Test VisionAdapter can load from registry
            from src.core.vision import VisionAdapter

            adapter = VisionAdapter()

            # Test loading first model
            try:
                adapter.load_from_registry(model_ids[0])
                logger.info(f"✅ Successfully loaded model from registry: {model_ids[0]}")

                # Verify model properties
                if not adapter.is_loaded:
                    logger.error("❌ Model not marked as loaded")
                    return False

                if len(adapter.class_names) != 38:
                    logger.error(f"❌ Expected 38 classes, got {len(adapter.class_names)}")
                    return False

            except Exception as e:
                logger.error(f"❌ Failed to load model from registry: {e}")
                return False

            # 3. Test model switching
            try:
                # Switch to second model
                adapter.load_from_registry(model_ids[1])
                logger.info(f"✅ Successfully switched to model: {model_ids[1]}")

                # Verify switch worked
                if not adapter.is_loaded:
                    logger.error("❌ Model not loaded after switch")
                    return False

            except Exception as e:
                logger.error(f"❌ Failed to switch models: {e}")
                return False

            # 4. Test model manager integration
            from src.features.model_switching.model_manager import PlantGuardModelManager

            # Create model manager config with registry models
            config_path = temp_path / "models.json"
            config_data = {
                "default_model": "registry_model_1",
                "models": {
                    "registry_model_1": {
                        "name": "Registry Model 1",
                        "type": "local",
                        "model_id": f"registry:{model_ids[0]}",
                        "description": "First test model from registry",
                        "accuracy": 0.90,
                        "confidence_threshold": 0.7,
                        "enabled": True,
                        "device": "cpu",
                    },
                    "registry_model_2": {
                        "name": "Registry Model 2",
                        "type": "local",
                        "model_id": f"registry:{model_ids[1]}",
                        "description": "Second test model from registry",
                        "accuracy": 0.95,
                        "confidence_threshold": 0.7,
                        "enabled": True,
                        "device": "cpu",
                    },
                },
            }

            with config_path.open("w") as f:
                json.dump(config_data, f)

            # Initialize model manager
            manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

            # Test listing models
            models = manager.list_available_models()
            if len(models) != 2:
                logger.error(f"❌ Expected 2 models in manager, got {len(models)}")
                return False

            logger.info(f"✅ Model manager loaded {len(models)} registry models")

            # 5. Test prediction with registry models
            test_image = Image.new("RGB", (224, 224), color="green")

            # Mock the actual model prediction since we have dummy weights
            from unittest.mock import patch

            with patch.object(adapter, "predict") as mock_predict:
                mock_predict.return_value = ("test_class", 0.95)

                # Test prediction
                predicted_class, confidence = adapter.predict(test_image)

                if predicted_class != "test_class" or confidence != 0.95:
                    logger.error("❌ Prediction test failed")
                    return False

                logger.info("✅ Prediction test successful")

            # 6. Test model comparison
            comparison = registry.compare_models(model_ids)

            if len(comparison.models) != 2:
                logger.error(f"❌ Expected 2 models in comparison, got {len(comparison.models)}")
                return False

            # Get best model by accuracy
            best_model = comparison.get_best_model("accuracy")
            if best_model.metadata.model_id != model_ids[1]:  # Second model has higher accuracy
                logger.error("❌ Best model selection failed")
                return False

            logger.info("✅ Model comparison successful")

            # 7. Test backward compatibility
            legacy_path = temp_path / "legacy_model.pt"
            legacy_checkpoint = {
                "model_state_dict": {
                    "conv1.weight": torch.randn(64, 3, 7, 7),
                    "fc.weight": torch.randn(38, 2048),
                    "fc.bias": torch.randn(38),
                },
                "num_classes": 38,
                "class_names": [f"class_{i}" for i in range(38)],
                # No registry metadata
            }
            torch.save(legacy_checkpoint, legacy_path)

            # Test compatibility detection
            is_compatible = adapter.is_compatible_with_registry_format(str(legacy_path))
            if is_compatible:
                logger.error("❌ Legacy model incorrectly detected as registry format")
                return False

            # Test migration
            migrated_path = temp_path / "migrated_model.pt"
            adapter.migrate_legacy_model(str(legacy_path), str(migrated_path))

            # Verify migration
            is_migrated_compatible = adapter.is_compatible_with_registry_format(str(migrated_path))
            if not is_migrated_compatible:
                logger.error("❌ Model migration failed")
                return False

            logger.info("✅ Backward compatibility test successful")

            logger.info("🎉 All model switching integration tests passed!")
            return True

        except Exception as e:
            logger.error(f"❌ Model switching integration test failed: {e}")
            return False


def main() -> int:
    """Main test function."""
    logger.info("🚀 Starting model switching integration tests...")

    try:
        success = test_model_switching_integration()

        if success:
            logger.info("✅ Model switching integration tests completed successfully!")
            return 0
        else:
            logger.error("❌ Model switching integration tests failed!")
            return 1

    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Tests failed with unexpected error: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
