"""Generate class mapping JSON file from dataset directory.

This script creates a mapping between model class indices and human-readable names.
"""



import argparse
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def clean_class_name(raw_name: str) -> str:
    """Convert raw class name to human-readable format.

    Args:
        raw_name: Raw class name from dataset

    Returns:
        Human-readable name
    """
    # Replace underscores with spaces
    name = raw_name.replace("_", " ")

    # Handle special cases
    name = re.sub(r"\(including sour\)", "", name)
    name = re.sub(r"\(maize\)", "", name)
    name = re.sub(r"bell ", "Bell ", name)
    name = re.sub(r"Two-spotted spider mite", "", name)

    # Clean up extra spaces
    name = re.sub(r"\s+", " ", name).strip()

    # Capitalize properly
    words = name.split()
    cleaned_words = []

    for word in words:
        if word.lower() in ["and", "or", "the", "of", "in"]:
            cleaned_words.append(word.lower())
        else:
            cleaned_words.append(word.capitalize())

    return " ".join(cleaned_words)


def extract_plant_type(class_name: str) -> str:
    """Extract plant type from class name.

    Args:
        class_name: Raw class name

    Returns:
        Plant type
    """
    if "___" in class_name:
        plant_part = class_name.split("___")[0]

        # Handle special cases
        if "(" in plant_part:
            plant_part = plant_part.split("(")[0].strip()

        if "," in plant_part:
            plant_part = plant_part.split(",")[0].strip()

        return plant_part.replace("_", " ").title()

    return "Unknown"


def generate_class_mapping(dataset_dir: Path) -> dict:
    """Generate class mapping from dataset directory.

    Args:
        dataset_dir: Path to dataset directory

    Returns:
        Dictionary with class mapping
    """
    # Find train directory
    train_dir = dataset_dir / "train"
    if not train_dir.exists():
        train_dir = dataset_dir

    # Get class directories
    class_dirs = [d for d in train_dir.iterdir() if d.is_dir()]
    class_names = sorted([d.name for d in class_dirs])

    logger.info("Found %d classes", len(class_names))

    # Generate mappings
    class_to_readable = {}
    plant_types: dict[str, list[str]] = {}

    for class_name in class_names:
        # Generate readable name
        readable_name = clean_class_name(class_name)
        class_to_readable[class_name] = readable_name

        # Extract plant type
        plant_type = extract_plant_type(class_name)

        if plant_type not in plant_types:
            plant_types[plant_type] = []
        plant_types[plant_type].append(class_name)

        logger.debug("Class: %s -> %s (%s)", class_name, readable_name, plant_type)

    return {
        "classes": class_names,
        "class_to_readable": class_to_readable,
        "plant_types": plant_types,
    }


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate class mapping JSON")
    parser.add_argument("--dataset_dir", type=str, required=True, help="Dataset directory")
    parser.add_argument("--output_path", type=str, required=True, help="Output JSON file path")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    dataset_dir = Path(args.dataset_dir)
    output_path = Path(args.output_path)

    # Generate mapping
    mapping = generate_class_mapping(dataset_dir)

    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(mapping, f, indent=2)

    logger.info("Class mapping saved to %s", output_path)
    logger.info("Generated mapping for %d classes", len(mapping["classes"]))


if __name__ == "__main__":
    main()
