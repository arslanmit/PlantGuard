"""Central memory configuration for PlantGuard.

This module provides centralized memory limits and configuration
to ensure consistent 4GB memory usage across all systems.
"""

# Global Memory Configuration
# =========================
# All memory limits in the PlantGuard project are set to 4GB maximum
# to ensure consistent performance across different hardware configurations.

# Memory limits in different units
from typing import Any, Dict, List, Optional, Tuple, Union, Generator

MEMORY_LIMIT_GB = 4.0  # 4 GB maximum memory usage
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024  # 4096 MB
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_MB * 1024 * 1024  # bytes

# Performance and testing baselines (in MB)
MEMORY_BASELINE_MAX = MEMORY_LIMIT_MB * 0.35  # 1433 MB (35% of limit for baseline)
MEMORY_TRAINING_MAX = MEMORY_LIMIT_MB * 0.5  # 2048 MB (50% of limit for training)
MEMORY_REGISTRY_MAX = MEMORY_LIMIT_MB * 0.375  # 1536 MB (37.5% of limit for registry)
MEMORY_ADAPTER_MAX = MEMORY_LIMIT_MB * 0.5  # 2048 MB (50% of limit for adapter)

# Memory optimization thresholds
MEMORY_WARNING_THRESHOLD = 0.8  # Warn at 80% of limit (3.2GB)
MEMORY_CRITICAL_THRESHOLD = 0.9  # Critical at 90% of limit (3.6GB)
MEMORY_OOM_THRESHOLD = 0.95  # OOM prevention at 95% of limit (3.8GB)

# Batch size and training parameters optimized for 4GB
DEFAULT_BATCH_SIZE = 16
MIN_BATCH_SIZE = 8
MAX_BATCH_SIZE = 32
GRADIENT_ACCUMULATION_STEPS = 4

# Memory-related training settings
ENABLE_MIXED_PRECISION = True
ENABLE_GRADIENT_CHECKPOINTING = True
PIN_MEMORY = False  # Disabled to save memory
PERSISTENT_WORKERS = False  # Disabled to save memory
DEFAULT_NUM_WORKERS = 2  # Limited workers to save memory


def get_memory_config() -> dict:
    """Get complete memory configuration dictionary.

    Returns:
        Dictionary with all memory configuration values
    """
    return {
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "memory_limit_mb": MEMORY_LIMIT_MB,
        "memory_baseline_max": MEMORY_BASELINE_MAX,
        "memory_training_max": MEMORY_TRAINING_MAX,
        "memory_registry_max": MEMORY_REGISTRY_MAX,
        "memory_adapter_max": MEMORY_ADAPTER_MAX,
        "memory_warning_threshold": MEMORY_WARNING_THRESHOLD,
        "memory_critical_threshold": MEMORY_CRITICAL_THRESHOLD,
        "memory_oom_threshold": MEMORY_OOM_THRESHOLD,
        "default_batch_size": DEFAULT_BATCH_SIZE,
        "min_batch_size": MIN_BATCH_SIZE,
        "max_batch_size": MAX_BATCH_SIZE,
        "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
        "enable_mixed_precision": ENABLE_MIXED_PRECISION,
        "enable_gradient_checkpointing": ENABLE_GRADIENT_CHECKPOINTING,
        "pin_memory": PIN_MEMORY,
        "persistent_workers": PERSISTENT_WORKERS,
        "default_num_workers": DEFAULT_NUM_WORKERS,
    }


def validate_memory_usage(current_memory_mb: float) -> tuple[bool, str]:
    """Validate current memory usage against limits.

    Args:
        current_memory_mb: Current memory usage in MB

    Returns:
        Tuple of (is_valid, message)
    """
    if current_memory_mb > MEMORY_LIMIT_MB:
        return False, f"Memory usage {current_memory_mb:.1f}MB exceeds 4GB limit"
    elif current_memory_mb > MEMORY_LIMIT_MB * MEMORY_CRITICAL_THRESHOLD:
        return (
            False,
            f"Memory usage {current_memory_mb:.1f}MB in critical zone (>{MEMORY_LIMIT_MB * MEMORY_CRITICAL_THRESHOLD:.1f}MB)",
        )
    elif current_memory_mb > MEMORY_LIMIT_MB * MEMORY_WARNING_THRESHOLD:
        return (
            True,
            f"Memory usage {current_memory_mb:.1f}MB in warning zone (>{MEMORY_LIMIT_MB * MEMORY_WARNING_THRESHOLD:.1f}MB)",
        )
    else:
        return True, f"Memory usage {current_memory_mb:.1f}MB is within normal limits"
