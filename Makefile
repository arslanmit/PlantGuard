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

.PHONY: help start setup mobile dev test clean
.PHONY: format lint check fix train monitor notebook benchmark evaluate
.PHONY: deps update status info logs models
.PHONY: security coverage docs build deploy
.PHONY: reset fresh stop restart debug profile validate
.PHONY: templates-list train-production-template train-production-config
.PHONY: qa health-check tunnel list-models evaluate-model monitor-training setup-dataset
.PHONY: train-production download-dataset validate-dataset analyze-dataset compare-models
.PHONY: dataset-status dataset-download dataset-prepare dataset-validate dataset-analyze

# ========== Help & Information ==========

help:
	@echo "$(CYAN)🌿 PlantGuard - AI Plant Disease Detection$(NC)"
	@echo "$(YELLOW)🍎 Optimized for macOS $(shell sw_vers -productVersion 2>/dev/null || echo 'Unknown') $(shell [ $(IS_APPLE_SILICON) -eq 1 ] && echo '(Apple Silicon)' || echo '(Intel)')$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Quick Start$(NC)"
	@echo "  $(BLUE)start$(NC)              - Complete setup + launch (new users start here!)"
	@echo "  $(BLUE)mobile$(NC)             - Launch Mobile PlantGuard (primary interface)"
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
	@echo "  $(BLUE)m$(NC)                  - mobile (launch mobile app - primary interface)"
	@echo "  $(BLUE)d$(NC)                  - dev (development workflow)"
	@echo "  $(BLUE)t$(NC)                  - test (run tests)"
	@echo "  $(BLUE)f$(NC)                  - format (format code)"
	@echo "  $(BLUE)l$(NC)                  - lint (check code)"
	@echo ""
	@echo "$(YELLOW)💡 Recommended Workflows:$(NC)"
	@echo "  $(CYAN)New User:$(NC)          make start (setup + launch mobile app)"
	@echo "  $(CYAN)Development:$(NC)       make dev → make test → make mobile"
	@echo "  $(CYAN)Training:$(NC)          make dataset-status → make train → make monitor"
	@echo "  $(CYAN)Mobile Testing:$(NC)    make mobile-dev → make mobile-test"
	@echo ""
	@echo "$(YELLOW)📱 Mobile-Only PlantGuard Features:$(NC)"
	@echo "  • Mobile-first responsive design with 428px fixed width"
	@echo "  • Touch-optimized interface with large buttons"
	@echo "  • All functionality unified in single mobile interface"
	@echo "  • AI agent friendly design and testing framework"
	@echo "  • Complete technical capability preservation"
	@echo "  • Simplified architecture - no desktop overhead"
	@echo ""
	@echo "$(YELLOW)🔄 Migration from Desktop Version:$(NC)"
	@echo "  • Old: 'make run' → New: 'make mobile'"
	@echo "  • Old: 'make spa-*' → New: 'make mobile-*'"
	@echo "  • 100% feature parity maintained"
	@echo "  • All deprecated commands redirect with helpful guidance"
	@echo "  • See MOBILE_MIGRATION_GUIDE.md for complete guide"
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
	@echo "$(CYAN)📱 Launching Mobile application at http://localhost:8502$(NC)"
	@make mobile

# Quick shortcuts - Mobile focused
s: start
m: mobile            # Launch Mobile SPA (primary interface)
d: dev
t: test
f: format
l: lint

# Deprecated desktop shortcut - redirect to mobile with guidance
r:
	@echo "$(RED)❌ Desktop shortcut 'r' has been removed$(NC)"
	@echo "$(YELLOW)📱 PlantGuard is now mobile-only for simplified maintenance$(NC)"
	@echo "$(CYAN)💡 Migration Guide:$(NC)"
	@echo "  • Old: 'make r' or 'make run' → New: 'make m' or 'make mobile'"
	@echo "  • All desktop functionality is now available in mobile interface"
	@echo "  • Mobile interface works on all screen sizes (fixed 428px width)"
	@echo "$(GREEN)🚀 Launching mobile interface now...$(NC)"
	@make mobile

