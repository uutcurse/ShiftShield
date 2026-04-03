"""
AQI Service
===========
Provides realistic Air Quality Index (AQI) data for Indian cities.

For MVP this uses deterministic mock data seeded by city + week,
producing stable readings that only shift week-over-week.

In production, this would call:
  - CPCB API (Central Pollution Control Board)
  - IQAir API
  - OpenAQ API

AQI Scale (Indian Standard):
  0-50    Good
  51-100  Satisfactory
  101-200 Moderate
  201-300 Poor
  301-400 Very Poor
  401-500 Severe / Hazardous
"""

from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────────────────────────────────
_AQI_CACHE: dict[str, dict] = {}
AQI_CACHE_TTL = 1800  # 30 minutes


# ─────────────────────────────────────────────────────────────────────────────
# City AQI Profiles  (realistic monthly ranges for India)
# ─────────────────────────────────────────────────────────────────────────────
CITY_AQI_PROFILES: dict[str, dict] = {
    "Delhi": {
        "annual_range": (100, 500),
        # Month → (min, max)  — severely worse in winter smog season
        "monthly_ranges": {
            1: (280, 500), 2: (200, 420), 3: (150, 300), 4: (120, 250),
            5: (130, 280), 6: (100, 200), 7: (80, 180), 8: (80, 170),
            9: (100, 200), 10: (200, 420), 11: (320, 500), 12: (350, 500),
        },
        "primary_pollutant": "PM2.5",
        "secondary_pollutant": "NO2",
        "typical_pm25_range": (80, 350),
        "typical_pm10_range": (150, 500),
        "worst_months": [10, 11, 12, 1],
        "note": "Severe smog Oct–Jan due to crop burning + vehicular emissions",
    },
    "Mumbai": {
        "annual_range": (60, 280),
        "monthly_ranges": {
            1: (120, 250), 2: (100, 220), 3: (90, 200), 4: (80, 180),
            5: (80, 160), 6: (60, 120), 7: (50, 100), 8: (50, 100),
            9: (60, 130), 10: (100, 200), 11: (130, 250), 12: (140, 280),
        },
        "primary_pollutant": "PM10",
        "secondary_pollutant": "SO2",
        "typical_pm25_range": (30, 150),
        "typical_pm10_range": (60, 250),
        "worst_months": [11, 12, 1],
        "note": "Construction dust + sea salt aerosols are primary contributors",
    },
    "Bengaluru": {
        "annual_range": (40, 200),
        "monthly_ranges": {
            1: (100, 180), 2: (90, 160), 3: (80, 150), 4: (60, 130),
            5: (50, 120), 6: (40, 90), 7: (40, 80), 8: (40, 80),
            9: (50, 100), 10: (70, 150), 11: (100, 190), 12: (110, 200),
        },
        "primary_pollutant": "PM2.5",
        "secondary_pollutant": "CO",
        "typical_pm25_range": (20, 100),
        "typical_pm10_range": (40, 170),
        "worst_months": [11, 12, 1],
        "note": "Rapid urbanisation and vehicle density are key drivers",
    },
    "Chennai": {
        "annual_range": (50, 200),
        "monthly_ranges": {
            1: (100, 180), 2: (90, 170), 3: (80, 160), 4: (70, 150),
            5: (80, 160), 6: (70, 140), 7: (70, 130), 8: (60, 130),
            9: (70, 150), 10: (80, 170), 11: (100, 200), 12: (110, 190),
        },
        "primary_pollutant": "PM10",
        "secondary_pollutant": "NO2",
        "typical_pm25_range": (25, 110),
        "typical_pm10_range": (50, 190),
        "worst_months": [11, 12],
        "note": "Industrial corridor at Manali strongly affects readings",
    },
    "Hyderabad": {
        "annual_range": (50, 250),
        "monthly_ranges": {
            1: (130, 240), 2: (120, 220), 3: (110, 200), 4: (100, 190),
            5: (100, 200), 6: (70, 150), 7: (60, 130), 8: (60, 130),
            9: (80, 160), 10: (120, 220), 11: (150, 250), 12: (160, 250),
        },
        "primary_pollutant": "PM2.5",
        "secondary_pollutant": "PM10",
        "typical_pm25_range": (30, 140),
        "typical_pm10_range": (60, 220),
        "worst_months": [11, 12, 1],
        "note": "Granite quarrying in outer areas elevates PM10 readings",
    },
    "Kolkata": {
        "annual_range": (60, 350),
        "monthly_ranges": {
            1: (200, 350), 2: (180, 320), 3: (150, 280), 4: (120, 220),
            5: (100, 200), 6: (70, 140), 7: (60, 120), 8: (60, 120),
            9: (80, 150), 10: (140, 260), 11: (200, 350), 12: (230, 380),
        },
        "primary_pollutant": "PM2.5",
        "secondary_pollutant": "SO2",
        "typical_pm25_range": (40, 200),
        "typical_pm10_range": (80, 320),
        "worst_months": [11, 12, 1, 2],
        "note": "Brick kilns and industrial zones severely impact air quality",
    },
    "Pune": {
        "annual_range": (40, 200),
        "monthly_ranges": {
            1: (100, 180), 2: (90, 170), 3: (80, 150), 4: (70, 140),
            5: (80, 160), 6: (60, 120), 7: (50, 100), 8: (50, 100),
            9: (60, 120), 10: (90, 170), 11: (110, 190), 12: (120, 200),
        },
        "primary_pollutant": "PM10",
        "secondary_pollutant": "NO2",
        "typical_pm25_range": (20, 100),
        "typical_pm10_range": (40, 170),
        "worst_months": [11, 12],
        "note": "Hadapsar and Bhosari industrial zones are primary sources",
    },
    "Jaipur": {
        "annual_range": (60, 300),
        "monthly_ranges": {
            1: (150, 280), 2: (130, 260), 3: (120, 240), 4: (120, 280),
            5: (130, 300), 6: (100, 240), 7: (70, 160), 8: (70, 160),
            9: (90, 180), 10: (140, 260), 11: (180, 300), 12: (200, 300),
        },
        "primary_pollutant": "PM10",
        "secondary_pollutant": "SO2",
        "typical_pm25_range": (40, 160),
        "typical_pm10_range": (80, 280),
        "worst_months": [4, 5, 11, 12],
        "note": "Dust storms in summer and winter smog from stubble burning",
    },
}

