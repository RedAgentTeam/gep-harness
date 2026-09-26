# 安全策略

## 适用版本

请对照当前 GitHub Release 报告问题。现在的发布版本是 **v54.0**。更早的 `v33.0` 不再作为当前版本接受安全修复。

## 报告方式

不要在公开 Issue 里粘贴密钥、令牌、私钥或未公开的服务器地址。

请使用 GitHub 的私密通报：

https://github.com/RedAgentTeam/gep-harness/security/advisories/new

写清影响范围、复现步骤，以及你是否已经在本地确认。维护者确认后会回复。

## 仓库里的约定

- API 密钥只放在环境变量或仓库根目录被 git 忽略的 `.env`。
- 不要把 `openclaw-harness/events/events.jsonl` 提交进仓库。它是本机的追加日志。
- 生产节点未部署。不要在 Issue 里索要或张贴生产地址。
