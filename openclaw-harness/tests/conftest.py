"""conftest.py — auto-inject shared paths for all tests in this directory."""
import sys
from pathlib import Path

# scripts/ (llm_fill_gene.py, scan_events.py, etc.)
scripts_dir = Path(__file__).parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# openclaw-a2a/src/ (a2a_protocol.py, gene_sync.py)
a2a_src = Path(__file__).parent.parent.parent / "openclaw-a2a" / "src"
if str(a2a_src) not in sys.path:
    sys.path.insert(0, str(a2a_src))
