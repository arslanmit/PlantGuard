#!/usr/bin/env python3
"""Test model inference on a sample image."""

import json
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


class CustomResNet(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        # Load a pre-trained ResNet50
        resnet = models.resnet50(pretrained=False)

        # Use all layers except the final fully connected layer as the backbone
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])

        # Add a custom classifier
        self.fc = nn.Linear(resnet.fc.in_features, num_classes)

    def forward(self, x):
        # Forward pass through the backbone
        x = self.backbone(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = self.fc(x)  # Classifier
        return x


def load_model(model_path):
    """Load the model from checkpoint."""
    print(f"Loading model from {model_path}...")
    checkpoint = torch.load(model_path, map_location="cpu")

    # Create model with correct number of classes
    if "class_names" in checkpoint:
        num_classes = len(checkpoint["class_names"])
    elif "config" in checkpoint and "num_classes" in checkpoint["config"]:
        num_classes = checkpoint["config"]["num_classes"]
    else:
        num_classes = 2  # Default to binary classification

    model = CustomResNet(num_classes=num_classes)

    # Load the state dict
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.eval()
    print(f"Model loaded with {num_classes} classes")

    # Get class names if available
    class_names = checkpoint.get("class_names", [f"class_{i}" for i in range(num_classes)])

    return model, class_names


def preprocess_image(image_path):
    """Preprocess image for model inference."""
    # Define the same transforms used during training
    transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # Load and preprocess the image
    image = Image.open(image_path).convert("RGB")
    input_tensor = transform(image)
    input_batch = input_tensor.unsqueeze(0)  # Create a mini-batch as expected by the model

    return input_batch, image


def predict(model, input_batch, class_names):
    """Run model inference and return predictions."""
    with torch.no_grad():
        output = model(input_batch)

    # Get probabilities
    probabilities = torch.nn.functional.softmax(output[0], dim=0)

    # Get top 5 predictions
    top5_prob, top5_catid = torch.topk(probabilities, min(5, len(class_names)))

    return [{"class": class_names[i], "probability": prob.item()} for i, prob in zip(top5_catid, top5_prob, strict=False)]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test model inference on an image.")
    parser.add_argument("--model", type=str, default="data/models/converted_model_fixed.pt", help="Path to the model file")
    parser.add_argument("--image", type=str, required=True, help="Path to the input image")

    args = parser.parse_args()

    # Load model
    model, class_names = load_model(args.model)
    print(f"Class names: {class_names}")

    # Load and preprocess image
    input_batch, image = preprocess_image(args.image)

    # Run inference
    predictions = predict(model, input_batch, class_names)

    # Print results
    print("\nPredictions:")
    for pred in predictions:
        print(f"{pred['class']}: {pred['probability'] * 100:.2f}%")

    # Save results
    result = {"image": args.image, "predictions": predictions, "class_names": class_names}

    Path("runs/inference").mkdir(parents=True, exist_ok=True)
    output_file = f"runs/inference/{Path(args.image).name.split('.')[0]}_results.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to {output_file}")
