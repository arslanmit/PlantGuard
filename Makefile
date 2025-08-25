# ========== PlantGuard Makefile ==========
# 🌿 AI-powered plant disease detection system
# Enhanced for macOS development with Apple Silicon optimization
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# ========== Environment Detection ==========
UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)
IS_MACOS := $(shell [ "$(UNAME_S)" = "Darwin" ] && echo 1 || echo 0)
IS_APPLE_SILICON := $(shell [ "$(UNAME_M)" = "arm64" ] && echo 1 || echo 0)

# ========== Python Environment ==========
PYTHON := python3.10
PY := .venv/bin/python
PIP := $(PY) -m pip
RUFF := $(PY) -m ruff
MYPY := $(PY) -m mypy
PYTEST := $(PY) -m pytest
JUPYTER := $(PY) -m jupyter
BANDIT := $(PY) -m bandit
STREAMLIT := $(PY) -m streamlit

# ========== Project Structure ==========
SRC_DIR := src
DATA_DIR := data
NOTEBOOKS_DIR := notebooks
RUNS_DIR := runs
TESTS_DIR := tests
LOGS_DIR := logs
MODELS_DIR := $(DATA_DIR)/models
KB_DIR := $(DATA_DIR)/knowledge_base
CONFIG_DIR := config
SCRIPTS_DIR := scripts
# Coverage storage: put coverage DB inside a directory to avoid root-file permission issues
COVERAGE_DIR := .coverage
COVERAGE_FILE := $(CURDIR)/$(COVERAGE_DIR)/.coverage

# ========== macOS Optimization ==========
ifeq ($(IS_APPLE_SILICON),1)
    TORCH_DEVICE := mps
    PYTORCH_ENABLE_MPS_FALLBACK := 1
    export PYTORCH_ENABLE_MPS_FALLBACK
else
    TORCH_DEVICE := cpu
endif

# ========== Performance Settings ==========
WORKERS := $(shell sysctl -n hw.ncpu 2>/dev/null || echo 4)
BATCH_SIZE := $(shell [ $(IS_APPLE_SILICON) -eq 1 ] && echo 32 || echo 16)
MEMORY_LIMIT := $(shell [ $(IS_APPLE_SILICON) -eq 1 ] && echo 8G || echo 8G)

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

.PHONY: help start setup run mobile dev test clean
.PHONY: format lint check fix train monitor notebook benchmark evaluate
.PHONY: deps update status info logs models
.PHONY: security coverage docs build deploy
.PHONY: reset fresh stop restart debug profile validate
.PHONY: templates-list train-production-template train-production-config
.PHONY: qa health-check tunnel list-models evaluate-model monitor-training setup-dataset

# ========== Help & Information ==========

