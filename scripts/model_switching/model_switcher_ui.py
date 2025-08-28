#!/usr/bin/env python3
"""Simple Streamlit UI for switching between PlantGuard models."""

import sys
from pathlib import Path

import streamlit as st
from PIL import Image

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.features.model_switching.model_manager import PlantGuardModelManager


@st.cache_resource
def get_model_manager() -> "PlantGuardModelManager":
    """Get cached model manager instance without autoload to render UI fast."""
    return PlantGuardModelManager(autoload_default=False)


def process_image(image: Image.Image, image_name: str, manager: "PlantGuardModelManager", current_model_info: dict) -> None:
    """Process an image and display results."""
    # Display image
    st.image(image, caption=f"Testing: {image_name}", use_container_width=True)

    # Get prediction
    if "error" not in current_model_info:
        with st.spinner("Analyzing image..."):
            result = manager.get_readable_prediction(image)

        # Display results
        st.markdown("### [DETAILS] Prediction Results")

        col_a, col_b = st.columns(2)

        with col_a:
            st.metric("[LEAF] Plant Type", result["plant_type"])
            st.metric("[VIRUS] Disease", result["disease"])

        with col_b:
            st.metric("[SUMMARY] Confidence", result["confidence_percentage"])
            health_status = "Healthy [DONE]" if result["is_healthy"] else "Diseased [WARNING]"
            st.metric("[HEALTHY] Health Status", health_status)

        # Additional info
        st.info(f"[TIP] **Recommendation:** {result['recommendation']}")

        # Raw prediction details
        with st.expander("[TOOL] Technical Details"):
            st.json(
                {
                    "raw_prediction": result["raw_prediction"],
                    "confidence_score": result["confidence"],
                    "model_info": result["model_info"],
                }
            )

        # Show model info
        st.markdown("### [AI] Model Information")
        st.write(f"**Model:** {current_model_info['name']}")
        st.write(f"**Type:** {current_model_info['type']}")
        if current_model_info.get("description"):
            st.write(f"**Description:** {current_model_info['description']}")

    else:
        st.error(f"[TODO] Model Error: {current_model_info['error']}")


def main() -> None:
    """Main Streamlit app."""
    st.set_page_config(page_title="PlantGuard Model Switcher", page_icon="[PLANT]", layout="wide")

    st.title("[PLANT] PlantGuard Model Switcher")
    st.markdown("Easy switching between different plant disease detection models")

    # Initialize model manager
    try:
        manager = get_model_manager()
    except Exception as e:
        st.error(f"Failed to initialize model manager: {e}")
        return

    # Sidebar for model selection
    st.sidebar.header("[AI] Model Selection")

    # Get available models
    models = manager.list_available_models()
    enabled_models = [m for m in models if m["enabled"]]

    if not enabled_models:
        st.sidebar.error("No enabled models found")
        return

    # Model selection dropdown
    model_options = {f"{m['name']} ({m['accuracy']:.1%})": m["id"] for m in enabled_models}

    current_model_info = manager.get_current_model_info()
    _current_model_name = current_model_info.get("name", "None")

    # Find current selection
    default_index = 0
    for i, (_display_name, model_id) in enumerate(model_options.items()):
        if model_id == current_model_info.get("model_id", "").split("/")[-1]:
            default_index = i
            break

    selected_display = st.sidebar.selectbox(
        "Choose Model:",
        options=list(model_options.keys()),
        index=default_index,
        help="Select a model to switch to",
    )

    selected_model_id = model_options[selected_display]

    # Switch model button (sidebar)
    if st.sidebar.button("[PARTIAL] Switch Model", type="primary"):
        with st.spinner(f"Loading model: {selected_model_id}"):
            if manager.switch_model(selected_model_id):
                st.sidebar.success(f"[DONE] Switched to: {selected_model_id}")
                st.rerun()
            else:
                st.sidebar.error(f"[TODO] Failed to switch to: {selected_model_id}")

    # Current model info
    st.sidebar.markdown("---")
    st.sidebar.subheader("[SUMMARY] Current Model")

    if "error" not in current_model_info:
        st.sidebar.info(f"""
        **Name:** {current_model_info["name"]}

        **Type:** {current_model_info["type"]}

        **Accuracy:** {current_model_info["accuracy"]:.1%}

        **Classes:** {current_model_info["num_classes"]}

        **Device:** {current_model_info["device"]}
        """)
    else:
        st.sidebar.warning("No model loaded")

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("[SEARCH] Test Current Model")

        # Central switch button mirrors sidebar for convenience
        if st.button("[PARTIAL] Switch Model", help="Load the selected model from the sidebar"):
            with st.spinner(f"Loading model: {selected_model_id}"):
                if manager.switch_model(selected_model_id):
                    st.success(f"[DONE] Switched to: {selected_model_id}")
                    st.rerun()
                else:
                    st.error(f"[TODO] Failed to switch to: {selected_model_id}")

        # Image upload
        uploaded_file = st.file_uploader(
            "Upload plant image",
            type=["jpg", "jpeg", "png"],
            help="Upload an image of a plant leaf to test the current model",
        )

        # Sample image selection disabled
        st.markdown("**Sample image selection disabled.** Use the upload control to test your own images.")

        # Process uploaded image
        if uploaded_file is not None:
            try:
                # Load image
                image = Image.open(uploaded_file)
                image_name = uploaded_file.name

                # Process the uploaded image
                process_image(image, image_name, manager, current_model_info)

            except Exception as e:
                st.error(f"Error processing image: {e}")

    with col2:
        st.header("[SUMMARY] Model Comparison")

        # Show all models in a table
        if models:
            model_data = []
            for model in models:
                status = "[GREEN] Current" if model["is_current"] else "⚪ Available" if model["enabled"] else "[RED] Disabled"
                model_data.append(
                    {
                        "Model": model["name"],
                        "Type": model["type"],
                        "Accuracy": f"{model['accuracy']:.1%}" if model["accuracy"] > 0 else "Unknown",
                        "Status": status,
                    }
                )

            st.dataframe(model_data, use_container_width=True)

            # Model configuration
            st.markdown("---")
            st.subheader("⚙️ Configuration")

            if st.button("[WRITE] Edit Model Config"):
                st.info("Model configuration file: `config/models.json`")
                st.markdown("""
                You can edit the configuration file to:
                - Add new models
                - Change model settings
                - Enable/disable models
                - Set confidence thresholds
                """)


if __name__ == "__main__":
    main()
