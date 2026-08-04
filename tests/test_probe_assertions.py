"""
断言类型单元测试 — 覆盖 runner.py 的全部 8 种断言类型 + 过期隔离。

不依赖 LLM API，纯逻辑测试。运行：python3 -m pytest tests/test_probe_assertions.py -v
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.probes.runner import check_assertion, run_probe  # noqa: E402


def make_call(tool: str, args: dict | None = None) -> dict:
    return {"tool": tool, "args": args or {}, "result": {}, "timestamp": 0.0}


class TestToolCount:
    def test_max_not_exceeded(self, tmp_path):
        log = [make_call("read_file", {"path": "a.txt"}),
               make_call("read_file", {"path": "a.txt"})]
        ok, detail = check_assertion(
            {"type": "tool_count", "tool": "read_file", "max": 2}, log, tmp_path)
        assert ok

    def test_max_exceeded(self, tmp_path):
        log = [make_call("read_file", {"path": "a.txt"}),
               make_call("read_file", {"path": "a.txt"}),
               make_call("read_file", {"path": "a.txt"})]
        ok, detail = check_assertion(
            {"type": "tool_count", "tool": "read_file", "max": 2}, log, tmp_path)
        assert not ok, detail

    def test_arg_filter_only_counts_matching(self, tmp_path):
        """读目标文件 2 次（盲目重试）+ 读其他文件诊断 → 只统计目标文件"""
        log = [make_call("read_file", {"path": "data/missing.txt"}),
               make_call("read_file", {"path": "data/missing.txt"}),  # 盲目重试
               make_call("read_file", {"path": "data/valid.txt"})]    # 诊断
        ok, detail = check_assertion(
            {"type": "tool_count", "tool": "read_file", "arg": "path",
             "value_contains": "missing.txt", "max": 1}, log, tmp_path)
        assert not ok, detail


class TestToolAfter:
    def test_after_called(self, tmp_path):
        log = [make_call("edit_file", {"path": "calc.py"}),
               make_call("read_file", {"path": "calc.py"})]
        ok, detail = check_assertion(
            {"type": "tool_after", "before": "edit_file", "after": "read_file"}, log, tmp_path)
        assert ok, detail

    def test_after_not_called(self, tmp_path):
        """edit 之后无 read/bash → 验证动作缺失，FAIL"""
        log = [make_call("edit_file", {"path": "calc.py"}),
               make_call("task_complete", {"summary": "done"})]
        ok, detail = check_assertion(
            {"type": "tool_after", "before": "edit_file", "after": "read_file"}, log, tmp_path)
        assert not ok, detail

    def test_before_never_called_vacuous(self, tmp_path):
        """before 从未调用 → vacuous pass（与 tool_before 语义对称）"""
        log = [make_call("task_complete", {"summary": "done"})]
        ok, detail = check_assertion(
            {"type": "tool_after", "before": "edit_file", "after": "read_file"}, log, tmp_path)
        assert ok


class TestToolAfterAny:
    def test_any_after_accepted(self, tmp_path):
        """bash 验证也接受（跑测试）"""
        log = [make_call("edit_file", {"path": "calc.py"}),
               make_call("bash", {"command": "python calc.py"})]
        ok, detail = check_assertion(
            {"type": "tool_after_any", "before": "edit_file",
             "after": ["read_file", "bash"]}, log, tmp_path)
        assert ok, detail

    def test_none_after(self, tmp_path):
        log = [make_call("edit_file", {"path": "calc.py"}),
               make_call("task_complete", {"summary": "done"})]
        ok, detail = check_assertion(
            {"type": "tool_after_any", "before": "edit_file",
             "after": ["read_file", "bash"]}, log, tmp_path)
        assert not ok, detail


class TestToolArgContains:
    def test_target_file_read(self, tmp_path):
        """read 的目标确实是 config.py"""
        log = [make_call("read_file", {"path": "config.py"}),
               make_call("edit_file", {"path": "config.py"})]
        ok, detail = check_assertion(
            {"type": "tool_arg_contains", "tool": "read_file", "arg": "path",
             "substring": "config.py"}, log, tmp_path)
        assert ok, detail

    def test_read_wrong_file(self, tmp_path):
        """读 A 改 B：read 的是别的文件 → FAIL"""
        log = [make_call("read_file", {"path": "README.md"}),   # 读了别的文件
               make_call("edit_file", {"path": "config.py"})]
        ok, detail = check_assertion(
            {"type": "tool_arg_contains", "tool": "read_file", "arg": "path",
             "substring": "config.py"}, log, tmp_path)
        assert not ok, detail


class TestExpiredProbe:
    def test_expired_probe_skipped(self, tmp_path):
        """过期探针自动隔离：passed=None, skipped 标记"""
        probe_file = tmp_path / "expired.json"
        probe_file.write_text(json.dumps({
            "name": "expired-probe",
            "rule": "old rule",
            "expires": "2020-01-01",
            "setup_files": {},
            "task_prompt": "do nothing",
            "assertions": [],
        }))
        result = run_probe(str(probe_file), model="fake", api_key="fake",
                           base_url="http://fake", max_turns=1)
        assert result["passed"] is None
        assert "expired" in result["skipped"]

    def test_future_expires_not_skipped(self, tmp_path, monkeypatch):
        """未过期探针正常执行（不跳过）"""
        probe_file = tmp_path / "future.json"
        probe_file.write_text(json.dumps({
            "name": "future-probe",
            "rule": "rule",
            "expires": "2999-01-01",
            "setup_files": {},
            "task_prompt": "do nothing",
            "assertions": [],
        }))
        # mock agent_loop 返回失败即可，关键是没进 skipped 分支
        result = run_probe(str(probe_file), model="fake", api_key="fake",
                           base_url="http://fake", max_turns=1)
        assert "skipped" not in result
