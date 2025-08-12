#!/usr/bin/env python3
"""Simple Streamlit UI for switching between PlantGuard models."""

import json
import sys
from pathlib import Path

import streamlit as st
from PIL import Image

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from src.core.model_manager import PlantGuardModelManager


@st.cache_resource
def get_model_manager():
    """Get cached model manager instance without autoload to render UI fast."""
    return PlantGuardModelManager(autoload_default=False)


def main():
    """Main Streamlit app."""
    st.set_page_config(page_title="PlantGuard Model Switcher", page_icon="🌱", layout="wide")

    st.title("🌱 PlantGuard Model Switcher")
    st.markdown("Easy switching between different plant disease detection models")

    # Initialize model manager
    try:
        manager = get_model_manager()
    except Exception as e:
        st.error(f"Failed to initialize model manager: {e}")
        return

    # Sidebar for model selection
    st.sidebar.header("🤖 Model Selection")

    # Get available models
    models = manager.list_available_models()
    enabled_models = [m for m in models if m["enabled"]]

    if not enabled_models:
        st.sidebar.error("No enabled models found")
        return

    # Model selection dropdown
    model_options = {f"{m['name']} ({m['accuracy']:.1%})": m["id"] for m in enabled_models}

    current_model_info = manager.get_current_model_info()
    current_model_name = current_model_info.get("name", "None")

    # Find current selection
    default_index = 0
    for i, (display_name, model_id) in enumerate(model_options.items()):
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
    if st.sidebar.button("🔄 Switch Model", type="primary"):
        with st.spinner(f"Loading model: {selected_model_id}"):
            if manager.switch_model(selected_model_id):
                st.sidebar.success(f"✅ Switched to: {selected_model_id}")
                st.rerun()
            else:
                st.sidebar.error(f"❌ Failed to switch to: {selected_model_id}")

    # Current model info
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Current Model")

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
        st.header("🔍 Test Current Model")

        # Central switch button mirrors sidebar for convenience
        if st.button("🔄 Switch Model", help="Load the selected model from the sidebar"):
            with st.spinner(f"Loading model: {selected_model_id}"):
                if manager.switch_model(selected_model_id):
                    st.success(f"✅ Switched to: {selected_model_id}")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to switch to: {selected_model_id}")

        # Image upload
        uploaded_file = st.file_uploader(
            "Upload plant image",
            type=["jpg", "jpeg", "png"],
            help="Upload an image of a plant leaf to test the current model",
        )

        # Sample image selection
        st.markdown("**Or choose a sample image:**")

        sample_images = list(Path("data/pictures").glob("*.jpg"))
        if sample_images:
            sample_names = [img.name for img in sample_images]
            selected_sample = st.selectbox(
                "Sample images:",
                options=["None"] + sample_names,
                help="Select a sample image for testing",
            )

            if selected_sample != "None":
                sample_path = Path("data/pictures") / selected_sample
                if sample_path.exists():
                    uploaded_file = sample_path

        # Process image
        if uploaded_file is not None:
            try:
                # Load image
                if isinstance(uploaded_file, Path):
                    image = Image.open(uploaded_file)
                    image_name = uploaded_file.name
                else:
                    image = Image.open(uploaded_file)
                    image_name = uploaded_file.name

                # Display image
                st.image(image, caption=f"Testing: {image_name}", use_column_width=True)

                # Get prediction
                if "error" not in current_model_info:
                    with st.spinner("Analyzing image..."):
                        result = manager.get_readable_prediction(image)

                    # Display results
                    st.markdown("### 📋 Prediction Results")

                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.metric("🌿 Plant Type", result["plant_type"])
                        st.metric("🦠 Disease", result["disease"])

                    with col_b:
                        st.metric("📊 Confidence", result["confidence_percentage"])

                        health_status = "Healthy ✅" if result["is_healthy"] else "Diseased ⚠️"
                        st.metric("💚 Health Status", health_status)

                    # Additional info
                    st.info(f"💡 **Recommendation:** {result['recommendation']}")

                    # Raw prediction details
                    with st.expander("🔧 Technical Details"):
                        st.json(
                            {
                                "raw_prediction": result["raw_prediction"],
                                "confidence_score": result["confidence"],
                                "model_info": result["model_info"],
                            }
                        )

                else:
                    st.error("No model loaded for prediction")

            except Exception as e:
                st.error(f"Error processing image: {e}")

    with col2:
        st.header("📊 Model Comparison")

        # Show all models in a table
        if models:
            model_data = []
            for model in models:
                status = (
                    "🟢 Current"
                    if model["is_current"]
                    else "⚪ Available"
                    if model["enabled"]
                    else "🔴 Disabled"
                )
                model_data.append(
                    {
                        "Model": model["name"],
                        "Type": model["type"],
                        "Accuracy": f"{model['accuracy']:.1%}"
                        if model["accuracy"] > 0
                        else "Unknown",
                        "Status": status,
                    }
                )

            st.dataframe(model_data, use_container_width=True)

        # Quick benchmark button
        if st.button("🏁 Quick Benchmark", help="Test all enabled models on sample images"):
            with st.spinner("Running benchmark..."):
                # Load test metadata
                metadata_path = "data/pictures/sample_images_metadata.json"
                if Path(metadata_path).exists():
                    with open(metadata_path) as f:
                        metadata = json.load(f)

                    benchmark_results = []

                    for model_info in enabled_models[:3]:  # Limit to 3 models for speed
                        model_id = model_info["id"]

                        if manager.switch_model(model_id):
                            correct = 0
                            total = 0

                            # Test on first 3 images for speed
                            for sample in metadata["sample_images"][:3]:
                                image_path = Path("data/pictures") / sample["filename"]

                                if image_path.exists():
                                    try:
                                        image = Image.open(image_path)
                                        result = manager.get_readable_prediction(image)

                                        # Simple accuracy check
                                        gt_plant = sample["plant"].lower()
                                        pred_plant = result["plant_type"].lower()

                                        if gt_plant in pred_plant or pred_plant in gt_plant:
                                            correct += 1

                                        total += 1

                                    except Exception:
                                        continue

                            if total > 0:
                                accuracy = correct / total
                                benchmark_results.append(
                                    {
                                        "Model": model_info["name"],
                                        "Accuracy": f"{accuracy:.1%}",
                                        "Tested": f"{correct}/{total}",
                                    }
                                )

                    if benchmark_results:
                        st.markdown("### 🏆 Benchmark Results")
                        st.dataframe(benchmark_results, use_container_width=True)
                    else:
                        st.warning("No benchmark results available")
                else:
                    st.error("Test metadata not found")

        # Model configuration
        st.markdown("---")
        st.subheader("⚙️ Configuration")

        if st.button("📝 Edit Model Config"):
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
