"""Gesture Handler Component for PlantGuard Mobile Interface.

Provides touch gesture support for mobile devices including swipe gestures,
pinch-to-zoom, and touch interactions for enhanced mobile user experience.
"""

import logging
from collections.abc import Callable

import streamlit as st

logger = logging.getLogger(__name__)


class GestureHandler:
    """Handler for mobile touch gestures and interactions."""

    def __init__(self):
        self.gesture_events = {
            "swipe_left": [],
            "swipe_right": [],
            "swipe_up": [],
            "swipe_down": [],
            "pinch_zoom": [],
            "tap": [],
            "long_press": [],
        }
        self._initialize_gesture_state()

    def _initialize_gesture_state(self):
        """Initialize gesture state management."""
        if "gesture_state" not in st.session_state:
            st.session_state.gesture_state = {
                "last_gesture": None,
                "gesture_data": {},
                "touch_start": None,
                "touch_end": None,
                "gesture_enabled": True,
            }

    def enable_swipe_navigation(self, on_swipe_left: Callable | None = None, on_swipe_right: Callable | None = None):
        """Enable swipe gestures for navigation.

        Args:
            on_swipe_left: Callback function for left swipe
            on_swipe_right: Callback function for right swipe
        """
        if on_swipe_left is not None:
            self.gesture_events["swipe_left"].append(on_swipe_left)
        if on_swipe_right is not None:
            self.gesture_events["swipe_right"].append(on_swipe_right)

        # Inject touch event handlers via JavaScript
        swipe_js = """
        <script>
        let touchStartX = 0;
        let touchStartY = 0;
        let touchEndX = 0;
        let touchEndY = 0;

        document.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }, false);

        document.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            handleSwipe();
        }, false);

        function handleSwipe() {
            const threshold = 50; // Minimum distance for swipe
            const restraint = 100; // Maximum distance in perpendicular direction
            const allowedTime = 300; // Maximum time for swipe

            let distX = touchEndX - touchStartX;
            let distY = touchEndY - touchStartY;

            if (Math.abs(distX) >= threshold && Math.abs(distY) <= restraint) {
                if (distX > 0) {
                    // Swipe right
                    window.parent.postMessage({type: 'gesture', gesture: 'swipe_right'}, '*');
                } else {
                    // Swipe left
                    window.parent.postMessage({type: 'gesture', gesture: 'swipe_left'}, '*');
                }
            }

            if (Math.abs(distY) >= threshold && Math.abs(distX) <= restraint) {
                if (distY > 0) {
                    // Swipe down
                    window.parent.postMessage({type: 'gesture', gesture: 'swipe_down'}, '*');
                } else {
                    // Swipe up
                    window.parent.postMessage({type: 'gesture', gesture: 'swipe_up'}, '*');
                }
            }
        }
        </script>
        """

        st.markdown(swipe_js, unsafe_allow_html=True)

    def enable_pinch_zoom(self, target_element: str = "image", on_zoom_in: Callable | None = None, on_zoom_out: Callable | None = None):
        """Enable pinch-to-zoom gesture for images.

        Args:
            target_element: CSS selector for target elements
            on_zoom_in: Callback for zoom in gesture
            on_zoom_out: Callback for zoom out gesture
        """
        if on_zoom_in is not None:
            self.gesture_events["pinch_zoom"].append(on_zoom_in)
        if on_zoom_out is not None:
            self.gesture_events["pinch_zoom"].append(on_zoom_out)

        # Inject pinch-to-zoom handlers
        pinch_js = f"""
        <script>
        let initialDistance = 0;
        let scale = 1;

        document.addEventListener('touchstart', function(e) {{
            if (e.touches.length == 2) {{
                initialDistance = getDistance(e.touches[0], e.touches[1]);
            }}
        }}, false);

        document.addEventListener('touchmove', function(e) {{
            if (e.touches.length == 2) {{
                e.preventDefault();
                let currentDistance = getDistance(e.touches[0], e.touches[1]);
                let delta = currentDistance - initialDistance;

                if (Math.abs(delta) > 10) {{
                    if (delta > 0) {{
                        // Pinch out (zoom in)
                        window.parent.postMessage({{type: 'gesture', gesture: 'zoom_in', target: '{target_element}'}}, '*');
                    }} else {{
                        // Pinch in (zoom out)
                        window.parent.postMessage({{type: 'gesture', gesture: 'zoom_out', target: '{target_element}'}}, '*');
                    }}
                    initialDistance = currentDistance;
                }}
            }}
        }}, false);

        function getDistance(touch1, touch2) {{
            let dx = touch2.clientX - touch1.clientX;
            let dy = touch2.clientY - touch1.clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }}
        </script>
        """

        st.markdown(pinch_js, unsafe_allow_html=True)

    def enable_touch_feedback(self):
        """Enable visual feedback for touch interactions."""
        touch_feedback_css = """
        <style>
        /* Touch-friendly button styling */
        .stButton > button {
            min-height: 44px !important;
            transition: all 0.2s ease !important;
            touch-action: manipulation !important;
        }

        .stButton > button:active {
            transform: scale(0.95) !important;
            background-color: rgba(34, 197, 94, 0.1) !important;
        }

        /* Swipe indicator */
        .swipe-indicator {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(34, 197, 94, 0.9);
            color: white;
            padding: 12px 24px;
            border-radius: 24px;
            font-weight: bold;
            z-index: 9999;
            display: none;
            animation: swipeIndicator 0.5s ease;
        }

        @keyframes swipeIndicator {
            0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
            100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }

        /* Touch ripple effect */
        .touch-ripple {
            position: relative;
            overflow: hidden;
        }

        .touch-ripple::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(34, 197, 94, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.3s, height 0.3s;
        }

        .touch-ripple:active::before {
            width: 200px;
            height: 200px;
        }

        /* Image gesture container */
        .gesture-image-container {
            position: relative;
            overflow: hidden;
            touch-action: pan-x pan-y;
            user-select: none;
            -webkit-user-select: none;
        }

        .gesture-image {
            transition: transform 0.2s ease;
            max-width: 100%;
            height: auto;
        }

        /* Mobile-specific improvements */
        @media (max-width: 768px) {
            .stButton > button {
                min-height: 48px !important;
                font-size: 16px !important;
            }

            .stSelectbox > div > div {
                min-height: 44px !important;
            }
        }
        </style>
        """

        st.markdown(touch_feedback_css, unsafe_allow_html=True)

    def create_swipeable_image_viewer(self, images: list, current_index: int = 0) -> int:
        """Create a swipeable image viewer with gesture support.

        Args:
            images: List of images to display
            current_index: Index of currently displayed image

        Returns:
            New current index after swipe gestures
        """
        if not images:
            return current_index

        # Initialize swipe state
        if "swipe_image_index" not in st.session_state:
            st.session_state.swipe_image_index = current_index

        # Enable swipe navigation for images
        def next_image():
            if st.session_state.swipe_image_index < len(images) - 1:
                st.session_state.swipe_image_index += 1

        def prev_image():
            if st.session_state.swipe_image_index > 0:
                st.session_state.swipe_image_index -= 1

        self.enable_swipe_navigation(prev_image, next_image)

        # Render image viewer
        current_idx = st.session_state.swipe_image_index

        # Image container with gesture support
        image_html = f"""
        <div class="gesture-image-container" style="text-align: center; margin: 16px 0;">
            <div style="
                background: #F3F4F6;
                border-radius: 12px;
                padding: 16px;
                border: 2px solid #E5E7EB;
            ">
                <div style="margin-bottom: 12px;">
                    <span style="color: #6B7280; font-weight: 600;">
                        Swipe ← → to navigate • Image {current_idx + 1} of {len(images)}
                    </span>
                </div>
            </div>
        </div>
        """

        st.markdown(image_html, unsafe_allow_html=True)

        # Display current image
        if 0 <= current_idx < len(images):
            st.image(images[current_idx], use_column_width=True, caption=f"Image {current_idx + 1} of {len(images)}")

        # Navigation buttons as fallback
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if current_idx > 0:
                if st.button("← Previous", key="prev_image_btn"):
                    st.session_state.swipe_image_index -= 1
                    st.rerun()

        with col3:
            if current_idx < len(images) - 1:
                if st.button("Next →", key="next_image_btn"):
                    st.session_state.swipe_image_index += 1
                    st.rerun()

        return st.session_state.swipe_image_index

    def handle_gesture_event(self, gesture_type: str, data: dict | None = None):
        """Handle gesture events and trigger callbacks.

        Args:
            gesture_type: Type of gesture (swipe_left, swipe_right, etc.)
            data: Additional gesture data
        """
        if gesture_type in self.gesture_events:
            for callback in self.gesture_events[gesture_type]:
                try:
                    if data:
                        callback(data)
                    else:
                        callback()
                except Exception as e:
                    logger.warning(f"Gesture callback failed: {e}")

        # Update gesture state
        st.session_state.gesture_state["last_gesture"] = gesture_type
        st.session_state.gesture_state["gesture_data"] = data or {}

    def render_gesture_debug_info(self):
        """Render debug information for gesture testing."""
        if st.checkbox("Show Gesture Debug Info", value=False):
            st.markdown("### 🤏 Gesture Debug Information")

            gesture_state = st.session_state.get("gesture_state", {})

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Last Gesture", gesture_state.get("last_gesture", "None"))
                st.metric("Gesture Enabled", gesture_state.get("gesture_enabled", False))

            with col2:
                if gesture_state.get("gesture_data"):
                    st.json(gesture_state["gesture_data"])
                else:
                    st.info("No gesture data")

            # Test buttons
            st.markdown("**Test Gestures:**")

            test_col1, test_col2, test_col3 = st.columns(3)

            with test_col1:
                if st.button("Test Swipe Left"):
                    self.handle_gesture_event("swipe_left")

            with test_col2:
                if st.button("Test Swipe Right"):
                    self.handle_gesture_event("swipe_right")

            with test_col3:
                if st.button("Test Pinch Zoom"):
                    self.handle_gesture_event("pinch_zoom", {"direction": "in"})

    def create_touch_friendly_interface(self):
        """Create touch-friendly interface improvements."""
        # Add touch-friendly CSS
        self.enable_touch_feedback()

        # Set minimum touch target sizes
        touch_css = """
        <style>
        /* Ensure all interactive elements meet 44px minimum */
        .stButton > button,
        .stSelectbox > div,
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            min-height: 44px !important;
        }

        /* Increase spacing between elements on mobile */
        @media (max-width: 768px) {
            .stButton {
                margin-bottom: 12px !important;
            }

            .stColumns > div {
                padding: 8px !important;
            }
        }

        /* Touch scroll improvements */
        .main .block-container {
            -webkit-overflow-scrolling: touch;
        }
        </style>
        """

        st.markdown(touch_css, unsafe_allow_html=True)


def create_gesture_handler() -> GestureHandler:
    """Create and return a GestureHandler instance.

    Returns:
        GestureHandler instance
    """
    return GestureHandler()


# Usage example for integration
if __name__ == "__main__":
    st.title("🤏 Gesture Handler Test")

    # Create gesture handler
    gesture_handler = create_gesture_handler()

    # Enable touch feedback
    gesture_handler.create_touch_friendly_interface()

    # Test swipeable image viewer
    test_images = [
        "https://via.placeholder.com/400x300/22C55E/FFFFFF?text=Image+1",
        "https://via.placeholder.com/400x300/10B981/FFFFFF?text=Image+2",
        "https://via.placeholder.com/400x300/0EA5E9/FFFFFF?text=Image+3",
    ]

    st.markdown("### Swipeable Image Viewer")
    current_idx = gesture_handler.create_swipeable_image_viewer(test_images)

    # Show gesture debug info
    gesture_handler.render_gesture_debug_info()
