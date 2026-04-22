"""SQLAlchemy declarative base."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base for all ORM models.

    type_annotation_map: `datetime` fields default to TIMESTAMPTZ to match
    the DDL (all timestamp columns are TIMESTAMPTZ in the initial migration).
    """

    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }
