"""工具执行层单元测试"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.tools import ToolExecutor


def test_list_files():
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "a.py").write_text("hello")
        (work / "b.py").write_text("world")
        (work / ".hidden").write_text("x")

        executor = ToolExecutor(work)
        result = executor.execute("list_files", {})

        assert result["success"]
        assert set(result["files"]) == {"a.py", "b.py"}
        assert len(executor.call_log) == 1


def test_read_file():
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "test.txt").write_text("hello world")

        executor = ToolExecutor(work)
        result = executor.execute("read_file", {"path": "test.txt"})

        assert result["success"]
        assert result["content"] == "hello world"


def test_read_file_not_found():
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        executor = ToolExecutor(work)
        result = executor.execute("read_file", {"path": "nope.txt"})

        assert not result["success"]
        assert "not found" in result["error"]


def test_write_file():
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        executor = ToolExecutor(work)
        executor.execute("write_file", {"path": "new.py", "content": "x=1"})

        assert (work / "new.py").read_text() == "x=1"


def test_edit_file_unique_match():
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "f.py").write_text("hello world\nline two\n")

        executor = ToolExecutor(work)
        result = executor.execute("edit_file", {
            "path": "f.py",
            "old_text": "hello world",
            "new_text": "hi there",
        })

        assert result["success"]
        assert "hi there" in (work / "f.py").read_text()


def test_edit_file_multiple_matches():
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "f.py").write_text("dup\ndup\ndup\n")

        executor = ToolExecutor(work)
        result = executor.execute("edit_file", {
            "path": "f.py",
            "old_text": "dup",
            "new_text": "fixed",
        })

        assert not result["success"]
        assert "matched 3 times" in result["error"]


def test_bash_echo():
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        executor = ToolExecutor(work)
        result = executor.execute("bash", {"command": "echo hello"})

        assert result["success"]
        assert "hello" in result["stdout"]
        assert result["exit_code"] == 0


def test_bash_dangerous_blocked():
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        executor = ToolExecutor(work)
        result = executor.execute("bash", {"command": "cat /etc/passwd"})

        assert not result["success"]
        assert "Dangerous" in result["error"]


def test_tool_definitions():
    executor = ToolExecutor(Path("."))
    tools = executor.tool_definitions()
    names = [t["function"]["name"] for t in tools]
    assert "read_file" in names
    assert "edit_file" in names
    assert "bash" in names
    assert "task_complete" in names
