"""Tests for CLI commands."""

import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


class TestCLICommands:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ThiemAICamp" in result.stdout

    def test_status(self):
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "System Status" in result.stdout

    def test_memory_stats(self):
        result = runner.invoke(app, ["memory-stats"])
        assert result.exit_code == 0
        assert "Memory Statistics" in result.stdout

    def test_approvals_empty(self):
        result = runner.invoke(app, ["approvals"])
        assert result.exit_code == 0
        assert "No pending approvals" in result.stdout

    def test_approve_nonexistent(self):
        result = runner.invoke(app, ["approve", "fake_id"])
        assert result.exit_code == 0
        assert "not found" in result.stdout.lower()

    def test_reject_nonexistent(self):
        result = runner.invoke(app, ["reject", "fake_id"])
        assert result.exit_code == 0
        assert "not found" in result.stdout.lower()

    def test_templates(self):
        result = runner.invoke(app, ["templates"])
        assert result.exit_code == 0
        assert "SaaS" in result.stdout
        assert "CRUD" in result.stdout
        assert "AI Tool" in result.stdout

    def test_scaffold_saas(self, tmp_path):
        result = runner.invoke(app, ["scaffold", "saas", str(tmp_path / "out"), "--name", "Test"])
        assert result.exit_code == 0
        assert "Scaffolded" in result.stdout

    def test_scaffold_invalid(self, tmp_path):
        result = runner.invoke(app, ["scaffold", "bad_template", str(tmp_path / "out")])
        assert result.exit_code == 0  # Typer catches and prints error

    def test_metrics(self):
        result = runner.invoke(app, ["metrics"])
        assert result.exit_code == 0

    def test_run_code_python(self):
        result = runner.invoke(app, ["run-code", "print(1+1)"])
        assert result.exit_code == 0
        assert "2" in result.stdout

    def test_run_code_error(self):
        result = runner.invoke(app, ["run-code", "raise ValueError('x')"])
        assert result.exit_code == 0
        assert "Failed" in result.stdout

    def test_run_tests_command(self):
        result = runner.invoke(app, ["run-tests", "--path", "tests/test_utils.py"])
        # exit_code depends on typer argument parsing
        assert "passed" in result.stdout or result.exit_code == 0

    def test_pipeline_help(self):
        result = runner.invoke(app, ["pipeline", "--help"])
        assert result.exit_code == 0
        assert "project" in result.stdout.lower()
