"""
Notification System - Gửi thông báo qua nhiều kênh.
Hỗ trợ: Console, Webhook (Slack/Discord), File log.
"""

import json
import logging
from datetime import datetime
from typing import Optional
from enum import Enum
from dataclasses import dataclass

from src.persistence.database import Database

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    CONSOLE = "console"
    WEBHOOK = "webhook"
    FILE = "file"


class NotificationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


LEVEL_ICONS = {
    NotificationLevel.INFO: "[INFO]",
    NotificationLevel.SUCCESS: "[OK]",
    NotificationLevel.WARNING: "[WARN]",
    NotificationLevel.ERROR: "[ERROR]",
    NotificationLevel.CRITICAL: "[CRITICAL]",
}


@dataclass
class Notification:
    title: str
    message: str
    level: NotificationLevel = NotificationLevel.INFO
    channel: NotificationChannel = NotificationChannel.CONSOLE
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Notifier:
    """Multi-channel notification system."""

    def __init__(
        self,
        db: Optional[Database] = None,
        webhook_url: Optional[str] = None,
        log_file: Optional[str] = None,
    ):
        self.db = db or Database()
        self.webhook_url = webhook_url
        self.log_file = log_file or "./data/notifications.log"
        self._channels: list[NotificationChannel] = [NotificationChannel.CONSOLE]

        if webhook_url:
            self._channels.append(NotificationChannel.WEBHOOK)

    def add_channel(self, channel: NotificationChannel) -> None:
        if channel not in self._channels:
            self._channels.append(channel)

    def notify(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        channels: Optional[list[NotificationChannel]] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Gửi notification qua tất cả channels đã cấu hình."""
        notification = Notification(
            title=title, message=message, level=level, metadata=metadata or {}
        )

        target_channels = channels or self._channels

        for channel in target_channels:
            try:
                if channel == NotificationChannel.CONSOLE:
                    self._send_console(notification)
                elif channel == NotificationChannel.WEBHOOK:
                    self._send_webhook(notification)
                elif channel == NotificationChannel.FILE:
                    self._send_file(notification)

                # Persist to DB
                self.db.log_notification(
                    channel=channel.value,
                    message=f"{title}: {message}",
                    payload=metadata,
                )
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.value}: {e}")

    def _send_console(self, notification: Notification) -> None:
        """Print notification to console."""
        icon = LEVEL_ICONS.get(notification.level, "[INFO]")
        print(f"\n{icon} {notification.title}")
        print(f"  {notification.message}")
        if notification.metadata:
            for k, v in notification.metadata.items():
                print(f"  {k}: {v}")

    def _send_webhook(self, notification: Notification) -> None:
        """Send notification via webhook (Slack/Discord compatible)."""
        if not self.webhook_url:
            return

        import urllib.request
        import urllib.error

        payload = {
            "text": f"{LEVEL_ICONS[notification.level]} *{notification.title}*\n{notification.message}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{LEVEL_ICONS[notification.level]} *{notification.title}*\n{notification.message}",
                    },
                }
            ],
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            logger.info(f"Webhook notification sent: {notification.title}")
        except urllib.error.URLError as e:
            logger.error(f"Webhook failed: {e}")

    def _send_file(self, notification: Notification) -> None:
        """Append notification to log file."""
        import os
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(
                f"[{timestamp}] {notification.level.value.upper()} | "
                f"{notification.title} | {notification.message}\n"
            )

    # ── Convenience methods ────────────────────────────────────

    def pipeline_started(self, project_name: str, task_count: int) -> None:
        self.notify(
            f"Pipeline Started: {project_name}",
            f"Running {task_count} tasks",
            NotificationLevel.INFO,
            metadata={"project": project_name, "tasks": task_count},
        )

    def pipeline_completed(self, project_name: str, duration_seconds: float) -> None:
        self.notify(
            f"Pipeline Completed: {project_name}",
            f"Finished in {duration_seconds:.1f}s",
            NotificationLevel.SUCCESS,
            metadata={"project": project_name, "duration": duration_seconds},
        )

    def pipeline_failed(self, project_name: str, error: str) -> None:
        self.notify(
            f"Pipeline Failed: {project_name}",
            f"Error: {error}",
            NotificationLevel.ERROR,
            metadata={"project": project_name, "error": error},
        )

    def approval_needed(self, request_id: str, title: str) -> None:
        self.notify(
            f"Approval Needed: {title}",
            f"Request ID: {request_id}. Please review and approve/reject.",
            NotificationLevel.WARNING,
            metadata={"request_id": request_id},
        )

    def review_result(self, filename: str, score: float, approved: bool) -> None:
        level = NotificationLevel.SUCCESS if approved else NotificationLevel.WARNING
        self.notify(
            f"Code Review: {filename}",
            f"Score: {score}/10 - {'Approved' if approved else 'Needs Revision'}",
            level,
            metadata={"file": filename, "score": score, "approved": approved},
        )
