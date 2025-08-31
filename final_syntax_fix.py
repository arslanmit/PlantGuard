#!/usr/bin/env python3
"""Final comprehensive fix for all syntax errors."""

import ast
from pathlib import Path


def fix_file_completely(file_path: Path) -> bool:
    """Completely fix a file by removing all misplaced typing imports and adding one at the top."""
    try:
        content = file_path.read_text(encoding="utf-8")

        # Check if file has syntax errors
        try:
            ast.parse(content)
            return False  # No syntax errors
        except SyntaxError:
            pass  # Has syntax errors, continue

        lines = content.split("\n")
        clean_lines = []

        # Remove ALL typing import lines (both correct and incorrect)
        for line in lines:
            if "from typing import" in line:
                continue
            clean_lines.append(line)

        # Find the right place to insert typing import
        insert_idx = 0

        for i, line in enumerate(clean_lines):
            stripped = line.strip()

            # Skip shebang, encoding, docstrings
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                insert_idx = i + 1
                continue

            # If we find any import, insert before it
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_idx = i
                break

            # If we find code, insert before it
            if stripped and not stripped.startswith("#"):
                insert_idx = i
                break

        # Insert typing import at the correct location
        clean_lines.insert(insert_idx, "from typing import Any, Dict, List, Optional, Tuple, Union, Generator")
        clean_lines.insert(insert_idx + 1, "")  # Add blank line

        # Write the fixed content
        fixed_content = "\n".join(clean_lines)
        file_path.write_text(fixed_content, encoding="utf-8")

        # Verify the fix
        try:
            ast.parse(fixed_content)
            return True
        except SyntaxError as e:
            print(f"Fix verification failed for {file_path}: {e}")
            # Try without typing import
            clean_lines_no_typing = [line for line in clean_lines if "from typing import" not in line]
            fallback_content = "\n".join(clean_lines_no_typing)
            file_path.write_text(fallback_content, encoding="utf-8")
            return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Fix all files with syntax errors."""
    # List of files with known syntax errors
    error_files = [
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
            if fix_file_completely(file_path):
                print(f"Fixed: {file_path}")
                fixed_count += 1

    print(f"Fixed {fixed_count} files")

    # Final validation
    print("\nFinal validation...")
    errors = 0
    for file_path_str in error_files:
        file_path = Path(file_path_str)
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                print(f"Still has error: {file_path} - {e}")
                errors += 1

    if errors == 0:
        print("✅ All files fixed successfully!")
    else:
        print(f"❌ {errors} files still have errors")


if __name__ == "__main__":
    main()
