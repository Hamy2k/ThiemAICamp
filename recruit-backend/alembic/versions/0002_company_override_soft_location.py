"""Add jobs.company_name_override + allow soft location

Revision ID: 0002_company_override
Revises: 0001_initial
Create Date: 2026-04-22
"""
from __future__ import annotations

from alembic import op


revision = "0002_company_override"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_name_override TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS company_name_override")
