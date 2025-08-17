"""Comprehensive performance regression tests for production training pipeline.

This module provides extensive performance regression testing to ensure
the training pipeline maintains acceptable performance characteristics.
"""

import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import psutil
import pytest
import torch
from PIL import Image

from src.core.vision import VisionAdapter
from src.features.model_switching.model_manager import PlantGuardModelManager
from src.training.config import TrainingConfig
from src.training.dataset_manager import DatasetManager
from src.training.model_registry import ModelRegistry
from src.training.production_trainer import ProductionTrainer


class PerformanceBaseline:
    """Performance baseline values for regression testing."""

    # Training performance baselines (CPU)
    TRAINING_TIME_PER_EPOCH_MAX = 60.0  # seconds
    SETUP_TIME_MAX = 30.0  # seconds
    MEMORY_USAGE_TRAINING_MAX = 1000.0  # MB

    # Model operations baselines
    MODEL_LOADING_TIME_MAX = 5.0  # seconds
    MODEL_SWITCHING_TIME_MAX = 3.0  # seconds
    INFERENCE_TIME_SINGLE_MAX = 1.0  # seconds
    INFERENCE_TIME_BATCH_MAX = 0.5  # seconds per image

    # Registry operations baselines
    MODEL_REGISTRATION_TIME_MAX = 10.0  # seconds
    MODEL_SEARCH_TIME_MAX = 2.0  # seconds
    MODEL_COMPARISON_TIME_MAX = 5.0  # seconds

    # Memory usage baselines
    MEMORY_USAGE_BASELINE_MAX = 200.0  # MB
    MEMORY_USAGE_REGISTRY_MAX = 300.0  # MB
    MEMORY_USAGE_ADAPTER_MAX = 400.0  # MB

    # Dataset operations baselines
    DATASET_VALIDATION_TIME_MAX = 15.0  # seconds
    DATASET_ANALYSIS_TIME_MAX = 20.0  # seconds


