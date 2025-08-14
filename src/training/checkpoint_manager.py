"""Checkpoint management system for production training pipeline.

This module provides comprehensive checkpoint management including saving, loading,
validation, corruption detection, and automatic cleanup with configurable retention policies.
"""

import hashlib
import json
import logging
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch

logger = logging.getLogger(__name__)


@dataclass
class CheckpointData:
    """Data container for checkpoint saving."""

    optimizer_state: dict[str, Any]
    scheduler_state: dict[str, Any] | None
    training_state: dict[str, Any]
    config: dict[str, Any]
    epoch: int
    step: int
    val_loss: float
    val_accuracy: float
    training_time: float
    scaler_state: dict[str, Any] | None = None


@dataclass
class CheckpointMetadata:
    """Metadata for training checkpoints."""

    checkpoint_id: str
    epoch: int
    step: int
    timestamp: float
    model_architecture: str
    num_classes: int
    best_val_loss: float
    best_val_accuracy: float
    training_time: float
    file_size_bytes: int
    checksum: str
    config_hash: str
    pytorch_version: str
    device_type: str


class CheckpointManager:
    """Manages training checkpoints with validation and retention policies."""

    def __init__(
        self,
        checkpoint_dir: Path,
        max_checkpoints: int = 5,
        save_best_only: bool = False,
        save_frequency: int = 1,
    ) -> None:
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
            max_checkpoints: Maximum number of checkpoints to keep
            save_best_only: Whether to save only the best checkpoints
            save_frequency: Save checkpoint every N epochs
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints
        self.save_best_only = save_best_only
        self.save_frequency = save_frequency

        # Create checkpoint directory
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Metadata file
        self.metadata_file = self.checkpoint_dir / "checkpoint_metadata.json"
        self.metadata: dict[str, CheckpointMetadata] = {}

        # Load existing metadata
        self._load_metadata()

        logger.info("CheckpointManager initialized: %s", self.checkpoint_dir)

    def save_checkpoint(
        self,
        model: torch.nn.Module,
        checkpoint_data: CheckpointData,
        force_save: bool = False,
    ) -> Path | None:
        """Save training checkpoint.

        Args:
            model: PyTorch model
            checkpoint_data: Container with all checkpoint data
            force_save: Force save even if conditions not met

        Returns:
            Path to saved checkpoint or None if not saved
        """
        # Check if we should save this checkpoint
        if not force_save and not self._should_save_checkpoint(
            checkpoint_data.epoch, checkpoint_data.val_loss
        ):
            return None

        try:
            # Generate checkpoint ID
            checkpoint_id = f"epoch_{checkpoint_data.epoch:04d}_{int(time.time())}"
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pt"

            # Prepare checkpoint data
            checkpoint_dict = {
                "checkpoint_id": checkpoint_id,
                "epoch": checkpoint_data.epoch,
                "step": checkpoint_data.step,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": checkpoint_data.optimizer_state,
                "scheduler_state_dict": checkpoint_data.scheduler_state,
                "training_state": checkpoint_data.training_state,
                "config": checkpoint_data.config,
                "val_loss": checkpoint_data.val_loss,
                "val_accuracy": checkpoint_data.val_accuracy,
                "training_time": checkpoint_data.training_time,
                "timestamp": time.time(),
                "pytorch_version": torch.__version__,
                "device_type": str(next(model.parameters()).device),
            }

            if checkpoint_data.scaler_state is not None:
                checkpoint_dict["scaler_state_dict"] = checkpoint_data.scaler_state

            # Save checkpoint
            torch.save(checkpoint_dict, checkpoint_path)

            # Calculate file size and checksum
            file_size = checkpoint_path.stat().st_size
            checksum = self._calculate_checksum(checkpoint_path)

            # Create metadata
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                epoch=checkpoint_data.epoch,
                step=checkpoint_data.step,
                timestamp=time.time(),
                model_architecture=checkpoint_data.config.get("model_architecture", "unknown"),
                num_classes=checkpoint_data.config.get("num_classes", 0),
                best_val_loss=checkpoint_data.val_loss,
                best_val_accuracy=checkpoint_data.val_accuracy,
                training_time=checkpoint_data.training_time,
                file_size_bytes=file_size,
                checksum=checksum,
                config_hash=self._hash_config(checkpoint_data.config),
                pytorch_version=torch.__version__,
                device_type=str(next(model.parameters()).device),
            )

            # Store metadata
            self.metadata[checkpoint_id] = metadata
            self._save_metadata()

            # Cleanup old checkpoints
            self._cleanup_old_checkpoints()

            logger.info(
                "Checkpoint saved: %s (epoch %d, val_loss: %.6f, size: %.1fMB)",
                checkpoint_path,
                checkpoint_data.epoch,
                checkpoint_data.val_loss,
                file_size / 1024**2,
            )

            return checkpoint_path

        except Exception:
            logger.exception("Failed to save checkpoint")
            return None

    def load_checkpoint(self, checkpoint_path: Path | str) -> dict[str, Any] | None:
        """Load checkpoint with validation.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Checkpoint data or None if failed
        """
        checkpoint_path = Path(checkpoint_path)

        if not checkpoint_path.exists():
            logger.error("Checkpoint file not found: %s", checkpoint_path)
            return None

        try:
            logger.info("Loading checkpoint: %s", checkpoint_path)

            # Load checkpoint
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)

            # Validate checkpoint
            if not self._validate_checkpoint_data(checkpoint):
                logger.error("Checkpoint validation failed")
                return None

            # Verify checksum if available
            if not self._verify_checkpoint_integrity(checkpoint_path, checkpoint):
                logger.warning("Checkpoint integrity check failed, but proceeding")

            logger.info(
                "Checkpoint loaded successfully: epoch %s", checkpoint.get("epoch", "unknown")
            )
            return checkpoint  # type: ignore[no-any-return]

        except Exception:
            logger.exception("Failed to load checkpoint")
            return None

    def find_latest_checkpoint(self) -> Path | None:
        """Find the latest checkpoint.

        Returns:
            Path to latest checkpoint or None if no checkpoints found
        """
        if not self.metadata:
            return None

        # Find checkpoint with highest epoch
        latest_metadata = max(self.metadata.values(), key=lambda x: x.epoch)
        checkpoint_path = self.checkpoint_dir / f"{latest_metadata.checkpoint_id}.pt"

        if checkpoint_path.exists():
            return checkpoint_path

        logger.warning("Latest checkpoint file not found: %s", checkpoint_path)
        return None

    def find_best_checkpoint(self, metric: str = "val_loss") -> Path | None:
        """Find the best checkpoint based on specified metric.

        Args:
            metric: Metric to use for selection ('val_loss' or 'val_accuracy')

        Returns:
            Path to best checkpoint or None if no checkpoints found
        """
        if not self.metadata:
            return None

        if metric == "val_loss":
            best_metadata = min(self.metadata.values(), key=lambda x: x.best_val_loss)
        elif metric == "val_accuracy":
            best_metadata = max(self.metadata.values(), key=lambda x: x.best_val_accuracy)
        else:
            logger.error("Unsupported metric: %s", metric)
            return None

        checkpoint_path = self.checkpoint_dir / f"{best_metadata.checkpoint_id}.pt"

        if checkpoint_path.exists():
            return checkpoint_path

        logger.warning("Best checkpoint file not found: %s", checkpoint_path)
        return None

    def list_checkpoints(self) -> list[CheckpointMetadata]:
        """List all available checkpoints.

        Returns:
            List of checkpoint metadata sorted by epoch
        """
        return sorted(self.metadata.values(), key=lambda x: x.epoch)

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to delete

        Returns:
            True if deleted successfully
        """
        if checkpoint_id not in self.metadata:
            logger.error("Checkpoint not found: %s", checkpoint_id)
            return False

        try:
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pt"
            if checkpoint_path.exists():
                checkpoint_path.unlink()

            # Remove from metadata
            del self.metadata[checkpoint_id]
            self._save_metadata()

            logger.info("Checkpoint deleted: %s", checkpoint_id)
            return True

        except Exception:
            logger.exception("Failed to delete checkpoint %s", checkpoint_id)
            return False

    def cleanup_corrupted_checkpoints(self) -> int:
        """Remove corrupted checkpoints.

        Returns:
            Number of corrupted checkpoints removed
        """
        corrupted_count = 0
        corrupted_ids = []

        for checkpoint_id in self.metadata:
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.pt"

            if not checkpoint_path.exists():
                logger.warning("Checkpoint file missing: %s", checkpoint_path)
                corrupted_ids.append(checkpoint_id)
                continue

            # Verify integrity
            try:
                checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
                if not self._validate_checkpoint_data(checkpoint):
                    logger.warning("Corrupted checkpoint detected: %s", checkpoint_id)
                    corrupted_ids.append(checkpoint_id)
                    continue

                # Verify checksum
                if not self._verify_checkpoint_integrity(checkpoint_path, checkpoint):
                    logger.warning("Checksum mismatch for checkpoint: %s", checkpoint_id)
                    corrupted_ids.append(checkpoint_id)

            except Exception as e:
                logger.warning("Failed to validate checkpoint %s: %s", checkpoint_id, e)
                corrupted_ids.append(checkpoint_id)

        # Remove corrupted checkpoints
        for checkpoint_id in corrupted_ids:
            if self.delete_checkpoint(checkpoint_id):
                corrupted_count += 1

        if corrupted_count > 0:
            logger.info("Removed %d corrupted checkpoints", corrupted_count)

        return corrupted_count

    def get_checkpoint_info(self, checkpoint_id: str) -> CheckpointMetadata | None:
        """Get information about a specific checkpoint.

        Args:
            checkpoint_id: ID of checkpoint

        Returns:
            Checkpoint metadata or None if not found
        """
        return self.metadata.get(checkpoint_id)

    def export_checkpoint_summary(self) -> dict[str, Any]:
        """Export summary of all checkpoints.

        Returns:
            Dictionary with checkpoint summary
        """
        if not self.metadata:
            return {"total_checkpoints": 0, "checkpoints": []}

        checkpoints = []
        total_size = 0

        for metadata in sorted(self.metadata.values(), key=lambda x: x.epoch):
            checkpoint_info = {
                "checkpoint_id": metadata.checkpoint_id,
                "epoch": metadata.epoch,
                "val_loss": metadata.best_val_loss,
                "val_accuracy": metadata.best_val_accuracy,
                "training_time": metadata.training_time,
                "file_size_mb": metadata.file_size_bytes / (1024**2),
                "timestamp": metadata.timestamp,
            }
            checkpoints.append(checkpoint_info)
            total_size += metadata.file_size_bytes

        return {
            "total_checkpoints": len(checkpoints),
            "total_size_mb": total_size / (1024**2),
            "checkpoint_dir": str(self.checkpoint_dir),
            "checkpoints": checkpoints,
        }

    def _should_save_checkpoint(self, epoch: int, val_loss: float) -> bool:
        """Determine if checkpoint should be saved.

        Args:
            epoch: Current epoch
            val_loss: Current validation loss

        Returns:
            True if checkpoint should be saved
        """
        # Always save if no checkpoints exist
        if not self.metadata:
            return True

        # Check frequency
        if (epoch + 1) % self.save_frequency != 0:
            return False

        # If save_best_only, only save if this is the best so far
        if self.save_best_only:
            best_loss = min(meta.best_val_loss for meta in self.metadata.values())
            return val_loss < best_loss

        return True

    def _cleanup_old_checkpoints(self) -> None:
        """Remove old checkpoints based on retention policy."""
        if len(self.metadata) <= self.max_checkpoints:
            return

        # Sort by epoch (keep most recent)
        sorted_metadata = sorted(self.metadata.values(), key=lambda x: x.epoch, reverse=True)

        # Keep the most recent checkpoints
        to_remove = sorted_metadata[self.max_checkpoints :]

        for metadata in to_remove:
            self.delete_checkpoint(metadata.checkpoint_id)

        if to_remove:
            logger.info("Cleaned up %d old checkpoints", len(to_remove))

    def _validate_checkpoint_data(self, checkpoint: dict[str, Any]) -> bool:
        """Validate checkpoint data structure.

        Args:
            checkpoint: Checkpoint data

        Returns:
            True if valid
        """
        required_keys = [
            "epoch",
            "model_state_dict",
            "optimizer_state_dict",
            "config",
        ]

        for key in required_keys:
            if key not in checkpoint:
                logger.error("Missing required key in checkpoint: %s", key)
                return False

        # Validate model state dict
        model_state = checkpoint["model_state_dict"]
        if not isinstance(model_state, dict) or not model_state:
            logger.error("Invalid model state dict")
            return False

        return True

    def _verify_checkpoint_integrity(
        self, checkpoint_path: Path, checkpoint: dict[str, Any]
    ) -> bool:
        """Verify checkpoint file integrity using checksum.

        Args:
            checkpoint_path: Path to checkpoint file
            checkpoint: Loaded checkpoint data

        Returns:
            True if integrity check passes
        """
        checkpoint_id = checkpoint.get("checkpoint_id")
        if not checkpoint_id or checkpoint_id not in self.metadata:
            # No metadata available for verification
            return True

        stored_checksum = self.metadata[checkpoint_id].checksum
        current_checksum = self._calculate_checksum(checkpoint_path)

        return stored_checksum == current_checksum

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file.

        Args:
            file_path: Path to file

        Returns:
            SHA256 checksum as hex string
        """
        sha256_hash = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _hash_config(self, config: dict[str, Any]) -> str:
        """Calculate hash of configuration.

        Args:
            config: Configuration dictionary

        Returns:
            SHA256 hash of config
        """
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()

    def _load_metadata(self) -> None:
        """Load checkpoint metadata from file."""
        if not self.metadata_file.exists():
            return

        try:
            with self.metadata_file.open(encoding="utf-8") as f:
                metadata_dict = json.load(f)

            self.metadata = {}
            for checkpoint_id, data in metadata_dict.items():
                self.metadata[checkpoint_id] = CheckpointMetadata(**data)

            logger.info("Loaded metadata for %d checkpoints", len(self.metadata))

        except Exception as e:
            logger.warning("Failed to load checkpoint metadata: %s", e)
            self.metadata = {}

    def _save_metadata(self) -> None:
        """Save checkpoint metadata to file."""
        try:
            metadata_dict = {}
            for checkpoint_id, metadata in self.metadata.items():
                metadata_dict[checkpoint_id] = asdict(metadata)

            with self.metadata_file.open("w", encoding="utf-8") as f:
                json.dump(metadata_dict, f, indent=2, default=str)

        except Exception as e:
            logger.warning("Failed to save checkpoint metadata: %s", e)

    def create_backup(self, backup_dir: Path | str) -> bool:
        """Create backup of all checkpoints.

        Args:
            backup_dir: Directory to store backup

        Returns:
            True if backup successful
        """
        backup_dir = Path(backup_dir)

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copy all checkpoint files
            for checkpoint_id in self.metadata:
                src_path = self.checkpoint_dir / f"{checkpoint_id}.pt"
                dst_path = backup_dir / f"{checkpoint_id}.pt"

                if src_path.exists():
                    shutil.copy2(src_path, dst_path)

            # Copy metadata
            if self.metadata_file.exists():
                shutil.copy2(self.metadata_file, backup_dir / "checkpoint_metadata.json")

            logger.info("Checkpoint backup created: %s", backup_dir)
            return True

        except Exception:
            logger.exception("Failed to create checkpoint backup")
            return False

    def restore_from_backup(self, backup_dir: Path | str) -> bool:
        """Restore checkpoints from backup.

        Args:
            backup_dir: Directory containing backup

        Returns:
            True if restore successful
        """
        backup_dir = Path(backup_dir)

        if not backup_dir.exists():
            logger.error("Backup directory not found: %s", backup_dir)
            return False

        try:
            # Clear current checkpoints
            for checkpoint_path in self.checkpoint_dir.glob("*.pt"):
                checkpoint_path.unlink()

            # Restore checkpoint files
            for backup_file in backup_dir.glob("*.pt"):
                dst_path = self.checkpoint_dir / backup_file.name
                shutil.copy2(backup_file, dst_path)

            # Restore metadata
            backup_metadata = backup_dir / "checkpoint_metadata.json"
            if backup_metadata.exists():
                shutil.copy2(backup_metadata, self.metadata_file)
                self._load_metadata()

            logger.info("Checkpoints restored from backup: %s", backup_dir)
            return True

        except Exception:
            logger.exception("Failed to restore from backup")
            return False
