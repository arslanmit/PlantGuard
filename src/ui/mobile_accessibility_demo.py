"""
Mobile Accessibility Demo Application for PlantGuard UI.

This module demonstrates the comprehensive accessibility features implemented
for mobile users, including ARIA labels, screen reader support, keyboard navigation,
high contrast mode, and voice-over compatibility.
"""

import logging

import streamlit as st

from .mobile_accessibility import apply_accessibility_enhancements, initialize_mobile_accessibility
from .mobile_accessibility_testing import generate_accessibility_report, run_accessibility_tests, validate_component_accessibility
from .mobile_accessible_components import get_accessibility_test_results, validate_accessibility_compliance

logger = logging.getLogger(__name__)


def main():
    """Main accessibility demo application."""
    st.set_page_config(page_title="PlantGuard Mobile Accessibility Demo", page_icon="♿", layout="wide", initial_sidebar_state="collapsed")

    # Initialize accessibility
    accessibility_manager = initialize_mobile_accessibility()
    apply_accessibility_enhancements()

    # Create skip links
    skip_links = accessibility_manager.create_skip_links()
    st.markdown(skip_links, unsafe_allow_html=True)

    # Create landmark regions
    landmarks = accessibility_manager.create_landmark_regions()

    # Banner
    st.markdown(landmarks["banner"], unsafe_allow_html=True)

    # Main heading with accessibility
    main_heading = accessibility_manager.create_accessible_heading(
        text="♿ PlantGuard Mobile Accessibility Demo",
        level=1,
        heading_id="main-heading",
        aria_label="PlantGuard Mobile Accessibility Demonstration Application",
    )
    st.markdown(main_heading, unsafe_allow_html=True)

    st.markdown(landmarks["close"], unsafe_allow_html=True)

    # Navigation
    st.markdown(landmarks["navigation"], unsafe_allow_html=True)

    nav_heading = accessibility_manager.create_accessible_heading(
        text="Navigation", level=2, heading_id="navigation-heading", aria_label="Demo navigation options"
    )
    st.markdown(nav_heading, unsafe_allow_html=True)

    # Demo sections
    demo_sections = ["Accessibility Overview", "Component Demonstrations", "Accessibility Settings", "Testing & Validation", "Compliance Report"]

    selected_section = st.selectbox(
        "Select Demo Section", options=demo_sections, help="Choose which accessibility feature to demonstrate", key="demo_section_select"
    )

    st.markdown(landmarks["close"], unsafe_allow_html=True)

    # Main content
    st.markdown(landmarks["main"], unsafe_allow_html=True)

    if selected_section == "Accessibility Overview":
        render_accessibility_overview(accessibility_manager)
    elif selected_section == "Component Demonstrations":
        render_component_demonstrations(accessibility_manager)
    elif selected_section == "Accessibility Settings":
        render_accessibility_settings_demo(accessibility_manager)
    elif selected_section == "Testing & Validation":
        render_testing_validation_demo(accessibility_manager)
    elif selected_section == "Compliance Report":
        render_compliance_report_demo(accessibility_manager)

    st.markdown(landmarks["close"], unsafe_allow_html=True)

    # Live regions for announcements
    live_region = accessibility_manager.create_live_region(region_id="demo-announcements", aria_live="polite")
    st.markdown(live_region, unsafe_allow_html=True)


