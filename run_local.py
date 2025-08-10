#!/usr/bin/env python3
"""
Local development runner for PlantGuard
Usage: python run_local.py
"""

import subprocess  # nosec B404
import sys


def check_requirements() -> bool:
    """Check if requirements are installed"""
    try:
        import streamlit  # noqa: F401
        import torch  # noqa: F401
        import transformers  # noqa: F401

        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please install requirements: pip install -r requirements-colab.txt")
        return False


def run_streamlit() -> bool:
    """Run Streamlit app"""
    if not check_requirements():
        return False

    print("🚀 Starting PlantGuard Streamlit app...")
    print("📱 Open http://localhost:8501 in your browser")
    print("🎙️ For microphone support, use HTTPS (ngrok/cloudflare)")

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
        print("\n👋 PlantGuard stopped")
    except Exception as e:
        print(f"❌ Error running Streamlit: {e}")
        return False

    return True


if __name__ == "__main__":
    run_streamlit()
