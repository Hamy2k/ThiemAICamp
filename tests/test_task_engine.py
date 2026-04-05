"""Tests for task engine."""

import os
import json
import pytest
import tempfile
from src.persistence.database import Database
from src.engine.task_engine import (
    TaskEngine, Project, Milestone, Task, Subtask,
    Status, Priority,
)


@pytest.fixture
def db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(db_path=os.path.join(tmpdir, "test.db"))
        yield db
        db.close()


@pytest.fixture
def engine(db):
    return TaskEngine(db=db)


class TestProjectHierarchy:
    def test_create_project(self, engine):
        project = engine.create_project("Test Project", "A test")
        assert project.name == "Test Project"
        assert project.id in engine.projects

    def test_add_milestone(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP", deadline="2025-06-01")
        assert len(project.milestones) == 1
        assert m.deadline == "2025-06-01"

    def test_add_task_with_subtasks(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        task = m.add_task("Build API", priority=Priority.HIGH)
        task.add_subtask("Setup routes")
        task.add_subtask("Add validation")
        assert len(task.subtasks) == 2

    def test_progress_calculation(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        t1 = m.add_task("Task 1")
        t2 = m.add_task("Task 2")
        assert project.progress() == 0.0

        t1.complete()
        assert m.progress() == 0.5
        assert project.progress() == 0.5

        t2.complete()
        assert project.progress() == 1.0


class TestTaskAssignment:
    def test_get_next_task_by_priority(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        low = m.add_task("Low task", priority=Priority.LOW)
        high = m.add_task("High task", priority=Priority.HIGH)

        task = engine.get_next_task("agent_1")
        assert task.id == high.id
        assert task.status == Status.IN_PROGRESS

    def test_dependency_blocking(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        t1 = m.add_task("First", priority=Priority.HIGH)
        t2 = m.add_task("Second", priority=Priority.CRITICAL)
        t2.dependencies = [t1.id]

        # t2 is CRITICAL but blocked by t1
        task = engine.get_next_task("agent_1")
        assert task.id == t1.id

    def test_cross_milestone_deps(self, engine):
        project = engine.create_project("P1")
        m1 = project.add_milestone("Phase 1")
        m2 = project.add_milestone("Phase 2")
        t1 = m1.add_task("Setup DB", priority=Priority.HIGH)
        t2 = m2.add_task("Build API", priority=Priority.CRITICAL)
        t2.dependencies = [t1.id]

        # t2 blocked by t1 across milestones
        task = engine.get_next_task("agent_1")
        assert task.id == t1.id

    def test_complete_unblocks_dependent(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        t1 = m.add_task("First", priority=Priority.HIGH)
        t2 = m.add_task("Second", priority=Priority.CRITICAL)
        t2.dependencies = [t1.id]

        engine.get_next_task("agent_1")  # gets t1
        engine.complete_task(t1.id)

        task = engine.get_next_task("agent_2")
        assert task.id == t2.id

    def test_no_double_assignment(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        m.add_task("Only task", priority=Priority.HIGH)

        t1 = engine.get_next_task("agent_1")
        t2 = engine.get_next_task("agent_2")  # No more tasks
        assert t1 is not None
        assert t2 is None

    def test_agent_gets_existing_task(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        m.add_task("Task", priority=Priority.HIGH)

        t1 = engine.get_next_task("agent_1")
        t2 = engine.get_next_task("agent_1")  # Same agent, returns same task
        assert t1.id == t2.id


class TestTaskOperations:
    def test_fail_task(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        t = m.add_task("Task")
        t.status = Status.IN_PROGRESS
        engine.fail_task(t.id, "timeout")
        assert t.status == Status.FAILED

    def test_reassign_task(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("MVP")
        t = m.add_task("Task")
        t.status = Status.IN_PROGRESS
        t.assigned_agent = "agent_1"

        engine.reassign_task(t.id, "agent_2")
        assert t.assigned_agent == "agent_2"
        assert t.status == Status.IN_PROGRESS


class TestPersistence:
    def test_save_and_load_file(self, engine):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            filepath = f.name

        try:
            project = engine.create_project("P1", "Test project")
            m = project.add_milestone("MVP")
            t = m.add_task("Task 1", priority=Priority.HIGH)
            t.add_subtask("Subtask 1")

            engine.save_to_file(filepath)

            engine2 = TaskEngine()
            engine2.load_from_file(filepath)

            loaded = list(engine2.projects.values())[0]
            assert loaded.name == "P1"
            assert len(loaded.milestones) == 1
            assert len(loaded.milestones[0].tasks) == 1
            assert len(loaded.milestones[0].tasks[0].subtasks) == 1
        finally:
            os.unlink(filepath)

    def test_milestone_overdue(self, engine):
        project = engine.create_project("P1")
        m = project.add_milestone("Past", deadline="2020-01-01")
        assert m.is_overdue is True

        m2 = project.add_milestone("Future", deadline="2099-01-01")
        assert m2.is_overdue is False
