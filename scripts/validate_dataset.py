#!/usr/bin/env python3
"""Script to validate dataset integrity using DatasetManager."""

from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.training.dataset_manager import DatasetManager


def main() -> None:
    """Validate dataset integrity."""

    parser = argparse.ArgumentParser(description="Validate dataset integrity")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        help="Dataset directory to validate (if not specified, checks common locations)",
    )
    args = parser.parse_args()

    dm = DatasetManager()

    if args.dataset_dir:
        datasets_to_check = [(args.dataset_dir, f"Dataset at {args.dataset_dir}")]
    else:
        # Check for datasets to validate
        datasets_to_check = [
            ("data/processed/plantvillage", "Processed PlantVillage"),
            ("data/PlantVillage", "Legacy PlantVillage"),
            ("data/raw/plantvillage", "Raw PlantVillage"),
        ]

    found_dataset = False
    all_valid = True

    for dataset_path, dataset_name in datasets_to_check:
        if Path(dataset_path).exists():
            print(f"[SEARCH] Validating {dataset_name} at {dataset_path}...")
            result = dm.validate_dataset(Path(dataset_path))

            print(f"[SUMMARY] Results for {dataset_name}:")
            print(f"  Total files: {result.total_files}")
            print(f"  Valid files: {result.valid_files}")
            print(f"  Corrupted files: {len(result.corrupted_files)}")
            print(f"  Classes found: {len(result.class_counts)}")

            if result.is_valid:
                print("  [DONE] Dataset is valid")
            else:
                print("  [TODO] Dataset has issues")
                all_valid = False

            if result.errors:
                print("  [ALERT] Errors:")
                for error in result.errors:
                    print(f"    - {error}")

            if result.warnings:
                print("  [WARNING]  Warnings:")
                for warning in result.warnings:
                    print(f"    - {warning}")

            print()
            found_dataset = True

    if not found_dataset:
        print("[TODO] No datasets found to validate")
        print("[TIP] Run 'make dataset-download' first, then 'make dataset-prepare' if needed")
        sys.exit(1)

    if not all_valid:
        print("[TODO] Some datasets have validation issues")
        sys.exit(1)
    else:
        print("[DONE] All datasets are valid")


if __name__ == "__main__":
    main()
