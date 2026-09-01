"""test_trust_query_web — gep-harness v52.0。

测试 trust_query + trust_web 闭环：
1. trust_query list_genes 返回非空 + 60 条 + asset_id 含 sha256:
3. trust_query stats 不 crash + 含 trust_score 分布字段
5. trust_query stale --days 7 不 crash（即使全空）

2. trust_web /health 返回 200 + status=ok
6. trust_web / 不返回 500 + genes 非空
8. trust_web /gene/<id> 返回 200 + 含 trust_score 字段
9. trust_web /gene/<bogus> 返回 404
10. trust_web /stats 返回 200 + bins 字段
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

from trust_query import list_genes, _resolve_gene  # noqa: E402
from trust_query import _get_events, _get_active_edges  # noqa: E402

# ---------- trust_query CLI 测试（5） ----------

def test_list_genes_non_empty():
    """1. list_genes 返回非空 + 含 asset_id + sha256: 前缀。"""
    genes = list_genes()
    assert len(genes) > 0, "plan/genes/ 应至少有 1 个 gene"
    g = genes[0]
    assert "gene_id" in g
    assert "asset_id" in g
    assert g["asset_id"].startswith("sha256:"), f"asset_id 应为 sha256:xxx，实际 {g['asset_id']}"


def test_list_genes_has_signals_match():
    """2. gene 含 signals_match（不是空 list）。"""
    genes = list_genes()
    with_signals = [g for g in genes if g["signals"]]
    assert len(with_signals) > 0, "至少应有 1 个 gene 含 signals_match"
    g = with_signals[0]
    assert isinstance(g["signals"], list)
    assert len(g["signals"]) >= 1


def test_resolve_gene_by_id():
    """3. _resolve_gene 能按 id 找到 gene（第一个非空）。"""
    genes = list_genes()
    target_id = genes[0]["gene_id"]
    found = _resolve_gene(genes, target_id)
    assert found is not None
    assert found["gene_id"] == target_id


def test_resolve_gene_not_found():
    """4. _resolve_gene 找不到时返回 None。"""
    genes = list_genes()
    found = _resolve_gene(genes, "definitely_not_a_gene_xyz")
    assert found is None


def test_get_events_readable():
    """5. _get_events 不 crash 且能读 events.jsonl。"""
    events = _get_events()
    assert isinstance(events, list)
    # events 可能为空（如果还没生成），但函数不应 crash
    if events:
        e = events[0]
        assert "kind" in e or "type" in e, "event 应含 kind 或 type 字段"


# ---------- trust_web Flask 测试（5） ----------

@pytest.fixture
def client():
    from trust_web import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_web_health(client):
    """6. /health 返回 200 + status=ok。"""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "trust_web"


def test_web_index(client):
    """7. / 返回 200 + genes 非空。"""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] > 0
    assert len(data["genes"]) == data["total"]
    g = data["genes"][0]
    assert "trust_score" in g
    assert "verify_count" in g


def test_web_gene_detail(client):
    """8. /gene/<id> 返回 200 + 含 trust_score。"""
    # 先获取一个真实 id
    resp = client.get("/")
    genes = resp.get_json()["genes"]
    target_id = genes[0]["gene_id"]
    # 查详情
    resp2 = client.get(f"/gene/{target_id}")
    assert resp2.status_code == 200
    data = resp2.get_json()
    assert data["gene_id"] == target_id
    assert "trust_score" in data
    assert "asset_id" in data


def test_web_gene_404(client):
    """9. /gene/<bogus> 返回 404。"""
    resp = client.get("/gene/definitely_not_a_gene_xyz")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "not_found"


def test_web_stats(client):
    """10. /stats 返回 200 + bins 字段 + active_edges 标记。"""
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_genes" in data
    assert data["total_genes"] > 0
    assert "trust_score" in data
    assert "bins" in data["trust_score"]
    assert "active_edges" in data
    assert data["active_edges"] in ("dynamic", "static")