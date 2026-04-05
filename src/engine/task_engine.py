"""
UPGRADE 2 - TASK ENGINE (v2 - thread-safe, cross-milestone deps, persistence)
Quản lý hierarchy: Project > Milestones > Tasks > Subtasks.
Mỗi agent chỉ nhận 1 task nhỏ tại một thời điểm.
"""

import uuid
import json
import threading
import logging
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

from src.persistence.database import Database

logger = logging.getLogger(__name__)


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Subtask:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    status: Status = Status.PENDING
    assigned_agent: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def complete(self):
        self.status = Status.COMPLETED
        self.completed_at = datetime.now().isoformat()


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    status: Status = Status.PENDING
    priority: Priority = Priority.MEDIUM
    assigned_agent: Optional[str] = None
    subtasks: list[Subtask] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def add_subtask(self, title: str, description: str = "") -> Subtask:
        subtask = Subtask(title=title, description=description)
        self.subtasks.append(subtask)
        return subtask

    def progress(self) -> float:
        if not self.subtasks:
            return 1.0 if self.status == Status.COMPLETED else 0.0
        done = sum(1 for s in self.subtasks if s.status == Status.COMPLETED)
        return done / len(self.subtasks)

    def complete(self):
        self.status = Status.COMPLETED
        self.completed_at = datetime.now().isoformat()

    def fail(self, reason: str = ""):
        self.status = Status.FAILED
        logger.warning(f"Task {self.id} '{self.title}' failed: {reason}")


@dataclass
class Milestone:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    tasks: list[Task] = field(default_factory=list)
    deadline: Optional[str] = None

    def add_task(self, title: str, description: str = "", priority: Priority = Priority.MEDIUM) -> Task:
        task = Task(title=title, description=description, priority=priority)
        self.tasks.append(task)
        return task

    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        return sum(t.progress() for t in self.tasks) / len(self.tasks)

    @property
    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        try:
            return datetime.now() > datetime.fromisoformat(self.deadline)
        except ValueError:
            return False


