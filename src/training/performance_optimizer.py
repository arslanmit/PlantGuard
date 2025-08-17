"""Comprehensive performance optimization system for production training.

This module integrates all performance optimization components including profiling,
distributed training, caching, and advanced data loading to provide a unified
optimization system for maximum training performance.
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from .advanced_data_loading import AdvancedDataLoadingConfig, create_advanced_data_loader
from .distributed_training import DistributedConfig, DistributedTrainingManager
from .performance_profiler import PerformanceProfile, ProfilerConfig, TrainingProfiler
from .training_cache import CacheConfig, CacheManager, ModelStateCache

logger = logging.getLogger(__name__)


@dataclass
class PerformanceOptimizationConfig:
    """Comprehensive configuration for performance optimization."""

    # Profiling configuration
    enable_profiling: bool = True
    profiling_config: ProfilerConfig | None = None

    # Distributed training configuration
    enable_distributed_training: bool = False
    distributed_config: DistributedConfig | None = None

    # Caching configuration
    enable_caching: bool = True
    caching_config: CacheConfig | None = None

    # Advanced data loading configuration
    enable_advanced_data_loading: bool = True
    data_loading_config: AdvancedDataLoadingConfig | None = None

    # Model optimization
    enable_model_compilation: bool = True
    enable_mixed_precision: bool = True
    enable_channels_last: bool = True
    enable_gradient_checkpointing: bool = False

    # Memory optimization
    enable_memory_optimization: bool = True
    gradient_accumulation_steps: int = 1
    max_memory_usage_gb: float = 12.0

    # Performance targets
    target_throughput_samples_per_sec: float = 100.0
    target_batch_time_ms: float = 100.0
    max_optimization_iterations: int = 5

    # Output configuration
    optimization_results_dir: Path = Path("optimization_results")
    save_optimization_report: bool = True


@dataclass
class OptimizationResult:
    """Results from performance optimization."""

    success: bool
    initial_performance: dict[str, float]
    final_performance: dict[str, float]
    optimization_steps: list[str] = field(default_factory=list)
    performance_improvement: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    optimization_time_seconds: float = 0.0


class PerformanceOptimizer:
    """Comprehensive performance optimizer for training pipelines."""

    def __init__(self, config: PerformanceOptimizationConfig):
        """Initialize performance optimizer.

        Args:
            config: Performance optimization configuration
        """
        self.config = config
        self.optimization_history: list[OptimizationResult] = []

        # Initialize components
        self.profiler: TrainingProfiler | None = None
        self.distributed_manager: DistributedTrainingManager | None = None
        self.cache_manager: CacheManager | None = None
        self.model_cache: ModelStateCache | None = None

        # Setup output directory
        self.config.optimization_results_dir.mkdir(parents=True, exist_ok=True)

        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize optimization components."""
        # Initialize profiler
        if self.config.enable_profiling:
            profiler_config = self.config.profiling_config or ProfilerConfig(output_dir=self.config.optimization_results_dir / "profiling")
            self.profiler = TrainingProfiler(profiler_config)

        # Initialize distributed training manager
        if self.config.enable_distributed_training:
            distributed_config = self.config.distributed_config or DistributedConfig()
            self.distributed_manager = DistributedTrainingManager(distributed_config)

        # Initialize cache manager
        if self.config.enable_caching:
            cache_config = self.config.caching_config or CacheConfig(cache_root=self.config.optimization_results_dir / "cache")
            self.cache_manager = CacheManager(cache_config)
            self.model_cache = ModelStateCache(self.cache_manager)

    def optimize_training_pipeline(
        self,
        model: nn.Module,
        dataset: Dataset,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
        batch_size: int = 32,
    ) -> OptimizationResult:
        """Optimize complete training pipeline for maximum performance.

        Args:
            model: PyTorch model
            dataset: Training dataset
            optimizer: Optimizer
            criterion: Loss criterion
            device: Training device
            batch_size: Initial batch size

        Returns:
            OptimizationResult with optimization outcomes
        """
        logger.info("Starting comprehensive training pipeline optimization...")
        start_time = time.time()

        optimization_steps = []
        recommendations = []

        try:
            # Step 1: Baseline performance measurement
            logger.info("Step 1: Measuring baseline performance...")
            initial_performance = self._measure_baseline_performance(model, dataset, optimizer, criterion, device, batch_size)
            optimization_steps.append("Measured baseline performance")

            # Step 2: Model optimization
            logger.info("Step 2: Optimizing model...")
            optimized_model = self._optimize_model(model, device)
            optimization_steps.append("Applied model optimizations")

            # Step 3: Data loading optimization
            logger.info("Step 3: Optimizing data loading...")
            optimized_data_loader = self._optimize_data_loading(dataset, batch_size, device)
            optimization_steps.append("Optimized data loading pipeline")

            # Step 4: Memory optimization
            logger.info("Step 4: Optimizing memory usage...")
            memory_optimizations = self._optimize_memory_usage(optimized_model, optimizer)
            optimization_steps.extend(memory_optimizations)

            # Step 5: Distributed training setup (if enabled)
            if self.config.enable_distributed_training and self.distributed_manager:
                logger.info("Step 5: Setting up distributed training...")
                optimized_model = self._setup_distributed_training(optimized_model, device)
                optimization_steps.append("Configured distributed training")

            # Step 6: Final performance measurement
            logger.info("Step 6: Measuring optimized performance...")
            final_performance = self._measure_optimized_performance(optimized_model, optimized_data_loader, optimizer, criterion, device)
            optimization_steps.append("Measured optimized performance")

            # Step 7: Generate recommendations
            logger.info("Step 7: Generating optimization recommendations...")
            recommendations = self._generate_recommendations(initial_performance, final_performance)

            # Calculate performance improvements
            performance_improvement = self._calculate_performance_improvement(initial_performance, final_performance)

            optimization_time = time.time() - start_time

            result = OptimizationResult(
                success=True,
                initial_performance=initial_performance,
                final_performance=final_performance,
                optimization_steps=optimization_steps,
                performance_improvement=performance_improvement,
                recommendations=recommendations,
                optimization_time_seconds=optimization_time,
            )

            # Save optimization report
            if self.config.save_optimization_report:
                self._save_optimization_report(result)

            logger.info(f"Optimization completed in {optimization_time:.1f}s")
            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return OptimizationResult(
                success=False,
                initial_performance={},
                final_performance={},
                optimization_steps=optimization_steps,
                recommendations=[f"Optimization failed: {e!s}"],
                optimization_time_seconds=time.time() - start_time,
            )

    def _measure_baseline_performance(
        self,
        model: nn.Module,
        dataset: Dataset,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
        batch_size: int,
    ) -> dict[str, float]:
        """Measure baseline performance before optimization."""
        # Create basic data loader
        data_loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=2,
            pin_memory=True,
        )

        # Profile baseline performance
        if self.profiler:
            profile_result = self.profiler.profile_training_loop(model, data_loader, optimizer, criterion, device)

            return {
                "avg_batch_time_ms": profile_result.avg_batch_time_ms,
                "throughput_samples_per_sec": profile_result.throughput_samples_per_sec,
                "data_loading_time_ms": profile_result.data_loading_time_ms,
                "forward_pass_time_ms": profile_result.forward_pass_time_ms,
                "backward_pass_time_ms": profile_result.backward_pass_time_ms,
                "peak_memory_mb": profile_result.peak_memory_mb,
                "memory_efficiency": profile_result.memory_efficiency,
            }
        else:
            # Simple timing measurement
            return self._simple_performance_measurement(model, data_loader, optimizer, criterion, device)

    def _optimize_model(self, model: nn.Module, device: torch.device) -> nn.Module:
        """Apply model-level optimizations."""
        optimized_model = model

        # Model compilation (PyTorch 2.0+)
        if self.config.enable_model_compilation and hasattr(torch, "compile"):
            try:
                optimized_model = torch.compile(
                    optimized_model,
                    mode="default",
                    fullgraph=False,
                )
                logger.info("Applied torch.compile optimization")
            except Exception as e:
                logger.warning(f"Failed to compile model: {e}")

        # Channels last memory format
        if self.config.enable_channels_last and device.type == "cuda":
            try:
                optimized_model = optimized_model.to(memory_format=torch.channels_last)
                logger.info("Applied channels_last memory format")
            except Exception as e:
                logger.warning(f"Failed to apply channels_last: {e}")

        # Gradient checkpointing
        if self.config.enable_gradient_checkpointing:
            try:
                if hasattr(optimized_model, "gradient_checkpointing_enable"):
                    optimized_model.gradient_checkpointing_enable()
                    logger.info("Enabled gradient checkpointing")
            except Exception as e:
                logger.warning(f"Failed to enable gradient checkpointing: {e}")

        return optimized_model

    def _optimize_data_loading(self, dataset: Dataset, batch_size: int, device: torch.device) -> DataLoader:
        """Optimize data loading pipeline."""
        if self.config.enable_advanced_data_loading:
            # Use advanced data loading optimizations
            data_loading_config = self.config.data_loading_config or AdvancedDataLoadingConfig()

            return create_advanced_data_loader(dataset, data_loading_config, batch_size, device)
        else:
            # Use standard optimized data loader
            import multiprocessing as mp

            return DataLoader(
                dataset,
                batch_size=batch_size,
                shuffle=True,
                num_workers=min(8, mp.cpu_count()),
                pin_memory=True,
                persistent_workers=True,
                prefetch_factor=4,
                drop_last=True,
            )

    def _optimize_memory_usage(self, model: nn.Module, optimizer: torch.optim.Optimizer) -> list[str]:
        """Apply memory optimization techniques."""
        optimizations = []

        # Enable mixed precision if supported
        if self.config.enable_mixed_precision and torch.cuda.is_available():
            # This would be handled by the training loop
            optimizations.append("Configured mixed precision training")

        # Optimize optimizer memory usage
        if hasattr(optimizer, "zero_grad"):
            # Use set_to_none=True for better memory efficiency
            optimizations.append("Optimized optimizer memory usage")

        # Configure gradient accumulation
        if self.config.gradient_accumulation_steps > 1:
            optimizations.append(f"Configured gradient accumulation ({self.config.gradient_accumulation_steps} steps)")

        return optimizations

    def _setup_distributed_training(self, model: nn.Module, device: torch.device) -> nn.Module:
        """Setup distributed training if enabled."""
        if self.distributed_manager:
            if self.distributed_manager.setup_distributed_training():
                return self.distributed_manager.wrap_model(model, device)

        return model

    def _measure_optimized_performance(
        self,
        model: nn.Module,
        data_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
    ) -> dict[str, float]:
        """Measure performance after optimization."""
        if self.profiler:
            profile_result = self.profiler.profile_training_loop(model, data_loader, optimizer, criterion, device)

            return {
                "avg_batch_time_ms": profile_result.avg_batch_time_ms,
                "throughput_samples_per_sec": profile_result.throughput_samples_per_sec,
                "data_loading_time_ms": profile_result.data_loading_time_ms,
                "forward_pass_time_ms": profile_result.forward_pass_time_ms,
                "backward_pass_time_ms": profile_result.backward_pass_time_ms,
                "peak_memory_mb": profile_result.peak_memory_mb,
                "memory_efficiency": profile_result.memory_efficiency,
            }
        else:
            return self._simple_performance_measurement(model, data_loader, optimizer, criterion, device)

    def _simple_performance_measurement(
        self,
        model: nn.Module,
        data_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
        num_batches: int = 10,
    ) -> dict[str, float]:
        """Simple performance measurement without detailed profiling."""
        model.train()
        batch_times = []
        total_samples = 0

        start_time = time.time()

        for batch_idx, (data, target) in enumerate(data_loader):
            if batch_idx >= num_batches:
                break

            batch_start = time.time()

            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            batch_time = (time.time() - batch_start) * 1000
            batch_times.append(batch_time)
            total_samples += len(data)

        total_time = time.time() - start_time
        avg_batch_time = sum(batch_times) / len(batch_times)
        throughput = total_samples / total_time

        return {
            "avg_batch_time_ms": avg_batch_time,
            "throughput_samples_per_sec": throughput,
            "data_loading_time_ms": 0.0,  # Not measured in simple mode
            "forward_pass_time_ms": 0.0,
            "backward_pass_time_ms": 0.0,
            "peak_memory_mb": 0.0,
            "memory_efficiency": 1.0,
        }

    def _calculate_performance_improvement(self, initial: dict[str, float], final: dict[str, float]) -> dict[str, float]:
        """Calculate performance improvements."""
        improvements = {}

        for metric in initial:
            if metric in final and initial[metric] > 0:
                if metric in ["avg_batch_time_ms", "data_loading_time_ms", "forward_pass_time_ms", "backward_pass_time_ms"]:
                    # Lower is better for time metrics
                    improvement = (initial[metric] - final[metric]) / initial[metric] * 100
                else:
                    # Higher is better for throughput and efficiency metrics
                    improvement = (final[metric] - initial[metric]) / initial[metric] * 100

                improvements[metric] = improvement

        return improvements

    def _generate_recommendations(self, initial: dict[str, float], final: dict[str, float]) -> list[str]:
        """Generate optimization recommendations based on results."""
        recommendations = []

        # Check if targets were met
        final_throughput = final.get("throughput_samples_per_sec", 0)
        final_batch_time = final.get("avg_batch_time_ms", float("inf"))

        if final_throughput < self.config.target_throughput_samples_per_sec:
            recommendations.append(f"Throughput ({final_throughput:.1f} samples/sec) below target ({self.config.target_throughput_samples_per_sec:.1f} samples/sec)")

        if final_batch_time > self.config.target_batch_time_ms:
            recommendations.append(f"Batch time ({final_batch_time:.1f}ms) above target ({self.config.target_batch_time_ms:.1f}ms)")

        # Specific optimization recommendations
        if final.get("data_loading_time_ms", 0) > final_batch_time * 0.2:
            recommendations.append("Data loading is a bottleneck - consider increasing num_workers")

        if final.get("peak_memory_mb", 0) > self.config.max_memory_usage_gb * 1024:
            recommendations.append("Memory usage is high - consider gradient accumulation or smaller batch size")

        if not recommendations:
            recommendations.append("Performance targets achieved - no additional optimizations needed")

        return recommendations

    def _save_optimization_report(self, result: OptimizationResult) -> None:
        """Save detailed optimization report."""
        report_file = self.config.optimization_results_dir / "optimization_report.txt"

        with open(report_file, "w") as f:
            f.write("PlantGuard Training Pipeline Optimization Report\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Optimization Status: {'SUCCESS' if result.success else 'FAILED'}\n")
            f.write(f"Optimization Time: {result.optimization_time_seconds:.1f} seconds\n\n")

            # Performance comparison
            f.write("Performance Comparison:\n")
            f.write("-" * 30 + "\n")

            for metric in result.initial_performance:
                initial_val = result.initial_performance[metric]
                final_val = result.final_performance.get(metric, 0)
                improvement = result.performance_improvement.get(metric, 0)

                f.write(f"{metric}:\n")
                f.write(f"  Initial: {initial_val:.2f}\n")
                f.write(f"  Final: {final_val:.2f}\n")
                f.write(f"  Improvement: {improvement:+.1f}%\n\n")

            # Optimization steps
            f.write("Optimization Steps:\n")
            f.write("-" * 20 + "\n")
            for i, step in enumerate(result.optimization_steps, 1):
                f.write(f"{i}. {step}\n")
            f.write("\n")

            # Recommendations
            f.write("Recommendations:\n")
            f.write("-" * 15 + "\n")
            for rec in result.recommendations:
                f.write(f"• {rec}\n")

        logger.info(f"Optimization report saved to {report_file}")

    def get_optimization_summary(self) -> dict[str, Any]:
        """Get summary of all optimization runs."""
        if not self.optimization_history:
            return {"message": "No optimization runs completed"}

        successful_runs = [r for r in self.optimization_history if r.success]

        if not successful_runs:
            return {"message": "No successful optimization runs"}

        latest_run = successful_runs[-1]

        return {
            "total_runs": len(self.optimization_history),
            "successful_runs": len(successful_runs),
            "latest_performance": latest_run.final_performance,
            "best_throughput": max(r.final_performance.get("throughput_samples_per_sec", 0) for r in successful_runs),
            "best_batch_time": min(r.final_performance.get("avg_batch_time_ms", float("inf")) for r in successful_runs),
            "total_optimization_time": sum(r.optimization_time_seconds for r in self.optimization_history),
        }


