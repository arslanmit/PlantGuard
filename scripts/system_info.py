from typing import Any

#!/usr/bin/env python3
"""
Simple system info script for PlantGuard Makefile
"""


import json
import platform
from datetime import datetime

import psutil


def get_system_info() -> Any:
    """Get comprehensive system information"""
    info = {
        "timestamp": datetime.now().isoformat(),
        "command": "api-info",
        "status": "success",
        "system": {
            "platform": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "cpu_count": psutil.cpu_count(),
            "disk_free_gb": round(psutil.disk_usage(".").free / (1024**3), 1),
        },
        "project": {"name": "PlantGuard", "version": "1.0.0", "directory": str(Path.cwd())},
    }
    return info


if __name__ == "__main__":
    print(json.dumps(get_system_info(), indent=2))
