---
inclusion: always
---

# Code Quality & Linting Standards

## Critical Rule

**ALWAYS** validate generated and existing code against the linting rules defined in `pyproject.toml`. Fix any violations immediately before presenting code to the user.

## Mandatory Code Standards

### Line Length & Formatting

- **Max line length**: 100 characters
- **String quotes**: Use double quotes consistently
- **Import sorting**: First-party (`src`, `plantguard`) before third-party (`torch`, `numpy`, `streamlit`, `PIL`)

### Type Annotations (Required)

- All function definitions must include complete type hints
- Return types required for all functions (use `-> None` for procedures)
- No `Any` types for `*args`/`**kwargs` - use proper generic types
- Import types from `typing` or `collections.abc` as needed

### Function Complexity Limits

- **Max parameters**: 6 per function
- **Max cyclomatic complexity**: 10
- **Max statements**: 50 per function
- **Max return statements**: 6 per function
- **Max branches**: 12 conditional branches

### Security & Best Practices

- No bare `except:` clauses - always specify exception types
- No `print()` statements in production code - use logging instead
- Use `pathlib.Path` over `os.path` for file operations
- Proper exception handling with specific exception types
- No hardcoded secrets or credentials

## AI Assistant Actions

### Before Writing Code

1. Check existing code style in the file/module
2. Ensure all imports are properly organized
3. Verify type hints are complete and accurate

### After Writing Code

1. Run mental check against 100-character line limit
2. Verify all functions have type annotations
3. Check for security anti-patterns (bare except, hardcoded values)
4. Ensure proper error handling patterns

### Common Fixes to Apply

- Add missing type annotations: `def process_image(img: PIL.Image.Image) -> tuple[str, float]:`
- Break long lines at logical points (after commas, before operators)
- Replace `print()` with `logger.info()` or `st.write()`
- Use specific exceptions: `except FileNotFoundError:` instead of `except:`
- Add docstrings for public functions with clear parameter descriptions

## Testing Requirements

- All `src/` modules require test coverage
- Use `pytest` with strict markers
- Tests may use `assert` statements and magic values (exceptions to normal rules)

## Quality Commands

Run these commands to validate code quality:

```bash
ruff check --fix .        # Auto-fix style issues
ruff format .             # Format code consistently  
mypy src/                 # Type checking
pytest --cov=src/         # Run tests with coverage
```
