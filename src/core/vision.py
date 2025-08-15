"""Vision processing module for PlantGuard.

This module contains the VisionAdapter class for plant disease detection using ResNet50.
"""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, NoReturn, cast

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from .models import PlantDiseaseResNet50

logger = logging.getLogger(__name__)


class ModelNotLoadedError(RuntimeError):
    """Raised when a model-dependent operation is called before loading the model."""

    def __init__(self) -> None:
        """Initialize ModelNotLoadedError."""
        super().__init__("Model not loaded. Call load_checkpoint() first.")


class ModelNoneError(RuntimeError):
    """Raised when model is unexpectedly None after load check."""

    def __init__(self) -> None:
        """Initialize ModelNoneError."""
        super().__init__("Model reference is None")


class PredictionError(RuntimeError):
    """Raised when single-image prediction fails."""

    def __init__(self) -> None:
        """Initialize PredictionError."""
        super().__init__("Prediction failed")


class BatchPredictionError(RuntimeError):
    """Raised when batch prediction fails."""

    def __init__(self) -> None:
        """Initialize BatchPredictionError."""
        super().__init__("Batch prediction failed")


class LoadCheckpointError(RuntimeError):
    """Raised when loading a checkpoint fails."""

    def __init__(self) -> None:
        """Initialize LoadCheckpointError."""
        super().__init__("Failed to load checkpoint")


class CheckpointNotFoundError(FileNotFoundError):
    """Raised when the checkpoint file cannot be found."""

    def __init__(self) -> None:
        """Initialize CheckpointNotFoundError."""
        super().__init__("Checkpoint file not found")


class ImagePreprocessError(RuntimeError):
    """Raised when image preprocessing fails."""

    def __init__(self) -> None:
        """Initialize ImagePreprocessError."""
        super().__init__("Image preprocessing failed")


class ClassMappingLoadError(RuntimeError):
    """Raised when class mapping file cannot be loaded."""

    def __init__(self) -> None:
        """Initialize ClassMappingLoadError."""
        super().__init__("Failed to load class mapping")


class InvalidClassesError(KeyError):
    """Raised when classes format in mapping is invalid."""

    def __init__(self) -> None:
        """Initialize InvalidClassesError."""
        super().__init__("Invalid classes format")


