"""Validation helpers for future provider ingestion."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation


class InputValidationError(ValueError):
    """Raised when a provider input is not safe to store or use."""


def _finite_decimal(value: Decimal | float | int | str, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise InputValidationError(f"{field_name} must be numeric.") from error

    if not decimal_value.is_finite():
        raise InputValidationError(f"{field_name} must be finite.")

    return decimal_value


def _timezone_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InputValidationError(f"{field_name} must include a timezone.")


def validate_pm25_input(
    *,
    value_ug_m3: Decimal | float | int | str,
    unit: str,
    observed_at: datetime,
    now: datetime | None = None,
) -> Decimal:
    """Validate and normalize one future PM2.5 provider measurement."""
    if unit != "ug/m3":
        raise InputValidationError("PM2.5 unit must be ug/m3.")

    _timezone_aware(observed_at, "PM2.5 observation time")
    comparison_time = now or datetime.now(timezone.utc)
    _timezone_aware(comparison_time, "Current time")
    if observed_at > comparison_time + timedelta(minutes=5):
        raise InputValidationError("PM2.5 observation time is too far in the future.")

    value = _finite_decimal(value_ug_m3, "PM2.5 value")
    if value < 0:
        raise InputValidationError("PM2.5 value cannot be negative.")

    return value


def validate_weather_input(
    *,
    temperature_c: Decimal | float | int | str,
    humidity_percent: Decimal | float | int | str,
    wind_speed_kmh: Decimal | float | int | str,
    dew_point_c: Decimal | float | int | str,
    surface_pressure_hpa: Decimal | float | int | str,
    precipitation_mm: Decimal | float | int | str,
    shortwave_radiation_w_m2: Decimal | float | int | str,
    wind_direction_degrees: Decimal | float | int | str,
    valid_at: datetime,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    """Validate and normalize one future weather provider record."""
    _timezone_aware(valid_at, "Weather valid time")
    temperature = _finite_decimal(temperature_c, "Temperature")
    humidity = _finite_decimal(humidity_percent, "Humidity")
    wind_speed = _finite_decimal(wind_speed_kmh, "Wind speed")
    dew_point = _finite_decimal(dew_point_c, "Dew point")
    surface_pressure = _finite_decimal(surface_pressure_hpa, "Surface pressure")
    precipitation = _finite_decimal(precipitation_mm, "Precipitation")
    shortwave_radiation = _finite_decimal(shortwave_radiation_w_m2, "Shortwave radiation")
    wind_direction = _finite_decimal(wind_direction_degrees, "Wind direction")

    if humidity < 0 or humidity > 100:
        raise InputValidationError("Humidity must be between 0 and 100.")
    if wind_speed < 0:
        raise InputValidationError("Wind speed cannot be negative.")
    if surface_pressure <= 0:
        raise InputValidationError("Surface pressure must be positive.")
    if precipitation < 0:
        raise InputValidationError("Precipitation cannot be negative.")
    if shortwave_radiation < 0:
        raise InputValidationError("Shortwave radiation cannot be negative.")
    if wind_direction < 0 or wind_direction > 360:
        raise InputValidationError("Wind direction must be between 0 and 360 degrees.")

    return (
        temperature,
        humidity,
        wind_speed,
        dew_point,
        surface_pressure,
        precipitation,
        shortwave_radiation,
        wind_direction,
    )
