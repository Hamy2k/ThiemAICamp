"""Tests for persistence layer."""

import os
import json
import pytest
import tempfile
from src.persistence.database import Database


@pytest.fixture
def db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(db_path=os.path.join(tmpdir, "test.db"))
        yield db
        db.close()


class TestApprovals:
    def test_save_and_get_pending(self, db):
        db.save_approval({
            "id": "ap_001",
            "type": "task_approval",
            "title": "Test approval",
            "description": "Test desc",
            "status": "pending",
            "reviewer": "Thiem",
            "feedback": "",
            "requested_at": "2025-01-01T00:00:00",
            "responded_at": None,
        })
        pending = db.get_pending_approvals()
        assert len(pending) == 1
        assert pending[0]["title"] == "Test approval"

    def test_update_approval_status(self, db):
        db.save_approval({
            "id": "ap_002",
            "type": "deploy_approval",
            "title": "Deploy",
            "description": "",
            "status": "pending",
            "reviewer": "Thiem",
            "feedback": "",
            "requested_at": "2025-01-01T00:00:00",
        })
        db.update_approval_status("ap_002", "approved", "LGTM")
        history = db.get_approval_history()
        assert len(history) == 1
        assert history[0]["status"] == "approved"
        assert history[0]["feedback"] == "LGTM"


class TestMetrics:
    def test_save_and_summary(self, db):
        db.save_metric({
            "agent_name": "api_agent",
            "task_id": "task_001",
            "start_time": 1000.0,
            "end_time": 1005.0,
            "duration_seconds": 5.0,
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "status": "completed",
        })
        db.save_metric({
            "agent_name": "ui_agent",
            "task_id": "task_002",
            "start_time": 1000.0,
            "end_time": 1003.0,
            "duration_seconds": 3.0,
            "input_tokens": 50,
            "output_tokens": 100,
            "total_tokens": 150,
            "error": "timeout",
            "status": "error",
        })
        summary = db.get_metrics_summary()
        assert summary["total_runs"] == 2
        assert summary["completed"] == 1
        assert summary["errors"] == 1
        assert summary["total_tokens"] == 450

    def test_agent_metrics(self, db):
        db.save_metric({
            "agent_name": "api_agent",
            "task_id": "t1",
            "duration_seconds": 5.0,
            "total_tokens": 300,
            "status": "completed",
        })
        rows = db.get_agent_metrics("api_agent")
        assert len(rows) == 1
        assert rows[0]["task_id"] == "t1"


class TestTaskState:
    def test_save_and_load(self, db):
        project_data = {"name": "Test", "milestones": []}
        db.save_task_state("proj_1", project_data)
        loaded = db.load_task_state("proj_1")
        assert loaded["name"] == "Test"

    def test_load_nonexistent(self, db):
        assert db.load_task_state("nonexistent") is None

    def test_list_projects(self, db):
        db.save_task_state("p1", {"name": "Project 1"})
        db.save_task_state("p2", {"name": "Project 2"})
        projects = db.list_projects()
        assert len(projects) == 2


class TestExecutionLogs:
    def test_log_and_retrieve(self, db):
        log_id = db.log_execution(
            run_id="run_001",
            agent_role="api",
            action="generate_code",
            input_data="Build user API",
            status="running",
        )
        assert log_id > 0

        db.update_execution_log(
            log_id, status="completed",
            output_data="def get_users(): ...",
            files_changed=["api/users.py"],
        )

        logs = db.get_execution_logs("run_001")
        assert len(logs) == 1
        assert logs[0]["status"] == "completed"
        assert "users.py" in logs[0]["files_changed"]
