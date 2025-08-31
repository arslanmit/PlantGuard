#!/usr/bin/env python3
"""Simple syntax validation for Python files."""

import ast
import sys
from pathlib import Path


def validate_file(file_path: Path) -> bool:
    """Validate Python syntax of a file."""
from typing import Any, Dict, List, Optional, Tuple, Union, Generator

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False


def main() -> None:
    """Validate all Python files in the project."""
    project_files = []

    # Get project files (excluding .venv)
    for pattern in ["*.py", "src/**/*.py", "tests/**/*.py", "scripts/**/*.py"]:
        for file_path in Path().glob(pattern):
            if ".venv" not in str(file_path):
                project_files.append(file_path)

    print(f"Validating {len(project_files)} Python files...")

    errors = 0
    for file_path in project_files:
        if not validate_file(file_path):
            errors += 1

    if errors == 0:
        print("✅ All Python files have valid syntax!")
        return True
    else:
        print(f"❌ Found {errors} files with syntax errors")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
