#!/usr/bin/env python3
"""
Script to fix strict mode type annotations for production readiness.

This script addresses task 17 from the code-quality-fixes spec:
- Add missing return type annotations to all functions (864 strict mode errors)
- Fix "no-untyped-def" errors in mobile testing suites and validation scripts
- Add proper type annotations to all class methods and standalone functions
- Fix "no-untyped-call" errors by adding type annotations to called functions

Requirements: 1.1, 6.1
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TypeAnnotationFixer:
    """Fixes missing type annotations in Python files."""

    def __init__(self) -> None:
        self.fixed_files: list[str] = []
        self.errors_found: dict[str, list[str]] = {}
        self.common_return_types = {
            "test_": "None",  # Test functions typically return None
            "setUp": "None",
            "tearDown": "None",
            "render": "None",  # UI render methods
            "display": "None",
            "show": "None",
            "print": "None",
            "log": "None",
            "validate": "bool",
            "check": "bool",
            "is_": "bool",
            "has_": "bool",
            "can_": "bool",
            "should_": "bool",
            "get_": "Any",  # Getters can return various types
            "load_": "Any",
            "create_": "Any",
            "build_": "Any",
            "make_": "Any",
            "generate_": "Any",
            "process_": "Any",
            "run_": "Any",
            "execute_": "Any",
            "init": "None",  # __init__ methods
            "__init__": "None",
            "main": "None",
            "setup": "None",
            "cleanup": "None",
        }

    def get_mypy_errors(self) -> list[str]:
        """Get mypy errors in strict mode."""
        try:
            result = subprocess.run(["mypy", "--strict", "."], capture_output=True, text=True, timeout=120)
            return result.stdout.split("\n") if result.stdout else []
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not run mypy: {e}")
            return []

    def parse_mypy_errors(self, errors: list[str]) -> dict[str, list[str]]:
        """Parse mypy errors to extract files with missing annotations."""
        file_errors: dict[str, list[str]] = {}

        for error in errors:
            if not error.strip():
                continue

            # Parse mypy error format: file:line: error: message
            match = re.match(r"^([^:]+):(\d+):\s*error:\s*(.+)$", error)
            if not match:
                continue

            file_path, line_num, message = match.groups()

            # Focus on type annotation errors
            if any(
                keyword in message.lower()
                for keyword in [
                    "no return value expected",
                    "missing return statement",
                    "function is missing a return type annotation",
                    "function is missing a type annotation",
                    "no-untyped-def",
                    "no-untyped-call",
                    "missing type annotation",
                ]
            ):
                if file_path not in file_errors:
                    file_errors[file_path] = []
                file_errors[file_path].append(f"Line {line_num}: {message}")

        return file_errors

    def infer_return_type(self, func_name: str, func_body: str) -> str:
        """Infer return type based on function name and body analysis."""
        # Check function name patterns
        for pattern, return_type in self.common_return_types.items():
            if func_name.startswith(pattern):
                return return_type

        # Analyze function body for return statements
        if "return None" in func_body or func_body.strip().endswith("return"):
            return "None"
        elif "return True" in func_body or "return False" in func_body:
            return "bool"
        elif re.search(r"return \d+", func_body):
            return "int"
        elif re.search(r"return \d+\.\d+", func_body):
            return "float"
        elif re.search(r'return ["\']', func_body):
            return "str"
        elif re.search(r"return \[", func_body):
            return "List[Any]"
        elif re.search(r"return \{", func_body):
            return "Dict[str, Any]"
        elif "yield" in func_body:
            return "Generator[Any, None, None]"

        # Default to Any for complex cases
        return "Any"

    def add_missing_imports(self, file_content: str) -> str:
        """Add missing typing imports."""
        lines = file_content.split("\n")

        # Check if typing imports exist
        has_typing_import = any("from typing import" in line or "import typing" in line for line in lines)

        if not has_typing_import:
            # Find the right place to insert imports (after docstring, before other imports)
            insert_index = 0
            in_docstring = False

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Skip shebang and encoding
                if stripped.startswith("#"):
                    insert_index = i + 1
                    continue

                # Handle docstrings
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if not in_docstring:
                        in_docstring = True
                    elif stripped.endswith('"""') or stripped.endswith("'''"):
                        in_docstring = False
                        insert_index = i + 1
                    continue

                if in_docstring:
                    continue

                # Found first import or code
                if stripped and not stripped.startswith("#"):
                    insert_index = i
                    break

            # Add comprehensive typing imports
            typing_import = "from typing import Any, Dict, List, Optional, Tuple, Union, Generator"
            lines.insert(insert_index, typing_import)
            lines.insert(insert_index + 1, "")

        return "\n".join(lines)

    def fix_function_annotations(self, file_content: str) -> str:
        """Add missing return type annotations to functions."""
        lines = file_content.split("\n")
        modified_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Match function definitions without return type annotations
            func_match = re.match(r"^(\s*)(def\s+(\w+)\s*\([^)]*\))\s*:\s*$", line)
            if func_match:
                indent, func_def, func_name = func_match.groups()

                # Skip if already has return type annotation
                if "->" in func_def:
                    modified_lines.append(line)
                    i += 1
                    continue

                # Collect function body to analyze return type
                func_body_lines = []
                j = i + 1
                current_indent = len(indent)

                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() == "":
                        func_body_lines.append(next_line)
                        j += 1
                        continue

                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= current_indent and next_line.strip():
                        break

                    func_body_lines.append(next_line)
                    j += 1

                func_body = "\n".join(func_body_lines)
                return_type = self.infer_return_type(func_name, func_body)

                # Add return type annotation
                new_func_def = f"{func_def} -> {return_type}:"
                modified_lines.append(f"{indent}{new_func_def}")

            else:
                modified_lines.append(line)

            i += 1

        return "\n".join(modified_lines)

    def fix_method_annotations(self, file_content: str) -> str:
        """Fix method annotations in classes."""
        lines = file_content.split("\n")
        modified_lines = []

        for line in lines:
            # Match method definitions without return annotations
            method_match = re.match(r"^(\s*)(def\s+(\w+)\s*\([^)]*\))\s*:\s*$", line)
            if method_match:
                indent, method_def, method_name = method_match.groups()

                # Skip if already has return type annotation
                if "->" in method_def:
                    modified_lines.append(line)
                    continue

                # Special handling for common method patterns
                if (
                    method_name == "__init__"
                    or method_name.startswith("test_")
                    or method_name in ["setUp", "tearDown", "setup", "cleanup"]
                    or method_name.startswith("render")
                    or method_name.startswith("display")
                ):
                    return_type = "None"
                elif method_name.startswith("is_") or method_name.startswith("has_"):
                    return_type = "bool"
                else:
                    return_type = "Any"

                new_method_def = f"{method_def} -> {return_type}:"
                modified_lines.append(f"{indent}{new_method_def}")
            else:
                modified_lines.append(line)

        return "\n".join(modified_lines)

    def fix_file(self, file_path: Path) -> bool:
        """Fix type annotations in a single file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()

            # Apply fixes
            content = original_content
            content = self.add_missing_imports(content)
            content = self.fix_function_annotations(content)
            content = self.fix_method_annotations(content)

            # Only write if content changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info(f"Fixed type annotations in {file_path}")
                self.fixed_files.append(str(file_path))
                return True

            return False

        except Exception as e:
            logger.error(f"Error fixing {file_path}: {e}")
            return False

    def get_python_files(self) -> list[Path]:
        """Get all Python files in the project."""
        python_files = []

        # Key directories to check
        directories = [
            Path("src"),
            Path("tests"),
            Path("scripts"),
            Path(),  # Root level files
        ]

        for directory in directories:
            if directory.exists():
                if directory == Path():
                    # Only get .py files directly in root, not subdirectories
                    python_files.extend(directory.glob("*.py"))
                else:
                    # Recursively get all .py files in subdirectories
                    python_files.extend(directory.rglob("*.py"))

        # Filter out __pycache__ and other unwanted files
        filtered_files = []
        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue
            if ".venv" in str(file_path):
                continue
            if "node_modules" in str(file_path):
                continue
            filtered_files.append(file_path)

        return filtered_files

    def run_validation(self) -> tuple[bool, dict[str, Any]]:
        """Run validation to check if fixes were successful."""
        logger.info("Running mypy validation...")

        try:
            result = subprocess.run(["mypy", "--strict", "."], capture_output=True, text=True, timeout=120)

            errors = result.stdout.split("\n") if result.stdout else []
            type_errors = [
                e
                for e in errors
                if "error:" in e and any(keyword in e.lower() for keyword in ["missing return type", "no-untyped-def", "no-untyped-call"])
            ]

            success = len(type_errors) == 0

            return success, {
                "total_errors": len([e for e in errors if "error:" in e]),
                "type_annotation_errors": len(type_errors),
                "files_fixed": len(self.fixed_files),
                "sample_remaining_errors": type_errors[:10],
            }

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False, {"error": str(e)}

    def generate_report(self, validation_results: dict[str, Any]) -> None:
        """Generate a report of the fixes applied."""
        report_path = Path("type_annotation_fix_report.md")

        with open(report_path, "w") as f:
            f.write("# Type Annotation Fix Report\n\n")
            f.write("## Summary\n\n")
            f.write(f"- Files processed: {len(self.get_python_files())}\n")
            f.write(f"- Files modified: {len(self.fixed_files)}\n")
            f.write(f"- Remaining type errors: {validation_results.get('type_annotation_errors', 'Unknown')}\n\n")

            f.write("## Files Modified\n\n")
            for file_path in self.fixed_files:
                f.write(f"- {file_path}\n")

            if validation_results.get("sample_remaining_errors"):
                f.write("\n## Sample Remaining Errors\n\n")
                for error in validation_results["sample_remaining_errors"]:
                    f.write(f"- {error}\n")

            f.write("\n## Next Steps\n\n")
            if validation_results.get("type_annotation_errors", 0) > 0:
                f.write("- Review remaining errors and add specific type annotations\n")
                f.write("- Consider using `# type: ignore` for complex cases\n")
                f.write("- Run mypy again to verify fixes\n")
            else:
                f.write("- All type annotation errors have been resolved!\n")
                f.write("- Consider running full test suite to ensure functionality\n")

        logger.info(f"Report generated: {report_path}")


def main() -> None:
    """Main function to run the type annotation fixer."""
    logger.info("Starting type annotation fixes for production readiness...")

    fixer = TypeAnnotationFixer()

    # Get all Python files
    python_files = fixer.get_python_files()
    logger.info(f"Found {len(python_files)} Python files to process")

    # Fix each file
    for file_path in python_files:
        fixer.fix_file(file_path)

    # Run validation
    success, results = fixer.run_validation()

    # Generate report
    fixer.generate_report(results)

    # Summary
    logger.info("Type annotation fixes completed!")
    logger.info(f"Files modified: {len(fixer.fixed_files)}")
    logger.info(f"Remaining type errors: {results.get('type_annotation_errors', 'Unknown')}")

    if success:
        logger.info("✅ All type annotation errors have been resolved!")
    else:
        logger.warning("⚠️  Some type annotation errors remain. Check the report for details.")


if __name__ == "__main__":
    main()
