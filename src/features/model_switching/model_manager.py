"""Model Manager for PlantGuard - Easy model switching and configuration.

This module provides a unified interface to switch between different plant disease
detection models easily through configuration.
"""

import json
import logging
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import torch
from PIL import Image

logger = logging.getLogger(__name__)


@runtime_checkable
class VisionAdapterProtocol(Protocol):
    """Protocol for vision adapters compatible with the model manager."""

    def predict(self, image: Image.Image) -> tuple[str, float]:
        """Return (predicted_class, confidence) for the given image."""
        ...

    def get_class_names(self) -> list[str]:
        """Return a copy of the class names supported by the model."""
        ...


class ModelConfig:
    """Configuration for a plant disease model."""

    def __init__(self, config_dict: dict[str, Any]):
        self.name = config_dict["name"]
        self.type = config_dict["type"]  # "huggingface", "local", "custom"
        self.model_id = config_dict["model_id"]
        self.description = config_dict.get("description", "")
        self.accuracy = config_dict.get("accuracy", 0.0)
        self.confidence_threshold = config_dict.get("confidence_threshold", 0.5)
        self.enabled = config_dict.get("enabled", True)
        self.device_preference = config_dict.get("device", "auto")
        self.preprocessing = config_dict.get("preprocessing", {})


