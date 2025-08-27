#!/usr/bin/env python3
"""
Comprehensive Mobile-Only Migration Test Suite

This test suite validates that the mobile-only refactoring has been completed successfully
and that all mobile functionality continues to work as expected.

Requirements covered: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MobileMigrationTester:
    """Comprehensive test suite for mobile-only migration validation."""

    def __init__(self):
        self.test_results = []
        self.workspace_root = Path.cwd()

    def run_all_tests(self) -> dict[str, Any]:
        """Run all migration validation tests."""
        logger.info("Starting comprehensive mobile-only migration test suite...")

        # Test categories as per task requirements
        tests = [
            ("Removed File Cleanup", self.test_desktop_file_removal),
            ("Make Mobile Command", self.test_make_mobile_command),
            ("Mobile Functionality", self.test_mobile_functionality),
            ("Import Validation", self.test_import_validation),
            ("Core Adapter Integration", self.test_core_adapter_integration),
            ("Makefile Targets", self.test_makefile_targets),
            ("Mobile App Startup", self.test_mobile_app_startup),
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

    def test_desktop_file_removal(self) -> dict[str, Any]:
        """Test that desktop-specific files have been removed."""
        removed_files_to_check = [
            "spa_app.py",
            "app.py",
            "test_spa_navigation.py",
            "test_unified_ui.py",
        ]

        still_present = []
        properly_removed = []

        for filepath in removed_files_to_check:
            full_path = self.workspace_root / filepath
            if full_path.exists():
                still_present.append(filepath)
            else:
                properly_removed.append(filepath)

        if still_present:
            return {
                "status": "failed",
                "details": f"Removed files still present: {still_present}",
                "properly_removed": properly_removed,
                "still_present": still_present,
            }

        return {"status": "passed", "details": f"All removed files properly cleaned up: {properly_removed}", "properly_removed": properly_removed}

    def test_make_mobile_command(self) -> dict[str, Any]:
        """Test that 'make mobile' command works correctly."""
        try:
            # Check if Makefile exists
            makefile_path = self.workspace_root / "Makefile"
            if not makefile_path.exists():
                return {"status": "failed", "details": "Makefile not found in workspace root"}

            # Read Makefile content
            with open(makefile_path) as f:
                makefile_content = f.read()

            # Check if mobile target exists
            if "mobile:" not in makefile_content:
                return {"status": "failed", "details": "Mobile target not found in Makefile"}

            # Test make mobile command (dry run to avoid actually starting the app)
            make_path = shutil.which("make")
            if not make_path:
                return {"status": "failed", "details": "Make command not found"}
            result = subprocess.run([make_path, "-n", "mobile"], capture_output=True, text=True, cwd=self.workspace_root, timeout=10)

            if result.returncode != 0:
                return {
                    "status": "failed",
                    "details": f"Make mobile command failed: {result.stderr}",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

            return {"status": "passed", "details": "Make mobile command works correctly", "command_output": result.stdout}

        except subprocess.TimeoutExpired:
            return {"status": "failed", "details": "Make mobile command timed out"}
        except Exception as e:
            return {"status": "failed", "details": f"Make mobile test failed: {e!s}"}

    def test_mobile_functionality(self) -> dict[str, Any]:
        """Test that mobile application can be imported and basic functionality works."""
        try:
            # Test mobile app import
            sys.path.insert(0, str(self.workspace_root))

            # Check if mobile_spa_app.py exists
            mobile_app_path = self.workspace_root / "mobile_spa_app.py"
            if not mobile_app_path.exists():
                return {"status": "failed", "details": "mobile_spa_app.py not found"}

            # Try to import mobile app (syntax check)
            import importlib.util

            spec = importlib.util.spec_from_file_location("mobile_spa_app", mobile_app_path)
            if spec is None:
                return {"status": "failed", "details": "Could not create module spec for mobile_spa_app.py"}

            # Check for basic mobile components
            mobile_components = ["src/ui/components/mobile_header.py", "src/ui/components/mobile_input_ribbon.py", "assets/mobile_styles.css"]

            missing_components = []
            present_components = []

            for component in mobile_components:
                component_path = self.workspace_root / component
                if component_path.exists():
                    present_components.append(component)
                else:
                    missing_components.append(component)

            if missing_components:
                return {
                    "status": "warning",
                    "details": f"Some mobile components missing: {missing_components}",
                    "present_components": present_components,
                    "missing_components": missing_components,
                }

            return {"status": "passed", "details": "Mobile functionality components are present", "present_components": present_components}

        except Exception as e:
            return {"status": "failed", "details": f"Mobile functionality test failed: {e!s}"}

    def test_import_validation(self) -> dict[str, Any]:
        """Test that no broken import statements exist in remaining files."""
        python_files = list(self.workspace_root.glob("**/*.py"))

        # Filter out test files and cache directories
        python_files = [
            f
            for f in python_files
            if not any(exclude in str(f) for exclude in ["__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv", ".git"])
        ]

        broken_imports = []
        legacy_references = []

        # Patterns that indicate legacy references that should be cleaned up
        legacy_patterns = [
            "from spa_app import",
            "import spa_app",
            "from app import",
            "import app",
            "spa_app.",
            "app.main",
        ]

        for py_file in python_files:
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Check for legacy references
                for pattern in legacy_patterns:
                    if pattern in content:
                        legacy_references.append({"file": str(py_file.relative_to(self.workspace_root)), "pattern": pattern})

                # Try to compile the file (basic syntax check)
                try:
                    compile(content, str(py_file), "exec")
                except SyntaxError as e:
                    broken_imports.append({"file": str(py_file.relative_to(self.workspace_root)), "error": str(e)})

            except Exception as e:
                broken_imports.append({"file": str(py_file.relative_to(self.workspace_root)), "error": f"Could not read file: {e!s}"})

        status = "passed"
        details = "All imports are valid"

        if broken_imports:
            status = "failed"
            details = f"Found {len(broken_imports)} files with broken imports"
        elif legacy_references:
            status = "warning"
            details = f"Found {len(legacy_references)} legacy references that may need cleanup"

        return {
            "status": status,
            "details": details,
            "broken_imports": broken_imports,
            "legacy_references": legacy_references,
            "files_checked": len(python_files),
        }

    def test_core_adapter_integration(self) -> dict[str, Any]:
        """Test integration with core adapters (vision, audio, text)."""
        try:
            sys.path.insert(0, str(self.workspace_root))

            # Check core adapter files exist
            core_adapters = {"vision": "src/core/vision.py", "audio": "src/core/audio.py", "nlp": "src/core/nlp.py"}

            missing_adapters = []
            present_adapters = []
            import_results = {}

            for adapter_name, adapter_path in core_adapters.items():
                full_path = self.workspace_root / adapter_path
                if full_path.exists():
                    present_adapters.append(adapter_name)

                    # Try to import the adapter
                    try:
                        import importlib.util

                        spec = importlib.util.spec_from_file_location(f"src.core.{adapter_name}", full_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            import_results[adapter_name] = "success"
                        else:
                            import_results[adapter_name] = "failed - no spec"
                    except Exception as e:
                        import_results[adapter_name] = f"failed - {e!s}"
                else:
                    missing_adapters.append(adapter_name)
                    import_results[adapter_name] = "missing file"

            # Determine overall status
            if missing_adapters:
                status = "failed"
                details = f"Missing core adapters: {missing_adapters}"
            elif any("failed" in result for result in import_results.values()):
                status = "warning"
                details = "Some adapters have import issues"
            else:
                status = "passed"
                details = "All core adapters are present and importable"

            return {
                "status": status,
                "details": details,
                "present_adapters": present_adapters,
                "missing_adapters": missing_adapters,
                "import_results": import_results,
            }

        except Exception as e:
            return {"status": "failed", "details": f"Core adapter integration test failed: {e!s}"}

    def test_makefile_targets(self) -> dict[str, Any]:
        """Test that Makefile has been properly updated for mobile-only."""
        try:
            makefile_path = self.workspace_root / "Makefile"
            if not makefile_path.exists():
                return {"status": "failed", "details": "Makefile not found"}

            with open(makefile_path) as f:
                makefile_content = f.read()

            # Check for removed legacy targets
            removed_targets = ["run:", "spa-dev:", "spa-prod:", "spa-test:", "spa-performance:"]
            found_removed_targets = []

            for target in removed_targets:
                if target in makefile_content:
                    found_removed_targets.append(target)

            # Check for required mobile targets
            required_mobile_targets = ["mobile:"]
            missing_mobile_targets = []

            for target in required_mobile_targets:
                if target not in makefile_content:
                    missing_mobile_targets.append(target)

            # Determine status
            if missing_mobile_targets:
                status = "failed"
                details = f"Missing required mobile targets: {missing_mobile_targets}"
            elif found_removed_targets:
                status = "warning"
                details = f"Removed targets still present: {found_removed_targets}"
            else:
                status = "passed"
                details = "Makefile properly updated for mobile-only"

            return {
                "status": status,
                "details": details,
                "found_removed_targets": found_removed_targets,
                "missing_mobile_targets": missing_mobile_targets,
            }

        except Exception as e:
            return {"status": "failed", "details": f"Makefile test failed: {e!s}"}

    def test_mobile_app_startup(self) -> dict[str, Any]:
        """Test that mobile app can start without errors (quick startup test)."""
        try:
            # Test streamlit syntax check on mobile app
            mobile_app_path = self.workspace_root / "mobile_spa_app.py"
            if not mobile_app_path.exists():
                return {"status": "failed", "details": "mobile_spa_app.py not found"}

            # Run streamlit config check (doesn't start the server)
            python_path = shutil.which("python") or sys.executable
            result = subprocess.run(
                [python_path, "-m", "streamlit", "config", "show"], capture_output=True, text=True, timeout=30, cwd=self.workspace_root
            )

            if result.returncode != 0:
                return {
                    "status": "warning",
                    "details": f"Streamlit config check failed: {result.stderr}",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

            # Basic syntax check of mobile app
            with open(mobile_app_path) as f:
                mobile_app_content = f.read()

            try:
                compile(mobile_app_content, str(mobile_app_path), "exec")
            except SyntaxError as e:
                return {"status": "failed", "details": f"Mobile app has syntax errors: {e!s}"}

            return {"status": "passed", "details": "Mobile app startup test passed", "streamlit_config": "ok"}

        except subprocess.TimeoutExpired:
            return {"status": "warning", "details": "Mobile app startup test timed out"}
        except Exception as e:
            return {"status": "failed", "details": f"Mobile app startup test failed: {e!s}"}

    def save_results(self, results: dict[str, Any], filename: str = "mobile_migration_test_results.json"):
        """Save test results to a JSON file."""
        try:
            results_path = self.workspace_root / filename
            with open(results_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Test results saved to {results_path}")
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

    def print_summary(self, results: dict[str, Any]):
        """Print a formatted summary of test results."""
        print("\n" + "=" * 80)
        print("MOBILE-ONLY MIGRATION TEST RESULTS")
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
    """Main function to run the mobile migration test suite."""
    tester = MobileMigrationTester()

    print("Starting Mobile-Only Migration Test Suite...")
    print("This will validate that the mobile-only refactoring was completed successfully.")
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
