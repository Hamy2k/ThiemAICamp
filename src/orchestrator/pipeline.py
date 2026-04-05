"""
ORCHESTRATOR - Main Pipeline kết nối toàn bộ 7 modules.
Flow: Plan > Approve > Dev (parallel) > Review > QA > Deploy

Đây là bộ não trung tâm của ThiemAICamp - kết nối:
1. Memory (tìm patterns/bugs tương tự)
2. Task Engine (phân chia tasks)
3. Human Approval (checkpoint trước khi dev)
4. Dev Team (4 agents song song)
5. Reviewer + QA (review pipeline)
6. LangSmith Logger (observability)
7. Templates (scaffold nếu cần)
"""

import uuid
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from src.persistence.database import Database
from src.memory.chroma_store import MemoryStore
from src.engine.task_engine import TaskEngine, Project, Priority, Status
from src.agents.dev_team import DevTeam, AgentRole
from src.agents.reviewer import ReviewPipeline
from src.checkpoints.human_approval import HumanApprovalSystem, CheckpointType, ApprovalStatus
from src.monitoring.langsmith_logger import LangSmithLogger

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    PLANNING = "planning"
    APPROVAL = "approval"
    DEVELOPMENT = "development"
    REVIEW = "review"
    QA = "qa"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineRun:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    project_name: str = ""
    stage: PipelineStage = PipelineStage.PLANNING
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    results: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_name": self.project_name,
            "stage": self.stage.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "results": self.results,
            "errors": self.errors,
        }


