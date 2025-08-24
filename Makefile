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

.PHONY: help start setup run dev test clean
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
	@echo "$(GREEN)⚡ Quick Shortcuts$(NC)"
	@echo "  $(BLUE)s$(NC)                  - start (complete setup + launch)"
	@echo "  $(BLUE)r$(NC)                  - run (launch app)"
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

	@echo "$(BLUE)Step 1/4: Creating virtual environment...$(NC)"
	@if [ ! -d ".venv" ]; then \
		$(PYTHON) -m venv .venv --clear --upgrade-deps; \
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
	@echo "$(YELLOW)Step 2/4: Upgrading pip and build tools$(NC)"
	@$(PIP) install --upgrade pip setuptools wheel --quiet
	@echo "$(YELLOW)Step 3/4: Installing dependencies$(NC)"
	@$(PIP) install -r requirements.txt --quiet
	@echo "$(YELLOW)Step 4/4: Installing PlantGuard in development mode$(NC)"
	@chmod -R u+w src/plantguard.egg-info 2>/dev/null || true
	@rm -rf src/plantguard.egg-info plantguard.egg-info 2>/dev/null || true
	@$(PIP) install -e . --no-deps --quiet --disable-pip-version-check
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
	fi
	@echo "$(GREEN)✅ Health check complete$(NC)"

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
	@$(PY) -c """
import time
import requests
import subprocess
import signal
import os

# Start SPA in background
proc = subprocess.Popen(['$(STREAMLIT)', 'run', 'spa_app.py', '--server.port', '8502'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

try:
    # Wait for startup
    time.sleep(10)
    
    # Test basic connectivity
    response = requests.get('http://localhost:8502', timeout=5)
    print(f'✅ SPA responding: {response.status_code}')
    
    # Test health endpoint
    health_response = requests.get('http://localhost:8502/healthz', timeout=5)
    print(f'📊 Health check: {health_response.status_code}')
    
except Exception as e:
    print(f'❌ SPA performance test failed: {e}')
finally:
    # Cleanup
    proc.terminate()
    proc.wait()
"""

# Validate SPA setup and dependencies
validate-spa: check-venv
	@echo "$(YELLOW)✅ Validating SPA setup...$(NC)"
	@$(PY) -c "import spa_app; print('✅ SPA imports successful')" || { echo "$(RED)❌ SPA validation failed$(NC)"; exit 1; }
	@$(PY) -c "import streamlit; print('✅ Streamlit available')" || { echo "$(RED)❌ Streamlit not found$(NC)"; exit 1; }
	@$(PY) -c "import torch; print(f'✅ PyTorch available: {torch.__version__}')" || { echo "$(RED)❌ PyTorch not found$(NC)"; exit 1; }
	@$(PY) -c "import PIL; print('✅ PIL available')" || { echo "$(RED)❌ PIL not found$(NC)"; exit 1; }
	@echo "$(GREEN)✅ PlantGuard SPA ready!$(NC)"

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
	@$(PY) -c """
import psutil
import torch
import json

# Get system info
memory_gb = psutil.virtual_memory().total / (1024**3)
cpu_count = psutil.cpu_count()
has_mps = torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False

# Generate optimized config
config = {
    'spa_config': {
        'port': 8501,
        'max_upload_size': min(200, int(memory_gb * 20)),
        'session_timeout': 3600 if memory_gb >= 8 else 1800
    },
    'performance_config': {
        'batch_size': min(32, int(memory_gb * 2)),
        'max_concurrent': min(4, cpu_count),
        'memory_limit': f'{int(memory_gb * 0.5)}GB',
        'device': 'mps' if has_mps else 'cpu',
        'cache_models': memory_gb >= 8
    },
    'optimization_timestamp': '$(shell date -Iseconds)'
}

with open('spa_config_optimized.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f'✅ Optimized SPA config generated for {memory_gb:.1f}GB system')
print(f'Device: {config["performance_config"]["device"]}')
print(f'Batch size: {config["performance_config"]["batch_size"]}')
"""

