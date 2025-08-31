#!/usr/bin/env python3
"""Quick fix for misplaced typing imports."""

import re
from pathlib import Path


def fix_file_imports(file_path: Path) -> bool:
    """Fix misplaced typing imports in a file."""
    try:
        content = file_path.read_text(encoding="utf-8")

        # Pattern to find misplaced typing imports
        pattern = r"^(\s+)from typing import.*$"

        if re.search(pattern, content, re.MULTILINE):
            # Remove misplaced typing imports
            content = re.sub(pattern, "", content, flags=re.MULTILINE)

            # Add typing import at the top if not already there
            if "from typing import" not in content:
                lines = content.split("\n")

                # Find insertion point (after docstring and other imports)
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith("import ") or line.strip().startswith("from "):
                        if "typing" not in line:
                            insert_idx = i + 1
                    elif (
                        line.strip()
                        and not line.strip().startswith("#")
                        and not line.strip().startswith('"""')
                        and not line.strip().startswith("'''")
                    ):
                        break

                lines.insert(insert_idx, "from typing import Any, Dict, List, Optional, Tuple, Union, Generator")
                content = "\n".join(lines)

            file_path.write_text(content, encoding="utf-8")
            return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")

    return False


def main():
    """Fix all Python files with misplaced imports."""
    python_files = list(Path().rglob("*.py"))

    fixed_count = 0
    for py_file in python_files:
        if fix_file_imports(py_file):
            print(f"Fixed: {py_file}")
            fixed_count += 1

    print(f"Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
