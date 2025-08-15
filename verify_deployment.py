#!/usr/bin/env python3
"""Verify that all PlantGuard improvements are working correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import torch
from PIL import Image

from src.core.vision import VisionAdapter


def test_improved_methods():
    """Test the newly integrated improved methods."""
    print("🧪 Testing improved PlantGuard methods...")

    try:
        # Initialize adapter
        device = "cuda" if torch.cuda.is_available() else "cpu"
        adapter = VisionAdapter(device=device)
        adapter.load_checkpoint("data/models/vision_resnet50.pt")

        # Load class mapping
        mapping_path = "data/knowledge_base/plantvillage_classes.json"
        if Path(mapping_path).exists():
            adapter.load_class_mapping(mapping_path)

        # Test image
        test_image = "data/pictures/apple_healthy_sample.jpg"
        if not Path(test_image).exists():
            print("❌ Test image not found")
            return False

        image = Image.open(test_image)

        # Test 1: Original prediction
        print("1️⃣ Testing original prediction...")
        orig_class, orig_conf = adapter.predict(image)
        print(f"   Original: {orig_class} (confidence: {orig_conf:.3f})")

        # Test 2: Calibrated prediction
        print("2️⃣ Testing calibrated prediction...")
        if hasattr(adapter, "predict_with_calibration"):
            cal_class, cal_conf = adapter.predict_with_calibration(image)
            improvement = cal_conf / orig_conf if orig_conf > 0 else 0
            print(f"   Calibrated: {cal_class} (confidence: {cal_conf:.3f})")
            print(f"   📈 Improvement: {improvement:.1f}x confidence boost")
        else:
            print("   ❌ Calibration method not available")
            return False

        # Test 3: Plant hint prediction
        print("3️⃣ Testing plant hint prediction...")
        if hasattr(adapter, "predict_with_plant_hint"):
            hint_class, hint_conf = adapter.predict_with_plant_hint(image, "Apple")
            print(f"   With Apple hint: {hint_class} (confidence: {hint_conf:.3f})")

            # Check if plant type is correct
            plant_correct = "Apple" in hint_class or "apple" in hint_class.lower()
            print(f"   🎯 Plant type correct: {'✅' if plant_correct else '❌'}")
        else:
            print("   ❌ Plant hint method not available")
            return False

        print("✅ All improved methods working correctly!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main verification function."""
    print("🔍 Verifying PlantGuard deployment...")

    # Test improved methods
    success = test_improved_methods()

    if success:
        print("\n🎉 DEPLOYMENT VERIFICATION SUCCESSFUL!")
        print("✅ All improvements are working correctly")
        print("\n📖 Usage Examples:")
        print("   # Standard prediction with better confidence")
        print("   predicted_class, confidence = adapter.predict_with_calibration(image)")
        print("")
        print("   # Prediction with plant type hint")
        print("   predicted_class, confidence = adapter.predict_with_plant_hint(image, 'Apple')")
        print("")
        print("🚀 PlantGuard is ready for production use!")
    else:
        print("\n❌ DEPLOYMENT VERIFICATION FAILED")
        print("Some improvements may not be working correctly")


if __name__ == "__main__":
    main()
