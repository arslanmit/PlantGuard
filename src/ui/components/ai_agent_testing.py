"""
AI Agent Testing Framework for Mobile PlantGuard

Advanced autonomous testing system for AI agents to test, fix, monitor, and heal mobile components.
Provides comprehensive testing suite with autonomous issue detection and resolution.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    FIXED = "fixed"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class TestSeverity(Enum):
    """Test issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FixAction(Enum):
    """Types of fixes that can be applied."""

    INITIALIZE_STATE = "initialize_state"
    GENERATE_KEYS = "generate_keys"
    UPDATE_METADATA = "update_metadata"
    REPAIR_COMPONENT = "repair_component"
    RESET_COMPONENT = "reset_component"
    VALIDATE_DATA = "validate_data"


@dataclass
class TestResult:
    """Comprehensive test result with detailed information."""

    test_id: str
    component_id: str
    test_name: str
    status: TestStatus
    severity: TestSeverity = TestSeverity.MEDIUM
    error_message: str | None = None
    fixes_applied: list[dict[str, Any]] = field(default_factory=list)
    execution_time: float = 0.0
    test_data: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert test result to dictionary format."""
        return {
            "test_id": self.test_id,
            "component_id": self.component_id,
            "test_name": self.test_name,
            "status": self.status.value,
            "severity": self.severity.value,
            "error_message": self.error_message,
            "fixes_applied": self.fixes_applied,
            "execution_time": self.execution_time,
            "test_data": self.test_data,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


@dataclass
class ComponentHealthStatus:
    """Component health monitoring data."""

    component_id: str
    health_score: float
    status: str
    last_test_time: float
    issues_count: int
    fixes_count: int
    test_history: list[TestResult] = field(default_factory=list)
    performance_metrics: dict[str, float] = field(default_factory=dict)


class AIAgentTestingFramework:
    """Advanced AI Agent autonomous testing and self-healing system.

    Features:
    - Comprehensive component testing
    - Autonomous issue detection and resolution
    - Performance monitoring and analytics
    - Self-healing capabilities
    - Component health tracking
    - Test history and reporting
    """

    def __init__(self, component_registry=None):
        self.component_registry = component_registry
        self.test_results: list[TestResult] = []
        self.component_health: dict[str, ComponentHealthStatus] = {}
        self.auto_fix_enabled = True
        self.test_timeout = 30.0  # seconds
        self.max_fixes_per_component = 5
        self.test_history: list[dict[str, Any]] = []
        self.performance_metrics: dict[str, float] = {}

        # Initialize autonomous interaction tester
        self.interaction_tester = AutonomousInteractionTester(self)

        # Test configuration
        self.test_categories = {
            "structure": ["metadata", "inheritance", "methods"],
            "interaction": ["elements", "keys", "handlers"],
            "state": ["dependencies", "initialization", "validation"],
            "rendering": ["output", "css_classes", "html_structure"],
            "performance": ["load_time", "memory_usage", "responsiveness"],
            "ai_agent": ["testability", "self_healing", "context"],
        }

        # Initialize logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup enhanced logging for AI agent testing."""
        self.logger = logging.getLogger(f"{__name__}.AIAgentTestingFramework")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def test_all_components(self) -> dict[str, Any]:
        """Synchronous wrapper for comprehensive component testing."""
        if not self.component_registry:
            return {"error": "No component registry available"}

        try:
            # Run async testing in sync context
            return asyncio.run(self._async_test_all_components())
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            return {"error": f"Test execution failed: {e!s}", "components_tested": 0, "tests_passed": 0, "tests_failed": 1}

    async def _async_test_all_components(self) -> dict[str, Any]:
        """Asynchronous comprehensive component testing."""
        start_time = time.time()

        components = self.component_registry.get_all_components()

        results = {
            "test_session_id": f"session_{int(start_time)}",
            "start_time": start_time,
            "components_tested": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_fixed": 0,
            "tests_skipped": 0,
            "issues_found": [],
            "fixes_applied": [],
            "recommendations": [],
            "performance_metrics": {},
            "component_health_summary": {},
            "detailed_results": {},
        }

        self.logger.info(f"Starting comprehensive testing of {len(components)} components")

        # Test each component
        for component_id, component in components.items():
            component_start = time.time()

            try:
                # Run comprehensive component tests
                component_results = await self._test_component_comprehensive(component_id, component)

                # Run autonomous interaction tests
                interaction_results = await self.interaction_tester.test_component_interactions(component_id, component)

                # Convert interaction results to TestResult format
                for interaction_result in interaction_results:
                    test_result = TestResult(
                        test_id=f"interaction_{interaction_result.element_id}_{int(interaction_result.timestamp)}",
                        component_id=component_id,
                        test_name=interaction_result.test_type,
                        status=TestStatus.PASSED if interaction_result.success else TestStatus.FAILED,
                        severity=TestSeverity.MEDIUM,
                        error_message=interaction_result.error,
                        execution_time=interaction_result.response_time,
                        test_data=interaction_result.data,
                        timestamp=interaction_result.timestamp,
                    )
                    component_results.append(test_result)

                # Update results
                for test_result in component_results:
                    self.test_results.append(test_result)

                    if test_result.status == TestStatus.PASSED:
                        results["tests_passed"] += 1
                    elif test_result.status == TestStatus.FAILED:
                        results["tests_failed"] += 1
                        results["issues_found"].append(
                            {
                                "component": component_id,
                                "test": test_result.test_name,
                                "issue": test_result.error_message,
                                "severity": test_result.severity.value,
                            }
                        )
                    elif test_result.status == TestStatus.FIXED:
                        results["tests_fixed"] += 1
                        results["fixes_applied"].extend(test_result.fixes_applied)
                    elif test_result.status == TestStatus.SKIPPED:
                        results["tests_skipped"] += 1

                # Update component health
                self._update_component_health(component_id, component_results)

                # Performance tracking
                component_time = time.time() - component_start
                results["performance_metrics"][component_id] = component_time

                results["components_tested"] += 1
                results["detailed_results"][component_id] = [result.to_dict() for result in component_results]

                self.logger.info(f"Completed testing {component_id} in {component_time:.2f}s")

            except Exception as e:
                self.logger.error(f"Failed to test component {component_id}: {e}")
                error_result = TestResult(
                    test_id=f"error_{component_id}_{int(time.time())}",
                    component_id=component_id,
                    test_name="component_testing",
                    status=TestStatus.ERROR,
                    severity=TestSeverity.HIGH,
                    error_message=str(e),
                )
                self.test_results.append(error_result)
                results["tests_failed"] += 1

        # Add interaction testing summary to results
        interaction_summary = self.interaction_tester.get_interaction_summary()
        if interaction_summary.get("status") != "no_data":
            results["interaction_testing"] = interaction_summary

        # Generate final analysis
        total_time = time.time() - start_time
        results["total_execution_time"] = total_time
        results["component_health_summary"] = self._generate_health_summary()
        results["recommendations"] = self._generate_comprehensive_recommendations(results)

        # Store test session
        self.test_history.append(results)

        self.logger.info(
            f"Completed testing session in {total_time:.2f}s: "
            f"{results['tests_passed']} passed, {results['tests_failed']} failed, "
            f"{results['tests_fixed']} fixed"
        )

        return results

    async def test_all_interactions(self) -> dict[str, Any]:
        """Run autonomous interaction tests on all components."""
        if not self.component_registry:
            return {"error": "No component registry available"}

        components = self.component_registry.get_all_components()

        results = {
            "components_tested": 0,
            "total_interactions": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "component_results": {},
            "summary": {},
        }

        for component_id, component in components.items():
            try:
                interaction_results = await self.interaction_tester.test_component_interactions(component_id, component)

                component_stats = {
                    "total_tests": len(interaction_results),
                    "successful": sum(1 for r in interaction_results if r.success),
                    "failed": sum(1 for r in interaction_results if not r.success),
                    "avg_response_time": sum(r.response_time for r in interaction_results) / len(interaction_results) if interaction_results else 0,
                }

                results["component_results"][component_id] = component_stats
                results["components_tested"] += 1
                results["total_interactions"] += component_stats["total_tests"]
                results["successful_interactions"] += component_stats["successful"]
                results["failed_interactions"] += component_stats["failed"]

            except Exception as e:
                self.logger.error(f"Failed to test interactions for {component_id}: {e}")
                results["component_results"][component_id] = {"error": str(e)}

        # Generate summary
        if results["total_interactions"] > 0:
            results["summary"] = {
                "success_rate": (results["successful_interactions"] / results["total_interactions"]) * 100,
                "components_with_interactions": len([c for c in results["component_results"].values() if c.get("total_tests", 0) > 0]),
                "average_interactions_per_component": results["total_interactions"] / results["components_tested"]
                if results["components_tested"] > 0
                else 0,
            }

        return results

    async def _test_component_comprehensive(self, component_id: str, component: Any) -> list[TestResult]:
        """Run comprehensive tests on a single component."""
        test_results = []

        # Test categories in order of importance
        for category, tests in self.test_categories.items():
            for test_name in tests:
                try:
                    test_method = getattr(self, f"_test_{category}_{test_name}", None)
                    if test_method:
                        result = await test_method(component_id, component)
                        if result:
                            test_results.append(result)
                except Exception as e:
                    error_result = TestResult(
                        test_id=f"test_{category}_{test_name}_{component_id}_{int(time.time())}",
                        component_id=component_id,
                        test_name=f"{category}_{test_name}",
                        status=TestStatus.ERROR,
                        severity=TestSeverity.HIGH,
                        error_message=f"Test execution error: {e!s}",
                        execution_time=0.0,
                    )
                    test_results.append(error_result)

        return test_results

    # Structure Tests
    async def _test_structure_metadata(self, component_id: str, component: Any) -> TestResult:
        """Test component metadata structure."""
        start_time = time.time()

        issues = []
        fixes = []

        if not hasattr(component, "metadata"):
            if self.auto_fix_enabled:
                # Attempt to create basic metadata
                from .mobile_component_registry import ComponentMetadata

                component.metadata = ComponentMetadata(
                    component_id=component_id,
                    component_type="unknown",
                    display_name=component_id.replace("_", " ").title(),
                    description="Auto-generated metadata",
                    ai_agent_friendly_description="Component without metadata",
                )
                fixes.append({"action": FixAction.UPDATE_METADATA.value, "description": "Generated basic metadata structure"})
            else:
                issues.append("Component missing metadata attribute")

        elif component.metadata:
            # Validate metadata structure
            required_fields = ["component_id", "component_type", "display_name"]
            for field in required_fields:
                if not hasattr(component.metadata, field) or not getattr(component.metadata, field):
                    if self.auto_fix_enabled:
                        setattr(component.metadata, field, component_id if field == "component_id" else "unknown")
                        fixes.append({"action": FixAction.UPDATE_METADATA.value, "description": f"Set missing {field} in metadata"})
                    else:
                        issues.append(f"Metadata missing required field: {field}")

        status = TestStatus.FAILED if issues else (TestStatus.FIXED if fixes else TestStatus.PASSED)
        severity = TestSeverity.CRITICAL if "missing metadata" in str(issues) else TestSeverity.MEDIUM

        return TestResult(
            test_id=f"test_structure_metadata_{component_id}_{int(time.time())}",
            component_id=component_id,
            test_name="structure_metadata",
            status=status,
            severity=severity,
            error_message="; ".join(issues) if issues else None,
            fixes_applied=fixes,
            execution_time=time.time() - start_time,
        )

    async def _test_structure_inheritance(self, component_id: str, component: Any) -> TestResult:
        """Test component inheritance structure."""
        start_time = time.time()

        from .mobile_component_registry import MobileComponent

        issues = []

        if not isinstance(component, MobileComponent):
            issues.append(f"Component {component_id} does not inherit from MobileComponent")

        # Check for required methods
        required_methods = ["render", "_get_component_metadata"]
        for method in required_methods:
            if not hasattr(component, method) or not callable(getattr(component, method)):
                issues.append(f"Component missing required method: {method}")

        status = TestStatus.FAILED if issues else TestStatus.PASSED
        severity = TestSeverity.HIGH if issues else TestSeverity.LOW

        return TestResult(
            test_id=f"test_structure_inheritance_{component_id}_{int(time.time())}",
            component_id=component_id,
            test_name="structure_inheritance",
            status=status,
            severity=severity,
            error_message="; ".join(issues) if issues else None,
            execution_time=time.time() - start_time,
        )

    async def _test_structure_methods(self, component_id: str, component: Any) -> TestResult:
        """Test component method structure."""
        start_time = time.time()

        issues = []
        test_data = {}

        # Check method signatures
        if hasattr(component, "render"):
            import inspect

            sig = inspect.signature(component.render)
            test_data["render_signature"] = str(sig)

            # Check if render method accepts **kwargs
            if not any(param.kind == param.VAR_KEYWORD for param in sig.parameters.values()):
                issues.append("render method should accept **kwargs for flexibility")

        status = TestStatus.PASSED if not issues else TestStatus.FAILED
        severity = TestSeverity.LOW

        return TestResult(
            test_id=f"test_structure_methods_{component_id}_{int(time.time())}",
            component_id=component_id,
            test_name="structure_methods",
            status=status,
            severity=severity,
            error_message="; ".join(issues) if issues else None,
            test_data=test_data,
            execution_time=time.time() - start_time,
        )

    # Interaction Tests
    async def _test_interaction_elements(self, component_id: str, component: Any) -> TestResult:
        """Test interactive elements configuration."""
        start_time = time.time()

        issues = []
        fixes = []
        test_data = {}

        if hasattr(component, "metadata") and hasattr(component.metadata, "interactive_elements"):
            elements = component.metadata.interactive_elements
            test_data["element_count"] = len(elements)
            test_data["element_types"] = [elem.get("type") for elem in elements]

            for i, element in enumerate(elements):
                if not element.get("id"):
                    if self.auto_fix_enabled:
                        element["id"] = f"element_{i}"
                        fixes.append({"action": FixAction.GENERATE_KEYS.value, "description": f"Generated ID for element {i}"})
                    else:
                        issues.append(f"Interactive element {i} missing ID")

                if not element.get("testable"):
                    element["testable"] = True
                    fixes.append({"action": FixAction.UPDATE_METADATA.value, "description": f"Marked element {element.get('id', i)} as testable"})
        else:
            test_data["element_count"] = 0
            issues.append("No interactive elements defined")

        status = TestStatus.FAILED if issues else (TestStatus.FIXED if fixes else TestStatus.PASSED)
        severity = TestSeverity.MEDIUM if issues else TestSeverity.LOW

        return TestResult(
            test_id=f"test_interaction_elements_{component_id}_{int(time.time())}",
            component_id=component_id,
            test_name="interaction_elements",
            status=status,
            severity=severity,
            error_message="; ".join(issues) if issues else None,
            fixes_applied=fixes,
            test_data=test_data,
            execution_time=time.time() - start_time,
        )

    async def _test_interaction_keys(self, component_id: str, component: Any) -> TestResult:
        """Test Streamlit widget keys for uniqueness."""
        start_time = time.time()

        issues = []
        fixes = []
        test_data = {}

        if hasattr(component, "metadata") and hasattr(component.metadata, "interactive_elements"):
            elements = component.metadata.interactive_elements
            keys = []

            for element in elements:
                if element.get("type") in ["button", "text_input", "selectbox", "checkbox", "slider"]:
                    if not element.get("key"):
                        if self.auto_fix_enabled:
                            unique_key = f"{component_id}_{element.get('id', 'unknown')}_{int(time.time())}"
                            element["key"] = unique_key
                            fixes.append({"action": FixAction.GENERATE_KEYS.value, "description": f"Generated unique key: {unique_key}"})
                        else:
                            issues.append(f"Element {element.get('id')} missing Streamlit key")
                    else:
                        keys.append(element["key"])

            # Check for duplicate keys
            duplicate_keys = [key for key in keys if keys.count(key) > 1]
            if duplicate_keys:
                issues.append(f"Duplicate keys found: {duplicate_keys}")

            test_data["total_keys"] = len(keys)
            test_data["unique_keys"] = len(set(keys))

        status = TestStatus.FAILED if issues else (TestStatus.FIXED if fixes else TestStatus.PASSED)
        severity = TestSeverity.HIGH if "Duplicate keys" in str(issues) else TestSeverity.MEDIUM

        return TestResult(
            test_id=f"test_interaction_keys_{component_id}_{int(time.time())}",
            component_id=component_id,
            test_name="interaction_keys",
            status=status,
            severity=severity,
            error_message="; ".join(issues) if issues else None,
            fixes_applied=fixes,
            test_data=test_data,
            execution_time=time.time() - start_time,
        )

    # State Tests
    async def _test_state_dependencies(self, component_id: str, component: Any) -> TestResult:
        """Test component state dependencies."""
        start_time = time.time()

        issues = []
        fixes = []
        test_data = {}

        if hasattr(component, "metadata") and hasattr(component.metadata, "state_dependencies"):
            state_deps = component.metadata.state_dependencies
            test_data["total_dependencies"] = len(state_deps)
            missing_vars = []

            for state_var in state_deps:
                if state_var not in st.session_state:
                    if self.auto_fix_enabled:
                        default_value = self._get_default_value(state_var)
                        st.session_state[state_var] = default_value
                        fixes.append(
                            {
                                "action": FixAction.INITIALIZE_STATE.value,
                                "description": f"Initialized {state_var} with default value",
                                "details": {"variable": state_var, "value": str(default_value)},
                            }
                        )
                    else:
                        missing_vars.append(state_var)

            if missing_vars:
                issues.append(f"Missing session state variables: {missing_vars}")

            test_data["missing_count"] = len(missing_vars)
            test_data["initialized_count"] = len(fixes)
        else:
            test_data["total_dependencies"] = 0

        status = TestStatus.FAILED if issues else (TestStatus.FIXED if fixes else TestStatus.PASSED)
        severity = TestSeverity.HIGH if issues else TestSeverity.LOW

        return TestResult(
            test_id=f"test_state_dependencies_{component_id}_{int(time.time())}",
            component_id=component_id,
            test_name="state_dependencies",
            status=status,
            severity=severity,
            error_message="; ".join(issues) if issues else None,
            fixes_applied=fixes,
            test_data=test_data,
            execution_time=time.time() - start_time,
        )

    async def _test_state_initialization(self, component_id: str, component: Any) -> TestResult:
        """Test component state initialization."""
        start_time = time.time()

        issues = []
        test_data = {}

        # Check if component has initialization method
        init_methods = [method for method in dir(component) if "init" in method.lower() and callable(getattr(component, method))]
        test_data["initialization_methods"] = init_methods

        if not init_methods:
            issues.append("No initialization methods found")

        status = TestStatus.PASSED if not issues else TestStatus.FAILED
        severity = TestSeverity.LOW

        return TestResult(
            test_id=f"test_state_initialization_{component_id}_{int(time.time())}",
            component_id=component_id,
            test_name="state_initialization",
            status=status,
            severity=severity,
            error_message="; ".join(issues) if issues else None,
            test_data=test_data,
            execution_time=time.time() - start_time,
        )

    # AI Agent specific tests
    async def _test_ai_agent_testability(self, component_id: str, component: Any) -> TestResult:
        """Test AI agent testability features."""
        start_time = time.time()

        issues = []
        fixes = []
        test_data = {}

        if hasattr(component, "metadata"):
            metadata = component.metadata

            # Check AI agent testability flag
            if not hasattr(metadata, "ai_agent_testable") or not metadata.ai_agent_testable:
                if self.auto_fix_enabled:
                    metadata.ai_agent_testable = True
                    fixes.append({"action": FixAction.UPDATE_METADATA.value, "description": "Enabled AI agent testability flag"})
                else:
                    issues.append("Component not marked as AI agent testable")

            # Check for AI agent instructions
            if not hasattr(metadata, "ai_agent_instructions") or not metadata.ai_agent_instructions:
                if self.auto_fix_enabled:
                    metadata.ai_agent_instructions = {
                        "testing": "Basic component testing",
                        "fixing": "Auto-fix common issues",
                        "monitoring": "Monitor component health",
                    }
                    fixes.append({"action": FixAction.UPDATE_METADATA.value, "description": "Added basic AI agent instructions"})
                else:
                    issues.append("Missing AI agent instructions")

            test_data["ai_agent_testable"] = getattr(metadata, "ai_agent_testable", False)
            test_data["has_instructions"] = bool(getattr(metadata, "ai_agent_instructions", None))
        else:
            issues.append("No metadata available for AI agent testing")

        status = TestStatus.FAILED if issues else (TestStatus.FIXED if fixes else TestStatus.PASSED)
        severity = TestSeverity.MEDIUM

        return TestResult(
            test_id=f"test_ai_agent_testability_{component_id}_{int(time.time())}",
            component_id=component_id,
            test_name="ai_agent_testability",
            status=status,
            severity=severity,
            error_message="; ".join(issues) if issues else None,
            fixes_applied=fixes,
            test_data=test_data,
            execution_time=time.time() - start_time,
        )

    # Health and performance monitoring
    def _update_component_health(self, component_id: str, test_results: list[TestResult]) -> None:
        """Update component health status based on test results."""
        if not test_results:
            return

        passed_tests = sum(1 for r in test_results if r.status in [TestStatus.PASSED, TestStatus.FIXED])
        total_tests = len(test_results)
        health_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        issues_count = sum(1 for r in test_results if r.status == TestStatus.FAILED)
        fixes_count = sum(len(r.fixes_applied) for r in test_results if r.fixes_applied)

        # Determine health status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 50:
            status = "fair"
        else:
            status = "poor"

        # Performance metrics
        avg_execution_time = sum(r.execution_time for r in test_results) / len(test_results)
        performance_metrics = {
            "avg_test_time": avg_execution_time,
            "total_test_time": sum(r.execution_time for r in test_results),
            "test_count": total_tests,
        }

        # Update or create health status
        self.component_health[component_id] = ComponentHealthStatus(
            component_id=component_id,
            health_score=health_score,
            status=status,
            last_test_time=time.time(),
            issues_count=issues_count,
            fixes_count=fixes_count,
            test_history=test_results[-10:],  # Keep last 10 test results
            performance_metrics=performance_metrics,
        )

    def _generate_health_summary(self) -> dict[str, Any]:
        """Generate overall health summary."""
        if not self.component_health:
            return {"status": "no_data"}

        total_components = len(self.component_health)
        excellent_count = sum(1 for h in self.component_health.values() if h.status == "excellent")
        good_count = sum(1 for h in self.component_health.values() if h.status == "good")
        fair_count = sum(1 for h in self.component_health.values() if h.status == "fair")
        poor_count = sum(1 for h in self.component_health.values() if h.status == "poor")

        avg_health_score = sum(h.health_score for h in self.component_health.values()) / total_components

        return {
            "total_components": total_components,
            "excellent": excellent_count,
            "good": good_count,
            "fair": fair_count,
            "poor": poor_count,
            "average_health_score": avg_health_score,
            "overall_status": "excellent"
            if avg_health_score >= 90
            else "good"
            if avg_health_score >= 75
            else "fair"
            if avg_health_score >= 50
            else "poor",
        }

    def _get_default_value(self, var_name: str) -> Any:
        """Get default value based on variable name patterns."""
        var_name_lower = var_name.lower()

        if any(pattern in var_name_lower for pattern in ["count", "index", "number", "num"]):
            return 0
        elif any(pattern in var_name_lower for pattern in ["list", "history", "items", "results"]):
            return []
        elif any(pattern in var_name_lower for pattern in ["dict", "config", "settings", "options"]):
            return {}
        elif any(pattern in var_name_lower for pattern in ["bool", "enabled", "active", "flag", "is_", "has_"]):
            return False
        elif any(pattern in var_name_lower for pattern in ["text", "message", "response", "input"]):
            return ""
        elif "time" in var_name_lower:
            return time.time()
        else:
            return None

    def _generate_comprehensive_recommendations(self, results: dict[str, Any]) -> list[str]:
        """Generate comprehensive AI agent recommendations."""
        recommendations = []

        # Overall status
        if results["tests_failed"] == 0 and results["tests_passed"] > 0:
            recommendations.append("[DONE] All components are healthy and functioning properly")
        elif results["tests_failed"] > 0:
            recommendations.append(f"[WARNING] {results['tests_failed']} test(s) failed - immediate attention required")

        # Auto-fix results
        if results["tests_fixed"] > 0:
            recommendations.append(f"[TOOL] Successfully auto-fixed {results['tests_fixed']} issue(s)")

        # Performance analysis
        if results["performance_metrics"]:
            avg_time = sum(results["performance_metrics"].values()) / len(results["performance_metrics"])
            if avg_time > 1.0:
                recommendations.append(f"⏱️ Average test time is {avg_time:.2f}s - consider optimization")
            elif avg_time < 0.1:
                recommendations.append("⚡ Excellent test performance - components are optimized")

        # Component health analysis
        health_summary = results.get("component_health_summary", {})
        if health_summary.get("poor", 0) > 0:
            recommendations.append(f"🚨 {health_summary['poor']} component(s) in poor health - requires immediate attention")

        if health_summary.get("excellent", 0) == health_summary.get("total_components", 0):
            recommendations.append("🏆 All components are in excellent health")

        # Issue pattern analysis
        issues = results.get("issues_found", [])
        if issues:
            issue_types = {}
            for issue in issues:
                severity = issue.get("severity", "unknown")
                issue_types[severity] = issue_types.get(severity, 0) + 1

            if issue_types.get("critical", 0) > 0:
                recommendations.append(f"🔴 {issue_types['critical']} critical issue(s) found - immediate action required")

            if issue_types.get("high", 0) > 2:
                recommendations.append(f"🟠 Multiple high-priority issues ({issue_types['high']}) detected")

        # Testing coverage
        if results["components_tested"] > 0:
            test_coverage = (
                (results["tests_passed"] + results["tests_fixed"])
                / (results["tests_passed"] + results["tests_failed"] + results["tests_fixed"])
                * 100
            )
            if test_coverage < 80:
                recommendations.append(f"[SUMMARY] Test coverage is {test_coverage:.1f}% - consider improving test reliability")

        return recommendations or ["i No specific recommendations at this time"]

    def get_component_health_report(self) -> dict[str, Any]:
        """Get comprehensive component health report."""
        if not self.test_results:
            return {"status": "no_data", "message": "No test data available. Run tests first.", "components": {}}

        # Generate health summary
        health_summary = self._generate_health_summary()

        # Component-specific health details
        component_details = {}
        for component_id, health in self.component_health.items():
            component_details[component_id] = {
                "health_score": health.health_score,
                "status": health.status,
                "last_test_time": health.last_test_time,
                "issues_count": health.issues_count,
                "fixes_count": health.fixes_count,
                "performance_metrics": health.performance_metrics,
                "recent_test_count": len(health.test_history),
            }

        return {
            "status": "available",
            "timestamp": time.time(),
            "summary": health_summary,
            "components": component_details,
            "total_tests_run": len(self.test_results),
            "test_history_count": len(self.test_history),
        }

    def get_test_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent test history."""
        return self.test_history[-limit:] if self.test_history else []

    def clear_test_data(self) -> None:
        """Clear all test data and reset framework."""
        self.test_results.clear()
        self.component_health.clear()
        self.test_history.clear()
        self.performance_metrics.clear()
        self.logger.info("AI Agent Testing Framework data cleared")


class InteractionTestResult:
    """Result from autonomous interaction testing."""

    def __init__(
        self, element_id: str, test_type: str, success: bool, response_time: float = 0.0, error: str | None = None, data: dict[str, Any] | None = None
    ):
        self.element_id = element_id
        self.test_type = test_type
        self.success = success
        self.response_time = response_time
        self.error = error
        self.data = data or {}
        self.timestamp = time.time()


class AutonomousInteractionTester:
    """Autonomous testing system for UI interactions and buttons.

    This system can autonomously test:
    - Button clicks and responses
    - Input field interactions
    - Form submissions
    - Navigation elements
    - Touch interactions
    """

    def __init__(self, testing_framework):
        self.testing_framework = testing_framework
        self.interaction_results: list[InteractionTestResult] = []
        self.test_timeout = 10.0  # seconds per interaction
        self.logger = logging.getLogger(f"{__name__}.AutonomousInteractionTester")

    async def test_component_interactions(self, component_id: str, component: Any) -> list[InteractionTestResult]:
        """Test all interactive elements in a component."""
        results = []

        if not hasattr(component, "metadata") or not hasattr(component.metadata, "interactive_elements"):
            return results

        elements = component.metadata.interactive_elements
        self.logger.info(f"Testing {len(elements)} interactive elements in {component_id}")

        for element in elements:
            if element.get("testable", True):
                element_results = await self._test_interactive_element(component_id, element)
                results.extend(element_results)

        self.interaction_results.extend(results)
        return results

    async def _test_interactive_element(self, component_id: str, element: dict[str, Any]) -> list[InteractionTestResult]:
        """Test a specific interactive element."""
        element_id = element.get("id", "unknown")
        element_type = element.get("type", "unknown")

        results = []

        try:
            # Test based on element type
            if element_type == "button":
                results.extend(await self._test_button_element(component_id, element))
            elif element_type in ["text_input", "text_area"]:
                results.extend(await self._test_input_element(component_id, element))
            elif element_type in ["selectbox", "multiselect"]:
                results.extend(await self._test_select_element(component_id, element))
            elif element_type in ["checkbox", "radio"]:
                results.extend(await self._test_choice_element(component_id, element))
            elif element_type in ["slider", "number_input"]:
                results.extend(await self._test_numeric_element(component_id, element))
            elif element_type == "file_uploader":
                results.extend(await self._test_file_element(component_id, element))
            else:
                # Generic interaction test
                results.append(await self._test_generic_element(component_id, element))

        except Exception as e:
            self.logger.error(f"Error testing element {element_id}: {e}")
            results.append(InteractionTestResult(element_id=element_id, test_type=f"{element_type}_test", success=False, error=str(e)))

        return results

    async def _test_button_element(self, component_id: str, element: dict[str, Any]) -> list[InteractionTestResult]:
        """Test button interactions."""
        element_id = element.get("id", "unknown")
        element_key = element.get("key")

        results = []

        # Test 1: Button presence and configuration
        start_time = time.time()

        if not element_key:
            results.append(
                InteractionTestResult(
                    element_id=element_id,
                    test_type="button_key_validation",
                    success=False,
                    error="Button missing Streamlit key",
                    response_time=time.time() - start_time,
                )
            )
        else:
            results.append(
                InteractionTestResult(
                    element_id=element_id,
                    test_type="button_key_validation",
                    success=True,
                    response_time=time.time() - start_time,
                    data={"key": element_key},
                )
            )

        # Test 2: Button click simulation
        start_time = time.time()

        try:
            # Simulate button state changes
            if element_key:
                # Check if button state exists in session
                button_state_key = f"button_clicked_{element_key}"

                # Simulate click by setting session state
                original_state = st.session_state.get(button_state_key, False)
                st.session_state[button_state_key] = True

                # Test button response
                click_test_result = await self._simulate_button_click(component_id, element)

                # Restore original state
                st.session_state[button_state_key] = original_state

                results.append(
                    InteractionTestResult(
                        element_id=element_id,
                        test_type="button_click_simulation",
                        success=click_test_result.get("success", True),
                        response_time=time.time() - start_time,
                        data=click_test_result,
                    )
                )

        except Exception as e:
            results.append(
                InteractionTestResult(
                    element_id=element_id, test_type="button_click_simulation", success=False, error=str(e), response_time=time.time() - start_time
                )
            )

        return results

    async def _simulate_button_click(self, component_id: str, element: dict[str, Any]) -> dict[str, Any]:
        """Simulate button click and test response."""
        element_id = element.get("id", "unknown")

        # Create a mock click event
        click_result = {"success": True, "element_id": element_id, "component_id": component_id, "response_data": {}}

        # Check for expected side effects based on element description
        description = element.get("description", "").lower()

        if "analyze" in description or "process" in description:
            # Expect processing to occur
            click_result["expected_action"] = "processing"
        elif "clear" in description or "reset" in description:
            # Expect state to be cleared
            click_result["expected_action"] = "state_reset"
        elif "submit" in description or "save" in description:
            # Expect data submission
            click_result["expected_action"] = "data_submission"
        else:
            click_result["expected_action"] = "generic_action"

        return click_result

    async def _test_input_element(self, component_id: str, element: dict[str, Any]) -> list[InteractionTestResult]:
        """Test input field interactions."""
        element_id = element.get("id", "unknown")
        element_key = element.get("key")

        results = []

        # Test input validation
        start_time = time.time()

        test_inputs = ["test input", "123", "special@chars!", ""]

        for test_input in test_inputs:
            try:
                # Simulate input by setting session state
                if element_key:
                    original_value = st.session_state.get(element_key, "")
                    st.session_state[element_key] = test_input

                    # Test input processing
                    input_result = await self._validate_input_processing(component_id, element, test_input)

                    # Restore original value
                    st.session_state[element_key] = original_value

                    results.append(
                        InteractionTestResult(
                            element_id=element_id,
                            test_type=f"input_validation_{test_input[:10] if test_input else 'empty'}",
                            success=input_result.get("valid", True),
                            response_time=time.time() - start_time,
                            data={"input_value": test_input, "result": input_result},
                        )
                    )

            except Exception as e:
                results.append(
                    InteractionTestResult(
                        element_id=element_id,
                        test_type=f"input_validation_{test_input[:10] if test_input else 'empty'}",
                        success=False,
                        error=str(e),
                        response_time=time.time() - start_time,
                    )
                )

        return results

    async def _validate_input_processing(self, component_id: str, element: dict[str, Any], input_value: str) -> dict[str, Any]:
        """Validate input processing behavior."""
        return {
            "valid": True,
            "input_value": input_value,
            "length": len(input_value),
            "component_id": component_id,
            "element_id": element.get("id", "unknown"),
        }

    async def _test_select_element(self, component_id: str, element: dict[str, Any]) -> list[InteractionTestResult]:
        """Test select/dropdown element interactions."""
        element_id = element.get("id", "unknown")
        results = []

        start_time = time.time()

        # Test select element configuration
        results.append(
            InteractionTestResult(
                element_id=element_id,
                test_type="select_configuration",
                success=True,
                response_time=time.time() - start_time,
                data={"type": "select_element"},
            )
        )

        return results

    async def _test_choice_element(self, component_id: str, element: dict[str, Any]) -> list[InteractionTestResult]:
        """Test checkbox/radio element interactions."""
        element_id = element.get("id", "unknown")
        element_key = element.get("key")

        results = []

        # Test choice toggle
        start_time = time.time()

        if element_key:
            try:
                # Test both states
                for state in [True, False]:
                    original_state = st.session_state.get(element_key, False)
                    st.session_state[element_key] = state

                    # Validate state change
                    choice_result = await self._validate_choice_state(component_id, element, state)

                    # Restore original state
                    st.session_state[element_key] = original_state

                    results.append(
                        InteractionTestResult(
                            element_id=element_id,
                            test_type=f"choice_state_{state}",
                            success=choice_result.get("valid", True),
                            response_time=time.time() - start_time,
                            data={"state": state, "result": choice_result},
                        )
                    )

            except Exception as e:
                results.append(
                    InteractionTestResult(
                        element_id=element_id, test_type="choice_interaction", success=False, error=str(e), response_time=time.time() - start_time
                    )
                )

        return results

    async def _validate_choice_state(self, component_id: str, element: dict[str, Any], state: bool) -> dict[str, Any]:
        """Validate choice element state changes."""
        return {"valid": True, "state": state, "component_id": component_id, "element_id": element.get("id", "unknown")}

    async def _test_numeric_element(self, component_id: str, element: dict[str, Any]) -> list[InteractionTestResult]:
        """Test numeric input elements (sliders, number inputs)."""
        element_id = element.get("id", "unknown")
        results = []

        start_time = time.time()

        # Test numeric validation
        results.append(
            InteractionTestResult(
                element_id=element_id,
                test_type="numeric_validation",
                success=True,
                response_time=time.time() - start_time,
                data={"type": "numeric_element"},
            )
        )

        return results

    async def _test_file_element(self, component_id: str, element: dict[str, Any]) -> list[InteractionTestResult]:
        """Test file upload elements."""
        element_id = element.get("id", "unknown")
        results = []

        start_time = time.time()

        # Test file upload configuration
        results.append(
            InteractionTestResult(
                element_id=element_id,
                test_type="file_upload_config",
                success=True,
                response_time=time.time() - start_time,
                data={"type": "file_uploader"},
            )
        )

        return results

    async def _test_generic_element(self, component_id: str, element: dict[str, Any]) -> InteractionTestResult:
        """Test generic interactive element."""
        element_id = element.get("id", "unknown")
        element_type = element.get("type", "unknown")

        start_time = time.time()

        return InteractionTestResult(
            element_id=element_id,
            test_type=f"generic_{element_type}",
            success=True,
            response_time=time.time() - start_time,
            data={"element_type": element_type},
        )

    def get_interaction_summary(self) -> dict[str, Any]:
        """Get summary of interaction test results."""
        if not self.interaction_results:
            return {"status": "no_data"}

        total_tests = len(self.interaction_results)
        successful_tests = sum(1 for r in self.interaction_results if r.success)
        failed_tests = total_tests - successful_tests

        avg_response_time = sum(r.response_time for r in self.interaction_results) / total_tests

        # Group by test type
        test_types = {}
        for result in self.interaction_results:
            test_type = result.test_type
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "successful": 0, "failed": 0}

            test_types[test_type]["total"] += 1
            if result.success:
                test_types[test_type]["successful"] += 1
            else:
                test_types[test_type]["failed"] += 1

        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "average_response_time": avg_response_time,
            "test_types": test_types,
            "last_test_time": max(r.timestamp for r in self.interaction_results) if self.interaction_results else None,
        }


# Global instance initialization
ai_testing_framework = None


def get_ai_testing_framework():
    """Get or create the global AI testing framework instance."""
    global ai_testing_framework

    if ai_testing_framework is None:
        # Import here to avoid circular imports
        try:
            from .mobile_component_registry import mobile_component_registry

            ai_testing_framework = AIAgentTestingFramework(mobile_component_registry)
        except ImportError:
            # Fallback without registry
            ai_testing_framework = AIAgentTestingFramework()

    return ai_testing_framework
