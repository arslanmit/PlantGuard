"""Unit tests for optimizer and scheduler factories."""

import pytest
import torch
from torch import nn
from torch.optim.lr_scheduler import (
    CosineAnnealingLR,
    ExponentialLR,
    LinearLR,
    ReduceLROnPlateau,
    StepLR,
)

from src.training.config import EarlyStoppingConfig, SchedulerConfig, TrainingConfig
from src.training.optimizers import (
    EarlyStopping,
    OptimizerFactory,
    SchedulerFactory,
    TrainingComponents,
    create_training_components,
)


class SimpleModel(nn.Module):
    """Simple model for testing."""

    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(10, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        result: torch.Tensor = self.linear(x)
        return result


class TestOptimizerFactory:
    """Test OptimizerFactory functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.model = SimpleModel()
        self.config = TrainingConfig(
            learning_rate=0.001,
            weight_decay=1e-4,
            momentum=0.9,
        )

    def test_create_adam_optimizer(self) -> None:
        """Test Adam optimizer creation."""
        self.config.optimizer = "adam"
        optimizer = OptimizerFactory.create_optimizer(self.model, self.config)

        assert isinstance(optimizer, torch.optim.Adam)
        assert optimizer.param_groups[0]["lr"] == 0.001
        assert optimizer.param_groups[0]["weight_decay"] == 1e-4

    def test_create_adamw_optimizer(self) -> None:
        """Test AdamW optimizer creation."""
        self.config.optimizer = "adamw"
        optimizer = OptimizerFactory.create_optimizer(self.model, self.config)

        assert isinstance(optimizer, torch.optim.AdamW)
        assert optimizer.param_groups[0]["lr"] == 0.001
        assert optimizer.param_groups[0]["weight_decay"] == 1e-4

    def test_create_sgd_optimizer(self) -> None:
        """Test SGD optimizer creation."""
        self.config.optimizer = "sgd"
        optimizer = OptimizerFactory.create_optimizer(self.model, self.config)

        assert isinstance(optimizer, torch.optim.SGD)
        assert optimizer.param_groups[0]["lr"] == 0.001
        assert optimizer.param_groups[0]["weight_decay"] == 1e-4
        assert optimizer.param_groups[0]["momentum"] == 0.9

    def test_create_rmsprop_optimizer(self) -> None:
        """Test RMSprop optimizer creation."""
        self.config.optimizer = "rmsprop"
        optimizer = OptimizerFactory.create_optimizer(self.model, self.config)

        assert isinstance(optimizer, torch.optim.RMSprop)
        assert optimizer.param_groups[0]["lr"] == 0.001
        assert optimizer.param_groups[0]["weight_decay"] == 1e-4
        assert optimizer.param_groups[0]["momentum"] == 0.9

    def test_create_unsupported_optimizer(self) -> None:
        """Test unsupported optimizer raises ValueError."""
        self.config.optimizer = "unsupported"

        with pytest.raises(ValueError, match="Unsupported optimizer"):
            OptimizerFactory.create_optimizer(self.model, self.config)

    def test_optimizer_case_insensitive(self) -> None:
        """Test optimizer creation is case insensitive."""
        self.config.optimizer = "ADAM"
        optimizer = OptimizerFactory.create_optimizer(self.model, self.config)

        assert isinstance(optimizer, torch.optim.Adam)


class TestSchedulerFactory:
    """Test SchedulerFactory functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.model = SimpleModel()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)

    def test_create_step_scheduler(self) -> None:
        """Test StepLR scheduler creation."""
        config = SchedulerConfig(type="step", step_size=30, gamma=0.1)
        scheduler = SchedulerFactory.create_scheduler(self.optimizer, config)

        assert isinstance(scheduler, StepLR)
        assert scheduler.step_size == 30
        assert scheduler.gamma == 0.1

    def test_create_exponential_scheduler(self) -> None:
        """Test ExponentialLR scheduler creation."""
        config = SchedulerConfig(type="exponential", gamma=0.95)
        scheduler = SchedulerFactory.create_scheduler(self.optimizer, config)

        assert isinstance(scheduler, ExponentialLR)
        assert scheduler.gamma == 0.95

    def test_create_cosine_scheduler(self) -> None:
        """Test CosineAnnealingLR scheduler creation."""
        config = SchedulerConfig(type="cosine", T_max=100, eta_min=1e-6)
        scheduler = SchedulerFactory.create_scheduler(self.optimizer, config)

        assert isinstance(scheduler, CosineAnnealingLR)
        assert scheduler.T_max == 100
        assert scheduler.eta_min == 1e-6

    def test_create_plateau_scheduler(self) -> None:
        """Test ReduceLROnPlateau scheduler creation."""
        config = SchedulerConfig(type="plateau", factor=0.5, patience=10)
        scheduler = SchedulerFactory.create_scheduler(self.optimizer, config)

        assert isinstance(scheduler, ReduceLROnPlateau)
        assert scheduler.factor == 0.5
        assert scheduler.patience == 10

    def test_create_linear_scheduler(self) -> None:
        """Test LinearLR scheduler creation."""
        config = SchedulerConfig(type="linear", T_max=50, eta_min=1e-5)
        scheduler = SchedulerFactory.create_scheduler(self.optimizer, config)

        assert isinstance(scheduler, LinearLR)
        assert scheduler.total_iters == 50

    def test_create_none_scheduler(self) -> None:
        """Test no scheduler creation."""
        config = SchedulerConfig(type="none")
        scheduler = SchedulerFactory.create_scheduler(self.optimizer, config)

        assert scheduler is None

    def test_create_unsupported_scheduler(self) -> None:
        """Test unsupported scheduler raises ValueError."""
        with pytest.raises(ValueError, match="Invalid scheduler type"):
            SchedulerConfig(type="unsupported")

    def test_scheduler_case_insensitive(self) -> None:
        """Test scheduler creation is case insensitive."""
        config = SchedulerConfig(type="STEP", step_size=30, gamma=0.1)
        scheduler = SchedulerFactory.create_scheduler(self.optimizer, config)

        assert isinstance(scheduler, StepLR)