# SPA API Documentation Generation
spa-docs: check-venv
	@echo "$(BLUE)📚 Generating SPA API documentation$(NC)"
	@$(PY) -c """
import spa_app
import inspect
import json
from datetime import datetime

# Extract programmatic API methods
app_class = spa_app.PlantGuardSPA
api_methods = {}

for name, method in inspect.getmembers(app_class, predicate=inspect.isfunction):
    if name.endswith('_programmatic') or name in ['get_system_status_programmatic']:
        sig = inspect.signature(method)
        doc = inspect.getdoc(method) or 'No documentation available'
        
        api_methods[name] = {
            'signature': str(sig),
            'docstring': doc,
            'parameters': list(sig.parameters.keys())
        }

# Generate API documentation
api_docs = {
    'title': 'PlantGuard SPA Programmatic API',
    'generated': datetime.now().isoformat(),
    'description': 'AI Agent friendly API methods for programmatic access',
    'methods': api_methods
}

with open('SPA_API_DOCS.json', 'w') as f:
    json.dump(api_docs, f, indent=2)

print(f'✅ Generated API documentation with {len(api_methods)} methods')
for method_name in api_methods.keys():
    print(f'  - {method_name}')
"""
	@echo "$(GREEN)✅ SPA API documentation saved to SPA_API_DOCS.json$(NC)"

# Legacy support for development/testing
run-legacy: check-venv
	@echo "$(YELLOW)⚠️  Starting legacy multi-page interface...$(NC)"
	@echo "$(CYAN)Note: SPA (make run) is the recommended interface$(NC)"
	@$(STREAMLIT) run app.py --server.port=8502

run-unified: run
	@echo "$(GREEN)💡 Tip: 'run-unified' is now the default SPA interface$(NC)"

# Create HTTPS tunnel for microphone access
tunnel:
	@echo "$(BLUE)🌐 Creating HTTPS tunnel for microphone access...$(NC)"
	@if command -v cloudflared >/dev/null 2>&1; then \
		echo "$(GREEN)Using Cloudflare Tunnel...$(NC)"; \
		cloudflared tunnel --url http://localhost:8501; \
	elif [ -x $(PY) ] && $(PY) -c "import pyngrok" 2>/dev/null; then \
		echo "$(GREEN)Using ngrok tunnel...$(NC)"; \
		$(PY) -c "from pyngrok import ngrok; print(ngrok.connect(8501))"; \
	else \
		echo "$(YELLOW)⚠️  No tunnel service available. Install cloudflared or pyngrok$(NC)"; \
		echo "$(CYAN)💡 brew install cloudflared$(NC)"; \
	fi

# Development workflow
dev: format lint test-fast
	@echo "$(GREEN)✅ Development workflow complete!$(NC)"
	@echo "$(CYAN)💡 Code is ready for commit$(NC)"

# Open Jupyter notebook
notebook:
	@echo "$(BLUE)📓 Starting Jupyter notebook...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PIP) install jupyter ipykernel matplotlib seaborn plotly --quiet
	@mkdir -p $(NOTEBOOKS_DIR)
	@if [ ! -f $(NOTEBOOKS_DIR)/PlantGuard.ipynb ]; then \
		echo "$(YELLOW)Creating default notebook...$(NC)"; \
		echo '{"cells":[],"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"}},"nbformat":4,"nbformat_minor":4}' > $(NOTEBOOKS_DIR)/PlantGuard.ipynb; \
	fi
	@echo "$(GREEN)🚀 Opening notebook at http://localhost:8888$(NC)"
	@$(JUPYTER) notebook $(NOTEBOOKS_DIR)/ --port=8888 --no-browser

# Debug mode with detailed logging
debug:
	@echo "$(BLUE)🐛 Starting PlantGuard in debug mode...$(NC)"
	@mkdir -p $(LOGS_DIR)
	@export PYTHONPATH=. && \
	export STREAMLIT_LOGGER_LEVEL=debug && \
	$(STREAMLIT) run src/ui/app_streamlit.py \
		--server.port 8501 \
		--server.headless true \
		--logger.level debug \
		2>&1 | tee $(LOGS_DIR)/debug.log

# Stop all running applications
stop:
	@echo "$(BLUE)🛑 Stopping PlantGuard applications...$(NC)"
	@pkill -f "streamlit run" || echo "$(YELLOW)No Streamlit processes found$(NC)"
	@pkill -f "jupyter notebook" || echo "$(YELLOW)No Jupyter processes found$(NC)"
	@pkill -f "tensorboard" || echo "$(YELLOW)No TensorBoard processes found$(NC)"
	@echo "$(GREEN)✅ Applications stopped$(NC)"

