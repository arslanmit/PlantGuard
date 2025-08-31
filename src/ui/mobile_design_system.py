"""
Mobile CSS Design System for PlantGuard UI.

This module provides standardized CSS classes, component styling, and design tokens
optimized for mobile interfaces and AI agent recognition.
"""

from enum import Enum

import streamlit as st


class ButtonVariant(Enum):
    """Button style variants for mobile interface."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    GHOST = "ghost"


class ComponentSize(Enum):
    """Component size variants."""

    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"
    EXTRA_LARGE = "xl"


class MobileDesignSystem:
    """Mobile CSS design system with standardized components and styling."""

    def __init__(self) -> None:
        """Initialize mobile design system."""
        self.design_tokens = self._get_design_tokens()
        self._apply_design_system()

    def _get_design_tokens(self) -> dict[str, Any]:
        """Get design tokens for consistent styling."""
        return {
            "colors": {
                "primary": "#16A34A",
                "primary_hover": "#15803D",
                "primary_active": "#14532D",
                "secondary": "#6B7280",
                "secondary_hover": "#4B5563",
                "success": "#10B981",
                "warning": "#F59E0B",
                "danger": "#EF4444",
                "surface": "#FFFFFF",
                "background": "#F8FAFC",
                "text_primary": "#1F2937",
                "text_secondary": "#6B7280",
                "text_muted": "#9CA3AF",
                "border": "#E5E7EB",
                "border_focus": "#3B82F6",
            },
            "spacing": {
                "xs": "4px",
                "sm": "8px",
                "md": "16px",
                "lg": "24px",
                "xl": "32px",
                "2xl": "48px",
            },
            "typography": {
                "xs": "12px",
                "sm": "14px",
                "base": "16px",
                "lg": "18px",
                "xl": "20px",
                "2xl": "24px",
                "3xl": "30px",
            },
            "shadows": {
                "sm": "0 1px 2px rgba(0,0,0,0.05)",
                "md": "0 4px 6px rgba(0,0,0,0.1)",
                "lg": "0 10px 15px rgba(0,0,0,0.1)",
                "xl": "0 20px 25px rgba(0,0,0,0.1)",
            },
            "radius": {
                "sm": "6px",
                "md": "8px",
                "lg": "12px",
                "xl": "16px",
                "full": "9999px",
            },
        }

    def _apply_design_system(self) -> None:
        """Apply the complete mobile design system CSS."""
        design_css = self._get_design_system_css()
        st.markdown(design_css, unsafe_allow_html=True)

    def _get_design_system_css(self) -> str:
        """Generate complete mobile design system CSS."""
        tokens = self.design_tokens

        return f"""
        <style>
        /* Mobile Design System - Component Styles */
        
        /* Button Components with mobile- prefix for AI agent recognition */
        .mobile-button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 48px;
            min-width: 48px;
            padding: 12px 16px;
            font-size: {tokens["typography"]["base"]};
            font-weight: 600;
            line-height: 1.2;
            border: none;
            border-radius: {tokens["radius"]["lg"]};
            cursor: pointer;
            transition: all 0.2s ease;
            touch-action: manipulation;
            text-decoration: none;
            box-sizing: border-box;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
        }}
        
        /* Button Variants */
        .mobile-button-primary {{
            background-color: {tokens["colors"]["primary"]};
            color: white;
            box-shadow: {tokens["shadows"]["sm"]};
        }}
        
        .mobile-button-primary:hover {{
            background-color: {tokens["colors"]["primary_hover"]};
            box-shadow: {tokens["shadows"]["md"]};
            transform: translateY(-1px);
        }}
        
        .mobile-button-primary:active {{
            background-color: {tokens["colors"]["primary_active"]};
            transform: translateY(0);
        }}
        
        .mobile-button-secondary {{
            background-color: {tokens["colors"]["surface"]};
            color: {tokens["colors"]["text_primary"]};
            border: 2px solid {tokens["colors"]["border"]};
        }}
        
        .mobile-button-secondary:hover {{
            border-color: {tokens["colors"]["secondary"]};
            box-shadow: {tokens["shadows"]["sm"]};
        }}
        
        .mobile-button-success {{
            background-color: {tokens["colors"]["success"]};
            color: white;
        }}
        
        .mobile-button-warning {{
            background-color: {tokens["colors"]["warning"]};
            color: white;
        }}
        
        .mobile-button-danger {{
            background-color: {tokens["colors"]["danger"]};
            color: white;
        }}
        
        .mobile-button-ghost {{
            background-color: transparent;
            color: {tokens["colors"]["primary"]};
            border: 2px solid transparent;
        }}
        
        .mobile-button-ghost:hover {{
            background-color: rgba(22, 163, 74, 0.1);
            border-color: {tokens["colors"]["primary"]};
        }}
        
        /* Button Sizes */
        .mobile-button-sm {{
            min-height: 40px;
            padding: 8px 12px;
            font-size: {tokens["typography"]["sm"]};
        }}
        
        .mobile-button-lg {{
            min-height: 56px;
            padding: 16px 24px;
            font-size: {tokens["typography"]["lg"]};
        }}
        
        .mobile-button-xl {{
            min-height: 64px;
            padding: 20px 32px;
            font-size: {tokens["typography"]["xl"]};
        }}
        
        /* Full width button */
        .mobile-button-full {{
            width: 100%;
        }}
        
        /* Card Components */
        .mobile-card {{
            background-color: {tokens["colors"]["surface"]};
            border-radius: {tokens["radius"]["lg"]};
            padding: {tokens["spacing"]["md"]};
            box-shadow: {tokens["shadows"]["sm"]};
            border: 1px solid {tokens["colors"]["border"]};
            margin-bottom: {tokens["spacing"]["md"]};
            box-sizing: border-box;
        }}
        
        .mobile-card-elevated {{
            box-shadow: {tokens["shadows"]["lg"]};
            border: none;
        }}
        
        .mobile-card-interactive {{
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .mobile-card-interactive:hover {{
            box-shadow: {tokens["shadows"]["md"]};
            transform: translateY(-2px);
        }}
        
        .mobile-card-interactive:active {{
            transform: translateY(0);
        }}
        
        /* Card Header */
        .mobile-card-header {{
            padding-bottom: {tokens["spacing"]["sm"]};
            margin-bottom: {tokens["spacing"]["sm"]};
            border-bottom: 1px solid {tokens["colors"]["border"]};
        }}
        
        .mobile-card-title {{
            font-size: {tokens["typography"]["lg"]};
            font-weight: 600;
            color: {tokens["colors"]["text_primary"]};
            margin: 0;
        }}
        
        .mobile-card-subtitle {{
            font-size: {tokens["typography"]["sm"]};
            color: {tokens["colors"]["text_secondary"]};
            margin: 4px 0 0 0;
        }}
        
        /* Input Components */
        .mobile-input {{
            width: 100%;
            min-height: 48px;
            padding: 12px 16px;
            font-size: {tokens["typography"]["base"]};
            border: 2px solid {tokens["colors"]["border"]};
            border-radius: {tokens["radius"]["md"]};
            background-color: {tokens["colors"]["surface"]};
            color: {tokens["colors"]["text_primary"]};
            box-sizing: border-box;
            transition: border-color 0.2s ease;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
        }}
        
        .mobile-input:focus {{
            outline: none;
            border-color: {tokens["colors"]["border_focus"]};
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }}
        
        .mobile-input::placeholder {{
            color: {tokens["colors"]["text_muted"]};
        }}
        
        /* Textarea */
        .mobile-textarea {{
            min-height: 96px;
            resize: vertical;
            font-family: inherit;
        }}
        
        /* Loading States */
        .mobile-loading {{
            position: relative;
            pointer-events: none;
            opacity: 0.7;
        }}
        
        .mobile-loading::after {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid transparent;
            border-top: 2px solid {tokens["colors"]["primary"]};
            border-radius: 50%;
            animation: mobile-spin 1s linear infinite;
        }}
        
        @keyframes mobile-spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Progress Bar */
        .mobile-progress {{
            width: 100%;
            height: 8px;
            background-color: {tokens["colors"]["border"]};
            border-radius: {tokens["radius"]["full"]};
            overflow: hidden;
        }}
        
        .mobile-progress-bar {{
            height: 100%;
            background-color: {tokens["colors"]["primary"]};
            border-radius: {tokens["radius"]["full"]};
            transition: width 0.3s ease;
        }}
        
        /* Badge/Chip Components */
        .mobile-badge {{
            display: inline-flex;
            align-items: center;
            padding: 4px 8px;
            font-size: {tokens["typography"]["xs"]};
            font-weight: 500;
            border-radius: {tokens["radius"]["full"]};
            background-color: {tokens["colors"]["border"]};
            color: {tokens["colors"]["text_secondary"]};
        }}
        
        .mobile-badge-primary {{
            background-color: {tokens["colors"]["primary"]};
            color: white;
        }}
        
        .mobile-badge-success {{
            background-color: {tokens["colors"]["success"]};
            color: white;
        }}
        
        .mobile-badge-warning {{
            background-color: {tokens["colors"]["warning"]};
            color: white;
        }}
        
        /* Alert Components */
        .mobile-alert {{
            padding: {tokens["spacing"]["md"]};
            border-radius: {tokens["radius"]["md"]};
            margin-bottom: {tokens["spacing"]["md"]};
            border-left: 4px solid;
        }}
        
        .mobile-alert-info {{
            background-color: #EBF8FF;
            border-color: #3B82F6;
            color: #1E40AF;
        }}
        
        .mobile-alert-success {{
            background-color: #ECFDF5;
            border-color: {tokens["colors"]["success"]};
            color: #065F46;
        }}
        
        .mobile-alert-warning {{
            background-color: #FFFBEB;
            border-color: {tokens["colors"]["warning"]};
            color: #92400E;
        }}
        
        .mobile-alert-error {{
            background-color: #FEF2F2;
            border-color: {tokens["colors"]["danger"]};
            color: #991B1B;
        }}
        
        /* Divider */
        .mobile-divider {{
            height: 1px;
            background-color: {tokens["colors"]["border"]};
            margin: {tokens["spacing"]["lg"]} 0;
            border: none;
        }}
        
        /* Spacing Utilities */
        .mobile-mt-xs {{ margin-top: {tokens["spacing"]["xs"]}; }}
        .mobile-mt-sm {{ margin-top: {tokens["spacing"]["sm"]}; }}
        .mobile-mt-md {{ margin-top: {tokens["spacing"]["md"]}; }}
        .mobile-mt-lg {{ margin-top: {tokens["spacing"]["lg"]}; }}
        .mobile-mt-xl {{ margin-top: {tokens["spacing"]["xl"]}; }}
        
        .mobile-mb-xs {{ margin-bottom: {tokens["spacing"]["xs"]}; }}
        .mobile-mb-sm {{ margin-bottom: {tokens["spacing"]["sm"]}; }}
        .mobile-mb-md {{ margin-bottom: {tokens["spacing"]["md"]}; }}
        .mobile-mb-lg {{ margin-bottom: {tokens["spacing"]["lg"]}; }}
        .mobile-mb-xl {{ margin-bottom: {tokens["spacing"]["xl"]}; }}
        
        .mobile-p-xs {{ padding: {tokens["spacing"]["xs"]}; }}
        .mobile-p-sm {{ padding: {tokens["spacing"]["sm"]}; }}
        .mobile-p-md {{ padding: {tokens["spacing"]["md"]}; }}
        .mobile-p-lg {{ padding: {tokens["spacing"]["lg"]}; }}
        .mobile-p-xl {{ padding: {tokens["spacing"]["xl"]}; }}
        
        /* Text Utilities */
        .mobile-text-xs {{ font-size: {tokens["typography"]["xs"]}; }}
        .mobile-text-sm {{ font-size: {tokens["typography"]["sm"]}; }}
        .mobile-text-base {{ font-size: {tokens["typography"]["base"]}; }}
        .mobile-text-lg {{ font-size: {tokens["typography"]["lg"]}; }}
        .mobile-text-xl {{ font-size: {tokens["typography"]["xl"]}; }}
        .mobile-text-2xl {{ font-size: {tokens["typography"]["2xl"]}; }}
        
        .mobile-text-primary {{ color: {tokens["colors"]["text_primary"]}; }}
        .mobile-text-secondary {{ color: {tokens["colors"]["text_secondary"]}; }}
        .mobile-text-muted {{ color: {tokens["colors"]["text_muted"]}; }}
        
        .mobile-text-center {{ text-align: center; }}
        .mobile-text-left {{ text-align: left; }}
        .mobile-text-right {{ text-align: right; }}
        
        .mobile-font-normal {{ font-weight: 400; }}
        .mobile-font-medium {{ font-weight: 500; }}
        .mobile-font-semibold {{ font-weight: 600; }}
        .mobile-font-bold {{ font-weight: 700; }}
        
        /* Layout Utilities */
        .mobile-flex {{ display: flex; }}
        .mobile-flex-col {{ flex-direction: column; }}
        .mobile-flex-row {{ flex-direction: row; }}
        .mobile-items-center {{ align-items: center; }}
        .mobile-justify-center {{ justify-content: center; }}
        .mobile-justify-between {{ justify-content: space-between; }}
        .mobile-gap-xs {{ gap: {tokens["spacing"]["xs"]}; }}
        .mobile-gap-sm {{ gap: {tokens["spacing"]["sm"]}; }}
        .mobile-gap-md {{ gap: {tokens["spacing"]["md"]}; }}
        .mobile-gap-lg {{ gap: {tokens["spacing"]["lg"]}; }}
        
        .mobile-w-full {{ width: 100%; }}
        .mobile-h-full {{ height: 100%; }}
        
        /* Visual Feedback Animations */
        .mobile-pulse {{
            animation: mobile-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        
        @keyframes mobile-pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .mobile-bounce {{
            animation: mobile-bounce 1s infinite;
        }}
        
        @keyframes mobile-bounce {{
            0%, 20%, 53%, 80%, 100% {{ transform: translate3d(0,0,0); }}
            40%, 43% {{ transform: translate3d(0, -30px, 0); }}
            70% {{ transform: translate3d(0, -15px, 0); }}
            90% {{ transform: translate3d(0, -4px, 0); }}
        }}
        
        /* Touch feedback */
        .mobile-touch-feedback {{
            position: relative;
            overflow: hidden;
        }}
        
        .mobile-touch-feedback::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }}
        
        .mobile-touch-feedback:active::before {{
            width: 300px;
            height: 300px;
        }}
        
        /* Accessibility improvements */
        .mobile-sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }}
        
        /* Focus styles for accessibility */
        .mobile-focus-visible:focus-visible {{
            outline: 2px solid {tokens["colors"]["border_focus"]};
            outline-offset: 2px;
        }}
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {{
            .mobile-button {{
                border: 2px solid;
            }}
            
            .mobile-card {{
                border: 2px solid {tokens["colors"]["border"]};
            }}
        }}
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        </style>
        """

    def create_button(
        self,
        text: str,
        variant: ButtonVariant = ButtonVariant.PRIMARY,
        size: ComponentSize = ComponentSize.MEDIUM,
        full_width: bool = False,
        loading: bool = False,
        disabled: bool = False,
        icon: str | None = None,
    ) -> str:
        """Create a mobile-optimized button with specified styling."""
        classes = ["mobile-button", f"mobile-button-{variant.value}"]

        if size != ComponentSize.MEDIUM:
            classes.append(f"mobile-button-{size.value}")

        if full_width:
            classes.append("mobile-button-full")

        if loading:
            classes.append("mobile-loading")

        class_str = " ".join(classes)
        disabled_attr = "disabled" if disabled else ""

        icon_html = f'<span class="mobile-button-icon">{icon}</span>' if icon else ""

        return f"""
        <button class="{class_str}" {disabled_attr}>
            {icon_html}
            <span>{text}</span>
        </button>
        """

    def create_card(
        self, content: str, title: str | None = None, subtitle: str | None = None, elevated: bool = False, interactive: bool = False
    ) -> str:
        """Create a mobile-optimized card component."""
        classes = ["mobile-card"]

        if elevated:
            classes.append("mobile-card-elevated")

        if interactive:
            classes.append("mobile-card-interactive")

        class_str = " ".join(classes)

        header_html = ""
        if title or subtitle:
            header_html = f"""
            <div class="mobile-card-header">
                {f'<h3 class="mobile-card-title">{title}</h3>' if title else ""}
                {f'<p class="mobile-card-subtitle">{subtitle}</p>' if subtitle else ""}
            </div>
            """

        return f"""
        <div class="{class_str}">
            {header_html}
            <div class="mobile-card-content">
                {content}
            </div>
        </div>
        """

    def create_alert(self, message: str, alert_type: str = "info") -> str:
        """Create a mobile-optimized alert component."""
        return f"""
        <div class="mobile-alert mobile-alert-{alert_type}">
            {message}
        </div>
        """

    def create_progress_bar(self, progress: float, label: str | None = None) -> str:
        """Create a mobile-optimized progress bar."""
        progress_percent = max(0, min(100, progress * 100))

        label_html = f'<div class="mobile-text-sm mobile-mb-xs">{label}</div>' if label else ""

        return f"""
        {label_html}
        <div class="mobile-progress">
            <div class="mobile-progress-bar" style="width: {progress_percent}%"></div>
        </div>
        """


# Utility functions for design system
def get_mobile_design_system() -> MobileDesignSystem:
    """Get or create mobile design system instance."""
    if "mobile_design_system" not in st.session_state:
        st.session_state.mobile_design_system = MobileDesignSystem()

    return st.session_state.mobile_design_system


def apply_mobile_component_styles() -> None:
    """Apply mobile component styles to the current page."""
    design_system = get_mobile_design_system()
    # Styles are automatically applied during initialization


def create_mobile_button(text: str, variant: str = "primary", size: str = "md", full_width: bool = False, key: str | None = None) -> bool:
    """Create a Streamlit button with mobile styling."""
    # This would integrate with Streamlit's button component
    # For now, return a placeholder
    return st.button(text, key=key, help=f"Mobile-optimized {variant} button", use_container_width=full_width)
