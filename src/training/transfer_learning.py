"""Transfer learning optimization for production training.

This module provides configurable layer freezing strategies, progressive unfreezing,
transfer learning evaluation, and fine-tuning optimization with different learning rates per layer.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import torch.nn as nn
from torch.optim import Optimizer

logger = logging.getLogger(__name__)


class FreezingStrategy(Enum):
    """Layer freezing strategies for transfer learning."""

    NONE = "none"  # No freezing
    BACKBONE_ONLY = "backbone_only"  # Freeze backbone, train classifier
    GRADUAL_UNFREEZE = "gradual_unfreeze"  # Gradually unfreeze layers
    LAYER_WISE = "layer_wise"  # Different learning rates per layer group
    CUSTOM = "custom"  # Custom freezing pattern


@dataclass
class LayerGroup:
    """Configuration for a group of layers with specific training settings."""

    name: str
    layer_names: list[str]
    learning_rate_multiplier: float = 1.0
    frozen: bool = False
    unfreeze_epoch: int = 0


@dataclass
class TransferLearningConfig:
    """Configuration for transfer learning optimization."""

    # Freezing strategy
    strategy: FreezingStrategy = FreezingStrategy.BACKBONE_ONLY

    # Progressive unfreezing
    enable_progressive_unfreezing: bool = False
    unfreeze_schedule: list[int] = field(default_factory=lambda: [10, 20, 30])  # Epochs to unfreeze layers

    # Layer-wise learning rates
    enable_layer_wise_lr: bool = False
    backbone_lr_multiplier: float = 0.1  # Lower LR for pre-trained layers
    classifier_lr_multiplier: float = 1.0  # Full LR for new layers

    # Fine-tuning optimization
    warmup_epochs: int = 5  # Epochs to warm up with frozen backbone
    discriminative_lr_decay: float = 0.5  # LR decay factor for deeper layers

    # Custom layer groups
    custom_layer_groups: list[LayerGroup] = field(default_factory=list)


class TransferLearningOptimizer:
    """Transfer learning optimizer with configurable strategies."""

    def __init__(
        self,
        model: nn.Module,
        config: TransferLearningConfig,
        base_learning_rate: float = 0.001,
    ) -> None:
        """Initialize transfer learning optimizer.

        Args:
            model: PyTorch model
            config: Transfer learning configuration
            base_learning_rate: Base learning rate
        """
        self.model = model
        self.config = config
        self.base_lr = base_learning_rate

        # Model analysis
        self.layer_info = self._analyze_model_layers()
        self.layer_groups = self._create_layer_groups()

        # State tracking
        self.current_epoch = 0
        self.frozen_layers: set[str] = set()
        self.unfrozen_epochs: list[int] = []

        # Apply initial freezing strategy
        self._apply_initial_freezing()

        logger.info(f"Transfer learning optimizer initialized with strategy: {config.strategy.value}")
        self._log_layer_status()

    def _analyze_model_layers(self) -> dict[str, dict[str, Any]]:
        """Analyze model layers and their properties.

        Returns:
            Dictionary with layer information
        """
        layer_info = {}

        for name, module in self.model.named_modules():
            if len(list(module.children())) == 0:  # Leaf modules only
                layer_info[name] = {
                    "module": module,
                    "type": type(module).__name__,
                    "parameters": sum(p.numel() for p in module.parameters()),
                    "trainable_parameters": sum(p.numel() for p in module.parameters() if p.requires_grad),
                    "is_classifier": self._is_classifier_layer(name, module),
                    "depth": len(name.split(".")),
                }

        logger.info(f"Analyzed {len(layer_info)} layers in model")
        return layer_info

    def _is_classifier_layer(self, name: str, module: nn.Module) -> bool:
        """Check if a layer is part of the classifier.

        Args:
            name: Layer name
            module: Layer module

        Returns:
            True if layer is part of classifier
        """
        # Common classifier layer names
        classifier_names = ["fc", "classifier", "head", "linear", "output"]

        # Check if name contains classifier keywords
        name_lower = name.lower()
        if any(cls_name in name_lower for cls_name in classifier_names):
            return True

        # Check if it's a final linear layer
        return bool(isinstance(module, nn.Linear) and "fc" in name_lower)

    def _create_layer_groups(self) -> list[LayerGroup]:
        """Create layer groups based on configuration.

        Returns:
            List of layer groups
        """
        if self.config.custom_layer_groups:
            return self.config.custom_layer_groups.copy()

        # Create default layer groups
        layer_groups = []

        # Separate backbone and classifier layers
        backbone_layers = []
        classifier_layers = []

        for name, info in self.layer_info.items():
            if info["is_classifier"]:
                classifier_layers.append(name)
            else:
                backbone_layers.append(name)

        # Create backbone group
        if backbone_layers:
            backbone_group = LayerGroup(
                name="backbone",
                layer_names=backbone_layers,
                learning_rate_multiplier=self.config.backbone_lr_multiplier,
                frozen=self.config.strategy in [FreezingStrategy.BACKBONE_ONLY, FreezingStrategy.GRADUAL_UNFREEZE],
            )
            layer_groups.append(backbone_group)

        # Create classifier group
        if classifier_layers:
            classifier_group = LayerGroup(
                name="classifier",
                layer_names=classifier_layers,
                learning_rate_multiplier=self.config.classifier_lr_multiplier,
                frozen=False,  # Classifier is usually not frozen
            )
            layer_groups.append(classifier_group)

        # For gradual unfreezing, create more granular groups
        if self.config.strategy == FreezingStrategy.GRADUAL_UNFREEZE and backbone_layers:
            layer_groups = self._create_gradual_unfreeze_groups(backbone_layers, classifier_layers)

        return layer_groups

    def _create_gradual_unfreeze_groups(
        self,
        backbone_layers: list[str],
        classifier_layers: list[str],
    ) -> list[LayerGroup]:
        """Create layer groups for gradual unfreezing.

        Args:
            backbone_layers: List of backbone layer names
            classifier_layers: List of classifier layer names

        Returns:
            List of layer groups for gradual unfreezing
        """
        layer_groups = []

        # Sort backbone layers by depth (deeper layers first for unfreezing)
        backbone_layers_sorted = sorted(backbone_layers, key=lambda name: self.layer_info[name]["depth"], reverse=True)

        # Split backbone into groups for gradual unfreezing
        num_groups = len(self.config.unfreeze_schedule)
        group_size = max(1, len(backbone_layers_sorted) // num_groups)

        for i in range(num_groups):
            start_idx = i * group_size
            end_idx = start_idx + group_size if i < num_groups - 1 else len(backbone_layers_sorted)

            group_layers = backbone_layers_sorted[start_idx:end_idx]
            unfreeze_epoch = self.config.unfreeze_schedule[i] if i < len(self.config.unfreeze_schedule) else 0

            group = LayerGroup(
                name=f"backbone_group_{i}",
                layer_names=group_layers,
                learning_rate_multiplier=self.config.backbone_lr_multiplier,
                frozen=True,
                unfreeze_epoch=unfreeze_epoch,
            )
            layer_groups.append(group)

        # Add classifier group
        if classifier_layers:
            classifier_group = LayerGroup(
                name="classifier",
                layer_names=classifier_layers,
                learning_rate_multiplier=self.config.classifier_lr_multiplier,
                frozen=False,
            )
            layer_groups.append(classifier_group)

        return layer_groups

    def _apply_initial_freezing(self) -> None:
        """Apply initial layer freezing based on strategy."""
        if self.config.strategy == FreezingStrategy.NONE:
            return

        # Freeze layers according to layer groups
        for group in self.layer_groups:
            if group.frozen:
                self._freeze_layer_group(group)

    def _freeze_layer_group(self, group: LayerGroup) -> None:
        """Freeze all layers in a group.

        Args:
            group: Layer group to freeze
        """
        frozen_params = 0

        for layer_name in group.layer_names:
            if layer_name in self.layer_info:
                module = self.layer_info[layer_name]["module"]
                for param in module.parameters():
                    param.requires_grad = False
                    frozen_params += param.numel()

                self.frozen_layers.add(layer_name)

        logger.info(f"Frozen layer group '{group.name}': {frozen_params:,} parameters")

    def _unfreeze_layer_group(self, group: LayerGroup) -> None:
        """Unfreeze all layers in a group.

        Args:
            group: Layer group to unfreeze
        """
        unfrozen_params = 0

        for layer_name in group.layer_names:
            if layer_name in self.layer_info:
                module = self.layer_info[layer_name]["module"]
                for param in module.parameters():
                    param.requires_grad = True
                    unfrozen_params += param.numel()

                self.frozen_layers.discard(layer_name)

        group.frozen = False
        logger.info(f"Unfrozen layer group '{group.name}': {unfrozen_params:,} parameters")

    def update_epoch(self, epoch: int) -> bool:
        """Update transfer learning state for new epoch.

        Args:
            epoch: Current epoch number

        Returns:
            True if any layers were unfrozen
        """
        self.current_epoch = epoch
        layers_unfrozen = False

        # Check for progressive unfreezing
        if self.config.enable_progressive_unfreezing:
            for group in self.layer_groups:
                if group.frozen and group.unfreeze_epoch > 0 and epoch >= group.unfreeze_epoch:
                    self._unfreeze_layer_group(group)
                    self.unfrozen_epochs.append(epoch)
                    layers_unfrozen = True

        # Check for warmup completion
        if epoch >= self.config.warmup_epochs and self.config.strategy == FreezingStrategy.BACKBONE_ONLY:
            # Optionally unfreeze backbone after warmup
            backbone_groups = [g for g in self.layer_groups if g.name.startswith("backbone")]
            for group in backbone_groups:
                if group.frozen:
                    self._unfreeze_layer_group(group)
                    layers_unfrozen = True

        if layers_unfrozen:
            self._log_layer_status()

        return layers_unfrozen

    def create_optimizer_param_groups(self, optimizer_class: type, **optimizer_kwargs) -> Optimizer:
        """Create optimizer with layer-wise learning rates.

        Args:
            optimizer_class: Optimizer class (e.g., torch.optim.Adam)
            **optimizer_kwargs: Additional optimizer arguments

        Returns:
            Optimizer with layer-wise parameter groups
        """
        if not self.config.enable_layer_wise_lr:
            # Standard optimizer for all parameters
            return optimizer_class(self.model.parameters(), lr=self.base_lr, **optimizer_kwargs)
        # Create parameter groups with different learning rates
        optimizer_param_groups: list[dict[str, object]] = []

        for group in self.layer_groups:
            group_params = []

            for layer_name in group.layer_names:
                if layer_name in self.layer_info:
                    module = self.layer_info[layer_name]["module"]
                    group_params.extend(module.parameters())

            if group_params:
                # Filter out frozen parameters
                trainable_params = [p for p in group_params if p.requires_grad]

                if trainable_params:
                    group_lr = self.base_lr * group.learning_rate_multiplier
                    param_group = {
                        "params": trainable_params,
                        "lr": group_lr,
                        "name": group.name,
                    }
                    optimizer_param_groups.append(param_group)

        if not optimizer_param_groups:
            # Fallback to standard optimizer
            return optimizer_class(self.model.parameters(), lr=self.base_lr, **optimizer_kwargs)

        optimizer = optimizer_class(optimizer_param_groups, **optimizer_kwargs)

        logger.info(f"Created optimizer with {len(optimizer_param_groups)} parameter groups:")
        for i, group in enumerate(optimizer_param_groups):
            num_params = sum(p.numel() for p in group["params"])
            logger.info(f"  Group '{group['name']}': LR={group['lr']:.6f}, Params={num_params:,}")

        return optimizer

    def get_layer_statistics(self) -> dict[str, Any]:
        """Get statistics about layer freezing and training.

        Returns:
            Dictionary with layer statistics
        """
        total_params = sum(info["parameters"] for info in self.layer_info.values())
        trainable_params = sum(info["parameters"] for name, info in self.layer_info.items() if name not in self.frozen_layers)
        frozen_params = total_params - trainable_params

        # Group statistics
        group_stats = []
        for group in self.layer_groups:
            group_total = sum(self.layer_info[name]["parameters"] for name in group.layer_names if name in self.layer_info)
            group_trainable = sum(
                self.layer_info[name]["parameters"] for name in group.layer_names if name in self.layer_info and name not in self.frozen_layers
            )

            group_stats.append(
                {
                    "name": group.name,
                    "total_params": group_total,
                    "trainable_params": group_trainable,
                    "frozen": group.frozen,
                    "lr_multiplier": group.learning_rate_multiplier,
                }
            )

        return {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "frozen_parameters": frozen_params,
            "trainable_ratio": trainable_params / total_params if total_params > 0 else 0,
            "num_layer_groups": len(self.layer_groups),
            "group_statistics": group_stats,
            "unfrozen_epochs": self.unfrozen_epochs,
            "current_epoch": self.current_epoch,
        }

    def _log_layer_status(self) -> None:
        """Log current layer freezing status."""
        stats = self.get_layer_statistics()

        logger.info("Transfer Learning Status:")
        logger.info(f"  Total parameters: {stats['total_parameters']:,}")
        logger.info(f"  Trainable parameters: {stats['trainable_parameters']:,}")
        logger.info(f"  Frozen parameters: {stats['frozen_parameters']:,}")
        logger.info(f"  Trainable ratio: {stats['trainable_ratio']:.1%}")

        logger.info("Layer Groups:")
        for group_stat in stats["group_statistics"]:
            status = "FROZEN" if group_stat["frozen"] else "TRAINABLE"
            logger.info(
                f"  {group_stat['name']}: {group_stat['trainable_params']:,}/{group_stat['total_params']:,} params, LRx{group_stat['lr_multiplier']:.2f}, {status}"
            )

    def evaluate_transfer_learning_effectiveness(
        self,
        train_losses: list[float],
        val_losses: list[float],
        val_accuracies: list[float],
    ) -> dict[str, Any]:
        """Evaluate transfer learning effectiveness.

        Args:
            train_losses: Training losses over epochs
            val_losses: Validation losses over epochs
            val_accuracies: Validation accuracies over epochs

        Returns:
            Dictionary with transfer learning evaluation metrics
        """
        from typing import Any

        evaluation: dict[str, Any] = {
            "strategy": self.config.strategy.value,
            "total_epochs": len(train_losses),
            "unfrozen_epochs": self.unfrozen_epochs,
        }

        if len(val_accuracies) > 0:
            # Overall performance
            evaluation["final_accuracy"] = val_accuracies[-1]
            evaluation["best_accuracy"] = max(val_accuracies)
            evaluation["best_accuracy_epoch"] = val_accuracies.index(max(val_accuracies))

            # Convergence analysis
            if len(val_accuracies) >= 10:
                # Check if accuracy improved in last 10 epochs
                recent_improvement = max(val_accuracies[-10:]) > max(val_accuracies[:-10]) if len(val_accuracies) > 10 else False
                evaluation["recent_improvement"] = recent_improvement

                # Calculate convergence rate (epochs to reach 90% of best accuracy)
                target_accuracy = max(val_accuracies) * 0.9
                convergence_epoch = next((i for i, acc in enumerate(val_accuracies) if acc >= target_accuracy), len(val_accuracies))
                evaluation["convergence_epoch"] = convergence_epoch

        # Analyze impact of unfreezing
        if self.unfrozen_epochs and len(val_accuracies) > max(self.unfrozen_epochs):
            unfreeze_impacts = []

            for unfreeze_epoch in self.unfrozen_epochs:
                if unfreeze_epoch < len(val_accuracies) - 5:  # Need at least 5 epochs after unfreezing
                    before_acc = val_accuracies[unfreeze_epoch - 1] if unfreeze_epoch > 0 else 0
                    after_acc = max(val_accuracies[unfreeze_epoch : unfreeze_epoch + 5])
                    improvement = after_acc - before_acc

                    unfreeze_impacts.append(
                        {
                            "epoch": unfreeze_epoch,
                            "accuracy_before": before_acc,
                            "accuracy_after": after_acc,
                            "improvement": improvement,
                        }
                    )

            evaluation["unfreeze_impacts"] = unfreeze_impacts

        return evaluation

    def get_recommendations(self, evaluation: dict[str, Any]) -> list[str]:
        """Get recommendations for improving transfer learning.

        Args:
            evaluation: Transfer learning evaluation results

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check if transfer learning is effective
        if "final_accuracy" in evaluation and evaluation["final_accuracy"] < 0.7:
            recommendations.append("Low final accuracy - consider using a different pre-trained model or adjusting learning rates")

        # Check convergence
        if "convergence_epoch" in evaluation:
            total_epochs = evaluation["total_epochs"]
            convergence_ratio = evaluation["convergence_epoch"] / total_epochs

            if convergence_ratio > 0.8:
                recommendations.append("Slow convergence - consider higher learning rates or earlier unfreezing")
            elif convergence_ratio < 0.2:
                recommendations.append("Very fast convergence - consider lower learning rates to avoid overfitting")

        # Analyze unfreezing impacts
        if "unfreeze_impacts" in evaluation:
            negative_impacts = [impact for impact in evaluation["unfreeze_impacts"] if impact["improvement"] < 0]
            if len(negative_impacts) > len(evaluation["unfreeze_impacts"]) / 2:
                recommendations.append("Unfreezing appears to hurt performance - consider keeping more layers frozen")

        # Check for recent improvement
        if evaluation.get("recent_improvement", True) is False:
            recommendations.append("No recent improvement - consider unfreezing more layers or adjusting learning rates")

        return recommendations


