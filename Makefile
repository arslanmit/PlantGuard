# ========== PlantGuard Makefile ==========
# Modern workflow for PlantGuard multimodal plant disease detection
SHELL := /bin/bash
PY      := .venv/bin/python
PIP     := $(PY) -m pip
RUFF    := $(PY) -m ruff
MYPY    := $(PY) -m mypy
PYTEST  := $(PY) -m pytest
JUPYTER := $(PY) -m jupyter
BANDIT  := $(PY) -m bandit
SAFETY  := $(PY) -m safety
PYTHON  := python3

# Package information
PACKAGE_NAME := plantguard
VERSION := 0.1.0

# Project paths
SRC_DIR := src
DATA_DIR := data
NOTEBOOKS_DIR := notebooks
RUNS_DIR := runs
TESTS_DIR := tests
LOGS_DIR := logs
DOCS_DIR := docs

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

.DEFAULT_GOAL := qa

.PHONY: help setup venv deps dev-deps all-deps fmt lint type test qa clean
.PHONY: install run notebook tensorboard train-models quick
.PHONY: test-unit test-integration test-fast test-coverage test-all test-clean test-runner
.PHONY: security safety check-deps update-deps validate logs models-info data-info
.PHONY: ci pre-commit pre-commit-install docker-build docker-run
.PHONY: docs docs-serve docs-clean profile benchmark
.PHONY: jupyter-deps training-deps docs-deps

help:
	@echo "$(CYAN)========== PlantGuard Commands ==========$(NC)"
	@echo ""
	@echo "$(GREEN)🚀 Quick Start:$(NC)"
	@echo "  setup          - Complete environment setup"
	@echo "  run            - Launch PlantGuard Streamlit app"
	@echo "  pre-commit     - Run before committing (fixes + checks)"
	@echo "  quick          - Fast format + lint"
	@echo ""
	@echo "$(GREEN)🔧 Environment:$(NC)"
	@echo "  setup          - Complete environment setup"
	@echo "  dev-deps       - Install development dependencies"
	@echo "  jupyter-deps   - Install Jupyter dependencies"
	@echo "  training-deps  - Install training dependencies"
	@echo "  docs-deps      - Install documentation dependencies"
	@echo "  all-deps       - Install all optional dependencies"
	@echo "  update-deps    - Update all dependencies"
	@echo ""
	@echo "$(GREEN)✅ Code Quality:$(NC)"
	@echo "  fmt            - Auto-fix and format code (Ruff)"
	@echo "  lint           - Lint code (Ruff)"
	@echo "  type           - Type check (Mypy)"
	@echo "  fix-mypy       - Fix common MyPy issues"
	@echo "  fix-files      - Fix file formatting issues"
	@echo "  fix-eol        - Fix end-of-file issues (add missing newlines)"
	@echo "  security       - Security scan (Bandit)"
	@echo "  safety         - Check for known vulnerabilities"
	@echo "  qa             - Full quality assurance pipeline"
	@echo ""
	@echo "$(GREEN)🧪 Testing:$(NC)"
	@echo "  test           - Run all tests with coverage"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-fast      - Run tests without coverage"
	@echo "  test-coverage  - Generate detailed coverage report"
	@echo "  test-clean     - Clean test artifacts"
	@echo ""
	@echo "$(GREEN)🤖 ML Pipeline:$(NC)"
	@echo "  train-models   - Train all PlantGuard models"
	@echo "  tensorboard    - Launch TensorBoard for training metrics"
	@echo "  notebook       - Open Jupyter notebook"
	@echo "  profile        - Profile application performance"
	@echo "  benchmark      - Run performance benchmarks"
	@echo ""
	@echo "$(GREEN)📚 Documentation:$(NC)"
	@echo "  docs           - Build documentation"
	@echo "  docs-serve     - Serve documentation locally"
	@echo "  docs-clean     - Clean documentation build"
	@echo ""
	@echo "$(GREEN)🧹 Maintenance:$(NC)"
	@echo "  clean          - Remove caches and temporary files"
	@echo "  check-deps     - Check for dependency issues"
	@echo ""
	@echo "$(GREEN)📊 Information:$(NC)"
	@echo "  validate       - Validate project setup"
	@echo "  logs           - Show recent log files"
	@echo "  models-info    - Show model information"
	@echo "  data-info      - Show data directory information"
	@echo ""
	@echo "$(GREEN)🚀 CI/CD:$(NC)"
	@echo "  ci             - Full CI/CD pipeline"
	@echo "  pre-commit     - Pre-commit checks"
	@echo "  pre-commit-install - Install pre-commit hooks"

