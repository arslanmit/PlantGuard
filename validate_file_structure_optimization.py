#!/usr/bin/env python3
"""
Validation script for Task 10: File Structure Optimization
Validates that all requirements have been met for mobile-only file structure.
"""

import json
from pathlib import Path
from typing import Any


def validate_task_10_requirements() -> dict[str, Any]:
    """Validate all Task 10 requirements are met."""

    workspace_root = Path.cwd()
    results = {
        "requirement_8_1": validate_mobile_focused_structure(workspace_root),
        "requirement_8_2": validate_empty_directories_cleaned(workspace_root),
        "requirement_8_3": validate_file_references_updated(workspace_root),
        "requirement_8_4": validate_mobile_components_organized(workspace_root),
        "requirement_8_5": validate_mobile_assets_only(workspace_root),
        "overall_status": "pending",
    }

    # Determine overall status
    all_passed = all(result.get("status") == "passed" for result in results.values() if isinstance(result, dict) and "status" in result)

    results["overall_status"] = "passed" if all_passed else "needs_attention"

    return results


def validate_mobile_focused_structure(workspace_root: Path) -> dict[str, Any]:
    """Requirement 8.1: Maintain clear mobile-focused directory structure."""

    expected_structure = {
        "mobile_apps": ["mobile_spa_app.py"],
        "mobile_assets": ["assets/mobile_styles.css", "assets/mobile_optimized_styles.css"],
        "mobile_components": ["src/ui/mobile_*.py"],
        "mobile_tests": ["test_mobile_*.py"],
        "core_adapters": ["src/core/vision.py", "src/core/audio.py", "src/core/nlp.py"],
    }

    found_structure = {}
    missing_items = []

    # Check mobile apps
    mobile_apps = []
    for app in expected_structure["mobile_apps"]:
        app_path = workspace_root / app
        if app_path.exists():
            mobile_apps.append(app)
        else:
            missing_items.append(app)
    found_structure["mobile_apps"] = mobile_apps

    # Check mobile assets
    mobile_assets = []
    for asset in expected_structure["mobile_assets"]:
        asset_path = workspace_root / asset
        if asset_path.exists():
            mobile_assets.append(asset)
        else:
            missing_items.append(asset)
    found_structure["mobile_assets"] = mobile_assets

    # Check mobile components
    mobile_components = list(workspace_root.glob("src/ui/mobile_*.py"))
    found_structure["mobile_components"] = [str(comp.relative_to(workspace_root)) for comp in mobile_components]

    # Check mobile tests
    mobile_tests = list(workspace_root.glob("test_mobile_*.py"))
    found_structure["mobile_tests"] = [str(test.relative_to(workspace_root)) for test in mobile_tests]

    # Check core adapters
    core_adapters = []
    for adapter in expected_structure["core_adapters"]:
        adapter_path = workspace_root / adapter
        if adapter_path.exists():
            core_adapters.append(adapter)
        else:
            missing_items.append(adapter)
    found_structure["core_adapters"] = core_adapters

    status = "passed" if not missing_items else "failed"

    return {
        "requirement": "8.1 - Mobile-focused directory structure",
        "status": status,
        "found_structure": found_structure,
        "missing_items": missing_items,
        "details": f"Mobile structure organized with {len(mobile_apps)} apps, {len(mobile_assets)} assets, {len(mobile_components)} components, {len(mobile_tests)} tests",
    }


def validate_empty_directories_cleaned(workspace_root: Path) -> dict[str, Any]:
    """Requirement 8.2: Remove empty directories left behind."""

    # Find potentially empty directories (excluding system dirs)
    exclude_patterns = [".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache"]

    empty_dirs = []
    for root_dir in workspace_root.rglob("*"):
        if root_dir.is_dir():
            # Skip excluded directories
            if any(pattern in str(root_dir) for pattern in exclude_patterns):
                continue

            # Check if directory is empty
            with contextlib.suppress(PermissionError):
                if not any(root_dir.iterdir()):
                    empty_dirs.append(str(root_dir.relative_to(workspace_root)))

    status = "passed" if not empty_dirs else "warning"

    return {
        "requirement": "8.2 - Empty directories cleaned",
        "status": status,
        "empty_directories": empty_dirs,
        "details": f"Found {len(empty_dirs)} empty directories" if empty_dirs else "No empty directories found",
    }


