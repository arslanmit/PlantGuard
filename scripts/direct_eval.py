#!/usr/bin/env python3
"""Direct model evaluation script."""

import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import DataLoader, Dataset
from PIL import Image
import json
from tqdm import tqdm

# Define the model architecture to match the training
class PlantDiseaseModel(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        # Use a pre-trained ResNet50 as the backbone
        self.backbone = models.resnet50(pretrained=False)
        
        # Replace the final fully connected layer
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Linear(in_features, num_classes)
    
    def forward(self, x):
        return self.backbone(x)

def load_model(model_path, num_classes=2):
    """Load the model from checkpoint."""
    print(f"Loading model from {model_path}...")
    
    # Create model with the correct architecture
    model = PlantDiseaseModel(num_classes=num_classes)
    
    # Load the state dict
    checkpoint = torch.load(model_path, map_location='cpu')
    
    # Check if the checkpoint contains a 'model_state_dict' key
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint
    
    # Load the state dict with strict=False to ignore missing keys
    model.load_state_dict(state_dict, strict=False)
    model.eval()
    
    # Get class names if available
    class_names = checkpoint.get('class_names', [f'class_{i}' for i in range(num_classes)])
    
    return model, class_names

class PlantDiseaseDataset(Dataset):
    """Custom dataset for plant disease classification."""
    
    def __init__(self, root_dir, transform=None):
        """
        Args:
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self.root_dir = root_dir
        self.transform = transform
        
        # Get list of classes (subdirectories)
        self.classes = [d for d in os.listdir(root_dir) 
                       if os.path.isdir(os.path.join(root_dir, d))]
        self.classes.sort()
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        
        # Get list of all image files
        self.samples = []
        for class_name in self.classes:
            class_dir = os.path.join(root_dir, class_name)
            for img_name in os.listdir(class_dir):
                if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.samples.append((
                        os.path.join(class_dir, img_name),
                        self.class_to_idx[class_name]
                    ))
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
            
        return image, label

def evaluate_model(model, data_loader, device, class_names):
    """Evaluate the model on the given data loader."""
    model = model.to(device)
    model.eval()
    
    correct = 0
    total = 0
    class_correct = [0] * len(class_names)
    class_total = [0] * len(class_names)
    
    with torch.no_grad():
        for images, labels in tqdm(data_loader, desc="Evaluating"):
            images, labels = images.to(device), labels.to(device)
            
            # Forward pass
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            
            # Update statistics
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            # Update per-class statistics
            for i in range(len(labels)):
                label = labels[i]
                class_correct[label] += (predicted[i] == label).item()
                class_total[label] += 1
    
    # Calculate overall accuracy
    accuracy = 100 * correct / total
    print(f"\nOverall Accuracy: {accuracy:.2f}%")
    
    # Print per-class accuracy
    print("\nPer-class accuracy:")
    for i in range(len(class_names)):
        if class_total[i] > 0:
            print(f"  {class_names[i]}: {100 * class_correct[i] / class_total[i]:.2f}% ({class_correct[i]}/{class_total[i]})")
    
    return accuracy, class_correct, class_total

def main():
    # Set device
    device = torch.device("mps" if torch.backends.mps.is_available() 
                          else "cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Model and data paths
    model_path = "data/models/latest_model.pt"
    data_dir = "data/plantvillage_dummy_improved_smoke"
    
    # Try to find validation directory, fall back to train if not found
    val_dir = os.path.join(data_dir, 'val')
    if not os.path.exists(val_dir):
        print(f"Validation directory not found: {val_dir}")
        print("Using train directory instead...")
        val_dir = os.path.join(data_dir, 'train')
    
    # Define transforms
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    # Create dataset and data loader
    try:
        val_dataset = PlantDiseaseDataset(val_dir, transform=transform)
        val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=2)
        
        print(f"Found {len(val_dataset)} images in {val_dir}")
        print(f"Classes: {val_dataset.classes}")
        
        # Load model with the correct number of classes
        model, class_names = load_model(model_path, num_classes=len(val_dataset.classes))
        
        # Evaluate
        accuracy, class_correct, class_total = evaluate_model(model, val_loader, device, class_names)
        
        # Save results
        results = {
            'model': model_path,
            'dataset': val_dir,
            'accuracy': accuracy,
            'num_samples': len(val_dataset),
            'classes': val_dataset.classes,
            'class_accuracy': {
                cls: {
                    'correct': class_correct[i],
                    'total': class_total[i],
                    'accuracy': 100 * class_correct[i] / class_total[i] if class_total[i] > 0 else 0
                }
                for i, cls in enumerate(val_dataset.classes)
            }
        }
        
        os.makedirs('runs/evaluation', exist_ok=True)
        with open('runs/evaluation/direct_eval_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\nResults saved to runs/evaluation/direct_eval_results.json")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