# AQI Category thresholds (Indian AQI scale)
AQI_CATEGORIES = [
    (0, 50, "Good", "🟢", "Minimal impact on health"),
    (51, 100, "Satisfactory", "🟡", "Minor breathing discomfort in sensitive people"),
    (101, 200, "Moderate", "🟠", "Breathing discomfort for people with lung/heart disease"),
    (201, 300, "Poor", "🔴", "Breathing discomfort to most on prolonged exposure"),
    (301, 400, "Very Poor", "🟣", "Respiratory illness on prolonged exposure"),
    (401, 500, "Severe / Hazardous", "⚫", "Affects healthy people; serious risk for sensitive groups"),
]


def _aqi_category(aqi: int) -> tuple[str, str, str]:
    """Return (category, emoji, health_impact) for an AQI value."""
    for lo, hi, cat, emoji, impact in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            return cat, emoji, impact
    return "Hazardous", "⚫", "Emergency conditions — everyone affected"


def _pm25_from_aqi(aqi: int, rng: random.Random) -> int:
    """Estimate PM2.5 from AQI with some variance."""
    # Rough conversion: PM2.5 ≈ AQI * 0.5–0.7 for Indian scale
    return round(aqi * rng.uniform(0.5, 0.68))


def _pm10_from_pm25(pm25: int, rng: random.Random) -> int:
    """PM10 is typically 1.5–2.5× PM2.5."""
    return round(pm25 * rng.uniform(1.5, 2.5))


