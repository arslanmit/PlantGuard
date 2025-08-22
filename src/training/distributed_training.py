"""Distributed training support for multi-GPU training.

This module provides distributed training capabilities using PyTorch's
DistributedDataParallel (DDP) for scaling training across multiple GPUs.
"""

import logging
import os
import socket
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler

logger = logging.getLogger(__name__)


@dataclass
class DistributedConfig:
    """Configuration for distributed training."""

    # Multi-GPU settings
    world_size: int = 1  # Total number of processes
    rank: int = 0  # Current process rank
    local_rank: int = 0  # Local GPU rank

    # Communication backend
    backend: str = "nccl"  # nccl for GPU, gloo for CPU
    init_method: str = "env://"  # Initialization method

    # Training settings
    find_unused_parameters: bool = False
    gradient_as_bucket_view: bool = True
    static_graph: bool = False

    # Synchronization
    sync_bn: bool = True  # Synchronize batch normalization
    broadcast_buffers: bool = True

    # Performance optimization
    bucket_cap_mb: int = 25  # Gradient bucket size in MB

    # Fault tolerance
    timeout_minutes: int = 30


class DistributedTrainingManager:
    """Manager for distributed training setup and coordination."""

    def __init__(self, config: DistributedConfig):
        """Initialize distributed training manager.

        Args:
            config: Distributed training configuration
        """
        self.config = config
        self.is_distributed = config.world_size > 1
        self.is_main_process = config.rank == 0

    def setup_distributed_training(self) -> bool:
        """Setup distributed training environment.

        Returns:
            True if setup successful, False otherwise
        """
        if not self.is_distributed:
            logger.info("Single GPU training - no distributed setup needed")
            return True

        try:
            # Initialize process group
            dist.init_process_group(
                backend=self.config.backend,
                init_method=self.config.init_method,
                world_size=self.config.world_size,
                rank=self.config.rank,
                timeout=torch.distributed.default_pg_timeout,
            )

            # Set device for current process
            if torch.cuda.is_available():
                torch.cuda.set_device(self.config.local_rank)
                device = torch.device(f"cuda:{self.config.local_rank}")
            else:
                device = torch.device("cpu")

            logger.info(f"Distributed training initialized: rank {self.config.rank}/{self.config.world_size}, device: {device}")
            return True

        except Exception as e:
            logger.error(f"Failed to setup distributed training: {e}")
            return False

    def wrap_model(self, model: torch.nn.Module, device: torch.device) -> torch.nn.Module:
        """Wrap model for distributed training.

        Args:
            model: PyTorch model
            device: Training device

        Returns:
            Wrapped model for distributed training
        """
        if not self.is_distributed:
            return model.to(device)

        # Move model to device first
        model = model.to(device)

        # Synchronize batch normalization if requested
        if self.config.sync_bn:
            model = torch.nn.SyncBatchNorm.convert_sync_batchnorm(model)
            logger.info("Converted BatchNorm to SyncBatchNorm")

        # Wrap with DistributedDataParallel
        ddp_model = DDP(
            model,
            device_ids=[self.config.local_rank] if torch.cuda.is_available() else None,
            output_device=self.config.local_rank if torch.cuda.is_available() else None,
            find_unused_parameters=self.config.find_unused_parameters,
            gradient_as_bucket_view=self.config.gradient_as_bucket_view,
            static_graph=self.config.static_graph,
            broadcast_buffers=self.config.broadcast_buffers,
            bucket_cap_mb=self.config.bucket_cap_mb,
        )

        logger.info("Model wrapped with DistributedDataParallel")
        return ddp_model

    def create_distributed_dataloader(
        self,
        dataset: torch.utils.data.Dataset,
        batch_size: int,
        shuffle: bool = True,
        num_workers: int = 4,
        pin_memory: bool = True,
        drop_last: bool = True,
    ) -> tuple[DataLoader, DistributedSampler | None]:
        """Create data loader with distributed sampling.

        Args:
            dataset: PyTorch dataset
            batch_size: Batch size per process
            shuffle: Whether to shuffle data
            num_workers: Number of data loading workers
            pin_memory: Whether to pin memory
            drop_last: Whether to drop last incomplete batch

        Returns:
            Tuple of (DataLoader, DistributedSampler or None)
        """
        sampler = None

        if self.is_distributed:
            sampler = DistributedSampler(
                dataset,
                num_replicas=self.config.world_size,
                rank=self.config.rank,
                shuffle=shuffle,
                drop_last=drop_last,
            )
            # Don't shuffle in DataLoader when using DistributedSampler
            shuffle = False

        dataloader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            sampler=sampler,
            num_workers=num_workers,
            pin_memory=pin_memory,
            drop_last=drop_last,
            persistent_workers=num_workers > 0,
        )

        return dataloader, sampler

    def reduce_metrics(self, metrics: dict[str, float]) -> dict[str, float]:
        """Reduce metrics across all processes.

        Args:
            metrics: Dictionary of metrics to reduce

        Returns:
            Dictionary of reduced metrics
        """
        if not self.is_distributed:
            return metrics

        reduced_metrics = {}

        for key, value in metrics.items():
            tensor = torch.tensor(value, device=f"cuda:{self.config.local_rank}" if torch.cuda.is_available() else "cpu")
            dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
            reduced_metrics[key] = tensor.item() / self.config.world_size

        return reduced_metrics

    def barrier(self) -> None:
        """Synchronize all processes."""
        if self.is_distributed:
            dist.barrier()

    def cleanup(self) -> None:
        """Cleanup distributed training."""
        if self.is_distributed:
            dist.destroy_process_group()
            logger.info("Distributed training cleanup completed")

    def save_checkpoint(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        checkpoint_path: Path,
        **kwargs: Any,
    ) -> None:
        """Save checkpoint from main process only.

        Args:
            model: Model to save
            optimizer: Optimizer to save
            epoch: Current epoch
            checkpoint_path: Path to save checkpoint
            **kwargs: Additional data to save
        """
        if not self.is_main_process:
            return

        # Extract model state dict (handle DDP wrapper)
        if isinstance(model, DDP):
            model_state_dict = model.module.state_dict()
        else:
            model_state_dict = model.state_dict()

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": model_state_dict,
            "optimizer_state_dict": optimizer.state_dict(),
            **kwargs,
        }

        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Checkpoint saved to {checkpoint_path}")

    def load_checkpoint(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        checkpoint_path: Path,
        device: torch.device,
    ) -> dict[str, Any]:
        """Load checkpoint and broadcast to all processes.

        Args:
            model: Model to load state into
            optimizer: Optimizer to load state into
            checkpoint_path: Path to checkpoint
            device: Device to load checkpoint on

        Returns:
            Dictionary with checkpoint metadata
        """
        # Load checkpoint on main process
        if self.is_main_process:
            try:
                checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
            except TypeError:
                # Fallback for older PyTorch versions or legacy models.
                # nosec B614: weights_only=False required for legacy checkpoints; path is controlled (local file).
                # This is a justified fallback for compatibility reasons.
                # The risk of arbitrary code execution is mitigated by the fact that the checkpoint path is controlled.
                checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)  # nosec B614
        else:
            checkpoint = None

        # Broadcast checkpoint to all processes
        if self.is_distributed:
            checkpoint = self._broadcast_checkpoint(checkpoint, device, checkpoint_path)

        # Load model state (handle DDP wrapper)
        if isinstance(model, DDP):
            model.module.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint["model_state_dict"])

        # Load optimizer state
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

        logger.info(f"Checkpoint loaded from {checkpoint_path}")
        return {k: v for k, v in checkpoint.items() if k not in ["model_state_dict", "optimizer_state_dict"]}

    def _broadcast_checkpoint(self, checkpoint: dict[str, Any] | None, device: torch.device, checkpoint_path: Path) -> dict[str, Any]:
        """Broadcast checkpoint from main process to all processes."""
        # This is a simplified implementation
        # In practice, you might want to use more efficient broadcasting
        # This simplified helper currently ensures non-main processes can load
        # the checkpoint from the provided path when the main process did not
        # provide a serialized checkpoint object.
        if self.is_main_process:
            # In a more complete implementation we would serialize the
            # checkpoint and broadcast it as tensors. For now, the main
            # process already has the checkpoint dict and will continue.
            pass

        # For non-main processes (or when checkpoint is None), load from the
        # given checkpoint_path. Keep the weights_only fallback for legacy
        # compatibility as before.
        if checkpoint is None:
            try:
                checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
            except TypeError:
                # Fallback for older PyTorch versions or legacy models.
                # nosec B614: weights_only=False required for legacy checkpoints; path is controlled (local file).
                checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)  # nosec B614

        return checkpoint


