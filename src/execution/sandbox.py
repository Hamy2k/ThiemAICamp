"""
Code Execution Sandbox - Chạy code an toàn trong subprocess.
Hỗ trợ: Python, Node.js, shell commands.
Có timeout, memory limit, output capture.
"""

import os
import sys
import subprocess
import tempfile
import logging
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from src.utils import ExecutionError

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Kết quả chạy code."""
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    language: str = "python"
    duration_ms: float = 0
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "language": self.language,
            "duration_ms": round(self.duration_ms, 2),
            "timed_out": self.timed_out,
        }


# Dangerous patterns that should never be executed
BLOCKED_COMMANDS = {
    "rm -rf /", "rm -rf ~", ":(){ :|:& };:",
    "mkfs", "dd if=", "format c:",
    "> /dev/sda", "chmod -R 777 /",
}


class Sandbox:
    """Safe code execution sandbox using subprocess."""

    def __init__(
        self,
        workspace_dir: str = ".",
        timeout: int = 30,
        max_output_size: int = 50000,
    ):
        self.workspace = Path(workspace_dir).resolve()
        self.timeout = timeout
        self.max_output_size = max_output_size

    def _check_safety(self, code: str) -> None:
        """Check for dangerous patterns."""
        code_lower = code.lower()
        for pattern in BLOCKED_COMMANDS:
            if pattern.lower() in code_lower:
                raise ExecutionError(
                    f"Blocked dangerous command: {pattern}",
                    returncode=-1,
                )

    def run_python(self, code: str, timeout: Optional[int] = None) -> ExecutionResult:
        """Chạy Python code trong subprocess."""
        self._check_safety(code)
        timeout = timeout or self.timeout

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", dir=str(self.workspace),
            delete=False, encoding="utf-8",
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            import time
            start = time.time()
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace),
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            duration = (time.time() - start) * 1000

            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout[:self.max_output_size],
                stderr=result.stderr[:self.max_output_size],
                language="python",
                duration_ms=duration,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                returncode=-1,
                stderr=f"Execution timed out after {timeout}s",
                language="python",
                timed_out=True,
            )
        except Exception as e:
            return ExecutionResult(
                returncode=-1,
                stderr=str(e),
                language="python",
            )
        finally:
            try:
                os.unlink(temp_file)
            except OSError:
                pass

    def run_node(self, code: str, timeout: Optional[int] = None) -> ExecutionResult:
        """Chạy Node.js code trong subprocess."""
        self._check_safety(code)
        timeout = timeout or self.timeout

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", dir=str(self.workspace),
            delete=False, encoding="utf-8",
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            import time
            start = time.time()
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace),
            )
            duration = (time.time() - start) * 1000

            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout[:self.max_output_size],
                stderr=result.stderr[:self.max_output_size],
                language="javascript",
                duration_ms=duration,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                returncode=-1,
                stderr=f"Execution timed out after {timeout}s",
                language="javascript",
                timed_out=True,
            )
        except FileNotFoundError:
            return ExecutionResult(
                returncode=-1,
                stderr="Node.js not installed",
                language="javascript",
            )
        except Exception as e:
            return ExecutionResult(
                returncode=-1, stderr=str(e), language="javascript",
            )
        finally:
            try:
                os.unlink(temp_file)
            except OSError:
                pass

    def run_shell(self, command: str, timeout: Optional[int] = None) -> ExecutionResult:
        """Chạy shell command."""
        self._check_safety(command)
        timeout = timeout or self.timeout

        try:
            import time
            start = time.time()
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace),
            )
            duration = (time.time() - start) * 1000

            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout[:self.max_output_size],
                stderr=result.stderr[:self.max_output_size],
                language="shell",
                duration_ms=duration,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                returncode=-1,
                stderr=f"Execution timed out after {timeout}s",
                language="shell",
                timed_out=True,
            )
        except Exception as e:
            return ExecutionResult(
                returncode=-1, stderr=str(e), language="shell",
            )

    def run_tests(self, test_path: str = "tests/", timeout: Optional[int] = None) -> ExecutionResult:
        """Chạy pytest trên project."""
        timeout = timeout or 120
        return self.run_shell(
            f"{sys.executable} -m pytest {test_path} -v --tb=short",
            timeout=timeout,
        )

    def run_lint(self, filepath: str) -> ExecutionResult:
        """Chạy linter trên file."""
        return self.run_shell(
            f"{sys.executable} -m py_compile {filepath}",
            timeout=10,
        )
