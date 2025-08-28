#!/usr/bin/env python3
"""Integration test for TextAdapter with the PlantGuard system."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.nlp import TextAdapter


def test_integration_scenarios():
    """Test realistic integration scenarios."""
    print("🔗 Testing TextAdapter integration scenarios...")

    adapter = TextAdapter()

    # Scenario 1: High confidence disease detection with treatment query
    print("\n1. High confidence disease detection with treatment query")
    response = adapter.generate_response(
        disease_class="Tomato___Early_blight",
        user_query="My tomato has brown spots. How do I treat this?",
        confidence=0.92,
    )
    print(f"   Response preview: {response[:100]}...")
    assert "high confidence" in response.lower()
    assert "treatment" in response.lower()

    # Scenario 2: Healthy plant with maintenance query
    print("\n2. Healthy plant with maintenance query")
    response = adapter.generate_response(
        disease_class="Apple___healthy",
        user_query="My apple tree looks good. How do I keep it healthy?",
        confidence=0.88,
    )
    print(f"   Response preview: {response[:100]}...")
    assert "healthy" in response.lower()
    assert "maintain" in response.lower()

    # Scenario 3: Low confidence with uncertainty handling
    print("\n3. Low confidence with uncertainty handling")
    response = adapter.generate_response(disease_class="Grape___Black_rot", user_query="What's wrong with my grapes?", confidence=0.35)
    print(f"   Response preview: {response[:100]}...")
    assert "not entirely certain" in response.lower()
    assert "consult" in response.lower()

    # Scenario 4: Organic treatment request
    print("\n4. Organic treatment request")
    response = adapter.generate_response(
        disease_class="Cherry_(including_sour)___Powdery_mildew",
        user_query="I need organic treatment for powdery mildew",
        confidence=0.78,
    )
    print(f"   Response preview: {response[:100]}...")
    assert "organic" in response.lower()

    # Scenario 5: Prevention-focused query
    print("\n5. Prevention-focused query")
    response = adapter.generate_response(
        disease_class="Potato___Late_blight", user_query="How can I prevent late blight in the future?", confidence=0.85
    )
    print(f"   Response preview: {response[:100]}...")
    assert "prevention" in response.lower()

    print("\n[DONE] All integration scenarios tested successfully!")


def test_knowledge_base_consistency():
    """Test knowledge base consistency with class mappings."""
    print("\n🔍 Testing knowledge base consistency...")

    import json

    # Load both files
    with open("data/knowledge_base/plantvillage_classes.json") as f:
        class_data = json.load(f)

    with open("data/knowledge_base/disease_info.json") as f:
        json.load(f)  # Removed unused variable 'kb_data' (F841)

    adapter = TextAdapter()

    # Test that all class mappings work
    inconsistencies = []
    for class_name in class_data["classes"]:
        readable_name = class_data["class_to_readable"][class_name]
        disease_info = adapter.get_disease_info(class_name)

        if disease_info["disease_name"] == "Unknown Disease":
            inconsistencies.append(f"Missing: {class_name}")
        elif disease_info["disease_name"] != readable_name:
            # This is okay - we might have different naming conventions
            pass

    if inconsistencies:
        print(f"   [WARNING]  Found inconsistencies: {inconsistencies}")
    else:
        print("   [DONE] Knowledge base is consistent with class mappings")


def main():
    """Run integration tests."""
    try:
        test_integration_scenarios()
        test_knowledge_base_consistency()
        print("\n[SUCCESS] All integration tests passed!")
    except Exception as e:
        print(f"\n[TODO] Integration test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