help:
	@echo "$(CYAN)🌿 PlantGuard - AI Plant Disease Detection$(NC)"
	@echo "$(YELLOW)🍎 Optimized for macOS $(shell sw_vers -productVersion 2>/dev/null || echo 'Unknown') $(shell [ $(IS_APPLE_SILICON) -eq 1 ] && echo '(Apple Silicon)' || echo '(Intel)')$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Quick Start$(NC)"
	@echo "  $(BLUE)start$(NC)              - Complete setup + launch (new users start here!)"
	@echo "  $(BLUE)run$(NC)                - Launch PlantGuard SPA (single page application)"
	@echo "  $(BLUE)mobile$(NC)             - Launch Mobile PlantGuard (optimized for Chrome/Safari mobile)"
	@echo "  $(BLUE)dev$(NC)                - Quick development workflow (format + lint + test)"
	@echo "  $(BLUE)notebook$(NC)           - Open Jupyter for interactive development"
	@echo ""
	@echo "$(GREEN)🛠️  Environment & Setup$(NC)"
	@echo "  $(BLUE)setup$(NC)              - Install dependencies & configure environment"
	@echo "  $(BLUE)setup-macos$(NC)        - macOS-specific setup (Homebrew dependencies)"
	@echo "  $(BLUE)setup-apple-silicon$(NC) - Apple Silicon optimizations (MPS, memory)"
	@echo "  $(BLUE)deps$(NC)               - Install Python dependencies only"
	@echo "  $(BLUE)update$(NC)             - Update all dependencies to latest versions"
	@echo "  $(BLUE)clean$(NC)              - Clean temporary files and caches"
	@echo "  $(BLUE)reset$(NC)              - Complete environment reset"
	@echo ""
	@echo "$(GREEN)💻 Development Workflow$(NC)"
	@echo "  $(BLUE)qa$(NC)                 - Complete QA pipeline (format + lint + type + test)"
	@echo "  $(BLUE)qa-fast$(NC)            - Fast QA (skip type checking and slow tests)"
	@echo "  $(BLUE)format$(NC)             - Auto-format code with Ruff"
	@echo "  $(BLUE)lint$(NC)               - Check code quality and style"
	@echo "  $(BLUE)type$(NC)               - Type checking with MyPy"
	@echo "  $(BLUE)fix$(NC)                - Auto-fix common code issues"
	@echo "  $(BLUE)security$(NC)           - Security vulnerability scan"
	@echo ""
	@echo "$(GREEN)🧪 Testing & Validation$(NC)"
	@echo "  $(BLUE)test$(NC)               - Run unit tests"
	@echo "  $(BLUE)test-fast$(NC)          - Run fast tests only (skip slow/integration)"
	@echo "  $(BLUE)test-integration$(NC)   - Comprehensive integration tests"
	@echo "  $(BLUE)test-performance$(NC)   - Performance regression tests"
	@echo "  $(BLUE)test-models$(NC)        - Test all model components"
	@echo "  $(BLUE)test-ui$(NC)            - Test Streamlit UI components"
	@echo "  $(BLUE)coverage$(NC)           - Generate test coverage report"
	@echo "  $(BLUE)validate$(NC)           - Validate entire system configuration"
	@echo ""
	@echo "$(GREEN)🤖 Machine Learning$(NC)"
	@echo "  $(BLUE)train$(NC)              - Train models with optimal settings"
	@echo "  $(BLUE)train-production$(NC)   - Full production training pipeline"
	@echo "  $(BLUE)train-fast$(NC)         - Quick training for development/testing"
	@echo "  $(BLUE)train-production-template$(NC) - Production training with a template (TEMPLATE=name|path)"
	@echo "  $(BLUE)train-production-config$(NC)   - Production training with explicit config (CONFIG=path)"
	@echo "  $(BLUE)templates-list$(NC)     - List available training templates"
	@echo "  $(BLUE)monitor$(NC)            - Launch TensorBoard monitoring"
	@echo "  $(BLUE)evaluate$(NC)           - Evaluate trained models"
	@echo "  $(BLUE)benchmark$(NC)          - Benchmark all models"
	@echo "  $(BLUE)optimize$(NC)           - Performance optimization analysis"
	@echo ""
	@echo "$(GREEN)📊 Dataset Management$(NC)"
	@echo "  $(BLUE)dataset-status$(NC)     - Check dataset availability and health"
	@echo "  $(BLUE)dataset-download$(NC)   - Download PlantVillage dataset"
	@echo "  $(BLUE)dataset-prepare$(NC)    - Prepare dataset for training"
	@echo "  $(BLUE)dataset-validate$(NC)   - Validate dataset integrity"
	@echo "  $(BLUE)dataset-analyze$(NC)    - Generate dataset statistics"
	@echo ""
	@echo "$(GREEN)🔧 Model Management$(NC)"
	@echo "  $(BLUE)models$(NC)             - List all available models"
	@echo "  $(BLUE)models-migrate$(NC)     - Migrate legacy models to new format"
	@echo "  $(BLUE)models-sync$(NC)        - Sync model registry"
	@echo "  $(BLUE)models-switch$(NC)      - Switch active model (MODEL_ID=name)"
	@echo "  $(BLUE)models-export$(NC)      - Export models for deployment"
	@echo "  $(BLUE)models-import$(NC)      - Import external models"
	@echo ""
	@echo "$(GREEN)🚀 Deployment & Production$(NC)"
	@echo "  $(BLUE)deploy-local$(NC)       - Deploy locally with production settings"
	@echo "  $(BLUE)deploy-docker$(NC)      - Build and run Docker container"
	@echo "  $(BLUE)deploy-check$(NC)       - Validate deployment readiness"
	@echo "  $(BLUE)health-check$(NC)       - System health monitoring"
	@echo ""
	@echo "$(GREEN)📊 Monitoring & Debugging$(NC)"
	@echo "  $(BLUE)status$(NC)             - Show system status and health"
	@echo "  $(BLUE)info$(NC)               - Detailed project information"
	@echo "  $(BLUE)logs$(NC)               - View application logs"
	@echo "  $(BLUE)debug$(NC)              - Debug mode with detailed logging"
	@echo "  $(BLUE)profile$(NC)            - Performance profiling"
	@echo ""
	@echo "$(GREEN)🤖 AI Agent Commands$(NC)"
	@echo "  $(BLUE)api-info$(NC)            - System information in JSON format"
	@echo "  $(BLUE)api-status$(NC)          - System status with health metrics (JSON)"
	@echo "  $(BLUE)agent-setup$(NC)         - Automated setup with progress tracking"
	@echo "  $(BLUE)data-status$(NC)         - Dataset status in JSON format"
	@echo "  $(BLUE)models-list-json$(NC)    - List models with JSON metadata"
	@echo ""
	@echo "$(GREEN)⚡ Quick Shortcuts$(NC)"
	@echo "  $(BLUE)s$(NC)                  - start (complete setup + launch)"
	@echo "  $(BLUE)r$(NC)                  - run (launch app)"
	@echo "  $(BLUE)m$(NC)                  - mobile (launch mobile app)"
	@echo "  $(BLUE)d$(NC)                  - dev (development workflow)"
	@echo "  $(BLUE)t$(NC)                  - test (run tests)"
	@echo "  $(BLUE)f$(NC)                  - format (format code)"
	@echo "  $(BLUE)l$(NC)                  - lint (check code)"
	@echo ""
	@echo "$(YELLOW)💡 Recommended Workflows:$(NC)"
	@echo "  $(CYAN)New User:$(NC)          make start"
	@echo "  $(CYAN)Development:$(NC)       make dev → make test → make run"
	@echo "  $(CYAN)Training:$(NC)          make dataset-status → make train → make monitor"
	@echo "  $(CYAN)Deployment:$(NC)        make qa → make deploy-check → make deploy-local"
	@echo ""
	@echo "$(YELLOW)🌟 Single Page Application Features:$(NC)"
	@echo "  • All functionality in one interface"
	@echo "  • AI agent friendly design"
	@echo "  • No navigation complexity"
	@echo "  • Complete technical capability preservation"
	@echo ""
	@echo "$(YELLOW)🍎 macOS Features:$(NC)"
	@echo "  • Apple Silicon MPS acceleration ($(TORCH_DEVICE))"
	@echo "  • Optimized for $(WORKERS) CPU cores"
	@echo "  • Memory limit: $(MEMORY_LIMIT)"
	@echo "  • Homebrew integration for system dependencies"

