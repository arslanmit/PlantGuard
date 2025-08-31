from typing import Any

"""
Mobile Layout Manager for PlantGuard UI.

This module provides the core mobile layout management system with responsive design,
touch optimization, and AI agent-friendly component architecture.
"""


import logging

import streamlit as st

logger = logging.getLogger(__name__)


class MobileLayoutManager:
    """Main layout manager for mobile interface with single-column responsive design."""

    def __init__(self, component_id: str = "mobile_layout", **kwargs) -> None:
        """Initialize mobile layout manager with configuration."""
        self.component_id = component_id
        self.config = {
            "layout_type": "single_column",
            "touch_target_size": 48,
            "spacing_unit": 16,
            "max_width": "100%",
            "grid_columns": 2,  # For 2x2 input grid
            "breakpoint_mobile": 768,
            "breakpoint_small": 480,
        }

        # Update config with any provided kwargs
        self.config.update(kwargs)

        # Initialize viewport and base styles
        self._setup_viewport()
        self._apply_base_mobile_styles()

        # Initialize performance optimizations
        self._initialize_performance_optimizations()

    def _setup_viewport(self) -> None:
        """Set up mobile-specific viewport meta tags."""
        viewport_meta = """
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        """
        st.markdown(viewport_meta, unsafe_allow_html=True)

    def _apply_base_mobile_styles(self) -> None:
        """Apply core mobile-first CSS styles with touch optimization."""
        mobile_css = self._get_mobile_base_css()
        st.markdown(mobile_css, unsafe_allow_html=True)

    def _get_mobile_base_css(self) -> str:
        """Generate mobile-optimized base CSS with CSS variables."""
        return f"""
        <style>
        /* CSS Variables for consistent mobile design */
        :root {{
            --primary-color: #16A34A;
            --primary-hover: #15803D;
            --accent-color: #22C55E;
            --background-color: #F8FAFC;
            --surface-color: #FFFFFF;
            --text-primary: #1F2937;
            --text-secondary: #6B7280;
            --border-color: #E5E7EB;
            --shadow-light: 0 1px 3px rgba(0,0,0,0.1);
            --shadow-medium: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-heavy: 0 10px 15px rgba(0,0,0,0.1);
            
            /* Mobile spacing system */
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: {self.config["spacing_unit"]}px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            
            /* Touch targets */
            --touch-target-min: {self.config["touch_target_size"]}px;
            --touch-target-comfortable: 56px;
            
            /* Typography */
            --font-size-xs: 12px;
            --font-size-sm: 14px;
            --font-size-base: 16px;
            --font-size-lg: 18px;
            --font-size-xl: 20px;
            --font-size-2xl: 24px;
            
            /* Border radius */
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
        }}
        
        /* Mobile-first responsive layout */
        .mobile-main-layout {{
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            max-width: 100vw;
            margin: 0;
            padding: 0;
            background-color: var(--background-color);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        /* Single column container */
        .mobile-container {{
            width: 100%;
            max-width: 100vw;
            margin: 0 auto;
            padding: var(--spacing-md);
            box-sizing: border-box;
        }}
        
        /* Mobile section styling */
        .mobile-section {{
            width: 100%;
            margin-bottom: var(--spacing-lg);
            padding: var(--spacing-md);
            background-color: var(--surface-color);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-light);
            box-sizing: border-box;
        }}
        
        /* 2x2 Input grid system */
        .mobile-input-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--spacing-md);
            width: 100%;
            margin-bottom: var(--spacing-lg);
            padding: var(--spacing-md);
        }}
        
        /* Touch-optimized typography */
        .mobile-title {{
            font-size: var(--font-size-2xl);
            font-weight: 700;
            color: var(--text-primary);
            margin: 0 0 var(--spacing-md) 0;
            line-height: 1.2;
        }}
        
        .mobile-subtitle {{
            font-size: var(--font-size-lg);
            font-weight: 600;
            color: var(--text-primary);
            margin: 0 0 var(--spacing-sm) 0;
            line-height: 1.3;
        }}
        
        .mobile-text {{
            font-size: var(--font-size-base);
            color: var(--text-secondary);
            line-height: 1.5;
            margin: 0 0 var(--spacing-sm) 0;
        }}
        
        /* Responsive breakpoints */
        @media (max-width: {self.config["breakpoint_mobile"]}px) {{
            .mobile-container {{
                padding: var(--spacing-sm);
            }}
            
            .mobile-section {{
                padding: var(--spacing-sm);
                margin-bottom: var(--spacing-md);
            }}
            
            .mobile-input-grid {{
                gap: var(--spacing-sm);
                padding: var(--spacing-sm);
            }}
        }}
        
        @media (max-width: {self.config["breakpoint_small"]}px) {{
            .mobile-container {{
                padding: var(--spacing-xs);
            }}
            
            .mobile-input-grid {{
                gap: var(--spacing-xs);
                padding: var(--spacing-xs);
            }}
            
            .mobile-title {{
                font-size: var(--font-size-xl);
            }}
        }}
        
        /* Touch optimization */
        * {{
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }}
        
        /* Allow text selection for content */
        .mobile-text, .mobile-content, p, span {{
            -webkit-user-select: text;
            -moz-user-select: text;
            -ms-user-select: text;
            user-select: text;
        }}
        
        /* Prevent horizontal scroll */
        html, body {{
            overflow-x: hidden;
            max-width: 100vw;
        }}
        
        /* Streamlit specific overrides */
        .main .block-container {{
            padding-top: var(--spacing-md);
            padding-bottom: var(--spacing-md);
            max-width: 100%;
        }}
        
        /* Hide Streamlit menu and footer on mobile */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        </style>
        """

    def render_mobile_layout(self) -> None:
        """Render the complete mobile layout structure."""
        # Apply layout container
        st.markdown('<div class="mobile-main-layout">', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="mobile-container">', unsafe_allow_html=True)

            # Header section
            self._render_mobile_header()

            # Main content area
            self._render_mobile_content_area()

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_mobile_header(self) -> None:
        """Render mobile-optimized header."""
        st.markdown(
            """
        <div class="mobile-section">
            <h1 class="mobile-title">[LEAF] PlantGuard</h1>
            <p class="mobile-text">AI-powered plant disease detection</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def _render_mobile_content_area(self) -> None:
        """Render main content area placeholder."""
        st.markdown(
            """
        <div class="mobile-section">
            <h2 class="mobile-subtitle">Mobile Interface Ready</h2>
            <p class="mobile-text">Mobile layout manager initialized with responsive design.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def create_input_grid(self) -> None:
        """Create 2x2 responsive grid for input components."""
        st.markdown('<div class="mobile-input-grid">', unsafe_allow_html=True)

        # Grid will be populated by input components
        # This creates the container structure

        st.markdown("</div>", unsafe_allow_html=True)

    def create_mobile_section(self, title: str | None = None, content_class: str = "mobile-content") -> None:
        """Create a mobile-optimized section container."""
        st.markdown('<div class="mobile-section">', unsafe_allow_html=True)

        if title:
            st.markdown(f'<h2 class="mobile-subtitle">{title}</h2>', unsafe_allow_html=True)

        st.markdown(f'<div class="{content_class}">', unsafe_allow_html=True)

        # Content will be added by calling components

        st.markdown("</div></div>", unsafe_allow_html=True)

    def get_responsive_columns(self, mobile_cols: int = 1) -> list[Any]:
        """Create mobile column layout."""
        # Mobile-only system - use mobile column count
        return st.columns(mobile_cols)

    def _get_fallback_css(self) -> str:
        """Generate fallback CSS for mobile layout with fixed 428px design."""
        return """
        <style>
        :root {
            --mobile-max-width: 428px;
            --primary-color: #16A34A;
            --primary-hover: #15803D;
            --accent-color: #22C55E;
            --background-color: #F8FAFC;
            --surface-color: #FFFFFF;
            --text-primary: #1F2937;
            --text-secondary: #6B7280;
            --border-color: #E5E7EB;
            --spacing-unit: 16px;
            --touch-target-size: 48px;
            --border-radius: 12px;
        }
        
        .mobile-fallback {
            width: 100%;
            max-width: var(--mobile-max-width);
            padding: var(--spacing-unit);
            margin: 0 auto;
            background-color: var(--background-color);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .mobile-fallback-container {
            width: 100%;
            max-width: 428px;
            margin: 0 auto;
            padding: 16px;
            box-sizing: border-box;
        }
        
        .mobile-fallback-section {
            width: 100%;
            padding: 16px;
            margin-bottom: 24px;
            background-color: var(--surface-color);
            border-radius: var(--border-radius);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .mobile-fallback-button {
            min-height: var(--touch-target-size);
            min-width: var(--touch-target-size);
            padding: 12px 16px;
            border-radius: var(--border-radius);
            background-color: var(--primary-color);
            color: white;
            border: none;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            touch-action: manipulation;
        }
        
        .mobile-fallback-button:hover {
            background-color: var(--primary-hover);
        }
        </style>
        """

    @property
    def performance_optimizer(self) -> Any:
        """Get performance optimizer instance or fallback configuration."""
        if hasattr(self, "_performance_optimizer") and self._performance_optimizer is not None:
            return self._performance_optimizer
        else:
            # Return fallback configuration when optimizer is not available
            return {
                "status": "fallback",
                "optimization_level": "basic",
                "memory_management": False,
                "lazy_loading": False,
                "cache_enabled": False,
                "bundle_optimization": False,
            }

    @property
    def bundle_optimizer(self) -> dict[str, Any] | None:
        """Get bundle optimizer instance or None if not available."""
        if hasattr(self, "_bundle_optimizer"):
            return self._bundle_optimizer
        else:
            return None

    def apply_touch_optimization(self) -> None:
        """Apply touch-specific optimizations."""
        touch_css = """
        <style>
        /* Touch action optimization */
        .mobile-button, .mobile-input, .mobile-card {{
            touch-action: manipulation;
        }}
        
        /* Prevent zoom on input focus */
        input, textarea, select {{
            font-size: var(--font-size-base);
        }}
        
        /* Smooth scrolling */
        html {{
            scroll-behavior: smooth;
        }}
        
        /* Optimize for touch scrolling */
        .mobile-scrollable {{
            -webkit-overflow-scrolling: touch;
            overflow-y: auto;
        }}
        </style>
        """
        st.markdown(touch_css, unsafe_allow_html=True)

    def load_fallback_css(self) -> None:
        """Load fallback CSS for compatibility mode."""
        try:
            fallback_css = self._get_fallback_css()
            st.markdown(fallback_css, unsafe_allow_html=True)
            logger.debug("Fallback CSS loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load fallback CSS: {e}")

    def create_css_bundle(self, css_files: dict[str, str], bundle_name: str) -> bool:
        """Create CSS bundle using bundle optimizer."""
        try:
            if hasattr(self, "_bundle_optimizer") and self._bundle_optimizer:
                return self._bundle_optimizer.create_css_bundle(css_files, bundle_name)
            else:
                logger.debug("Bundle optimizer not available, skipping CSS bundling")
                return False
        except Exception as e:
            logger.warning(f"Failed to create CSS bundle: {e}")
            return False

    def load_css_bundle(self, bundle_name: str) -> bool:
        """Load CSS bundle by name."""
        try:
            if hasattr(self, "_bundle_optimizer") and self._bundle_optimizer:
                return self._bundle_optimizer.load_bundle(bundle_name)
            else:
                logger.debug("Bundle optimizer not available, cannot load CSS bundle")
                return False
        except Exception as e:
            logger.warning(f"Failed to load CSS bundle: {e}")
            return False

    def _initialize_performance_optimizations(self) -> None:
        """Initialize performance optimization systems."""
        try:
            # Initialize bundle optimizer with proper error handling
            MobileBundleOptimizer = ImportErrorRecovery.safe_import_from(
                "ui.components.mobile_bundle_optimizer", "MobileBundleOptimizer", logger_name="mobile_layout_manager"
            )
            if MobileBundleOptimizer:
                self._bundle_optimizer = MobileBundleOptimizer()
                logger.debug("Bundle optimizer initialized")
            else:
                self._bundle_optimizer = None

            # Initialize performance optimizer with proper error handling
            MobilePerformanceOptimizer = ImportErrorRecovery.safe_import_from(
                "ui.components.mobile_performance_optimizer", "MobilePerformanceOptimizer", logger_name="mobile_layout_manager"
            )
            if MobilePerformanceOptimizer:
                self._performance_optimizer = MobilePerformanceOptimizer()
                logger.debug("Performance optimizer initialized")
            else:
                self._performance_optimizer = None

        except Exception as e:
            logger.warning(f"Failed to initialize performance optimizations: {e}")
            self._bundle_optimizer = None
            self._performance_optimizer = None


# Utility functions for mobile layout
def initialize_mobile_layout(component_id: str = "mobile_layout") -> MobileLayoutManager:
    """Initialize and return mobile layout manager instance."""
    if "mobile_layout_manager" not in st.session_state:
        st.session_state.mobile_layout_manager = MobileLayoutManager(component_id)

    return st.session_state.mobile_layout_manager


def is_mobile_device() -> bool:
    """Detect if user is on mobile device (placeholder for future enhancement)."""
    # This is a placeholder - in a real implementation, you might use
    # JavaScript to detect screen size or user agent
    return True  # For now, assume mobile-first approach


def get_mobile_breakpoint() -> str:
    """Get current mobile breakpoint for responsive behavior."""
    # Placeholder for dynamic breakpoint detection
    return "mobile"  # Default to mobile breakpoint
