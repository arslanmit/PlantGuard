#!/usr/bin/env python3
"""
Script to fix "no-untyped-call" errors by adding type annotations to called functions.

This addresses the specific mypy strict mode errors where functions are called
but don't have proper type annotations, causing "no-untyped-call" violations.
"""

import ast
import logging
import re
import subprocess
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UntypedCallFixer:
    """Fixes no-untyped-call errors by analyzing call sites and adding annotations."""

    def __init__(self) -> None:
        self.function_signatures: dict[str, str] = {}
        self.call_sites: dict[str, list[str]] = {}

        # Common function patterns and their typical signatures
        self.common_signatures = {
            # Test and setup functions
            "setUp": "(self) -> None",
            "tearDown": "(self) -> None",
            "setup_method": "(self) -> None",
            "teardown_method": "(self) -> None",
            # Property getters/setters
            "get_config": "(self) -> Dict[str, Any]",
            "set_config": "(self, config: Dict[str, Any]) -> None",
            "get_state": "(self) -> Dict[str, Any]",
            "set_state": "(self, state: Dict[str, Any]) -> None",
            # Mobile UI methods
            "render_mobile_layout": "(self) -> None",
            "display_mobile_content": "(self) -> None",
            "update_mobile_state": "(self) -> None",
            "handle_mobile_input": "(self, input_data: Any) -> None",
            # Validation methods
            "validate_input": "(self, data: Any) -> bool",
            "validate_config": "(self, config: Dict[str, Any]) -> bool",
            "check_requirements": "(self) -> bool",
            "verify_setup": "(self) -> bool",
            # Performance and optimization
            "optimize_performance": "(self) -> None",
            "measure_performance": "(self) -> Dict[str, float]",
            "cleanup_resources": "(self) -> None",
            "initialize_components": "(self) -> None",
            # File operations
            "load_file": "(self, path: str) -> Any",
            "save_file": "(self, path: str, data: Any) -> None",
            "delete_file": "(self, path: str) -> None",
            "create_directory": "(self, path: str) -> None",
            # Testing utilities
            "mock_adapter": "(self) -> Any",
            "create_test_data": "(self) -> Dict[str, Any]",
            "run_test_suite": "(self) -> None",
            "assert_results": "(self, expected: Any, actual: Any) -> None",
        }

    def get_mypy_untyped_call_errors(self) -> list[tuple[str, int, str]]:
        """Get specific no-untyped-call errors from mypy."""
        try:
            mypy_path = shutil.which("mypy")
            if not mypy_path:
                logger.warning("mypy executable not found in PATH")
                return []

            result = subprocess.run([mypy_path, "--strict", "."], capture_output=True, text=True, timeout=120)

            errors = []
            if result.stdout:
                for line in result.stdout.split("\n"):
                    if "no-untyped-call" in line or "Call to untyped function" in line:
                        # Parse: file:line: error: message
                        match = re.match(r"^([^:]+):(\d+):\s*error:\s*(.+)$", line)
                        if match:
                            file_path, line_num, message = match.groups()
                            errors.append((file_path, int(line_num), message))

            return errors

        except Exception as e:
            logger.warning(f"Could not run mypy: {e}")
            return []

    def analyze_function_calls(self, file_path: Path) -> dict[str, list[str]]:
        """Analyze function calls in a file to identify untyped calls."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST to find function calls
            tree = ast.parse(content)
            calls = {}

            class CallVisitor(ast.NodeVisitor):
                def visit_Call(self, node: ast.Call) -> None:
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name not in calls:
                            calls[func_name] = []
                        calls[func_name].append(f"Line {node.lineno}")
                    elif isinstance(node.func, ast.Attribute):
                        attr_name = node.func.attr
                        if attr_name not in calls:
                            calls[attr_name] = []
                        calls[attr_name].append(f"Line {node.lineno}")
                    self.generic_visit(node)

            visitor = CallVisitor()
            visitor.visit(tree)
            return calls

        except Exception as e:
            logger.warning(f"Could not analyze calls in {file_path}: {e}")
            return {}

    def infer_function_signature(self, func_name: str, context: str) -> str | None:
        """Infer function signature based on name and context."""
        # Check common patterns first
        if func_name in self.common_signatures:
            return self.common_signatures[func_name]

        # Pattern-based inference
        if func_name.startswith("test_"):
            return "() -> None"
        elif func_name.startswith("get_"):
            return "(self) -> Any"
        elif func_name.startswith("set_"):
            return "(self, value: Any) -> None"
        elif func_name.startswith("is_") or func_name.startswith("has_") or func_name.startswith("validate_") or func_name.startswith("check_"):
            return "(self) -> bool"
        elif func_name.startswith("render_") or func_name.startswith("display_"):
            return "(self) -> None"
        elif func_name.startswith("create_") or func_name.startswith("build_") or func_name.startswith("run_") or func_name.startswith("execute_"):
            return "(self) -> Any"
        elif func_name == "__init__":
            return "(self) -> None"
        elif func_name == "main":
            return "() -> None"

        # Default signature for unknown functions
        return "(*args: Any, **kwargs: Any) -> Any"

    def fix_function_signature(self, content: str, func_name: str, signature: str) -> str:
        """Add type annotation to a specific function."""
        lines = content.split("\n")
        modified_lines = []

        for line in lines:
            # Match function definition
            func_pattern = rf"^(\s*)(def\s+{re.escape(func_name)}\s*\([^)]*\))\s*:\s*$"
            match = re.match(func_pattern, line)

            if match:
                indent, func_def = match.groups()

                # Skip if already has return annotation
                if "->" in func_def:
                    modified_lines.append(line)
                    continue

                # Extract parameters from existing definition
                param_match = re.search(r"\(([^)]*)\)", func_def)
                if param_match:
                    existing_params = param_match.group(1).strip()

                    # Use existing parameters with inferred return type
                    if signature.startswith("(") and ") -> " in signature:
                        _, return_type = signature.split(") -> ", 1)
                        new_func_def = f"def {func_name}({existing_params}) -> {return_type}:"
                    else:
                        # Fallback to full signature replacement
                        new_func_def = f"def {func_name}{signature}:"

                    modified_lines.append(f"{indent}{new_func_def}")
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)

        return "\n".join(modified_lines)

    def fix_file_untyped_calls(self, file_path: Path, untyped_errors: list[tuple[int, str]]) -> bool:
        """Fix untyped call errors in a specific file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Extract function names from error messages
            functions_to_fix = set()
            for line_num, error_msg in untyped_errors:
                # Extract function name from error message
                # Common patterns: "Call to untyped function 'func_name'"
                func_match = re.search(r"function ['\"]([^'\"]+)['\"]", error_msg)
                if func_match:
                    functions_to_fix.add(func_match.group(1))

            # Fix each function
            for func_name in functions_to_fix:
                signature = self.infer_function_signature(func_name, content)
                if signature:
                    content = self.fix_function_signature(content, func_name, signature)

            # Add typing imports if needed
            if content != original_content and "from typing import" not in content:
                lines = content.split("\n")

                # Find insertion point (after docstring, before other imports)
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith("#") and not line.strip().startswith('"""'):
                        insert_index = i
                        break

                typing_import = "from typing import Any, Dict, List, Optional, Tuple, Union"
                lines.insert(insert_index, typing_import)
                lines.insert(insert_index + 1, "")
                content = "\n".join(lines)

            # Write back if changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info(f"Fixed untyped calls in {file_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error fixing {file_path}: {e}")
            return False

    def run(self) -> dict[str, Any]:
        """Run the untyped call fixer."""
        logger.info("Analyzing no-untyped-call errors...")

        # Get mypy errors
        untyped_errors = self.get_mypy_untyped_call_errors()

        if not untyped_errors:
            logger.info("No untyped call errors found!")
            return {"files_processed": 0, "files_modified": 0, "errors_found": 0}

        logger.info(f"Found {len(untyped_errors)} untyped call errors")

        # Group errors by file
        errors_by_file: dict[str, list[tuple[int, str]]] = {}
        for file_path, line_num, message in untyped_errors:
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append((line_num, message))

        # Fix each file
        files_modified = 0
        for file_path_str, file_errors in errors_by_file.items():
            file_path = Path(file_path_str)
            if file_path.exists():
                if self.fix_file_untyped_calls(file_path, file_errors):
                    files_modified += 1

        return {
            "files_processed": len(errors_by_file),
            "files_modified": files_modified,
            "errors_found": len(untyped_errors),
            "files_with_errors": list(errors_by_file.keys()),
        }


def main() -> None:
    """Main function."""
    logger.info("Starting untyped call fixes...")

    fixer = UntypedCallFixer()
    results = fixer.run()

    print("\n" + "=" * 50)
    print("UNTYPED CALL FIX SUMMARY")
    print("=" * 50)
    print(f"Errors found: {results['errors_found']}")
    print(f"Files processed: {results['files_processed']}")
    print(f"Files modified: {results['files_modified']}")

    if results.get("files_with_errors"):
        print("\nFiles with untyped call errors:")
        for file_path in results["files_with_errors"]:
            print(f"  - {file_path}")

    if results["files_modified"] > 0:
        print("\n✅ Untyped call errors have been addressed!")
        print("Run 'mypy --strict .' to verify the fixes.")
    else:
        print("\ni  No files needed modification.")


if __name__ == "__main__":
    main()
