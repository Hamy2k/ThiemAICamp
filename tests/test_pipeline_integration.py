"""Integration test - full pipeline flow with mock LLM."""

import pytest
import asyncio
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock

from src.orchestrator.pipeline import Pipeline, PipelineStage
from src.agents.dev_team import AgentRole
from src.persistence.database import Database


@pytest.fixture
def tmp_workspace(tmp_path):
    return str(tmp_path / "workspace")


@pytest.fixture
def db(tmp_path):
    db = Database(db_path=str(tmp_path / "test.db"))
    yield db
    db.close()


def _mock_llm_response(content):
    mock_response = MagicMock()
    mock_response.content = content
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    return mock_llm


class TestPipelineIntegration:
    @patch("src.agents.dev_team.ChatAnthropic")
    @patch("src.agents.reviewer.ChatAnthropic")
    def test_full_pipeline_auto_approve(self, mock_reviewer_llm, mock_dev_llm, tmp_workspace, db):
        """Full pipeline: Plan > Dev (file write) > Review > Complete."""
        # Dev agent returns code with FILE blocks
        mock_dev_llm.return_value = _mock_llm_response(
            'FILE: src/api.py\n```python\ndef get_users():\n    return []\n```'
        )
        # Reviewer returns approval JSON
        mock_reviewer_llm.return_value = _mock_llm_response(
            '{"approved": true, "score": 8.5, "summary": "Good", "comments": []}'
        )

        from src.memory.chroma_store import MemoryStore
        memory = MemoryStore(persist_dir=str(tmp_workspace + "_chroma"))

        pipeline = Pipeline(
            db=db,
            memory=memory,
            auto_approve=True,
            workspace_dir=tmp_workspace,
        )

        tasks = [
            {"title": "Build user API", "role": "api", "priority": "high", "description": "Create GET /users endpoint"},
        ]

        run = asyncio.get_event_loop().run_until_complete(
            pipeline.run_project("Test Project", "Integration test", tasks)
        )

        # Pipeline should complete
        assert run.stage == PipelineStage.COMPLETED
        assert run.completed_at is not None
        assert len(run.errors) == 0

        # Planning results
        assert "planning" in run.results
        assert run.results["planning"]["total_tasks"] == 1

        # Development results
        assert "development" in run.results
        assert "api" in run.results["development"]
        dev_result = run.results["development"]["api"]
        assert dev_result["status"] == "completed"
        assert "src/api.py" in dev_result.get("files_written", [])

        # Review results
        assert "review" in run.results

        # Run is tracked
        assert pipeline.get_run(run.id) is not None

    @patch("src.agents.dev_team.ChatAnthropic")
    def test_pipeline_dev_failure_handled(self, mock_dev_llm, tmp_workspace, db):
        """Pipeline handles agent failures gracefully."""
        mock_dev_llm.return_value.ainvoke = AsyncMock(side_effect=RuntimeError("LLM down"))

        from src.memory.chroma_store import MemoryStore
        memory = MemoryStore(persist_dir=str(tmp_workspace + "_chroma"))

        pipeline = Pipeline(db=db, memory=memory, auto_approve=True, workspace_dir=tmp_workspace)

        tasks = [
            {"title": "Failing task", "role": "api", "priority": "medium", "description": "This will fail"},
        ]

        # Should not raise - errors captured in run
        run = asyncio.get_event_loop().run_until_complete(
            pipeline.run_project("Fail Project", "Test failure", tasks)
        )

        # Dev errors captured
        assert "development" in run.results
        assert run.results["development"]["api"]["status"] == "error"
        assert len(run.errors) > 0

    @patch("src.agents.dev_team.ChatAnthropic")
    @patch("src.agents.reviewer.ChatAnthropic")
    def test_pipeline_multi_agent_parallel(self, mock_reviewer, mock_dev, tmp_workspace, db):
        """Multiple agents run in parallel."""
        mock_dev.return_value = _mock_llm_response(
            'FILE: output.py\n```python\nresult = True\n```'
        )
        mock_reviewer.return_value = _mock_llm_response(
            '{"approved": true, "score": 9.0, "summary": "Great", "comments": []}'
        )

        from src.memory.chroma_store import MemoryStore
        memory = MemoryStore(persist_dir=str(tmp_workspace + "_chroma"))

        pipeline = Pipeline(db=db, memory=memory, auto_approve=True, workspace_dir=tmp_workspace)

        tasks = [
            {"title": "Build API", "role": "api", "priority": "high", "description": "API"},
            {"title": "Build Auth", "role": "auth", "priority": "high", "description": "Auth"},
            {"title": "Build DB", "role": "db", "priority": "medium", "description": "DB"},
        ]

        run = asyncio.get_event_loop().run_until_complete(
            pipeline.run_project("Multi", "Multi agent test", tasks)
        )

        assert run.stage == PipelineStage.COMPLETED
        dev = run.results["development"]
        # At least some agents completed (parallel may share roles)
        completed_count = sum(1 for v in dev.values() if v.get("status") == "completed")
        assert completed_count >= 1

    def test_system_status(self, tmp_workspace, db):
        """System status returns all component states."""
        from src.memory.chroma_store import MemoryStore
        memory = MemoryStore(persist_dir=str(tmp_workspace + "_chroma"))
        pipeline = Pipeline(db=db, memory=memory, workspace_dir=tmp_workspace)

        status = pipeline.get_system_status()
        assert "team_status" in status
        assert "pending_approvals" in status
        assert "metrics_summary" in status
        assert "memory_stats" in status
        assert status["active_runs"] == 0

    @patch("src.agents.dev_team.ChatAnthropic")
    def test_single_task(self, mock_llm, tmp_workspace, db):
        """Run single task through pipeline."""
        mock_llm.return_value = _mock_llm_response("def hello(): return 'world'")

        from src.memory.chroma_store import MemoryStore
        memory = MemoryStore(persist_dir=str(tmp_workspace + "_chroma"))
        pipeline = Pipeline(db=db, memory=memory, workspace_dir=tmp_workspace)

        result = asyncio.get_event_loop().run_until_complete(
            pipeline.run_single_task("Write hello function", role=AgentRole.API, review=False)
        )

        assert result["role"] == "api"
        assert "hello" in result["output"]
