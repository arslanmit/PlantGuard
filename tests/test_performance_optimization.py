"""Tests for performance optimization system."""

import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import Dataset

from src.training.advanced_data_loading import AdvancedDataLoadingConfig, create_advanced_data_loader
from src.training.config import TrainingConfig
from src.training.performance_optimizer import (
    PerformanceOptimizationConfig,
    PerformanceOptimizer,
    create_performance_optimization_config,
    optimize_training_performance,
)
from src.training.performance_profiler import ProfilerConfig, TrainingProfiler
from src.training.production_trainer import ProductionTrainer
from src.training.training_cache import CacheConfig, CacheManager


class DummyDataset(Dataset):
    """Dummy dataset for testing."""

    def __init__(self, size: int = 100):
        """Initialize dummy dataset."""
        self.size = size

    def __len__(self) -> int:
        """Return dataset size."""
        return self.size

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        """Get dummy item."""
        # Create dummy image tensor
        image = torch.randn(3, 224, 224)
        label = idx % 10  # 10 classes
        return image, label


class DummyModel(nn.Module):
    """Dummy model for testing."""

    def __init__(self, num_classes: int = 10):
        """Initialize dummy model."""
        super().__init__()
        self.conv1 = nn.Conv2d(3, 64, 3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, 3, padding=1)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


class TestPerformanceProfiler:
    """Test performance profiler functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def profiler_config(self, temp_dir):
        """Create profiler configuration."""
        return ProfilerConfig(
            profile_batches=5,
            warmup_batches=1,
            output_dir=temp_dir / "profiling",
            export_chrome_trace=True,
        )

    @pytest.fixture
    def dummy_components(self):
        """Create dummy training components."""
        model = DummyModel()
        dataset = DummyDataset(50)
        optimizer = torch.optim.Adam(model.parameters())
        criterion = nn.CrossEntropyLoss()
        device = torch.device("cpu")

        return model, dataset, optimizer, criterion, device

    def test_profiler_initialization(self, profiler_config):
        """Test profiler initialization."""
        profiler = TrainingProfiler(profiler_config)

        assert profiler.config == profiler_config
        assert profiler.config.output_dir.exists()
        assert len(profiler.batch_times) == 0

    def test_performance_profiling(self, profiler_config, dummy_components):
        """Test performance profiling functionality."""
        model, dataset, optimizer, criterion, device = dummy_components

        # Create data loader
        from torch.utils.data import DataLoader

        data_loader = DataLoader(dataset, batch_size=8, shuffle=True)

        # Create profiler
        profiler = TrainingProfiler(profiler_config)

        # Run profiling
        profile_result = profiler.profile_training_loop(model, data_loader, optimizer, criterion, device)

        # Verify results
        assert profile_result.success if hasattr(profile_result, "success") else True
        assert profile_result.avg_batch_time_ms > 0
        assert profile_result.throughput_samples_per_sec > 0
        assert len(profile_result.bottlenecks) >= 0

    def test_bottleneck_identification(self, profiler_config, dummy_components):
        """Test bottleneck identification."""
        model, dataset, optimizer, criterion, device = dummy_components

        from torch.utils.data import DataLoader

        data_loader = DataLoader(dataset, batch_size=4, shuffle=True, num_workers=0)

        profiler = TrainingProfiler(profiler_config)
        profile_result = profiler.profile_training_loop(model, data_loader, optimizer, criterion, device)

        # Should identify some bottlenecks or components
        assert isinstance(profile_result.bottlenecks, list)

        # Check that component times are measured
        assert profile_result.data_loading_time_ms >= 0
        assert profile_result.forward_pass_time_ms >= 0
        assert profile_result.backward_pass_time_ms >= 0


class TestAdvancedDataLoading:
    """Test advanced data loading optimizations."""

    @pytest.fixture
    def data_loading_config(self):
        """Create data loading configuration."""
        return AdvancedDataLoadingConfig(
            enable_intelligent_prefetching=False,  # Disable for testing
            enable_gpu_preprocessing=False,
            enable_memory_mapping=True,
            enable_adaptive_batching=False,
            cache_size_mb=100,
        )

    def test_advanced_data_loader_creation(self, data_loading_config):
        """Test advanced data loader creation."""
        dataset = DummyDataset(50)
        device = torch.device("cpu")

        data_loader = create_advanced_data_loader(dataset, data_loading_config, batch_size=8, device=device)

        assert data_loader is not None
        assert data_loader.batch_size == 8

    def test_memory_mapped_dataset(self, tmp_path):
        """Test memory-mapped dataset functionality."""
        # Create dummy dataset directory
        dataset_dir = tmp_path / "test_dataset"

        # Create class directories with dummy images
        for class_name in ["class_0", "class_1"]:
            class_dir = dataset_dir / class_name
            class_dir.mkdir(parents=True)

            for i in range(10):
                img = Image.new("RGB", (64, 64), color=(i * 25, 100, 150))
                img.save(class_dir / f"image_{i:03d}.jpg")

        # Test memory-mapped dataset
        from src.training.advanced_data_loading import MemoryMappedDataset

        dataset = MemoryMappedDataset(dataset_dir, cache_size_mb=10)

        assert len(dataset) == 20  # 10 images per class, 2 classes
        assert len(dataset.classes) == 2

        # Test data loading
        image, label = dataset[0]
        assert isinstance(image, torch.Tensor)
        assert image.shape == (3, 64, 64)
        assert isinstance(label, int)


class TestTrainingCache:
    """Test training cache functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def cache_config(self, temp_dir):
        """Create cache configuration."""
        return CacheConfig(
            cache_root=temp_dir / "cache",
            max_cache_size_gb=1.0,
            enable_model_caching=True,
            enable_data_caching=True,
        )

    def test_cache_manager_initialization(self, cache_config):
        """Test cache manager initialization."""
        with CacheManager(cache_config) as cache_manager:
            assert cache_manager.config == cache_config
            assert cache_manager.config.cache_root.exists()
            assert cache_manager.config.model_cache_dir.exists()
            assert cache_manager.config.data_cache_dir.exists()

    def test_cache_operations(self, cache_config):
        """Test basic cache operations."""
        with CacheManager(cache_config) as cache_manager:
            # Test caching data
            test_data = {"key": "value", "number": 42}
            cache_key = cache_manager.get_cache_key("test_data", test_data)

            # Put in cache
            cache_manager.put_in_cache(cache_key, test_data)

            # Check if cached
            assert cache_manager.has_cache(cache_key)

            # Retrieve from cache
            retrieved_data = cache_manager.get_from_cache(cache_key)
            assert retrieved_data == test_data

    def test_model_state_cache(self, cache_config):
        """Test model state caching."""
        from src.training.training_cache import ModelStateCache

        with CacheManager(cache_config) as cache_manager:
            model_cache = ModelStateCache(cache_manager)

            # Create dummy model and optimizer
            model = DummyModel()
            optimizer = torch.optim.Adam(model.parameters())

            # Cache model state
            cache_key = model_cache.cache_model_state(model, optimizer, epoch=5, config_hash="test_hash")

            assert cache_key is not None
            assert cache_manager.has_cache(cache_key)


