"""Performance benchmark tests for the production training pipeline.

These tests measure and validate performance characteristics of the training system.
"""
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import psutil
import pytest
import torch
from PIL import Image

from src.core.vision import VisionAdapter
from src.training.config import TrainingConfig
from src.training.dataset_manager import DatasetManager
from src.training.production_trainer import ProductionTrainer


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def benchmark_dataset(self, temp_dir):
        """Create benchmark dataset with realistic size."""
        dataset_dir = temp_dir / "benchmark_dataset"

        # Create larger dataset for benchmarking
        classes = ["class_0", "class_1", "class_2", "class_3"]
        samples_per_class = 50  # Reasonable size for benchmarking

        for split in ["train", "val"]:
            split_dir = dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                num_samples = samples_per_class if split == "train" else samples_per_class // 5

                for i in range(num_samples):
                    # Create realistic-sized images
                    img = Image.new("RGB", (224, 224), color=(i * 5, 100, 150))
                    img.save(class_dir / f"image_{i:04d}.jpg")

        return dataset_dir

    @pytest.fixture
    def benchmark_config(self, benchmark_dataset, temp_dir):
        """Create configuration for benchmarking."""
        config = TrainingConfig()
        config.experiment_name = "benchmark_test"
        config.model_architecture = "resnet50"
        config.num_classes = 4
        config.epochs = 5  # Reasonable for benchmarking
        config.batch_size = 16
        config.learning_rate = 0.001
        config.device = "cpu"  # Use CPU for consistent benchmarking
        config.num_workers = 2
        
        # Set dataset path in the dataset manager
        self.dataset_manager = DatasetManager()
        self.dataset_manager.base_data_dir = benchmark_dataset
        
        return config

    def test_training_speed_benchmark(self, benchmark_config, benchmark_dataset):
        """Benchmark training speed and set performance expectations."""
        # Update config to use the benchmark dataset
        benchmark_config.data_dir = str(benchmark_dataset)
        
        # Ensure num_classes matches the benchmark dataset (4 classes)
        benchmark_config.num_classes = 4
        
        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(benchmark_config, dataset_manager)

        # Measure setup time
        setup_start = time.time()
        setup_success = trainer.setup_training()
        setup_time = time.time() - setup_start

        # Setup should be fast and successful
        assert setup_success, f"Setup failed: {getattr(trainer.error_handler, 'last_error', 'Unknown error')}"
        assert setup_time < 30, f"Setup took too long: {setup_time:.2f}s"

        # Measure training time
        train_start = time.time()
        result = trainer.train()
        train_time = time.time() - train_start

        if not result.success:
            logger.error(f"Training failed: {result.error_message}")
            
        assert result.success, f"Training failed: {result.error_message}"

        # Performance expectations (adjust based on hardware)
        # These are reasonable expectations for CPU training
        max_time_per_epoch = 60  # seconds
        expected_max_time = benchmark_config.epochs * max_time_per_epoch

        assert train_time < expected_max_time, f"Training too slow: {train_time:.2f}s > {expected_max_time}s"

        # Log performance metrics
        print("\n📊 Training Performance Metrics:")
        print(f"   Setup Time: {setup_time:.2f}s")
        print(f"   Training Time: {train_time:.2f}s")
        print(f"   Time per Epoch: {train_time / benchmark_config.epochs:.2f}s")
        print(f"   Final Validation Accuracy: {result.best_val_accuracy:.3f}")

        # Check if we achieved reasonable accuracy (adjust based on dataset complexity)
        min_expected_accuracy = 0.25  # Random chance for 4 classes is 0.25
        assert result.best_val_accuracy >= min_expected_accuracy, \
            f"Model accuracy too low: {result.best_val_accuracy:.3f} < {min_expected_accuracy}"

    def test_memory_usage_benchmark(self, benchmark_config, temp_dir):
        """Benchmark memory usage during training."""
        import gc

        # Clear memory before test
        gc.collect()

        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(benchmark_config, dataset_manager)

        # Measure memory during setup
        assert trainer.setup_training()
        setup_memory = process.memory_info().rss / 1024 / 1024

        # Measure memory during training
        result = trainer.train()
        peak_memory = process.memory_info().rss / 1024 / 1024

        assert result.success

        # Memory usage expectations
        setup_increase = setup_memory - baseline_memory
        peak_increase = peak_memory - baseline_memory

        # Should not use excessive memory for this dataset size
        assert setup_increase < 500, f"Setup memory usage too high: {setup_increase:.1f}MB"
        assert peak_increase < 1000, f"Peak memory usage too high: {peak_increase:.1f}MB"

        print("\n🧠 Memory Usage Metrics:")
        print(f"   Baseline: {baseline_memory:.1f}MB")
        print(f"   After Setup: {setup_memory:.1f}MB (+{setup_increase:.1f}MB)")
        print(f"   Peak Training: {peak_memory:.1f}MB (+{peak_increase:.1f}MB)")

    def test_data_loading_performance(self, benchmark_config, temp_dir):
        """Benchmark data loading performance."""
        from src.training.data_loader import create_data_loaders

        # Test data loader creation time
        start_time = time.time()
        train_loader, val_loader = create_data_loaders(
            dataset_path=benchmark_config.dataset_path, batch_size=benchmark_config.batch_size, num_workers=benchmark_config.num_workers, img_size=(224, 224)
        )
        loader_creation_time = time.time() - start_time

        assert loader_creation_time < 10, f"Data loader creation too slow: {loader_creation_time:.2f}s"

        # Test data loading speed
        start_time = time.time()
        batch_count = 0

        for batch_idx, (images, labels) in enumerate(train_loader):
            batch_count += 1
            if batch_idx >= 10:  # Test first 10 batches
                break

        loading_time = time.time() - start_time
        time_per_batch = loading_time / batch_count

        # Should load batches reasonably fast
        assert time_per_batch < 2.0, f"Data loading too slow: {time_per_batch:.3f}s per batch"

        print("\n📦 Data Loading Metrics:")
        print(f"   Loader Creation: {loader_creation_time:.2f}s")
        print(f"   Time per Batch: {time_per_batch:.3f}s")
        print(f"   Batches per Second: {1 / time_per_batch:.1f}")

    def test_model_inference_speed(self, benchmark_config, temp_dir):
        """Benchmark model inference speed."""
        # Train a model first
        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(benchmark_config, dataset_manager)

        assert trainer.setup_training()
        result = trainer.train()
        assert result.success

        # Load model for inference
        adapter = VisionAdapter()
        adapter.load_checkpoint(str(result.best_model_path))

        # Create test images
        test_images = []
        for i in range(100):  # 100 test images
            img = Image.new("RGB", (224, 224), color=(i * 2, 100, 150))
            test_images.append(img)

        # Benchmark single image inference
        start_time = time.time()
        for img in test_images[:10]:  # Test 10 images
            prediction, confidence = adapter.predict(img)

        single_inference_time = (time.time() - start_time) / 10

        # Benchmark batch inference
        start_time = time.time()
        batch_results = adapter.predict_batch(test_images[:20])  # Batch of 20
        batch_inference_time = (time.time() - start_time) / 20

        # Performance expectations
        assert single_inference_time < 1.0, f"Single inference too slow: {single_inference_time:.3f}s"
        assert batch_inference_time < 0.5, f"Batch inference too slow: {batch_inference_time:.3f}s"

        print("\n🔮 Inference Performance:")
        print(f"   Single Image: {single_inference_time:.3f}s")
        print(f"   Batch (per image): {batch_inference_time:.3f}s")
        print(f"   Speedup: {single_inference_time / batch_inference_time:.1f}x")

    def test_disk_io_performance(self, benchmark_config, temp_dir):
        """Benchmark disk I/O performance during training."""
        import os

        # Monitor disk usage
        disk_usage_start = shutil.disk_usage(temp_dir)

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(benchmark_config, dataset_manager)

        assert trainer.setup_training()

        # Measure checkpoint saving performance
        start_time = time.time()
        result = trainer.train()
        total_time = time.time() - start_time

        assert result.success

        # Check disk usage
        disk_usage_end = shutil.disk_usage(temp_dir)
        disk_used = (disk_usage_start.free - disk_usage_end.free) / 1024 / 1024  # MB

        # Check model files were created
        model_files = list(benchmark_config.output_dir.rglob("*.pt"))
        assert len(model_files) > 0, "Should create model files"

        # Calculate total model size
        total_model_size = sum(f.stat().st_size for f in model_files) / 1024 / 1024  # MB

        print("\n💾 Disk I/O Metrics:")
        print(f"   Total Disk Used: {disk_used:.1f}MB")
        print(f"   Model Files Size: {total_model_size:.1f}MB")
        print(f"   Number of Checkpoints: {len(model_files)}")

    def test_scalability_with_dataset_size(self, temp_dir):
        """Test how performance scales with dataset size."""
        dataset_sizes = [10, 50, 100]  # samples per class
        performance_metrics = []

        for size in dataset_sizes:
            # Create dataset of specific size
            dataset_dir = temp_dir / f"dataset_{size}"
            self._create_sized_dataset(dataset_dir, size)

            config = TrainingConfig()
            config.experiment_name = f"scale_test_{size}"
            config.model_architecture = "resnet50"
            config.num_classes = 2
            config.epochs = 2  # Short for scaling test
            config.batch_size = 8
            config.device = "cpu"
            
            # Set dataset path in the dataset manager
            self.dataset_manager = DatasetManager()
            self.dataset_manager.base_data_dir = dataset_dir

            # Measure training time
            dataset_manager = DatasetManager()
            trainer = ProductionTrainer(config, dataset_manager)

            assert trainer.setup_training()

            start_time = time.time()
            result = trainer.train()
            train_time = time.time() - start_time

            assert result.success

            performance_metrics.append(
                {
                    "dataset_size": size,
                    "train_time": train_time,
                    "accuracy": result.best_val_accuracy,
                    "time_per_sample": train_time / (size * 2 * 2),  # 2 classes, 2 epochs
                }
            )

        # Analyze scaling
        print("\n📈 Scalability Analysis:")
        for metrics in performance_metrics:
            print(f"   Size {metrics['dataset_size']}: {metrics['train_time']:.1f}s, {metrics['time_per_sample']:.4f}s/sample, acc={metrics['accuracy']:.3f}")

        # Check that scaling is reasonable (not exponential)
        small_time = performance_metrics[0]["time_per_sample"]
        large_time = performance_metrics[-1]["time_per_sample"]

        # Time per sample shouldn't increase dramatically
        assert large_time < small_time * 3, "Scaling performance degraded too much"

    def test_concurrent_training_performance(self, benchmark_config, temp_dir):
        """Test performance with multiple concurrent training processes."""
        import queue
        import threading

        # This test simulates multiple training jobs
        # In practice, you'd run separate processes

        results_queue = queue.Queue()

        def train_worker(worker_id):
            """Worker function for concurrent training."""
            try:
                # Create separate config for each worker
                worker_config = TrainingConfig(
                    experiment_name=f"concurrent_test_{worker_id}",
                    dataset_path=benchmark_config.dataset_path,
                    model_architecture="resnet50",
                    num_classes=benchmark_config.num_classes,
                    epochs=2,  # Short for concurrent test
                    batch_size=8,  # Smaller batch for memory
                    device="cpu",
                    output_dir=temp_dir / f"models_{worker_id}",
                )

                dataset_manager = DatasetManager()
                trainer = ProductionTrainer(worker_config, dataset_manager)

                start_time = time.time()
                trainer.setup_training()
                result = trainer.train()
                end_time = time.time()

                results_queue.put(
                    {
                        "worker_id": worker_id,
                        "success": result.success,
                        "time": end_time - start_time,
                        "accuracy": result.best_accuracy if result.success else 0,
                    }
                )

            except Exception as e:
                results_queue.put(
                    {
                        "worker_id": worker_id,
                        "success": False,
                        "error": str(e),
                        "time": 0,
                        "accuracy": 0,
                    }
                )

        # Start concurrent workers
        num_workers = 2  # Keep low for test stability
        threads = []

        start_time = time.time()

        for i in range(num_workers):
            thread = threading.Thread(target=train_worker, args=(i,))
            thread.start()
            threads.append(thread)

        # Wait for completion
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == num_workers, "All workers should complete"

        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) > 0, "At least one worker should succeed"

        print("\n🔄 Concurrent Training Metrics:")
        print(f"   Workers: {num_workers}")
        print(f"   Total Time: {total_time:.1f}s")
        print(f"   Successful: {len(successful_results)}/{num_workers}")

        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"   Worker {result['worker_id']}: {status} {result['time']:.1f}s, acc={result['accuracy']:.3f}")

    def _create_sized_dataset(self, dataset_dir: Path, samples_per_class: int):
        """Create dataset with specific number of samples per class."""
        classes = ["class_0", "class_1"]

        for split in ["train", "val"]:
            split_dir = dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                num_samples = samples_per_class if split == "train" else max(1, samples_per_class // 10)

                for i in range(num_samples):
                    img = Image.new("RGB", (224, 224), color=(i * 3, 100, 150))
                    img.save(class_dir / f"image_{i:04d}.jpg")


@pytest.mark.performance
class TestRegressionBenchmarks:
    """Regression tests to ensure performance doesn't degrade."""

    def test_training_time_regression(self, tmp_path):
        """Test that training time doesn't regress significantly."""
        # This would compare against baseline performance metrics
        # For now, we'll establish reasonable expectations

        baseline_time_per_epoch = 30  # seconds for small dataset
        tolerance = 1.5  # 50% tolerance

        # Create small test dataset
        dataset_dir = tmp_path / "regression_dataset"
        self._create_minimal_dataset(dataset_dir)

        config = TrainingConfig()
        config.experiment_name = "regression_test"
        config.epochs = 1
        config.batch_size = 4
        config.device = "cpu"
        
        # Set dataset path in the dataset manager
        self.dataset_manager = DatasetManager()
        self.dataset_manager.base_data_dir = dataset_dir

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        assert trainer.setup_training()

        start_time = time.time()
        result = trainer.train()
        actual_time = time.time() - start_time

        assert result.success

        # Check against baseline
        max_allowed_time = baseline_time_per_epoch * tolerance
        assert actual_time < max_allowed_time, f"Training time regression detected: {actual_time:.1f}s > {max_allowed_time:.1f}s"

    def test_memory_usage_regression(self, tmp_path):
        """Test that memory usage doesn't regress significantly."""
        baseline_memory_mb = 500  # MB for small dataset
        tolerance = 1.5  # 50% tolerance

        import gc

        gc.collect()

        process = psutil.Process()
        baseline = process.memory_info().rss / 1024 / 1024

        # Create and run training
        dataset_dir = tmp_path / "memory_regression_dataset"
        self._create_minimal_dataset(dataset_dir)

        config = TrainingConfig()
        config.experiment_name = "memory_regression_test"
        config.epochs = 1
        config.batch_size = 4
        config.device = "cpu"
        
        # Set dataset path in the dataset manager
        self.dataset_manager = DatasetManager()
        self.dataset_manager.base_data_dir = dataset_dir

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager)

        assert trainer.setup_training()
        result = trainer.train()

        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = peak_memory - baseline

        assert result.success

        max_allowed_memory = baseline_memory_mb * tolerance
        assert memory_increase < max_allowed_memory, f"Memory usage regression detected: {memory_increase:.1f}MB > {max_allowed_memory:.1f}MB"

    def _create_minimal_dataset(self, dataset_dir: Path):
        """Create minimal dataset for regression tests."""
        classes = ["class_0", "class_1"]

        for split in ["train", "val"]:
            split_dir = dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                # Very small dataset for regression tests
                num_samples = 5 if split == "train" else 2

                for i in range(num_samples):
                    img = Image.new("RGB", (224, 224), color=(i * 50, 100, 150))
                    img.save(class_dir / f"image_{i}.jpg")
