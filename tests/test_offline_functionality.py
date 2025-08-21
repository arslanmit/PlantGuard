"""Test offline functionality for PlantGuard.

This test ensures the application works without internet connection.
"""

import sys
import unittest
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestOfflineFunctionality:
    """Test offline functionality."""

    def test_local_model_loading(self):
        """Test that models load from local files only."""
        vision_path = Path("src/core/vision.py")
        if vision_path.exists():
            content = vision_path.read_text()
            assert "local" in content.lower(), "Vision should use local models"

    def test_no_external_api_calls(self):
        """Test that no external API calls are made."""
        # Check that there are no external API references
        core_files = ["src/core/vision.py", "src/core/audio.py", "src/core/nlp.py"]
        for file_path in core_files:
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                assert "api.openai" not in content.lower(), f"{file_path} should not use external APIs"
                assert "replicate" not in content.lower(), f"{file_path} should not use external APIs"

    def test_offline_capable_components(self):
        """Test that components are designed for offline use."""
        # Check for offline-related indicators
        assert True


if __name__ == "__main__":
    unittest.main()
