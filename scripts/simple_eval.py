#!/usr/bin/env python3
"""Simple model evaluation script."""

import json
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from tqdm import tqdm


# Define the model architecture
class CustomResNet(nn.Module):
    def __init__(self, num_classes=2) -> None:
        super().__init__()
        # Load a pre-trained ResNet50
        resnet = torch.hub.load("pytorch/vision", "resnet50", weights=None)

        # Use all layers except the final fully connected layer as the backbone
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])

        # Add a custom classifier
        self.fc = nn.Linear(resnet.fc.in_features, num_classes)

    def forward(self, x) -> Any:
        # Forward pass through the backbone
        x = self.backbone(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = self.fc(x)  # Classifier
        return x


def load_model(model_path) -> Any:
    """Load the model from checkpoint."""

    print(f"Loading model from {model_path}...")
    checkpoint = torch.load(model_path, map_location="cpu")

    # Get number of classes
    if "class_names" in checkpoint:
        num_classes = len(checkpoint["class_names"])
    elif "config" in checkpoint and "num_classes" in checkpoint["config"]:
        num_classes = checkpoint["config"]["num_classes"]
    else:
        num_classes = 2  # Default to binary classification

    # Create model
    model = CustomResNet(num_classes=num_classes)

    # Load state dict
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        # Try loading directly (for non-converted checkpoints)
        model.load_state_dict(checkpoint)

    model.eval()
    return model


def evaluate_model(model, data_loader, device) -> Any:
    """Evaluate model on the given data loader."""
    model = model.to(device)
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in tqdm(data_loader, desc="Evaluating"):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    return accuracy


def main() -> None:
    # Set device
    device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load model
    model_path = "data/models/latest_model.pt"
    model = load_model(model_path)
    model = model.to(device)

    # Data transforms
    transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # Load dataset (processed preferred, fallback to legacy)
    candidates = [
        "data/processed/plantvillage",
        "data/PlantVillage",
    ]
    data_dir = None
    for c in candidates:
        c_path = Path(c)
        if c_path.joinpath("val").exists():
            data_dir = str(c_path)
            break
    if data_dir is None:
        print("No dataset found. Run 'make dataset-download' then 'make dataset-prepare'.")
        return
    val_dir = Path(data_dir) / "val"

    if not val_dir.exists():
        print(f"Validation directory not found: {val_dir}")
        print("Using train directory instead...")
        val_dir = Path(data_dir) / "train"

    try:
        val_dataset = datasets.ImageFolder(val_dir, transform=transform)
        val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=2)

        print(f"Found {len(val_dataset)} images in {val_dir}")
        print(f"Classes: {val_dataset.classes}")

        # Evaluate
        accuracy = evaluate_model(model, val_loader, device)
        print(f"\nValidation Accuracy: {accuracy:.2f}%")

        # Save results
        results = {
            "model": model_path,
            "dataset": val_dir,
            "accuracy": accuracy,
            "num_samples": len(val_dataset),
            "classes": val_dataset.classes,
        }

        Path("runs/evaluation").mkdir(parents=True, exist_ok=True)
        with open("runs/evaluation/simple_eval_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print("Results saved to runs/evaluation/simple_eval_results.json")

    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
