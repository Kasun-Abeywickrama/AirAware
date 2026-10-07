"""External API adapters for live PM2.5 observations and weather data.

Integrates with:
1. OpenAQ REST API v3 - Ground-truth hourly PM2.5 readings for Delhi.
2. Open-Meteo Weather API - Hourly weather variables (temperature, humidity, wind, radiation).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx

from .config import Settings


class ProviderError(RuntimeError):
    """Custom exception raised when an external API call fails or returns invalid data.

    Allows workers to catch external API issues safely without crashing the service.
    """


@dataclass(frozen=True)
class Pm25Reading:
    """Standardized PM2.5 observation data structure."""

    observed_at: datetime  # UTC timestamp when the measurement was recorded
    value_ug_m3: Decimal   # PM2.5 concentration in micrograms per cubic meter (µg/m³)
    unit: str              # Standardized unit string ('ug/m3')


@dataclass(frozen=True)
class WeatherReading:
    """Standardized meteorological reading data structure."""

    valid_at: datetime                   # UTC timestamp for which weather conditions apply
    temperature_c: Decimal              # 2-meter air temperature in Celsius (°C)
    humidity_percent: Decimal           # 2-meter relative humidity percentage (0-100%)
    wind_speed_kmh: Decimal             # 10-meter wind speed in kilometers per hour (km/h)
    dew_point_c: Decimal                # 2-meter dew point temperature in Celsius (°C)
    surface_pressure_hpa: Decimal       # Atmospheric surface pressure in hectopascals (hPa)
    precipitation_mm: Decimal           # Total hourly precipitation in millimeters (mm)
    shortwave_radiation_w_m2: Decimal   # Direct & diffuse solar radiation in Watts/m² (W/m²)
    wind_direction_degrees: Decimal     # Wind direction in degrees (0-360°)


class OpenAQAdapter:
    """HTTP client adapter to query the OpenAQ REST API (v3)."""

    base_url = "https://api.openaq.org/v3"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def latest_pm25(self) -> Pm25Reading:
        """Fetch the most recent PM2.5 reading from the configured station."""
        # 1. Ensure API key is configured
        if not self._settings.openaq_api_key:
            raise ProviderError("OpenAQ is not configured.")

        try:
            with httpx.Client(timeout=self._settings.provider_timeout_seconds) as client:
                # Retrieve sensor canonical unit (e.g., 'ug/m3')
                canonical_unit = self._configured_pm25_unit(client)

                # Query latest measurements for the configured OpenAQ location
                response = client.get(
                    f"{self.base_url}/locations/{self._settings.openaq_location_id}/latest",
                    headers={"X-API-Key": self._settings.openaq_api_key},
                    params={"limit": 100},
                )
        except httpx.HTTPError as error:
            raise ProviderError("OpenAQ request failed.") from error

        if response.status_code != 200:
            raise ProviderError("OpenAQ returned an unavailable response.")

        # 2. Locate the specific PM2.5 sensor ID in the response list
        results = response.json().get("results", [])
        item = next(
            (
                result
                for result in results
                if int(result.get("sensorsId", result.get("sensorId", -1)))
                == self._settings.openaq_sensor_id
            ),
            None,
        )
        if item is None:
            raise ProviderError("OpenAQ did not return the configured PM2.5 sensor.")

        # 3. Extract observation value and UTC timestamp
        value = item.get("value")
        if isinstance(value, dict):
            value = value.get("value")
        observed_at = item.get("datetime", {}).get("utc")
        if value is None or not observed_at:
            raise ProviderError("OpenAQ returned an incomplete PM2.5 reading.")

        # 4. Parse timestamp and cast value to high-precision Decimal
        try:
            timestamp = datetime.fromisoformat(str(observed_at).replace("Z", "+00:00"))
            decimal_value = Decimal(str(value))
        except (TypeError, ValueError) as error:
            raise ProviderError("OpenAQ returned an invalid PM2.5 reading.") from error

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return Pm25Reading(timestamp, decimal_value, canonical_unit)

    def _configured_pm25_unit(self, client: httpx.Client) -> str:
        """Verify the configured sensor type and retrieve its canonical unit from sensor metadata.

        OpenAQ's location 'latest' response omits parameter metadata, so we query
        the /sensors/{id} endpoint directly to verify parameter name is 'pm25'.
        """
        response = client.get(
            f"{self.base_url}/sensors/{self._settings.openaq_sensor_id}",
            headers={"X-API-Key": self._settings.openaq_api_key},
        )
        if response.status_code != 200:
            raise ProviderError("OpenAQ sensor metadata is unavailable.")

        results = response.json().get("results", [])
        sensor = results[0] if results else None
        parameter = sensor.get("parameter", {}) if isinstance(sensor, dict) else {}
        if parameter.get("name") != "pm25":
            raise ProviderError("Configured OpenAQ sensor is not PM2.5.")
        return _canonical_pm25_unit(str(parameter.get("units", "")))

    def hourly_pm25_history(self, hours: int) -> list[Pm25Reading]:
        """Fetch historical hourly PM2.5 readings for ML feature lag construction."""
        if not self._settings.openaq_api_key:
            raise ProviderError("OpenAQ is not configured.")
        if hours < 1:
            raise ValueError("hours must be positive.")

        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=hours)
        try:
            with httpx.Client(timeout=self._settings.provider_timeout_seconds) as client:
                # Query historical hourly aggregates from OpenAQ
                response = client.get(
                    f"{self.base_url}/sensors/{self._settings.openaq_sensor_id}/hours",
                    headers={"X-API-Key": self._settings.openaq_api_key},
                    params={
                        "datetime_from": start.isoformat().replace("+00:00", "Z"),
                        "datetime_to": end.isoformat().replace("+00:00", "Z"),
                        "limit": 1000,
                        "page": 1,
                    },
                )
        except httpx.HTTPError as error:
            raise ProviderError("OpenAQ history request failed.") from error

        if response.status_code != 200:
            raise ProviderError("OpenAQ history is unavailable.")

        # Parse and format each historical hourly reading
        readings: list[Pm25Reading] = []
        try:
            for item in response.json().get("results", []):
                period = item.get("period", {})
                observed_at = period.get("datetimeTo", {}).get("utc")
                value = item.get("value")
                unit = item.get("parameter", {}).get("units") or item.get("unit", "")
                if observed_at is None or value is None:
                    continue
                readings.append(
                    Pm25Reading(
                        observed_at=_parse_utc_timestamp(observed_at),
                        value_ug_m3=Decimal(str(value)),
                        unit=_canonical_pm25_unit(str(unit)),
                    )
                )
        except (TypeError, ValueError) as error:
            raise ProviderError("OpenAQ returned invalid PM2.5 history.") from error

        if not readings:
            raise ProviderError("OpenAQ returned no PM2.5 history.")

        # Return readings sorted in chronological ascending order
        return sorted(readings, key=lambda item: item.observed_at)


class OpenMeteoAdapter:
    """HTTP client adapter to fetch weather metrics and forecasts from Open-Meteo."""

    url = "https://api.open-meteo.com/v1/forecast"

    # List of required atmospheric and meteorological feature variables
    variables = (
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "dew_point_2m",
        "surface_pressure",
        "precipitation",
        "shortwave_radiation",
        "wind_direction_10m",
    )

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def hourly_weather(self) -> list[WeatherReading]:
        """Fetch past 1 day and future 2 days of hourly weather metrics for Delhi coordinates."""
        try:
            with httpx.Client(timeout=self._settings.provider_timeout_seconds) as client:
                response = client.get(
                    self.url,
                    params={
                        "latitude": self._settings.station_latitude,
                        "longitude": self._settings.station_longitude,
                        "hourly": ",".join(self.variables),
                        "timezone": "UTC",
                        "past_days": 1,
                        "forecast_days": 2,
                    },
                )
        except httpx.HTTPError as error:
            raise ProviderError("Open-Meteo request failed.") from error

        if response.status_code != 200:
            raise ProviderError("Open-Meteo returned an unavailable response.")

        hourly = response.json().get("hourly", {})
        times = hourly.get("time", [])
        values = [hourly.get(variable, []) for variable in self.variables]

        # Verify time dimension aligns with all requested meteorological series
        if not times or any(len(series) != len(times) for series in values):
            raise ProviderError("Open-Meteo returned incomplete weather data.")

        # Transform raw array response into structured WeatherReading objects
        readings: list[WeatherReading] = []
        try:
            for index, stamp in enumerate(times):
                if any(series[index] is None for series in values):
                    continue
                readings.append(
                    WeatherReading(
                        valid_at=datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).replace(
                            tzinfo=timezone.utc
                        ),
                        temperature_c=Decimal(str(values[0][index])),
                        humidity_percent=Decimal(str(values[1][index])),
                        wind_speed_kmh=Decimal(str(values[2][index])),
                        dew_point_c=Decimal(str(values[3][index])),
                        surface_pressure_hpa=Decimal(str(values[4][index])),
                        precipitation_mm=Decimal(str(values[5][index])),
                        shortwave_radiation_w_m2=Decimal(str(values[6][index])),
                        wind_direction_degrees=Decimal(str(values[7][index])),
                    )
                )
        except (TypeError, ValueError) as error:
            raise ProviderError("Open-Meteo returned invalid weather data.") from error

        if not readings:
            raise ProviderError("Open-Meteo returned no usable weather data.")

        return readings


def _canonical_pm25_unit(unit: str) -> str:
    """Normalize various unicode and ASCII PM2.5 unit representations into 'ug/m3'."""
    if unit.strip() in {"ug/m3", "µg/m³", "µg/m3", "ug/m³"}:
        return "ug/m3"
    raise ProviderError("OpenAQ returned an unsupported PM2.5 unit.")


def _parse_utc_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 string and ensure it has an explicit UTC timezone."""
    timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
