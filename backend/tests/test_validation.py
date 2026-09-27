from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from backend.app.services.validation import (
    InputValidationError,
    validate_pm25_input,
    validate_weather_input,
)


NOW = datetime(2026, 9, 27, 10, tzinfo=timezone.utc)


def test_valid_pm25_input_is_normalized() -> None:
    result = validate_pm25_input(
        value_ug_m3="62.4",
        unit="ug/m3",
        observed_at=NOW,
        now=NOW,
    )

    assert result == Decimal("62.4")


@pytest.mark.parametrize(
    ("value", "unit", "observed_at", "message"),
    [
        (-1, "ug/m3", NOW, "cannot be negative"),
        ("NaN", "ug/m3", NOW, "must be finite"),
        (10, "ppm", NOW, "must be ug/m3"),
        (10, "ug/m3", NOW.replace(tzinfo=None), "must include a timezone"),
        (10, "ug/m3", NOW + timedelta(minutes=6), "too far in the future"),
    ],
)
def test_invalid_pm25_input_is_rejected(value, unit, observed_at, message) -> None:
    with pytest.raises(InputValidationError, match=message):
        validate_pm25_input(
            value_ug_m3=value,
            unit=unit,
            observed_at=observed_at,
            now=NOW,
        )


def test_future_weather_input_is_allowed() -> None:
    values = validate_weather_input(
        temperature_c="31.5",
        humidity_percent="72",
        wind_speed_kmh="10.2",
        dew_point_c="25.0",
        surface_pressure_hpa="1004",
        precipitation_mm="0",
        shortwave_radiation_w_m2="500",
        wind_direction_degrees="180",
        valid_at=NOW + timedelta(days=1),
    )

    assert values == (
        Decimal("31.5"), Decimal("72"), Decimal("10.2"), Decimal("25.0"),
        Decimal("1004"), Decimal("0"), Decimal("500"), Decimal("180"),
    )


@pytest.mark.parametrize(
    ("temperature", "humidity", "wind_speed", "valid_at", "message"),
    [
        ("NaN", 72, 10, NOW, "Temperature must be finite"),
        (31, -1, 10, NOW, "Humidity must be between 0 and 100"),
        (31, 101, 10, NOW, "Humidity must be between 0 and 100"),
        (31, 72, -1, NOW, "Wind speed cannot be negative"),
        (31, 72, 10, NOW.replace(tzinfo=None), "must include a timezone"),
    ],
)
def test_invalid_weather_input_is_rejected(
    temperature,
    humidity,
    wind_speed,
    valid_at,
    message,
) -> None:
    with pytest.raises(InputValidationError, match=message):
        validate_weather_input(
            temperature_c=temperature,
            humidity_percent=humidity,
            wind_speed_kmh=wind_speed,
            dew_point_c=25,
            surface_pressure_hpa=1004,
            precipitation_mm=0,
            shortwave_radiation_w_m2=500,
            wind_direction_degrees=180,
            valid_at=valid_at,
        )


@pytest.mark.parametrize(
    ("surface_pressure", "precipitation", "radiation", "wind_direction", "message"),
    [
        (0, 0, 0, 180, "Surface pressure must be positive"),
        (1004, -1, 0, 180, "Precipitation cannot be negative"),
        (1004, 0, -1, 180, "Shortwave radiation cannot be negative"),
        (1004, 0, 0, 361, "Wind direction must be between 0 and 360"),
    ],
)
def test_invalid_model_weather_fields_are_rejected(
    surface_pressure,
    precipitation,
    radiation,
    wind_direction,
    message,
) -> None:
    with pytest.raises(InputValidationError, match=message):
        validate_weather_input(
            temperature_c=31,
            humidity_percent=72,
            wind_speed_kmh=10,
            dew_point_c=25,
            surface_pressure_hpa=surface_pressure,
            precipitation_mm=precipitation,
            shortwave_radiation_w_m2=radiation,
            wind_direction_degrees=wind_direction,
            valid_at=NOW,
        )
