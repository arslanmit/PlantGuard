"""
Migration Safety Framework for PlantGuard Mobile-Only Refactoring

This module provides comprehensive backup, tracking, rollback, and validation
capabilities for safely migrating from multi-interface to mobile-only system.
"""

import json
import logging
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MigrationStatus:
    """Track migration progress and changes."""

    migration_id: str
    start_time: str
    files_removed: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    files_backed_up: list[str] = field(default_factory=list)
    imports_cleaned: list[str] = field(default_factory=list)
    targets_removed: list[str] = field(default_factory=list)

    migration_complete: bool = False
    validation_passed: bool = False
    backup_created: bool = False
    rollback_available: bool = False

    def add_removed_file(self, filepath: str) -> Any:
        """Track a removed file."""
        if filepath not in self.files_removed:
            self.files_removed.append(filepath)
            logger.info(f"Tracked file removal: {filepath}")

    def add_modified_file(self, filepath: str) -> Any:
        """Track a modified file."""
        if filepath not in self.files_modified:
            self.files_modified.append(filepath)
            logger.info(f"Tracked file modification: {filepath}")

    def add_backed_up_file(self, filepath: str) -> Any:
        """Track a backed up file."""
        if filepath not in self.files_backed_up:
            self.files_backed_up.append(filepath)

    def add_cleaned_import(self, filepath: str, import_name: str) -> Any:
        """Track cleaned import."""
        entry = f"{filepath}:{import_name}"
        if entry not in self.imports_cleaned:
            self.imports_cleaned.append(entry)
            logger.info(f"Tracked import cleanup: {entry}")

    def add_removed_target(self, target: str) -> Any:
        """Track removed Makefile target."""
        if target not in self.targets_removed:
            self.targets_removed.append(target)
            logger.info(f"Tracked target removal: {target}")

    def get_summary(self) -> dict[str, Any]:
        """Get migration summary."""
        return {
            "migration_id": self.migration_id,
            "start_time": self.start_time,
            "files_removed": len(self.files_removed),
            "files_modified": len(self.files_modified),
            "files_backed_up": len(self.files_backed_up),
            "imports_cleaned": len(self.imports_cleaned),
            "targets_removed": len(self.targets_removed),
            "migration_complete": self.migration_complete,
            "validation_passed": self.validation_passed,
            "backup_created": self.backup_created,
            "rollback_available": self.rollback_available,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class MigrationBackupManager:
    """Manages backup creation and restoration for migration safety."""

    def __init__(self, backup_dir: Path | None = None) -> None:
        self.backup_dir = backup_dir or Path(".migration_backups")
        self.backup_dir.mkdir(exist_ok=True)

    def create_full_backup(self, migration_id: str) -> Path:
        """Create a full backup of the current codebase state."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{migration_id}_{timestamp}"
        backup_path = self.backup_dir / backup_name

        logger.info(f"Creating full backup at: {backup_path}")

        try:
            # Create backup directory
            backup_path.mkdir(exist_ok=True)

            # Files and directories to backup
            items_to_backup = [
                "src/",
                "assets/",
                "config/",
                "tests/",
                "scripts/",
                "mobile_spa_app.py",
                "Makefile",
                "requirements.txt",
                "pyproject.toml",
                "README.md",
                # Test files that might be removed
                "test_spa_navigation.py",
                "test_unified_ui.py",
                "test_mobile_*.py",
            ]

            backed_up_files = []

            for item in items_to_backup:
                source_path = Path(item)
                if source_path.exists():
                    dest_path = backup_path / item

                    if source_path.is_file():
                        # Backup individual file
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, dest_path)
                        backed_up_files.append(str(source_path))
                    elif source_path.is_dir():
                        # Backup entire directory
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                        backed_up_files.extend([str(p) for p in source_path.rglob("*") if p.is_file()])

            # Create backup manifest
            manifest = {
                "migration_id": migration_id,
                "backup_timestamp": timestamp,
                "backup_path": str(backup_path),
                "files_backed_up": backed_up_files,
                "total_files": len(backed_up_files),
            }

            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"Backup created successfully: {len(backed_up_files)} files backed up")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_from_backup(self, backup_path: Path) -> bool:
        """Restore codebase from backup."""
        try:
            manifest_path = backup_path / "backup_manifest.json"
            if not manifest_path.exists():
                logger.error(f"Backup manifest not found: {manifest_path}")
                return False

            with open(manifest_path) as f:
                manifest = json.load(f)

            logger.info(f"Restoring from backup: {manifest['backup_timestamp']}")

            # Restore files
            restored_count = 0
            for item in backup_path.iterdir():
                if item.name == "backup_manifest.json":
                    continue

                dest_path = Path(item.name)

                if item.is_file():
                    shutil.copy2(item, dest_path)
                    restored_count += 1
                elif item.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(item, dest_path)
                    restored_count += len([p for p in item.rglob("*") if p.is_file()])

            logger.info(f"Restore completed: {restored_count} files restored")
            return True

        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False

    def list_backups(self) -> list[dict[str, Any]]:
        """List available backups."""
        backups = []

        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                manifest_path = backup_dir / "backup_manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                        backups.append(manifest)
                    except Exception as e:
                        logger.warning(f"Failed to read backup manifest {manifest_path}: {e}")

        return sorted(backups, key=lambda x: x["backup_timestamp"], reverse=True)


class MigrationTracker:
    """Tracks all changes made during migration."""

    def __init__(self, migration_id: str) -> None:
        self.migration_id = migration_id
        self.status = MigrationStatus(migration_id=migration_id, start_time=datetime.now().isoformat())
        self.log_file = Path(f".migration_logs/migration_{migration_id}.json")
        self.log_file.parent.mkdir(exist_ok=True)

        # Save initial status
        self._save_status()

    def _save_status(self) -> Any:
        """Save current status to log file."""
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.status.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save migration status: {e}")

    def track_file_removal(self, filepath: str) -> Any:
        """Track file removal."""
        self.status.add_removed_file(filepath)
        self._save_status()

    def track_file_modification(self, filepath: str) -> Any:
        """Track file modification."""
        self.status.add_modified_file(filepath)
        self._save_status()

    def track_import_cleanup(self, filepath: str, import_name: str) -> Any:
        """Track import cleanup."""
        self.status.add_cleaned_import(filepath, import_name)
        self._save_status()

    def track_target_removal(self, target: str) -> Any:
        """Track Makefile target removal."""
        self.status.add_removed_target(target)
        self._save_status()

    def set_backup_created(self, backup_path: Path) -> Any:
        """Mark backup as created."""
        self.status.backup_created = True
        self.status.rollback_available = True
        for file_path in backup_path.rglob("*"):
            if file_path.is_file() and file_path.name != "backup_manifest.json":
                self.status.add_backed_up_file(str(file_path.relative_to(backup_path)))
        self._save_status()

    def set_migration_complete(self, success: bool = True) -> Any:
        """Mark migration as complete."""
        self.status.migration_complete = success
        self._save_status()

    def set_validation_passed(self, passed: bool = True) -> Any:
        """Mark validation as passed."""
        self.status.validation_passed = passed
        self._save_status()

    def get_status(self) -> MigrationStatus:
        """Get current migration status."""
        return self.status


class MigrationValidator:
    """Validates system integrity during migration."""

    def __init__(self, migration_tracker: MigrationTracker) -> None:
        self.tracker = migration_tracker
        self.validation_results = []

    def validate_file_integrity(self) -> dict[str, Any]:
        """Validate that essential files still exist and are valid."""
        essential_files = [
            "mobile_spa_app.py",
            "src/core/vision.py",
            "src/core/audio.py",
            "src/core/nlp.py",
            "Makefile",
            "requirements.txt",
        ]

        results = {"passed": [], "failed": [], "warnings": []}

        for filepath in essential_files:
            path = Path(filepath)
            if path.exists():
                try:
                    # Basic syntax check for Python files
                    if filepath.endswith(".py"):
                        with open(path) as f:
                            content = f.read()
                        compile(content, filepath, "exec")

                    results["passed"].append(filepath)
                except SyntaxError as e:
                    results["failed"].append(f"{filepath}: Syntax error - {e}")
                except Exception as e:
                    results["warnings"].append(f"{filepath}: Warning - {e}")
            else:
                results["failed"].append(f"{filepath}: File missing")

        return {"test": "file_integrity", "status": "passed" if not results["failed"] else "failed", "details": results}

    def validate_import_statements(self) -> dict[str, Any]:
        """Validate that import statements are clean and functional."""
        python_files = [
            "mobile_spa_app.py",
            "src/core/vision.py",
            "src/core/audio.py",
            "src/core/nlp.py",
        ]

        legacy_import_patterns = [
            "from spa_app import",
            "import spa_app",
            "from app import",
            "import app",
        ]

        results = {"passed": [], "failed": [], "warnings": []}

        for filepath in python_files:
            path = Path(filepath)
            if path.exists():
                try:
                    with open(path) as f:
                        content = f.read()

                    # Check for legacy imports
                    found_legacy_imports = []
                    for pattern in legacy_import_patterns:
                        if pattern in content:
                            found_legacy_imports.append(pattern)

                    if found_legacy_imports:
                        results["failed"].append({"file": filepath, "legacy_imports": found_legacy_imports})
                    else:
                        results["passed"].append(filepath)

                except Exception as e:
                    results["warnings"].append(f"{filepath}: {e}")

        return {"test": "import_statements", "status": "passed" if not results["failed"] else "failed", "details": results}

    def validate_makefile_targets(self) -> dict[str, Any]:
        """Validate Makefile targets are properly updated."""
        try:
            with open("Makefile") as f:
                makefile_content = f.read()

            # Check mobile target exists
            if "mobile:" not in makefile_content:
                return {"test": "makefile_targets", "status": "failed", "details": "Mobile target not found in Makefile"}

            # Check legacy targets are handled
            legacy_targets = ["run:", "spa-dev:", "spa-prod:"]
            found_legacy_targets = []

            for target in legacy_targets:
                if target in makefile_content:
                    found_legacy_targets.append(target)

            status = "passed"
            details = "Makefile properly configured for mobile-only"

            if found_legacy_targets:
                status = "warning"
                details = f"Legacy targets still present: {found_legacy_targets}"

            return {"test": "makefile_targets", "status": status, "details": details}

        except Exception as e:
            return {"test": "makefile_targets", "status": "failed", "details": f"Failed to validate Makefile: {e}"}

    def validate_mobile_functionality(self) -> dict[str, Any]:
        """Validate that mobile functionality is intact."""
        try:
            # Test mobile app import
            import importlib.util

            # Check mobile_spa_app can be imported
            spec = importlib.util.spec_from_file_location("mobile_spa_app", "mobile_spa_app.py")
            if spec is None:
                return {"test": "mobile_functionality", "status": "failed", "details": "Cannot load mobile_spa_app.py"}

            # Check core adapters can be imported
            core_modules = ["src.core.vision", "src.core.audio", "src.core.nlp"]

            failed_imports = []
            for module in core_modules:
                try:
                    importlib.import_module(module)
                except ImportError as e:
                    failed_imports.append(f"{module}: {e}")

            if failed_imports:
                return {"test": "mobile_functionality", "status": "failed", "details": f"Failed imports: {failed_imports}"}

            return {"test": "mobile_functionality", "status": "passed", "details": "All mobile components import successfully"}

        except Exception as e:
            return {"test": "mobile_functionality", "status": "failed", "details": f"Mobile functionality test failed: {e}"}

    def run_comprehensive_validation(self) -> dict[str, Any]:
        """Run all validation tests."""
        tests = {
            "file_integrity": self.validate_file_integrity(),
            "import_statements": self.validate_import_statements(),
            "makefile_targets": self.validate_makefile_targets(),
            "mobile_functionality": self.validate_mobile_functionality(),
        }

        # Overall status
        failed_tests = [name for name, result in tests.items() if result["status"] == "failed"]
        warning_tests = [name for name, result in tests.items() if result["status"] == "warning"]
        passed_tests = [name for name, result in tests.items() if result["status"] == "passed"]

        overall_status = "passed"
        if failed_tests:
            overall_status = "failed"
        elif warning_tests:
            overall_status = "warning"

        tests["overall_summary"] = {
            "status": overall_status,
            "passed": len(passed_tests),
            "warnings": len(warning_tests),
            "failed": len(failed_tests),
            "details": f"Validation completed: {len(passed_tests)} passed, {len(warning_tests)} warnings, {len(failed_tests)} failed",
        }

        # Update tracker
        self.tracker.set_validation_passed(overall_status in ["passed", "warning"])

        return tests


class MigrationSafetyFramework:
    """Main framework coordinating all migration safety components."""

    def __init__(self, migration_name: str = "mobile_only_refactoring") -> None:
        self.migration_id = f"{migration_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize components
        self.backup_manager = MigrationBackupManager()
        self.tracker = MigrationTracker(self.migration_id)
        self.validator = MigrationValidator(self.tracker)

        logger.info(f"Migration safety framework initialized: {self.migration_id}")

    def create_safety_checkpoint(self) -> bool:
        """Create a complete safety checkpoint before migration."""
        try:
            logger.info("Creating migration safety checkpoint...")

            # Create full backup
            backup_path = self.backup_manager.create_full_backup(self.migration_id)
            self.tracker.set_backup_created(backup_path)

            # Run initial validation
            validation_results = self.validator.run_comprehensive_validation()

            logger.info("Safety checkpoint created successfully")
            logger.info(f"Backup location: {backup_path}")
            logger.info(f"Migration ID: {self.migration_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to create safety checkpoint: {e}")
            return False

    def rollback_migration(self) -> bool:
        """Rollback migration to previous state."""
        try:
            logger.info(f"Rolling back migration: {self.migration_id}")

            # Find the backup for this migration
            backups = self.backup_manager.list_backups()
            target_backup = None

            for backup in backups:
                if backup["migration_id"] == self.migration_id:
                    target_backup = Path(backup["backup_path"])
                    break

            if not target_backup:
                logger.error(f"No backup found for migration: {self.migration_id}")
                return False

            # Restore from backup
            success = self.backup_manager.restore_from_backup(target_backup)

            if success:
                logger.info("Migration rollback completed successfully")
                # Mark migration as incomplete
                self.tracker.set_migration_complete(False)
            else:
                logger.error("Migration rollback failed")

            return success

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def validate_migration_state(self) -> dict[str, Any]:
        """Validate current migration state."""
        return self.validator.run_comprehensive_validation()

    def get_migration_status(self) -> dict[str, Any]:
        """Get comprehensive migration status."""
        return {
            "migration_id": self.migration_id,
            "status": self.tracker.get_status().get_summary(),
            "backups_available": len(self.backup_manager.list_backups()),
            "validation_results": self.validator.validation_results,
        }

    def finalize_migration(self) -> bool:
        """Finalize migration after successful completion."""
        try:
            # Run final validation
            validation_results = self.validator.run_comprehensive_validation()

            if validation_results["overall_summary"]["status"] == "failed":
                logger.error("Final validation failed - migration not finalized")
                return False

            # Mark migration as complete
            self.tracker.set_migration_complete(True)

            logger.info("Migration finalized successfully")
            logger.info(f"Migration summary: {self.tracker.get_status().get_summary()}")

            return True

        except Exception as e:
            logger.error(f"Failed to finalize migration: {e}")
            return False


# Convenience functions for easy usage
def create_migration_framework(migration_name: str = "mobile_only_refactoring") -> MigrationSafetyFramework:
    """Create and initialize migration safety framework."""
    return MigrationSafetyFramework(migration_name)


def create_safety_checkpoint(framework: MigrationSafetyFramework) -> bool:
    """Create safety checkpoint using framework."""
    return framework.create_safety_checkpoint()


def validate_migration(framework: MigrationSafetyFramework) -> dict[str, Any]:
    """Validate migration using framework."""
    return framework.validate_migration_state()


def rollback_migration(framework: MigrationSafetyFramework) -> bool:
    """Rollback migration using framework."""
    return framework.rollback_migration()
