"""Production training engine for PlantGuard with robust training loop and error handling.

This module provides the ProductionTrainer class that implements a production-ready
training pipeline with checkpoint management, error recovery, and comprehensive monitoring.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.cuda.amp import GradScaler, autocast
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from .checkpoint_manager import CheckpointData, CheckpointManager
from .config import TrainingConfig
from .dataset_manager import DatasetManager
from .error_handler import TrainingErrorHandler
from .optimizers import TrainingComponents, create_training_components
from .resource_manager import get_resource_manager

logger = logging.getLogger(__name__)


@dataclass
class TrainingState:
    """Training state for persistence and resumption."""

    epoch: int = 0
    step: int = 0
    best_val_loss: float = float("inf")
    best_val_accuracy: float = 0.0
    best_epoch: int = 0
    train_losses: list[float] = field(default_factory=list)
    val_losses: list[float] = field(default_factory=list)
    val_accuracies: list[float] = field(default_factory=list)
    learning_rates: list[float] = field(default_factory=list)
    total_training_time: float = 0.0
    last_checkpoint_path: str | None = None


@dataclass
class TrainingResult:
    """Result of training process."""

    success: bool
    final_epoch: int
    best_val_loss: float
    best_val_accuracy: float
    best_epoch: int
    total_training_time: float
    model_path: str | None = None
    error_message: str | None = None
    training_history: dict[str, list[float]] = field(default_factory=dict)


class ProductionTrainer:
    """Production-ready trainer with robust training loop and error handling."""

    def __init__(
        self,
        config: TrainingConfig,
        dataset_manager: DatasetManager | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize ProductionTrainer.

        Args:
            config: Training configuration
            dataset_manager: Dataset manager instance
            output_dir: Output directory for models and logs
        """
        self.config = config
        self.dataset_manager = dataset_manager or DatasetManager()
        self.output_dir = (
            Path(output_dir or "runs") / f"{config.experiment_name}_{int(time.time())}"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.model: nn.Module | None = None
        self.train_loader: DataLoader | None = None
        self.val_loader: DataLoader | None = None
        self.training_components: TrainingComponents | None = None
        self.scaler: GradScaler | None = None
        self.writer: SummaryWriter | None = None

        # Training state
        self.state = TrainingState()
        self.device = torch.device("cpu")

        # Resource manager
        self.resource_manager = get_resource_manager()

        # Checkpoint manager
        self.checkpoint_manager = CheckpointManager(
            checkpoint_dir=self.output_dir / "checkpoints",
            max_checkpoints=config.max_checkpoints_to_keep,
            save_frequency=config.save_every_n_epochs,
        )

        # Error handler
        self.error_handler = TrainingErrorHandler(
            log_dir=self.output_dir / "logs",
            enable_notifications=False,  # Can be enabled for production environments
        )

        # Setup logging
        self._setup_logging()

        logger.info(f"ProductionTrainer initialized with output directory: {self.output_dir}")

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_file = self.output_dir / "training.log"

        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(file_handler)

        logger.info("Logging setup complete")

    def setup_training(self) -> bool:
        """Setup training components and validate prerequisites.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            logger.info("Setting up training environment...")

            # Validate prerequisites
            if not self._validate_prerequisites():
                return False

            # Setup device
            self._setup_device()

            # Setup model
            if not self._setup_model():
                return False

            # Setup data loaders
            if not self._setup_data_loaders():
                return False

            # Setup training components
            self._setup_training_components()

            # Setup mixed precision
            self._setup_mixed_precision()

            # Setup tensorboard
            self._setup_tensorboard()

            # Save configuration
            self._save_config()

            logger.info("Training setup completed successfully")
            return True

        except Exception:
            logger.exception("Failed to setup training")
            return False

    def _validate_prerequisites(self) -> bool:
        """Validate training prerequisites.

        Returns:
            True if all prerequisites are met
        """
        logger.info("Validating training prerequisites...")

        # Check disk space (require at least 1GB free)
        try:
            import shutil

            free_space_gb = shutil.disk_usage(self.output_dir).free / (1024**3)
            if free_space_gb < 1.0:
                logger.error(
                    f"Insufficient disk space: {free_space_gb:.1f}GB available (minimum: 1GB)"
                )
                return False
            logger.info(f"Disk space check passed: {free_space_gb:.1f}GB available")
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")

        # Check memory availability
        resource_info = self.resource_manager.detect_resources()
        if resource_info.available_memory < 2.0:  # Require at least 2GB
            logger.error(
                f"Insufficient memory: {resource_info.available_memory:.1f}GB available "
                f"(minimum: 2GB)"
            )
            return False

        logger.info("Prerequisites validation passed")
        return True

    def _setup_device(self) -> None:
        """Setup training device."""
        if self.config.device == "auto":
            # Auto-detect best device
            resource_info = self.resource_manager.detect_resources()
            device_str = resource_info.device_type
        else:
            device_str = self.config.device

        self.device = torch.device(device_str)
        logger.info(f"Using device: {self.device}")

        # Log device information
        if self.device.type == "cuda":
            logger.info(f"CUDA device: {torch.cuda.get_device_name(self.device)}")
            cuda_memory_gb = torch.cuda.get_device_properties(self.device).total_memory / 1024**3
            logger.info(f"CUDA memory: {cuda_memory_gb:.1f}GB")
        elif self.device.type == "mps":
            logger.info("Using Apple Silicon GPU (MPS)")

    def _setup_model(self) -> bool:
        """Setup the training model.

        Returns:
            True if model setup successful
        """
        try:
            logger.info(f"Setting up {self.config.model_architecture} model...")

            # Import here to avoid circular imports
            from torchvision import models

            # Create model based on architecture
            if self.config.model_architecture == "resnet50":
                model = models.resnet50(pretrained=self.config.pretrained)
                # Modify final layer for our number of classes
                model.fc = nn.Linear(model.fc.in_features, self.config.num_classes)
                self.model = model
            elif self.config.model_architecture == "resnet18":
                model = models.resnet18(pretrained=self.config.pretrained)
                model.fc = nn.Linear(model.fc.in_features, self.config.num_classes)
                self.model = model
            else:
                msg = f"Unsupported architecture: {self.config.model_architecture}"
                raise ValueError(msg)

            # Add dropout if specified
            if self.config.dropout_rate > 0 and hasattr(self.model, "fc"):
                original_fc = self.model.fc
                if isinstance(original_fc, nn.Module):
                    self.model.fc = nn.Sequential(nn.Dropout(self.config.dropout_rate), original_fc)

            # Move model to device
            self.model = self.model.to(self.device)

            # Freeze backbone if specified
            if self.config.freeze_backbone:
                self._freeze_backbone()

            # Log model information
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            logger.info(
                f"Model created: {total_params:,} total parameters, {trainable_params:,} trainable"
            )

            return True

        except Exception:
            logger.exception("Failed to setup model")
            return False

    def _freeze_backbone(self) -> None:
        """Freeze backbone layers for transfer learning."""
        if self.model is None:
            return

        logger.info("Freezing backbone layers...")

        # Freeze all layers except the final classifier
        for name, param in self.model.named_parameters():
            if "fc" not in name:  # Don't freeze the final fully connected layer
                param.requires_grad = False

        frozen_params = sum(p.numel() for p in self.model.parameters() if not p.requires_grad)
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

        logger.info(f"Frozen {frozen_params:,} parameters, {trainable_params:,} remain trainable")

    def _setup_data_loaders(self) -> bool:
        """Setup training and validation data loaders.

        Returns:
            True if data loaders setup successful
        """
        try:
            logger.info("Setting up data loaders...")

            # Import here to avoid circular imports
            from torchvision.datasets import ImageFolder

            # Define transforms
            train_transforms = self._get_train_transforms()
            val_transforms = self._get_val_transforms()

            # Assume dataset is already prepared with train/val split
            dataset_dir = Path("data/processed/plantvillage")  # Default path
            train_dir = dataset_dir / "train"
            val_dir = dataset_dir / "val"

            if not train_dir.exists() or not val_dir.exists():
                logger.error(f"Dataset not found at {dataset_dir}. Please prepare dataset first.")
                return False

            # Create datasets
            train_dataset = ImageFolder(train_dir, transform=train_transforms)
            val_dataset = ImageFolder(val_dir, transform=val_transforms)

            logger.info(f"Train dataset: {len(train_dataset)} samples")
            logger.info(f"Validation dataset: {len(val_dataset)} samples")
            logger.info(f"Number of classes: {len(train_dataset.classes)}")

            # Optimize batch size if needed
            if hasattr(self.config, "_auto_batch_size") or self.config.batch_size == 32:
                optimal_batch_size = self.resource_manager.get_optimal_batch_size()
                self.config.batch_size = optimal_batch_size
                logger.info(f"Auto-optimized batch size: {optimal_batch_size}")

            # Create data loaders
            self.train_loader = DataLoader(
                train_dataset,
                batch_size=self.config.batch_size,
                shuffle=True,
                num_workers=self.config.num_workers,
                pin_memory=self.config.pin_memory,
                persistent_workers=self.config.persistent_workers and self.config.num_workers > 0,
            )

            self.val_loader = DataLoader(
                val_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                num_workers=self.config.num_workers,
                pin_memory=self.config.pin_memory,
                persistent_workers=self.config.persistent_workers and self.config.num_workers > 0,
            )

            # Save class names for later use
            self.class_names = train_dataset.classes
            class_to_idx_file = self.output_dir / "class_to_idx.json"
            with class_to_idx_file.open("w") as f:
                json.dump(train_dataset.class_to_idx, f, indent=2)

            logger.info("Data loaders setup completed")
            return True

        except Exception:
            logger.exception("Failed to setup data loaders")
            return False

    def _get_train_transforms(self) -> Any:
        """Get training data transforms."""
        from torchvision import transforms

        transform_list = []

        # Resize and crop
        transform_list.extend(
            [
                transforms.Resize(256),
                transforms.RandomCrop(224),
            ]
        )

        # Data augmentation
        if self.config.data_augmentation.enabled:
            if self.config.data_augmentation.horizontal_flip:
                transform_list.append(transforms.RandomHorizontalFlip())

            if self.config.data_augmentation.vertical_flip:
                transform_list.append(transforms.RandomVerticalFlip())

            if self.config.data_augmentation.rotation > 0:
                transform_list.append(
                    transforms.RandomRotation(self.config.data_augmentation.rotation)
                )

            if (
                self.config.data_augmentation.brightness > 0
                or self.config.data_augmentation.contrast > 0
            ):
                transform_list.append(
                    transforms.ColorJitter(
                        brightness=self.config.data_augmentation.brightness,
                        contrast=self.config.data_augmentation.contrast,
                    )
                )

        # Convert to tensor
        transform_list.append(transforms.ToTensor())

        # Normalization
        if self.config.data_augmentation.normalize:
            transform_list.append(
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],  # ImageNet means
                    std=[0.229, 0.224, 0.225],  # ImageNet stds
                )
            )

        return transforms.Compose(transform_list)

    def _get_val_transforms(self) -> Any:
        """Get validation data transforms."""
        from torchvision import transforms

        transform_list = [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
        ]

        if self.config.data_augmentation.normalize:
            transform_list.append(
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                )
            )

        return transforms.Compose(transform_list)

    def _setup_training_components(self) -> None:
        """Setup optimizer, scheduler, and early stopping."""
        logger.info("Setting up training components...")

        if self.model is None:
            raise RuntimeError("Model must be setup before training components")

        self.training_components = create_training_components(self.model, self.config)
        logger.info("Training components setup completed")

    def _setup_mixed_precision(self) -> None:
        """Setup mixed precision training if enabled."""
        if self.config.mixed_precision and self.device.type in ["cuda", "mps"]:
            self.scaler = GradScaler()
            logger.info("Mixed precision training enabled")
        else:
            self.scaler = None
            if self.config.mixed_precision:
                logger.warning("Mixed precision requested but not supported on current device")

    def _setup_tensorboard(self) -> None:
        """Setup TensorBoard logging."""
        log_dir = self.output_dir / "tensorboard"
        self.writer = SummaryWriter(log_dir)
        logger.info(f"TensorBoard logging setup: {log_dir}")

    def _save_config(self) -> None:
        """Save training configuration."""
        config_file = self.output_dir / "config.json"
        self.config.to_json(config_file)
        logger.info(f"Configuration saved to {config_file}")

    def train(self) -> TrainingResult:
        """Execute the training loop.

        Returns:
            TrainingResult with training outcomes
        """
        if not self.setup_training():
            return TrainingResult(
                success=False,
                final_epoch=0,
                best_val_loss=float("inf"),
                best_val_accuracy=0.0,
                best_epoch=0,
                total_training_time=0.0,
                error_message="Training setup failed",
            )

        logger.info("Starting training...")
        start_time = time.time()

        try:
            # Training loop
            for epoch in range(self.state.epoch, self.config.epochs):
                self.state.epoch = epoch
                epoch_start_time = time.time()

                # Train one epoch
                train_loss = self._train_epoch()

                # Validate
                val_loss, val_accuracy = self._validate_epoch()

                # Update learning rate
                if self.training_components:
                    self.training_components.step_scheduler(val_loss)
                    current_lr = self.training_components.get_current_lr()
                else:
                    current_lr = self.config.learning_rate

                # Update training state
                self.state.train_losses.append(train_loss)
                self.state.val_losses.append(val_loss)
                self.state.val_accuracies.append(val_accuracy)
                self.state.learning_rates.append(current_lr)

                # Check for best model
                if val_loss < self.state.best_val_loss:
                    self.state.best_val_loss = val_loss
                    self.state.best_val_accuracy = val_accuracy
                    self.state.best_epoch = epoch
                    self._save_best_model()

                # Log metrics
                epoch_time = time.time() - epoch_start_time
                self._log_epoch_metrics(
                    epoch, train_loss, val_loss, val_accuracy, current_lr, epoch_time
                )

                # Save checkpoint
                if (epoch + 1) % self.config.save_every_n_epochs == 0:
                    self._save_checkpoint_with_manager(epoch, val_loss, val_accuracy)

                # Check early stopping
                if self.training_components and self.training_components.check_early_stopping(
                    val_loss, epoch
                ):
                    logger.info(f"Early stopping triggered at epoch {epoch}")
                    break

            # Training completed
            total_time = time.time() - start_time
            self.state.total_training_time = total_time

            logger.info(f"Training completed in {total_time:.2f} seconds")
            logger.info(
                f"Best validation loss: {self.state.best_val_loss:.6f} "
                f"at epoch {self.state.best_epoch}"
            )
            logger.info(f"Best validation accuracy: {self.state.best_val_accuracy:.4f}")

            # Save final state
            self._save_training_state()

            return TrainingResult(
                success=True,
                final_epoch=self.state.epoch,
                best_val_loss=self.state.best_val_loss,
                best_val_accuracy=self.state.best_val_accuracy,
                best_epoch=self.state.best_epoch,
                total_training_time=total_time,
                model_path=str(self.output_dir / "best_model.pt"),
                training_history={
                    "train_loss": self.state.train_losses,
                    "val_loss": self.state.val_losses,
                    "val_accuracy": self.state.val_accuracies,
                    "learning_rate": self.state.learning_rates,
                },
            )

        except Exception as e:
            logger.exception("Training failed: %s", e)
            return TrainingResult(
                success=False,
                final_epoch=self.state.epoch,
                best_val_loss=self.state.best_val_loss,
                best_val_accuracy=self.state.best_val_accuracy,
                best_epoch=self.state.best_epoch,
                total_training_time=time.time() - start_time,
                error_message=str(e),
            )

        finally:
            # Cleanup
            if self.writer:
                self.writer.close()

    def _train_epoch(self) -> float:
        """Train for one epoch.

        Returns:
            Average training loss for the epoch
        """
        if self.model is None or self.train_loader is None or self.training_components is None:
            raise RuntimeError("Training components not properly initialized")

        self.model.train()
        total_loss = 0.0
        num_batches = 0

        # Progress bar
        pbar = tqdm(self.train_loader, desc=f"Epoch {self.state.epoch + 1}/{self.config.epochs}")

        for batch_idx, (batch_data, batch_target) in enumerate(pbar):
            data, target = batch_data.to(self.device), batch_target.to(self.device)

            # Zero gradients
            self.training_components.zero_grad()

            # Forward pass with mixed precision
            if self.scaler is not None:
                with autocast():
                    output = self.model(data)
                    loss = nn.functional.cross_entropy(output, target)

                # Backward pass with gradient scaling
                self.scaler.scale(loss).backward()

                # Gradient accumulation
                if (batch_idx + 1) % self.config.gradient_accumulation_steps == 0:
                    # Gradient clipping
                    if self.config.gradient_clip_norm is not None:
                        self.scaler.unscale_(self.training_components.optimizer)
                        torch.nn.utils.clip_grad_norm_(
                            self.model.parameters(), self.config.gradient_clip_norm
                        )

                    self.scaler.step(self.training_components.optimizer)
                    self.scaler.update()
                    self.training_components.zero_grad()
            else:
                # Standard forward pass
                output = self.model(data)
                loss = nn.functional.cross_entropy(output, target)

                # Backward pass
                loss.backward()

                # Gradient accumulation
                if (batch_idx + 1) % self.config.gradient_accumulation_steps == 0:
                    # Gradient clipping
                    if self.config.gradient_clip_norm is not None:
                        torch.nn.utils.clip_grad_norm_(
                            self.model.parameters(), self.config.gradient_clip_norm
                        )

                    self.training_components.step_optimizer()
                    self.training_components.zero_grad()

            total_loss += loss.item()
            num_batches += 1
            self.state.step += 1

            # Update progress bar
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

            # Log batch metrics
            if self.state.step % self.config.log_every_n_steps == 0 and self.writer:
                self.writer.add_scalar("Loss/Train_Batch", loss.item(), self.state.step)
                self.writer.add_scalar(
                    "Learning_Rate",
                    self.training_components.get_current_lr(),
                    self.state.step,
                )

        return total_loss / num_batches if num_batches > 0 else 0.0

    def _validate_epoch(self) -> tuple[float, float]:
        """Validate for one epoch.

        Returns:
            Tuple of (average validation loss, validation accuracy)
        """
        if self.model is None or self.val_loader is None:
            raise RuntimeError("Validation components not properly initialized")

        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for batch_data, batch_target in tqdm(self.val_loader, desc="Validation", leave=False):
                data, target = batch_data.to(self.device), batch_target.to(self.device)

                # Forward pass
                if self.scaler is not None:
                    with autocast():
                        output = self.model(data)
                        loss = nn.functional.cross_entropy(output, target)
                else:
                    output = self.model(data)
                    loss = nn.functional.cross_entropy(output, target)

                total_loss += loss.item()

                # Calculate accuracy
                _, predicted = torch.max(output.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()

        avg_loss = total_loss / len(self.val_loader)
        accuracy = correct / total if total > 0 else 0.0

        return avg_loss, accuracy

    def _log_epoch_metrics(
        self,
        epoch: int,
        train_loss: float,
        val_loss: float,
        val_accuracy: float,
        learning_rate: float,
        epoch_time: float,
    ) -> None:
        """Log metrics for the epoch."""
        # Console logging
        logger.info(
            f"Epoch {epoch + 1}/{self.config.epochs} - "
            f"Train Loss: {train_loss:.6f}, "
            f"Val Loss: {val_loss:.6f}, "
            f"Val Acc: {val_accuracy:.4f}, "
            f"LR: {learning_rate:.8f}, "
            f"Time: {epoch_time:.2f}s"
        )

        # TensorBoard logging
        if self.writer:
            self.writer.add_scalar("Loss/Train", train_loss, epoch)
            self.writer.add_scalar("Loss/Validation", val_loss, epoch)
            self.writer.add_scalar("Accuracy/Validation", val_accuracy, epoch)
            self.writer.add_scalar("Learning_Rate_Epoch", learning_rate, epoch)
            self.writer.add_scalar("Time/Epoch", epoch_time, epoch)

    def _save_best_model(self) -> None:
        """Save the best model."""
        if self.model is None:
            return

        best_model_path = self.output_dir / "best_model.pt"
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "epoch": self.state.epoch,
                "best_val_loss": self.state.best_val_loss,
                "best_val_accuracy": self.state.best_val_accuracy,
                "config": asdict(self.config),
                "class_names": getattr(self, "class_names", []),
            },
            best_model_path,
        )

        logger.info(f"Best model saved: {best_model_path}")

    def _save_checkpoint_with_manager(
        self, epoch: int, val_loss: float, val_accuracy: float
    ) -> None:
        """Save training checkpoint using checkpoint manager."""
        if self.model is None or self.training_components is None:
            return

        try:
            # Prepare training state
            training_state = asdict(self.state)

            # Save checkpoint using manager
            checkpoint_data = CheckpointData(
                optimizer_state=self.training_components.get_state_dict().get("optimizer", {}),
                scheduler_state=self.training_components.get_state_dict().get("scheduler"),
                training_state=training_state,
                config=asdict(self.config),
                epoch=epoch,
                step=self.state.step,
                val_loss=val_loss,
                val_accuracy=val_accuracy,
                training_time=self.state.total_training_time,
                scaler_state=self.scaler.state_dict() if self.scaler else None,
            )
            checkpoint_path = self.checkpoint_manager.save_checkpoint(
                model=self.model,
                checkpoint_data=checkpoint_data,
            )

            if checkpoint_path:
                self.state.last_checkpoint_path = str(checkpoint_path)
                logger.info(f"Checkpoint saved via manager: {checkpoint_path}")
            else:
                logger.warning("Checkpoint not saved (conditions not met)")

        except Exception:
            logger.exception("Failed to save checkpoint via manager")
            # Fallback to legacy checkpoint saving
            self._save_checkpoint_legacy(epoch)

    def _save_checkpoint_legacy(self, epoch: int) -> None:
        """Legacy checkpoint saving method as fallback."""
        if self.model is None or self.training_components is None:
            return

        checkpoint_path = self.output_dir / f"checkpoint_epoch_{epoch + 1}.pt"

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "training_components": self.training_components.get_state_dict(),
            "training_state": asdict(self.state),
            "config": asdict(self.config),
            "scaler_state_dict": self.scaler.state_dict() if self.scaler else None,
        }

        torch.save(checkpoint, checkpoint_path)
        self.state.last_checkpoint_path = str(checkpoint_path)

        logger.info(f"Legacy checkpoint saved: {checkpoint_path}")

    def _cleanup_old_checkpoints(self) -> None:
        """Remove old checkpoints to save disk space."""
        # This is now handled by the checkpoint manager
        try:
            corrupted_count = self.checkpoint_manager.cleanup_corrupted_checkpoints()
            if corrupted_count > 0:
                logger.info(f"Cleaned up {corrupted_count} corrupted checkpoints")
        except Exception as e:
            logger.warning(f"Failed to cleanup corrupted checkpoints: {e}")

    def _save_training_state(self) -> None:
        """Save final training state."""
        state_file = self.output_dir / "training_state.json"
        with state_file.open("w") as f:
            json.dump(asdict(self.state), f, indent=2, default=str)

        logger.info(f"Training state saved: {state_file}")

    def resume_from_checkpoint(self, checkpoint_path: Path | str) -> TrainingResult:
        """Resume training from a checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            TrainingResult with training outcomes
        """
        checkpoint_path = Path(checkpoint_path)

        if not checkpoint_path.exists():
            logger.error(f"Checkpoint file not found: {checkpoint_path}")
            return TrainingResult(
                success=False,
                final_epoch=0,
                best_val_loss=float("inf"),
                best_val_accuracy=0.0,
                best_epoch=0,
                total_training_time=0.0,
                error_message=f"Checkpoint file not found: {checkpoint_path}",
            )

        try:
            logger.info(f"Resuming training from checkpoint: {checkpoint_path}")

            # Load checkpoint using manager
            checkpoint = self.checkpoint_manager.load_checkpoint(checkpoint_path)

            if checkpoint is None:
                return TrainingResult(
                    success=False,
                    final_epoch=0,
                    best_val_loss=float("inf"),
                    best_val_accuracy=0.0,
                    best_epoch=0,
                    total_training_time=0.0,
                    error_message="Failed to load checkpoint or checkpoint is corrupted",
                )

            # Setup training (this will create model and components)
            if not self.setup_training():
                return TrainingResult(
                    success=False,
                    final_epoch=0,
                    best_val_loss=float("inf"),
                    best_val_accuracy=0.0,
                    best_epoch=0,
                    total_training_time=0.0,
                    error_message="Failed to setup training for resumption",
                )

            # Restore model state
            if self.model is not None:
                self.model.load_state_dict(checkpoint["model_state_dict"])
                logger.info("Model state restored from checkpoint")

            # Restore training components
            if self.training_components is not None and "training_components" in checkpoint:
                self.training_components.load_state_dict(checkpoint["training_components"])
                logger.info("Training components state restored from checkpoint")

            # Restore scaler state
            if (
                self.scaler is not None
                and "scaler_state_dict" in checkpoint
                and checkpoint["scaler_state_dict"]
            ):
                self.scaler.load_state_dict(checkpoint["scaler_state_dict"])
                logger.info("Mixed precision scaler state restored from checkpoint")

            # Restore training state
            if "training_state" in checkpoint:
                state_dict = checkpoint["training_state"]
                self.state.epoch = state_dict.get("epoch", 0)
                self.state.step = state_dict.get("step", 0)
                self.state.best_val_loss = state_dict.get("best_val_loss", float("inf"))
                self.state.best_val_accuracy = state_dict.get("best_val_accuracy", 0.0)
                self.state.best_epoch = state_dict.get("best_epoch", 0)
                self.state.train_losses = state_dict.get("train_losses", [])
                self.state.val_losses = state_dict.get("val_losses", [])
                self.state.val_accuracies = state_dict.get("val_accuracies", [])
                self.state.learning_rates = state_dict.get("learning_rates", [])
                self.state.total_training_time = state_dict.get("total_training_time", 0.0)
                logger.info(f"Training state restored: resuming from epoch {self.state.epoch + 1}")

            # Continue training from the next epoch
            self.state.epoch += 1

            # Execute training loop
            return self.train()

        except Exception as e:
            logger.exception("Failed to resume from checkpoint: %s", e)
            return TrainingResult(
                success=False,
                final_epoch=0,
                best_val_loss=float("inf"),
                best_val_accuracy=0.0,
                best_epoch=0,
                total_training_time=0.0,
                error_message=f"Failed to resume from checkpoint: {e}",
            )

    def _validate_checkpoint(self, checkpoint: dict[str, Any]) -> bool:
        """Validate checkpoint integrity and compatibility.

        Args:
            checkpoint: Loaded checkpoint dictionary

        Returns:
            True if checkpoint is valid and compatible
        """
        required_keys = ["epoch", "model_state_dict", "config"]

        # Check required keys
        for key in required_keys:
            if key not in checkpoint:
                logger.error(f"Missing required key in checkpoint: {key}")
                return False

        # Check model state dict
        model_state = checkpoint["model_state_dict"]
        if not isinstance(model_state, dict) or not model_state:
            logger.error("Invalid model state dict in checkpoint")
            return False

        # Check config compatibility
        checkpoint_config = checkpoint["config"]
        if not isinstance(checkpoint_config, dict):
            logger.error("Invalid config in checkpoint")
            return False

        # Validate critical config parameters match
        critical_params = ["model_architecture", "num_classes"]
        for param in critical_params:
            if param in checkpoint_config:
                checkpoint_value = checkpoint_config[param]
                current_value = getattr(self.config, param)
                if checkpoint_value != current_value:
                    logger.error(
                        f"Config mismatch for {param}: checkpoint={checkpoint_value}, "
                        f"current={current_value}"
                    )
                    return False

        logger.info("Checkpoint validation passed")
        return True

    def evaluate_model(self, model_path: Path | str) -> dict[str, Any]:
        """Evaluate a trained model.

        Args:
            model_path: Path to model file

        Returns:
            Dictionary with evaluation results
        """
        model_path = Path(model_path)

        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return {"error": f"Model file not found: {model_path}"}

        try:
            logger.info(f"Evaluating model: {model_path}")

            # Load model
            checkpoint = torch.load(model_path, map_location=self.device)  # nosec B614

            # Setup model if not already done
            if self.model is None and not self._setup_model():
                return {"error": "Failed to setup model for evaluation"}

            # Load model state
            if self.model is not None:
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.model.eval()

            # Setup data loader if not already done
            if self.val_loader is None and not self._setup_data_loaders():
                return {"error": "Failed to setup data loaders for evaluation"}

            # Run evaluation
            val_loss, val_accuracy = self._validate_epoch()

            # Calculate per-class metrics
            class_metrics = self._calculate_class_metrics()

            results = {
                "validation_loss": val_loss,
                "validation_accuracy": val_accuracy,
                "class_metrics": class_metrics,
                "model_path": str(model_path),
                "evaluation_time": time.time(),
            }

            # Add checkpoint metadata if available
            if "best_val_loss" in checkpoint:
                results["training_best_val_loss"] = checkpoint["best_val_loss"]
            if "best_val_accuracy" in checkpoint:
                results["training_best_val_accuracy"] = checkpoint["best_val_accuracy"]
            if "epoch" in checkpoint:
                results["training_epoch"] = checkpoint["epoch"]

            logger.info(
                f"Model evaluation completed: accuracy={val_accuracy:.4f}, loss={val_loss:.6f}"
            )
            return results

        except Exception as e:
            logger.exception("Model evaluation failed")
            return {"error": f"Model evaluation failed: {e}"}

    def _calculate_class_metrics(self) -> dict[str, Any]:
        """Calculate per-class evaluation metrics.

        Returns:
            Dictionary with per-class metrics
        """
        if self.model is None or self.val_loader is None:
            return {}

        import numpy as np
        from sklearn.metrics import classification_report, confusion_matrix

        self.model.eval()
        all_predictions: list[int] = []
        all_targets: list[int] = []

        with torch.no_grad():
            for batch_data, batch_target in self.val_loader:
                data = batch_data.to(self.device)
                target = batch_target

                if self.scaler is not None:
                    with autocast():
                        output = self.model(data)
                else:
                    output = self.model(data)

                _, predicted = torch.max(output, 1)

                all_predictions.extend(predicted.cpu().numpy())
                all_targets.extend(target.numpy())

        # Convert to numpy arrays
        y_true = np.array(all_targets)
        y_pred = np.array(all_predictions)

        # Calculate confusion matrix
        cm = confusion_matrix(y_true, y_pred)

        # Calculate classification report
        class_names = getattr(
            self, "class_names", [f"class_{i}" for i in range(self.config.num_classes)]
        )
        report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)

        return {
            "confusion_matrix": cm.tolist(),
            "classification_report": report,
            "class_names": class_names,
        }

    def export_model(self, model_path: Path | str, export_format: str = "pytorch") -> Path | None:
        """Export model for deployment.

        Args:
            model_path: Path to model file
            export_format: Export format ('pytorch', 'onnx', 'torchscript')

        Returns:
            Path to exported model or None if failed
        """
        model_path = Path(model_path)

        # Early validation checks
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return None

        try:
            logger.info(f"Exporting model to {export_format} format...")

            # Load model
            checkpoint = torch.load(model_path, map_location=self.device)  # nosec B614

            # Setup model if needed
            if self.model is None and not self._setup_model():
                logger.error("Failed to setup model for export")
                return None

            # Load model state
            if self.model is not None:
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.model.eval()

            export_path = self.output_dir / f"exported_model.{export_format.lower()}"
            export_success = self._perform_export(
                export_format, export_path, checkpoint, self.model
            )

            if export_success:
                logger.info(f"Model exported successfully: {export_path}")
                return export_path
            else:
                return None

        except Exception:
            logger.exception("Model export failed")
            return None

    def _perform_export(
        self, export_format: str, export_path: Path, checkpoint: dict, model: torch.nn.Module | None
    ) -> bool:
        """Perform the actual model export based on format."""
        format_lower = export_format.lower()

        if format_lower == "pytorch":
            return self._export_pytorch(export_path, checkpoint, model)
        elif format_lower == "torchscript":
            return self._export_torchscript(export_path, model)
        elif format_lower == "onnx":
            return self._export_onnx(export_path, model)
        else:
            logger.error(f"Unsupported export format: {export_format}")
            return False

    def _export_pytorch(
        self, export_path: Path, checkpoint: dict, model: torch.nn.Module | None
    ) -> bool:
        """Export as PyTorch model."""
        if model is None:
            logger.error("Cannot export model: model is None")
            return False

        export_dict = {
            "model_state_dict": model.state_dict(),
            "config": checkpoint.get("config", asdict(self.config)),
            "class_names": checkpoint.get("class_names", getattr(self, "class_names", [])),
            "export_time": time.time(),
        }
        torch.save(export_dict, export_path)
        return True

    def _export_torchscript(self, export_path: Path, model: torch.nn.Module | None) -> bool:
        """Export as TorchScript."""
        dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
        traced_model = torch.jit.trace(model, dummy_input)
        traced_model.save(str(export_path))
        return True

    def _export_onnx(self, export_path: Path, model: torch.nn.Module | None) -> bool:
        """Export as ONNX."""
        try:
            import torch.onnx as torch_onnx

            dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
            if model is not None:
                torch_onnx.export(
                    model,
                    (dummy_input,),
                    str(export_path),
                    export_params=True,
                    opset_version=11,
                    do_constant_folding=True,
                    input_names=["input"],
                    output_names=["output"],
                    dynamic_axes={
                        "input": {0: "batch_size"},
                        "output": {0: "batch_size"},
                    },
                )
            return True
        except ImportError:
            logger.error("ONNX export requires onnx package: pip install onnx")
            return False

    def get_training_summary(self) -> dict[str, Any]:
        """Get summary of training progress and results.

        Returns:
            Dictionary with training summary
        """
        return {
            "experiment_name": self.config.experiment_name,
            "current_epoch": self.state.epoch,
            "total_epochs": self.config.epochs,
            "best_val_loss": self.state.best_val_loss,
            "best_val_accuracy": self.state.best_val_accuracy,
            "best_epoch": self.state.best_epoch,
            "total_training_time": self.state.total_training_time,
            "output_directory": str(self.output_dir),
            "last_checkpoint": self.state.last_checkpoint_path,
            "training_history_length": len(self.state.train_losses),
            "device": str(self.device),
            "model_architecture": self.config.model_architecture,
            "batch_size": self.config.batch_size,
            "learning_rate": self.config.learning_rate,
            "optimizer": self.config.optimizer,
        }

    def cleanup(self) -> None:
        """Cleanup resources and temporary files."""
        try:
            # Close TensorBoard writer
            if self.writer:
                self.writer.close()
                self.writer = None

            # Clear CUDA cache if using GPU
            if self.device.type == "cuda":
                torch.cuda.empty_cache()

            # Clear model from memory
            self.model = None
            self.training_components = None
            self.scaler = None

            logger.info("Training resources cleaned up")

        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def find_latest_checkpoint(self) -> Path | None:
        """Find the latest checkpoint for resumption.

        Returns:
            Path to latest checkpoint or None if no checkpoints found
        """
        return self.checkpoint_manager.find_latest_checkpoint()

    def find_best_checkpoint(self, metric: str = "val_loss") -> Path | None:
        """Find the best checkpoint based on specified metric.

        Args:
            metric: Metric to use for selection ('val_loss' or 'val_accuracy')

        Returns:
            Path to best checkpoint or None if no checkpoints found
        """
        return self.checkpoint_manager.find_best_checkpoint(metric)

    def list_checkpoints(self) -> list[dict[str, Any]]:
        """List all available checkpoints.

        Returns:
            List of checkpoint information dictionaries
        """
        checkpoints = self.checkpoint_manager.list_checkpoints()
        return [
            {
                "checkpoint_id": cp.checkpoint_id,
                "epoch": cp.epoch,
                "val_loss": cp.best_val_loss,
                "val_accuracy": cp.best_val_accuracy,
                "training_time": cp.training_time,
                "file_size_mb": cp.file_size_bytes / (1024**2),
                "timestamp": cp.timestamp,
            }
            for cp in checkpoints
        ]

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to delete

        Returns:
            True if deleted successfully
        """
        return self.checkpoint_manager.delete_checkpoint(checkpoint_id)

    def create_checkpoint_backup(self, backup_dir: Path | str) -> bool:
        """Create backup of all checkpoints.

        Args:
            backup_dir: Directory to store backup

        Returns:
            True if backup successful
        """
        return self.checkpoint_manager.create_backup(backup_dir)

    def restore_checkpoint_backup(self, backup_dir: Path | str) -> bool:
        """Restore checkpoints from backup.

        Args:
            backup_dir: Directory containing backup

        Returns:
            True if restore successful
        """
        return self.checkpoint_manager.restore_from_backup(backup_dir)

    def get_checkpoint_summary(self) -> dict[str, Any]:
        """Get summary of all checkpoints.

        Returns:
            Dictionary with checkpoint summary
        """
        return self.checkpoint_manager.export_checkpoint_summary()

    def auto_resume_training(self) -> TrainingResult:
        """Automatically resume training from the latest checkpoint.

        Returns:
            TrainingResult with training outcomes
        """
        latest_checkpoint = self.find_latest_checkpoint()

        if latest_checkpoint is None:
            logger.info("No checkpoints found, starting fresh training")
            return self.train()

        logger.info(f"Auto-resuming from latest checkpoint: {latest_checkpoint}")
        return self.resume_from_checkpoint(latest_checkpoint)

    def force_save_checkpoint(self, epoch: int | None = None) -> Path | None:
        """Force save a checkpoint regardless of save conditions.

        Args:
            epoch: Epoch number (uses current epoch if None)

        Returns:
            Path to saved checkpoint or None if failed
        """
        if self.model is None or self.training_components is None:
            logger.error("Cannot save checkpoint: model or training components not initialized")
            return None

        epoch = epoch if epoch is not None else self.state.epoch

        # Get current validation metrics (run validation if needed)
        if self.val_loader is not None:
            val_loss, val_accuracy = self._validate_epoch()
        else:
            val_loss, val_accuracy = (
                self.state.best_val_loss,
                self.state.best_val_accuracy,
            )

        try:
            checkpoint_data = CheckpointData(
                optimizer_state=self.training_components.get_state_dict().get("optimizer", {}),
                scheduler_state=self.training_components.get_state_dict().get("scheduler"),
                training_state=asdict(self.state),
                config=asdict(self.config),
                epoch=epoch,
                step=self.state.step,
                val_loss=val_loss,
                val_accuracy=val_accuracy,
                training_time=self.state.total_training_time,
                scaler_state=self.scaler.state_dict() if self.scaler else None,
            )
            checkpoint_path = self.checkpoint_manager.save_checkpoint(
                model=self.model,
                checkpoint_data=checkpoint_data,
                force_save=True,
            )

            if checkpoint_path:
                logger.info(f"Forced checkpoint save successful: {checkpoint_path}")
            else:
                logger.error("Forced checkpoint save failed")

            return checkpoint_path

        except Exception:
            logger.exception("Failed to force save checkpoint")
            return None

    def _train_epoch_with_recovery(self) -> float:
        """Train for one epoch with error recovery.

        Returns:
            Average training loss for the epoch
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return self._train_epoch()
            except Exception as e:
                retry_count += 1
                logger.warning(f"Training epoch failed (attempt {retry_count}/{max_retries}): {e}")

                # Handle the error
                context = {
                    "trainer": self,
                    "model": self.model,
                    "config": self.config,
                    "epoch": self.state.epoch,
                    "retry_count": retry_count,
                }

                recovery_successful = self.error_handler.handle_error(
                    e, context, self.state.epoch, self.state.step
                )

                if not recovery_successful and retry_count >= max_retries:
                    logger.error("Failed to recover from training epoch error after all retries")
                    raise
                elif recovery_successful:
                    logger.info("Recovered from training epoch error, retrying...")
                    continue
                else:
                    logger.info(f"Recovery attempted, retrying ({retry_count}/{max_retries})")
                    time.sleep(1)  # Brief pause before retry

        # This should not be reached, but just in case
        raise RuntimeError("Training epoch failed after all recovery attempts")

    def _validate_epoch_with_recovery(self) -> tuple[float, float]:
        """Validate for one epoch with error recovery.

        Returns:
            Tuple of (average validation loss, validation accuracy)
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return self._validate_epoch()
            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"Validation epoch failed (attempt {retry_count}/{max_retries}): {e}"
                )

                # Handle the error
                context = {
                    "trainer": self,
                    "model": self.model,
                    "config": self.config,
                    "epoch": self.state.epoch,
                    "retry_count": retry_count,
                }

                recovery_successful = self.error_handler.handle_error(
                    e, context, self.state.epoch, self.state.step
                )

                if not recovery_successful and retry_count >= max_retries:
                    logger.error("Failed to recover from validation epoch error after all retries")
                    raise
                elif recovery_successful:
                    logger.info("Recovered from validation epoch error, retrying...")
                    continue
                else:
                    logger.info(f"Recovery attempted, retrying ({retry_count}/{max_retries})")
                    time.sleep(1)  # Brief pause before retry

        # This should not be reached, but just in case
        raise RuntimeError("Validation epoch failed after all recovery attempts")

    def train_with_error_recovery(self) -> TrainingResult:
        """Execute training with comprehensive error recovery.

        Returns:
            TrainingResult with training outcomes
        """
        if not self.setup_training():
            return self._create_failed_result("Training setup failed", 0.0)

        logger.info("Starting training with error recovery...")
        start_time = time.time()

        try:
            self._run_training_loop()
            return self._create_success_result(start_time)

        except Exception as e:
            logger.exception("Training failed: %s", e)
            self._export_error_report_safe()
            return self._create_failed_result(str(e), time.time() - start_time)

        finally:
            self._cleanup_training()

    def _run_training_loop(self) -> None:
        """Run the main training loop with error recovery."""
        for epoch in range(self.state.epoch, self.config.epochs):
            self.state.epoch = epoch
            epoch_start_time = time.time()

            if self._process_epoch_with_recovery(epoch, epoch_start_time):
                break  # Early stopping triggered

    def _process_epoch_with_recovery(self, epoch: int, epoch_start_time: float) -> bool:
        """Process a single epoch with error recovery.

        Returns:
            True if early stopping was triggered, False otherwise
        """
        try:
            return self._process_single_epoch(epoch, epoch_start_time)
        except Exception as e:
            return self._handle_epoch_error(e, epoch)

    def _process_single_epoch(self, epoch: int, epoch_start_time: float) -> bool:
        """Process a single training epoch.

        Returns:
            True if early stopping was triggered, False otherwise
        """
        # Train and validate
        train_loss = self._train_epoch_with_recovery()
        val_loss, val_accuracy = self._validate_epoch_with_recovery()

        # Update learning rate and state
        current_lr = self._update_learning_rate(val_loss)
        self._update_training_state(train_loss, val_loss, val_accuracy, current_lr)

        # Check for best model and save if needed
        self._check_and_save_best_model(val_loss, val_accuracy, epoch)

        # Log metrics
        epoch_time = time.time() - epoch_start_time
        self._log_epoch_metrics(epoch, train_loss, val_loss, val_accuracy, current_lr, epoch_time)

        # Save checkpoint if needed
        self._save_checkpoint_if_needed(epoch, val_loss, val_accuracy)

        # Check early stopping
        return self._check_early_stopping(val_loss, epoch)

    def _update_learning_rate(self, val_loss: float) -> float:
        """Update learning rate and return current rate."""
        if self.training_components:
            self.training_components.step_scheduler(val_loss)
            return self.training_components.get_current_lr()
        return self.config.learning_rate

    def _update_training_state(
        self, train_loss: float, val_loss: float, val_accuracy: float, current_lr: float
    ) -> None:
        """Update training state with current metrics."""
        self.state.train_losses.append(train_loss)
        self.state.val_losses.append(val_loss)
        self.state.val_accuracies.append(val_accuracy)
        self.state.learning_rates.append(current_lr)

    def _check_and_save_best_model(self, val_loss: float, val_accuracy: float, epoch: int) -> None:
        """Check if current model is best and save if so."""
        if val_loss < self.state.best_val_loss:
            self.state.best_val_loss = val_loss
            self.state.best_val_accuracy = val_accuracy
            self.state.best_epoch = epoch
            self._save_best_model()

    def _save_checkpoint_if_needed(self, epoch: int, val_loss: float, val_accuracy: float) -> None:
        """Save checkpoint if conditions are met."""
        if (epoch + 1) % self.config.save_every_n_epochs == 0:
            try:
                self._save_checkpoint_with_manager(epoch, val_loss, val_accuracy)
            except Exception as e:
                logger.warning(f"Checkpoint save failed: {e}")

    def _check_early_stopping(self, val_loss: float, epoch: int) -> bool:
        """Check if early stopping should be triggered."""
        if self.training_components and self.training_components.check_early_stopping(
            val_loss, epoch
        ):
            logger.info(f"Early stopping triggered at epoch {epoch}")
            return True
        return False

    def _handle_epoch_error(self, error: Exception, epoch: int) -> bool:
        """Handle epoch-level errors with recovery."""
        context = {
            "trainer": self,
            "model": self.model,
            "config": self.config,
            "epoch": epoch,
        }

        recovery_successful = self.error_handler.handle_error(
            error, context, epoch, self.state.step
        )

        if not recovery_successful:
            logger.error(f"Failed to recover from error at epoch {epoch}, stopping training")
            raise error
        else:
            logger.info(f"Recovered from error at epoch {epoch}, continuing training")
            return False  # Continue training

    def _create_success_result(self, start_time: float) -> TrainingResult:
        """Create a successful training result."""
        total_time = time.time() - start_time
        self.state.total_training_time = total_time

        logger.info(f"Training completed in {total_time:.2f} seconds")
        logger.info(
            f"Best validation loss: {self.state.best_val_loss:.6f} at epoch {self.state.best_epoch}"
        )
        logger.info(f"Best validation accuracy: {self.state.best_val_accuracy:.4f}")

        self._save_training_state()
        self._export_error_report_safe()

        return TrainingResult(
            success=True,
            final_epoch=self.state.epoch,
            best_val_loss=self.state.best_val_loss,
            best_val_accuracy=self.state.best_val_accuracy,
            best_epoch=self.state.best_epoch,
            total_training_time=total_time,
            model_path=str(self.output_dir / "best_model.pt"),
            training_history={
                "train_loss": self.state.train_losses,
                "val_loss": self.state.val_losses,
                "val_accuracy": self.state.val_accuracies,
                "learning_rate": self.state.learning_rates,
            },
        )

    def _create_failed_result(self, error_message: str, training_time: float) -> TrainingResult:
        """Create a failed training result."""
        return TrainingResult(
            success=False,
            final_epoch=self.state.epoch,
            best_val_loss=self.state.best_val_loss,
            best_val_accuracy=self.state.best_val_accuracy,
            best_epoch=self.state.best_epoch,
            total_training_time=training_time,
            error_message=error_message,
        )

    def _export_error_report_safe(self) -> None:
        """Safely export error report."""
        try:
            error_report_path = self.output_dir / "error_report.json"
            self.error_handler.export_error_report(error_report_path)
        except Exception as export_error:
            logger.debug("Failed to export error report: %s", export_error)

    def _cleanup_training(self) -> None:
        """Cleanup training resources."""
        if self.writer:
            self.writer.close()

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of training errors.

        Returns:
            Dictionary with error summary
        """
        return self.error_handler.get_error_summary()

    def export_error_report(self, output_file: Path | str) -> None:
        """Export detailed error report.

        Args:
            output_file: Path to output file
        """
        self.error_handler.export_error_report(output_file)

    def handle_manual_error_recovery(self, exception: Exception) -> bool:
        """Manually trigger error recovery for a given exception.

        Args:
            exception: Exception to recover from

        Returns:
            True if recovery was successful
        """
        context = {
            "trainer": self,
            "model": self.model,
            "config": self.config,
            "epoch": self.state.epoch,
        }

        return self.error_handler.handle_error(
            exception, context, self.state.epoch, self.state.step
        )
