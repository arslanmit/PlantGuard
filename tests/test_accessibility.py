"""Test accessibility functionality for PlantGuard UI components.

This test ensures accessibility features are working correctly.
"""

import sys
import unittest
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestAccessibility(unittest.TestCase):
    """Test accessibility features."""

    def test_accessibility_tester_exists(self):
        """Test that accessibility tester component exists."""

    accessibility_tester_path = Path("src/ui/components/accessibility_tester.py")
    assert accessibility_tester_path.exists(), "AccessibilityTester component should exist"

    def test_accessibility_page_exists(self):
        """Test that accessibility page exists."""

    accessibility_page_path = Path("pages/accessibility.py")
    assert accessibility_page_path.exists(), "Accessibility page should exist"

    def test_aria_labels_implemented(self):
        """Test that ARIA labels are implemented in components."""
        analysis_card_path = Path("src/ui/components/analysis_card.py")
        if analysis_card_path.exists():
            content = analysis_card_path.read_text()
            assert "aria-label" in content, "ARIA labels should be implemented in analysis card"

    def test_screen_reader_support(self):
        """Test that screen reader support is implemented."""
        css_path = Path("assets/styles.css")
        if css_path.exists():
            content = css_path.read_text()
            assert "sr-only" in content, "Screen reader support classes should exist in CSS"

    def test_keyboard_navigation_support(self):
        """Test that keyboard navigation is supported."""
        css_path = Path("assets/styles.css")
        if css_path.exists():
            content = css_path.read_text()
            assert "focus" in content, "Focus styles for keyboard navigation should exist"


if __name__ == "__main__":
    unittest.main()
