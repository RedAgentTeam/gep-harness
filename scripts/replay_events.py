"""Replay last 10 events — used by Makefile replay target."""
import json
import sys


def replay_event(e: dict) -> str:
    """Format one event as a single line."""
    kind = e.get("kind", "?")
    tool = e.get("tool_name", "-")
    return f"  {kind:25s} tool={tool:15s}"


def replay_stdin() -> int:
    """Read JSON lines from stdin, print formatted events. Return count."""
    count = 0
    for line in sys.stdin:
        try:
            e = json.loads(line)
        except Exception:
            continue
        print(replay_event(e))
        count += 1
    return count


if __name__ == "__main__":
    replay_stdin()