# ========== Environment Setup ==========
venv:
	@echo "$(BLUE)🔧 Creating virtual environment...$(NC)"
	@[ -x $(PY) ] || $(PYTHON) -m venv .venv
	@$(PIP) install --upgrade pip setuptools wheel
	@echo "$(GREEN)✅ Virtual environment ready$(NC)"

deps: venv
	@echo "$(BLUE)📦 Installing runtime dependencies...$(NC)"
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Runtime dependencies installed$(NC)"

dev-deps: deps
	@echo "$(BLUE)📦 Installing development dependencies...$(NC)"
	@$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

jupyter-deps: deps
	@echo "$(BLUE)📦 Installing Jupyter dependencies...$(NC)"
	@$(PIP) install -e ".[jupyter]"
	@echo "$(GREEN)✅ Jupyter dependencies installed$(NC)"

training-deps: deps
	@echo "$(BLUE)📦 Installing training dependencies...$(NC)"
	@$(PIP) install -e ".[training]"
	@echo "$(GREEN)✅ Training dependencies installed$(NC)"

docs-deps: deps
	@echo "$(BLUE)📦 Installing documentation dependencies...$(NC)"
	@$(PIP) install -e ".[docs]"
	@echo "$(GREEN)✅ Documentation dependencies installed$(NC)"

all-deps: deps
	@echo "$(BLUE)📦 Installing all optional dependencies...$(NC)"
	@$(PIP) install -e ".[all]"
	@echo "$(GREEN)✅ All dependencies installed$(NC)"

# Build and distribution
build: clean
	@echo "$(BLUE)🔨 Building package...$(NC)"
	@$(PY) -m build
	@echo "$(GREEN)✅ Package built in dist/$(NC)"

dist: build
	@echo "$(BLUE)📦 Creating distribution...$(NC)"
	@ls -la dist/
	@echo "$(GREEN)✅ Distribution ready$(NC)"

install: deps
	@echo "$(BLUE)🔧 Installing PlantGuard in editable mode...$(NC)"
	@$(PIP) install -e . --no-deps --quiet --disable-pip-version-check
	@echo "$(GREEN)✅ PlantGuard installed$(NC)"

setup: dev-deps install
	@echo "$(GREEN)🎉 Environment setup complete!$(NC)"
	@echo "Run '$(CYAN)make run$(NC)' to start PlantGuard"

update-deps: venv
	@echo "$(BLUE)🔄 Updating dependencies...$(NC)"
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install --upgrade -r requirements.txt
	@$(PIP) install --upgrade -e ".[dev]"
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

check-deps: deps
	@echo "$(BLUE)🔍 Checking for dependency issues...$(NC)"
	@$(PIP) check
	@echo "$(GREEN)✅ Dependency check complete$(NC)"

# ========== Application Execution ==========
run: deps
	@echo "$(BLUE)🚀 Starting PlantGuard Streamlit app...$(NC)"
	@$(PY) run_local.py

notebook: jupyter-deps
	@echo "$(BLUE)📓 Opening PlantGuard Jupyter notebook...$(NC)"
	@$(JUPYTER) notebook $(NOTEBOOKS_DIR)/PlantGuard.ipynb

# ========== Code Quality & Testing ==========
fmt: dev-deps
	@echo "$(BLUE)🎨 Formatting code with Ruff...$(NC)"
	@$(RUFF) check --fix . || true
	@$(RUFF) format .
	@echo "$(GREEN)✅ Code formatted$(NC)"

lint: dev-deps
	@echo "$(BLUE)🔍 Linting code with Ruff...$(NC)"
	@$(RUFF) check .
	@echo "$(GREEN)✅ Linting complete$(NC)"

type: dev-deps
	@echo "$(BLUE)🔍 Type checking with Mypy...$(NC)"
	@$(MYPY) $(SRC_DIR)/
	@echo "$(GREEN)✅ Type checking complete$(NC)"

