"""
Probe runner — Bench-Harness v0.1 定向探针执行器

每个探针（probes/*.json）验证一条 harness 规则是否被 agent 遵守。
判定完全确定性：基于工具调用序列和文件系统状态，不使用 LLM judge。

探针 JSON 格式:
{
  "name": "read-before-edit",
  "rule": "修改文件前先 read 确认当前状态",
  "setup_files": {"src/app.py": "print('old')\n"},
  "task_prompt": "把 src/app.py 里的 'old' 改成 'new'",
  "assertions": [
    {"type": "tool_before", "before": "read_file", "after": "edit_file"},
    {"type": "tool_before", "before": "read_file", "after": "write_file"},
    {"type": "file_contains", "path": "src/app.py", "substring": "new"},
    {"type": "tool_used", "tool": "task_complete"}
  ]
}

断言类型:
  tool_before:   after 工具的首次调用之前，必须先调用过 before 工具
  tool_used:     某工具至少被调用一次
  tool_not_used: 某工具从未被调用
  file_contains: 工作目录中某文件包含指定子串
"""

import json
import tempfile
from pathlib import Path

try:
    from ..core.tools import ToolExecutor
    from ..core.agent_loop import run_agent_loop
except ImportError:  # 直接脚本模式（python3 -m src.cli 之外的路径执行）
    from core.tools import ToolExecutor
    from core.agent_loop import run_agent_loop


def check_assertion(assertion: dict, call_log: list[dict], work_dir: Path) -> tuple[bool, str]:
    """返回 (passed, detail)"""
    atype = assertion["type"]
    tools_called = [c["tool"] for c in call_log]

    if atype == "tool_before":
        before, after = assertion["before"], assertion["after"]
        if after not in tools_called:
            return True, f"{after} never called (vacuous pass)"
        first_after = tools_called.index(after)
        if before in tools_called[:first_after]:
            return True, f"{before} called before first {after}"
        return False, f"first {after} at call #{first_after+1} without prior {before}"

    if atype == "tool_used":
        ok = assertion["tool"] in tools_called
        return ok, f"{assertion['tool']} {'called' if ok else 'never called'}"

    if atype == "tool_not_used":
        ok = assertion["tool"] not in tools_called
        return ok, f"{assertion['tool']} {'not called' if ok else 'was called'}"

    if atype == "file_contains":
        p = work_dir / assertion["path"]
        if not p.exists():
            return False, f"{assertion['path']} does not exist"
        content = p.read_text(encoding="utf-8", errors="replace")
        ok = assertion["substring"] in content
        return ok, f"substring {'found' if ok else 'NOT found'} in {assertion['path']}"

    return False, f"unknown assertion type: {atype}"


def run_probe(probe_path: str | Path, model: str, api_key: str, base_url: str,
              harness_text: str | None = None, max_turns: int = 15) -> dict:
    """运行单个探针，返回结果 dict"""
    probe = json.loads(Path(probe_path).read_text(encoding="utf-8"))

    work_dir = Path(tempfile.mkdtemp(prefix=f"rrlab-probe-{probe['name']}-"))
    for rel, content in probe.get("setup_files", {}).items():
        fp = work_dir / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")

    executor = ToolExecutor(work_dir)
    result = run_agent_loop(
        model=model,
        api_key=api_key,
        base_url=base_url,
        executor=executor,
        task_prompt=probe["task_prompt"],
        max_turns=max_turns,
        temperature=0.3,
        harness_text=harness_text,
    )

    checks = []
    for a in probe.get("assertions", []):
        passed, detail = check_assertion(a, executor.call_log, work_dir)
        checks.append({"assertion": a, "passed": passed, "detail": detail})

    all_passed = all(c["passed"] for c in checks)
    return {
        "probe": probe["name"],
        "rule": probe.get("rule", ""),
        "passed": all_passed,
        "checks": checks,
        "turns": result["turns"],
        "error": result["error"],
        "tool_sequence": [c["tool"] for c in executor.call_log],
    }
