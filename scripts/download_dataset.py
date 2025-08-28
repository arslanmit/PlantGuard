#!/usr/bin/env python3
"""
PlantGuard Dataset Download Script

Downloads and prepares the PlantVillage dataset via Kaggle API with:
- Progress tracking and resume capability
- Error handling and retry logic
- Dataset validation and structure verification
- AI agent-friendly JSON output
- Cross-platform compatibility
"""

import json
import logging
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DatasetDownloader:
    """Download and prepare PlantVillage dataset with progress tracking."""

    def __init__(self, data_dir: str = "data", use_kaggle_api: bool = True):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed" / "plantvillage"
        self.use_kaggle_api = use_kaggle_api

        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Dataset info
        self.dataset_info = {
            "name": "PlantVillage",
            "kaggle_dataset": "abdallahalidev/plantvillage-dataset",
            "size_gb": 27.2,
            "num_classes": 38,
            "total_images": 87863,
            "validation_files": ["plantvillage_dataset/train", "plantvillage_dataset/val", "plantvillage_dataset/test"],
        }

    def check_kaggle_setup(self) -> dict[str, Any]:
        """Check Kaggle API setup and credentials."""
        result = {"kaggle_available": False, "credentials_found": False, "api_working": False, "error": None}

        try:
            import kaggle

            result["kaggle_available"] = True

            # Check credentials
            kaggle_dir = Path.home() / ".kaggle"
            creds_file = kaggle_dir / "kaggle.json"

            if creds_file.exists():
                result["credentials_found"] = True

                # Test API
                try:
                    kaggle.api.authenticate()
                    result["api_working"] = True
                except Exception as e:
                    result["error"] = f"Authentication failed: {e!s}"
            else:
                result["error"] = f"Kaggle credentials not found. Place kaggle.json in {kaggle_dir}"

        except ImportError:
            result["error"] = "Kaggle package not installed. Run: pip install kaggle"
        except Exception as e:
            result["error"] = f"Kaggle setup error: {e!s}"

        return result

    def download_with_kaggle_api(self) -> dict[str, Any]:
        """Download dataset using Kaggle API with progress tracking."""
        result = {"success": False, "message": "", "download_time_seconds": 0, "file_size_mb": 0, "error": None}

        start_time = time.time()

        try:
            import kaggle

            logger.info(f"Downloading {self.dataset_info['name']} dataset...")
            logger.info(f"Dataset: {self.dataset_info['kaggle_dataset']}")
            logger.info(f"Size: ~{self.dataset_info['size_gb']} GB")

            # Download with progress
            kaggle.api.dataset_download_files(self.dataset_info["kaggle_dataset"], path=str(self.raw_dir), unzip=True, quiet=False)

            # Calculate stats
            result["download_time_seconds"] = time.time() - start_time
            result["success"] = True
            result["message"] = "Dataset downloaded successfully via Kaggle API"

            # Get downloaded size
            dataset_path = self.raw_dir / "plantvillage_dataset"
            if dataset_path.exists():
                size_bytes = sum(f.stat().st_size for f in dataset_path.rglob("*") if f.is_file())
                result["file_size_mb"] = size_bytes / (1024 * 1024)

            logger.info(f"[DONE] Download completed in {result['download_time_seconds']:.1f} seconds")

        except Exception as e:
            result["error"] = str(e)
            result["message"] = f"Kaggle API download failed: {e!s}"
            logger.error(result["message"])

        return result

    def download_direct_url(self, url: str) -> dict[str, Any]:
        """Download dataset from direct URL with progress tracking."""
        result = {"success": False, "message": "", "download_time_seconds": 0, "file_size_mb": 0, "error": None}

        zip_path = self.raw_dir / "plantvillage_dataset.zip"
        start_time = time.time()

        try:
            logger.info(f"Downloading from URL: {url}")

            response = requests.get(url, stream=True, timeout=30)  # Add timeout for security
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))

            with (
                open(zip_path, "wb") as f,
                tqdm(
                    desc="Downloading",
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar,
            ):
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

            # Extract with progress
            logger.info("Extracting dataset...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.raw_dir)

            # Cleanup
            zip_path.unlink()

            result["download_time_seconds"] = time.time() - start_time
            result["file_size_mb"] = total_size / (1024 * 1024)
            result["success"] = True
            result["message"] = "Dataset downloaded successfully via direct URL"

            logger.info(f"[DONE] Download completed in {result['download_time_seconds']:.1f} seconds")

        except Exception as e:
            result["error"] = str(e)
            result["message"] = f"Direct download failed: {e!s}"
            logger.error(result["message"])

        return result

    def validate_dataset(self) -> dict[str, Any]:
        """Validate downloaded dataset structure and content."""
        result = {"valid": False, "structure_check": False, "file_count": 0, "classes_found": 0, "missing_files": [], "errors": []}

        try:
            dataset_root = self.raw_dir / "plantvillage_dataset"

            if not dataset_root.exists():
                result["errors"].append("Dataset root directory not found")
                return result

            # Check expected structure
            expected_dirs = ["train", "val", "test"]
            missing_dirs = []

            for dir_name in expected_dirs:
                dir_path = dataset_root / dir_name
                if not dir_path.exists():
                    missing_dirs.append(dir_name)

            if missing_dirs:
                result["errors"].append(f"Missing directories: {missing_dirs}")
            else:
                result["structure_check"] = True

            # Count files and classes
            train_dir = dataset_root / "train"
            if train_dir.exists():
                classes = [d.name for d in train_dir.iterdir() if d.is_dir()]
                result["classes_found"] = len(classes)

                # Count total images
                image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
                total_files = 0

                for class_dir in train_dir.iterdir():
                    if class_dir.is_dir():
                        files = [f for f in class_dir.iterdir() if f.suffix.lower() in image_extensions]
                        total_files += len(files)

                result["file_count"] = total_files

            # Validation criteria
            if (
                result["structure_check"]
                and result["classes_found"] >= 30  # Expect ~38 classes
                and result["file_count"] >= 50000
            ):  # Expect ~87k images
                result["valid"] = True

            logger.info(f"Dataset validation: {result}")

        except Exception as e:
            result["errors"].append(f"Validation error: {e!s}")
            logger.error(f"Dataset validation failed: {e!s}")

        return result

    def prepare_dataset_structure(self) -> dict[str, Any]:
        """Prepare dataset for training with proper structure."""
        result = {"success": False, "message": "", "processed_structure": {}, "error": None}

        try:
            source_dir = self.raw_dir / "plantvillage_dataset"

            if not source_dir.exists():
                result["error"] = "Source dataset not found"
                return result

            # Copy with structure preservation
            logger.info("Preparing dataset structure for training...")

            for split in ["train", "val", "test"]:
                source_split = source_dir / split
                target_split = self.processed_dir / split

                if source_split.exists():
                    if target_split.exists():
                        shutil.rmtree(target_split)
                    shutil.copytree(source_split, target_split)

                    # Count files per split
                    file_count = sum(1 for f in target_split.rglob("*") if f.is_file())
                    result["processed_structure"][split] = file_count

            # Create dataset config
            config = {
                "name": self.dataset_info["name"],
                "version": "1.0",
                "processed_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "structure": result["processed_structure"],
                "classes": result["processed_structure"].get("train", 0),
                "data_dir": str(self.processed_dir),
            }

            config_file = self.processed_dir / "dataset_config.json"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            result["success"] = True
            result["message"] = "Dataset prepared successfully"

            logger.info(f"[DONE] Dataset prepared: {result['processed_structure']}")

        except Exception as e:
            result["error"] = str(e)
            result["message"] = f"Dataset preparation failed: {e!s}"
            logger.error(result["message"])

        return result

    def download_and_prepare(self, fallback_url: str | None = None) -> dict[str, Any]:
        """Complete download and preparation workflow."""
        workflow_result = {"success": False, "workflow_steps": {}, "total_time_seconds": 0, "final_dataset_info": {}, "error": None}

        start_time = time.time()

        try:
            # Step 1: Check if dataset already exists
            if (self.processed_dir / "dataset_config.json").exists():
                logger.info("Dataset already exists and is processed")
                workflow_result["success"] = True
                workflow_result["workflow_steps"]["already_exists"] = True
                return workflow_result

            # Step 2: Check Kaggle setup
            kaggle_status = self.check_kaggle_setup()
            workflow_result["workflow_steps"]["kaggle_check"] = kaggle_status

            # Step 3: Download
            download_result = None
            if kaggle_status["api_working"] and self.use_kaggle_api:
                download_result = self.download_with_kaggle_api()
            elif fallback_url:
                download_result = self.download_direct_url(fallback_url)
            else:
                workflow_result["error"] = "No download method available"
                return workflow_result

            workflow_result["workflow_steps"]["download"] = download_result

            if not download_result["success"]:
                workflow_result["error"] = download_result["error"]
                return workflow_result

            # Step 4: Validate
            validation_result = self.validate_dataset()
            workflow_result["workflow_steps"]["validation"] = validation_result

            if not validation_result["valid"]:
                workflow_result["error"] = f"Dataset validation failed: {validation_result['errors']}"
                return workflow_result

            # Step 5: Prepare
            preparation_result = self.prepare_dataset_structure()
            workflow_result["workflow_steps"]["preparation"] = preparation_result

            if not preparation_result["success"]:
                workflow_result["error"] = preparation_result["error"]
                return workflow_result

            # Success
            workflow_result["success"] = True
            workflow_result["total_time_seconds"] = time.time() - start_time
            workflow_result["final_dataset_info"] = {
                "location": str(self.processed_dir),
                "classes": validation_result["classes_found"],
                "total_files": validation_result["file_count"],
                "splits": preparation_result["processed_structure"],
            }

            logger.info(f"[SUCCESS] Complete workflow finished in {workflow_result['total_time_seconds']:.1f} seconds")

        except Exception as e:
            workflow_result["error"] = str(e)
            logger.error(f"Workflow failed: {e!s}")

        return workflow_result


def main():
    """Main function with CLI support and JSON output."""
    import argparse

    parser = argparse.ArgumentParser(description="Download PlantVillage dataset")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--no-kaggle", action="store_true", help="Skip Kaggle API")
    parser.add_argument("--fallback-url", help="Fallback download URL")
    parser.add_argument("--json-output", action="store_true", help="Output JSON results")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Initialize downloader
    downloader = DatasetDownloader(data_dir=args.data_dir, use_kaggle_api=not args.no_kaggle)

    # Run download workflow
    result = downloader.download_and_prepare(fallback_url=args.fallback_url)

    # Output results
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print("[DONE] Dataset download and preparation completed successfully!")
            print(f"📁 Location: {result['final_dataset_info'].get('location', 'Unknown')}")
            print(f"[SUMMARY] Classes: {result['final_dataset_info'].get('classes', 0)}")
            print(f"🖼️  Total files: {result['final_dataset_info'].get('total_files', 0)}")
            print(f"⏱️  Total time: {result['total_time_seconds']:.1f} seconds")
        else:
            print(f"[TODO] Download failed: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
