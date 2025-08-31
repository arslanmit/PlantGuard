#!/usr/bin/env python3
"""Validate the disease knowledge base for completeness and accuracy."""


import json
from pathlib import Path


def validate_knowledge_base() -> bool:
    """Validate the disease knowledge base."""
    # Load knowledge base

    kb_path = Path("data/knowledge_base/disease_info.json")
    if not kb_path.exists():
        print("[TODO] Knowledge base file not found")
        return False

    with open(kb_path, encoding="utf-8") as f:
        kb_data = json.load(f)

    # Load class mapping
    with open("data/knowledge_base/plantvillage_classes.json") as f:
        class_data = json.load(f)

    print("[SEARCH] Validating knowledge base...")

    # Check schema
    required_fields = ["schema_version", "last_updated", "diseases"]
    for field in required_fields:
        if field not in kb_data:
            print(f"[TODO] Missing required field: {field}")
            return False

    diseases = kb_data["diseases"]
    expected_classes = set(class_data["classes"])
    actual_classes = set(diseases.keys())

    # Check completeness
    missing = expected_classes - actual_classes
    extra = actual_classes - expected_classes

    if missing:
        print(f"[TODO] Missing diseases: {missing}")
        return False

    if extra:
        print(f"[WARNING]  Extra diseases: {extra}")

    # Validate each disease entry
    required_disease_fields = [
        "disease_name",
        "plant_type",
        "severity",
        "description",
        "symptoms",
        "treatment",
        "prevention",
        "affected_parts",
        "season",
        "economic_impact",
    ]

    valid_count = 0
    for class_name, disease_info in diseases.items():
        missing_fields = []
        for field in required_disease_fields:
            if field not in disease_info:
                missing_fields.append(field)

        if missing_fields:
            print(f"[TODO] {class_name} missing fields: {missing_fields}")
        else:
            valid_count += 1

    print(f"[DONE] Validated {valid_count}/{len(diseases)} disease entries")
    print(f"[DONE] Knowledge base covers all {len(expected_classes)} PlantVillage classes")

    # Check treatment structure
    treatment_issues = 0
    for class_name, disease_info in diseases.items():
        treatment = disease_info.get("treatment", {})
        if not isinstance(treatment, dict):
            print(f"[TODO] {class_name}: treatment should be a dictionary")
            treatment_issues += 1
            continue

        required_treatment_keys = ["immediate", "preventive", "organic"]
        for key in required_treatment_keys:
            if key not in treatment:
                print(f"[TODO] {class_name}: missing treatment.{key}")
                treatment_issues += 1

    if treatment_issues == 0:
        print("[DONE] All treatment structures are valid")
    else:
        print(f"[TODO] Found {treatment_issues} treatment structure issues")

    return missing == set() and treatment_issues == 0


def main() -> None:
    """Run validation."""
    success = validate_knowledge_base()
    if success:
        print("\n[SUCCESS] Knowledge base validation passed!")
    else:
        print("\n[TODO] Knowledge base validation failed!")
    return success


if __name__ == "__main__":
    main()
