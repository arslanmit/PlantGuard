"""Unit tests for resource management utilities."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.training.resource_manager import (
    ResourceInfo,
    ResourceManager,
    detect_optimal_config,
    get_resource_manager,
)


class TestResourceManager:
    """Test ResourceManager functionality."""

    def test_init(self) -> None:
        """Test ResourceManager initialization."""
        manager = ResourceManager()
        assert manager._resource_info is None
        assert manager._optimal_batch_sizes == {}

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.device_count", return_value=1)
    @patch("torch.cuda.get_device_name", return_value="NVIDIA RTX 3080")
    def test_detect_device_cuda(self, mock_name: Any, mock_count: Any, mock_available: Any) -> None:
        """Test CUDA device detection."""
        manager = ResourceManager()
        device_type, device_name, device_count = manager._detect_device()

        assert device_type == "cuda"
        assert device_name == "NVIDIA RTX 3080"
        assert device_count == 1

    @patch("torch.cuda.is_available", return_value=False)
    @patch("torch.backends.mps.is_available", return_value=True)
    def test_detect_device_mps(self, mock_mps: Any, mock_cuda: Any) -> None:
        """Test MPS device detection."""
        manager = ResourceManager()
        device_type, device_name, device_count = manager._detect_device()

        assert device_type == "mps"
        assert device_name == "Apple Silicon GPU"
        assert device_count == 1

    @patch("torch.cuda.is_available", return_value=False)
    @patch("torch.backends.mps.is_available", return_value=False)
    @patch("torch.get_num_threads", return_value=8)
    @patch("platform.processor", return_value="Intel Core i7")
    def test_detect_device_cpu(
        self, mock_processor: Any, mock_threads: Any, mock_mps: Any, mock_cuda: Any
    ) -> None:
        """Test CPU device detection."""
        manager = ResourceManager()
        device_type, device_name, device_count = manager._detect_device()

        assert device_type == "cpu"
        assert device_name == "Intel Core i7"
        assert device_count == 8

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.get_device_properties")
    @patch("torch.cuda.memory_allocated", return_value=1024**3)  # 1GB
    def test_get_memory_info_cuda(
        self, mock_allocated: Any, mock_properties: Any, mock_available: Any
    ) -> None:
        """Test CUDA memory information retrieval."""
        # Mock device properties
        mock_props = MagicMock()
        mock_props.total_memory = 8 * (1024**3)  # 8GB
        mock_properties.return_value = mock_props

        manager = ResourceManager()
        total_gb, available_gb = manager._get_memory_info("cuda")

        assert total_gb == 8.0
        assert available_gb == 7.0  # 8GB - 1GB allocated

    @patch("psutil.virtual_memory")
    def test_get_memory_info_mps(self, mock_memory: Any) -> None:
        """Test MPS memory information retrieval."""
        # Mock system memory
        mock_mem = MagicMock()
        mock_mem.total = 16 * (1024**3)  # 16GB
        mock_mem.available = 12 * (1024**3)  # 12GB
        mock_memory.return_value = mock_mem

        manager = ResourceManager()
        total_gb, available_gb = manager._get_memory_info("mps")

        # MPS uses 70% of system memory, capped at 32GB
        expected_total = min(16.0 * 0.7, 32.0)
        expected_available = min(12.0 * 0.7, expected_total)

        assert total_gb == expected_total
        assert available_gb == expected_available

    def test_get_memory_info_mps_no_psutil(self) -> None:
        """Test MPS memory info without psutil."""
        with patch("psutil.virtual_memory", side_effect=ImportError):
            manager = ResourceManager()
            total_gb, available_gb = manager._get_memory_info("mps")

            # Should use conservative defaults
            assert total_gb == 16.0
            assert available_gb == 12.0

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.get_device_capability", return_value=(7, 5))  # Compute capability 7.5
    def test_check_mixed_precision_support_cuda(
        self, mock_capability: Any, mock_available: Any
    ) -> None:
        """Test mixed precision support check for CUDA."""
        manager = ResourceManager()
        supported = manager._check_mixed_precision_support("cuda")
        assert supported is True

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.get_device_capability", return_value=(6, 1))  # Compute capability 6.1
    def test_check_mixed_precision_support_cuda_old(
        self, mock_capability: Any, mock_available: Any
    ) -> None:
        """Test mixed precision support check for old CUDA."""
        manager = ResourceManager()
        supported = manager._check_mixed_precision_support("cuda")
        assert supported is False

    def test_check_mixed_precision_support_mps(self) -> None:
        """Test mixed precision support check for MPS."""
        manager = ResourceManager()
        supported = manager._check_mixed_precision_support("mps")
        assert supported is True

    def test_check_mixed_precision_support_cpu(self) -> None:
        """Test mixed precision support check for CPU."""
        manager = ResourceManager()
        supported = manager._check_mixed_precision_support("cpu")
        assert supported is False

    def test_round_to_power_of_2(self) -> None:
        """Test rounding to power of 2."""
        manager = ResourceManager()

        assert manager._round_to_power_of_2(0) == 1
        assert manager._round_to_power_of_2(1) == 1
        assert manager._round_to_power_of_2(3) == 2
        assert manager._round_to_power_of_2(7) == 4
        assert manager._round_to_power_of_2(8) == 8
        assert manager._round_to_power_of_2(15) == 8
        assert manager._round_to_power_of_2(16) == 16
        assert manager._round_to_power_of_2(100) == 64

    @patch.object(ResourceManager, "detect_resources")
    def test_get_optimal_batch_size(self, mock_detect: Any) -> None:
        """Test optimal batch size calculation."""
        # Mock resource info
        mock_resource_info = ResourceInfo(
            device_type="cuda",
            device_name="Test GPU",
            device_count=1,
            total_memory=8.0,
            available_memory=6.0,
            cpu_count=8,
            cpu_name="Test CPU",
            platform="Linux",
            python_version="3.11.0",
            pytorch_version="2.0.0",
            mixed_precision_supported=True,
            distributed_training_supported=True,
        )
        mock_detect.return_value = mock_resource_info

        manager = ResourceManager()
        batch_size = manager.get_optimal_batch_size(
            model_size_mb=100.0,
            image_size=(224, 224),
            channels=3,
            safety_factor=0.8,
        )

        assert isinstance(batch_size, int)
        assert batch_size >= 1
        # Should be a power of 2
        assert batch_size & (batch_size - 1) == 0

    @patch.object(ResourceManager, "detect_resources")
    def test_get_optimal_batch_size_cpu(self, mock_detect: Any) -> None:
        """Test optimal batch size calculation for CPU."""
        # Mock CPU resource info
        mock_resource_info = ResourceInfo(
            device_type="cpu",
            device_name="Test CPU",
            device_count=1,
            total_memory=16.0,
            available_memory=12.0,
            cpu_count=8,
            cpu_name="Test CPU",
            platform="Linux",
            python_version="3.11.0",
            pytorch_version="2.0.0",
            mixed_precision_supported=False,
            distributed_training_supported=True,
        )
        mock_detect.return_value = mock_resource_info

        manager = ResourceManager()
        batch_size = manager.get_optimal_batch_size()

        # CPU should be capped at 16
        assert batch_size <= 16

    @patch.object(ResourceManager, "detect_resources")
    def test_get_optimal_num_workers(self, mock_detect: Any) -> None:
        """Test optimal number of workers calculation."""
        mock_resource_info = ResourceInfo(
            device_type="cuda",
            device_name="Test GPU",
            device_count=1,
            total_memory=8.0,
            available_memory=6.0,
            cpu_count=16,
            cpu_name="Test CPU",
            platform="Linux",
            python_version="3.11.0",
            pytorch_version="2.0.0",
            mixed_precision_supported=True,
            distributed_training_supported=True,
        )
        mock_detect.return_value = mock_resource_info

        manager = ResourceManager()
        num_workers = manager.get_optimal_num_workers()

        # Should be capped at 8 for GPU
        assert num_workers == 8

    @patch.object(ResourceManager, "detect_resources")
    def test_get_optimal_num_workers_cpu(self, mock_detect: Any) -> None:
        """Test optimal number of workers calculation for CPU."""
        mock_resource_info = ResourceInfo(
            device_type="cpu",
            device_name="Test CPU",
            device_count=1,
            total_memory=16.0,
            available_memory=12.0,
            cpu_count=8,
            cpu_name="Test CPU",
            platform="Linux",
            python_version="3.11.0",
            pytorch_version="2.0.0",
            mixed_precision_supported=False,
            distributed_training_supported=True,
        )
        mock_detect.return_value = mock_resource_info

        manager = ResourceManager()
        num_workers = manager.get_optimal_num_workers()

        # CPU should use half the cores
        assert num_workers == 4

    @patch.object(ResourceManager, "detect_resources")
    @patch.object(ResourceManager, "get_optimal_batch_size", return_value=32)
    @patch.object(ResourceManager, "get_optimal_num_workers", return_value=4)
    def test_optimize_training_config(
        self, mock_workers: Any, mock_batch: Any, mock_detect: Any
    ) -> None:
        """Test training configuration optimization."""
        mock_resource_info = ResourceInfo(
            device_type="cuda",
            device_name="Test GPU",
            device_count=1,
            total_memory=8.0,
            available_memory=6.0,
            cpu_count=8,
            cpu_name="Test CPU",
            platform="Linux",
            python_version="3.11.0",
            pytorch_version="2.0.0",
            mixed_precision_supported=True,
            distributed_training_supported=True,
        )
        mock_detect.return_value = mock_resource_info

        manager = ResourceManager()
        config = {
            "device": "auto",
            "batch_size": "auto",
            "num_workers": "auto",
            "mixed_precision": "auto",
        }

        optimized = manager.optimize_training_config(config)

        assert optimized["device"] == "cuda"
        assert optimized["batch_size"] == 32
        assert optimized["num_workers"] == 4
        assert optimized["mixed_precision"] is True

    @patch.object(ResourceManager, "detect_resources")
    def test_optimize_training_config_mixed_precision_warning(self, mock_detect: Any) -> None:
        """Test mixed precision warning when not supported."""
        mock_resource_info = ResourceInfo(
            device_type="cpu",
            device_name="Test CPU",
            device_count=1,
            total_memory=16.0,
            available_memory=12.0,
            cpu_count=8,
            cpu_name="Test CPU",
            platform="Linux",
            python_version="3.11.0",
            pytorch_version="2.0.0",
            mixed_precision_supported=False,
            distributed_training_supported=True,
        )
        mock_detect.return_value = mock_resource_info

        manager = ResourceManager()
        config = {"mixed_precision": True}

        optimized = manager.optimize_training_config(config)

        # Should be disabled due to lack of support
        assert optimized["mixed_precision"] is False

    def test_estimate_model_size(self) -> None:
        """Test model size estimation."""
        manager = ResourceManager()

        assert manager._estimate_model_size("resnet18") == 45
        assert manager._estimate_model_size("resnet50") == 100
        assert manager._estimate_model_size("resnet152") == 230
        assert manager._estimate_model_size("unknown") == 100  # Default

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.memory_allocated", return_value=1024**3)  # 1GB
    @patch("torch.cuda.memory_reserved", return_value=2 * 1024**3)  # 2GB
    @patch("torch.cuda.get_device_properties")
    def test_get_memory_usage_cuda(
        self, mock_props: Any, mock_reserved: Any, mock_allocated: Any, mock_available: Any
    ) -> None:
        """Test memory usage retrieval for CUDA."""
        mock_device_props = MagicMock()
        mock_device_props.total_memory = 8 * (1024**3)  # 8GB
        mock_props.return_value = mock_device_props

        manager = ResourceManager()
        # Mock resource info to return CUDA
        with patch.object(manager, "detect_resources") as mock_detect:
            mock_resource_info = ResourceInfo(
                device_type="cuda",
                device_name="Test GPU",
                device_count=1,
                total_memory=8.0,
                available_memory=6.0,
                cpu_count=8,
                cpu_name="Test CPU",
                platform="Linux",
                python_version="3.11.0",
                pytorch_version="2.0.0",
                mixed_precision_supported=True,
                distributed_training_supported=True,
            )
            mock_detect.return_value = mock_resource_info

            usage = manager.get_memory_usage()

            assert "gpu_allocated" in usage
            assert "gpu_reserved" in usage
            assert "gpu_total" in usage
            assert "gpu_free" in usage
            assert usage["gpu_allocated"] == 1.0
            assert usage["gpu_reserved"] == 2.0
            assert usage["gpu_total"] == 8.0
            assert usage["gpu_free"] == 6.0

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.empty_cache")
    def test_clear_memory_cache(self, mock_empty_cache: Any, mock_available: Any) -> None:
        """Test memory cache clearing."""
        manager = ResourceManager()
        manager.clear_memory_cache()

        mock_empty_cache.assert_called_once()


class TestGlobalFunctions:
    """Test global utility functions."""

    def test_get_resource_manager_singleton(self) -> None:
        """Test that get_resource_manager returns singleton."""
        manager1 = get_resource_manager()
        manager2 = get_resource_manager()

        assert manager1 is manager2
        assert isinstance(manager1, ResourceManager)

    @patch.object(ResourceManager, "optimize_training_config")
    def test_detect_optimal_config_with_base(self, mock_optimize: Any) -> None:
        """Test detect_optimal_config with base configuration."""
        base_config = {"epochs": 100, "learning_rate": 0.001}
        mock_optimize.return_value = {"epochs": 100, "learning_rate": 0.001, "device": "cuda"}

        result = detect_optimal_config(base_config)

        mock_optimize.assert_called_once_with(base_config)
        assert result["epochs"] == 100

    @patch.object(ResourceManager, "optimize_training_config")
    def test_detect_optimal_config_without_base(self, mock_optimize: Any) -> None:
        """Test detect_optimal_config without base configuration."""
        mock_optimize.return_value = {"device": "cuda", "batch_size": 32}

        detect_optimal_config()

        # Should be called with default auto config
        expected_config = {
            "device": "auto",
            "batch_size": "auto",
            "num_workers": "auto",
            "mixed_precision": "auto",
        }
        mock_optimize.assert_called_once_with(expected_config)


if __name__ == "__main__":
    pytest.main([__file__])
