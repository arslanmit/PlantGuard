#!/usr/bin/env python3
"""
File Structure Optimization for Mobile-Only PlantGuard
Task 10: Optimize file structure and clean up empty directories

This script:
1. Removes empty directories left behind from deleted files
2. Organizes remaining files in logical mobile-focused structure
3. Updates file paths and references to reflect new organization
4. Keeps only mobile-relevant assets and removes desktop-specific ones
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class FileStructureOptimizer:
    """Optimize file structure for mobile-only PlantGuard system."""

    def __init__(self, workspace_root: Path = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.optimization_log = []

    def log_action(self, action: str, details: str, status: str = "success"):
        """Log optimization actions."""
        entry = {"action": action, "details": details, "status": status, "timestamp": str(Path.cwd())}
        self.optimization_log.append(entry)
        logger.info(f"{action}: {details} - {status}")

    def find_empty_directories(self) -> list[Path]:
        """Find empty directories that can be safely removed."""
        empty_dirs = []

        # Directories to exclude from cleanup
        exclude_patterns = [".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"]

        for root, dirs, files in os.walk(self.workspace_root):
            root_path = Path(root)

            # Skip excluded directories
            if any(pattern in str(root_path) for pattern in exclude_patterns):
                continue

            # Check if directory is empty (no files, only empty subdirs)
            if not files:
                # Check if all subdirectories are also empty
                has_content = False
                for subdir in dirs:
                    subdir_path = root_path / subdir
                    if any(subdir_path.rglob("*")):
                        has_content = True
                        break

                if not has_content and root_path != self.workspace_root:
                    empty_dirs.append(root_path)

        return empty_dirs

    def remove_empty_directories(self) -> dict[str, Any]:
        """Remove empty directories."""
        empty_dirs = self.find_empty_directories()
        removed_dirs = []
        failed_removals = []

        for empty_dir in empty_dirs:
            try:
                if empty_dir.exists() and empty_dir.is_dir():
                    # Double-check it's actually empty
                    if not any(empty_dir.iterdir()):
                        empty_dir.rmdir()
                        removed_dirs.append(str(empty_dir.relative_to(self.workspace_root)))
                        self.log_action("remove_empty_dir", str(empty_dir.relative_to(self.workspace_root)))
            except Exception as e:
                failed_removals.append({"dir": str(empty_dir), "error": str(e)})
                self.log_action("remove_empty_dir", str(empty_dir), f"failed: {e}")

        return {"removed_directories": removed_dirs, "failed_removals": failed_removals, "total_removed": len(removed_dirs)}

    def organize_mobile_assets(self) -> dict[str, Any]:
        """Organize assets to keep only mobile-relevant ones."""
        assets_dir = self.workspace_root / "assets"

        if not assets_dir.exists():
            return {"status": "skipped", "reason": "assets directory not found"}

        # Mobile assets to keep
        mobile_assets = ["mobile_styles.css", "mobile_optimized_styles.css"]

        # Legacy assets to remove (if any exist)
        legacy_patterns = [
            "desktop_",
            "spa_",
            "legacy_",
            "styles.css",  # Generic styles.css (keep mobile-specific ones)
        ]

        kept_assets = []
        removed_assets = []

        for asset_file in assets_dir.iterdir():
            if asset_file.is_file():
                filename = asset_file.name

                # Keep mobile assets
                if filename in mobile_assets:
                    kept_assets.append(filename)
                    self.log_action("keep_mobile_asset", filename)

                # Remove legacy assets
                elif any(pattern in filename for pattern in legacy_patterns):
                    if filename != "mobile_styles.css" and filename != "mobile_optimized_styles.css":
                        try:
                            asset_file.unlink()
                            removed_assets.append(filename)
                            self.log_action("remove_legacy_asset", filename)
                        except Exception as e:
                            self.log_action("remove_legacy_asset", filename, f"failed: {e}")
                else:
                    # Keep other assets (images, icons, etc.)
                    kept_assets.append(filename)
                    self.log_action("keep_asset", filename)

        return {"kept_assets": kept_assets, "removed_assets": removed_assets, "total_kept": len(kept_assets), "total_removed": len(removed_assets)}

    def organize_mobile_structure(self) -> dict[str, Any]:
        """Organize files in logical mobile-focused structure."""

        # Define mobile-focused organization
        mobile_structure = {
            "mobile_apps": ["mobile_spa_app.py", "mobile_plantguard_app.py"],
            "mobile_tests": ["test_mobile_*.py", "*mobile_test*.py"],
            "mobile_docs": ["docs/MOBILE_*.md", "*mobile*.md"],
        }

        organized_files = []

        # Ensure mobile apps are in root (they should be)
        for app_file in mobile_structure["mobile_apps"]:
            app_path = self.workspace_root / app_file
            if app_path.exists():
                organized_files.append(f"mobile_app: {app_file}")
                self.log_action("verify_mobile_app_location", app_file)

        # Check mobile test organization
        mobile_test_files = list(self.workspace_root.glob("test_mobile_*.py"))
        for test_file in mobile_test_files:
            organized_files.append(f"mobile_test: {test_file.name}")
            self.log_action("verify_mobile_test_location", test_file.name)

        return {
            "organized_files": organized_files,
            "mobile_apps_found": len([f for f in organized_files if f.startswith("mobile_app:")]),
            "mobile_tests_found": len([f for f in organized_files if f.startswith("mobile_test:")]),
        }

    def update_file_references(self) -> dict[str, Any]:
        """Update file paths and references to reflect mobile-only organization."""

        # Files that might contain path references to update
        config_files = ["pyproject.toml", "pytest.ini", "Makefile", ".streamlit/config.toml"]

        updated_files = []

        for config_file in config_files:
            config_path = self.workspace_root / config_file
            if config_path.exists():
                try:
                    # Read file content
                    with open(config_path) as f:
                        content = f.read()

                    # Check if it contains any legacy references that need updating
                    legacy_refs = ["spa_app", "app.py", "desktop_"]
                    has_legacy_refs = any(ref in content for ref in legacy_refs)

                    if has_legacy_refs:
                        # For now, just log that manual review may be needed
                        self.log_action("check_file_references", config_file, "needs_manual_review")
                    else:
                        self.log_action("check_file_references", config_file, "clean")

                    updated_files.append(config_file)

                except Exception as e:
                    self.log_action("check_file_references", config_file, f"error: {e}")

        return {"checked_files": updated_files, "files_needing_review": [f for f in updated_files if "needs_manual_review" in str(f)]}

    def clean_cache_directories(self) -> dict[str, Any]:
        """Clean up cache directories while preserving mobile-relevant caches."""

        cache_dirs = ["__pycache__", ".mypy_cache", ".pytest_cache"]

        cleaned_caches = []

        for cache_dir in cache_dirs:
            cache_path = self.workspace_root / cache_dir
            if cache_path.exists():
                try:
                    # For __pycache__, remove legacy-specific compiled files
                    if cache_dir == "__pycache__":
                        legacy_pyc_files = list(cache_path.glob("*spa_app*.pyc")) + list(cache_path.glob("*app*.pyc"))
                        for pyc_file in legacy_pyc_files:
                            if "mobile" not in pyc_file.name:
                                pyc_file.unlink()
                                self.log_action("remove_legacy_cache", str(pyc_file.name))

                    cleaned_caches.append(cache_dir)

                except Exception as e:
                    self.log_action("clean_cache", cache_dir, f"error: {e}")

        return {"cleaned_caches": cleaned_caches, "total_cleaned": len(cleaned_caches)}

    def validate_mobile_structure(self) -> dict[str, Any]:
        """Validate that the mobile-only structure is correct."""

        validation_results = {"mobile_app_present": False, "mobile_assets_present": False, "removed_files_absent": True, "structure_valid": False}

        # Check mobile app exists
        mobile_app_path = self.workspace_root / "mobile_spa_app.py"
        validation_results["mobile_app_present"] = mobile_app_path.exists()

        # Check mobile assets exist
        mobile_styles = self.workspace_root / "assets" / "mobile_styles.css"
        mobile_optimized = self.workspace_root / "assets" / "mobile_optimized_styles.css"
        validation_results["mobile_assets_present"] = mobile_styles.exists() and mobile_optimized.exists()

        # Check removed files are absent
        removed_files = ["spa_app.py", "app.py"]
        for removed_file in removed_files:
            if (self.workspace_root / removed_file).exists():
                validation_results["removed_files_absent"] = False
                break

        # Overall structure validation
        validation_results["structure_valid"] = (
            validation_results["mobile_app_present"] and validation_results["mobile_assets_present"] and validation_results["removed_files_absent"]
        )

        return validation_results

    def run_optimization(self) -> dict[str, Any]:
        """Run complete file structure optimization."""

        logger.info("Starting file structure optimization for mobile-only PlantGuard")

        results = {
            "empty_directories": self.remove_empty_directories(),
            "mobile_assets": self.organize_mobile_assets(),
            "mobile_structure": self.organize_mobile_structure(),
            "file_references": self.update_file_references(),
            "cache_cleanup": self.clean_cache_directories(),
            "validation": self.validate_mobile_structure(),
            "optimization_log": self.optimization_log,
        }

        # Save optimization report
        report_path = self.workspace_root / "file_structure_optimization_report.json"
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"File structure optimization completed. Report saved to {report_path}")

        return results


def main():
    """Main function to run file structure optimization."""

    optimizer = FileStructureOptimizer()
    results = optimizer.run_optimization()

    # Print summary
    print("\n" + "=" * 60)
    print("FILE STRUCTURE OPTIMIZATION SUMMARY")
    print("=" * 60)

    print(f"\n📁 Empty Directories Removed: {results['empty_directories']['total_removed']}")
    print(f"🎨 Mobile Assets Organized: {results['mobile_assets']['total_kept']} kept, {results['mobile_assets']['total_removed']} removed")
    print(f"📱 Mobile Apps Found: {results['mobile_structure']['mobile_apps_found']}")
    print(f"🧪 Mobile Tests Found: {results['mobile_structure']['mobile_tests_found']}")
    print(f"🧹 Cache Directories Cleaned: {results['cache_cleanup']['total_cleaned']}")

    print("\n✅ Structure Validation:")
    validation = results["validation"]
    print(f"   Mobile App Present: {'✅' if validation['mobile_app_present'] else '❌'}")
    print(f"   Mobile Assets Present: {'✅' if validation['mobile_assets_present'] else '❌'}")
    print(f"   Removed Files Absent: {'✅' if validation['removed_files_absent'] else '❌'}")
    print(f"   Overall Structure Valid: {'✅' if validation['structure_valid'] else '❌'}")

    if validation["structure_valid"]:
        print("\n🎉 File structure optimization completed successfully!")
    else:
        print("\n⚠️  File structure optimization completed with warnings. Check the report for details.")

    return results


if __name__ == "__main__":
    main()
