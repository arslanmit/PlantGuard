#!/usr/bin/env python3
"""Analyze which packages from requirements.txt are actually used in the codebase."""

import ast
import re
from pathlib import Path


def extract_imports_from_file(file_path: Path) -> set[str]:
    """Extract top-level package imports from a Python file."""
from typing import Any, Dict, List, Optional, Tuple, Union, Generator

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Parse AST to get imports
        tree = ast.parse(content)
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level package name
                    package = alias.name.split(".")[0]
                    imports.add(package)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level package name
                    package = node.module.split(".")[0]
                    imports.add(package)

        return imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return set()


def get_requirements_packages() -> set[str]:
    """Extract package names from requirements.txt."""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        return set()

    packages = set()
    with open(req_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract package name (before >= or == or other operators)
                package = re.split(r"[>=<!=]", line)[0].strip()
                # Handle package names with underscores/hyphens
                package = package.replace("-", "_").lower()
                packages.add(package)

    return packages


def main() -> None:
    """Main analysis function."""
    print("[INFO] Analyzing dependency usage...")

    # Get all Python files in the project
    python_files = []
    for pattern in ["*.py", "src/**/*.py"]:
        python_files.extend(Path().glob(pattern))

    # Extract all imports from all Python files
    all_imports = set()
    for py_file in python_files:
        if py_file.name.startswith("."):
            continue
        imports = extract_imports_from_file(py_file)
        all_imports.update(imports)

    # Get packages from requirements.txt
    required_packages = get_requirements_packages()

    # Map common import names to package names
    import_to_package = {
        "cv2": "opencv_python_headless",
        "PIL": "pillow",
        "sklearn": "scikit_learn",
        "yaml": "pyyaml",
        "torch": "torch",
        "torchvision": "torchvision",
        "torchaudio": "torchaudio",
        "transformers": "transformers",
        "streamlit": "streamlit",
        "librosa": "librosa",
        "whisper": "openai_whisper",
        "numpy": "numpy",
        "pandas": "pandas",
        "plotly": "plotly",
        "pytest": "pytest",
        "ruff": "ruff",
        "mypy": "mypy",
        "tensorboard": "tensorboard",
        "psutil": "psutil",
        "wandb": "wandb",
        "optuna": "optuna",
        "watchdog": "watchdog",
        "streamlit_webrtc": "streamlit_webrtc",
        "streamlit_option_menu": "streamlit_option_menu",
        "pycloudflared": "pycloudflared",
        "pyngrok": "pyngrok",
        "soundfile": "soundfile",
        "speech_recognition": "speechrecognition",
        "reportlab": "reportlab",
        "bandit": "bandit",
        "safety": "safety",
        "pre_commit": "pre_commit",
        "sphinx": "sphinx",
        "sphinx_rtd_theme": "sphinx_rtd_theme",
        "jupyter": "jupyter",
        "ipykernel": "ipykernel",
        "matplotlib": "matplotlib",
        "seaborn": "seaborn",
    }

    # Find used packages
    used_packages = set()
    for import_name in all_imports:
        package_name = import_to_package.get(import_name, import_name.lower())
        if package_name in required_packages:
            used_packages.add(package_name)

    # Find unused packages
    unused_packages = required_packages - used_packages

    print("\n[RESULTS] Analysis Results:")
    print(f"Total packages in requirements.txt: {len(required_packages)}")
    print(f"Used packages: {len(used_packages)}")
    print(f"Unused packages: {len(unused_packages)}")

    if unused_packages:
        print(f"\n[UNUSED] Unused packages ({len(unused_packages)}):")
        for pkg in sorted(unused_packages):
            print(f"  - {pkg}")

    print(f"\n[USED] Used packages ({len(used_packages)}):")
    for pkg in sorted(used_packages):
        print(f"  - {pkg}")


if __name__ == "__main__":
    main()
