"""Optimizer and scheduler factories for production training pipeline.

This module provides factory functions for creating optimizers, learning rate schedulers,
and early stopping mechanisms with comprehensive configuration support.
"""

import logging
from typing import Any

import torch
from torch import nn, optim
from torch.optim.lr_scheduler import CosineAnnealingLR, ExponentialLR, LinearLR, ReduceLROnPlateau, StepLR

from .config import EarlyStoppingConfig, TrainingConfig

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
        scheduler_config: Any,
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
        # Allow scheduler_config to be either a SchedulerConfig object, a plain
        # string (e.g. "step"), or a dict containing a "type" key. This
        # makes the factory more robust to tests and older callers that pass
        # a simple string.
        if scheduler_config is None:
            scheduler_type = "none"
        elif isinstance(scheduler_config, str):
            scheduler_type = scheduler_config.lower()
        elif isinstance(scheduler_config, dict):
            scheduler_type = str(scheduler_config.get("type", "")).lower()
        else:
            # Fallback for dataclass-like objects with a `type` attribute
            scheduler_type = str(getattr(scheduler_config, "type", "")).lower()

        # Helper to safely read configuration fields whether scheduler_config is a dict or an object
        def _cfg(field: str, default=None):
            if isinstance(scheduler_config, dict):
                return scheduler_config.get(field, default)
            return getattr(scheduler_config, field, default)

        if scheduler_type in {"none", ""}:
            logger.info("No learning rate scheduler configured")
            return None

        scheduler: torch.optim.lr_scheduler.LRScheduler
        if scheduler_type == "step":
            step_size = _cfg("step_size", 10)
            gamma = _cfg("gamma", 0.1)
            scheduler = StepLR(
                optimizer,
                step_size=step_size,
                gamma=gamma,
            )
            logger.info(f"Created StepLR scheduler: step_size={step_size}, gamma={gamma}")

        elif scheduler_type == "exponential":
            gamma = _cfg("gamma", 0.95)
            scheduler = ExponentialLR(
                optimizer,
                gamma=gamma,
            )
            logger.info(f"Created ExponentialLR scheduler: gamma={gamma}")

        elif scheduler_type == "cosine":
            T_max = _cfg("T_max", 50)
            eta_min = _cfg("eta_min", 0.0)
            scheduler = CosineAnnealingLR(
                optimizer,
                T_max=T_max,
                eta_min=eta_min,
            )
            logger.info(f"Created CosineAnnealingLR scheduler: T_max={T_max}, eta_min={eta_min}")

        elif scheduler_type == "plateau":
            factor = _cfg("factor", 0.1)
            patience = _cfg("patience", 10)
            mode = _cfg("mode", "min")
            scheduler = ReduceLROnPlateau(
                optimizer,
                mode=mode,  # Assume we're monitoring loss by default
                factor=factor,
                patience=patience,
            )
            logger.info(f"Created ReduceLROnPlateau scheduler: factor={factor}, patience={patience}, mode={mode}")

        elif scheduler_type == "linear":
            T_max = _cfg("T_max", 100)
            eta_min = _cfg("eta_min", 0.0)
            base_lr = float(optimizer.param_groups[0].get("lr", 1.0))
            end_factor = eta_min / base_lr if base_lr != 0 else 0.0
            scheduler = LinearLR(
                optimizer,
                start_factor=1.0,
                end_factor=end_factor,
                total_iters=T_max,
            )
            logger.info(f"Created LinearLR scheduler: total_iters={T_max}, end_factor={end_factor}")

        else:
            raise ValueError(f"Unsupported scheduler: {scheduler_type}. Supported schedulers: step, exponential, cosine, plateau, linear, none")

        return scheduler


class EarlyStopping:
    """Early stopping mechanism to prevent overfitting."""

    def __init__(self, config: EarlyStoppingConfig | dict) -> None:
        """Initialize early stopping.

        Args:
            config: Early stopping configuration dataclass or plain dict
        """
        # Normalize config whether it's a dataclass or a plain dict used in tests
        if isinstance(config, dict):
            cfg = config
            self.config = None
            self.enabled = bool(cfg.get("enabled", False))
            self.monitor = str(cfg.get("monitor", "val_loss"))
            self.patience = int(cfg.get("patience", 10))
            self.min_delta = float(cfg.get("min_delta", 0.0))
            self.mode = str(cfg.get("mode", "min"))
        else:
            self.config = config
            self.enabled = getattr(config, "enabled", False)
            self.monitor = getattr(config, "monitor", "val_loss")
            self.patience = getattr(config, "patience", 10)
            self.min_delta = getattr(config, "min_delta", 0.0)
            self.mode = getattr(config, "mode", "min")

        self.best_score: float | None = None
        self.counter = 0
        self.best_epoch = 0
        self.should_stop = False

        # Determine if we want to maximize or minimize the metric
        self.is_better = self._is_better_max if self.mode == "max" else self._is_better_min

        logger.info(f"Early stopping initialized: monitor={self.monitor}, patience={self.patience}, min_delta={self.min_delta}, mode={self.mode}")

    def _is_better_min(self, score: float, best_score: float) -> bool:
        """Check if score is better when minimizing."""
        # Lower scores are better when minimizing (e.g., loss)
        try:
            return score < best_score - self.min_delta
        except TypeError:
            # If types are incompatible, be conservative and return False
            return False

    def _is_better_max(self, score: float, best_score: float) -> bool:
        """Check if score is better when maximizing."""
        try:
            return score > best_score + self.min_delta
        except TypeError:
            # If types are incompatible, be conservative and return False
            return False

    def __call__(self, score: float, epoch: int) -> bool:
        """Check if training should stop early.

        Args:
            score: Current metric score
            epoch: Current epoch number

        Returns:
            True if training should stop, False otherwise
        """
        if not self.enabled:
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
            return False
        else:
            self.counter += 1
            logger.info(f"Early stopping: no improvement for {self.counter}/{self.patience} epochs")

            if self.counter >= self.patience:
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
