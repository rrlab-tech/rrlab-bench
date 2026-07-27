"""
工具执行层 — 在沙箱内执行工具调用，记录所有操作

包含五个工具：list_files, read_file, write_file, edit_file, bash
"""

import shlex
import subprocess
import time
from pathlib import Path


class ToolExecutor:
    """在沙箱内执行工具调用，记录所有操作"""

    def __init__(self, work_dir: Path, bash_timeout: int = 10):
        self.work_dir = work_dir.resolve()
        self.bash_timeout = bash_timeout
        self.call_log: list[dict] = []

    # ── 公开接口 ──

    def execute(self, tool_name: str, args: dict) -> dict:
        """路由到具体工具，记录日志，返回结果"""
        method = getattr(self, f"_tool_{tool_name}", None)
        if method is None:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        timestamp = time.time()
        try:
            result = method(args)
        except Exception as e:
            result = {"success": False, "error": str(e)}

        self.call_log.append({
            "tool": tool_name,
            "args": args,
            "result": result,
            "timestamp": timestamp,
        })
        return result

    def tool_definitions(self) -> list[dict]:
        """返回 OpenAI function calling 格式的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List all files in the project directory",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the content of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path relative to project root",
                            },
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write or overwrite a file with new content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path relative to project root",
                            },
                            "content": {
                                "type": "string",
                                "description": "Full new content of the file",
                            },
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Replace a specific string in a file. If the old string appears multiple times, the operation will fail — use read_file to verify first.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path relative to project root",
                            },
                            "old_text": {
                                "type": "string",
                                "description": "Exact text to replace (must be unique in the file)",
                            },
                            "new_text": {
                                "type": "string",
                                "description": "Replacement text",
                            },
                        },
                        "required": ["path", "old_text", "new_text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Execute a shell command in the project directory. Use for running tests, installing dependencies, or file operations.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute",
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "task_complete",
                    "description": "Signal that the assigned task has been completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Brief description of what was done",
                            },
                        },
                        "required": ["summary"],
                    },
                },
            },
        ]

    # ── 内部工具实现 ──

    def _tool_list_files(self, _args: dict) -> dict:
        files = []
        for f in sorted(self.work_dir.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                rel = str(f.relative_to(self.work_dir))
                files.append(rel)
        return {"success": True, "files": files}

    def _tool_read_file(self, args: dict) -> dict:
        path = self.work_dir / args["path"]
        try:
            resolved = path.resolve()
            if not str(resolved).startswith(str(self.work_dir)):
                return {"success": False, "error": "Path escapes sandbox"}
            content = resolved.read_text(encoding="utf-8")
            return {"success": True, "content": content}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {args['path']}"}
        except IsADirectoryError:
            return {"success": False, "error": f"Is a directory: {args['path']}"}

    def _tool_write_file(self, args: dict) -> dict:
        path = self.work_dir / args["path"]
        resolved = path.resolve()
        if not str(resolved).startswith(str(self.work_dir)):
            return {"success": False, "error": "Path escapes sandbox"}
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(args["content"], encoding="utf-8")
        return {"success": True}

    def _tool_edit_file(self, args: dict) -> dict:
        path = self.work_dir / args["path"]
        old_text = args["old_text"]
        new_text = args["new_text"]

        resolved = path.resolve()
        if not str(resolved).startswith(str(self.work_dir)):
            return {"success": False, "error": "Path escapes sandbox"}

        try:
            content = resolved.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {args['path']}"}

        count = content.count(old_text)
        if count == 0:
            return {"success": False, "error": "old_text not found in file"}
        if count > 1:
            return {
                "success": False,
                "error": f"old_text matched {count} times — must be unique. Use read_file to verify.",
            }

        new_content = content.replace(old_text, new_text, 1)
        resolved.write_text(new_content, encoding="utf-8")
        return {"success": True}

    def _tool_bash(self, args: dict) -> dict:
        command = args["command"]

        # 安全检查：禁止明显的路径逃逸和破坏性操作
        dangerous = ["/etc/", "/System/", "/var/", "~", "$HOME", "$("]
        for d in dangerous:
            if d in command:
                return {"success": False, "error": f"Dangerous pattern detected: {d}"}

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.work_dir),
                timeout=self.bash_timeout,
            )
            return {
                "success": True,
                "stdout": proc.stdout[-2000:],
                "stderr": proc.stderr[-2000:],
                "exit_code": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {self.bash_timeout}s"}
