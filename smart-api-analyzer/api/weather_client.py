"""Weather API service layer using Open-Meteo (no API key required)."""

import requests
from typing import Optional

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _get(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def geocode(city: str) -> Optional[dict]:
    """Resolve city name to lat/lon. Returns first result or None."""
    data = _get(GEO_URL, {"name": city, "count": 1, "language": "en", "format": "json"})
    results = data.get("results")
    if not results:
        return None
    return results[0]  # {name, latitude, longitude, country, timezone, ...}


def fetch_forecast(lat: float, lon: float, timezone: str = "auto") -> dict:
    """Fetch 7-day hourly + daily forecast from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "daily": [
            "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
            "windspeed_10m_max", "weathercode", "sunrise", "sunset",
            "uv_index_max", "precipitation_probability_max",
        ],
        "hourly": [
            "temperature_2m", "relativehumidity_2m", "windspeed_10m",
            "precipitation_probability", "weathercode",
        ],
        "current_weather": True,
        "forecast_days": 7,
    }
    return _get(FORECAST_URL, params)


def fetch_historical(lat: float, lon: float, start: str, end: str, timezone: str = "auto") -> dict:
    """Fetch historical daily data for trend analysis (start/end: YYYY-MM-DD)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "start_date": start,
        "end_date": end,
        "daily": [
            "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "windspeed_10m_max",
        ],
    }
    return _get(FORECAST_URL, params)
