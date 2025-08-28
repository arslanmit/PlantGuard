"""
Mobile Upload Input Component for PlantGuard UI.

This module provides a mobile-optimized file upload component with
drag-and-drop support and image validation.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image

from .mobile_base_component import MobileBaseComponent
from .mobile_error_handler import ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MobileUploadInput(MobileBaseComponent):
    """Mobile-optimized file upload component with drag-and-drop support."""

    def __init__(self, component_id: str, title: str = "Upload Input", **kwargs):
        """
        Initialize mobile upload input component.

        Args:
            component_id: Unique identifier for this component
            title: Display title for the component
            **kwargs: Additional component arguments
        """
        super().__init__(component_id, title, **kwargs)

        # Upload configuration
        self.upload_config = {
            "max_file_size": 200 * 1024 * 1024,  # 200MB
            "allowed_types": ["jpg", "jpeg", "png", "webp"],
            "max_files": 5,
            "image_quality": 95,
        }

        # Initialize upload state
        self._initialize_upload_state()

        logger.debug("MobileUploadInput initialized: %s", component_id)

    def _initialize_upload_state(self) -> None:
        """Initialize upload-specific state."""
        upload_state = {
            "uploaded_files": [],
            "current_file": None,
            "upload_progress": 0,
            "validation_results": {},
            "processing_status": "idle",  # idle, uploading, processing, complete, error
            "last_upload": None,
        }

        current_state = self.get_state()
        if "upload_data" not in current_state["data"]:
            current_state["data"]["upload_data"] = upload_state
            self.set_state(current_state)

    def render(self) -> None:
        """Render the mobile upload input interface."""
        try:
            # Get current state
            state = self.get_state()
            upload_data = state["data"].get("upload_data", {})

            # Render upload interface container
            st.markdown(
                f"""
                <div class="mobile-upload-input mobile-component" 
                     data-component-id="{self.component_id}"
                     data-testid="upload-input-{self.component_id}">
                """,
                unsafe_allow_html=True,
            )

            # Upload interface
            self._render_upload_interface(upload_data)

            # Show upload progress if uploading
            if upload_data.get("processing_status") == "uploading":
                self._render_upload_progress(upload_data)

            # Display uploaded files
            if upload_data.get("uploaded_files"):
                self._render_uploaded_files(upload_data["uploaded_files"])

            # Display current file if selected
            if upload_data.get("current_file"):
                self._render_current_file(upload_data["current_file"])

            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Upload input rendering failed: %s", e)
            self.handle_error(e, ErrorCategory.COMPONENT, ErrorSeverity.HIGH)

    def _render_upload_interface(self, upload_data: dict[str, Any]) -> None:
        """Render the main upload interface."""
        # File uploader with mobile optimization
        uploaded_file = st.file_uploader(
            "📁 Select Plant Image",
            type=self.upload_config["allowed_types"],
            key=f"{self.component_id}_uploader",
            help=f"Upload plant images (max {self.upload_config['max_file_size'] // (1024 * 1024)}MB)",
            accept_multiple_files=False,
            label_visibility="visible",
        )

        # Handle file upload
        if uploaded_file is not None:
            self._handle_file_upload(uploaded_file)

        # Drag and drop area (visual enhancement)
        st.markdown(
            """
            <div class="mobile-upload-dropzone">
                <div class="upload-icon">📁</div>
                <p>Drag and drop plant images here</p>
                <p class="upload-hint">or use the button above</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upload tips
        with st.expander("📋 Upload Tips", expanded=False):
            st.markdown("""
            **For best results:**
            - Use clear, well-lit photos
            - Focus on affected plant parts
            - Avoid blurry or dark images
            - Supported formats: JPG, PNG, WebP
            - Maximum file size: 200MB
            """)

    def _handle_file_upload(self, uploaded_file) -> None:
        """Handle uploaded file processing."""
        try:
            # Update processing status
            self._update_processing_status("uploading")

            # Validate file
            validation_result = self._validate_uploaded_file(uploaded_file)

            if not validation_result["is_valid"]:
                self._show_validation_errors(validation_result["errors"])
                self._update_processing_status("error")
                return

            # Process the uploaded file
            self._update_processing_status("processing")

            # Load image
            image = Image.open(uploaded_file)

            # Create file info
            file_info = {
                "filename": uploaded_file.name,
                "size": uploaded_file.size,
                "type": uploaded_file.type,
                "image": image,
                "upload_timestamp": datetime.now().isoformat(),
                "validation": validation_result,
            }

            # Store file info
            state = self.get_state()
            upload_data = state["data"]["upload_data"]
            upload_data["current_file"] = file_info
            upload_data["last_upload"] = file_info
            upload_data["processing_status"] = "complete"

            # Add to uploaded files list
            if "uploaded_files" not in upload_data:
                upload_data["uploaded_files"] = []

            upload_data["uploaded_files"].append(file_info)

            # Keep only recent files (limit memory usage)
            if len(upload_data["uploaded_files"]) > self.upload_config["max_files"]:
                upload_data["uploaded_files"] = upload_data["uploaded_files"][-self.upload_config["max_files"] :]

            # Update state
            state["data"]["upload_data"] = upload_data
            self.set_state(state)

            # Trigger analysis
            self._trigger_analysis(image, uploaded_file.name)

            st.success(f"✅ File uploaded successfully: {uploaded_file.name}")

        except Exception as e:
            logger.error("File upload processing failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)
            self._update_processing_status("error")
            st.error("❌ Failed to process uploaded file. Please try again.")

    def _validate_uploaded_file(self, uploaded_file) -> dict[str, Any]:
        """Validate uploaded file."""
        validation_result = {"is_valid": True, "errors": [], "warnings": []}

        try:
            # Check file size
            if uploaded_file.size > self.upload_config["max_file_size"]:
                validation_result["is_valid"] = False
                max_mb = self.upload_config["max_file_size"] // (1024 * 1024)
                validation_result["errors"].append(f"File too large. Maximum size: {max_mb}MB")

            # Check file type
            file_extension = Path(uploaded_file.name).suffix.lower().lstrip(".")
            if file_extension not in self.upload_config["allowed_types"]:
                validation_result["is_valid"] = False
                allowed = ", ".join(self.upload_config["allowed_types"])
                validation_result["errors"].append(f"Unsupported file type. Allowed: {allowed}")

            # Try to open as image
            try:
                image = Image.open(uploaded_file)

                # Check image dimensions
                width, height = image.size
                if width < 100 or height < 100:
                    validation_result["warnings"].append("Image resolution is very low. Results may be poor.")

                if width > 4000 or height > 4000:
                    validation_result["warnings"].append("Image resolution is very high. Processing may be slow.")

                # Check image format
                if image.format not in ["JPEG", "PNG", "WEBP"]:
                    validation_result["warnings"].append(f"Unusual image format: {image.format}")

                # Reset file pointer
                uploaded_file.seek(0)

            except Exception as img_error:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Invalid image file: {img_error!s}")

        except Exception as e:
            logger.error("File validation failed: %s", e)
            validation_result["is_valid"] = False
            validation_result["errors"].append("File validation failed")

        return validation_result

    def _show_validation_errors(self, errors: list[str]) -> None:
        """Display validation errors to user."""
        for error in errors:
            st.error(f"❌ {error}")

    def _update_processing_status(self, status: str) -> None:
        """Update processing status."""
        state = self.get_state()
        upload_data = state["data"]["upload_data"]
        upload_data["processing_status"] = status
        state["data"]["upload_data"] = upload_data
        self.set_state(state)

    def _render_upload_progress(self, upload_data: dict[str, Any]) -> None:
        """Render upload progress indicator."""
        progress = upload_data.get("upload_progress", 0)

        st.markdown("### 📤 Uploading...")
        progress_bar = st.progress(progress / 100)

        if progress < 100:
            st.info(f"Upload progress: {progress}%")
        else:
            st.success("Upload complete!")

    def _render_uploaded_files(self, uploaded_files: list[dict[str, Any]]) -> None:
        """Render list of uploaded files."""
        st.markdown("### 📁 Recent Uploads")

        for i, file_info in enumerate(reversed(uploaded_files[-3:])):  # Show last 3 files
            with st.expander(f"📄 {file_info['filename']}", expanded=(i == 0)):
                col1, col2 = st.columns([2, 1])

                with col1:
                    # File details
                    st.write(f"**Size:** {self._format_file_size(file_info['size'])}")
                    st.write(f"**Type:** {file_info['type']}")
                    st.write(f"**Uploaded:** {file_info['upload_timestamp'][:19]}")

                    # Validation info
                    if file_info.get("validation", {}).get("warnings"):
                        for warning in file_info["validation"]["warnings"]:
                            st.warning(f"⚠️ {warning}")

                with col2:
                    # Action buttons
                    if st.button("🔍 Analyze", key=f"{self.component_id}_analyze_{i}"):
                        self._trigger_analysis(file_info["image"], file_info["filename"])

                    if st.button("❌ Remove", key=f"{self.component_id}_remove_{i}"):
                        self._remove_uploaded_file(file_info["filename"])

    def _render_current_file(self, file_info: dict[str, Any]) -> None:
        """Render the currently selected file."""
        st.markdown("### 🖼️ Current Image")

        # Display image
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(file_info["image"], caption=file_info["filename"], use_column_width=True)

        # File information
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Filename:** {file_info['filename']}")
            st.write(f"**Size:** {self._format_file_size(file_info['size'])}")

        with col2:
            st.write(f"**Dimensions:** {file_info['image'].size[0]}x{file_info['image'].size[1]}")
            st.write(f"**Format:** {file_info['image'].format}")

        # Action buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🔍 Analyze", key=f"{self.component_id}_analyze_current"):
                self._trigger_analysis(file_info["image"], file_info["filename"])

        with col2:
            if st.button("💾 Save", key=f"{self.component_id}_save_current"):
                self._save_image(file_info)

        with col3:
            if st.button("🔄 Replace", key=f"{self.component_id}_replace"):
                self._clear_current_file()

        with col4:
            if st.button("❌ Clear", key=f"{self.component_id}_clear_current"):
                self._clear_current_file()

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _remove_uploaded_file(self, filename: str) -> None:
        """Remove uploaded file from list."""
        state = self.get_state()
        upload_data = state["data"]["upload_data"]

        # Remove from uploaded files
        upload_data["uploaded_files"] = [f for f in upload_data["uploaded_files"] if f["filename"] != filename]

        # Clear current file if it matches
        if upload_data.get("current_file") and upload_data["current_file"]["filename"] == filename:
            upload_data["current_file"] = None

        # Update state
        state["data"]["upload_data"] = upload_data
        self.set_state(state)

        st.success(f"🗑️ Removed: {filename}")

    def _clear_current_file(self) -> None:
        """Clear the current file selection."""
        state = self.get_state()
        upload_data = state["data"]["upload_data"]
        upload_data["current_file"] = None
        state["data"]["upload_data"] = upload_data
        self.set_state(state)

        st.success("🧹 Current file cleared")

    def _save_image(self, file_info: dict[str, Any]) -> None:
        """Save uploaded image to temporary file."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                file_info["image"].save(tmp_file.name, "JPEG", quality=self.upload_config["image_quality"])

                # Store file path in state
                state = self.get_state()
                upload_data = state["data"]["upload_data"]
                upload_data["saved_image_path"] = tmp_file.name
                state["data"]["upload_data"] = upload_data
                self.set_state(state)

                st.success(f"💾 Image saved: {file_info['filename']}")

        except Exception as e:
            logger.error("Image save failed: %s", e)
            st.error("❌ Failed to save image")

    def _trigger_analysis(self, image: Image.Image, filename: str) -> None:
        """Trigger plant disease analysis for uploaded image."""
        try:
            # Import mobile integration
            from .mobile_adapter_integration import mobile_integration

            # Perform analysis using mobile integration
            with st.spinner(f"🔍 Analyzing {filename}..."):
                analysis_result = mobile_integration.analyze_image(image=image, source="upload", component_id=self.component_id)

                # Extract results
                disease_name = analysis_result.get("disease_name", "Unknown")
                confidence = analysis_result.get("confidence", 0.0)

                # Check for errors
                if "error" in analysis_result:
                    st.error(f"❌ Analysis failed: {analysis_result['error']}")
                    return

                # Display result with enhanced information
                if confidence > 0.7:
                    st.success(f"🌿 Analysis Complete: {disease_name} ({confidence:.1%} confidence)")
                elif confidence > 0.4:
                    st.warning(f"⚠️ Moderate confidence: {disease_name} ({confidence:.1%} confidence)")
                else:
                    st.warning(f"⚠️ Low confidence result: {disease_name} ({confidence:.1%} confidence)")
                    st.info("💡 Try uploading a clearer image with better lighting for more accurate results.")

                # Show disease information if available
                disease_info = analysis_result.get("disease_info", {})
                if disease_info and disease_info.get("description"):
                    with st.expander("i Disease Information", expanded=False):
                        st.write(f"**Description:** {disease_info['description']}")

                        # Show treatment if available
                        treatment = disease_info.get("treatment", {})
                        if treatment.get("immediate"):
                            st.write("**Immediate Treatment:**")
                            for i, step in enumerate(treatment["immediate"][:3], 1):
                                st.write(f"{i}. {step}")

        except Exception as e:
            logger.error("Analysis failed: %s", e)
            self.handle_error(e, ErrorCategory.INTEGRATION, ErrorSeverity.MEDIUM)
            st.error("❌ Analysis failed. Please try again or check the image quality.")

    def get_current_image(self) -> Image.Image | None:
        """Get the currently selected image."""
        state = self.get_state()
        upload_data = state["data"].get("upload_data", {})
        current_file = upload_data.get("current_file")

        if current_file:
            return current_file["image"]
        return None

    def get_uploaded_files(self) -> list[dict[str, Any]]:
        """Get list of uploaded files."""
        state = self.get_state()
        upload_data = state["data"].get("upload_data", {})
        return upload_data.get("uploaded_files", [])

    def clear_upload_state(self) -> None:
        """Clear all upload state and files."""
        self._initialize_upload_state()
        st.success("🧹 Upload state cleared")
