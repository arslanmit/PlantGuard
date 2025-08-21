"""PlantGuard UI Components Package.

This package provides reusable UI components for the PlantGuard application,
including chat interface, voice interface, image interface, analysis cards,
comparison view, history management, navigation, input ribbon, mobile gesture support,
model switching, and status indicators.
"""

from .analysis_card import AnalysisCard, AnalysisResult, create_analysis_card
from .chat_interface import ChatInterface, ChatMessage, create_chat_interface
from .compare_view import CompareView, ComparisonResult, create_compare_view
from .gesture_handler import GestureHandler, create_gesture_handler
from .history_manager import HistoryEntry, HistoryManager, create_history_manager
from .image_interface import ImageInterface, create_image_interface
from .input_ribbon import InputRibbon
from .interface_toggle import InterfaceToggle, create_interface_toggle
from .model_switcher import ModelSwitcher
from .navigation import NavigationHeader, NavigationSidebar
from .status_indicator import render_status_indicator
from .voice_interface import VoiceInterface, create_voice_interface

__all__ = [
    "AnalysisCard",
    "AnalysisResult",
    "ChatInterface",
    "ChatMessage",
    "CompareView",
    "ComparisonResult",
    "GestureHandler",
    "HistoryEntry",
    "HistoryManager",
    "ImageInterface",
    "InputRibbon",
    "InterfaceToggle",
    "ModelSwitcher",
    "NavigationHeader",
    "NavigationSidebar",
    "VoiceInterface",
    "create_analysis_card",
    "create_chat_interface",
    "create_compare_view",
    "create_gesture_handler",
    "create_history_manager",
    "create_image_interface",
    "create_interface_toggle",
    "create_voice_interface",
    "render_status_indicator",
]
