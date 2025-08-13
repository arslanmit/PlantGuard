"""PlantGuard - Multimodal Plant Disease Detection System with Model Switching.

Enhanced main Streamlit application with easy model switching capabilities.
"""

import sys
from pathlib import Path

import streamlit as st
from PIL import Image

# Add project src to path (repo root / src)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from src.core.model_manager import PlantGuardModelManager
from src.utils.logging import setup_logger

# Configure logging
logger = setup_logger("plantguard", log_file="logs/app.log")


@st.cache_resource
def get_model_manager() -> "PlantGuardModelManager":
    """Get cached model manager instance without autoload to render UI fast."""
    return PlantGuardModelManager(autoload_default=False)


def main() -> None:
    """Main PlantGuard application with model switching."""
    st.set_page_config(
        page_title="PlantGuard - Plant Disease Detection",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Header
    st.title("🌱 PlantGuard")
    st.markdown("**Multimodal Plant Disease Detection System**")

    # Initialize model manager
    try:
        manager = get_model_manager()
    except Exception as e:
        st.error(f"Failed to initialize PlantGuard: {e}")
        st.stop()

    # Sidebar - Model Selection
    with st.sidebar:
        st.header("🤖 Model Selection")

        # Get available models
        models = manager.list_available_models()
        enabled_models = [m for m in models if m["enabled"]]

        if not enabled_models:
            st.error("No models available")
            st.stop()

        # Model selection
        model_options = {}
        current_model_info = manager.get_current_model_info()

        for model in enabled_models:
            display_name = f"{model['name']} ({model['accuracy']:.1%})"
            model_options[display_name] = model["id"]

        # Find current selection
        default_index = 0
        if "error" not in current_model_info:
            for i, (_, model_id) in enumerate(model_options.items()):
                if model_id in current_model_info.get("model_id", ""):
                    default_index = i
                    break

        selected_display = st.selectbox(
            "Choose Model:",
            options=list(model_options.keys()),
            index=default_index,
            help="Select a model for plant disease detection",
        )

        selected_model_id = model_options[selected_display]

        # Auto-switch if different model selected
        is_error = "error" in current_model_info
        is_different = selected_model_id not in current_model_info.get("model_id", "")
        if is_error or is_different:
            with st.spinner(f"Loading {selected_model_id}..."):
                if manager.switch_model(selected_model_id):
                    st.success(f"✅ Loaded: {selected_model_id}")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to load: {selected_model_id}")

        # Current model info
        st.markdown("---")
        st.subheader("📊 Current Model")

        current_model_info = manager.get_current_model_info()
        if "error" not in current_model_info:
            st.info(f"""
            **{current_model_info["name"]}**

            Type: {current_model_info["type"]}

            Accuracy: {current_model_info["accuracy"]:.1%}

            Classes: {current_model_info["num_classes"]}

            Device: {current_model_info["device"]}
            """)
        else:
            st.warning("No model loaded")

        # Quick model comparison
        st.markdown("---")
        st.subheader("⚡ Quick Actions")

        if st.button("🔄 Switch to Best Model") and manager.switch_model("vit_best"):
            st.success("Switched to Vision Transformer")
            st.rerun()

        if st.button("🚀 Switch to Fast Model") and manager.switch_model("mobilenet_fast"):
            st.success("Switched to MobileNet")
            st.rerun()

    # Main content area
    tab1, tab2, tab3 = st.tabs(["🔍 Detection", "📊 Batch Analysis", "⚙️ Settings"])

    with tab1:
        st.header("🔍 Plant Disease Detection")

        # Image input methods
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📸 Upload Image")

            uploaded_file = st.file_uploader(
                "Choose a plant image",
                type=["jpg", "jpeg", "png"],
                help="Upload a clear image of a plant leaf",
            )

            # Sample images
            st.subheader("🖼️ Or Try Sample Images")

            sample_images = list(Path("data/pictures").glob("*.jpg"))
            if sample_images:
                sample_cols = st.columns(3)

                for i, img_path in enumerate(sample_images[:6]):  # Show first 6
                    with sample_cols[i % 3]:
                        try:
                            img = Image.open(img_path)
                            st.image(img, caption=img_path.name, use_column_width=True)

                            if st.button("Analyze", key=f"sample_{i}"):
                                # Convert Path to file-like object for processing
                                with open(img_path, "rb") as f:
                                    image_bytes = f.read()
                                # Process the image directly
                                img_for_analysis = Image.open(img_path)
                        except Exception as e:
                            st.warning(f"Could not load image {img_path}: {e}")
                            continue

        with col2:
            st.subheader("📋 Results")

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
                    st.image(image, caption=f"Analyzing: {image_name}", use_column_width=True)

                    # Get prediction
                    if "error" not in current_model_info:
                        with st.spinner("🔍 Analyzing plant..."):
                            result = manager.get_readable_prediction(image)

                        # Display results with styling
                        st.markdown("### 🎯 Detection Results")

                        # Main results
                        st.metric("🌿 Plant Type", result["plant_type"])
                        st.metric("🦠 Disease", result["disease"])
                        st.metric("📊 Confidence", result["confidence_percentage"])

                        # Health status with color coding
                        if result["is_healthy"]:
                            st.success("💚 Plant is Healthy!")
                        else:
                            st.warning("⚠️ Disease Detected")

                        # Recommendation
                        st.info(f"💡 {result['recommendation']}")

                        # Model info
                        st.caption(f"🤖 Analyzed by: {result['model_info']['model_name']}")

                        # Detailed results in expander
                        with st.expander("🔧 Technical Details"):
                            st.json(
                                {
                                    "raw_prediction": result["raw_prediction"],
                                    "confidence_score": result["confidence"],
                                    "model_details": result["model_info"],
                                }
                            )

                    else:
                        st.error("❌ No model loaded")

                except Exception as e:
                    st.error(f"Error analyzing image: {e}")

            else:
                st.info("👆 Upload an image or select a sample to start detection")

    with tab2:
        st.header("📊 Batch Analysis")
        st.markdown("Analyze multiple images at once")

        # Multiple file upload
        uploaded_files = st.file_uploader(
            "Upload multiple plant images",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload multiple images for batch analysis",
        )

        if uploaded_files:
            st.subheader(f"📋 Analyzing {len(uploaded_files)} images")

            if "error" not in current_model_info:
                progress_bar = st.progress(0)
                results_container = st.container()

                batch_results = []

                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        image = Image.open(uploaded_file)
                        result = manager.get_readable_prediction(image)

                        batch_results.append(
                            {
                                "Image": uploaded_file.name,
                                "Plant": result["plant_type"],
                                "Disease": result["disease"],
                                "Healthy": "Yes" if result["is_healthy"] else "No",
                                "Confidence": result["confidence_percentage"],
                            }
                        )

                        progress_bar.progress((i + 1) / len(uploaded_files))

                    except Exception as e:
                        batch_results.append(
                            {
                                "Image": uploaded_file.name,
                                "Plant": "Error",
                                "Disease": str(e),
                                "Healthy": "Unknown",
                                "Confidence": "0%",
                            }
                        )

                # Display results table
                with results_container:
                    st.dataframe(batch_results, use_container_width=True)

                    # Summary statistics
                    healthy_count = sum(1 for r in batch_results if r["Healthy"] == "Yes")
                    diseased_count = len(batch_results) - healthy_count

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Images", len(batch_results))
                    with col2:
                        st.metric("Healthy Plants", healthy_count)
                    with col3:
                        st.metric("Diseased Plants", diseased_count)

            else:
                st.error("❌ No model loaded for batch analysis")

    with tab3:
        st.header("⚙️ Settings & Configuration")

        # Model comparison
        st.subheader("🏆 Model Comparison")

        if models:
            model_data = []
            for model in models:
                status_icon = "🟢" if model["is_current"] else "⚪" if model["enabled"] else "🔴"
                model_data.append(
                    {
                        "Status": status_icon,
                        "Model": model["name"],
                        "Type": model["type"],
                        "Accuracy": f"{model['accuracy']:.1%}"
                        if model["accuracy"] > 0
                        else "Unknown",
                        "Description": model["description"],
                    }
                )

            st.dataframe(model_data, use_container_width=True)

        # Configuration info
        st.subheader("📝 Configuration")
        st.info("""
        **Model Configuration File:** `config/models.json`

        You can edit this file to:
        - Add new models from Hugging Face
        - Adjust confidence thresholds
        - Enable/disable models
        - Change default model
        """)

        # System info
        st.subheader("💻 System Information")
        if "error" not in current_model_info:
            st.code(f"""
Device: {current_model_info["device"]}
Model Type: {current_model_info["type"]}
Classes: {current_model_info["num_classes"]}
Configuration: config/models.json
            """)

        # Quick benchmark
        if st.button("🏁 Run Quick Benchmark"):
            with st.spinner("Benchmarking models..."):
                # This would run the benchmark from model_switcher.py
                st.info(
                    "Benchmark feature - run `python scripts/model_switching/model_switcher.py --benchmark` in terminal"
                )


if __name__ == "__main__":
    logger.info("Starting PlantGuard application with Model Manager")
    main()