# ─────────────────────────────────────────────────────────────────────────────
# Mock AQI data generator
# ─────────────────────────────────────────────────────────────────────────────
def _generate_aqi(city: str) -> dict:
    """Generate deterministic mock AQI data for a city."""
    now = datetime.now(timezone.utc)
    month = now.month
    # Seed: consistent for a given city+day (changes daily)
    seed_str = f"aqi-{city}-{now.date().isoformat()}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    profile = CITY_AQI_PROFILES.get(city, CITY_AQI_PROFILES["Mumbai"])
    aqi_min, aqi_max = profile["monthly_ranges"].get(month, profile["annual_range"])
    aqi = round(rng.uniform(aqi_min, aqi_max))
    aqi = max(0, min(500, aqi))

    category, emoji, health_impact = _aqi_category(aqi)
    pm25 = _pm25_from_aqi(aqi, rng)
    pm10 = _pm10_from_pm25(pm25, rng)
    no2 = round(rng.uniform(20, 180))
    co = round(rng.uniform(0.5, 8.0), 1)
    so2 = round(rng.uniform(5, 60))
    o3 = round(rng.uniform(20, 120))

    in_worst_month = month in profile.get("worst_months", [])

    return {
        "city": city,
        "aqi": aqi,
        "category": category,
        "category_emoji": emoji,
        "health_impact": health_impact,
        "primary_pollutant": profile["primary_pollutant"],
        "components": {
            "pm25_ugm3": pm25,
            "pm10_ugm3": pm10,
            "no2_ugm3": no2,
            "co_mgm3": co,
            "so2_ugm3": so2,
            "o3_ugm3": o3,
        },
        "seasonal_note": profile["note"],
        "is_seasonal_peak": in_worst_month,
        "is_mock": True,
        "timestamp": now.isoformat(),
        "advisory": _advisory(aqi),
    }


def _advisory(aqi: int) -> str:
    """Human-readable advisory message for delivery workers."""
    if aqi <= 50:
        return "✅ Air quality is good. Safe to work."
    elif aqi <= 100:
        return "🟡 Satisfactory air. Sensitive workers may feel minor discomfort."
    elif aqi <= 200:
        return "🟠 Moderate pollution. Wear a mask on long shifts."
    elif aqi <= 300:
        return "🔴 Poor air quality. Limit exposure. N95 mask recommended."
    elif aqi <= 400:
        return "🟣 Very poor AQI. Delivery pauses advisable for health."
    else:
        return "⚫ HAZARDOUS. Emergency conditions. Avoid outdoor work."


# ─────────────────────────────────────────────────────────────────────────────
# Cache helpers
# ─────────────────────────────────────────────────────────────────────────────
def _cache_get(key: str) -> dict | None:
    entry = _AQI_CACHE.get(key)
    if entry and entry["expires_at"] > time.time():
        return entry["data"]
    _AQI_CACHE.pop(key, None)
    return None


def _cache_set(key: str, data: dict) -> None:
    _AQI_CACHE[key] = {"data": data, "expires_at": time.time() + AQI_CACHE_TTL}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def get_aqi(city: str) -> dict:
    """
    Get current AQI for a city.

    Returns mock data with realistic seasonal variance.
    In production this would call CPCB / IQAir / OpenAQ.
    Cached for 30 minutes.
    """
    cache_key = f"aqi:{city}"
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "cache_hit": True}

    data = _generate_aqi(city)
    _cache_set(cache_key, data)
    return data


def get_all_city_aqi() -> list[dict]:
    """Get AQI snapshot for all supported cities."""
    return [get_aqi(city) for city in CITY_AQI_PROFILES]


def get_aqi_trend(city: str, days: int = 7) -> list[dict]:
    """Simulate a 7-day historical AQI trend for a city."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    trend = []
    profile = CITY_AQI_PROFILES.get(city, CITY_AQI_PROFILES["Mumbai"])
    for d in range(days, 0, -1):
        past_date = (now - timedelta(days=d)).date()
        month = past_date.month
        seed_str = f"aqi-{city}-{past_date.isoformat()}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        aqi_min, aqi_max = profile["monthly_ranges"].get(month, profile["annual_range"])
        aqi = round(rng.uniform(aqi_min, aqi_max))
        category, emoji, _ = _aqi_category(aqi)
        trend.append({
            "date": past_date.isoformat(),
            "aqi": aqi,
            "category": category,
            "category_emoji": emoji,
        })
    return trend