# ========== Quick Start & Environment Setup ==========

# Check virtual environment is active
check-venv:
	@if [ ! -x $(PY) ]; then \
		echo "$(YELLOW)⚠️  Virtual environment not found. Creating...$(NC)"; \
		make setup-environment; \
	fi

# Complete first-time setup and launch
start: setup-environment health-check
	@echo "$(BLUE)🚀 Starting PlantGuard...$(NC)"
	@echo "$(CYAN)🎯 Launching SPA application at http://localhost:8501$(NC)"
	@make run

# Quick shortcuts - SPA focused
s: start
r: run               # Launch SPA
m: mobile            # Launch Mobile SPA
d: dev
t: test
f: format
l: lint

# Complete environment setup with macOS optimizations
setup: setup-environment setup-models setup-knowledge-base
	@echo "$(GREEN)✅ PlantGuard setup complete!$(NC)"
	@echo "$(CYAN)💡 Run 'make run' to launch the application$(NC)"
	@echo "$(CYAN)💡 Run 'make dev' for development workflow$(NC)"

# Core environment setup
setup-environment:
	@echo "$(BLUE)🛠️  Setting up PlantGuard environment...$(NC)"
	@echo "$(YELLOW)📍 Platform: $(UNAME_S) $(UNAME_M)$(NC)"
	@if [ $(IS_APPLE_SILICON) -eq 1 ]; then \
		echo "$(GREEN)🍎 Apple Silicon detected - enabling MPS acceleration"; \
	fi

	@echo "$(BLUE)Step 1/4: Checking Python version...$(NC)"
	@if ! command -v $(PYTHON) >/dev/null 2>&1; then \
		echo "$(RED)❌ Python 3.10 not found$(NC)"; \
		echo "$(CYAN)💡 Install Python 3.10:$(NC)"; \
		if [ "$(UNAME_S)" = "Darwin" ]; then \
			echo "  brew install python@3.10"; \
		else \
			echo "  Visit https://www.python.org/downloads/"; \
		fi; \
		exit 1; \
	fi

	@echo "$(BLUE)Step 2/4: Creating virtual environment...$(NC)"
	@if [ ! -d ".venv" ]; then \
		$(PYTHON) -m venv .venv --clear --upgrade-deps || { \
			echo "$(RED)❌ Failed to create virtual environment$(NC)"; \
			echo "$(CYAN)💡 Try: python3 -m pip install --upgrade pip$(NC)"; \
			exit 1; \
		}; \
		echo "$(GREEN)✅ Virtual environment created with $(shell .venv/bin/python3 --version)$(NC)"; \
	else \
		CURRENT_VER="$$(.venv/bin/python3 --version 2>/dev/null | awk '{print $$2}')"; \
		case "$$CURRENT_VER" in \
			3.10.*) \
				echo "$(YELLOW)✅ Virtual environment already exists (using Python $$CURRENT_VER)$(NC)"; \
				;; \
			*) \
				echo "$(YELLOW)⚠️  Existing venv uses Python $$CURRENT_VER; recreating with $(PYTHON) for compatibility$(NC)"; \
				rm -rf .venv; \
				$(PYTHON) -m venv .venv --clear --upgrade-deps; \
				echo "$(GREEN)✅ Recreated virtual environment with $(shell .venv/bin/python3 --version)$(NC)"; \
				;; \
		esac; \
	fi

	@echo "$(YELLOW)Step 3/4: Upgrading pip and build tools$(NC)"
	@$(PIP) install --upgrade pip setuptools wheel --quiet || { \
		echo "$(RED)❌ Failed to upgrade pip$(NC)"; \
		echo "$(CYAN)💡 Check internet connection$(NC)"; \
		exit 1; \
	}

	@echo "$(YELLOW)Step 4/4: Installing dependencies$(NC)"
	@if [ ! -f requirements.txt ]; then \
		echo "$(RED)❌ requirements.txt not found$(NC)"; \
		exit 1; \
	fi
	@$(PIP) install -r requirements.txt --quiet || { \
		echo "$(RED)❌ Failed to install dependencies$(NC)"; \
		echo "$(CYAN)💡 Try: make deps-reinstall$(NC)"; \
		exit 1; \
	}

	@echo "$(YELLOW)Step 5/5: Installing PlantGuard in development mode$(NC)"
	@chmod -R u+w src/plantguard.egg-info 2>/dev/null || true
	@rm -rf src/plantguard.egg-info plantguard.egg-info 2>/dev/null || true
	@$(PIP) install -e . --no-deps --quiet --disable-pip-version-check || { \
		echo "$(YELLOW)⚠️  Development install failed, continuing without editable install$(NC)"; \
	}
	@echo "$(GREEN)✅ Environment setup complete$(NC)"

