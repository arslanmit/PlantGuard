"""PlantGuard - Multimodal Plant Disease Detection System.

Main Streamlit application entry point.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import after path setup
from src.ui.app import main  # noqa: E402
from src.utils.logging import setup_logger  # noqa: E402

# Configure logging
logger = setup_logger("plantguard", log_file="logs/app.log")

if __name__ == "__main__":
    logger.info("Starting PlantGuard application")
    main()
