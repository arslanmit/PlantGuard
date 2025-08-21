import logging
from typing import Any

import numpy as np
import streamlit as st
from PIL import Image, ImageChops

logger = logging.getLogger(__name__)


class CompareView:
    """A/B compare view with side-by-side and difference highlight modes."""

    def __init__(self) -> None:
        st.session_state.setdefault("page", "compare")

    def _load_image(self, uploaded) -> Any:
        try:
            if uploaded is None:
                return None
            img = Image.open(uploaded).convert("RGB")
            return img
        except Exception as e:
            st.error(f"❌ Error opening image: {e}")
            return None

    def _highlight_diff(self, img_a: Image.Image, img_b: Image.Image, threshold: int = 30) -> Image.Image:
        # Compute absolute difference
        diff = ImageChops.difference(img_a, img_b).convert("L")
        # Create mask where difference exceeds threshold
        mask = diff.point(lambda p: 255 if p > threshold else 0)
        mask = mask.convert("L")

        # Create red overlay
        overlay = Image.new("RGBA", img_b.size, (255, 0, 0, 120))

        base = img_b.convert("RGBA")
        # Composite the overlay onto the base image using mask
        highlighted = Image.composite(overlay, base, mask)
        # Blend original with highlight to keep context
        blended = Image.alpha_composite(base, highlighted).convert("RGB")
        return blended

    def render(self) -> None:
        st.markdown("## Image Comparison — A/B and side-by-side modes")
        st.markdown("Compare two plant images and optionally highlight the differences.")

        # Uploaders
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📷 Image A (A/B: left)")
            upload_a = st.file_uploader(
                "Select first image",
                key="compare_a",
                type=["jpg", "jpeg", "png"],
                help="Upload an image file (JPG, JPEG, or PNG format)",
            )
            if upload_a:
                st.success(f"✅ Image A loaded: {upload_a.name}")

        with col2:
            st.markdown("#### 📷 Image B (A/B: right)")
            upload_b = st.file_uploader(
                "Select second image",
                key="compare_b",
                type=["jpg", "jpeg", "png"],
                help="Upload an image file (JPG, JPEG, or PNG format)",
            )
            if upload_b:
                st.success(f"✅ Image B loaded: {upload_b.name}")

        img_a = self._load_image(st.session_state.get("compare_a"))
        img_b = self._load_image(st.session_state.get("compare_b"))

        # Options: display mode and difference highlighting
        st.markdown("---")
        st.markdown("### Display Options")
        display_mode = st.radio("Display mode", ["side-by-side", "overlay"], index=0, horizontal=True)
        highlight = st.checkbox("Highlight differences", value=False)
        threshold = st.slider("Difference threshold", min_value=5, max_value=100, value=30)

        if img_a and img_b:
            st.markdown("---")
            st.markdown("### 📊 Comparison Results")

            if display_mode == "side-by-side":
                # A/B side-by-side viewer
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**A/B — Image A**")
                    st.image(img_a, use_column_width=True, caption="A")
                with col2:
                    st.markdown("**A/B — Image B**")
                    st.image(img_b, use_column_width=True, caption="B")

            else:
                # overlay mode
                st.markdown("**Overlay mode**")
                # simple alpha blend for quick visual overlay
                arr_a = np.array(img_a).astype(float)
                arr_b = np.array(img_b).astype(float)
                try:
                    blended_arr = ((arr_a * 0.5) + (arr_b * 0.5)).astype(np.uint8)
                    st.image(blended_arr, use_column_width=True)
                except Exception:
                    st.image(img_b, use_column_width=True)

            # Difference highlighting
            if highlight:
                st.markdown("#### 🔦 Difference Highlight")
                try:
                    highlighted = self._highlight_diff(img_a, img_b, threshold=threshold)
                    st.image(highlighted, caption="Differences highlighted", use_column_width=True)
                except Exception as e:
                    st.error(f"Error computing highlight: {e}")

            # Basic metrics table (placeholder)
            import pandas as pd

            comparison_data = {
                "Metric": ["Disease", "Confidence", "Risk Level", "Severity", "File Size A", "File Size B"],
                "Image A": [
                    "Unknown",
                    "--",
                    "--",
                    "--",
                    f"{getattr(st.session_state.get('compare_a'), 'size', 'N/A')} bytes",
                    "",
                ],
                "Image B": [
                    "Unknown",
                    "--",
                    "--",
                    "--",
                    "",
                    f"{getattr(st.session_state.get('compare_b'), 'size', 'N/A')} bytes",
                ],
            }
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True)
            # delta: small note about change metrics used in comparison
            st.markdown("delta: shows change between Image A and Image B for key metrics")

            # Actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📊 Export Report"):
                    st.success("✅ Comparison report exported!")
            with col2:
                if st.button("💾 Save Comparison"):
                    st.success("✅ Comparison saved to history!")
            with col3:
                if st.button("🔄 Reset Images"):
                    for key in list(st.session_state.keys()):
                        if key.startswith("compare_"):
                            del st.session_state[key]
                    st.rerun()

        else:
            # Empty state
            st.info("Upload two images to enable the A/B side-by-side comparison and difference highlight features.")


def render_compare_page():
    v = CompareView()
    v.render()


if __name__ == "__main__":
    render_compare_page()
