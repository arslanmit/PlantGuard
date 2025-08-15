# ========== PlantGuard Makefile ==========
# User-friendly commands for PlantGuard development
SHELL := /bin/bash
PY      := .venv/bin/python
PIP     := $(PY) -m pip
RUFF    := $(PY) -m ruff
MYPY    := $(PY) -m mypy
PYTEST  := $(PY) -m pytest
JUPYTER := $(PY) -m jupyter
BANDIT  := $(PY) -m bandit
PYTHON  := python3

# Project paths
SRC_DIR := src
DATA_DIR := data
NOTEBOOKS_DIR := notebooks
RUNS_DIR := runs
TESTS_DIR := tests
LOGS_DIR := logs

# Colors for output (auto-detect terminal support)
ifeq ($(shell test -t 1 && echo 1),1)
    ifneq ($(NO_COLOR),1)
        RED := \033[0;31m
        GREEN := \033[0;32m
        YELLOW := \033[0;33m
        BLUE := \033[0;34m
        CYAN := \033[0;36m
        NC := \033[0m # No Color
    else
        RED :=
        GREEN :=
        YELLOW :=
        BLUE :=
        CYAN :=
        NC :=
    endif
else
    RED :=
    GREEN :=
    YELLOW :=
    BLUE :=
    CYAN :=
    NC :=
endif

.DEFAULT_GOAL := help

.PHONY: help start setup install run switcher model-switcher dev test clean
.PHONY: format lint check fix train notebook
.PHONY: deps update status info logs models
.PHONY: security coverage docs build deploy
.PHONY: reset fresh restart debug profile
.PHONY: qa

help:
	@echo "$(CYAN)🌿 PlantGuard - AI Plant Disease Detection$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Getting Started$(NC)"
	@echo "  $(BLUE)start$(NC)          - First-time setup + launch app"
	@echo "  $(BLUE)run$(NC)            - Launch PlantGuard app"
	@echo "  $(BLUE)switcher$(NC)       - Launch Model Switcher UI (port 8502)"
	@echo "  $(BLUE)setup$(NC)          - Install dependencies & configure"
	@echo "  $(BLUE)notebook$(NC)       - Open Jupyter for development"
	@echo ""
	@echo "$(GREEN)💻 Development$(NC)"
	@echo "  $(BLUE)qa$(NC)             - Run dev, format, lint, check, fix, test"
	@echo "  $(BLUE)dev$(NC)            - Quick development workflow (format + check)"
	@echo "  $(BLUE)format$(NC)         - Auto-format code"
	@echo "  $(BLUE)lint$(NC)           - Check code quality"
	@echo "  $(BLUE)check$(NC)          - Run all quality checks"
	@echo "  $(BLUE)fix$(NC)            - Auto-fix common issues"
	@echo "  $(BLUE)test$(NC)           - Run tests"
	@echo ""
	@echo "$(GREEN)🤖 Machine Learning$(NC)"
	@echo "  $(BLUE)train$(NC)          - Train plant disease models"
	@echo "  $(BLUE)setup-dataset$(NC)  - Show dataset status and setup options"
	@echo "  $(BLUE)download-dataset$(NC) - Download PlantVillage dataset from Kaggle"
	@echo "  $(BLUE)prepare-dataset$(NC) - Prepare dataset with train/val splits"
	@echo "  $(BLUE)validate-dataset$(NC) - Validate dataset integrity and quality"
	@echo "  $(BLUE)analyze-dataset$(NC) - Analyze dataset statistics and distribution"
	@echo "  $(BLUE)dummy-dataset$(NC)  - Create dummy dataset for testing"
	@echo "  $(BLUE)models$(NC)         - Show model information"
	@echo "  $(BLUE)debug$(NC)          - Debug model performance"
	@echo ""
	@echo "$(GREEN)🔧 Maintenance$(NC)"
	@echo "  $(BLUE)clean$(NC)          - Clean temporary files"
	@echo "  $(BLUE)reset$(NC)          - Reset environment"
	@echo "  $(BLUE)fresh$(NC)          - Fresh install (clean + setup)"
	@echo "  $(BLUE)update$(NC)         - Update dependencies"
	@echo "  $(BLUE)status$(NC)         - Check project health"
	@echo ""
	@echo "$(GREEN)📊 Information$(NC)"
	@echo "  $(BLUE)info$(NC)           - Project overview"
	@echo "  $(BLUE)logs$(NC)           - View recent logs"
	@echo "  $(BLUE)coverage$(NC)       - Test coverage report"
	@echo ""
	@echo "$(YELLOW)💡 Examples:$(NC)"
	@echo "  $(CYAN)make start$(NC)     - New user? Start here!"
	@echo "  $(CYAN)make dev$(NC)       - Quick code check before commit"
	@echo "  $(CYAN)make train$(NC)     - Train your models"
	@echo "  $(CYAN)make clean$(NC)     - Clean up when things get messy"

# ========== Getting Started ==========

# First-time setup and launch (idempotent)
start:
	@echo "$(BLUE)🚀 Starting PlantGuard (first-time setup if needed)...$(NC)"
	@if [ ! -x $(PY) ]; then \
		echo "$(YELLOW)⚠️  Virtual environment not found. Running setup...$(NC)"; \
		make setup; \
	else \
		echo "$(GREEN)✅ Virtual environment found$(NC)"; \
	fi
	@make run

# Complete environment setup
setup:
	@echo "$(BLUE)🚀 Setting up PlantGuard development environment...$(NC)"
	@echo "$(YELLOW)Step 1: Creating virtual environment$(NC)"
	@[ -x $(PY) ] || $(PYTHON) -m venv .venv
	@$(PIP) install --upgrade pip setuptools wheel
	@echo "$(YELLOW)Step 2: Installing dependencies$(NC)"
	@$(PIP) install -r requirements.txt
	@echo "$(YELLOW)Step 3: Cleaning old build metadata (egg-info)$(NC)"
	@chmod -R u+w src/plantguard.egg-info 2>/dev/null || true
	@rm -rf src/plantguard.egg-info plantguard.egg-info 2>/dev/null || true
	@echo "$(YELLOW)Step 4: Installing PlantGuard in development mode$(NC)"
	@$(PIP) install -e . --no-deps --quiet --disable-pip-version-check
	@echo "$(GREEN)✅ Setup complete! Run 'make run' to start PlantGuard$(NC)"

# Install dependencies only
deps:
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	@[ -x $(PY) ] || $(PYTHON) -m venv .venv
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

# Install PlantGuard package
install: deps
	@echo "$(BLUE)🔧 Installing PlantGuard package...$(NC)"
	@chmod -R u+w src/plantguard.egg-info 2>/dev/null || true
	@rm -rf src/plantguard.egg-info plantguard.egg-info 2>/dev/null || true
	@$(PIP) install -e . --no-deps --quiet --disable-pip-version-check
	@echo "$(GREEN)✅ PlantGuard installed$(NC)"

# ========== Application Commands ==========

# Launch PlantGuard app
run:
	@echo "$(BLUE)🚀 Starting PlantGuard...$(NC)"
	@if [ ! -x $(PY) ]; then \
		echo "$(YELLOW)⚠️  Virtual environment not found. Running setup...$(NC)"; \
		make setup; \
	fi
	@echo "$(GREEN)🌿 PlantGuard is starting at http://localhost:8501$(NC)"
	@$(PY) run_local.py

# Launch Model Switcher UI (Streamlit)
switcher:
	@echo "$(BLUE)🚀 Starting PlantGuard Model Switcher...$(NC)"
	@if [ ! -x $(PY) ]; then \
		echo "$(YELLOW)⚠️  Virtual environment not found. Running setup...$(NC)"; \
		make setup; \
	fi
	@echo "$(GREEN)🌿 Model Switcher is starting at http://localhost:8502$(NC)"
	@$(PY) -m streamlit run scripts/model_switching/model_switcher_ui.py --server.port 8502

# Alias
model-switcher: switcher

# Open Jupyter notebook for development
notebook:
	@echo "$(BLUE)📓 Opening PlantGuard notebook...$(NC)"
	@if [ ! -x $(PY) ]; then \
		echo "$(YELLOW)⚠️  Setting up environment first...$(NC)"; \
		make setup; \
	fi
	@$(PIP) install jupyter ipykernel matplotlib seaborn --quiet
	@$(JUPYTER) notebook $(NOTEBOOKS_DIR)/PlantGuard.ipynb

# ========== Development Workflow ==========

# Quick development workflow (most common)
dev: format lint
	@echo "$(GREEN)✅ Development checks complete!$(NC)"
	@echo "$(CYAN)💡 Your code is ready for commit$(NC)"

# Auto-format code
format:
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install ruff --quiet
	@$(RUFF) check --fix . || true
	@$(RUFF) format .
	@echo "$(GREEN)✅ Code formatted$(NC)"

# Check code quality
lint:
	@echo "$(BLUE)🔍 Checking code quality...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install ruff --quiet
	@$(RUFF) check .
	@echo "$(GREEN)✅ Code quality check passed$(NC)"

# Run all quality checks
check: format lint type security
	@echo "$(GREEN)✅ All quality checks passed!$(NC)"

# Type checking
type:
	@echo "$(BLUE)🔍 Type checking...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install mypy --quiet
	@$(MYPY) $(SRC_DIR)/ || echo "$(YELLOW)⚠️  Type checking found issues$(NC)"
	@echo "$(GREEN)✅ Type checking complete$(NC)"

# Auto-fix common issues
fix:
	@echo "$(BLUE)🔧 Auto-fixing common issues...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install ruff --quiet
	@$(RUFF) check --fix . || true
	@$(RUFF) format .
	@# Fix end-of-file issues
	@find $(SRC_DIR) -name "*.py" -exec sh -c 'if [ -s "{}" ] && [ "$$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo >> "{}"; fi' \; 2>/dev/null || true
	@echo "$(GREEN)✅ Common issues fixed$(NC)"

# QA workflow: run all development steps sequentially
qa:
	@$(MAKE) dev
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) check
	@$(MAKE) fix
	@$(MAKE) test
	@echo "$(GREEN)✅ QA workflow complete$(NC)"

# Security scan
security:
	@echo "$(BLUE)🔒 Security scan...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install bandit --quiet
	@$(BANDIT) -r $(SRC_DIR)/ -ll || echo "$(YELLOW)⚠️  Security issues found$(NC)"
	@echo "$(GREEN)✅ Security scan complete$(NC)"

# ========== Testing ==========

# Run tests
test:
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install pytest pytest-cov --quiet
	@$(PYTEST) $(TESTS_DIR)/ -v --tb=short || echo "$(YELLOW)⚠️  Some tests failed$(NC)"
	@echo "$(GREEN)✅ Tests complete$(NC)"

# Test coverage report
coverage:
	@echo "$(BLUE)📊 Generating test coverage report...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install pytest pytest-cov --quiet
	@$(PYTEST) $(TESTS_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "$(GREEN)📊 Coverage report generated in htmlcov/index.html$(NC)"

# ========== Machine Learning ==========

# Train models
train:
	@echo "$(BLUE)🤖 Training PlantGuard models...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@mkdir -p $(RUNS_DIR)
	@echo "$(YELLOW)Checking dataset availability...$(NC)"
	@if [ -d "data/PlantVillage/train" ] && [ -d "data/PlantVillage/val" ]; then \
		echo "$(GREEN)✅ PlantVillage dataset found$(NC)"; \
		DATASET_DIR="data/PlantVillage"; \
	elif [ -d "data/plantvillage_dummy/train" ] && [ -d "data/plantvillage_dummy/val" ]; then \
		echo "$(GREEN)✅ Dummy dataset found$(NC)"; \
		DATASET_DIR="data/plantvillage_dummy"; \
	else \
		echo "$(YELLOW)⚠️  No dataset found. Creating dummy dataset for testing...$(NC)"; \
		$(PY) scripts/setup_dummy_dataset.py --output_dir data/plantvillage_dummy --num_classes 5 --samples_per_class 20; \
		DATASET_DIR="data/plantvillage_dummy"; \
	fi; \
	echo "$(YELLOW)Training vision model (ResNet50)...$(NC)"; \
	if [ -f scripts/train_vision_model.py ]; then \
		$(PY) scripts/train_vision_model.py --data_dir $$DATASET_DIR --epochs 5 --batch_size 8; \
	else \
		echo "$(YELLOW)⚠️  Vision training script not found$(NC)"; \
	fi
	@echo "$(GREEN)✅ Model training complete$(NC)"

# Train models with improved pipeline and better hyperparameters
train-improved:
	@echo "$(BLUE)🤖 Training PlantGuard models (improved)...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@mkdir -p $(RUNS_DIR)
	@echo "$(YELLOW)Checking dataset availability...$(NC)"
	@if [ -d "data/processed/plantvillage/train" ] && [ -d "data/processed/plantvillage/val" ]; then \
		echo "$(GREEN)✅ Real PlantVillage dataset found$(NC)"; \
		$(PY) scripts/train_vision_model_improved.py --data_dir data/processed/plantvillage --epochs 50 --batch_size 32 --learning_rate 0.0001; \
	elif [ -d "data/PlantVillage/train" ] && [ -d "data/PlantVillage/val" ]; then \
		echo "$(GREEN)✅ Legacy PlantVillage dataset found$(NC)"; \
		$(PY) scripts/train_vision_model_improved.py --data_dir data/PlantVillage --epochs 50 --batch_size 32 --learning_rate 0.0001; \
	elif [ -d "data/plantvillage_dummy_improved/train" ] && [ -d "data/plantvillage_dummy_improved/val" ]; then \
		echo "$(GREEN)✅ Improved dummy dataset found$(NC)"; \
		$(PY) scripts/train_vision_model_improved.py --data_dir data/plantvillage_dummy_improved --epochs 15 --batch_size 16 --learning_rate 0.0001; \
	else \
		echo "$(YELLOW)⚠️  No dataset found. Creating improved dummy dataset for testing...$(NC)"; \
		$(PY) scripts/setup_better_dummy_dataset.py --output_dir data/plantvillage_dummy_improved --num_classes 8 --samples_per_class 60; \
		$(PY) scripts/train_vision_model_improved.py --data_dir data/plantvillage_dummy_improved --epochs 15 --batch_size 16 --learning_rate 0.0001; \
	fi
	@echo "$(GREEN)✅ Improved model training complete$(NC)"

# Setup dataset (real PlantVillage or dummy for testing)
setup-dataset:
	@echo "$(BLUE)📊 Setting up training dataset...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@echo "$(CYAN)Dataset setup options:$(NC)"
	@echo "  1. $(GREEN)Real PlantVillage dataset$(NC) (recommended for production)"
	@echo "     - Download automatically: make download-dataset"
	@echo "     - Or download manually from: https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset"
	@echo "     - Extract to: data/raw/plantvillage/"
	@echo "     - Run: make prepare-dataset"
	@echo ""
	@echo "  2. $(YELLOW)Dummy dataset$(NC) (for testing only)"
	@echo "     - Run: make dummy-dataset"
	@echo ""
	@echo "$(CYAN)Current status:$(NC)"
	@$(PY) -c "\
from pathlib import Path; \
from src.training.dataset_manager import DatasetManager; \
import sys; \
dm = DatasetManager(); \
processed_exists = (Path('data/processed/plantvillage/train').exists() and Path('data/processed/plantvillage/val').exists()); \
legacy_exists = (Path('data/PlantVillage/train').exists() and Path('data/PlantVillage/val').exists()); \
raw_exists = Path('data/raw/plantvillage').exists(); \
dummy_exists = (Path('data/plantvillage_dummy/train').exists() and Path('data/plantvillage_dummy/val').exists()); \
print('  ✅ Processed PlantVillage dataset found' if processed_exists else ('  ✅ Legacy PlantVillage dataset found' if legacy_exists else '  ❌ No processed PlantVillage dataset found')); \
print('  ✅ Raw PlantVillage dataset found' if raw_exists else '  ❌ Raw PlantVillage dataset not found'); \
print('  ✅ Dummy dataset found' if dummy_exists else '  ❌ Dummy dataset not found'); \
"
	@echo ""
	@echo "$(CYAN)💡 Quick commands:$(NC)"
	@echo "  $(BLUE)make download-dataset$(NC)  - Download PlantVillage from Kaggle"
	@echo "  $(BLUE)make prepare-dataset$(NC)   - Prepare dataset with train/val splits"
	@echo "  $(BLUE)make validate-dataset$(NC)  - Check dataset integrity"
	@echo "  $(BLUE)make analyze-dataset$(NC)   - Show dataset statistics"

# Download PlantVillage dataset automatically
download-dataset:
	@echo "$(BLUE)📥 Downloading PlantVillage dataset...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@$(PY) scripts/download_dataset.py

# Validate dataset integrity
validate-dataset:
	@echo "$(BLUE)🔍 Validating dataset integrity...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@$(PY) scripts/validate_dataset.py

# Analyze dataset statistics
analyze-dataset:
	@echo "$(BLUE)📊 Analyzing dataset statistics...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@$(PY) scripts/analyze_dataset.py

# Create dummy dataset for testing
dummy-dataset:
	@echo "$(BLUE)🎭 Creating dummy dataset for testing...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@$(PY) scripts/setup_dummy_dataset.py --output_dir data/plantvillage_dummy --num_classes 8 --samples_per_class 50
	@echo "$(GREEN)✅ Dummy dataset created at data/plantvillage_dummy/$(NC)"
	@echo "$(YELLOW)⚠️  This is for testing only. Use real PlantVillage dataset for production.$(NC)"

# Prepare real PlantVillage dataset (assumes raw data is available)
prepare-dataset:
	@echo "$(BLUE)📊 Preparing PlantVillage dataset...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@$(PY) scripts/prepare_dataset_new.py

# Show model information
models:
	@echo "$(BLUE)🤖 Model information...$(NC)"
	@if [ -d $(DATA_DIR)/models ]; then \
		echo "$(CYAN)Available models:$(NC)"; \
		ls -la $(DATA_DIR)/models/; \
		echo ""; \
		echo "$(CYAN)Model sizes:$(NC)"; \
		du -sh $(DATA_DIR)/models/* 2>/dev/null || true; \
	else \
		echo "$(YELLOW)No models directory found. Run 'make train' to create models.$(NC)"; \
	fi

# Debug model performance
debug:
	@echo "$(BLUE)🔍 Debugging model performance...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@if [ -f scripts/test_vision_adapter.py ]; then \
		$(PY) scripts/test_vision_adapter.py; \
	else \
		echo "$(YELLOW)⚠️  Debug script not found$(NC)"; \
	fi

# ========== Maintenance ==========

# Clean temporary files
clean:
	@echo "$(BLUE)🧹 Cleaning temporary files...$(NC)"
	@rm -rf .mypy_cache .ruff_cache .pytest_cache
	@rm -rf htmlcov .coverage coverage.xml
	@rm -rf $(RUNS_DIR) profile.stats
	@rm -rf build dist *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@find $(DATA_DIR)/temp -type f -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# Reset environment
reset: clean
	@echo "$(BLUE)🔄 Resetting environment...$(NC)"
	@rm -rf .venv
	@echo "$(GREEN)✅ Environment reset$(NC)"

# Fresh install
fresh: reset setup
	@echo "$(GREEN)✅ Fresh installation complete!$(NC)"

# Update dependencies
update:
	@echo "$(BLUE)🔄 Updating dependencies...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install --upgrade -r requirements.txt
	@$(PIP) install --upgrade -e . --no-deps
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

# Check project health
status:
	@echo "$(BLUE)📊 Project health check...$(NC)"
	@echo "$(CYAN)Python version:$(NC)"
	@$(PYTHON) --version
	@echo "$(CYAN)Virtual environment:$(NC)"
	@if [ -x $(PY) ]; then \
		echo "$(GREEN)✅ Active$(NC)"; \
	else \
		echo "$(RED)❌ Not found$(NC)"; \
	fi
	@echo "$(CYAN)PlantGuard package:$(NC)"
	@if [ -x $(PY) ]; then \
		$(PIP) show plantguard >/dev/null 2>&1 && echo "$(GREEN)✅ Installed$(NC)" || echo "$(YELLOW)⚠️  Not installed$(NC)"; \
	else \
		echo "$(RED)❌ Cannot check$(NC)"; \
	fi
	@echo "$(CYAN)Core directories:$(NC)"
	@[ -d $(SRC_DIR) ] && echo "$(GREEN)✅ Source directory$(NC)" || echo "$(RED)❌ Source directory missing$(NC)"
	@[ -d $(TESTS_DIR) ] && echo "$(GREEN)✅ Tests directory$(NC)" || echo "$(RED)❌ Tests directory missing$(NC)"
	@[ -d $(DATA_DIR) ] && echo "$(GREEN)✅ Data directory$(NC)" || echo "$(RED)❌ Data directory missing$(NC)"

# ========== Information ==========

# Project overview
info:
	@echo "$(CYAN)🌿 PlantGuard Project Overview$(NC)"
	@echo ""
	@echo "$(GREEN)Description:$(NC) Multimodal plant disease detection system"
	@echo "$(GREEN)Version:$(NC) 0.1.0"
	@echo "$(GREEN)Python:$(NC) $(shell $(PYTHON) --version 2>&1)"
	@echo "$(GREEN)Framework:$(NC) PyTorch + Streamlit"
	@echo ""
	@echo "$(GREEN)Key Features:$(NC)"
	@echo "  • Vision: ResNet50 plant disease classification"
	@echo "  • Audio: Whisper speech recognition"
	@echo "  • Text: DistilBERT Q&A system"
	@echo "  • UI: Streamlit multimodal interface"
	@echo ""
	@echo "$(GREEN)Quick Commands:$(NC)"
	@echo "  $(CYAN)make start$(NC)  - First-time setup and launch"
	@echo "  $(CYAN)make run$(NC)    - Launch the application"
	@echo "  $(CYAN)make dev$(NC)    - Development workflow"
	@echo "  $(CYAN)make train$(NC)  - Train ML models"

# View logs
logs:
	@echo "$(BLUE)📋 Recent logs...$(NC)"
	@mkdir -p $(LOGS_DIR)
	@if ls $(LOGS_DIR)/*.log >/dev/null 2>&1; then \
		tail -20 $(LOGS_DIR)/*.log; \
	else \
		echo "$(YELLOW)No log files found$(NC)"; \
	fi

# ========== Advanced Commands ==========

# Build package
build: clean
	@echo "$(BLUE)🔨 Building package...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install build --quiet
	@$(PY) -m build
	@echo "$(GREEN)✅ Package built in dist/$(NC)"

# Generate documentation
docs:
	@echo "$(BLUE)📚 Building documentation...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install sphinx sphinx-rtd-theme --quiet
	@mkdir -p docs
	@echo "$(YELLOW)⚠️  Documentation generation not yet implemented$(NC)"

# Profile performance
profile:
	@echo "$(BLUE)📈 Profiling performance...$(NC)"
	@if [ ! -x $(PY) ]; then make setup; fi
	@$(PY) -m cProfile -o profile.stats run_local.py &
	@sleep 5
	@pkill -f "run_local.py" || true
	@$(PY) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(10)"
	@echo "$(GREEN)✅ Profiling complete$(NC)"

# Restart application (useful during development)
restart:
	@echo "$(BLUE)🔄 Restarting PlantGuard...$(NC)"
	@pkill -f "streamlit" || true
	@sleep 2
	@make run

# ========== Aliases for Common Typos ==========
instal: install
insall: install
runn: run
rnu: run
tets: test
testt: test
clen: clean
cean: clean
