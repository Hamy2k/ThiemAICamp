"""
UPGRADE 5 - OBSERVABILITY
LangSmith logging: agent runtime, token usage, errors.
"""

import os
import time
import functools
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Any, Callable

from langsmith import Client as LangSmithClient
from langsmith import traceable


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
            "duration_seconds": round(self.duration_seconds, 2),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "error": self.error,
            "status": self.status,
            "metadata": self.metadata,
        }


class LangSmithLogger:
    """Logger tích hợp LangSmith cho observability."""

    def __init__(
        self,
        project_name: str = "ThiemAICamp",
        api_key: Optional[str] = None,
    ):
        self.project_name = project_name
        self.metrics_history: list[AgentMetrics] = []

        # Setup LangSmith environment
        if api_key:
            os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ.setdefault("LANGSMITH_PROJECT", project_name)
        os.environ.setdefault("LANGSMITH_TRACING", "true")

        self._client = None

    @property
    def client(self) -> Optional[LangSmithClient]:
        if self._client is None and os.environ.get("LANGSMITH_API_KEY"):
            self._client = LangSmithClient()
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
        return metrics

    def end_tracking(
        self,
        metrics: AgentMetrics,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error: Optional[str] = None,
    ) -> AgentMetrics:
        """Kết thúc tracking."""
        metrics.end_time = time.time()
        metrics.input_tokens = input_tokens
        metrics.output_tokens = output_tokens
        metrics.total_tokens = input_tokens + output_tokens
        metrics.error = error
        metrics.status = "error" if error else "completed"
        return metrics

    def track_agent(self, agent_name: str):
        """Decorator để tự động track agent execution."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                task_id = kwargs.get("task_id", f"task_{int(time.time())}")
                metrics = self.start_tracking(agent_name, task_id)
                try:
                    result = await func(*args, **kwargs)
                    # Extract token usage if available
                    if hasattr(result, "usage_metadata"):
                        self.end_tracking(
                            metrics,
                            input_tokens=getattr(result.usage_metadata, "input_tokens", 0),
                            output_tokens=getattr(result.usage_metadata, "output_tokens", 0),
                        )
                    else:
                        self.end_tracking(metrics)
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
                    self.end_tracking(metrics)
                    return result
                except Exception as e:
                    self.end_tracking(metrics, error=str(e))
                    raise

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator

    def get_summary(self) -> dict:
        """Lấy tổng quan metrics."""
        completed = [m for m in self.metrics_history if m.status == "completed"]
        errors = [m for m in self.metrics_history if m.status == "error"]

        total_tokens = sum(m.total_tokens for m in self.metrics_history)
        total_duration = sum(m.duration_seconds for m in self.metrics_history)
        avg_duration = total_duration / len(self.metrics_history) if self.metrics_history else 0

        return {
            "total_runs": len(self.metrics_history),
            "completed": len(completed),
            "errors": len(errors),
            "total_tokens": total_tokens,
            "total_duration_seconds": round(total_duration, 2),
            "avg_duration_seconds": round(avg_duration, 2),
            "error_rate": f"{len(errors) / len(self.metrics_history) * 100:.1f}%" if self.metrics_history else "0%",
            "recent_errors": [
                {"agent": m.agent_name, "task": m.task_id, "error": m.error}
                for m in errors[-5:]
            ],
        }

    def get_agent_stats(self, agent_name: str) -> dict:
        """Lấy stats cho một agent cụ thể."""
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
