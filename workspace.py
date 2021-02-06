import os
from pathlib import Path

PROJECT_ROOT = Path(".").absolute()
PROJECT_SCRIPT = PROJECT_ROOT / "scripts"
WORKSPACE = Path("/workspace")
SHARED = WORKSPACE / "shared"
CACHE = WORKSPACE / "cache"
LOGS = CACHE / "logs"
GROUP = WORKSPACE / "group"
USER = WORKSPACE / "user"
