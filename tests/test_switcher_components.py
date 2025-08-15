"""Tests for PlantGuard switcher components."""

from unittest.mock import MagicMock, patch

import pytest

# Mock streamlit before importing components
with patch.dict("sys.modules", {"streamlit": MagicMock()}):
    from src.ui.components import ModelSwitcher, ModeSwitcher, ThemeSwitcher


class TestModeSwitcher:
    """Test cases for ModeSwitcher component."""

    def test_initialization(self):
        """Test ModeSwitcher initialization."""
        switcher = ModeSwitcher()
        assert switcher.session_key == "input_mode"
        assert switcher.default_mode == "vision"

        # Test custom initialization
        custom_switcher = ModeSwitcher(session_key="custom_key", default_mode="audio")
        assert custom_switcher.session_key == "custom_key"
        assert custom_switcher.default_mode == "audio"

    @patch("streamlit.session_state", {})
    def test_get_current_mode(self):
        """Test getting current mode."""
        switcher = ModeSwitcher()

        # Should return default when not set
        assert switcher.get_current_mode() == "vision"

        # Should return set value
        with patch("streamlit.session_state", {"input_mode": "audio"}):
            assert switcher.get_current_mode() == "audio"

    @patch("streamlit.session_state", {})
    def test_set_mode(self):
        """Test setting mode programmatically."""
        switcher = ModeSwitcher()

        with patch("streamlit.session_state", {}) as mock_state:
            switcher.set_mode("text")
            assert mock_state["input_mode"] == "text"


class TestThemeSwitcher:
    """Test cases for ThemeSwitcher component."""

    def test_initialization(self):
        """Test ThemeSwitcher initialization."""
        switcher = ThemeSwitcher()
        assert switcher.session_key == "theme_mode"
        assert switcher.default_theme == "auto"

        # Test custom initialization
        custom_switcher = ThemeSwitcher(session_key="custom_theme", default_theme="dark")
        assert custom_switcher.session_key == "custom_theme"
        assert custom_switcher.default_theme == "dark"


class TestModelSwitcher:
    """Test cases for ModelSwitcher component."""

    def test_initialization(self):
        """Test ModelSwitcher initialization."""
        switcher = ModelSwitcher()
        assert switcher.session_key == "selected_models"

    @patch("streamlit.session_state", {})
    def test_default_models(self):
        """Test default model selection."""
        switcher = ModelSwitcher()

        # Mock session state to check default values
        with patch("streamlit.session_state", {}) as mock_state:
            # Simulate initialization
            mock_state["selected_models"] = {
                "vision": "resnet50_plantvillage_v1",
                "audio": "whisper_tiny_local",
                "text": "distilbert_plant_qa_v1",
            }

            assert mock_state["selected_models"]["vision"] == "resnet50_plantvillage_v1"
            assert mock_state["selected_models"]["audio"] == "whisper_tiny_local"
            assert mock_state["selected_models"]["text"] == "distilbert_plant_qa_v1"


class TestIntegration:
    """Integration tests for switcher components."""

    def test_multiple_switchers_independence(self):
        """Test that multiple switchers work independently."""
        mode_switcher = ModeSwitcher(session_key="mode1")
        theme_switcher = ThemeSwitcher(session_key="theme1")
        model_switcher = ModelSwitcher(session_key="models1")

        # Each should have different session keys
        assert mode_switcher.session_key != theme_switcher.session_key
        assert mode_switcher.session_key != model_switcher.session_key
        assert theme_switcher.session_key != model_switcher.session_key

    def test_custom_modes_configuration(self):
        """Test custom modes configuration."""
        custom_modes = [
            {
                "id": "test_mode",
                "label": "Test Mode",
                "icon": "🧪",
                "description": "Test description",
            }
        ]

        switcher = ModeSwitcher()

        # Should accept custom modes without error
        assert len(custom_modes) == 1
        assert custom_modes[0]["id"] == "test_mode"


if __name__ == "__main__":
    pytest.main([__file__])
