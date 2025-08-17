#!/usr/bin/env python3
"""Test model loading and inference."""

import torch
import torchvision.transforms as transforms
from PIL import Image
import os

def load_model(model_path):
    """Load the model and print its architecture."""
    print(f"Loading model from {model_path}...")
    checkpoint = torch.load(model_path, map_location='cpu')
    print("Checkpoint keys:", checkpoint.keys())
    
    if 'model_state_dict' in checkpoint:
        print("\nModel state dict keys:")
        for key in list(checkpoint['model_state_dict'].keys())[:10]:
            print(f"  {key}")
        print("  ...")
    
    if 'config' in checkpoint:
        print("\nModel config:", checkpoint['config'])
    
    if 'class_names' in checkpoint:
        print("\nClass names:", checkpoint['class_names'])
    
    return checkpoint

if __name__ == "__main__":
    model_path = "data/models/converted_model.pt"
    checkpoint = load_model(model_path)
    
    # Try to create a model and load the state dict
    try:
        from torchvision import models
        print("\nAttempting to load model architecture...")
        
        # Try to determine the model architecture
        if any('resnet' in key for key in checkpoint['model_state_dict'].keys()):
            print("Detected ResNet architecture")
            model = models.resnet50(pretrained=False)
            
            # Modify the final layer based on number of classes
            if 'class_names' in checkpoint:
                num_classes = len(checkpoint['class_names'])
            else:
                num_classes = 2  # Default to binary classification
                
            model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
            
            # Load the state dict
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()
            print("Model loaded successfully!")
            
            # Print model summary
            print("\nModel architecture:")
            print(model)
            
    except Exception as e:
        print(f"Error loading model: {e}")
        import traceback
        traceback.print_exc()