def validate_file_references_updated(workspace_root: Path) -> dict[str, Any]:
    """Requirement 8.3: Update file paths and references."""

    config_files = ["pyproject.toml", "pytest.ini", "Makefile", ".streamlit/config.toml"]

    checked_files = []
    issues_found = []

    # Check for legacy references in config files
    legacy_patterns = ["spa_app.py", "app.py", "desktop_"]

    for config_file in config_files:
        config_path = workspace_root / config_file
        if config_path.exists():
            try:
                with open(config_path) as f:
                    content = f.read()

                found_patterns = []
                for pattern in legacy_patterns:
                    if pattern in content and "mobile_spa_app.py" not in content:
                        found_patterns.append(pattern)

                if found_patterns:
                    issues_found.append({"file": config_file, "patterns": found_patterns})

                checked_files.append(config_file)

            except Exception as e:
                issues_found.append({"file": config_file, "error": str(e)})

    status = "passed" if not issues_found else "warning"

    return {
        "requirement": "8.3 - File references updated",
        "status": status,
        "checked_files": checked_files,
        "issues_found": issues_found,
        "details": f"Checked {len(checked_files)} config files, found {len(issues_found)} issues",
    }


def validate_mobile_components_organized(workspace_root: Path) -> dict[str, Any]:
    """Requirement 8.4: Organize mobile components logically."""

    # Check mobile component organization
    mobile_ui_components = list((workspace_root / "src" / "ui").glob("mobile_*.py"))
    mobile_tests = list(workspace_root.glob("test_mobile_*.py"))
    mobile_apps = [workspace_root / "mobile_spa_app.py"]

    organized_components = {
        "mobile_ui_components": len(mobile_ui_components),
        "mobile_tests": len(mobile_tests),
        "mobile_apps": len([app for app in mobile_apps if app.exists()]),
    }

    # Check if components are logically grouped
    well_organized = (
        organized_components["mobile_ui_components"] > 0 and organized_components["mobile_tests"] > 0 and organized_components["mobile_apps"] > 0
    )

    status = "passed" if well_organized else "warning"

    return {
        "requirement": "8.4 - Mobile components organized logically",
        "status": status,
        "organized_components": organized_components,
        "details": f"Found {organized_components['mobile_ui_components']} UI components, {organized_components['mobile_tests']} tests, {organized_components['mobile_apps']} apps",
    }


def validate_mobile_assets_only(workspace_root: Path) -> dict[str, Any]:
    """Requirement 8.5: Keep only mobile-relevant assets."""

    assets_dir = workspace_root / "assets"

    if not assets_dir.exists():
        return {"requirement": "8.5 - Mobile-relevant assets only", "status": "warning", "details": "Assets directory not found"}

    # Check assets
    all_assets = list(assets_dir.glob("*"))
    mobile_assets = [asset for asset in all_assets if "mobile" in asset.name.lower()]
    desktop_assets = [asset for asset in all_assets if any(pattern in asset.name.lower() for pattern in ["desktop", "spa", "legacy"])]

    # Remove desktop-specific patterns but keep mobile ones
    problematic_assets = [asset for asset in desktop_assets if "mobile" not in asset.name.lower()]

    status = "passed" if not problematic_assets else "warning"

    return {
        "requirement": "8.5 - Mobile-relevant assets only",
        "status": status,
        "mobile_assets": [asset.name for asset in mobile_assets],
        "problematic_assets": [asset.name for asset in problematic_assets],
        "total_assets": len(all_assets),
        "details": f"Found {len(mobile_assets)} mobile assets, {len(problematic_assets)} problematic assets",
    }


def main():
    """Main validation function."""

    print("🔍 Validating Task 10: File Structure Optimization")
    print("=" * 60)

    results = validate_task_10_requirements()

    # Print results
    for req_key, req_result in results.items():
        if req_key == "overall_status":
            continue

        if isinstance(req_result, dict) and "requirement" in req_result:
            status_emoji = "[DONE]" if req_result["status"] == "passed" else ("[WARNING]" if req_result["status"] == "warning" else "[TODO]")
            print(f"\n{status_emoji} {req_result['requirement']}")
            print(f"   Status: {req_result['status']}")
            print(f"   Details: {req_result['details']}")

            if req_result["status"] != "passed" and "issues_found" in req_result:
                for issue in req_result["issues_found"]:
                    print(f"   Issue: {issue}")

    # Overall status
    overall_emoji = "[SUCCESS]" if results["overall_status"] == "passed" else "[WARNING]"
    print(f"\n{overall_emoji} Overall Task 10 Status: {results['overall_status'].upper()}")

    # Save detailed results
    results_file = Path.cwd() / "task_10_validation_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Detailed results saved to: {results_file}")

    return results


if __name__ == "__main__":
    main()