class TestEarlyStopping:
    """Test EarlyStopping functionality."""

    def test_early_stopping_disabled(self) -> None:
        """Test early stopping when disabled."""
        config = EarlyStoppingConfig(enabled=False)
        early_stopping = EarlyStopping(config)

        # Should never trigger when disabled
        assert early_stopping(1.0, 1) is False
        assert early_stopping(2.0, 2) is False
        assert early_stopping(3.0, 3) is False

    def test_early_stopping_minimize_mode(self) -> None:
        """Test early stopping in minimize mode."""
        config = EarlyStoppingConfig(
            enabled=True,
            patience=2,
            min_delta=0.01,
            mode="min",
        )
        early_stopping = EarlyStopping(config)

        # First score - should not stop
        assert early_stopping(1.0, 1) is False
        assert early_stopping.get_best_score() == 1.0
        assert early_stopping.get_best_epoch() == 1

        # Better score - should not stop
        assert early_stopping(0.8, 2) is False
        assert early_stopping.get_best_score() == 0.8
        assert early_stopping.get_best_epoch() == 2

        # Worse score - should not stop (patience=2)
        assert early_stopping(0.9, 3) is False

        # Still worse - should stop after patience=2 epochs
        assert early_stopping(1.0, 4) is True

    def test_early_stopping_maximize_mode(self) -> None:
        """Test early stopping in maximize mode."""
        config = EarlyStoppingConfig(
            enabled=True,
            patience=2,
            min_delta=0.01,
            mode="max",
        )
        early_stopping = EarlyStopping(config)

        # First score
        assert early_stopping(0.8, 1) is False

        # Better score (higher)
        assert early_stopping(0.9, 2) is False
        assert early_stopping.get_best_score() == 0.9

        # Worse scores
        assert early_stopping(0.85, 3) is False
        assert early_stopping(0.8, 4) is True

    def test_early_stopping_min_delta(self) -> None:
        """Test early stopping with min_delta threshold."""
        config = EarlyStoppingConfig(
            enabled=True,
            patience=1,
            min_delta=0.1,
            mode="min",
        )
        early_stopping = EarlyStopping(config)

        # First score
        assert early_stopping(1.0, 1) is False

        # Small improvement (less than min_delta) - should count as no improvement
        # Should trigger early stopping after patience=1 epochs
        assert early_stopping(0.95, 2) is True

    def test_early_stopping_reset(self) -> None:
        """Test early stopping reset functionality."""
        config = EarlyStoppingConfig(enabled=True, patience=2)
        early_stopping = EarlyStopping(config)

        # Set some state
        early_stopping(1.0, 1)
        early_stopping(1.1, 2)

        assert early_stopping.get_best_score() == 1.0
        assert early_stopping.counter == 1

        # Reset
        early_stopping.reset()

        assert early_stopping.get_best_score() is None
        assert early_stopping.counter == 0
        assert early_stopping.best_epoch == 0
        assert early_stopping.should_stop is False


