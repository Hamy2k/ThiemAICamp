"""
UPGRADE 2 - TASK ENGINE
Quản lý hierarchy: Project > Milestones > Tasks > Subtasks.
Mỗi agent chỉ nhận 1 task nhỏ tại một thời điểm.
"""

import uuid
import json
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional


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


class TaskEngine:
    """Quản lý toàn bộ project hierarchy và phân phối tasks cho agents."""

    def __init__(self):
        self.projects: dict[str, Project] = {}

    def create_project(self, name: str, description: str = "") -> Project:
        project = Project(name=name, description=description)
        self.projects[project.id] = project
        return project

    def get_next_task(self, agent_id: str) -> Optional[Task]:
        """Lấy task tiếp theo cho agent. Mỗi agent chỉ nhận 1 task."""
        # Ưu tiên: critical > high > medium > low
        priority_order = [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]

        for priority in priority_order:
            for project in self.projects.values():
                for milestone in project.milestones:
                    for task in milestone.tasks:
                        if task.status == Status.PENDING and task.priority == priority:
                            # Kiểm tra dependencies
                            if self._dependencies_met(task, milestone):
                                task.status = Status.IN_PROGRESS
                                task.assigned_agent = agent_id
                                return task
        return None

    def _dependencies_met(self, task: Task, milestone: Milestone) -> bool:
        """Kiểm tra tất cả dependencies đã hoàn thành chưa."""
        for dep_id in task.dependencies:
            dep_task = next((t for t in milestone.tasks if t.id == dep_id), None)
            if dep_task and dep_task.status != Status.COMPLETED:
                return False
        return True

    def complete_task(self, task_id: str) -> bool:
        """Đánh dấu task là hoàn thành."""
        for project in self.projects.values():
            for milestone in project.milestones:
                for task in milestone.tasks:
                    if task.id == task_id:
                        task.complete()
                        return True
        return False

    def get_project_summary(self, project_id: str) -> dict:
        """Lấy tổng quan tiến độ project."""
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
                }
                for m in project.milestones
            ],
        }

    def save_to_file(self, filepath: str) -> None:
        """Lưu trạng thái vào file JSON."""
        data = {}
        for pid, project in self.projects.items():
            data[pid] = asdict(project)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_from_file(self, filepath: str) -> None:
        """Load trạng thái từ file JSON."""
        with open(filepath, "r") as f:
            data = json.load(f)
        # Reconstruct projects from saved data
        self.projects.clear()
        for pid, pdata in data.items():
            project = Project(
                id=pdata["id"],
                name=pdata["name"],
                description=pdata["description"],
                created_at=pdata["created_at"],
            )
            for mdata in pdata.get("milestones", []):
                milestone = Milestone(
                    id=mdata["id"],
                    title=mdata["title"],
                    description=mdata["description"],
                    deadline=mdata.get("deadline"),
                )
                for tdata in mdata.get("tasks", []):
                    task = Task(
                        id=tdata["id"],
                        title=tdata["title"],
                        description=tdata["description"],
                        status=Status(tdata["status"]),
                        priority=Priority(tdata["priority"]),
                        assigned_agent=tdata.get("assigned_agent"),
                        dependencies=tdata.get("dependencies", []),
                        created_at=tdata["created_at"],
                        completed_at=tdata.get("completed_at"),
                    )
                    for sdata in tdata.get("subtasks", []):
                        subtask = Subtask(
                            id=sdata["id"],
                            title=sdata["title"],
                            description=sdata["description"],
                            status=Status(sdata["status"]),
                            assigned_agent=sdata.get("assigned_agent"),
                            created_at=sdata["created_at"],
                            completed_at=sdata.get("completed_at"),
                        )
                        task.subtasks.append(subtask)
                    milestone.tasks.append(task)
                project.milestones.append(milestone)
            self.projects[pid] = project