class Pipeline:
    """Main orchestrator kết nối tất cả modules."""

    def __init__(
        self,
        db: Optional[Database] = None,
        memory: Optional[MemoryStore] = None,
        auto_approve: bool = False,
    ):
        self.db = db or Database()
        self.memory = memory or MemoryStore()
        self.task_engine = TaskEngine(db=self.db)
        self.dev_team = DevTeam()
        self.review_pipeline = ReviewPipeline()
        self.approval_system = HumanApprovalSystem(db=self.db)
        self.logger = LangSmithLogger(db=self.db)
        self.auto_approve = auto_approve
        self.runs: dict[str, PipelineRun] = {}

    async def run_project(
        self,
        project_name: str,
        description: str,
        tasks: list[dict],
        require_approval: bool = True,
    ) -> PipelineRun:
        """
        Chạy full pipeline cho một project.

        Args:
            project_name: Tên project
            description: Mô tả project
            tasks: List of {"title": str, "description": str, "role": str, "priority": str}
            require_approval: Có cần approval không
        """
        run = PipelineRun(project_name=project_name)
        self.runs[run.id] = run

        metrics = self.logger.start_tracking("pipeline", run.id)

        try:
            # ── Stage 1: PLANNING ──────────────────────────────────
            run.stage = PipelineStage.PLANNING
            logger.info(f"[{run.id}] Stage: PLANNING - {project_name}")

            # Search memory for similar past work
            memory_context = self.memory.search_all(description, n_results=2)
            relevant_patterns = []
            for collection, results in memory_context.items():
                for r in results:
                    if r.get("distance", 1.0) < 0.5:
                        relevant_patterns.append(r["content"][:200])

            if relevant_patterns:
                logger.info(f"Found {len(relevant_patterns)} relevant patterns from memory")
                run.results["memory_hits"] = len(relevant_patterns)

            # Create project in task engine
            project = self.task_engine.create_project(project_name, description)
            milestone = project.add_milestone("Main", description=description)

            role_map = {
                "api": AgentRole.API,
                "ui": AgentRole.UI,
                "auth": AgentRole.AUTH,
                "db": AgentRole.DB,
            }

            for t in tasks:
                priority = Priority(t.get("priority", "medium"))
                task = milestone.add_task(t["title"], t.get("description", ""), priority)
                deps = t.get("dependencies", [])
                if deps:
                    task.dependencies = deps

            run.results["planning"] = {
                "project_id": project.id,
                "total_tasks": len(tasks),
                "memory_context": len(relevant_patterns),
            }

            # ── Stage 2: APPROVAL ──────────────────────────────────
            if require_approval and not self.auto_approve:
                run.stage = PipelineStage.APPROVAL
                logger.info(f"[{run.id}] Stage: APPROVAL")

                request = self.approval_system.create_checkpoint(
                    checkpoint_type=CheckpointType.TASK_APPROVAL,
                    title=f"Approve project: {project_name}",
                    description=f"{description}\n\nTasks: {len(tasks)}",
                    details={
                        "tasks": [t["title"] for t in tasks],
                        "memory_context": relevant_patterns[:3],
                    },
                )

                result = await self.approval_system.wait_for_approval(
                    request.id, poll_interval=2.0
                )

                if result.status != ApprovalStatus.APPROVED:
                    run.stage = PipelineStage.FAILED
                    run.errors.append(f"Approval {result.status.value}: {result.feedback}")
                    logger.warning(f"[{run.id}] Approval rejected/timeout")
                    return run

                run.results["approval"] = {"status": "approved", "feedback": result.feedback}

            # ── Stage 3: DEVELOPMENT (parallel) ────────────────────
            run.stage = PipelineStage.DEVELOPMENT
            logger.info(f"[{run.id}] Stage: DEVELOPMENT")

            assignments = {}
            for t in tasks:
                role_str = t.get("role", "api")
                role = role_map.get(role_str, AgentRole.API)
                assignments[role] = t.get("description", t["title"])

            dev_results = await self.dev_team.assign_parallel(assignments)

            run.results["development"] = {}
            for role, result in dev_results.items():
                is_error = isinstance(result, str) and result.startswith("ERROR:")
                run.results["development"][role.value] = {
                    "status": "error" if is_error else "completed",
                    "output_length": len(result),
                    "preview": result[:300] if not is_error else result,
                }
                if is_error:
                    run.errors.append(f"Dev {role.value}: {result}")

            # Mark tasks completed
            for task in milestone.tasks:
                role_str = None
                for t in tasks:
                    if t["title"] == task.title:
                        role_str = t.get("role", "api")
                        break
                if role_str:
                    role = role_map.get(role_str, AgentRole.API)
                    dev_output = dev_results.get(role, "")
                    if not (isinstance(dev_output, str) and dev_output.startswith("ERROR:")):
                        self.task_engine.complete_task(task.id)

            # ── Stage 4: REVIEW ────────────────────────────────────
            run.stage = PipelineStage.REVIEW
            logger.info(f"[{run.id}] Stage: REVIEW")

            review_results = {}
            for role, output in dev_results.items():
                if isinstance(output, str) and not output.startswith("ERROR:"):
                    try:
                        review = await self.review_pipeline.run(
                            output, filename=f"{role.value}_output",
                            context=f"Project: {project_name}"
                        )
                        review_results[role.value] = review
                    except Exception as e:
                        logger.error(f"Review failed for {role.value}: {e}")
                        review_results[role.value] = {"error": str(e)}

            run.results["review"] = review_results

            # ── Stage 5: COMPLETE ──────────────────────────────────
            run.stage = PipelineStage.COMPLETED
            run.completed_at = datetime.now().isoformat()

            # Store learnings in memory
            try:
                self.memory.store_architecture_decision(
                    title=f"Project: {project_name}",
                    context=description,
                    decision=f"Completed with {len(tasks)} tasks",
                    consequences=f"Reviews: {json.dumps({k: v.get('passed', False) for k, v in review_results.items() if isinstance(v, dict)}, default=str)}",
                )
            except Exception as e:
                logger.debug(f"Memory store failed (non-critical): {e}")

            logger.info(f"[{run.id}] Pipeline COMPLETED for {project_name}")

        except Exception as e:
            run.stage = PipelineStage.FAILED
            run.errors.append(str(e))
            logger.error(f"[{run.id}] Pipeline FAILED: {e}")
            self.logger.end_tracking(metrics, error=str(e))
            raise
        else:
            self.logger.end_tracking(metrics)

        # Persist run to DB
        try:
            import json
            self.db.log_execution(
                run_id=run.id, agent_role="pipeline", action="run_project",
                input_data=json.dumps({"name": project_name, "tasks": len(tasks)}),
                output_data=json.dumps(run.to_dict(), default=str),
                status=run.stage.value,
            )
        except Exception as e:
            logger.error(f"Failed to persist run: {e}")

        return run

    async def run_single_task(
        self,
        task_description: str,
        role: AgentRole = AgentRole.API,
        review: bool = True,
    ) -> dict:
        """Chạy một task đơn lẻ qua pipeline (Plan > Dev > Review)."""
        metrics = self.logger.start_tracking(role.value, f"single_{uuid.uuid4().hex[:6]}")

        try:
            # Dev
            dev_output = await self.dev_team.assign_task(role, task_description)

            result = {
                "role": role.value,
                "output": dev_output,
                "review": None,
            }

            # Review
            if review:
                review_result = await self.review_pipeline.run(
                    dev_output, filename=f"{role.value}_task"
                )
                result["review"] = review_result

            self.logger.end_tracking(metrics)
            return result

        except Exception as e:
            self.logger.end_tracking(metrics, error=str(e))
            raise

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        return self.runs.get(run_id)

    def get_all_runs(self) -> list[dict]:
        return [r.to_dict() for r in self.runs.values()]

    def get_system_status(self) -> dict:
        """Tổng quan trạng thái toàn hệ thống."""
        return {
            "team_status": self.dev_team.team_status(),
            "pending_approvals": self.approval_system.get_pending(),
            "metrics_summary": self.logger.get_summary(),
            "memory_stats": self.memory.get_stats(),
            "active_runs": sum(
                1 for r in self.runs.values()
                if r.stage not in (PipelineStage.COMPLETED, PipelineStage.FAILED)
            ),
            "total_runs": len(self.runs),
        }


# Need json import at module level for the memory store call
import json
