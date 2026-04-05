"""Tests for execution layer - file_ops and sandbox."""

import os
import pytest
from pathlib import Path
from src.execution.file_ops import FileOperations
from src.execution.sandbox import Sandbox, ExecutionResult


class TestFileOperations:
    @pytest.fixture
    def file_ops(self, tmp_path):
        return FileOperations(str(tmp_path))

    def test_write_new_file(self, file_ops, tmp_path):
        result = file_ops.write_file("hello.py", "print('hello')")
        assert result["is_new"] is True
        assert (tmp_path / "hello.py").read_text() == "print('hello')"

    def test_write_updates_existing(self, file_ops, tmp_path):
        file_ops.write_file("test.py", "v1")
        file_ops.write_file("test.py", "v2")
        assert (tmp_path / "test.py").read_text() == "v2"

    def test_read_file(self, file_ops, tmp_path):
        (tmp_path / "readme.txt").write_text("Hello", encoding="utf-8")
        content = file_ops.read_file("readme.txt")
        assert content == "Hello"

    def test_read_nonexistent(self, file_ops):
        with pytest.raises(FileNotFoundError):
            file_ops.read_file("nonexistent.py")

    def test_edit_file(self, file_ops, tmp_path):
        file_ops.write_file("app.py", "name = 'old'")
        file_ops.edit_file("app.py", "'old'", "'new'")
        assert (tmp_path / "app.py").read_text() == "name = 'new'"

    def test_edit_text_not_found(self, file_ops):
        file_ops.write_file("app.py", "hello")
        with pytest.raises(ValueError):
            file_ops.edit_file("app.py", "nonexistent", "new")

    def test_delete_file(self, file_ops, tmp_path):
        file_ops.write_file("to_delete.py", "temp")
        file_ops.delete_file("to_delete.py")
        assert not (tmp_path / "to_delete.py").exists()

    def test_list_files(self, file_ops, tmp_path):
        file_ops.write_file("a.py", "")
        file_ops.write_file("src/b.py", "")
        files = file_ops.list_files()
        assert "a.py" in files
        assert "src/b.py" in files

    def test_path_traversal_blocked(self, file_ops):
        with pytest.raises(PermissionError):
            file_ops.read_file("../../etc/passwd")

    def test_blocked_patterns(self, file_ops):
        with pytest.raises(PermissionError):
            file_ops.write_file(".env", "SECRET=x")
        with pytest.raises(PermissionError):
            file_ops.write_file(".git/config", "bad")

    def test_get_diff(self, file_ops):
        file_ops.write_file("diff.py", "line1\nline2\n")
        diff = file_ops.get_diff("diff.py", "line1\nline3\n")
        assert "-line2" in diff
        assert "+line3" in diff

    def test_backup_and_restore(self, file_ops, tmp_path):
        file_ops.write_file("important.py", "original")
        file_ops.write_file("important.py", "modified")
        file_ops.restore_backup("important.py")
        assert (tmp_path / "important.py").read_text() == "original"

    def test_get_changes(self, file_ops):
        file_ops.write_file("a.py", "")
        file_ops.write_file("b.py", "")
        changes = file_ops.get_changes()
        assert len(changes) == 2
        assert sorted(file_ops.get_changed_files()) == ["a.py", "b.py"]

    def test_nested_directory_creation(self, file_ops, tmp_path):
        file_ops.write_file("deep/nested/dir/file.py", "content")
        assert (tmp_path / "deep/nested/dir/file.py").read_text() == "content"


class TestSandbox:
    @pytest.fixture
    def sandbox(self, tmp_path):
        return Sandbox(workspace_dir=str(tmp_path), timeout=10)

    def test_run_python_success(self, sandbox):
        result = sandbox.run_python("print('hello world')")
        assert result.success
        assert "hello world" in result.stdout

    def test_run_python_error(self, sandbox):
        result = sandbox.run_python("raise ValueError('bad')")
        assert not result.success
        assert "ValueError" in result.stderr

    def test_run_python_timeout(self, sandbox):
        result = sandbox.run_python("import time; time.sleep(60)", timeout=1)
        assert result.timed_out
        assert not result.success

    def test_run_python_computation(self, sandbox):
        result = sandbox.run_python("print(sum(range(100)))")
        assert result.success
        assert "4950" in result.stdout

    def test_run_shell(self, sandbox):
        result = sandbox.run_shell("echo test123")
        assert result.success
        assert "test123" in result.stdout

    def test_blocked_commands(self, sandbox):
        from src.utils import ExecutionError
        with pytest.raises(ExecutionError):
            sandbox.run_shell("rm -rf /")

    def test_execution_result_to_dict(self):
        result = ExecutionResult(returncode=0, stdout="ok", language="python", duration_ms=123.4)
        d = result.to_dict()
        assert d["success"] is True
        assert d["duration_ms"] == 123.4

    def test_run_tests(self, sandbox, tmp_path):
        # Create a simple test file
        test_file = tmp_path / "test_simple.py"
        test_file.write_text("def test_basic(): assert 1 + 1 == 2")
        result = sandbox.run_tests(str(test_file))
        assert result.success or "passed" in result.stdout.lower()

    def test_run_lint_valid(self, sandbox, tmp_path):
        py_file = tmp_path / "valid.py"
        py_file.write_text("x = 1\nprint(x)\n")
        result = sandbox.run_lint(str(py_file))
        assert result.success

    def test_run_lint_invalid(self, sandbox, tmp_path):
        py_file = tmp_path / "invalid.py"
        py_file.write_text("def bad(\n")
        result = sandbox.run_lint(str(py_file))
        assert not result.success
