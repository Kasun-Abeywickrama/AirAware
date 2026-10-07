"""
Database Repository: System Events.

This module handles recording and querying operational system logs and audit events,
such as ingestion job failures, forecast runs, or background worker status.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.system_event import SystemEvent


class SystemEventRepository:
    """Repository class to persist and retrieve operational system events."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with an active database session."""
        self._session = session

    def record(self, *, component: str, level: str, message: str) -> SystemEvent:
        """
        Record a new operational system event.

        Args:
            component: Name of the subsystem (e.g., 'ingestion', 'forecasting', 'scheduler').
            level: Severity level (e.g., 'INFO', 'WARNING', 'ERROR').
            message: Descriptive, sanitized status or error message.

        Returns:
            The newly created SystemEvent record.
        """
        event = SystemEvent(component=component, level=level, message=message)
        self._session.add(event)
        self._session.flush()
        return event

    def list_recent(self, limit: int = 20) -> list[SystemEvent]:
        """
        Retrieve recent system events in reverse chronological order (newest first).

        Args:
            limit: Maximum number of events to fetch (default: 20).

        Returns:
            List of recent SystemEvent instances.
        """
        statement = select(SystemEvent).order_by(SystemEvent.created_at.desc()).limit(limit)
        return list(self._session.scalars(statement).all())