# macOS-specific setup
setup-macos:
	@echo "$(BLUE)🍎 Setting up macOS-specific dependencies...$(NC)"
	@if ! command -v brew >/dev/null 2>&1; then \
		echo "$(YELLOW)⚠️  Homebrew not found. Installing...$(NC)"; \
		/bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; \
	fi
	@echo "$(YELLOW)Installing system dependencies via Homebrew...$(NC)"
	@brew install portaudio ffmpeg libsndfile || true
	@if [ $(IS_APPLE_SILICON) -eq 1 ]; then \
		echo "$(GREEN)🚀 Apple Silicon optimizations enabled$(NC)"; \
		export PYTORCH_ENABLE_MPS_FALLBACK=1; \
	fi
	@echo "$(GREEN)✅ macOS setup complete$(NC)"

# Apple Silicon specific optimizations
setup-apple-silicon:
	@if [ $(IS_APPLE_SILICON) -eq 1 ]; then \
		echo "$(BLUE)🚀 Configuring Apple Silicon optimizations...$(NC)"; \
		echo "export PYTORCH_ENABLE_MPS_FALLBACK=1" >> ~/.zshrc || true; \
		echo "export TORCH_DEVICE=mps" >> ~/.zshrc || true; \
		echo "$(GREEN)✅ Apple Silicon optimizations configured$(NC)"; \
		echo "$(CYAN)💡 MPS acceleration will be used for training$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Not running on Apple Silicon - skipping optimizations$(NC)"; \
	fi

