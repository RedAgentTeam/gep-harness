# GEP A2A Mock Peer — Non-Prod Deployment Guide

> ⚠️ **严禁部署到美机（<美机生产 IP>）**。SOUL 第 5 条铁律：美机任何写盘需先问"在哪台机器做"。

## 适用范围

- ✅ 本机（VM-0-11-ubuntu，dev node）
- ✅ 测试节点（任何非生产机器）
- ❌ 美机生产节点
- ❌ 任何 goapi / api.unvw.com 相关机器

## 安装步骤

### 1. 复制 systemd unit

```bash
sudo cp openclaw-a2a/systemd/gep-a2a-mock-peer.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 2. 启用 + 启动

```bash
sudo systemctl enable gep-a2a-mock-peer
sudo systemctl start gep-a2a-mock-peer
sudo systemctl status gep-a2a-mock-peer
```

### 3. 验证端口监听

```bash
ss -tlnp | grep 19880
# 应输出: LISTEN 0  5  0.0.0.0:19880  ...  users:(("python3",pid=...,fd=3))
```

### 4. 本机起 gene_sync 推 Gene

```bash
cd /data/disk/gep-harness
python3 openclaw-a2a/src/gene_sync.py \
  --peer=http://127.0.0.1:19880/a2a/receive \
  --pool-dir=/root/.openclaw/gene-pool \
  --min-gdi=0.7
```

期望输出：`sent=N accepted=N rejected=0`

## 端口选择规则

| 端口 | 状态 | 备注 |
|------|------|------|
| 19880 | 推荐（mock_peer 默认） | 本机默认安全 |
| 443 | ✅ 需 nginx 反代 | 生产推荐，但需要 nginx + SSL 配置 |
| 8080 | ✅ 已放行（多数云） | 跨公网可用 |
| 22 | ❌ SSH 占 | 不要用 |

## 防火墙注意事项

- 本机 localhost：默认通
- 跨节点：需要 cloud security group + iptables 双重放行
- 阿里云安全组：默认只放行 22/80/443/3000/8080，19880 需手动加

## 日志查看

```bash
# systemd journal
journalctl -u gep-a2a-mock-peer -f

# 启动 banner
journalctl -u gep-a2a-mock-peer | grep "listening"
```

## 停止 + 卸载

```bash
sudo systemctl stop gep-a2a-mock-peer
sudo systemctl disable gep-a2a-mock-peer
sudo rm /etc/systemd/system/gep-a2a-mock-peer.service
sudo systemctl daemon-reload
```

## pytest 等价验证

不需要 systemd 也能验证 A2A 协议本身：

```bash
cd /data/disk/gep-harness
python3 -m pytest openclaw-a2a/tests/test_mock_peer.py -v
# 期望: 3 passed
```

## 严禁事项

1. **不要在美机（<美机生产 IP>）部署** —— SOUL 第 5 条铁律
2. **不要绑 0.0.0.0 在公网无防火墙** —— 容易被打
3. **不要传 API key 到 peer URL** —— A2A 协议不用 key，用 signature
4. **不要让 mock_peer 持久化数据** —— 它只是回 ack，不存数据

## 相关文件

| 文件 | 用途 |
|------|------|
| `openclaw-a2a/src/mock_peer.py` | mock peer 实现 |
| `openclaw-a2a/src/gene_sync.py` | 同步引擎 |
| `openclaw-a2a/src/a2a_protocol.py` | 协议实现（envelope + signature） |
| `openclaw-a2a/tests/test_mock_peer.py` | 3 pytest tests |
| `openclaw-a2a/systemd/gep-a2a-mock-peer.service` | systemd unit |
