"""
ShiftShield Configuration
=========================
Central configuration for the parametric insurance platform.
Manages database URLs, API keys, JWT settings, and zone/sub-zone definitions
for Indian cities.
"""

from __future__ import annotations

import os
from typing import Final


# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────
DATABASE_URL: Final[str] = os.getenv(
    "DATABASE_URL",
    "sqlite:///./shiftshield.db",
)

# ─────────────────────────────────────────────────────────────────────────────
# Redis
# ─────────────────────────────────────────────────────────────────────────────
REDIS_URL: Final[str] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ─────────────────────────────────────────────────────────────────────────────
# External APIs
# ─────────────────────────────────────────────────────────────────────────────
OPENWEATHERMAP_API_KEY: Final[str] = os.getenv(
    "OPENWEATHERMAP_API_KEY",
    "YOUR_OPENWEATHERMAP_API_KEY_HERE",
)

# ─────────────────────────────────────────────────────────────────────────────
# JWT / Auth
# ─────────────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY: Final[str] = os.getenv(
    "JWT_SECRET_KEY",
    "shiftshield-super-secret-change-me-in-production",
)
JWT_ALGORITHM: Final[str] = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")  # 24 hours
)

# ─────────────────────────────────────────────────────────────────────────────
# Insurance Constants
# ─────────────────────────────────────────────────────────────────────────────

# Policy tiers with weekly premiums (INR) and payout caps
POLICY_TIERS: Final[dict] = {
    "basic": {
        "weekly_premium": 49,
        "max_payout_per_event": 200,
        "max_events_per_week": 3,
    },
    "standard": {
        "weekly_premium": 99,
        "max_payout_per_event": 500,
        "max_events_per_week": 5,
    },
    "premium": {
        "weekly_premium": 199,
        "max_payout_per_event": 1000,
        "max_events_per_week": 7,
    },
    "ultra": {
        "weekly_premium": 349,
        "max_payout_per_event": 2000,
        "max_events_per_week": 10,
    },
}

# Trigger thresholds (default; can be refined per-zone)
TRIGGER_THRESHOLDS: Final[dict] = {
    "rain": 15.0,        # mm/hr – moderate rain
    "aqi": 300.0,        # AQI – "Very Unhealthy"
    "heat": 42.0,        # °C – extreme heat
    "flood": 100.0,      # mm cumulative in 6 hrs
    "curfew": 1.0,       # binary flag (0/1)
}

# ─────────────────────────────────────────────────────────────────────────────
# Zones & Sub-Zones
# ─────────────────────────────────────────────────────────────────────────────
ZONES: Final[dict[str, list[str]]] = {
    "Mumbai": [
        "Andheri",
        "Bandra",
        "Dadar",
        "Borivali",
        "Churchgate",
        "Kurla",
        "Malad",
        "Goregaon",
    ],
    "Delhi": [
        "Connaught Place",
        "Saket",
        "Dwarka",
        "Rohini",
        "Lajpat Nagar",
        "Karol Bagh",
        "Janakpuri",
        "Pitampura",
    ],
    "Bengaluru": [
        "Koramangala",
        "Indiranagar",
        "Whitefield",
        "HSR Layout",
        "Jayanagar",
        "Malleshwaram",
        "Electronic City",
        "Marathahalli",
    ],
    "Hyderabad": [
        "Banjara Hills",
        "Gachibowli",
        "Madhapur",
        "Secunderabad",
        "Ameerpet",
        "Kukatpally",
        "HITEC City",
        "Dilsukhnagar",
    ],
    "Chennai": [
        "T. Nagar",
        "Adyar",
        "Velachery",
        "Anna Nagar",
        "Mylapore",
        "Guindy",
        "Tambaram",
        "Porur",
    ],
    "Kolkata": [
        "Salt Lake",
        "Park Street",
        "Howrah",
        "Dum Dum",
        "New Town",
        "Gariahat",
        "Tollygunge",
        "Ballygunge",
    ],
    "Pune": [
        "Koregaon Park",
        "Hinjawadi",
        "Kharadi",
        "Viman Nagar",
        "Baner",
        "Kothrud",
        "Hadapsar",
        "Aundh",
    ],
    "Jaipur": [
        "Malviya Nagar",
        "Vaishali Nagar",
        "Mansarovar",
        "C-Scheme",
        "Tonk Road",
        "Jagatpura",
        "Ajmer Road",
        "Raja Park",
    ],
}

# Flattened list of all city names for quick validation
CITY_NAMES: Final[list[str]] = list(ZONES.keys())

# Zone risk multipliers (higher → more weather-prone)
ZONE_RISK_MULTIPLIERS: Final[dict[str, float]] = {
    "Mumbai": 1.35,       # monsoon flooding
    "Delhi": 1.25,        # AQI + extreme heat
    "Bengaluru": 1.10,    # occasional heavy rain
    "Hyderabad": 1.15,    # flash floods
    "Chennai": 1.30,      # cyclones + heavy rain
    "Kolkata": 1.20,      # monsoon flooding
    "Pune": 1.05,         # moderate climate
    "Jaipur": 1.15,       # extreme heat
}

# Seasonal multipliers (month → multiplier)
SEASONAL_MULTIPLIERS: Final[dict[int, float]] = {
    1: 0.90,   # Jan – cool & dry
    2: 0.90,   # Feb
    3: 1.00,   # Mar – warming up
    4: 1.10,   # Apr – heat begins
    5: 1.20,   # May – peak heat
    6: 1.30,   # Jun – monsoon onset
    7: 1.40,   # Jul – peak monsoon
    8: 1.35,   # Aug – monsoon
    9: 1.25,   # Sep – monsoon retreat
    10: 1.10,  # Oct – post-monsoon
    11: 1.05,  # Nov – AQI spikes (Delhi)
    12: 0.95,  # Dec – winter
}
