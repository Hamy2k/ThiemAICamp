"""
Persistence Layer - SQLite backend cho toàn bộ ThiemAICamp.
Lưu trữ: approvals, metrics, task state, execution logs.
"""

import os
import json
import sqlite3
import threading
from datetime import datetime
from typing import Optional, Any
from contextlib import contextmanager


class Database:
    """Thread-safe SQLite persistence layer."""

    def __init__(self, db_path: str = "./data/thiemaicamp.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    @contextmanager
    def transaction(self):
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_schema(self):
        with self.transaction() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    checkpoint_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    details TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'pending',
                    reviewer TEXT DEFAULT 'Thiem',
                    feedback TEXT DEFAULT '',
                    requested_at TEXT NOT NULL,
                    responded_at TEXT,
                    timeout_seconds INTEGER DEFAULT 3600
                );

                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    start_time REAL,
                    end_time REAL,
                    duration_seconds REAL DEFAULT 0,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    error TEXT,
                    status TEXT DEFAULT 'pending',
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS task_state (
                    id TEXT PRIMARY KEY,
                    project_data TEXT NOT NULL,
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    agent_role TEXT,
                    action TEXT NOT NULL,
                    input_data TEXT DEFAULT '',
                    output_data TEXT DEFAULT '',
                    files_changed TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'pending',
                    error TEXT,
                    started_at TEXT DEFAULT (datetime('now')),
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload TEXT DEFAULT '{}',
                    sent_at TEXT DEFAULT (datetime('now')),
                    status TEXT DEFAULT 'sent'
                );

                CREATE INDEX IF NOT EXISTS idx_metrics_agent ON metrics(agent_name);
                CREATE INDEX IF NOT EXISTS idx_metrics_task ON metrics(task_id);
                CREATE INDEX IF NOT EXISTS idx_execution_run ON execution_logs(run_id);
                CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
            """)

    # ── Approvals ──────────────────────────────────────────────

    def save_approval(self, approval: dict) -> None:
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO approvals
                (id, checkpoint_type, title, description, details, status,
                 reviewer, feedback, requested_at, responded_at, timeout_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                approval["id"],
                approval["type"],
                approval["title"],
                approval.get("description", ""),
                json.dumps(approval.get("details", {})),
                approval["status"],
                approval.get("reviewer", "Thiem"),
                approval.get("feedback", ""),
                approval["requested_at"],
                approval.get("responded_at"),
                approval.get("timeout_seconds", 3600),
            ))

    def get_pending_approvals(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM approvals WHERE status = 'pending' ORDER BY requested_at"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_approval_history(self, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM approvals WHERE status != 'pending' ORDER BY responded_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_approval_status(self, approval_id: str, status: str, feedback: str = "") -> None:
        with self.transaction() as conn:
            conn.execute(
                "UPDATE approvals SET status=?, feedback=?, responded_at=? WHERE id=?",
                (status, feedback, datetime.now().isoformat(), approval_id)
            )

    # ── Metrics ────────────────────────────────────────────────

    def save_metric(self, metric: dict) -> int:
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO metrics
                (agent_name, task_id, start_time, end_time, duration_seconds,
                 input_tokens, output_tokens, total_tokens, error, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric["agent_name"],
                metric["task_id"],
                metric.get("start_time", 0),
                metric.get("end_time", 0),
                metric.get("duration_seconds", 0),
                metric.get("input_tokens", 0),
                metric.get("output_tokens", 0),
                metric.get("total_tokens", 0),
                metric.get("error"),
                metric.get("status", "pending"),
                json.dumps(metric.get("metadata", {})),
            ))
            return cursor.lastrowid

    def get_metrics_summary(self) -> dict:
        conn = self._get_conn()
        row = conn.execute("""
            SELECT
                COUNT(*) as total_runs,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as errors,
                SUM(total_tokens) as total_tokens,
                SUM(duration_seconds) as total_duration,
                AVG(duration_seconds) as avg_duration
            FROM metrics
        """).fetchone()
        return dict(row) if row else {}

    def get_agent_metrics(self, agent_name: str, limit: int = 100) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM metrics WHERE agent_name=? ORDER BY created_at DESC LIMIT ?",
            (agent_name, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Task State ─────────────────────────────────────────────

    def save_task_state(self, project_id: str, project_data: dict) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO task_state (id, project_data, updated_at) VALUES (?, ?, ?)",
                (project_id, json.dumps(project_data, default=str), datetime.now().isoformat())
            )

    def load_task_state(self, project_id: str) -> Optional[dict]:
        conn = self._get_conn()
        row = conn.execute("SELECT project_data FROM task_state WHERE id=?", (project_id,)).fetchone()
        return json.loads(row["project_data"]) if row else None

    def list_projects(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT id, updated_at FROM task_state ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

    # ── Execution Logs ─────────────────────────────────────────

    def log_execution(self, run_id: str, agent_role: str, action: str,
                      input_data: str = "", output_data: str = "",
                      files_changed: list[str] = None, status: str = "running",
                      error: str = None) -> int:
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO execution_logs
                (run_id, agent_role, action, input_data, output_data, files_changed, status, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id, agent_role, action, input_data, output_data,
                json.dumps(files_changed or []), status, error
            ))
            return cursor.lastrowid

    def update_execution_log(self, log_id: int, status: str,
                             output_data: str = "", error: str = None,
                             files_changed: list[str] = None) -> None:
        with self.transaction() as conn:
            conn.execute("""
                UPDATE execution_logs
                SET status=?, output_data=?, error=?, files_changed=?, completed_at=?
                WHERE id=?
            """, (status, output_data, error,
                  json.dumps(files_changed or []),
                  datetime.now().isoformat(), log_id))

    def get_execution_logs(self, run_id: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM execution_logs WHERE run_id=? ORDER BY started_at",
            (run_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Notifications ──────────────────────────────────────────

    def log_notification(self, channel: str, message: str, payload: dict = None) -> None:
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO notifications (channel, message, payload) VALUES (?, ?, ?)",
                (channel, message, json.dumps(payload or {}))
            )

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
