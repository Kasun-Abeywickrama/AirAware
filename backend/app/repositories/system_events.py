"""Queries for safe operational system events."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.system_event import SystemEvent


class SystemEventRepository:
    """Record concise operational events for later administration."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, *, component: str, level: str, message: str) -> SystemEvent:
        """Store a caller-supplied safe event message."""
        event = SystemEvent(component=component, level=level, message=message)
        self._session.add(event)
        self._session.flush()
        return event

    def list_recent(self, limit: int = 20) -> list[SystemEvent]:
        """Return recent events in newest-first order."""
        statement = select(SystemEvent).order_by(SystemEvent.created_at.desc()).limit(limit)
        return list(self._session.scalars(statement).all())
