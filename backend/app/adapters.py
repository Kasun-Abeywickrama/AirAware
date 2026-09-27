"""Live PM2.5 and weather provider adapters."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

import httpx

from .config import Settings


class ProviderError(RuntimeError):
    """A safe provider failure suitable for operational handling."""


@dataclass(frozen=True)
class Pm25Reading:
    observed_at: datetime
    value_ug_m3: Decimal
    unit: str


@dataclass(frozen=True)
class WeatherReading:
    valid_at: datetime
    temperature_c: Decimal
    humidity_percent: Decimal
    wind_speed_kmh: Decimal


class OpenAQAdapter:
    """Fetch the configured PM2.5 sensor from OpenAQ v3."""

    base_url = "https://api.openaq.org/v3"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def latest_pm25(self) -> Pm25Reading:
        if not self._settings.openaq_api_key:
            raise ProviderError("OpenAQ is not configured.")

        try:
            with httpx.Client(timeout=self._settings.provider_timeout_seconds) as client:
                response = client.get(
                    f"{self.base_url}/locations/{self._settings.openaq_location_id}/latest",
                    headers={"X-API-Key": self._settings.openaq_api_key},
                    params={"limit": 100},
                )
        except httpx.HTTPError as error:
            raise ProviderError("OpenAQ request failed.") from error

        if response.status_code != 200:
            raise ProviderError("OpenAQ returned an unavailable response.")

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

        value = item.get("value")
        if isinstance(value, dict):
            value = value.get("value")
        observed_at = item.get("datetime", {}).get("utc")
        unit = item.get("parameter", {}).get("units") or item.get("unit", "")
        if value is None or not observed_at:
            raise ProviderError("OpenAQ returned an incomplete PM2.5 reading.")

        canonical_unit = _canonical_pm25_unit(str(unit))
        try:
            timestamp = datetime.fromisoformat(str(observed_at).replace("Z", "+00:00"))
            decimal_value = Decimal(str(value))
        except (TypeError, ValueError) as error:
            raise ProviderError("OpenAQ returned an invalid PM2.5 reading.") from error
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return Pm25Reading(timestamp, decimal_value, canonical_unit)


class OpenMeteoAdapter:
    """Fetch UTC hourly weather values from Open-Meteo."""

    url = "https://api.open-meteo.com/v1/forecast"
    variables = ("temperature_2m", "relative_humidity_2m", "wind_speed_10m")

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def hourly_weather(self) -> list[WeatherReading]:
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
        if not times or any(len(series) != len(times) for series in values):
            raise ProviderError("Open-Meteo returned incomplete weather data.")

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
                    )
                )
        except (TypeError, ValueError) as error:
            raise ProviderError("Open-Meteo returned invalid weather data.") from error

        if not readings:
            raise ProviderError("Open-Meteo returned no usable weather data.")
        return readings


def _canonical_pm25_unit(unit: str) -> str:
    if unit.strip() in {"ug/m3", "µg/m³", "µg/m3", "ug/m³"}:
        return "ug/m3"
    raise ProviderError("OpenAQ returned an unsupported PM2.5 unit.")
