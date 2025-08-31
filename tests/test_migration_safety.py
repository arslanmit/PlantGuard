from typing import Any, Dict, List, Optional, Tuple, Union, Generator
"""
Test suite for Migration Safety Framework

Tests backup, tracking, rollback, and validation functionality.
"""


import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.migration_safety import (MigrationBackupManager,
                                    MigrationSafetyFramework, MigrationStatus,
                                    MigrationTracker, MigrationValidator)


class TestMigrationStatus:
    """Test MigrationStatus data class."""
    
    def test_migration_status_creation(self) -> None:
        """Test creating migration status."""
        status = MigrationStatus(
            migration_id="test_migration_123",
            start_time="2024-01-01T10:00:00"
        )
        
        assert status.migration_id == "test_migration_123"
        assert status.start_time == "2024-01-01T10:00:00"
        assert status.files_removed == []
        assert status.migration_complete is False
    
    def test_add_removed_file(self) -> None:
        """Test tracking removed files."""
        status = MigrationStatus("test", "2024-01-01T10:00:00")
        
        status.add_removed_file("spa_app.py")
        status.add_removed_file("app.py")
        
        assert "spa_app.py" in status.files_removed
        assert "app.py" in status.files_removed
        assert len(status.files_removed) == 2
        
        # Test duplicate prevention
        status.add_removed_file("spa_app.py")
        assert len(status.files_removed) == 2
    
    def test_add_modified_file(self) -> None:
        """Test tracking modified files."""
        status = MigrationStatus("test", "2024-01-01T10:00:00")
        
        status.add_modified_file("Makefile")
        status.add_modified_file("mobile_spa_app.py")
        
        assert "Makefile" in status.files_modified
        assert "mobile_spa_app.py" in status.files_modified
        assert len(status.files_modified) == 2
    
    def test_get_summary(self) -> None:
        """Test getting migration summary."""
        status = MigrationStatus("test", "2024-01-01T10:00:00")
        status.add_removed_file("spa_app.py")
        status.add_modified_file("Makefile")
        status.migration_complete = True
        
        summary = status.get_summary()
        
        assert summary["migration_id"] == "test"
        assert summary["files_removed"] == 1
        assert summary["files_modified"] == 1
        assert summary["migration_complete"] is True


class TestMigrationBackupManager:
    """Test MigrationBackupManager functionality."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backup_manager = MigrationBackupManager(self.temp_dir / "backups")
        
        # Create test files
        self.test_files = {
            "test_app.py": "print('test app')",
            "test_config.json": '{"test": true}',
            "src/test_module.py": "def test_function(): pass"
        }
        
        for filepath, content in self.test_files.items():
            full_path = self.temp_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
    
    def teardown_method(self) -> Any:
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_full_backup(self) -> None:
        """Test creating full backup."""
        # Change to temp directory for test
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.temp_dir)
            
            backup_path = self.backup_manager.create_full_backup("test_migration")
            
            assert backup_path.exists()
            assert (backup_path / "backup_manifest.json").exists()
            
            # Check manifest
            with open(backup_path / "backup_manifest.json") as f:
                manifest = json.load(f)
            
            assert manifest["migration_id"] == "test_migration"
            assert "backup_timestamp" in manifest
            assert "files_backed_up" in manifest
            
        finally:
            os.chdir(original_cwd)
    
    def test_list_backups(self) -> None:
        """Test listing available backups."""
        # Create test backup directory structure
        backup_dir = self.backup_manager.backup_dir / "backup_test_123"
        backup_dir.mkdir(parents=True)
        
        manifest = {
            "migration_id": "test_123",
            "backup_timestamp": "20240101_100000",
            "files_backed_up": ["test.py"],
            "total_files": 1
        }
        
        with open(backup_dir / "backup_manifest.json", 'w') as f:
            json.dump(manifest, f)
        
        backups = self.backup_manager.list_backups()
        
        assert len(backups) == 1
        assert backups[0]["migration_id"] == "test_123"


class TestMigrationTracker:
    """Test MigrationTracker functionality."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Patch the log file location
        with patch.object(Path, 'cwd', return_value=self.temp_dir):
            self.tracker = MigrationTracker("test_migration")
    
    def teardown_method(self) -> Any:
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_track_file_removal(self) -> None:
        """Test tracking file removal."""
        self.tracker.track_file_removal("spa_app.py")
        
        status = self.tracker.get_status()
        assert "spa_app.py" in status.files_removed
    
    def test_track_file_modification(self) -> None:
        """Test tracking file modification."""
        self.tracker.track_file_modification("Makefile")
        
        status = self.tracker.get_status()
        assert "Makefile" in status.files_modified
    
    def test_track_import_cleanup(self) -> None:
        """Test tracking import cleanup."""
        self.tracker.track_import_cleanup("mobile_spa_app.py", "from spa_app import")
        
        status = self.tracker.get_status()
        assert "mobile_spa_app.py:from spa_app import" in status.imports_cleaned
    
    def test_set_migration_complete(self) -> None:
        """Test setting migration complete."""
        self.tracker.set_migration_complete(True)
        
        status = self.tracker.get_status()
        assert status.migration_complete is True


