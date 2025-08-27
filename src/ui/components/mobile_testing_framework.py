"""
Mobile Testing Framework Integration for PlantGuard UI.

This module provides a unified interface for all mobile testing capabilities
including component testing, AI agent testing, and mobile-specific validation
with comprehensive reporting and AI agent support.
"""

import logging
import time
from datetime import datetime
from typing import Any

from .mobile_ai_agent_tester import MobileAIAgentTester
from .mobile_component_tester import MobileComponentTester
from .mobile_specific_tester import MobileSpecificTester
from .mobile_state_manager import MobileStateManager

logger = logging.getLogger(__name__)


class MobileTestingFramework:
    """
    Unified mobile testing framework for PlantGuard UI.

    Integrates component testing, AI agent testing, and mobile-specific
    validation into a comprehensive testing solution with automated
    reporting and AI agent support.
    """

    def __init__(self):
        """Initialize the unified mobile testing framework."""
        # Initialize all testing components
        self.component_tester = MobileComponentTester()
        self.ai_agent_tester = MobileAIAgentTester()
        self.mobile_specific_tester = MobileSpecificTester()
        self.state_manager = MobileStateManager()

        # Framework configuration
        self.config = {
            "auto_healing_enabled": True,
            "continuous_monitoring": True,
            "comprehensive_reporting": True,
            "ai_agent_integration": True,
            "performance_tracking": True,
        }

        # Test execution history
        self.test_execution_history: list[dict[str, Any]] = []

        logger.info("MobileTestingFramework initialized with all testing modules")

    def test_all_components(self) -> dict[str, Any]:
        """
        Test all registered mobile components.

        Returns:
            Dictionary with test results for all components
        """
        try:
            # Get all registered components from the mobile component registry
            from .mobile_component_registry import mobile_component_registry

            components = mobile_component_registry.get_all_components()

            if not components:
                return {
                    "components_tested": 0,
                    "status": "no_components_registered",
                    "message": "No components found in registry",
                    "test_results": {},
                }

            test_results = {}
            total_tested = 0
            total_passed = 0

            for component_id, component_class in components.items():
                try:
                    # Run validation for each component
                    validation_result = self.run_full_component_validation(component_id)
                    test_results[component_id] = validation_result

                    total_tested += 1

                    # Check if component passed
                    overall_summary = validation_result.get("overall_summary", {})
                    if overall_summary.get("overall_status") == "passed":
                        total_passed += 1

                except Exception as e:
                    test_results[component_id] = {"error": str(e), "status": "test_failed"}
                    total_tested += 1

            return {
                "components_tested": total_tested,
                "components_passed": total_passed,
                "success_rate": (total_passed / total_tested * 100) if total_tested > 0 else 0,
                "status": "completed",
                "test_results": test_results,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Failed to test all components: {e}")
            return {"components_tested": 0, "status": "framework_error", "error": str(e), "test_results": {}}

    def run_full_component_validation(self, component_id: str) -> dict[str, Any]:
        """
        Run complete validation suite for a mobile component.

        Args:
            component_id: Component to validate

        Returns:
            Comprehensive validation results
        """
        logger.info("Starting full component validation for: %s", component_id)

        start_time = datetime.now()
        execution_id = f"validation_{component_id}_{int(start_time.timestamp())}"

        validation_results: dict[str, Any] = {
            "execution_id": execution_id,
            "component_id": component_id,
            "start_time": start_time.isoformat(),
            "component_tests": {},
            "mobile_specific_tests": {},
            "ai_agent_tests": {},
            "overall_summary": {},
            "recommendations": [],
            "status": "running",
        }

        try:
            # 1. Run basic component tests
            logger.info("Running basic component tests")
            component_results = self._run_component_tests(component_id)
            validation_results["component_tests"] = component_results

            # 2. Run mobile-specific tests
            logger.info("Running mobile-specific tests")
            mobile_results = self.mobile_specific_tester.run_comprehensive_mobile_tests(component_id)
            validation_results["mobile_specific_tests"] = mobile_results

            # 3. Run AI agent tests
            logger.info("Running AI agent tests")
            ai_results = self._run_ai_agent_tests(component_id)
            validation_results["ai_agent_tests"] = ai_results

            # 4. Generate overall summary
            validation_results["overall_summary"] = self._generate_overall_summary(validation_results)

            # 5. Generate recommendations
            validation_results["recommendations"] = self._generate_comprehensive_recommendations(validation_results)

            # 6. Apply auto-healing if enabled and needed
            if self.config["auto_healing_enabled"]:
                healing_results = self._apply_auto_healing(component_id, validation_results)
                validation_results["healing_applied"] = healing_results

            validation_results["status"] = "completed"

        except Exception as e:
            logger.error("Full component validation failed: %s", e)
            validation_results["status"] = "failed"
            validation_results["error"] = str(e)

        finally:
            end_time = datetime.now()
            validation_results["end_time"] = end_time.isoformat()
            validation_results["duration"] = (end_time - start_time).total_seconds()

            # Store in execution history
            self.test_execution_history.append(validation_results)

        logger.info("Full component validation completed for %s in %.2fs", component_id, validation_results["duration"])

        return validation_results

    def _run_component_tests(self, component_id: str) -> dict[str, Any]:
        """Run basic component tests."""
        try:
            # Get component type from registry
            component_type = self._determine_component_type(component_id)

            if component_type:
                # Run component test suite
                test_results = self.component_tester.run_component_test_suite(component_type, component_id)

                return {
                    "component_type": component_type,
                    "test_results": [r.to_dict() for r in test_results],
                    "summary": {
                        "total_tests": len(test_results),
                        "passed_tests": len([r for r in test_results if r.status == "passed"]),
                        "failed_tests": len([r for r in test_results if r.status == "failed"]),
                        "error_tests": len([r for r in test_results if r.status == "error"]),
                    },
                }
            else:
                return {
                    "error": f"Could not determine component type for {component_id}",
                    "test_results": [],
                    "summary": {"total_tests": 0, "passed_tests": 0, "failed_tests": 0, "error_tests": 1},
                }

        except Exception as e:
            logger.error("Component tests failed: %s", e)
            return {"error": str(e), "test_results": [], "summary": {"total_tests": 0, "passed_tests": 0, "failed_tests": 0, "error_tests": 1}}

    def _run_ai_agent_tests(self, component_id: str) -> dict[str, Any]:
        """Run AI agent tests."""
        try:
            # Validate component health
            health_result = self.ai_agent_tester.validate_component_health(component_id)

            # Detect and heal issues if needed
            healing_result = None
            if health_result.status == "failed":
                healing_result = self.ai_agent_tester.detect_and_heal_issues(component_id)

            return {
                "health_validation": health_result.to_dict(),
                "healing_result": healing_result.to_dict() if healing_result else None,
                "summary": {
                    "health_status": health_result.status,
                    "health_confidence": health_result.confidence,
                    "healing_applied": healing_result is not None,
                    "healing_successful": healing_result.status == "healed" if healing_result else False,
                },
            }

        except Exception as e:
            logger.error("AI agent tests failed: %s", e)
            return {
                "error": str(e),
                "summary": {"health_status": "error", "health_confidence": 0.0, "healing_applied": False, "healing_successful": False},
            }

    def _determine_component_type(self, component_id: str) -> str | None:
        """Determine component type from component ID."""
        # Map component ID patterns to types
        type_patterns = {
            "camera": "mobilecamerainput",
            "upload": "mobileuploadinput",
            "voice": "mobilevoiceinput",
            "text": "mobiletextinput",
            "analysis": "mobileanalysisdisplay",
            "chat": "mobilechatinterface",
            "history": "mobilehistoryview",
        }

        component_id_lower = component_id.lower()
        for pattern, component_type in type_patterns.items():
            if pattern in component_id_lower:
                return component_type

        return None

    def _generate_overall_summary(self, validation_results: dict[str, Any]) -> dict[str, Any]:
        """Generate overall validation summary."""
        summary = {
            "overall_status": "unknown",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "error_tests": 0,
            "success_rate": 0.0,
            "mobile_readiness": "unknown",
            "ai_agent_compatibility": "unknown",
            "performance_grade": "unknown",
        }

        try:
            # Aggregate component test results
            component_summary = validation_results.get("component_tests", {}).get("summary", {})
            summary["total_tests"] += component_summary.get("total_tests", 0)
            summary["passed_tests"] += component_summary.get("passed_tests", 0)
            summary["failed_tests"] += component_summary.get("failed_tests", 0)
            summary["error_tests"] += component_summary.get("error_tests", 0)

            # Aggregate mobile-specific test results
            mobile_summary = validation_results.get("mobile_specific_tests", {}).get("summary", {})
            if "total_tests" in mobile_summary:
                summary["total_tests"] += mobile_summary["total_tests"]
                summary["passed_tests"] += mobile_summary["passed_tests"]
                summary["failed_tests"] += mobile_summary["failed_tests"]

            # Get mobile readiness
            summary["mobile_readiness"] = mobile_summary.get("mobile_readiness", "unknown")

            # Get AI agent compatibility
            ai_summary = validation_results.get("ai_agent_tests", {}).get("summary", {})
            health_confidence = ai_summary.get("health_confidence", 0.0)

            if health_confidence >= 0.9:
                summary["ai_agent_compatibility"] = "excellent"
            elif health_confidence >= 0.7:
                summary["ai_agent_compatibility"] = "good"
            elif health_confidence >= 0.5:
                summary["ai_agent_compatibility"] = "fair"
            else:
                summary["ai_agent_compatibility"] = "poor"

            # Calculate overall success rate
            total_tests = summary["total_tests"]
            passed_tests = summary["passed_tests"]
            if isinstance(total_tests, int) and total_tests > 0 and isinstance(passed_tests, int):
                summary["success_rate"] = passed_tests / total_tests
            else:
                summary["success_rate"] = 0.0

            # Determine overall status
            success_rate = summary["success_rate"]
            if isinstance(success_rate, int | float):
                if success_rate >= 0.9:
                    summary["overall_status"] = "excellent"
                elif success_rate >= 0.8:
                    summary["overall_status"] = "good"
                elif success_rate >= 0.6:
                    summary["overall_status"] = "fair"
                else:
                    summary["overall_status"] = "poor"
            else:
                summary["overall_status"] = "unknown"

            # Determine performance grade
            performance_tests = validation_results.get("mobile_specific_tests", {}).get("performance_tests", [])
            if performance_tests:
                critical_issues = len([t for t in performance_tests if t.get("impact_level") == "critical"])
                high_issues = len([t for t in performance_tests if t.get("impact_level") == "high"])

                if critical_issues > 0:
                    summary["performance_grade"] = "poor"
                elif high_issues > 2:
                    summary["performance_grade"] = "fair"
                elif high_issues > 0:
                    summary["performance_grade"] = "good"
                else:
                    summary["performance_grade"] = "excellent"

        except Exception as e:
            logger.error("Failed to generate overall summary: %s", e)
            summary["error"] = str(e)

        return summary

    def _generate_comprehensive_recommendations(self, validation_results: dict[str, Any]) -> list[str]:
        """Generate comprehensive recommendations from all test results."""
        recommendations = []

        try:
            # Get recommendations from each test category
            component_tests = validation_results.get("component_tests", {})
            mobile_tests = validation_results.get("mobile_specific_tests", {})
            ai_tests = validation_results.get("ai_agent_tests", {})
            overall_summary = validation_results.get("overall_summary", {})

            # Component-level recommendations
            if "error" in component_tests:
                recommendations.append("Fix component testing system issues before deployment")
            elif component_tests.get("summary", {}).get("failed_tests", 0) > 0:
                failed_count = component_tests["summary"]["failed_tests"]
                recommendations.append(f"Address {failed_count} failed component tests")

            # Mobile-specific recommendations
            mobile_recommendations = mobile_tests.get("recommendations", [])
            recommendations.extend(mobile_recommendations)

            # AI agent recommendations
            ai_summary = ai_tests.get("summary", {})
            if ai_summary.get("health_status") == "failed":
                recommendations.append("Component has health issues that may affect AI agent operation")

            if ai_summary.get("healing_applied") and not ai_summary.get("healing_successful"):
                recommendations.append("Auto-healing failed - manual intervention required")

            # Overall recommendations based on summary
            overall_status = overall_summary.get("overall_status", "unknown")
            mobile_readiness = overall_summary.get("mobile_readiness", "unknown")
            performance_grade = overall_summary.get("performance_grade", "unknown")

            if overall_status == "poor":
                recommendations.append("Component requires significant improvements before production deployment")
            elif overall_status == "fair":
                recommendations.append("Component needs improvements for optimal mobile experience")

            if mobile_readiness == "poor":
                recommendations.append("Critical mobile usability issues must be addressed")

            if performance_grade == "poor":
                recommendations.append("Critical performance issues detected - optimization required")
            elif performance_grade == "fair":
                recommendations.append("Performance improvements recommended for better mobile experience")

            # Success recommendations
            if overall_status == "excellent" and mobile_readiness == "excellent":
                recommendations.append("Component meets excellent standards for mobile deployment")

            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec not in seen:
                    seen.add(rec)
                    unique_recommendations.append(rec)

            return unique_recommendations

        except Exception as e:
            logger.error("Failed to generate recommendations: %s", e)
            return [f"Error generating recommendations: {e!s}"]

    def _apply_auto_healing(self, component_id: str, validation_results: dict[str, Any]) -> dict[str, Any]:
        """Apply auto-healing based on validation results."""
        healing_results: dict[str, Any] = {"healing_attempted": False, "healing_successful": False, "actions_taken": [], "remaining_issues": []}

        try:
            # Check if healing is needed
            overall_summary = validation_results.get("overall_summary", {})

            if overall_summary.get("overall_status") in ["poor", "fair"]:
                logger.info("Applying auto-healing for component: %s", component_id)

                healing_results["healing_attempted"] = True

                # Apply AI agent healing
                healing_result = self.ai_agent_tester.detect_and_heal_issues(component_id)

                if healing_result.status == "healed":
                    healing_results["healing_successful"] = True
                    if hasattr(healing_result, "actions_taken") and isinstance(healing_result.actions_taken, list):
                        healing_results["actions_taken"].extend(healing_result.actions_taken)
                else:
                    if hasattr(healing_result, "findings") and isinstance(healing_result.findings, list):
                        healing_results["remaining_issues"].extend(healing_result.findings)

                logger.info("Auto-healing completed for %s: %s", component_id, "successful" if healing_results["healing_successful"] else "failed")

        except Exception as e:
            logger.error("Auto-healing failed: %s", e)
            healing_results["error"] = str(e)

        return healing_results

    def run_continuous_monitoring(self) -> dict[str, Any]:
        """
        Run continuous monitoring for all mobile components.

        Returns:
            Monitoring results
        """
        logger.info("Starting continuous monitoring cycle")

        monitoring_results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "component_discovery": {},
            "health_checks": {},
            "performance_monitoring": {},
            "summary": {},
            "alerts": [],
        }

        try:
            # Run component discovery
            discovery_result = self.ai_agent_tester.discover_components()
            monitoring_results["component_discovery"] = discovery_result.to_dict()

            # Get all component states for monitoring
            all_states = self.state_manager.get_all_component_states()

            # Monitor each component
            for component_id in all_states:
                try:
                    # Health check
                    health_result = self.ai_agent_tester.validate_component_health(component_id)
                    monitoring_results["health_checks"][component_id] = health_result.to_dict()

                    # Performance check
                    performance_results = self.mobile_specific_tester.test_mobile_performance(component_id)
                    monitoring_results["performance_monitoring"][component_id] = [p.to_dict() for p in performance_results]

                    # Generate alerts for critical issues
                    if health_result.confidence < 0.5:
                        monitoring_results["alerts"].append(
                            {
                                "type": "health_critical",
                                "component_id": component_id,
                                "message": f"Component {component_id} has critical health issues",
                                "confidence": health_result.confidence,
                            }
                        )

                    # Check for critical performance issues
                    critical_perf_issues = [p for p in performance_results if p.impact_level == "critical"]
                    if critical_perf_issues:
                        monitoring_results["alerts"].append(
                            {
                                "type": "performance_critical",
                                "component_id": component_id,
                                "message": f"Component {component_id} has {len(critical_perf_issues)} critical performance issues",
                                "issues": [p.metric_name for p in critical_perf_issues],
                            }
                        )

                except Exception as e:
                    logger.error("Monitoring failed for component %s: %s", component_id, e)
                    monitoring_results["alerts"].append(
                        {"type": "monitoring_error", "component_id": component_id, "message": f"Monitoring failed: {e!s}"}
                    )

            # Generate monitoring summary
            health_checks = monitoring_results["health_checks"]
            alerts = monitoring_results["alerts"]

            healthy_count = 0
            if isinstance(health_checks, dict):
                for health_result in health_checks.values():
                    if isinstance(health_result, dict) and health_result.get("confidence", 0) > 0.7:
                        healthy_count += 1

            critical_alerts_count = 0
            if isinstance(alerts, list):
                for alert in alerts:
                    if isinstance(alert, dict) and "critical" in alert.get("type", ""):
                        critical_alerts_count += 1

            monitoring_results["summary"] = {
                "components_monitored": len(all_states),
                "healthy_components": healthy_count,
                "critical_alerts": critical_alerts_count,
                "monitoring_status": "completed",
            }

        except Exception as e:
            logger.error("Continuous monitoring failed: %s", e)
            monitoring_results["summary"] = {"monitoring_status": "failed", "error": str(e)}

        return monitoring_results

    def generate_comprehensive_report(self) -> dict[str, Any]:
        """
        Generate comprehensive testing framework report.

        Returns:
            Comprehensive report
        """
        report = {
            "framework_info": {"version": "1.0.0", "timestamp": datetime.now().isoformat(), "configuration": self.config},
            "execution_history": self.test_execution_history,
            "component_testing": self.component_tester.generate_test_report(),
            "ai_agent_testing": self.ai_agent_tester.generate_agent_report(),
            "mobile_specific_testing": self.mobile_specific_tester.generate_mobile_test_report(),
            "framework_statistics": self._get_framework_statistics(),
            "recommendations": self._generate_framework_recommendations(),
        }

        return report

    def _get_framework_statistics(self) -> dict[str, Any]:
        """Get framework usage statistics."""
        return {
            "total_validations_run": len(self.test_execution_history),
            "component_tester_stats": self.component_tester.get_test_statistics(),
            "ai_agent_tester_stats": self.ai_agent_tester.get_agent_statistics(),
            "mobile_specific_tester_stats": self.mobile_specific_tester.get_mobile_test_statistics(),
        }

    def _generate_framework_recommendations(self) -> list[str]:
        """Generate framework-level recommendations."""
        recommendations = []

        # Analyze execution history
        if len(self.test_execution_history) > 0:
            recent_executions = self.test_execution_history[-10:]  # Last 10 executions

            # Check for recurring issues
            failed_executions = [e for e in recent_executions if e.get("status") == "failed"]
            if len(failed_executions) > len(recent_executions) * 0.3:  # More than 30% failures
                recommendations.append("High failure rate detected - review component implementations")

            # Check for performance trends
            poor_performance = [e for e in recent_executions if e.get("overall_summary", {}).get("performance_grade") == "poor"]
            if len(poor_performance) > 0:
                recommendations.append("Performance issues detected across multiple components")

        # Framework configuration recommendations
        if not self.config["auto_healing_enabled"]:
            recommendations.append("Consider enabling auto-healing for better component reliability")

        if not self.config["continuous_monitoring"]:
            recommendations.append("Enable continuous monitoring for proactive issue detection")

        return recommendations

    def clear_all_test_data(self) -> None:
        """Clear all test data and results."""
        self.test_execution_history.clear()
        self.component_tester.clear_test_results()
        self.ai_agent_tester.clear_agent_results()
        self.mobile_specific_tester.clear_mobile_test_results()

        logger.info("Cleared all test data and results")

    def get_framework_status(self) -> dict[str, Any]:
        """
        Get current framework status.

        Returns:
            Framework status information
        """
        return {
            "framework_initialized": True,
            "configuration": self.config,
            "test_modules_loaded": {
                "component_tester": self.component_tester is not None,
                "ai_agent_tester": self.ai_agent_tester is not None,
                "mobile_specific_tester": self.mobile_specific_tester is not None,
            },
            "execution_history_count": len(self.test_execution_history),
            "last_execution": self.test_execution_history[-1] if self.test_execution_history else None,
        }
