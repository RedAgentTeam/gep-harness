"""Test trust_persist.py v24.0 — integrity check + audit log + verify。"""

import json
import sys
from pathlib import Path

REPO = Path("/data/disk/gep-harness")
sys.path.insert(0, str(REPO / "scripts"))

import trust_persist as tp


SAMPLE_EDGES = {
    "BeautifulMathematics": {"cell-biology": 0.91},
    "cell-biology": {"BeautifulMathematics": 0.91},
}


def setup_function(_):
    """每个测试前清掉持久化和 audit 文件。"""
    tp.clear_active_edges()
    log = tp.get_audit_log_path()
    if log.exists():
        log.unlink()


def teardown_function(_):
    """每个测试后清理（防止污染）。"""
    tp.clear_active_edges()
    log = tp.get_audit_log_path()
    if log.exists():
        log.unlink()
    from cross_library_auto import set_active_edges
    set_active_edges(None)


def test_compute_checksum_deterministic():
    """compute_checksum 对相同输入返回相同 hash。"""
    c1 = tp.compute_checksum(SAMPLE_EDGES)
    c2 = tp.compute_checksum(SAMPLE_EDGES)
    assert c1 == c2
    assert len(c1) == 64  # SHA256 hex


def test_compute_checksum_order_independent():
    """compute_checksum 用 sort_keys，顺序无关。"""
    edges_a = {"A": {"X": 0.5}, "B": {"X": 0.5}}
    edges_b = {"B": {"X": 0.5}, "A": {"X": 0.5}}
    assert tp.compute_checksum(edges_a) == tp.compute_checksum(edges_b)


def test_save_active_edges_v2_schema():
    """save_active_edges 写 v2 schema + checksum + version。"""
    path = tp.save_active_edges(SAMPLE_EDGES, source="test")
    data = json.loads(path.read_text())
    assert data["version"] == "v2"
    assert data["schema"] == "trust-active-edges-v2"
    assert "checksum_sha256" in data
    assert data["checksum_sha256"] == tp.compute_checksum(SAMPLE_EDGES)
    assert data["libraries"] == 2
    assert data["source"] == "test"


def test_save_active_edges_writes_audit_log():
    """save_active_edges 写 audit log 一条 save 记录。"""
    log = tp.get_audit_log_path()
    if log.exists():
        log.unlink()
    tp.save_active_edges(SAMPLE_EDGES, source="test")
    assert log.exists()
    lines = log.read_text().strip().split("\n")
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "save"
    assert record["source"] == "test"
    assert record["libraries"] == 2
    assert "checksum_sha256" in record
    assert "ts" in record


def test_clear_active_edges_writes_audit_log():
    """clear_active_edges 写 audit log 一条 clear 记录。"""
    tp.save_active_edges(SAMPLE_EDGES)
    log = tp.get_audit_log_path()
    lines_before = len(log.read_text().strip().split("\n")) if log.exists() else 0
    tp.clear_active_edges()
    lines_after = len(log.read_text().strip().split("\n"))
    assert lines_after == lines_before + 1
    last = json.loads(log.read_text().strip().split("\n")[-1])
    assert last["event"] == "clear"


def test_auto_load_active_edges_writes_audit_log():
    """auto_load_active_edges 写 audit log 一条 auto_load 记录。"""
    tp.save_active_edges(SAMPLE_EDGES)
    log = tp.get_audit_log_path()
    lines_before = len(log.read_text().strip().split("\n"))
    tp.auto_load_active_edges()
    lines_after = len(log.read_text().strip().split("\n"))
    assert lines_after == lines_before + 1
    last = json.loads(log.read_text().strip().split("\n")[-1])
    assert last["event"] == "auto_load"


def test_audit_log_is_append_only():
    """audit log 不会 truncate 已有记录。"""
    tp.save_active_edges(SAMPLE_EDGES)
    log = tp.get_audit_log_path()
    lines_before = len(log.read_text().strip().split("\n"))
    # 多次操作
    tp.clear_active_edges()
    tp.save_active_edges(SAMPLE_EDGES)
    tp.auto_load_active_edges()
    lines_after = len(log.read_text().strip().split("\n"))
    # 应有 4 条新记录（clear + save + auto_load + 之前的 1 条 save）
    assert lines_after >= lines_before + 3


def test_verify_active_edges_ok():
    """verify_active_edges 正常文件 → (True, ok message)。"""
    tp.save_active_edges(SAMPLE_EDGES, source="test")
    ok, _ = tp.verify_active_edges()
    assert ok is True


def test_verify_active_edges_no_file():
    """verify_active_edges 文件不存在 → (False, error message)。"""
    ok, msg = tp.verify_active_edges()
    assert ok is False
    assert "不存在" in msg


def test_verify_active_edges_corrupted_checksum():
    """verify_active_edges 文件被篡改 → (False, checksum mismatch)。"""
    tp.save_active_edges(SAMPLE_EDGES)
    path = tp.get_persist_path()
    data = json.loads(path.read_text())
    # 篡改 dynamic_edges 内容
    data["dynamic_edges"]["BeautifulMathematics"]["cell-biology"] = 0.5
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    ok, msg = tp.verify_active_edges()
    assert ok is False
    assert "checksum" in msg.lower()


def test_verify_active_edges_wrong_version():
    """verify_active_edges version 不为 v2 → (False, version 错误)。"""
    tp.save_active_edges(SAMPLE_EDGES)
    path = tp.get_persist_path()
    data = json.loads(path.read_text())
    data["version"] = "v999"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    ok, msg = tp.verify_active_edges()
    assert ok is False
    assert "version" in msg.lower()


def test_verify_active_edges_lib_count_mismatch():
    """verify_active_edges libraries 计数不匹配 → (False)。"""
    tp.save_active_edges(SAMPLE_EDGES)
    path = tp.get_persist_path()
    data = json.loads(path.read_text())
    data["libraries"] = 99  # 错的
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    ok, msg = tp.verify_active_edges()
    assert ok is False
    assert "libraries" in msg.lower() or "计数" in msg


def test_verify_active_edges_logs_ok():
    """verify_active_edges 成功 → 写 audit log 一条 verify_ok。"""
    tp.save_active_edges(SAMPLE_EDGES)
    log = tp.get_audit_log_path()
    lines_before = len(log.read_text().strip().split("\n"))
    ok, _ = tp.verify_active_edges()
    assert ok is True
    lines_after = len(log.read_text().strip().split("\n"))
    assert lines_after == lines_before + 1
    last = json.loads(log.read_text().strip().split("\n")[-1])
    assert last["event"] == "verify_ok"


def test_cli_verify_command():
    """CLI trust_persist.py verify 子命令跑通。"""
    tp.save_active_edges(SAMPLE_EDGES)
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/trust_persist.py", "verify"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "integrity OK" in result.stdout


def test_cron_workflow_includes_verify():
    """cron_hourly_workflow 应包含 trust_persist verify 步骤。"""
    import inspect
    src = inspect.getsource(__import__("cron_hourly_workflow").main)
    assert "trust_persist" in src
    assert '"verify"' in src


def test_cron_workflow_7_steps_message():
    """cron_hourly_workflow 末尾打印 "7 步全部 OK"。"""
    src = open(REPO / "scripts" / "cron_hourly_workflow.py").read()
    assert "7 步全部 OK" in src


def test_audit_log_path_xdg():
    """audit_log 路径与 active_edges 同目录。"""
    edges_path = tp.get_persist_path()
    audit_path = tp.get_audit_log_path()
    assert audit_path.parent == edges_path.parent
    assert audit_path.name == "audit_trust.log"