#!/usr/bin/env python3
"""
from typing import Any, Dict, List, Optional, Tuple, Union

Example usage of the Migration Safety Framework

This script demonstrates how to use the migration safety framework
for the PlantGuard mobile-only refactoring.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.migration_safety import MigrationSafetyFramework


def main() -> None:
    """Demonstrate migration safety framework usage."""

    print("=== PlantGuard Migration Safety Framework Example ===\n")

    # 1. Create the migration safety framework
    print("1. Creating migration safety framework...")
    framework = MigrationSafetyFramework("mobile_only_refactoring")
    print(f"   Migration ID: {framework.migration_id}")

    # 2. Create safety checkpoint
    print("\n2. Creating safety checkpoint...")
    success = framework.create_safety_checkpoint()

    if success:
        print("   [DONE] Safety checkpoint created successfully")
        status = framework.get_migration_status()
        print(f"   Files backed up: {status['status']['files_backed_up']}")
    else:
        print("   [TODO] Failed to create safety checkpoint")
        return

    # 3. Simulate migration changes
    print("\n3. Simulating migration changes...")

    # Track file removals
    removed_files = ["spa_app.py", "app.py", "test_spa_navigation.py", "test_unified_ui.py"]

    for file_path in removed_files:
        framework.tracker.track_file_removal(file_path)
        print(f"   Tracked removal: {file_path}")

    # Track file modifications
    files_to_modify = ["Makefile", "mobile_spa_app.py", "README.md"]

    for file_path in files_to_modify:
        framework.tracker.track_file_modification(file_path)
        print(f"   Tracked modification: {file_path}")

    # Track import cleanups
    import_cleanups = [
        ("mobile_spa_app.py", "from spa_app import"),
        ("src/ui/components/mobile_header.py", "import spa_app"),
    ]

    for file_path, import_stmt in import_cleanups:
        framework.tracker.track_import_cleanup(file_path, import_stmt)
        print(f"   Tracked import cleanup: {import_stmt} from {file_path}")

    # Track Makefile target removals
    removed_targets = ["run", "spa-dev", "spa-prod", "spa-test"]

    for target in removed_targets:
        framework.tracker.track_target_removal(target)
        print(f"   Tracked target removal: {target}")

    # 4. Validate migration state
    print("\n4. Validating migration state...")
    validation_results = framework.validate_migration_state()

    print("   Validation Results:")
    for test_name, result in validation_results.items():
        if test_name == "overall_summary":
            continue

        status_icon = {"passed": "[DONE]", "warning": "[WARNING]", "failed": "[TODO]"}.get(result["status"], "[UNKNOWN]")

        print(f"   {status_icon} {test_name}: {result['status']}")

        if result["status"] != "passed":
            print(f"      Details: {result['details']}")

    # Overall summary
    summary = validation_results["overall_summary"]
    summary_icon = {"passed": "[DONE]", "warning": "[WARNING]", "failed": "[TODO]"}.get(summary["status"], "[UNKNOWN]")

    print(f"\n   {summary_icon} Overall Status: {summary['status']}")
    print(f"   {summary['details']}")

    # 5. Show migration status
    print("\n5. Migration Status Summary:")
    status = framework.get_migration_status()
    migration_status = status["status"]

    print(f"   Migration ID: {status['migration_id']}")
    print(f"   Files Removed: {migration_status['files_removed']}")
    print(f"   Files Modified: {migration_status['files_modified']}")
    print(f"   Imports Cleaned: {migration_status['imports_cleaned']}")
    print(f"   Targets Removed: {migration_status['targets_removed']}")
    print(f"   Backup Created: {migration_status['backup_created']}")
    print(f"   Rollback Available: {migration_status['rollback_available']}")

    # 6. Demonstrate rollback capability (optional)
    print("\n6. Rollback capability:")
    if migration_status["rollback_available"]:
        print("   [DONE] Rollback is available if needed")
        print("   Use: framework.rollback_migration() to restore previous state")
    else:
        print("   [TODO] No rollback available")

    # 7. Finalize migration (when ready)
    print("\n7. Migration finalization:")
    if validation_results["overall_summary"]["status"] in ["passed", "warning"]:
        print("   Ready to finalize migration")
        print("   Use: framework.finalize_migration() when all tasks complete")
    else:
        print("   [WARNING]  Migration validation failed - address issues before finalizing")

    print("\n=== Example Complete ===")
    print(f"Migration tracking log: {framework.tracker.log_file}")
    print("Use the CLI tool for interactive management:")
    print("  python scripts/migration_safety_cli.py status")
    print("  python scripts/migration_safety_cli.py validate")
    print("  python scripts/migration_safety_cli.py rollback")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExample cancelled by user")
    except Exception as e:
        print(f"Error running example: {e}")
        sys.exit(1)
