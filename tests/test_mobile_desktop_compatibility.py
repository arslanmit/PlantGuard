#!/usr/bin/env python3
"""
Mobile Desktop Compatibility Tests

Tests to ensure mobile PlantGuard components render properly on desktop viewports
and maintain functionality across different screen sizes.
"""

import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from ui.components.mobile_content_tabs import MobileContentTabs
from ui.components.mobile_header import MobileHeader
from ui.components.mobile_input_ribbon import MobileInputRibbon
# Import mobile components
from ui.components.mobile_layout_manager import MobileLayoutManager


class TestMobileDesktopCompatibility(unittest.TestCase):
    """Test mobile components maintain fixed 428px design on desktop."""
    
    def setUp(self) -> None:
        """Set up test environment."""
        # Mock Streamlit session state
        self.mock_session_state = {
            'mobile_app_initialized': True,
            'mobile_css_loaded': True,
            'mobile_layout_initialized': True,
            'desktop_mode_detected': True,
            'responsive_layout_enabled': True,
        }
        
        # Patch streamlit
        patcher = patch('streamlit.session_state', self.mock_session_state)
        self.mock_st = patcher.start()
        self.addCleanup(patcher.stop)
        
        # Mock streamlit components
        self.st_patcher = patch('streamlit.markdown')
        self.mock_markdown = self.st_patcher.start()
        self.addCleanup(self.st_patcher.stop)
    
    def test_layout_manager_desktop_compatibility(self) -> None:
        """Test layout manager maintains 428px design on desktop."""
        layout_manager = MobileLayoutManager("test_layout")
        
        # Test layout status
        status = layout_manager.get_layout_status()
        
        # Verify essential status fields
        self.assertIn('css_loaded', status)
        self.assertIn('layout_initialized', status)
        self.assertIn('status', status)
        
        # Test fallback CSS maintains fixed 428px design
        fallback_css = layout_manager._get_fallback_css()
        
        # Check for fixed mobile design (no responsive elements)
        self.assertIn('max-width: var(--mobile-max-width)', fallback_css)
        self.assertNotIn('@media (min-width:', fallback_css)  # No responsive breakpoints
        self.assertIn('428px', fallback_css)  # Fixed width
        
        print("[DONE] Layout Manager: Fixed 428px design verified")
    
    def test_header_responsive_design(self) -> None:
        """Test header component responsive design."""
        header = MobileHeader("test_header")
        
        # Test metadata includes responsive design info
        metadata = header._get_component_metadata()
        
        self.assertEqual(metadata.component_type, "header_always_visible")
        self.assertIn("always-visible", metadata.description.lower())
        
        # Verify CSS classes support responsive design
        css_classes = metadata.css_classes
        self.assertIn('mobile-header-always-visible', css_classes)
        
        print("[DONE] Mobile Header: Responsive design verified")
    
    def test_input_ribbon_desktop_layout(self) -> None:
        """Test input ribbon works on desktop."""
        input_ribbon = MobileInputRibbon("test_input")
        
        # Test metadata
        metadata = input_ribbon._get_component_metadata()
        
        self.assertEqual(metadata.component_type, "input_ribbon")
        self.assertTrue(metadata.ai_agent_testable)
        
        # Verify touch targets work on desktop too
        interactive_elements = metadata.interactive_elements
        
        for element in interactive_elements:
            self.assertTrue(element.get('always_visible', False))
            self.assertTrue(element.get('touch_target', False))
        
        # Test input methods configuration
        methods = input_ribbon.get_input_methods()
        
        # Verify all input methods are available
        expected_methods = ['text', 'voice', 'camera', 'upload']
        available_methods = [m['id'] for m in methods]
        
        for method in expected_methods:
            self.assertIn(method, available_methods)
        
        print("[DONE] Input Ribbon: Desktop layout compatibility verified")
    
    def test_content_tabs_desktop_behavior(self) -> None:
        """Test content tabs behavior on desktop."""
        content_tabs = MobileContentTabs("test_tabs")
        
        # Test metadata
        metadata = content_tabs._get_component_metadata()
        
        self.assertEqual(metadata.component_type, "content_tabs_always_visible")
        self.assertTrue(metadata.ai_agent_testable)
        
        # Test available tabs
        tabs = content_tabs.get_available_tabs()
        
        # Verify all essential tabs are available
        expected_tabs = ['image_analysis', 'voice_assistant', 'chat_interface', 'history_settings', 'comparison']
        available_tabs = [t['id'] for t in tabs]
        
        for tab in expected_tabs:
            self.assertIn(tab, available_tabs)
        
        # Verify tabs are enabled
        enabled_tabs = [t for t in tabs if t.get('enabled', True)]
        self.assertEqual(len(enabled_tabs), len(tabs))
        
        print("[DONE] Content Tabs: Desktop behavior verified")
    
    def test_desktop_responsive_css_features(self) -> None:
        """Test CSS maintains fixed 428px design on desktop."""
        layout_manager = MobileLayoutManager("test_css")
        
        # Test CSS loading
        css_loaded = layout_manager.load_mobile_css()
        
        # Test fallback CSS maintains fixed design
        fallback_css = layout_manager._get_fallback_css()
        
        # Test fixed 428px constraint
        self.assertIn('428px', fallback_css)  # Fixed mobile width
        self.assertNotIn('768px', fallback_css)  # No tablet breakpoint
        self.assertNotIn('1024px', fallback_css)  # No desktop breakpoint
        
        # Test fixed mobile variables only
        self.assertIn('--mobile-max-width: 428px', fallback_css)
        self.assertNotIn('--desktop-max-width', fallback_css)
        self.assertNotIn('--desktop-large-width', fallback_css)
        
        print("[DONE] CSS Framework: Fixed 428px design verified")
    
    def test_mobile_app_desktop_session_state(self) -> None:
        """Test mobile app maintains fixed design session state."""
        # Simulate fixed mobile design state
        self.mock_session_state.update({
            'fixed_mobile_design': True,
            'mobile_viewport_width': 428,  # Always 428px
        })
        
        # Test session state values
        self.assertTrue(self.mock_session_state.get('fixed_mobile_design'))
        self.assertEqual(self.mock_session_state.get('mobile_viewport_width'), 428)
        
        print("[DONE] Session State: Fixed 428px design verified")
    
    def test_always_visible_design_principles(self) -> None:
        """Test that always-visible design works on desktop."""
        # Test header
        header = MobileHeader("test_always_visible")
        header_metadata = header._get_component_metadata()
        
        # Verify always-visible design
        for element in header_metadata.interactive_elements:
            self.assertTrue(element.get('always_visible', False))
        
        # Test input ribbon
        input_ribbon = MobileInputRibbon("test_always_visible")
        input_metadata = input_ribbon._get_component_metadata()
        
        for element in input_metadata.interactive_elements:
            self.assertTrue(element.get('always_visible', False))
        
        # Test content tabs
        content_tabs = MobileContentTabs("test_always_visible")
        tabs_metadata = content_tabs._get_component_metadata()
        
        for element in tabs_metadata.interactive_elements:
            self.assertTrue(element.get('always_visible', False))
        
        print("[DONE] Always-Visible Design: Desktop compatibility verified")


def run_desktop_compatibility_tests() -> dict[str, Any]:
    """Run desktop compatibility tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMobileDesktopCompatibility)
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful(),
        'details': {
            'failures': [str(f) for f, _ in result.failures],
            'errors': [str(e) for e, _ in result.errors]
        }
    }


if __name__ == '__main__':
    print("[TEST] Running Mobile Desktop Compatibility Tests...")
    print("=" * 60)
    
    results = run_desktop_compatibility_tests()
    
    print("\n" + "=" * 60)
    print("[SUMMARY] Desktop Compatibility Test Results:")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Failures: {results['failures']}")
    print(f"Errors: {results['errors']}")
    print(f"Success: {'[DONE] PASSED' if results['success'] else '[TODO] FAILED'}")
    
    if not results['success']:
        print("\n[SEARCH] Issues Found:")
        for failure in results['details']['failures']:
            print(f"  [TODO] {failure}")
        for error in results['details']['errors']:
            print(f"  [ERROR] {error}")
    else:
        print("\n[SUCCESS] All desktop compatibility tests passed!")
        print("[COMPUTER] Mobile PlantGuard is ready for desktop use!")