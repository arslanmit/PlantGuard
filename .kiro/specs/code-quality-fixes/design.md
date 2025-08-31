# Design Document

## Overview

This design addresses systematic code quality improvements across the PlantGuard codebase, focusing on type safety, import organization, security best practices, and test reliability. The approach prioritizes achieving mypy strict mode compliance (zero errors from current 535), then addressing import and style issues, and finally improving test infrastructure to support PlantGuard's local-only ML inference requirements.

The design ensures compliance with PlantGuard's core constraints: all ML inference must remain local-only, no external APIs for core functionality, and offline capability after model downloads. All fixes maintain the project's privacy-first architecture while improving code quality and maintainability.

## Architecture

### Fix Priority Levels

1. **Critical**: Mypy strict mode compliance (535 errors → 0 errors)
2. **High**: Security issues and import organization (187 ruff issues)
3. **Medium**: Code style and formatting issues (Unicode characters, line length)
4. **Low**: Test infrastructure improvements and cleanup

### Component Categories

- **Core Adapters**: Vision, Audio, Text adapters with proper type annotations
- **Mobile UI Components**: Layout managers, state managers, testing frameworks
- **Test Infrastructure**: Mock interfaces, fixture setup, error handling
- **Utility Scripts**: File operations, security improvements, path handling

## Components and Interfaces

### Type Annotation Fixes

**Mobile Testing Framework**:
```python
class MobileTestingFramework:
    def __init__(self) -> None:
        self.performance_metrics: dict[str, float] = {}
        self.test_results: list[dict[str, Any]] = []
        
    def validate_performance(self, metrics: dict[str, float]) -> bool:
        # Fix comparison operations with proper typing
        return all(isinstance(v, (int, float)) for v in metrics.values())
```

**Adapter Properties**:
```python
class MobileAdapterIntegration:
    @property
    def vision_adapter(self) -> Optional[VisionAdapter]:
        return self._vision_adapter
        
    @vision_adapter.setter
    def vision_adapter(self, adapter: Optional[VisionAdapter]) -> None:
        self._vision_adapter = adapter
```

### Import Organization Strategy

**File Structure**:
```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Optional, Any

# Third-party imports
import streamlit as st
import torch
import numpy as np

# First-party imports
from src.core.vision import VisionAdapter
from src.ui.components.mobile_layout_manager import MobileLayoutManager
```

**Conditional Import Pattern**:
```python
try:
    from src.ui.mobile_spa_app import MobileSPAApp
except ImportError:
    MobileSPAApp = None

def get_mobile_app():
    if MobileSPAApp is None:
        raise ImportError("Mobile SPA app not available")
    return MobileSPAApp()
```

### Security Improvements

**Subprocess Security**:
```python
import shutil
import subprocess
from pathlib import Path

def run_secure_command(command: str) -> subprocess.CompletedProcess:
    # Use full path resolution to prevent S607 security issues
    cmd_path = shutil.which(command)
    if not cmd_path:
        raise FileNotFoundError(f"Command not found: {command}")
    return subprocess.run([cmd_path], timeout=30, check=True, capture_output=True)
```

**Path Operations**:
```python
from pathlib import Path
import tempfile

def safe_file_operations(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()  # Instead of os.unlink()
    
    parent_dir = path.parent  # Instead of os.path.dirname()
    working_dir = Path.cwd()  # Instead of os.getcwd()

def create_temp_file() -> Path:
    # Use tempfile module for secure temporary file creation
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    return Path(temp_file.name)
```

**Exception Handling**:
```python
import contextlib
import logging

logger = logging.getLogger(__name__)

def safe_operation_with_logging():
    try:
        # Risky operation
        result = perform_operation()
        return result
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.warning(f"Operation failed: {e}")
        return None

# Use contextlib.suppress for simple pass cases
with contextlib.suppress(FileNotFoundError):
    Path("optional_file.txt").unlink()
```

### Mobile Component Integration

**Mock Interface Design**:
```python
class MockVisionAdapter:
    def __init__(self):
        self.predict = MagicMock(return_value=("Healthy", 0.95))
        self.load_checkpoint = MagicMock()

class MobileAdapterIntegration:
    def __init__(self):
        self._vision_adapter: Optional[VisionAdapter] = None
        self._audio_adapter: Optional[AudioAdapter] = None
        self._text_adapter: Optional[TextAdapter] = None
```

