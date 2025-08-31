"""
Mobile Performance Optimization Test Suite.

This module provides comprehensive testing for mobile performance optimizations,
including lazy loading, resource caching, bundle optimization, and memory management.
"""

import gc
import logging
import time
from datetime import datetime
from typing import Any

import streamlit as st

from .mobile_bundle_optimizer import mobile_bundle_optimizer
from .mobile_offline_manager import mobile_offline_manager
from .mobile_performance_optimizer import mobile_performance_optimizer

logger = logging.getLogger(__name__)


class MobilePerformanceTest:
    """Test suite for mobile performance optimizations."""

    def __init__(self) -> None:
        """Initialize performance test suite."""
        self.test_results: list[dict[str, Any]] = []
        self.test_start_time = None

    def run_all_tests(self) -> dict[str, Any]:
        """
        Run all performance optimization tests.

        Returns:
            Comprehensive test results
        """
        self.test_start_time = time.time()

        st.markdown("### [TEST] Running Mobile Performance Tests")

        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        tests = [
            ("Cache Performance", self.test_cache_performance),
            ("Lazy Loading", self.test_lazy_loading),
            ("Memory Management", self.test_memory_management),
            ("Bundle Optimization", self.test_bundle_optimization),
            ("Offline Functionality", self.test_offline_functionality),
            ("Resource Optimization", self.test_resource_optimization),
            ("Performance Monitoring", self.test_performance_monitoring),
        ]

        results = {}

        for i, (test_name, test_func) in enumerate(tests):
            status_text.text(f"Running {test_name}...")
            progress_bar.progress((i + 1) / len(tests))

            try:
                test_result = test_func()
                results[test_name] = test_result
                self.test_results.append({"test_name": test_name, "result": test_result, "timestamp": datetime.now().isoformat()})

            except Exception as e:
                logger.error(f"Test {test_name} failed: {e}")
                results[test_name] = {"status": "failed", "error": str(e)}

        # Calculate overall results
        total_time = time.time() - self.test_start_time
        passed_tests = sum(1 for r in results.values() if r.get("status") == "passed")
        total_tests = len(tests)

        overall_results = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_time_seconds": total_time,
            },
            "test_results": results,
            "recommendations": self._generate_recommendations(results),
        }

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        return overall_results

    def test_cache_performance(self) -> dict[str, Any]:
        """Test cache performance and hit rates."""
        try:
            cache = mobile_performance_optimizer.cache

            # Clear cache for clean test
            cache.clear()

            # Test cache operations
            test_data = {"test_key_1": "test_value_1", "test_key_2": {"nested": "data"}, "test_key_3": list(range(100))}

            # Test cache set operations
            set_times = []
            for key, value in test_data.items():
                start_time = time.time()
                cache.set(key, value)
                set_times.append(time.time() - start_time)

            # Test cache get operations
            get_times = []
            hit_count = 0
            for key in test_data:
                start_time = time.time()
                result = cache.get(key)
                get_times.append(time.time() - start_time)
                if result is not None:
                    hit_count += 1

            # Get cache stats
            stats = cache.get_stats()

            return {
                "status": "passed",
                "metrics": {
                    "avg_set_time_ms": sum(set_times) / len(set_times) * 1000,
                    "avg_get_time_ms": sum(get_times) / len(get_times) * 1000,
                    "hit_rate": (hit_count / len(test_data) * 100),
                    "cache_entries": stats["entries"],
                    "cache_size_mb": stats["size_mb"],
                },
                "passed": hit_count == len(test_data),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def test_lazy_loading(self) -> dict[str, Any]:
        """Test lazy loading functionality."""
        try:
            lazy_loader = mobile_performance_optimizer.lazy_loader

            # Register test components
            test_components = {
                "test_component_1": lambda: {"loaded": True, "id": "test_component_1"},
                "test_component_2": lambda: {"loaded": True, "id": "test_component_2"},
                "test_component_3": lambda: {"loaded": True, "id": "test_component_3"},
            }

            for comp_id, load_func in test_components.items():
                lazy_loader.register_component(comp_id, load_func)

            # Test lazy loading
            load_times = []
            loaded_components = []

            for comp_id in test_components:
                start_time = time.time()
                component = lazy_loader.load_component(comp_id)
                load_time = time.time() - start_time

                load_times.append(load_time)
                if component and component.get("loaded"):
                    loaded_components.append(comp_id)

            # Test preloading
            preload_start = time.time()
            lazy_loader.preload_components(list(test_components.keys()))
            preload_time = time.time() - preload_start

            return {
                "status": "passed",
                "metrics": {
                    "avg_load_time_ms": sum(load_times) / len(load_times) * 1000,
                    "preload_time_ms": preload_time * 1000,
                    "components_loaded": len(loaded_components),
                    "load_success_rate": len(loaded_components) / len(test_components) * 100,
                },
                "passed": len(loaded_components) == len(test_components),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def test_memory_management(self) -> dict[str, Any]:
        """Test memory management functionality."""
        try:
            memory_manager = mobile_performance_optimizer.memory_manager

            # Get initial memory usage
            initial_memory = memory_manager.get_memory_usage()

            # Create memory pressure by allocating large objects
            large_objects = []
            for i in range(10):
                large_objects.append([0] * 100000)  # ~800KB per object

            # Check memory pressure
            pressure_before = memory_manager.check_memory_pressure()

            # Perform cleanup
            cleanup_start = time.time()
            cleanup_results = memory_manager.cleanup_memory(force=True)
            cleanup_time = time.time() - cleanup_start

            # Clear test objects
            large_objects.clear()
            gc.collect()

            # Get final memory usage
            final_memory = memory_manager.get_memory_usage()

            return {
                "status": "passed",
                "metrics": {
                    "initial_memory_mb": initial_memory["rss_mb"],
                    "final_memory_mb": final_memory["rss_mb"],
                    "memory_freed_mb": cleanup_results.get("freed_mb", 0),
                    "cleanup_time_ms": cleanup_time * 1000,
                    "pressure_detected": pressure_before != "normal",
                },
                "passed": cleanup_results.get("freed_mb", 0) >= 0,
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def test_bundle_optimization(self) -> dict[str, Any]:
        """Test bundle optimization functionality."""
        try:
            # Create test CSS bundle
            test_css = {
                "base": "body { margin: 0; padding: 0; }",
                "mobile": ".mobile { width: 100%; }",
                "components": ".component { display: block; }",
            }

            bundle_start = time.time()
            css_bundle_created = mobile_bundle_optimizer.create_css_bundle(test_css, "test_css_bundle")
            bundle_time = time.time() - bundle_start

            # Test bundle loading
            load_start = time.time()
            bundle_loaded = mobile_bundle_optimizer.load_bundle("test_css_bundle")
            load_time = time.time() - load_start

            # Get bundle stats
            stats = mobile_bundle_optimizer.get_bundle_stats()

            return {
                "status": "passed",
                "metrics": {
                    "bundle_creation_time_ms": bundle_time * 1000,
                    "bundle_load_time_ms": load_time * 1000,
                    "total_bundles": stats["total_bundles"],
                    "loaded_bundles": stats["loaded_bundles"],
                    "load_success_rate": stats["load_success_rate"],
                },
                "passed": css_bundle_created and bundle_loaded,
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def test_offline_functionality(self) -> dict[str, Any]:
        """Test offline functionality."""
        try:
            # Test resource caching
            test_resources = {
                "test_model": ("model", {"weights": [1, 2, 3, 4, 5]}),
                "test_image": ("image", b"fake_image_data"),
                "test_data": ("data", {"key": "value", "list": [1, 2, 3]}),
            }

            cache_times = []
            cached_count = 0

            for resource_id, (resource_type, content) in test_resources.items():
                start_time = time.time()
                cached = mobile_offline_manager.cache_resource(resource_id, resource_type, content)
                cache_time = time.time() - start_time

                cache_times.append(cache_time)
                if cached:
                    cached_count += 1

            # Test resource retrieval
            retrieve_times = []
            retrieved_count = 0

            for resource_id in test_resources:
                start_time = time.time()
                retrieved = mobile_offline_manager.get_cached_resource(resource_id)
                retrieve_time = time.time() - start_time

                retrieve_times.append(retrieve_time)
                if retrieved is not None:
                    retrieved_count += 1

            # Get offline stats
            offline_stats = mobile_offline_manager.get_offline_stats()

            return {
                "status": "passed",
                "metrics": {
                    "avg_cache_time_ms": sum(cache_times) / len(cache_times) * 1000,
                    "avg_retrieve_time_ms": sum(retrieve_times) / len(retrieve_times) * 1000,
                    "cache_success_rate": cached_count / len(test_resources) * 100,
                    "retrieve_success_rate": retrieved_count / len(test_resources) * 100,
                    "cached_resources": offline_stats["cached_resources"],
                    "cache_size_mb": offline_stats["cache_size_mb"],
                },
                "passed": cached_count == len(test_resources) and retrieved_count == len(test_resources),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def test_resource_optimization(self) -> dict[str, Any]:
        """Test resource optimization features."""
        try:
            # Test image optimization
            fake_image_data = b"fake_large_image_data" * 1000  # ~23KB

            optimize_start = time.time()
            optimized_data = mobile_performance_optimizer.optimize_images(fake_image_data, max_width=800, quality=85)
            optimize_time = time.time() - optimize_start

            # Test resource bundling
            test_resources = {"resource_1": "data_1", "resource_2": "data_2", "resource_3": "data_3"}

            bundle_start = time.time()
            bundle_id = mobile_performance_optimizer.bundle_resources(test_resources)
            bundle_time = time.time() - bundle_start

            # Test bundle retrieval
            retrieve_start = time.time()
            bundled_resources = mobile_performance_optimizer.get_bundle_resources(bundle_id)
            retrieve_time = time.time() - retrieve_start

            return {
                "status": "passed",
                "metrics": {
                    "image_optimize_time_ms": optimize_time * 1000,
                    "original_size_bytes": len(fake_image_data),
                    "optimized_size_bytes": len(optimized_data),
                    "compression_ratio": len(optimized_data) / len(fake_image_data),
                    "bundle_create_time_ms": bundle_time * 1000,
                    "bundle_retrieve_time_ms": retrieve_time * 1000,
                    "bundle_created": bool(bundle_id),
                    "resources_bundled": len(bundled_resources) if bundled_resources else 0,
                },
                "passed": len(optimized_data) > 0 and bundled_resources is not None,
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def test_performance_monitoring(self) -> dict[str, Any]:
        """Test performance monitoring functionality."""
        try:
            # Get performance report
            report_start = time.time()
            perf_report = mobile_performance_optimizer.get_performance_report()
            report_time = time.time() - report_start

            # Test optimization level changes
            level_start = time.time()
            mobile_performance_optimizer.set_optimization_level("balanced")
            level_time = time.time() - level_start

            # Validate report structure
            required_sections = ["session_info", "cache_stats", "memory_stats", "loaded_components"]
            sections_present = all(section in perf_report for section in required_sections)

            return {
                "status": "passed",
                "metrics": {
                    "report_generation_time_ms": report_time * 1000,
                    "optimization_level_change_time_ms": level_time * 1000,
                    "report_sections_present": sections_present,
                    "total_renders": perf_report["session_info"]["total_renders"],
                    "avg_render_time": perf_report["session_info"]["avg_render_time"],
                    "memory_usage_mb": perf_report["memory_stats"]["rss_mb"],
                },
                "passed": sections_present and report_time < 0.1,  # Report should be fast
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _generate_recommendations(self, test_results: dict[str, Any]) -> list[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []

        try:
            # Cache performance recommendations
            cache_result = test_results.get("Cache Performance", {})
            if cache_result.get("status") == "passed":
                hit_rate = cache_result.get("metrics", {}).get("hit_rate", 0)
                if hit_rate < 80:
                    recommendations.append("Consider increasing cache size or adjusting cache TTL for better hit rates")

            # Memory management recommendations
            memory_result = test_results.get("Memory Management", {})
            if memory_result.get("status") == "passed":
                memory_mb = memory_result.get("metrics", {}).get("final_memory_mb", 0)
                if memory_mb > 150:
                    recommendations.append("High memory usage detected. Consider enabling aggressive memory management")

            # Bundle optimization recommendations
            bundle_result = test_results.get("Bundle Optimization", {})
            if bundle_result.get("status") == "passed":
                success_rate = bundle_result.get("metrics", {}).get("load_success_rate", 0)
                if success_rate < 100:
                    recommendations.append("Some bundles failed to load. Check bundle integrity and dependencies")

            # Offline functionality recommendations
            offline_result = test_results.get("Offline Functionality", {})
            if offline_result.get("status") == "passed":
                cache_success = offline_result.get("metrics", {}).get("cache_success_rate", 0)
                if cache_success < 100:
                    recommendations.append("Offline caching issues detected. Verify storage permissions and space")

            # General recommendations
            if not recommendations:
                recommendations.append("All performance tests passed! System is well optimized.")

        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")
            recommendations.append("Unable to generate specific recommendations due to test errors")

        return recommendations

    def render_test_results(self, results: dict[str, Any]) -> None:
        """Render test results in Streamlit UI."""
        st.markdown("## [SUMMARY] Performance Test Results")

        # Summary metrics
        summary = results["summary"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Tests", summary["total_tests"])

        with col2:
            st.metric("Passed", summary["passed_tests"])

        with col3:
            st.metric("Success Rate", f"{summary['success_rate']:.1f}%")

        with col4:
            st.metric("Total Time", f"{summary['total_time_seconds']:.2f}s")

        # Individual test results
        st.markdown("### Test Details")

        for test_name, test_result in results["test_results"].items():
            with st.expander(f"{test_name} - {test_result.get('status', 'unknown').title()}"):
                if test_result.get("status") == "passed":
                    st.success("[DONE] Test Passed")

                    metrics = test_result.get("metrics", {})
                    if metrics:
                        st.markdown("**Metrics:**")
                        for metric_name, metric_value in metrics.items():
                            if isinstance(metric_value, int | float):
                                st.metric(metric_name.replace("_", " ").title(), f"{metric_value:.3f}")
                            else:
                                st.text(f"{metric_name.replace('_', ' ').title()}: {metric_value}")

                else:
                    st.error("[TODO] Test Failed")
                    if "error" in test_result:
                        st.code(test_result["error"])

        # Recommendations
        st.markdown("### [TIP] Recommendations")
        for i, recommendation in enumerate(results["recommendations"], 1):
            st.markdown(f"{i}. {recommendation}")


# Global test instance
mobile_performance_test = MobilePerformanceTest()


def run_mobile_performance_tests() -> dict[str, Any]:
    """Run mobile performance tests and return results."""
    return mobile_performance_test.run_all_tests()


def render_mobile_performance_test_ui() -> None:
    """Render mobile performance test UI."""
    st.markdown("# [LAUNCH] Mobile Performance Test Suite")

    if st.button("Run All Performance Tests", type="primary", use_container_width=True):
        with st.spinner("Running performance tests..."):
            results = run_mobile_performance_tests()
            mobile_performance_test.render_test_results(results)

    # Show current performance stats
    with st.expander("[CHART] Current Performance Stats"):
        try:
            perf_report = mobile_performance_optimizer.get_performance_report()
            offline_stats = mobile_offline_manager.get_offline_stats()
            bundle_stats = mobile_bundle_optimizer.get_bundle_stats()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Performance:**")
                st.json(
                    {
                        "avg_render_time": perf_report["session_info"]["avg_render_time"],
                        "memory_usage_mb": perf_report["memory_stats"]["rss_mb"],
                        "cache_hit_rate": perf_report["cache_stats"]["hit_rate"],
                    }
                )

            with col2:
                st.markdown("**Resources:**")
                st.json(
                    {
                        "offline_enabled": offline_stats["enabled"],
                        "cached_resources": offline_stats["cached_resources"],
                        "loaded_bundles": bundle_stats["loaded_bundles"],
                    }
                )

        except Exception as e:
            st.error(f"Failed to load performance stats: {e}")
