#!/usr/bin/env python3
"""Verify that Task 5 implementation meets all specified requirements."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.nlp import TextAdapter


def verify_requirements():
    """Verify all Task 5 requirements are met."""
    print("🔍 Verifying Task 5 requirements...")

    # Requirement 9.1: JSON schema for disease information storage
    print("\n✅ Requirement 9.1: JSON schema for disease information storage")
    kb_path = Path("data/knowledge_base/disease_info.json")
    assert kb_path.exists(), "Knowledge base file must exist"

    with open(kb_path) as f:
        kb_data = json.load(f)

    # Verify schema structure
    required_fields = ["schema_version", "last_updated", "diseases"]
    for field in required_fields:
        assert field in kb_data, f"Knowledge base must have {field} field"

    print("   ✓ JSON schema implemented with required fields")

    # Requirement 9.2: Comprehensive disease data for all 38 classes
    print("\n✅ Requirement 9.2: Comprehensive disease data for all 38 classes")

    # Load PlantVillage classes
    with open("data/knowledge_base/plantvillage_classes.json") as f:
        class_data = json.load(f)

    diseases = kb_data["diseases"]
    expected_classes = set(class_data["classes"])
    actual_classes = set(diseases.keys())

    assert expected_classes == actual_classes, f"Must cover all 38 classes. Missing: {expected_classes - actual_classes}"

    # Verify each disease has comprehensive information
    required_disease_fields = ["disease_name", "plant_type", "severity", "description", "symptoms", "treatment", "prevention", "affected_parts", "season", "economic_impact"]

    for disease_class, disease_info in diseases.items():
        for field in required_disease_fields:
            assert field in disease_info, f"{disease_class} must have {field} field"

        # Verify treatment structure
        treatment = disease_info["treatment"]
        assert isinstance(treatment, dict), f"{disease_class} treatment must be a dictionary"
        for treatment_type in ["immediate", "preventive", "organic"]:
            assert treatment_type in treatment, f"{disease_class} must have {treatment_type} treatment"

    print(f"   ✓ All {len(diseases)} diseases have comprehensive information")

    # Requirement 3.2: get_disease_info() method with fallback handling
    print("\n✅ Requirement 3.2: get_disease_info() method with fallback handling")

    adapter = TextAdapter()

    # Test known disease
    known_info = adapter.get_disease_info("Apple___Apple_scab")
    assert known_info["disease_name"] == "Apple Scab", "Must return correct disease info"

    # Test unknown disease (fallback)
    unknown_info = adapter.get_disease_info("Unknown___Disease")
    assert unknown_info["disease_name"] == "Unknown Disease", "Must provide fallback for unknown diseases"
    assert "not in our current knowledge base" in unknown_info["description"], "Must have appropriate fallback message"

    print("   ✓ get_disease_info() implemented with fallback handling")

    # Requirement 3.3: generate_response() method with template-based formatting
    print("\n✅ Requirement 3.3: generate_response() method with template-based formatting")

    # Test response generation
    response = adapter.generate_response("Apple___Apple_scab", "How do I treat this?", 0.85)
    assert len(response) > 100, "Response must be comprehensive"
    assert "Apple Scab" in response, "Response must include disease name"
    assert "Treatment" in response, "Response must include treatment information"

    # Test healthy plant response
    healthy_response = adapter.generate_response("Apple___healthy", "How is my plant?", 0.95)
    assert "healthy" in healthy_response.lower(), "Must recognize healthy plants"

    print("   ✓ generate_response() implemented with template-based formatting")

    # Requirement 3.4: analyze_query_intent() method using keyword matching
    print("\n✅ Requirement 3.4: analyze_query_intent() method using keyword matching")

    # Test intent analysis
    treatment_intents = adapter.analyze_query_intent("How do I treat this disease?")
    assert "treatment" in treatment_intents, "Must detect treatment intent"

    prevention_intents = adapter.analyze_query_intent("How can I prevent this?")
    assert "prevention" in prevention_intents, "Must detect prevention intent"

    organic_intents = adapter.analyze_query_intent("What organic treatments work?")
    assert "organic" in organic_intents, "Must detect organic intent"

    print("   ✓ analyze_query_intent() implemented with keyword matching")

    # Requirement 9.3, 9.4, 9.5: Treatment advice formatting with medical disclaimers
    print("\n✅ Requirements 9.3-9.5: Treatment advice formatting with medical disclaimers")

    # Test treatment advice formatting
    disease_info = adapter.get_disease_info("Apple___Apple_scab")
    treatment_advice = adapter.format_treatment_advice(disease_info, ["treatment", "organic"])
    assert "Disclaimer" in treatment_advice, "Must include medical disclaimer"
    assert "educational purposes only" in treatment_advice, "Must specify educational purpose"

    # Test response includes disclaimers
    disease_response = adapter.generate_response("Apple___Black_rot", "What should I do?", 0.75)
    assert "educational purposes only" in disease_response, "Disease responses must include disclaimers"

    print("   ✓ Treatment advice formatting with appropriate medical disclaimers")

    print("\n🎉 All Task 5 requirements verified successfully!")

    # Summary
    print("\n📊 Implementation Summary:")
    print(f"   • Knowledge base covers {len(diseases)} diseases")
    print("   • All 38 PlantVillage classes included")
    print("   • Comprehensive disease information with treatment details")
    print("   • Fallback handling for unknown diseases")
    print("   • Template-based response generation")
    print("   • Intent analysis using keyword matching")
    print("   • Medical disclaimers included")
    print("   • Validation scripts created")


def main():
    """Run verification."""
    try:
        verify_requirements()
    except AssertionError as e:
        print(f"\n❌ Requirement verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
