"""
UPGRADE 6 - HUMAN CHECKPOINT
Flow: PM xong > Hỏi Thiêm > Dev bắt đầu.
Approval step cho các quyết định quan trọng.
"""

import asyncio
import json
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable, Any


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class CheckpointType(str, Enum):
    TASK_APPROVAL = "task_approval"          # PM xong, chờ Thiêm duyệt
    ARCHITECTURE_DECISION = "arch_decision"  # Quyết định kiến trúc quan trọng
    DEPLOY_APPROVAL = "deploy_approval"      # Trước khi deploy
    BUDGET_APPROVAL = "budget_approval"      # Chi phí vượt ngưỡng
    CODE_REVIEW = "code_review"              # Code cần human review


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
    reviewer: str = "Thiem"
    feedback: str = ""
    timeout_seconds: int = 3600  # 1 hour default

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
            "status": self.status.value,
            "reviewer": self.reviewer,
            "feedback": self.feedback,
            "requested_at": self.requested_at,
            "responded_at": self.responded_at,
        }


class HumanApprovalSystem:
    """Hệ thống checkpoint chờ approval từ Thiêm trước khi dev bắt đầu."""

    def __init__(self):
        self.pending_requests: dict[str, ApprovalRequest] = {}
        self.history: list[ApprovalRequest] = []
        self._callbacks: dict[str, Callable] = {}
        self._request_counter = 0

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
    ) -> ApprovalRequest:
        """Tạo checkpoint mới chờ approval."""
        request = ApprovalRequest(
            id=self._next_id(),
            checkpoint_type=checkpoint_type,
            title=title,
            description=description,
            details=details or {},
            timeout_seconds=timeout_seconds,
        )
        self.pending_requests[request.id] = request
        self._notify_pending(request)
        return request

    def _notify_pending(self, request: ApprovalRequest) -> None:
        """Thông báo có request mới cần approval."""
        print(f"\n{'='*60}")
        print(f"🔔 CHECKPOINT: Cần approval từ {request.reviewer}")
        print(f"{'='*60}")
        print(f"ID: {request.id}")
        print(f"Loại: {request.checkpoint_type.value}")
        print(f"Tiêu đề: {request.title}")
        print(f"Mô tả: {request.description}")
        if request.details:
            print(f"Chi tiết: {json.dumps(request.details, indent=2, ensure_ascii=False)}")
        print(f"{'='*60}\n")

    def approve(self, request_id: str, feedback: str = "") -> bool:
        """Approve một request."""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests.pop(request_id)
        request.approve(feedback)
        self.history.append(request)

        # Trigger callback nếu có
        if request_id in self._callbacks:
            self._callbacks.pop(request_id)(request)

        return True

    def reject(self, request_id: str, feedback: str = "") -> bool:
        """Reject một request."""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests.pop(request_id)
        request.reject(feedback)
        self.history.append(request)

        if request_id in self._callbacks:
            self._callbacks.pop(request_id)(request)

        return True

    async def wait_for_approval(
        self,
        request_id: str,
        poll_interval: float = 1.0,
    ) -> ApprovalRequest:
        """Chờ approval (async). Trả về khi có response hoặc timeout."""
        request = self.pending_requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} không tồn tại")

        elapsed = 0.0
        while request.status == ApprovalStatus.PENDING:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            if elapsed >= request.timeout_seconds:
                request.status = ApprovalStatus.TIMEOUT
                self.pending_requests.pop(request_id, None)
                self.history.append(request)
                break

            # Check if already approved/rejected
            if request_id not in self.pending_requests:
                break

        return request

    def on_response(self, request_id: str, callback: Callable) -> None:
        """Đăng ký callback khi có response."""
        self._callbacks[request_id] = callback

    def get_pending(self) -> list[dict]:
        """Lấy danh sách requests đang chờ."""
        return [r.to_dict() for r in self.pending_requests.values()]

    def get_history(self, limit: int = 20) -> list[dict]:
        """Lấy lịch sử approval."""
        return [r.to_dict() for r in self.history[-limit:]]

    def get_stats(self) -> dict:
        """Thống kê approval."""
        approved = sum(1 for r in self.history if r.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for r in self.history if r.status == ApprovalStatus.REJECTED)
        timeout = sum(1 for r in self.history if r.status == ApprovalStatus.TIMEOUT)
        return {
            "pending": len(self.pending_requests),
            "total_processed": len(self.history),
            "approved": approved,
            "rejected": rejected,
            "timeout": timeout,
            "approval_rate": f"{approved / len(self.history) * 100:.1f}%" if self.history else "N/A",
        }


# Convenience function cho flow chính
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
    result = await approval_system.wait_for_approval(request.id)
    return result
