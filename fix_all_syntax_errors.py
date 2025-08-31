#!/usr/bin/env python3
"""Fix all syntax errors caused by misplaced typing imports."""

import ast
import re
from pathlib import Path


def fix_file_syntax(file_path: Path) -> bool:
    """Fix syntax errors in a file by moving misplaced typing imports."""
    try:
        content = file_path.read_text(encoding="utf-8")

        # Check if file has syntax errors first
        try:
            ast.parse(content)
            return False  # No syntax errors, no need to fix
        except SyntaxError:
            pass  # Has syntax errors, continue to fix

        lines = content.split("\n")
        fixed_lines = []
        typing_imports = []

        # Remove misplaced typing imports
        for line in lines:
            # Check if this is a misplaced typing import (indented)
            if re.match(r"^\s+from typing import", line):
                # Extract the import content
                import_match = re.search(r"from typing import (.+)", line)
                if import_match:
                    typing_imports.append(import_match.group(1))
                continue
            fixed_lines.append(line)

        if not typing_imports:
            return False  # No misplaced imports found

        # Find the right place to insert the typing import
        insert_idx = 0
        in_docstring = False

        for i, line in enumerate(fixed_lines):
            stripped = line.strip()

            # Handle docstrings
            if '"""' in stripped or "'''" in stripped:
                if not in_docstring:
                    in_docstring = True
                    if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        in_docstring = False
                        insert_idx = i + 1
                else:
                    in_docstring = False
                    insert_idx = i + 1
                continue

            if in_docstring:
                continue

            # Skip shebang and encoding
            if stripped.startswith("#"):
                insert_idx = i + 1
                continue

            # If we find an import, insert before it
            if stripped.startswith("import ") or stripped.startswith("from "):
                if "typing" not in stripped:
                    insert_idx = i
                    break

            # If we find code, insert before it
            if stripped and not stripped.startswith("#"):
                insert_idx = i
                break

        # Combine all typing imports
        all_imports = set()
        for imp in typing_imports:
            # Split by comma and clean up
            for item in imp.split(","):
                all_imports.add(item.strip())

        # Create the typing import line
        typing_line = f"from typing import {', '.join(sorted(all_imports))}"

        # Insert the typing import
        fixed_lines.insert(insert_idx, typing_line)

        # Write the fixed content
        fixed_content = "\n".join(fixed_lines)
        file_path.write_text(fixed_content, encoding="utf-8")

        # Verify the fix worked
        try:
            ast.parse(fixed_content)
            return True
        except SyntaxError as e:
            print(f"Fix failed for {file_path}: {e}")
            return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main() -> None:
    """Fix all Python files with syntax errors."""
    # Get all Python files in the project
    python_files = []
    for pattern in ["*.py", "src/**/*.py", "tests/**/*.py", "scripts/**/*.py"]:
        for file_path in Path().glob(pattern):
            if ".venv" not in str(file_path) and "__pycache__" not in str(file_path):
                python_files.append(file_path)

    print(f"Checking {len(python_files)} Python files for syntax errors...")

    fixed_count = 0
    for file_path in python_files:
        if fix_file_syntax(file_path):
            print(f"Fixed: {file_path}")
            fixed_count += 1

    print(f"Fixed {fixed_count} files")

    # Validate all files now have correct syntax
    print("\nValidating fixes...")
    errors = 0
    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            print(f"Still has syntax error: {file_path} - {e}")
            errors += 1
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            errors += 1

    if errors == 0:
        print("[DONE] All Python files now have valid syntax!")
    else:
        print(f"[TODO] {errors} files still have syntax errors")


if __name__ == "__main__":
    main()
