"""Vision processing module for PlantGuard.

This module contains the VisionAdapter class for plant disease detection using ResNet50.
"""

import json
import logging
from pathlib import Path
from typing import NoReturn

import torch
from PIL import Image
from torch.nn import functional
from torchvision import transforms

from .models import PlantDiseaseResNet50

logger = logging.getLogger(__name__)


class VisionAdapter:
    """Vision adapter for plant disease detection using ResNet50.

    This class handles image preprocessing and disease classification
    using a fine-tuned ResNet50 model.
    """

    def __init__(self, model_path: str | None = None, device: str = "cpu") -> None:
        """Initialize VisionAdapter.

        Args:
            model_path: Path to trained model weights
            device: Device to run model on ("cpu" or "cuda")
        """
        self.device = torch.device(device)
        self.model_path = model_path
        self.model: PlantDiseaseResNet50 | None = None
        self.transform = self._create_transform()
        self.class_names: list[str] = []
        self.is_loaded = False
        self.class_to_readable: dict[str, str] = {}
        self.plant_types: dict[str, list[str]] = {}

        logger.info("VisionAdapter initialized with device: %s", self.device)

        # Load model if path provided
        if model_path:
            try:
                self.load_checkpoint(model_path)
            except (FileNotFoundError, RuntimeError, KeyError):
                logger.exception("Failed to load model from %s", model_path)

    def _raise_model_none_error(self) -> NoReturn:
        """Raise RuntimeError for model being None despite is_loaded check."""
        msg = "Model is None despite is_loaded check"
        raise RuntimeError(msg)

    def _create_transform(self) -> transforms.Compose:
        """Create image preprocessing transform."""
        return transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def predict(self, image: Image.Image) -> tuple[str, float]:
        """Predict disease class for input image.

        Args:
            image: PIL Image of plant leaf

        Returns:
            Tuple of (disease_class_name, confidence_score)
        """
        if not self.is_loaded:
            msg = "Model not loaded. Call load_checkpoint() first."
            raise RuntimeError(msg)

        try:
            # Preprocess image
            input_tensor = self.preprocess_image(image)
            input_batch = input_tensor.unsqueeze(0).to(self.device)

            # Inference
            if self.model is not None:
                self.model.eval()
                with torch.no_grad():
                    outputs = self.model(input_batch)
                    probabilities = functional.softmax(outputs, dim=1)
                    confidence, predicted_idx = torch.max(probabilities, 1)

                    predicted_class = self.class_names[int(predicted_idx.item())]
                    confidence_score = float(confidence.item())

                    logger.debug(
                        "Prediction: %s (confidence: %.3f)",
                        predicted_class,
                        confidence_score,
                    )

                    return predicted_class, confidence_score

            # This should never happen due to is_loaded check, but needed for type safety
            self._raise_model_none_error()

        except (RuntimeError, IndexError, ValueError) as e:
            logger.exception("Prediction failed")
            msg = f"Prediction failed: {e}"
            raise RuntimeError(msg) from e

    def predict_batch(self, images: list[Image.Image]) -> list[tuple[str, float]]:
        """Predict disease classes for multiple images.

        Args:
            images: List of PIL Images

        Returns:
            List of tuples (disease_class_name, confidence_score)
        """
        if not self.is_loaded:
            msg = "Model not loaded. Call load_checkpoint() first."
            raise RuntimeError(msg)

        if not images:
            return []

        try:
            # Preprocess all images
            input_tensors = []
            for image in images:
                tensor = self.preprocess_image(image)
                input_tensors.append(tensor)

            # Stack into batch
            input_batch = torch.stack(input_tensors).to(self.device)

            # Inference
            if self.model is not None:
                self.model.eval()
                with torch.no_grad():
                    outputs = self.model(input_batch)
                    probabilities = functional.softmax(outputs, dim=1)
                    confidences, predicted_indices = torch.max(probabilities, 1)

                    results = []
                    for i in range(len(images)):
                        predicted_class = self.class_names[int(predicted_indices[i].item())]
                        confidence_score = float(confidences[i].item())
                        results.append((predicted_class, confidence_score))

                    logger.debug("Batch prediction completed for %d images", len(images))
                    return results

            # This should never happen due to is_loaded check, but needed for type safety
            self._raise_model_none_error()

        except (RuntimeError, IndexError, ValueError) as e:
            logger.exception("Batch prediction failed")
            msg = f"Batch prediction failed: {e}"
            raise RuntimeError(msg) from e

    def load_checkpoint(self, path: str) -> None:
        """Load trained model weights.

        Args:
            path: Path to model checkpoint
        """
        checkpoint_path = Path(path)

        if not checkpoint_path.exists():
            msg = f"Checkpoint file not found: {path}"
            raise FileNotFoundError(msg)

        try:
            logger.info("Loading model checkpoint from %s", path)

            # Load checkpoint
            # Use weights_only when available for safer loading; fall back if not supported
            try:
                checkpoint = torch.load(path, map_location=self.device, weights_only=True)  # nosec B614
            except TypeError:
                checkpoint = torch.load(path, map_location=self.device)  # nosec B614

            # Extract information
            num_classes = checkpoint.get("num_classes", 38)
            self.class_names = checkpoint.get("class_names", [])

            if not self.class_names:
                logger.warning("No class names found in checkpoint, using indices")
                self.class_names = [f"class_{i}" for i in range(num_classes)]

            # Create model
            self.model = PlantDiseaseResNet50(num_classes=num_classes, pretrained=False)

            # Load state dict
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.to(self.device)
            self.model.eval()

            self.is_loaded = True
            self.model_path = path

            logger.info(
                "Model loaded successfully: %d classes, device: %s",
                num_classes,
                self.device,
            )

        except (FileNotFoundError, RuntimeError, KeyError, ValueError) as e:
            logger.exception("Failed to load checkpoint")
            self.is_loaded = False
            msg = f"Failed to load checkpoint: {e}"
            raise RuntimeError(msg) from e

    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """Apply preprocessing transformations to image.

        Args:
            image: PIL Image

        Returns:
            Preprocessed tensor
        """
        try:
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Apply transforms
            tensor: torch.Tensor = self.transform(image)
        except (ValueError, RuntimeError, TypeError) as e:
            logger.exception("Image preprocessing failed")
            msg = f"Image preprocessing failed: {e}"
            raise RuntimeError(msg) from e
        else:
            return tensor

    def get_class_names(self) -> list[str]:
        """Get list of class names.

        Returns:
            List of class names
        """
        return self.class_names.copy()

    def load_class_mapping(self, mapping_path: str) -> None:
        """Load class mapping from JSON file.

        Args:
            mapping_path: Path to class mapping JSON file
        """
        try:
            with Path(mapping_path).open() as f:
                mapping_data = json.load(f)

            self.class_names = mapping_data["classes"]
            self.class_to_readable = mapping_data.get("class_to_readable", {})
            self.plant_types = mapping_data.get("plant_types", {})

            logger.info("Class mapping loaded: %d classes", len(self.class_names))

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.exception("Failed to load class mapping")
            msg = f"Failed to load class mapping: {e}"
            raise RuntimeError(msg) from e

    def get_readable_name(self, class_name: str) -> str:
        """Convert class name to human-readable format.

        Args:
            class_name: Raw class name from model

        Returns:
            Human-readable disease name
        """
        return self.class_to_readable.get(class_name, class_name)

    def get_plant_type(self, class_name: str) -> str:
        """Extract plant type from class name.

        Args:
            class_name: Raw class name from model

        Returns:
            Plant type (e.g., "Apple", "Tomato")
        """
        for plant_type, classes in self.plant_types.items():
            if class_name in classes:
                return plant_type

        # Fallback: extract from class name
        return class_name.split("___")[0] if "___" in class_name else "Unknown"

    def is_healthy(self, class_name: str) -> bool:
        """Check if the predicted class indicates a healthy plant.

        Args:
            class_name: Raw class name from model

        Returns:
            True if plant is healthy, False otherwise
        """
        return "healthy" in class_name.lower()

    def predict_with_readable_name(self, image: Image.Image) -> tuple[str, str, float, str]:
        """Predict with human-readable disease name and plant type.

        Args:
            image: PIL Image of plant leaf

        Returns:
            Tuple of (raw_class, readable_name, confidence, plant_type)
        """
        raw_class, confidence = self.predict(image)
        readable_name = self.get_readable_name(raw_class)
        plant_type = self.get_plant_type(raw_class)

        return raw_class, readable_name, confidence, plant_type

    def get_model_info(self) -> dict:
        """Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "is_loaded": self.is_loaded,
            "model_path": self.model_path,
            "device": str(self.device),
            "num_classes": len(self.class_names),
            "class_names": self.class_names.copy(),
            "has_readable_mapping": bool(self.class_to_readable),
            "has_plant_types": bool(self.plant_types),
        }
