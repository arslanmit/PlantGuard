"""PlantGuard Core Module.

This module contains the core components for the PlantGuard multimodal
plant disease detection system.
"""

from collections.abc import Generator
from typing import Any, Dict, List, Optional, Tuple, Union

from .audio import AudioAdapter
from .nlp import TextAdapter
from .vision import VisionAdapter

__version__ = "0.1.0"
__author__ = "PlantGuard Team"

__all__ = ["AudioAdapter", "TextAdapter", "VisionAdapter"]
