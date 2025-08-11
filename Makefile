.PHONY: lint format type-check install-dev install run notebook clean

# Install project dependencies
install:
	pip3 install -r requirements-colab.txt

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Run the PlantGuard Streamlit app
run:
	python3 run_local.py

# Run the PlantGuard Jupyter notebook
notebook:
	jupyter notebook notebooks/PlantGuard.ipynb

# Format code with black and isort
format:
	black src/ run_local.py
	isort src/ run_local.py

# Run all linting checks
lint:
	flake8 src/ run_local.py
	black --check src/ run_local.py
	isort --check-only src/ run_local.py

# Run type checking
type-check:
	mypy src/

# Run security checks
security:
	bandit -r src/

# Run all checks
check: lint type-check security



# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Fix common issues automatically
fix:
	black src/ run_local.py
	isort src/ run_local.py

# Run pre-commit on all files
pre-commit-all:
	pre-commit run --all-files