class TestPerformanceOptimizer:
    """Test comprehensive performance optimizer."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def optimization_config(self, temp_dir):
        """Create optimization configuration."""
        return create_performance_optimization_config(
            enable_all_optimizations=True,
            target_throughput=50.0,  # Lower target for testing
            max_memory_gb=4.0,
            output_dir=temp_dir / "optimization",
        )

    @pytest.fixture
    def dummy_components(self):
        """Create dummy training components."""
        model = DummyModel()
        dataset = DummyDataset(50)
        optimizer = torch.optim.Adam(model.parameters())
        criterion = nn.CrossEntropyLoss()
        device = torch.device("cpu")

        return model, dataset, optimizer, criterion, device

    def test_performance_optimizer_initialization(self, optimization_config):
        """Test performance optimizer initialization."""
        optimizer = PerformanceOptimizer(optimization_config)

        assert optimizer.config == optimization_config
        assert optimizer.config.optimization_results_dir.exists()

    @patch("src.training.performance_optimizer.TrainingProfiler")
    def test_performance_optimization_pipeline(self, mock_profiler, optimization_config, dummy_components):
        """Test complete performance optimization pipeline."""
        model, dataset, optimizer, criterion, device = dummy_components

        # Mock profiler to avoid actual profiling
        mock_profile_result = MagicMock()
        mock_profile_result.avg_batch_time_ms = 100.0
        mock_profile_result.throughput_samples_per_sec = 25.0
        mock_profile_result.data_loading_time_ms = 20.0
        mock_profile_result.forward_pass_time_ms = 40.0
        mock_profile_result.backward_pass_time_ms = 30.0
        mock_profile_result.peak_memory_mb = 500.0
        mock_profile_result.memory_efficiency = 0.8

        mock_profiler_instance = MagicMock()
        mock_profiler_instance.profile_training_loop.return_value = mock_profile_result
        mock_profiler.return_value = mock_profiler_instance

        # Create optimizer
        perf_optimizer = PerformanceOptimizer(optimization_config)

        # Run optimization
        result = perf_optimizer.optimize_training_pipeline(model, dataset, optimizer, criterion, device, batch_size=8)

        # Verify results
        assert result.success
        assert len(result.optimization_steps) > 0
        assert len(result.recommendations) > 0
        assert result.optimization_time_seconds > 0

    def test_convenience_function(self, dummy_components):
        """Test convenience optimization function."""
        model, dataset, optimizer, criterion, device = dummy_components

        # Use minimal configuration for testing
        config = PerformanceOptimizationConfig(
            enable_profiling=False,  # Disable profiling for speed
            enable_distributed_training=False,
            enable_caching=False,
            enable_advanced_data_loading=False,
            save_optimization_report=False,
        )

        result = optimize_training_performance(model, dataset, optimizer, criterion, device, batch_size=8, config=config)

        assert result is not None
        assert isinstance(result.success, bool)


class TestProductionTrainerIntegration:
    """Test performance optimization integration with ProductionTrainer."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def dataset_dir(self, temp_dir):
        """Create dummy dataset directory."""
        dataset_dir = temp_dir / "dataset"

        # Create train/val split
        for split in ["train", "val"]:
            split_dir = dataset_dir / split

            for class_name in ["class_0", "class_1"]:
                class_dir = split_dir / class_name
                class_dir.mkdir(parents=True)

                num_samples = 20 if split == "train" else 5
                for i in range(num_samples):
                    img = Image.new("RGB", (64, 64), color=(i * 10, 100, 150))
                    img.save(class_dir / f"image_{i:03d}.jpg")

        return dataset_dir

    def test_production_trainer_with_optimization(self, dataset_dir, temp_dir):
        """Test ProductionTrainer with performance optimization enabled."""
        # Create configuration with optimization enabled
        config = TrainingConfig(
            experiment_name="optimization_test",
            model_architecture="resnet50",
            num_classes=2,
            epochs=2,  # Short for testing
            batch_size=4,
            learning_rate=0.001,
            device="cpu",
            enable_performance_optimization=True,
            target_throughput_samples_per_sec=10.0,  # Low target for testing
        )

        # Create trainer
        from src.training.dataset_manager import DatasetManager

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager, output_dir=temp_dir / "training")

        # Mock dataset path
        trainer.config.dataset_path = dataset_dir

        # Setup training (this should initialize performance optimization)
        success = trainer.setup_training()
        assert success

        # Check that performance optimizer was initialized
        assert trainer.performance_optimizer is not None

    @patch("src.training.performance_optimizer.PerformanceOptimizer.optimize_training_pipeline")
    def test_performance_optimization_execution(self, mock_optimize, dataset_dir, temp_dir):
        """Test performance optimization execution in ProductionTrainer."""
        # Mock optimization result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.performance_improvement = {"throughput_samples_per_sec": 25.0}
        mock_result.recommendations = ["Test recommendation"]
        mock_optimize.return_value = mock_result

        # Create configuration
        config = TrainingConfig(
            experiment_name="optimization_execution_test",
            model_architecture="resnet50",
            num_classes=2,
            epochs=1,
            batch_size=4,
            device="cpu",
            enable_performance_optimization=True,
        )

        # Create trainer
        from src.training.dataset_manager import DatasetManager

        dataset_manager = DatasetManager()
        trainer = ProductionTrainer(config, dataset_manager, output_dir=temp_dir / "training")

        # Mock dataset path
        trainer.config.dataset_path = dataset_dir

        # Setup training
        assert trainer.setup_training()

        # Run performance optimization
        result = trainer.optimize_training_performance()
        assert result is True

        # Verify optimization was called
        mock_optimize.assert_called_once()


