"""Pre-solidify declaration: change_kind, before/after evidence, rollback.

A score jump can be a fault fix rather than a new capability. Solidify must
see which one it is, with the same eval on both sides, both numbers, an
evidence path, and a rollback point. Anything missing or malformed refuses
the write and exits non-zero.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import solidify as sf


def _valid(**overrides):
    decl = {
        "change_kind": "fault_fix",
        "before": {"eval": "MATH-500", "value": 7.9},
        "after": {"eval": "MATH-500", "value": 48.1},
        "evidence_path": "logs/exp8/eval/merged.json",
        "rollback": "c7c7ec9",
    }
    decl.update(overrides)
    return decl


def _gene(gid="decl_gene", declaration=None, include_declaration=True):
    gene = {
        "type": "Gene",
        "schema_version": "1.12.1",
        "id": gid,
        "signals_match": [f"sig_{gid}"],
        "summary": f"summary_{gid}",
        "category": "repair",
        "strategy": ["a", "b", "c"],
        "constraints": ["c1"],
        "validation": {"check": "ok"},
    }
    gene["asset_id"] = sf.compute_asset_id(gene)
    if include_declaration:
        gene["solidify_declaration"] = _valid() if declaration is None else declaration
    return gene


def _stage(tmp_path, monkeypatch, gene, filename="decl_gene.json"):
    fake_genes = tmp_path / "plan" / "genes"
    fake_events = tmp_path / "plan" / "events"
    fake_genes.mkdir(parents=True)
    fake_events.mkdir(parents=True)
    monkeypatch.setattr(sf, "PLAN_GENES", fake_genes)
    monkeypatch.setattr(sf, "PLAN_EVENTS", fake_events)
    monkeypatch.setattr(sf, "GEP_HARNESS", tmp_path)
    staging = tmp_path / "staging"
    staging.mkdir()
    path = staging / filename
    path.write_text(json.dumps(gene), encoding="utf-8")
    return staging, fake_genes, fake_events


def _run(staging, extra_args=None):
    argv = ["solidify.py", "--staging", str(staging), "--yes"]
    if extra_args:
        argv.extend(extra_args)
    with patch.object(sys, "argv", argv):
        try:
            sf.main()
        except SystemExit as caught:
            return caught.code
    return 0


def test_parse_pass_fault_fix_and_new_capability():
    """Both legal change_kind values normalize and produce no problems."""
    problems, normalized = sf.parse_solidify_declaration(_valid())
    assert problems == []
    assert normalized["change_kind"] == "fault_fix"
    assert normalized["before"] == {"eval": "MATH-500", "value": 7.9}
    assert normalized["after"]["eval"] == "MATH-500"
    assert normalized["after"]["value"] == 48.1
    assert normalized["evidence_path"].endswith("merged.json")
    assert normalized["rollback"] == "c7c7ec9"

    problems, normalized = sf.parse_solidify_declaration(
        _valid(change_kind="new_capability")
    )
    assert problems == []
    assert normalized["change_kind"] == "new_capability"


def test_parse_pass_flat_cli_shape_and_numeric_strings():
    """CLI-style flat fields and numeric strings are accepted."""
    problems, normalized = sf.parse_solidify_declaration({
        "change_kind": "new_capability",
        "before_eval": "GSM8K",
        "before": "13.8",
        "after_eval": "GSM8K",
        "after": "67.1",
        "evidence": "logs/exp8/gsm8k/merged.json",
        "rollback": "backup:/tmp/genes-before.tar",
    })
    assert problems == []
    assert normalized["before"] == {"eval": "GSM8K", "value": 13.8}
    assert normalized["after"]["value"] == 67.1
    assert normalized["evidence_path"] == "logs/exp8/gsm8k/merged.json"


def test_pass_writes_gene_and_records_declaration(tmp_path, monkeypatch):
    """A complete declaration is solidified; the harness field stays off the Gene."""
    staging, fake_genes, fake_events = _stage(tmp_path, monkeypatch, _gene())
    code = _run(staging)
    assert code in (0, None)
    written = json.loads((fake_genes / "decl_gene.json").read_text(encoding="utf-8"))
    assert "solidify_declaration" not in written
    assert written["id"] == "decl_gene"
    event = json.loads((fake_events / "event_solidify_decl_gene.json").read_text(encoding="utf-8"))
    recorded = event["meta"]["solidify_declaration"]
    assert recorded["change_kind"] == "fault_fix"
    assert recorded["before"]["eval"] == recorded["after"]["eval"] == "MATH-500"
    assert recorded["rollback"] == "c7c7ec9"


def test_pass_cli_flags_without_gene_field(tmp_path, monkeypatch):
    """The same declaration can be supplied entirely on the solidify CLI."""
    staging, fake_genes, fake_events = _stage(
        tmp_path, monkeypatch, _gene(include_declaration=False),
    )
    code = _run(staging, [
        "--change-kind", "new_capability",
        "--eval-name", "MATH-500",
        "--before", "7.9",
        "--after", "48.1",
        "--evidence", "logs/exp8/eval/merged.json",
        "--rollback", "c7c7ec9",
    ])
    assert code in (0, None)
    assert (fake_genes / "decl_gene.json").exists()
    event = json.loads((fake_events / "event_solidify_decl_gene.json").read_text(encoding="utf-8"))
    assert event["meta"]["solidify_declaration"]["change_kind"] == "new_capability"


@pytest.mark.parametrize("overrides,needle", [
    ({"change_kind": None}, "missing change_kind"),
    ({"before": {"eval": "MATH-500"}}, "missing before.value"),
    ({"after": {"eval": "MATH-500"}}, "missing after.value"),
    ({"before": {"value": 7.9}}, "missing before.eval"),
    ({"after": {"value": 48.1}}, "missing after.eval"),
    ({"evidence_path": None}, "missing evidence_path"),
    ({"rollback": None}, "missing rollback"),
])
def test_missing_item_names_the_gap_and_writes_nothing(tmp_path, monkeypatch, capsys, overrides, needle):
    """Each required item, when absent, is named, exits non-zero, and writes nothing."""
    decl = _valid()
    for key, value in overrides.items():
        if value is None:
            decl.pop(key, None)
        else:
            decl[key] = value
    staging, fake_genes, fake_events = _stage(tmp_path, monkeypatch, _gene(declaration=decl))
    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--yes"]):
        with pytest.raises(SystemExit) as caught:
            sf.main()
    assert caught.value.code not in (0, None)
    assert needle in capsys.readouterr().out
    assert not (fake_genes / "decl_gene.json").exists()
    assert not any(fake_events.glob("event_solidify_*.json"))


@pytest.mark.parametrize("overrides,needle", [
    ({"change_kind": None}, "missing change_kind"),
    ({"before": {"eval": "MATH-500"}}, "missing before.value"),
    ({"after": {"eval": "MATH-500"}}, "missing after.value"),
    ({"before": {"value": 7.9}}, "missing before.eval"),
    ({"after": {"value": 48.1}}, "missing after.eval"),
    ({"evidence_path": None}, "missing evidence_path"),
    ({"rollback": None}, "missing rollback"),
])
def test_missing_item_message(overrides, needle, capsys):
    """parse_solidify_declaration names the missing item and nothing else."""
    decl = _valid()
    for key, value in overrides.items():
        if value is None:
            decl.pop(key, None)
        else:
            decl[key] = value
    problems, normalized = sf.parse_solidify_declaration(decl)
    assert normalized is None
    assert problems == [needle]
    assert needle.split()[1] in problems[0]


def test_invalid_change_kind():
    problems, normalized = sf.parse_solidify_declaration(_valid(change_kind="optimize"))
    assert normalized is None
    assert any(p.startswith("invalid change_kind:") for p in problems)
    assert "optimize" in problems[0]


def test_mismatched_eval_names():
    decl = _valid(before={"eval": "MATH-500", "value": 7.9}, after={"eval": "GSM8K", "value": 67.1})
    problems, normalized = sf.parse_solidify_declaration(decl)
    assert normalized is None
    assert problems == ["eval name mismatch: before.eval='MATH-500' after.eval='GSM8K'"]


def test_empty_paths():
    problems, _ = sf.parse_solidify_declaration(_valid(evidence_path="   ", rollback="c7c7ec9"))
    assert problems == ["empty evidence_path"]
    problems, _ = sf.parse_solidify_declaration(_valid(rollback="  "))
    assert problems == ["empty rollback"]


def test_invalid_number():
    decl = _valid(before={"eval": "MATH-500", "value": "n/a"})
    problems, normalized = sf.parse_solidify_declaration(decl)
    assert normalized is None
    assert problems == ["invalid before.value: 'n/a'"]


def test_refuse_on_missing_exits_nonzero_and_writes_nothing(tmp_path, monkeypatch, capsys):
    """main() refuses a candidate with no declaration: non-zero, no gene file."""
    staging, fake_genes, fake_events = _stage(
        tmp_path, monkeypatch, _gene(include_declaration=False),
    )
    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--yes"]):
        with pytest.raises(SystemExit) as caught:
            sf.main()
    assert caught.value.code not in (0, None)
    out = capsys.readouterr().out
    assert "missing change_kind" in out
    assert "missing before.value" in out
    assert "missing after.value" in out
    assert "missing evidence_path" in out
    assert "missing rollback" in out
    assert "拒绝固化" in out
    assert "未写入任何 Gene" in out
    assert not (fake_genes / "decl_gene.json").exists()
    assert not any(fake_events.glob("event_solidify_*.json"))


def test_refuse_invalid_change_kind_exits_nonzero(tmp_path, monkeypatch, capsys):
    staging, fake_genes, _events = _stage(
        tmp_path, monkeypatch, _gene(declaration=_valid(change_kind="bugfix")),
    )
    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--yes"]):
        with pytest.raises(SystemExit) as caught:
            sf.main()
    assert caught.value.code not in (0, None)
    out = capsys.readouterr().out
    assert "invalid change_kind:" in out
    assert "bugfix" in out
    assert not (fake_genes / "decl_gene.json").exists()


def test_refuse_mismatched_eval_names_exits_nonzero(tmp_path, monkeypatch, capsys):
    decl = _valid(
        before={"eval": "MATH-500", "value": 7.9},
        after={"eval": "GSM8K", "value": 67.1},
    )
    staging, fake_genes, _events = _stage(tmp_path, monkeypatch, _gene(declaration=decl))
    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--yes"]):
        with pytest.raises(SystemExit) as caught:
            sf.main()
    assert caught.value.code not in (0, None)
    out = capsys.readouterr().out
    assert "eval name mismatch" in out
    assert "MATH-500" in out
    assert "GSM8K" in out
    assert not (fake_genes / "decl_gene.json").exists()


def test_one_bad_declaration_blocks_the_whole_run(tmp_path, monkeypatch, capsys):
    """A sibling with a valid declaration is not written either."""
    staging, fake_genes, _events = _stage(
        tmp_path, monkeypatch, _gene(gid="good_gene"), filename="good_gene.json",
    )
    bad = _gene(gid="bad_gene", include_declaration=False)
    (staging / "bad_gene.json").write_text(json.dumps(bad), encoding="utf-8")
    with patch.object(sys, "argv", ["solidify.py", "--staging", str(staging), "--yes"]):
        with pytest.raises(SystemExit) as caught:
            sf.main()
    assert caught.value.code not in (0, None)
    assert "missing change_kind" in capsys.readouterr().out
    assert not (fake_genes / "good_gene.json").exists()
    assert not (fake_genes / "bad_gene.json").exists()


def test_subprocess_missing_declaration_exits_nonzero(tmp_path):
    """The solidify process itself exits non-zero and does not touch plan/genes."""
    staging = tmp_path / "staging"
    staging.mkdir()
    gid = "subprocess_refuse_decl"
    gene = _gene(gid=gid, include_declaration=False)
    (staging / f"{gid}.json").write_text(json.dumps(gene), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/solidify.py"),
         "--staging", str(staging), "--yes"],
        capture_output=True, text=True, cwd=str(REPO), timeout=60,
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "missing change_kind" in combined
    assert "missing before.value" in combined
    assert "missing evidence_path" in combined
    assert "missing rollback" in combined
    assert "拒绝固化" in combined
    assert not (REPO / "plan" / "genes" / f"{gid}.json").exists()
    assert not (REPO / "plan" / "events" / f"event_solidify_{gid}.json").exists()
