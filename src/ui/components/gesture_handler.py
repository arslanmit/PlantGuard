from typing import Any

"""Enhanced Gesture Handler Component for PlantGuard Mobile Interface.


Provides comprehensive touch gesture support for mobile devices including:
- Advanced swipe gestures with velocity detection
- Pinch-to-zoom with momentum
- Touch feedback animations and haptic responses
- Proper touch-action CSS optimization
- Multi-touch gesture recognition
- Touch target size optimization
"""

import logging
from collections.abc import Callable

import streamlit as st

logger = logging.getLogger(__name__)


class EnhancedGestureHandler:
    """Enhanced handler for mobile touch gestures and interactions with advanced features."""

    def __init__(self) -> None:
        self.gesture_events = {
            "swipe_left": [],
            "swipe_right": [],
            "swipe_up": [],
            "swipe_down": [],
            "pinch_zoom_in": [],
            "pinch_zoom_out": [],
            "tap": [],
            "double_tap": [],
            "long_press": [],
            "pan": [],
            "rotate": [],
        }

        # Enhanced gesture configuration
        self.config = {
            "swipe_threshold": 50,  # Minimum distance for swipe
            "swipe_restraint": 100,  # Maximum perpendicular distance
            "swipe_velocity_threshold": 0.3,  # Minimum velocity for swipe
            "tap_threshold": 10,  # Maximum movement for tap
            "long_press_duration": 500,  # Long press duration in ms
            "double_tap_delay": 300,  # Double tap max delay
            "pinch_threshold": 10,  # Minimum distance change for pinch
            "touch_target_min": 44,  # Minimum touch target size (px)
            "haptic_enabled": True,  # Enable haptic feedback
            "animation_enabled": True,  # Enable touch animations
        }

        self._initialize_gesture_state()
        self._setup_touch_optimization()

    def _initialize_gesture_state(self) -> Any:
        """Initialize enhanced gesture state management."""
        if "enhanced_gesture_state" not in st.session_state:
            st.session_state.enhanced_gesture_state = {
                "last_gesture": None,
                "gesture_data": {},
                "touch_start": None,
                "touch_end": None,
                "gesture_enabled": True,
                "touch_points": [],
                "gesture_history": [],
                "velocity": {"x": 0, "y": 0},
                "scale": 1.0,
                "rotation": 0,
                "last_tap_time": 0,
                "tap_count": 0,
                "active_touches": 0,
                "gesture_start_time": 0,
            }

    def _setup_touch_optimization(self) -> Any:
        """Setup touch optimization CSS and JavaScript."""
        self._inject_touch_optimization_css()
        self._inject_enhanced_gesture_js()

    def _inject_touch_optimization_css(self) -> Any:
        """Inject comprehensive touch optimization CSS."""
        touch_css = """
        <style>
        /* Enhanced Touch Optimization CSS */
        :root {
            --touch-target-min: 44px;
            --touch-target-optimal: 48px;
            --touch-spacing: 8px;
            --touch-feedback-duration: 0.15s;
            --haptic-feedback-color: rgba(34, 197, 94, 0.2);
        }
        
        /* Touch Action Optimization */
        .touch-optimized {
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
        
        .touch-pan-x { touch-action: pan-x; }
        .touch-pan-y { touch-action: pan-y; }
        .touch-pan-xy { touch-action: pan-x pan-y; }
        .touch-pinch-zoom { touch-action: pinch-zoom; }
        .touch-none { touch-action: none; }
        
        /* Enhanced Touch Targets */
        .touch-target {
            min-height: var(--touch-target-min);
            min-width: var(--touch-target-min);
            padding: 12px;
            margin: var(--touch-spacing);
            position: relative;
            overflow: hidden;
            cursor: pointer;
            transition: all var(--touch-feedback-duration) ease;
        }
        
        .touch-target-optimal {
            min-height: var(--touch-target-optimal);
            min-width: var(--touch-target-optimal);
        }
        
        /* Touch Feedback Animations */
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
            background: var(--haptic-feedback-color);
            transform: translate(-50%, -50%);
            transition: width 0.3s ease, height 0.3s ease, opacity 0.3s ease;
            opacity: 0;
            pointer-events: none;
        }
        
        .touch-ripple.active::before {
            width: 200px;
            height: 200px;
            opacity: 1;
        }
        
        .touch-ripple.fade::before {
            opacity: 0;
        }
        
        /* Touch Press States */
        .touch-press {
            transform: scale(0.98);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .touch-hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Gesture Feedback Indicators */
        .gesture-indicator {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(34, 197, 94, 0.9);
            color: white;
            padding: 12px 24px;
            border-radius: 24px;
            font-weight: 600;
            font-size: 14px;
            z-index: 9999;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
        }
        
        .gesture-indicator.show {
            opacity: 1;
            animation: gestureIndicator 0.8s ease;
        }
        
        @keyframes gestureIndicator {
            0% { 
                opacity: 0; 
                transform: translate(-50%, -50%) scale(0.8); 
            }
            30% { 
                opacity: 1; 
                transform: translate(-50%, -50%) scale(1.1); 
            }
            100% { 
                opacity: 1; 
                transform: translate(-50%, -50%) scale(1); 
            }
        }
        
        /* Swipe Direction Indicators */
        .swipe-left-indicator::after { content: '← Swipe Left'; }
        .swipe-right-indicator::after { content: 'Swipe Right →'; }
        .swipe-up-indicator::after { content: '↑ Swipe Up'; }
        .swipe-down-indicator::after { content: '↓ Swipe Down'; }
        .pinch-in-indicator::after { content: '[SMALL] Pinch In'; }
        .pinch-out-indicator::after { content: '[HANDS] Pinch Out'; }
        .tap-indicator::after { content: '[POINTER] Tap'; }
        .double-tap-indicator::after { content: '[POINTER][POINTER] Double Tap'; }
        .long-press-indicator::after { content: '[POINTER]⏱️ Long Press'; }
        
        /* Touch-Optimized Buttons */
        .mobile-button-touch {
            min-height: var(--touch-target-optimal);
            min-width: var(--touch-target-optimal);
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            cursor: pointer;
            transition: all var(--touch-feedback-duration) ease;
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
            position: relative;
            overflow: hidden;
        }
        
        .mobile-button-touch:active {
            transform: scale(0.98);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        /* Gesture-Enabled Containers */
        .gesture-container {
            position: relative;
            overflow: hidden;
            touch-action: none;
            user-select: none;
            -webkit-user-select: none;
        }
        
        .swipeable-container {
            touch-action: pan-x;
            overflow-x: hidden;
        }
        
        .pinchable-container {
            touch-action: pinch-zoom;
            overflow: hidden;
        }
        
        .pannable-container {
            touch-action: pan-x pan-y;
            overflow: hidden;
        }
        
        /* Accessibility Enhancements */
        @media (prefers-reduced-motion: reduce) {
            .touch-ripple::before,
            .gesture-indicator,
            .mobile-button-touch {
                animation: none !important;
                transition: none !important;
            }
        }
        
        /* High Contrast Mode */
        @media (prefers-contrast: high) {
            .touch-target {
                border: 2px solid currentColor;
            }
            
            .gesture-indicator {
                background: #000;
                color: #fff;
                border: 2px solid #fff;
            }
        }
        
        /* Touch Target Size Adjustments for Small Screens */
        @media (max-width: 360px) {
            :root {
                --touch-target-min: 40px;
                --touch-target-optimal: 44px;
                --touch-spacing: 6px;
            }
        }
        
        /* Large Touch Targets for Accessibility */
        @media (prefers-reduced-motion: reduce) {
            :root {
                --touch-target-min: 48px;
                --touch-target-optimal: 56px;
            }
        }
        </style>
        """
        st.markdown(touch_css, unsafe_allow_html=True)

    def _inject_enhanced_gesture_js(self) -> Any:
        """Inject enhanced gesture recognition JavaScript."""
        gesture_js = """
        <script>
        class EnhancedGestureRecognizer {
            constructor() {
                this.touches = new Map();
                this.gestureState = {
                    isActive: false,
                    startTime: 0,
                    lastTapTime: 0,
                    tapCount: 0,
                    initialDistance: 0,
                    initialAngle: 0,
                    scale: 1,
                    rotation: 0
                };
                
                this.config = {
                    swipeThreshold: 50,
                    swipeRestraint: 100,
                    velocityThreshold: 0.3,
                    tapThreshold: 10,
                    longPressDelay: 500,
                    doubleTapDelay: 300,
                    pinchThreshold: 10
                };
                
                this.setupEventListeners();
            }
            
            setupEventListeners() {
                document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
                document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
                document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
                document.addEventListener('touchcancel', this.handleTouchCancel.bind(this), { passive: false });
            }
            
            handleTouchStart(e) {
                const now = Date.now();
                this.gestureState.startTime = now;
                this.gestureState.isActive = true;
                
                // Store touch points
                for (let touch of e.changedTouches) {
                    this.touches.set(touch.identifier, {
                        startX: touch.clientX,
                        startY: touch.clientY,
                        currentX: touch.clientX,
                        currentY: touch.clientY,
                        startTime: now
                    });
                }
                
                // Handle multi-touch gestures
                if (e.touches.length === 2) {
                    const touch1 = e.touches[0];
                    const touch2 = e.touches[1];
                    this.gestureState.initialDistance = this.getDistance(touch1, touch2);
                    this.gestureState.initialAngle = this.getAngle(touch1, touch2);
                }
                
                // Add visual feedback
                this.addTouchFeedback(e.touches[0]);
                
                // Setup long press detection
                if (e.touches.length === 1) {
                    setTimeout(() => {
                        if (this.gestureState.isActive && this.touches.size === 1) {
                            this.triggerGesture('long_press', {
                                x: e.touches[0].clientX,
                                y: e.touches[0].clientY
                            });
                        }
                    }, this.config.longPressDelay);
                }
            }
            
            handleTouchMove(e) {
                e.preventDefault(); // Prevent scrolling during gestures
                
                // Update touch positions
                for (let touch of e.changedTouches) {
                    if (this.touches.has(touch.identifier)) {
                        const touchData = this.touches.get(touch.identifier);
                        touchData.currentX = touch.clientX;
                        touchData.currentY = touch.clientY;
                    }
                }
                
                // Handle multi-touch gestures
                if (e.touches.length === 2) {
                    this.handlePinchGesture(e.touches[0], e.touches[1]);
                }
                
                // Handle pan gesture
                if (e.touches.length === 1) {
                    this.handlePanGesture(e.touches[0]);
                }
            }
            
            handleTouchEnd(e) {
                const now = Date.now();
                const duration = now - this.gestureState.startTime;
                
                // Process ended touches
                for (let touch of e.changedTouches) {
                    if (this.touches.has(touch.identifier)) {
                        const touchData = this.touches.get(touch.identifier);
                        
                        // Calculate gesture metrics
                        const deltaX = touch.clientX - touchData.startX;
                        const deltaY = touch.clientY - touchData.startY;
                        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                        const velocity = distance / duration;
                        
                        // Determine gesture type
                        if (distance < this.config.tapThreshold && duration < this.config.longPressDelay) {
                            this.handleTapGesture(touch, now);
                        } else if (velocity > this.config.velocityThreshold && distance > this.config.swipeThreshold) {
                            this.handleSwipeGesture(deltaX, deltaY, velocity);
                        }
                        
                        this.touches.delete(touch.identifier);
                    }
                }
                
                // Reset gesture state if no more touches
                if (e.touches.length === 0) {
                    this.gestureState.isActive = false;
                    this.removeTouchFeedback();
                }
            }
            
            handleTouchCancel(e) {
                this.touches.clear();
                this.gestureState.isActive = false;
                this.removeTouchFeedback();
            }
            
            handleTapGesture(touch, now) {
                const timeSinceLastTap = now - this.gestureState.lastTapTime;
                
                if (timeSinceLastTap < this.config.doubleTapDelay) {
                    this.gestureState.tapCount++;
                } else {
                    this.gestureState.tapCount = 1;
                }
                
                this.gestureState.lastTapTime = now;
                
                // Trigger appropriate tap event
                if (this.gestureState.tapCount === 1) {
                    setTimeout(() => {
                        if (this.gestureState.tapCount === 1) {
                            this.triggerGesture('tap', {
                                x: touch.clientX,
                                y: touch.clientY
                            });
                        }
                    }, this.config.doubleTapDelay);
                } else if (this.gestureState.tapCount === 2) {
                    this.triggerGesture('double_tap', {
                        x: touch.clientX,
                        y: touch.clientY
                    });
                    this.gestureState.tapCount = 0;
                }
            }
            
            handleSwipeGesture(deltaX, deltaY, velocity) {
                const absX = Math.abs(deltaX);
                const absY = Math.abs(deltaY);
                
                let direction;
                if (absX > absY && absX > this.config.swipeThreshold) {
                    direction = deltaX > 0 ? 'swipe_right' : 'swipe_left';
                } else if (absY > absX && absY > this.config.swipeThreshold) {
                    direction = deltaY > 0 ? 'swipe_down' : 'swipe_up';
                }
                
                if (direction) {
                    this.triggerGesture(direction, {
                        deltaX: deltaX,
                        deltaY: deltaY,
                        velocity: velocity,
                        distance: Math.sqrt(deltaX * deltaX + deltaY * deltaY)
                    });
                    
                    this.showGestureIndicator(direction);
                }
            }
            
            handlePinchGesture(touch1, touch2) {
                const currentDistance = this.getDistance(touch1, touch2);
                const currentAngle = this.getAngle(touch1, touch2);
                
                const scaleChange = currentDistance / this.gestureState.initialDistance;
                const rotationChange = currentAngle - this.gestureState.initialAngle;
                
                if (Math.abs(scaleChange - 1) > 0.1) {
                    const gestureType = scaleChange > 1 ? 'pinch_zoom_out' : 'pinch_zoom_in';
                    this.triggerGesture(gestureType, {
                        scale: scaleChange,
                        rotation: rotationChange,
                        centerX: (touch1.clientX + touch2.clientX) / 2,
                        centerY: (touch1.clientY + touch2.clientY) / 2
                    });
                }
            }
            
            handlePanGesture(touch) {
                const touchData = this.touches.get(touch.identifier);
                if (touchData) {
                    const deltaX = touch.clientX - touchData.startX;
                    const deltaY = touch.clientY - touchData.startY;
                    
                    this.triggerGesture('pan', {
                        deltaX: deltaX,
                        deltaY: deltaY,
                        currentX: touch.clientX,
                        currentY: touch.clientY
                    });
                }
            }
            
            getDistance(touch1, touch2) {
                const dx = touch2.clientX - touch1.clientX;
                const dy = touch2.clientY - touch1.clientY;
                return Math.sqrt(dx * dx + dy * dy);
            }
            
            getAngle(touch1, touch2) {
                const dx = touch2.clientX - touch1.clientX;
                const dy = touch2.clientY - touch1.clientY;
                return Math.atan2(dy, dx) * 180 / Math.PI;
            }
            
            addTouchFeedback(touch) {
                const target = document.elementFromPoint(touch.clientX, touch.clientY);
                if (target) {
                    target.classList.add('touch-ripple', 'active');
                    
                    // Add haptic feedback if supported
                    if (navigator.vibrate) {
                        navigator.vibrate(10);
                    }
                }
            }
            
            removeTouchFeedback() {
                const activeElements = document.querySelectorAll('.touch-ripple.active');
                activeElements.forEach(el => {
                    el.classList.remove('active');
                    el.classList.add('fade');
                    setTimeout(() => {
                        el.classList.remove('touch-ripple', 'fade');
                    }, 300);
                });
            }
            
            showGestureIndicator(gestureType) {
                const indicator = document.createElement('div');
                indicator.className = `gesture-indicator ${gestureType}-indicator show`;
                document.body.appendChild(indicator);
                
                setTimeout(() => {
                    indicator.classList.remove('show');
                    setTimeout(() => {
                        document.body.removeChild(indicator);
                    }, 200);
                }, 800);
            }
            
            triggerGesture(type, data) {
                // Send gesture event to Streamlit
                window.parent.postMessage({
                    type: 'enhanced_gesture',
                    gesture: type,
                    data: data,
                    timestamp: Date.now()
                }, '*');
                
                // Trigger haptic feedback
                if (navigator.vibrate) {
                    const vibrationPatterns = {
                        'tap': [10],
                        'double_tap': [10, 50, 10],
                        'long_press': [50],
                        'swipe_left': [20],
                        'swipe_right': [20],
                        'swipe_up': [20],
                        'swipe_down': [20],
                        'pinch_zoom_in': [30],
                        'pinch_zoom_out': [30]
                    };
                    
                    const pattern = vibrationPatterns[type] || [10];
                    navigator.vibrate(pattern);
                }
            }
        }
        
        // Initialize enhanced gesture recognizer
        if (!window.enhancedGestureRecognizer) {
            window.enhancedGestureRecognizer = new EnhancedGestureRecognizer();
        }
        </script>
        """
        st.markdown(gesture_js, unsafe_allow_html=True)

    def enable_enhanced_swipe_navigation(
        self,
        on_swipe_left: Callable | None = None,
        on_swipe_right: Callable | None = None,
        on_swipe_up: Callable | None = None,
        on_swipe_down: Callable | None = None,
        velocity_threshold: float = 0.3,
    ):
        """Enable enhanced swipe gestures for navigation with velocity detection.

        Args:
            on_swipe_left: Callback function for left swipe
            on_swipe_right: Callback function for right swipe
            on_swipe_up: Callback function for up swipe
            on_swipe_down: Callback function for down swipe
            velocity_threshold: Minimum velocity for swipe recognition
        """
        # Register callbacks
        if on_swipe_left is not None:
            self.gesture_events["swipe_left"].append(on_swipe_left)
        if on_swipe_right is not None:
            self.gesture_events["swipe_right"].append(on_swipe_right)
        if on_swipe_up is not None:
            self.gesture_events["swipe_up"].append(on_swipe_up)
        if on_swipe_down is not None:
            self.gesture_events["swipe_down"].append(on_swipe_down)

        # Update configuration
        self.config["swipe_velocity_threshold"] = velocity_threshold

        # Enable gesture recognition (already injected in __init__)
        logger.info("Enhanced swipe navigation enabled with velocity threshold: %f", velocity_threshold)

    def enable_pinch_zoom(self, target_element: str = "image", on_zoom_in: Callable | None = None, on_zoom_out: Callable | None = None) -> Any:
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

    def enable_touch_feedback(self) -> Any:
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
        def next_image() -> Any:
            if st.session_state.swipe_image_index < len(images) - 1:
                st.session_state.swipe_image_index += 1

        def prev_image() -> Any:
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
                        Swipe ← → to navigate - Image {current_idx + 1} of {len(images)}
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

    def handle_gesture_event(self, gesture_type: str, data: dict | None = None) -> Any:
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

    def render_gesture_debug_info(self) -> None:
        """Render debug information for gesture testing."""
        if st.checkbox("Show Gesture Debug Info", value=False):
            st.markdown("### [SMALL] Gesture Debug Information")

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

    def create_touch_friendly_interface(self) -> Any:
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
    st.title("[SMALL] Gesture Handler Test")

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
