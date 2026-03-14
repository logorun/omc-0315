# 故障排除记录: Gateway trustedProxies 配置缺失

**日期**: 2026-03-15
**服务器**: 216.116.160.79 (ecs95033)
**严重程度**: P1 - 服务不可用
**状态**: 已解决

## 问题概述

79 gateway (gw-79-ec.imlogo.net) 的 WebSocket 连接失败，导致:
- Mission Control 无法通过 RPC 调用远程 gateway
- Agent 创建/管理操作超时
- Webhook worker 报错 `gateway.rpc.call.gateway_error`

## 症状

### 1. Webhook Worker 日志
```
WARNING app.services.openclaw.gateway_rpc gateway.rpc.call.gateway_error method=agents.create duration_ms=40
WARNING app.services.openclaw.lifecycle_reconcile lifecycle.reconcile.max_attempts_reached wake_attempts=3
```

### 2. Gateway 日志 (关键)
```
{"subsystem":"gateway/ws"} Proxy headers detected from untrusted address. 
Connection will not be treated as local. 
Configure gateway.trustedProxies to restore local client detection behind your proxy.
```

### 3. WebSocket 连接测试
```bash
# 返回 200 而不是 101 (WebSocket 升级)
curl -sk -H 'Connection: Upgrade' -H 'Upgrade: websocket' https://gw-79-ec.imlogo.net/
# 返回 HTML 内容而不是 WebSocket 升级响应
```

## 根本原因

### 1. Gateway 服务未运行
用户级 systemd 服务 `openclaw-gateway.service` 处于停止状态。

### 2. 缺少 trustedProxies 配置
Gateway 配置文件 `/root/.openclaw/openclaw.json` 中没有 `trustedProxies` 设置。

当 Gateway 运行在反向代理 (Caddy) 后面时，WebSocket 连接来自代理的 IP (127.0.0.1)，
而不是原始客户端 IP。Gateway 默认不信任来自非回环地址的代理头信息。

## 解决方案

### 步骤 1: 启动 Gateway 服务
```bash
# 检查服务状态
systemctl --user status openclaw-gateway

# 启动服务
systemctl --user start openclaw-gateway

# 确保开机自启
systemctl --user enable openclaw-gateway
```

### 步骤 2: 添加 trustedProxies 配置
```bash
# 备份配置
cp /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.bak.$(date +%s)

# 添加 trustedProxies (使用 jq)
jq '.gateway.trustedProxies = ["127.0.0.1", "::1"]' /root/.openclaw/openclaw.json > /tmp/openclaw.json.new
mv /tmp/openclaw.json.new /root/.openclaw/openclaw.json

# 重启服务使配置生效
systemctl --user restart openclaw-gateway
```

### 步骤 3: 验证修复
```bash
# 检查 gateway 健康状态
curl -sk https://gw-79-ec.imlogo.net/health
# 期望输出: {"ok":true,"status":"live"}

# 检查日志中不再有 proxy 警告
tail -50 /tmp/openclaw/openclaw-*.log | grep -i proxy
```

## 配置参考

### 完整的 gateway.trustedProxies 配置
```json
{
  "gateway": {
    "trustedProxies": [
      "127.0.0.1",
      "::1"
    ]
  }
}
```

### Caddy 配置 (79 服务器)
```caddyfile
# /etc/caddy/Caddyfile
gw-79-ec.imlogo.net {
    reverse_proxy localhost:18789
}
```

### Systemd 服务配置
```ini
# /root/.config/systemd/user/openclaw-gateway.service
[Unit]
Description=OpenClaw Gateway (v2026.3.11)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/node /usr/lib/node_modules/openclaw/dist/index.js gateway --port 18789 --allow-unconfigured
Restart=always
RestartSec=10
```

## 验证清单

- [ ] Gateway 服务运行中: `systemctl --user status openclaw-gateway`
- [ ] 端口监听: `ss -tlnp | grep 18789`
- [ ] 健康检查通过: `curl https://gw-79-ec.imlogo.net/health`
- [ ] Mission Control 显示 Gateway Online
- [ ] Agents 状态为 online
- [ ] 日志无 proxy 警告

## 相关文档

- `/root/openclaw-mission-control/docs/troubleshooting/gateway-79-troubleshooting.md`
- `/root/openclaw-mission-control/docs/troubleshooting/gateway-connection.md`
- `/root/omc-analysis/docs/gateway-mc-troubleshooting.md` (79 服务器本地)

## 关键学习

1. **反向代理后的 Gateway 必须配置 trustedProxies**
   - Caddy/Nginx 代理 WebSocket 时，源 IP 变为 127.0.0.1
   - Gateway 需要知道哪些代理是可信的

2. **用户级 systemd 服务**
   - 使用 `systemctl --user` 而非 `systemctl`
   - 需要 `loginctl enable-linger` 确保用户登出后服务继续运行

3. **故障排除顺序**
   1. 检查服务状态
   2. 检查端口监听
   3. 检查反向代理配置
   4. 检查 gateway 日志 (特别是 proxy 相关警告)

## SSH 访问信息

| 服务器 | SSH 别名 | 端口 | 用户 |
|--------|----------|------|------|
| 78 (Mission Control) | `ssh ecs` | 30022 | root |
| 79 (Gateway) | `ssh ecs95033` | 30022 | root |

## 快速恢复命令

```bash
# 在 79 服务器上快速恢复 gateway
ssh ecs95033 '
  systemctl --user start openclaw-gateway
  jq -e ".gateway.trustedProxies" /root/.openclaw/openclaw.json >/dev/null 2>&1 || \
    jq ".gateway.trustedProxies = [\"127.0.0.1\", \"::1\"]" /root/.openclaw/openclaw.json > /tmp/oc.json && \
    mv /tmp/oc.json /root/.openclaw/openclaw.json && \
    systemctl --user restart openclaw-gateway
  curl -s http://localhost:18789/health
'
```
