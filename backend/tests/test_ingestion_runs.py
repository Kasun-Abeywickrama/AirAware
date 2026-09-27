from sqlalchemy import CheckConstraint

from backend.app.models.ingestion_run import IngestionRun
from backend.app.repositories.ingestion_runs import IngestionRunRepository


class FakeSession:
    def __init__(self, latest_run=None):
        self.latest_run = latest_run
        self.added = []
        self.flush_count = 0

    def add(self, item) -> None:
        self.added.append(item)

    def flush(self) -> None:
        self.flush_count += 1

    def scalar(self, statement):
        return self.latest_run


def test_ingestion_run_has_source_and_status_constraints() -> None:
    table = IngestionRun.__table__
    constraint_names = {constraint.name for constraint in table.constraints}

    assert "ck_ingestion_runs_source_type" in constraint_names
    assert "ck_ingestion_runs_status" in constraint_names
    assert table.c.status.server_default is not None
    assert sum(isinstance(item, CheckConstraint) for item in table.constraints) == 2


def test_repository_starts_running_pm25_run() -> None:
    session = FakeSession()
    repository = IngestionRunRepository(session)

    run = repository.start("pm25")

    assert run.source_type == "pm25"
    assert run.status == "running"
    assert session.added == [run]
    assert session.flush_count == 1


def test_repository_marks_run_succeeded() -> None:
    session = FakeSession()
    run = IngestionRun(source_type="weather")
    repository = IngestionRunRepository(session)

    result = repository.mark_succeeded(run)

    assert result is run
    assert run.status == "succeeded"
    assert run.completed_at is not None
    assert run.failure_reason is None


def test_repository_marks_run_failed() -> None:
    session = FakeSession()
    run = IngestionRun(source_type="pm25")
    repository = IngestionRunRepository(session)

    result = repository.mark_failed(run, "Provider unavailable")

    assert result is run
    assert run.status == "failed"
    assert run.completed_at is not None
    assert run.failure_reason == "Provider unavailable"


def test_repository_returns_latest_run_for_source_type() -> None:
    latest_run = IngestionRun(source_type="weather")
    repository = IngestionRunRepository(FakeSession(latest_run=latest_run))

    assert repository.get_latest("weather") is latest_run
