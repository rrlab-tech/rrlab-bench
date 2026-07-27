"""
Agent 循环 — 多轮工具调用驱动的 Agent 执行引擎

使用 OpenAI function calling 协议，支持 DeepSeek、Kimi、OpenRouter 等。
"""

import json
import ssl
import time
import urllib.request
import urllib.error
from pathlib import Path

from .tools import ToolExecutor


def run_agent_loop(
    model: str,
    api_key: str,
    base_url: str,
    executor: ToolExecutor,
    task_prompt: str,
    max_turns: int = 20,
    temperature: float = 0.7,
    timeout: int = 300,
) -> dict:
    """
    多轮 Agent 循环

    返回:
        {
          "completed": bool,
          "turns": int,
          "tool_calls": list[dict],
          "final_message": str,
          "error": str | None,
          "elapsed": float,
          "prompt_tokens": int,
          "completion_tokens": int,
          "total_tokens": int,
        }
    """

    def _with_token_return(**kw):
        """构造统一的返回结构"""
        base = {
            "completed": False,
            "turns": turns,
            "tool_calls": executor.call_log,
            "final_message": "",
            "error": None,
            "elapsed": time.time() - start_time,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
        }
        base.update(kw)
        return base

    tools = executor.tool_definitions()

    system_prompt = (
        "You are a coding agent working in a project directory. "
        "Use the provided tools to explore, modify, and verify code. "
        "Work methodically: read files before editing them, verify changes after making them. "
        "Call task_complete ONLY when you are confident the task is fully done. "
        "If a tool returns an error, diagnose the problem — do NOT guess and retry blindly."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_prompt},
    ]

    completed = False
    turns = 0
    start_time = time.time()
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    while turns < max_turns and time.time() - start_time < timeout:
        turns += 1

        payload = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        # 所有模型统一 max thinking
        if "claude" in model.lower() or "opus" in model.lower():
            # Claude Opus 5 via OpenRouter 使用 reasoning 对象
            effort = "medium" if "opus-5" in model.lower() else "max"
            payload["reasoning"] = {"effort": effort}
        elif "minimax" in model.lower():
            payload["thinking"] = {"type": "adaptive"}
        elif "grok" in model.lower():
            payload["reasoning_effort"] = "high"
        else:
            payload["reasoning_effort"] = "max"
        if "kimi" in model.lower():
            payload["temperature"] = 1.0

        try:
            req = urllib.request.Request(
                f"{base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            return _with_token_return(error=f"HTTP {e.code}: {error_body[:500]}")
        except Exception as e:
            return _with_token_return(error=str(e))

        # 累积 token 用量
        usage = data.get("usage", {})
        total_prompt_tokens += usage.get("prompt_tokens", 0)
        total_completion_tokens += usage.get("completion_tokens", 0)
        total_tokens += usage.get("total_tokens", 0)

        choice = data["choices"][0]
        msg = choice["message"]
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            final = msg.get("content", "")
            return _with_token_return(completed=True, final_message=final)

        messages.append(msg)

        for tc in tool_calls:
            func = tc["function"]
            tool_name = func["name"]
            if tool_name == "task_complete":
                completed = True
            try:
                args = json.loads(func.get("arguments", "{}"))
            except (json.JSONDecodeError, TypeError):
                args = {}
            result = executor.execute(tool_name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })

        if completed:
            return _with_token_return(completed=True, final_message=msg.get("content", ""))

    return _with_token_return(final_message="max_turns reached")