**Layout Manager Completion**:
```python
class MobileLayoutManager:
    def _get_fallback_css(self) -> str:
        return """
        .mobile-fallback {
            width: 100%;
            max-width: 100vw;
            padding: 1rem;
        }
        """
    
    @property
    def performance_optimizer(self) -> dict[str, Any]:
        return getattr(self, '_performance_optimizer', {})
```

## Data Models

### Error Tracking Model

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class CodeQualityIssue:
    file_path: str
    line_number: int
    issue_type: Literal['type', 'import', 'security', 'style']
    severity: Literal['critical', 'high', 'medium', 'low']
    description: str
    fix_applied: bool = False
```

### Test Configuration Model

```python
@dataclass
class TestConfig:
    mock_streamlit_state: bool = True
    mock_adapters: bool = True
    skip_model_loading: bool = True
    temp_file_cleanup: bool = True
    line_length_limit: int = 100  # PlantGuard standard
```

### Unicode Character Replacement Model

```python
@dataclass
class UnicodeReplacement:
    original_char: str
    replacement_char: str
    file_path: str
    line_number: int
    
# Standard replacements for RUF001 issues
UNICODE_REPLACEMENTS: dict[str, str] = {
    'ℹ': 'i',  # Information symbol to ASCII 'i'
    '…': '...',  # Ellipsis to three dots
    '"': '"',   # Smart quotes to standard quotes
    '"': '"',
    ''': "'",
    ''': "'"
}
```

## Error Handling

### Type Error Recovery

```python
def safe_type_conversion(value: Any, target_type: type) -> Any:
    try:
        if isinstance(value, target_type):
            return value
        return target_type(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Type conversion failed: {e}")
        return None
```

### Import Error Handling

```python
import importlib.util
from typing import Optional, Any

def safe_import(module_name: str) -> Optional[Any]:
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        logger.debug(f"Optional import failed: {module_name} - {e}")
        return None

def check_module_availability(module_name: str) -> bool:
    """Check if module is available without importing it"""
    spec = importlib.util.find_spec(module_name)
    return spec is not None

# Conditional import pattern for optional dependencies
def get_optional_dependency(module_name: str, fallback_class=None):
    if check_module_availability(module_name):
        return importlib.import_module(module_name)
    elif fallback_class:
        logger.warning(f"Using fallback for {module_name}")
        return fallback_class
    else:
        raise ImportError(f"Required module {module_name} not available")
```

## Testing Strategy

### Mock Strategy for Mobile Components

```python
@pytest.fixture
def mock_streamlit_state():
    with patch('streamlit.session_state', new_callable=dict) as mock_state:
        mock_state.update({
            'analysis_results': [],
            'mobile_performance': {},
            'adapter_status': 'ready'
        })
        yield mock_state
```

### Adapter Testing Pattern

```python
@pytest.fixture
def mock_adapters():
    with patch.multiple(
        'src.ui.components.mobile_adapter_integration',
        VisionAdapter=MagicMock,
        AudioAdapter=MagicMock,
        TextAdapter=MagicMock
    ):
        yield
```

### File System Testing

```python
import tempfile
from pathlib import Path

@pytest.fixture
def temp_model_file():
    # Use tempfile for secure temporary file creation
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        temp_path = Path(tmp.name)
    
    # Ensure proper cleanup
    yield temp_path
    
    if temp_path.exists():
        temp_path.unlink()

@pytest.fixture
def temp_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
```

## Code Style and Formatting Standards

### Line Length Management

```python
# Before: Long line exceeding 100 characters
very_long_function_call_with_many_parameters(param1, param2, param3, param4, param5, param6)

# After: Properly formatted within 100 character limit
very_long_function_call_with_many_parameters(
    param1, param2, param3, 
    param4, param5, param6
)
```

### Unicode Character Standardization

```python
# Automated replacement patterns for RUF001 issues
def replace_unicode_characters(content: str) -> str:
    replacements = {
        'ℹ': 'i',      # Information symbol
        '…': '...',     # Ellipsis
        '"': '"',       # Smart quotes
        '"': '"',
        ''': "'",
        ''': "'"
    }
    
    for original, replacement in replacements.items():
        content = content.replace(original, replacement)
    
    return content
```

### Variable Naming Standards

```python
# Before: Ambiguous single letters
def process_data(d, l, s):
    pass

# After: Descriptive variable names
def process_data(data_dict: dict[str, Any], 
                item_list: list[str], 
                status_string: str) -> None:
    pass
```

## Implementation Phases

### Phase 1: Critical Import and Type Fixes
- Fix F404 `from __future__` imports placement in conftest.py
- Move E402 module-level imports to file tops across all affected files
- Remove F401 unused imports in src/__init__.py and other modules
- Update UP035 deprecated typing imports (typing.Dict → dict, typing.List → list)
- Organize imports in standard library, third-party, first-party order
- Add missing return type annotations (535 mypy errors → 0)

**Rationale**: Import organization and basic type annotations are foundational for all other fixes. Proper import structure prevents circular dependencies and ensures consistent module loading.

### Phase 2: Security and Unicode Issues
- Replace S607 subprocess calls with secure shutil.which() validation
- Fix RUF001 ambiguous Unicode characters (ℹ → i) for better compatibility
- Convert os.path operations to pathlib.Path for modern Python practices
- Add subprocess timeouts and proper validation to prevent hanging
- Implement proper exception logging instead of silent continues

**Rationale**: Security fixes prevent potential vulnerabilities, while Unicode standardization ensures cross-platform compatibility. These changes align with PlantGuard's security-first approach.

### Phase 3: Type Parameter and Generic Fixes
- Fix type-arg errors for generic dict/list usage throughout codebase
- Replace Any return types with specific type annotations
- Add proper type parameters to all generic types (dict[K, V], list[T])
- Fix no-untyped-def and no-untyped-call errors
- Update Collection types to concrete list/dict types where appropriate

**Rationale**: Specific type annotations enable better IDE support, catch runtime errors at development time, and improve code maintainability.

### Phase 4: Mobile Component Integration and Testing
- Add proper type annotations to adapter properties (_vision_adapter, _audio_adapter, _text_adapter)
- Fix mobile testing framework type safety and comparison operations
- Implement proper mock interfaces for Streamlit session state in tests
- Complete missing methods in layout managers
- Fix import errors and missing dependencies in test files
- Add proper fixture setup and teardown for adapter tests

**Rationale**: Mobile components are critical for PlantGuard's UI functionality. Proper testing infrastructure ensures reliability while maintaining the offline-first architecture.

### Phase 5: Final Validation and Cleanup
- Achieve mypy --strict zero errors (from current 535)
- Resolve all ruff linting issues (from current 187)
- Ensure all tests pass with improved infrastructure
- Verify compliance with PlantGuard's 100-character line length standard
- Generate comprehensive quality report with zero errors
- Validate that all fixes maintain offline-first architecture

**Rationale**: Final validation ensures all quality improvements work together cohesively and don't introduce regressions in PlantGuard's core functionality.

## Mypy Strict Mode Compliance Strategy

### Current Error Categories (535 total errors)

1. **no-untyped-def**: Functions missing return type annotations
2. **no-untyped-call**: Calls to untyped functions
3. **type-arg**: Missing type parameters for generic types
4. **no-any-return**: Functions returning Any instead of specific types

### Systematic Resolution Approach

**Function Annotation Pattern**:
```python
# Before: Missing return type
def main():
    process_files()

# After: Complete type annotation
def main() -> None:
    process_files()

# Before: Generic return type
def get_config() -> Any:
    return load_config()

# After: Specific return type
def get_config() -> dict[str, str]:
    return load_config()
```

**Generic Type Parameter Resolution**:
```python
# Before: Missing type parameters
results: dict = {}
items: list = []

# After: Complete type parameters
results: dict[str, float] = {}
items: list[str] = []
```

**Call Chain Type Safety**:
```python
# Ensure all called functions have proper type annotations
def typed_function(data: dict[str, Any]) -> bool:
    return validate_data(data)  # validate_data must also be typed

def validate_data(data: dict[str, Any]) -> bool:
    return all(isinstance(v, (str, int, float)) for v in data.values())
```

This systematic approach ensures that achieving zero mypy strict mode errors doesn't compromise PlantGuard's core architecture or offline-first requirements.