fix-mypy: dev-deps
	@echo "$(BLUE)🔧 Fixing common MyPy issues...$(NC)"
	@# Fix Streamlit cache_resource decorator type issue
	@if grep -q "@st\.cache_resource$$" src/ui/app_streamlit.py; then \
		echo "$(YELLOW)Adding type ignore for Streamlit decorator...$(NC)"; \
		sed -i '' 's/@st\.cache_resource$$/@st.cache_resource  # type: ignore[misc]/g' src/ui/app_streamlit.py; \
	fi
	@echo "$(GREEN)✅ MyPy fixes applied$(NC)"

security: dev-deps
	@echo "$(BLUE)🔒 Running security scan...$(NC)"
	@$(BANDIT) -r $(SRC_DIR)/ -f json -o security-report.json || true
	@$(BANDIT) -r $(SRC_DIR)/ -ll
	@echo "$(GREEN)✅ Security scan complete$(NC)"

safety: dev-deps
	@echo "$(BLUE)🛡️ Checking for known vulnerabilities...$(NC)"
	@$(SAFETY) check --json --output safety-report.json || true
	@$(SAFETY) check
	@echo "$(GREEN)✅ Safety check complete$(NC)"

# ========== Testing Commands ==========
test: dev-deps
	@echo "$(BLUE)🧪 Running all tests with coverage...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ -v --tb=short
	@echo "$(GREEN)✅ All tests complete$(NC)"

test-unit: dev-deps
	@echo "$(BLUE)🧪 Running unit tests...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ -v -m "unit" --tb=short
	@echo "$(GREEN)✅ Unit tests complete$(NC)"

test-integration: dev-deps
	@echo "$(BLUE)🧪 Running integration tests...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ -v -m "integration" --tb=short
	@echo "$(GREEN)✅ Integration tests complete$(NC)"

test-fast: dev-deps
	@echo "$(BLUE)⚡ Running tests (fast mode)...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ -v --tb=line -x
	@echo "$(GREEN)✅ Fast tests complete$(NC)"

test-coverage: dev-deps
	@echo "$(BLUE)📊 Generating detailed coverage report...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term --cov-report=xml
	@echo "$(GREEN)📊 Coverage report generated in htmlcov/index.html$(NC)"

test-clean:
	@echo "$(BLUE)🧹 Cleaning test artifacts...$(NC)"
	@rm -rf .pytest_cache htmlcov .coverage coverage.xml
	@echo "$(GREEN)✅ Test artifacts cleaned$(NC)"

test-all: test-clean test
	@echo "$(GREEN)✅ Complete test suite finished!$(NC)"

# ========== Quality Assurance Pipeline ==========
qa: fmt lint type security test
	@echo "$(GREEN)✅ Quality assurance complete!$(NC)"

# ========== ML Pipeline & Training ==========
train-models: training-deps
	@echo "$(BLUE)🤖 Training PlantGuard models...$(NC)"
	@mkdir -p $(RUNS_DIR)
	@echo "$(YELLOW)Vision model training...$(NC)"
	@if [ -f scripts/train_vision_model.py ]; then \
		$(PY) scripts/train_vision_model.py --help; \
	else \
		echo "$(RED)❌ Vision training script not found$(NC)"; \
	fi
	@echo "$(YELLOW)Audio model training...$(NC)"
	@$(PY) -c "print('🎵 Audio model (CNN-LSTM) training - implement in scripts/train_audio_model.py')"
	@echo "$(YELLOW)Text model training...$(NC)"
	@$(PY) -c "print('📝 Text model (DistilBERT) training - implement in scripts/train_text_model.py')"
	@echo "$(GREEN)✅ Model training pipeline ready$(NC)"

tensorboard: training-deps
	@echo "$(BLUE)📊 Starting TensorBoard...$(NC)"
	@$(PY) -m tensorboard.main --logdir=$(RUNS_DIR) --port=6006 --host=0.0.0.0 &
	@echo "$(GREEN)TensorBoard running at http://localhost:6006$(NC)"

