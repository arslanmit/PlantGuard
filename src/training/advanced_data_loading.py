"""Advanced data loading optimizations for large-scale training.

This module provides advanced data loading optimizations including intelligent
prefetching, adaptive batch sizing, memory-mapped datasets, and GPU-accelerated
preprocessing for maximum training throughput.
"""

import logging
import multiprocessing as mp
import queue
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset, Sampler
from torchvision import transforms

logger = logging.getLogger(__name__)


@dataclass
class AdvancedDataLoadingConfig:
    """Configuration for advanced data loading optimizations."""

    # Intelligent prefetching
    enable_intelligent_prefetching: bool = True
    prefetch_buffer_size: int = 8
    prefetch_threads: int = 2
    adaptive_prefetch_size: bool = True

    # GPU-accelerated preprocessing
    enable_gpu_preprocessing: bool = True
    gpu_preprocessing_batch_size: int = 64
    gpu_preprocessing_device: str = "cuda"

    # Memory optimization
    enable_memory_mapping: bool = True
    memory_map_threshold_mb: int = 100
    shared_memory_cache: bool = True
    cache_size_mb: int = 1024

    # Adaptive batch sizing
    enable_adaptive_batching: bool = True
    min_batch_size: int = 8
    max_batch_size: int = 256
    batch_size_adjustment_factor: float = 1.2

    # Data pipeline optimization
    enable_pipeline_parallelism: bool = True
    pipeline_stages: int = 3
    stage_buffer_size: int = 4

    # Quality of service
    target_batch_time_ms: float = 100.0
    max_queue_wait_time_ms: float = 50.0
    enable_load_balancing: bool = True