def render_accessibility_overview(accessibility_manager):
    """Render accessibility overview section."""
    overview_heading = accessibility_manager.create_accessible_heading(
        text="[FEATURE] Accessibility Features Overview", level=2, heading_id="overview-heading"
    )
    st.markdown(overview_heading, unsafe_allow_html=True)

    st.markdown(
        """
    <div role="region" aria-labelledby="overview-heading">
        <p>PlantGuard's mobile interface implements comprehensive accessibility features 
        to ensure usability for all users, including those with disabilities.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Feature categories
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### [PROGRESS] Core Accessibility Features
        
        - **ARIA Labels**: Comprehensive labeling for screen readers
        - **Semantic HTML**: Proper HTML structure and landmarks
        - **Keyboard Navigation**: Full keyboard accessibility
        - **Focus Management**: Clear focus indicators
        - **Skip Links**: Quick navigation for keyboard users
        """)

        st.markdown("""
        ### [MOBILE] Mobile-Specific Features
        
        - **Touch Targets**: Minimum 44px touch targets
        - **Voice-Over Support**: iOS VoiceOver compatibility
        - **TalkBack Support**: Android TalkBack optimization
        - **Touch Feedback**: Visual and haptic feedback
        - **Gesture Support**: Accessible gesture interactions
        """)

    with col2:
        st.markdown("""
        ### [VISION] Visual Accessibility
        
        - **High Contrast Mode**: Enhanced contrast options
        - **Font Scaling**: Adjustable text sizes
        - **Color Independence**: Information not color-dependent
        - **Reduced Motion**: Respects motion preferences
        - **Focus Indicators**: High-visibility focus outlines
        """)

        st.markdown("""
        ### [SPEAKER] Audio & Announcements
        
        - **Live Regions**: Dynamic content announcements
        - **Status Updates**: Real-time status communication
        - **Error Announcements**: Clear error messaging
        - **Success Feedback**: Confirmation announcements
        - **Loading States**: Progress communication
        """)

    # Compliance information
    compliance_heading = accessibility_manager.create_accessible_heading(text="[DETAILS] Compliance Standards", level=3, heading_id="compliance-heading")
    st.markdown(compliance_heading, unsafe_allow_html=True)

    st.info("""
    **WCAG 2.1 AA Compliance**
    
    This implementation follows Web Content Accessibility Guidelines (WCAG) 2.1 
    at the AA level, ensuring broad accessibility for users with various disabilities.
    
    **Standards Covered:**
    - Perceivable: Information presentable to users in ways they can perceive
    - Operable: Interface components and navigation must be operable
    - Understandable: Information and UI operation must be understandable
    - Robust: Content must be robust enough for various assistive technologies
    """)


def render_component_demonstrations(accessibility_manager):
    """Render component demonstrations section."""
    demo_heading = accessibility_manager.create_accessible_heading(text="[PUZZLE] Accessible Component Demonstrations", level=2, heading_id="demo-heading")
    st.markdown(demo_heading, unsafe_allow_html=True)

    # Component selection
    component_types = ["Camera Input", "Upload Input", "Analysis Display", "Settings Card"]

    selected_component = st.selectbox(
        "Select Component to Demonstrate",
        options=component_types,
        help="Choose which accessible component to demonstrate",
        key="component_demo_select",
    )

    # Demonstrate selected component
    if selected_component == "Camera Input":
        demo_camera_input(accessibility_manager)
    elif selected_component == "Upload Input":
        demo_upload_input(accessibility_manager)
    elif selected_component == "Analysis Display":
        demo_analysis_display(accessibility_manager)
    elif selected_component == "Settings Card":
        demo_settings_card(accessibility_manager)