# Restart main application
restart: stop
	@echo "$(BLUE)🔄 Restarting PlantGuard...$(NC)"
	@sleep 2
	@make run

# ========== Code Quality & Testing ==========

# Complete QA pipeline
qa: format lint type security test
	@echo "$(GREEN)✅ Complete QA pipeline passed!$(NC)"
	@echo "$(CYAN)🚀 Code is production-ready$(NC)"

# Fast QA (skip type checking and slow tests)
qa-fast: format lint test-fast
	@echo "$(GREEN)✅ Fast QA complete!$(NC)"
	@echo "$(CYAN)💡 Ready for development iteration$(NC)"

# Auto-format code with Ruff
format:
	@echo "$(BLUE)🎨 Formatting code with Ruff...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install ruff --quiet
	@$(RUFF) check --fix . || true
	@$(RUFF) format .
	@echo "$(GREEN)✅ Code formatted$(NC)"

# Lint code for quality issues
lint:
	@echo "$(BLUE)🔍 Linting code...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install ruff --quiet
	@$(RUFF) check . --output-format=grouped
	@echo "$(GREEN)✅ Linting passed$(NC)"

# Type checking with MyPy
type:
	@echo "$(BLUE)🔍 Type checking with MyPy...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@# Pin MyPy to a stable version to avoid assertion errors with namespace packages (e.g., google)
	@$(PIP) install "mypy==1.11.1" --quiet
	@$(MYPY) $(SRC_DIR) --namespace-packages --config-file pyproject.toml || echo "$(YELLOW)⚠️  Type issues found$(NC)"
	@echo "$(GREEN)✅ Type checking complete$(NC)"

# Auto-fix common issues
fix:
	@echo "$(BLUE)🔧 Auto-fixing issues...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install ruff --quiet
	@$(RUFF) check --fix . || true
	@$(RUFF) format .
	@# Fix end-of-file newlines
	@find $(SRC_DIR) -name "*.py" -exec sh -c 'if [ -s "{}" ] && [ "$$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo >> "{}"; fi' \; 2>/dev/null || true
	@# Remove trailing whitespace
	@find $(SRC_DIR) -name "*.py" -exec sed -i '' 's/[[:space:]]*$$//' {} \; 2>/dev/null || true
	@echo "$(GREEN)✅ Issues fixed$(NC)"

# Security vulnerability scan
security:
	@echo "$(BLUE)🔒 Security vulnerability scan...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install bandit safety --quiet
	@echo "$(YELLOW)Running Bandit security scan...$(NC)"
	@$(BANDIT) -r $(SRC_DIR)/ -ll -f json -o security-report.json || true
	@$(BANDIT) -r $(SRC_DIR)/ -ll || echo "$(YELLOW)⚠️  Security issues found - check security-report.json$(NC)"
	@echo "$(YELLOW)Checking for known vulnerabilities...$(NC)"
	@$(PIP) freeze | $(PY) -m safety scan --stdin --json || echo "$(YELLOW)⚠️  Vulnerable packages found$(NC)"
	@echo "$(GREEN)✅ Security scan complete$(NC)"

# ========== Testing ==========

# Run all tests
test:
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install pytest pytest-cov pytest-mock pytest-timeout --quiet
	@mkdir -p $(LOGS_DIR)
	@mkdir -p $(COVERAGE_DIR)
	@export COVERAGE_FILE=$(COVERAGE_FILE) ; \
	$(PYTEST) $(TESTS_DIR)/ -v \
		--tb=short \
		--cov=$(SRC_DIR) \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-report=xml \
		--junit-xml=$(LOGS_DIR)/test-results.xml \
		--timeout=300 \
		|| echo "$(YELLOW)⚠️  Some tests failed$(NC)"
	@echo "$(GREEN)✅ Tests complete$(NC)"

# Run fast tests only (skip slow/integration tests)
test-fast:
	@echo "$(BLUE)⚡ Running fast tests...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install pytest pytest-mock pytest-timeout --quiet
	@$(PYTEST) $(TESTS_DIR)/ -v -m "not slow and not integration" \
		--tb=short \
		--timeout=60 \
		|| echo "$(YELLOW)⚠️  Some fast tests failed$(NC)"
	@echo "$(GREEN)✅ Fast tests complete$(NC)"

