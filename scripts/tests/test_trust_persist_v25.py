"""Test trust_persist.py v25.0 — audit rotate + query + stats。"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
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
    for old in log.parent.glob("audit_trust.log.*"):
        old.unlink()


def teardown_function(_):
    """每个测试后清理（防止污染）。"""
    tp.clear_active_edges()
    log = tp.get_audit_log_path()
    if log.exists():
        log.unlink()
    for old in log.parent.glob("audit_trust.log.*"):
        old.unlink()
    # 重置 rotate 阈值
    tp.MAX_AUDIT_LOG_SIZE = 1024 * 1024
    tp.AUDIT_KEEP_ROTATED = 5
    from cross_library_auto import set_active_edges
    set_active_edges(None)


def test_max_audit_log_size_constant():
    """MAX_AUDIT_LOG_SIZE 常量默认 1MB。"""
    assert tp.MAX_AUDIT_LOG_SIZE == 1024 * 1024
    assert tp.AUDIT_KEEP_ROTATED == 5


def test_rotate_audit_log_no_rotate_small():
    """小 log 不应触发 rotate。"""
    log = tp.get_audit_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("small content")
    tp._rotate_audit_log_if_needed(log)
    # 文件不应被轮转
    assert log.exists()
    rotated = list(log.parent.glob("audit_trust.log.*"))
    assert rotated == []


def test_rotate_audit_log_triggers():
    """log 超过阈值应触发 rotate（带日期后缀）。"""
    log = tp.get_audit_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    # 临时降低阈值便于测试
    tp.MAX_AUDIT_LOG_SIZE = 100
    log.write_text("x" * 200)
    tp._rotate_audit_log_if_needed(log)
    # 原文件应不存在（被轮转）
    assert not log.exists()
    # 应有 rotated 文件
    rotated = list(log.parent.glob("audit_trust.log.*"))
    assert len(rotated) == 1
    assert rotated[0].name.startswith("audit_trust.log.2")


def test_rotate_keeps_only_n_files():
    """rotate 后只保留最近 AUDIT_KEEP_ROTATED 个文件。"""
    log = tp.get_audit_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    tp.MAX_AUDIT_LOG_SIZE = 50
    tp.AUDIT_KEEP_ROTATED = 3
    # 手动创建 5 个 rotated 文件
    for i in range(5):
        rotated = log.with_name(f"audit_trust.log.20260820_08000{i}")
        rotated.write_text(f"old rotated {i}")
    # 再触发一次 rotate
    log.write_text("x" * 100)
    tp._rotate_audit_log_if_needed(log)
    rotated = sorted(log.parent.glob("audit_trust.log.*"))
    assert len(rotated) == 3  # 只保留 3 个


def test_write_audit_log_triggers_rotate():
    """write_audit_log 在文件超阈值时应自动 rotate。"""
    tp.MAX_AUDIT_LOG_SIZE = 200
    for i in range(20):
        tp.write_audit_log("save", source=f"t{i}", libraries=5)
    log = tp.get_audit_log_path()
    # 当前文件不应太大
    if log.exists():
        assert log.stat().st_size < 1000  # 远低于 1MB
    # 至少有一个 rotated 文件
    rotated = list(log.parent.glob("audit_trust.log.*"))
    assert len(rotated) >= 1


def test_iter_audit_records_includes_rotated():
    """_iter_audit_records 默认包含 rotated 文件。"""
    log = tp.get_audit_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    # 写一些到当前
    tp.write_audit_log("save", source="current1")
    tp.write_audit_log("save", source="current2")
    # 手动创建 rotated 文件
    rotated = log.with_name("audit_trust.log.20260101_000000")
    rotated.write_text(json.dumps({"ts": "2026-01-01T00:00:00", "event": "save", "source": "rotated1"}) + "\n")
    # 验证 iter 返回所有
    recs = list(tp._iter_audit_records())
    sources = [r.get("source") for r in recs]
    assert "current1" in sources
    assert "current2" in sources
    assert "rotated1" in sources


def test_query_audit_log_no_filter():
    """query_audit_log 不带 filter 返回所有记录（按 limit）。"""
    for i in range(5):
        tp.write_audit_log("save", source=f"q{i}")
    recs = tp.query_audit_log(limit=10)
    assert len(recs) == 5


def test_query_audit_log_event_filter():
    """query_audit_log --event=save 只返回 save 记录。"""
    tp.write_audit_log("save", source="s1")
    tp.write_audit_log("clear")
    tp.write_audit_log("save", source="s2")
    recs = tp.query_audit_log(event="save", limit=10)
    assert len(recs) == 2
    for r in recs:
        assert r["event"] == "save"


def test_query_audit_log_since_filter():
    """query_audit_log --since 过滤时间之前的记录。"""
    tp.write_audit_log("save", source="old")
    tp.write_audit_log("save", source="new")
    # 假设 since = 2099（过滤掉所有）
    recs = tp.query_audit_log(since="2099-01-01T00:00:00", limit=10)
    assert recs == []


def test_query_audit_log_limit():
    """query_audit_log --limit 限制返回条数。"""
    for i in range(10):
        tp.write_audit_log("save", source=f"l{i}")
    recs = tp.query_audit_log(limit=3)
    assert len(recs) == 3


def test_query_audit_log_reverse_order():
    """query_audit_log 返回结果按时间倒序（最新优先）。"""
    tp.write_audit_log("save", source="first")
    tp.write_audit_log("save", source="second")
    tp.write_audit_log("save", source="third")
    recs = tp.query_audit_log(limit=10)
    assert recs[0]["source"] == "third"
    assert recs[-1]["source"] == "first"


def test_audit_stats_empty():
    """audit_stats 空 log → total=0。"""
    stats = tp.audit_stats()
    assert stats["total"] == 0
    assert stats["by_event"] == {}
    assert stats["files"] == 0


def test_audit_stats_with_records():
    """audit_stats 有记录时正确分类。"""
    tp.write_audit_log("save", source="a")
    tp.write_audit_log("save", source="b")
    tp.write_audit_log("clear")
    tp.write_audit_log("auto_load")
    stats = tp.audit_stats()
    assert stats["total"] == 4
    assert stats["by_event"]["save"] == 2
    assert stats["by_event"]["clear"] == 1
    assert stats["by_event"]["auto_load"] == 1
    assert stats["first_ts"] is not None
    assert stats["last_ts"] is not None


def test_audit_stats_files_count():
    """audit_stats 统计文件数（含 rotated）。"""
    log = tp.get_audit_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    tp.write_audit_log("save")
    # 手动创建 rotated
    rotated = log.with_name("audit_trust.log.20260101_000000")
    rotated.write_text("{}\n")
    stats = tp.audit_stats()
    assert stats["files"] == 2  # current + 1 rotated


def test_cli_audit_query_command():
    """CLI audit-query 子命令跑通。"""
    tp.write_audit_log("save", source="cli_test")
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/trust_persist.py", "audit-query", "--limit=5"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "查询结果" in result.stdout
    assert "save" in result.stdout


def test_cli_audit_stats_command():
    """CLI audit-stats 子命令跑通。"""
    tp.write_audit_log("save")
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/trust_persist.py", "audit-stats"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "总记录数" in result.stdout
    assert "按事件分布" in result.stdout


def test_corrupted_audit_line_skipped():
    """_iter_audit_records 应跳过损坏的 JSON 行。"""
    log = tp.get_audit_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        json.dumps({"ts": "2026-01-01T00:00:00", "event": "save"}) + "\n"
        + "not valid json\n"
        + json.dumps({"ts": "2026-01-02T00:00:00", "event": "clear"}) + "\n"
    )
    recs = list(tp._iter_audit_records())
    assert len(recs) == 2  # 损坏行被跳过
    assert recs[0]["event"] == "save"
    assert recs[1]["event"] == "clear"


def test_rotate_handles_duplicate_timestamp():
    """rotate 同秒内多次触发应避免覆盖。"""
    log = tp.get_audit_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    tp.MAX_AUDIT_LOG_SIZE = 50
    # 手动创建同名 rotated 文件
    log.write_text("x" * 100)
    tp._rotate_audit_log_if_needed(log)
    log.write_text("y" * 100)  # 再次触发
    tp._rotate_audit_log_if_needed(log)
    rotated = list(log.parent.glob("audit_trust.log.*"))
    assert len(rotated) == 2  # 应有 2 个不同名 rotated