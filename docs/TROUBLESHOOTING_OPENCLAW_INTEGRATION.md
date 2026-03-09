# OpenClaw Gateway 集成故障排除指南

> 本文档记录了 Mission Control 与 OpenClaw Gateway 集成过程中遇到的问题及解决方案。
> 最后更新: 2026-03-09

---

## 目录

1. [Agent 显示 OFFLINE](#1-agent-显示-offline)
2. [任务分配通知失败 (Connection refused)](#2-任务分配通知失败-connection-refused)
3. [Agent API 端点错误](#3-agent-api-端点错误)
4. [Agent Token 认证失败](#4-agent-token-认证失败)
5. [Workspace 路径重复问题](#5-workspace-路径重复问题)
6. [配置参考](#配置参考)

---

## 1. Agent 显示 OFFLINE

### 症状
- Mission Control 前端显示 Agent 状态为 `offline`
- 数据库中 `last_seen_at` 时间过期

### 根本原因
Agent 的 heartbeat 请求未能成功发送到 Mission Control API。

**原因 A**: Gateway 的 `exec.security` 未配置，默认需要审批，导致 heartbeat curl 命令超时无人批准。

### 解决方案

在 Gateway 的 `/root/.openclaw/openclaw.json` 中配置：

```json
{
  "tools": {
    "exec": {
      "host": "gateway",
      "security": "full"
    }
  }
}
```

**原因 B**: Agent 的 HEARTBEAT.md 中使用了错误的 token。

检查数据库中的 `agent_token_hash` 是否与 HEARTBEAT.md 中的 token 匹配。如果不匹配，需要重新 provision agent 或更新 HEARTBEAT.md。

---

## 2. 任务分配通知失败 (Connection refused)

### 症状
- 后端日志显示 `[Errno 111] Connection refused`
- 任务分配成功但 Agent 未收到通知
- 活动日志中没有 `task.assignee_notified` 事件

### 根本原因
Mission Control 后端尝试通过 WebSocket 连接 Gateway 发送通知，但使用了 device pairing 模式，而后端无法完成设备配对流程。

### 解决方案

**步骤 1**: 在 Gateway 配置中启用 `dangerouslyDisableDeviceAuth`

```json
{
  "gateway": {
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789",
        "http://YOUR_SERVER_IP:18789"
      ],
      "dangerouslyDisableDeviceAuth": true
    }
  }
}
```

**步骤 2**: 在 Mission Control 数据库中配置 Gateway

```sql
UPDATE gateways
SET disable_device_pairing = true
WHERE id = 'YOUR_GATEWAY_ID';
```

**步骤 3**: 重启 Gateway 服务

```bash
systemctl --user restart openclaw-gateway
```

---

## 3. Agent API 端点错误

### 症状
- Agent 尝试更新任务时返回 `404 Not Found`
- 日志显示请求路径为 `/api/v1/agent/tasks/{task_id}`

### 根本原因
Agent 的 HEARTBEAT.md 中使用了错误的 API 端点格式。

### 解决方案

**错误格式**:
```
/api/v1/agent/tasks/{task_id}
```

**正确格式**:
```
/api/v1/agent/boards/{board_id}/tasks/{task_id}
```

更新 Agent 的 HEARTBEAT.md，确保包含正确的端点格式和示例。

---

## 4. Agent Token 认证失败

### 症状
- 后端日志显示 `agent auth invalid token`
- heartbeat 请求返回 `401 Unauthorized`

### 根本原因
HEARTBEAT.md 中的 token 与数据库中的 `agent_token_hash` 不匹配。

### 解决方案

**方法 A**: 重新 provision agent（推荐）

通过 Mission Control API 触发重新 provision：

```bash
curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/provision" \
  -H "Authorization: Bearer {user_token}"
```

**方法 B**: 手动更新 HEARTBEAT.md

1. 查看后端日志获取新 token（provision 时会输出）
2. 或通过 API 重新获取 token

---

## 5. Workspace 路径重复问题

### 症状
- Agent 读取文件时路径错误
- 路径出现重复，如 `/workspace/xxx/workspace/xxx/`

### 根本原因
Gateway 配置中 `agents.list[].workspace` 路径配置错误，导致路径重复。

### 解决方案

检查并修正 Gateway 配置：

```json
// 错误
{
  "workspace": "/root/.openclaw/workspace/workspace-xxx/workspace-xxx"
}

// 正确
{
  "workspace": "/root/.openclaw/workspace/workspace-xxx"
}
```

---

## 配置参考

### Gateway 完整配置示例

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789",
        "http://YOUR_SERVER_IP:18789"
      ],
      "dangerouslyDisableDeviceAuth": true
    },
    "auth": {
      "mode": "token",
      "token": "YOUR_GATEWAY_TOKEN"
    }
  },
  "tools": {
    "profile": "coding",
    "exec": {
      "host": "gateway",
      "security": "full"
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "your-provider/your-model"
      },
      "workspace": "/root/.openclaw/workspace"
    },
    "list": [
      {
        "id": "mc-gateway-YOUR_GATEWAY_ID",
        "name": "Main Gateway Agent",
        "workspace": "/root/.openclaw/workspace/workspace-gateway-YOUR_GATEWAY_ID",
        "heartbeat": {
          "every": "10m",
          "target": "last"
        }
      }
    ]
  }
}
```

### Agent HEARTBEAT.md 模板

```markdown
# HEARTBEAT.md

## Required inputs
- BASE_URL: `http://localhost:8000`
- AUTH_TOKEN: `YOUR_AGENT_TOKEN`
- AGENT_ID: `YOUR_AGENT_ID`

## API Endpoints

### Heartbeat
```bash
curl -s -X POST "http://localhost:8000/api/v1/agent/heartbeat" \
  -H "X-Agent-Token: YOUR_AGENT_TOKEN"
```

### Update Task (IMPORTANT: requires board_id)
```bash
# 正确格式: /api/v1/agent/boards/{board_id}/tasks/{task_id}
curl -s -X PATCH "http://localhost:8000/api/v1/agent/boards/{board_id}/tasks/{task_id}" \
  -H "X-Agent-Token: YOUR_AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress","comment":"Starting work"}'
```

**常见错误**: 使用 `/api/v1/agent/tasks/{task_id}` (缺少 board_id)
**正确格式**: `/api/v1/agent/boards/{board_id}/tasks/{task_id}`
```

### 关键 API 端点列表

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/v1/agent/heartbeat` | POST | Agent 心跳 |
| `/api/v1/agent/boards` | GET | 列出可见 Boards |
| `/api/v1/agent/boards/{board_id}/tasks` | GET | 获取任务列表 |
| `/api/v1/agent/boards/{board_id}/tasks/{task_id}` | PATCH | 更新任务 |
| `/api/v1/agent/boards/{board_id}/tasks/{task_id}/comments` | POST | 添加评论 |

---

## 调试命令

### 检查 Gateway 状态
```bash
openclaw gateway status
```

### 查看 Gateway 日志
```bash
tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

### 查看后端日志
```bash
docker compose -f /root/openclaw-mission-control/compose.yml logs -f backend
```

### 检查 Agent 状态
```bash
curl -s "http://localhost:8000/api/v1/agents/{agent_id}" \
  -H "Authorization: Bearer {user_token}" | jq '.'
```

### 检查任务活动日志
```bash
curl -s "http://localhost:8000/api/v1/activity?board_id={board_id}&limit=10" \
  -H "Authorization: Bearer {user_token}" | jq '.'
```

### 数据库查询
```bash
docker exec openclaw-mission-control-db-1 psql -U postgres -d mission_control -c \
  "SELECT id, name, status, last_seen_at FROM agents;"
```

---

## 常见错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| 401 | Unauthorized | 检查 X-Agent-Token 是否正确 |
| 404 | Not Found | 检查 API 端点格式，确保包含 board_id |
| 405 | Method Not Allowed | 检查 HTTP 方法是否正确 |
| 422 | Validation Error | 检查请求体格式 |

---

## 工作流验证清单

- [ ] Gateway 服务运行正常 (`openclaw gateway status`)
- [ ] Gateway RPC probe 正常
- [ ] Agent 配置中 `exec.security: "full"`
- [ ] Gateway 配置中 `dangerouslyDisableDeviceAuth: true`
- [ ] 数据库中 `disable_device_pairing: true`
- [ ] Agent HEARTBEAT.md 中 token 正确
- [ ] Agent HEARTBEAT.md 中 API 端点格式正确
- [ ] Agent workspace 路径无重复
