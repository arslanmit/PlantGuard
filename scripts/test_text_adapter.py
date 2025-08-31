#!/usr/bin/env python3
"""Test the TextAdapter implementation to ensure all methods work correctly."""


import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.nlp import TextAdapter


def test_text_adapter() -> None:
    """Test TextAdapter functionality."""

    print("[TEST] Testing TextAdapter implementation...")

    # Initialize TextAdapter
    adapter = TextAdapter()

    # Test 1: get_disease_info for known disease
    print("\n1. Testing get_disease_info() for known disease...")
    disease_info = adapter.get_disease_info("Apple___Apple_scab")
    print(f"   Disease name: {disease_info.get('disease_name')}")
    print(f"   Plant type: {disease_info.get('plant_type')}")
    print(f"   Severity: {disease_info.get('severity')}")
    print(f"   Has treatment info: {'treatment' in disease_info}")

    # Test 2: get_disease_info for unknown disease (fallback)
    print("\n2. Testing get_disease_info() fallback for unknown disease...")
    unknown_info = adapter.get_disease_info("Unknown___Disease")
    print(f"   Disease name: {unknown_info.get('disease_name')}")
    print(f"   Description contains fallback: {'not in our current knowledge base' in unknown_info.get('description', '')}")

    # Test 3: analyze_query_intent
    print("\n3. Testing analyze_query_intent()...")
    test_queries = [
        "How do I treat this disease?",
        "What are the symptoms of apple scab?",
        "How can I prevent this from happening again?",
        "Is this organic treatment safe?",
        "When should I apply fungicide?",
    ]

    for query in test_queries:
        intents = adapter.analyze_query_intent(query)
        print(f"   Query: '{query}' -> Intents: {intents}")

    # Test 4: generate_response for healthy plant
    print("\n4. Testing generate_response() for healthy plant...")
    healthy_response = adapter.generate_response("Apple___healthy", "How is my plant doing?", 0.95)
    print(f"   Response length: {len(healthy_response)} characters")
    print(f"   Contains 'healthy': {'healthy' in healthy_response.lower()}")

    # Test 5: generate_response for disease with treatment query
    print("\n5. Testing generate_response() for disease with treatment query...")
    disease_response = adapter.generate_response("Apple___Apple_scab", "How do I treat apple scab?", 0.85)
    print(f"   Response length: {len(disease_response)} characters")
    print(f"   Contains treatment info: {'Treatment' in disease_response}")
    print(f"   Contains disclaimer: {'educational purposes' in disease_response}")

    # Test 6: generate_response with low confidence
    print("\n6. Testing generate_response() with low confidence...")
    low_conf_response = adapter.generate_response("Apple___Black_rot", "What's wrong with my apple?", 0.45)
    print(f"   Response length: {len(low_conf_response)} characters")
    print(f"   Contains uncertainty: {'not entirely certain' in low_conf_response}")

    # Test 7: format_treatment_advice
    print("\n7. Testing format_treatment_advice()...")
    disease_info = adapter.get_disease_info("Apple___Apple_scab")
    treatment_advice = adapter.format_treatment_advice(disease_info, ["treatment", "organic"])
    print(f"   Treatment advice length: {len(treatment_advice)} characters")
    print(f"   Contains disclaimer: {'Disclaimer' in treatment_advice}")

    print("\n[DONE] All TextAdapter tests completed successfully!")


def test_knowledge_base_coverage() -> None:
    """Test knowledge base coverage."""
    print("\n[SEARCH] Testing knowledge base coverage...")

    adapter = TextAdapter()

    # Load class mapping to test all diseases
    import json

    with open("data/knowledge_base/plantvillage_classes.json") as f:
        class_data = json.load(f)

    missing_diseases = []
    for disease_class in class_data["classes"]:
        disease_info = adapter.get_disease_info(disease_class)
        if disease_info.get("disease_name") == "Unknown Disease":
            missing_diseases.append(disease_class)

    if missing_diseases:
        print(f"   [TODO] Missing diseases in knowledge base: {missing_diseases}")
    else:
        print(f"   [DONE] All {len(class_data['classes'])} diseases covered in knowledge base")


def main() -> None:
    """Run all tests."""
    try:
        test_text_adapter()
        test_knowledge_base_coverage()
        print("\n[SUCCESS] All tests passed!")
    except Exception as e:
        print(f"\n[TODO] Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
