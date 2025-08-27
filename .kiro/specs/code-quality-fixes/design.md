# Design Document

## Overview

This design addresses systematic code quality improvements across the PlantGuard codebase, focusing on type safety, import organization, security best practices, and test reliability. The approach prioritizes fixing critical type errors first, then addressing import and style issues, and finally improving test infrastructure.

## Architecture

### Fix Priority Levels

1. **Critical**: Type errors that break mypy validation
2. **High**: Security issues and import organization
3. **Medium**: Code style and formatting issues
4. **Low**: Test infrastructure improvements

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
        self.performance_metrics: Dict[str, float] = {}
        self.test_results: List[Dict[str, Any]] = []
        
    def validate_performance(self, metrics: Dict[str, float]) -> bool:
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
from typing import Dict, List, Optional

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
from pathlib import Path

def run_secure_command(command: str) -> subprocess.CompletedProcess:
    # Use full path resolution
    cmd_path = shutil.which(command)
    if not cmd_path:
        raise FileNotFoundError(f"Command not found: {command}")
    return subprocess.run([cmd_path], timeout=30, check=True)
```

**Path Operations**:
```python
from pathlib import Path

def safe_file_operations(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()  # Instead of os.unlink()
    
    parent_dir = path.parent  # Instead of os.path.dirname()
    working_dir = Path.cwd()  # Instead of os.getcwd()
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
    def performance_optimizer(self) -> Dict[str, Any]:
        return getattr(self, '_performance_optimizer', {})
```

## Data Models

### Error Tracking Model

```python
@dataclass
class CodeQualityIssue:
    file_path: str
    line_number: int
    issue_type: str  # 'type', 'import', 'security', 'style'
    severity: str    # 'critical', 'high', 'medium', 'low'
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
def safe_import(module_name: str) -> Optional[Any]:
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        logger.debug(f"Optional import failed: {module_name} - {e}")
        return None
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
@pytest.fixture
def temp_model_file():
    temp_path = Path("data/models/vision_resnet50.pt")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.touch()
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()
```

## Implementation Phases

### Phase 1: Critical Type Fixes
- Fix mobile_testing_framework.py type errors
- Add proper type annotations to adapter properties
- Fix Collection type usage

### Phase 2: Import Organization
- Move all imports to file tops
- Remove unused imports
- Implement conditional import patterns

### Phase 3: Security and Best Practices
- Replace subprocess calls with secure versions
- Convert os.path to pathlib.Path
- Add request timeouts and proper exception logging

### Phase 4: Test Infrastructure
- Fix mobile component mocking
- Add proper session state fixtures
- Implement graceful model file handling

### Phase 5: Code Style Cleanup
- Fix ambiguous variable names
- Replace Unicode characters
- Implement contextlib.suppress patterns