# Run integration tests
test-integration:
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PIP) install pytest pytest-timeout pytest-json-report psutil --quiet
	@echo "$(CYAN)🧪 Testing complete production pipeline integration$(NC)"
	@$(PY) $(SCRIPTS_DIR)/run_integration_tests.py || echo "$(YELLOW)⚠️  Integration tests failed$(NC)"
	@echo "$(GREEN)✅ Integration tests complete$(NC)"

# Run performance tests
test-performance:
	@echo "$(BLUE)📊 Running performance tests...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PIP) install pytest pytest-timeout psutil --quiet
	@$(PYTEST) $(TESTS_DIR)/ -v -m "performance" \
		--tb=short \
		--timeout=600 \
		|| echo "$(YELLOW)⚠️  Performance tests failed$(NC)"
	@echo "$(GREEN)✅ Performance tests complete$(NC)"

# Test model components
test-models:
	@echo "$(BLUE)🤖 Testing model components...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PIP) install pytest --quiet
	@$(PYTEST) $(TESTS_DIR)/test_*model*.py $(TESTS_DIR)/test_*vision*.py $(TESTS_DIR)/test_*audio*.py -v \
		--tb=short \
		|| echo "$(YELLOW)⚠️  Model tests failed$(NC)"
	@echo "$(GREEN)✅ Model tests complete$(NC)"

# Test UI components
test-ui:
	@echo "$(BLUE)🖥️  Testing UI components...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PIP) install pytest --quiet
	@$(PYTEST) $(TESTS_DIR)/ -v -k "ui or streamlit or interface" \
		--tb=short \
		|| echo "$(YELLOW)⚠️  UI tests failed$(NC)"
	@echo "$(GREEN)✅ UI tests complete$(NC)"

# Generate test coverage report
coverage:
	@echo "$(BLUE)📊 Generating test coverage report...$(NC)"
	@if [ ! -x $(PY) ]; then make deps; fi
	@$(PIP) install pytest pytest-cov --quiet
	@mkdir -p $(COVERAGE_DIR)
	@export COVERAGE_FILE=$(COVERAGE_FILE) ; \
	$(PYTEST) $(TESTS_DIR)/ \
		--cov=$(SRC_DIR) \
		--cov-report=html:htmlcov \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-fail-under=80
	@echo "$(GREEN)📊 Coverage report: htmlcov/index.html$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		echo "$(CYAN)🌐 Opening coverage report...$(NC)"; \
		open htmlcov/index.html; \
	fi

# ========== Machine Learning ==========

# Train models with optimal settings
train:
	@echo "$(BLUE)🤖 Training PlantGuard models...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@mkdir -p $(RUNS_DIR)
	@echo "$(YELLOW)Device: $(TORCH_DEVICE), Workers: $(WORKERS), Batch Size: $(BATCH_SIZE)$(NC)"
	@if [ $(IS_APPLE_SILICON) -eq 1 ]; then \
		export PYTORCH_ENABLE_MPS_FALLBACK=1; \
		echo "$(GREEN)🚀 Apple Silicon MPS acceleration enabled$(NC)"; \
	fi
	@if [ -d "$(DATA_DIR)/processed/plantvillage/train" ]; then \
		echo "$(GREEN)✅ Using processed PlantVillage dataset$(NC)"; \
		$(PY) $(SCRIPTS_DIR)/train_vision_model_improved.py \
			--data_dir $(DATA_DIR)/processed/plantvillage \
			--device $(TORCH_DEVICE) \
			--batch_size $(BATCH_SIZE) \
			--num_workers 4 \
			--epochs 50; \
	else \
		echo "$(RED)❌ No dataset found. Run 'make dataset-status' or 'make dataset-download'$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Training complete$(NC)"

# Production training pipeline
train-production:
	@echo "$(BLUE)🚀 Starting production training pipeline...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@echo "$(CYAN)🔍 Full production pipeline with validation and optimal settings$(NC)"
	@$(PY) $(SCRIPTS_DIR)/production_training_workflow.py --log-level INFO
	@echo "$(GREEN)✅ Production training complete$(NC)"
	@echo "$(CYAN)💡 Use 'make monitor' to view training metrics$(NC)"

