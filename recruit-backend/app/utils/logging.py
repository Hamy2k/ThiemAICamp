"""Structured JSON logging to stdout."""
from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(level: str = "INFO") -> None:
    """Install root JSON formatter. Idempotent."""
    root = logging.getLogger()
    if getattr(root, "_json_configured", False):
        return
    root.setLevel(level.upper())
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d",
        rename_fields={"asctime": "ts", "levelname": "level"},
    )
    handler.setFormatter(fmt)
    root.addHandler(handler)
    root._json_configured = True  # type: ignore[attr-defined]
