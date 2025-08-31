from collections.abc import Generator
from typing import Any, Dict, List, Optional, Tuple, Union

"""PlantGuard Core Module.

This module contains the core components for the PlantGuard multimodal
plant disease detection system.
"""


__version__ = "0.1.0"
__author__ = "PlantGuard Team"

from .audio import AudioAdapter
from .nlp import TextAdapter
from .vision import VisionAdapter

__all__ = ["AudioAdapter", "TextAdapter", "VisionAdapter"]
