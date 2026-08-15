# A2A 跨节点 Gene Sync — 部署状态

> 日期：2026-08-14
> 协议：A2A v0.1.0 (a2a_protocol.py)
> GEP 版本：1.12.1

## 当前状态

| 项 | 状态 |
|---|---|
| A2A 协议代码 | ✅ 完整（a2a_protocol.py + gene_sync.py） |
| GenePool 本地目录 | ✅ 已初始化（`~/.openclaw/gene-pool/`） |
| known_peers.json | ❌ 不存在（单节点，无 peer） |
| 美机 (<美机生产 IP>) SSH | ❌ Permission denied（需胡老师确认密码） |
| A2A server 运行 | ❌ 未启动（需要 peer 才有意义） |
| plan/genes/ → local/ | ❌ 未同步 |

## GenePool 目录结构

```
~/.openclaw/gene-pool/
├── local/          # 本节点产生的 Gene（GDI >= 0.7）
├── imported/       # 从 peer 接收并接受的 Gene
├── quarantined/    # GDI < 0.7，待审查
├── conflicts/      # LWW 冲突 losers
├── audit.jsonl     # 操作审计日志
└── known_peers.json # 已知 peer URL 列表
```

## 部署步骤（需要第二节点）

### 前置条件
- 两台机器都能访问对方（端口 9877 开放或通过隧道）
- 共享密钥 `A2A_SHARED_SECRET` 配置

### 步骤 1: 配置 known_peers.json

```json
["http://<peer-host>:9877"]
```

### 步骤 2: 启动 A2A server（每台机器）

```bash
cd /data/disk/gep-harness/openclaw-a2a
A2A_SHARED_SECRET=<your-secret> A2A_GENE_POOL_DIR=~/.openclaw/gene-pool \
  python3 -m openclaw-a2a.src.a2a_protocol --host 0.0.0.0 --port 9877
```

### 步骤 3: 同步 Gene（本节点 → peer）

```bash
cd /data/disk/gep-harness
A2A_SHARED_SECRET=<your-secret> \
  python3 openclaw-a2a/src/gene_sync.py --peer http://<peer-host>:9877
```

### 步骤 4: 广播（自动发现所有 known peers）

```bash
A2A_SHARED_SECRET=<your-secret> \
  python3 openclaw-a2a/src/gene_sync.py --broadcast --bootstrap http://<peer-host>:9877
```

## 当前阻塞

**需要胡老师确认：**
1. 美机 (<美机生产 IP>) SSH 凭证是否还能用？（上次 Permission denied）
2. 是否需要在美机部署第二 A2A node？
3. 还是用本机 standalone 测试 GenePool local/ 初始化即可？

## 本地测试（无需 peer）

```bash
# 初始化 GenePool
mkdir -p ~/.openclaw/gene-pool/{local,imported,quarantined,conflicts}

# 将 plan/genes/ 正式 Gene 复制到 local/
cp /data/disk/gep-harness/plan/genes/*.json ~/.openclaw/gene-pool/local/

# 验证
ls ~/.openclaw/gene-pool/local/ | wc -l
```