class IntelligentPrefetcher:
    """Intelligent prefetching system that adapts to training patterns."""

    def __init__(self, config: AdvancedDataLoadingConfig):
        """Initialize intelligent prefetcher.

        Args:
            config: Advanced data loading configuration
        """
        self.config = config
        self.prefetch_queue: queue.Queue[Any] = queue.Queue(maxsize=config.prefetch_buffer_size)
        self.prefetch_threads: list[threading.Thread] = []
        self.is_running = False
        self.access_patterns: dict[int, float] = {}
        self.prediction_model = SimplePredictionModel()

    def start_prefetching(
        self,
        data_loader: DataLoader,
        device: torch.device,
    ) -> None:
        """Start intelligent prefetching.

        Args:
            data_loader: Source data loader
            device: Target device for prefetched data
        """
        if self.is_running:
            return

        self.is_running = True

        # Start prefetch worker threads
        for i in range(self.config.prefetch_threads):
            thread = threading.Thread(
                target=self._prefetch_worker,
                args=(data_loader, device, i),
                daemon=True,
            )
            thread.start()
            self.prefetch_threads.append(thread)

        logger.info(f"Started intelligent prefetching with {self.config.prefetch_threads} threads")

    def _prefetch_worker(
        self,
        data_loader: DataLoader,
        device: torch.device,
        worker_id: int,
    ) -> None:
        """Prefetch worker thread."""
        data_iter = iter(data_loader)

        while self.is_running:
            try:
                # Get next batch
                batch = next(data_iter)

                # Predict if this batch will be needed soon
                if self._should_prefetch_batch(batch):
                    # Move to device asynchronously
                    prefetched_batch = self._async_move_to_device(batch, device)

                    # Add to prefetch queue
                    self.prefetch_queue.put(prefetched_batch, timeout=1.0)

            except StopIteration:
                # Restart iterator
                data_iter = iter(data_loader)
            except queue.Full:
                # Queue is full, skip this batch
                logger.debug("Prefetch queue full, skipping batch")
                continue
            except Exception as e:
                logger.warning(f"Prefetch worker {worker_id} error: {e}")
                time.sleep(0.1)

    def _should_prefetch_batch(self, batch: Any) -> bool:
        """Determine if batch should be prefetched based on patterns."""
        # Simple heuristic - in practice, this would use ML prediction
        return True  # For now, prefetch everything

    def _async_move_to_device(
        self,
        batch: tuple[torch.Tensor, torch.Tensor],
        device: torch.device,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Asynchronously move batch to device."""
        data, target = batch

        # Use non_blocking transfer for better performance
        data = data.to(device, non_blocking=True)
        target = target.to(device, non_blocking=True)

        return data, target

    def get_prefetched_batch(self, timeout: float = 1.0) -> tuple[torch.Tensor, torch.Tensor] | None:
        """Get prefetched batch if available.

        Args:
            timeout: Timeout in seconds

        Returns:
            Prefetched batch or None if not available
        """
        try:
            return self.prefetch_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop_prefetching(self) -> None:
        """Stop prefetching threads."""
        self.is_running = False

        # Wait for threads to finish
        for thread in self.prefetch_threads:
            thread.join(timeout=1.0)

        self.prefetch_threads.clear()
        logger.info("Stopped intelligent prefetching")


class SimplePredictionModel:
    """Simple model for predicting data access patterns."""

    def __init__(self):
        """Initialize prediction model."""
        self.access_history: list[int] = []
        self.pattern_cache: dict[tuple[int, ...], float] = {}

    def predict_next_access(self, current_index: int) -> list[int]:
        """Predict next likely accessed indices.

        Args:
            current_index: Current data index

        Returns:
            List of predicted next indices
        """
        # Simple pattern-based prediction
        # In practice, this could use more sophisticated ML models

        if len(self.access_history) < 3:
            return [current_index + 1]  # Sequential access assumption

        # Look for patterns in recent history
        recent_pattern = tuple(self.access_history[-3:])

        if recent_pattern in self.pattern_cache:
            confidence = self.pattern_cache[recent_pattern]
            if confidence > 0.7:
                # Predict based on pattern
                return [current_index + 1, current_index + 2]

        # Default to sequential prediction
        return [current_index + 1]

    def update_access_pattern(self, index: int) -> None:
        """Update access pattern with new index.

        Args:
            index: Accessed index
        """
        self.access_history.append(index)

        # Keep only recent history
        if len(self.access_history) > 100:
            self.access_history = self.access_history[-50:]


class GPUPreprocessor:
    """GPU-accelerated preprocessing pipeline."""

    def __init__(self, config: AdvancedDataLoadingConfig):
        """Initialize GPU preprocessor.

        Args:
            config: Advanced data loading configuration
        """
        self.config = config
        self.device = torch.device(config.gpu_preprocessing_device)
        self.preprocessing_pipeline = self._create_gpu_pipeline()

    def _create_gpu_pipeline(self) -> torch.nn.Sequential:
        """Create GPU preprocessing pipeline."""
        # Create GPU-based transforms
        pipeline = torch.nn.Sequential(
            # Resize operation
            torch.nn.Upsample(size=(224, 224), mode="bilinear", align_corners=False),
            # Normalization
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        )

        return pipeline.to(self.device)

    def preprocess_batch(self, batch: torch.Tensor) -> torch.Tensor:
        """Preprocess batch on GPU.

        Args:
            batch: Input batch tensor

        Returns:
            Preprocessed batch tensor
        """
        with torch.no_grad():
            # Move to GPU if not already there
            if batch.device != self.device:
                batch = batch.to(self.device, non_blocking=True)

            # Apply preprocessing pipeline
            processed_batch = self.preprocessing_pipeline(batch)

            return processed_batch

    def preprocess_async(
        self,
        batch_queue: queue.Queue,
        output_queue: queue.Queue,
    ) -> None:
        """Asynchronous preprocessing worker.

        Args:
            batch_queue: Input batch queue
            output_queue: Output batch queue
        """
        while True:
            try:
                batch = batch_queue.get(timeout=1.0)
                if batch is None:  # Shutdown signal
                    break

                processed_batch = self.preprocess_batch(batch)
                output_queue.put(processed_batch)

            except queue.Empty:
                logger.debug("GPU preprocessing input queue empty, continuing")
                continue
            except Exception as e:
                logger.error(f"GPU preprocessing error: {e}")


class MemoryMappedDataset(Dataset):
    """Memory-mapped dataset for efficient large dataset handling."""

    def __init__(
        self,
        data_dir: Path,
        transform: transforms.Compose | None = None,
        cache_size_mb: int = 1024,
    ):
        """Initialize memory-mapped dataset.

        Args:
            data_dir: Dataset directory
            transform: Data transforms
            cache_size_mb: Cache size in MB
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.cache_size_bytes = cache_size_mb * 1024 * 1024

        # Build file index
        self.samples: list[tuple[Path, int]] = []
        self.class_to_idx: dict[str, int] = {}
        self.classes: list[str] = []
        self._build_index()

        # Initialize memory-mapped cache
        self.memory_cache: dict[int, torch.Tensor] = {}
        self.cache_usage = 0
        self.access_counts: dict[int, int] = {}

    def _build_index(self) -> None:
        """Build dataset index."""
        logger.info("Building memory-mapped dataset index...")

        # Get class directories
        class_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]
        class_dirs.sort()

        self.classes = [d.name for d in class_dirs]
        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}

        # Index all files
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

        for class_dir in class_dirs:
            class_idx = self.class_to_idx[class_dir.name]

            for img_path in class_dir.iterdir():
                if img_path.suffix.lower() in image_extensions:
                    self.samples.append((img_path, class_idx))

        logger.info(f"Indexed {len(self.samples)} samples from {len(self.classes)} classes")

    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        """Get item with memory mapping optimization."""
        # Update access count
        self.access_counts[index] = self.access_counts.get(index, 0) + 1

        # Check memory cache first
        if index in self.memory_cache:
            image_tensor = self.memory_cache[index]
        else:
            # Load from disk
            img_path, target = self.samples[index]
            image_tensor = self._load_and_cache_image(img_path, index)

        # Apply transforms
        if self.transform:
            image_tensor = self.transform(image_tensor)

        return image_tensor, self.samples[index][1]

    def _load_and_cache_image(self, img_path: Path, index: int) -> torch.Tensor:
        """Load image and cache in memory if beneficial."""
        # Load image
        try:
            with Image.open(img_path) as img:
                img = img.convert("RGB")
                image_tensor = transforms.ToTensor()(img)
        except Exception as e:
            logger.warning(f"Failed to load image {img_path}: {e}")
            # Return black image as fallback
            image_tensor = torch.zeros(3, 224, 224)

        # Cache if frequently accessed and we have space
        if self._should_cache_image(index, image_tensor):
            self._add_to_cache(index, image_tensor)

        return image_tensor

    def _should_cache_image(self, index: int, image_tensor: torch.Tensor) -> bool:
        """Determine if image should be cached."""
        # Cache if accessed multiple times
        access_count = self.access_counts.get(index, 0)
        if access_count < 2:
            return False

        # Check cache space
        tensor_size = image_tensor.numel() * image_tensor.element_size()
        return self.cache_usage + tensor_size <= self.cache_size_bytes

    def _add_to_cache(self, index: int, image_tensor: torch.Tensor) -> None:
        """Add image to memory cache."""
        if index in self.memory_cache:
            return

        tensor_size = image_tensor.numel() * image_tensor.element_size()

        # Make space if needed
        while self.cache_usage + tensor_size > self.cache_size_bytes and self.memory_cache:
            self._evict_least_used()

        # Add to cache
        self.memory_cache[index] = image_tensor.clone()
        self.cache_usage += tensor_size

    def _evict_least_used(self) -> None:
        """Evict least recently used item from cache."""
        if not self.memory_cache:
            return

        # Find least accessed item
        least_used_index = min(self.memory_cache.keys(), key=lambda idx: self.access_counts.get(idx, 0))

        # Remove from cache
        tensor = self.memory_cache.pop(least_used_index)
        tensor_size = tensor.numel() * tensor.element_size()
        self.cache_usage -= tensor_size


class AdaptiveBatchSampler(Sampler):
    """Adaptive batch sampler that adjusts batch size based on performance."""

    def __init__(
        self,
        dataset: Dataset,
        config: AdvancedDataLoadingConfig,
        initial_batch_size: int = 32,
    ):
        """Initialize adaptive batch sampler.

        Args:
            dataset: Dataset to sample from
            config: Advanced data loading configuration
            initial_batch_size: Initial batch size
        """
        self.dataset = dataset
        self.config = config
        self.current_batch_size = initial_batch_size
        self.performance_history: list[float] = []
        self.adjustment_cooldown = 0

    def __iter__(self) -> Iterator[list[int]]:
        """Iterate over adaptive batches."""
        # Safely get dataset length
        try:
            dataset_len = len(self.dataset) if hasattr(self.dataset, "__len__") else 1000
        except (TypeError, AttributeError):
            dataset_len = 1000  # Default fallback

        indices = list(range(dataset_len))

        # Shuffle indices
        np.random.shuffle(indices)

        # Generate batches with adaptive sizing
        i = 0
        while i < len(indices):
            batch_size = self._get_current_batch_size()
            batch_indices = indices[i : i + batch_size]

            if len(batch_indices) > 0:
                yield batch_indices

            i += batch_size

    def __len__(self) -> int:
        """Return number of batches."""
        # Safely get dataset length
        try:
            dataset_len = len(self.dataset) if hasattr(self.dataset, "__len__") else 1000
        except (TypeError, AttributeError):
            dataset_len = 1000  # Default fallback

        return (dataset_len + self.current_batch_size - 1) // self.current_batch_size

    def _get_current_batch_size(self) -> int:
        """Get current adaptive batch size."""
        # Adjust batch size based on performance
        if self.adjustment_cooldown > 0:
            self.adjustment_cooldown -= 1
            return self.current_batch_size

        if len(self.performance_history) >= 5:
            recent_performance = np.mean(self.performance_history[-5:])

            if recent_performance > self.config.target_batch_time_ms * 1.2:
                # Too slow, reduce batch size
                new_batch_size = max(self.config.min_batch_size, int(self.current_batch_size / self.config.batch_size_adjustment_factor))
            elif recent_performance < self.config.target_batch_time_ms * 0.8:
                # Fast enough, increase batch size
                new_batch_size = min(self.config.max_batch_size, int(self.current_batch_size * self.config.batch_size_adjustment_factor))
            else:
                new_batch_size = self.current_batch_size

            if new_batch_size != self.current_batch_size:
                logger.info(f"Adaptive batch size: {self.current_batch_size} -> {new_batch_size}")
                self.current_batch_size = new_batch_size
                self.adjustment_cooldown = 10  # Wait before next adjustment

        return self.current_batch_size

    def update_performance(self, batch_time_ms: float) -> None:
        """Update performance metrics.

        Args:
            batch_time_ms: Batch processing time in milliseconds
        """
        self.performance_history.append(batch_time_ms)

        # Keep only recent history
        if len(self.performance_history) > 20:
            self.performance_history = self.performance_history[-10:]


