"""Training script for PlantGuard vision model.

This script trains a ResNet50 model on the PlantVillage dataset for plant disease classification.
"""


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
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.models import PlantDiseaseResNet50

logger = logging.getLogger(__name__)


class PlantVillageTrainer:
    """Trainer class for PlantVillage dataset."""

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        device: torch.device,
        learning_rate: float = 0.001,
        weight_decay: float = 1e-4,
    ):
        """Initialize trainer.

        Args:
            model: PyTorch model to train
            train_loader: Training data loader
            val_loader: Validation data loader
            device: Device to train on
            learning_rate: Learning rate for optimizer
            weight_decay: Weight decay for regularization
        """
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device

        # Loss function and optimizer
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )

        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=10, gamma=0.1)

        # Metrics tracking
        self.best_val_acc = 0.0
        self.train_losses: list[float] = []
        self.val_losses: list[float] = []
        self.val_accuracies: list[float] = []

    def train_epoch(self) -> float:
        """Train for one epoch.

        Returns:
            Average training loss for the epoch
        """
        self.model.train()
        running_loss = 0.0
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
            self.optimizer.step()

            # Update metrics
            running_loss += loss.item()

            # Update progress bar
            progress_bar.set_postfix(
                {
                    "Loss": f"{loss.item():.4f}",
                    "Avg Loss": f"{running_loss / (batch_idx + 1):.4f}",
                }
            )

        return running_loss / num_batches

    def validate(self) -> tuple[float, float]:
        """Validate the model.

        Returns:
            Tuple of (validation_loss, validation_accuracy)
        """
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

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

        return avg_loss, accuracy

    def save_checkpoint(
        self,
        epoch: int,
        val_acc: float,
        save_path: Path,
        class_names: list[str],
    ) -> None:
        """Save model checkpoint.

        Args:
            epoch: Current epoch number
            val_acc: Validation accuracy
            save_path: Path to save checkpoint
            class_names: List of class names
        """
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "val_acc": val_acc,
            "class_names": class_names,
            "num_classes": len(class_names),
        }

        torch.save(checkpoint, save_path)
        logger.info("Checkpoint saved to %s", save_path)

    def train(
        self,
        num_epochs: int,
        save_dir: Path,
        class_names: list[str],
        writer: SummaryWriter,
    ) -> None:
        """Train the model for specified number of epochs.

        Args:
            num_epochs: Number of epochs to train
            save_dir: Directory to save checkpoints
            class_names: List of class names
            writer: TensorBoard writer
        """
        logger.info("Starting training for %d epochs", num_epochs)

        for epoch in range(num_epochs):
            start_time = time.time()

            # Train for one epoch
            train_loss = self.train_epoch()

            # Validate
            val_loss, val_acc = self.validate()

            # Update learning rate
            self.scheduler.step()

            # Log metrics
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            self.val_accuracies.append(val_acc)

            # TensorBoard logging
            writer.add_scalar("Loss/Train", train_loss, epoch)
            writer.add_scalar("Loss/Validation", val_loss, epoch)
            writer.add_scalar("Accuracy/Validation", val_acc, epoch)
            writer.add_scalar("Learning_Rate", self.scheduler.get_last_lr()[0], epoch)

            # Save best model
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                best_model_path = save_dir / "best_model.pt"
                self.save_checkpoint(epoch, val_acc, best_model_path, class_names)

            # Save latest model
            latest_model_path = save_dir / "latest_model.pt"
            self.save_checkpoint(epoch, val_acc, latest_model_path, class_names)

            epoch_time = time.time() - start_time

            logger.info(
                "Epoch %d/%d - Train Loss: %.4f, Val Loss: %.4f, Val Acc: %.2f%%, Time: %.2fs",
                epoch + 1,
                num_epochs,
                train_loss,
                val_loss,
                val_acc,
                epoch_time,
            )

        logger.info("Training completed. Best validation accuracy: %.2f%%", self.best_val_acc)


def create_data_transforms() -> tuple[transforms.Compose, transforms.Compose]:
    """Create data transforms for training and validation.

    Returns:
        Tuple of (train_transform, val_transform)
    """
    # Training transforms with augmentation
    train_transform = transforms.Compose(
        [
            transforms.Resize((256, 256)),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
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


def create_data_loaders(
    data_dir: Path,
    batch_size: int = 32,
    num_workers: int = 4,
) -> tuple[DataLoader, DataLoader, list[str]]:
    """Create data loaders for training and validation.

    Args:
        data_dir: Path to dataset directory
        batch_size: Batch size for data loaders
        num_workers: Number of worker processes

    Returns:
        Tuple of (train_loader, val_loader, class_names)
    """
    train_transform, val_transform = create_data_transforms()

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

    return train_loader, val_loader, class_names


def main() -> None:
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train PlantGuard vision model")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to dataset directory")
    parser.add_argument("--save_dir", type=str, default="data/models", help="Directory to save models")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--device", type=str, default="auto", help="Device to use (cpu/cuda/auto)")
    parser.add_argument("--num_workers", type=int, default=4, help="Number of data loader workers")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

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

    # Create TensorBoard writer
    timestamp = int(time.time())
    log_dir = Path("runs") / f"plantguard_vision_{timestamp}"
    writer = SummaryWriter(log_dir)
    logger.info("TensorBoard logs will be saved to: %s", log_dir)

    try:
        # Create data loaders
        train_loader, val_loader, class_names = create_data_loaders(data_dir, args.batch_size, args.num_workers)

        # Save class names
        class_names_path = save_dir / "class_names.json"
        with class_names_path.open("w") as f:
            json.dump(class_names, f, indent=2)
        logger.info("Class names saved to %s", class_names_path)

        # Create model
        model = PlantDiseaseResNet50(num_classes=len(class_names), pretrained=True)

        # Create trainer
        trainer = PlantVillageTrainer(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            device=device,
            learning_rate=args.learning_rate,
            weight_decay=args.weight_decay,
        )

        # Train model
        trainer.train(args.epochs, save_dir, class_names, writer)

    except Exception:
        logger.exception("Training failed")
        raise
    finally:
        writer.close()


if __name__ == "__main__":
    main()
