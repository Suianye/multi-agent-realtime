# 多AI工具实时协作系统 - 实现计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 创建一个实时多AI工具协作系统，让Claude Code、Codex、OpenClaw、Hermes Agent真正协作执行任务，并通过Web界面实时可视化。

**Architecture:** 
- 后端：Python + asyncio + WebSocket，负责调用各AI工具CLI并实时推送状态
- 前端：纯HTML/CSS/JS，通过WebSocket接收实时数据并渲染
- 通信：WebSocket双向通信，JSON消息格式

**Tech Stack:** Python 3.11+, asyncio, subprocess, websockets, HTML5, CSS3, JavaScript

---

## 已确认的CLI调用方式

| 工具 | 非交互式调用 | 备注 |
|------|-------------|------|
| Claude Code | `claude -p "prompt"` | `-p` 参数非交互模式 |
| Codex | `codex exec "prompt"` | `exec` 子命令 |
| OpenClaw | `openclaw agent -m "prompt" --json` | `agent` 子命令 + `--json` 输出 |
| Hermes | 通过 `delegate_task` 工具调用 | 内置工具 |

---

## Task 1: 创建后端服务器 (server.py)

**Objective:** 创建WebSocket服务器，处理前端连接和任务分发

**Files:**
- Create: `C:/Users/MECHREVO/multi-agent-realtime/backend/server.py`

**功能:**
1. WebSocket服务器监听端口8765
2. 接收前端连接，维护客户端列表
3. 接收任务请求，分发给代理管理器
4. 实时广播代理状态和日志

---

## Task 2: 创建代理管理器 (agents.py)

**Objective:** 封装4个AI工具的CLI调用

**Files:**
- Create: `C:/Users/MECHREVO/multi-agent-realtime/backend/agents.py`

**功能:**
1. 定义统一的Agent接口
2. 实现ClaudeCodeAgent, CodexAgent, OpenClawAgent, HermesAgent
3. 异步调用CLI，捕获输出
4. 返回结构化结果

---

## Task 3: 创建任务调度器 (dispatcher.py)

**Objective:** 根据任务类型选择最佳代理

**Files:**
- Create: `C:/Users/MECHREVO/multi-agent-realtime/backend/dispatcher.py`

**功能:**
1. 分析任务类型（代码生成、优化、审查、调试）
2. 根据代理能力选择最佳执行者
3. 支持串行、并行、竞争三种模式

---

## Task 4: 创建前端界面 (index.html)

**Objective:** 实时可视化界面

**Files:**
- Create: `C:/Users/MECHREVO/multi-agent-realtime/frontend/index.html`

**功能:**
1. WebSocket连接后端
2. 代理状态卡片（实时更新）
3. 任务队列展示
4. 通信日志面板
5. 任务输入和控制按钮

---

## Task 5: 集成测试

**Objective:** 端到端测试

**验证步骤:**
1. 启动后端服务器
2. 打开前端界面
3. 输入测试任务
4. 观察代理执行和实时更新

---

## 消息协议

### 前端 → 后端
```json
{
  "type": "execute_task",
  "task": {
    "name": "任务名称",
    "prompt": "任务内容",
    "mode": "auto|serial|parallel|compete"
  }
}
```

### 后端 → 前端
```json
{
  "type": "agent_status",
  "agent": "claude-code",
  "status": "working|idle|error",
  "task": "当前任务"
}
```

```json
{
  "type": "log",
  "source": "协调器",
  "target": "claude-code",
  "message": "分配任务: xxx"
}
```

```json
{
  "type": "task_result",
  "agent": "claude-code",
  "result": "执行结果",
  "duration": 3.5
}
```
