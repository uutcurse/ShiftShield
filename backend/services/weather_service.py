"""
Weather Service
===============
Fetches real-time weather data from OpenWeatherMap API.
Falls back to deterministic mock data if no API key is configured
or if the API call fails.

Responses are cached in memory for 30 minutes to avoid spamming the API.
"""

from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import OPENWEATHERMAP_API_KEY

# ─────────────────────────────────────────────────────────────────────────────
# In-memory cache  { cache_key: { "data": ..., "expires_at": unix_ts } }
# ─────────────────────────────────────────────────────────────────────────────
_CACHE: dict[str, dict] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes

OWM_BASE = "https://api.openweathermap.org/data/2.5"

# City → OWM query string (some cities need disambiguation)
CITY_OWM_NAMES: dict[str, str] = {
    "Mumbai": "Mumbai,IN",
    "Delhi": "Delhi,IN",
    "Bengaluru": "Bengaluru,IN",
    "Chennai": "Chennai,IN",
    "Hyderabad": "Hyderabad,IN",
    "Kolkata": "Kolkata,IN",
    "Pune": "Pune,IN",
    "Jaipur": "Jaipur,IN",
}

# Approximate city coordinates for API calls
CITY_COORDS: dict[str, tuple[float, float]] = {
    "Mumbai": (19.076, 72.877),
    "Delhi": (28.704, 77.102),
    "Bengaluru": (12.972, 77.594),
    "Chennai": (13.082, 80.270),
    "Hyderabad": (17.385, 78.487),
    "Kolkata": (22.572, 88.363),
    "Pune": (18.520, 73.856),
    "Jaipur": (26.912, 75.787),
}

# ─────────────────────────────────────────────────────────────────────────────
# Mock Data Generator  (realistic, deterministic per city+hour)
# ─────────────────────────────────────────────────────────────────────────────
# Base climate profiles per city
CITY_CLIMATE: dict[str, dict] = {
    "Mumbai": {
        "temp_range": (24, 35), "humidity_range": (60, 95),
        "monsoon_months": [6, 7, 8, 9],
        "monsoon_rain_range": (10, 60), "dry_rain_range": (0, 3),
        "wind_range": (10, 35),
        "description_wet": "heavy rain and thunderstorms",
        "description_dry": "partly cloudy with sea breeze",
    },
    "Delhi": {
        "temp_range": (8, 46), "humidity_range": (20, 85),
        "monsoon_months": [7, 8, 9],
        "heat_months": [4, 5, 6],
        "monsoon_rain_range": (5, 40), "dry_rain_range": (0, 1),
        "wind_range": (5, 25),
        "description_wet": "scattered thundershowers",
        "description_dry": "hazy with dust particles",
    },
    "Bengaluru": {
        "temp_range": (15, 35), "humidity_range": (40, 90),
        "monsoon_months": [5, 6, 7, 8, 9, 10],
        "monsoon_rain_range": (5, 35), "dry_rain_range": (0, 2),
        "wind_range": (8, 20),
        "description_wet": "intermittent rain showers",
        "description_dry": "pleasant with light clouds",
    },
    "Chennai": {
        "temp_range": (22, 42), "humidity_range": (55, 95),
        "monsoon_months": [10, 11, 12],
        "monsoon_rain_range": (8, 50), "dry_rain_range": (0, 2),
        "wind_range": (10, 40),
        "description_wet": "northeast monsoon rains",
        "description_dry": "hot and humid",
    },
    "Hyderabad": {
        "temp_range": (15, 44), "humidity_range": (25, 85),
        "monsoon_months": [7, 8, 9],
        "monsoon_rain_range": (5, 45), "dry_rain_range": (0, 1),
        "wind_range": (5, 20),
        "description_wet": "heavy rain spells",
        "description_dry": "hot and partly cloudy",
    },
    "Kolkata": {
        "temp_range": (12, 42), "humidity_range": (50, 95),
        "monsoon_months": [6, 7, 8, 9],
        "monsoon_rain_range": (8, 55), "dry_rain_range": (0, 2),
        "wind_range": (8, 35),
        "description_wet": "torrential rainfall with thunder",
        "description_dry": "humid with occasional clouds",
    },
    "Pune": {
        "temp_range": (12, 40), "humidity_range": (30, 90),
        "monsoon_months": [6, 7, 8, 9],
        "monsoon_rain_range": (5, 30), "dry_rain_range": (0, 1),
        "wind_range": (8, 22),
        "description_wet": "moderate rainfall",
        "description_dry": "clear and pleasant",
    },
    "Jaipur": {
        "temp_range": (5, 48), "humidity_range": (10, 75),
        "monsoon_months": [7, 8, 9],
        "heat_months": [4, 5, 6],
        "monsoon_rain_range": (3, 25), "dry_rain_range": (0, 0.5),
        "wind_range": (5, 30),
        "description_wet": "dust storm followed by rain",
        "description_dry": "hot and sunny",
    },
}


