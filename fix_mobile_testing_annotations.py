#!/usr/bin/env python3
"""
Targeted script to fix type annotations in mobile testing suites and validation scripts.

This script specifically addresses the mobile testing framework and validation scripts
that have the most "no-untyped-def" and "no-untyped-call" errors.
"""

import logging
import re
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MobileTestingAnnotationFixer:
    """Fixes type annotations specifically in mobile testing and validation files."""

    def __init__(self) -> None:
        self.mobile_test_files = [
            "mobile_testing_validation.py",
            "test_mobile_comprehensive.py",
            "test_mobile_integration.py",
            "test_mobile_layout.py",
            "test_mobile_optimization.py",
            "test_mobile_error_recovery.py",
            "test_mobile_history_settings.py",
            "test_mobile_state_management.py",
            "test_mobile_migration_comprehensive.py",
            "mobile_comprehensive_testing_suite.py",
            "mobile_testing_optimization_suite.py",
            "validate_mobile_integration.py",
            "validate_mobile_performance.py",
            "validate_spa_solution.py",
            "final_system_validation.py",
            "final_validation_test_suite.py",
        ]

        self.validation_scripts = [
            "validate_file_structure_optimization.py",
            "mobile_accessibility_validator.py",
            "mobile_performance_optimizer.py",
            "run_comprehensive_mobile_tests.py",
        ]

    def get_target_files(self) -> list[Path]:
        """Get all target mobile testing and validation files."""
        target_files = []

        # Check root directory and common locations
        search_paths = [Path(), Path("tests"), Path("scripts")]

        all_target_names = self.mobile_test_files + self.validation_scripts

        for search_path in search_paths:
            if search_path.exists():
                for file_name in all_target_names:
                    file_path = search_path / file_name
                    if file_path.exists():
                        target_files.append(file_path)

        return target_files

    def fix_test_function_annotations(self, content: str) -> str:
        """Fix test function annotations with proper pytest patterns."""
        lines = content.split("\n")
        modified_lines = []

        for line in lines:
            # Match test function definitions
            test_match = re.match(r"^(\s*)(def\s+(test_\w+)\s*\([^)]*\))\s*:\s*$", line)
            if test_match:
                indent, func_def, func_name = test_match.groups()

                # Skip if already has return annotation
                if "->" in func_def:
                    modified_lines.append(line)
                    continue

                # All test functions return None
                new_func_def = f"{func_def} -> None:"
                modified_lines.append(f"{indent}{new_func_def}")
                continue

            # Match fixture functions
            fixture_match = re.match(r"^(\s*)(def\s+(\w+)\s*\([^)]*\))\s*:\s*$", line)
            if fixture_match and "@pytest.fixture" in "".join(lines[max(0, lines.index(line) - 3) : lines.index(line)]):
                indent, func_def, func_name = fixture_match.groups()

                if "->" in func_def:
                    modified_lines.append(line)
                    continue

                # Fixtures typically return Any or Generator
                if "yield" in content[content.find(line) :]:
                    return_type = "Generator[Any, None, None]"
                else:
                    return_type = "Any"

                new_func_def = f"{func_def} -> {return_type}:"
                modified_lines.append(f"{indent}{new_func_def}")
                continue

            modified_lines.append(line)

        return "\n".join(modified_lines)

    def fix_validation_function_annotations(self, content: str) -> str:
        """Fix validation function annotations."""
        lines = content.split("\n")
        modified_lines = []

        validation_patterns = {
            "validate_": "bool",
            "check_": "bool",
            "verify_": "bool",
            "run_": "Any",
            "execute_": "Any",
            "generate_": "Any",
            "create_": "Any",
            "setup_": "None",
            "cleanup_": "None",
            "main": "None",
        }

        for line in lines:
            func_match = re.match(r"^(\s*)(def\s+(\w+)\s*\([^)]*\))\s*:\s*$", line)
            if func_match:
                indent, func_def, func_name = func_match.groups()

                if "->" in func_def:
                    modified_lines.append(line)
                    continue

                # Determine return type based on function name
                return_type = "Any"  # Default
                for pattern, ret_type in validation_patterns.items():
                    if func_name.startswith(pattern):
                        return_type = ret_type
                        break

                new_func_def = f"{func_def} -> {return_type}:"
                modified_lines.append(f"{indent}{new_func_def}")
                continue

            modified_lines.append(line)

        return "\n".join(modified_lines)

    def fix_class_method_annotations(self, content: str) -> str:
        """Fix class method annotations in mobile testing classes."""
        lines = content.split("\n")
        modified_lines = []

        method_patterns = {
            "__init__": "None",
            "setUp": "None",
            "tearDown": "None",
            "setup_method": "None",
            "teardown_method": "None",
            "test_": "None",
            "validate_": "bool",
            "check_": "bool",
            "get_": "Any",
            "set_": "None",
            "render_": "None",
            "display_": "None",
            "run_": "Any",
            "execute_": "Any",
        }

        for line in lines:
            method_match = re.match(r"^(\s+)(def\s+(\w+)\s*\([^)]*\))\s*:\s*$", line)
            if method_match:
                indent, method_def, method_name = method_match.groups()

                if "->" in method_def:
                    modified_lines.append(line)
                    continue

                # Determine return type
                return_type = "Any"  # Default
                for pattern, ret_type in method_patterns.items():
                    if method_name.startswith(pattern) or method_name == pattern:
                        return_type = ret_type
                        break

                new_method_def = f"{method_def} -> {return_type}:"
                modified_lines.append(f"{indent}{new_method_def}")
                continue

            modified_lines.append(line)

        return "\n".join(modified_lines)

    def add_comprehensive_imports(self, content: str) -> str:
        """Add comprehensive typing imports for mobile testing files."""
        lines = content.split("\n")

        # Check existing imports
        has_typing = any("from typing import" in line or "import typing" in line for line in lines)
        has_pytest = any("import pytest" in line or "from pytest" in line for line in lines)

        # Find insertion point
        insert_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                # Skip docstrings
                quote_type = '"""' if '"""' in line else "'''"
                if line.count(quote_type) == 1:  # Opening docstring
                    for j in range(i + 1, len(lines)):
                        if quote_type in lines[j]:
                            insert_index = j + 1
                            break
                else:  # Single line docstring
                    insert_index = i + 1
                break
            elif line.strip() and not line.strip().startswith("#"):
                insert_index = i
                break

        # Add imports if missing
        imports_to_add = []

        if not has_typing:
            imports_to_add.append("from typing import Any, Dict, List, Optional, Tuple, Union, Generator")

        if not has_pytest and any("test_" in line for line in lines):
            imports_to_add.append("import pytest")

        # Insert imports
        for i, import_line in enumerate(imports_to_add):
            lines.insert(insert_index + i, import_line)

        if imports_to_add:
            lines.insert(insert_index + len(imports_to_add), "")

        return "\n".join(lines)

    def fix_file(self, file_path: Path) -> bool:
        """Fix a single mobile testing or validation file."""
        try:
            logger.info(f"Processing {file_path}")

            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()

            content = original_content

            # Apply fixes in order
            content = self.add_comprehensive_imports(content)
            content = self.fix_test_function_annotations(content)
            content = self.fix_validation_function_annotations(content)
            content = self.fix_class_method_annotations(content)

            # Write back if changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info(f"[DONE] Fixed type annotations in {file_path}")
                return True
            else:
                logger.info(f"i  No changes needed for {file_path}")
                return False

        except Exception as e:
            logger.error(f"[TODO] Error processing {file_path}: {e}")
            return False

    def run(self) -> dict[str, Any]:
        """Run the mobile testing annotation fixer."""
        target_files = self.get_target_files()

        if not target_files:
            logger.warning("No mobile testing or validation files found!")
            return {"files_processed": 0, "files_modified": 0}

        logger.info(f"Found {len(target_files)} mobile testing/validation files")

        files_modified = 0
        for file_path in target_files:
            if self.fix_file(file_path):
                files_modified += 1

        results = {"files_processed": len(target_files), "files_modified": files_modified, "target_files": [str(f) for f in target_files]}

        logger.info(f"Completed! Modified {files_modified}/{len(target_files)} files")
        return results


def main() -> None:
    """Main function."""
    logger.info("Starting mobile testing type annotation fixes...")

    fixer = MobileTestingAnnotationFixer()
    results = fixer.run()

    print("\n" + "=" * 50)
    print("MOBILE TESTING TYPE ANNOTATION FIX SUMMARY")
    print("=" * 50)
    print(f"Files processed: {results['files_processed']}")
    print(f"Files modified: {results['files_modified']}")
    print("\nTarget files found:")
    for file_path in results["target_files"]:
        print(f"  - {file_path}")

    if results["files_modified"] > 0:
        print("\n[DONE] Type annotations have been added to mobile testing files!")
        print("Next steps:")
        print("  1. Run 'mypy --strict .' to check for remaining errors")
        print("  2. Run the main fix_strict_type_annotations.py for other files")
        print("  3. Run tests to ensure functionality is preserved")
    else:
        print("\ni  No files needed modification (already have type annotations)")


if __name__ == "__main__":
    main()
