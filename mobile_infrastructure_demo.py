"""
Mobile Infrastructure Demo for PlantGuard UI.

This demo application validates the mobile component foundation
and demonstrates the infrastructure for AI agent development.
"""

import logging
from datetime import datetime

import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import mobile components
try:
    from src.ui.components import AI_AGENT_INFO, MobileTestComponent, create_mobile_app, get_component_registry, validate_mobile_infrastructure

    components_available = True
except ImportError as e:
    logger.error(f"Failed to import mobile components: {e}")
    components_available = False


def main():
    """Main demo application."""
    st.set_page_config(page_title="PlantGuard Mobile Infrastructure Demo", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")

    if not components_available:
        st.error("❌ Mobile components not available. Please check the installation.")
        return

    # Validate infrastructure
    validation_results = validate_mobile_infrastructure()

    st.title("🌿 PlantGuard Mobile Infrastructure Demo")
    st.markdown("---")

    # Show infrastructure status
    st.header("📊 Infrastructure Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Components Available",
            validation_results["components_registered"],
            delta="Ready" if validation_results["infrastructure_available"] else "Error",
        )

    with col2:
        st.metric(
            "Core Systems",
            "5/5" if validation_results["core_components_functional"] else "Error",
            delta="Functional" if validation_results["core_components_functional"] else "Failed",
        )

    with col3:
        st.metric(
            "AI Agent Support",
            "Enabled" if validation_results["ai_discovery_info_available"] else "Disabled",
            delta="Ready" if validation_results["ai_discovery_info_available"] else "Error",
        )

    # Show detailed validation results
    with st.expander("🔍 Detailed Validation Results"):
        st.json(validation_results)

    st.markdown("---")

    # Demo mobile layout manager
    st.header("📱 Mobile Layout Manager Demo")

    try:
        # Create mobile app
        mobile_app = create_mobile_app()

        st.success("✅ Mobile Layout Manager created successfully!")

        # Show configuration
        config = mobile_app.get_config()
        st.markdown("**Layout Configuration:**")
        st.json(config)

        # Render mobile layout (header and basic structure)
        st.markdown("**Mobile Layout Preview:**")
        mobile_app.render()

    except Exception as e:
        st.error(f"❌ Mobile Layout Manager failed: {e}")
        logger.error(f"Mobile layout manager error: {e}")

    st.markdown("---")

    # Demo component registry
    st.header("🗂️ Component Registry Demo")

    try:
        registry = get_component_registry()

        st.success("✅ Component Registry created successfully!")

        # Show available components
        available_components = registry.get_available_components()
        st.markdown(f"**Available Components:** {', '.join(available_components)}")

        # Show AI agent discovery info
        discovery_info = registry.discover_components_for_ai_agent()
        with st.expander("🤖 AI Agent Discovery Information"):
            st.json(discovery_info)

        # Show registry statistics
        stats = registry.get_registry_stats()
        st.markdown("**Registry Statistics:**")
        st.json(stats)

    except Exception as e:
        st.error(f"❌ Component Registry failed: {e}")
        logger.error(f"Component registry error: {e}")

    st.markdown("---")

    # Demo test component
    st.header("🧪 Test Component Demo")

    try:
        # Create test component
        test_component = MobileTestComponent(component_id="demo_test_component", title="Infrastructure Test Component")

        st.success("✅ Test Component created successfully!")

        # Show component metadata
        metadata = test_component.get_metadata()
        with st.expander("📋 Component Metadata"):
            st.json(metadata)

        # Render test component with error handling
        st.markdown("**Test Component UI:**")
        test_component.render_with_error_handling()

        # Show automated test results
        st.markdown("**Automated Test Results:**")
        test_results = test_component.run_automated_tests()

        for test_name, result in test_results.items():
            if isinstance(result, bool):
                icon = "✅" if result else "❌"
                st.markdown(f"- {test_name}: {icon}")
            else:
                st.markdown(f"- {test_name}: {result}")

    except Exception as e:
        st.error(f"❌ Test Component failed: {e}")
        logger.error(f"Test component error: {e}")

    st.markdown("---")

    # AI Agent Information
    st.header("🤖 AI Agent Development Information")

    st.markdown("""
    This mobile infrastructure is designed for AI agent development with the following features:
    
    **Component Discovery:**
    - Standardized CSS class naming: `mobile-{component-type}-{element}`
    - Component registry with metadata for AI navigation
    - Predictable state management patterns
    
    **Error Handling:**
    - Graceful degradation when components fail
    - Comprehensive error categorization and recovery
    - Fallback rendering for failed components
    
    **State Management:**
    - Centralized state with predictable keys: `mobile_{component_id}_state`
    - Session persistence and restoration
    - Validation and error tracking
    
    **Development Patterns:**
    - Base component class with standardized interface
    - Consistent render() method pattern
    - Built-in error handling and recovery
    """)

    with st.expander("📚 AI Agent Development Guide"):
        st.json(AI_AGENT_INFO)

    # Footer
    st.markdown("---")
    st.markdown(f"**Demo completed at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("**Status:** Mobile infrastructure foundation ready for development! ✅")


if __name__ == "__main__":
    main()
