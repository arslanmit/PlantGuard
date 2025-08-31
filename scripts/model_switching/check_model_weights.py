#!/usr/bin/env python3
"""Check if the model has been properly trained."""

from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import sys
from pathlib import Path

import torch

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def check_model_training_status(model_path: str) -> bool:
    """Check if model appears to be trained or is just random weights."""

    print("[SEARCH] Analyzing model weights...")

    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

    print("[SUMMARY] Model Information:")
    print(f"   Classes: {checkpoint.get('num_classes', 'Unknown')}")
    print(f"   Epoch: {checkpoint.get('epoch', 'Unknown')}")
    print(f"   Training Loss: {checkpoint.get('train_loss', 'Unknown')}")
    print(f"   Validation Accuracy: {checkpoint.get('val_accuracy', 'Unknown')}")
    print(f"   Best Accuracy: {checkpoint.get('best_accuracy', 'Unknown')}")

    # Check if this looks like a trained model
    state_dict = checkpoint.get("model_state_dict", {})

    if not state_dict:
        print("[TODO] No model state dict found - this appears to be an empty/dummy model")
        return False

    # Check final layer weights (should not be random if trained)
    fc_weight = None
    for key, value in state_dict.items():
        if "fc.weight" in key or "classifier.weight" in key:
            fc_weight = value
            break

    if fc_weight is not None:
        weight_std = torch.std(fc_weight).item()
        weight_mean = torch.mean(fc_weight).item()
        print(f"   Final layer weight std: {weight_std:.6f}")
        print(f"   Final layer weight mean: {weight_mean:.6f}")

        # Random weights typically have std around 0.02-0.1 for ResNet
        if weight_std < 0.001:
            print("[WARNING]  Weights appear to be zeros - model not trained")
            return False
        elif 0.001 < weight_std < 0.01:
            print("[WARNING]  Weights appear very small - possibly undertrained")
            return False
        elif weight_std > 0.5:
            print("[WARNING]  Weights appear very large - possibly random initialization")
            return False
        else:
            print("[DONE] Weights appear reasonable for a trained model")
            return True
    else:
        print("[TODO] Could not find final layer weights")
        return False


def main() -> None:
    model_path = "data/models/vision_resnet50.pt"

    if not Path(model_path).exists():
        print(f"[TODO] Model file not found: {model_path}")
        return

    check_model_training_status(model_path)

    print("\n[PROGRESS] Recommendation:")
    print("   Based on the analysis above:")
    print("   - If weights appear untrained, run: python scripts/train_vision_model.py")
    print("   - If weights appear trained but performance is poor, consider:")
    print("     * Retraining with more epochs")
    print("     * Adjusting learning rate")
    print("     * Using data augmentation")
    print("     * Checking training data quality")


if __name__ == "__main__":
    main()