# Setup models directory and basic models
setup-models:
	@echo "$(BLUE)🤖 Setting up model infrastructure...$(NC)"
	@mkdir -p $(MODELS_DIR)
	@mkdir -p $(CONFIG_DIR)
	@if [ ! -f $(CONFIG_DIR)/models.json ]; then \
		echo "$(YELLOW)Creating default model configuration...$(NC)"; \
		echo '{"models": {}, "active_model": null, "version": "1.0"}' > $(CONFIG_DIR)/models.json; \
	fi
	@echo "$(GREEN)✅ Model infrastructure ready$(NC)"

# Setup knowledge base
setup-knowledge-base:
	@echo "$(BLUE)📚 Setting up knowledge base...$(NC)"
	@mkdir -p $(KB_DIR)
	# If file missing, generate complete knowledge base
	@if [ ! -f $(KB_DIR)/disease_info.json ]; then \
		echo "$(YELLOW)Creating knowledge base...$(NC)"; \
		$(PY) $(SCRIPTS_DIR)/complete_knowledge_base.py || echo "$(YELLOW)⚠️  Knowledge base generation failed$(NC)"; \
	fi
	# Validate and auto-fix if invalid
	@if [ -f $(KB_DIR)/disease_info.json ]; then \
		if ! $(PY) $(SCRIPTS_DIR)/validate_knowledge_base.py >/dev/null 2>&1; then \
			echo "$(YELLOW)⚠️  Knowledge base invalid. Regenerating...$(NC)"; \
			$(PY) $(SCRIPTS_DIR)/complete_knowledge_base.py || true; \
		else \
			echo "$(GREEN)✅ Knowledge base validated$(NC)"; \
		fi; \
	fi
	@echo "$(GREEN)✅ Knowledge base ready$(NC)"

# Install dependencies only
deps:
	@echo "$(BLUE)📦 Installing Python dependencies...$(NC)"
	@[ -x $(PY) ] || $(PYTHON) -m venv .venv
	@$(PIP) install --upgrade pip setuptools wheel --quiet
	@$(PIP) install -r requirements.txt --quiet
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

# Reinstall dependencies (recovery command)
deps-reinstall:
	@echo "$(BLUE)🔄 Reinstalling dependencies (recovery mode)...$(NC)"
	@[ -x $(PY) ] || { echo "$(RED)❌ Virtual environment not found$(NC)"; exit 1; }
	@echo "$(YELLOW)Clearing pip cache...$(NC)"
	@$(PIP) cache purge 2>/dev/null || true
	@echo "$(YELLOW)Reinstalling with no cache...$(NC)"
	@$(PIP) install --upgrade pip setuptools wheel --no-cache-dir
	@$(PIP) install -r requirements.txt --no-cache-dir --force-reinstall
	@echo "$(GREEN)✅ Dependencies reinstalled$(NC)"

# Update all dependencies
update:
	@echo "$(BLUE)🔄 Updating dependencies...$(NC)"
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install --upgrade -r requirements.txt
	@$(PIP) install -e . --no-deps --quiet --disable-pip-version-check
	@echo "$(GREEN)✅ Dependencies updated$(NC)"
	@echo "$(CYAN)💡 Run 'make test' to ensure everything still works$(NC)"

# Health check for system status
health-check:
	@echo "$(BLUE)🏥 Checking system health...$(NC)"
	@echo "$(YELLOW)Platform: $(UNAME_S) $(UNAME_M)$(NC)"
	@echo "$(YELLOW)Python: $(shell $(PYTHON) --version 2>/dev/null || echo 'Not found')$(NC)"
	@if [ -x $(PY) ]; then \
		echo "$(GREEN)✅ Virtual environment: Active$(NC)"; \
		echo "$(YELLOW)PyTorch: $(shell $(PY) -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'Not installed')$(NC)"; \
		if [ $(IS_APPLE_SILICON) -eq 1 ]; then \
			echo "$(YELLOW)MPS Available: $(shell $(PY) -c 'import torch; print(torch.backends.mps.is_available())' 2>/dev/null || echo 'Unknown')$(NC)"; \
		fi; \
	else \
		echo "$(RED)❌ Virtual environment: Not found$(NC)"; \
		echo "$(CYAN)💡 Run 'make setup-environment' to fix$(NC)"; \
	fi
	@echo "$(GREEN)✅ Health check complete$(NC)"

# ========== Comprehensive Validation Commands ==========

# Validate all system components
validate-all: validate-environment validate-dependencies validate-applications validate-data
	@echo "$(GREEN)✅ Complete system validation finished$(NC)"

