"""任务调度器 - 根据任务类型选择最佳代理"""
import re
from typing import List

# 代理能力映射
AGENT_CAPABILITIES = {
    "claude-code": ["code-generation", "debugging", "documentation", "general"],
    "codex": ["code-generation", "optimization", "refactoring"],
    "openclaw": ["code-review", "analysis", "general"],
    "hermes": ["coordination", "planning", "general"],
}

def analyze_task(prompt: str) -> str:
    """分析任务类型"""
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["审查", "review", "检查", "check"]):
        return "code-review"
    elif any(w in prompt_lower for w in ["优化", "optimize", "性能", "performance"]):
        return "optimization"
    elif any(w in prompt_lower for w in ["重构", "refactor"]):
        return "refactoring"
    elif any(w in prompt_lower for w in ["调试", "debug", "bug", "错误"]):
        return "debugging"
    elif any(w in prompt_lower for w in ["文档", "document", "readme"]):
        return "documentation"
    elif any(w in prompt_lower for w in ["写", "创建", "实现", "build", "create", "implement"]):
        return "code-generation"
    else:
        return "general"

def select_agent(prompt: str, agents: dict, mode: str = "auto") -> List[str]:
    """根据模式选择代理"""
    if mode == "parallel":
        return list(agents.keys())
    elif mode == "compete":
        return list(agents.keys())
    elif mode == "serial":
        task_type = analyze_task(prompt)
        best = []
        for agent_id, caps in AGENT_CAPABILITIES.items():
            if task_type in caps or "general" in caps:
                best.append(agent_id)
        return best if best else ["claude-code"]
    else:  # auto
        task_type = analyze_task(prompt)
        best_agent = None
        best_score = -1
        for agent_id, caps in AGENT_CAPABILITIES.items():
            score = 0
            if task_type in caps:
                score = 10
            if "general" in caps:
                score += 1
            if score > best_score:
                best_score = score
                best_agent = agent_id
        return [best_agent or "claude-code"]
