#!/usr/bin/env python3
"""
Validate Backward Compatibility Implementation

This script validates that all backward compatibility and user guidance features
are properly implemented for the mobile-only refactoring.
"""

import subprocess
import sys
from pathlib import Path


class BackwardCompatibilityValidator:
    """Validates backward compatibility implementation."""

    def __init__(self):
        self.deprecated_commands = [
            "run",
            "r",
            "spa",
            "spa-dev",
            "spa-prod",
            "spa-test",
            "spa-performance",
            "spa-config",
            "spa-optimize",
            "spa-docs",
            "validate-spa",
            "app",
            "desktop",
            "gui",
            "run-desktop",
            "run-legacy",
            "start-spa",
        ]

        self.mobile_commands = [
            "mobile",
            "m",
            "mobile-dev",
            "mobile-prod",
            "mobile-test",
            "mobile-performance",
            "mobile-config",
            "mobile-optimize",
            "mobile-docs",
            "validate-mobile",
        ]

        self.required_files = [
            "MOBILE_MIGRATION_GUIDE.md",
            "MOBILE_FEATURE_PARITY.md",
            "MIGRATION_INSTRUCTIONS.md",
            "scripts/migration_helper.py",
            "scripts/command_aliases.sh",
        ]

        self.results = []

    def validate_makefile_redirects(self) -> dict[str, bool]:
        """Validate that deprecated commands exist in Makefile with redirects."""
        print("🔍 Validating Makefile redirects...")

        try:
            with open("Makefile") as f:
                makefile_content = f.read()
        except FileNotFoundError:
            return {"makefile_exists": False}

        results = {"makefile_exists": True}

        for cmd in self.deprecated_commands:
            # Check if command exists as a target
            target_pattern = f"{cmd}:"
            has_target = target_pattern in makefile_content

            # Check if it has guidance messages
            has_guidance = "PlantGuard is now mobile-only" in makefile_content

            results[f"{cmd}_target"] = has_target
            results[f"{cmd}_guidance"] = has_guidance

            if has_target:
                print(f"  ✅ {cmd}: Target exists with redirect")
            else:
                print(f"  ❌ {cmd}: Target missing")

        return results

    def validate_mobile_commands(self) -> dict[str, bool]:
        """Validate that mobile commands exist and work."""
        print("🔍 Validating mobile commands...")

        results = {}

        for cmd in self.mobile_commands:
            try:
                # Use --dry-run to test without actually executing
                make_path = shutil.which("make")
                if not make_path:
                    continue
                result = subprocess.run([make_path, cmd, "--dry-run"], capture_output=True, text=True, timeout=10)

                command_exists = result.returncode == 0
                results[f"{cmd}_exists"] = command_exists

                if command_exists:
                    print(f"  ✅ {cmd}: Command exists")
                else:
                    print(f"  ❌ {cmd}: Command missing or broken")

            except subprocess.TimeoutExpired:
                results[f"{cmd}_exists"] = False
                print(f"  ❌ {cmd}: Command timeout")
            except Exception as e:
                results[f"{cmd}_exists"] = False
                print(f"  ❌ {cmd}: Error - {e}")

        return results

    def validate_documentation_files(self) -> dict[str, bool]:
        """Validate that all required documentation files exist."""
        print("🔍 Validating documentation files...")

        results = {}

        for file_path in self.required_files:
            path = Path(file_path)
            exists = path.exists()
            results[f"{file_path}_exists"] = exists

            if exists:
                # Check file size to ensure it's not empty
                size = path.stat().st_size
                has_content = size > 100  # At least 100 bytes
                results[f"{file_path}_has_content"] = has_content

                if has_content:
                    print(f"  ✅ {file_path}: Exists with content ({size} bytes)")
                else:
                    print(f"  ⚠️  {file_path}: Exists but appears empty")
            else:
                print(f"  ❌ {file_path}: Missing")
                results[f"{file_path}_has_content"] = False

        return results

    def validate_migration_helper(self) -> dict[str, bool]:
        """Validate migration helper script functionality."""
        print("🔍 Validating migration helper script...")

        results = {}

        # Test command migration
        try:
            python_path = shutil.which("python") or sys.executable
            result = subprocess.run([python_path, "scripts/migration_helper.py", "command", "run"], capture_output=True, text=True, timeout=10)

            command_help_works = result.returncode == 0
            has_guidance = "Command Removed" in result.stdout

            results["migration_helper_command"] = command_help_works and has_guidance

            if command_help_works and has_guidance:
                print("  ✅ Migration helper command function works")
            else:
                print("  ❌ Migration helper command function broken")

        except Exception as e:
            results["migration_helper_command"] = False
            print(f"  ❌ Migration helper command test failed: {e}")

        # Test feature migration
        try:
            python_path = shutil.which("python") or sys.executable
            result = subprocess.run(
                [python_path, "scripts/migration_helper.py", "feature", "image_analysis"], capture_output=True, text=True, timeout=10
            )

            feature_help_works = result.returncode == 0
            has_feature_info = "Feature Status" in result.stdout

            results["migration_helper_feature"] = feature_help_works and has_feature_info

            if feature_help_works and has_feature_info:
                print("  ✅ Migration helper feature function works")
            else:
                print("  ❌ Migration helper feature function broken")

        except Exception as e:
            results["migration_helper_feature"] = False
            print(f"  ❌ Migration helper feature test failed: {e}")

        # Test summary generation
        try:
            python_path = shutil.which("python") or sys.executable
            result = subprocess.run([python_path, "scripts/migration_helper.py", "summary"], capture_output=True, text=True, timeout=10)

            summary_works = result.returncode == 0
            has_json = '"migration_type"' in result.stdout

            results["migration_helper_summary"] = summary_works and has_json

            if summary_works and has_json:
                print("  ✅ Migration helper summary function works")
            else:
                print("  ❌ Migration helper summary function broken")

        except Exception as e:
            results["migration_helper_summary"] = False
            print(f"  ❌ Migration helper summary test failed: {e}")

        return results

    def validate_readme_updates(self) -> dict[str, bool]:
        """Validate that README has been updated for mobile-only."""
        print("🔍 Validating README updates...")

        results = {}

        try:
            with open("README.md") as f:
                readme_content = f.read()

            # Check for mobile-only mentions
            has_mobile_only = "mobile-only" in readme_content.lower()
            has_migration_info = "migration" in readme_content.lower()
            has_mobile_commands = "make mobile" in readme_content
            has_feature_parity = "feature parity" in readme_content.lower()

            results["readme_mobile_only"] = has_mobile_only
            results["readme_migration_info"] = has_migration_info
            results["readme_mobile_commands"] = has_mobile_commands
            results["readme_feature_parity"] = has_feature_parity

            if has_mobile_only:
                print("  ✅ README mentions mobile-only approach")
            else:
                print("  ❌ README missing mobile-only information")

            if has_migration_info:
                print("  ✅ README includes migration information")
            else:
                print("  ❌ README missing migration information")

            if has_mobile_commands:
                print("  ✅ README shows mobile commands")
            else:
                print("  ❌ README missing mobile command examples")

        except FileNotFoundError:
            results = {"readme_mobile_only": False, "readme_migration_info": False, "readme_mobile_commands": False, "readme_feature_parity": False}
            print("  ❌ README.md not found")

        return results

    def run_comprehensive_validation(self) -> dict[str, dict]:
        """Run all validation tests."""
        print("🧪 Running Comprehensive Backward Compatibility Validation")
        print("=" * 60)
        print()

        validation_results = {
            "makefile_redirects": self.validate_makefile_redirects(),
            "mobile_commands": self.validate_mobile_commands(),
            "documentation_files": self.validate_documentation_files(),
            "migration_helper": self.validate_migration_helper(),
            "readme_updates": self.validate_readme_updates(),
        }

        print()
        print("📊 Validation Summary")
        print("=" * 30)

        total_tests = 0
        passed_tests = 0

        for category, results in validation_results.items():
            category_passed = sum(1 for v in results.values() if v is True)
            category_total = len(results)

            total_tests += category_total
            passed_tests += category_passed

            status = "✅" if category_passed == category_total else "⚠️" if category_passed > 0 else "❌"
            print(f"{status} {category}: {category_passed}/{category_total} tests passed")

        print()
        overall_status = "✅ PASSED" if passed_tests == total_tests else "⚠️ PARTIAL" if passed_tests > 0 else "❌ FAILED"
        print(f"Overall Status: {overall_status} ({passed_tests}/{total_tests} tests passed)")

        if passed_tests == total_tests:
            print("🎉 All backward compatibility features are working correctly!")
        elif passed_tests > total_tests * 0.8:
            print("⚠️ Most features working, some issues need attention")
        else:
            print("❌ Significant issues found, backward compatibility needs work")

        return validation_results

    def generate_validation_report(self, results: dict) -> None:
        """Generate a detailed validation report."""
        report_path = "backward_compatibility_validation_report.json"

        import json

        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"📄 Detailed validation report saved to: {report_path}")


def main():
    """Main validation function."""
    validator = BackwardCompatibilityValidator()
    results = validator.run_comprehensive_validation()
    validator.generate_validation_report(results)

    # Exit with appropriate code
    total_tests = sum(len(category_results) for category_results in results.values())
    passed_tests = sum(sum(1 for v in category_results.values() if v is True) for category_results in results.values())

    if passed_tests == total_tests:
        sys.exit(0)  # All tests passed
    elif passed_tests > total_tests * 0.8:
        sys.exit(1)  # Most tests passed, some issues
    else:
        sys.exit(2)  # Significant failures


if __name__ == "__main__":
    main()
