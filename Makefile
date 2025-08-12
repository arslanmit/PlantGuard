# ========== PlantGuard Makefile ==========
# Streamlined workflow for PlantGuard multimodal plant disease detection
SHELL := /bin/bash
PY      := .venv/bin/python
PIP     := $(PY) -m pip
RUFF    := $(PY) -m ruff
MYPY    := $(PY) -m mypy
PYTEST  := $(PY) -m pytest
JUPYTER := $(PY) -m jupyter
PYTHON  := python3

# Project paths
SRC_DIR := src
DATA_DIR := data
NOTEBOOKS_DIR := notebooks
RUNS_DIR := runs
TESTS_DIR := tests
LOGS_DIR := logs

.DEFAULT_GOAL := qa

.PHONY: help setup venv deps dev-deps fmt lint type test qa clean
.PHONY: install run notebook tensorboard train-models quick
.PHONY: test-unit test-fast test-coverage test-all test-clean test-runner
.PHONY: security check-deps update-deps validate logs models-info data-info
.PHONY: ci pre-commit docker-build docker-run

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
	@echo "  dev-deps   - Install development dependencies"
	@echo "  update-deps - Update all dependencies"
	@echo ""
	@echo "✅ Code Quality:"
	@echo "  fmt        - Auto-fix and format code (Ruff)"
	@echo "  lint       - Lint code (Ruff)"
	@echo "  type       - Type check (Mypy)"
	@echo "  security   - Security scan (Bandit)"
	@echo "  qa         - Full quality assurance (fmt→lint→type→test)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test       - Run all tests with coverage"
	@echo "  test-unit  - Run unit tests only"
	@echo "  test-fast  - Run tests without coverage"
	@echo "  test-coverage - Generate coverage report"
	@echo "  test-clean - Clean test artifacts"
	@echo ""
	@echo "🤖 ML Pipeline:"
	@echo "  train-models    - Train all PlantGuard models"
	@echo "  tensorboard     - Launch TensorBoard for training metrics"
	@echo "  notebook        - Open Jupyter notebook"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean      - Remove caches and temporary files"
	@echo "  check-deps - Check for dependency vulnerabilities"
	@echo ""
	@echo "📊 Information:"
	@echo "  validate   - Validate project setup"
	@echo "  logs       - Show recent log files"
	@echo "  models-info - Show model information"
	@echo "  data-info  - Show data directory information"
	@echo ""
	@echo "🔧 Alternative:"
	@echo "  test-runner - Use run_tests.py script"
	@echo ""
	@echo "🚀 CI/CD:"
	@echo "  ci         - Full CI/CD pipeline (clean→setup→qa)"
	@echo "  pre-commit - Pre-commit checks (fmt→lint→type)"

# ========== Environment Setup ==========
venv:
	@echo "🔧 Creating virtual environment..."
	@[ -x $(PY) ] || $(PYTHON) -m venv .venv
	@$(PIP) install --upgrade pip setuptools wheel
	@echo "✅ Virtual environment ready"

deps: venv
	@echo "📦 Installing runtime dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "✅ Runtime dependencies installed"

dev-deps: deps
	@echo "📦 Installing development dependencies..."
	@$(PIP) install -e ".[dev]"
	@echo "✅ Development dependencies installed"

install: deps
	@echo "🔧 Installing PlantGuard in editable mode..."
	@$(PIP) install -e . --no-deps --quiet --disable-pip-version-check
	@echo "✅ PlantGuard installed"

setup: dev-deps install
	@echo "🎉 Environment setup complete!"
	@echo "Run 'make run' to start PlantGuard"

update-deps: venv
	@echo "🔄 Updating dependencies..."
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install --upgrade -r requirements.txt
	@$(PIP) install --upgrade -e ".[dev]"
	@echo "✅ Dependencies updated"

check-deps: deps
	@echo "🔍 Checking for dependency vulnerabilities..."
	@$(PIP) check
	@echo "✅ Dependency check complete"

# ========== Application Execution ==========
run: deps
	@echo "🚀 Starting PlantGuard Streamlit app..."
	@$(PY) run_local.py

notebook: deps
	@echo "📓 Opening PlantGuard Jupyter notebook..."
	@$(JUPYTER) notebook $(NOTEBOOKS_DIR)/PlantGuard.ipynb

# ========== Code Quality & Testing ==========
fmt: dev-deps
	@echo "🎨 Formatting code with Ruff..."
	@$(RUFF) check --fix . --quiet
	@$(RUFF) format . --quiet
	@echo "✅ Code formatted"

lint: dev-deps
	@echo "🔍 Linting code with Ruff..."
	@$(RUFF) check .
	@echo "✅ Linting complete"

type: dev-deps
	@echo "🔍 Type checking with Mypy..."
	@$(MYPY) $(SRC_DIR)
	@echo "✅ Type checking complete"

