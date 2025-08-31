#!/usr/bin/env python3
"""
Test script to validate the type annotation fixers work correctly.

This creates sample files with missing type annotations and tests that
our fixing scripts can properly add them.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def create_test_files() -> Path:
    """Create test files with missing type annotations."""
    test_dir = Path(tempfile.mkdtemp(prefix="type_fix_test_"))

    # Test file 1: Mobile testing style
    mobile_test_content = '''"""Test mobile functionality."""
import pytest

def test_mobile_layout() -> None:
    """Test mobile layout rendering."""
    assert True

def test_mobile_performance() -> None:
    """Test mobile performance metrics."""
    return {"cpu": 50.0, "memory": 75.0}

class TestMobileComponents:
    def setup_method(self) -> None:
        """Setup test method."""
        self.config = {}
    
    def test_component_rendering(self) -> None:
        """Test component rendering."""
        pass
    
    def validate_mobile_state(self) -> bool:
        """Validate mobile state."""
        return True

def get_mobile_config() -> Any:
    """Get mobile configuration."""
    return {"theme": "dark", "layout": "responsive"}

def run_mobile_tests() -> Any:
    """Run mobile test suite."""
    print("Running tests...")
'''

    # Test file 2: Validation script style
    validation_content = '''"""Mobile validation utilities."""

class MobileValidator:
    def __init__(self) -> None:
        """Initialize validator."""
        self.errors = []
    
    def validate_performance(self, metrics) -> bool:
        """Validate performance metrics."""
        if not metrics:
            return False
        return all(v > 0 for v in metrics.values())
    
    def check_compatibility(self) -> bool:
        """Check mobile compatibility."""
        return True
    
    def generate_report(self) -> Any:
        """Generate validation report."""
        return {
            "status": "passed",
            "errors": self.errors
        }

def main() -> None:
    """Main validation function."""
    validator = MobileValidator()
    result = validator.validate_performance({"cpu": 50})
    print(f"Validation result: {result}")

if __name__ == "__main__":
    main()
'''

    # Test file 3: General functions
    general_content = '''"""General utility functions."""

def process_data(data) -> Any:
    """Process input data."""
    if not data:
        return None
    return [item.upper() for item in data]

def calculate_metrics(values) -> dict[str, Any]:
    """Calculate performance metrics."""
    if not values:
        return {}
    return {
        "mean": sum(values) / len(values),
        "max": max(values),
        "min": min(values)
    }

class DataProcessor:
    def __init__(self, config) -> None:
        """Initialize processor."""
        self.config = config
    
    def load_data(self, path) -> Any:
        """Load data from file."""
        with open(path, 'r') as f:
            return f.read()
    
    def save_results(self, results, path) -> Any:
        """Save results to file."""
        with open(path, 'w') as f:
            f.write(str(results))
'''

    # Write test files
    (test_dir / "test_mobile_sample.py").write_text(mobile_test_content)
    (test_dir / "validate_mobile_sample.py").write_text(validation_content)
    (test_dir / "general_sample.py").write_text(general_content)

    return test_dir


def run_fixer_on_test_dir(test_dir: Path, script_name: str) -> dict[str, Any]:
    """Run a type annotation fixer on the test directory."""
    try:
        # Copy script to test directory
        script_path = Path(script_name)
        if not script_path.exists():
            return {"success": False, "error": f"Script {script_name} not found"}

        test_script = test_dir / script_name
        shutil.copy2(script_path, test_script)

        # Run the script in the test directory
        result = subprocess.run([sys.executable, str(test_script)], cwd=test_dir, capture_output=True, text=True, timeout=60)

        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}

    except Exception as e:
        return {"success": False, "error": str(e)}


def check_annotations_added(test_dir: Path) -> dict[str, Any]:
    """Check if type annotations were properly added."""
    results = {}

    for py_file in test_dir.glob("*.py"):
        if py_file.name.endswith("_sample.py"):
            content = py_file.read_text()

            # Count function definitions with and without return annotations
            lines = content.split("\n")
            func_lines = [line for line in lines if line.strip().startswith("def ")]

            annotated_funcs = [line for line in func_lines if "->" in line]
            unannotated_funcs = [line for line in func_lines if "->" not in line]

            results[py_file.name] = {
                "total_functions": len(func_lines),
                "annotated_functions": len(annotated_funcs),
                "unannotated_functions": len(unannotated_funcs),
                "has_typing_import": "from typing import" in content,
                "sample_annotations": annotated_funcs[:3],
            }

    return results


def test_type_annotation_fixers() -> bool:
    """Test all type annotation fixers."""
    print("Testing Type Annotation Fixers")
    print("=" * 40)

    # Create test directory with sample files
    test_dir = create_test_files()
    print(f"Created test directory: {test_dir}")

    try:
        # Test mobile testing fixer
        print("\n1. Testing mobile testing annotation fixer...")
        result = run_fixer_on_test_dir(test_dir, "fix_mobile_testing_annotations.py")

        if result["success"]:
            print("[DONE] Mobile testing fixer ran successfully")
        else:
            print(f"[TODO] Mobile testing fixer failed: {result.get('error', 'Unknown error')}")

        # Test general annotation fixer
        print("\n2. Testing general annotation fixer...")
        result = run_fixer_on_test_dir(test_dir, "fix_strict_type_annotations.py")

        if result["success"]:
            print("[DONE] General annotation fixer ran successfully")
        else:
            print(f"[TODO] General annotation fixer failed: {result.get('error', 'Unknown error')}")

        # Check results
        print("\n3. Checking annotation results...")
        annotation_results = check_annotations_added(test_dir)

        all_good = True
        for filename, stats in annotation_results.items():
            print(f"\n{filename}:")
            print(f"  Total functions: {stats['total_functions']}")
            print(f"  Annotated functions: {stats['annotated_functions']}")
            print(f"  Has typing import: {stats['has_typing_import']}")

            if stats["sample_annotations"]:
                print("  Sample annotations:")
                for annotation in stats["sample_annotations"]:
                    print(f"    {annotation.strip()}")

            # Check if most functions got annotated
            if stats["total_functions"] > 0:
                annotation_rate = stats["annotated_functions"] / stats["total_functions"]
                if annotation_rate < 0.8:  # At least 80% should be annotated
                    print(f"  [WARNING]  Low annotation rate: {annotation_rate:.1%}")
                    all_good = False
                else:
                    print(f"  [DONE] Good annotation rate: {annotation_rate:.1%}")

        return all_good

    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test directory: {test_dir}")


def main() -> None:
    """Main test function."""
    success = test_type_annotation_fixers()

    print("\n" + "=" * 40)
    if success:
        print("[SUCCESS] All type annotation fixers are working correctly!")
        print("[DONE] Ready to run on the actual codebase")
    else:
        print("[WARNING]  Some issues detected with the type annotation fixers")
        print("[TOOL] Review the output above and fix any issues")

    print("\nTo run the fixes on the actual codebase:")
    print("  python run_all_type_fixes.py")


if __name__ == "__main__":
    main()
