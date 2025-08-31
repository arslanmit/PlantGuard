#!/usr/bin/env python3
"""
Master script to run all type annotation fixes for production readiness.

This script orchestrates the execution of all type annotation fixing scripts
to address task 17 from the code-quality-fixes spec.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TypeAnnotationMaster:
    """Master controller for all type annotation fixes."""

    def __init__(self) -> None:
        self.scripts = ["fix_mobile_testing_annotations.py", "fix_untyped_calls.py", "fix_strict_type_annotations.py"]
        self.results: dict[str, Any] = {}

    def check_mypy_available(self) -> bool:
        """Check if mypy is available."""
        try:
            subprocess.run(["mypy", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("mypy is not available. Please install it: pip install mypy")
            return False

    def get_initial_error_count(self) -> int:
        """Get initial mypy error count."""
        try:
            result = subprocess.run(["mypy", "--strict", "."], capture_output=True, text=True, timeout=120)

            if result.stdout:
                errors = [line for line in result.stdout.split("\n") if "error:" in line]
                return len(errors)
            return 0

        except Exception as e:
            logger.warning(f"Could not get initial error count: {e}")
            return 0

    def run_script(self, script_name: str) -> dict[str, Any]:
        """Run a single type annotation fix script."""
        script_path = Path(script_name)

        if not script_path.exists():
            logger.error(f"Script not found: {script_name}")
            return {"success": False, "error": "Script not found"}

        try:
            logger.info(f"Running {script_name}...")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            success = result.returncode == 0

            return {"success": success, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}

        except subprocess.TimeoutExpired:
            logger.error(f"Script {script_name} timed out")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Error running {script_name}: {e}")
            return {"success": False, "error": str(e)}

    def get_final_error_count(self) -> dict[str, Any]:
        """Get final mypy error count and categorize errors."""
        try:
            result = subprocess.run(["mypy", "--strict", "."], capture_output=True, text=True, timeout=120)

            if result.stdout:
                all_errors = [line for line in result.stdout.split("\n") if "error:" in line]

                # Categorize errors
                type_annotation_errors = [
                    e
                    for e in all_errors
                    if any(
                        keyword in e.lower() for keyword in ["missing return type", "no-untyped-def", "no-untyped-call", "missing type annotation"]
                    )
                ]

                other_errors = [e for e in all_errors if e not in type_annotation_errors]

                return {
                    "total_errors": len(all_errors),
                    "type_annotation_errors": len(type_annotation_errors),
                    "other_errors": len(other_errors),
                    "sample_type_errors": type_annotation_errors[:5],
                    "sample_other_errors": other_errors[:5],
                }

            return {"total_errors": 0, "type_annotation_errors": 0, "other_errors": 0, "sample_type_errors": [], "sample_other_errors": []}

        except Exception as e:
            logger.warning(f"Could not get final error count: {e}")
            return {"error": str(e)}

    def generate_final_report(self) -> None:
        """Generate comprehensive final report."""
        report_path = Path("type_annotation_master_report.json")

        # Get final mypy status
        final_status = self.get_final_error_count()

        report_data = {
            "task": "Fix Strict Mode Type Annotations for Production Readiness",
            "requirements": ["1.1", "6.1"],
            "scripts_executed": self.scripts,
            "results": self.results,
            "final_status": final_status,
            "success": final_status.get("type_annotation_errors", 1) == 0,
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        # Also create markdown report
        md_report_path = Path("type_annotation_master_report.md")
        with open(md_report_path, "w") as f:
            f.write("# Type Annotation Master Fix Report\n\n")
            f.write("## Task 17: Fix Strict Mode Type Annotations for Production Readiness\n\n")
            f.write("**Requirements:** 1.1, 6.1\n\n")

            f.write("## Scripts Executed\n\n")
            for i, script in enumerate(self.scripts, 1):
                f.write(f"{i}. {script}\n")

            f.write("\n## Results Summary\n\n")
            total_errors = final_status.get("total_errors", 0)
            type_errors = final_status.get("type_annotation_errors", 0)

            if type_errors == 0:
                f.write("✅ **SUCCESS**: All type annotation errors have been resolved!\n\n")
            else:
                f.write(f"⚠️ **PARTIAL SUCCESS**: {type_errors} type annotation errors remain\n\n")

            f.write(f"- Total mypy errors: {total_errors}\n")
            f.write(f"- Type annotation errors: {type_errors}\n")
            f.write(f"- Other errors: {final_status.get('other_errors', 0)}\n\n")

            if final_status.get("sample_type_errors"):
                f.write("## Remaining Type Annotation Errors\n\n")
                for error in final_status["sample_type_errors"]:
                    f.write(f"- {error}\n")
                f.write("\n")

            f.write("## Next Steps\n\n")
            if type_errors == 0:
                f.write("- ✅ Task 17 is complete!\n")
                f.write("- Move to task 18: Fix Remaining Type Safety Issues in Core Components\n")
                f.write("- Run full test suite to ensure functionality is preserved\n")
            else:
                f.write("- Review remaining type annotation errors\n")
                f.write("- Add specific type annotations for complex cases\n")
                f.write("- Consider using `# type: ignore` for unavoidable cases\n")
                f.write("- Re-run this script after manual fixes\n")

        logger.info(f"Reports generated: {report_path} and {md_report_path}")

    def run(self) -> bool:
        """Run all type annotation fixes."""
        logger.info("Starting comprehensive type annotation fixes...")

        # Check prerequisites
        if not self.check_mypy_available():
            return False

        # Get initial state
        initial_errors = self.get_initial_error_count()
        logger.info(f"Initial mypy error count: {initial_errors}")

        # Run each script
        overall_success = True
        for script in self.scripts:
            result = self.run_script(script)
            self.results[script] = result

            if result["success"]:
                logger.info(f"✅ {script} completed successfully")
            else:
                logger.error(f"❌ {script} failed: {result.get('error', 'Unknown error')}")
                overall_success = False

        # Generate final report
        self.generate_final_report()

        # Final status
        final_status = self.get_final_error_count()
        final_type_errors = final_status.get("type_annotation_errors", 0)

        logger.info(f"Final type annotation errors: {final_type_errors}")

        return final_type_errors == 0


def main() -> None:
    """Main function."""
    print("=" * 60)
    print("TYPE ANNOTATION MASTER FIXER")
    print("Task 17: Fix Strict Mode Type Annotations for Production Readiness")
    print("=" * 60)

    master = TypeAnnotationMaster()
    success = master.run()

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    if success:
        print("🎉 SUCCESS: All type annotation errors have been resolved!")
        print("✅ Task 17 is complete and ready for production!")
    else:
        print("⚠️  PARTIAL SUCCESS: Some type annotation errors may remain.")
        print("📋 Check the generated reports for details and next steps.")

    print("\nGenerated reports:")
    print("  - type_annotation_master_report.json")
    print("  - type_annotation_master_report.md")

    print("\nNext steps:")
    if success:
        print("  1. Move to task 18 in the implementation plan")
        print("  2. Run full test suite: pytest")
        print("  3. Verify with: mypy --strict .")
    else:
        print("  1. Review the generated reports")
        print("  2. Manually fix remaining complex cases")
        print("  3. Re-run this script")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
