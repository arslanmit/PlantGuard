#!/usr/bin/env python3
"""
Test script for mobile app optimization enhancements.

This script tests the enhanced mobile functionality including:
- Core adapter integration
- Performance optimization
- Enhanced UI features
- Mobile-only system validation
"""


import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_mobile_app_imports() -> None:
    """Test that all mobile app imports work correctly."""
    print("[TEST] Testing mobile app imports...")

    try:
        # Test mobile app import
        import mobile_spa_app

        print("[PASS] mobile_spa_app imported successfully")

        # Test core function
        framework = mobile_spa_app.get_ai_testing_framework()
        print("[PASS] AI testing framework created successfully")

        # Test adapter loading function
        adapters = mobile_spa_app.load_core_adapters()
        print("[PASS] Core adapters loading function works")

        return True

    except Exception as e:
        print(f"[FAIL] Import test failed: {e}")
        return False


def test_mobile_app_class() -> None:
    """Test mobile app class initialization."""
    print("\n[TEST] Testing mobile app class...")

    try:
        import mobile_spa_app

        # Create app instance (without Streamlit context)
        app = mobile_spa_app.MobilePlantGuardApp()
        print("[PASS] MobilePlantGuardApp created successfully")

        # Test method existence
        methods_to_test = [
            "_load_core_adapters",
            "_initialize_performance_optimization",
            "analyze_image_with_adapters",
            "process_voice_input",
            "process_text_query",
            "render_performance_status",
        ]

        for method_name in methods_to_test:
            if hasattr(app, method_name):
                print(f"[PASS] Method {method_name} exists")
            else:
                print(f"[FAIL] Method {method_name} missing")
                return False

        return True

    except Exception as e:
        print(f"[FAIL] Class test failed: {e}")
        return False


def test_performance_optimizer() -> None:
    """Test performance optimizer integration."""
    print("\n[TEST] Testing performance optimizer...")

    try:
        from ui.components.mobile_performance_optimizer import mobile_performance_optimizer

        # Test basic functionality
        report = mobile_performance_optimizer.get_performance_report()
        print("[PASS] Performance report generated")

        # Test cache functionality
        cache_stats = mobile_performance_optimizer.cache.get_stats()
        print("[PASS] Cache statistics available")

        # Test memory manager
        memory_stats = mobile_performance_optimizer.memory_manager.get_memory_usage()
        print("[DONE] Memory statistics available")

        return True

    except Exception as e:
        print(f"[TODO] Performance optimizer test failed: {e}")
        return False


def test_core_adapters() -> None:
    """Test core adapter functionality."""
    print("\n[TEST] Testing core adapters...")

    try:
        from core.audio import AudioAdapter
        from core.nlp import TextAdapter
        from core.vision import VisionAdapter

        # Test adapter creation
        vision = VisionAdapter(lazy_load=True)
        audio = AudioAdapter()
        text = TextAdapter()

        print("[DONE] All core adapters created successfully")

        # Test basic methods exist
        assert hasattr(vision, "predict"), "Vision adapter missing predict method"
        assert hasattr(audio, "transcribe"), "Audio adapter missing transcribe method"
        assert hasattr(text, "generate_response"), "Text adapter missing generate_response method"

        print("[DONE] All required methods exist")

        return True

    except Exception as e:
        print(f"[TODO] Core adapters test failed: {e}")
        return False


def main() -> None:
    """Run all tests."""
    print("[LAUNCH] Starting mobile app optimization tests...\n")

    tests = [test_mobile_app_imports, test_mobile_app_class, test_performance_optimizer, test_core_adapters]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n[SUMMARY] Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All tests passed! Mobile app optimization is working correctly.")
        return True
    else:
        print("[TODO] Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
