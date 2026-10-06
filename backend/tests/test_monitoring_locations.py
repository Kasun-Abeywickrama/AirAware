from sqlalchemy import CheckConstraint, UniqueConstraint

from backend.app.models.monitoring_location import MonitoringLocation
from backend.app.repositories.monitoring_locations import MonitoringLocationRepository


class FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class FakeSession:
    def __init__(self, location=None, active_locations=None):
        self.location = location
        self.active_locations = active_locations or []

    def scalar(self, statement):
        return self.location

    def scalars(self, statement):
        return FakeScalarResult(self.active_locations)


def test_monitoring_location_has_required_constraints() -> None:
    table = MonitoringLocation.__table__
    constraint_names = {constraint.name for constraint in table.constraints}

    assert "uq_monitoring_locations_provider_location" in constraint_names
    assert "ck_monitoring_locations_latitude_range" in constraint_names
    assert "ck_monitoring_locations_longitude_range" in constraint_names
    assert table.c.active.server_default is not None

    assert any(isinstance(item, UniqueConstraint) for item in table.constraints)
    assert sum(isinstance(item, CheckConstraint) for item in table.constraints) == 2


def test_repository_finds_matching_location() -> None:
    location = MonitoringLocation(
        name="Example Station",
        provider="example-provider",
        provider_location_id="station-1",
        latitude=28.6,
        longitude=77.2,
        timezone="Asia/Kolkata",
    )
    repository = MonitoringLocationRepository(FakeSession(location=location))

    result = repository.get_by_provider_location_id("example-provider", "station-1")

    assert result is location


def test_repository_returns_none_for_unknown_location() -> None:
    repository = MonitoringLocationRepository(FakeSession())

    result = repository.get_by_provider_location_id("example-provider", "missing")

    assert result is None


def test_repository_lists_active_locations() -> None:
    first = MonitoringLocation(
        name="First Station",
        provider="example-provider",
        provider_location_id="station-1",
        latitude=28.6,
        longitude=77.2,
        timezone="Asia/Kolkata",
    )
    second = MonitoringLocation(
        name="Second Station",
        provider="example-provider",
        provider_location_id="station-2",
        latitude=28.7,
        longitude=77.3,
        timezone="Asia/Kolkata",
    )
    repository = MonitoringLocationRepository(FakeSession(active_locations=[first, second]))

    assert repository.list_active() == [first, second]
