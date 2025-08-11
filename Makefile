# ========== PlantGuard Makefile ==========
# Streamlined workflow for PlantGuard multimodal plant disease detection
SHELL := /bin/bash
PY      := .venv/bin/python
PIP     := $(PY) -m pip
RUFF    := $(PY) -m ruff
MYPY    := $(PY) -m mypy
PYTEST  := $(PY) -m pytest
JUPYTER := $(PY) -m jupyter

# Project paths
SRC_DIR := src
DATA_DIR := data
NOTEBOOKS_DIR := notebooks
RUNS_DIR := runs

.DEFAULT_GOAL := qa

.PHONY: help setup venv deps fmt lint type test qa clean
.PHONY: install run notebook tensorboard train-models quick

help:
	@echo "========== PlantGuard Commands =========="
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  setup      - Complete environment setup"
	@echo "  run        - Launch PlantGuard Streamlit app"
	@echo "  quick      - Fast format + lint"
	@echo ""
	@echo "🔧 Environment:"
	@echo "  setup      - Complete environment setup"
	@echo ""
	@echo "✅ Code Quality:"
	@echo "  fmt        - Auto-fix and format code (Ruff)"
	@echo "  lint       - Lint code (Ruff)"
	@echo "  type       - Type check (Mypy)"
	@echo "  test       - Run tests with coverage"
	@echo "  qa         - Full quality assurance (fmt→lint→type→test)"
	@echo ""
	@echo "🤖 ML Pipeline:"
	@echo "  train-models    - Train all PlantGuard models"
	@echo "  tensorboard     - Launch TensorBoard for training metrics"
	@echo "  notebook        - Open Jupyter notebook"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean      - Remove caches and temporary files"

# ========== Environment Setup ==========
venv:
	@echo "🔧 Creating virtual environment..."
	@[ -x $(PY) ] || python3 -m venv .venv
	@$(PIP) install --upgrade pip setuptools wheel
	@echo "✅ Virtual environment ready"

deps: venv
	@echo "📦 Installing runtime dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "✅ Runtime dependencies installed"

install: deps
	@echo "🔧 Installing PlantGuard in editable mode..."
	@$(PIP) install -e . --no-deps --quiet --disable-pip-version-check
	@echo "✅ PlantGuard installed"

setup: deps install
	@echo "🎉 Environment setup complete!"
	@echo "Run 'make run' to start PlantGuard"

# ========== Application Execution ==========
run: deps
	@echo "🚀 Starting PlantGuard Streamlit app..."
	@$(PY) run_local.py

notebook: deps
	@echo "📓 Opening PlantGuard Jupyter notebook..."
	@$(PIP) install -q jupyter >/dev/null 2>&1 || true
	@$(JUPYTER) notebook $(NOTEBOOKS_DIR)/PlantGuard.ipynb

# ========== Code Quality & Testing ==========
fmt: 
	@echo "🎨 Formatting code with Ruff..."
	@if [ ! -x $(PY) ]; then $(MAKE) venv; fi
	@$(PIP) install -q ruff >/dev/null 2>&1 || true
	@$(RUFF) check --fix . --quiet
	@$(RUFF) format . --quiet
	@echo "✅ Code formatted"

lint:
	@echo "🔍 Linting code with Ruff..."
	@if [ ! -x $(PY) ]; then $(MAKE) venv; fi
	@$(PIP) install -q ruff >/dev/null 2>&1 || true
	@$(RUFF) check .
	@echo "✅ Linting complete"

type:
	@echo "🔍 Type checking with Mypy..."
	@if [ ! -x $(PY) ]; then $(MAKE) venv; fi
	@$(PIP) install -q mypy >/dev/null 2>&1 || true
	@$(MYPY) $(SRC_DIR)
	@echo "✅ Type checking complete"

test: venv
	@echo "🧪 Running tests with coverage..."
	@$(PIP) install -q pytest pytest-cov >/dev/null 2>&1 || true
	@$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html
	@echo "✅ Tests complete"

qa: fmt lint type test
	@echo "✅ Quality assurance complete!"

# ========== ML Pipeline & Training ==========
train-models: deps
	@echo "🤖 Training PlantGuard models..."
	@mkdir -p $(RUNS_DIR)
	@echo "Vision model training..."
	@$(PY) -c "print('🔍 Vision model (ResNet50) training - implement in src/training/train_vision.py')"
	@echo "Audio model training..."
	@$(PY) -c "print('🎵 Audio model (CNN-LSTM) training - implement in src/training/train_audio.py')"
	@echo "Text model training..."
	@$(PY) -c "print('📝 Text model (DistilBERT) training - implement in src/training/train_text.py')"
	@echo "✅ Model training complete (implement actual training scripts)"

tensorboard: deps
	@echo "📊 Starting TensorBoard..."
	@$(PIP) install -q tensorboard >/dev/null 2>&1 || true
	@$(PY) -m tensorboard.main --logdir=$(RUNS_DIR) --port=6006 &
	@echo "TensorBoard running at http://localhost:6006"

# ========== Maintenance ==========
clean:
	@echo "🧹 Cleaning up caches and temporary files..."
	@rm -rf .mypy_cache .ruff_cache .pytest_cache dist build
	@rm -rf htmlcov .coverage coverage.xml
	@rm -rf $(RUNS_DIR) profile.stats security-report.json
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.orig" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

# ========== Quick Development Workflow ==========
quick: fmt lint
	@echo "⚡ Quick workflow complete!"