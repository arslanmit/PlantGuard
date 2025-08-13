#!/usr/bin/env python3
"""Test runner script for PlantGuard project.

Provides convenient commands for running different types of tests.
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Constants
MIN_ARGS = 2


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)

    try:
        subprocess.run(cmd, check=True, cwd=Path.cwd())
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False

    print(f"✅ {description} completed successfully")
    return True


def _show_usage() -> None:
    """Show usage information."""
    print("Usage: python run_tests.py [command]")
    print("\nAvailable commands:")
    print("  all       - Run all tests with coverage")
    print("  unit      - Run unit tests only")
    print("  fast      - Run tests without coverage")
    print("  coverage  - Generate coverage report")
    print("  clean     - Clean test artifacts")


def _run_all_tests() -> bool:
    """Run all tests with coverage."""
    return run_command(
        [
            "python",
            "-m",
            "pytest",
            "tests/",
            "-v",
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term",
        ],
        "Running all tests with coverage",
    )


def _run_unit_tests() -> bool:
    """Run unit tests only."""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-v", "-m", "unit"], "Running unit tests"
    )


def _run_fast_tests() -> bool:
    """Run tests without coverage."""
    return run_command(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"], "Running tests (fast mode)"
    )


def _generate_coverage() -> bool:
    """Generate coverage report."""
    success = run_command(
        ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=html"],
        "Generating coverage report",
    )
    if success:
        coverage_path = Path.cwd() / "htmlcov" / "index.html"
        print(f"\n📊 Coverage report generated in: {coverage_path}")
    return success


def _clean_artifacts() -> bool:
    """Clean test artifacts."""
    artifacts = [".pytest_cache", "htmlcov", ".coverage"]
    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"🧹 Removed {artifact}")
    print("✅ Test artifacts cleaned")
    return True


def main() -> None:
    """Main test runner."""
    if len(sys.argv) < MIN_ARGS:
        _show_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "all":
        success = _run_all_tests()
    elif command == "unit":
        success = _run_unit_tests()
    elif command == "fast":
        success = _run_fast_tests()
    elif command == "coverage":
        success = _generate_coverage()
    elif command == "clean":
        success = _clean_artifacts()
    else:
        print(f"❌ Unknown command: {command}")
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