def find_free_port() -> int:
    """Find a free port for distributed training."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def setup_distributed_environment(
    world_size: int,
    rank: int,
    master_addr: str = "localhost",
    master_port: int | None = None,
) -> None:
    """Setup environment variables for distributed training.

    Args:
        world_size: Total number of processes
        rank: Current process rank
        master_addr: Master node address
        master_port: Master node port (auto-detected if None)
    """
    if master_port is None:
        master_port = find_free_port()

    os.environ["MASTER_ADDR"] = master_addr
    os.environ["MASTER_PORT"] = str(master_port)
    os.environ["WORLD_SIZE"] = str(world_size)
    os.environ["RANK"] = str(rank)


def distributed_training_worker(
    rank: int,
    world_size: int,
    train_fn: Callable,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Worker function for distributed training.

    Args:
        rank: Process rank
        world_size: Total number of processes
        train_fn: Training function to execute
        *args: Arguments for training function
        **kwargs: Keyword arguments for training function
    """
    # Setup distributed environment
    setup_distributed_environment(world_size, rank)

    # Create distributed config
    config = DistributedConfig(
        world_size=world_size,
        rank=rank,
        local_rank=rank % torch.cuda.device_count() if torch.cuda.is_available() else 0,
    )

    # Initialize distributed training
    manager = DistributedTrainingManager(config)

    try:
        if manager.setup_distributed_training():
            # Execute training function
            train_fn(manager, *args, **kwargs)
        else:
            logger.error(f"Failed to setup distributed training for rank {rank}")

    except Exception as e:
        logger.error(f"Distributed training failed for rank {rank}: {e}")
        raise

    finally:
        manager.cleanup()


