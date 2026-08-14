"""Pytest conftest for scripts/tests/ — adds scripts/ to sys.path."""
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
