from typing import Any, Dict, List, Optional, Tuple, Union, Generator
#!/usr/bin/env python3
"""
Integration test for Migration Safety Framework

This script tests the complete migration safety workflow in a controlled environment.
"""


import shutil
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.migration_safety import MigrationSafetyFramework


def create_test_project(temp_dir: Path) -> Any:
    """Create a test project structure."""
    test_files = {
        # Main applications
        "mobile_spa_app.py": """
import streamlit as st
from src.core.vision import VisionAdapter
from src.core.audio import AudioAdapter
from src.core.nlp import TextAdapter

st.title("PlantGuard Mobile")
st.write("Mobile-only plant disease detection")
""",
        "spa_app.py": """
import streamlit as st
from src.core.vision import VisionAdapter

st.title("PlantGuard Desktop SPA")
st.write("Desktop single-page application")
""",
        "app.py": """
import streamlit as st

st.title("PlantGuard Legacy")
st.write("Legacy multi-page application")
""",
        # Core adapters
        "src/core/__init__.py": "",
        "src/core/vision.py": """
class VisionAdapter:
    def predict(self, image) -> str:
        return "healthy", 0.95
""",
        "src/core/audio.py": """
class AudioAdapter:
    def transcribe(self, audio) -> str:
        return "plant looks healthy"
""",
        "src/core/nlp.py": """
class TextAdapter:
    def extract_features(self, text) -> List[Any]:
        return [0.1, 0.2, 0.3]
""",
        # UI components
        "src/ui/__init__.py": "",
        "src/ui/components/__init__.py": "",
        "src/ui/components/mobile_header.py": """
import streamlit as st
from spa_app import desktop_function  # This should be cleaned

def mobile_header() -> Any:
    st.header("Mobile Header")
""",
        # Configuration and build files
        "Makefile": """
# Desktop targets (to be removed)
run:
\t@echo "Starting desktop SPA"
\tstreamlit run spa_app.py

spa-dev:
\t@echo "Desktop development mode"
\tstreamlit run spa_app.py --server.port 8501

spa-prod:
\t@echo "Desktop production mode"
\tstreamlit run spa_app.py --server.headless true

# Mobile targets (to be kept)
mobile:
\t@echo "Starting mobile app"
\tstreamlit run mobile_spa_app.py --server.port 8502

m: mobile

test:
\tpytest tests/
""",
        "requirements.txt": """
streamlit>=1.28.0
torch>=2.0.0
transformers>=4.20.0
Pillow>=9.0.0
""",
        "README.md": """
# PlantGuard

Plant disease detection system with desktop and mobile interfaces.

## Usage

- Desktop: `make run`
- Mobile: `make mobile`
""",
        # Test files
        "test_spa_navigation.py": """
def test_spa_navigation() -> None:
    assert True
""",
        "test_unified_ui.py": """
def test_unified_ui() -> None:
    assert True
""",
        "test_mobile_integration.py": """
def test_mobile_integration() -> None:
    assert True
""",
    }

    for filepath, content in test_files.items():
        full_path = temp_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    print(f"Created test project with {len(test_files)} files")


def simulate_migration_changes(framework: MigrationSafetyFramework) -> Any:
    """Simulate the migration changes."""
    print("\n=== Simulating Migration Changes ===")

    # 1. Remove desktop files
    desktop_files = ["spa_app.py", "app.py", "test_spa_navigation.py", "test_unified_ui.py"]

    for file_path in desktop_files:
        Path(file_path).unlink(missing_ok=True)
        framework.tracker.track_file_removal(file_path)
        print(f"✓ Removed: {file_path}")

    # 2. Clean up imports
    mobile_header_file = Path("src/ui/components/mobile_header.py")
    if mobile_header_file.exists():
        content = mobile_header_file.read_text()
        # Remove desktop import
        cleaned_content = content.replace("from spa_app import desktop_function  # This should be cleaned\n", "")
        mobile_header_file.write_text(cleaned_content)
        framework.tracker.track_file_modification(str(mobile_header_file))
        framework.tracker.track_import_cleanup(str(mobile_header_file), "from spa_app import desktop_function")
        print(f"✓ Cleaned imports in: {mobile_header_file}")

    # 3. Update Makefile
    makefile = Path("Makefile")
    if makefile.exists():
        content = makefile.read_text()

        # Remove desktop targets and redirect run to mobile
        updated_content = """
# Mobile-only targets
mobile:
\t@echo "Starting mobile app"
\tstreamlit run mobile_spa_app.py --server.port 8502

m: mobile

# Redirect old desktop command to mobile
run: mobile
\t@echo "Desktop interface removed - using mobile interface"

start: mobile

test:
\tpytest tests/
"""
        makefile.write_text(updated_content)
        framework.tracker.track_file_modification("Makefile")
        framework.tracker.track_target_removal("spa-dev")
        framework.tracker.track_target_removal("spa-prod")
        print("✓ Updated Makefile for mobile-only")

    # 4. Update README
    readme = Path("README.md")
    if readme.exists():
        updated_readme = """
# PlantGuard Mobile

Plant disease detection system with mobile-first interface.

## Usage

- Mobile: `make mobile` or `make m`
- Alternative: `make run` (redirects to mobile)

## Migration

This system has been migrated to mobile-only. Desktop SPA interface has been removed.
"""
        readme.write_text(updated_readme)
        framework.tracker.track_file_modification("README.md")
        print("✓ Updated README for mobile-only")


