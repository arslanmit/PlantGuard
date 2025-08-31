#!/usr/bin/env python3
"""Script to analyze dataset statistics using DatasetManager."""

from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.training.dataset_manager import DatasetManager


def main() -> None:
    """Analyze dataset statistics."""

    parser = argparse.ArgumentParser(description="Analyze dataset statistics")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        help="Dataset directory to analyze (if not specified, checks common locations)",
    )
    args = parser.parse_args()

    dm = DatasetManager()

    if args.dataset_dir:
        datasets_to_check = [(args.dataset_dir, f"Dataset at {args.dataset_dir}")]
    else:
        # Check for datasets to analyze
        datasets_to_check = [
            ("data/processed/plantvillage", "Processed PlantVillage"),
            ("data/PlantVillage", "Legacy PlantVillage"),
            ("data/raw/plantvillage", "Raw PlantVillage"),
        ]

    found_dataset = False

    for dataset_path, dataset_name in datasets_to_check:
        if Path(dataset_path).exists():
            print(f"[SUMMARY] Analyzing {dataset_name} at {dataset_path}...")
            info = dm.analyze_dataset(Path(dataset_path))

            print(f"[CHART] Dataset Analysis for {dataset_name}:")
            print(f"  Name: {info.name}")
            print(f"  Total samples: {info.total_samples:,}")
            print(f"  Number of classes: {info.num_classes}")
            print(f"  Dataset size: {info.dataset_size_mb:.1f} MB")

            if info.train_samples > 0 or info.val_samples > 0:
                print(f"  Train samples: {info.train_samples:,}")
                print(f"  Validation samples: {info.val_samples:,}")

            print("  [DETAILS] Class distribution:")
            if isinstance(info.class_distribution, dict):
                # Check if this is a split dataset format (nested dict)
                distribution_values = list(info.class_distribution.values())
                has_nested_dicts = any(isinstance(v, dict) for v in distribution_values)

                if has_nested_dicts:
                    # Split dataset format: dict[str, dict[str, int]]
                    for class_name, splits in info.class_distribution.items():
                        if isinstance(splits, dict):
                            total = splits.get("train", 0) + splits.get("val", 0)
                            train_count = splits.get("train", 0)
                            val_count = splits.get("val", 0)
                            print(f"    {class_name}: {total} total (train: {train_count}, val: {val_count})")
                else:
                    # Single directory format: dict[str, int]
                    for class_name, count in sorted(info.class_distribution.items()):
                        if isinstance(count, int):
                            print(f"    {class_name}: {count}")

            if info.corrupted_files:
                print(f"  [WARNING]  Corrupted files: {len(info.corrupted_files)}")
                MAX_CORRUPTED_FILES_TO_SHOW = 10
                if len(info.corrupted_files) <= MAX_CORRUPTED_FILES_TO_SHOW:
                    for corrupted_file in info.corrupted_files:
                        print(f"    - {corrupted_file}")
                else:
                    print(f"    (showing first {MAX_CORRUPTED_FILES_TO_SHOW} of {len(info.corrupted_files)})")
                    for corrupted_file in info.corrupted_files[:MAX_CORRUPTED_FILES_TO_SHOW]:
                        print(f"    - {corrupted_file}")

            print()
            found_dataset = True

    if not found_dataset:
        print("[TODO] No datasets found to analyze")
        print("[TIP] Run 'make dataset-download' first, then 'make dataset-prepare' if needed")
        sys.exit(1)

    print("[DONE] Dataset analysis complete")


if __name__ == "__main__":
    main()
