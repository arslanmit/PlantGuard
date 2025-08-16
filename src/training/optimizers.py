"""Optimizer and scheduler factories for production training pipeline.

This module provides factory functions for creating optimizers, learning rate schedulers,
and early stopping mechanisms with comprehensive configuration support.
"""

import logging
from typing import Any

import torch
from torch import nn, optim
from torch.optim.lr_scheduler import (
    CosineAnnealingLR,
    ExponentialLR,
    LinearLR,
    ReduceLROnPlateau,
    StepLR,
)

from .config import EarlyStoppingConfig, SchedulerConfig, TrainingConfig

logger = logging.getLogger(__name__)


class OptimizerFactory:
    """Factory for creating optimizers with proper configuration."""

    @staticmethod
    def create_optimizer(
        model: nn.Module,
        config: TrainingConfig,
    ) -> optim.Optimizer:
        """Create optimizer based on configuration.

        Args:
            model: PyTorch model
            config: Training configuration

        Returns:
            Configured optimizer

        Raises:
            ValueError: If optimizer type is not supported
        """
        optimizer_name = config.optimizer.lower()
        params = model.parameters()

        optimizer: optim.Optimizer
        if optimizer_name == "adam":
            optimizer = optim.Adam(
                params,
                lr=config.learning_rate,
                weight_decay=config.weight_decay,
            )
        elif optimizer_name == "adamw":
            optimizer = optim.AdamW(
                params,
                lr=config.learning_rate,
                weight_decay=config.weight_decay,
            )
        elif optimizer_name == "sgd":
            optimizer = optim.SGD(
                params,
                lr=config.learning_rate,
                momentum=config.momentum,
                weight_decay=config.weight_decay,
            )
        elif optimizer_name == "rmsprop":
            optimizer = optim.RMSprop(
                params,
                lr=config.learning_rate,
                weight_decay=config.weight_decay,
                momentum=config.momentum,
            )
        else:
            raise ValueError(f"Unsupported optimizer: {optimizer_name}. Supported optimizers: adam, adamw, sgd, rmsprop")

        logger.info(f"Created {optimizer_name.upper()} optimizer with lr={config.learning_rate}")
        return optimizer


class SchedulerFactory:
    """Factory for creating learning rate schedulers with proper configuration."""

    @staticmethod
    def create_scheduler(
        optimizer: optim.Optimizer,
        scheduler_config: SchedulerConfig,
    ) -> torch.optim.lr_scheduler.LRScheduler | None:
        """Create learning rate scheduler based on configuration.

        Args:
            optimizer: PyTorch optimizer
            scheduler_config: Scheduler configuration

        Returns:
            Configured scheduler or None if scheduler type is 'none'

        Raises:
            ValueError: If scheduler type is not supported
        """
        scheduler_type = scheduler_config.type.lower()

        if scheduler_type == "none":
            logger.info("No learning rate scheduler configured")
            return None

        scheduler: torch.optim.lr_scheduler.LRScheduler
        if scheduler_type == "step":
            scheduler = StepLR(
                optimizer,
                step_size=scheduler_config.step_size,
                gamma=scheduler_config.gamma,
            )
            logger.info(f"Created StepLR scheduler: step_size={scheduler_config.step_size}, gamma={scheduler_config.gamma}")

        elif scheduler_type == "exponential":
            scheduler = ExponentialLR(
                optimizer,
                gamma=scheduler_config.gamma,
            )
            logger.info(f"Created ExponentialLR scheduler: gamma={scheduler_config.gamma}")

        elif scheduler_type == "cosine":
            scheduler = CosineAnnealingLR(
                optimizer,
                T_max=scheduler_config.T_max,
                eta_min=scheduler_config.eta_min,
            )
            logger.info(f"Created CosineAnnealingLR scheduler: T_max={scheduler_config.T_max}, eta_min={scheduler_config.eta_min}")

        elif scheduler_type == "plateau":
            scheduler = ReduceLROnPlateau(
                optimizer,
                mode="min",  # Assume we're monitoring loss
                factor=scheduler_config.factor,
                patience=scheduler_config.patience,
            )
            logger.info(f"Created ReduceLROnPlateau scheduler: factor={scheduler_config.factor}, patience={scheduler_config.patience}")

        elif scheduler_type == "linear":
            scheduler = LinearLR(
                optimizer,
                start_factor=1.0,
                end_factor=scheduler_config.eta_min / float(optimizer.param_groups[0]["lr"]),
                total_iters=scheduler_config.T_max,
            )
            logger.info(f"Created LinearLR scheduler: total_iters={scheduler_config.T_max}, end_factor={scheduler_config.eta_min}")

        else:
            raise ValueError(f"Unsupported scheduler: {scheduler_type}. Supported schedulers: step, exponential, cosine, plateau, linear, none")

        return scheduler


