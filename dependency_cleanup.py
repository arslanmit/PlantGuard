#!/usr/bin/env python3
"""
Dependency Cleanup Script for Mobile PlantGuard

Analyzes and removes unused dependencies to optimize mobile performance.
"""

from pathlib import Path


def analyze_unused_dependencies():
    """Analyze and suggest unused dependencies for removal."""

    # Read current requirements
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return

    with open(requirements_file) as f:
        lines = f.readlines()

    # Packages that are likely unused after desktop removal
    potentially_unused = [
        "pyngrok",  # Only needed for external access, not core mobile
        "pycloudflared",  # Alternative tunneling, not essential
        "sphinx",  # Documentation generation
        "sphinx-rtd-theme",  # Documentation theme
        "bandit",  # Security scanning (dev tool)
        "safety",  # Security checking (dev tool)
        "pre-commit",  # Git hooks (dev tool)
    ]

    # Keep essential packages for mobile
    essential_mobile = [
        "torch",
        "torchvision",
        "torchaudio",
        "torchmetrics",
        "numpy",
        "pandas",
        "scikit-learn",
        "opencv-python-headless",
        "Pillow",
        "transformers",
        "accelerate",
        "datasets",
        "huggingface-hub",
        "librosa",
        "soundfile",
        "openai-whisper",
        "streamlit",
        "streamlit-webrtc",
        "streamlit-option-menu",
        "plotly",
        "python-dotenv",
        "tensorboard",
        "psutil",
    ]

    print("🔍 Dependency Analysis:")
    print(f"  • Total packages in requirements.txt: {len([l for l in lines if l.strip() and not l.startswith('#')])}")
    print(f"  • Essential mobile packages: {len(essential_mobile)}")
    print(f"  • Potentially unused packages: {len(potentially_unused)}")

    return potentially_unused


if __name__ == "__main__":
    unused = analyze_unused_dependencies()
    print("\n💡 Consider removing these packages for mobile optimization:")
    for pkg in unused:
        print(f"  - {pkg}")