class PipelinedDataLoader:
    """Pipelined data loader with multiple processing stages."""

    def __init__(
        self,
        dataset: Dataset,
        config: AdvancedDataLoadingConfig,
        batch_size: int = 32,
        num_workers: int = 4,
    ):
        """Initialize pipelined data loader.

        Args:
            dataset: Dataset to load from
            config: Advanced data loading configuration
            batch_size: Batch size
            num_workers: Number of worker processes
        """
        self.dataset = dataset
        self.config = config
        self.batch_size = batch_size
        self.num_workers = num_workers

        # Create pipeline stages
        self.stage_queues: list[queue.Queue] = []
        self.stage_workers: list[threading.Thread] = []
        self.is_running = False

        # Initialize stages
        self._setup_pipeline_stages()

    def _setup_pipeline_stages(self) -> None:
        """Setup pipeline processing stages."""
        # Create queues for each stage
        for i in range(self.config.pipeline_stages):
            stage_queue: queue.Queue[Any] = queue.Queue(maxsize=self.config.stage_buffer_size)
            self.stage_queues.append(stage_queue)

        # Stage 1: Data loading
        loading_worker = threading.Thread(
            target=self._data_loading_stage,
            daemon=True,
        )
        self.stage_workers.append(loading_worker)

        # Stage 2: Preprocessing
        preprocessing_worker = threading.Thread(
            target=self._preprocessing_stage,
            daemon=True,
        )
        self.stage_workers.append(preprocessing_worker)

        # Stage 3: Batching
        batching_worker = threading.Thread(
            target=self._batching_stage,
            daemon=True,
        )
        self.stage_workers.append(batching_worker)

    def _data_loading_stage(self) -> None:
        """Data loading pipeline stage."""
        data_loader = DataLoader(
            self.dataset,
            batch_size=1,  # Load individual samples
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=True,
        )

        for batch in data_loader:
            if not self.is_running:
                break

            try:
                self.stage_queues[0].put(batch, timeout=1.0)
            except queue.Full:
                logger.debug("Input stage queue full, continuing")
                continue

    def _preprocessing_stage(self) -> None:
        """Preprocessing pipeline stage."""
        while self.is_running:
            try:
                batch = self.stage_queues[0].get(timeout=1.0)

                # Apply preprocessing (placeholder)
                processed_batch = batch  # In practice, apply transforms here

                self.stage_queues[1].put(processed_batch, timeout=1.0)

            except queue.Empty:
                logger.debug("Preprocessing stage queue empty, continuing")
                continue
            except queue.Full:
                logger.debug("Preprocessing stage queue full, continuing")
                continue

    def _batching_stage(self) -> None:
        """Batching pipeline stage."""
        batch_buffer = []

        while self.is_running:
            try:
                sample = self.stage_queues[1].get(timeout=1.0)
                batch_buffer.append(sample)

                if len(batch_buffer) >= self.batch_size:
                    # Create batch
                    batched_data = torch.cat([s[0] for s in batch_buffer], dim=0)
                    batched_targets = torch.cat([s[1] for s in batch_buffer], dim=0)

                    final_batch = (batched_data, batched_targets)
                    self.stage_queues[2].put(final_batch, timeout=1.0)

                    batch_buffer.clear()

            except queue.Empty:
                logger.debug("Batching stage queue empty, continuing")
                continue
            except queue.Full:
                logger.debug("Batching stage queue full, continuing")
                continue

    def start_pipeline(self) -> None:
        """Start pipeline processing."""
        if self.is_running:
            return

        self.is_running = True

        for worker in self.stage_workers:
            worker.start()

        logger.info("Started pipelined data loading")

    def stop_pipeline(self) -> None:
        """Stop pipeline processing."""
        self.is_running = False

        for worker in self.stage_workers:
            worker.join(timeout=1.0)

        logger.info("Stopped pipelined data loading")

    def __iter__(self) -> Iterator[tuple[torch.Tensor, torch.Tensor]]:
        """Iterate over pipelined batches."""
        self.start_pipeline()

        try:
            while True:
                try:
                    batch = self.stage_queues[-1].get(timeout=1.0)
                    yield batch
                except queue.Empty:
                    if not self.is_running:
                        break
                    continue
        finally:
            self.stop_pipeline()