class EarlyStopping:
    """Early stopping mechanism to prevent overfitting."""

    def __init__(self, config: EarlyStoppingConfig) -> None:
        """Initialize early stopping.

        Args:
            config: Early stopping configuration
        """
        self.config = config
        self.best_score: float | None = None
        self.counter = 0
        self.best_epoch = 0
        self.should_stop = False

        # Determine if we want to maximize or minimize the metric
        self.is_better = self._is_better_max if config.mode == "max" else self._is_better_min

        logger.info(f"Early stopping initialized: monitor={config.monitor}, patience={config.patience}, min_delta={config.min_delta}, mode={config.mode}")

    def _is_better_min(self, score: float, best_score: float) -> bool:
        """Check if score is better when minimizing."""
        return score < best_score - self.config.min_delta

    def _is_better_max(self, score: float, best_score: float) -> bool:
        """Check if score is better when maximizing."""
        return score > best_score + self.config.min_delta

    def __call__(self, score: float, epoch: int) -> bool:
        """Check if training should stop early.

        Args:
            score: Current metric score
            epoch: Current epoch number

        Returns:
            True if training should stop, False otherwise
        """
        if not self.config.enabled:
            return False

        if self.best_score is None:
            self.best_score = score
            self.best_epoch = epoch
            logger.info(f"Early stopping: initial best score = {score:.6f}")
            return False

        if self.is_better(score, self.best_score):
            self.best_score = score
            self.best_epoch = epoch
            self.counter = 0
            logger.info(f"Early stopping: new best score = {score:.6f} at epoch {epoch}")
        else:
            self.counter += 1
            logger.info(f"Early stopping: no improvement for {self.counter}/{self.config.patience} epochs")

            if self.counter >= self.config.patience:
                self.should_stop = True
                logger.info(f"Early stopping triggered! Best score: {self.best_score:.6f} at epoch {self.best_epoch}")
                return True

        return False

    def get_best_score(self) -> float | None:
        """Get the best score achieved.

        Returns:
            Best score or None if no scores recorded
        """
        return self.best_score

    def get_best_epoch(self) -> int:
        """Get the epoch with the best score.

        Returns:
            Best epoch number
        """
        return self.best_epoch

    def reset(self) -> None:
        """Reset early stopping state."""
        self.best_score = None
        self.counter = 0
        self.best_epoch = 0
        self.should_stop = False
        logger.info("Early stopping state reset")


class TrainingComponents:
    """Container for training components (optimizer, scheduler, early stopping)."""

    def __init__(
        self,
        model: nn.Module,
        config: TrainingConfig,
    ) -> None:
        """Initialize training components.

        Args:
            model: PyTorch model
            config: Training configuration
        """
        self.config = config

        # Create optimizer
        self.optimizer = OptimizerFactory.create_optimizer(model, config)

        # Create scheduler
        self.scheduler = SchedulerFactory.create_scheduler(self.optimizer, config.scheduler)

        # Create early stopping
        self.early_stopping = EarlyStopping(config.early_stopping)

        logger.info("Training components initialized successfully")

    def step_scheduler(self, metric: float | None = None) -> None:
        """Step the learning rate scheduler.

        Args:
            metric: Metric value for ReduceLROnPlateau scheduler
        """
        if self.scheduler is None:
            return

        if isinstance(self.scheduler, ReduceLROnPlateau):
            if metric is None:
                logger.warning("ReduceLROnPlateau scheduler requires metric, skipping step")
                return
            self.scheduler.step(metric)
        else:
            self.scheduler.step()

        # Log current learning rate
        current_lr = self.optimizer.param_groups[0]["lr"]
        logger.debug(f"Learning rate updated to: {current_lr:.8f}")

    def check_early_stopping(self, metric: float, epoch: int) -> bool:
        """Check if training should stop early.

        Args:
            metric: Current metric value
            epoch: Current epoch number

        Returns:
            True if training should stop
        """
        return self.early_stopping(metric, epoch)

    def get_state_dict(self) -> dict[str, Any]:
        """Get state dictionary for checkpointing.

        Returns:
            State dictionary containing optimizer and scheduler states
        """
        state_dict = {
            "optimizer": self.optimizer.state_dict(),
            "early_stopping": {
                "best_score": self.early_stopping.best_score,
                "counter": self.early_stopping.counter,
                "best_epoch": self.early_stopping.best_epoch,
                "should_stop": self.early_stopping.should_stop,
            },
        }

        if self.scheduler is not None:
            state_dict["scheduler"] = self.scheduler.state_dict()

        return state_dict

    def load_state_dict(self, state_dict: dict[str, Any]) -> None:
        """Load state dictionary from checkpoint.

        Args:
            state_dict: State dictionary to load
        """
        if "optimizer" in state_dict:
            self.optimizer.load_state_dict(state_dict["optimizer"])
            logger.info("Optimizer state loaded from checkpoint")

        if "scheduler" in state_dict and self.scheduler is not None:
            self.scheduler.load_state_dict(state_dict["scheduler"])
            logger.info("Scheduler state loaded from checkpoint")

        if "early_stopping" in state_dict:
            es_state = state_dict["early_stopping"]
            self.early_stopping.best_score = es_state.get("best_score")
            self.early_stopping.counter = es_state.get("counter", 0)
            self.early_stopping.best_epoch = es_state.get("best_epoch", 0)
            self.early_stopping.should_stop = es_state.get("should_stop", False)
            logger.info("Early stopping state loaded from checkpoint")

    def get_current_lr(self) -> float:
        """Get current learning rate.

        Returns:
            Current learning rate
        """
        return float(self.optimizer.param_groups[0]["lr"])

    def zero_grad(self) -> None:
        """Zero gradients."""
        self.optimizer.zero_grad()

    def step_optimizer(self) -> None:
        """Step the optimizer."""
        self.optimizer.step()


def create_training_components(
    model: nn.Module,
    config: TrainingConfig,
) -> TrainingComponents:
    """Create training components from configuration.

    Args:
        model: PyTorch model
        config: Training configuration

    Returns:
        TrainingComponents instance
    """
    return TrainingComponents(model, config)
