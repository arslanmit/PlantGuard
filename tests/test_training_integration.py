"""Integration tests for training configuration system."""

import torch
from torch import nn

from src.training.config import TrainingConfig
from src.training.optimizers import create_training_components
from src.training.resource_manager import get_resource_manager
from typing import Any, Dict, List, Optional, Tuple, Union, Generator


class SimpleModel(nn.Module):
    """Simple model for testing."""


    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(10, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        result: torch.Tensor = self.linear(x)
        return result


def test_end_to_end_training_setup() -> None:
    """Test complete training setup with all components."""
    # Create a training configuration
    config = TrainingConfig(
        experiment_name="integration_test",
        optimizer="adam",
        learning_rate=0.001,
        batch_size=32,
        device="auto",
        mixed_precision=True,
    )

    # Auto-optimize the configuration
    optimized_config = config.auto_optimize_resources()

    # Create a simple model
    model = SimpleModel()

    # Create training components
    components = create_training_components(model, optimized_config)

    # Verify components were created
    assert components.optimizer is not None
    assert components.scheduler is not None  # Default step scheduler
    assert components.early_stopping is not None

    # Test a simple training step simulation
    x = torch.randn(optimized_config.batch_size, 10)
    y = torch.randn(optimized_config.batch_size, 1)

    # Forward pass
    output = model(x)
    loss = nn.MSELoss()(output, y)

    # Backward pass
    components.zero_grad()
    loss.backward()
    components.step_optimizer()

    # Step scheduler
    components.step_scheduler()

    # Check early stopping
    should_stop = components.check_early_stopping(loss.item(), 1)
    assert should_stop is False  # Should not stop on first epoch

    # Verify we can get current learning rate
    lr = components.get_current_lr()
    assert lr > 0


def test_resource_manager_integration() -> None:
    """Test resource manager integration."""
    resource_manager = get_resource_manager()

    # Detect resources
    resource_info = resource_manager.detect_resources()

    assert resource_info.device_type in ["cuda", "mps", "cpu"]
    assert resource_info.total_memory > 0
    assert resource_info.available_memory > 0
    assert resource_info.cpu_count > 0

    # Test configuration optimization
    base_config = {
        "device": "auto",
        "batch_size": "auto",
        "num_workers": "auto",
        "mixed_precision": "auto",
    }

    optimized = resource_manager.optimize_training_config(base_config)

    assert optimized["device"] in ["cuda", "mps", "cpu"]
    assert isinstance(optimized["batch_size"], int)
    assert optimized["batch_size"] > 0
    assert isinstance(optimized["num_workers"], int)
    assert optimized["num_workers"] >= 0
    assert isinstance(optimized["mixed_precision"], bool)


def test_configuration_templates() -> None:
    """Test that all configuration templates work."""
    from src.training.config import ConfigTemplates

    templates = [
        ConfigTemplates.quick_test(),
        ConfigTemplates.production_training(),
        ConfigTemplates.fine_tuning(),
        ConfigTemplates.memory_efficient(),
        ConfigTemplates.auto_optimized(),
    ]

    model = SimpleModel()

    for template in templates:
        # Each template should be valid
        assert isinstance(template, TrainingConfig)

        # Should be able to create training components
        components = create_training_components(model, template)
        assert components.optimizer is not None
        assert components.early_stopping is not None

        # Should be able to serialize/deserialize
        config_dict = template.to_dict()
        restored = TrainingConfig.from_dict(config_dict)
        assert restored.experiment_name == template.experiment_name


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
