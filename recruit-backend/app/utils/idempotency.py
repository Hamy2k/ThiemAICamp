"""In-memory idempotency store for MVP.

Production: replace with Redis. Key = sha256(phone + job_id + window_bucket).
"""
from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass


@dataclass
class _Entry:
    value: str
    expires_at: float


class IdempotencyStore:
    """Simple TTL map keyed by fingerprint."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._store: dict[str, _Entry] = {}

    def _gc(self) -> None:
        now = time.time()
        expired = [k for k, e in self._store.items() if e.expires_at < now]
        for k in expired:
            self._store.pop(k, None)

    def get(self, key: str) -> str | None:
        with self._lock:
            self._gc()
            entry = self._store.get(key)
            if entry is None or entry.expires_at < time.time():
                return None
            return entry.value

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._store[key] = _Entry(value=value, expires_at=time.time() + self._ttl)


def fingerprint(phone_e164: str, job_id: str) -> str:
    raw = f"{phone_e164}|{job_id}".encode()
    return hashlib.sha256(raw).hexdigest()


_singleton: IdempotencyStore | None = None


def get_store(ttl_seconds: int = 600) -> IdempotencyStore:
    global _singleton
    if _singleton is None:
        _singleton = IdempotencyStore(ttl_seconds=ttl_seconds)
    return _singleton