def create_transfer_learning_optimizer(
    model: nn.Module,
    strategy: FreezingStrategy = FreezingStrategy.BACKBONE_ONLY,
    base_learning_rate: float = 0.001,
    config: TransferLearningConfig | None = None,
) -> TransferLearningOptimizer:
    """Create transfer learning optimizer with default configuration.

    Args:
        model: PyTorch model
        strategy: Freezing strategy to use
        base_learning_rate: Base learning rate
        config: Custom transfer learning configuration (optional)

    Returns:
        TransferLearningOptimizer instance
    """
    if config is None:
        config = TransferLearningConfig(strategy=strategy)

    return TransferLearningOptimizer(model, config, base_learning_rate)


def create_resnet_transfer_config(
    strategy: FreezingStrategy = FreezingStrategy.GRADUAL_UNFREEZE,
    unfreeze_schedule: list[int] | None = None,
) -> TransferLearningConfig:
    """Create optimized transfer learning configuration for ResNet models.

    Args:
        strategy: Freezing strategy
        unfreeze_schedule: Custom unfreezing schedule (optional)

    Returns:
        TransferLearningConfig optimized for ResNet
    """
    if unfreeze_schedule is None:
        unfreeze_schedule = [5, 15, 25, 35]  # Gradual unfreezing over epochs

    return TransferLearningConfig(
        strategy=strategy,
        enable_progressive_unfreezing=True,
        unfreeze_schedule=unfreeze_schedule,
        enable_layer_wise_lr=True,
        backbone_lr_multiplier=0.1,  # Lower LR for pre-trained layers
        classifier_lr_multiplier=1.0,  # Full LR for new classifier
        warmup_epochs=5,
        discriminative_lr_decay=0.5,
    )
