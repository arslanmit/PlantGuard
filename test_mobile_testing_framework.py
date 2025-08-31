#!/usr/bin/env python3
"""
Test runner for Mobile Testing Framework.

This script demonstrates the comprehensive mobile testing framework
for PlantGuard UI components with automated testing, validation,
and reporting capabilities.
"""


import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.components.mobile_testing_framework import MobileTestingFramework

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def main() -> None:
    """Run mobile testing framework demonstration."""
    logger.info("Starting Mobile Testing Framework demonstration")

    try:
        # Initialize testing framework
        testing_framework = MobileTestingFramework()

        # Get framework status
        status = testing_framework.get_framework_status()
        logger.info("Framework Status: %s", status)

        # Test component IDs to validate
        test_components = [
            "mobile_camera_input_test",
            "mobile_upload_input_test",
            "mobile_voice_input_test",
            "mobile_text_input_test",
            "mobile_analysis_display_test",
        ]

        # Run full validation for each test component
        validation_results = {}

        for component_id in test_components:
            logger.info("Running full validation for: %s", component_id)

            try:
                result = testing_framework.run_full_component_validation(component_id)
                validation_results[component_id] = result

                # Log summary
                summary = result.get("overall_summary", {})
                logger.info(
                    "Validation completed for %s: Status=%s, Success Rate=%.1f%%",
                    component_id,
                    summary.get("overall_status", "unknown"),
                    summary.get("success_rate", 0) * 100,
                )

            except Exception as e:
                logger.error("Validation failed for %s: %s", component_id, e)
                validation_results[component_id] = {"error": str(e)}

        # Run continuous monitoring
        logger.info("Running continuous monitoring cycle")
        monitoring_results = testing_framework.run_continuous_monitoring()

        monitoring_summary = monitoring_results.get("summary", {})
        logger.info(
            "Monitoring completed: %d components monitored, %d alerts generated",
            monitoring_summary.get("components_monitored", 0),
            len(monitoring_results.get("alerts", [])),
        )

        # Generate comprehensive report
        logger.info("Generating comprehensive testing report")
        comprehensive_report = testing_framework.generate_comprehensive_report()

        # Display summary results
        print("\n" + "=" * 80)
        print("MOBILE TESTING FRAMEWORK RESULTS SUMMARY")
        print("=" * 80)

        print("\nFramework Configuration:")
        config = comprehensive_report["framework_info"]["configuration"]
        for key, value in config.items():
            print(f"  {key}: {value}")

        print("\nValidation Results:")
        for component_id, result in validation_results.items():
            if "error" in result:
                print(f"  {component_id}: ERROR - {result['error']}")
            else:
                summary = result.get("overall_summary", {})
                status = summary.get("overall_status", "unknown")
                success_rate = summary.get("success_rate", 0) * 100
                mobile_readiness = summary.get("mobile_readiness", "unknown")
                print(f"  {component_id}: {status.upper()} (Success: {success_rate:.1f}%, Mobile: {mobile_readiness})")

        print("\nMonitoring Results:")
        print(f"  Components Monitored: {monitoring_summary.get('components_monitored', 0)}")
        print(f"  Healthy Components: {monitoring_summary.get('healthy_components', 0)}")
        print(f"  Critical Alerts: {monitoring_summary.get('critical_alerts', 0)}")

        # Display alerts if any
        alerts = monitoring_results.get("alerts", [])
        if alerts:
            print("\nAlerts Generated:")
            for alert in alerts[:5]:  # Show first 5 alerts
                print(f"  {alert['type']}: {alert['message']}")
            if len(alerts) > 5:
                print(f"  ... and {len(alerts) - 5} more alerts")

        print("\nFramework Statistics:")
        stats = comprehensive_report["framework_statistics"]
        print(f"  Total Validations Run: {stats['total_validations_run']}")

        component_stats = stats.get("component_tester_stats", {})
        if component_stats:
            print(f"  Component Tests: {component_stats.get('total_test_results', 0)} results")

        ai_stats = stats.get("ai_agent_tester_stats", {})
        if ai_stats:
            print(f"  AI Agent Tests: {ai_stats.get('total_agent_tests', 0)} tests")

        mobile_stats = stats.get("mobile_specific_tester_stats", {})
        if mobile_stats:
            print(
                f"  Mobile Tests: Touch={mobile_stats.get('touch_tests_run', 0)}, "
                f"Responsive={mobile_stats.get('responsive_tests_run', 0)}, "
                f"Accessibility={mobile_stats.get('accessibility_tests_run', 0)}"
            )

        # Display recommendations
        recommendations = comprehensive_report.get("recommendations", [])
        if recommendations:
            print("\nFramework Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. {rec}")
            if len(recommendations) > 5:
                print(f"  ... and {len(recommendations) - 5} more recommendations")

        print("\n" + "=" * 80)
        print("Testing framework demonstration completed successfully!")
        print("=" * 80)

        return True

    except Exception as e:
        logger.error("Testing framework demonstration failed: %s", e)
        print(f"\nERROR: Testing framework demonstration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