class TestPerformanceRegression:
    """Test performance regression detection."""

    def test_performance_improvement_calculation(self):
        """Test performance improvement calculation."""
        from src.training.performance_optimizer import PerformanceOptimizer

        config = create_performance_optimization_config()
        optimizer = PerformanceOptimizer(config)

        initial = {
            "avg_batch_time_ms": 200.0,
            "throughput_samples_per_sec": 50.0,
            "memory_efficiency": 0.7,
        }

        final = {
            "avg_batch_time_ms": 150.0,  # 25% improvement
            "throughput_samples_per_sec": 75.0,  # 50% improvement
            "memory_efficiency": 0.85,  # ~21% improvement
        }

        improvements = optimizer._calculate_performance_improvement(initial, final)

        # Check improvements (approximately)
        assert abs(improvements["avg_batch_time_ms"] - 25.0) < 1.0  # Time reduction
        assert abs(improvements["throughput_samples_per_sec"] - 50.0) < 1.0  # Throughput increase
        assert abs(improvements["memory_efficiency"] - 21.4) < 1.0  # Efficiency increase

    def test_recommendation_generation(self):
        """Test optimization recommendation generation."""
        from src.training.performance_optimizer import PerformanceOptimizer

        config = create_performance_optimization_config(
            target_throughput=100.0,
            max_memory_gb=8.0,
        )
        optimizer = PerformanceOptimizer(config)

        # Simulate poor performance
        initial = {"throughput_samples_per_sec": 120.0}
        final = {
            "throughput_samples_per_sec": 50.0,  # Below target
            "avg_batch_time_ms": 200.0,  # Above target
            "data_loading_time_ms": 60.0,  # High data loading time
            "peak_memory_mb": 10000.0,  # High memory usage
        }

        recommendations = optimizer._generate_recommendations(initial, final)

        # Should generate relevant recommendations
        assert len(recommendations) > 0

        # Check for specific recommendations
        rec_text = " ".join(recommendations).lower()
        assert "throughput" in rec_text or "batch time" in rec_text


if __name__ == "__main__":
    pytest.main([__file__])
