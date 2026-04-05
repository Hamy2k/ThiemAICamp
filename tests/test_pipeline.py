"""Tests for orchestrator pipeline."""

import pytest
from src.orchestrator.pipeline import Pipeline, PipelineRun, PipelineStage


class TestPipelineRun:
    def test_default_values(self):
        run = PipelineRun(project_name="test")
        assert run.stage == PipelineStage.PLANNING
        assert run.project_name == "test"
        assert run.errors == []

    def test_to_dict(self):
        run = PipelineRun(project_name="test")
        d = run.to_dict()
        assert d["project_name"] == "test"
        assert d["stage"] == "planning"
        assert "started_at" in d


class TestPipelineInit:
    def test_pipeline_creates_all_components(self, tmp_path):
        p = Pipeline(workspace_dir=str(tmp_path))
        assert p.task_engine is not None
        assert p.dev_team is not None
        assert p.review_pipeline is not None
        assert p.approval_system is not None
        assert p.logger is not None
        assert p.notifier is not None
        assert p.file_ops is not None
        assert p.sandbox is not None

    def test_auto_approve_flag(self, tmp_path):
        p = Pipeline(auto_approve=True, workspace_dir=str(tmp_path))
        assert p.auto_approve is True

    def test_get_system_status(self, tmp_path):
        p = Pipeline(workspace_dir=str(tmp_path))
        status = p.get_system_status()
        assert "team_status" in status
        assert "pending_approvals" in status
        assert "metrics_summary" in status
        assert "memory_stats" in status
        assert status["active_runs"] == 0

    def test_get_run_nonexistent(self, tmp_path):
        p = Pipeline(workspace_dir=str(tmp_path))
        assert p.get_run("nonexistent") is None

    def test_get_all_runs_empty(self, tmp_path):
        p = Pipeline(workspace_dir=str(tmp_path))
        assert p.get_all_runs() == []


class TestPipelineStages:
    def test_stage_values(self):
        assert PipelineStage.PLANNING.value == "planning"
        assert PipelineStage.APPROVAL.value == "approval"
        assert PipelineStage.DEVELOPMENT.value == "development"
        assert PipelineStage.REVIEW.value == "review"
        assert PipelineStage.COMPLETED.value == "completed"
        assert PipelineStage.FAILED.value == "failed"
