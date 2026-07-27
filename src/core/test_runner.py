"""
测试运行器 — 在沙箱内执行 pytest 并解析结果

解析 pytest 的 -v 输出格式，返回结构化的测试结果。
"""

import re
import subprocess
from pathlib import Path


class TestRunner:
    """在沙箱内运行测试套件，解析结果"""

    def __init__(self, work_dir: Path, test_command: str, timeout: int = 60):
        self.work_dir = work_dir
        self.test_command = test_command
        self.timeout = timeout

    def run(self) -> dict:
        """
        执行测试命令，解析输出

        返回:
          {
            "success": bool,           # 测试命令本身是否成功执行（exit_code=0）
            "total": int,
            "passed": list[str],
            "failed": list[str],
            "errors": list[str],       # 收集阶段或执行阶段的错误
            "raw_output": str,
            "exit_code": int,
          }
        """

        try:
            proc = subprocess.run(
                self.test_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.work_dir),
                timeout=self.timeout,
            )
            stdout = proc.stdout
            stderr = proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "total": 0,
                "passed": [],
                "failed": [],
                "errors": ["test command timed out"],
                "raw_output": "",
                "exit_code": -1,
            }

        raw_output = stdout + "\n" + stderr

        # 检查是否是「代码根本跑不起来」
        if _is_code_broken(stderr):
            return {
                "success": False,
                "total": 0,
                "passed": [],
                "failed": [],
                "errors": ["code cannot run: " + _extract_import_error(stderr)],
                "raw_output": raw_output[:2000],
                "exit_code": exit_code,
            }

        # 解析 pytest 的 -v 输出
        passed = _parse_passed(stdout)
        failed = _parse_failed(stdout)
        errors = _parse_errors(stdout, stderr)

        return {
            "success": exit_code == 0 and len(failed) == 0 and len(errors) == 0,
            "total": len(passed) + len(failed) + len(errors),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "raw_output": raw_output[:2000],
            "exit_code": exit_code,
        }


def _is_code_broken(stderr: str) -> bool:
    """检测是否是代码无法运行（而非测试失败）"""
    patterns = [
        "ImportError", "ModuleNotFoundError", "SyntaxError",
        "IndentationError", "NameError", "AttributeError",
    ]
    return any(p in stderr for p in patterns)


def _extract_import_error(stderr: str) -> str:
    """提取 import 错误信息"""
    for line in stderr.splitlines():
        for pattern in ["ImportError", "ModuleNotFoundError", "SyntaxError"]:
            if pattern in line:
                return line.strip()[:120]
    return stderr.strip()[:120]


def _parse_passed(stdout: str) -> list[str]:
    """解析 PASSED 测试名"""
    tests = []
    for line in stdout.splitlines():
        if "PASSED" in line:
            match = re.search(r'(\S+::\S+)', line)
            if match:
                tests.append(match.group(1))
    return tests


def _parse_failed(stdout: str) -> list[str]:
    """解析 FAILED 测试名"""
    tests = []
    for line in stdout.splitlines():
        if "FAILED" in line:
            match = re.search(r'(\S+::\S+)', line)
            if match:
                tests.append(match.group(1))
    return tests


def _parse_errors(stdout: str, stderr: str) -> list[str]:
    """解析 ERROR 测试名"""
    tests = []
    for source in [stdout, stderr]:
        for line in source.splitlines():
            if "ERROR" in line and "ERRORS" not in line:
                match = re.search(r'(\S+::\S+)', line)
                if match:
                    tests.append(match.group(1))
    return tests
