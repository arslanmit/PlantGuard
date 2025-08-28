#!/usr/bin/env python3
"""
PlantGuard Performance Optimization Script

Analyzes system capabilities and provides optimization recommendations for:
- Model inference performance
- Memory usage optimization
- Apple Silicon MPS acceleration
- Batch size optimization
- Training parameter tuning
- AI agent-friendly JSON output
"""

import json
import logging
import platform
import time
from pathlib import Path
from typing import Any

import psutil

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """System performance analysis and optimization recommendations."""

    def __init__(self):
        self.system_info = self._gather_system_info()
        self.optimization_results = {}

    def _gather_system_info(self) -> dict[str, Any]:
        """Gather comprehensive system information."""
        info = {
            "platform": {
                "system": platform.system(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "is_apple_silicon": platform.machine() == "arm64" and platform.system() == "Darwin",
            },
            "memory": {
                "total_gb": psutil.virtual_memory().total / (1024**3),
                "available_gb": psutil.virtual_memory().available / (1024**3),
                "used_percent": psutil.virtual_memory().percent,
            },
            "cpu": {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            },
            "disk": {
                "total_gb": psutil.disk_usage(".").total / (1024**3),
                "free_gb": psutil.disk_usage(".").free / (1024**3),
                "used_percent": (psutil.disk_usage(".").total - psutil.disk_usage(".").free) / psutil.disk_usage(".").total * 100,
            },
        }

        # PyTorch specific info
        try:
            import torch

            info["pytorch"] = {
                "version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "mps_available": torch.backends.mps.is_available() if hasattr(torch.backends, "mps") else False,
                "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            }
        except ImportError:
            info["pytorch"] = {"installed": False}

        return info

    def analyze_memory_optimization(self) -> dict[str, Any]:
        """Analyze memory usage and provide optimization recommendations."""
        memory_info = self.system_info["memory"]
        total_gb = memory_info["total_gb"]
        available_gb = memory_info["available_gb"]

        recommendations = {
            "current_status": {
                "total_memory_gb": round(total_gb, 1),
                "available_memory_gb": round(available_gb, 1),
                "memory_pressure": "high" if memory_info["used_percent"] > 80 else "medium" if memory_info["used_percent"] > 60 else "low",
            },
            "batch_size_recommendations": {},
            "model_loading_strategy": "",
            "memory_optimizations": [],
        }

        # Batch size recommendations based on available memory
        if total_gb >= 32:
            recommendations["batch_size_recommendations"] = {
                "training": 64,
                "inference": 128,
                "explanation": "High memory system - can handle large batches",
            }
        elif total_gb >= 16:
            recommendations["batch_size_recommendations"] = {
                "training": 32,
                "inference": 64,
                "explanation": "Medium memory system - moderate batch sizes",
            }
        elif total_gb >= 8:
            recommendations["batch_size_recommendations"] = {
                "training": 16,
                "inference": 32,
                "explanation": "Standard memory system - conservative batch sizes",
            }
        else:
            recommendations["batch_size_recommendations"] = {
                "training": 8,
                "inference": 16,
                "explanation": "Low memory system - use small batch sizes",
            }

        # Model loading strategy
        if available_gb > 8:
            recommendations["model_loading_strategy"] = "keep_models_in_memory"
        elif available_gb > 4:
            recommendations["model_loading_strategy"] = "selective_model_caching"
        else:
            recommendations["model_loading_strategy"] = "load_on_demand"

        # Memory optimization techniques
        optimizations = []

        if memory_info["used_percent"] > 70:
            optimizations.append(
                {"technique": "enable_gradient_checkpointing", "description": "Reduce memory usage during training", "impact": "medium"}
            )

        if total_gb < 16:
            optimizations.append({"technique": "use_mixed_precision", "description": "Use float16 instead of float32", "impact": "high"})

        optimizations.append(
            {
                "technique": "enable_memory_efficient_attention",
                "description": "Use attention implementations that use less memory",
                "impact": "medium",
            }
        )

        recommendations["memory_optimizations"] = optimizations

        return recommendations

    def analyze_compute_optimization(self) -> dict[str, Any]:
        """Analyze compute capabilities and provide optimization recommendations."""
        cpu_info = self.system_info["cpu"]
        pytorch_info = self.system_info.get("pytorch", {})
        platform_info = self.system_info["platform"]

        recommendations = {"device_strategy": {}, "parallelization": {}, "compute_optimizations": []}

        # Device selection strategy
        device_priority = []

        if pytorch_info.get("mps_available", False):
            device_priority.append("mps")
            recommendations["device_strategy"]["primary"] = "mps"
            recommendations["device_strategy"]["reason"] = "Apple Silicon MPS acceleration available"
            recommendations["device_strategy"]["optimizations"] = [
                "Enable MPS fallback for unsupported operations",
                "Use TF32 precision for faster computation",
                "Optimize memory allocation patterns",
            ]
        elif pytorch_info.get("cuda_available", False):
            device_priority.append("cuda")
            recommendations["device_strategy"]["primary"] = "cuda"
            recommendations["device_strategy"]["reason"] = "NVIDIA GPU acceleration available"
        else:
            device_priority.append("cpu")
            recommendations["device_strategy"]["primary"] = "cpu"
            recommendations["device_strategy"]["reason"] = "CPU-only computation"

        # Parallelization recommendations
        physical_cores = cpu_info["physical_cores"]
        logical_cores = cpu_info["logical_cores"]

        if physical_cores >= 8:
            worker_count = min(8, physical_cores)
            prefetch_factor = 4
        elif physical_cores >= 4:
            worker_count = min(4, physical_cores)
            prefetch_factor = 2
        else:
            worker_count = 1
            prefetch_factor = 2

        recommendations["parallelization"] = {
            "num_workers": worker_count,
            "prefetch_factor": prefetch_factor,
            "pin_memory": pytorch_info.get("cuda_available", False),
            "explanation": f"Optimized for {physical_cores} physical cores",
        }

        # Compute optimizations
        optimizations = []

        if platform_info["is_apple_silicon"]:
            optimizations.extend(
                [
                    {
                        "technique": "mps_optimization",
                        "description": "Enable Apple Silicon MPS acceleration",
                        "config": {"PYTORCH_ENABLE_MPS_FALLBACK": "1", "torch.backends.mps.allow_tf32": True},
                    },
                    {
                        "technique": "memory_format_optimization",
                        "description": "Use channels-last memory format for better performance",
                        "impact": "medium",
                    },
                ]
            )

        if pytorch_info.get("cuda_available", False):
            optimizations.append(
                {
                    "technique": "cuda_optimization",
                    "description": "Enable CUDA optimizations",
                    "config": {"torch.backends.cudnn.benchmark": True, "torch.backends.cudnn.enabled": True},
                }
            )

        optimizations.append({"technique": "jit_compilation", "description": "Use TorchScript JIT compilation for inference", "impact": "high"})

        recommendations["compute_optimizations"] = optimizations

        return recommendations

    def analyze_model_optimization(self) -> dict[str, Any]:
        """Analyze model-specific optimization opportunities."""
        memory_gb = self.system_info["memory"]["total_gb"]
        is_apple_silicon = self.system_info["platform"]["is_apple_silicon"]

        recommendations = {"model_selection": {}, "optimization_techniques": [], "inference_optimizations": []}

        # Model selection based on system capabilities
        if memory_gb >= 16 and is_apple_silicon:
            recommendations["model_selection"] = {
                "primary_model": "vision_transformer",
                "reason": "High-performance system can handle ViT efficiently",
                "fallback_models": ["resnet50", "mobilenet"],
            }
        elif memory_gb >= 8:
            recommendations["model_selection"] = {
                "primary_model": "resnet50",
                "reason": "Balanced performance for medium-spec systems",
                "fallback_models": ["mobilenet"],
            }
        else:
            recommendations["model_selection"] = {
                "primary_model": "mobilenet",
                "reason": "Lightweight model for resource-constrained systems",
                "fallback_models": [],
            }

        # Optimization techniques
        techniques = [
            {"name": "model_quantization", "description": "Reduce model precision to int8", "memory_saving": "~75%", "performance_impact": "minimal"},
            {
                "name": "dynamic_quantization",
                "description": "Quantize weights dynamically during inference",
                "memory_saving": "~50%",
                "performance_impact": "minimal",
            },
        ]

        if is_apple_silicon:
            techniques.append(
                {
                    "name": "ane_optimization",
                    "description": "Optimize for Apple Neural Engine",
                    "memory_saving": "variable",
                    "performance_impact": "significant_improvement",
                }
            )

        recommendations["optimization_techniques"] = techniques

        # Inference optimizations
        inference_opts = [
            {"technique": "batch_inference", "description": "Process multiple images in single batch", "speedup": "2-4x"},
            {"technique": "model_warming", "description": "Pre-warm model with dummy inputs", "benefit": "consistent_inference_times"},
            {"technique": "async_preprocessing", "description": "Preprocess images asynchronously", "benefit": "reduced_latency"},
        ]

        recommendations["inference_optimizations"] = inference_opts

        return recommendations

    def generate_config_recommendations(self) -> dict[str, Any]:
        """Generate specific configuration recommendations."""
        memory_opts = self.analyze_memory_optimization()
        compute_opts = self.analyze_compute_optimization()
        model_opts = self.analyze_model_optimization()

        config = {
            "training_config": {
                "batch_size": memory_opts["batch_size_recommendations"]["training"],
                "num_workers": compute_opts["parallelization"]["num_workers"],
                "pin_memory": compute_opts["parallelization"]["pin_memory"],
                "prefetch_factor": compute_opts["parallelization"]["prefetch_factor"],
                "device": compute_opts["device_strategy"]["primary"],
                "mixed_precision": memory_opts["memory_optimizations"],
            },
            "inference_config": {
                "batch_size": memory_opts["batch_size_recommendations"]["inference"],
                "device": compute_opts["device_strategy"]["primary"],
                "model_selection": model_opts["model_selection"]["primary_model"],
                "optimizations": [opt["technique"] for opt in model_opts["inference_optimizations"]],
            },
            "environment_variables": {},
            "system_optimizations": [],
        }

        # Environment variables
        if self.system_info["platform"]["is_apple_silicon"]:
            config["environment_variables"]["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
            config["environment_variables"]["TORCH_DEVICE"] = "mps"

        # System-specific optimizations
        if self.system_info["memory"]["total_gb"] < 8:
            config["system_optimizations"].append("Enable swap if needed")

        if self.system_info["cpu"]["physical_cores"] >= 8:
            config["system_optimizations"].append("Consider process affinity for training")

        return config

    def benchmark_system(self) -> dict[str, Any]:
        """Run basic system benchmarks."""
        benchmarks = {"cpu_benchmark": {}, "memory_benchmark": {}, "io_benchmark": {}, "pytorch_benchmark": {}}

        try:
            # CPU benchmark - simple computation
            start_time = time.time()
            result = sum(i**2 for i in range(100000))
            cpu_time = time.time() - start_time

            benchmarks["cpu_benchmark"] = {
                "computation_time_ms": round(cpu_time * 1000, 2),
                "operations_per_second": round(100000 / cpu_time, 0),
                "performance_rating": "high" if cpu_time < 0.01 else "medium" if cpu_time < 0.05 else "low",
            }

            # Memory benchmark
            start_time = time.time()
            large_list = list(range(1000000))
            memory_time = time.time() - start_time
            del large_list

            benchmarks["memory_benchmark"] = {
                "allocation_time_ms": round(memory_time * 1000, 2),
                "performance_rating": "high" if memory_time < 0.1 else "medium" if memory_time < 0.5 else "low",
            }

            # PyTorch benchmark if available
            try:
                import torch

                device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"

                # Create random tensor and measure operations
                start_time = time.time()
                x = torch.randn(1000, 1000, device=device)
                y = torch.matmul(x, x.T)
                torch_time = time.time() - start_time

                benchmarks["pytorch_benchmark"] = {
                    "device": device,
                    "matrix_multiply_time_ms": round(torch_time * 1000, 2),
                    "performance_rating": "high" if torch_time < 0.01 else "medium" if torch_time < 0.1 else "low",
                }

            except Exception as e:
                benchmarks["pytorch_benchmark"] = {"error": str(e)}

        except Exception as e:
            logger.error(f"Benchmark failed: {e!s}")
            benchmarks["error"] = str(e)

        return benchmarks

    def run_complete_analysis(self) -> dict[str, Any]:
        """Run complete performance analysis and optimization."""
        analysis_start = time.time()

        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": self.system_info,
            "memory_analysis": self.analyze_memory_optimization(),
            "compute_analysis": self.analyze_compute_optimization(),
            "model_analysis": self.analyze_model_optimization(),
            "config_recommendations": self.generate_config_recommendations(),
            "benchmarks": self.benchmark_system(),
            "analysis_time_seconds": 0,
            "summary": {},
        }

        results["analysis_time_seconds"] = round(time.time() - analysis_start, 2)

        # Generate summary
        memory_gb = self.system_info["memory"]["total_gb"]
        device = results["compute_analysis"]["device_strategy"]["primary"]
        is_apple_silicon = self.system_info["platform"]["is_apple_silicon"]

        summary = {"system_classification": "", "primary_recommendations": [], "expected_performance": "", "optimization_potential": ""}

        # System classification
        if memory_gb >= 32 and (device in ["mps", "cuda"]):
            summary["system_classification"] = "high_performance"
            summary["expected_performance"] = "excellent"
        elif memory_gb >= 16 and (device in ["mps", "cuda"]):
            summary["system_classification"] = "high_standard"
            summary["expected_performance"] = "very_good"
        elif memory_gb >= 8:
            summary["system_classification"] = "standard"
            summary["expected_performance"] = "good"
        else:
            summary["system_classification"] = "resource_constrained"
            summary["expected_performance"] = "limited"

        # Primary recommendations
        if is_apple_silicon:
            summary["primary_recommendations"].append("Enable MPS acceleration")

        if memory_gb < 8:
            summary["primary_recommendations"].append("Use lightweight models")
            summary["primary_recommendations"].append("Enable mixed precision")

        if results["benchmarks"]["cpu_benchmark"].get("performance_rating") == "low":
            summary["primary_recommendations"].append("Consider CPU optimization")

        summary["optimization_potential"] = (
            "high" if len(summary["primary_recommendations"]) > 2 else "medium" if len(summary["primary_recommendations"]) > 0 else "low"
        )

        results["summary"] = summary

        return results


def main():
    """Main function with CLI support and JSON output."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze and optimize PlantGuard performance")
    parser.add_argument("--json-output", action="store_true", help="Output JSON results")
    parser.add_argument("--save-config", help="Save configuration to file")
    parser.add_argument("--benchmark", action="store_true", help="Run system benchmarks")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Initialize optimizer
    optimizer = PerformanceOptimizer()

    # Run analysis
    logger.info("Running performance analysis...")
    results = optimizer.run_complete_analysis()

    # Save configuration if requested
    if args.save_config:
        config_path = Path(args.save_config)
        with open(config_path, "w") as f:
            json.dump(results["config_recommendations"], f, indent=2)
        logger.info(f"Configuration saved to {config_path}")

    # Output results
    if args.json_output:
        print(json.dumps(results, indent=2))
    else:
        # Human-readable output
        summary = results["summary"]
        system_info = results["system_info"]

        print("[LAUNCH] PlantGuard Performance Analysis Results")
        print("=" * 50)

        print(f"\n[COMPUTER] System Classification: {summary['system_classification'].replace('_', ' ').title()}")
        print(f"[SUMMARY] Expected Performance: {summary['expected_performance'].replace('_', ' ').title()}")
        print(f"[ACTIONS] Optimization Potential: {summary['optimization_potential'].title()}")

        print("\n[TOOL] System Specs:")
        print(f"  Memory: {system_info['memory']['total_gb']:.1f} GB")
        print(f"  CPU Cores: {system_info['cpu']['physical_cores']} physical / {system_info['cpu']['logical_cores']} logical")
        print(f"  Platform: {system_info['platform']['system']} {system_info['platform']['machine']}")

        if system_info.get("pytorch", {}).get("installed", True):
            pytorch_info = system_info["pytorch"]
            device = results["compute_analysis"]["device_strategy"]["primary"]
            print(f"  PyTorch Device: {device.upper()}")

            if pytorch_info.get("mps_available"):
                print("  [APPLE] Apple Silicon MPS: Available")
            if pytorch_info.get("cuda_available"):
                print(f"  [INTERACTIVE] CUDA GPUs: {pytorch_info['device_count']}")

        print("\n[ACTIONS] Primary Recommendations:")
        for rec in summary["primary_recommendations"]:
            print(f"  • {rec}")

        batch_size = results["config_recommendations"]["training_config"]["batch_size"]
        num_workers = results["config_recommendations"]["training_config"]["num_workers"]

        print("\n[PROGRESS] Optimal Configuration:")
        print(f"  Training Batch Size: {batch_size}")
        print(f"  Data Loader Workers: {num_workers}")
        print(f"  Recommended Model: {results['model_analysis']['model_selection']['primary_model']}")

        if args.benchmark:
            benchmarks = results["benchmarks"]
            print("\n[CHART] Performance Benchmarks:")

            cpu_bench = benchmarks.get("cpu_benchmark", {})
            if cpu_bench:
                print(f"  CPU Performance: {cpu_bench.get('performance_rating', 'unknown').title()}")
                print(f"  Operations/sec: {cpu_bench.get('operations_per_second', 0):,.0f}")

            torch_bench = benchmarks.get("pytorch_benchmark", {})
            if torch_bench and "error" not in torch_bench:
                print(f"  PyTorch ({torch_bench['device']}): {torch_bench.get('performance_rating', 'unknown').title()}")

        print(f"\n⏱️  Analysis completed in {results['analysis_time_seconds']} seconds")

        if args.save_config:
            print(f"[SAVE] Configuration saved to {args.save_config}")


if __name__ == "__main__":
    main()
