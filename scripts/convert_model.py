#!/usr/bin/env python3
"""Convert a trained model to the expected format for evaluation."""

import argparse
import os
import torch

def convert_model(input_path, output_path):
    """Convert a trained model to the expected format for evaluation.
    
    Args:
        input_path: Path to the input model file
        output_path: Path to save the converted model
    """
    print(f"Loading model from {input_path}...")
    checkpoint = torch.load(input_path, map_location='cpu')
    
    # Extract the model state dict
    model_state_dict = checkpoint['model_state_dict']
    
    # Create a new checkpoint with the expected format
    converted_checkpoint = {
        'model_state_dict': model_state_dict,
        'config': {
            'num_classes': checkpoint['num_classes'],
            'model_architecture': 'resnet50'  # Assuming it's a ResNet50 based on the state dict
        },
        'class_names': checkpoint['class_names']
    }
    
    # Save the converted model
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    torch.save(converted_checkpoint, output_path)
    print(f"Converted model saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert a trained model to the expected format for evaluation.')
    parser.add_argument('--input', type=str, required=True, help='Path to the input model file')
    parser.add_argument('--output', type=str, required=True, help='Path to save the converted model')
    
    args = parser.parse_args()
    convert_model(args.input, args.output)