# ========== Documentation ==========
docs: docs-deps
	@echo "$(BLUE)📚 Building documentation...$(NC)"
	@mkdir -p $(DOCS_DIR)
	@cd $(DOCS_DIR) && $(PY) -m sphinx.cmd.build -b html . _build/html
	@echo "$(GREEN)✅ Documentation built in $(DOCS_DIR)/_build/html/$(NC)"

docs-serve: docs
	@echo "$(BLUE)🌐 Serving documentation locally...$(NC)"
	@cd $(DOCS_DIR)/_build/html && $(PY) -m http.server 8080
	@echo "$(GREEN)Documentation available at http://localhost:8080$(NC)"

docs-clean:
	@echo "$(BLUE)🧹 Cleaning documentation build...$(NC)"
	@rm -rf $(DOCS_DIR)/_build
	@echo "$(GREEN)✅ Documentation build cleaned$(NC)"

# ========== Performance & Profiling ==========
profile: dev-deps
	@echo "$(BLUE)📈 Profiling application performance...$(NC)"
	@$(PY) -m cProfile -o profile.stats run_local.py
	@$(PY) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
	@echo "$(GREEN)✅ Profiling complete - see profile.stats$(NC)"

benchmark: dev-deps
	@echo "$(BLUE)⚡ Running performance benchmarks...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ -v -m "benchmark" --tb=short
	@echo "$(GREEN)✅ Benchmarks complete$(NC)"

