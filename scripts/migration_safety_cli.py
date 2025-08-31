from typing import Any

#!/usr/bin/env python3
"""
Command-line interface for PlantGuard Migration Safety Framework

Usage:
    python scripts/migration_safety_cli.py create-checkpoint
    python scripts/migration_safety_cli.py validate
    python scripts/migration_safety_cli.py rollback [migration_id]
    python scripts/migration_safety_cli.py status
    python scripts/migration_safety_cli.py list-backups
"""


import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.migration_safety import MigrationBackupManager, MigrationSafetyFramework, create_migration_framework


def create_checkpoint(args) -> Any:
    """Create a migration safety checkpoint."""
    print("Creating migration safety checkpoint...")

    framework = create_migration_framework("mobile_only_refactoring")
    success = framework.create_safety_checkpoint()

    if success:
        print("[DONE] Safety checkpoint created successfully!")
        print(f"Migration ID: {framework.migration_id}")
        status = framework.get_migration_status()
        print(f"Files backed up: {status['status']['files_backed_up']}")
    else:
        print("[TODO] Failed to create safety checkpoint")
        sys.exit(1)


def validate_migration(args) -> bool:
    """Validate current migration state."""
    print("Validating migration state...")

    # Try to find existing migration or create new framework
    framework = create_migration_framework("mobile_only_refactoring")
    results = framework.validate_migration_state()

    print("\n=== Validation Results ===")

    for test_name, result in results.items():
        if test_name == "overall_summary":
            continue

        status_icon = {"passed": "[DONE]", "warning": "[WARNING]", "failed": "[TODO]"}.get(result["status"], "[UNKNOWN]")

        print(f"{status_icon} {test_name}: {result['status']}")
        if result["status"] != "passed":
            print(f"   Details: {result['details']}")

    # Overall summary
    summary = results["overall_summary"]
    summary_icon = {"passed": "[DONE]", "warning": "[WARNING]", "failed": "[TODO]"}.get(summary["status"], "[UNKNOWN]")

    print(f"\n{summary_icon} Overall Status: {summary['status']}")
    print(f"   {summary['details']}")

    if summary["status"] == "failed":
        sys.exit(1)


def rollback_migration(args) -> Any:
    """Rollback migration to previous state."""
    migration_id = args.migration_id

    if not migration_id:
        # List available migrations
        backup_manager = MigrationBackupManager()
        backups = backup_manager.list_backups()

        if not backups:
            print("No backups available for rollback")
            sys.exit(1)

        print("Available backups:")
        for i, backup in enumerate(backups):
            print(f"  {i + 1}. {backup['migration_id']} ({backup['backup_timestamp']})")

        try:
            choice = int(input("Select backup to rollback to (number): ")) - 1
            if 0 <= choice < len(backups):
                migration_id = backups[choice]["migration_id"]
            else:
                print("Invalid selection")
                sys.exit(1)
        except (ValueError, KeyboardInterrupt):
            print("Rollback cancelled")
            sys.exit(1)

    print(f"Rolling back migration: {migration_id}")

    framework = MigrationSafetyFramework("mobile_only_refactoring")
    framework.migration_id = migration_id

    success = framework.rollback_migration()

    if success:
        print("[DONE] Migration rollback completed successfully")
    else:
        print("[TODO] Migration rollback failed")
        sys.exit(1)


def show_status(args) -> None:
    """Show current migration status."""
    framework = create_migration_framework("mobile_only_refactoring")
    status = framework.get_migration_status()

    print("=== Migration Status ===")
    print(f"Migration ID: {status['migration_id']}")
    print(f"Backups Available: {status['backups_available']}")

    migration_status = status["status"]
    print("\nMigration Progress:")
    print(f"  Files Removed: {migration_status['files_removed']}")
    print(f"  Files Modified: {migration_status['files_modified']}")
    print(f"  Files Backed Up: {migration_status['files_backed_up']}")
    print(f"  Imports Cleaned: {migration_status['imports_cleaned']}")
    print(f"  Targets Removed: {migration_status['targets_removed']}")
    print(f"  Migration Complete: {migration_status['migration_complete']}")
    print(f"  Validation Passed: {migration_status['validation_passed']}")
    print(f"  Backup Created: {migration_status['backup_created']}")
    print(f"  Rollback Available: {migration_status['rollback_available']}")


def list_backups(args) -> Any:
    """List available backups."""
    backup_manager = MigrationBackupManager()
    backups = backup_manager.list_backups()

    if not backups:
        print("No backups available")
        return

    print("=== Available Backups ===")
    for backup in backups:
        print(f"Migration ID: {backup['migration_id']}")
        print(f"  Timestamp: {backup['backup_timestamp']}")
        print(f"  Files: {backup['total_files']}")
        print(f"  Path: {backup['backup_path']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PlantGuard Migration Safety Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migration_safety_cli.py create-checkpoint
  python scripts/migration_safety_cli.py validate
  python scripts/migration_safety_cli.py rollback
  python scripts/migration_safety_cli.py status
  python scripts/migration_safety_cli.py list-backups
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create checkpoint command
    checkpoint_parser = subparsers.add_parser("create-checkpoint", help="Create a migration safety checkpoint")
    checkpoint_parser.set_defaults(func=create_checkpoint)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate current migration state")
    validate_parser.set_defaults(func=validate_migration)

    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback migration to previous state")
    rollback_parser.add_argument("migration_id", nargs="?", help="Migration ID to rollback to (optional - will prompt if not provided)")
    rollback_parser.set_defaults(func=rollback_migration)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show current migration status")
    status_parser.set_defaults(func=show_status)

    # List backups command
    list_parser = subparsers.add_parser("list-backups", help="List available backups")
    list_parser.set_defaults(func=list_backups)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
