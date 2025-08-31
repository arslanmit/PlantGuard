"""
Mobile Camera Input Component for PlantGuard UI.

This module provides a mobile-optimized camera input component with
device camera integration using streamlit-webrtc.
"""

import logging
import tempfile
from datetime import datetime
from typing import Any

import streamlit as st
from PIL import Image
from streamlit_webrtc import RTCConfiguration, WebRtcMode, webrtc_streamer

from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileCameraInput(MobileBaseComponent):
    """Mobile-optimized camera input component with device camera integration."""

    def __init__(self, component_id: str, title: str = "Camera Input", **kwargs) -> None:
        """
        Initialize mobile camera input component.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Camera-specific configuration
        self.camera_config = {
            "video_constraints": {
                "width": {"ideal": 1280, "max": 1920},
                "height": {"ideal": 720, "max": 1080},
                "facingMode": "environment",  # Use back camera for plant photos
            },
            "audio": False,  # No audio needed for plant photos
            "rtc_configuration": RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
        }

        # Initialize camera state
        self._initialize_camera_state()

        logger.debug("MobileCameraInput initialized: %s", component_id)

    def _initialize_camera_state(self) -> None:
        """Initialize camera-specific state."""
        camera_state = {
            "camera_active": False,
            "camera_permission_granted": False,
            "last_capture": None,
            "capture_count": 0,
            "camera_error": None,
            "stream_active": False,
        }

        current_state = self.get_state()
        if "camera_data" not in current_state["data"]:
            current_state["data"]["camera_data"] = camera_state
            self.set_state(current_state)

    def render(self) -> None:
        """Render the mobile camera input interface."""
        try:
            # Get current state
            state = self.get_state()
            camera_data = state["data"].get("camera_data", {})

            # Render camera interface container
            st.markdown(
                f"""
                <div class="mobile-camera-input mobile-component" 
                     data-component-id="{self.component_id}"
                     data-testid="camera-input-{self.component_id}">
                """,
                unsafe_allow_html=True,
            )

            # Camera activation button
            col1, col2 = st.columns([3, 1])

            with col1:
                camera_button_text = "[CAMERA] Stop Camera" if camera_data.get("camera_active") else "[CAMERA] Take Photo"
                camera_clicked = st.button(
                    camera_button_text,
                    key=f"{self.component_id}_camera_btn",
                    help="Activate camera to take plant photo",
                    use_container_width=True,
                    type="primary" if not camera_data.get("camera_active") else "secondary",
                )

            with col2:
                # Settings button for camera configuration
                if st.button("[SETTINGS]", key=f"{self.component_id}_settings", help="Camera settings"):
                    self._toggle_camera_settings()

            # Handle camera button click
            if camera_clicked:
                self._handle_camera_toggle()

            # Render camera settings if expanded
            if camera_data.get("settings_expanded", False):
                self._render_camera_settings()

            # Render camera interface if active
            if camera_data.get("camera_active", False):
                self._render_camera_interface()

            # Display last captured image if available
            if camera_data.get("last_capture"):
                self._render_captured_image(camera_data["last_capture"])

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Camera input rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)

    def _handle_camera_toggle(self) -> None:
        """Handle camera activation/deactivation."""
        try:
            state = self.get_state()
            camera_data = state["data"]["camera_data"]

            # Toggle camera state
            camera_data["camera_active"] = not camera_data.get("camera_active", False)

            if camera_data["camera_active"]:
                # Activating camera
                camera_data["camera_error"] = None
                camera_data["stream_active"] = True
                st.success("[CAMERA] Camera activated! Point at plant and capture image.")
            else:
                # Deactivating camera
                camera_data["stream_active"] = False
                st.info("[CAMERA] Camera deactivated.")

            # Update state
            state["data"]["camera_data"] = camera_data
            self.set_state(state)

        except Exception as e:
            logger.error("Camera toggle failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)

    def _render_camera_interface(self) -> None:
        """Render the camera streaming interface using streamlit-webrtc."""
        try:
            st.markdown("### [CAMERA] Camera View")

            # Create WebRTC streamer for camera access
            webrtc_ctx = webrtc_streamer(
                key=f"{self.component_id}_camera_stream",
                mode=WebRtcMode.SENDONLY,
                rtc_configuration=self.camera_config["rtc_configuration"],
                media_stream_constraints={"video": self.camera_config["video_constraints"], "audio": self.camera_config["audio"]},
                video_frame_callback=self._process_video_frame,
                async_processing=True,
            )

            # Camera controls
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("[PHOTO] Capture", key=f"{self.component_id}_capture", disabled=not webrtc_ctx.state.playing):
                    self._capture_image(webrtc_ctx)

            with col2:
                if st.button("[PARTIAL] Flip Camera", key=f"{self.component_id}_flip"):
                    self._flip_camera()

            with col3:
                if st.button("[TODO] Close", key=f"{self.component_id}_close"):
                    self._handle_camera_toggle()

            # Display camera status
            if webrtc_ctx.state.playing:
                st.success("[GREEN] Camera is active")
            else:
                st.warning("[YELLOW] Camera is starting...")

        except Exception as e:
            logger.error("Camera interface rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.HIGH)
            st.error("[TODO] Camera access failed. Please check permissions and try again.")

    def _process_video_frame(self, frame) -> None:
        """Process video frame from camera stream."""
        try:
            # Store current frame for capture
            state = self.get_state()
            camera_data = state["data"]["camera_data"]
            camera_data["current_frame"] = frame
            state["data"]["camera_data"] = camera_data
            self.set_state(state)

        except Exception as e:
            logger.warning("Video frame processing failed: %s", e)

    def _capture_image(self, webrtc_ctx) -> None:
        """Capture image from camera stream."""
        try:
            state = self.get_state()
            camera_data = state["data"]["camera_data"]

            # Get current frame
            current_frame = camera_data.get("current_frame")
            if current_frame is None:
                st.warning("[WARNING] No camera frame available. Please wait for camera to initialize.")
                return

            # Convert frame to PIL Image
            image = self._frame_to_image(current_frame)

            if image:
                # Store captured image
                camera_data["last_capture"] = {
                    "image": image,
                    "timestamp": datetime.now().isoformat(),
                    "filename": f"camera_capture_{camera_data.get('capture_count', 0) + 1}.jpg",
                }
                camera_data["capture_count"] = camera_data.get("capture_count", 0) + 1

                # Update state
                state["data"]["camera_data"] = camera_data
                self.set_state(state)

                # Trigger analysis
                self._trigger_analysis(image)

                st.success("[PHOTO] Image captured successfully!")

            else:
                st.error("[TODO] Failed to capture image. Please try again.")

        except Exception as e:
            logger.error("Image capture failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)

    def _frame_to_image(self, frame) -> Image.Image | None:
        """Convert video frame to PIL Image."""
        try:
            # Convert frame to numpy array
            import numpy as np

            # Handle different frame formats
            if hasattr(frame, "to_ndarray"):
                img_array = frame.to_ndarray(format="rgb24")
            elif hasattr(frame, "to_image"):
                return frame.to_image()
            else:
                # Fallback for different frame types
                img_array = np.array(frame)

            # Convert to PIL Image
            image = Image.fromarray(img_array)
            return image

        except Exception as e:
            logger.error("Frame to image conversion failed: %s", e)
            return None

    def _flip_camera(self) -> None:
        """Toggle between front and back camera."""
        try:
            state = self.get_state()
            camera_data = state["data"]["camera_data"]

            # Toggle facing mode
            current_facing = self.camera_config["video_constraints"].get("facingMode", "environment")
            new_facing = "user" if current_facing == "environment" else "environment"

            self.camera_config["video_constraints"]["facingMode"] = new_facing
            camera_data["camera_flipped"] = not camera_data.get("camera_flipped", False)

            # Update state
            state["data"]["camera_data"] = camera_data
            self.set_state(state)

            st.info(f"[PARTIAL] Switched to {'front' if new_facing == 'user' else 'back'} camera")

        except Exception as e:
            logger.error("Camera flip failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.LOW)

    def _render_camera_settings(self) -> None:
        """Render camera settings panel."""
        with st.expander("[CAMERA] Camera Settings", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                # Resolution settings
                resolution_options = {
                    "HD (1280x720)": {"width": 1280, "height": 720},
                    "Full HD (1920x1080)": {"width": 1920, "height": 1080},
                    "Standard (640x480)": {"width": 640, "height": 480},
                }

                selected_resolution = st.selectbox(
                    "Resolution", options=list(resolution_options.keys()), index=0, key=f"{self.component_id}_resolution"
                )

                # Update camera config
                if selected_resolution in resolution_options:
                    res = resolution_options[selected_resolution]
                    self.camera_config["video_constraints"]["width"]["ideal"] = res["width"]
                    self.camera_config["video_constraints"]["height"]["ideal"] = res["height"]

            with col2:
                # Camera selection
                camera_options = ["Back Camera (Environment)", "Front Camera (User)"]
                selected_camera = st.selectbox("Camera", options=camera_options, index=0, key=f"{self.component_id}_camera_select")

                # Update facing mode
                facing_mode = "environment" if "Back" in selected_camera else "user"
                self.camera_config["video_constraints"]["facingMode"] = facing_mode

    def _toggle_camera_settings(self) -> None:
        """Toggle camera settings panel."""
        state = self.get_state()
        camera_data = state["data"]["camera_data"]
        camera_data["settings_expanded"] = not camera_data.get("settings_expanded", False)
        state["data"]["camera_data"] = camera_data
        self.set_state(state)

    def _render_captured_image(self, capture_data: dict[str, Any]) -> None:
        """Render the last captured image."""
        st.markdown("### [PHOTO] Captured Image")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(capture_data["image"], caption=f"Captured: {capture_data['timestamp'][:19]}", use_column_width=True)

        # Action buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("[PARTIAL] Retake", key=f"{self.component_id}_retake"):
                self._clear_capture()

        with col2:
            if st.button("[SAVE] Save", key=f"{self.component_id}_save"):
                self._save_image(capture_data)

        with col3:
            if st.button("[SEARCH] Analyze", key=f"{self.component_id}_analyze"):
                self._trigger_analysis(capture_data["image"])

        with col4:
            if st.button("[TODO] Delete", key=f"{self.component_id}_delete"):
                self._clear_capture()

    def _clear_capture(self) -> None:
        """Clear the captured image."""
        state = self.get_state()
        camera_data = state["data"]["camera_data"]
        camera_data["last_capture"] = None
        state["data"]["camera_data"] = camera_data
        self.set_state(state)
        st.success("[DELETE] Image cleared")

    def _save_image(self, capture_data: dict[str, Any]) -> None:
        """Save captured image to temporary file."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                capture_data["image"].save(tmp_file.name, "JPEG", quality=95)

                # Store file path in state for potential download
                state = self.get_state()
                camera_data = state["data"]["camera_data"]
                camera_data["saved_image_path"] = tmp_file.name
                state["data"]["camera_data"] = camera_data
                self.set_state(state)

                st.success(f"[SAVE] Image saved: {capture_data['filename']}")

        except Exception as e:
            logger.error("Image save failed: %s", e)
            st.error("[TODO] Failed to save image")

    def _trigger_analysis(self, image: Image.Image) -> None:
        """Trigger plant disease analysis for captured image."""
        try:
            # Import mobile integration
            from .mobile_adapter_integration import mobile_integration

            # Perform analysis using mobile integration
            with st.spinner("[SEARCH] Analyzing plant image..."):
                analysis_result = mobile_integration.analyze_image(image=image, source="camera", component_id=self.component_id)

                # Extract results
                disease_name = analysis_result.get("disease_name", "Unknown")
                confidence = analysis_result.get("confidence", 0.0)

                # Check for errors
                if "error" in analysis_result:
                    st.error(f"[TODO] Analysis failed: {analysis_result['error']}")
                    return

                # Display result with mobile-optimized feedback
                if confidence > 0.7:
                    st.success(f"[LEAF] Analysis Complete: {disease_name} ({confidence:.1%} confidence)")
                elif confidence > 0.4:
                    st.warning(f"[WARNING] Moderate confidence: {disease_name} ({confidence:.1%} confidence)")
                    st.info("[TIP] Try taking another photo with better lighting or closer to the affected area.")
                else:
                    st.warning(f"[WARNING] Low confidence result: {disease_name} ({confidence:.1%} confidence)")
                    st.info("[TIP] For better results:\n- Ensure good lighting\n- Focus on affected plant parts\n- Hold camera steady")

                # Show disease information if available
                disease_info = analysis_result.get("disease_info", {})
                if disease_info and disease_info.get("description"):
                    with st.expander("i Disease Information", expanded=False):
                        st.write(f"**Description:** {disease_info['description']}")

                        # Show immediate treatment steps
                        treatment = disease_info.get("treatment", {})
                        if treatment.get("immediate"):
                            st.write("**Immediate Actions:**")
                            for i, step in enumerate(treatment["immediate"][:3], 1):
                                st.write(f"{i}. {step}")

        except Exception as e:
            logger.error("Analysis failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)
            st.error("[TODO] Analysis failed. Please try again or upload the image manually.")

    def get_captured_image(self) -> Image.Image | None:
        """Get the last captured image."""
        state = self.get_state()
        camera_data = state["data"].get("camera_data", {})
        capture_data = camera_data.get("last_capture")

        if capture_data:
            return capture_data["image"]
        return None

    def clear_camera_state(self) -> None:
        """Clear all camera state and captured images."""
        self._initialize_camera_state()
        st.success("[CLEAN] Camera state cleared")
