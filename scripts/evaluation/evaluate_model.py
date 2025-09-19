#!/usr/bin/env python3
"""Script for evaluating trained models with comprehensive metrics.

This script provides a command-line interface for the automated model validation system,
allowing users to evaluate trained models with detailed metrics and reporting.
"""



import argparse
import contextlib
import logging
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder

try:
    from plantguard.training.model_validator import (
        AutomatedModelValidator,
        ValidationConfig,
    )
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from plantguard.training.model_validator import (
        AutomatedModelValidator,
        ValidationConfig,
    )

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def find_model_path(model_path: str | None = None) -> Path:
    """Find the model path to evaluate.

    Args:
        model_path: Optional explicit model path

    Returns:
        Path to the model file

    Raises:
        FileNotFoundError: If no model is found
    """
    if model_path:
        model_path = Path(model_path)
        if model_path.exists():
            return model_path
        else:
            raise FileNotFoundError(f"Model not found: {model_path}")

    # Search for models in common locations
    search_paths = [
        Path("data/models/vision_resnet50.pt"),
        Path("data/models").glob("*.pt"),
        Path("runs").glob("*/best_model.pt"),
        Path("runs").glob("*/*.pt"),
    ]

    found_models = []
    for search_path in search_paths:
        if isinstance(search_path, Path) and search_path.exists():
            found_models.append(search_path)
        else:
            # Handle glob patterns
            with contextlib.suppress(AttributeError, TypeError):
                found_models.extend(list(search_path))

    if not found_models:
        raise FileNotFoundError("No trained models found. Please train a model first with 'make train' or specify --model-path")

    # Return the most recent model
    found_models.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return found_models[0]


def find_dataset_path(dataset_path: str | None = None) -> Path:
    """Find the validation dataset path.

    Args:
        dataset_path: Optional explicit dataset path

    Returns:
        Path to the dataset directory

    Raises:
        FileNotFoundError: If no dataset is found
    """
    if dataset_path:
        dataset_path = Path(dataset_path)
        if dataset_path.exists() and (dataset_path / "val").exists():
            return dataset_path
        else:
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    # Search for datasets in common locations
    search_paths = [
        Path("data/processed/plantvillage"),
        Path("data/PlantVillage"),
    ]

    for search_path in search_paths:
        if search_path.exists() and (search_path / "val").exists():
            return search_path

    raise FileNotFoundError("No validation dataset found. Please run 'make dataset-download' then 'make dataset-prepare'")


def create_data_loader(dataset_path: Path, batch_size: int = 32) -> tuple[DataLoader, list[str]]:
    """Create validation data loader.

    Args:
        dataset_path: Path to dataset directory
        batch_size: Batch size for data loader

    Returns:
        Tuple of (data_loader, class_names)
    """
    # Standard transforms for evaluation
    transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    val_dataset = ImageFolder(dataset_path / "val", transform=transform)
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=min(4, torch.get_num_threads()),
        pin_memory=torch.cuda.is_available(),
    )

    return val_loader, val_dataset.classes


def main() -> None:
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description="Evaluate trained PlantGuard models with comprehensive metrics")
    parser.add_argument("--model-path", type=str, help="Path to the model file to evaluate")
    parser.add_argument("--dataset-path", type=str, help="Path to the dataset directory (should contain 'val' subdirectory)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for evaluation (default: 32)")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="runs/evaluation",
        help="Output directory for evaluation reports (default: runs/evaluation)",
    )
    parser.add_argument("--min-accuracy", type=float, default=0.7, help="Minimum accuracy threshold for validation (default: 0.7)")
    parser.add_argument("--num-samples", type=int, default=100, help="Number of samples for detailed testing (default: 100)")
    parser.add_argument("--strict", action="store_true", help="Use strict validation mode with higher thresholds")
    parser.add_argument("--baseline", type=str, help="Name of baseline model for regression analysis")

    args = parser.parse_args()

    try:
        # Find model and dataset
        print("[SEARCH] Finding model and dataset...")
        model_path = find_model_path(args.model_path)
        dataset_path = find_dataset_path(args.dataset_path)

        print(f"[FOLDER] Model: {model_path}")
        print(f"[SUMMARY] Dataset: {dataset_path}")

        # Create data loader
        print("[LIBRARY] Loading validation dataset...")
        val_loader, class_names = create_data_loader(dataset_path, args.batch_size)
        print(f"[DONE] Loaded {len(val_loader.dataset)} samples, {len(class_names)} classes")

        # Setup validation configuration
        config = ValidationConfig(
            min_accuracy=args.min_accuracy,
            enable_sample_testing=True,
            num_test_samples=args.num_samples,
            strict_mode=args.strict,
        )

        # Initialize validator
        print("[AI] Initializing model validator...")
        validator = AutomatedModelValidator(config=config)

        # Run evaluation
        print("[ACTIONS] Running comprehensive model evaluation...")
        result = validator.validate_model(
            model_path=model_path,
            validation_data_loader=val_loader,
            class_names=class_names,
            baseline_model_name=args.baseline,
        )

        # Display results
        print("\n" + "=" * 80)
        print(validator.generate_validation_summary(result))

        # Save detailed report
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / "validation_report.json"
        validator.save_validation_report(result, report_path)

        # Save text summary
        summary_path = output_dir / "validation_summary.txt"
        with summary_path.open("w", encoding="utf-8") as f:
            f.write(validator.generate_validation_summary(result))

        print(f"\n[DOCUMENT] Detailed report saved to: {report_path}")
        print(f"[DOCUMENT] Summary saved to: {summary_path}")

        # Exit with appropriate code
        if result.validation_passed:
            print(f"\n[SUCCESS] VALIDATION PASSED (Score: {result.overall_score:.3f})")
            sys.exit(0)
        else:
            print(f"\n[TODO] VALIDATION FAILED (Score: {result.overall_score:.3f})")
            if result.critical_issues:
                print("Critical issues:")
                for issue in result.critical_issues:
                    print(f"  - {issue}")
            sys.exit(1)

    except Exception as e:
        logger.exception("Evaluation failed")
        print(f"\n[TODO] Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
