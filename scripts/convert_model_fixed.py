#!/usr/bin/env python3
"""Convert a trained model to the expected format for evaluation."""

import argparse
import os
import torch
import torch.nn as nn
from torchvision import models

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

def convert_model(input_path, output_path):
    """Convert a trained model to the expected format for evaluation.
    
    Args:
        input_path: Path to the input model file
        output_path: Path to save the converted model
    """
    print(f"Loading model from {input_path}...")
    checkpoint = torch.load(input_path, map_location='cpu')
    
    # Print the structure of the checkpoint for debugging
    print("Checkpoint keys:", checkpoint.keys())
    
    # Create a new checkpoint with the expected format
    converted_checkpoint = {
        'model_state_dict': checkpoint['model_state_dict'],
        'config': {
            'num_classes': checkpoint['num_classes'],
            'model_architecture': 'resnet50'
        },
        'class_names': checkpoint['class_names']
    }
    
    # Save the converted model
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    torch.save(converted_checkpoint, output_path)
    print(f"Converted model saved to {output_path}")
    
    # Test loading the model
    print("\nTesting model loading...")
    try:
        model = CustomResNet(num_classes=checkpoint['num_classes'])
        model.load_state_dict(converted_checkpoint['model_state_dict'])
        model.eval()
        print("✅ Model loaded successfully!")
        print(f"Model architecture: {model}")
        
        # Test a forward pass with a dummy input
        print("\nTesting forward pass with dummy input...")
        dummy_input = torch.randn(1, 3, 224, 224)  # Batch of 1, 3 channels, 224x224 image
        with torch.no_grad():
            output = model(dummy_input)
            print(f"Output shape: {output.shape}")
            print(f"Sample output: {output[0][:5].tolist()}...")  # First 5 logits
            
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a trained model to the expected format for evaluation.')
    parser.add_argument('--input', type=str, default='data/models/latest_model.pt', help='Path to the input model file')
    parser.add_argument('--output', type=str, default='data/models/converted_model_fixed.pt', 
                       help='Path to save the converted model')
    
    args = parser.parse_args()
    convert_model(args.input, args.output)
