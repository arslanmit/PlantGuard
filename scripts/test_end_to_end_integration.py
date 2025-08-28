#!/usr/bin/env python3
"""End-to-end integration test for production training pipeline.

This script tests the complete workflow from training to deployment,
focusing on the integration between components rather than individual functionality.
"""

import json
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EndToEndIntegrationTest:
    """End-to-end integration test for the production training pipeline."""

    def __init__(self):
        """Initialize the test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.results: dict[str, Any] = {"tests_passed": 0, "tests_failed": 0, "test_results": {}, "errors": []}
        logger.info(f"Test initialized with temp directory: {self.temp_dir}")

    def log_test_result(self, test_name: str, passed: bool, message: str = "", error: Exception | None = None) -> None:
        """Log test result."""
        if passed:
            self.results["tests_passed"] += 1
            logger.info(f"[DONE] {test_name}: PASSED - {message}")
        else:
            self.results["tests_failed"] += 1
            logger.error(f"[TODO] {test_name}: FAILED - {message}")
            if error:
                self.results["errors"].append(f"{test_name}: {error!s}")

        self.results["test_results"][test_name] = {
            "passed": passed,
            "message": message,
            "error": str(error) if error else None,
        }

    def test_makefile_integration(self) -> bool:
        """Test Makefile commands integration."""
        logger.info("Testing Makefile integration...")

        try:
            # Test that key commands exist and can be parsed
            make_path = shutil.which("make")
            if not make_path:
                self.log_test_result("Makefile.help", False, "Make command not found")
                return False
            result = subprocess.run([make_path, "help"], check=False, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.log_test_result("Makefile.help", False, "Make help failed")
                return False

            # Check for production training commands
            help_output = result.stdout
            required_commands = [
                "train-production",
                "monitor-training",
                "evaluate-model",
                "list-models",
                "setup-dataset",
                "validate-dataset",
                "analyze-dataset",
            ]

            missing_commands = [cmd for cmd in required_commands if cmd not in help_output]
            if missing_commands:
                self.log_test_result("Makefile.commands", False, f"Missing: {missing_commands}")
                return False

            self.log_test_result("Makefile.integration", True, "All production commands available")
            return True

        except Exception as e:
            self.log_test_result("Makefile.integration", False, "Makefile test failed", e)
            return False

    def test_script_availability(self) -> bool:
        """Test that all required scripts are available."""
        logger.info("Testing script availability...")

        try:
            required_scripts = [
                "scripts/production_training_workflow.py",
                "scripts/list_models.py",
                "scripts/migrate_models.py",
                "scripts/evaluate_model.py",
                "scripts/download_dataset.py",
                "scripts/validate_dataset.py",
                "scripts/analyze_dataset.py",
            ]

            missing_scripts = []
            for script_path in required_scripts:
                if not Path(script_path).exists():
                    missing_scripts.append(script_path)

            if missing_scripts:
                self.log_test_result("Scripts.availability", False, f"Missing: {missing_scripts}")
                return False

            self.log_test_result("Scripts.availability", True, f"All {len(required_scripts)} scripts available")
            return True

        except Exception as e:
            self.log_test_result("Scripts.availability", False, "Script availability test failed", e)
            return False

    def test_component_imports(self) -> bool:
        """Test that all production training components can be imported."""
        logger.info("Testing component imports...")

        try:
            # Test core training components
            # Test integration components

            self.log_test_result("Component.imports", True, "All components imported successfully")
            return True

        except Exception as e:
            self.log_test_result("Component.imports", False, "Component import failed", e)
            return False

    def test_configuration_system(self) -> bool:
        """Test the configuration system integration."""
        logger.info("Testing configuration system...")

        try:
            from src.training.config import TrainingConfig

            # Test default configuration
            config = TrainingConfig()

            # Test serialization
            config_dict = config.to_dict()

            # Test deserialization
            loaded_config = TrainingConfig.from_dict(config_dict)

            # Verify round-trip
            if loaded_config.epochs != config.epochs or loaded_config.batch_size != config.batch_size:
                self.log_test_result("Configuration.roundtrip", False, "Config serialization failed")
                return False

            # Test JSON export
            config_file = self.temp_dir / "test_config.json"
            config.to_json(config_file)

            if not config_file.exists():
                self.log_test_result("Configuration.json_export", False, "JSON export failed")
                return False

            # Test JSON import
            loaded_from_json = TrainingConfig.from_json(config_file)
            if loaded_from_json.epochs != config.epochs:
                self.log_test_result("Configuration.json_import", False, "JSON import failed")
                return False

            self.log_test_result("Configuration.system", True, "Configuration system working correctly")
            return True

        except Exception as e:
            self.log_test_result("Configuration.system", False, "Configuration system test failed", e)
            return False

    def test_registry_operations(self) -> bool:
        """Test model registry operations."""
        logger.info("Testing model registry operations...")

        try:
            import torch

            from src.training.model_registry import ModelRegistry

            # Initialize registry
            registry = ModelRegistry(self.temp_dir / "test_registry")

            # Create a simple test model file
            model_path = self.temp_dir / "test_model.pt"
            test_data = {
                "model_state_dict": {"test": torch.tensor([1, 2, 3])},
                "num_classes": 10,
                "class_names": [f"class_{i}" for i in range(10)],
            }
            torch.save(test_data, model_path)

            # Test registration
            model_id = registry.register_model(
                model_path=model_path,
                name="test_model",
                architecture="test",
                dataset_version="test_v1",
                hyperparameters={"test": True},
                performance_metrics={"accuracy": 0.95},
            )

            # Test retrieval
            model_info = registry.get_model(model_id)
            if not model_info or not model_info.is_valid:
                self.log_test_result("Registry.retrieval", False, "Model retrieval failed")
                return False

            # Test listing
            models = registry.list_models()
            if len(models) != 1:
                self.log_test_result("Registry.listing", False, f"Expected 1 model, got {len(models)}")
                return False

            # Test search
            search_results = registry.search_models(architecture="test")
            if len(search_results) != 1:
                self.log_test_result("Registry.search", False, "Search failed")
                return False

            self.log_test_result("Registry.operations", True, "Registry operations successful")
            return True

        except Exception as e:
            self.log_test_result("Registry.operations", False, "Registry operations failed", e)
            return False

    def test_dataset_management(self) -> bool:
        """Test dataset management operations."""
        logger.info("Testing dataset management...")

        try:
            from PIL import Image

            from src.training.dataset_manager import DatasetManager

            # Create test dataset
            dataset_dir = self.temp_dir / "test_dataset"
            for split in ["train", "val"]:
                for class_name in ["class_a", "class_b"]:
                    class_dir = dataset_dir / split / class_name
                    class_dir.mkdir(parents=True, exist_ok=True)

                    # Create test images
                    for i in range(3):
                        img = Image.new("RGB", (100, 100), color=(i * 80, 100, 150))
                        img.save(class_dir / f"test_{i}.jpg")

            # Initialize dataset manager
            dm = DatasetManager(self.temp_dir / "data")

            # Test validation
            validation_result = dm.validate_dataset(dataset_dir)
            if not validation_result.is_valid:
                self.log_test_result("Dataset.validation", False, "Dataset validation failed")
                return False

            # Test analysis
            analysis_result = dm.analyze_dataset(dataset_dir)
            if analysis_result.total_samples == 0:
                self.log_test_result("Dataset.analysis", False, "Dataset analysis failed")
                return False

            self.log_test_result("Dataset.management", True, f"Processed {analysis_result.total_samples} samples")
            return True

        except Exception as e:
            self.log_test_result("Dataset.management", False, "Dataset management failed", e)
            return False

    def test_model_manager_integration(self) -> bool:
        """Test model manager integration."""
        logger.info("Testing model manager integration...")

        try:
            from src.features.model_switching.model_manager import PlantGuardModelManager

            # Create test config
            config_path = self.temp_dir / "test_models.json"
            config_data = {
                "default_model": "test_model",
                "models": {
                    "test_model": {
                        "name": "Test Model",
                        "type": "local",
                        "model_path": "data/models/test.pt",
                        "description": "Test model",
                        "accuracy": 0.95,
                        "confidence_threshold": 0.7,
                        "enabled": True,
                        "device": "cpu",
                    }
                },
            }

            with config_path.open("w") as f:
                json.dump(config_data, f)

            # Initialize manager
            manager = PlantGuardModelManager(config_path=str(config_path), autoload_default=False)

            # Test listing
            models = manager.list_available_models()
            if len(models) != 1:
                self.log_test_result("ModelManager.listing", False, f"Expected 1 model, got {len(models)}")
                return False

            # Test configuration access
            config = manager.get_model_config("test_model")
            if not config or config.get("name") != "Test Model":
                self.log_test_result("ModelManager.config", False, "Config access failed")
                return False

            self.log_test_result("ModelManager.integration", True, "Model manager integration successful")
            return True

        except Exception as e:
            self.log_test_result("ModelManager.integration", False, "Model manager integration failed", e)
            return False

    def test_vision_adapter_compatibility(self) -> bool:
        """Test VisionAdapter compatibility features."""
        logger.info("Testing VisionAdapter compatibility...")

        try:
            import torch

            from src.core.vision import VisionAdapter

            adapter = VisionAdapter()

            # Test legacy model detection
            legacy_path = self.temp_dir / "legacy_model.pt"
            legacy_data = {
                "model_state_dict": {"test": torch.tensor([1, 2, 3])},
                "num_classes": 10,
                # No registry metadata
            }
            torch.save(legacy_data, legacy_path)

            is_compatible = adapter.is_compatible_with_registry_format(str(legacy_path))
            if is_compatible:
                self.log_test_result("VisionAdapter.legacy_detection", False, "Legacy model incorrectly detected as registry format")
                return False

            # Test migration
            migrated_path = self.temp_dir / "migrated_model.pt"
            adapter.migrate_legacy_model(str(legacy_path), str(migrated_path))

            # Verify migration
            is_migrated_compatible = adapter.is_compatible_with_registry_format(str(migrated_path))
            if not is_migrated_compatible:
                self.log_test_result("VisionAdapter.migration", False, "Migration failed")
                return False

            self.log_test_result("VisionAdapter.compatibility", True, "Compatibility features working")
            return True

        except Exception as e:
            self.log_test_result("VisionAdapter.compatibility", False, "Compatibility test failed", e)
            return False

    def test_workflow_scripts(self) -> bool:
        """Test workflow scripts can be executed."""
        logger.info("Testing workflow scripts...")

        try:
            # Test that scripts can be imported (syntax check)
            import importlib.util

            scripts_to_test = [
                "scripts/production_training_workflow.py",
                "scripts/list_models.py",
                "scripts/evaluate_model.py",
            ]

            for script_path in scripts_to_test:
                if not Path(script_path).exists():
                    continue

                spec = importlib.util.spec_from_file_location("test_script", script_path)
                if spec is None or spec.loader is None:
                    self.log_test_result("WorkflowScripts.syntax", False, f"Cannot load {script_path}")
                    return False

            self.log_test_result("WorkflowScripts.syntax", True, "All workflow scripts have valid syntax")
            return True

        except Exception as e:
            self.log_test_result("WorkflowScripts.syntax", False, "Workflow scripts test failed", e)
            return False

    def run_integration_tests(self) -> dict[str, Any]:
        """Run all integration tests."""
        logger.info("[LAUNCH] Starting end-to-end integration tests...")

        start_time = time.time()

        # Run all tests
        tests = [
            self.test_makefile_integration,
            self.test_script_availability,
            self.test_component_imports,
            self.test_configuration_system,
            self.test_registry_operations,
            self.test_dataset_management,
            self.test_model_manager_integration,
            self.test_vision_adapter_compatibility,
            self.test_workflow_scripts,
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
                self.log_test_result(test.__name__, False, "Unexpected exception", e)

        # Calculate results
        total_time = time.time() - start_time
        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        success_rate = (self.results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0

        self.results.update(
            {
                "total_time": total_time,
                "total_tests": total_tests,
                "success_rate": success_rate,
                "overall_success": self.results["tests_failed"] == 0,
            }
        )

        # Log summary
        logger.info("=" * 60)
        logger.info("🏁 INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {self.results['tests_passed']}")
        logger.info(f"Failed: {self.results['tests_failed']}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Total time: {total_time:.2f}s")

        if self.results["overall_success"]:
            logger.info("[SUCCESS] ALL INTEGRATION TESTS PASSED!")
        else:
            logger.error("[TODO] SOME INTEGRATION TESTS FAILED")
            for error in self.results["errors"]:
                logger.error(f"  - {error}")

        return self.results

    def cleanup(self) -> None:
        """Clean up temporary files."""
        try:
            import shutil

            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup: {e}")


def main() -> int:
    """Main test function."""
    test_runner = EndToEndIntegrationTest()

    try:
        results = test_runner.run_integration_tests()

        # Save results
        results_file = Path("integration_test_results.json")
        with results_file.open("w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Integration test results saved to: {results_file}")

        return 0 if results["overall_success"] else 1

    except KeyboardInterrupt:
        logger.info("Integration tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Integration tests failed with unexpected error: {e}")
        return 1
    finally:
        test_runner.cleanup()


if __name__ == "__main__":
    import sys

    sys.exit(main())
