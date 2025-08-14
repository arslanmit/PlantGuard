"""Resource management utilities for production training pipeline.

This module provides automatic resource detection, memory optimization,
and hardware-specific configuration for efficient training.
"""

import logging
import platform
import subprocess  # nosec B404  # nosec B404
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

logger = logging.getLogger(__name__)


@dataclass
class ResourceInfo:
    """Information about available system resources."""

    # Device information
    device_type: str  # 'cuda', 'mps', 'cpu'
    device_name: str
    device_count: int

    # Memory information (in GB)
    total_memory: float
    available_memory: float

    # CPU information
    cpu_count: int
    cpu_name: str

    # System information
    platform: str
    python_version: str
    pytorch_version: str

    # Capabilities
    mixed_precision_supported: bool
    distributed_training_supported: bool


class ResourceManager:
    """Manages system resources and provides optimization recommendations."""

    def __init__(self) -> None:
        """Initialize resource manager."""
        self._resource_info: ResourceInfo | None = None
        self._optimal_batch_sizes: dict[str, int] = {}

    def detect_resources(self) -> ResourceInfo:
        """Detect available system resources.

        Returns:
            ResourceInfo containing system capabilities
        """
        if self._resource_info is None:
            self._resource_info = self._gather_resource_info()

        return self._resource_info

    def _gather_resource_info(self) -> ResourceInfo:
        """Gather comprehensive resource information."""
        # Detect device type and capabilities
        device_type, device_name, device_count = self._detect_device()

        # Get memory information
        total_memory, available_memory = self._get_memory_info(device_type)

        # Get CPU information
        cpu_count, cpu_name = self._get_cpu_info()

        # Check capabilities
        mixed_precision_supported = self._check_mixed_precision_support(device_type)
        distributed_training_supported = self._check_distributed_support()

        return ResourceInfo(
            device_type=device_type,
            device_name=device_name,
            device_count=device_count,
            total_memory=total_memory,
            available_memory=available_memory,
            cpu_count=cpu_count,
            cpu_name=cpu_name,
            platform=platform.system(),
            python_version=sys.version.split()[0],
            pytorch_version=torch.__version__,
            mixed_precision_supported=mixed_precision_supported,
            distributed_training_supported=distributed_training_supported,
        )

    def _detect_device(self) -> tuple[str, str, int]:
        """Detect the best available device.

        Returns:
            Tuple of (device_type, device_name, device_count)
        """
        # Check for CUDA
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown CUDA"
            logger.info(f"CUDA detected: {device_count} device(s), primary: {device_name}")
            return "cuda", device_name, device_count

        # Check for MPS (Apple Silicon)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device_name = "Apple Silicon GPU"
            logger.info("MPS (Apple Silicon) detected")
            return "mps", device_name, 1

        # Fallback to CPU
        cpu_name = platform.processor() or "Unknown CPU"
        cpu_count = torch.get_num_threads()
        logger.info(f"Using CPU: {cpu_name} ({cpu_count} threads)")
        return "cpu", cpu_name, cpu_count

    def _get_memory_info(self, device_type: str) -> tuple[float, float]:
        """Get memory information for the specified device type.

        Args:
            device_type: Type of device ('cuda', 'mps', 'cpu')

        Returns:
            Tuple of (total_memory_gb, available_memory_gb)
        """
        if device_type == "cuda" and torch.cuda.is_available():
            # Get GPU memory
            total_memory = torch.cuda.get_device_properties(0).total_memory
            allocated_memory = torch.cuda.memory_allocated(0)
            available_memory = total_memory - allocated_memory

            total_gb = total_memory / (1024**3)
            available_gb = available_memory / (1024**3)

            logger.info(f"GPU Memory: {available_gb:.1f}GB available / {total_gb:.1f}GB total")
            return total_gb, available_gb

        elif device_type == "mps":
            # For MPS, we can't directly query memory, so estimate based on system
            try:
                # Try to get system memory as approximation
                import psutil

                memory = psutil.virtual_memory()
                total_gb = memory.total / (1024**3)
                available_gb = memory.available / (1024**3)

                # MPS typically uses shared memory, so use a fraction
                mps_total = min(total_gb * 0.7, 32.0)  # Assume max 32GB or 70% of system
                mps_available = min(available_gb * 0.7, mps_total)

                logger.info(
                    f"MPS Memory (estimated): {mps_available:.1f}GB available / "
                    f"{mps_total:.1f}GB total"
                )
                return mps_total, mps_available
            except ImportError:
                logger.warning("psutil not available, using default MPS memory estimates")
                return 16.0, 12.0  # Conservative defaults

        else:
            # CPU memory
            try:
                import psutil

                memory = psutil.virtual_memory()
                total_gb = memory.total / (1024**3)
                available_gb = memory.available / (1024**3)

                logger.info(
                    f"System Memory: {available_gb:.1f}GB available / {total_gb:.1f}GB total"
                )
                return total_gb, available_gb
            except ImportError:
                logger.warning("psutil not available, using default memory estimates")
                return 8.0, 4.0  # Conservative defaults

    def _get_cpu_info(self) -> tuple[int, str]:
        """Get CPU information.

        Returns:
            Tuple of (cpu_count, cpu_name)
        """
        cpu_count = torch.get_num_threads()

        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(  # nosec S603 S607
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                cpu_name = result.stdout.strip()
            elif platform.system() == "Linux":
                with Path("/proc/cpuinfo").open() as f:
                    for line in f:
                        if line.startswith("model name"):
                            cpu_name = line.split(":")[1].strip()
                            break
                    else:
                        cpu_name = "Unknown Linux CPU"
            else:
                cpu_name = platform.processor() or "Unknown CPU"
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            cpu_name = platform.processor() or "Unknown CPU"

        return cpu_count, cpu_name

    def _check_mixed_precision_support(self, device_type: str) -> bool:
        """Check if mixed precision training is supported.

        Args:
            device_type: Type of device

        Returns:
            True if mixed precision is supported
        """
        if device_type == "cuda":
            # Check for Tensor Core support (compute capability >= 7.0)
            if torch.cuda.is_available():
                major, minor = torch.cuda.get_device_capability(0)
                compute_capability = float(major) + float(minor) / 10
                return bool(compute_capability >= 7.0)
        elif device_type == "mps":
            # MPS supports mixed precision on newer Apple Silicon
            return True

        # CPU doesn't support mixed precision
        return False

    def _check_distributed_support(self) -> bool:
        """Check if distributed training is supported.

        Returns:
            True if distributed training is available
        """
        return bool(torch.distributed.is_available())

    def get_optimal_batch_size(
        self,
        model_size_mb: float = 100.0,
        image_size: tuple[int, int] = (224, 224),
        channels: int = 3,
        safety_factor: float = 0.8,
    ) -> int:
        """Calculate optimal batch size based on available memory.

        Args:
            model_size_mb: Estimated model size in MB
            image_size: Input image dimensions (height, width)
            channels: Number of input channels
            safety_factor: Safety factor to avoid OOM (0.0-1.0)

        Returns:
            Recommended batch size
        """
        resource_info = self.detect_resources()

        # Calculate memory per sample (forward + backward pass)
        h, w = image_size
        bytes_per_pixel = 4  # float32

        # Input tensor memory
        input_memory_mb = (h * w * channels * bytes_per_pixel) / (1024**2)

        # Estimate gradient and activation memory (rough approximation)
        # Forward pass activations: ~2x input size for ResNet-like models
        # Backward pass gradients: ~1x model size
        activation_memory_mb = input_memory_mb * 2
        gradient_memory_mb = model_size_mb

        # Total memory per sample
        memory_per_sample_mb = input_memory_mb + activation_memory_mb + gradient_memory_mb

        # Available memory in MB
        available_memory_mb = resource_info.available_memory * 1024 * safety_factor

        # Reserve memory for model weights and optimizer states
        reserved_memory_mb = model_size_mb * 3  # Model + optimizer states
        usable_memory_mb = max(available_memory_mb - reserved_memory_mb, 100)

        # Calculate batch size
        optimal_batch_size = max(1, int(usable_memory_mb / memory_per_sample_mb))

        # Apply device-specific constraints
        if resource_info.device_type == "cpu":
            # CPU training is slower, use smaller batches
            optimal_batch_size = min(optimal_batch_size, 16)
        elif resource_info.device_type == "mps":
            # MPS has some limitations, be conservative
            optimal_batch_size = min(optimal_batch_size, 64)

        # Ensure power of 2 for better performance
        optimal_batch_size = self._round_to_power_of_2(optimal_batch_size)

        logger.info(
            f"Calculated optimal batch size: {optimal_batch_size} "
            f"(Memory per sample: {memory_per_sample_mb:.1f}MB, "
            f"Usable memory: {usable_memory_mb:.1f}MB)"
        )

        return optimal_batch_size

    def _round_to_power_of_2(self, value: int) -> int:
        """Round value down to nearest power of 2.

        Args:
            value: Input value

        Returns:
            Nearest power of 2 (rounded down)
        """
        if value <= 0:
            return 1

        # Find the highest power of 2 less than or equal to value
        power = 1
        while power * 2 <= value:
            power *= 2

        return power

    def get_optimal_num_workers(self) -> int:
        """Get optimal number of data loading workers.

        Returns:
            Recommended number of workers
        """
        resource_info = self.detect_resources()

        # Base on CPU count but consider device type
        if resource_info.device_type == "cpu":
            # For CPU training, leave some cores for training
            num_workers = max(1, resource_info.cpu_count // 2)
        else:
            # For GPU/MPS training, can use more workers
            num_workers = min(resource_info.cpu_count, 8)  # Cap at 8 to avoid overhead

        logger.info(f"Recommended number of workers: {num_workers}")
        return num_workers

    def optimize_training_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Optimize training configuration based on available resources.

        Args:
            config: Training configuration dictionary

        Returns:
            Optimized configuration dictionary
        """
        resource_info = self.detect_resources()
        optimized_config = config.copy()

        # Auto-detect device
        if config.get("device") == "auto":
            optimized_config["device"] = resource_info.device_type

        # Optimize batch size if not specified or if auto-optimization requested
        if config.get("batch_size") == "auto" or config.get("auto_batch_size", False):
            model_arch = config.get("model_architecture", "resnet50")
            model_size = self._estimate_model_size(model_arch)
            optimal_batch_size = self.get_optimal_batch_size(model_size)
            optimized_config["batch_size"] = optimal_batch_size

        # Optimize number of workers
        if config.get("num_workers") == "auto":
            optimized_config["num_workers"] = self.get_optimal_num_workers()

        # Adjust mixed precision based on device capabilities
        if config.get("mixed_precision") == "auto":
            optimized_config["mixed_precision"] = resource_info.mixed_precision_supported
        elif config.get("mixed_precision") and not resource_info.mixed_precision_supported:
            logger.warning("Mixed precision requested but not supported, disabling")
            optimized_config["mixed_precision"] = False

        # Adjust pin_memory based on device
        if resource_info.device_type == "cpu":
            optimized_config["pin_memory"] = False

        # Log optimization results
        self._log_optimization_results(config, optimized_config, resource_info)

        return optimized_config

    def _estimate_model_size(self, architecture: str) -> float:
        """Estimate model size in MB for common architectures.

        Args:
            architecture: Model architecture name

        Returns:
            Estimated model size in MB
        """
        size_estimates = {
            "resnet18": 45,
            "resnet34": 85,
            "resnet50": 100,
            "resnet101": 170,
            "resnet152": 230,
        }

        return size_estimates.get(architecture.lower(), 100)  # Default to ResNet50 size

    def _log_optimization_results(
        self,
        original_config: dict[str, Any],
        optimized_config: dict[str, Any],
        resource_info: ResourceInfo,
    ) -> None:
        """Log the results of configuration optimization.

        Args:
            original_config: Original configuration
            optimized_config: Optimized configuration
            resource_info: Detected resource information
        """
        logger.info("=== Resource Detection Results ===")
        logger.info(f"Device: {resource_info.device_type} ({resource_info.device_name})")
        logger.info(f"Memory: {resource_info.available_memory:.1f}GB available")
        logger.info(f"CPU: {resource_info.cpu_name} ({resource_info.cpu_count} cores)")
        mixed_precision_status = (
            "Supported" if resource_info.mixed_precision_supported else "Not supported"
        )
        logger.info(f"Mixed Precision: {mixed_precision_status}")

        logger.info("=== Configuration Optimizations ===")

        changes = []
        for key in ["device", "batch_size", "num_workers", "mixed_precision", "pin_memory"]:
            if key in optimized_config and optimized_config[key] != original_config.get(key):
                old_val = original_config.get(key, "not set")
                new_val = optimized_config[key]
                changes.append(f"{key}: {old_val} → {new_val}")

        if changes:
            for change in changes:
                logger.info(f"  {change}")
        else:
            logger.info("  No optimizations needed")

    def get_memory_usage(self) -> dict[str, float]:
        """Get current memory usage information.

        Returns:
            Dictionary with memory usage statistics (in GB)
        """
        resource_info = self.detect_resources()
        usage = {}

        if resource_info.device_type == "cuda" and torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)

            usage.update(
                {
                    "gpu_allocated": allocated,
                    "gpu_reserved": reserved,
                    "gpu_total": total,
                    "gpu_free": total - reserved,
                }
            )

        try:
            import psutil

            memory = psutil.virtual_memory()
            usage.update(
                {
                    "system_total": memory.total / (1024**3),
                    "system_available": memory.available / (1024**3),
                    "system_used": memory.used / (1024**3),
                    "system_percent": memory.percent,
                }
            )
        except ImportError:
            logger.debug("psutil not available, skipping system memory info")

        return usage

    def clear_memory_cache(self) -> None:
        """Clear memory caches to free up memory."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("Cleared CUDA memory cache")

        # Force garbage collection
        import gc

        gc.collect()
        logger.info("Performed garbage collection")


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance.

    Returns:
        ResourceManager instance
    """
    if not hasattr(get_resource_manager, "_instance"):
        get_resource_manager._instance = ResourceManager()  # type: ignore[attr-defined]
    return get_resource_manager._instance  # type: ignore[attr-defined,no-any-return]


def detect_optimal_config(base_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Detect optimal training configuration for current system.

    Args:
        base_config: Base configuration to optimize (optional)

    Returns:
        Optimized configuration dictionary
    """
    if base_config is None:
        base_config = {
            "device": "auto",
            "batch_size": "auto",
            "num_workers": "auto",
            "mixed_precision": "auto",
        }

    resource_manager = get_resource_manager()
    return resource_manager.optimize_training_config(base_config)
