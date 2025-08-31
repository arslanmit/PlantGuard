"""
Mobile Test Component for PlantGuard UI.

This module provides a test component to validate the mobile infrastructure
and demonstrate the component architecture for AI agents.
"""

import logging
from typing import Any

import streamlit as st

from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileTestComponent(MobileBaseComponent):
    """Test component for validating mobile infrastructure."""

    def __init__(self, component_id: str, title: str, **kwargs) -> None:
        """
        Initialize test component.

        Args:
            component_id: Unique identifier for this component instance
            title: Display title for the component
            **kwargs: Additional component-specific arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Test-specific metadata
        self.update_metadata(
            {
                "test_component": True,
                "supports_validation": True,
                "supports_error_simulation": True,
                "ai_test_patterns": ["button_click_test", "state_management_test", "error_handling_test", "css_class_test"],
            }
        )

    def render(self) -> None:
        """Render the test component UI."""
        try:
            css_classes = " ".join(self.get_css_classes())

            st.markdown(
                f"""
            <div class="{css_classes}">
                <div class="mobile-card">
                    <div class="mobile-card-header">
                        <h3 class="mobile-card-title">{self.title}</h3>
                        <span class="mobile-status-indicator">
                            <span style="color: var(--success-color);">●</span> Active
                        </span>
                    </div>
                    <div class="mobile-card-content">
                        <p>Mobile infrastructure test component</p>
                        <div class="mobile-test-info">
                            <strong>Component ID:</strong> {self.component_id}<br>
                            <strong>Component Type:</strong> {self.component_type}<br>
                            <strong>CSS Classes:</strong> {", ".join(self.get_css_classes())}<br>
                            <strong>State Key:</strong> {self._component_metadata["state_key"]}
                        </div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Render test controls
            self._render_test_controls()

            # Render state display
            self._render_state_display()

        except Exception as e:
            logger.error(f"Test component rendering failed: {e}")
            raise

    def _render_test_controls(self) -> None:
        """Render test control buttons."""
        st.markdown("### Test Controls")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("[TEST] Test State", key=f"{self.component_id}_test_state"):
                self._test_state_management()

        with col2:
            if st.button("[WARNING] Test Error", key=f"{self.component_id}_test_error"):
                self._test_error_handling()

        with col3:
            if st.button("[PARTIAL] Reset", key=f"{self.component_id}_reset"):
                self._reset_component()

    def _render_state_display(self) -> None:
        """Render current state display."""
        st.markdown("### Current State")

        state = self.get_state()

        # Display key state information
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**UI State:**")
            ui_state = state.get("ui_state", {})
            for key, value in ui_state.items():
                icon = "[DONE]" if value else "[TODO]"
                st.markdown(f"- {key}: {icon} {value}")

        with col2:
            st.markdown("**Component Info:**")
            st.markdown(f"- Visible: {'[DONE]' if self.is_visible() else '[TODO]'}")
            st.markdown(f"- Loading: {'[DONE]' if self.is_loading() else '[TODO]'}")
            st.markdown(f"- Disabled: {'[DONE]' if self.is_disabled() else '[TODO]'}")
            st.markdown(f"- Has Error: {'[DONE]' if self.has_error() else '[TODO]'}")

        # Display full state in expander
        with st.expander("Full State (for AI Agent Debugging)"):
            st.json(state)

    def _test_state_management(self) -> None:
        """Test state management functionality."""
        try:
            # Update component data
            test_data = {
                "test_timestamp": st.session_state.get("test_timestamp", 0) + 1,
                "test_message": f"State test #{st.session_state.get('test_timestamp', 0) + 1}",
                "test_values": {"string_value": "test_string", "number_value": 42, "boolean_value": True, "list_value": [1, 2, 3]},
            }

            # Update state
            self.update_state({"data": test_data})

            # Store test timestamp in session state
            st.session_state["test_timestamp"] = test_data["test_timestamp"]

            st.success(f"[DONE] State management test completed! Test #{test_data['test_timestamp']}")

        except Exception as e:
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.MEDIUM, "State management test failed")

    def _test_error_handling(self) -> None:
        """Test error handling functionality."""
        try:
            # Simulate different types of errors
            error_type = st.session_state.get("error_test_type", 0) % 4

            if error_type == 0:
                # Component error
                raise ValueError("Simulated component error for testing")
            elif error_type == 1:
                # Validation error
                self.handle_error(
                    ValueError("Invalid input provided"),
                    ErrorCategory.VALIDATION,
                    ErrorSeverity.LOW,
                    "Test validation error - please check your input",
                )
            elif error_type == 2:
                # Network error
                self.handle_error(
                    ConnectionError("Network connection failed"),
                    ErrorCategory.NETWORK,
                    ErrorSeverity.MEDIUM,
                    "Test network error - connection unavailable",
                )
            else:
                # Permission error
                self.handle_error(
                    PermissionError("Access denied"), ErrorCategory.PERMISSION, ErrorSeverity.HIGH, "Test permission error - access denied"
                )

            # Increment error test type for next test
            st.session_state["error_test_type"] = error_type + 1

        except Exception as e:
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.MEDIUM, "Error handling test encountered an error")

    def _reset_component(self) -> None:
        """Reset component to initial state."""
        try:
            # Clear component state
            self.clear_state()

            # Clear any errors
            self.clear_error()

            # Reset session state test counters
            if "test_timestamp" in st.session_state:
                del st.session_state["test_timestamp"]
            if "error_test_type" in st.session_state:
                del st.session_state["error_test_type"]

            st.success("[DONE] Component reset successfully!")

            # Force rerun to show updated state
            st.experimental_rerun()

        except Exception as e:
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.MEDIUM, "Component reset failed")

    def validate_input(self, input_data: Any) -> dict[str, Any]:
        """
        Validate test component input.

        Args:
            input_data: Input data to validate

        Returns:
            Validation result dictionary
        """
        validation_result = super().validate_input(input_data)

        # Add test-specific validation
        if isinstance(input_data, dict):
            if "test_field" in input_data:
                test_value = input_data["test_field"]
                if not isinstance(test_value, str) or len(test_value) < 3:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append("Test field must be a string with at least 3 characters")

        return validation_result

    def get_test_results(self) -> dict[str, Any]:
        """
        Get test results for AI agent validation.

        Returns:
            Test results dictionary
        """
        state = self.get_state()

        return {
            "component_initialized": state.get("initialized", False),
            "state_management_working": "data" in state and bool(state["data"]),
            "error_handling_working": self.error_handler.get_error_statistics()["total_errors"] > 0,
            "css_classes_generated": len(self.get_css_classes()) > 0,
            "metadata_available": bool(self._component_metadata),
            "ui_state_functional": "ui_state" in state,
            "validation_functional": "validation" in state,
            "last_test_timestamp": state.get("data", {}).get("test_timestamp", 0),
        }

    def run_automated_tests(self) -> dict[str, bool]:
        """
        Run automated tests for AI agent validation.

        Returns:
            Dictionary of test results
        """
        test_results = {}

        try:
            # Test 1: State management
            original_state = self.get_state()
            self.update_state({"data": {"test": "automated_test"}})
            updated_state = self.get_state()
            test_results["state_management"] = updated_state["data"]["test"] == "automated_test"

            # Test 2: UI state management
            self.set_loading(True)
            test_results["ui_state_loading"] = self.is_loading()
            self.set_loading(False)

            self.set_disabled(True)
            test_results["ui_state_disabled"] = self.is_disabled()
            self.set_disabled(False)

            # Test 3: CSS class generation
            css_classes = self.get_css_classes()
            test_results["css_classes"] = len(css_classes) >= 4  # Should have at least 4 classes

            # Test 4: Metadata availability
            metadata = self.get_metadata()
            test_results["metadata"] = all(key in metadata for key in ["component_id", "component_type", "css_classes"])

            # Test 5: Error handling (without actually triggering errors)
            test_results["error_handler"] = hasattr(self, "error_handler") and self.error_handler is not None

            # Test 6: Validation
            validation_result = self.validate_input({"test_field": "valid_test_input"})
            test_results["validation"] = validation_result["is_valid"]

        except Exception as e:
            logger.error(f"Automated test failed: {e}")
            test_results["automated_test_error"] = str(e)

        return test_results
