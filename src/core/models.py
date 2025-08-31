"""Model architectures for PlantGuard.

This module contains the ResNet50 model architecture for plant disease classification.
"""


import logging

import torch
from torch import nn
from torchvision import models
from torchvision.models import ResNet50_Weights

logger = logging.getLogger(__name__)


class PlantDiseaseResNet50(nn.Module):
    """ResNet50 model for plant disease classification.

    Uses ImageNet pre-trained ResNet50 with custom classification head
    for 38 PlantVillage disease classes.
    """

    def __init__(self, num_classes: int = 38, pretrained: bool = True) -> None:
        """Initialize ResNet50 model.

        Args:
            num_classes: Number of disease classes (default: 38 for PlantVillage)
            pretrained: Whether to use ImageNet pre-trained weights
        """
        super().__init__()
        self.num_classes = num_classes

        # Load ResNet50 with optional ImageNet weights (modern API)
        weights = ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
        self.backbone = models.resnet50(weights=weights)

        # Replace final classification layer
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Linear(in_features, num_classes)

        logger.info(
            "PlantDiseaseResNet50 initialized with %d classes, pretrained=%s",
            num_classes,
            pretrained,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the model.

        Args:
            x: Input tensor of shape (batch_size, 3, 224, 224)

        Returns:
            Output logits of shape (batch_size, num_classes)
        """
        features: torch.Tensor = self.backbone(x)
        return features

    def get_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract features from the model before final classification.

        Args:
            x: Input tensor of shape (batch_size, 3, 224, 224)

        Returns:
            Feature tensor of shape (batch_size, 2048)
        """
        # Forward through all layers except the final classifier
        x = self.backbone.conv1(x)
        x = self.backbone.bn1(x)
        x = self.backbone.relu(x)
        x = self.backbone.maxpool(x)

        x = self.backbone.layer1(x)
        x = self.backbone.layer2(x)
        x = self.backbone.layer3(x)
        x = self.backbone.layer4(x)

        x = self.backbone.avgpool(x)
        return torch.flatten(x, 1)

    def freeze_backbone(self) -> None:
        """Freeze backbone parameters for fine-tuning only the classifier."""
        for param in self.backbone.parameters():
            param.requires_grad = False

        # Unfreeze final layer
        for param in self.backbone.fc.parameters():
            param.requires_grad = True

        logger.info("Backbone frozen, only final layer trainable")

    def unfreeze_backbone(self) -> None:
        """Unfreeze all parameters for full fine-tuning."""
        for param in self.backbone.parameters():
            param.requires_grad = True

        logger.info("All parameters unfrozen for full fine-tuning")
