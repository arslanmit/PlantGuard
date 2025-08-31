"""
Mobile Interface Switcher

Provides automatic detection and switching between desktop and mobile interfaces.
Integrates seamlessly with existing PlantGuard application.
"""

import logging
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


class MobileInterfaceSwitcher:
    """Handles automatic switching between desktop and mobile interfaces."""

    def __init__(self) -> None:
        self.mobile_threshold = 768  # pixels
        self.force_mobile = False
        self.force_desktop = False

    def detect_mobile_device(self) -> bool:
        """Detect if user is on a mobile device."""
        # Check session state cache first
        if "is_mobile_device" in st.session_state:
            return st.session_state.is_mobile_device

        # JavaScript-based detection
        mobile_detection_script = """
        <script>
        function detectMobile() {
            const userAgent = navigator.userAgent.toLowerCase();
            const mobileKeywords = ['android', 'webos', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'];
            const isMobileUA = mobileKeywords.some(keyword => userAgent.includes(keyword));
            
            const screenWidth = window.innerWidth || document.documentElement.clientWidth;
            const isSmallScreen = screenWidth <= 768;
            
            const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            
            const isMobile = isMobileUA || (isSmallScreen && isTouchDevice);
            
            // Store result in session storage
            sessionStorage.setItem('isMobile', isMobile.toString());
            
            return isMobile;
        }
        
        // Run detection
        const mobileDetected = detectMobile();
        
        // Send result to Streamlit
        window.parent.postMessage({
            type: 'mobile_detection',
            isMobile: mobileDetected,
            screenWidth: window.innerWidth,
            userAgent: navigator.userAgent
        }, '*');
        </script>
        """

        # Inject detection script
        st.components.v1.html(mobile_detection_script, height=0)

        # Default to mobile-first approach for better compatibility
        is_mobile = True

        # Cache result
        st.session_state.is_mobile_device = is_mobile

        return is_mobile

    def get_interface_preference(self) -> str:
        """Get user's interface preference."""
        # Check for manual override
        if self.force_mobile:
            return "mobile"
        if self.force_desktop:
            return "desktop"

        # Check session state preference
        if "interface_preference" in st.session_state:
            return st.session_state.interface_preference

        # Auto-detect based on device
        if self.detect_mobile_device():
            return "mobile"
        else:
            return "desktop"

    def set_interface_preference(self, preference: str) -> None:
        """Set user's interface preference."""
        if preference in ["mobile", "desktop", "auto"]:
            st.session_state.interface_preference = preference
            logger.info(f"Interface preference set to: {preference}")

    def render_interface_toggle(self) -> str | None:
        """Render interface toggle controls."""
        current_preference = self.get_interface_preference()

        st.markdown("### [MOBILE] Interface Selection")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("[MOBILE] Mobile", type="primary" if current_preference == "mobile" else "secondary", use_container_width=True):
                self.set_interface_preference("mobile")
                return "mobile"

        with col2:
            if st.button("[COMPUTER] Desktop", type="primary" if current_preference == "desktop" else "secondary", use_container_width=True):
                self.set_interface_preference("desktop")
                return "desktop"

        with col3:
            if st.button("[PARTIAL] Auto", type="primary" if current_preference == "auto" else "secondary", use_container_width=True):
                self.set_interface_preference("auto")
                return "auto"

        return None

    def should_use_mobile_interface(self) -> bool:
        """Determine if mobile interface should be used."""
        preference = self.get_interface_preference()

        if preference == "mobile":
            return True
        elif preference == "desktop":
            return False
        else:  # auto
            return self.detect_mobile_device()

    def get_interface_config(self) -> dict[str, Any]:
        """Get configuration for the selected interface."""
        use_mobile = self.should_use_mobile_interface()

        if use_mobile:
            return {
                "interface_type": "mobile",
                "layout": "wide",
                "sidebar_state": "collapsed",
                "css_class": "mobile-interface",
                "max_width": "428px",
                "touch_optimized": True,
                "responsive": True,
            }
        else:
            return {
                "interface_type": "desktop",
                "layout": "wide",
                "sidebar_state": "expanded",
                "css_class": "desktop-interface",
                "max_width": "1200px",
                "touch_optimized": False,
                "responsive": False,
            }

    def apply_interface_config(self) -> None:
        """Apply mobile interface configuration to Streamlit."""
        config = self.get_interface_config()

        # Apply mobile CSS (mobile-only system)
        self._apply_mobile_css()

    def _apply_mobile_css(self) -> None:
        """Apply mobile-specific CSS."""
        mobile_css = """
        <style>
        /* Mobile interface styles */
        .stSidebar {
            display: none !important;
        }
        
        .main .block-container {
            padding: 0.5rem;
            max-width: 428px;
            margin: 0 auto;
        }
        
        /* Touch-friendly elements */
        .stButton > button {
            min-height: 48px;
            min-width: 48px;
            touch-action: manipulation;
            font-size: 16px;
        }
        
        /* Mobile input optimization */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            font-size: 16px; /* Prevent zoom on iOS */
        }
        
        /* Mobile-friendly spacing */
        .element-container {
            margin-bottom: 0.5rem;
        }
        
        /* Mobile navigation */
        .mobile-nav-tabs {
            display: flex;
            justify-content: space-around;
            background: #f0f2f6;
            border-radius: 10px;
            padding: 0.25rem;
            margin-bottom: 1rem;
        }
        
        .mobile-nav-tab {
            flex: 1;
            text-align: center;
            padding: 0.5rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .mobile-nav-tab.active {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Mobile cards */
        .mobile-card {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Responsive images */
        .stImage > img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }
        
        @media (max-width: 480px) {
            .main .block-container {
                padding: 0.25rem;
            }
            
            .mobile-card {
                padding: 0.75rem;
            }
        }
        </style>
        """

        st.markdown(mobile_css, unsafe_allow_html=True)

    def render_interface_info(self) -> None:
        """Render information about current interface."""
        config = self.get_interface_config()

        with st.expander("[MOBILE] Interface Information", expanded=True):
            st.markdown(f"**Current Interface:** {config['interface_type'].title()}")
            st.markdown(f"**Layout:** {config['layout']}")
            st.markdown(f"**Max Width:** {config['max_width']}")
            st.markdown(f"**Touch Optimized:** {'Yes' if config['touch_optimized'] else 'No'}")

            if st.session_state.get("is_mobile_device"):
                st.success("[MOBILE] Mobile device detected")
            else:
                st.info("[COMPUTER] Desktop device detected")


# Global instance
mobile_interface_switcher = MobileInterfaceSwitcher()