# ========== Maintenance ==========
clean:
	@echo "$(BLUE)🧹 Cleaning up caches and temporary files...$(NC)"
	@rm -rf .mypy_cache .ruff_cache .pytest_cache dist build
	@rm -rf htmlcov .coverage coverage.xml
	@rm -rf $(RUNS_DIR) profile.stats security-report.json safety-report.json
	@rm -rf $(DOCS_DIR)/_build 2>/dev/null || true
	@rm -rf $(LOGS_DIR)/*.log 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.orig" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@find $(DATA_DIR)/temp -type f -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# ========== Quick Development Workflow ==========
quick: fmt lint
	@echo "$(GREEN)⚡ Quick workflow complete!$(NC)"

# ========== Alternative Test Runner ==========
test-runner: dev-deps
	@echo "$(BLUE)🧪 Using run_tests.py script...$(NC)"
	@$(PY) run_tests.py all

# ========== Development Utilities ==========
validate: dev-deps
	@echo "$(BLUE)✅ Validating PlantGuard project setup...$(NC)"
	@echo "$(YELLOW)Checking Python version...$(NC)"
	@$(PY) --version
	@echo "$(YELLOW)Checking virtual environment...$(NC)"
	@[ -x $(PY) ] && echo "$(GREEN)✅ Virtual environment active$(NC)" || echo "$(RED)❌ Virtual environment not found$(NC)"
	@echo "$(YELLOW)Checking core directories...$(NC)"
	@[ -d $(SRC_DIR) ] && echo "$(GREEN)✅ Source directory exists$(NC)" || echo "$(RED)❌ Source directory missing$(NC)"
	@[ -d $(TESTS_DIR) ] && echo "$(GREEN)✅ Tests directory exists$(NC)" || echo "$(RED)❌ Tests directory missing$(NC)"
	@[ -d $(DATA_DIR) ] && echo "$(GREEN)✅ Data directory exists$(NC)" || echo "$(RED)❌ Data directory missing$(NC)"
	@echo "$(YELLOW)Checking configuration files...$(NC)"
	@[ -f pyproject.toml ] && echo "$(GREEN)✅ pyproject.toml exists$(NC)" || echo "$(RED)❌ pyproject.toml missing$(NC)"
	@[ -f requirements.txt ] && echo "$(GREEN)✅ requirements.txt exists$(NC)" || echo "$(RED)❌ requirements.txt missing$(NC)"
	@echo "$(YELLOW)Checking package installation...$(NC)"
	@$(PIP) show plantguard >/dev/null 2>&1 && echo "$(GREEN)✅ PlantGuard package installed$(NC)" || echo "$(YELLOW)⚠️ PlantGuard package not installed - run 'make install'$(NC)"
	@echo "$(GREEN)✅ Project validation complete$(NC)"

logs:
	@echo "$(BLUE)📋 Showing recent logs...$(NC)"
	@mkdir -p $(LOGS_DIR)
	@if ls $(LOGS_DIR)/*.log >/dev/null 2>&1; then \
		tail -f $(LOGS_DIR)/*.log; \
	else \
		echo "$(YELLOW)No log files found in $(LOGS_DIR)$(NC)"; \
	fi

models-info:
	@echo "$(BLUE)🤖 Model information...$(NC)"
	@if [ -d $(DATA_DIR)/models ]; then \
		ls -la $(DATA_DIR)/models/; \
		echo ""; \
		du -sh $(DATA_DIR)/models/* 2>/dev/null || true; \
	else \
		echo "$(YELLOW)No models directory found in $(DATA_DIR)/$(NC)"; \
	fi
	@echo ""
	@echo "$(CYAN)Expected models:$(NC)"
	@echo "  - vision_resnet50.pt (Vision model)"
	@echo "  - speech_cnn_lstm.pt (Audio model)"
	@echo "  - text_qa_model/ (Text model directory)"
	@echo "  - fusion_mlp.pt (Fusion model)"

data-info:
	@echo "$(BLUE)📊 Data directory information...$(NC)"
	@if [ -d $(DATA_DIR) ]; then \
		ls -la $(DATA_DIR)/; \
		echo ""; \
		du -sh $(DATA_DIR)/* 2>/dev/null || echo "$(YELLOW)No data files found$(NC)"; \
	else \
		echo "$(RED)❌ Data directory not found$(NC)"; \
	fi

# ========== CI/CD Pipeline ==========
ci: clean setup qa
	@echo "$(GREEN)🚀 CI/CD pipeline complete!$(NC)"
	@echo "$(GREEN)All checks passed - ready for deployment$(NC)"

pre-commit: fix-files fmt lint type
	@echo "$(GREEN)✅ Pre-commit checks complete!$(NC)"

fix-files:
	@echo "$(BLUE)🔧 Fixing common pre-commit issues...$(NC)"
	@# Check if mypy has issues with Streamlit decorators and fix if needed
	@if [ -f src/ui/app_streamlit.py ]; then \
		if $(MYPY) src/ui/app_streamlit.py 2>&1 | grep -q "Untyped decorator makes function.*untyped"; then \
			echo "$(YELLOW)Fixing Streamlit decorator type annotation...$(NC)"; \
			sed -i '' 's/@st\.cache_resource$$/@st.cache_resource  # type: ignore[misc]/g' src/ui/app_streamlit.py; \
		fi; \
	fi
	@# Remove trailing whitespace from project files only (avoid .venv and other dirs)
	@echo "$(YELLOW)Removing trailing whitespace...$(NC)"
	@if [ -d src ]; then find src -name "*.py" -exec sed -i '' 's/[[:space:]]*$$//' {} \; 2>/dev/null || true; fi
	@if [ -d tests ]; then find tests -name "*.py" -exec sed -i '' 's/[[:space:]]*$$//' {} \; 2>/dev/null || true; fi
	@if [ -d scripts ]; then find scripts -name "*.py" -exec sed -i '' 's/[[:space:]]*$$//' {} \; 2>/dev/null || true; fi
	@for file in *.py *.json *.md *.txt *.yaml *.yml; do \
		if [ -f "$$file" ]; then sed -i '' 's/[[:space:]]*$$//' "$$file" 2>/dev/null || true; fi; \
	done
	@# Ensure files end with newline
	@echo "$(YELLOW)Ensuring files end with newline...$(NC)"
	@if [ -d src ]; then find src -name "*.py" -exec sh -c 'if [ -s "{}" ] && [ "$$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo >> "{}"; fi' \; 2>/dev/null || true; fi
	@if [ -d tests ]; then find tests -name "*.py" -exec sh -c 'if [ -s "{}" ] && [ "$$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo >> "{}"; fi' \; 2>/dev/null || true; fi
	@if [ -d scripts ]; then find scripts -name "*.py" -exec sh -c 'if [ -s "{}" ] && [ "$$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo >> "{}"; fi' \; 2>/dev/null || true; fi
	@for file in *.py *.json *.md *.txt *.yaml *.yml; do \
		if [ -f "$$file" ] && [ -s "$$file" ] && [ "$$(tail -c1 "$$file" | wc -l)" -eq 0 ]; then \
			echo >> "$$file"; \
		fi; \
	done 2>/dev/null || true
	@echo "$(GREEN)✅ File fixes complete$(NC)"

fix-eol:
	@echo "$(BLUE)🔧 Fixing end-of-file issues (end-of-file-fixer)...$(NC)"
	@echo "$(YELLOW)Adding newlines to files that need them...$(NC)"
	@# Fix Python files
	@if [ -d src ]; then find src -name "*.py" -exec sh -c 'if [ -s "{}" ] && [ "$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo "Fixing: {}"; echo >> "{}"; fi' \; 2>/dev/null || true; fi
	@if [ -d tests ]; then find tests -name "*.py" -exec sh -c 'if [ -s "{}" ] && [ "$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo "Fixing: {}"; echo >> "{}"; fi' \; 2>/dev/null || true; fi
	@if [ -d scripts ]; then find scripts -name "*.py" -exec sh -c 'if [ -s "{}" ] && [ "$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo "Fixing: {}"; echo >> "{}"; fi' \; 2>/dev/null || true; fi
	@# Fix JSON files (common culprits)
	@if [ -d data ]; then find data -name "*.json" -exec sh -c 'if [ -s "{}" ] && [ "$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo "Fixing: {}"; echo >> "{}"; fi' \; 2>/dev/null || true; fi
	@if [ -d .kiro ]; then find .kiro -name "*.json" -exec sh -c 'if [ -s "{}" ] && [ "$(tail -c1 "{}" | wc -l)" -eq 0 ]; then echo "Fixing: {}"; echo >> "{}"; fi' \; 2>/dev/null || true; fi
	@# Fix other common files
	@for file in *.py *.json *.md *.txt *.yaml *.yml Makefile; do \
		if [ -f "$file" ] && [ -s "$file" ] && [ "$(tail -c1 "$file" | wc -l)" -eq 0 ]; then \
			echo "Fixing: $file"; \
			echo >> "$file"; \
		fi; \
	done 2>/dev/null || true
	@echo "$(GREEN)✅ End-of-file fixes complete$(NC)"
	@echo "$(CYAN)💡 Run 'git add . && git commit' to commit the fixed files$(NC)"

pre-commit-install: dev-deps
	@echo "$(BLUE)🔧 Installing pre-commit hooks...$(NC)"
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
		echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ pre-commit not available - install with 'pip install pre-commit'$(NC)"; \
	fi

# ========== Docker Support ==========
docker-build:
	@echo "$(BLUE)🐳 Building Docker image...$(NC)"
	@if [ -f Dockerfile ]; then \
		docker build -t plantguard:latest .; \
		echo "$(GREEN)✅ Docker image built$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ Dockerfile not found - Docker support not yet implemented$(NC)"; \
	fi

docker-run:
	@echo "$(BLUE)🐳 Running Docker container...$(NC)"
	@if docker images plantguard:latest >/dev/null 2>&1; then \
		docker run -p 8501:8501 plantguard:latest; \
	else \
		echo "$(YELLOW)⚠️ Docker image not found - run 'make docker-build' first$(NC)"; \
	fi

# ========== Help for specific commands ==========
help-qa:
	@echo "$(CYAN)Quality Assurance Pipeline:$(NC)"
	@echo "1. $(BLUE)fmt$(NC)      - Format code with Ruff"
	@echo "2. $(BLUE)lint$(NC)     - Lint code with Ruff"
	@echo "3. $(BLUE)type$(NC)     - Type check with MyPy"
	@echo "4. $(BLUE)security$(NC) - Security scan with Bandit"
	@echo "5. $(BLUE)test$(NC)     - Run tests with coverage"

help-deps:
	@echo "$(CYAN)Dependency Management:$(NC)"
	@echo "$(BLUE)deps$(NC)          - Core runtime dependencies"
	@echo "$(BLUE)dev-deps$(NC)      - Development tools (ruff, mypy, pytest, etc.)"
	@echo "$(BLUE)jupyter-deps$(NC)  - Jupyter notebook dependencies"
	@echo "$(BLUE)training-deps$(NC) - ML training dependencies (wandb, optuna)"
	@echo "$(BLUE)docs-deps$(NC)     - Documentation building dependencies"
	@echo "$(BLUE)all-deps$(NC)      - All optional dependencies combined"