def _seed_rng(city: str, hour_bucket: int) -> random.Random:
    """Return a seeded RNG that's consistent for a given city+hour."""
    seed_str = f"{city}-{hour_bucket}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    return random.Random(seed)


def _mock_weather(city: str) -> dict:
    """Generate realistic mock weather for a city."""
    now = datetime.now(timezone.utc)
    month = now.month
    hour_bucket = now.hour // 3  # changes every 3 hours
    day_bucket = now.timetuple().tm_yday

    climate = CITY_CLIMATE.get(city, CITY_CLIMATE["Mumbai"])
    rng = _seed_rng(city, day_bucket * 100 + hour_bucket)

    temp_min, temp_max = climate["temp_range"]
    humidity_min, humidity_max = climate["humidity_range"]

    in_monsoon = month in climate.get("monsoon_months", [])
    in_heat = month in climate.get("heat_months", [])

    # Temperature
    if in_heat:
        temp = rng.uniform(temp_max * 0.90, temp_max)
    elif in_monsoon:
        temp = rng.uniform(temp_min * 1.3, temp_max * 0.75)
    else:
        temp = rng.uniform(temp_min, temp_max * 0.80)

    # Humidity
    if in_monsoon:
        humidity = rng.uniform(humidity_max * 0.75, humidity_max)
    else:
        humidity = rng.uniform(humidity_min, humidity_max * 0.65)

    # Rain (mm per 3 hours)
    if in_monsoon:
        rain_mm_3hr = round(rng.uniform(*climate["monsoon_rain_range"]), 1)
    else:
        rain_mm_3hr = round(rng.uniform(*climate["dry_rain_range"]), 1)

    # Wind
    wind_speed = round(rng.uniform(*climate["wind_range"]), 1)

    # Description
    if rain_mm_3hr > 15:
        description = climate["description_wet"]
    elif rain_mm_3hr > 3:
        description = "light rain"
    elif temp > 42:
        description = "extreme heat wave"
    else:
        description = climate["description_dry"]

    return {
        "city": city,
        "source": "mock_data",
        "temp_c": round(temp, 1),
        "feels_like_c": round(temp + (humidity / 100) * 3 - wind_speed * 0.1, 1),
        "humidity_pct": round(humidity),
        "rain_mm_3hr": rain_mm_3hr,
        "rain_mm_1hr": round(rain_mm_3hr / 3, 1),
        "wind_speed_kmh": wind_speed,
        "description": description,
        "cloud_cover_pct": round(rng.uniform(20, 95) if in_monsoon else rng.uniform(0, 60)),
        "pressure_hpa": round(rng.uniform(1005, 1020)),
        "visibility_km": round(rng.uniform(1, 6) if rain_mm_3hr > 10 else rng.uniform(5, 15), 1),
        "timestamp": now.isoformat(),
        "is_mock": True,
    }


def _mock_forecast(city: str, days: int = 7) -> list[dict]:
    """Generate a realistic multi-day forecast."""
    now = datetime.now(timezone.utc)
    month = now.month
    climate = CITY_CLIMATE.get(city, CITY_CLIMATE["Mumbai"])
    in_monsoon = month in climate.get("monsoon_months", [])

    forecast = []
    for day_offset in range(days):
        rng = _seed_rng(city, now.timetuple().tm_yday + day_offset)
        temp_min, temp_max = climate["temp_range"]
        temp = round(rng.uniform(temp_min * 1.1, temp_max * 0.9), 1) if not in_monsoon else round(
            rng.uniform(temp_min * 1.2, temp_max * 0.75), 1)
        rain = round(rng.uniform(*climate["monsoon_rain_range"]) if in_monsoon
                     else rng.uniform(*climate["dry_rain_range"]), 1)
        humidity = round(rng.uniform(70, 95) if in_monsoon else rng.uniform(30, 70))
        from datetime import timedelta
        forecast_date = (now + timedelta(days=day_offset)).date()
        forecast.append({
            "date": forecast_date.isoformat(),
            "temp_high_c": temp,
            "temp_low_c": round(temp - rng.uniform(4, 10), 1),
            "rain_mm": rain,
            "humidity_pct": humidity,
            "description": climate["description_wet"] if rain > 10 else climate["description_dry"],
            "rain_probability_pct": int(min(100, (rain / 30) * 100)),
            "is_mock": True,
        })
    return forecast


