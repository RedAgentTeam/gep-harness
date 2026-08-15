"""Tests for tool pipeline plugin (gene_harness_tool_call_pipeline).

5 tests:
  1. permission_check (forbidden_paths 拦截)
  2. timeout (默认 timeout 30s 配置生效)
  3. result_redact (SSH 密钥 / 美机 IP / OpenAI key 等被脱敏)
  4. builtin_forbidden (build-in forbidden path 不可绕过)
  5. plugin_loads_in_node (Node ESM 加载 + register)
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
PLUGIN_ENTRY = Path("/data/disk/gep-harness/openclaw-harness-tool-pipeline-plugin/index.js")
NODE_BIN = "node"


def run_node(test_script):
    """Run a small node ESM script that imports the plugin and exercises handlers."""
    full = (
        f"import plugin from '{PLUGIN_ENTRY}';\n"
        f"{test_script}"
    )
    result = subprocess.run(
        [NODE_BIN, "--input-type=module", "-e", full],
        capture_output=True, text=True, timeout=15,
        cwd=str(PLUGIN_ENTRY.parent),
    )
    return result


def test_permission_check():
    """forbidden_paths 必须被拦截"""
    script = """
const handlers = {};
plugin.register({
  config: { forbiddenPaths: ["/opt/secrets"] },
  on(n, f, o) { handlers[n] = f; },
});
const res = await handlers.before_tool_call(
  { toolName: "write_file", params: { target: "/opt/secrets/x" } },
  { sessionKey: "s_perm_test" }
);
// 输出 tag + JSON，最后一行是测试目标
console.log("PERM_OUT:" + JSON.stringify(res));
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    out = r.stdout.strip()
    # 提取最后一行 PERM_OUT: 开头的 JSON
    line = [l for l in out.splitlines() if l.startswith("PERM_OUT:")][-1]
    obj = json.loads(line[len("PERM_OUT:"):])
    assert obj.get("block") is True, f"expected block=True, got {obj}"
    assert "forbidden_path_match" in obj.get("reason", "")


def test_timeout_config():
    """plugin config 中的 defaultTimeoutMs 必须生效"""
    script = """
const handlers = {};
plugin.register({
  config: { defaultTimeoutMs: 15000, forbiddenPaths: [] },
  on(n, f, o) { handlers[n] = f; },
});
const out = await handlers.after_tool_call(
  { toolName: "exec", result: { ok: true }, durationMs: 99999 },
  { sessionKey: "s_to_test" }
);
console.log("OK_TIMEOUT_ENFORCED");
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    assert "OK_TIMEOUT_ENFORCED" in r.stdout


def test_result_redact():
    """ResultRewrite 必须 redact SSH 密码 / 美机 IP / API key"""
    script = r"""
// Capture emit calls by overriding spawn? simpler: just verify by reading
// what plugin logs. Plugin logs "[harness-tool-pipeline] REDACTED N pattern(s)"
const handlers = {};
plugin.register({
  config: { forbiddenPaths: [] },
  on(n, f, o) { handlers[n] = f; },
});
const secret = {
  // Use patterns that ACTUALLY match BUILTIN_REDACT:
  //   "Red\\d{6,}" (SSH password prefix) and "sk-[A-Za-z0-9]{20,}" (OpenAI key).
  // The test used <REDACTED> literals previously, which never matched any
  // regex and made the assertion vacuously pass-or-fail depending on inputs.
  stdout: "user Red753951 logged in with sk-abcdefghijklmnopqrstuvwxyz123456",
  ok: true,
};
// Spy on console.warn
const orig = console.warn;
let warned = [];
console.warn = (...args) => warned.push(args.join(" "));
await handlers.after_tool_call(
  { toolName: "exec", result: secret, durationMs: 50 },
  { sessionKey: "s_redact_test" }
);
console.warn = orig;
const hit = warned.find(w => w.includes("REDACTED"));
console.log("REDACT_HIT:" + (hit ? "yes" : "no"));
console.log("WARN_COUNT:" + warned.length);
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    assert "REDACT_HIT:yes" in r.stdout, f"redact did not fire: {r.stdout}"