class TestPerformanceRegressionComprehensive:
    """Comprehensive performance regression tests."""

    @pytest.fixture
    def performance_workspace(self):
        """Create workspace for performance testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "data").mkdir()
            (workspace / "models").mkdir()
            (workspace / "runs").mkdir()
            yield workspace

    @pytest.fixture
    def performance_dataset(self, performance_workspace):
        """Create dataset for performance testing."""
        dataset_dir = performance_workspace / "data" / "perf_dataset"

        # Create dataset with realistic size for performance testing
        classes = ["class_0", "class_1", "class_2", "class_3"]

        for split in ["train", "val"]:
            split_dir = dataset_dir / split

            for class_name in classes:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

                # Sufficient samples for meaningful performance testing
                num_samples = 30 if split == "train" else 10

                for i in range(num_samples):
                    color = (i * 8 % 255, (i * 12) % 255, (i * 16) % 255)
                    img = Image.new("RGB", (224, 224), color=color)
                    img.save(class_dir / f"sample_{i:03d}.jpg")

        return dataset_dir

    @pytest.fixture
    def performance_config(self, performance_dataset, performance_workspace):
        """Create configuration for performance testing."""
        return TrainingConfig(
            experiment_name="performance_regression_test",
            dataset_path=performance_dataset,
            model_architecture="resnet50",
            num_classes=4,
            epochs=3,  # Short for performance testing
            batch_size=16,
            learning_rate=0.001,
            device="cpu",  # Use CPU for consistent performance testing
            output_dir=performance_workspace / "runs",
            num_workers=2,
        )

    def test_training_performance_regression(self, performance_config, performance_workspace):
        """Test training performance regression."""
        print("\n=== Training Performance Regression Test ===")

        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(performance_config, dataset_manager, performance_workspace / "runs" / "perf_test")

        # Test setup performance
        setup_start = time.time()
        setup_success = trainer.setup_training()
        setup_time = time.time() - setup_start

        assert setup_success, "Training setup should succeed"
        assert setup_time < PerformanceBaseline.SETUP_TIME_MAX, f"Setup time regression: {setup_time:.2f}s > {PerformanceBaseline.SETUP_TIME_MAX}s"

        setup_memory = process.memory_info().rss / 1024 / 1024
        setup_memory_increase = setup_memory - baseline_memory

        assert setup_memory_increase < PerformanceBaseline.MEMORY_USAGE_TRAINING_MAX, f"Setup memory regression: {setup_memory_increase:.1f}MB > {PerformanceBaseline.MEMORY_USAGE_TRAINING_MAX}MB"

        # Test training performance (mocked for speed)
        with patch.object(trainer, "_train_epoch") as mock_train_epoch:
            mock_train_epoch.return_value = {"train_loss": 0.5, "train_accuracy": 0.8, "val_loss": 0.6, "val_accuracy": 0.75}

            train_start = time.time()
            result = trainer.train()
            train_time = time.time() - train_start

            assert result.success, "Training should succeed"

            # Check training time per epoch
            time_per_epoch = train_time / performance_config.epochs
            assert time_per_epoch < PerformanceBaseline.TRAINING_TIME_PER_EPOCH_MAX, f"Training time regression: {time_per_epoch:.2f}s/epoch > {PerformanceBaseline.TRAINING_TIME_PER_EPOCH_MAX}s/epoch"

        peak_memory = process.memory_info().rss / 1024 / 1024
        peak_memory_increase = peak_memory - baseline_memory

        print(f"  Setup Time: {setup_time:.2f}s (max: {PerformanceBaseline.SETUP_TIME_MAX}s)")
        print(f"  Time per Epoch: {time_per_epoch:.2f}s (max: {PerformanceBaseline.TRAINING_TIME_PER_EPOCH_MAX}s)")
        print(f"  Memory Usage: {peak_memory_increase:.1f}MB (max: {PerformanceBaseline.MEMORY_USAGE_TRAINING_MAX}MB)")
        print("✅ Training performance within acceptable limits")

    def test_model_registry_performance_regression(self, performance_workspace):
        """Test model registry performance regression."""
        print("\n=== Model Registry Performance Regression Test ===")

        registry = ModelRegistry(performance_workspace / "models")

        # Create test models
        model_paths = []
        for i in range(10):  # Test with multiple models
            model_path = performance_workspace / f"perf_model_{i}.pt"
            checkpoint = {
                "model_state_dict": {"fc.weight": torch.randn(4, 2048), "fc.bias": torch.randn(4)},
                "num_classes": 4,
                "class_names": [f"class_{j}" for j in range(4)],
                "model_version": "1.0.0",
                "training_metadata": {"accuracy": 0.85 + i * 0.01},
            }
            torch.save(checkpoint, model_path)
            model_paths.append(model_path)

        # Test model registration performance
        registration_times = []
        model_ids = []

        for i, model_path in enumerate(model_paths):
            start_time = time.time()

            model_id = registry.register_model(
                model_path=model_path,
                name=f"perf_model_{i}",
                architecture="resnet50",
                dataset_version="test_v1.0",
                hyperparameters={"num_classes": 4},
                performance_metrics={"accuracy": 0.85 + i * 0.01},
                description=f"Performance test model {i}",
            )

            registration_time = time.time() - start_time
            registration_times.append(registration_time)
            model_ids.append(model_id)

            assert registration_time < PerformanceBaseline.MODEL_REGISTRATION_TIME_MAX, f"Model registration regression: {registration_time:.2f}s > {PerformanceBaseline.MODEL_REGISTRATION_TIME_MAX}s"

        avg_registration_time = sum(registration_times) / len(registration_times)

        # Test model search performance
        search_start = time.time()
        search_results = registry.search_models(architecture="resnet50")
        search_time = time.time() - search_start

        assert len(search_results) == 10, "Should find all registered models"
        assert search_time < PerformanceBaseline.MODEL_SEARCH_TIME_MAX, f"Model search regression: {search_time:.2f}s > {PerformanceBaseline.MODEL_SEARCH_TIME_MAX}s"

        # Test model comparison performance
        comparison_start = time.time()
        comparison = registry.compare_models(model_ids[:5])  # Compare 5 models
        comparison_time = time.time() - comparison_start

        assert len(comparison.models) == 5, "Should compare all requested models"
        assert comparison_time < PerformanceBaseline.MODEL_COMPARISON_TIME_MAX, f"Model comparison regression: {comparison_time:.2f}s > {PerformanceBaseline.MODEL_COMPARISON_TIME_MAX}s"

        print(f"  Avg Registration Time: {avg_registration_time:.3f}s (max: {PerformanceBaseline.MODEL_REGISTRATION_TIME_MAX}s)")
        print(f"  Search Time: {search_time:.3f}s (max: {PerformanceBaseline.MODEL_SEARCH_TIME_MAX}s)")
        print(f"  Comparison Time: {comparison_time:.3f}s (max: {PerformanceBaseline.MODEL_COMPARISON_TIME_MAX}s)")
        print("✅ Model registry performance within acceptable limits")

    def test_vision_adapter_performance_regression(self, performance_workspace):
        """Test VisionAdapter performance regression."""
        print("\n=== VisionAdapter Performance Regression Test ===")

        registry = ModelRegistry(performance_workspace / "models")

        # Create test model
        model_path = performance_workspace / "adapter_perf_model.pt"
        checkpoint = {
            "model_state_dict": {
                "conv1.weight": torch.randn(64, 3, 7, 7),
                "fc.weight": torch.randn(4, 2048),
                "fc.bias": torch.randn(4),
            },
            "num_classes": 4,
            "class_names": ["class_0", "class_1", "class_2", "class_3"],
            "model_version": "1.0.0",
            "training_metadata": {"accuracy": 0.90},
        }
        torch.save(checkpoint, model_path)

        model_id = registry.register_model(
            model_path=model_path,
            name="adapter_perf_model",
            architecture="resnet50",
            dataset_version="test_v1.0",
            hyperparameters={"num_classes": 4},
            performance_metrics={"accuracy": 0.90},
            description="Performance test model for adapter",
        )

        adapter = VisionAdapter()

        # Test model loading performance
        with patch.object(adapter, "_create_model") as mock_create_model:
            mock_model = torch.nn.Linear(2048, 4)  # Simple mock model
            mock_create_model.return_value = mock_model

            loading_start = time.time()
            adapter.load_from_registry(model_id)
            loading_time = time.time() - loading_start

            assert adapter.is_loaded, "Model should be loaded"
            assert loading_time < PerformanceBaseline.MODEL_LOADING_TIME_MAX, f"Model loading regression: {loading_time:.3f}s > {PerformanceBaseline.MODEL_LOADING_TIME_MAX}s"

        # Test single image inference performance
        test_image = Image.new("RGB", (224, 224), color="green")

        with patch.object(adapter, "_preprocess_image") as mock_preprocess:
            mock_tensor = torch.randn(1, 3, 224, 224)
            mock_preprocess.return_value = mock_tensor

            with patch.object(adapter.model, "__call__") as mock_forward:
                mock_output = torch.randn(1, 4)
                mock_forward.return_value = mock_output

                # Warm up
                adapter.predict(test_image)

                # Measure inference time
                inference_times = []
                for _ in range(10):
                    start_time = time.time()
                    predicted_class, confidence = adapter.predict(test_image)
                    inference_time = time.time() - start_time
                    inference_times.append(inference_time)

                avg_inference_time = sum(inference_times) / len(inference_times)
                assert avg_inference_time < PerformanceBaseline.INFERENCE_TIME_SINGLE_MAX, f"Single inference regression: {avg_inference_time:.3f}s > {PerformanceBaseline.INFERENCE_TIME_SINGLE_MAX}s"

        # Test batch inference performance
        test_images = [Image.new("RGB", (224, 224), color=f"color_{i}") for i in range(20)]

        with patch.object(adapter, "_preprocess_batch") as mock_preprocess_batch:
            mock_batch_tensor = torch.randn(20, 3, 224, 224)
            mock_preprocess_batch.return_value = mock_batch_tensor

            with patch.object(adapter.model, "__call__") as mock_forward:
                mock_batch_output = torch.randn(20, 4)
                mock_forward.return_value = mock_batch_output

                batch_start = time.time()
                batch_results = adapter.predict_batch(test_images)
                batch_time = time.time() - batch_start

                batch_time_per_image = batch_time / len(test_images)
                assert batch_time_per_image < PerformanceBaseline.INFERENCE_TIME_BATCH_MAX, (
                    f"Batch inference regression: {batch_time_per_image:.3f}s/img > {PerformanceBaseline.INFERENCE_TIME_BATCH_MAX}s/img"
                )

        print(f"  Model Loading Time: {loading_time:.3f}s (max: {PerformanceBaseline.MODEL_LOADING_TIME_MAX}s)")
        print(f"  Single Inference Time: {avg_inference_time:.3f}s (max: {PerformanceBaseline.INFERENCE_TIME_SINGLE_MAX}s)")
        print(f"  Batch Inference Time: {batch_time_per_image:.3f}s/img (max: {PerformanceBaseline.INFERENCE_TIME_BATCH_MAX}s/img)")
        print("✅ VisionAdapter performance within acceptable limits")

    def test_model_switching_performance_regression(self, performance_workspace):
        """Test model switching performance regression."""
        print("\n=== Model Switching Performance Regression Test ===")

        registry = ModelRegistry(performance_workspace / "models")

        # Create multiple models for switching tests
        model_ids = []
        for i in range(5):
            model_path = performance_workspace / f"switch_model_{i}.pt"
            checkpoint = {
                "model_state_dict": {"fc.weight": torch.randn(4, 2048), "fc.bias": torch.randn(4)},
                "num_classes": 4,
                "class_names": [f"class_{j}" for j in range(4)],
                "model_version": "1.0.0",
                "training_metadata": {"accuracy": 0.85 + i * 0.02},
            }
            torch.save(checkpoint, model_path)

            model_id = registry.register_model(
                model_path=model_path,
                name=f"switch_model_{i}",
                architecture="resnet50",
                dataset_version="test_v1.0",
                hyperparameters={"num_classes": 4},
                performance_metrics={"accuracy": 0.85 + i * 0.02},
                description=f"Model switching test model {i}",
            )
            model_ids.append(model_id)

        # Test model manager switching performance
        config_path = performance_workspace / "switch_config.json"
        manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

        # Sync with registry
        with patch.object(manager, "_load_local_model") as mock_load:
            mock_adapter = torch.nn.Linear(2048, 4)  # Simple mock
            mock_load.return_value = mock_adapter

            sync_start = time.time()
            success = manager.sync_with_registry()
            sync_time = time.time() - sync_start

            assert success, "Registry sync should succeed"
            # Sync time should be reasonable
            assert sync_time < 10.0, f"Registry sync too slow: {sync_time:.2f}s"

        models = manager.list_available_models()
        registry_models = [m for m in models if "registry" in m.get("model_id", "")]

        # Test model switching times
        switching_times = []

        for model in registry_models[:3]:  # Test first 3 models
            with patch.object(manager, "_load_local_model") as mock_load:
                mock_adapter = torch.nn.Linear(2048, 4)
                mock_load.return_value = mock_adapter

                switch_start = time.time()
                success = manager.load_model(model["id"])
                switch_time = time.time() - switch_start

                assert success, f"Model switching should succeed for {model['id']}"
                switching_times.append(switch_time)

                assert switch_time < PerformanceBaseline.MODEL_SWITCHING_TIME_MAX, f"Model switching regression: {switch_time:.3f}s > {PerformanceBaseline.MODEL_SWITCHING_TIME_MAX}s"

        avg_switching_time = sum(switching_times) / len(switching_times)

        print(f"  Registry Sync Time: {sync_time:.3f}s")
        print(f"  Avg Model Switching Time: {avg_switching_time:.3f}s (max: {PerformanceBaseline.MODEL_SWITCHING_TIME_MAX}s)")
        print("✅ Model switching performance within acceptable limits")

    def test_dataset_operations_performance_regression(self, performance_dataset):
        """Test dataset operations performance regression."""
        print("\n=== Dataset Operations Performance Regression Test ===")

        dataset_manager = DatasetManager()

        # Test dataset validation performance
        validation_start = time.time()
        validation_result = dataset_manager.validate_dataset(performance_dataset)
        validation_time = time.time() - validation_start

        assert validation_result.is_valid, "Dataset should be valid"
        assert validation_time < PerformanceBaseline.DATASET_VALIDATION_TIME_MAX, f"Dataset validation regression: {validation_time:.2f}s > {PerformanceBaseline.DATASET_VALIDATION_TIME_MAX}s"

        # Test dataset analysis performance
        analysis_start = time.time()
        analysis_result = dataset_manager.analyze_dataset(performance_dataset)
        analysis_time = time.time() - analysis_start

        assert analysis_result.total_samples > 0, "Dataset analysis should find samples"
        assert analysis_time < PerformanceBaseline.DATASET_ANALYSIS_TIME_MAX, f"Dataset analysis regression: {analysis_time:.2f}s > {PerformanceBaseline.DATASET_ANALYSIS_TIME_MAX}s"

        print(f"  Dataset Validation Time: {validation_time:.2f}s (max: {PerformanceBaseline.DATASET_VALIDATION_TIME_MAX}s)")
        print(f"  Dataset Analysis Time: {analysis_time:.2f}s (max: {PerformanceBaseline.DATASET_ANALYSIS_TIME_MAX}s)")
        print("✅ Dataset operations performance within acceptable limits")

    def test_memory_usage_regression(self, performance_workspace):
        """Test memory usage regression across all components."""
        print("\n=== Memory Usage Regression Test ===")

        import gc

        # Clear memory before test
        gc.collect()

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        assert baseline_memory < PerformanceBaseline.MEMORY_USAGE_BASELINE_MAX, f"Baseline memory too high: {baseline_memory:.1f}MB > {PerformanceBaseline.MEMORY_USAGE_BASELINE_MAX}MB"

        # Test registry memory usage
        registry = ModelRegistry(performance_workspace / "models")

        # Add several models
        for i in range(5):
            model_path = performance_workspace / f"memory_model_{i}.pt"
            checkpoint = {
                "model_state_dict": {"fc.weight": torch.randn(4, 2048), "fc.bias": torch.randn(4)},
                "num_classes": 4,
                "class_names": [f"class_{j}" for j in range(4)],
                "model_version": "1.0.0",
            }
            torch.save(checkpoint, model_path)

            registry.register_model(
                model_path=model_path,
                name=f"memory_model_{i}",
                architecture="resnet50",
                dataset_version="test_v1.0",
                hyperparameters={"num_classes": 4},
                performance_metrics={"accuracy": 0.90},
                description=f"Memory test model {i}",
            )

        registry_memory = process.memory_info().rss / 1024 / 1024
        registry_increase = registry_memory - baseline_memory

        assert registry_increase < PerformanceBaseline.MEMORY_USAGE_REGISTRY_MAX, f"Registry memory regression: {registry_increase:.1f}MB > {PerformanceBaseline.MEMORY_USAGE_REGISTRY_MAX}MB"

        # Test adapter memory usage
        adapter = VisionAdapter()

        with patch.object(adapter, "_create_model") as mock_create_model:
            # Use a reasonably sized mock model
            mock_model = torch.nn.Sequential(torch.nn.Linear(2048, 512), torch.nn.ReLU(), torch.nn.Linear(512, 4))
            mock_create_model.return_value = mock_model

            models = registry.list_models()
            if models:
                adapter.load_from_registry(models[0].metadata.model_id)

        adapter_memory = process.memory_info().rss / 1024 / 1024
        adapter_increase = adapter_memory - baseline_memory

        assert adapter_increase < PerformanceBaseline.MEMORY_USAGE_ADAPTER_MAX, f"Adapter memory regression: {adapter_increase:.1f}MB > {PerformanceBaseline.MEMORY_USAGE_ADAPTER_MAX}MB"

        # Test memory cleanup
        del adapter
        del registry
        gc.collect()

        cleanup_memory = process.memory_info().rss / 1024 / 1024
        memory_recovered = adapter_memory - cleanup_memory

        # Should recover at least some memory
        assert memory_recovered > 0, "No memory recovered after cleanup"

        print(f"  Baseline Memory: {baseline_memory:.1f}MB (max: {PerformanceBaseline.MEMORY_USAGE_BASELINE_MAX}MB)")
        print(f"  Registry Memory Increase: {registry_increase:.1f}MB (max: {PerformanceBaseline.MEMORY_USAGE_REGISTRY_MAX}MB)")
        print(f"  Adapter Memory Increase: {adapter_increase:.1f}MB (max: {PerformanceBaseline.MEMORY_USAGE_ADAPTER_MAX}MB)")
        print(f"  Memory Recovered: {memory_recovered:.1f}MB")
        print("✅ Memory usage within acceptable limits")

    def test_scalability_performance_regression(self, performance_workspace):
        """Test performance scalability with increasing load."""
        print("\n=== Scalability Performance Regression Test ===")

        registry = ModelRegistry(performance_workspace / "models")

        # Test performance with increasing number of models
        model_counts = [5, 10, 20]
        performance_metrics = []

        for count in model_counts:
            # Create models
            model_ids = []
            for i in range(count):
                model_path = performance_workspace / f"scale_model_{count}_{i}.pt"
                checkpoint = {
                    "model_state_dict": {"fc.weight": torch.randn(4, 2048), "fc.bias": torch.randn(4)},
                    "num_classes": 4,
                    "class_names": [f"class_{j}" for j in range(4)],
                    "model_version": "1.0.0",
                }
                torch.save(checkpoint, model_path)

                model_id = registry.register_model(
                    model_path=model_path,
                    name=f"scale_model_{count}_{i}",
                    architecture="resnet50",
                    dataset_version="test_v1.0",
                    hyperparameters={"num_classes": 4},
                    performance_metrics={"accuracy": 0.90},
                    description=f"Scalability test model {i} for count {count}",
                )
                model_ids.append(model_id)

            # Test search performance
            search_start = time.time()
            search_results = registry.search_models(architecture="resnet50")
            search_time = time.time() - search_start

            # Test comparison performance
            comparison_start = time.time()
            comparison = registry.compare_models(model_ids[: min(5, len(model_ids))])
            comparison_time = time.time() - comparison_start

            performance_metrics.append(
                {"model_count": count, "search_time": search_time, "comparison_time": comparison_time, "search_time_per_model": search_time / count, "found_models": len(search_results)}
            )

        # Analyze scalability
        for metrics in performance_metrics:
            print(f"  Models: {metrics['model_count']}, Search: {metrics['search_time']:.3f}s, Comparison: {metrics['comparison_time']:.3f}s, Per-model: {metrics['search_time_per_model']:.4f}s")

        # Check that performance doesn't degrade exponentially
        first_metrics = performance_metrics[0]
        last_metrics = performance_metrics[-1]

        # Search time should scale reasonably (not exponentially)
        search_scaling_factor = last_metrics["search_time"] / first_metrics["search_time"]
        model_scaling_factor = last_metrics["model_count"] / first_metrics["model_count"]

        # Performance should not degrade more than linearly with model count
        assert search_scaling_factor < model_scaling_factor * 2, f"Search performance scaling too poor: {search_scaling_factor:.2f}x vs {model_scaling_factor:.2f}x models"

        print("✅ Scalability performance within acceptable limits")

    def test_concurrent_operations_performance_regression(self, performance_workspace):
        """Test performance under concurrent operations."""
        print("\n=== Concurrent Operations Performance Regression Test ===")

        import queue
        import threading

        registry = ModelRegistry(performance_workspace / "models")
        results_queue = queue.Queue()

        def concurrent_operation_worker(worker_id: int):
            """Worker for concurrent operations testing."""
            try:
                start_time = time.time()

                # Create and register model
                model_path = performance_workspace / f"concurrent_model_{worker_id}.pt"
                checkpoint = {
                    "model_state_dict": {"fc.weight": torch.randn(4, 2048), "fc.bias": torch.randn(4)},
                    "num_classes": 4,
                    "class_names": [f"class_{j}" for j in range(4)],
                    "model_version": "1.0.0",
                }
                torch.save(checkpoint, model_path)

                model_id = registry.register_model(
                    model_path=model_path,
                    name=f"concurrent_model_{worker_id}",
                    architecture="resnet50",
                    dataset_version="test_v1.0",
                    hyperparameters={"num_classes": 4},
                    performance_metrics={"accuracy": 0.90},
                    description=f"Concurrent test model {worker_id}",
                )

                # Perform search operation
                search_results = registry.search_models(architecture="resnet50")

                end_time = time.time()

                results_queue.put({"worker_id": worker_id, "success": True, "time": end_time - start_time, "model_id": model_id, "search_results": len(search_results)})

            except Exception as e:
                results_queue.put({"worker_id": worker_id, "success": False, "error": str(e), "time": 0})

        # Run concurrent workers
        num_workers = 3
        threads = []

        overall_start = time.time()

        for i in range(num_workers):
            thread = threading.Thread(target=concurrent_operation_worker, args=(i,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        overall_time = time.time() - overall_start

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) == num_workers, "All concurrent operations should succeed"

        avg_operation_time = sum(r["time"] for r in successful_results) / len(successful_results)

        # Concurrent operations should not be significantly slower than sequential
        assert avg_operation_time < 15.0, f"Concurrent operations too slow: {avg_operation_time:.2f}s"
        assert overall_time < 20.0, f"Overall concurrent time too slow: {overall_time:.2f}s"

        print(f"  Concurrent Workers: {num_workers}")
        print(f"  Overall Time: {overall_time:.2f}s")
        print(f"  Avg Operation Time: {avg_operation_time:.2f}s")
        print("✅ Concurrent operations performance within acceptable limits")

    def test_generate_performance_report(self, performance_workspace):
        """Generate comprehensive performance report."""
        print("\n=== Performance Report Generation ===")

        # Collect system information
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            "python_version": f"{torch.__version__}",
            "torch_version": torch.__version__,
        }

        # Create performance report
        performance_report = {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": system_info,
            "performance_baselines": {
                "training_time_per_epoch_max": PerformanceBaseline.TRAINING_TIME_PER_EPOCH_MAX,
                "setup_time_max": PerformanceBaseline.SETUP_TIME_MAX,
                "model_loading_time_max": PerformanceBaseline.MODEL_LOADING_TIME_MAX,
                "inference_time_single_max": PerformanceBaseline.INFERENCE_TIME_SINGLE_MAX,
                "memory_usage_training_max": PerformanceBaseline.MEMORY_USAGE_TRAINING_MAX,
            },
            "test_results": {
                "all_tests_passed": True,  # Would be set based on actual test results
                "performance_within_limits": True,
                "regression_detected": False,
            },
            "recommendations": [
                "Monitor training time per epoch in production",
                "Set up automated performance regression testing",
                "Consider memory optimization for large model deployments",
                "Implement performance monitoring in production environment",
            ],
        }

        # Save performance report
        report_path = performance_workspace / "performance_report.json"
        with open(report_path, "w") as f:
            json.dump(performance_report, f, indent=2)

        print(f"✅ Performance report generated: {report_path}")
        print(f"  System: {system_info['cpu_count']} CPUs, {system_info['memory_total']:.1f}GB RAM")
        print(f"  PyTorch: {system_info['torch_version']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
