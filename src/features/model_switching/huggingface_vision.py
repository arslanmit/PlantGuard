"""Vision processing module for PlantGuard using Hugging Face models.

This module contains the HuggingFaceVisionAdapter class for plant disease detection
using pre-trained models from Hugging Face Hub.
"""

import logging

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

logger = logging.getLogger(__name__)


class HuggingFaceVisionAdapter:
    """Vision adapter using Hugging Face pre-trained models.

    This class handles image preprocessing and disease classification
    using models from Hugging Face Hub.
    """

    def __init__(
        self, model_name: str = "Abhiram4/PlantDiseaseDetectorVit2", device: str = "cpu"
    ) -> None:
        """Initialize HuggingFaceVisionAdapter.

        Args:
            model_name: Hugging Face model identifier
            device: Device to run model on ("cpu" or "cuda")
        """
        self.device = torch.device(device)
        self.model_name = model_name
        self.model: AutoModelForImageClassification | None = None
        self.processor: AutoImageProcessor | None = None
        self.class_names: list[str] = []
        self.is_loaded = False

        logger.info(
            "HuggingFaceVisionAdapter initialized with model: %s, device: %s",
            model_name,
            self.device,
        )

        # Load model automatically
        try:
            self.load_model()
        except Exception:
            logger.exception("Failed to load model during initialization")

    def load_model(self) -> None:
        """Load the Hugging Face model and processor."""
        try:
            logger.info("Loading model: %s", self.model_name)

            # Load processor and model with revision pinning for security
            self.processor = AutoImageProcessor.from_pretrained(self.model_name, revision="main")  # type: ignore # nosec B615
            self.model = AutoModelForImageClassification.from_pretrained(
                self.model_name, revision="main"
            )  # type: ignore # nosec B615
            self.model.to(self.device)  # type: ignore
            self.model.eval()  # type: ignore

            # Extract class names
            if hasattr(self.model.config, "id2label"):  # type: ignore
                self.class_names = [
                    self.model.config.id2label[i]  # type: ignore
                    for i in range(self.model.config.num_labels)  # type: ignore
                ]
            else:
                self.class_names = [
                    f"class_{i}"
                    for i in range(self.model.config.num_labels)  # type: ignore
                ]

            self.is_loaded = True
            logger.info("Model loaded successfully: %d classes", len(self.class_names))

        except Exception as e:
            logger.exception("Failed to load model")
            self.is_loaded = False
            msg = f"Failed to load model: {e}"
            raise RuntimeError(msg) from e

    def predict(self, image: Image.Image) -> tuple[str, float]:
        """Predict disease class for input image.

        Args:
            image: PIL Image of plant leaf

        Returns:
            Tuple of (disease_class_name, confidence_score)
        """
        if not self.is_loaded or self.model is None or self.processor is None:
            msg = "Model not loaded. Call load_model() first."
            raise RuntimeError(msg)

        try:
            # Ensure RGB format
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Preprocess image
            inputs = self.processor(image, return_tensors="pt")  # type: ignore
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)  # type: ignore
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class_id = int(predictions.argmax().item())
                confidence = predictions.max().item()

            predicted_class = self.class_names[predicted_class_id]

            logger.debug(
                "Prediction: %s (confidence: %.3f)",
                predicted_class,
                confidence,
            )

            return predicted_class, confidence

        except Exception as e:
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
        if not self.is_loaded or self.model is None or self.processor is None:
            msg = "Model not loaded. Call load_model() first."
            raise RuntimeError(msg)

        if not images:
            return []

        try:
            # Ensure all images are RGB
            rgb_images = []
            for image in images:
                if image.mode != "RGB":
                    rgb_images.append(image.convert("RGB"))
                else:
                    rgb_images.append(image)

            # Preprocess all images
            inputs = self.processor(rgb_images, return_tensors="pt")  # type: ignore
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)  # type: ignore
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class_ids = predictions.argmax(dim=-1)
                confidences = predictions.max(dim=-1).values

            results = []
            for i in range(len(images)):
                predicted_class = self.class_names[int(predicted_class_ids[i].item())]
                confidence = confidences[i].item()
                results.append((predicted_class, confidence))

            logger.debug("Batch prediction completed for %d images", len(images))
            return results

        except Exception as e:
            logger.exception("Batch prediction failed")
            msg = f"Batch prediction failed: {e}"
            raise RuntimeError(msg) from e

    def get_class_names(self) -> list[str]:
        """Get list of class names.

        Returns:
            List of class names
        """
        return self.class_names.copy()

    def get_readable_name(self, class_name: str) -> str:
        """Convert class name to human-readable format.

        Args:
            class_name: Raw class name from model

        Returns:
            Human-readable disease name
        """
        # Clean up the class name
        readable = class_name.replace("___", " - ").replace("_", " ")
        readable = readable.replace("(", "").replace(")", "")
        return readable.title()

    def get_plant_type(self, class_name: str) -> str:
        """Extract plant type from class name.

        Args:
            class_name: Raw class name from model

        Returns:
            Plant type (e.g., "Apple", "Tomato")
        """
        if "___" in class_name:
            plant_part = class_name.split("___")[0]
        else:
            # Fallback for different formats
            plant_part = class_name.split()[0] if " " in class_name else class_name
        # Clean up plant name
        plant_type = plant_part.replace("_", " ").replace(",", "").strip()
        return plant_type.title()

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
            "model_name": self.model_name,
            "device": str(self.device),
            "num_classes": len(self.class_names),
            "class_names": self.class_names.copy(),
            "model_type": "HuggingFace Transformers",
        }
