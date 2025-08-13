#!/usr/bin/env python3
"""Script to prepare dataset using DatasetManager."""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.training.dataset_manager import DatasetConfig, DatasetManager


def main() -> None:
    """Prepare dataset with train/val splits."""
    parser = argparse.ArgumentParser(description="Prepare dataset with train/val splits")
    parser.add_argument(
        "--source-dir",
        type=str,
        help="Source dataset directory (if not specified, checks common locations)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/plantvillage",
        help="Output directory for prepared dataset",
    )
    parser.add_argument(
        "--train-ratio", type=float, default=0.8, help="Ratio of data for training (default: 0.8)"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducible splits (default: 42)",
    )
    args = parser.parse_args()

    dm = DatasetManager()

    if args.source_dir:
        source_dir = Path(args.source_dir)
        if not source_dir.exists():
            print(f"❌ Source directory not found: {source_dir}")
            sys.exit(1)
    else:
        # Look for raw dataset in multiple locations
        raw_locations = ["data/raw/plantvillage", "data/PlantVillage_raw", "data/raw/PlantVillage"]

        source_dir = None
        for location in raw_locations:
            if Path(location).exists():
                source_dir = Path(location)
                print(f"✅ Found raw dataset at {location}")
                break

        if source_dir is None:
            print("❌ Raw PlantVillage dataset not found")
            print("🔍 Checked locations:")
            for location in raw_locations:
                print(f"  - {location}")
            print("💡 Please run 'make download-dataset' or download manually")
            sys.exit(1)

    # Prepare dataset with configuration
    output_dir = Path(args.output_dir)
    config = DatasetConfig(
        train_ratio=args.train_ratio,
        val_ratio=1.0 - args.train_ratio,
        random_seed=args.random_seed,
        min_samples_per_class=10,
    )

    print(f"📊 Preparing dataset from {source_dir} to {output_dir}...")
    print("⚙️  Configuration:")
    print(f"  Train ratio: {config.train_ratio}")
    print(f"  Validation ratio: {config.val_ratio}")
    print(f"  Random seed: {config.random_seed}")
    print(f"  Min samples per class: {config.min_samples_per_class}")

    success = dm.prepare_dataset(source_dir, output_dir, config)

    if success:
        print("✅ Dataset preparation completed")
        print(f"📁 Dataset prepared at {output_dir}")
        print("💡 Run 'make analyze-dataset' to see statistics")
    else:
        print("❌ Dataset preparation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
