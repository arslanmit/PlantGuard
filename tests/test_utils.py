"""Test utilities for handling optional imports and missing model files."""

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import Mock

logger = logging.getLogger(__name__)


def safe_import(module_name: str, package: Optional[str] = None) -> Optional[Any]:
    """Safely import a module with proper error handling.
    
    Args:
        module_name: Name of module to import
        package: Package name for relative imports
        
    Returns:
        Imported module or None if import fails
    """
    try:
        spec = importlib.util.find_spec(module_name, package)
        if spec is None:
            logger.debug(f"Module not found: {module_name}")
            return None
            
        module = importlib.import_module(module_name, package)
        logger.debug(f"Successfully imported: {module_name}")
        return module
        
    except ImportError as e:
        logger.debug(f"Import failed for {module_name}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error importing {module_name}: {e}")
        return None


def check_module_availability(module_name: str) -> bool:
    """Check if a module is available for import.
    
    Args:
        module_name: Name of module to check
        
    Returns:
        True if module can be imported
    """
    spec = importlib.util.find_spec(module_name)
    return spec is not None


def create_mock_adapter(adapter_type: str) -> Mock:
    """Create a mock adapter for testing.
    
    Args:
        adapter_type: Type of adapter ('vision', 'audio', 'text')
        
    Returns:
        Mock adapter with appropriate methods
    """
    mock_adapter = Mock()
    
    if adapter_type == 'vision':
        mock_adapter.predict.return_value = ("Healthy", 0.95)
        mock_adapter.load_checkpoint = Mock()
        
    elif adapter_type == 'audio':
        mock_adapter.transcribe.return_value = "Test transcription"
        mock_adapter.predict_disease.return_value = ("Healthy", 0.90)
        
    elif adapter_type == 'text':
        mock_adapter.extract_features.return_value = Mock()
        mock_adapter.generate_response.return_value = "Test response"
        mock_adapter.get_disease_info.return_value = {
            "plant_type": "Test Plant",
            "severity": "Low"
        }
    
    return mock_adapter


def setup_test_environment():
    """Setup test environment with proper path configuration."""
    # Add src to Python path
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Add root directory for mobile_spa_app
    root_path = Path(__file__).parent.parent
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))


def get_test_model_config() -> Dict[str, Any]:
    """Get test configuration that handles missing model files gracefully.
    
    Returns:
        Test configuration dictionary
    """
    return {
        "vision_model_path": "data/models/test_vision.pt",
        "audio_model_path": "data/models/test_audio.pt", 
        "text_model_path": "data/models/test_text.pt",
        "fallback_mode": True,
        "skip_model_loading": True,
        "use_mock_adapters": True
    }


def handle_missing_model_files(model_paths: list[str]) -> Dict[str, bool]:
    """Check which model files are missing and return status.
    
    Args:
        model_paths: List of model file paths to check
        
    Returns:
        Dictionary mapping paths to availability status
    """
    status = {}
    
    for path in model_paths:
        try:
            file_path = Path(path)
            status[path] = file_path.exists() and file_path.is_file()
        except Exception as e:
            logger.debug(f"Error checking model file {path}: {e}")
            status[path] = False
    
    return status


def create_fallback_app_class():
    """Create a fallback app class for testing when main app is not available."""
    
    class FallbackPlantGuardApp:
        """Fallback app class for testing."""
        
        def __init__(self):
            self.models = {"vision": {}, "audio": {}, "text": {}}
            self.layout_manager = Mock()
            self.header = Mock()
            self.input_ribbon = Mock()
            self.content_tabs = Mock()
            self.image_analysis = Mock()
            self.voice_interface = Mock()
            self.chat_interface = Mock()
            self.vision_adapter = create_mock_adapter('vision')
            self.audio_adapter = create_mock_adapter('audio')
            self.text_adapter = create_mock_adapter('text')

        def render_header(self):
            return "PlantGuard AI"

        def render_image_analysis_tab(self):
            return "Image Analysis"

        def render_voice_assistant_tab(self):
            return "Voice Assistant"

        def render_chat_interface_tab(self):
            return "Chat Assistant"

        def render_history_settings_tab(self):
            return "History & Settings"

        def render_comparison_tab(self):
            return "Image Comparison"

        def initialize_components(self):
            pass

        def initialize_app_state(self):
            pass
    
    return FallbackPlantGuardApp


def validate_test_requirements() -> Dict[str, bool]:
    """Validate that test requirements are met.
    
    Returns:
        Dictionary with validation results
    """
    results = {}
    
    # Check Python path setup
    src_path = Path(__file__).parent.parent / "src"
    results['src_path_available'] = src_path.exists()
    results['src_in_path'] = str(src_path) in sys.path
    
    # Check core modules
    core_modules = ['core.vision', 'core.audio', 'core.nlp']
    for module in core_modules:
        results[f'{module}_available'] = check_module_availability(module)
    
    # Check UI components
    ui_components = [
        'ui.components.mobile_layout_manager',
        'ui.components.mobile_header',
        'ui.components.mobile_image_analysis'
    ]
    for component in ui_components:
        results[f'{component}_available'] = check_module_availability(component)
    
    # Check mobile app
    results['mobile_spa_app_available'] = check_module_availability('mobile_spa_app')
    
    return results