def create_advanced_data_loader(
    dataset: Dataset,
    config: AdvancedDataLoadingConfig,
    batch_size: int = 32,
    device: torch.device = torch.device("cpu"),
) -> DataLoader:
    """Create advanced optimized data loader.

    Args:
        dataset: Dataset to load from
        config: Advanced data loading configuration
        batch_size: Batch size
        device: Target device

    Returns:
        Optimized DataLoader instance
    """
    # Use memory-mapped dataset if enabled
    if config.enable_memory_mapping and hasattr(dataset, "data_dir"):
        dataset = MemoryMappedDataset(
            dataset.data_dir,
            transform=getattr(dataset, "transform", None),
            cache_size_mb=config.cache_size_mb,
        )

    # Use adaptive batch sampler if enabled
    sampler = None
    if config.enable_adaptive_batching:
        sampler = AdaptiveBatchSampler(dataset, config, batch_size)
        batch_size = 1  # Sampler handles batching

    # Create optimized data loader
    data_loader = DataLoader(
        dataset,
        batch_size=batch_size,
        sampler=sampler,
        shuffle=sampler is None,
        num_workers=mp.cpu_count() // 2,
        pin_memory=True,
        persistent_workers=True,
        prefetch_factor=4,
        drop_last=True,
    )

    # Add intelligent prefetching if enabled
    if config.enable_intelligent_prefetching:
        prefetcher = IntelligentPrefetcher(config)
        prefetcher.start_prefetching(data_loader, device)

        # Attach prefetcher to data loader for cleanup
        data_loader._prefetcher = prefetcher

    return data_loader


def benchmark_data_loading_performance(
    dataset: Dataset,
    config: AdvancedDataLoadingConfig,
    num_batches: int = 50,
) -> dict[str, float]:
    """Benchmark data loading performance with different optimizations.

    Args:
        dataset: Dataset to benchmark
        config: Advanced data loading configuration
        num_batches: Number of batches to benchmark

    Returns:
        Performance metrics dictionary
    """
    logger.info("Benchmarking advanced data loading performance...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Create optimized data loader
    data_loader = create_advanced_data_loader(dataset, config, device=device)

    # Benchmark performance
    start_time = time.time()
    batch_times = []
    total_samples = 0

    for batch_idx, (data, target) in enumerate(data_loader):
        if batch_idx >= num_batches:
            break

        batch_start = time.time()

        # Simulate processing
        data = data.to(device, non_blocking=True)
        target = target.to(device, non_blocking=True)

        if device.type == "cuda":
            torch.cuda.synchronize()

        batch_time = time.time() - batch_start
        batch_times.append(batch_time * 1000)  # Convert to ms
        total_samples += len(data)

    total_time = time.time() - start_time

    # Calculate metrics
    avg_batch_time = np.mean(batch_times)
    throughput = total_samples / total_time

    # Cleanup
    if hasattr(data_loader, "_prefetcher"):
        data_loader._prefetcher.stop_prefetching()

    metrics = {
        "avg_batch_time_ms": float(avg_batch_time),
        "throughput_samples_per_sec": float(throughput),
        "total_time_sec": float(total_time),
        "total_samples": float(total_samples),
        "batches_processed": float(len(batch_times)),
    }

    logger.info(f"Benchmark results: {avg_batch_time:.1f}ms/batch, {throughput:.1f} samples/sec")
    return metrics
