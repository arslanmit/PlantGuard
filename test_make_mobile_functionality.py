#!/usr/bin/env python3
"""
Make Mobile Command Functionality Test

This test validates that the 'make mobile' command works correctly and that
the mobile application can start properly.

Requirements covered: 7.2 (Validate that make mobile command works correctly)
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MakeMobileTester:
    """Test the make mobile command functionality."""

    def __init__(self):
        self.workspace_root = Path.cwd()

    def test_make_mobile_dry_run(self) -> dict[str, Any]:
        """Test make mobile command with dry run to see what it would do."""
        try:
            make_path = shutil.which("make")
            if not make_path:
                return {
                    "status": "failed",
                    "details": "Make command not found",
                    "stdout": "",
                    "stderr": "Make executable not found in PATH",
                }
            result = subprocess.run([make_path, "-n", "mobile"], capture_output=True, text=True, cwd=self.workspace_root, timeout=30)

            if result.returncode != 0:
                return {
                    "status": "failed",
                    "details": f"Make mobile dry run failed with return code {result.returncode}",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

            # Check if the output contains expected commands
            expected_patterns = ["mobile_spa_app.py", "streamlit run", "--server.port 8502"]

            missing_patterns = []
            for pattern in expected_patterns:
                if pattern not in result.stdout:
                    missing_patterns.append(pattern)

            if missing_patterns:
                return {
                    "status": "warning",
                    "details": f"Make mobile dry run missing expected patterns: {missing_patterns}",
                    "stdout": result.stdout,
                    "missing_patterns": missing_patterns,
                }

            return {"status": "passed", "details": "Make mobile dry run successful", "stdout": result.stdout}

        except subprocess.TimeoutExpired:
            return {"status": "failed", "details": "Make mobile dry run timed out"}
        except Exception as e:
            return {"status": "failed", "details": f"Make mobile dry run test failed: {e!s}"}

    def test_make_mobile_validation(self) -> dict[str, Any]:
        """Test the validation steps in make mobile command."""
        try:
            # Test individual validation commands that make mobile runs
            # Get secure executable paths
            test_path = shutil.which("test")
            python_path = shutil.which("python") or sys.executable

            validation_commands = []

            # Check if mobile_spa_app.py exists
            if test_path:
                validation_commands.append([test_path, "-f", "mobile_spa_app.py"])

            # Check if python can import mobile_spa_app
            validation_commands.extend(
                [
                    [python_path, "-c", "import mobile_spa_app; print('Mobile SPA imports successful')"],
                    # Check if streamlit is available
                    [python_path, "-c", "import streamlit; print('Streamlit available')"],
                    # Check if PyTorch is available
                    [python_path, "-c", "import torch; print(f'PyTorch available: {torch.__version__}')"],
                    # Check if PIL is available
                    [python_path, "-c", "import PIL; print('PIL available')"],
                ]
            )

            validation_results = {}

            for i, cmd in enumerate(validation_commands):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.workspace_root, timeout=30)

                    validation_results[f"validation_{i + 1}"] = {
                        "command": " ".join(cmd),
                        "returncode": result.returncode,
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr.strip(),
                        "success": result.returncode == 0,
                    }

                except subprocess.TimeoutExpired:
                    validation_results[f"validation_{i + 1}"] = {"command": " ".join(cmd), "error": "timeout", "success": False}
                except Exception as e:
                    validation_results[f"validation_{i + 1}"] = {"command": " ".join(cmd), "error": str(e), "success": False}

            # Check overall success
            failed_validations = [v for v in validation_results.values() if not v.get("success", False)]

            if failed_validations:
                return {
                    "status": "failed",
                    "details": f"Failed {len(failed_validations)} validation steps",
                    "validation_results": validation_results,
                    "failed_validations": failed_validations,
                }

            return {"status": "passed", "details": "All make mobile validation steps passed", "validation_results": validation_results}

        except Exception as e:
            return {"status": "failed", "details": f"Make mobile validation test failed: {e!s}"}

    def test_mobile_app_startup_quick(self) -> dict[str, Any]:
        """Test that mobile app can start quickly (5 second test)."""
        try:
            # Start the mobile app in background
            logger.info("Starting mobile app for quick startup test...")

            make_path = shutil.which("make")
            if not make_path:
                return {"status": "failed", "details": "Make command not found"}

            proc = subprocess.Popen(
                [make_path, "mobile"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.workspace_root,
                preexec_fn=os.setsid,  # Create new process group
            )

            # Wait for 5 seconds to see if it starts
            time.sleep(5)

            # Check if process is still running
            poll_result = proc.poll()

            if poll_result is None:
                # Process is still running, which is good
                logger.info("Mobile app started successfully, terminating test process...")

                # Terminate the process group
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    time.sleep(2)

                    # Force kill if still running
                    if proc.poll() is None:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)

                except ProcessLookupError:
                    pass  # Process already terminated

                return {
                    "status": "passed",
                    "details": "Mobile app started successfully and was running after 5 seconds",
                    "startup_time": "< 5 seconds",
                }
            else:
                # Process terminated, check why
                stdout, stderr = proc.communicate()

                return {
                    "status": "failed",
                    "details": f"Mobile app terminated with return code {poll_result}",
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "return_code": poll_result,
                }

        except Exception as e:
            # Clean up any remaining processes
            try:
                if "proc" in locals() and proc.poll() is None:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except:
                pass

            return {"status": "failed", "details": f"Mobile app startup test failed: {e!s}"}

    def test_port_availability(self) -> dict[str, Any]:
        """Test that the mobile app port (8502) is available."""
        try:
            # Test if port 8502 is available
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            result = sock.connect_ex(("localhost", 8502))
            sock.close()

            if result == 0:
                # Port is in use
                return {"status": "warning", "details": "Port 8502 is currently in use (mobile app may be running)", "port": 8502, "in_use": True}
            else:
                # Port is available
                return {"status": "passed", "details": "Port 8502 is available for mobile app", "port": 8502, "in_use": False}

        except Exception as e:
            return {"status": "failed", "details": f"Port availability test failed: {e!s}"}

    def run_all_tests(self) -> dict[str, Any]:
        """Run all make mobile functionality tests."""
        logger.info("Starting make mobile functionality tests...")

        tests = [
            ("Make Mobile Dry Run", self.test_make_mobile_dry_run),
            ("Make Mobile Validation", self.test_make_mobile_validation),
            ("Port Availability", self.test_port_availability),
            ("Mobile App Quick Startup", self.test_mobile_app_startup_quick),
        ]

        results = {}
        overall_status = "passed"

        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                result = test_func()
                results[test_name] = result

                if result["status"] == "failed":
                    overall_status = "failed"
                elif result["status"] == "warning" and overall_status != "failed":
                    overall_status = "warning"

            except Exception as e:
                logger.error(f"Test {test_name} crashed: {e}")
                results[test_name] = {"status": "failed", "error": str(e), "details": f"Test execution failed with exception: {e}"}
                overall_status = "failed"

        # Generate summary
        results["summary"] = {
            "overall_status": overall_status,
            "total_tests": len(tests),
            "passed": len([r for r in results.values() if isinstance(r, dict) and r.get("status") == "passed"]),
            "failed": len([r for r in results.values() if isinstance(r, dict) and r.get("status") == "failed"]),
            "warnings": len([r for r in results.values() if isinstance(r, dict) and r.get("status") == "warning"]),
        }

        return results

    def save_results(self, results: dict[str, Any], filename: str = "make_mobile_test_results.json"):
        """Save test results."""
        try:
            results_path = self.workspace_root / filename
            with open(results_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Test results saved to {results_path}")
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

    def print_summary(self, results: dict[str, Any]):
        """Print formatted summary of test results."""
        print("\n" + "=" * 80)
        print("MAKE MOBILE FUNCTIONALITY TEST RESULTS")
        print("=" * 80)

        summary = results.get("summary", {})
        overall_status = summary.get("overall_status", "unknown")

        # Status indicator
        status_symbols = {"passed": "✅", "failed": "❌", "warning": "⚠️"}

        print(f"\nOverall Status: {status_symbols.get(overall_status, '❓')} {overall_status.upper()}")
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed', 0)}")
        print(f"Failed: {summary.get('failed', 0)}")
        print(f"Warnings: {summary.get('warnings', 0)}")

        print("\nDetailed Results:")
        print("-" * 40)

        for test_name, result in results.items():
            if test_name == "summary":
                continue

            if isinstance(result, dict):
                status = result.get("status", "unknown")
                symbol = status_symbols.get(status, "❓")
                details = result.get("details", "No details")

                print(f"{symbol} {test_name}: {status}")
                print(f"   {details}")

                # Show additional info for failed tests
                if status == "failed" and "error" in result:
                    print(f"   Error: {result['error']}")
                print()

        print("=" * 80)


def main():
    """Main function to run make mobile functionality tests."""
    tester = MakeMobileTester()

    print("Starting Make Mobile Functionality Tests...")
    print("This will validate that the 'make mobile' command works correctly.")
    print()

    # Run all tests
    results = tester.run_all_tests()

    # Save results
    tester.save_results(results)

    # Print summary
    tester.print_summary(results)

    # Exit with appropriate code
    overall_status = results.get("summary", {}).get("overall_status", "failed")
    if overall_status == "passed":
        sys.exit(0)
    elif overall_status == "warning":
        sys.exit(1)  # Warnings but no failures
    else:
        sys.exit(2)  # Failures detected


if __name__ == "__main__":
    main()
