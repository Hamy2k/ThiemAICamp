"""
UPGRADE 5 - OBSERVABILITY (v2 - with persistence + real LangSmith traces)
LangSmith logging: agent runtime, token usage, errors.
"""

import os
import time
import logging
import functools
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable

from src.persistence.database import Database

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    agent_name: str
    task_id: str
    start_time: float = 0.0
    end_time: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    error: Optional[str] = None
    status: str = "pending"
    metadata: dict = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": round(self.duration_seconds, 2),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "error": self.error,
            "status": self.status,
            "metadata": self.metadata,
        }


class LangSmithLogger:
    """Logger tích hợp LangSmith + SQLite persistence."""

    MAX_MEMORY_RECORDS = 1000  # Cap in-memory history

    def __init__(
        self,
        project_name: str = "ThiemAICamp",
        api_key: Optional[str] = None,
        db: Optional[Database] = None,
    ):
        self.project_name = project_name
        self.metrics_history: list[AgentMetrics] = []
        self.db = db or Database()

        # Setup LangSmith
        if api_key:
            os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ.setdefault("LANGSMITH_PROJECT", project_name)
        os.environ.setdefault("LANGSMITH_TRACING", "true")

        self._client = None

    @property
    def client(self):
        if self._client is None and os.environ.get("LANGSMITH_API_KEY"):
            try:
                from langsmith import Client as LangSmithClient
                self._client = LangSmithClient()
                logger.info("LangSmith client initialized")
            except Exception as e:
                logger.warning(f"LangSmith client init failed: {e}")
        return self._client

    def start_tracking(self, agent_name: str, task_id: str, **metadata) -> AgentMetrics:
        """Bắt đầu tracking một agent execution."""
        metrics = AgentMetrics(
            agent_name=agent_name,
            task_id=task_id,
            start_time=time.time(),
            status="running",
            metadata=metadata,
        )
        self.metrics_history.append(metrics)
        # Prune old records from memory
        if len(self.metrics_history) > self.MAX_MEMORY_RECORDS:
            self.metrics_history = self.metrics_history[-self.MAX_MEMORY_RECORDS:]
        return metrics

    def end_tracking(
        self,
        metrics: AgentMetrics,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error: Optional[str] = None,
    ) -> AgentMetrics:
        """Kết thúc tracking và persist to DB."""
        metrics.end_time = time.time()
        metrics.input_tokens = input_tokens
        metrics.output_tokens = output_tokens
        metrics.total_tokens = input_tokens + output_tokens
        metrics.error = error
        metrics.status = "error" if error else "completed"

        # Persist to database
        try:
            self.db.save_metric(metrics.to_dict())
        except Exception as e:
            logger.error(f"Failed to persist metric: {e}")

        # Send to LangSmith if available
        self._send_to_langsmith(metrics)

        return metrics

    def _send_to_langsmith(self, metrics: AgentMetrics) -> None:
        """Send trace to LangSmith."""
        if not self.client:
            return
        try:
            self.client.create_run(
                name=f"{metrics.agent_name}/{metrics.task_id}",
                run_type="chain",
                inputs={"task_id": metrics.task_id, **metrics.metadata},
                outputs={"status": metrics.status, "error": metrics.error},
                start_time=datetime.fromtimestamp(metrics.start_time),
                end_time=datetime.fromtimestamp(metrics.end_time) if metrics.end_time else None,
                extra={
                    "tokens": {
                        "input": metrics.input_tokens,
                        "output": metrics.output_tokens,
                        "total": metrics.total_tokens,
                    }
                },
            )
        except Exception as e:
            logger.debug(f"LangSmith trace send failed (non-critical): {e}")

    def track_agent(self, agent_name: str):
        """Decorator để tự động track agent execution."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                task_id = kwargs.get("task_id", f"task_{int(time.time())}")
                metrics = self.start_tracking(agent_name, task_id)
                try:
                    result = await func(*args, **kwargs)
                    tokens = self._extract_tokens(result)
                    self.end_tracking(metrics, **tokens)
                    return result
                except Exception as e:
                    self.end_tracking(metrics, error=str(e))
                    raise

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                task_id = kwargs.get("task_id", f"task_{int(time.time())}")
                metrics = self.start_tracking(agent_name, task_id)
                try:
                    result = func(*args, **kwargs)
                    tokens = self._extract_tokens(result)
                    self.end_tracking(metrics, **tokens)
                    return result
                except Exception as e:
                    self.end_tracking(metrics, error=str(e))
                    raise

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator

    def _extract_tokens(self, result) -> dict:
        """Extract token usage from LangChain response."""
        tokens = {"input_tokens": 0, "output_tokens": 0}
        if hasattr(result, "usage_metadata"):
            meta = result.usage_metadata
            tokens["input_tokens"] = getattr(meta, "input_tokens", 0) or 0
            tokens["output_tokens"] = getattr(meta, "output_tokens", 0) or 0
        elif hasattr(result, "response_metadata"):
            meta = result.response_metadata
            usage = meta.get("usage", {})
            tokens["input_tokens"] = usage.get("input_tokens", 0)
            tokens["output_tokens"] = usage.get("output_tokens", 0)
        return tokens

    def get_summary(self) -> dict:
        """Lấy tổng quan metrics (from DB if available)."""
        try:
            return self.db.get_metrics_summary()
        except Exception:
            completed = [m for m in self.metrics_history if m.status == "completed"]
            errors = [m for m in self.metrics_history if m.status == "error"]
            total_tokens = sum(m.total_tokens for m in self.metrics_history)
            total_duration = sum(m.duration_seconds for m in self.metrics_history)
            n = len(self.metrics_history)
            return {
                "total_runs": n,
                "completed": len(completed),
                "errors": len(errors),
                "total_tokens": total_tokens,
                "total_duration": round(total_duration, 2),
                "avg_duration": round(total_duration / n, 2) if n else 0,
            }

    def get_agent_stats(self, agent_name: str) -> dict:
        """Lấy stats cho một agent cụ thể."""
        try:
            rows = self.db.get_agent_metrics(agent_name)
            if rows:
                return {
                    "agent_name": agent_name,
                    "runs": len(rows),
                    "total_tokens": sum(r.get("total_tokens", 0) for r in rows),
                    "avg_duration": round(
                        sum(r.get("duration_seconds", 0) for r in rows) / len(rows), 2
                    ),
                    "error_count": sum(1 for r in rows if r.get("status") == "error"),
                }
        except Exception:
            pass

        agent_metrics = [m for m in self.metrics_history if m.agent_name == agent_name]
        if not agent_metrics:
            return {"agent_name": agent_name, "runs": 0}
        return {
            "agent_name": agent_name,
            "runs": len(agent_metrics),
            "total_tokens": sum(m.total_tokens for m in agent_metrics),
            "avg_duration": round(
                sum(m.duration_seconds for m in agent_metrics) / len(agent_metrics), 2
            ),
            "error_count": sum(1 for m in agent_metrics if m.status == "error"),
        }