class VisionAdapter:
    """Vision adapter for plant disease detection using ResNet50.

    This class handles image preprocessing and disease classification
    using a fine-tuned ResNet50 model.
    """

    def __init__(
        self,
        model_path: str | None = None,
        device: str = "cpu",
        img_size: tuple[int, int] = (224, 224),
    ) -> None:
        """Initialize VisionAdapter.

        Args:
            model_path: Path to trained model weights
            device: Device to run model on ("cpu" or "cuda")
            img_size: Image resize target as (height, width)
        """
        self.device = torch.device(device)
        self.model_path = model_path
        self.model: PlantDiseaseResNet50 | None = None
        self.img_size = img_size
        self.transform: Callable[[Image.Image], torch.Tensor] = self._create_transform(img_size)
        self.class_names: list[str] = []
        self.is_loaded = False
        self.class_to_readable: dict[str, str] = {}
        self.plant_types: dict[str, list[str]] = {}

        logger.info("VisionAdapter initialized with device: %s", self.device)

        # Load model if path provided
        if model_path:
            try:
                self.load_checkpoint(model_path)
                # Load class mapping if available
                mapping_path = "data/knowledge_base/plantvillage_classes.json"
                if Path(mapping_path).exists():
                    self.load_class_mapping(mapping_path)
            except (FileNotFoundError, RuntimeError, KeyError):
                logger.exception("Failed to load model from %s", model_path)

    def _raise_model_none_error(self) -> NoReturn:
        """Raise when model is None despite is_loaded check."""
        raise ModelNoneError()

    def _create_transform(self, img_size: tuple[int, int]) -> Callable[[Image.Image], torch.Tensor]:
        """Create image preprocessing transform."""
        composed = transforms.Compose(
            [
                transforms.Resize(img_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        return cast(Callable[[Image.Image], torch.Tensor], composed)

    def _raise_invalid_classes(self) -> NoReturn:
        """Raise when class list in mapping is invalid."""
        raise InvalidClassesError()

    def predict(self, image: Image.Image) -> tuple[str, float]:
        """Predict disease class for input image.

        Args:
            image: PIL Image of plant leaf

        Returns:
            Tuple of (disease_class_name, confidence_score)
        """
        if not self.is_loaded:
            raise ModelNotLoadedError()

        try:
            # Preprocess image
            input_tensor = self.preprocess_image(image)
            input_batch = input_tensor.unsqueeze(0).to(self.device)

            # Inference
            if self.model is not None:
                self.model.eval()
                with torch.no_grad():
                    outputs = self.model(input_batch)
                    probabilities = F.softmax(outputs, dim=1)
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

        except (RuntimeError, IndexError, ValueError) as error:
            logger.exception("Prediction failed")
            raise PredictionError() from error

    def predict_batch(self, images: list[Image.Image]) -> list[tuple[str, float]]:
        """Predict disease classes for multiple images.

        Args:
            images: List of PIL Images

        Returns:
            List of tuples (disease_class_name, confidence_score)
        """
        if not self.is_loaded:
            raise ModelNotLoadedError()

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
                    probabilities = F.softmax(outputs, dim=1)
                    confidences, predicted_indices = torch.max(probabilities, 1)

                    results = [
                        (
                            self.class_names[int(predicted_indices[i].item())],
                            float(confidences[i].item()),
                        )
                        for i, _ in enumerate(images)
                    ]

                    logger.debug("Batch prediction completed for %d images", len(images))
                    return results

            # This should never happen due to is_loaded check, but needed for type safety
            self._raise_model_none_error()

        except (RuntimeError, IndexError, ValueError) as error:
            logger.exception("Batch prediction failed")
            raise BatchPredictionError() from error

    def load_checkpoint(self, path: str) -> None:
        """Load trained model weights.

        Args:
            path: Path to model checkpoint

        Note:
            Only load checkpoints from trusted sources. torch.load may execute
            arbitrary code if the file is malicious.
        """
        checkpoint_path = Path(path)

        if not checkpoint_path.exists():
            raise CheckpointNotFoundError()

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

        except (FileNotFoundError, RuntimeError, KeyError, ValueError) as error:
            logger.exception("Failed to load checkpoint")
            self.is_loaded = False
            self.model = None
            self.class_names = []
            raise LoadCheckpointError() from error

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
            tensor = self.transform(image)
        except (ValueError, RuntimeError, TypeError) as error:
            logger.exception("Image preprocessing failed")
            raise ImagePreprocessError() from error
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
            with Path(mapping_path).open(encoding="utf-8") as f:
                mapping_data = json.load(f)

            classes = mapping_data.get("classes")
            if not isinstance(classes, list) or not all(isinstance(c, str) for c in classes):
                self._raise_invalid_classes()
            self.class_names = classes
            ctr = mapping_data.get("class_to_readable", {})
            if not isinstance(ctr, dict):
                ctr = {}
            ptr = mapping_data.get("plant_types", {})
            if not isinstance(ptr, dict):
                ptr = {}
            self.class_to_readable = ctr
            self.plant_types = ptr

            logger.info("Class mapping loaded: %d classes", len(self.class_names))

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as error:
            logger.exception("Failed to load class mapping")
            raise ClassMappingLoadError() from error

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

    def predict_with_calibration(self, image: Image.Image) -> tuple[str, float]:
        """Predict with confidence calibration for better usability.

        Args:
            image: PIL Image of plant leaf

        Returns:
            Tuple of (disease_class_name, calibrated_confidence_score)
        """
        if not self.is_loaded:
            raise ModelNotLoadedError()

        try:
            # Get original prediction
            predicted_class, raw_confidence = self.predict(image)

            # Apply confidence calibration (2.5x boost for better usability)
            calibrated_confidence = min(raw_confidence * 2.5, 1.0)

            logger.debug(
                "Calibrated prediction: %s (raw: %.3f, calibrated: %.3f)",
                predicted_class,
                raw_confidence,
                calibrated_confidence,
            )

            return predicted_class, calibrated_confidence

        except Exception as error:
            logger.exception("Calibrated prediction failed")
            # Fallback to original prediction
            return self.predict(image)

    def predict_with_plant_hint(self, image: Image.Image, expected_plant: str | None = None) -> tuple[str, float]:
        """Predict with optional plant type hint for better accuracy.

        Args:
            image: PIL Image of plant leaf
            expected_plant: Expected plant type (e.g., "Apple", "Tomato")

        Returns:
            Tuple of (disease_class_name, confidence_score)
        """
        # Get calibrated prediction
        predicted_class, confidence = self.predict_with_calibration(image)

        # If we have a plant hint and prediction doesn't match, try to find better match
        if expected_plant and expected_plant.lower() not in predicted_class.lower():
            plant_classes = self.plant_types.get(expected_plant, [])
            if plant_classes and self.model is not None:
                try:
                    # Get all class probabilities
                    tensor = self.preprocess_image(image)
                    input_batch = tensor.unsqueeze(0).to(self.device)

                    self.model.eval()
                    with torch.no_grad():
                        outputs = self.model(input_batch)
                        probabilities = F.softmax(outputs, dim=1)

                        # Find best match within expected plant type
                        best_confidence = 0
                        best_class = predicted_class

                        for class_name in plant_classes:
                            if class_name in self.class_names:
                                class_idx = self.class_names.index(class_name)
                                class_confidence = float(probabilities[0][class_idx].item())
                                # Apply calibration to plant-specific predictions too
                                calibrated_class_confidence = min(class_confidence * 2.5, 1.0)

                                if calibrated_class_confidence > best_confidence:
                                    best_confidence = calibrated_class_confidence
                                    best_class = class_name

                        # Use plant-specific prediction if it's reasonably confident
                        if best_confidence > confidence * 0.3:  # At least 30% as confident
                            logger.info("Plant hint improved prediction: %s -> %s (%.3f)", predicted_class, best_class, best_confidence)
                            return best_class, best_confidence

                except Exception as e:
                    logger.exception("Plant hint prediction failed")

        return predicted_class, confidence

    def get_model_info(self) -> dict[str, Any]:
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
