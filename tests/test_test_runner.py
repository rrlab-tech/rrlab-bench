"""TestRunner 单元测试"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.test_runner import TestRunner, _is_code_broken, _parse_passed, _parse_failed


def test_parse_all_pass():
    """解析 pytest -v 全通过输出"""
    stdout = """
tests/test_a.py::test_one PASSED
tests/test_a.py::test_two PASSED
tests/test_b.py::test_three PASSED
============================== 3 passed in 0.01s ==============================
"""
    assert _parse_passed(stdout) == [
        "tests/test_a.py::test_one",
        "tests/test_a.py::test_two",
        "tests/test_b.py::test_three",
    ]
    assert _parse_failed(stdout) == []


def test_detect_broken_code():
    """检测代码崩溃"""
    stderr = "Traceback (most recent call last):\n  File \"...\", line 1, in <module>\nModuleNotFoundError: No module named 'src'"
    assert _is_code_broken(stderr)


def test_real_runner_pass():
    """真实运行器 — 全绿项目"""
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "tests").mkdir()
        (work / "tests" / "__init__.py").write_text("")
        (work / "tests" / "test_pass.py").write_text("def test_ok(): assert True")
        runner = TestRunner(work, "python3 -m pytest tests/ -v --tb=short 2>&1")
        r = runner.run()
        assert r["success"]
        assert r["total"] >= 1
        assert any("test_ok" in t for t in r["passed"])


def test_real_runner_fail():
    """真实运行器 — 有失败"""
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "tests").mkdir()
        (work / "tests" / "__init__.py").write_text("")
        (work / "tests" / "test_fail.py").write_text("def test_bad(): assert False")
        runner = TestRunner(work, "python3 -m pytest tests/ -v --tb=short 2>&1")
        r = runner.run()
        assert not r["success"]
        assert r["total"] >= 1
