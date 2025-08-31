"""Configuration management for PlantGuard."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Generator


@dataclass
class Config:
    """Configuration class for PlantGuard system."""

    # Model paths
    vision_model_path: str = "data/models/plant_disease_resnet50.pth"
    knowledge_base_path: str = "data/knowledge_base/disease_info.json"
    whisper_model_name: str = "openai/whisper-tiny"

    # Data paths
    dataset_path: str = "data/PlantVillage"
    temp_dir: str = "data/tmp"
    logs_dir: str = "logs"

    # Model parameters
    num_classes: int = 38
    image_size: int = 224
    batch_size: int = 32
    confidence_threshold: float = 0.5

    # Audio parameters
    max_audio_duration: int = 60  # seconds
    supported_audio_formats: list[str] = field(default_factory=lambda: ["wav", "mp3", "m4a"])

    # Image parameters
    max_image_size: int = 200 * 1024 * 1024  # 200MB
    supported_image_formats: list[str] = field(default_factory=lambda: ["jpg", "jpeg", "png"])

    def __post_init__(self) -> None:
        """Initialize default values after dataclass creation."""
        # Default values are now handled by field(default_factory)
        # Create directories if they don't exist
        for path in [self.temp_dir, self.logs_dir]:
            Path(path).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            vision_model_path=os.getenv("VISION_MODEL_PATH", cls.vision_model_path),
            knowledge_base_path=os.getenv("KNOWLEDGE_BASE_PATH", cls.knowledge_base_path),
            whisper_model_name=os.getenv("WHISPER_MODEL_NAME", cls.whisper_model_name),
            dataset_path=os.getenv("DATASET_PATH", cls.dataset_path),
            temp_dir=os.getenv("TEMP_DIR", cls.temp_dir),
            logs_dir=os.getenv("LOGS_DIR", cls.logs_dir),
        )
