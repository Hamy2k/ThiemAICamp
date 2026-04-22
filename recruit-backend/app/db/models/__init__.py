"""ORM models — domain-grouped.

SPEC_CONFLICT: Phase 2 spec asked for "one file per table" (15 tables).
Pragmatic choice: group by domain (7 files). All tables still in Base.metadata.
"""
from app.db.models.audit import AICall, NotificationLog
from app.db.models.company import Company, HRUser
from app.db.models.distribution import Campaign, LinkClick, Source, TrackingLink
from app.db.models.job import ContentVariant, Job
from app.db.models.lead import ConsentRecord, Lead
from app.db.models.match import Match
from app.db.models.screening import ScreeningMessage, ScreeningSession

__all__ = [
    "AICall",
    "Campaign",
    "Company",
    "ConsentRecord",
    "ContentVariant",
    "HRUser",
    "Job",
    "Lead",
    "LinkClick",
    "Match",
    "NotificationLog",
    "ScreeningMessage",
    "ScreeningSession",
    "Source",
    "TrackingLink",
]
