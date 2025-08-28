"""
Mobile Image Analysis Interface for PlantGuard

Integrates VisionAdapter with mobile-optimized UI components.
Provides touch-friendly image upload, analysis, and results display.
"""

import time
from typing import Any

import streamlit as st
from PIL import Image

# Import existing adapters
try:
    from core.model_manager import ModelManager
    from core.vision import VisionAdapter
except ImportError:
    # Fallback for development/testing
    from src.adapters_compat import VisionAdapter

    ModelManager = None

from .mobile_component_registry import ComponentMetadata, MobileComponent, register_mobile_component


@register_mobile_component
class MobileImageAnalysis(MobileComponent):
    """Mobile-optimized image analysis interface.

    Features:
    - Touch-friendly image upload
    - Camera integration
    - Real-time analysis with progress
    - Mobile-optimized results display
    - AI agent testable
    """

    def __init__(self, component_id: str = "mobile_image_analysis", **kwargs):
        super().__init__(component_id, **kwargs)
        self.vision_adapter = None
        self.model_manager = kwargs.get("model_manager")
        self.max_image_size = kwargs.get("max_image_size", (1024, 1024))
        self.supported_formats = ["jpg", "jpeg", "png", "webp"]

    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        return ComponentMetadata(
            component_id=self.component_id,
            component_type="image_analysis",
            display_name="Mobile Image Analysis",
            description="Mobile interface for plant disease detection via image analysis",
            ai_agent_friendly_description=(
                "Image analysis component that provides mobile-optimized interface for "
                "uploading plant images, running AI analysis, and displaying results"
            ),
            interactive_elements=[
                {
                    "id": "image_uploader",
                    "type": "file_uploader",
                    "key": f"{self.component_id}_image_uploader",
                    "description": "Image file upload widget",
                    "testable": True,
                },
                {
                    "id": "camera_capture",
                    "type": "camera_input",
                    "key": f"{self.component_id}_camera",
                    "description": "Camera capture widget",
                    "testable": True,
                },
                {
                    "id": "analyze_button",
                    "type": "button",
                    "key": f"{self.component_id}_analyze",
                    "description": "Analysis trigger button",
                    "testable": True,
                },
                {
                    "id": "clear_button",
                    "type": "button",
                    "key": f"{self.component_id}_clear",
                    "description": "Clear results button",
                    "testable": True,
                },
            ],
            state_dependencies=["uploaded_image", "analysis_results", "analysis_in_progress", "vision_adapter_loaded"],
            css_classes=["mobile-image-analysis", "mobile-image-upload", "mobile-analysis-results", "mobile-image-preview"],
            test_scenarios=[
                {
                    "name": "image_upload",
                    "description": "Test image upload functionality",
                    "expected_outcome": "Image uploads and displays correctly",
                },
                {"name": "analysis_execution", "description": "Test analysis execution", "expected_outcome": "Analysis runs and returns results"},
                {
                    "name": "results_display",
                    "description": "Test results display formatting",
                    "expected_outcome": "Results display in mobile-friendly format",
                },
            ],
            ai_agent_instructions={
                "testing": "Test image upload, analysis execution, results display",
                "fixing": "Initialize VisionAdapter, handle upload errors, format results",
                "monitoring": "Monitor analysis performance, image processing times",
            },
            version="1.0.0",
            ai_agent_testable=True,
            auto_fix_enabled=True,
        )

    def initialize_vision_components(self) -> None:
        """Initialize vision analysis components."""
        # Initialize session state
        if "uploaded_image" not in st.session_state:
            st.session_state.uploaded_image = None

        if "analysis_results" not in st.session_state:
            st.session_state.analysis_results = None

        if "analysis_in_progress" not in st.session_state:
            st.session_state.analysis_in_progress = False

        if "vision_adapter_loaded" not in st.session_state:
            st.session_state.vision_adapter_loaded = False

        # Initialize VisionAdapter if not already done
        if not self.vision_adapter:
            try:
                self.vision_adapter = VisionAdapter()
                st.session_state.vision_adapter_loaded = True
            except Exception as e:
                st.error(f"Failed to initialize VisionAdapter: {e}")
                st.session_state.vision_adapter_loaded = False

    def render_image_upload_section(self) -> Image.Image | None:
        """Render image upload interface.

        Returns:
            PIL.Image: Uploaded image or None
        """
        st.markdown("### 📸 Upload Plant Image")

        # Create tabs for different input methods
        upload_tab, camera_tab = st.tabs(["📎 Upload File", "📷 Camera"])

        uploaded_image = None

        with upload_tab:
            uploaded_file = st.file_uploader(
                "Choose plant image",
                type=self.supported_formats,
                key=f"{self.component_id}_image_uploader",
                help="Upload a clear photo of plant leaves showing any symptoms",
            )

            if uploaded_file:
                try:
                    uploaded_image = Image.open(uploaded_file)
                    st.session_state.uploaded_image = uploaded_image
                except Exception as e:
                    st.error(f"Error loading image: {e}")

        with camera_tab:
            # Camera input (Streamlit camera_input widget)
            camera_image = st.camera_input("Take a photo", key=f"{self.component_id}_camera", help="Take a clear photo of the plant leaves")

            if camera_image:
                try:
                    uploaded_image = Image.open(camera_image)
                    st.session_state.uploaded_image = uploaded_image
                except Exception as e:
                    st.error(f"Error processing camera image: {e}")

        return uploaded_image

    def render_image_preview(self, image: Image.Image) -> None:
        """Render mobile-optimized image preview."""
        if not image:
            return

        st.markdown("#### 🖼️ Image Preview")

        # Display image with mobile-friendly sizing
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(image, caption="Uploaded Plant Image", use_column_width=True)

        # Image info
        with st.expander("[SUMMARY] Image Information"):
            st.markdown(f"**Size:** {image.size[0]} x {image.size[1]} pixels")
            st.markdown(f"**Format:** {image.format}")
            st.markdown(f"**Mode:** {image.mode}")

    def render_analysis_controls(self, has_image: bool) -> bool:
        """Render analysis control buttons.

        Returns:
            bool: True if analysis was triggered
        """
        if not has_image:
            st.info("[MOBILE] Upload an image to start analysis")
            return False

        col1, col2 = st.columns(2)

        with col1:
            analyze_clicked = st.button(
                "🔍 Analyze Plant",
                key=f"{self.component_id}_analyze",
                use_container_width=True,
                disabled=st.session_state.get("analysis_in_progress", False),
                type="primary",
            )

        with col2:
            clear_clicked = st.button("🗑️ Clear", key=f"{self.component_id}_clear", use_container_width=True)

        if clear_clicked:
            self.clear_analysis()
            st.rerun()

        return analyze_clicked

    def perform_analysis(self, image: Image.Image) -> dict[str, Any]:
        """Perform plant disease analysis.

        Returns:
            Dict containing analysis results
        """
        if not self.vision_adapter:
            return {"error": "Vision adapter not initialized", "success": False}

        try:
            st.session_state.analysis_in_progress = True

            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Preprocess image
            status_text.text("Preprocessing image...")
            progress_bar.progress(20)

            # Resize image if too large
            if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                image = image.resize(self.max_image_size, Image.Resampling.LANCZOS)

            # Run analysis
            status_text.text("Analyzing plant health...")
            progress_bar.progress(60)

            # Get prediction
            prediction, confidence = self.vision_adapter.predict(image)

            status_text.text("Generating detailed results...")
            progress_bar.progress(80)

            # Get additional info if available
            try:
                raw_class, readable_name, confidence_score, plant_type = self.vision_adapter.predict_with_readable_name(image)

                results = {
                    "success": True,
                    "prediction": readable_name,
                    "confidence": confidence_score,
                    "plant_type": plant_type,
                    "raw_class": raw_class,
                    "is_healthy": self.vision_adapter.is_healthy(raw_class),
                    "timestamp": time.time(),
                }
            except AttributeError:
                # Fallback for basic adapter
                results = {
                    "success": True,
                    "prediction": prediction,
                    "confidence": confidence,
                    "plant_type": "Unknown",
                    "raw_class": prediction,
                    "is_healthy": "healthy" in prediction.lower(),
                    "timestamp": time.time(),
                }

            progress_bar.progress(100)
            status_text.text("Analysis complete!")

            # Clear progress indicators after a moment
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

            return results

        except Exception as e:
            return {"error": str(e), "success": False, "timestamp": time.time()}
        finally:
            st.session_state.analysis_in_progress = False

    def render_analysis_results(self, results: dict[str, Any]) -> None:
        """Render analysis results in mobile-friendly format."""
        if not results:
            return

        if not results.get("success", False):
            st.error(f"Analysis failed: {results.get('error', 'Unknown error')}")
            return

        st.markdown("### 🔍 Analysis Results")

        # Main result card
        is_healthy = results.get("is_healthy", False)
        confidence = results.get("confidence", 0.0)
        prediction = results.get("prediction", "Unknown")
        plant_type = results.get("plant_type", "Unknown")

        # Result styling based on health status
        if is_healthy:
            result_icon = "[DONE]"
            result_color = "green"
            result_message = "Plant appears healthy!"
        else:
            result_icon = "[WARNING]"
            result_color = "orange"
            result_message = "Potential issue detected"

        # Display main result
        st.markdown(
            f"""
        <div class="mobile-analysis-results" style="
            padding: 1rem; 
            border-radius: 12px; 
            border-left: 4px solid {result_color};
            background-color: rgba(22, 163, 74, 0.05);
            margin: 1rem 0;
        ">
            <h4>{result_icon} {result_message}</h4>
            <p><strong>Diagnosis:</strong> {prediction}</p>
            <p><strong>Plant Type:</strong> {plant_type}</p>
            <p><strong>Confidence:</strong> {confidence:.1%}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Detailed information in expandable sections
        with st.expander("[SUMMARY] Detailed Analysis"):
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Confidence Score", f"{confidence:.1%}")
                st.metric("Plant Type", plant_type)

            with col2:
                st.metric("Health Status", "Healthy" if is_healthy else "Needs Attention")
                timestamp = results.get("timestamp", time.time())
                st.metric("Analysis Time", time.strftime("%H:%M:%S", time.localtime(timestamp)))

        # Recommendations based on results
        if not is_healthy:
            with st.expander("[TIP] Recommendations"):
                st.markdown("""
                **General Care Tips:**
                - Ensure proper watering (not too much, not too little)
                - Check for adequate light conditions
                - Inspect for pests or fungal issues
                - Consider soil drainage and nutrition
                
                **Next Steps:**
                - Monitor plant daily for changes
                - Take action based on specific diagnosis
                - Consult plant care experts if symptoms persist
                """)
        else:
            with st.expander("🌱 Healthy Plant Care"):
                st.markdown("""
                **Keep Your Plant Healthy:**
                - Maintain current care routine
                - Regular monitoring for early detection
                - Consistent watering schedule
                - Proper light exposure
                - Regular fertilization as needed
                """)

    def clear_analysis(self) -> None:
        """Clear current analysis and uploaded image."""
        st.session_state.uploaded_image = None
        st.session_state.analysis_results = None
        st.session_state.analysis_in_progress = False

    def render(self, **kwargs) -> dict[str, Any]:
        """Render the complete mobile image analysis interface.

        Returns:
            Dict containing analysis results or status
        """
        # Initialize components
        self.initialize_vision_components()

        # Main container
        st.markdown('<div class="mobile-image-analysis" data-component="mobile-image-analysis" data-testable="true">', unsafe_allow_html=True)

        # Check if VisionAdapter is available
        if not st.session_state.get("vision_adapter_loaded", False):
            st.warning("[WARNING] Vision analysis not available. Please check system configuration.")
            st.markdown("</div>", unsafe_allow_html=True)
            return {"error": "VisionAdapter not loaded", "success": False}

        # Image upload section
        uploaded_image = self.render_image_upload_section()

        # Show image preview if available
        current_image = uploaded_image or st.session_state.get("uploaded_image")
        if current_image:
            self.render_image_preview(current_image)

        # Analysis controls
        analyze_triggered = self.render_analysis_controls(current_image is not None)

        # Perform analysis if triggered
        if analyze_triggered and current_image:
            with st.spinner("Analyzing plant image..."):
                results = self.perform_analysis(current_image)
                st.session_state.analysis_results = results

        # Display results
        current_results = st.session_state.get("analysis_results")
        if current_results:
            self.render_analysis_results(current_results)

        # Close container
        st.markdown("</div>", unsafe_allow_html=True)

        return current_results or {}

    def get_analysis_status(self) -> dict[str, Any]:
        """Get current analysis status for AI agent monitoring."""
        return {
            "component_id": self.component_id,
            "vision_adapter_loaded": st.session_state.get("vision_adapter_loaded", False),
            "has_uploaded_image": st.session_state.get("uploaded_image") is not None,
            "analysis_in_progress": st.session_state.get("analysis_in_progress", False),
            "has_results": st.session_state.get("analysis_results") is not None,
            "last_analysis_success": st.session_state.get("analysis_results", {}).get("success", False)
            if st.session_state.get("analysis_results")
            else None,
            "supported_formats": self.supported_formats,
            "max_image_size": self.max_image_size,
        }


# Utility functions
def create_mobile_image_analysis(model_manager=None, max_image_size=(1024, 1024)) -> MobileImageAnalysis:
    """Create and return a MobileImageAnalysis instance."""
    return MobileImageAnalysis(component_id="mobile_image_analysis", model_manager=model_manager, max_image_size=max_image_size)


def render_image_analysis_interface() -> dict[str, Any]:
    """Convenience function to render image analysis interface."""
    analysis = create_mobile_image_analysis()
    return analysis.render()