class TestTrainingComponents:
    """Test TrainingComponents functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.model = SimpleModel()
        self.config = TrainingConfig(
            optimizer="adam",
            learning_rate=0.001,
            scheduler=SchedulerConfig(type="step", step_size=30, gamma=0.1),
            early_stopping=EarlyStoppingConfig(enabled=True, patience=5),
        )

    def test_training_components_initialization(self) -> None:
        """Test TrainingComponents initialization."""
        components = TrainingComponents(self.model, self.config)

        assert isinstance(components.optimizer, torch.optim.Adam)
        assert isinstance(components.scheduler, StepLR)
        assert isinstance(components.early_stopping, EarlyStopping)

    def test_step_scheduler_regular(self) -> None:
        """Test stepping regular scheduler."""
        components = TrainingComponents(self.model, self.config)
        initial_lr = components.get_current_lr()

        # Step scheduler multiple times (with optimizer step first)
        for _ in range(30):  # step_size = 30
            components.step_optimizer()  # Must call optimizer.step() before scheduler.step()
            components.step_scheduler()

        # Learning rate should be reduced after 30 steps
        new_lr = components.get_current_lr()
        assert new_lr < initial_lr

    def test_step_scheduler_plateau(self) -> None:
        """Test stepping ReduceLROnPlateau scheduler."""
        config = TrainingConfig(
            optimizer="adam",
            learning_rate=0.001,
            scheduler=SchedulerConfig(type="plateau", factor=0.5, patience=2),
        )
        components = TrainingComponents(self.model, config)

        # Step with metric - need patience+1 steps to trigger
        components.step_optimizer()  # Must call optimizer.step() before scheduler.step()
        components.step_scheduler(metric=1.0)
        components.step_optimizer()
        components.step_scheduler(metric=1.1)  # Worse
        components.step_optimizer()
        components.step_scheduler(metric=1.2)  # Still worse
        components.step_optimizer()
        components.step_scheduler(metric=1.3)  # Still worse (triggers after patience=2)

        # Should reduce learning rate after patience steps
        assert components.get_current_lr() < 0.001

    def test_step_scheduler_plateau_no_metric(self) -> None:
        """Test stepping ReduceLROnPlateau scheduler without metric."""
        config = TrainingConfig(
            optimizer="adam",
            learning_rate=0.001,
            scheduler=SchedulerConfig(type="plateau", factor=0.5, patience=2),
        )
        components = TrainingComponents(self.model, config)

        # Should not crash when no metric provided
        components.step_optimizer()  # Must call optimizer.step() before scheduler.step()
        components.step_scheduler()  # No metric provided
        assert components.get_current_lr() == 0.001  # Should remain unchanged

    def test_check_early_stopping(self) -> None:
        """Test early stopping check."""
        components = TrainingComponents(self.model, self.config)

        # Should not stop initially
        assert components.check_early_stopping(1.0, 1) is False
        assert components.check_early_stopping(1.1, 2) is False

        # Continue with worse scores until patience is exceeded
        # Best score is 1.0 from epoch 1
        # Epoch 2 has score 1.1 (worse, counter=1)
        # Now we need 4 more epochs of no improvement to reach patience=5
        should_stop = components.check_early_stopping(1.2, 3)  # counter=2
        assert should_stop is False
        should_stop = components.check_early_stopping(1.2, 4)  # counter=3
        assert should_stop is False
        should_stop = components.check_early_stopping(1.2, 5)  # counter=4
        assert should_stop is False
        should_stop = components.check_early_stopping(1.2, 6)  # counter=5, should trigger
        assert should_stop is True

    def test_state_dict_operations(self) -> None:
        """Test state dictionary save/load operations."""
        components = TrainingComponents(self.model, self.config)

        # Set some state
        components.check_early_stopping(1.0, 1)
        components.step_optimizer()  # Must call optimizer.step() before scheduler.step()
        components.step_scheduler()

        # Get state dict
        state_dict = components.get_state_dict()

        assert "optimizer" in state_dict
        assert "scheduler" in state_dict
        assert "early_stopping" in state_dict

        # Create new components and load state
        new_components = TrainingComponents(self.model, self.config)
        new_components.load_state_dict(state_dict)

        # Verify state was loaded
        assert new_components.early_stopping.get_best_score() == 1.0

    def test_optimizer_operations(self) -> None:
        """Test optimizer operations."""
        components = TrainingComponents(self.model, self.config)

        # Test zero_grad and step
        components.zero_grad()
        components.step_optimizer()

        # Should not raise any errors
        assert True

    def test_no_scheduler(self) -> None:
        """Test components with no scheduler."""
        config = TrainingConfig(
            optimizer="adam",
            scheduler=SchedulerConfig(type="none"),
        )
        components = TrainingComponents(self.model, config)

        assert components.scheduler is None

        # Should not crash when stepping
        components.step_optimizer()  # Call optimizer step first for consistency
        components.step_scheduler()


class TestCreateTrainingComponents:
    """Test create_training_components function."""

    def test_create_training_components(self) -> None:
        """Test create_training_components function."""
        model = SimpleModel()
        config = TrainingConfig(optimizer="adam")

        components = create_training_components(model, config)

        assert isinstance(components, TrainingComponents)
        assert isinstance(components.optimizer, torch.optim.Adam)


if __name__ == "__main__":
    pytest.main([__file__])
