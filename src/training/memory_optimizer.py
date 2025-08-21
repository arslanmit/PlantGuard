"""Memory optimization and efficient training utilities for production training.

This module provides memory optimization features including gradient accumulation,
automatic memory management, memory profiling, and dynamic batch size adjustment.
"""

import gc
import logging
from dataclasses import dataclass, field
from typing import Any

import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler

logger = logging.getLogger(__name__)


@dataclass
class MemoryProfile:
    """Memory usage profile for training optimization."""

    peak_memory_mb: float = 0.0
    current_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    memory_utilization: float = 0.0
    fragmentation_ratio: float = 0.0
    gc_collections: int = 0
    recommendations: list[str] = field(default_factory=list)


@dataclass
class MemoryOptimizationConfig:
    """Configuration for memory optimization."""

    # Gradient accumulation
    enable_gradient_accumulation: bool = True
    max_gradient_accumulation_steps: int = 8

    # Memory management
    enable_automatic_gc: bool = True
    gc_frequency: int = 10  # Run GC every N batches
    clear_cache_frequency: int = 50  # Clear CUDA cache every N batches

    # Dynamic batch size adjustment
    enable_dynamic_batch_size: bool = True
    min_batch_size: int = 8
    max_batch_size: int = 128
    batch_size_adjustment_factor: float = 0.8  # Reduce by 20% on OOM

    # Memory monitoring
    memory_threshold: float = 0.9  # Trigger optimization at 90% memory usage
    enable_memory_profiling: bool = False
    profile_frequency: int = 100  # Profile every N batches