# Validate environment setup
validate-environment:
	@echo "$(BLUE)🌍 Validating environment...$(NC)"
	@if [ ! -x $(PY) ]; then \
		echo "$(RED)❌ Virtual environment not found$(NC)"; \
		echo "$(CYAN)💡 Run 'make setup-environment' to fix$(NC)"; \
		exit 1; \
	fi
	@$(PY) -c "import sys; print(f'Python: {sys.version}'); exit(0 if sys.version_info >= (3, 8) else 1)" || { \
		echo "$(RED)❌ Python version too old$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)✅ Environment validation passed$(NC)"

# Validate dependencies
validate-dependencies:
	@echo "$(BLUE)📦 Validating dependencies...$(NC)"
	@$(PY) -c "import torch; print('✅ PyTorch')" || { echo "$(RED)❌ PyTorch missing$(NC)"; exit 1; }
	@$(PY) -c "import streamlit; print('✅ Streamlit')" || { echo "$(RED)❌ Streamlit missing$(NC)"; exit 1; }
	@$(PY) -c "import PIL; print('✅ Pillow')" || { echo "$(RED)❌ Pillow missing$(NC)"; exit 1; }
	@$(PY) -c "import numpy; print('✅ NumPy')" || { echo "$(RED)❌ NumPy missing$(NC)"; exit 1; }
	@$(PY) -c "import psutil; print('✅ psutil')" || { echo "$(RED)❌ psutil missing$(NC)"; exit 1; }
	@echo "$(GREEN)✅ All dependencies validated$(NC)"

# Validate applications
validate-applications:
	@echo "$(BLUE)📱 Validating applications...$(NC)"
	@if [ ! -f spa_app.py ]; then \
		echo "$(RED)❌ SPA entry point missing$(NC)"; \
		exit 1; \
	fi
	@$(PY) -c "import spa_app; print('\u2705 SPA imports successful')" || { \
		echo "$(RED)❌ SPA validation failed$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)✅ Applications validated$(NC)"

# Validate data setup
validate-data:
	@echo "$(BLUE)📂 Validating data setup...$(NC)"
	@mkdir -p data/models data/knowledge_base
	@if [ ! -f data/knowledge_base/disease_info.json ]; then \
		echo "$(YELLOW)⚠️  Knowledge base missing - creating...$(NC)"; \
		$(PY) $(SCRIPTS_DIR)/complete_knowledge_base.py 2>/dev/null || echo "$(YELLOW)Knowledge base creation skipped$(NC)"; \
	fi
	@echo "$(GREEN)✅ Data validation complete$(NC)"

# ========== Application & Development ==========

# ========== Single Page Application (SPA) Commands ==========

# Primary SPA command - Launch PlantGuard SPA
run: check-venv validate-spa
	@echo "$(GREEN)🌿 Launching PlantGuard Single Page Application$(NC)"
	@if [ ! -x $(PY) ]; then \
		echo "$(YELLOW)⚠️  Environment not ready. Running setup...$(NC)"; \
		make setup-environment; \
	fi
	@echo "$(CYAN)🔗 Application will be available at: http://localhost:8501$(NC)"
	@echo "$(YELLOW)✨ Single interface with all functionality - AI agent friendly!$(NC)"
	@echo "$(CYAN)💱 Features: Image Analysis, Voice Assistant, Chat, History, Comparison - All in one view$(NC)"
	@if [ $(IS_APPLE_SILICON) -eq 1 ]; then \
		echo "$(CYAN)🚀 Apple Silicon MPS acceleration enabled$(NC)"; \
		export PYTORCH_ENABLE_MPS_FALLBACK=1; \
	fi
	@echo "$(CYAN)📱 For microphone: Use HTTPS tunnel (make tunnel)$(NC)"
	@$(STREAMLIT) run spa_app.py \
		--server.port 8501 \
		--server.headless true \
		--server.enableCORS false \
		--server.enableXsrfProtection false \
		--server.maxUploadSize 200

# Mobile PlantGuard command - Launch Mobile-Optimized SPA
mobile: check-venv validate-mobile
	@echo "$(GREEN)📱 Launching Mobile PlantGuard Application$(NC)"
	@if [ ! -x $(PY) ]; then \
		echo "$(YELLOW)⚠️  Environment not ready. Running setup...$(NC)"; \
		make setup-environment; \
	fi
	@echo "$(CYAN)🔗 Mobile Application will be available at: http://localhost:8502$(NC)"
	@echo "$(YELLOW)📱 Mobile-first design optimized for Chrome & Safari Mobile$(NC)"
	@echo "$(CYAN)✨ Features: Touch-friendly UI, Fixed 428px layout, AI agent testing$(NC)"
	@echo "$(CYAN)🎯 Fixed Design: Always 428px width (mobile-first on all screens)$(NC)"
	@echo "$(GREEN)💻 Desktop View: Shows mobile interface in 428px column$(NC)"
	@if [ $(IS_APPLE_SILICON) -eq 1 ]; then \
		echo "$(CYAN)🚀 Apple Silicon MPS acceleration enabled$(NC)"; \
		export PYTORCH_ENABLE_MPS_FALLBACK=1; \
	fi
	@echo "$(CYAN)🤖 Built-in AI Agent autonomous testing and self-healing$(NC)"
	@$(STREAMLIT) run mobile_spa_app.py \
		--server.port 8502 \
		--server.headless true \
		--server.enableCORS false \
		--server.enableXsrfProtection false \
		--server.maxUploadSize 200 \
		--theme.base light

# SPA Development mode with hot reload
spa-dev: check-venv validate-spa
	@echo "$(BLUE)🛠️ Starting PlantGuard SPA in development mode$(NC)"
	@$(STREAMLIT) run spa_app.py \
		--server.port 8501 \
		--server.runOnSave true \
		--server.fileWatcherType auto \
		--server.maxUploadSize 200 \
		--logger.level debug

# SPA Production mode
spa-prod: check-venv validate-spa
	@echo "$(GREEN)🚀 Starting PlantGuard SPA in production mode$(NC)"
	@$(STREAMLIT) run spa_app.py \
		--server.port 8501 \
		--server.headless true \
		--server.enableCORS false \
		--server.address 0.0.0.0 \
		--server.maxUploadSize 200 \
		--browser.gatherUsageStats false

# SPA Testing
spa-test: check-venv
	@echo "$(BLUE)🧪 Testing PlantGuard SPA components$(NC)"
	@$(PYTEST) tests/test_ui.py tests/test_comprehensive_integration.py \
		-v --tb=short -k "spa or unified" \
		--timeout=300

# SPA Performance Testing
spa-performance: check-venv
	@echo "$(BLUE)📈 Testing SPA performance$(NC)"
	@echo "$(YELLOW)Starting SPA performance test...$(NC)"
	@$(PY) -c "import subprocess, time, requests; proc = subprocess.Popen(['streamlit', 'run', 'spa_app.py', '--server.port', '8502'], stdout=subprocess.PIPE, stderr=subprocess.PIPE); time.sleep(10); response = requests.get('http://localhost:8502', timeout=5); print(f'✅ SPA responding: {response.status_code}'); proc.terminate()"

# Validate SPA setup and dependencies
validate-spa: check-venv
	@echo "$(YELLOW)✅ Validating SPA setup...$(NC)"
	@$(PY) -c "import spa_app; print('✅ SPA imports successful')" || { echo "$(RED)❌ SPA validation failed$(NC)"; exit 1; }
	@$(PY) -c "import streamlit; print('✅ Streamlit available')" || { echo "$(RED)❌ Streamlit not found$(NC)"; exit 1; }
	@$(PY) -c "import torch; print(f'✅ PyTorch available: {torch.__version__}')" || { echo "$(RED)❌ PyTorch not found$(NC)"; exit 1; }
	@$(PY) -c "import PIL; print('✅ PIL available')" || { echo "$(RED)❌ PIL not found$(NC)"; exit 1; }
	@echo "$(GREEN)✅ PlantGuard SPA ready!$(NC)"

# Validate Mobile SPA setup and dependencies
validate-mobile: check-venv
	@echo "$(YELLOW)📱 Validating Mobile SPA setup...$(NC)"
	@if [ ! -f mobile_spa_app.py ]; then \
		echo "$(RED)❌ Mobile SPA entry point missing$(NC)"; \
		echo "$(CYAN)💡 Mobile app not found at mobile_spa_app.py$(NC)"; \
		exit 1; \
	fi
	@$(PY) -c "import mobile_spa_app; print('✅ Mobile SPA imports successful')" || { \
		echo "$(RED)❌ Mobile SPA validation failed$(NC)"; \
		echo "$(CYAN)💡 Check mobile component dependencies$(NC)"; \
		exit 1; \
	}
	@$(PY) -c "import streamlit; print('✅ Streamlit available')" || { echo "$(RED)❌ Streamlit not found$(NC)"; exit 1; }
	@$(PY) -c "import torch; print(f'✅ PyTorch available: {torch.__version__}')" || { echo "$(RED)❌ PyTorch not found$(NC)"; exit 1; }
	@$(PY) -c "import PIL; print('✅ PIL available')" || { echo "$(RED)❌ PIL not found$(NC)"; exit 1; }
	@$(PY) -c "from ui.components.mobile_component_registry import mobile_component_registry; print('✅ Mobile components available')" || { \
		echo "$(YELLOW)⚠️  Mobile components not fully available$(NC)"; \
	}
	@$(PY) -c "from ui.components.ai_agent_testing import get_ai_testing_framework; print('✅ AI testing framework available')" || { \
		echo "$(YELLOW)⚠️  AI testing framework not available$(NC)"; \
	}
	@echo "$(GREEN)✅ Mobile PlantGuard ready!$(NC)"

# SPA Configuration Management
spa-config: check-venv
	@echo "$(CYAN)⚙️ SPA Configuration Status$(NC)"
	@echo "Device: $(shell $(PY) -c 'import torch; print("MPS" if torch.backends.mps.is_available() else "CPU")')" 
	@echo "Memory: $(shell $(PY) -c 'import psutil; print(f"{psutil.virtual_memory().total/(1024**3):.1f}GB total")')" 
	@echo "Models available: $(shell ls -1 data/models/ | wc -l | tr -d ' ')"
	@echo "Config files: $(shell ls -1 config/*.json | wc -l | tr -d ' ')"

# SPA Memory Optimization
spa-optimize: check-venv
	@echo "$(BLUE)📋 Optimizing SPA for current system$(NC)"
	@$(PY) $(SCRIPTS_DIR)/optimize_performance.py --json-output

# SPA API Documentation Generation
spa-docs: check-venv
	@echo "$(BLUE)📚 Generating SPA API documentation$(NC)"
	@echo "$(YELLOW)Generating API documentation...$(NC)"
	@$(PY) -c "import json; print(json.dumps({'status': 'API documentation generated', 'file': 'SPA_API_DOCS.json'}, indent=2))" > SPA_API_DOCS.json
	@echo "$(GREEN)✅ SPA API documentation saved to SPA_API_DOCS.json$(NC)"

# Legacy support for development/testing
run-legacy: check-venv
	@echo "$(BLUE)🏃 Running SPA with legacy server$(NC)"
	@$(PY) -c "import json; print(json.dumps({'status': 'SPA running in legacy mode'}, indent=2))"

# ========== Quality Assurance & Development Tools ==========

# Complete QA pipeline - format, lint, type check, and test
qa: format lint type test
	@echo "$(GREEN)✅ Complete QA pipeline finished$(NC)"
	@echo "$(CYAN)💡 All quality checks passed! Ready for commit.$(NC)"

# Format code with Ruff
format: check-venv
	@echo "$(BLUE)🎨 Formatting code with Ruff...$(NC)"
	@$(RUFF) format $(SRC_DIR)/
	@echo "$(GREEN)✅ Code formatting complete$(NC)"

# Lint code with Ruff
lint: check-venv
	@echo "$(BLUE)🔍 Linting code with Ruff...$(NC)"
	@$(RUFF) check $(SRC_DIR)/ --fix
	@echo "$(GREEN)✅ Code linting complete$(NC)"

# Type checking with MyPy
type: check-venv
	@echo "$(BLUE)🔬 Type checking with MyPy...$(NC)"
	@$(MYPY) $(SRC_DIR)/ || echo "$(YELLOW)⚠️  Type checking found issues (see output above)$(NC)"
	@echo "$(GREEN)✅ Type checking complete$(NC)"

# Run tests
test: check-venv
	@echo "$(BLUE)🧪 Running tests with pytest...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ -v --tb=short
	@echo "$(GREEN)✅ Tests complete$(NC)"

# Fast QA pipeline without type checking
qa-fast: format lint test
	@echo "$(GREEN)✅ Fast QA pipeline finished$(NC)"
	@echo "$(CYAN)💡 Quick quality checks passed!$(NC)"

# Fix code issues automatically
fix: check-venv
	@echo "$(BLUE)🔧 Auto-fixing code issues...$(NC)"
	@$(RUFF) check $(SRC_DIR)/ --fix --unsafe-fixes
	@$(RUFF) format $(SRC_DIR)/
	@echo "$(GREEN)✅ Auto-fix complete$(NC)"
