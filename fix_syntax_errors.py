#!/usr/bin/env python3
"""Fix syntax errors caused by misplaced imports."""

import re
from pathlib import Path


def fix_syntax_errors(file_path: Path) -> bool:
    """Fix syntax errors in a file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Fix misplaced typing imports
        lines = content.split("\n")
        fixed_lines = []
        typing_import_found = False

        # First pass: remove misplaced typing imports and collect them
        for line in lines:
            if re.match(r"^\s+from typing import", line.strip()):
                # This is a misplaced typing import - skip it
                typing_import_found = True
                continue
            fixed_lines.append(line)

        if not typing_import_found:
            return False

        content = "\n".join(fixed_lines)

        # Second pass: add typing import at the correct location
        lines = content.split("\n")
        insert_idx = 0

        # Find the right place to insert the import
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip shebang, encoding, and docstrings
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                insert_idx = i + 1
                continue

            # If we find an import, insert before it
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_idx = i
                break

            # If we find code, insert before it
            if stripped and not stripped.startswith("#"):
                insert_idx = i
                break

        # Insert the typing import
        lines.insert(insert_idx, "from typing import Any, Dict, List, Optional, Tuple, Union, Generator")
        lines.insert(insert_idx + 1, "")  # Add blank line

        content = "\n".join(lines)

        # Write the fixed content
        file_path.write_text(content, encoding="utf-8")
        return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main() -> None:
    """Fix syntax errors in project files."""
    # Get all Python files with syntax errors
    error_files = [
        "simple_test.py",
        "tests/test_training_config.py",
        "tests/test_setup.py",
        "tests/test_optimizers.py",
        "tests/test_preprocessing.py",
        "tests/test_resource_manager.py",
        "tests/test_dataset_manager.py",
        "tests/test_model_evaluation.py",
        "scripts/convert_model_fixed.py",
        "scripts/test_text_adapter_integration.py",
        "scripts/test_inference.py",
        "scripts/simple_eval.py",
        "scripts/direct_eval.py",
        "scripts/validate_dataset.py",
        "scripts/prepare_dataset_new.py",
        "scripts/validate_apps.py",
        "scripts/test_text_adapter.py",
        "scripts/list_models.py",
        "scripts/test_model_loading.py",
        "scripts/analyze_dataset.py",
        "scripts/setup_better_dummy_dataset.py",
        "scripts/create_complete_knowledge_base.py",
        "scripts/convert_model.py",
        "scripts/validate_knowledge_base.py",
        "scripts/complete_knowledge_base.py",
        "scripts/model_switching/check_model_weights.py",
        "scripts/model_switching/add_new_model.py",
        "scripts/model_switching/integrate_model_manager.py",
        "scripts/model_switching/simple_model_test.py",
        "scripts/model_switching/model_switcher_ui.py",
        "scripts/model_switching/final_model_test.py",
    ]

    fixed_count = 0
    for file_path_str in error_files:
        file_path = Path(file_path_str)
        if file_path.exists():
            if fix_syntax_errors(file_path):
                print(f"Fixed: {file_path}")
                fixed_count += 1

    print(f"Fixed {fixed_count} files with syntax errors")


if __name__ == "__main__":
    main()