def main() -> None:
    """Run complete integration test."""
    print("=== Migration Safety Framework Integration Test ===")

    # Create temporary directory for test
    temp_dir = Path(tempfile.mkdtemp(prefix="plantguard_migration_test_"))
    original_cwd = Path.cwd()

    try:
        print(f"Test directory: {temp_dir}")

        # Change to test directory
        import os

        os.chdir(temp_dir)

        # 1. Create test project
        print("\n1. Creating test project...")
        create_test_project(temp_dir)

        # 2. Initialize migration framework
        print("\n2. Initializing migration safety framework...")
        framework = MigrationSafetyFramework("integration_test")
        print(f"Migration ID: {framework.migration_id}")

        # 3. Create safety checkpoint
        print("\n3. Creating safety checkpoint...")
        success = framework.create_safety_checkpoint()

        if not success:
            print("[TODO] Failed to create safety checkpoint")
            return False

        print("[DONE] Safety checkpoint created")
        status = framework.get_migration_status()
        print(f"Files backed up: {status['status']['files_backed_up']}")

        # 4. Validate initial state
        print("\n4. Validating initial state...")
        initial_validation = framework.validate_migration_state()
        print(f"Initial validation status: {initial_validation['overall_summary']['status']}")

        # 5. Perform migration changes
        print("\n5. Performing migration changes...")
        simulate_migration_changes(framework)

        # 6. Validate post-migration state
        print("\n6. Validating post-migration state...")
        final_validation = framework.validate_migration_state()

        print("\nValidation Results:")
        for test_name, result in final_validation.items():
            if test_name == "overall_summary":
                continue

            status_icon = {"passed": "[DONE]", "warning": "[WARNING]", "failed": "[TODO]"}.get(result["status"], "[UNKNOWN]")

            print(f"  {status_icon} {test_name}: {result['status']}")

            if result["status"] != "passed":
                print(f"     Details: {result['details']}")

        # Overall summary
        summary = final_validation["overall_summary"]
        summary_icon = {"passed": "[DONE]", "warning": "[WARNING]", "failed": "[TODO]"}.get(summary["status"], "[UNKNOWN]")

        print(f"\n{summary_icon} Overall Status: {summary['status']}")
        print(f"  {summary['details']}")

        # 7. Show final migration status
        print("\n7. Final migration status:")
        final_status = framework.get_migration_status()
        migration_status = final_status["status"]

        print(f"  Files Removed: {migration_status['files_removed']}")
        print(f"  Files Modified: {migration_status['files_modified']}")
        print(f"  Imports Cleaned: {migration_status['imports_cleaned']}")
        print(f"  Targets Removed: {migration_status['targets_removed']}")

        # 8. Test rollback capability
        print("\n8. Testing rollback capability...")
        if migration_status["rollback_available"]:
            print("[DONE] Rollback is available")

            # Demonstrate rollback (but don't actually do it)
            print("  Rollback would restore:")
            backups = framework.backup_manager.list_backups()
            if backups:
                backup = backups[0]
                print(f"    - {backup['total_files']} files")
                print(f"    - From backup: {backup['backup_timestamp']}")
        else:
            print("[TODO] Rollback not available")

        # 9. Finalize migration
        print("\n9. Finalizing migration...")
        if summary["status"] in ["passed", "warning"]:
            framework.tracker.set_migration_complete(True)
            finalized = framework.finalize_migration()

            if finalized:
                print("[DONE] Migration finalized successfully")
            else:
                print("[TODO] Migration finalization failed")
        else:
            print("[WARNING]  Migration has validation failures - not finalizing")

        print("\n=== Integration Test Complete ===")
        print(f"Test passed: {summary['status'] in ['passed', 'warning']}")

        return summary["status"] in ["passed", "warning"]

    except Exception as e:
        print(f"[TODO] Integration test failed: {e}")
        return False

    finally:
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
        print(f"Cleaned up test directory: {temp_dir}")


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