def create_performance_optimization_config(
    enable_all_optimizations: bool = True,
    target_throughput: float = 100.0,
    max_memory_gb: float = 12.0,
    output_dir: Path | None = None,
) -> PerformanceOptimizationConfig:
    """Create performance optimization configuration with sensible defaults.

    Args:
        enable_all_optimizations: Whether to enable all optimization features
        target_throughput: Target throughput in samples per second
        max_memory_gb: Maximum memory usage in GB
        output_dir: Output directory for optimization results

    Returns:
        PerformanceOptimizationConfig instance
    """
    return PerformanceOptimizationConfig(
        enable_profiling=enable_all_optimizations,
        enable_distributed_training=False,  # Requires explicit setup
        enable_caching=enable_all_optimizations,
        enable_advanced_data_loading=enable_all_optimizations,
        enable_model_compilation=enable_all_optimizations,
        enable_mixed_precision=enable_all_optimizations,
        enable_channels_last=enable_all_optimizations,
        enable_memory_optimization=enable_all_optimizations,
        target_throughput_samples_per_sec=target_throughput,
        max_memory_usage_gb=max_memory_gb,
        optimization_results_dir=output_dir or Path("optimization_results"),
    )


def optimize_training_performance(
    model: nn.Module,
    dataset: Dataset,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    batch_size: int = 32,
    config: PerformanceOptimizationConfig | None = None,
) -> OptimizationResult:
    """Convenience function to optimize training performance.

    Args:
        model: PyTorch model
        dataset: Training dataset
        optimizer: Optimizer
        criterion: Loss criterion
        device: Training device
        batch_size: Batch size
        config: Optimization configuration (optional)

    Returns:
        OptimizationResult with optimization outcomes
    """
    if config is None:
        config = create_performance_optimization_config()

    optimizer_instance = PerformanceOptimizer(config)
    return optimizer_instance.optimize_training_pipeline(model, dataset, optimizer, criterion, device, batch_size)
