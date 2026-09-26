"""Run a long shell command off the request path.

Emits command_start immediately and command_finish when the process exits
or the timeout fires. The original session id is on both events so a reader
can wake that session. The child is a new process; this function returns
as soon as it has been started.
"""

import subprocess
import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BIN = REPO / "openclaw-harness" / "bin"
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

from event_emitter import emit  # noqa: E402


def start(command: list[str], session_id: str, timeout_s: float, path: Path) -> subprocess.Popen:
    """Start command in the background and record start plus finish."""
    emit(
        session_id=session_id,
        kind="command_start",
        tool_name="shell",
        args={"command": command, "timeout_s": timeout_s},
        path=path,
    )
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    def _finish() -> None:
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
            status = "exit"
            code = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            status = "timeout"
            code = proc.returncode
        emit(
            session_id=session_id,
            kind="command_finish",
            tool_name="shell",
            result={
                "status": status,
                "exit_code": code,
                "stdout": (stdout or "")[:500],
                "stderr": (stderr or "")[:500],
            },
            path=path,
        )

    threading.Thread(target=_finish, daemon=True).start()
    return proc
