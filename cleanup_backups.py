#!/usr/bin/env python3
"""
Cleanup script to remove backup files created by replace_emojis.py
"""

import argparse
import sys
from pathlib import Path


def cleanup_backups(root_path: str, dry_run: bool = False):
    """Remove all .backup files in the directory tree."""
    root = Path(root_path)
    backup_files = list(root.rglob("*.backup"))

    if not backup_files:
        print("No backup files found.")
        return

    print(f"Found {len(backup_files)} backup files:")
    for backup_file in backup_files:
        relative_path = backup_file.relative_to(root)
        print(f"  {relative_path}")

    if dry_run:
        print(f"\nDry run: Would delete {len(backup_files)} backup files")
        return

    # Ask for confirmation
    response = input(f"\nDelete all {len(backup_files)} backup files? (y/N): ")
    if response.lower() not in ["y", "yes"]:
        print("Cancelled.")
        return

    # Delete backup files
    deleted_count = 0
    for backup_file in backup_files:
        try:
            backup_file.unlink()
            deleted_count += 1
        except (OSError, PermissionError) as e:
            print(f"Error deleting {backup_file}: {e}")

    print(f"\n✅ Successfully deleted {deleted_count} backup files!")


def main():
    parser = argparse.ArgumentParser(description="Clean up backup files created by replace_emojis.py")

    parser.add_argument("--path", default=".", help="Root path to search for backup files (default: current dir)")

    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")

    args = parser.parse_args()

    # Validate path
    root_path = Path(args.path).resolve()
    if not root_path.exists():
        print(f"Error: Path '{root_path}' does not exist")
        sys.exit(1)

    if not root_path.is_dir():
        print(f"Error: Path '{root_path}' is not a directory")
        sys.exit(1)

    try:
        cleanup_backups(str(root_path), args.dry_run)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
