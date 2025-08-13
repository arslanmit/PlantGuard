#!/usr/bin/env python3
"""Script to download PlantVillage dataset using DatasetManager."""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.training.dataset_manager import DatasetManager


def main() -> None:
    """Download PlantVillage dataset from Kaggle."""
    parser = argparse.ArgumentParser(description="Download PlantVillage dataset from Kaggle")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw/plantvillage",
        help="Output directory for downloaded dataset (default: data/raw/plantvillage)",
    )
    args = parser.parse_args()

    dm = DatasetManager()
    output_dir = Path(args.output_dir)

    print("📥 Downloading PlantVillage dataset from Kaggle...")
    print(f"📁 Output directory: {output_dir}")
    print()
    print("⚠️  Requirements:")
    print("  1. Kaggle API installed: pip install kaggle")
    print("  2. Kaggle API token configured:")
    print("     - Get token from: https://www.kaggle.com/account")
    print("     - Place kaggle.json in ~/.kaggle/")
    print("     - Set permissions: chmod 600 ~/.kaggle/kaggle.json")
    print()

    # Check if output directory already exists and has content
    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"⚠️  Output directory {output_dir} already exists and contains files")
        response = input("Do you want to continue? This may overwrite existing files (y/N): ")
        if response.lower() not in ["y", "yes"]:
            print("❌ Download cancelled")
            sys.exit(0)

    success = dm.download_plantvillage(output_dir)

    if success:
        print("✅ Dataset download completed successfully")
        print(f"📁 Dataset downloaded to: {output_dir}")
        print()
        print("🔄 Next steps:")
        print("  1. Run 'make prepare-dataset' to create train/val splits")
        print("  2. Run 'make validate-dataset' to check dataset integrity")
        print("  3. Run 'make analyze-dataset' to see dataset statistics")
    else:
        print("❌ Dataset download failed")
        print()
        print("🔧 Troubleshooting:")
        print("  1. Check Kaggle API installation: pip install kaggle")
        print("  2. Verify API token is configured: ls ~/.kaggle/kaggle.json")
        print("  3. Check token permissions: chmod 600 ~/.kaggle/kaggle.json")
        print("  4. Test API access: kaggle datasets list")
        sys.exit(1)


if __name__ == "__main__":
    main()