class TestMigrationValidator:
    """Test MigrationValidator functionality."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        with patch.object(Path, 'cwd', return_value=self.temp_dir):
            self.tracker = MigrationTracker("test_migration")
            self.validator = MigrationValidator(self.tracker)
    
    def teardown_method(self) -> Any:
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_validate_file_integrity_success(self) -> None:
        """Test file integrity validation with all files present."""
        # Create essential files
        essential_files = [
            "mobile_spa_app.py",
            "src/core/vision.py",
            "src/core/audio.py",
            "src/core/nlp.py",
            "Makefile",
            "requirements.txt"
        ]
        
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.temp_dir)
            
            for filepath in essential_files:
                path = Path(filepath)
                path.parent.mkdir(parents=True, exist_ok=True)
                
                if filepath.endswith('.py'):
                    path.write_text("# Valid Python file\nprint('test')")
                else:
                    path.write_text("# Test file content")
            
            result = self.validator.validate_file_integrity()
            
            assert result["status"] == "passed"
            assert len(result["details"]["passed"]) == len(essential_files)
            assert len(result["details"]["failed"]) == 0
            
        finally:
            os.chdir(original_cwd)
    
    def test_validate_file_integrity_missing_files(self) -> None:
        """Test file integrity validation with missing files."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.temp_dir)
            
            result = self.validator.validate_file_integrity()
            
            assert result["status"] == "failed"
            assert len(result["details"]["failed"]) > 0
            
        finally:
            os.chdir(original_cwd)
    
    def test_validate_import_statements(self) -> None:
        """Test import statement validation."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.temp_dir)
            
            # Create test file with desktop imports
            test_file = Path("mobile_spa_app.py")
            test_file.write_text("""
import streamlit as st
from spa_app import desktop_function  # This should be flagged
import mobile_components
""")
            
            result = self.validator.validate_import_statements()
            
            assert result["status"] == "failed"
            assert len(result["details"]["failed"]) > 0
            
        finally:
            os.chdir(original_cwd)
    
    def test_validate_makefile_targets(self) -> None:
        """Test Makefile target validation."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.temp_dir)
            
            # Create Makefile with mobile target
            makefile_content = """
mobile:
\t@echo "Starting mobile app"
\tstreamlit run mobile_spa_app.py

test:
\tpytest tests/
"""
            Path("Makefile").write_text(makefile_content)
            
            result = self.validator.validate_makefile_targets()
            
            assert result["status"] == "passed"
            
        finally:
            os.chdir(original_cwd)


class TestMigrationSafetyFramework:
    """Test complete MigrationSafetyFramework."""
    
    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test project structure
        test_files = {
            "mobile_spa_app.py": "import streamlit as st\nst.write('Mobile App')",
            "spa_app.py": "import streamlit as st\nst.write('Desktop App')",
            "src/core/vision.py": "class VisionAdapter: pass",
            "src/core/audio.py": "class AudioAdapter: pass",
            "src/core/nlp.py": "class TextAdapter: pass",
            "Makefile": "mobile:\n\tstreamlit run mobile_spa_app.py",
            "requirements.txt": "streamlit>=1.28.0"
        }
        
        for filepath, content in test_files.items():
            full_path = self.temp_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
    
    def teardown_method(self) -> Any:
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_framework_initialization(self) -> None:
        """Test framework initialization."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.temp_dir)
            
            framework = MigrationSafetyFramework("test_migration")
            
            assert framework.migration_id.startswith("test_migration_")
            assert framework.backup_manager is not None
            assert framework.tracker is not None
            assert framework.validator is not None
            
        finally:
            os.chdir(original_cwd)
    
    def test_create_safety_checkpoint(self) -> None:
        """Test creating safety checkpoint."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.temp_dir)
            
            framework = MigrationSafetyFramework("test_migration")
            success = framework.create_safety_checkpoint()
            
            assert success is True
            
            status = framework.get_migration_status()
            assert status["status"]["backup_created"] is True
            assert status["status"]["rollback_available"] is True
            
        finally:
            os.chdir(original_cwd)
    
    def test_get_migration_status(self) -> None:
        """Test getting migration status."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(self.temp_dir)
            
            framework = MigrationSafetyFramework("test_migration")
            status = framework.get_migration_status()
            
            assert "migration_id" in status
            assert "status" in status
            assert "backups_available" in status
            
        finally:
            os.chdir(original_cwd)


def test_integration_workflow() -> None:
    """Test complete integration workflow."""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create complete project structure for validation
        test_files = {
            "mobile_spa_app.py": "import streamlit as st\nst.write('Mobile App')",
            "src/core/vision.py": "class VisionAdapter: pass",
            "src/core/audio.py": "class AudioAdapter: pass", 
            "src/core/nlp.py": "class TextAdapter: pass",
            "Makefile": "mobile:\n\tstreamlit run mobile_spa_app.py",
            "requirements.txt": "streamlit>=1.28.0"
        }
        
        for filepath, content in test_files.items():
            full_path = temp_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        original_cwd = Path.cwd()
        import os
        os.chdir(temp_dir)
        
        # 1. Create framework
        framework = MigrationSafetyFramework("integration_test")
        
        # 2. Create safety checkpoint
        success = framework.create_safety_checkpoint()
        assert success is True
        
        # 3. Simulate some migration changes
        framework.tracker.track_file_removal("spa_app.py")
        framework.tracker.track_file_modification("Makefile")
        
        # 4. Validate migration state
        validation_results = framework.validate_migration_state()
        assert "overall_summary" in validation_results
        
        # 5. Get status
        status = framework.get_migration_status()
        assert status["status"]["files_removed"] == 1
        assert status["status"]["files_modified"] == 1
        
        # 6. Finalize migration
        framework.tracker.set_migration_complete(True)
        finalized = framework.finalize_migration()
        assert finalized is True
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])