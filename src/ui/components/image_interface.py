"""Image Input and Camera Integration for PlantGuard.

This module provides comprehensive image input capabilities including
multi-file upload, camera capture, image validation, and preprocessing
for the PlantGuard multimodal plant disease detection system.
"""

import io
import logging
from pathlib import Path

try:
    import cv2
except Exception:
    # Provide a minimal fallback so tests can import this module without OpenCV installed
    cv2 = None
import streamlit as st
from PIL import ExifTags, Image

logger = logging.getLogger(__name__)


class ImageInterface:
    """Image input and camera integration with upload and capture capabilities."""

    def __init__(self):
        """Initialize image interface."""
        self.max_file_size = 200 * 1024 * 1024  # 200MB
        self.supported_formats = ["jpg", "jpeg", "png"]
        self.max_image_dimension = 4096  # Maximum width/height
        self.target_size = (224, 224)  # Target size for model input

        # Initialize session state
        if "uploaded_images" not in st.session_state:
            st.session_state.uploaded_images = []
        if "captured_image" not in st.session_state:
            st.session_state.captured_image = None
        if "processed_images" not in st.session_state:
            st.session_state.processed_images = []

    def validate_image_file(self, image_file) -> tuple[bool, str]:
        """Validate uploaded image file.

        Args:
            image_file: Streamlit uploaded file object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not image_file:
            return False, "No image file provided"

        # Check file size
        if image_file.size > self.max_file_size:
            size_mb = image_file.size / (1024 * 1024)
            return False, f"Image too large ({size_mb:.1f}MB, max 200MB)"

        # Check file extension
        file_extension = Path(image_file.name).suffix.lower().lstrip(".")
        if file_extension not in self.supported_formats:
            return False, f"Unsupported format. Use: {', '.join(self.supported_formats)}"

        return True, ""

    def load_and_validate_image(self, image_file) -> Image.Image | None:
        """Load and validate image file.

        Args:
            image_file: Streamlit uploaded file object or PIL Image

        Returns:
            PIL Image or None if failed
        """
        try:
            # Handle different input types
            if hasattr(image_file, "read"):
                # Streamlit uploaded file
                image_bytes = image_file.read()
                image = Image.open(io.BytesIO(image_bytes))
            elif isinstance(image_file, Image.Image):
                # PIL Image
                image = image_file
            else:
                # Try to open as file path
                image = Image.open(image_file)

            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Check image dimensions
            width, height = image.size
            if width > self.max_image_dimension or height > self.max_image_dimension:
                st.warning(f"Large image ({width}x{height}). Consider resizing for better performance.")

            # Handle EXIF orientation
            image = self.correct_image_orientation(image)

            logger.info(f"Loaded image: {width}x{height}, mode: {image.mode}")
            return image

        except Exception as e:
            logger.warning(f"Failed to load image: {e}")
            st.toast("Failed to load image", icon="⚠️")
            return None

    def correct_image_orientation(self, image: Image.Image) -> Image.Image:
        """Correct image orientation based on EXIF data.

        Args:
            image: PIL Image

        Returns:
            Corrected PIL Image
        """
        try:
            # Get EXIF data
            exif = image._getexif()
            if exif is not None:
                # Find orientation tag
                for tag, value in exif.items():
                    if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == "Orientation":
                        # Apply rotation based on orientation
                        if value == 3:
                            image = image.rotate(180, expand=True)
                        elif value == 6:
                            image = image.rotate(270, expand=True)
                        elif value == 8:
                            image = image.rotate(90, expand=True)
                        break
        except Exception as e:
            logger.debug(f"Could not correct orientation: {e}")

        return image

    def preprocess_image(self, image: Image.Image, target_size: tuple[int, int] | None = None) -> Image.Image:
        """Preprocess image for model input.

        Args:
            image: PIL Image to preprocess
            target_size: Target size tuple (width, height)

        Returns:
            Preprocessed PIL Image
        """
        try:
            if target_size is None:
                target_size = self.target_size

            # Resize image while maintaining aspect ratio
            image_resized = image.copy()
            image_resized.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Create new image with target size and center the resized image
            new_image = Image.new("RGB", target_size, (255, 255, 255))

            # Calculate position to center the image
            x = (target_size[0] - image_resized.width) // 2
            y = (target_size[1] - image_resized.height) // 2

            new_image.paste(image_resized, (x, y))

            return new_image

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image

    def create_thumbnail(self, image: Image.Image, size: tuple[int, int] = (150, 150)) -> Image.Image:
        """Create thumbnail of image.

        Args:
            image: PIL Image
            size: Thumbnail size

        Returns:
            Thumbnail PIL Image
        """
        try:
            thumbnail = image.copy()
            thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
            return thumbnail
        except Exception as e:
            logger.warning(f"Thumbnail creation failed: {e}")
            return image

    def render_image_preview(self, image: Image.Image, caption: str = "", expand: bool = False) -> None:
        """Render image preview with zoom capabilities.

        Args:
            image: PIL Image to display
            caption: Image caption
            expand: Whether to show expanded view controls
        """
        try:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.image(image, caption=caption, use_container_width=True)

            with col2:
                st.metric("Size", f"{image.width}x{image.height}")
                st.metric("Mode", image.mode)

                if expand:
                    # Zoom controls
                    st.subheader("🔍 Zoom Controls")
                    zoom_level = st.slider("Zoom", 0.1, 3.0, 1.0, 0.1)

                    if zoom_level != 1.0:
                        # Apply zoom
                        zoomed_size = (int(image.width * zoom_level), int(image.height * zoom_level))
                        zoomed_image = image.resize(zoomed_size, Image.Resampling.LANCZOS)
                        st.image(zoomed_image, caption=f"Zoomed {zoom_level}x", use_container_width=True)

        except Exception as e:
            logger.warning(f"Image preview failed: {e}")
            st.error("Failed to display image preview")

    def render_upload_interface(self) -> list[Image.Image]:
        """Render multi-file image upload interface.

        Returns:
            List of uploaded PIL Images
        """
        st.subheader("📁 Image Upload")

        uploaded_files = st.file_uploader(
            "Choose image files",
            type=self.supported_formats,
            accept_multiple_files=True,
            help=f"Supported formats: {', '.join(self.supported_formats)}. Max size: 200MB per image",
        )

        images = []

        if uploaded_files:
            with st.status(f"📸 Processing {len(uploaded_files)} image(s)...", expanded=True) as status:
                valid_images = 0

                for i, uploaded_file in enumerate(uploaded_files):
                    st.write(f"Processing {uploaded_file.name}...")

                    # Validate file
                    is_valid, error_msg = self.validate_image_file(uploaded_file)
                    if not is_valid:
                        st.error(f"❌ {uploaded_file.name}: {error_msg}")
                        continue

                    # Load image
                    image = self.load_and_validate_image(uploaded_file)
                    if image:
                        images.append(image)
                        valid_images += 1
                        st.write(f"✅ {uploaded_file.name} loaded successfully")

                if valid_images > 0:
                    status.update(label=f"✅ Processed {valid_images} image(s) successfully!", state="complete")
                    st.session_state.uploaded_images = images
                else:
                    status.update(label="❌ No valid images processed", state="error")

        return images

    def render_camera_interface(self) -> Image.Image | None:
        """Render camera capture interface.

        Returns:
            Captured PIL Image or None
        """
        st.subheader("📷 Camera Capture")

        # Camera input
        camera_image = st.camera_input("Take a photo", help="Use your device's camera to capture a plant image")

        if camera_image:
            # Load and validate captured image
            image = self.load_and_validate_image(camera_image)
            if image:
                st.success("📸 Photo captured successfully!")
                st.session_state.captured_image = image

                # Show preview
                self.render_image_preview(image, "Captured Image", expand=True)

                return image

        return st.session_state.captured_image

    def render_batch_processing_interface(self, images: list[Image.Image]) -> list[Image.Image]:
        """Render batch processing interface for multiple images.

        Args:
            images: List of PIL Images to process

        Returns:
            List of processed PIL Images
        """
        if not images:
            return []

        st.subheader(f"⚙️ Batch Processing ({len(images)} images)")

        # Processing options
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            resize_images = st.checkbox("Resize for analysis", value=True, help="Resize images to optimal size for model")

        with col2:
            # Provide a checkbox without assigning it to a local variable to avoid unused-variable lint
            st.checkbox("Create thumbnails", value=True, help="Create thumbnail previews")

        with col3:
            if st.button("🚀 Process All", type="primary"):
                processed_images = []

                with st.progress(0) as progress_bar:
                    for i, image in enumerate(images):
                        try:
                            processed_image = image

                            if resize_images:
                                processed_image = self.preprocess_image(processed_image)

                            processed_images.append(processed_image)
                            progress_bar.progress((i + 1) / len(images))

                        except Exception as e:
                            logger.warning(f"Failed to process image {i}: {e}")
                            processed_images.append(image)

                st.session_state.processed_images = processed_images
                st.success(f"✅ Processed {len(processed_images)} images")
                return processed_images

        return st.session_state.processed_images or images

    def render_image_grid(self, images: list[Image.Image], cols: int = 3) -> None:
        """Render grid of images with thumbnails.

        Args:
            images: List of PIL Images
            cols: Number of columns in grid
        """
        if not images:
            st.info("No images to display")
            return

        st.subheader(f"🖼️ Image Gallery ({len(images)} images)")

        # Create grid
        for i in range(0, len(images), cols):
            row_images = images[i : i + cols]
            columns = st.columns(cols)

            for j, image in enumerate(row_images):
                with columns[j]:
                    # Create thumbnail
                    thumbnail = self.create_thumbnail(image)

                    # Display thumbnail
                    st.image(thumbnail, caption=f"Image {i + j + 1}", use_container_width=True)

                    # Image info
                    st.caption(f"{image.width}x{image.height}")

    def render_processing_controls(self, images: list[Image.Image]) -> None:
        """Render image processing controls.

        Args:
            images: List of current images
        """
        if not images:
            return

        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            st.metric("Total Images", len(images))

        with col2:
            total_pixels = sum(img.width * img.height for img in images)
            st.metric("Total Pixels", f"{total_pixels:,}")

        with col3:
            avg_size = sum(img.width * img.height for img in images) / len(images) if images else 0
            st.metric("Avg Size", f"{avg_size:,.0f}px")

        with col4:
            if st.button("🧹 Clear All"):
                st.session_state.uploaded_images = []
                st.session_state.captured_image = None
                st.session_state.processed_images = []
                st.rerun()

    def render_complete_interface(self) -> list[Image.Image]:
        """Render the complete image interface.

        Returns:
            List of processed PIL Images
        """
        st.header("📸 Image Input & Camera")

        # Interface tabs
        tab1, tab2 = st.tabs(["📁 Upload Images", "📷 Camera Capture"])

        all_images = []

        with tab1:
            uploaded_images = self.render_upload_interface()
            all_images.extend(uploaded_images)

        with tab2:
            captured_image = self.render_camera_interface()
            if captured_image:
                all_images.append(captured_image)

        # Combine all images
        if st.session_state.uploaded_images:
            all_images.extend(st.session_state.uploaded_images)
        if st.session_state.captured_image:
            all_images.append(st.session_state.captured_image)

        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in all_images:
            img_id = id(img)
            if img_id not in seen:
                seen.add(img_id)
                unique_images.append(img)

        # Batch processing and display
        if unique_images:
            st.markdown("---")
            processed_images = self.render_batch_processing_interface(unique_images)

            # Image grid
            st.markdown("---")
            self.render_image_grid(processed_images or unique_images)

            # Processing controls
            st.markdown("---")
            self.render_processing_controls(unique_images)

            return processed_images or unique_images

        return []


def create_image_interface() -> ImageInterface:
    """Create and return an ImageInterface instance.

    Returns:
        ImageInterface instance
    """
    return ImageInterface()


# Example usage and testing
if __name__ == "__main__":
    # Test the image interface
    st.title("📸 PlantGuard Image Interface Test")

    # Create image interface
    image_interface = create_image_interface()

    # Render interface
    images = image_interface.render_complete_interface()

    # Display results
    if images:
        st.success(f"Ready for analysis: {len(images)} images loaded")
    else:
        st.info("Upload or capture images to get started")
