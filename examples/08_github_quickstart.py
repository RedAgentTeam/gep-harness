"""Example 08 — GitHub clone 后 5 分钟上手 quickstart。

适合刚 clone gep-harness 的新用户：

    git clone https://github.com/RedAgentTeam/gep-harness.git
    cd gep-harness
    python3 examples/08_github_quickstart.py

跑这个脚本会自动验证：
1. GEP strict 校验（make verify）
2. pytest 全量（make test）
3. 5 库 evidence v3.0 闭环
4. 资产统计（genes / capsules / events）

路径无关 —— 用 __file__ 自动推断 repo 根，无需硬编码 /data/disk/...
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent  # 路径无关：脚本在 examples/，上溯一级


def run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    print(f"  → {' '.join(cmd)}")
    return subprocess.run(
        cmd, cwd=REPO, capture_output=True, text=True, timeout=timeout
    )


def check_python_version() -> None:
    """GEP harness 需要 Python 3.10+"""
    v = sys.version_info
    if v < (3, 10):
        print(f"  ✗ Python {v.major}.{v.minor} 不支持（需要 3.10+）")
        sys.exit(1)
    print(f"  ✓ Python {v.major}.{v.minor}.{v.micro}")


def check_make() -> None:
    """检查 GNU make 是否可用（CI/CD 友好）"""
    r = subprocess.run(["make", "--version"], capture_output=True, text=True)
    if r.returncode != 0:
        print("  ✗ make 不可用 — 安装 build-essential（apt）或 xcode-select（macOS）")
        sys.exit(1)
    print("  ✓ GNU make")


def count_assets() -> dict[str, int]:
    """统计 plan/ 目录的 genes / capsules / events 数"""
    counts = {"genes": 0, "capsules": 0, "events": 0, "mutations": 0}
    for kind in ("genes", "capsules", "events"):
        d = REPO / "plan" / kind
        if d.exists():
            counts[kind] = sum(1 for _ in d.glob("*.json"))
    mut = REPO / "plan" / "mutations"
    if mut.exists():
        counts["mutations"] = sum(1 for _ in mut.glob("*.json"))
    return counts


def main() -> None:
    print("=== Example 08: GitHub Quickstart ===\n")

    print("Step 1: 环境检查")
    check_python_version()
    check_make()
    print(f"  ✓ repo: {REPO}\n")

    print("Step 2: GEP strict 校验")
    result = run(["python3", "scripts/verify_assets.py"], timeout=60)
    summary = [l for l in result.stdout.splitlines() if "verified" in l.lower()]
    if summary:
        print(f"  {summary[-1].strip()}")
    if result.returncode != 0:
        print(f"  ✗ verify_assets.py 失败\n  {result.stderr[:300]}")
        sys.exit(1)
    print()

    print("Step 3: pytest 全量（557+ 测试）")
    result = run(
        ["python3", "-m", "pytest", "scripts/tests/", "openclaw-a2a/tests/", "-q"],
        timeout=300,
    )
    if result.returncode == 0:
        # 提取最后一行有 "passed" 的 summary
        for line in reversed(result.stdout.splitlines()):
            if "passed" in line and "no tests ran" not in line:
                print(f"  ✓ {line.strip()}")
                break
    else:
        print(f"  ✗ pytest 失败 (exit {result.returncode})")
        last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr[:300]
        print(f"    {last_line}")
        sys.exit(1)
    print()

    print("Step 4: 资产统计")
    counts = count_assets()
    for k, v in counts.items():
        print(f"  {k:10s}: {v}")
    print()

    print("Step 5: 5 库 evidence v3.0 闭环（示例 1 个 gene）")
    sample = REPO / "plan" / "genes" / "gene_candidate_000_hot_path:exec.json"
    if sample.exists():
        sys.path.insert(0, str(REPO / "scripts"))
        from cross_library_auto import auto_cross_library_evidence

        gene = json.loads(sample.read_text())
        ev = auto_cross_library_evidence(gene, version="v3.0")
        libs_referenced = set()
        for e in ev:
            for lib in (
                "BeautifulMathematics",
                "cell-biology",
                "CognitivePsychology",
                "OpenStaxBiology",
                "evomap",
            ):
                if f"[{lib}" in e:
                    libs_referenced.add(lib)
        expected = {
            "BeautifulMathematics",
            "cell-biology",
            "CognitivePsychology",
            "OpenStaxBiology",
            "evomap",
        }
        ok = libs_referenced == expected
        print(f"  5 库闭环: {'✓' if ok else '✗'}  {libs_referenced}")
    else:
        print(f"  ⊘ 跳过（{sample.name} 不存在）")
    print()

    print("=== ✓ Quickstart 完成 ===")
    print()
    print("下一步建议：")
    print("  1. 看 README.md → 项目定位 + 4 阶段闭环")
    print("  2. 看 CONTRIBUTING.md → 如何贡献 Gene/Capsule")
    print("  3. 跑 examples/01-07 → 各项能力实战")
    print("  4. 看 docs/CROSS_NODE_DEPLOY.md → A2A 跨节点协议")
    print("  5. 生产部署前必读 AI_AUTHORSHIP.md + .gitignore 脱敏规则")


if __name__ == "__main__":
    main()