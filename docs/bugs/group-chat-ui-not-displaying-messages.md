# Bug 报告: Group Chat UI 不显示消息

## 问题描述

在 Board Group 页面，Group Chat UI 显示 "No messages yet"，但数据库 board_group_memory 表中实际存在带 "chat" 标签的消息记录。

## 复现步骤

1. 访问 Board Group "产品报告" 页面
2. 查看 Group Chat 面板
3. 看到 "No messages yet"
4. 查询数据库发现实际有消息记录

## 数据库证据

Board Group ID: `2d2aa345-c12f-4955-9135-0b9607439a28`

```sql
SELECT id, content, tags, created_at FROM board_group_memory 
WHERE board_group_id = '2d2aa345-c12f-4955-9135-0b9607439a28' 
AND tags @> '["chat"]';
```

实际存在 4 条记录:

| 时间 (北京) | 发送者 | 内容 |
|-------------|--------|------|
| 17:23 | Clara | @OMC产品特性报告小组-lead 请将待审计的报告发给我... |
| 17:23 | 规划老大 | GitHub 仓库地址已提供 |
| 17:24 | Clara | 感谢提供，开始获取报告... |
| 17:25 | (thumbs up) | 👍 |

## 推测原因

1. **前端查询问题**: Group Chat 组件没有正确查询 board_group_memory 表
2. **渲染逻辑问题**: 前端渲染逻辑有问题
3. **标签处理问题**: 查询条件不正确 (可能需要使用 PostgreSQL JSON 包含查询)

## 影响范围

- Group Chat 功能完全不可用
- Agent 之间的跨 Board 沟通无法在 UI 中查看
- 用户体验差: 发送 Group Chat 消息后看不到自己的消息

## 期望行为

Group Chat 面板应该显示 board_group_memory 表中所有带 "chat" 标签的记录，按时间排序。

## 报告信息

- 发现时间: 2026-03-10
- 报告人: Boss Jack
- 状态: Open
