#!/usr/bin/env python3
"""Fix import placement issues in project files only."""

import re
from pathlib import Path


def fix_file_imports(file_path: Path) -> bool:
    """Fix misplaced typing imports in a file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Remove misplaced typing imports (indented ones)
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            # Skip lines that are indented typing imports
            if re.match(r"^\s+from typing import", line):
                continue
            fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        # Add typing import at the top if not already there and if needed
        if "from typing import" not in content and ("-> " in content or ": Dict" in content or ": List" in content):
            lines = content.split("\n")

            # Find insertion point (after docstring and other imports)
            insert_idx = 0
            in_docstring = False

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Handle docstrings
                if stripped.startswith('"""') or stripped.startswith("'''"):
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

                # Skip comments and shebang
                if stripped.startswith("#"):
                    insert_idx = i + 1
                    continue

                # Found import section
                if stripped.startswith("import ") or stripped.startswith("from "):
                    if "typing" not in stripped:
                        insert_idx = i + 1
                elif stripped and not stripped.startswith("#"):
                    # Found first non-import, non-comment line
                    break

            lines.insert(insert_idx, "from typing import Any, Dict, List, Optional, Tuple, Union, Generator")
            content = "\n".join(lines)

        # Only write if content changed
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")

    return False


def main():
    """Fix project files only."""
    # Only fix files in our project directories
    project_dirs = ["src", "tests", "scripts", "."]

    fixed_count = 0
    for dir_path in project_dirs:
        dir_obj = Path(dir_path)
        if not dir_obj.exists():
            continue

        if dir_path == ".":
            # Only get .py files directly in root
            py_files = list(dir_obj.glob("*.py"))
        else:
            # Get all .py files recursively
            py_files = list(dir_obj.rglob("*.py"))

        for py_file in py_files:
            # Skip .venv and other unwanted directories
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            if fix_file_imports(py_file):
                print(f"Fixed: {py_file}")
                fixed_count += 1

    print(f"Fixed {fixed_count} project files")


if __name__ == "__main__":
    main()
