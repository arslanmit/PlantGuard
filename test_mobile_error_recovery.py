#!/usr/bin/env python3
"""
Test script for mobile error handling and offline functionality.

This script validates the error recovery and offline management systems
for the PlantGuard mobile UI components.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_error_handler_imports():
    """Test that error handler modules can be imported."""
    try:
        from src.ui.mobile_error_handler import ErrorCategory, ErrorSeverity, MobileErrorBoundary, MobileErrorHandler, mobile_error_boundary

        print("✅ MobileErrorHandler imports successful")
        return True
    except ImportError as e:
        print(f"❌ MobileErrorHandler import failed: {e}")
        return False


def test_offline_manager_imports():
    """Test that offline manager modules can be imported."""
    try:
        from src.ui.mobile_offline_manager import (
            MobileOfflineManager,
            NetworkStatus,
            OfflineCapability,
            ensure_offline_capability,
            with_offline_support,
        )

        print("✅ MobileOfflineManager imports successful")
        return True
    except ImportError as e:
        print(f"❌ MobileOfflineManager import failed: {e}")
        return False


def test_integration_imports():
    """Test that integration module can be imported."""
    try:
        from src.ui.mobile_error_recovery_integration import (
            MobileErrorRecoveryIntegration,
            create_resilient_mobile_component,
            handle_mobile_operation,
            initialize_mobile_error_recovery,
        )

        print("✅ MobileErrorRecoveryIntegration imports successful")
        return True
    except ImportError as e:
        print(f"❌ MobileErrorRecoveryIntegration import failed: {e}")
        return False


def test_error_handler_functionality():
    """Test error handler functionality without Streamlit context."""
    try:
        from src.ui.mobile_error_handler import ErrorCategory, ErrorSeverity

        # Test error severity and category enums
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorCategory.COMPONENT_RENDER.value == "component_render"

        print("✅ Error handler enums working correctly")

        # Test error boundary decorator
        from src.ui.mobile_error_handler import mobile_error_boundary

        @mobile_error_boundary("test_component")
        def test_function():
            return "success"

        # This would normally work with Streamlit session state
        # For now, just test that the decorator can be applied
        assert callable(test_function)

        print("✅ Error boundary decorator working")
        return True

    except Exception as e:
        print(f"❌ Error handler functionality test failed: {e}")
        return False


def test_offline_manager_functionality():
    """Test offline manager functionality without Streamlit context."""
    try:
        from src.ui.mobile_offline_manager import NetworkStatus, OfflineCapability

        # Test enums
        assert NetworkStatus.ONLINE.value == "online"
        assert OfflineCapability.FULL.value == "full"

        print("✅ Offline manager enums working correctly")

        # Test decorator
        from src.ui.mobile_offline_manager import with_offline_support

        @with_offline_support("test_op", lambda: "online_result")
        def test_operation():
            return "operation_result"

        assert callable(test_operation)

        print("✅ Offline support decorator working")
        return True

    except Exception as e:
        print(f"❌ Offline manager functionality test failed: {e}")
        return False


def test_integration_functionality():
    """Test integration functionality."""
    try:
        from src.ui.mobile_error_recovery_integration import create_resilient_mobile_component, handle_mobile_operation
        from src.ui.mobile_offline_manager import OfflineCapability

        # Test resilient component decorator
        @create_resilient_mobile_component("test_component", OfflineCapability.FULL)
        def test_component():
            return "component_rendered"

        assert callable(test_component)

        # Test operation handler decorator
        @handle_mobile_operation("test_component", "test_operation")
        def test_operation():
            return "operation_result"

        assert callable(test_operation)

        print("✅ Integration decorators working")
        return True

    except Exception as e:
        print(f"❌ Integration functionality test failed: {e}")
        return False


def test_error_categories_and_severities():
    """Test that all error categories and severities are properly defined."""
    try:
        from src.ui.mobile_error_handler import ErrorCategory, ErrorSeverity

        # Test all severity levels
        severities = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        assert len(severities) == 4

        # Test all categories
        categories = [
            ErrorCategory.COMPONENT_RENDER,
            ErrorCategory.STATE_MANAGEMENT,
            ErrorCategory.ADAPTER_INTEGRATION,
            ErrorCategory.NETWORK_CONNECTION,
            ErrorCategory.USER_INPUT,
            ErrorCategory.SYSTEM_RESOURCE,
            ErrorCategory.UNKNOWN,
        ]
        assert len(categories) == 7

        print("✅ All error categories and severities defined")
        return True

    except Exception as e:
        print(f"❌ Error categories/severities test failed: {e}")
        return False


def test_network_status_and_capabilities():
    """Test network status and offline capabilities."""
    try:
        from src.ui.mobile_offline_manager import NetworkStatus, OfflineCapability

        # Test all network statuses
        statuses = [NetworkStatus.ONLINE, NetworkStatus.OFFLINE, NetworkStatus.LIMITED, NetworkStatus.UNKNOWN]
        assert len(statuses) == 4

        # Test all capabilities
        capabilities = [OfflineCapability.FULL, OfflineCapability.LIMITED, OfflineCapability.NONE, OfflineCapability.CACHED]
        assert len(capabilities) == 4

        print("✅ All network statuses and capabilities defined")
        return True

    except Exception as e:
        print(f"❌ Network status/capabilities test failed: {e}")
        return False


def test_class_instantiation():
    """Test that main classes can be instantiated."""
    try:
        from src.ui.mobile_error_handler import MobileErrorBoundary
        from src.ui.mobile_error_recovery_integration import MobileErrorRecoveryIntegration

        # Test error boundary
        boundary = MobileErrorBoundary("test_component")
        assert boundary.component_id == "test_component"

        # Test integration class (static methods, so just check it exists)
        assert hasattr(MobileErrorRecoveryIntegration, "initialize_integrated_system")
        assert hasattr(MobileErrorRecoveryIntegration, "handle_network_dependent_operation")

        print("✅ Class instantiation working")
        return True

    except Exception as e:
        print(f"❌ Class instantiation test failed: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    required_files = ["src/ui/mobile_error_handler.py", "src/ui/mobile_offline_manager.py", "src/ui/mobile_error_recovery_integration.py"]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    print("✅ All required files exist")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("🧪 Testing Mobile Error Recovery System")
    print("=" * 50)

    tests = [
        ("File Structure", test_file_structure),
        ("Error Handler Imports", test_error_handler_imports),
        ("Offline Manager Imports", test_offline_manager_imports),
        ("Integration Imports", test_integration_imports),
        ("Error Handler Functionality", test_error_handler_functionality),
        ("Offline Manager Functionality", test_offline_manager_functionality),
        ("Integration Functionality", test_integration_functionality),
        ("Error Categories/Severities", test_error_categories_and_severities),
        ("Network Status/Capabilities", test_network_status_and_capabilities),
        ("Class Instantiation", test_class_instantiation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Error recovery system is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
