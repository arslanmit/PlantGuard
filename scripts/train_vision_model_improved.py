"""Improved training script for PlantGuard vision model with better hyperparameters."""

import argparse
import json
import logging

# Add src to path for imports
import sys
import time
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.models import PlantDiseaseResNet50
from training.memory_limit import enforce_memory_limit
from training.monitor import TrainingMonitor

logger = logging.getLogger(__name__)


class ImprovedPlantVillageTrainer:
    """Improved trainer class with better hyperparameters and early stopping."""

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        device: torch.device,
        learning_rate: float = 0.0001,  # Lower LR for fine-tuning
        weight_decay: float = 1e-4,
        patience: int = 10,  # Early stopping patience
    ):
        """Initialize improved trainer.

        Args:
            model: PyTorch model to train
            train_loader: Training data loader
            val_loader: Validation data loader
            device: Device to train on
            learning_rate: Learning rate for optimizer (lower for fine-tuning)
            weight_decay: Weight decay for regularization
            patience: Early stopping patience
        """
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.patience = patience

        # Loss function and optimizer
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.AdamW(  # AdamW often works better than Adam
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )

        # Learning rate scheduler with cosine annealing
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=50, eta_min=1e-6)

        # Metrics tracking
        self.best_val_acc = 0.0
        self.best_val_loss = float("inf")
        self.patience_counter = 0
        self.train_losses: list[float] = []
        self.val_losses: list[float] = []
        self.val_accuracies: list[float] = []

    def train_epoch(self, monitor: TrainingMonitor | None = None) -> float:
        """Train for one epoch with improved progress tracking.

        Args:
            monitor: Optional TrainingMonitor for batch-level progress updates
        """
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        num_batches = len(self.train_loader)

        progress_bar = tqdm(self.train_loader, desc="Training")

        for batch_idx, (batch_images, batch_labels) in enumerate(progress_bar):
            images, labels = batch_images.to(self.device), batch_labels.to(self.device)

            # Zero gradients
            self.optimizer.zero_grad()

            # Forward pass
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)

            # Backward pass and optimization
            loss.backward()

            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

            self.optimizer.step()

            # Update metrics
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            # Batch-level progress update
            if monitor is not None:
                batch_acc = (predicted == labels).float().mean().item() * 100.0
                monitor.update_batch_progress(
                    loss=float(loss.item()),
                    accuracy=batch_acc,
                    learning_rate=self.optimizer.param_groups[0]["lr"],
                    batch_size=labels.size(0),
                )

            # Update progress bar
            current_acc = 100 * correct / total
            progress_bar.set_postfix(
                {
                    "Loss": f"{loss.item():.4f}",
                    "Avg Loss": f"{running_loss / (batch_idx + 1):.4f}",
                    "Acc": f"{current_acc:.2f}%",
                }
            )

        train_acc = 100 * correct / total
        avg_loss = running_loss / num_batches

        return avg_loss, train_acc

    def validate(
        self,
    ) -> tuple[float, float, list[int], list[int], torch.Tensor | None, torch.Tensor | None, torch.Tensor | None]:
        """Validate the model with improved metrics and collect predictions.

        Returns:
            avg_loss, accuracy, y_true_all, y_pred_all, sample_images, sample_outputs, sample_targets
        """
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        y_true_all: list[int] = []
        y_pred_all: list[int] = []
        sample_images: torch.Tensor | None = None
        sample_outputs: torch.Tensor | None = None
        sample_targets: torch.Tensor | None = None

        with torch.no_grad():
            progress_bar = tqdm(self.val_loader, desc="Validation")

            for batch_images, batch_labels in progress_bar:
                images, labels = batch_images.to(self.device), batch_labels.to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, labels)

                running_loss += loss.item()

                # Calculate accuracy
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

                # Collect predictions for confusion matrix
                y_true_all.extend(labels.detach().cpu().tolist())
                y_pred_all.extend(predicted.detach().cpu().tolist())

                # Save first batch for sample predictions
                if sample_images is None:
                    sample_images = images.detach().cpu()
                    sample_outputs = outputs.detach().cpu()
                    sample_targets = labels.detach().cpu()

                # Update progress bar
                accuracy = 100 * correct / total
                progress_bar.set_postfix(
                    {
                        "Loss": f"{loss.item():.4f}",
                        "Accuracy": f"{accuracy:.2f}%",
                    }
                )

        avg_loss = running_loss / len(self.val_loader)
        accuracy = 100 * correct / total

        return avg_loss, accuracy, y_true_all, y_pred_all, sample_images, sample_outputs, sample_targets

    def should_stop_early(self, val_loss: float) -> bool:
        """Check if training should stop early based on validation loss."""
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.patience_counter = 0
            return False
        else:
            self.patience_counter += 1
            return self.patience_counter >= self.patience

    def save_checkpoint(
        self,
        epoch: int,
        val_acc: float,
        save_path: Path,
        class_names: list[str],
        is_best: bool = False,
    ) -> None:
        """Save model checkpoint with additional metadata."""
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "val_acc": val_acc,
            "best_val_acc": self.best_val_acc,
            "class_names": class_names,
            "num_classes": len(class_names),
            "is_best": is_best,
        }

        torch.save(checkpoint, save_path)
        logger.info("Checkpoint saved to %s (Best: %s)", save_path, is_best)

    def train(
        self,
        num_epochs: int,
        save_dir: Path,
        class_names: list[str],
        monitor: TrainingMonitor,
    ) -> None:
        """Train the model with improved monitoring and early stopping."""
        logger.info("Starting improved training for %d epochs", num_epochs)
        logger.info("Early stopping patience: %d epochs", self.patience)

        # Setup monitor tracking
        monitor.setup_progress_tracking(total_epochs=num_epochs, steps_per_epoch=len(self.train_loader))

        for epoch in range(num_epochs):
            start_time = time.time()

            # Train for one epoch
            monitor.start_epoch_tracking(epoch)
            train_loss, train_acc = self.train_epoch(monitor=monitor)

            # Validate
            val_loss, val_acc, y_true_all, y_pred_all, sample_images, sample_outputs, sample_targets = self.validate()

            # Update learning rate
            self.scheduler.step()

            # Log metrics
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            self.val_accuracies.append(val_acc)

            # TrainingMonitor logging
            monitor.log_metrics(
                {
                    "Loss/Train": float(train_loss),
                    "Loss/Validation": float(val_loss),
                    "Accuracy/Train": float(train_acc),
                    "Accuracy/Validation": float(val_acc),
                },
                step=epoch,
                epoch=epoch,
            )

            # Log learning rate and histograms
            monitor.log_learning_rate(self.optimizer, step=epoch)
            monitor.log_histograms(self.model, step=epoch, log_gradients=False)

            # Log confusion matrix and sample predictions
            if y_true_all and y_pred_all:
                try:
                    monitor.log_confusion_matrix(y_true_all, y_pred_all, class_names, step=epoch)
                except Exception as e:
                    logger.warning("Failed to log confusion matrix: %s", e)

            if sample_images is not None and sample_outputs is not None and sample_targets is not None:
                try:
                    monitor.log_sample_predictions(sample_images, sample_outputs, sample_targets, class_names, step=epoch)
                except Exception as e:
                    logger.warning("Failed to log sample predictions: %s", e)

            # Finish epoch tracking
            monitor.finish_epoch_tracking(val_loss=float(val_loss), val_accuracy=float(val_acc), learning_rate=self.scheduler.get_last_lr()[0])

            # Save best model
            is_best = val_acc > self.best_val_acc
            if is_best:
                self.best_val_acc = val_acc
                best_model_path = save_dir / "best_model.pt"
                self.save_checkpoint(epoch, val_acc, best_model_path, class_names, is_best=True)

            # Save latest model
            latest_model_path = save_dir / "latest_model.pt"
            self.save_checkpoint(epoch, val_acc, latest_model_path, class_names)

            epoch_time = time.time() - start_time

            logger.info(
                "Epoch %d/%d - Train Loss: %.4f, Train Acc: %.2f%%, Val Loss: %.4f, Val Acc: %.2f%%, Time: %.2fs",
                epoch + 1,
                num_epochs,
                train_loss,
                train_acc,
                val_loss,
                val_acc,
                epoch_time,
            )

            # Early stopping check
            if self.should_stop_early(val_loss):
                logger.info(
                    "Early stopping triggered after %d epochs (patience: %d)",
                    epoch + 1,
                    self.patience,
                )
                break

        logger.info("Training completed. Best validation accuracy: %.2f%%", self.best_val_acc)