class MemoryProfiler:
    """Memory profiler for training optimization."""

    def __init__(self, config: MemoryOptimizationConfig) -> None:
        """Initialize memory profiler.

        Args:
            config: Memory optimization configuration
        """
        self.config = config
        self.profiles: list[MemoryProfile] = []
        self.peak_memory = 0.0
        self.gc_count = 0

    def profile_memory(self, step: int) -> MemoryProfile:
        """Profile current memory usage.

        Args:
            step: Current training step

        Returns:
            MemoryProfile with current memory statistics
        """
        profile = MemoryProfile()

        if torch.cuda.is_available():
            # CUDA memory profiling
            current_memory = torch.cuda.memory_allocated()
            peak_memory = torch.cuda.max_memory_allocated()
            total_memory = torch.cuda.get_device_properties(0).total_memory

            profile.current_memory_mb = current_memory / 1024**2
            profile.peak_memory_mb = peak_memory / 1024**2
            profile.available_memory_mb = (total_memory - current_memory) / 1024**2
            profile.memory_utilization = current_memory / total_memory

            # Calculate fragmentation (simplified)
            reserved_memory = torch.cuda.memory_reserved()
            if reserved_memory > 0:
                profile.fragmentation_ratio = (reserved_memory - current_memory) / reserved_memory

            self.peak_memory = max(self.peak_memory, profile.peak_memory_mb)

        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            # MPS memory profiling (limited)
            profile.current_memory_mb = torch.mps.current_allocated_memory() / 1024**2
            profile.peak_memory_mb = max(profile.current_memory_mb, self.peak_memory)
            self.peak_memory = profile.peak_memory_mb

        else:
            # CPU memory profiling
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            profile.current_memory_mb = memory_info.rss / 1024**2
            profile.peak_memory_mb = max(profile.current_memory_mb, self.peak_memory)
            self.peak_memory = profile.peak_memory_mb

        profile.gc_collections = self.gc_count

        # Generate recommendations
        profile.recommendations = self._generate_recommendations(profile)

        # Store profile
        self.profiles.append(profile)

        # Log if enabled
        if self.config.enable_memory_profiling and step % self.config.profile_frequency == 0:
            self._log_memory_profile(profile, step)

        return profile

    def _generate_recommendations(self, profile: MemoryProfile) -> list[str]:
        """Generate memory optimization recommendations.

        Args:
            profile: Current memory profile

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        if profile.memory_utilization > 0.9:
            recommendations.append("High memory usage detected - consider reducing batch size")

        if profile.fragmentation_ratio > 0.3:
            recommendations.append("High memory fragmentation - consider clearing CUDA cache")

        if profile.peak_memory_mb > profile.current_memory_mb * 1.5:
            recommendations.append("Memory spikes detected - consider gradient accumulation")

        return recommendations

    def _log_memory_profile(self, profile: MemoryProfile, step: int) -> None:
        """Log memory profile information.

        Args:
            profile: Memory profile to log
            step: Current training step
        """
        logger.info(f"Memory Profile (Step {step}):")
        logger.info(f"  Current: {profile.current_memory_mb:.1f} MB")
        logger.info(f"  Peak: {profile.peak_memory_mb:.1f} MB")
        logger.info(f"  Available: {profile.available_memory_mb:.1f} MB")
        logger.info(f"  Utilization: {profile.memory_utilization:.1%}")

        if profile.recommendations:
            logger.info("  Recommendations:")
            for rec in profile.recommendations:
                logger.info(f"    - {rec}")

    def get_memory_summary(self) -> dict[str, Any]:
        """Get summary of memory usage during training.

        Returns:
            Dictionary with memory usage summary
        """
        if not self.profiles:
            return {}

        current_memory = [p.current_memory_mb for p in self.profiles]
        peak_memory = [p.peak_memory_mb for p in self.profiles]
        utilization = [p.memory_utilization for p in self.profiles]

        return {
            "peak_memory_mb": max(peak_memory),
            "avg_memory_mb": sum(current_memory) / len(current_memory),
            "max_utilization": max(utilization),
            "avg_utilization": sum(utilization) / len(utilization),
            "total_profiles": len(self.profiles),
            "gc_collections": self.gc_count,
        }


class GradientAccumulator:
    """Gradient accumulation manager for memory-efficient training."""

    def __init__(
        self,
        model: nn.Module,
        config: MemoryOptimizationConfig,
        initial_accumulation_steps: int = 1,
    ) -> None:
        """Initialize gradient accumulator.

        Args:
            model: PyTorch model
            config: Memory optimization configuration
            initial_accumulation_steps: Initial gradient accumulation steps
        """
        self.model = model
        self.config = config
        self.accumulation_steps = initial_accumulation_steps
        self.current_step = 0
        self.accumulated_loss = 0.0

    def should_accumulate(self) -> bool:
        """Check if gradients should be accumulated.

        Returns:
            True if gradients should be accumulated, False if step should be taken
        """
        return (self.current_step + 1) % self.accumulation_steps != 0

    def accumulate_gradients(self, loss: torch.Tensor) -> torch.Tensor:
        """Accumulate gradients from loss.

        Args:
            loss: Loss tensor

        Returns:
            Scaled loss for backward pass
        """
        # Scale loss by accumulation steps
        scaled_loss = loss / self.accumulation_steps
        self.accumulated_loss += scaled_loss.item()

        return scaled_loss

    def step_completed(self) -> tuple[bool, float]:
        """Mark completion of a training step.

        Returns:
            Tuple of (should_step_optimizer, accumulated_loss)
        """
        self.current_step += 1
        should_step = not self.should_accumulate()

        if should_step:
            # Reset accumulated loss
            accumulated_loss = self.accumulated_loss
            self.accumulated_loss = 0.0
            return True, accumulated_loss

        return False, self.accumulated_loss

    def adjust_accumulation_steps(self, new_steps: int) -> None:
        """Adjust gradient accumulation steps.

        Args:
            new_steps: New number of accumulation steps
        """
        if new_steps != self.accumulation_steps:
            logger.info(f"Adjusting gradient accumulation steps: {self.accumulation_steps} -> {new_steps}")
            self.accumulation_steps = max(1, min(new_steps, self.config.max_gradient_accumulation_steps))

    def get_effective_batch_size(self, batch_size: int) -> int:
        """Get effective batch size considering accumulation.

        Args:
            batch_size: Base batch size

        Returns:
            Effective batch size
        """
        return batch_size * self.accumulation_steps


class DynamicBatchSizeManager:
    """Dynamic batch size adjustment based on memory usage."""

    def __init__(self, config: MemoryOptimizationConfig, initial_batch_size: int) -> None:
        """Initialize dynamic batch size manager.

        Args:
            config: Memory optimization configuration
            initial_batch_size: Initial batch size
        """
        self.config = config
        self.current_batch_size = initial_batch_size
        self.original_batch_size = initial_batch_size
        self.oom_count = 0
        self.successful_batches = 0

    def handle_oom_error(self) -> int:
        """Handle out-of-memory error by reducing batch size.

        Returns:
            New batch size
        """
        self.oom_count += 1
        old_batch_size = self.current_batch_size

        # Reduce batch size
        new_batch_size = max(self.config.min_batch_size, int(self.current_batch_size * self.config.batch_size_adjustment_factor))

        self.current_batch_size = new_batch_size

        logger.warning(f"OOM error #{self.oom_count}: Reducing batch size {old_batch_size} -> {new_batch_size}")

        # Clear memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

        return new_batch_size

    def record_successful_batch(self) -> None:
        """Record successful batch processing."""
        self.successful_batches += 1

    def can_increase_batch_size(self) -> bool:
        """Check if batch size can be increased.

        Returns:
            True if batch size can be safely increased
        """
        return (
            self.config.enable_dynamic_batch_size
            and self.current_batch_size < min(self.original_batch_size, self.config.max_batch_size)
            and self.successful_batches > 100  # Wait for stability
            and self.oom_count == 0  # No recent OOM errors
        )

    def increase_batch_size(self) -> int:
        """Increase batch size if conditions are met.

        Returns:
            New batch size
        """
        if self.can_increase_batch_size():
            old_batch_size = self.current_batch_size
            new_batch_size = min(
                int(self.current_batch_size / self.config.batch_size_adjustment_factor),
                min(self.original_batch_size, self.config.max_batch_size),
            )

            if new_batch_size > old_batch_size:
                self.current_batch_size = new_batch_size
                self.successful_batches = 0  # Reset counter
                logger.info(f"Increasing batch size: {old_batch_size} -> {new_batch_size}")
                return new_batch_size

        return self.current_batch_size

    def get_stats(self) -> dict[str, Any]:
        """Get batch size adjustment statistics.

        Returns:
            Dictionary with adjustment statistics
        """
        return {
            "current_batch_size": self.current_batch_size,
            "original_batch_size": self.original_batch_size,
            "oom_count": self.oom_count,
            "successful_batches": self.successful_batches,
            "batch_size_ratio": self.current_batch_size / self.original_batch_size,
        }


class MemoryOptimizer:
    """Main memory optimizer coordinating all memory optimization features."""

    def __init__(
        self,
        model: nn.Module,
        config: MemoryOptimizationConfig,
        initial_batch_size: int,
        gradient_accumulation_steps: int = 1,
    ) -> None:
        """Initialize memory optimizer.

        Args:
            model: PyTorch model
            config: Memory optimization configuration
            initial_batch_size: Initial batch size
            gradient_accumulation_steps: Initial gradient accumulation steps
        """
        self.model = model
        self.config = config

        # Initialize components
        self.profiler = MemoryProfiler(config)
        self.gradient_accumulator = GradientAccumulator(model, config, gradient_accumulation_steps)
        self.batch_size_manager = DynamicBatchSizeManager(config, initial_batch_size)

        # State tracking
        self.batch_count = 0
        self.last_gc_batch = 0
        self.last_cache_clear_batch = 0

    def optimize_memory_usage(self, step: int) -> None:
        """Perform memory optimization based on current usage.

        Args:
            step: Current training step
        """
        # Profile memory usage
        profile = self.profiler.profile_memory(step)

        # Automatic garbage collection
        if self.config.enable_automatic_gc:
            if self.batch_count - self.last_gc_batch >= self.config.gc_frequency:
                self._run_garbage_collection()
                self.last_gc_batch = self.batch_count

        # Clear CUDA cache if needed
        if torch.cuda.is_available():
            if self.batch_count - self.last_cache_clear_batch >= self.config.clear_cache_frequency:
                torch.cuda.empty_cache()
                self.last_cache_clear_batch = self.batch_count
                logger.debug("Cleared CUDA cache")

        # Adjust gradient accumulation based on memory usage
        if profile.memory_utilization > self.config.memory_threshold:
            current_steps = self.gradient_accumulator.accumulation_steps
            new_steps = min(current_steps * 2, self.config.max_gradient_accumulation_steps)
            if new_steps > current_steps:
                self.gradient_accumulator.adjust_accumulation_steps(new_steps)

    def handle_training_step(
        self,
        loss: torch.Tensor,
        optimizer: torch.optim.Optimizer,
        scaler: GradScaler | None = None,
    ) -> tuple[bool, float]:
        """Handle a training step with memory optimization.

        Args:
            loss: Training loss
            optimizer: Optimizer
            scaler: Gradient scaler for mixed precision (optional)

        Returns:
            Tuple of (optimizer_stepped, accumulated_loss)
        """
        self.batch_count += 1

        # Accumulate gradients
        scaled_loss = self.gradient_accumulator.accumulate_gradients(loss)

        # Backward pass
        if scaler is not None:
            scaler.scale(scaled_loss).backward()
        else:
            scaled_loss.backward()

        # Check if we should step the optimizer
        should_step, accumulated_loss = self.gradient_accumulator.step_completed()

        if should_step:
            # Step optimizer
            if scaler is not None:
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()

            optimizer.zero_grad()

            # Record successful batch
            self.batch_size_manager.record_successful_batch()

            # Try to increase batch size if conditions are met
            self.batch_size_manager.increase_batch_size()

        # Perform memory optimization
        self.optimize_memory_usage(self.batch_count)

        return should_step, accumulated_loss

    def handle_oom_error(self) -> dict[str, Any]:
        """Handle out-of-memory error with recovery strategies.

        Returns:
            Dictionary with recovery information
        """
        logger.warning("Handling OOM error with memory optimization")

        # Reduce batch size
        new_batch_size = self.batch_size_manager.handle_oom_error()

        # Increase gradient accumulation to maintain effective batch size
        current_accumulation = self.gradient_accumulator.accumulation_steps
        new_accumulation = min(current_accumulation * 2, self.config.max_gradient_accumulation_steps)
        self.gradient_accumulator.adjust_accumulation_steps(new_accumulation)

        # Aggressive memory cleanup
        self._aggressive_memory_cleanup()

        return {
            "new_batch_size": new_batch_size,
            "new_accumulation_steps": new_accumulation,
            "recovery_successful": True,
        }

    def _run_garbage_collection(self) -> None:
        """Run garbage collection."""
        collected = gc.collect()
        self.profiler.gc_count += 1
        logger.debug(f"Garbage collection: {collected} objects collected")

    def _aggressive_memory_cleanup(self) -> None:
        """Perform aggressive memory cleanup after OOM."""
        # Clear gradients
        if hasattr(self.model, "zero_grad"):
            self.model.zero_grad()

        # Run garbage collection multiple times
        for _ in range(3):
            gc.collect()

        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        logger.info("Performed aggressive memory cleanup")

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get comprehensive optimization statistics.

        Returns:
            Dictionary with optimization statistics
        """
        stats = {
            "memory_profile": self.profiler.get_memory_summary(),
            "batch_size_stats": self.batch_size_manager.get_stats(),
            "gradient_accumulation": {
                "current_steps": self.gradient_accumulator.accumulation_steps,
                "effective_batch_size": self.gradient_accumulator.get_effective_batch_size(self.batch_size_manager.current_batch_size),
            },
            "optimization_counts": {
                "total_batches": self.batch_count,
                "gc_runs": self.profiler.gc_count,
                "cache_clears": max(0, (self.batch_count // self.config.clear_cache_frequency)),
            },
        }

        return stats

    def log_optimization_summary(self) -> None:
        """Log summary of memory optimization results."""
        stats = self.get_optimization_stats()

        logger.info("Memory Optimization Summary:")
        logger.info(f"  Peak memory usage: {stats['memory_profile'].get('peak_memory_mb', 0):.1f} MB")
        logger.info(f"  Average memory usage: {stats['memory_profile'].get('avg_memory_mb', 0):.1f} MB")
        logger.info(f"  Current batch size: {stats['batch_size_stats']['current_batch_size']}")
        logger.info(f"  Effective batch size: {stats['gradient_accumulation']['effective_batch_size']}")
        logger.info(f"  OOM errors handled: {stats['batch_size_stats']['oom_count']}")
        logger.info(f"  GC runs: {stats['optimization_counts']['gc_runs']}")


def create_memory_optimizer(
    model: nn.Module,
    initial_batch_size: int,
    gradient_accumulation_steps: int = 1,
    config: MemoryOptimizationConfig | None = None,
) -> MemoryOptimizer:
    """Create memory optimizer with default configuration.

    Args:
        model: PyTorch model
        initial_batch_size: Initial batch size
        gradient_accumulation_steps: Initial gradient accumulation steps
        config: Memory optimization configuration (optional)

    Returns:
        MemoryOptimizer instance
    """
    if config is None:
        config = MemoryOptimizationConfig()

    return MemoryOptimizer(model, config, initial_batch_size, gradient_accumulation_steps)
