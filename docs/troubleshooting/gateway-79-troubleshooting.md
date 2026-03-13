# OpenClaw Mission Control - Gateway Troubleshooting Guide

## Gateway: 电商AI Gateway (.79)
- **Server IP**: 216.116.160.79
- **Gateway ID**: acd4001c-a911-4ec0-9f49-57d7f57a0fb7
- **Agent ID**: 2dde96be-1294-445e-bb70-663f6914f4c9
- **Gateway URL**: wss://gw-79-ec.imlogo.net:443
- **Gateway Token**: eed33f14de30bffdf188302021d697e9835cf46ec0d23a76

---

## 🔴 已解决: SIGTERM 信号导致 Gateway 重启

### 问题症状
- Gateway 进程每 6-60 秒收到 SIGTERM 信号并重启
- Caddy 返回 HTTP 502 错误
- Agent 状态显示 `provision_failed` 或 `provision_timeout`

### 根本原因
**QEMU Guest Agent** (`qemu-guest-agent.service`) 在发送 SIGTERM 信号

### 解决方案
```bash
# 在 gateway 服务器 (.79) 上执行
systemctl stop qemu-guest-agent
systemctl disable qemu-guest-agent
systemctl mask qemu-guest-agent
```

### 验证修复
```bash
# 检查 gateway 运行时间
ps -o etime= -p $(pgrep -f 'node.*gateway')

# 检查端口监听
netstat -tlnp | grep 18789

# 检查 MC 连接
curl -s "https://omc.imlogo.net/api/v1/gateways/status?gateway_url=wss://gw-79-ec.imlogo.net:443&gateway_token=TOKEN" -H "Authorization: Bearer AUTH_TOKEN" | jq '.'
```

---

## 配置文件

### Systemd Service (.79)
**File**: `/root/.config/systemd/user/openclaw-gateway.service`
- Restart: `on-failure`
- SuccessExitStatus: `0 143`

### OpenClaw Config (.79)
**File**: `/root/.openclaw/openclaw.json`
- `commands.restart`: `false` (已禁用内部重启)

### Caddy Config (.79)
**File**: `/etc/caddy/Caddyfile`
- Reverse proxy to localhost:18789

---

## 设备配对

### 手动配对步骤
```bash
# 检查待配对设备
cat /root/.openclaw/devices/pending.json | jq '.'

# 批准设备
pending=$(cat /root/.openclaw/devices/pending.json)
device_id=$(echo $pending | jq -r '.[].deviceId')
device=$(echo $pending | jq '.[]')
cat /root/.openclaw/devices/paired.json | jq --argjson dev "$device" --arg id "$device_id" '. + {($id): $dev}' > /tmp/paired.json
mv /tmp/paired.json /root/.openclaw/devices/paired.json
echo '{}' > /root/.openclaw/devices/pending.json
```

---

## Agent 状态管理

### 手动更新 Agent 状态
```bash
# 在 MC 服务器 (.78) 上执行
docker exec openclaw-mission-control-db-1 psql -U postgres -d mission_control -c \
  "UPDATE agents SET status = 'online', updated_at = NOW() WHERE id = '2dde96be-1294-445e-bb70-663f6914f4c9';"
```

---

## 故障排除命令

```bash
# 检查 gateway 日志
tail -f /tmp/openclaw/openclaw-2026-03-13.log | grep -a SIGTERM

# 检查 systemd 状态
systemctl --user status openclaw-gateway

# 重启 gateway
systemctl --user restart openclaw-gateway

# 检查监听端口
netstat -tlnp | grep 18789

# 检查 QEMU Guest Agent 状态
systemctl status qemu-guest-agent
```

---

## 调查历史

### 已排除的原因
- ❌ Systemd 重启策略 (NRestarts=0)
- ❌ Cron 作业
- ❌ 监控服务 (monit, supervisor, pm2)
- ❌ OOM Killer
- ❌ 内核 watchdog
- ❌ Avahi/mDNS 冲突
- ❌ OpenClaw 内部重启机制

### 确认的根本原因
- ✅ **QEMU Guest Agent** - 发送 SIGTERM 信号
  - QEMU Guest Agent 是云服务商用于 VM 管理的工具
  - 它可能定期发送信号来检查或管理进程
  - 禁用后 Gateway 稳定运行

---

## 相关链接
- GitHub: https://github.com/logorun/openclaw-mission-control
- MC Dashboard: https://omc.imlogo.net
- Gateway URL: wss://gw-79-ec.imlogo.net:443
