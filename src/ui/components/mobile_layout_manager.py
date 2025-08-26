"""
Mobile Layout Manager for PlantGuard UI.

This module provides the core layout management system for mobile interfaces,
implementing responsive design patterns and touch-optimized layouts with
performance optimizations for mobile devices.
"""

import logging
from datetime import datetime
from typing import Any

import streamlit as st

from .mobile_component_registry import MobileComponentRegistry
from .mobile_state_manager import MobileStateManager

logger = logging.getLogger(__name__)


class MobileLayoutManager:
    """Main layout manager for mobile interface."""

    def __init__(self, component_id: str = "mobile_layout", **kwargs):
        """Initialize mobile layout manager with configuration."""
        self.component_id = component_id
        self.config = {
            "layout_type": "single_column",
            "touch_target_size": 48,
            "spacing_unit": 16,
            "max_width": "100%",
            "breakpoints": {"mobile": 480, "tablet": 768, "desktop": 1024},
            "performance_optimizations": True,
            "lazy_loading": True,
            "resource_bundling": True,
            "offline_support": True,
        }

        # Update config with any provided kwargs
        self.config.update(kwargs)

        self.component_registry = MobileComponentRegistry()
        self.state_manager = MobileStateManager()
        self._css_injected = False

        # Initialize performance optimizations
        self._initialize_performance_optimizations()

    def render(self) -> None:
        """Render the complete mobile layout with performance optimizations."""
        try:
            # Check if performance optimizations are enabled
            if self.config.get("performance_optimizations", True):
                self._check_memory_pressure()
                self._preload_critical_resources()

            with st.container():
                self._apply_mobile_styles()
                self._render_header()
                self._render_main_content()
                self._render_status_bar()

                # Render performance indicators if enabled
                if self.config.get("show_performance_stats", False):
                    self._render_performance_stats()

        except Exception as e:
            logger.error(f"Mobile layout rendering failed: {e}")
            self._render_error_fallback()

    def _apply_mobile_styles(self) -> None:
        """Apply mobile-specific CSS styles."""
        if not self._css_injected:
            st.markdown(self._get_mobile_css(), unsafe_allow_html=True)
            self._css_injected = True

    def _get_mobile_css(self) -> str:
        """Generate mobile-optimized CSS with design system variables."""
        return """
        <style>
        :root {
            /* Color System */
            --primary-color: #16A34A;
            --primary-hover: #15803D;
            --accent-color: #22C55E;
            --background-color: #F8FAFC;
            --surface-color: #FFFFFF;
            --text-primary: #1F2937;
            --text-secondary: #6B7280;
            --border-color: #E5E7EB;
            --error-color: #EF4444;
            --warning-color: #F59E0B;
            --success-color: #10B981;
            
            /* Layout System */
            --touch-target-size: 48px;
            --border-radius: 12px;
            --border-radius-sm: 8px;
            --spacing-unit: 16px;
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            
            /* Typography */
            --font-size-xs: 12px;
            --font-size-sm: 14px;
            --font-size-base: 16px;
            --font-size-lg: 18px;
            --font-size-xl: 20px;
            --font-size-2xl: 24px;
            --font-weight-normal: 400;
            --font-weight-medium: 500;
            --font-weight-semibold: 600;
            --font-weight-bold: 700;
            
            /* Shadows */
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            
            /* Animation */
            --transition-fast: 0.15s ease;
            --transition-base: 0.2s ease;
            --transition-slow: 0.3s ease;
        }
        
        /* Mobile Layout Foundation */
        .mobile-main-layout {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding: 0;
            margin: 0;
            background-color: var(--background-color);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .mobile-container {
            width: 100%;
            max-width: 100vw;
            margin: 0 auto;
            padding: 0 var(--spacing-md);
            box-sizing: border-box;
        }
        
        .mobile-section {
            padding: var(--spacing-md);
            margin-bottom: var(--spacing-lg);
            background-color: var(--surface-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-sm);
        }
        
        /* Touch-Optimized Components */
        .mobile-button {
            min-height: var(--touch-target-size);
            min-width: var(--touch-target-size);
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: var(--border-radius);
            font-size: var(--font-size-base);
            font-weight: var(--font-weight-semibold);
            touch-action: manipulation;
            border: none;
            cursor: pointer;
            transition: all var(--transition-base);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--spacing-xs);
            text-decoration: none;
            user-select: none;
            -webkit-tap-highlight-color: transparent;
        }
        
        .mobile-button:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        .mobile-button:active {
            transform: translateY(0);
            box-shadow: var(--shadow-sm);
        }
        
        .mobile-button-primary {
            background-color: var(--primary-color);
            color: white;
        }
        
        .mobile-button-primary:hover {
            background-color: var(--primary-hover);
        }
        
        .mobile-button-secondary {
            background-color: var(--surface-color);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        /* Input Grid System */
        .mobile-input-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--spacing-sm);
            padding: var(--spacing-md);
            width: 100%;
            box-sizing: border-box;
        }
        
        .mobile-input-item {
            aspect-ratio: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            cursor: pointer;
            transition: all var(--transition-base);
            min-height: var(--touch-target-size);
        }
        
        .mobile-input-item:hover {
            border-color: var(--primary-color);
            box-shadow: var(--shadow-md);
        }
        
        .mobile-input-item:active {
            transform: scale(0.98);
        }
        
        /* Card System */
        .mobile-card {
            background: var(--surface-color);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            box-shadow: var(--shadow-sm);
            margin-bottom: var(--spacing-md);
            border: 1px solid var(--border-color);
        }
        
        .mobile-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--spacing-md);
            padding-bottom: var(--spacing-sm);
            border-bottom: 1px solid var(--border-color);
        }
        
        .mobile-card-title {
            font-size: var(--font-size-lg);
            font-weight: var(--font-weight-semibold);
            color: var(--text-primary);
            margin: 0;
        }
        
        /* Loading States */
        .mobile-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: var(--spacing-xl);
            color: var(--text-secondary);
        }
        
        .mobile-spinner {
            width: 24px;
            height: 24px;
            border: 2px solid var(--border-color);
            border-top: 2px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: var(--spacing-sm);
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Error States */
        .mobile-error {
            background-color: #FEF2F2;
            border: 1px solid #FECACA;
            color: var(--error-color);
            padding: var(--spacing-md);
            border-radius: var(--border-radius);
            margin-bottom: var(--spacing-md);
        }
        
        .mobile-error-title {
            font-weight: var(--font-weight-semibold);
            margin-bottom: var(--spacing-xs);
        }
        
        /* Responsive Breakpoints */
        @media (max-width: 480px) {
            .mobile-container {
                padding: 0 var(--spacing-sm);
            }
            
            .mobile-section {
                padding: var(--spacing-sm);
                margin-bottom: var(--spacing-md);
            }
            
            .mobile-input-grid {
                gap: var(--spacing-xs);
                padding: var(--spacing-sm);
            }
            
            .mobile-card {
                padding: var(--spacing-sm);
            }
        }
        
        @media (max-width: 360px) {
            :root {
                --spacing-unit: 12px;
                --spacing-md: 12px;
                --spacing-lg: 18px;
            }
            
            .mobile-button {
                font-size: var(--font-size-sm);
                padding: var(--spacing-xs) var(--spacing-sm);
            }
        }
        
        /* Accessibility Enhancements */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        @media (prefers-color-scheme: dark) {
            :root {
                --background-color: #0F172A;
                --surface-color: #1E293B;
                --text-primary: #F1F5F9;
                --text-secondary: #94A3B8;
                --border-color: #334155;
            }
        }
        
        /* Focus States for Accessibility */
        .mobile-button:focus,
        .mobile-input-item:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }
        
        /* High Contrast Mode Support */
        @media (prefers-contrast: high) {
            :root {
                --border-color: #000000;
                --text-secondary: var(--text-primary);
            }
        }
        </style>
        """

    def _render_header(self) -> None:
        """Render mobile header section."""
        try:
            st.markdown(
                """
            <div class="mobile-section">
                <div class="mobile-card-header">
                    <h1 class="mobile-card-title">🌿 PlantGuard Mobile</h1>
                    <div class="mobile-status-indicator" id="mobile-status">
                        <span style="color: var(--success-color);">●</span> Ready
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        except Exception as e:
            logger.warning(f"Header rendering failed: {e}")

    def _render_main_content(self) -> None:
        """Render main content area."""
        try:
            st.markdown('<div class="mobile-main-content">', unsafe_allow_html=True)

            # Main content will be populated by specific components
            # This is the container where mobile components will be rendered
            placeholder = st.empty()

            # Store placeholder in state for component access
            self.state_manager.set_global_state("main_content_placeholder", placeholder)

            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            logger.warning(f"Main content rendering failed: {e}")

    def _render_status_bar(self) -> None:
        """Render mobile status bar."""
        try:
            st.markdown(
                """
            <div class="mobile-status-bar" style="
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: var(--surface-color);
                border-top: 1px solid var(--border-color);
                padding: var(--spacing-xs) var(--spacing-md);
                font-size: var(--font-size-xs);
                color: var(--text-secondary);
                text-align: center;
                z-index: 1000;
            ">
                <span id="mobile-connection-status">Connected</span> • 
                <span id="mobile-last-update">Updated: {}</span>
            </div>
            """.format(datetime.now().strftime("%H:%M")),
                unsafe_allow_html=True,
            )
        except Exception as e:
            logger.warning(f"Status bar rendering failed: {e}")

    def _render_error_fallback(self) -> None:
        """Render error fallback interface."""
        st.markdown(
            """
        <div class="mobile-error">
            <div class="mobile-error-title">⚠️ Interface Error</div>
            <p>The mobile interface encountered an error. Please refresh the page.</p>
            <button onclick="window.location.reload()" class="mobile-button mobile-button-primary">
                🔄 Refresh Page
            </button>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def get_config(self) -> dict[str, Any]:
        """Get current layout configuration."""
        return self.config.copy()

    def update_config(self, updates: dict[str, Any]) -> None:
        """Update layout configuration."""
        self.config.update(updates)
        logger.info(f"Mobile layout config updated: {updates}")

    def register_component(self, component_type: str, component_class) -> None:
        """Register a new mobile component type."""
        self.component_registry.register_component(component_type, component_class)

    def create_component(self, component_type: str, component_id: str, title: str):
        """Create a mobile component instance."""
        return self.component_registry.create_component(component_type, component_id, title)

    def _initialize_performance_optimizations(self) -> None:
        """Initialize performance optimization systems."""
        try:
            # Try to import optional performance modules
            try:
                from .mobile_performance_optimizer import mobile_performance_optimizer

                mobile_performance_optimizer.set_optimization_level("auto")
            except ImportError:
                logger.debug("Mobile performance optimizer not available, using basic optimizations")

            # Try to enable offline mode if configured
            if self.config.get("offline_support", True):
                try:
                    from .mobile_offline_manager import mobile_offline_manager

                    mobile_offline_manager.enable_offline_mode()
                except ImportError:
                    logger.debug("Mobile offline manager not available")

            # Try to create CSS bundle for mobile styles
            if self.config.get("resource_bundling", True):
                try:
                    from .mobile_bundle_optimizer import mobile_bundle_optimizer

                    css_content = self._get_mobile_css()
                    mobile_bundle_optimizer.create_css_bundle({"mobile_layout": css_content}, "mobile_layout_styles")
                except ImportError:
                    logger.debug("Mobile bundle optimizer not available, using inline CSS")

            logger.debug("Performance optimizations initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize performance optimizations: {e}")

    def _check_memory_pressure(self) -> None:
        """Check and handle memory pressure."""
        try:
            memory_pressure = mobile_performance_optimizer.memory_manager.check_memory_pressure()

            if memory_pressure == "critical":
                # Force memory cleanup
                mobile_performance_optimizer.memory_manager.cleanup_memory(force=True)
                logger.warning("Critical memory pressure detected - performed cleanup")

                # Show user notification
                st.warning("⚠️ Low memory detected. Some features may be limited.")

            elif memory_pressure == "warning":
                # Gentle cleanup
                mobile_performance_optimizer.memory_manager.cleanup_memory()
                logger.info("Memory pressure warning - performed gentle cleanup")

        except Exception as e:
            logger.warning(f"Memory pressure check failed: {e}")

    def _preload_critical_resources(self) -> None:
        """Preload critical resources for better performance."""
        try:
            # Preload critical mobile components
            critical_components = ["mobile_header", "mobile_input_ribbon", "mobile_image_analysis"]

            mobile_performance_optimizer.preload_critical_components(critical_components)

            # Load critical bundles
            mobile_bundle_optimizer.preload_critical_bundles()

        except Exception as e:
            logger.warning(f"Failed to preload critical resources: {e}")

    def _render_performance_stats(self) -> None:
        """Render performance statistics for debugging."""
        try:
            with st.expander("📊 Performance Stats", expanded=False):
                # Get performance report
                perf_report = mobile_performance_optimizer.get_performance_report()

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Avg Render Time", f"{perf_report['session_info']['avg_render_time']:.3f}s")
                    st.metric("Cache Hit Rate", f"{perf_report['cache_stats']['hit_rate']:.1f}%")

                with col2:
                    st.metric("Memory Usage", f"{perf_report['memory_stats']['rss_mb']:.1f}MB")
                    st.metric("Memory Pressure", perf_report["memory_pressure"].title())

                with col3:
                    st.metric("Loaded Components", len(perf_report["loaded_components"]))
                    st.metric("Cache Size", f"{perf_report['cache_stats']['size_mb']:.1f}MB")

                # Offline stats
                offline_stats = mobile_offline_manager.get_offline_stats()
                if offline_stats["enabled"]:
                    st.markdown("**Offline Status:**")
                    st.json(
                        {
                            "connection": offline_stats["connection_status"],
                            "cached_resources": offline_stats["cached_resources"],
                            "queued_operations": offline_stats["queued_operations"],
                        }
                    )

        except Exception as e:
            logger.warning(f"Failed to render performance stats: {e}")

    def get_layout_status(self) -> dict[str, Any]:
        """Get comprehensive layout status including performance metrics."""
        try:
            base_status = {
                "status": "ready",
                "config": self.config.copy(),
                "css_injected": self._css_injected,
                "components_registered": len(self.component_registry.get_all_components()),
            }

            # Add performance metrics if optimizations are enabled
            if self.config.get("performance_optimizations", True):
                perf_report = mobile_performance_optimizer.get_performance_report()
                offline_stats = mobile_offline_manager.get_offline_stats()
                bundle_stats = mobile_bundle_optimizer.get_bundle_stats()

                base_status.update(
                    {
                        "performance": {
                            "avg_render_time": perf_report["session_info"]["avg_render_time"],
                            "memory_usage_mb": perf_report["memory_stats"]["rss_mb"],
                            "memory_pressure": perf_report["memory_pressure"],
                            "cache_hit_rate": perf_report["cache_stats"]["hit_rate"],
                        },
                        "offline": {
                            "enabled": offline_stats["enabled"],
                            "connection_status": offline_stats["connection_status"],
                            "cached_resources": offline_stats["cached_resources"],
                            "cache_size_mb": offline_stats["cache_size_mb"],
                        },
                        "bundles": {
                            "total_bundles": bundle_stats["total_bundles"],
                            "loaded_bundles": bundle_stats["loaded_bundles"],
                            "load_success_rate": bundle_stats["load_success_rate"],
                        },
                    }
                )

            return base_status

        except Exception as e:
            logger.error(f"Failed to get layout status: {e}")
            return {"status": "error", "error": str(e)}

    def enable_performance_monitoring(self) -> None:
        """Enable performance monitoring and stats display."""
        self.config["show_performance_stats"] = True
        logger.info("Performance monitoring enabled")

    def disable_performance_monitoring(self) -> None:
        """Disable performance monitoring and stats display."""
        self.config["show_performance_stats"] = False
        logger.info("Performance monitoring disabled")

    def optimize_for_low_memory(self) -> None:
        """Optimize layout for low memory devices."""
        # Set aggressive optimization level
        mobile_performance_optimizer.set_optimization_level("aggressive")

        # Reduce cache sizes
        mobile_performance_optimizer.cache.max_size_bytes = 25 * 1024 * 1024  # 25MB

        # Enable aggressive memory management
        self.config["aggressive_memory_management"] = True

        logger.info("Layout optimized for low memory devices")

    def load_mobile_css(self) -> None:
        """Load mobile CSS with performance optimizations."""
        if not self._css_injected:
            try:
                # Try to check if bundled CSS is available
                try:
                    from .mobile_bundle_optimizer import mobile_bundle_optimizer

                    if mobile_bundle_optimizer.load_bundle("mobile_layout_styles"):
                        logger.debug("Loaded CSS from bundle")
                    else:
                        # Fallback to inline CSS
                        self._apply_mobile_styles()
                except ImportError:
                    # Bundle optimizer not available, use inline CSS
                    self._apply_mobile_styles()

                self._css_injected = True

            except Exception as e:
                logger.warning(f"Failed to load optimized CSS: {e}")
                # Fallback to basic CSS injection
                self._apply_mobile_styles()
