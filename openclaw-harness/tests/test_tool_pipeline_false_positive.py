"""Regression tests for P1-3: tool pipeline MUST NOT produce false-positive blocks.

Background: the original implementation matched forbidden paths via substring
on the serialized params string, which caused false positives when a forbidden
path appeared in *unstructured* fields (e.g. error messages, doc content, free
text). The fix was to only inspect strongly-typed path fields (path/file/target/
src/dest/filename/filepath/etc.) and use PATH PREFIX matching (not substring).

These tests pin the fix down so future refactors don't reintroduce the bug.

3 pytest:
  1. Forbidden path in free-text field (doc content / error msg) must NOT block
  2. Forbidden path as a strongly-typed path field with PREFIX match blocks
  3. Forbidden path appearing as a SUBSTRING inside a longer safe path does NOT block
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
PLUGIN_ENTRY = Path("/data/disk/gep-harness/openclaw-harness-tool-pipeline-plugin/index.js")


def run_node(test_script):
    full = (
        f"import plugin from '{PLUGIN_ENTRY}';\n"
        f"{test_script}"
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", full],
        capture_output=True, text=True, timeout=15,
        cwd=str(PLUGIN_ENTRY.parent),
    )
    return result


def test_forbidden_path_in_free_text_field_does_not_block():
    """P1-3 fix: '/opt/goapi' appearing in a free-text 'message' field
    (NOT a strongly-typed path field) must NOT trigger block.

    This was the canonical false-positive case: a tool that returned an error
    message containing '/opt/goapi/goapi' was being blocked because the old
    substring matcher found the path anywhere in paramsStr.
    """
    script = """
const handlers = {};
plugin.register({
  config: { forbiddenPaths: ["/opt/goapi"] },
  on(n, f, o) { handlers[n] = f; },
});
const res = await handlers.before_tool_call(
  {
    toolName: "exec",
    params: {
      command: "ls",
      message: "previous error at /opt/goapi/goapi: permission denied",
      content: "see /opt/goapi/README.md for context",
    },
  },
  { sessionKey: "s_fp_freetext" }
);
const blocked = res && res.block === true ? "BLOCKED" : "PASS";
console.log("FP_FREETEXT:" + blocked);
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    line = [l for l in r.stdout.splitlines() if l.startswith("FP_FREETEXT:")][-1]
    assert line.endswith("PASS"), (
        f"Forbidden path in free-text 'message'/'content' fields must not block "
        f"(P1-3 fix). Got: {line}"
    )


def test_forbidden_path_as_typed_field_with_prefix_blocks():
    """When a forbidden path appears as a STRONGLY-TYPED path field AND
    matches by prefix (or equality), the call IS blocked."""
    script = """
const handlers = {};
plugin.register({
  config: { forbiddenPaths: ["/opt/goapi"] },
  on(n, f, o) { handlers[n] = f; },
});
const res = await handlers.before_tool_call(
  {
    toolName: "write_file",
    params: { target: "/opt/goapi/goapi" },
  },
  { sessionKey: "s_fp_typed" }
);
console.log("FP_TYPED:" + JSON.stringify(res));
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    line = [l for l in r.stdout.splitlines() if l.startswith("FP_TYPED:")][-1]
    obj = json.loads(line[len("FP_TYPED:"):])
    assert obj.get("block") is True, (
        f"Typed path '/opt/goapi/goapi' must block when /opt/goapi is forbidden. "
        f"Got: {obj}"
    )


def test_forbidden_path_as_substring_of_safe_path_does_not_block():
    """If '/opt/goapi' is forbidden, but a SAFE path '/opt/goapi-docs/readme.md'
    is requested, the call must NOT block (no prefix match).

    This catches the inverse failure mode: blocking on substring where the safe
    path merely *contains* the forbidden string but is in a different subtree.
    """
    script = """
const handlers = {};
plugin.register({
  config: { forbiddenPaths: ["/opt/goapi"] },
  on(n, f, o) { handlers[n] = f; },
});
const res = await handlers.before_tool_call(
  {
    toolName: "read_file",
    params: { path: "/opt/goapi-docs/readme.md" },
  },
  { sessionKey: "s_fp_substring" }
);
const blocked = res && res.block === true ? "BLOCKED" : "PASS";
console.log("FP_SUBSTRING:" + blocked);
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    line = [l for l in r.stdout.splitlines() if l.startswith("FP_SUBSTRING:")][-1]
    assert line.endswith("PASS"), (
        f"Safe path '/opt/goapi-docs/readme.md' must not block when only "
        f"'/opt/goapi' is forbidden (substring match is NOT prefix match). "
        f"Got: {line}"
    )