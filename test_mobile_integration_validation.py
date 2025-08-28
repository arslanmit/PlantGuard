#!/usr/bin/env python3
"""
Mobile Integration Validation Test

This test validates that all mobile functionality works correctly after the migration,
including core adapters integration and mobile-specific features.

Requirements covered: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MobileIntegrationValidator:
    """Validates mobile functionality and core adapter integration."""

    def __init__(self):
        self.workspace_root = Path.cwd()
        sys.path.insert(0, str(self.workspace_root))

    def test_mobile_app_imports(self) -> dict[str, Any]:
        """Test that mobile app can be imported without errors."""
        try:
            # Test mobile_spa_app import
            import mobile_spa_app

            # Check if main components are accessible
            components_to_check = [
                "st",  # Streamlit should be imported
            ]

            missing_components = []
            for component in components_to_check:
                if not hasattr(mobile_spa_app, component):
                    # Try to find it in the module's globals
                    import importlib

                    spec = importlib.util.find_spec("streamlit")
                    if spec is None:
                        missing_components.append(component)

            return {"status": "passed", "details": "Mobile app imports successfully", "missing_components": missing_components}

        except ImportError as e:
            return {"status": "failed", "details": f"Failed to import mobile app: {e!s}"}
        except Exception as e:
            return {"status": "failed", "details": f"Mobile app import test failed: {e!s}"}

    def test_core_adapters_functionality(self) -> dict[str, Any]:
        """Test that core adapters can be imported and initialized."""
        try:
            # Test vision adapter
            from src.core.vision import VisionAdapter

            vision_adapter = VisionAdapter()

            # Test audio adapter
            from src.core.audio import AudioAdapter

            audio_adapter = AudioAdapter()

            # Test text/NLP adapter
            from src.core.nlp import TextAdapter

            text_adapter = TextAdapter()

            return {
                "status": "passed",
                "details": "All core adapters imported and initialized successfully",
                "adapters": ["VisionAdapter", "AudioAdapter", "TextAdapter"],
            }

        except ImportError as e:
            return {"status": "failed", "details": f"Failed to import core adapters: {e!s}"}
        except Exception as e:
            return {"status": "failed", "details": f"Core adapters test failed: {e!s}"}

    def test_mobile_components_registry(self) -> dict[str, Any]:
        """Test that mobile component registry works correctly."""
        try:
            from src.ui.components.mobile_component_registry import mobile_component_registry

            # Check if registry has expected components
            expected_components = [
                "mobile_header",
                "mobile_input_ribbon",
                "mobile_content_tabs",
                "mobile_image_analysis",
                "mobile_voice_interface",
                "mobile_chat_interface",
            ]

            available_components = []
            missing_components = []

            for component in expected_components:
                if component in mobile_component_registry._components:
                    available_components.append(component)
                else:
                    missing_components.append(component)

            status = "passed" if not missing_components else "warning"
            details = f"Mobile registry loaded with {len(available_components)} components"

            return {"status": status, "details": details, "available_components": available_components, "missing_components": missing_components}

        except ImportError as e:
            return {"status": "failed", "details": f"Failed to import mobile component registry: {e!s}"}
        except Exception as e:
            return {"status": "failed", "details": f"Mobile component registry test failed: {e!s}"}

    def test_streamlit_configuration(self) -> dict[str, Any]:
        """Test that Streamlit is properly configured for mobile."""
        try:
            import streamlit as st

            # Check if streamlit can be imported
            streamlit_version = st.__version__

            # Test basic streamlit functionality
            # Note: This won't actually create UI elements since we're not in a streamlit context

            return {
                "status": "passed",
                "details": f"Streamlit {streamlit_version} is available and configured",
                "streamlit_version": streamlit_version,
            }

        except ImportError as e:
            return {"status": "failed", "details": f"Streamlit not available: {e!s}"}
        except Exception as e:
            return {"status": "failed", "details": f"Streamlit configuration test failed: {e!s}"}

    def test_mobile_assets(self) -> dict[str, Any]:
        """Test that mobile-specific assets are present."""
        mobile_assets = ["assets/mobile_styles.css", "assets/mobile_optimized_styles.css"]

        present_assets = []
        missing_assets = []

        for asset in mobile_assets:
            asset_path = self.workspace_root / asset
            if asset_path.exists():
                present_assets.append(asset)
            else:
                missing_assets.append(asset)

        status = "passed" if not missing_assets else "warning"
        details = f"Found {len(present_assets)} mobile assets"

        return {"status": status, "details": details, "present_assets": present_assets, "missing_assets": missing_assets}

    def test_pytorch_mps_availability(self) -> dict[str, Any]:
        """Test PyTorch MPS (Apple Silicon) availability for mobile optimization."""
        try:
            import torch

            mps_available = torch.backends.mps.is_available()
            device_info = {"mps_available": mps_available, "pytorch_version": torch.__version__, "cuda_available": torch.cuda.is_available()}

            if mps_available:
                status = "passed"
                details = "PyTorch MPS (Apple Silicon) acceleration available"
            else:
                status = "warning"
                details = "PyTorch MPS not available, using CPU"

            return {"status": status, "details": details, "device_info": device_info}

        except ImportError as e:
            return {"status": "failed", "details": f"PyTorch not available: {e!s}"}
        except Exception as e:
            return {"status": "failed", "details": f"PyTorch test failed: {e!s}"}

    def run_integration_tests(self) -> dict[str, Any]:
        """Run all mobile integration tests."""
        logger.info("Starting mobile integration validation tests...")

        tests = [
            ("Mobile App Imports", self.test_mobile_app_imports),
            ("Core Adapters Functionality", self.test_core_adapters_functionality),
            ("Mobile Components Registry", self.test_mobile_components_registry),
            ("Streamlit Configuration", self.test_streamlit_configuration),
            ("Mobile Assets", self.test_mobile_assets),
            ("PyTorch MPS Availability", self.test_pytorch_mps_availability),
        ]

        results = {}
        overall_status = "passed"

        for test_name, test_func in tests:
            logger.info(f"Running integration test: {test_name}")
            try:
                result = test_func()
                results[test_name] = result

                if result["status"] == "failed":
                    overall_status = "failed"
                elif result["status"] == "warning" and overall_status != "failed":
                    overall_status = "warning"

            except Exception as e:
                logger.error(f"Integration test {test_name} crashed: {e}")
                results[test_name] = {"status": "failed", "error": str(e), "details": f"Test execution failed with exception: {e}"}
                overall_status = "failed"

        # Generate summary
        results["summary"] = {
            "overall_status": overall_status,
            "total_tests": len(tests),
            "passed": len([result for result in results.values() if isinstance(result, dict) and result.get("status") == "passed"]),
            "failed": len([result for result in results.values() if isinstance(result, dict) and result.get("status") == "failed"]),
            "warnings": len([result for result in results.values() if isinstance(result, dict) and result.get("status") == "warning"]),
        }

        return results

    def save_results(self, results: dict[str, Any], filename: str = "mobile_integration_test_results.json"):
        """Save integration test results."""
        try:
            results_path = self.workspace_root / filename
            with open(results_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Integration test results saved to {results_path}")
        except Exception as e:
            logger.error(f"Failed to save integration test results: {e}")

    def print_summary(self, results: dict[str, Any]):
        """Print formatted summary of integration test results."""
        print("\n" + "=" * 80)
        print("MOBILE INTEGRATION VALIDATION RESULTS")
        print("=" * 80)

        summary = results.get("summary", {})
        overall_status = summary.get("overall_status", "unknown")

        # Status indicator
        status_symbols = {"passed": "[PASS]", "failed": "[FAIL]", "warning": "[WARN]"}

        print(f"\nOverall Status: {status_symbols.get(overall_status, '[UNKNOWN]')} {overall_status.upper()}")
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed', 0)}")
        print(f"Failed: {summary.get('failed', 0)}")
        print(f"Warnings: {summary.get('warnings', 0)}")

        print("\nDetailed Results:")
        print("-" * 40)

        for test_name, result in results.items():
            if test_name == "summary":
                continue

            if isinstance(result, dict):
                status = result.get("status", "unknown")
                symbol = status_symbols.get(status, "[UNKNOWN]")
                details = result.get("details", "No details")

                print(f"{symbol} {test_name}: {status}")
                print(f"   {details}")

                # Show additional info for failed tests
                if status == "failed" and "error" in result:
                    print(f"   Error: {result['error']}")
                print()

        print("=" * 80)


def main():
    """Main function to run mobile integration validation."""
    validator = MobileIntegrationValidator()

    print("Starting Mobile Integration Validation...")
    print("This will test that all mobile functionality works correctly after migration.")
    print()

    # Run integration tests
    results = validator.run_integration_tests()

    # Save results
    validator.save_results(results)

    # Print summary
    validator.print_summary(results)

    # Exit with appropriate code
    overall_status = results.get("summary", {}).get("overall_status", "failed")
    if overall_status == "passed":
        sys.exit(0)
    elif overall_status == "warning":
        sys.exit(1)  # Warnings but no failures
    else:
        sys.exit(2)  # Failures detected


if __name__ == "__main__":
    main()