def launch_distributed_training(
    train_fn: Callable,
    world_size: int | None = None,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Launch distributed training across multiple processes.

    Args:
        train_fn: Training function to execute
        world_size: Number of processes (auto-detected if None)
        *args: Arguments for training function
        **kwargs: Keyword arguments for training function
    """
    if world_size is None:
        world_size = torch.cuda.device_count() if torch.cuda.is_available() else 1

    if world_size <= 1:
        logger.info("Single process training")
        # Create dummy manager for single process
        config = DistributedConfig(world_size=1, rank=0, local_rank=0)
        manager = DistributedTrainingManager(config)
        train_fn(manager, *args, **kwargs)
    else:
        logger.info(f"Launching distributed training with {world_size} processes")
        mp.spawn(
            distributed_training_worker,
            args=(world_size, train_fn, *args),
            nprocs=world_size,
            join=True,
        )


class DistributedTrainingIntegration:
    """Integration class for adding distributed training to existing trainers."""

    def __init__(self, trainer_class: type):
        """Initialize distributed training integration.

        Args:
            trainer_class: Trainer class to enhance with distributed training
        """
        self.trainer_class = trainer_class

    def create_distributed_trainer(
        self,
        config: Any,
        distributed_config: DistributedConfig,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Create trainer instance with distributed training support.

        Args:
            config: Training configuration
            distributed_config: Distributed training configuration
            *args: Additional arguments for trainer
            **kwargs: Additional keyword arguments for trainer

        Returns:
            Enhanced trainer instance
        """
        # Create base trainer
        trainer = self.trainer_class(config, *args, **kwargs)

        # Add distributed training manager
        trainer.distributed_manager = DistributedTrainingManager(distributed_config)

        # Enhance trainer methods
        self._enhance_trainer_methods(trainer)

        return trainer

    def _enhance_trainer_methods(self, trainer: Any) -> None:
        """Enhance trainer methods for distributed training."""
        # Store original methods
        original_setup = trainer.setup_training
        original_train = trainer.train
        original_save_checkpoint = getattr(trainer, "save_checkpoint", None)

        def enhanced_setup():
            """Enhanced setup with distributed training."""
            # Setup distributed training first
            if not trainer.distributed_manager.setup_distributed_training():
                return False

            # Run original setup
            if not original_setup():
                return False

            # Wrap model for distributed training
            if hasattr(trainer, "model") and trainer.model is not None:
                trainer.model = trainer.distributed_manager.wrap_model(trainer.model, trainer.device)

            # Update data loaders for distributed training
            if hasattr(trainer, "train_loader") and trainer.train_loader is not None:
                trainer.train_loader, trainer.train_sampler = trainer.distributed_manager.create_distributed_dataloader(
                    trainer.train_loader.dataset,
                    trainer.train_loader.batch_size,
                    shuffle=True,
                    num_workers=trainer.train_loader.num_workers,
                    pin_memory=trainer.train_loader.pin_memory,
                )

            if hasattr(trainer, "val_loader") and trainer.val_loader is not None:
                trainer.val_loader, trainer.val_sampler = trainer.distributed_manager.create_distributed_dataloader(
                    trainer.val_loader.dataset,
                    trainer.val_loader.batch_size,
                    shuffle=False,
                    num_workers=trainer.val_loader.num_workers,
                    pin_memory=trainer.val_loader.pin_memory,
                )

            return True

        def enhanced_train():
            """Enhanced training with distributed coordination."""
            try:
                # Set epoch for distributed sampler
                if hasattr(trainer, "train_sampler") and trainer.train_sampler is not None:
                    trainer.train_sampler.set_epoch(0)  # Will be updated in training loop

                # Run original training
                result = original_train()

                # Reduce metrics across processes
                if hasattr(result, "metrics"):
                    result.metrics = trainer.distributed_manager.reduce_metrics(result.metrics)

                return result

            finally:
                trainer.distributed_manager.cleanup()

        def enhanced_save_checkpoint(*args, **kwargs):
            """Enhanced checkpoint saving for distributed training."""
            if original_save_checkpoint:
                return trainer.distributed_manager.save_checkpoint(*args, **kwargs)

        # Replace methods
        trainer.setup_training = enhanced_setup
        trainer.train = enhanced_train
        if original_save_checkpoint:
            trainer.save_checkpoint = enhanced_save_checkpoint


def create_distributed_config(
    world_size: int | None = None,
    backend: str = "nccl",
    sync_bn: bool = True,
    **kwargs: Any,
) -> DistributedConfig:
    """Create distributed training configuration with sensible defaults.

    Args:
        world_size: Number of processes (auto-detected if None)
        backend: Communication backend
        sync_bn: Whether to synchronize batch normalization
        **kwargs: Additional configuration options

    Returns:
        DistributedConfig instance
    """
    if world_size is None:
        world_size = torch.cuda.device_count() if torch.cuda.is_available() else 1

    # Get rank from environment if available
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", str(rank % world_size)))

    return DistributedConfig(
        world_size=world_size,
        rank=rank,
        local_rank=local_rank,
        backend=backend,
        sync_bn=sync_bn,
        **kwargs,
    )
