#!/usr/bin/env python3
"""
PlantGuard application runner
Usage: python run_local.py
"""

import logging
import subprocess  # nosec B404
import sys

# Configure logging instead of print statements
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def check_requirements() -> bool:
    """Check if requirements are installed"""
    try:
        import streamlit  # noqa: F401, PLC0415
        import torch  # noqa: F401, PLC0415
        import transformers  # noqa: F401, PLC0415
    except ImportError:
        logger.exception("❌ Missing dependencies")
        logger.exception("Please install requirements: pip install -r requirements.txt")
        return False
    else:
        logger.info("✅ Core dependencies found")
        return True


def run_streamlit() -> bool:
    """Run Streamlit app"""
    if not check_requirements():
        return False

    logger.info("🚀 Starting PlantGuard Streamlit app...")
    logger.info("📱 Open http://localhost:8501 in your browser")
    logger.info("🎙️ For microphone support, use HTTPS (ngrok/cloudflare)")

    try:
        subprocess.run(  # nosec B603
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "src/ui/app_streamlit.py",
                "--server.port",
                "8501",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        logger.info("\n👋 PlantGuard stopped")
        return True
    except subprocess.CalledProcessError:
        logger.exception("❌ Error running Streamlit")
        return False

    return True


if __name__ == "__main__":
    run_streamlit()
