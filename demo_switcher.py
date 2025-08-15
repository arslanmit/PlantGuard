#!/usr/bin/env python3
"""Demo script to test the PlantGuard switcher functionality."""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import streamlit as st

from src.ui.components import ModelSwitcher, ModeSwitcher, ThemeSwitcher


def main() -> None:
    """Demo application for testing switchers."""
    st.set_page_config(page_title="🔄 PlantGuard Switcher Demo", page_icon="🔄", layout="wide")

    st.title("🔄 PlantGuard Switcher Demo")
    st.markdown("Test the different switcher components for PlantGuard")

    # Mode Switcher Demo
    st.markdown("## 1. Mode Switcher")
    mode_switcher = ModeSwitcher()
    selected_mode = mode_switcher.render()
    st.success(f"Selected mode: **{selected_mode}**")

    st.markdown("---")

    # Theme Switcher Demo
    st.markdown("## 2. Theme Switcher")
    theme_switcher = ThemeSwitcher()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Sidebar Style")
        with st.container():
            theme_switcher.render(location="sidebar")

    with col2:
        st.markdown("### Expander Style")
        theme_switcher.render(location="expander")

    st.markdown("---")

    # Model Switcher Demo
    st.markdown("## 3. Model Switcher")
    model_switcher = ModelSwitcher()

    available_models = {
        "vision": [
            "resnet50_plantvillage_v1",
            "efficientnet_b0_plants",
            "vit_base_plants",
            "mobilenet_v3_plants",
        ],
        "audio": ["whisper_tiny_local", "wav2vec2_plant_sounds", "hubert_plant_audio"],
        "text": [
            "distilbert_plant_qa_v1",
            "roberta_plant_care",
            "t5_small_plant_qa",
            "bert_base_plant_diseases",
        ],
    }

    selected_models = model_switcher.render(available_models)
    st.success(f"Selected models: {selected_models}")

    st.markdown("---")

    # Custom Mode Switcher Demo
    st.markdown("## 4. Custom Mode Switcher")
    custom_modes = [
        {
            "id": "diagnosis",
            "label": "Disease Diagnosis",
            "icon": "🔬",
            "description": "Analyze plant diseases from images",
        },
        {
            "id": "care",
            "label": "Plant Care",
            "icon": "🌱",
            "description": "Get care tips and recommendations",
        },
        {
            "id": "identification",
            "label": "Plant ID",
            "icon": "🏷️",
            "description": "Identify plant species",
        },
        {
            "id": "monitoring",
            "label": "Health Monitor",
            "icon": "📊",
            "description": "Track plant health over time",
        },
    ]

    custom_switcher = ModeSwitcher(session_key="custom_mode", default_mode="diagnosis")
    selected_custom = custom_switcher.render(modes=custom_modes, columns=2)
    st.success(f"Selected custom mode: **{selected_custom}**")

    # Show session state for debugging
    st.markdown("---")
    st.markdown("## Debug: Session State")
    with st.expander("View Session State"):
        st.json(dict(st.session_state))


if __name__ == "__main__":
    main()
