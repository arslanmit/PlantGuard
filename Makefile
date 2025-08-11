# ---------- Python QA Makefile (Ruff + Mypy + Pytest) ----------
SHELL := /bin/bash
PY      := .venv/bin/python
PIP     := $(PY) -m pip
RUFF    := $(PY) -m ruff
MYPY    := $(PY) -m mypy
PYTEST  := $(PY) -m pytest

.DEFAULT_GOAL := qa

.PHONY: help venv deps fmt lint type test qa check clean versions install run notebook

help:
	@echo "Targets:"
	@echo "  venv       - Create .venv if missing"
	@echo "  deps       - Install dev deps (ruff, mypy, pytest, pytest-cov)"
	@echo "  fmt        - Auto-fix + format (Ruff)"
	@echo "  lint       - Lint (Ruff)"
	@echo "  type       - Type-check (Mypy)"
	@echo "  test       - Run tests (Pytest+coverage)"
	@echo "  qa         - fmt -> lint -> type -> test (DEFAULT)"
	@echo "  check      - No-fix CI check (fails on issues)"
	@echo "  clean      - Remove caches"
	@echo "  versions   - Show tool versions"
	@echo "  install    - Install project dependencies"
	@echo "  run        - Run PlantGuard Streamlit app"
	@echo "  notebook   - Run PlantGuard Jupyter notebook"

venv:
	@[ -x $(PY) ] || python3 -m venv .venv
	@$(PIP) install --upgrade pip setuptools wheel

deps: venv
	@$(PIP) install ruff mypy pytest pytest-cov

# Install project dependencies
install: venv
	@$(PIP) install -r requirements-colab.txt

# Run the PlantGuard Streamlit app
run: venv
	@$(PY) run_local.py

# Run the PlantGuard Jupyter notebook
notebook: venv
	@$(PY) -m jupyter notebook notebooks/PlantGuard.ipynb

fmt: deps
	@$(RUFF) check --fix .
	@$(RUFF) format .

lint: deps
	@$(RUFF) check .

type: deps
	@$(MYPY) .

test: deps
	@$(PYTEST)

qa: fmt lint type test

check: deps
	@$(RUFF) check .
	@$(RUFF) format --check .
	@$(MYPY) .
	@$(PYTEST)

clean:
	rm -rf .mypy_cache .ruff_cache .pytest_cache dist build
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

versions: deps
	@$(PY) -V
	@$(RUFF) --version
	@$(MYPY) --version
	@$(PYTEST) --version

# ---------------------------------------------------------------