class PlantGuardModelManager:
    """Unified model manager for easy switching between different models."""

    def __init__(self, config_path: str = "config/models.json", autoload_default: bool = True):
        """Initialize the model manager.

        Args:
            config_path: Path to model configuration file
            autoload_default: If True, automatically load the default model from config
        """
        self.config_path = Path(config_path)
        self.models_config: dict[str, ModelConfig] = {}
        self.current_model: ModelConfig | None = None
        self.current_adapter: VisionAdapterProtocol | None = None
        self.device = self._get_device()
        self.autoload_default = autoload_default

        # Load model configurations
        self.load_model_configs()

        logger.info("ModelManager initialized with %d available models", len(self.models_config))

    def _get_device(self) -> torch.device:
        """Get the best available device."""
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")

    def load_model_configs(self) -> None:
        """Load model configurations from JSON file."""
        if not self.config_path.exists():
            logger.warning("Config file not found, creating default: %s", self.config_path)
            self.create_default_config()

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config_data = json.load(f)

            self.models_config = {}
            for model_id, model_data in config_data["models"].items():
                self.models_config[model_id] = ModelConfig(model_data)

            # Set default model if specified and autoloading enabled
            default_model = config_data.get("default_model")
            if self.autoload_default and default_model and default_model in self.models_config:
                self.load_model(default_model)

            logger.info("Loaded %d model configurations", len(self.models_config))

        except Exception as e:
            logger.error("Failed to load model configs: %s", e)
            self.create_default_config()

    def create_default_config(self) -> None:
        """Create default model configuration file."""
        default_config = {
            "default_model": "vit_best",
            "models": {
                "vit_best": {
                    "name": "Vision Transformer (Best Performance)",
                    "type": "huggingface",
                    "model_id": "Abhiram4/PlantDiseaseDetectorVit2",
                    "description": "Vision Transformer model with 100% accuracy on test set",
                    "accuracy": 1.0,
                    "confidence_threshold": 0.7,
                    "enabled": True,
                    "device": "auto",
                },
                "mobilenet_fast": {
                    "name": "MobileNet (Fast & Lightweight)",
                    "type": "huggingface",
                    "model_id": "Diginsa/Plant-Disease-Detection-Project",
                    "description": "Lightweight MobileNet model, good for mobile/edge devices",
                    "accuracy": 0.95,
                    "confidence_threshold": 0.6,
                    "enabled": True,
                    "device": "auto",
                },
                "local_resnet": {
                    "name": "Local ResNet50",
                    "type": "local",
                    "model_id": "data/models/vision_resnet50.pt",
                    "description": "Local ResNet50 model (requires training)",
                    "accuracy": 0.05,
                    "confidence_threshold": 0.5,
                    "enabled": False,
                    "device": "auto",
                },
            },
        }

        # Create config directory
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save default config
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

        logger.info("Created default model config: %s", self.config_path)

        # Load the default config
        self.load_model_configs()

    def list_available_models(self) -> list[dict[str, Any]]:
        """List all available models with their details."""
        models = []
        for model_id, config in self.models_config.items():
            models.append(
                {
                    "id": model_id,
                    "name": config.name,
                    "type": config.type,
                    "model_id": config.model_id,
                    "description": config.description,
                    "accuracy": config.accuracy,
                    "enabled": config.enabled,
                    "is_current": model_id
                    == (self.current_model.name if self.current_model else None),
                }
            )
        return models

    def load_model(self, model_id: str) -> bool:
        """Load a specific model by ID.

        Args:
            model_id: Model identifier from config

        Returns:
            True if model loaded successfully, False otherwise
        """
        if model_id not in self.models_config:
            logger.error("Model ID not found: %s", model_id)
            return False

        config = self.models_config[model_id]

        if not config.enabled:
            logger.warning("Model is disabled: %s", model_id)
            return False

        try:
            logger.info("Loading model: %s (%s)", config.name, config.type)

            if config.type == "huggingface":
                self.current_adapter = self._load_huggingface_model(config)
            elif config.type == "local":
                self.current_adapter = self._load_local_model(config)
            else:
                logger.error("Unsupported model type: %s", config.type)
                return False

            self.current_model = config
            logger.info("Successfully loaded model: %s", config.name)
            return True

        except Exception as e:
            logger.error("Failed to load model %s: %s", model_id, e)
            return False

    def _load_huggingface_model(self, config: ModelConfig):
        """Load a Hugging Face model."""
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        class HuggingFaceAdapter:
            def __init__(self, model_id: str, device: torch.device):
                self.model_id = model_id
                self.device = device
                self.processor = AutoImageProcessor.from_pretrained(model_id)
                self.model = AutoModelForImageClassification.from_pretrained(model_id)
                self.model.to(device)
                self.model.eval()

                # Extract class names
                if hasattr(self.model.config, "id2label"):
                    self.class_names = [
                        self.model.config.id2label[i] for i in range(self.model.config.num_labels)
                    ]
                else:
                    self.class_names = [f"class_{i}" for i in range(self.model.config.num_labels)]

            def predict(self, image: Image.Image) -> tuple[str, float]:
                if image.mode != "RGB":
                    image = image.convert("RGB")

                inputs = self.processor(image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    predicted_class_id: int = int(predictions.argmax().item())
                    confidence: float = float(predictions.max().item())

                return self.class_names[predicted_class_id], confidence

            def get_class_names(self) -> list[str]:
                return self.class_names.copy()

        device_str = (
            config.device_preference if config.device_preference != "auto" else str(self.device)
        )
        device = torch.device(device_str)

        return HuggingFaceAdapter(config.model_id, device)

    def _load_local_model(self, config: ModelConfig):
        """Load a local PyTorch model."""
        # Import your existing VisionAdapter
        import sys
        from pathlib import Path

        # Ensure project root is on sys.path to import the src package
        sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
        from src.core.vision import VisionAdapter

        device_str = (
            config.device_preference if config.device_preference != "auto" else str(self.device)
        )
        adapter = VisionAdapter(device=device_str)
        adapter.load_checkpoint(config.model_id)
        return adapter

    def predict(self, image: Image.Image) -> tuple[str, float, dict[str, Any]]:
        """Predict using the current model.

        Args:
            image: PIL Image to classify

        Returns:
            Tuple of (predicted_class, confidence, metadata)
        """
        if not self.current_adapter or not self.current_model:
            raise RuntimeError("No model loaded. Call load_model() first.")

        predicted_class, confidence = self.current_adapter.predict(image)

        # Add metadata
        metadata = {
            "model_name": self.current_model.name,
            "model_type": self.current_model.type,
            "model_id": self.current_model.model_id,
            "confidence_threshold": self.current_model.confidence_threshold,
            "above_threshold": confidence >= self.current_model.confidence_threshold,
            "device": str(self.device),
        }

        return predicted_class, confidence, metadata

    def get_readable_prediction(self, image: Image.Image) -> dict[str, Any]:
        """Get a human-readable prediction with full details."""
        predicted_class, confidence, metadata = self.predict(image)

        # Parse class name for better readability
        if "___" in predicted_class:
            plant_type, disease = predicted_class.split("___", 1)
            plant_type = plant_type.replace("_", " ").replace(",", "").title()
            disease = disease.replace("_", " ").title()
        else:
            # Handle different formats
            parts = predicted_class.split()
            if len(parts) >= 2:
                plant_type = parts[0]
                disease = " ".join(parts[1:])
            else:
                plant_type = "Unknown"
                disease = predicted_class

        is_healthy = "healthy" in predicted_class.lower()

        return {
            "plant_type": plant_type,
            "disease": disease,
            "is_healthy": is_healthy,
            "confidence": confidence,
            "confidence_percentage": f"{confidence:.1%}",
            "raw_prediction": predicted_class,
            "model_info": metadata,
            "recommendation": self._get_recommendation(
                confidence, metadata["confidence_threshold"]
            ),
        }

    def _get_recommendation(self, confidence: float, threshold: float) -> str:
        """Get recommendation based on confidence."""
        if confidence >= threshold:
            return "High confidence - reliable prediction"
        elif confidence >= threshold * 0.7:
            return "Moderate confidence - consider additional verification"
        else:
            return "Low confidence - manual inspection recommended"

    def switch_model(self, model_id: str) -> bool:
        """Switch to a different model.

        Args:
            model_id: Model identifier to switch to

        Returns:
            True if switch successful, False otherwise
        """
        logger.info(
            "Switching from %s to %s",
            self.current_model.name if self.current_model else "None",
            model_id,
        )

        return self.load_model(model_id)

    def get_current_model_info(self) -> dict[str, Any]:
        """Get information about the currently loaded model."""
        if not self.current_model:
            return {"error": "No model loaded"}

        return {
            "name": self.current_model.name,
            "type": self.current_model.type,
            "model_id": self.current_model.model_id,
            "description": self.current_model.description,
            "accuracy": self.current_model.accuracy,
            "confidence_threshold": self.current_model.confidence_threshold,
            "device": str(self.device),
            "num_classes": len(self.current_adapter.get_class_names())
            if self.current_adapter
            else 0,
        }

    def update_model_config(self, model_id: str, updates: dict[str, Any]) -> bool:
        """Update configuration for a specific model.

        Args:
            model_id: Model identifier
            updates: Dictionary of updates to apply

        Returns:
            True if update successful, False otherwise
        """
        if model_id not in self.models_config:
            logger.error("Model ID not found: %s", model_id)
            return False

        try:
            # Load current config
            with open(self.config_path, encoding="utf-8") as f:
                config_data = json.load(f)

            # Apply updates
            for key, value in updates.items():
                if key in config_data["models"][model_id]:
                    config_data["models"][model_id][key] = value

            # Save updated config
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            # Reload configs
            self.load_model_configs()

            logger.info("Updated config for model: %s", model_id)
            return True

        except Exception as e:
            logger.error("Failed to update model config: %s", e)
            return False