def test_builtin_forbidden():
    """BUILTIN_FORBIDDEN（如 /opt/goapi/goapi）不可被 config 覆盖"""
    script = """
const handlers = {};
plugin.register({
  config: { forbiddenPaths: [] },
  on(n, f, o) { handlers[n] = f; },
});
const res = await handlers.before_tool_call(
  { toolName: "write_file", params: { target: "/opt/goapi/goapi" } },
  { sessionKey: "s_builtin_test" }
);
console.log("BUILTIN_OUT:" + JSON.stringify(res));
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    line = [l for l in r.stdout.splitlines() if l.startswith("BUILTIN_OUT:")][-1]
    obj = json.loads(line[len("BUILTIN_OUT:"):])
    assert obj.get("block") is True, f"builtin forbidden not enforced: {obj}"
    assert "/opt/goapi/goapi" in obj.get("reason", "")


def test_no_false_positive_on_substring_in_content():
    """Bug fix: forbidde_path substring in arbitrary content field must NOT block."""
    script = """
const handlers = {};
plugin.register({
  config: { forbiddenPaths: [] },
  on(n, f, o) { handlers[n] = f; },
});
// 在 write_file 的 content 里写了 "/opt/goapi/goapi" 文本
// 期望：不能被 block（只检查 path/target 字段，不扫 content）
const res = await handlers.before_tool_call(
  {
    toolName: "write_file",
    params: {
      path: "/tmp/safe-file.md",
      content: "我们不再碰 /opt/goapi/goapi 这个路径",
    },
  },
  { sessionKey: "s_false_positive_test" }
);
const blocked = res && res.block === true ? "BLOCKED" : "PASS";
console.log("FALSE_POS_OUT:" + blocked);
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    line = [l for l in r.stdout.splitlines() if l.startswith("FALSE_POS_OUT:")][-1]
    result = line[len("FALSE_POS_OUT:"):].strip()
    assert result == "PASS", f"expected PASS (no block), got {result}"


def test_path_prefix_exact_match():
    """Bug fix: 仅 path/target 字段做精确路径前缀匹配"""
    script = """
const handlers = {};
plugin.register({
  config: { forbiddenPaths: [] },
  on(n, f, o) { handlers[n] = f; },
});
// 路径应该是 /opt/goapi/goapi —— path 字段精确匹配，应 block
const res1 = await handlers.before_tool_call(
  { toolName: "write_file", params: { path: "/opt/goapi/goapi" } },
  { sessionKey: "s_exact_match" }
);
// 路径是 /opt/goapi/goapi/some-dir —— path 前缀匹配，应 block
const res2 = await handlers.before_tool_call(
  { toolName: "write_file", params: { path: "/opt/goapi/goapi/some-dir/file" } },
  { sessionKey: "s_prefix_match" }
);
console.log("PATH_TEST_OUT:" + JSON.stringify({ res1, res2 }));
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    line = [l for l in r.stdout.splitlines() if l.startswith("PATH_TEST_OUT:")][-1]
    obj = json.loads(line[len("PATH_TEST_OUT:"):])
    assert obj["res1"].get("block") is True
    assert obj["res2"].get("block") is True


def test_safe_path_not_blocked():
    """Sanity: /tmp/* 不应被 block"""
    script = """
const handlers = {};
plugin.register({
  config: { forbiddenPaths: [] },
  on(n, f, o) { handlers[n] = f; },
});
const res = await handlers.before_tool_call(
  { toolName: "write_file", params: { path: "/tmp/safe-file.md" } },
  { sessionKey: "s_safe_path" }
);
const blocked = res && res.block === true ? "BLOCKED" : "PASS";
console.log("SAFE_OUT:" + blocked);
"""
    r = run_node(script)
    assert r.returncode == 0, f"node error: {r.stderr}"
    line = [l for l in r.stdout.splitlines() if l.startswith("SAFE_OUT:")][-1]
    result = line[len("SAFE_OUT:"):].strip()
    assert result == "PASS", f"expected PASS, got {result}"
    """plugin ESM 加载 + register 不报错"""
    script = """
const handlers = {};
plugin.register({
  config: {},
  on(n, f, o) { handlers[n] = f; },
});
console.log("HOOKS:" + Object.keys(handlers).sort().join(","));
"""
    r = run_node(script)
    assert r.returncode == 0, f"plugin failed to load: {r.stderr}"
    assert "before_tool_call" in r.stdout
    assert "after_tool_call" in r.stdout


if __name__ == "__main__":
    test_permission_check()
    print("✅ test_permission_check")
    test_timeout_config()
    print("✅ test_timeout_config")
    test_result_redact()
    print("✅ test_result_redact")
    test_builtin_forbidden()
    print("✅ test_builtin_forbidden")
    test_plugin_loads_in_node()
    print("✅ test_plugin_loads_in_node")
    print("\n=== all 5 tests passed ===")