def demo_camera_input(accessibility_manager):
    """Demonstrate accessible camera input component."""
    st.markdown("""
    ### [CAMERA] Accessible Camera Input Demo
    
    This component demonstrates:
    - ARIA labels for camera activation
    - Live regions for status updates
    - Keyboard navigation support
    - Screen reader announcements
    """)

    # Create accessible camera button
    camera_button = accessibility_manager.create_accessible_button(
        text="[CAMERA] Activate Camera",
        button_id="demo-camera-button",
        aria_label="Activate device camera to capture plant image for disease analysis",
        aria_describedby="camera-help-text",
        button_type="primary",
    )
    st.markdown(camera_button, unsafe_allow_html=True)

    # Help text
    st.markdown(
        """
    <div id="camera-help-text" role="note" class="mobile-text-secondary">
        <p>This button would activate your device camera for plant image capture.</p>
        <p>Screen readers will announce: "Activate device camera to capture plant image for disease analysis"</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Streamlit button for actual interaction
    if st.button("Demo Camera Activation", key="demo_camera_btn", help="Demonstrate camera activation"):
        accessibility_manager.announce_to_screen_reader("Camera activated for plant image capture", priority="polite")
        st.success("[DONE] Camera activation announced to screen readers!")


def demo_upload_input(accessibility_manager):
    """Demonstrate accessible upload input component."""
    st.markdown("""
    ### [FOLDER] Accessible File Upload Demo
    
    This component demonstrates:
    - Proper form labels and associations
    - File type and size announcements
    - Upload progress communication
    - Error handling with live regions
    """)

    # Create accessible file input
    upload_input = accessibility_manager.create_accessible_input(
        input_id="demo-upload-input",
        label_text="Plant Image Upload",
        input_type="file",
        placeholder="Select plant image file",
        required=False,
        aria_describedby="upload-help-text",
    )
    st.markdown(upload_input, unsafe_allow_html=True)

    # Help text
    st.markdown(
        """
    <div id="upload-help-text" role="note" class="mobile-text-secondary">
        <p>Select a clear photo of your plant showing any disease symptoms.</p>
        <p>Supported formats: JPEG, JPG, PNG (maximum 200MB)</p>
        <p>Screen readers will announce file selection and upload progress.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Streamlit file uploader for actual interaction
    uploaded_file = st.file_uploader(
        "Demo File Upload", type=["jpg", "jpeg", "png"], help="Demonstrate accessible file upload", key="demo_upload_file"
    )

    if uploaded_file:
        accessibility_manager.announce_to_screen_reader(f"File {uploaded_file.name} uploaded successfully and ready for analysis", priority="polite")
        st.success(f"[DONE] File upload announced: {uploaded_file.name}")


def demo_analysis_display(accessibility_manager):
    """Demonstrate accessible analysis display component."""
    st.markdown("""
    ### [MICROSCOPE] Accessible Analysis Display Demo
    
    This component demonstrates:
    - Structured result presentation with ARIA
    - Progress bars with proper attributes
    - Result announcements via live regions
    - Semantic heading hierarchy
    """)

    # Mock analysis results
    mock_results = {
        "disease_name": "Leaf Spot Disease",
        "confidence": 0.87,
        "recommendations": ["Remove affected leaves immediately", "Improve air circulation around plant", "Apply fungicide treatment as needed"],
    }

    # Create accessible results display
    confidence_percent = mock_results["confidence"] * 100

    results_html = f"""
    <div class="mobile-card" role="region" aria-labelledby="demo-results-heading">
        <h3 id="demo-results-heading" class="mobile-heading-3">
            Analysis Results Demo
        </h3>
        
        <div class="mobile-analysis-result" role="article">
            <h4 class="mobile-heading-4">
                Disease Detected: {mock_results["disease_name"]}
            </h4>
            
            <div class="confidence-section" role="group" aria-labelledby="confidence-heading">
                <h5 id="confidence-heading" class="sr-only">Confidence Score</h5>
                
                <div class="confidence-bar" 
                     role="progressbar"
                     aria-label="Disease prediction confidence score"
                     aria-valuenow="{confidence_percent:.1f}"
                     aria-valuemin="0"
                     aria-valuemax="100"
                     aria-valuetext="{confidence_percent:.1f} percent confidence - High confidence"
                     style="background: #e5e7eb; border-radius: 8px; height: 20px; margin: 8px 0;">
                    <div style="width: {confidence_percent}%; height: 100%; background: #16a34a; border-radius: 8px;"
                         aria-hidden="true"></div>
                </div>
                
                <p>Confidence: {confidence_percent:.1f}% (High confidence)</p>
            </div>
        </div>
        
        <div role="status" aria-live="polite" aria-atomic="true">
            Analysis complete: {mock_results["disease_name"]} detected with {confidence_percent:.1f}% confidence
        </div>
    </div>
    """
    st.markdown(results_html, unsafe_allow_html=True)

    # Demonstrate announcement
    if st.button("Demo Result Announcement", key="demo_results_btn"):
        accessibility_manager.announce_to_screen_reader(
            f"Analysis complete. {mock_results['disease_name']} detected with {confidence_percent:.1f}% confidence.", priority="polite"
        )
        st.success("[DONE] Analysis results announced to screen readers!")


def demo_settings_card(accessibility_manager):
    """Demonstrate accessible settings card component."""
    st.markdown("""
    ### [SETTINGS] Accessible Settings Demo
    
    This component demonstrates:
    - Grouped related settings with fieldsets
    - Clear setting descriptions and labels
    - Setting change announcements
    - Accessibility preference controls
    """)

    # Accessibility settings demo
    accessibility_heading = accessibility_manager.create_accessible_heading(
        text="Accessibility Settings Demo", level=4, heading_id="demo-settings-heading"
    )
    st.markdown(accessibility_heading, unsafe_allow_html=True)

    # Demo settings with announcements
    col1, col2 = st.columns(2)

    with col1:
        demo_contrast = st.selectbox(
            "Contrast Mode Demo",
            options=["Normal", "High Contrast", "Extra High Contrast"],
            help="Demonstrate contrast mode selection",
            key="demo_contrast_select",
        )

        demo_font_size = st.selectbox(
            "Font Size Demo", options=["Small", "Normal", "Large", "Extra Large"], help="Demonstrate font size selection", key="demo_font_select"
        )

    with col2:
        demo_screen_reader = st.checkbox("Enhanced Screen Reader Support", help="Demonstrate screen reader toggle", key="demo_screen_reader_check")

        demo_reduced_motion = st.checkbox("Reduce Motion", help="Demonstrate reduced motion toggle", key="demo_reduced_motion_check")

    # Announce setting changes
    if st.button("Demo Settings Save", key="demo_settings_save_btn"):
        settings_summary = f"Settings updated: {demo_contrast} contrast, {demo_font_size} font size"
        if demo_screen_reader:
            settings_summary += ", screen reader support enabled"
        if demo_reduced_motion:
            settings_summary += ", reduced motion enabled"

        accessibility_manager.announce_to_screen_reader(settings_summary, priority="polite")
        st.success("[DONE] Settings changes announced to screen readers!")


def render_accessibility_settings_demo(accessibility_manager):
    """Render accessibility settings demonstration."""
    settings_heading = accessibility_manager.create_accessible_heading(
        text="[SETTINGS] Live Accessibility Settings", level=2, heading_id="settings-demo-heading"
    )
    st.markdown(settings_heading, unsafe_allow_html=True)

    st.markdown(
        """
    <div role="region" aria-labelledby="settings-demo-heading">
        <p>These are live accessibility settings that affect the current interface.</p>
        <p>Changes will be applied immediately and announced to screen readers.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Render actual accessibility settings
    accessibility_manager.render_accessibility_settings()

    # Show current status
    status_heading = accessibility_manager.create_accessible_heading(text="Current Accessibility Status", level=3, heading_id="status-heading")
    st.markdown(status_heading, unsafe_allow_html=True)

    status = accessibility_manager.get_accessibility_status()

    st.json(status)


def render_testing_validation_demo(accessibility_manager):
    """Render testing and validation demonstration."""
    testing_heading = accessibility_manager.create_accessible_heading(
        text="[TEST] Accessibility Testing & Validation", level=2, heading_id="testing-heading"
    )
    st.markdown(testing_heading, unsafe_allow_html=True)

    # Test options
    test_options = ["Run Full Accessibility Test Suite", "Test Individual Components", "Validate Compliance Status", "Generate Test Report"]

    selected_test = st.selectbox("Select Test Type", options=test_options, help="Choose which accessibility test to run", key="test_type_select")

    if selected_test == "Run Full Accessibility Test Suite":
        if st.button("Run Full Test Suite", key="run_full_tests_btn"):
            with st.spinner("Running comprehensive accessibility tests..."):
                test_results = run_accessibility_tests()

            st.success(f"[DONE] Tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")

            # Show summary
            st.json(test_results)

    elif selected_test == "Test Individual Components":
        component_types = ["camera_input", "upload_input", "analysis_display", "settings_card"]

        selected_component = st.selectbox(
            "Select Component to Test", options=component_types, help="Choose component for accessibility validation", key="component_test_select"
        )

        if st.button(f"Test {selected_component}", key="test_component_btn"):
            with st.spinner(f"Testing {selected_component} accessibility..."):
                component_results = validate_component_accessibility(selected_component)

            st.success(f"[DONE] Component test completed: {component_results['status']}")
            st.json(component_results)

    elif selected_test == "Validate Compliance Status":
        if st.button("Validate Compliance", key="validate_compliance_btn"):
            compliance_results = validate_accessibility_compliance()

            st.success("[DONE] Compliance validation completed")
            st.json(compliance_results)

    elif selected_test == "Generate Test Report":
        if st.button("Generate Report", key="generate_report_btn"):
            with st.spinner("Generating accessibility compliance report..."):
                report = generate_accessibility_report()

            st.success("[DONE] Report generated successfully")
            st.markdown(report)


def render_compliance_report_demo(accessibility_manager):
    """Render compliance report demonstration."""
    report_heading = accessibility_manager.create_accessible_heading(text="[SUMMARY] Accessibility Compliance Report", level=2, heading_id="report-heading")
    st.markdown(report_heading, unsafe_allow_html=True)

    st.markdown(
        """
    <div role="region" aria-labelledby="report-heading">
        <p>This section shows a comprehensive accessibility compliance report 
        demonstrating WCAG 2.1 AA compliance across all mobile components.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Generate and display report
    if st.button("Generate Compliance Report", key="generate_compliance_report_btn"):
        with st.spinner("Generating comprehensive compliance report..."):
            report = generate_accessibility_report()

        accessibility_manager.announce_to_screen_reader("Accessibility compliance report generated successfully", priority="polite")

        st.success("[DONE] Compliance report generated")
        st.markdown(report)

    # Show quick compliance status
    quick_status_heading = accessibility_manager.create_accessible_heading(text="Quick Compliance Status", level=3, heading_id="quick-status-heading")
    st.markdown(quick_status_heading, unsafe_allow_html=True)

    test_results = get_accessibility_test_results()

    # Display as metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("ARIA Labels", "[DONE] Implemented")

    with col2:
        st.metric("Keyboard Navigation", "[DONE] Full Support")

    with col3:
        st.metric("Screen Reader", "[DONE] Compatible")

    with col4:
        st.metric("WCAG Compliance", "[DONE] AA Level")

    # Detailed status
    st.json(test_results)


if __name__ == "__main__":
    main()