# ─────────────────────────────────────────────────────────────────────────────
# Cache helpers
# ─────────────────────────────────────────────────────────────────────────────
def _cache_get(key: str) -> dict | None:
    entry = _CACHE.get(key)
    if entry and entry["expires_at"] > time.time():
        return entry["data"]
    _CACHE.pop(key, None)
    return None


def _cache_set(key: str, data: dict | list) -> None:
    _CACHE[key] = {"data": data, "expires_at": time.time() + CACHE_TTL_SECONDS}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def get_current_weather(city: str) -> dict:
    """
    Fetch current weather for a city.

    Tries OpenWeatherMap first. Falls back to realistic mock data
    if the API key is missing, invalid, or the call fails.
    Results are cached for 30 minutes.
    """
    cache_key = f"weather:{city}"
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "cache_hit": True}

    api_key = OPENWEATHERMAP_API_KEY
    if api_key and api_key not in ("", "your_openweathermap_api_key_here"):
        try:
            lat, lon = CITY_COORDS.get(city, (19.076, 72.877))
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(
                    f"{OWM_BASE}/weather",
                    params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
                )
                resp.raise_for_status()
                raw = resp.json()

            rain_3hr = raw.get("rain", {}).get("3h", raw.get("rain", {}).get("1h", 0) * 3) or 0
            data = {
                "city": city,
                "source": "openweathermap",
                "temp_c": round(raw["main"]["temp"], 1),
                "feels_like_c": round(raw["main"]["feels_like"], 1),
                "humidity_pct": raw["main"]["humidity"],
                "rain_mm_3hr": round(rain_3hr, 1),
                "rain_mm_1hr": round(rain_3hr / 3, 1),
                "wind_speed_kmh": round(raw["wind"]["speed"] * 3.6, 1),
                "description": raw["weather"][0]["description"],
                "cloud_cover_pct": raw["clouds"]["all"],
                "pressure_hpa": raw["main"]["pressure"],
                "visibility_km": round(raw.get("visibility", 10000) / 1000, 1),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_mock": False,
            }
            _cache_set(cache_key, data)
            return data

        except Exception as e:
            print(f"[WeatherService] OWM API failed for {city}: {e} — using mock data")

    # Fallback to mock
    data = _mock_weather(city)
    _cache_set(cache_key, data)
    return data


def get_forecast(city: str, days: int = 7) -> list[dict]:
    """
    Fetch a multi-day forecast for a city.

    Tries OpenWeatherMap 5-day forecast. Falls back to mock data.
    Cached for 30 minutes.
    """
    cache_key = f"forecast:{city}:{days}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    api_key = OPENWEATHERMAP_API_KEY
    if api_key and api_key not in ("", "your_openweathermap_api_key_here"):
        try:
            lat, lon = CITY_COORDS.get(city, (19.076, 72.877))
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(
                    f"{OWM_BASE}/forecast",
                    params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "cnt": days * 8},
                )
                resp.raise_for_status()
                raw = resp.json()

            # Aggregate 3-hour slots into daily forecasts
            from collections import defaultdict
            daily: dict[str, list] = defaultdict(list)
            for item in raw.get("list", []):
                from datetime import datetime as dt
                d = dt.fromtimestamp(item["dt"]).date().isoformat()
                daily[d].append(item)

            forecast = []
            for date_str in sorted(daily.keys())[:days]:
                slots = daily[date_str]
                temps = [s["main"]["temp"] for s in slots]
                rains = [s.get("rain", {}).get("3h", 0) for s in slots]
                humidities = [s["main"]["humidity"] for s in slots]
                total_rain = round(sum(rains), 1)
                forecast.append({
                    "date": date_str,
                    "temp_high_c": round(max(temps), 1),
                    "temp_low_c": round(min(temps), 1),
                    "rain_mm": total_rain,
                    "humidity_pct": round(sum(humidities) / len(humidities)),
                    "description": slots[0]["weather"][0]["description"],
                    "rain_probability_pct": int(min(100, (total_rain / 30) * 100)),
                    "is_mock": False,
                })

            _cache_set(cache_key, forecast)
            return forecast

        except Exception as e:
            print(f"[WeatherService] OWM forecast failed for {city}: {e} — using mock data")

    forecast = _mock_forecast(city, days)
    _cache_set(cache_key, forecast)
    return forecast


def invalidate_cache(city: str | None = None) -> None:
    """Clear cached weather data (useful after simulating triggers)."""
    if city:
        _CACHE.pop(f"weather:{city}", None)
        for d in range(1, 8):
            _CACHE.pop(f"forecast:{city}:{d}", None)
    else:
        _CACHE.clear()