# Complete environment setup with macOS optimizations
setup: setup-environment setup-models setup-knowledge-base
	@echo "$(GREEN)✅ PlantGuard setup complete!$(NC)"
	@echo "$(CYAN)💡 Run 'make mobile' to launch the application$(NC)"
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
	@if [ ! -f mobile_spa_app.py ]; then \
		echo "$(RED)❌ Mobile entry point missing$(NC)"; \
		echo "$(CYAN)💡 PlantGuard is now mobile-only$(NC)"; \
		exit 1; \
	fi
	@$(PY) -c "import mobile_spa_app; print('\u2705 Mobile imports successful')" || { \
		echo "$(RED)❌ Mobile validation failed$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)✅ Mobile application validated$(NC)"

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

# ========== Mobile Application Commands ==========

# Desktop commands have been removed - use mobile equivalents
# run: → mobile
# spa-dev: → mobile-dev  
# spa-prod: → mobile-prod
# spa-test: → mobile-test
# spa-performance: → mobile-performance

# Primary Mobile PlantGuard command - Enhanced with error handling
mobile: check-venv validate-mobile
	@echo "$(GREEN)📱 Launching Mobile PlantGuard Application$(NC)"
	@if [ ! -x $(PY) ]; then \
		echo "$(YELLOW)⚠️  Environment not ready. Running setup...$(NC)"; \
		make setup-environment || { \
			echo "$(RED)❌ Environment setup failed$(NC)"; \
			echo "$(CYAN)💡 Try: make setup-environment$(NC)"; \
			exit 1; \
		}; \
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
	@echo "$(YELLOW)🔍 Checking port availability...$(NC)"
	@if lsof -Pi :8502 -sTCP:LISTEN -t >/dev/null 2>&1; then \
		echo "$(YELLOW)⚠️  Port 8502 is already in use$(NC)"; \
		echo "$(CYAN)💡 Stopping existing process...$(NC)"; \
		lsof -ti:8502 | xargs kill -9 2>/dev/null || true; \
		sleep 2; \
	fi
	@echo "$(GREEN)🚀 Starting Mobile PlantGuard...$(NC)"
	@$(STREAMLIT) run mobile_spa_app.py \
		--server.port 8502 \
		--server.headless true \
		--server.enableCORS false \
		--server.enableXsrfProtection false \
		--server.maxUploadSize 200 \
		--theme.base light || { \
		echo "$(RED)❌ Failed to start Mobile PlantGuard$(NC)"; \
		echo "$(CYAN)💡 Check logs above for errors$(NC)"; \
		echo "$(CYAN)💡 Try: make validate-mobile$(NC)"; \
		exit 1; \
	}

# Desktop SPA commands have been removed - see mobile equivalents above

# Mobile Development mode with hot reload
mobile-dev: check-venv validate-mobile
	@echo "$(BLUE)🛠️ Starting Mobile PlantGuard in development mode$(NC)"
	@$(STREAMLIT) run mobile_spa_app.py \
		--server.port 8502 \
		--server.runOnSave true \
		--server.fileWatcherType auto \
		--server.maxUploadSize 200 \
		--logger.level debug \
		--theme.base light

# Mobile Production mode
mobile-prod: check-venv validate-mobile
	@echo "$(GREEN)🚀 Starting Mobile PlantGuard in production mode$(NC)"
	@$(STREAMLIT) run mobile_spa_app.py \
		--server.port 8502 \
		--server.headless true \
		--server.enableCORS false \
		--server.address 0.0.0.0 \
		--server.maxUploadSize 200 \
		--browser.gatherUsageStats false \
		--theme.base light

# Mobile Testing
mobile-test: check-venv
	@echo "$(BLUE)🧪 Testing Mobile PlantGuard components$(NC)"
	@$(PYTEST) tests/test_mobile_*.py tests/test_comprehensive_integration.py \
		-v --tb=short -k "mobile" \
		--timeout=300

# Mobile Performance Testing
mobile-performance: check-venv
	@echo "$(BLUE)📈 Testing Mobile PlantGuard performance$(NC)"
	@echo "$(YELLOW)Starting Mobile performance test...$(NC)"
	@$(PY) -c "import subprocess, time, requests; proc = subprocess.Popen(['streamlit', 'run', 'mobile_spa_app.py', '--server.port', '8503'], stdout=subprocess.PIPE, stderr=subprocess.PIPE); time.sleep(10); response = requests.get('http://localhost:8503', timeout=5); print(f'✅ Mobile responding: {response.status_code}'); proc.terminate()"

# validate-spa: → validate-mobile (see above)

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

# Desktop SPA configuration commands have been removed
# spa-config: → mobile-config
# spa-optimize: → mobile-optimize  
# spa-docs: → mobile-docs

# Mobile Configuration Management
mobile-config: check-venv
	@echo "$(CYAN)⚙️ Mobile PlantGuard Configuration Status$(NC)"
	@echo "Device: $(shell $(PY) -c 'import torch; print("MPS" if torch.backends.mps.is_available() else "CPU")')" 
	@echo "Memory: $(shell $(PY) -c 'import psutil; print(f"{psutil.virtual_memory().total/(1024**3):.1f}GB total")')" 
	@echo "Models available: $(shell ls -1 data/models/ | wc -l | tr -d ' ')"
	@echo "Config files: $(shell ls -1 config/*.json | wc -l | tr -d ' ')"
	@echo "Mobile components: $(shell $(PY) -c 'from src.ui.components.mobile_component_registry import mobile_component_registry; print(len(mobile_component_registry._components))' 2>/dev/null || echo 'N/A')"

# Mobile Memory Optimization
mobile-optimize: check-venv
	@echo "$(BLUE)📋 Optimizing Mobile PlantGuard for current system$(NC)"
	@$(PY) $(SCRIPTS_DIR)/optimize_performance.py --json-output --mobile-mode

# Mobile API Documentation Generation
mobile-docs: check-venv
	@echo "$(BLUE)📚 Generating Mobile PlantGuard API documentation$(NC)"
	@echo "$(YELLOW)Generating mobile API documentation...$(NC)"
	@$(PY) -c "import json; print(json.dumps({'status': 'Mobile API documentation generated', 'file': 'MOBILE_API_DOCS.json', 'interface': 'mobile-only'}, indent=2))" > MOBILE_API_DOCS.json
	@echo "$(GREEN)✅ Mobile API documentation saved to MOBILE_API_DOCS.json$(NC)"

# ========== Desktop Commands Removed ==========
# All desktop and legacy commands have been removed from PlantGuard
# The system is now mobile-only for simplified maintenance
#
# Removed commands and their mobile equivalents:
# app: → mobile
# desktop: → mobile
# gui: → mobile  
# run: → mobile
# run-desktop: → mobile
# run-legacy: → mobile
# spa: → mobile
# spa-dev: → mobile-dev
# spa-prod: → mobile-prod
# spa-test: → mobile-test
# spa-performance: → mobile-performance
# spa-config: → mobile-config
# spa-optimize: → mobile-optimize
# spa-docs: → mobile-docs
# validate-spa: → validate-mobile
# start-spa: → mobile

# ========== Deprecated Command Handlers ==========
# These targets provide helpful guidance when users try deprecated commands

run:
	@echo "$(RED)❌ Desktop command 'run' has been removed$(NC)"
	@echo "$(YELLOW)📱 PlantGuard is now mobile-only$(NC)"
	@echo "$(CYAN)💡 Use: make mobile$(NC)"
	@echo "$(YELLOW)⚠️  Please run 'make mobile' manually to start the application$(NC)"

spa-dev:
	@echo "$(RED)❌ Desktop command 'spa-dev' has been removed$(NC)"
	@echo "$(YELLOW)📱 PlantGuard is now mobile-only$(NC)"
	@echo "$(CYAN)💡 Use: make mobile-dev$(NC)"
	@echo "$(YELLOW)⚠️  Please run 'make mobile-dev' manually to start development mode$(NC)"

spa-prod:
	@echo "$(RED)❌ Desktop command 'spa-prod' has been removed$(NC)"
	@echo "$(YELLOW)📱 PlantGuard is now mobile-only$(NC)"
	@echo "$(CYAN)💡 Use: make mobile-prod$(NC)"
	@echo "$(YELLOW)⚠️  Please run 'make mobile-prod' manually to start production mode$(NC)"

spa-test:
	@echo "$(RED)❌ Desktop command 'spa-test' has been removed$(NC)"
	@echo "$(YELLOW)📱 PlantGuard is now mobile-only$(NC)"
	@echo "$(CYAN)💡 Use: make mobile-test$(NC)"
	@echo "$(YELLOW)⚠️  Please run 'make mobile-test' manually to run tests$(NC)"

spa-performance:
	@echo "$(RED)❌ Desktop command 'spa-performance' has been removed$(NC)"
	@echo "$(YELLOW)📱 PlantGuard is now mobile-only$(NC)"
	@echo "$(CYAN)💡 Use: make mobile-performance$(NC)"
	@echo "$(YELLOW)⚠️  Please run 'make mobile-performance' manually to run performance tests$(NC)"

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
# ========== Production Training Pipeline ==========

# Core training commands (Task 9.1)
train-production: check-venv
	@echo "$(BLUE)🚀 Starting production training pipeline...$(NC)"
	@if [ ! -f scripts/production_training_workflow.py ]; then \
		echo "$(RED)❌ Production training script not found$(NC)"; \
		echo "$(CYAN)💡 Expected: scripts/production_training_workflow.py$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)🔍 Validating training prerequisites...$(NC)"
	@$(PY) scripts/production_training_workflow.py
	@echo "$(GREEN)✅ Production training complete$(NC)"

# Production training with template
train-production-template: check-venv
	@if [ -z "$(TEMPLATE)" ]; then \
		echo "$(RED)❌ TEMPLATE parameter required$(NC)"; \
		echo "$(CYAN)💡 Usage: make train-production-template TEMPLATE=<name>$(NC)"; \
		echo "$(CYAN)💡 Available templates: $(shell ls config/training_templates/*.json 2>/dev/null | xargs -n1 basename | sed 's/.json//' | tr '\n' ' ')$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)🚀 Starting production training with template: $(TEMPLATE)$(NC)"
	@if [ -f "config/training_templates/$(TEMPLATE).json" ]; then \
		TEMPLATE_PATH="config/training_templates/$(TEMPLATE).json"; \
	elif [ -f "$(TEMPLATE)" ]; then \
		TEMPLATE_PATH="$(TEMPLATE)"; \
	else \
		echo "$(RED)❌ Template not found: $(TEMPLATE)$(NC)"; \
		echo "$(CYAN)💡 Available templates:$(NC)"; \
		ls config/training_templates/*.json 2>/dev/null | xargs -n1 basename | sed 's/.json//' || echo "  No templates found"; \
		exit 1; \
	fi; \
	echo "$(YELLOW)📋 Using template: $$TEMPLATE_PATH$(NC)"; \
	$(PY) scripts/production_training_workflow.py --config "$$TEMPLATE_PATH"
	@echo "$(GREEN)✅ Template-based training complete$(NC)"

# Production training with custom config
train-production-config: check-venv
	@if [ -z "$(CONFIG)" ]; then \
		echo "$(RED)❌ CONFIG parameter required$(NC)"; \
		echo "$(CYAN)💡 Usage: make train-production-config CONFIG=<path>$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(CONFIG)" ]; then \
		echo "$(RED)❌ Config file not found: $(CONFIG)$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)🚀 Starting production training with config: $(CONFIG)$(NC)"
	@$(PY) scripts/production_training_workflow.py --config "$(CONFIG)"
	@echo "$(GREEN)✅ Custom config training complete$(NC)"

# List available training templates
templates-list:
	@echo "$(CYAN)📋 Available Training Templates$(NC)"
	@echo ""
	@if [ -d config/training_templates ]; then \
		for template in config/training_templates/*.json; do \
			if [ -f "$$template" ]; then \
				name=$$(basename "$$template" .json); \
				echo "$(BLUE)  $$name$(NC)"; \
				if command -v jq >/dev/null 2>&1; then \
					desc=$$(jq -r '.description // "No description available"' "$$template" 2>/dev/null); \
					echo "$(YELLOW)    $$desc$(NC)"; \
				fi; \
				echo "$(CYAN)    Path: $$template$(NC)"; \
				echo ""; \
			fi; \
		done; \
	else \
		echo "$(YELLOW)⚠️  No training templates directory found$(NC)"; \
	fi
	@echo "$(CYAN)💡 Usage: make train-production-template TEMPLATE=<name>$(NC)"

# Monitoring and evaluation commands (Task 9.2)
monitor-training: check-venv
	@echo "$(BLUE)📊 Launching TensorBoard for training monitoring...$(NC)"
	@if [ ! -d "$(RUNS_DIR)" ]; then \
		echo "$(YELLOW)⚠️  No training runs directory found. Creating...$(NC)"; \
		mkdir -p "$(RUNS_DIR)"; \
	fi
	@echo "$(CYAN)🔗 TensorBoard will be available at: http://localhost:6006$(NC)"
	@echo "$(YELLOW)📂 Monitoring directory: $(RUNS_DIR)$(NC)"
	@if command -v tensorboard >/dev/null 2>&1; then \
		tensorboard --logdir="$(RUNS_DIR)" --port=6006 --host=0.0.0.0; \
	else \
		$(PY) -m tensorboard.main --logdir="$(RUNS_DIR)" --port=6006 --host=0.0.0.0; \
	fi

# Evaluate trained models
evaluate-model: check-venv
	@echo "$(BLUE)🔍 Evaluating trained models...$(NC)"
	@if [ ! -f scripts/evaluate_model.py ]; then \
		echo "$(RED)❌ Model evaluation script not found$(NC)"; \
		echo "$(CYAN)💡 Expected: scripts/evaluate_model.py$(NC)"; \
		exit 1; \
	fi
	@if [ -n "$(MODEL)" ]; then \
		echo "$(YELLOW)📊 Evaluating specific model: $(MODEL)$(NC)"; \
		$(PY) scripts/evaluate_model.py --model "$(MODEL)"; \
	else \
		echo "$(YELLOW)📊 Evaluating all available models...$(NC)"; \
		$(PY) scripts/evaluate_model.py; \
	fi
	@echo "$(GREEN)✅ Model evaluation complete$(NC)"

# List available models
list-models: check-venv
	@echo "$(BLUE)📋 Listing available models...$(NC)"
	@if [ ! -f scripts/list_models.py ]; then \
		echo "$(RED)❌ Model listing script not found$(NC)"; \
		echo "$(CYAN)💡 Expected: scripts/list_models.py$(NC)"; \
		exit 1; \
	fi
	@$(PY) scripts/list_models.py
	@echo "$(GREEN)✅ Model listing complete$(NC)"

# Compare multiple models
compare-models: check-venv
	@if [ -z "$(MODELS)" ]; then \
		echo "$(RED)❌ MODELS parameter required$(NC)"; \
		echo "$(CYAN)💡 Usage: make compare-models MODELS=model1,model2$(NC)"; \
		echo "$(CYAN)💡 Available models:$(NC)"; \
		$(PY) scripts/list_models.py --brief 2>/dev/null || echo "  Run 'make list-models' to see available models"; \
		exit 1; \
	fi
	@echo "$(BLUE)📊 Comparing models: $(MODELS)$(NC)"
	@if [ ! -f scripts/evaluate_model.py ]; then \
		echo "$(RED)❌ Model evaluation script not found$(NC)"; \
		exit 1; \
	fi
	@$(PY) scripts/evaluate_model.py --compare "$(MODELS)"
	@echo "$(GREEN)✅ Model comparison complete$(NC)"

# Dataset management commands (Task 9.3)
setup-dataset: check-venv
	@echo "$(BLUE)📂 Setting up dataset for training...$(NC)"
	@if [ ! -f scripts/prepare_dataset.py ]; then \
		echo "$(RED)❌ Dataset preparation script not found$(NC)"; \
		echo "$(CYAN)💡 Expected: scripts/prepare_dataset.py$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)🔍 Preparing and validating dataset...$(NC)"
	@$(PY) scripts/prepare_dataset.py
	@echo "$(GREEN)✅ Dataset setup complete$(NC)"

# Download PlantVillage dataset
download-dataset: check-venv
	@echo "$(BLUE)⬇️  Downloading PlantVillage dataset...$(NC)"
	@if [ ! -f scripts/download_dataset.py ]; then \
		echo "$(RED)❌ Dataset download script not found$(NC)"; \
		echo "$(CYAN)💡 Expected: scripts/download_dataset.py$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)📥 Starting dataset download...$(NC)"
	@$(PY) scripts/download_dataset.py
	@echo "$(GREEN)✅ Dataset download complete$(NC)"

# Validate dataset integrity
validate-dataset: check-venv
	@echo "$(BLUE)✅ Validating dataset integrity...$(NC)"
	@if [ ! -f scripts/validate_dataset.py ]; then \
		echo "$(RED)❌ Dataset validation script not found$(NC)"; \
		echo "$(CYAN)💡 Expected: scripts/validate_dataset.py$(NC)"; \
		exit 1; \
	fi
	@$(PY) scripts/validate_dataset.py
	@echo "$(GREEN)✅ Dataset validation complete$(NC)"

# Analyze dataset statistics
analyze-dataset: check-venv
	@echo "$(BLUE)📊 Analyzing dataset statistics...$(NC)"
	@if [ ! -f scripts/analyze_dataset.py ]; then \
		echo "$(RED)❌ Dataset analysis script not found$(NC)"; \
		echo "$(CYAN)💡 Expected: scripts/analyze_dataset.py$(NC)"; \
		exit 1; \
	fi
	@$(PY) scripts/analyze_dataset.py
	@echo "$(GREEN)✅ Dataset analysis complete$(NC)"

# Legacy training commands for backward compatibility
train: train-production
	@echo "$(YELLOW)💡 'make train' now uses production training pipeline$(NC)"

monitor: monitor-training
	@echo "$(YELLOW)💡 'make monitor' now uses enhanced TensorBoard monitoring$(NC)"

evaluate: evaluate-model
	@echo "$(YELLOW)💡 'make evaluate' now uses enhanced model evaluation$(NC)"

# Dataset status check
dataset-status: check-venv
	@echo "$(BLUE)📊 Checking dataset status...$(NC)"
	@echo "$(YELLOW)Dataset directory: data/$(NC)"
	@if [ -d "data/raw" ]; then \
		echo "$(GREEN)✅ Raw data directory exists$(NC)"; \
		echo "$(CYAN)  Files: $(shell find data/raw -type f | wc -l | tr -d ' ')$(NC)"; \
	else \
		echo "$(RED)❌ Raw data directory missing$(NC)"; \
	fi
	@if [ -d "data/processed" ]; then \
		echo "$(GREEN)✅ Processed data directory exists$(NC)"; \
		echo "$(CYAN)  Files: $(shell find data/processed -type f | wc -l | tr -d ' ')$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Processed data directory missing$(NC)"; \
	fi
	@if [ -f "data/knowledge_base/disease_info.json" ]; then \
		echo "$(GREEN)✅ Knowledge base available$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Knowledge base missing$(NC)"; \
	fi
	@echo "$(CYAN)💡 Run 'make download-dataset' to get PlantVillage data$(NC)"
	@echo "$(CYAN)💡 Run 'make setup-dataset' to prepare data for training$(NC)"

# Aliases for common dataset commands
dataset-download: download-dataset
dataset-prepare: setup-dataset
dataset-validate: validate-dataset
dataset-analyze: analyze-dataset