security: dev-deps
	@echo "🔒 Running security scan..."
	@$(PY) -m bandit -r $(SRC_DIR) -f json -o security-report.json || true
	@$(PY) -m bandit -r $(SRC_DIR) -ll
	@echo "✅ Security scan complete"

# ========== Testing Commands ==========
test: dev-deps
	@echo "🧪 Running all tests with coverage..."
	@$(PYTEST) $(TESTS_DIR)/ -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html
	@echo "✅ All tests complete"

test-unit: dev-deps
	@echo "🧪 Running unit tests..."
	@$(PYTEST) $(TESTS_DIR)/ -v -m unit
	@echo "✅ Unit tests complete"

test-fast: dev-deps
	@echo "⚡ Running tests (fast mode)..."
	@$(PYTEST) $(TESTS_DIR)/ -v --tb=short
	@echo "✅ Fast tests complete"

test-coverage: dev-deps
	@echo "📊 Generating coverage report..."
	@$(PYTEST) $(TESTS_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in htmlcov/index.html"

test-clean:
	@echo "🧹 Cleaning test artifacts..."
	@rm -rf .pytest_cache htmlcov .coverage
	@echo "✅ Test artifacts cleaned"

test-all: test-clean test
	@echo "✅ Complete test suite finished!"

qa: fmt lint type security test
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
	@$(PY) -m tensorboard.main --logdir=$(RUNS_DIR) --port=6006 &
	@echo "TensorBoard running at http://localhost:6006"

# ========== Maintenance ==========
clean:
	@echo "🧹 Cleaning up caches and temporary files..."
	@rm -rf .mypy_cache .ruff_cache .pytest_cache dist build
	@rm -rf htmlcov .coverage coverage.xml
	@rm -rf $(RUNS_DIR) profile.stats security-report.json
	@rm -rf $(LOGS_DIR)/*.log 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.orig" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@find $(DATA_DIR)/temp -type f -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

# ========== Quick Development Workflow ==========
quick: fmt lint
	@echo "⚡ Quick workflow complete!"

# ========== Alternative Test Runner ==========
test-runner: dev-deps
	@echo "🧪 Using run_tests.py script..."
	@$(PY) run_tests.py all

# ========== Development Utilities ==========
validate: dev-deps
	@echo "✅ Validating PlantGuard project setup..."
	@echo "Checking Python version..."
	@$(PY) --version
	@echo "Checking virtual environment..."
	@[ -x $(PY) ] && echo "✅ Virtual environment active" || echo "❌ Virtual environment not found"
	@echo "Checking core directories..."
	@[ -d $(SRC_DIR) ] && echo "✅ Source directory exists" || echo "❌ Source directory missing"
	@[ -d $(TESTS_DIR) ] && echo "✅ Tests directory exists" || echo "❌ Tests directory missing"
	@[ -d $(DATA_DIR) ] && echo "✅ Data directory exists" || echo "❌ Data directory missing"
	@echo "Checking configuration files..."
	@[ -f pyproject.toml ] && echo "✅ pyproject.toml exists" || echo "❌ pyproject.toml missing"
	@[ -f requirements.txt ] && echo "✅ requirements.txt exists" || echo "❌ requirements.txt missing"
	@echo "✅ Project validation complete"

logs:
	@echo "📋 Showing recent logs..."
	@mkdir -p $(LOGS_DIR)
	@tail -f $(LOGS_DIR)/*.log 2>/dev/null || echo "No log files found in $(LOGS_DIR)"

models-info:
	@echo "🤖 Model information..."
	@ls -la $(DATA_DIR)/models/ 2>/dev/null || echo "No models found in $(DATA_DIR)/models/"
	@echo ""
	@echo "Expected models:"
	@echo "  - vision_resnet50.pt (Vision model)"
	@echo "  - speech_cnn_lstm.pt (Audio model)"
	@echo "  - text_qa_model/ (Text model directory)"
	@echo "  - fusion_mlp.pt (Fusion model)"

data-info:
	@echo "📊 Data directory information..."
	@ls -la $(DATA_DIR)/ 2>/dev/null || echo "Data directory not found"
	@echo ""
	@du -sh $(DATA_DIR)/* 2>/dev/null || echo "No data files found"

# ========== CI/CD Pipeline ==========
ci: clean setup qa
	@echo "🚀 CI/CD pipeline complete!"
	@echo "All checks passed - ready for deployment"

pre-commit: fmt lint type
	@echo "✅ Pre-commit checks complete!"

# ========== Docker Support (Future) ==========
docker-build:
	@echo "🐳 Building Docker image..."
	@echo "Docker support not yet implemented"

docker-run:
	@echo "🐳 Running Docker container..."
	@echo "Docker support not yet implemented"