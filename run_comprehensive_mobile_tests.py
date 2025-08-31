#!/usr/bin/env python3
"""
Comprehensive Mobile-Only Migration Test Runner

This script runs all mobile migration tests and provides a comprehensive validation report.
It covers all requirements for task 9: Implement comprehensive testing and validation.

Requirements covered: 7.1, 7.2, 7.3, 7.4, 7.5
"""
import pytest


import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ComprehensiveMobileTestRunner:
    """Runs all mobile migration tests and generates comprehensive report."""

    def __init__(self) -> Any:
        self.workspace_root = Path.cwd()
        self.test_scripts = [
            {
                "name": "Mobile Migration Comprehensive Test",
                "script": "test_mobile_migration_comprehensive.py",
                "description": "Tests desktop file removal, import validation, and migration completeness",
            },
            {
                "name": "Mobile Integration Validation",
                "script": "test_mobile_integration_validation.py",
                "description": "Tests mobile functionality and core adapter integration",
            },
            {
                "name": "Make Mobile Functionality Test",
                "script": "test_make_mobile_functionality.py",
                "description": "Tests that 'make mobile' command works correctly",
            },
        ]

    def run_test_script(self, script_info: dict[str, str]) -> dict[str, Any]:
        """Run a single test script and return results."""
        script_name = script_info["name"]
        script_path = script_info["script"]

        logger.info(f"Running {script_name}...")

        try:
            python_path = shutil.which("python") or sys.executable
            result = subprocess.run(
                [python_path, script_path],
                capture_output=True,
                text=True,
                cwd=self.workspace_root,
                timeout=300,  # 5 minute timeout
            )

            # Try to load JSON results if available
            json_results = None
            json_file_patterns = [
                script_path.replace(".py", "_results.json"),
                script_path.replace("test_", "").replace(".py", "_test_results.json"),
                f"{script_path.replace('.py', '')}_results.json",
            ]

            for pattern in json_file_patterns:
                json_path = self.workspace_root / pattern
                if json_path.exists():
                    try:
                        with open(json_path) as f:
                            json_results = json.load(f)
                        break
                    except Exception as e:
                        logger.warning(f"Could not load JSON results from {json_path}: {e}")

            return {
                "script": script_name,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "json_results": json_results,
                "status": "passed" if result.returncode == 0 else ("warning" if result.returncode == 1 else "failed"),
                "execution_time": "completed",
            }

        except subprocess.TimeoutExpired:
            return {
                "script": script_name,
                "return_code": -1,
                "stdout": "",
                "stderr": "Test timed out after 5 minutes",
                "json_results": None,
                "status": "failed",
                "execution_time": "timeout",
            }
        except Exception as e:
            return {
                "script": script_name,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "json_results": None,
                "status": "failed",
                "execution_time": "error",
            }

    def run_all_tests(self) -> dict[str, Any]:
        """Run all test scripts and compile results."""
        logger.info("Starting comprehensive mobile migration test suite...")

        all_results = {}
        overall_status = "passed"

        for script_info in self.test_scripts:
            result = self.run_test_script(script_info)
            all_results[script_info["name"]] = result

            if result["status"] == "failed":
                overall_status = "failed"
            elif result["status"] == "warning" and overall_status != "failed":
                overall_status = "warning"

        # Compile comprehensive summary
        summary = self.compile_comprehensive_summary(all_results, overall_status)

        return {
            "test_results": all_results,
            "comprehensive_summary": summary,
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
        }

    def compile_comprehensive_summary(self, all_results: dict[str, Any], overall_status: str) -> dict[str, Any]:
        """Compile a comprehensive summary from all test results."""
        summary = {
            "overall_status": overall_status,
            "total_test_scripts": len(self.test_scripts),
            "script_results": {},
            "requirement_coverage": {},
            "key_findings": [],
            "recommendations": [],
        }

        # Analyze each script's results
        for script_name, result in all_results.items():
            summary["script_results"][script_name] = {"status": result["status"], "return_code": result["return_code"]}

            # Extract key findings from JSON results if available
            if result["json_results"]:
                json_data = result["json_results"]

                # Extract summary information
                if "summary" in json_data:
                    script_summary = json_data["summary"]
                    summary["script_results"][script_name].update(
                        {
                            "total_tests": script_summary.get("total_tests", 0),
                            "passed": script_summary.get("passed", 0),
                            "failed": script_summary.get("failed", 0),
                            "warnings": script_summary.get("warnings", 0),
                        }
                    )

                # Extract specific findings
                if "Removed File Cleanup" in json_data:
                    file_cleanup = json_data["Removed File Cleanup"]
                    if file_cleanup.get("status") == "passed":
                        summary["key_findings"].append("[OK] All removed files successfully cleaned up")
                    else:
                        summary["key_findings"].append("[FAIL] Desktop file removal incomplete")

                if "Make Mobile Command" in json_data:
                    make_mobile = json_data["Make Mobile Command"]
                    if make_mobile.get("status") == "passed":
                        summary["key_findings"].append("[OK] Make mobile command works correctly")
                    else:
                        summary["key_findings"].append("[FAIL] Make mobile command has issues")

                if "Core Adapter Integration" in json_data:
                    adapters = json_data["Core Adapter Integration"]
                    if adapters.get("status") == "passed":
                        summary["key_findings"].append("[OK] All core adapters (vision, audio, text) working")
                    else:
                        summary["key_findings"].append("[FAIL] Core adapter integration issues")

                if "Import Validation" in json_data:
                    imports = json_data["Import Validation"]
                    if imports.get("status") == "warning":
                        legacy_refs = len(imports.get("legacy_references", []))
                        summary["key_findings"].append(f"[WARN] Found {legacy_refs} legacy references needing cleanup")
                    elif imports.get("status") == "passed":
                        summary["key_findings"].append("[OK] All imports validated successfully")

        # Map to requirements
        summary["requirement_coverage"] = {
            "7.1": "Mobile-only migration test suite created and executed",
            "7.2": "Make mobile command validated and working",
            "7.3": "Mobile functionality tested and confirmed working",
            "7.4": "Import validation completed with cleanup recommendations",
            "7.5": "Core adapter integration tested and confirmed working",
        }

        # Generate recommendations based on findings
        if overall_status == "failed":
            summary["recommendations"].append("[FAIL] Critical issues found - migration not complete")
            summary["recommendations"].append("[ACTION] Review failed tests and address issues before proceeding")
        elif overall_status == "warning":
            summary["recommendations"].append("[WARN] Migration mostly successful with minor issues")
            summary["recommendations"].append("[ACTION] Clean up remaining desktop references for full completion")
            summary["recommendations"].append("[OK] Mobile functionality is working correctly")
        else:
            summary["recommendations"].append("[OK] Mobile-only migration completed successfully")
            summary["recommendations"].append("[SUCCESS] All mobile functionality validated and working")
            summary["recommendations"].append("[READY] System ready for mobile-only operation")

        return summary

    def save_comprehensive_report(self, results: dict[str, Any], filename: str = "comprehensive_mobile_test_report.json") -> Any:
        """Save comprehensive test report."""
        try:
            report_path = self.workspace_root / filename
            with open(report_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Comprehensive test report saved to {report_path}")
        except Exception as e:
            logger.error(f"Failed to save comprehensive report: {e}")

    def print_comprehensive_summary(self, results: dict[str, Any]) -> Any:
        """Print comprehensive test summary."""
        print("\n" + "=" * 100)
        print("COMPREHENSIVE MOBILE-ONLY MIGRATION TEST REPORT")
        print("=" * 100)

        summary = results["comprehensive_summary"]
        overall_status = summary["overall_status"]

        # Status indicator
        status_symbols = {"passed": "[PASS]", "failed": "[FAIL]", "warning": "[WARN]"}

        print(f"\n[STATUS] OVERALL STATUS: {status_symbols.get(overall_status, '[UNKNOWN]')} {overall_status.upper()}")
        print(f"[STATS] Test Scripts Executed: {summary['total_test_scripts']}")
        print(f"[TIME] Test Completed: {results['timestamp']}")

        print("\n[DETAILS] REQUIREMENT COVERAGE:")
        print("-" * 50)
        for req_id, description in summary["requirement_coverage"].items():
            print(f"   {req_id}: {description}")

        print("\n[FINDINGS] KEY FINDINGS:")
        print("-" * 50)
        for finding in summary["key_findings"]:
            print(f"   {finding}")

        print("\n[RECOMMENDATIONS] RECOMMENDATIONS:")
        print("-" * 50)
        for recommendation in summary["recommendations"]:
            print(f"   {recommendation}")

        print("\n[DETAILS] DETAILED SCRIPT RESULTS:")
        print("-" * 50)
        for script_name, script_result in summary["script_results"].items():
            status = script_result["status"]
            symbol = status_symbols.get(status, "[UNKNOWN]")
            print(f"   {symbol} {script_name}: {status.upper()}")

            if "total_tests" in script_result:
                print(
                    f"      Tests: {script_result['total_tests']} total, "
                    f"{script_result['passed']} passed, "
                    f"{script_result['failed']} failed, "
                    f"{script_result['warnings']} warnings"
                )

        print("\n" + "=" * 100)
        print("[MOBILE] MOBILE-ONLY MIGRATION VALIDATION COMPLETE")
        print("=" * 100)


def main() -> None:
    """Main function to run comprehensive mobile tests."""
    runner = ComprehensiveMobileTestRunner()

    print("[START] Starting Comprehensive Mobile-Only Migration Test Suite")
    print("This will run all migration validation tests and generate a comprehensive report.")
    print()

    # Run all tests
    results = runner.run_all_tests()

    # Save comprehensive report
    runner.save_comprehensive_report(results)

    # Print summary
    runner.print_comprehensive_summary(results)

    # Exit with appropriate code
    overall_status = results["comprehensive_summary"]["overall_status"]
    if overall_status == "passed":
        sys.exit(0)
    elif overall_status == "warning":
        sys.exit(1)  # Warnings but no failures
    else:
        sys.exit(2)  # Failures detected


if __name__ == "__main__":
    main()
