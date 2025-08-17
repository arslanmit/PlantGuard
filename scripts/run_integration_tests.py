#!/usr/bin/env python3
"""Integration test runner for production training pipeline.

This script runs comprehensive integration tests for the production training
pipeline, including all component interactions and performance regression tests.
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """Runner for comprehensive integration tests."""

    def __init__(self, workspace_root: Path = None):
        """Initialize test runner."""
        self.workspace_root = workspace_root or Path.cwd()
        self.test_results: dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "total_duration": 0,
            "test_suites": {},
            "summary": {"total_tests": 0, "passed_tests": 0, "failed_tests": 0, "skipped_tests": 0, "success_rate": 0.0},
            "errors": [],
            "performance_metrics": {},
        }

    def run_test_suite(self, test_file: str, test_name: str, markers: list[str] = None, timeout: int = 300) -> dict[str, Any]:
        """Run a specific test suite."""
        logger.info(f"Running {test_name}...")

        # Build pytest command
        cmd = ["python", "-m", "pytest", test_file, "-v", "--tb=short"]

        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        # Add timeout
        cmd.extend(["--timeout", str(timeout)])

        # Add JSON report
        json_report_path = self.workspace_root / f"test_results_{test_name.lower().replace(' ', '_')}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_report_path}"])

        start_time = time.time()

        try:
            result = subprocess.run(cmd, check=False, cwd=self.workspace_root, capture_output=True, text=True, timeout=timeout)

            end_time = time.time()
            duration = end_time - start_time

            # Parse results
            test_result = {
                "name": test_name,
                "file": test_file,
                "duration": duration,
                "return_code": result.returncode,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
            }

            # Try to parse JSON report if available
            if json_report_path.exists():
                try:
                    with open(json_report_path) as f:
                        json_data = json.load(f)

                    test_result.update(
                        {
                            "tests_run": json_data.get("summary", {}).get("total", 0),
                            "tests_passed": json_data.get("summary", {}).get("passed", 0),
                            "tests_failed": json_data.get("summary", {}).get("failed", 0),
                            "tests_skipped": json_data.get("summary", {}).get("skipped", 0),
                        }
                    )

                    # Clean up JSON report
                    json_report_path.unlink(missing_ok=True)

                except Exception as e:
                    logger.warning(f"Could not parse JSON report for {test_name}: {e}")

            if test_result["success"]:
                logger.info(f"✅ {test_name} completed successfully in {duration:.2f}s")
            else:
                logger.error(f"❌ {test_name} failed in {duration:.2f}s")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr[:500]}...")

            return test_result

        except subprocess.TimeoutExpired:
            logger.error(f"❌ {test_name} timed out after {timeout}s")
            return {
                "name": test_name,
                "file": test_file,
                "duration": timeout,
                "return_code": -1,
                "success": False,
                "error": "Test timed out",
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 1,
                "tests_skipped": 0,
            }

        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            return {"name": test_name, "file": test_file, "duration": 0, "return_code": -1, "success": False, "error": str(e), "tests_run": 0, "tests_passed": 0, "tests_failed": 1, "tests_skipped": 0}

    def run_all_integration_tests(self, include_performance: bool = True, include_slow: bool = False) -> dict[str, Any]:
        """Run all integration tests."""
        logger.info("🚀 Starting comprehensive integration tests...")

        self.test_results["start_time"] = time.time()

        # Define test suites
        test_suites = [
            {"file": "tests/test_comprehensive_integration.py", "name": "Comprehensive Integration Tests", "timeout": 600, "markers": None},
            {"file": "tests/test_vision_adapter_registry_integration.py", "name": "VisionAdapter Registry Integration", "timeout": 300, "markers": None},
            {"file": "tests/test_model_switching_comprehensive.py", "name": "Model Switching Integration", "timeout": 400, "markers": None},
            {"file": "tests/test_end_to_end_deployment.py", "name": "End-to-End Deployment", "timeout": 500, "markers": None},
            {"file": "tests/test_production_training_integration.py", "name": "Production Training Integration", "timeout": 300, "markers": None},
        ]

        # Add performance tests if requested
        if include_performance:
            test_suites.append(
                {"file": "tests/test_performance_regression_comprehensive.py", "name": "Performance Regression Tests", "timeout": 800, "markers": ["performance"] if not include_slow else None}
            )

        # Add existing integration tests
        existing_integration_tests = ["scripts/test_production_workflow.py", "scripts/test_end_to_end_integration.py", "scripts/test_model_switching_integration.py"]

        for test_file in existing_integration_tests:
            if Path(test_file).exists():
                test_suites.append({"file": test_file, "name": f"Legacy {Path(test_file).stem.replace('_', ' ').title()}", "timeout": 300, "markers": None})

        # Run each test suite
        for suite in test_suites:
            if not Path(suite["file"]).exists():
                logger.warning(f"⚠️  Test file not found: {suite['file']}")
                continue

            result = self.run_test_suite(test_file=suite["file"], test_name=suite["name"], markers=suite.get("markers"), timeout=suite.get("timeout", 300))

            self.test_results["test_suites"][suite["name"]] = result

            # Update summary
            self.test_results["summary"]["total_tests"] += result.get("tests_run", 0)
            self.test_results["summary"]["passed_tests"] += result.get("tests_passed", 0)
            self.test_results["summary"]["failed_tests"] += result.get("tests_failed", 0)
            self.test_results["summary"]["skipped_tests"] += result.get("tests_skipped", 0)

            if not result["success"]:
                self.test_results["errors"].append({"test_suite": suite["name"], "error": result.get("error", "Test failed"), "stderr": result.get("stderr", "")})

        self.test_results["end_time"] = time.time()
        self.test_results["total_duration"] = self.test_results["end_time"] - self.test_results["start_time"]

        # Calculate success rate
        total_tests = self.test_results["summary"]["total_tests"]
        if total_tests > 0:
            self.test_results["summary"]["success_rate"] = self.test_results["summary"]["passed_tests"] / total_tests * 100

        return self.test_results

    def generate_report(self, output_file: Path = None) -> None:
        """Generate comprehensive test report."""
        if output_file is None:
            output_file = self.workspace_root / "integration_test_report.json"

        # Add system information
        import platform

        import psutil

        self.test_results["system_info"] = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "workspace_root": str(self.workspace_root),
        }

        # Save report
        with open(output_file, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)

        logger.info(f"📊 Test report saved to: {output_file}")

    def print_summary(self) -> None:
        """Print test summary to console."""
        print("\n" + "=" * 80)
        print("🏁 INTEGRATION TEST SUMMARY")
        print("=" * 80)

        summary = self.test_results["summary"]
        duration = self.test_results["total_duration"]

        print(f"Total Duration: {duration:.2f}s")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Skipped: {summary['skipped_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")

        print("\nTest Suite Results:")
        for suite_name, result in self.test_results["test_suites"].items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {suite_name}: {result['duration']:.2f}s")

        if self.test_results["errors"]:
            print("\nErrors:")
            for error in self.test_results["errors"]:
                print(f"  ❌ {error['test_suite']}: {error['error']}")

        overall_success = summary["failed_tests"] == 0
        if overall_success:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        else:
            print(f"\n💥 {summary['failed_tests']} TEST(S) FAILED")

        print("=" * 80)

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met for running tests."""
        logger.info("Checking test prerequisites...")

        # Check if pytest is available
        try:
            subprocess.run(["python", "-m", "pytest", "--version"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.error("❌ pytest not available. Install with: pip install pytest")
            return False

        # Check if required test files exist
        required_files = [
            "tests/test_comprehensive_integration.py",
            "tests/test_vision_adapter_registry_integration.py",
            "tests/test_model_switching_comprehensive.py",
            "tests/test_end_to_end_deployment.py",
        ]

        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            logger.error(f"❌ Missing test files: {missing_files}")
            return False

        # Check if source modules are importable
        try:
            import src.core.vision
            import src.features.model_switching.model_manager
            import src.training.model_registry
        except ImportError as e:
            logger.error(f"❌ Cannot import required modules: {e}")
            return False

        logger.info("✅ All prerequisites met")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run comprehensive integration tests for production training pipeline")
    parser.add_argument("--no-performance", action="store_true", help="Skip performance regression tests")
    parser.add_argument("--include-slow", action="store_true", help="Include slow tests (may take longer)")
    parser.add_argument("--output", type=Path, help="Output file for test report (default: integration_test_report.json)")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root directory (default: current directory)")
    parser.add_argument("--check-only", action="store_true", help="Only check prerequisites, don't run tests")

    args = parser.parse_args()

    # Initialize test runner
    runner = IntegrationTestRunner(workspace_root=args.workspace)

    # Check prerequisites
    if not runner.check_prerequisites():
        logger.error("❌ Prerequisites not met. Cannot run tests.")
        return 1

    if args.check_only:
        logger.info("✅ Prerequisites check passed")
        return 0

    try:
        # Run tests
        results = runner.run_all_integration_tests(include_performance=not args.no_performance, include_slow=args.include_slow)

        # Generate report
        runner.generate_report(args.output)

        # Print summary
        runner.print_summary()

        # Return appropriate exit code
        return 0 if results["summary"]["failed_tests"] == 0 else 1

    except KeyboardInterrupt:
        logger.info("❌ Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Test runner failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
