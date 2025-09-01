"""
Mobile Error Handler for PlantGuard UI.

This module provides error handling capabilities for mobile components.
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""
    VALIDATION = "validation"
    NETWORK = "network"
    SYSTEM = "system"
    USER = "user"
    UNKNOWN = "unknown"


class MobileErrorHandler:
    """Error handler for mobile components."""
    
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.error_count = 0
        self.last_error = None
    
    def handle_error(self, error: Exception, severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                    category: ErrorCategory = ErrorCategory.UNKNOWN) -> None:
        """Handle an error."""
        self.error_count += 1
        self.last_error = {
            "error": str(error),
            "severity": severity.value,
            "category": category.value,
            "timestamp": None
        }
        logger.error(f"Component {self.component_id} error: {error}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary."""
        return {
            "component_id": self.component_id,
            "error_count": self.error_count,
            "last_error": self.last_error
        }
