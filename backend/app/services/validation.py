"""
Service: Ingestion Data Validation and Guardrails.

This module provides data sanitization and boundary checks for external provider
data (OpenAQ PM2.5 observations and Open-Meteo weather parameters). It ensures that
corrupted, unphysical, or future-dated records are rejected before entering the database.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation


class InputValidationError(ValueError):
    """Custom exception raised when an incoming data point fails domain validation checks."""


def _finite_decimal(value: Decimal | float | int | str, field_name: str) -> Decimal:
    """
    Convert a value into a finite Decimal instance.

    Rejects strings that cannot be parsed as numbers, as well as NaN and Infinite values.

    Args:
        value: The raw input to parse.
        field_name: Name of the field for descriptive error messaging.

    Returns:
        A valid finite Decimal.

    Raises:
        InputValidationError: If the value is non-numeric, NaN, or infinite.
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise InputValidationError(f"{field_name} must be numeric.") from error

    if not decimal_value.is_finite():
        raise InputValidationError(f"{field_name} must be finite.")

    return decimal_value


def _timezone_aware(value: datetime, field_name: str) -> None:
    """
    Ensure a datetime object contains timezone information.

    Prevents timezone ambiguity errors across UTC and local time offsets.

    Args:
        value: Datetime object to inspect.
        field_name: Field name for descriptive error reporting.

    Raises:
        InputValidationError: If value is naive (lacks timezone info).
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise InputValidationError(f"{field_name} must include a timezone.")


def validate_pm25_input(
    *,
    value_ug_m3: Decimal | float | int | str,
    unit: str,
    observed_at: datetime,
    now: datetime | None = None,
) -> Decimal:
    """
    Validate and normalize an incoming PM2.5 observation.

    Domain Rules:
    1. Unit must be strictly 'ug/m3'.
    2. Observation timestamp must be timezone-aware.
    3. Timestamp cannot be more than 5 minutes in the future (guard against clock skew).
    4. PM2.5 concentration cannot be negative (physical impossibility).

    Args:
        value_ug_m3: PM2.5 measurement value.
        unit: Measurement unit string.
        observed_at: Timestamp when measurement occurred.
        now: Optional current time reference for testing.

    Returns:
        Sanitized Decimal value of PM2.5 concentration.

    Raises:
        InputValidationError: If any validation rule is violated.
    """
    # Guardrail 1: Confirm expected unit
    if unit != "ug/m3":
        raise InputValidationError("PM2.5 unit must be ug/m3.")

    # Guardrail 2: Ensure timezone is present
    _timezone_aware(observed_at, "PM2.5 observation time")

    # Guardrail 3: Reject timestamps too far in the future
    comparison_time = now or datetime.now(timezone.utc)
    _timezone_aware(comparison_time, "Current time")
    if observed_at > comparison_time + timedelta(minutes=5):
        raise InputValidationError("PM2.5 observation time is too far in the future.")

    # Guardrail 4: Non-negative physical constraint
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
    """
    Validate and normalize all 8 meteorological features for a given hour.

    Physical Boundary Rules:
    - Timestamp must be timezone-aware.
    - Humidity: 0% to 100%.
    - Wind speed: >= 0 km/h.
    - Surface pressure: > 0 hPa (atmospheric pressure must be positive).
    - Precipitation: >= 0 mm.
    - Solar radiation: >= 0 W/m2.
    - Wind direction: 0 to 360 degrees.

    Returns:
        Tuple of validated Decimals in canonical order:
        (temp, humidity, wind_speed, dew_point, pressure, precip, radiation, wind_direction)

    Raises:
        InputValidationError: If any physical boundary is violated.
    """
    _timezone_aware(valid_at, "Weather valid time")
    temperature = _finite_decimal(temperature_c, "Temperature")
    humidity = _finite_decimal(humidity_percent, "Humidity")
    wind_speed = _finite_decimal(wind_speed_kmh, "Wind speed")
    dew_point = _finite_decimal(dew_point_c, "Dew point")
    surface_pressure = _finite_decimal(surface_pressure_hpa, "Surface pressure")
    precipitation = _finite_decimal(precipitation_mm, "Precipitation")
    shortwave_radiation = _finite_decimal(shortwave_radiation_w_m2, "Shortwave radiation")
    wind_direction = _finite_decimal(wind_direction_degrees, "Wind direction")

    # Validate physical constraints
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
