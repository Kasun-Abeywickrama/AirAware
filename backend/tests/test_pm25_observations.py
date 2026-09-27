from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from backend.app.models.pm25_observation import Pm25Observation
from backend.app.repositories.pm25_observations import Pm25ObservationRepository


LOCATION_ID = UUID("00000000-0000-0000-0000-000000000010")
INGESTION_RUN_ID = UUID("00000000-0000-0000-0000-000000000020")


class FakeSession:
    def __init__(self, latest_observation=None):
        self.latest_observation = latest_observation
        self.added = []
        self.flush_count = 0

    def add(self, item) -> None:
        self.added.append(item)

    def flush(self) -> None:
        self.flush_count += 1

    def scalar(self, statement):
        return self.latest_observation


def test_pm25_observation_has_required_constraints() -> None:
    table = Pm25Observation.__table__
    constraint_names = {constraint.name for constraint in table.constraints}

    assert "uq_pm25_observations_location_observed_at" in constraint_names
    assert "ck_pm25_observations_non_negative_value" in constraint_names
    assert "ck_pm25_observations_unit" in constraint_names
    assert sum(isinstance(item, ForeignKeyConstraint) for item in table.constraints) == 2
    assert sum(isinstance(item, UniqueConstraint) for item in table.constraints) == 1
    assert sum(isinstance(item, CheckConstraint) for item in table.constraints) == 2
    assert table.c.unit.server_default is not None


def test_repository_creates_approved_observation() -> None:
    session = FakeSession()
    repository = Pm25ObservationRepository(session)
    observed_at = datetime(2026, 9, 27, 10, tzinfo=timezone.utc)

    observation = repository.create_approved(
        location_id=LOCATION_ID,
        ingestion_run_id=INGESTION_RUN_ID,
        observed_at=observed_at,
        value_ug_m3=Decimal("62.40"),
    )

    assert observation.location_id == LOCATION_ID
    assert observation.ingestion_run_id == INGESTION_RUN_ID
    assert observation.observed_at == observed_at
    assert observation.value_ug_m3 == Decimal("62.40")
    assert observation.unit == "ug/m3"
    assert session.added == [observation]
    assert session.flush_count == 1


def test_repository_returns_latest_observation_for_location() -> None:
    latest_observation = Pm25Observation(
        location_id=LOCATION_ID,
        ingestion_run_id=INGESTION_RUN_ID,
        observed_at=datetime(2026, 9, 27, 10, tzinfo=timezone.utc),
        value_ug_m3=Decimal("62.40"),
        unit="ug/m3",
    )
    repository = Pm25ObservationRepository(
        FakeSession(latest_observation=latest_observation)
    )

    assert repository.get_latest_for_location(LOCATION_ID) is latest_observation
