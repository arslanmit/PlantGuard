"""Performance profiler for training pipeline bottleneck analysis.

This module provides comprehensive profiling capabilities to identify and analyze
performance bottlenecks in the training pipeline, including data loading, model
forward/backward passes, and memory usage patterns.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil
import torch
from torch.profiler import ProfilerActivity, profile, record_function

logger = logging.getLogger(__name__)


@dataclass
class ProfilerConfig:
    """Configuration for performance profiling."""

    # Profiling activities
    profile_cpu: bool = True
    profile_cuda: bool = True
    profile_memory: bool = True
    record_shapes: bool = True
    with_stack: bool = False

    # Profiling scope
    profile_batches: int = 10
    warmup_batches: int = 2
    skip_first_batches: int = 1

    # Output configuration
    export_chrome_trace: bool = True
    export_tensorboard: bool = True
    output_dir: Path | None = None

    # Memory profiling
    memory_profile_frequency: int = 5
    detailed_memory_analysis: bool = True


@dataclass
class BottleneckAnalysis:
    """Analysis of performance bottlenecks."""

    component: str
    avg_time_ms: float
    percentage_of_total: float
    recommendations: list[str] = field(default_factory=list)
    severity: str = "low"  # low, medium, high, critical


@dataclass
class PerformanceProfile:
    """Comprehensive performance profile results."""

    total_time_ms: float
    avg_batch_time_ms: float
    throughput_samples_per_sec: float

    # Component breakdown
    data_loading_time_ms: float
    forward_pass_time_ms: float
    backward_pass_time_ms: float
    optimizer_step_time_ms: float

    # Memory metrics
    peak_memory_mb: float
    avg_memory_mb: float
    memory_efficiency: float

    # Bottleneck analysis
    bottlenecks: list[BottleneckAnalysis] = field(default_factory=list)

    # Detailed metrics
    detailed_metrics: dict[str, Any] = field(default_factory=dict)


class TrainingProfiler:
    """Comprehensive training pipeline profiler."""

    def __init__(self, config: ProfilerConfig) -> None:
        """Initialize training profiler.

        Args:
            config: Profiler configuration
        """
        self.config = config
        self.metrics: dict[str, list[float]] = defaultdict(list)
        self.memory_snapshots: list[dict[str, float]] = []
        self.batch_times: list[float] = []
        self.component_times: dict[str, list[float]] = defaultdict(list)

        # Setup output directory
        if self.config.output_dir is None:
            self.config.output_dir = Path("profiling_results")
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def profile_training_loop(
        self,
        model: torch.nn.Module,
        train_loader: torch.utils.data.DataLoader,
        optimizer: torch.optim.Optimizer,
        criterion: torch.nn.Module,
        device: torch.device,
    ) -> PerformanceProfile:
        """Profile complete training loop with detailed analysis.

        Args:
            model: PyTorch model
            train_loader: Training data loader
            optimizer: Optimizer
            criterion: Loss criterion
            device: Training device

        Returns:
            PerformanceProfile with comprehensive metrics
        """
        logger.info("Starting comprehensive training profiling...")

        # Setup profiling activities
        activities = []
        if self.config.profile_cpu:
            activities.append(ProfilerActivity.CPU)
        if self.config.profile_cuda and torch.cuda.is_available():
            activities.append(ProfilerActivity.CUDA)

        # Profile training loop
        with profile(
            activities=activities,
            record_shapes=self.config.record_shapes,
            profile_memory=self.config.profile_memory,
            with_stack=self.config.with_stack,
            on_trace_ready=self._trace_handler,
        ) as prof:
            self._run_profiled_training(model, train_loader, optimizer, criterion, device, prof)

        # Analyze results
        profile_result = self._analyze_profile_results()

        # Export results
        self._export_profiling_results(prof, profile_result)

        logger.info("Training profiling completed")
        return profile_result

    def _run_profiled_training(
        self,
        model: torch.nn.Module,
        train_loader: torch.utils.data.DataLoader,
        optimizer: torch.optim.Optimizer,
        criterion: torch.nn.Module,
        device: torch.device,
        prof: profile,
    ) -> None:
        """Run training loop with profiling instrumentation."""
        model.train()
        total_batches = 0

        for batch_idx, (data, target) in enumerate(train_loader):
            if total_batches >= self.config.profile_batches + self.config.warmup_batches:
                break

            batch_start_time = time.time()

            # Skip first few batches for warmup
            if batch_idx < self.config.skip_first_batches:
                continue

            # Data loading profiling
            with record_function("data_loading"):
                data_start = time.time()
                data = data.to(device, non_blocking=True)
                target = target.to(device, non_blocking=True)
                data_time = (time.time() - data_start) * 1000

            # Forward pass profiling
            with record_function("forward_pass"):
                forward_start = time.time()
                optimizer.zero_grad()
                output = model(data)
                loss = criterion(output, target)
                forward_time = (time.time() - forward_start) * 1000

            # Backward pass profiling
            with record_function("backward_pass"):
                backward_start = time.time()
                loss.backward()
                backward_time = (time.time() - backward_start) * 1000

            # Optimizer step profiling
            with record_function("optimizer_step"):
                optimizer_start = time.time()
                optimizer.step()
                optimizer_time = (time.time() - optimizer_start) * 1000

            # Record metrics
            batch_time = (time.time() - batch_start_time) * 1000
            self.batch_times.append(batch_time)
            self.component_times["data_loading"].append(data_time)
            self.component_times["forward_pass"].append(forward_time)
            self.component_times["backward_pass"].append(backward_time)
            self.component_times["optimizer_step"].append(optimizer_time)

            # Memory profiling
            if batch_idx % self.config.memory_profile_frequency == 0:
                self._record_memory_snapshot(batch_idx)

            # Profiler step
            prof.step()
            total_batches += 1

    def _record_memory_snapshot(self, batch_idx: int) -> None:
        """Record memory usage snapshot."""
        # Explicitly type as float-valued metrics to satisfy static typing
        snapshot: dict[str, float] = {"batch_idx": float(batch_idx)}

        if torch.cuda.is_available():
            snapshot.update(
                {
                    "cuda_allocated_mb": torch.cuda.memory_allocated() / 1024**2,
                    "cuda_reserved_mb": torch.cuda.memory_reserved() / 1024**2,
                    "cuda_max_allocated_mb": torch.cuda.max_memory_allocated() / 1024**2,
                }
            )

        # System memory
        process = psutil.Process()
        memory_info = process.memory_info()
        snapshot.update(
            {
                "system_memory_mb": memory_info.rss / 1024**2,
                "system_memory_percent": process.memory_percent(),
            }
        )

        self.memory_snapshots.append(snapshot)

    def _analyze_profile_results(self) -> PerformanceProfile:
        """Analyze profiling results and identify bottlenecks."""
        if not self.batch_times:
            raise ValueError("No profiling data collected")

        # Calculate basic metrics
        total_time_ms = sum(self.batch_times)
        avg_batch_time_ms = total_time_ms / len(self.batch_times)

        # Estimate throughput (assuming batch size from first component)
        estimated_batch_size = 32  # Default assumption
        throughput = (estimated_batch_size * len(self.batch_times)) / (total_time_ms / 1000)

        # Component averages
        data_loading_avg = sum(self.component_times["data_loading"]) / len(self.component_times["data_loading"])
        forward_pass_avg = sum(self.component_times["forward_pass"]) / len(self.component_times["forward_pass"])
        backward_pass_avg = sum(self.component_times["backward_pass"]) / len(self.component_times["backward_pass"])
        optimizer_step_avg = sum(self.component_times["optimizer_step"]) / len(self.component_times["optimizer_step"])

        # Memory metrics
        peak_memory_mb = 0.0
        avg_memory_mb = 0.0
        if self.memory_snapshots:
            if torch.cuda.is_available():
                cuda_memories = [s.get("cuda_allocated_mb", 0) for s in self.memory_snapshots]
                peak_memory_mb = max(cuda_memories)
                avg_memory_mb = sum(cuda_memories) / len(cuda_memories)
            else:
                system_memories = [s.get("system_memory_mb", 0) for s in self.memory_snapshots]
                peak_memory_mb = max(system_memories)
                avg_memory_mb = sum(system_memories) / len(system_memories)

        # Memory efficiency (simplified metric)
        memory_efficiency = min(1.0, avg_memory_mb / max(1.0, peak_memory_mb))

        # Bottleneck analysis
        bottlenecks = self._identify_bottlenecks(data_loading_avg, forward_pass_avg, backward_pass_avg, optimizer_step_avg, avg_batch_time_ms)

        return PerformanceProfile(
            total_time_ms=total_time_ms,
            avg_batch_time_ms=avg_batch_time_ms,
            throughput_samples_per_sec=throughput,
            data_loading_time_ms=data_loading_avg,
            forward_pass_time_ms=forward_pass_avg,
            backward_pass_time_ms=backward_pass_avg,
            optimizer_step_time_ms=optimizer_step_avg,
            peak_memory_mb=peak_memory_mb,
            avg_memory_mb=avg_memory_mb,
            memory_efficiency=memory_efficiency,
            bottlenecks=bottlenecks,
            detailed_metrics={
                "batch_times": self.batch_times,
                "component_times": dict(self.component_times),
                "memory_snapshots": self.memory_snapshots,
            },
        )

    def _identify_bottlenecks(
        self,
        data_loading_avg: float,
        forward_pass_avg: float,
        backward_pass_avg: float,
        optimizer_step_avg: float,
        total_avg: float,
    ) -> list[BottleneckAnalysis]:
        """Identify performance bottlenecks and generate recommendations."""
        bottlenecks = []

        # Analyze each component
        components = {
            "data_loading": data_loading_avg,
            "forward_pass": forward_pass_avg,
            "backward_pass": backward_pass_avg,
            "optimizer_step": optimizer_step_avg,
        }

        for component, avg_time in components.items():
            percentage = (avg_time / total_avg) * 100
            recommendations = []
            severity = "low"

            if component == "data_loading":
                if percentage > 30:
                    severity = "high"
                    recommendations.extend(
                        [
                            "Increase num_workers in DataLoader",
                            "Enable pin_memory and persistent_workers",
                            "Consider data preprocessing optimization",
                            "Use faster storage (SSD) for dataset",
                        ]
                    )
                elif percentage > 15:
                    severity = "medium"
                    recommendations.extend(
                        [
                            "Consider increasing num_workers",
                            "Enable pin_memory for GPU training",
                        ]
                    )

            elif component == "forward_pass":
                if percentage > 50:
                    severity = "high"
                    recommendations.extend(
                        [
                            "Enable mixed precision training",
                            "Consider model compilation (torch.compile)",
                            "Use channels_last memory format",
                            "Optimize model architecture",
                        ]
                    )
                elif percentage > 35:
                    severity = "medium"
                    recommendations.extend(
                        [
                            "Enable mixed precision training",
                            "Consider torch.compile optimization",
                        ]
                    )

            elif component == "backward_pass":
                if percentage > 40:
                    severity = "high"
                    recommendations.extend(
                        [
                            "Enable gradient checkpointing",
                            "Use gradient accumulation",
                            "Consider reducing model complexity",
                        ]
                    )
                elif percentage > 25:
                    severity = "medium"
                    recommendations.extend(
                        [
                            "Consider gradient accumulation",
                            "Enable mixed precision training",
                        ]
                    )

            elif component == "optimizer_step":
                if percentage > 20:
                    severity = "high"
                    recommendations.extend(
                        [
                            "Consider different optimizer (AdamW vs SGD)",
                            "Reduce optimizer overhead with larger batch sizes",
                            "Use gradient accumulation",
                        ]
                    )
                elif percentage > 10:
                    severity = "medium"
                    recommendations.extend(
                        [
                            "Consider optimizer choice",
                            "Use gradient accumulation",
                        ]
                    )

            if percentage > 5:  # Only report significant components
                bottlenecks.append(
                    BottleneckAnalysis(
                        component=component,
                        avg_time_ms=avg_time,
                        percentage_of_total=percentage,
                        recommendations=recommendations,
                        severity=severity,
                    )
                )

        # Sort by percentage (highest first)
        bottlenecks.sort(key=lambda x: x.percentage_of_total, reverse=True)
        return bottlenecks

    def _trace_handler(self, prof: profile) -> None:
        """Handle profiler trace events."""
        # This is called when profiler has trace data ready
        pass

    def _export_profiling_results(self, prof: profile, profile_result: PerformanceProfile) -> None:
        """Export profiling results to various formats."""
        output_dir = self.config.output_dir

        # Skip export if no output directory configured
        if output_dir is None:
            logger.warning("No output directory configured for profiling results")
            return

        # Export Chrome trace
        if self.config.export_chrome_trace:
            trace_file = output_dir / "training_profile.json"
            prof.export_chrome_trace(str(trace_file))
            logger.info(f"Chrome trace exported to {trace_file}")

        # Export TensorBoard logs
        if self.config.export_tensorboard:
            tb_dir = output_dir / "tensorboard"
            tb_dir.mkdir(exist_ok=True)
            # Note: TensorBoard export would require additional setup
            logger.info(f"TensorBoard logs directory: {tb_dir}")

        # Export summary report
        self._export_summary_report(profile_result, output_dir / "profile_summary.txt")

    def _export_summary_report(self, profile_result: PerformanceProfile, output_file: Path) -> None:
        """Export human-readable summary report."""
        with open(output_file, "w") as f:
            f.write("PlantGuard Training Performance Profile\n")
            f.write("=" * 50 + "\n\n")

            # Overall metrics
            f.write("Overall Performance:\n")
            f.write(f"  Total Time: {profile_result.total_time_ms:.1f}ms\n")
            f.write(f"  Average Batch Time: {profile_result.avg_batch_time_ms:.1f}ms\n")
            f.write(f"  Throughput: {profile_result.throughput_samples_per_sec:.1f} samples/sec\n\n")

            # Component breakdown
            f.write("Component Breakdown:\n")
            f.write(f"  Data Loading: {profile_result.data_loading_time_ms:.1f}ms\n")
            f.write(f"  Forward Pass: {profile_result.forward_pass_time_ms:.1f}ms\n")
            f.write(f"  Backward Pass: {profile_result.backward_pass_time_ms:.1f}ms\n")
            f.write(f"  Optimizer Step: {profile_result.optimizer_step_time_ms:.1f}ms\n\n")

            # Memory metrics
            f.write("Memory Usage:\n")
            f.write(f"  Peak Memory: {profile_result.peak_memory_mb:.1f}MB\n")
            f.write(f"  Average Memory: {profile_result.avg_memory_mb:.1f}MB\n")
            f.write(f"  Memory Efficiency: {profile_result.memory_efficiency:.2f}\n\n")

            # Bottlenecks
            if profile_result.bottlenecks:
                f.write("Performance Bottlenecks:\n")
                for bottleneck in profile_result.bottlenecks:
                    f.write(f"\n  {bottleneck.component.upper()} ({bottleneck.severity.upper()}):\n")
                    f.write(f"    Time: {bottleneck.avg_time_ms:.1f}ms ({bottleneck.percentage_of_total:.1f}%)\n")
                    if bottleneck.recommendations:
                        f.write("    Recommendations:\n")
                        for rec in bottleneck.recommendations:
                            f.write(f"      - {rec}\n")

        logger.info(f"Profile summary exported to {output_file}")


class DataLoaderProfiler:
    """Specialized profiler for data loading performance."""

    def __init__(self, config: ProfilerConfig) -> None:
        """Initialize data loader profiler."""
        self.config = config

    def profile_data_loader(self, data_loader: torch.utils.data.DataLoader, device: torch.device) -> dict[str, Any]:
        """Profile data loader performance in detail."""
        logger.info("Profiling data loader performance...")

        batch_times = []
        transfer_times = []
        total_samples = 0

        start_time = time.time()

        for batch_idx, (data, target) in enumerate(data_loader):
            if batch_idx >= self.config.profile_batches:
                break

            batch_start = time.time()

            # Measure data transfer time
            transfer_start = time.time()
            data = data.to(device, non_blocking=True)
            target = target.to(device, non_blocking=True)

            # Synchronize to measure actual transfer time
            if device.type == "cuda":
                torch.cuda.synchronize()

            transfer_time = time.time() - transfer_start
            batch_time = time.time() - batch_start

            batch_times.append(batch_time * 1000)  # Convert to ms
            transfer_times.append(transfer_time * 1000)
            total_samples += len(data)

        total_time = time.time() - start_time

        # Calculate metrics
        avg_batch_time = sum(batch_times) / len(batch_times)
        avg_transfer_time = sum(transfer_times) / len(transfer_times)
        throughput = total_samples / total_time

        # Analyze bottlenecks
        recommendations = []
        if avg_batch_time > 100:  # > 100ms per batch
            recommendations.append("Data loading is slow - increase num_workers")

        if avg_transfer_time > avg_batch_time * 0.3:
            recommendations.append("Data transfer is bottleneck - enable pin_memory")

        if data_loader.num_workers == 0:
            recommendations.append("Enable multiprocessing with num_workers > 0")

        return {
            "avg_batch_time_ms": avg_batch_time,
            "avg_transfer_time_ms": avg_transfer_time,
            "throughput_samples_per_sec": throughput,
            "total_batches": len(batch_times),
            "recommendations": recommendations,
            "detailed_times": {
                "batch_times": batch_times,
                "transfer_times": transfer_times,
            },
        }


def create_profiler_config(
    profile_batches: int = 10,
    output_dir: Path | None = None,
    detailed_analysis: bool = True,
) -> ProfilerConfig:
    """Create profiler configuration with sensible defaults."""
    return ProfilerConfig(
        profile_batches=profile_batches,
        output_dir=output_dir,
        detailed_memory_analysis=detailed_analysis,
        export_chrome_trace=True,
        export_tensorboard=True,
    )


def profile_training_performance(
    model: torch.nn.Module,
    train_loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: torch.nn.Module,
    device: torch.device,
    config: ProfilerConfig | None = None,
) -> PerformanceProfile:
    """Convenience function to profile training performance.

    Args:
        model: PyTorch model
        train_loader: Training data loader
        optimizer: Optimizer
        criterion: Loss criterion
        device: Training device
        config: Profiler configuration (optional)

    Returns:
        PerformanceProfile with comprehensive analysis
    """
    if config is None:
        config = create_profiler_config()

    profiler = TrainingProfiler(config)
    return profiler.profile_training_loop(model, train_loader, optimizer, criterion, device)
