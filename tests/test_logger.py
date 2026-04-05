"""Tests for langsmith_logger - tracking, decorator, summary."""

import os
import time
import pytest
import asyncio
import tempfile
from src.persistence.database import Database
from src.monitoring.langsmith_logger import LangSmithLogger, AgentMetrics


@pytest.fixture
def db(tmp_path):
    db = Database(db_path=str(tmp_path / "test.db"))
    yield db
    db.close()


@pytest.fixture
def logger(db):
    return LangSmithLogger(project_name="test", db=db)


class TestAgentMetrics:
    def test_duration(self):
        m = AgentMetrics(agent_name="test", task_id="t1", start_time=100.0, end_time=105.0)
        assert m.duration_seconds == 5.0

    def test_duration_no_end(self):
        m = AgentMetrics(agent_name="test", task_id="t1", start_time=100.0)
        assert m.duration_seconds == 0.0

    def test_to_dict(self):
        m = AgentMetrics(agent_name="api", task_id="t1", input_tokens=100, output_tokens=200, total_tokens=300, status="completed")
        d = m.to_dict()
        assert d["agent_name"] == "api"
        assert d["total_tokens"] == 300


class TestLangSmithLogger:
    def test_start_end_tracking(self, logger):
        metrics = logger.start_tracking("api_agent", "task_001")
        assert metrics.status == "running"
        assert metrics.start_time > 0

        logger.end_tracking(metrics, input_tokens=100, output_tokens=200)
        assert metrics.status == "completed"
        assert metrics.total_tokens == 300
        assert metrics.end_time >= metrics.start_time

    def test_tracking_error(self, logger):
        metrics = logger.start_tracking("api_agent", "task_err")
        logger.end_tracking(metrics, error="timeout")
        assert metrics.status == "error"
        assert metrics.error == "timeout"

    def test_memory_cap(self, logger):
        logger.MAX_MEMORY_RECORDS = 5
        for i in range(10):
            logger.start_tracking("agent", f"task_{i}")
        assert len(logger.metrics_history) <= 5

    def test_get_summary_from_db(self, logger, db):
        m = logger.start_tracking("agent", "t1")
        logger.end_tracking(m, input_tokens=100, output_tokens=200)
        summary = logger.get_summary()
        assert summary["total_runs"] >= 1

    def test_get_agent_stats(self, logger, db):
        m = logger.start_tracking("api_agent", "t1")
        logger.end_tracking(m, input_tokens=50, output_tokens=50)
        stats = logger.get_agent_stats("api_agent")
        assert stats["runs"] >= 1
        assert stats["total_tokens"] >= 100

    def test_decorator_sync(self, logger):
        @logger.track_agent("test_agent")
        def do_work():
            return "result"

        result = do_work()
        assert result == "result"
        assert len(logger.metrics_history) >= 1
        assert logger.metrics_history[-1].status == "completed"

    def test_decorator_sync_error(self, logger):
        @logger.track_agent("test_agent")
        def do_fail():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            do_fail()
        assert logger.metrics_history[-1].status == "error"

    def test_decorator_async(self, logger):
        @logger.track_agent("async_agent")
        async def do_async():
            return "async_result"

        result = asyncio.get_event_loop().run_until_complete(do_async())
        assert result == "async_result"

    def test_extract_tokens_no_metadata(self, logger):
        tokens = logger._extract_tokens("plain string")
        assert tokens["input_tokens"] == 0
        assert tokens["output_tokens"] == 0

    def test_persists_to_db(self, logger, db):
        m = logger.start_tracking("db_agent", "persist_test")
        logger.end_tracking(m, input_tokens=10, output_tokens=20)
        rows = db.get_agent_metrics("db_agent")
        assert len(rows) >= 1
