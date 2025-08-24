#!/usr/bin/env python3
"""
Test script for the unified PlantGuard interface.

This script validates that the new unified interface can:
1. Import all necessary modules
2. Initialize without errors
3. Handle basic functionality without full dependencies
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_imports():
    """Test that all required imports work."""
    print("🧪 Testing imports...")

    try:
        from ui.unified_app import UnifiedPlantGuardApp

        print("✅ Unified app import successful")
    except ImportError as e:
        print(f"❌ Unified app import failed: {e}")
        return False

    try:
        from adapters_compat import AudioAdapter, TextAdapter, VisionAdapter

        print("✅ Compatibility adapters import successful")
    except ImportError as e:
        print(f"❌ Compatibility adapters import failed: {e}")
        return False

    return True


def test_app_initialization():
    """Test that the app can be initialized."""
    print("\n🧪 Testing app initialization...")

    try:
        from ui.unified_app import UnifiedPlantGuardApp

        app = UnifiedPlantGuardApp()
        print("✅ App initialization successful")
        return True
    except Exception as e:
        print(f"❌ App initialization failed: {e}")
        return False


def test_mock_adapters():
    """Test that mock adapters work correctly."""
    print("\n🧪 Testing mock adapters...")

    try:
        from PIL import Image

        from adapters_compat import TextAdapter, VisionAdapter

        # Test Vision Adapter
        vision_adapter = VisionAdapter()

        # Create a simple test image
        test_image = Image.new("RGB", (224, 224), color="green")
        disease, confidence = vision_adapter.predict(test_image)

        print(f"✅ Vision adapter test: {disease} ({confidence:.1%})")

        # Test Text Adapter
        text_adapter = TextAdapter()
        response = text_adapter.generate_response(user_query="What causes plant diseases?")

        print(f"✅ Text adapter test: {len(response)} characters response")

        return True

    except Exception as e:
        print(f"❌ Mock adapter test failed: {e}")
        return False


def test_entry_point():
    """Test that the entry point script works."""
    print("\n🧪 Testing entry point...")

    try:
        import plantguard_unified

        print("✅ Entry point import successful")
        return True
    except ImportError as e:
        print(f"❌ Entry point import failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🌿 PlantGuard Unified Interface Test Suite")
    print("=" * 50)

    tests = [
        ("Module Imports", test_imports),
        ("App Initialization", test_app_initialization),
        ("Mock Adapters", test_mock_adapters),
        ("Entry Point", test_entry_point),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"💥 {test_name} test failed")
        except Exception as e:
            print(f"💥 {test_name} test crashed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Unified interface is ready to use.")
        print("\n💡 To launch the unified interface:")
        print("   make run-unified")
        print("   # or simply:")
        print("   make run")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
