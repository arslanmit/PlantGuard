from typing import Any, Dict, List, Optional, Tuple, Union, Generator

from src.core.vision import VisionAdapter


def test_vision_adapter_get_model_info() -> None:
    """Unit test: ensure VisionAdapter exposes get_model_info (token: model_loading)."""
    adapter = VisionAdapter(model_path=None, lazy_load=True)
    info = adapter.get_model_info()
    # Basic assertions to exercise the API without heavy dependencies
    assert isinstance(info, dict)
    assert "is_loaded" in info