def create_improved_data_transforms() -> tuple[transforms.Compose, transforms.Compose]:
    """Create improved data transforms with better augmentation."""
    # Training transforms with moderate augmentation
    train_transform = transforms.Compose(
        [
            transforms.Resize((256, 256)),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),  # Reduced rotation
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.05),  # Reduced jitter
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # Validation transforms without augmentation
    val_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    return train_transform, val_transform


def create_improved_data_loaders(
    data_dir: Path,
    batch_size: int = 16,  # Increased from 8
    num_workers: int = 4,
) -> tuple[DataLoader, DataLoader, list[str]]:
    """Create improved data loaders with better batch size."""
    train_transform, val_transform = create_improved_data_transforms()

    # Load datasets
    train_dataset = datasets.ImageFolder(
        root=data_dir / "train",
        transform=train_transform,
    )

    val_dataset = datasets.ImageFolder(
        root=data_dir / "val",
        transform=val_transform,
    )

    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,  # Drop last incomplete batch
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    class_names = train_dataset.classes

    logger.info("Dataset loaded: %d train, %d val samples", len(train_dataset), len(val_dataset))
    logger.info("Number of classes: %d", len(class_names))
    logger.info("Batch size: %d", batch_size)

    return train_loader, val_loader, class_names


def main() -> None:
    """Main training function with improved defaults."""
    parser = argparse.ArgumentParser(description="Train PlantGuard vision model (improved)")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to dataset directory")
    parser.add_argument("--save_dir", type=str, default="data/models", help="Directory to save models")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")  # Increased
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")  # Increased
    parser.add_argument("--learning_rate", type=float, default=0.0001, help="Learning rate")  # Reduced
    parser.add_argument("--weight_decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    parser.add_argument("--device", type=str, default="auto", help="Device to use (cpu/cuda/auto)")
    parser.add_argument("--num_workers", type=int, default=4, help="Number of data loader workers")
    parser.add_argument("--log_dir", type=str, default="runs", help="Directory to store training runs and reports")
    parser.add_argument("--tensorboard_port", type=int, default=6006, help="Port for TensorBoard server")
    parser.add_argument("--launch_tensorboard", action="store_true", help="Auto-launch TensorBoard during training")
    parser.add_argument(
        "--memory_limit",
        type=str,
        default=None,
        help="Optional memory limit for the training process (e.g. 4GB or 4294967296)",
    )
    # Control use of ImageNet pretrained weights
    parser.add_argument("--pretrained", dest="pretrained", action="store_true", help="Use ImageNet pretrained weights")
    parser.add_argument("--no-pretrained", dest="pretrained", action="store_false", help="Do not use pretrained weights")
    parser.set_defaults(pretrained=True)

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse and enforce memory limit if provided (CLI takes precedence over env var)
    def _parse_size(val: str) -> int:
        if val is None:
            return 0
        v = str(val).strip().upper()
        try:
            if v.endswith("GB"):
                return int(float(v[:-2]) * 1024**3)
            if v.endswith("MB"):
                return int(float(v[:-2]) * 1024**2)
            return int(v)
        except Exception:
            logger.warning("Unable to parse memory limit value: %s", val)
            return 0

    cli_limit = _parse_size(args.memory_limit)
    if cli_limit > 0:
        enforce_memory_limit(cli_limit)
    else:
        # enforce_memory_limit will also read PLANTGUARD_TRAIN_MEMORY_LIMIT_BYTES if set
        enforce_memory_limit(None)

    # Setup device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    logger.info("Using device: %s", device)

    # Create directories
    data_dir = Path(args.data_dir)
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Create TrainingMonitor
    experiment_name = "plantguard_vision_improved"
    monitor = TrainingMonitor(
        experiment_name=experiment_name,
        log_dir=args.log_dir,
        auto_launch_tensorboard=args.launch_tensorboard,
        tensorboard_port=args.tensorboard_port,
    )
    logger.info("Training logs will be saved to: %s", monitor.experiment_dir)

    try:
        # Create data loaders
        train_loader, val_loader, class_names = create_improved_data_loaders(data_dir, args.batch_size, args.num_workers)

        # Save class names
        class_names_path = save_dir / "class_names.json"
        with class_names_path.open("w") as f:
            json.dump(class_names, f, indent=2)
        logger.info("Class names saved to %s", class_names_path)

        # Create model
        model = PlantDiseaseResNet50(num_classes=len(class_names), pretrained=args.pretrained)

        # Create improved trainer
        trainer = ImprovedPlantVillageTrainer(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            device=device,
            learning_rate=args.learning_rate,
            weight_decay=args.weight_decay,
            patience=args.patience,
        )

        # Train model
        trainer.train(args.epochs, save_dir, class_names, monitor)

        # Generate comprehensive training report
        try:
            hyperparameters = {
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "learning_rate": args.learning_rate,
                "weight_decay": args.weight_decay,
                "patience": args.patience,
                "optimizer": "AdamW",
                "scheduler": "CosineAnnealingLR",
            }
            dataset_info = {
                "num_train_samples": len(train_loader.dataset),
                "num_val_samples": len(val_loader.dataset),
                "num_classes": len(class_names),
                "class_names": class_names,
            }
            model_info = {"architecture": "PlantDiseaseResNet50"}
            system_info = {"device": str(device)}

            generated = monitor.save_training_report(
                model=model,
                model_info=model_info,
                dataset_info=dataset_info,
                hyperparameters=hyperparameters,
                system_info=system_info,
            )
            logger.info("Training report generated: %s", {k: str(v) for k, v in generated.items()})
        except Exception:
            logger.exception("Failed to generate training report")

    except Exception:
        logger.exception("Training failed")
        raise
    finally:
        # Suppress any errors during monitor cleanup; monitor close should be best-effort
        import contextlib

        with contextlib.suppress(Exception):
            monitor.close()


if __name__ == "__main__":
    main()
