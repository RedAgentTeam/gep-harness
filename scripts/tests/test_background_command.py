"""Background shell events: start immediately, finish with exit or timeout."""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import background_command as bg


def _wait_for_finish(path: Path, timeout: float = 3.0) -> list[dict]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            if any(row.get("kind") == "command_finish" for row in rows):
                return rows
        v2 = path.with_name(path.stem + ".v2" + path.suffix)
        if v2.exists():
            rows = [json.loads(line) for line in v2.read_text().splitlines() if line.strip()]
            if any(row.get("kind") == "command_finish" for row in rows):
                return rows
        time.sleep(0.05)
    raise AssertionError("command_finish was not written")


def test_background_command_records_exit(tmp_path):
    log = tmp_path / "events.jsonl"
    bg.start([sys.executable, "-c", "print('ok')"], "sess-bg", 2.0, log)
    rows = _wait_for_finish(log)
    kinds = [row["kind"] for row in rows]
    assert kinds[0] == "command_start"
    assert "command_finish" in kinds
    finish = next(row for row in rows if row["kind"] == "command_finish")
    assert finish["session_id"] == "sess-bg"
    assert finish["result"]["status"] == "exit"
    assert finish["result"]["exit_code"] == 0


def test_background_command_records_timeout(tmp_path):
    log = tmp_path / "events.jsonl"
    bg.start([sys.executable, "-c", "import time; time.sleep(5)"], "sess-to", 0.2, log)
    rows = _wait_for_finish(log)
    finish = next(row for row in rows if row["kind"] == "command_finish")
    assert finish["result"]["status"] == "timeout"
