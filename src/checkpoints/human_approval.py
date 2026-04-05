"""
UPGRADE 6 - HUMAN CHECKPOINT (v2 - with persistence)
Flow: PM xong > Hỏi Thiêm > Dev bắt đầu.
Approval step cho các quyết định quan trọng.
"""

import asyncio
import json
import logging
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable

from src.persistence.database import Database
from src import config

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class CheckpointType(str, Enum):
    TASK_APPROVAL = "task_approval"
    ARCHITECTURE_DECISION = "arch_decision"
    DEPLOY_APPROVAL = "deploy_approval"
    BUDGET_APPROVAL = "budget_approval"
    CODE_REVIEW = "code_review"


@dataclass
class ApprovalRequest:
    id: str
    checkpoint_type: CheckpointType
    title: str
    description: str
    details: dict = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: str = field(default_factory=lambda: datetime.now().isoformat())
    responded_at: Optional[str] = None
    reviewer: str = ""
    feedback: str = ""
    timeout_seconds: int = 0

    def __post_init__(self):
        if not self.reviewer:
            self.reviewer = config.DEFAULT_REVIEWER
        if not self.timeout_seconds:
            self.timeout_seconds = config.APPROVAL_TIMEOUT

    def approve(self, feedback: str = "") -> None:
        self.status = ApprovalStatus.APPROVED
        self.responded_at = datetime.now().isoformat()
        self.feedback = feedback

    def reject(self, feedback: str = "") -> None:
        self.status = ApprovalStatus.REJECTED
        self.responded_at = datetime.now().isoformat()
        self.feedback = feedback

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.checkpoint_type.value,
            "title": self.title,
            "description": self.description,
            "details": self.details,
            "status": self.status.value,
            "reviewer": self.reviewer,
            "feedback": self.feedback,
            "requested_at": self.requested_at,
            "responded_at": self.responded_at,
            "timeout_seconds": self.timeout_seconds,
        }


class HumanApprovalSystem:
    """Hệ thống checkpoint chờ approval từ Thiêm trước khi dev bắt đầu."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.pending_requests: dict[str, ApprovalRequest] = {}
        self.history: list[ApprovalRequest] = []
        self._callbacks: dict[str, Callable] = {}
        self._request_counter = 0
        self._lock = asyncio.Lock()

    def _next_id(self) -> str:
        self._request_counter += 1
        return f"approval_{self._request_counter:04d}"

    def create_checkpoint(
        self,
        checkpoint_type: CheckpointType,
        title: str,
        description: str,
        details: Optional[dict] = None,
        timeout_seconds: int = 3600,
        reviewer: str = "Thiem",
    ) -> ApprovalRequest:
        """Tạo checkpoint mới chờ approval."""
        request = ApprovalRequest(
            id=self._next_id(),
            checkpoint_type=checkpoint_type,
            title=title,
            description=description,
            details=details or {},
            timeout_seconds=timeout_seconds,
            reviewer=reviewer,
        )
        self.pending_requests[request.id] = request

        # Persist to DB
        try:
            self.db.save_approval(request.to_dict())
        except Exception as e:
            logger.error(f"Failed to persist approval {request.id}: {e}")

        self._notify_pending(request)
        return request

    def _notify_pending(self, request: ApprovalRequest) -> None:
        """Thông báo có request mới cần approval."""
        logger.info(
            f"CHECKPOINT [{request.checkpoint_type.value}] "
            f"'{request.title}' - waiting for {request.reviewer}"
        )
        print(f"\n{'='*60}")
        print(f"CHECKPOINT: Can approval tu {request.reviewer}")
        print(f"{'='*60}")
        print(f"ID: {request.id}")
        print(f"Loai: {request.checkpoint_type.value}")
        print(f"Tieu de: {request.title}")
        print(f"Mo ta: {request.description}")
        if request.details:
            print(f"Chi tiet: {json.dumps(request.details, indent=2, ensure_ascii=False)}")
        print(f"{'='*60}\n")

    def approve(self, request_id: str, feedback: str = "") -> bool:
        """Approve một request."""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests.pop(request_id)
        request.approve(feedback)
        self.history.append(request)

        try:
            self.db.update_approval_status(request_id, "approved", feedback)
        except Exception as e:
            logger.error(f"Failed to persist approval status: {e}")

        if request_id in self._callbacks:
            try:
                self._callbacks.pop(request_id)(request)
            except Exception as e:
                logger.error(f"Approval callback failed: {e}")

        return True

    def reject(self, request_id: str, feedback: str = "") -> bool:
        """Reject một request."""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests.pop(request_id)
        request.reject(feedback)
        self.history.append(request)

        try:
            self.db.update_approval_status(request_id, "rejected", feedback)
        except Exception as e:
            logger.error(f"Failed to persist rejection status: {e}")

        if request_id in self._callbacks:
            try:
                self._callbacks.pop(request_id)(request)
            except Exception as e:
                logger.error(f"Rejection callback failed: {e}")

        return True

    async def wait_for_approval(
        self,
        request_id: str,
        poll_interval: float = 2.0,
    ) -> ApprovalRequest:
        """Chờ approval (async). Trả về khi có response hoặc timeout."""
        request = self.pending_requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} khong ton tai")

        elapsed = 0.0
        while request.status == ApprovalStatus.PENDING:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            if elapsed >= request.timeout_seconds:
                request.status = ApprovalStatus.TIMEOUT
                self.pending_requests.pop(request_id, None)
                self.history.append(request)
                try:
                    self.db.update_approval_status(request_id, "timeout")
                except Exception as e:
                    logger.error(f"Failed to persist timeout status: {e}")
                break
            if request_id not in self.pending_requests:
                break

        return request

    def on_response(self, request_id: str, callback: Callable) -> None:
        self._callbacks[request_id] = callback

    def get_pending(self) -> list[dict]:
        return [r.to_dict() for r in self.pending_requests.values()]

    def get_history(self, limit: int = 20) -> list[dict]:
        # Try DB first, fallback to in-memory
        try:
            return self.db.get_approval_history(limit)
        except Exception:
            return [r.to_dict() for r in self.history[-limit:]]

    def get_stats(self) -> dict:
        all_records = self.history
        approved = sum(1 for r in all_records if r.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for r in all_records if r.status == ApprovalStatus.REJECTED)
        timeout = sum(1 for r in all_records if r.status == ApprovalStatus.TIMEOUT)
        return {
            "pending": len(self.pending_requests),
            "total_processed": len(all_records),
            "approved": approved,
            "rejected": rejected,
            "timeout": timeout,
            "approval_rate": f"{approved / len(all_records) * 100:.1f}%" if all_records else "N/A",
        }


async def require_approval(
    approval_system: HumanApprovalSystem,
    title: str,
    description: str,
    checkpoint_type: CheckpointType = CheckpointType.TASK_APPROVAL,
    details: Optional[dict] = None,
) -> ApprovalRequest:
    """Helper: tạo checkpoint và chờ approval."""
    request = approval_system.create_checkpoint(
        checkpoint_type=checkpoint_type,
        title=title,
        description=description,
        details=details,
    )
    return await approval_system.wait_for_approval(request.id)
