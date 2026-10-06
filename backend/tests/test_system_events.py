from sqlalchemy import CheckConstraint

from backend.app.models.system_event import SystemEvent
from backend.app.repositories.system_events import SystemEventRepository


class FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class FakeSession:
    def __init__(self, recent_events=None):
        self.recent_events = recent_events or []
        self.added = []
        self.flush_count = 0

    def add(self, item) -> None:
        self.added.append(item)

    def flush(self) -> None:
        self.flush_count += 1

    def scalars(self, statement):
        return FakeScalarResult(self.recent_events)


def test_system_event_has_allowed_level_constraint() -> None:
    table = SystemEvent.__table__
    constraint_names = {constraint.name for constraint in table.constraints}

    assert "ck_system_events_level" in constraint_names
    assert sum(isinstance(item, CheckConstraint) for item in table.constraints) == 1


def test_repository_records_safe_event() -> None:
    session = FakeSession()
    repository = SystemEventRepository(session)

    event = repository.record(
        component="ingestion",
        level="warning",
        message="PM2.5 data source is temporarily unavailable.",
    )

    assert event.component == "ingestion"
    assert event.level == "warning"
    assert session.added == [event]
    assert session.flush_count == 1


def test_repository_lists_recent_events() -> None:
    event = SystemEvent(
        component="ingestion",
        level="info",
        message="Weather data collection completed.",
    )
    repository = SystemEventRepository(FakeSession(recent_events=[event]))

    assert repository.list_recent() == [event]
