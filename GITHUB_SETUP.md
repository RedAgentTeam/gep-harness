# gep-harness GitHub 发布完整指南

> **日期**：2026-08-15 20:07
> **作者**：devagent @ 胡老师指令
> **目标**：把 gep-harness 推到 https://github.com/RedAgentTeam/gep-harness

---

## 前置确认（5 条铁律）

1. ✅ 不编凭证（SOUL #1）— <user-email> 由你自己配
2. ✅ 不凭印象诊断 — 所有路径都先查
3. ✅ 不 write 覆盖 memory — MEMORY.md 全程 append
4. ❌ 不在本机做生产相关改动 — 本机 <本机 dev IP> 仅 dev/test
5. ❌ 不在没确认的情况下动生产节点机器 — 美机全程未触碰

---

## Step 1：网页创建仓库

```
浏览器：https://github.com/new

Repository name: gep-harness
Description: GEP v1.12.1 strict Harness — borrow from DeepSeek, self-evolve, A2A collaboration, cross-discipline 5 libraries
Visibility: ✅ Public

⚠️ Initialize 部分：全部不勾选
  ☐ Add a README file
  ☐ Add .gitignore
  ☐ Choose a license

点击 "Create repository"
```

---

## Step 2：本机 SSH key 配置

```bash
# 1. 生成 SSH key（专用 GitHub，不覆盖已有 key）
ssh-keygen -t ed25519 -C "<user-email>" -f ~/.ssh/github_redagentteam_ed25519

# 2. 配 ~/.ssh/config
cat >> ~/.ssh/config << 'EOF'
Host github.com
    IdentityFile ~/.ssh/github_redagentteam_ed25519
EOF

# 3. 测试 SSH 连接
ssh -T git@github.com
# 第一次会问 fingerprint，输入 yes
# 成功应看到：Hi RedAgentTeam! You've successfully authenticated...
```

---

## Step 3：GitHub 网页加 SSH 公钥

```
1. 浏览器打开：https://github.com/settings/keys
2. 点击 "New SSH key"
3. Title: "devagent@VM-0-11-ubuntu"
4. Key: 粘贴 `cat ~/.ssh/github_redagentteam_ed25519.pub` 的输出
5. 点击 "Add SSH key"
```

---

## Step 4：本机 git config（你自己配，SOUL #1）

```bash
git config --global user.name "Red Ho"
git config --global user.email "<user-email>"
```

---

## Step 5：本机连接 gep-harness 仓库

```bash
cd /data/disk/gep-harness
git remote add origin git@github.com:RedAgentTeam/gep-harness.git
git remote -v
```

---

## Step 6：推送（首次）

```bash
cd /data/disk/gep-harness
git push -u origin master
```

---

## Step 7：网页设置（推送后）

### 7.1 About 段

```
⚙️ Settings → General → Description
"借用 DeepSeek Harness + 跨学科 5 库 + A2A 协作 + Evolver 半自动"

⚙️ Website（可选）
留空
```

### 7.2 Topics（标签）

```
⚙️ Settings → General → Topics
- gep-harness
- self-evolving
- agent-collaboration
- cross-discipline
- solid-gene
- evomap
- gdi
- knowledge-graph
- append-only
- safe-solidify
```

### 7.3 Releases

```
1. https://github.com/RedAgentTeam/gep-harness/releases → Create a new release
2. Choose a tag: v33.0
3. Release title: "gep-harness v33.0 — 完整闭环科研级 Harness"
4. Description: 见下方"v33.0 Release Notes"
```

### 7.4 v33.0 Release Notes

```markdown
## gep-harness v33.0

GEP v1.12.1 strict Harness — 借鉴 DeepSeek Harness + 跨学科 5 库 + A2A 协作

### Features
- ✅ 跨 5 库 evidence v3.0 神经元网络（闭环互引）
- ✅ 5 格式可视化（PNG/SVG/PDF/EPS/MD）
- ✅ GitHub Actions CI（多 Python + 多 OS + 覆盖率）
- ✅ CHANGELOG 自动生成 + 自动 commit
- ✅ Solidify safe reject 守护（v10.1）
- ✅ A2A 本机双向 157/157 验证

### Testing
- ✅ pytest 59/59 PASS
- ✅ GEP strict 7/7
- ✅ cron safe reject 守护实战验证

### Documentation
- 📚 README.md (中文)
- 📚 README.en.md (English)
- 📚 CONTRIBUTING.md
- 📚 docs/ROADMAP_INDEX.md（89 期历史索引）
- 📚 docs/ROADMAP_v33.md（最新）
- 📚 docs/CROSS_NODE_DEPLOY.md
- 📚 docs/SOLIDIFY.md
- 📚 learnings/runtime-learning-2026-08-15-gep-harness-full-recap.md

### 3 Untouchable Rules
1. ❌ No Skill abstraction
2. ❌ No runtime plugin loading
3. ❌ No automatic Solidify

### License
MIT
```

---

## 已自动准备的（我做完的）

- ✅ LICENSE（MIT）
- ✅ README.md + README.en.md（双语）
- ✅ CONTRIBUTING.md
- ✅ OPEN_SOURCE_PLAN.md
- ✅ docs/CROSS_NODE_DEPLOY.md
- ✅ .github/workflows/ci.yml（GitHub Actions CI）
- ✅ examples/（7 个实战案例）
- ✅ .gitignore（GitHub 标准 Python）
- ✅ events.jsonl 移除跟踪（32M，保留 FS）

---

## 待你执行（5 步）

1. 网页创建仓库（Step 1）
2. 生成 SSH key + 配置（Step 2）
3. GitHub 加 SSH 公钥（Step 3）
4. 本机 git config user.name/email（Step 4）
5. `git push -u origin master`（Step 6）

**预计 5 分钟**。

---

## 安全提示

| ✅ | ❌ |
|---|---|
| 仓库 public（科研公开）| 仓库 private（你确定要？）|
| 推送前 review .gitignore| 推送 .env 或 credentials|
| SSH key 专用 GitHub| 复用其他 key|
| git config user.email = <user-email>（你自己配）| 我代你配（违反 SOUL #1）|

---

_作者：devagent | 创建：2026-08-15 20:07 | 项目：gep-harness_