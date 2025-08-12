---
inclusion: always
---

# PlantGuard Code Quality Standards

## Critical Validation Rule

**MANDATORY**: Validate all generated code against `pyproject.toml` linting rules before presenting to user. Fix violations immediately.

## Code Style Requirements

### Formatting Standards
- **Line length**: 100 characters maximum
- **Quotes**: Double quotes for all strings
- **Import order**: First-party (`src`, `plantguard`) before third-party (`torch`, `numpy`, `streamlit`, `PIL`)
- **Indentation**: 4 spaces (no tabs)

### Type Annotations (Mandatory)
- Complete type hints for all function parameters and return values
- Use `-> None` for functions without return values
- Avoid `Any` types - use specific generics for `*args`/`**kwargs`
- Import types from `typing` or `collections.abc`

Example:
```python
def process_image(img: PIL.Image.Image, threshold: float = 0.5) -> tuple[str, float]:
    """Process plant image for disease detection."""
```

### Function Complexity Limits
- Maximum 6 parameters per function
- Cyclomatic complexity ≤ 10
- Maximum 50 statements per function
- Maximum 6 return statements
- Maximum 12 conditional branches

### PlantGuard-Specific Standards
- Use `logger.info()` instead of `print()` in production code
- Use `pathlib.Path` for all file operations
- Specify exception types: `except FileNotFoundError:` not `except:`
- Clean up temporary files immediately after use
- Use `@st.cache_resource` for model loading in Streamlit

## Pre-Code Generation Checklist

1. Review existing code style in target file/module
2. Verify import organization follows project conventions
3. Confirm all functions will have complete type annotations
4. Plan error handling with specific exception types

## Post-Code Generation Validation

1. Check line length compliance (≤100 characters)
2. Verify type annotations on all functions
3. Confirm no bare `except:` clauses
4. Validate proper logging usage (no `print()` statements)
5. Check file path operations use `pathlib.Path`

## Common Fixes for PlantGuard

### Type Annotations
```python
# Fix missing annotations
def load_model(path: str) -> torch.nn.Module:
    return torch.load(path)

# Fix generic types
def process_batch(*images: PIL.Image.Image) -> list[tuple[str, float]]:
    return [(predict(img)) for img in images]
```

### Error Handling
```python
# Replace bare except
try:
    model = load_model(path)
except (FileNotFoundError, torch.serialization.pickle.UnpicklingError) as e:
    logger.error(f"Model loading failed: {e}")
    return None
```

### Logging
```python
# Replace print statements
logger.info(f"Processing image: {image_path}")  # Not print()
st.write(f"Detected disease: {disease}")        # For Streamlit UI
```

## Testing Standards

- All `src/` modules require test coverage
- Use `pytest` with type checking enabled
- Test files may use `assert` and magic values (exceptions to style rules)
- Mock external dependencies in tests

## Quality Validation Commands

```bash
ruff check --fix .     # Auto-fix style violations
ruff format .          # Apply consistent formatting
mypy src/              # Type checking validation
pytest --cov=src/      # Run tests with coverage report
```
