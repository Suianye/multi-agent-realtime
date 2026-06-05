# AI工作室 - 多代理协作系统

## 架构

```
用户需求 → Hermes(项目经理) 拆解任务
                ↓
    ┌──────────┼──────────┐
    ↓          ↓          ↓
Claude Code  Codex    OpenClaw
 (开发者)    (优化师)   (审查员)
    ↓          ↓          ↓
    └──────────┼──────────┘
               ↓
        审查循环 (不通过→修订→再审)
               ↓
           项目完成
```

## 角色分工

| 代理 | 角色 | 能力 |
|------|------|------|
| Hermes | 项目经理 | 需求分析、任务分解、团队协调 |
| Claude Code | 开发者 | 写代码、实现功能、调试 |
| Codex | 优化师 | 代码优化、重构、性能改进 |
| OpenClaw | 审查员 | 代码审查、质量检查、安全分析 |

## 协作流程

1. **需求分析** - Hermes 分析用户需求，拆解为子任务
2. **任务分配** - 根据代理能力分配子任务
3. **并行执行** - 无依赖的任务并行执行
4. **审查循环** - 代码类任务由 OpenClaw 审查
   - 通过 → 完成
   - 不通过 → 返回修改（最多2次）
5. **项目完成** - 所有子任务完成后汇报

## 消息协议 (WebSocket JSON)

### 前端 → 后端
- `start_project`: {name, requirement}
- `execute_task`: {prompt, mode} (兼容旧版)

### 后端 → 前端
- `agent_status`: 代理状态变化
- `log`: 实时日志
- `phase_change`: 阶段变化
- `task_breakdown`: 任务分解结果
- `task_status`: 子任务状态变化
- `task_result`: 任务执行结果
- `project_complete`: 项目完成

## 启动

```bash
cd ~/multi-agent-realtime
pip install websockets
python backend/server.py
# 浏览器打开 frontend/index.html
```