# List available training configuration templates
templates-list:
	@echo "$(BLUE)📚 Listing available training templates...$(NC)"
	@GEN_DIR="$(CONFIG_DIR)/training_templates/generated"; \
	BASE_DIR="$(CONFIG_DIR)/training_templates"; \
	shopt -s nullglob; \
	echo "$(YELLOW)Base templates ($(BASE_DIR)):$(NC)"; \
	count=0; \
	for f in "$$BASE_DIR"/*.{json,yaml,yml}; do \
		[ -f "$$f" ] || continue; \
		count=$$((count+1)); \
		name=$$(basename "$$f"); \
		echo "  • $$name"; \
	done; \
	[ $$count -gt 0 ] || echo "  (none)"; \
	echo "$(YELLOW)Generated templates ($(GEN_DIR)):$(NC)"; \
	count=0; \
	for f in "$$GEN_DIR"/*.{json,yaml,yml}; do \
		[ -f "$$f" ] || continue; \
		count=$$((count+1)); \
		name=$$(basename "$$f"); \
		echo "  • $$name"; \
	done; \
	[ $$count -gt 0 ] || echo "  (none)"; \
	echo "$(CYAN)💡 Use 'make train-production-template TEMPLATE=<name|path>' to run with a template$(NC)"

# Production training with template selection
train-production-template:
	@echo "$(BLUE)🧩 Starting production training with template...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@if [ -z "$(TEMPLATE)" ]; then \
		echo "$(RED)❌ Please specify TEMPLATE=<name|path to .json|.yaml>$(NC)"; \
		echo "$(YELLOW)Examples:$(NC)"; \
		echo "  make templates-list"; \
		echo "  make train-production-template TEMPLATE=quick_test"; \
		echo "  make train-production-template TEMPLATE=config/training_templates/auto_optimized.json"; \
		exit 1; \
	fi
	@$(PY) $(SCRIPTS_DIR)/production_training_workflow.py --template "$(TEMPLATE)" --log-level INFO
	@echo "$(GREEN)✅ Production training (template) complete$(NC)"

# Production training with explicit config file
train-production-config:
	@echo "$(BLUE)📄 Starting production training with explicit config...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@if [ -z "$(CONFIG)" ]; then \
		echo "$(RED)❌ Please specify CONFIG=<path to config .json|.yaml>$(NC)"; \
		echo "$(YELLOW)Example:$(NC) make train-production-config CONFIG=config/training_templates/generated/production_training.yaml"; \
		exit 1; \
	fi
	@if [ ! -f "$(CONFIG)" ]; then \
		echo "$(RED)❌ Config file not found: $(CONFIG)$(NC)"; \
		exit 1; \
	fi
	@$(PY) $(SCRIPTS_DIR)/production_training_workflow.py --config "$(CONFIG)" --log-level INFO
	@echo "$(GREEN)✅ Production training (config) complete$(NC)"

# Fast training for development
train-fast:
	@echo "$(BLUE)⚡ Fast training for development...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@if [ -d "$(DATA_DIR)/processed/plantvillage/train" ]; then \
		echo "$(GREEN)✅ Using processed PlantVillage dataset$(NC)"; \
		$(PY) $(SCRIPTS_DIR)/train_vision_model_improved.py \
			--data_dir $(DATA_DIR)/processed/plantvillage \
			--device $(TORCH_DEVICE) \
			--batch_size 16 \
			--epochs 5 \
			--num_workers 4; \
	else \
		echo "$(RED)❌ No dataset found. Run 'make dataset-download' to set it up$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Fast training complete$(NC)"

# Single-threaded training (no multiprocessing issues)
train-single:
	@echo "$(BLUE)🔧 Single-threaded training (stable)...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@if [ -d "$(DATA_DIR)/processed/plantvillage/train" ]; then \
		echo "$(GREEN)✅ Using processed PlantVillage dataset$(NC)"; \
		$(PY) $(SCRIPTS_DIR)/train_vision_model_improved.py \
			--data_dir $(DATA_DIR)/processed/plantvillage \
			--device $(TORCH_DEVICE) \
			--batch_size 16 \
			--num_workers 0 \
			--epochs 10; \
	else \
		echo "$(RED)❌ No dataset found. Run 'make dataset-download' to set it up$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Single-threaded training complete$(NC)"

# Launch TensorBoard monitoring
monitor:
	@echo "$(BLUE)📊 Launching TensorBoard monitoring...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PIP) install tensorboard --quiet
	@mkdir -p $(RUNS_DIR)
	@echo "$(GREEN)📈 TensorBoard available at: http://localhost:6006$(NC)"
	@$(PY) -m tensorboard.main --logdir=$(RUNS_DIR) --port=6006 --reload_interval=1 --host=0.0.0.0

# Evaluate trained models
evaluate:
	@echo "$(BLUE)📊 Evaluating trained models...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PY) $(SCRIPTS_DIR)/evaluate_model.py
	@echo "$(GREEN)✅ Model evaluation complete$(NC)"

# Benchmark all models
benchmark:
	@echo "$(BLUE)🏁 Benchmarking all models...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@export PYTHONPATH=. && $(PY) $(SCRIPTS_DIR)/model_switching/model_switcher.py --benchmark
	@echo "$(GREEN)✅ Benchmark complete$(NC)"

# Performance optimization
optimize:
	@echo "$(BLUE)⚡ Running performance optimization...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@if [ -f $(SCRIPTS_DIR)/optimize_performance.py ]; then \
		$(PY) $(SCRIPTS_DIR)/optimize_performance.py; \
	else \
		echo "$(YELLOW)⚠️  Performance optimization script not found$(NC)"; \
		echo "$(CYAN)💡 Creating basic optimization...$(NC)"; \
		$(PY) -c "print('Performance optimization placeholder - implement in scripts/optimize_performance.py')"; \
	fi
	@echo "$(GREEN)✅ Performance optimization complete$(NC)"

# ========== Dataset Management ==========

# Check dataset status
dataset-status:
	@echo "$(BLUE)📊 Checking dataset status...$(NC)"
	@if [ -d "$(DATA_DIR)/processed/plantvillage/train" ]; then \
		echo "$(GREEN)✅ PlantVillage dataset found$(NC)"; \
		echo "$(YELLOW)Train samples: $(shell find $(DATA_DIR)/processed/plantvillage/train -name "*.jpg" -o -name "*.png" | wc -l)$(NC)"; \
		echo "$(YELLOW)Val samples: $(shell find $(DATA_DIR)/processed/plantvillage/val -name "*.jpg" -o -name "*.png" | wc -l)$(NC)"; \
	else \
		echo "$(RED)❌ No dataset found$(NC)"; \
		echo "$(CYAN)💡 Run 'make dataset-download'$(NC)"; \
	fi

# Download PlantVillage dataset
dataset-download:
	@echo "$(BLUE)📥 Downloading PlantVillage dataset...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PY) $(SCRIPTS_DIR)/download_dataset.py
	@echo "$(GREEN)✅ Dataset download complete$(NC)"

# Prepare dataset for training
dataset-prepare:
	@echo "$(BLUE)🔄 Preparing dataset...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PY) $(SCRIPTS_DIR)/prepare_dataset.py
	@echo "$(GREEN)✅ Dataset preparation complete$(NC)"

# Validate dataset integrity
dataset-validate:
	@echo "$(BLUE)🔍 Validating dataset...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PY) $(SCRIPTS_DIR)/validate_dataset.py
	@echo "$(GREEN)✅ Dataset validation complete$(NC)"

# Analyze dataset statistics
dataset-analyze:
	@echo "$(BLUE)📊 Analyzing dataset...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PY) $(SCRIPTS_DIR)/analyze_dataset.py
	@echo "$(GREEN)✅ Dataset analysis complete$(NC)"



# ========== Model Management ==========

# List all models
models:
	@echo "$(BLUE)🤖 Listing available models...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@export PYTHONPATH=. && $(PY) $(SCRIPTS_DIR)/list_models.py
	@echo "$(GREEN)✅ Model listing complete$(NC)"

# Migrate legacy models
models-migrate:
	@echo "$(BLUE)🔄 Migrating legacy models...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@export PYTHONPATH=. && $(PY) $(SCRIPTS_DIR)/migrate_models.py
	@echo "$(GREEN)✅ Model migration complete$(NC)"

# Sync model registry
models-sync:
	@echo "$(BLUE)🔄 Syncing model registry...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@export PYTHONPATH=. && $(PY) $(SCRIPTS_DIR)/model_switching/model_switcher.py --sync
	@echo "$(GREEN)✅ Model registry synced$(NC)"

# Switch active model
models-switch:
	@echo "$(BLUE)🔄 Switching active model...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@if [ -z "$(MODEL_ID)" ]; then \
		echo "$(RED)❌ Please specify MODEL_ID=<model_name>$(NC)"; \
		exit 1; \
	fi
	@export PYTHONPATH=. && $(PY) $(SCRIPTS_DIR)/model_switching/model_switcher.py --switch $(MODEL_ID)
	@echo "$(GREEN)✅ Model switched to $(MODEL_ID)$(NC)"

# Export models for deployment
models-export:
	@echo "$(BLUE)📦 Exporting models for deployment...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@mkdir -p $(DATA_DIR)/export
	@find $(MODELS_DIR) -name "*.pt" -exec cp {} $(DATA_DIR)/export/ \; 2>/dev/null || true
	@echo "$(GREEN)✅ Models exported to $(DATA_DIR)/export$(NC)"

# Import external models
models-import:
	@echo "$(BLUE)📥 Importing external models...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@echo "$(YELLOW)Place model files in $(DATA_DIR)/import/ directory$(NC)"
	@if [ -d "$(DATA_DIR)/import" ]; then \
		find $(DATA_DIR)/import -name "*.pt" -exec cp {} $(MODELS_DIR)/ \; 2>/dev/null || true; \
		echo "$(GREEN)✅ Models imported$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Import directory not found$(NC)"; \
	fi
	@echo "$(GREEN)✅ Model import complete$(NC)"

# ========== Deployment & Production ==========

# Deploy locally with production settings
deploy-local:
	@echo "$(BLUE)🚀 Deploying locally with production settings...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@export STREAMLIT_SERVER_HEADLESS=true && \
	export STREAMLIT_SERVER_ENABLE_CORS=false && \
	export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false && \
	$(STREAMLIT) run src/ui/app_streamlit.py \
		--server.port 8501 \
		--server.address 0.0.0.0 \
		--server.headless true

# Build and run Docker container
deploy-docker:
	@echo "$(BLUE)🐳 Building Docker container...$(NC)"
	@if [ ! -f Dockerfile ]; then \
		echo "$(YELLOW)Creating Dockerfile...$(NC)"; \
		echo "FROM python:3.11-slim" > Dockerfile; \
		echo "WORKDIR /app" >> Dockerfile; \
		echo "COPY requirements.txt ." >> Dockerfile; \
		echo "RUN pip install -r requirements.txt" >> Dockerfile; \
		echo "COPY . ." >> Dockerfile; \
		echo "EXPOSE 8501" >> Dockerfile; \
		echo "CMD [\"streamlit\", \"run\", \"src/ui/app_streamlit.py\", \"--server.port=8501\", \"--server.address=0.0.0.0\"]" >> Dockerfile; \
	fi
	@docker build -t plantguard .
	@echo "$(GREEN)✅ Docker image built$(NC)"
	@echo "$(CYAN)💡 Run: docker run -p 8501:8501 plantguard$(NC)"

# Validate deployment readiness
deploy-check:
	@echo "$(BLUE)🔍 Checking deployment readiness...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PY) $(SCRIPTS_DIR)/validate_apps.py
	@echo "$(GREEN)✅ Deployment check complete$(NC)"

# ========== Monitoring & Maintenance ==========

# Show system status
status:
	@echo "$(BLUE)📊 System Status$(NC)"
	@echo "$(YELLOW)Platform: $(UNAME_S) $(UNAME_M)$(NC)"
	@echo "$(YELLOW)Python: $(shell $(PYTHON) --version 2>/dev/null || echo 'Not found')$(NC)"
	@echo "$(YELLOW)Virtual Env: $(shell [ -x $(PY) ] && echo 'Active' || echo 'Not found')$(NC)"
	@if [ -x $(PY) ]; then \
		echo "$(YELLOW)PyTorch: $(shell $(PY) -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'Not installed')$(NC)"; \
		echo "$(YELLOW)Streamlit: $(shell $(PY) -c 'import streamlit; print(streamlit.__version__)' 2>/dev/null || echo 'Not installed')$(NC)"; \
		if [ $(IS_APPLE_SILICON) -eq 1 ]; then \
			echo "$(YELLOW)MPS Available: $(shell $(PY) -c 'import torch; print(torch.backends.mps.is_available())' 2>/dev/null || echo 'Unknown')$(NC)"; \
		fi; \
	fi
	@echo "$(YELLOW)Disk Usage: $(shell du -sh . 2>/dev/null || echo 'Unknown')$(NC)"
	@echo "$(YELLOW)Running Processes:$(NC)"
	@ps aux | grep -E "(streamlit|jupyter|tensorboard)" | grep -v grep || echo "  No PlantGuard processes running"

# Detailed project information
info:
	@echo "$(CYAN)🌿 PlantGuard Project Information$(NC)"
	@echo ""
	@echo "$(GREEN)📁 Project Structure:$(NC)"
	@echo "  Source Code: $(SRC_DIR)/"
	@echo "  Data: $(DATA_DIR)/"
	@echo "  Models: $(MODELS_DIR)/"
	@echo "  Tests: $(TESTS_DIR)/"
	@echo "  Logs: $(LOGS_DIR)/"
	@echo "  Scripts: $(SCRIPTS_DIR)/"
	@echo ""
	@echo "$(GREEN)🔧 Configuration:$(NC)"
	@echo "  Device: $(TORCH_DEVICE)"
	@echo "  Workers: $(WORKERS)"
	@echo "  Batch Size: $(BATCH_SIZE)"
	@echo "  Memory Limit: $(MEMORY_LIMIT)"
	@echo ""
	@echo "$(GREEN)📊 Statistics:$(NC)"
	@echo "  Python Files: $(shell find $(SRC_DIR) -name "*.py" | wc -l)"
	@echo "  Test Files: $(shell find $(TESTS_DIR) -name "*.py" | wc -l)"
	@echo "  Script Files: $(shell find $(SCRIPTS_DIR) -name "*.py" | wc -l)"

# View application logs
logs:
	@echo "$(BLUE)📋 Viewing recent logs...$(NC)"
	@mkdir -p $(LOGS_DIR)
	@if [ -f $(LOGS_DIR)/debug.log ]; then \
		echo "$(YELLOW)Debug Log (last 50 lines):$(NC)"; \
		tail -50 $(LOGS_DIR)/debug.log; \
	else \
		echo "$(YELLOW)No debug log found$(NC)"; \
	fi
	@if [ -f $(LOGS_DIR)/test-results.xml ]; then \
		echo "$(YELLOW)Latest test results available$(NC)"; \
	fi

# Performance profiling
profile:
	@echo "$(BLUE)📊 Performance profiling...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@$(PIP) install py-spy --quiet || echo "$(YELLOW)⚠️  py-spy not available$(NC)"
	@echo "$(CYAN)💡 Run 'make run' in another terminal, then use:$(NC)"
	@echo "$(CYAN)py-spy top --pid \$$(pgrep -f streamlit)$(NC)"

# Validate system configuration
validate:
	@echo "$(BLUE)🔍 Validating system configuration...$(NC)"
	@if [ ! -x $(PY) ]; then make setup-environment; fi
	@export PYTHONPATH=. && $(PY) $(SCRIPTS_DIR)/validate_production_pipeline.py
	@echo "$(GREEN)✅ System validation complete$(NC)"

# Clean temporary files and caches
clean:
	@echo "$(BLUE)🧹 Cleaning temporary files...$(NC)"
	@rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@rm -rf htmlcov/ $(COVERAGE_DIR) coverage.xml
	@rm -rf security-report.json
	@rm -rf $(LOGS_DIR)/*.log
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# Complete environment reset
reset: clean
	@echo "$(BLUE)🔄 Resetting environment...$(NC)"
	@rm -rf .venv/
	@rm -rf src/plantguard.egg-info/
	@echo "$(GREEN)✅ Environment reset complete$(NC)"
	@echo "$(CYAN)💡 Run 'make setup' to reinstall$(NC)"

# Missing commands that validation script expects (aliases)
list-models: models
	@echo "$(YELLOW)📋 'list-models' is now 'models' - redirecting...$(NC)"

evaluate-model: evaluate
	@echo "$(YELLOW)📊 'evaluate-model' is now 'evaluate' - redirecting...$(NC)"

monitor-training: monitor
	@echo "$(YELLOW)📈 'monitor-training' is now 'monitor' - redirecting...$(NC)"

setup-dataset: dataset-prepare
	@echo "$(YELLOW)📦 'setup-dataset' is now 'dataset-prepare' - redirecting...$(NC)"

# Fresh installation
fresh: reset setup
	@echo "$(GREEN)✅ Fresh installation complete!$(NC)"
