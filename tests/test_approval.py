"""Tests for human approval system."""

import os
import pytest
import asyncio
import tempfile
from src.persistence.database import Database
from src.checkpoints.human_approval import (
    HumanApprovalSystem, CheckpointType, ApprovalStatus,
)


@pytest.fixture
def db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Database(db_path=os.path.join(tmpdir, "test.db"))
        yield db
        db.close()


@pytest.fixture
def approval(db):
    return HumanApprovalSystem(db=db)


class TestApprovalSystem:
    def test_create_checkpoint(self, approval):
        req = approval.create_checkpoint(
            CheckpointType.TASK_APPROVAL,
            "Test approval",
            "Please approve",
        )
        assert req.status == ApprovalStatus.PENDING
        assert req.id in approval.pending_requests

    def test_approve(self, approval):
        req = approval.create_checkpoint(
            CheckpointType.TASK_APPROVAL, "Test", "Desc"
        )
        result = approval.approve(req.id, "LGTM")
        assert result is True
        assert req.id not in approval.pending_requests
        assert len(approval.history) == 1
        assert approval.history[0].status == ApprovalStatus.APPROVED

    def test_reject(self, approval):
        req = approval.create_checkpoint(
            CheckpointType.DEPLOY_APPROVAL, "Deploy", "Desc"
        )
        result = approval.reject(req.id, "Not ready")
        assert result is True
        assert approval.history[0].status == ApprovalStatus.REJECTED
        assert approval.history[0].feedback == "Not ready"

    def test_approve_nonexistent(self, approval):
        assert approval.approve("fake_id") is False

    def test_get_pending(self, approval):
        approval.create_checkpoint(CheckpointType.TASK_APPROVAL, "T1", "D1")
        approval.create_checkpoint(CheckpointType.CODE_REVIEW, "T2", "D2")
        pending = approval.get_pending()
        assert len(pending) == 2

    def test_stats(self, approval):
        r1 = approval.create_checkpoint(CheckpointType.TASK_APPROVAL, "T1", "D1")
        r2 = approval.create_checkpoint(CheckpointType.TASK_APPROVAL, "T2", "D2")
        approval.approve(r1.id)
        approval.reject(r2.id, "No")

        stats = approval.get_stats()
        assert stats["approved"] == 1
        assert stats["rejected"] == 1
        assert stats["pending"] == 0

    def test_custom_reviewer(self, approval):
        req = approval.create_checkpoint(
            CheckpointType.TASK_APPROVAL, "Test", "Desc",
            reviewer="Alice",
        )
        assert req.reviewer == "Alice"

    def test_callback_on_approve(self, approval):
        callback_called = [False]

        def on_response(request):
            callback_called[0] = True

        req = approval.create_checkpoint(
            CheckpointType.TASK_APPROVAL, "Test", "Desc"
        )
        approval.on_response(req.id, on_response)
        approval.approve(req.id)
        assert callback_called[0] is True

    def test_timeout(self, approval):
        req = approval.create_checkpoint(
            CheckpointType.TASK_APPROVAL, "Test", "Desc",
            timeout_seconds=1,
        )
        result = asyncio.get_event_loop().run_until_complete(
            approval.wait_for_approval(req.id, poll_interval=0.5)
        )
        assert result.status == ApprovalStatus.TIMEOUT

    def test_persistence_to_db(self, approval, db):
        req = approval.create_checkpoint(
            CheckpointType.TASK_APPROVAL, "Persisted", "Test"
        )
        pending = db.get_pending_approvals()
        assert len(pending) == 1
        assert pending[0]["title"] == "Persisted"