@dataclass
class Project:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    milestones: list[Milestone] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_milestone(self, title: str, description: str = "", deadline: Optional[str] = None) -> Milestone:
        milestone = Milestone(title=title, description=description, deadline=deadline)
        self.milestones.append(milestone)
        return milestone

    def progress(self) -> float:
        if not self.milestones:
            return 0.0
        return sum(m.progress() for m in self.milestones) / len(self.milestones)

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks across all milestones."""
        tasks = []
        for m in self.milestones:
            tasks.extend(m.tasks)
        return tasks

    def find_task(self, task_id: str) -> Optional[Task]:
        for task in self.get_all_tasks():
            if task.id == task_id:
                return task
        return None


class TaskEngine:
    """Quản lý toàn bộ project hierarchy và phân phối tasks cho agents. Thread-safe."""

    def __init__(self, db: Optional[Database] = None):
        self.projects: dict[str, Project] = {}
        self.db = db or Database()
        self._lock = threading.RLock()

    def create_project(self, name: str, description: str = "") -> Project:
        with self._lock:
            project = Project(name=name, description=description)
            self.projects[project.id] = project
            self._persist(project)
            logger.info(f"Created project: {name} ({project.id})")
            return project

    def get_next_task(self, agent_id: str) -> Optional[Task]:
        """Lấy task tiếp theo cho agent. Mỗi agent chỉ nhận 1 task. Thread-safe."""
        priority_order = [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]

        with self._lock:
            # Check if agent already has a task
            for project in self.projects.values():
                for task in project.get_all_tasks():
                    if task.assigned_agent == agent_id and task.status == Status.IN_PROGRESS:
                        return task  # Already assigned

            # Find next available task
            for priority in priority_order:
                for project in self.projects.values():
                    for task in project.get_all_tasks():
                        if task.status == Status.PENDING and task.priority == priority:
                            if self._dependencies_met(task, project):
                                task.status = Status.IN_PROGRESS
                                task.assigned_agent = agent_id
                                self._persist(project)
                                logger.info(f"Assigned task '{task.title}' to {agent_id}")
                                return task
            return None

    def _dependencies_met(self, task: Task, project: Project) -> bool:
        """Kiểm tra dependencies across all milestones (cross-milestone support)."""
        all_tasks = project.get_all_tasks()
        for dep_id in task.dependencies:
            dep_task = next((t for t in all_tasks if t.id == dep_id), None)
            if dep_task is None:
                logger.warning(f"Dependency {dep_id} not found for task {task.id}")
                continue
            if dep_task.status != Status.COMPLETED:
                return False
        return True

    def complete_task(self, task_id: str) -> bool:
        with self._lock:
            for project in self.projects.values():
                task = project.find_task(task_id)
                if task:
                    task.complete()
                    self._persist(project)
                    logger.info(f"Completed task: {task.title} ({task_id})")
                    return True
            return False

    def fail_task(self, task_id: str, reason: str = "") -> bool:
        with self._lock:
            for project in self.projects.values():
                task = project.find_task(task_id)
                if task:
                    task.fail(reason)
                    self._persist(project)
                    return True
            return False

    def reassign_task(self, task_id: str, new_agent_id: str) -> bool:
        """Reassign a task to a different agent."""
        with self._lock:
            for project in self.projects.values():
                task = project.find_task(task_id)
                if task and task.status in (Status.IN_PROGRESS, Status.FAILED):
                    task.assigned_agent = new_agent_id
                    task.status = Status.IN_PROGRESS
                    self._persist(project)
                    logger.info(f"Reassigned task {task_id} to {new_agent_id}")
                    return True
            return False

    def get_project_summary(self, project_id: str) -> dict:
        project = self.projects.get(project_id)
        if not project:
            return {}
        return {
            "name": project.name,
            "progress": f"{project.progress() * 100:.1f}%",
            "milestones": [
                {
                    "title": m.title,
                    "progress": f"{m.progress() * 100:.1f}%",
                    "tasks_total": len(m.tasks),
                    "tasks_completed": sum(1 for t in m.tasks if t.status == Status.COMPLETED),
                    "overdue": m.is_overdue,
                }
                for m in project.milestones
            ],
        }

    def _persist(self, project: Project) -> None:
        """Save project state to DB."""
        try:
            self.db.save_task_state(project.id, asdict(project))
        except Exception as e:
            logger.error(f"Failed to persist project {project.id}: {e}")

    def save_to_file(self, filepath: str) -> None:
        with self._lock:
            data = {pid: asdict(p) for pid, p in self.projects.items()}
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)

    def load_from_file(self, filepath: str) -> None:
        with self._lock:
            with open(filepath, "r") as f:
                data = json.load(f)
            self.projects.clear()
            for pid, pdata in data.items():
                self.projects[pid] = self._reconstruct_project(pdata)

    def _reconstruct_project(self, pdata: dict) -> Project:
        project = Project(
            id=pdata["id"], name=pdata["name"],
            description=pdata["description"], created_at=pdata["created_at"],
        )
        for mdata in pdata.get("milestones", []):
            milestone = Milestone(
                id=mdata["id"], title=mdata["title"],
                description=mdata["description"], deadline=mdata.get("deadline"),
            )
            for tdata in mdata.get("tasks", []):
                task = Task(
                    id=tdata["id"], title=tdata["title"],
                    description=tdata["description"],
                    status=Status(tdata["status"]),
                    priority=Priority(tdata["priority"]),
                    assigned_agent=tdata.get("assigned_agent"),
                    dependencies=tdata.get("dependencies", []),
                    created_at=tdata["created_at"],
                    completed_at=tdata.get("completed_at"),
                )
                for sdata in tdata.get("subtasks", []):
                    task.subtasks.append(Subtask(
                        id=sdata["id"], title=sdata["title"],
                        description=sdata["description"],
                        status=Status(sdata["status"]),
                        assigned_agent=sdata.get("assigned_agent"),
                        created_at=sdata["created_at"],
                        completed_at=sdata.get("completed_at"),
                    ))
                milestone.tasks.append(task)
            project.milestones.append(milestone)
        return project
