"""
ShiftShield Premium Engine
==========================
AI-powered dynamic premium calculation — the CORE differentiator.

Computes personalised weekly premiums using 7 risk factors:
  1. Zone base risk              (city-level flood/heat/AQI profile)
  2. Sub-zone modifier           (micro-geography within the city)
  3. Seasonal multiplier         (monsoon, winter smog, heatwave months)
  4. Trust / loyalty discount    (tenure + fraud history)
  5. Claim history factor        (recent claim frequency)
  6. Weather forecast factor     (simulated 7-day AI prediction)
  7. Policy tier base rate       (Basic → Ultra)

Final formula:
  premium = base_rate × zone_risk × sub_zone_mod × seasonal × trust × claims × weather
  Clamped to [₹29 … ₹299], rounded to nearest ₹1.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models import User, Claim, ClaimStatus


# ═════════════════════════════════════════════════════════════════════════════
# 1. ZONE RISK DATA  (hardcoded for MVP — ML model in production)
# ═════════════════════════════════════════════════════════════════════════════
ZONE_RISK_DATA: dict[str, dict] = {
    "Mumbai": {
        "base_risk": 0.85,
        "flood_prone": True,
        "monsoon_months": [6, 7, 8, 9],
        "risk_label": "Very High",
        "primary_hazard": "monsoon flooding & waterlogging",
    },
    "Delhi": {
        "base_risk": 0.75,
        "aqi_prone": True,
        "winter_smog_months": [10, 11, 12, 1],
        "heat_months": [4, 5, 6],
        "risk_label": "High",
        "primary_hazard": "severe AQI & extreme summer heat",
    },
    "Bengaluru": {
        "base_risk": 0.55,
        "rain_prone": True,
        "monsoon_months": [5, 6, 7, 8, 9, 10],
        "risk_label": "Moderate",
        "primary_hazard": "unpredictable rain & urban flooding",
    },
    "Chennai": {
        "base_risk": 0.70,
        "cyclone_prone": True,
        "monsoon_months": [10, 11, 12],
        "risk_label": "High",
        "primary_hazard": "cyclones & northeast monsoon",
    },
    "Hyderabad": {
        "base_risk": 0.50,
        "flood_prone": True,
        "monsoon_months": [7, 8, 9],
        "risk_label": "Moderate",
        "primary_hazard": "flash floods during monsoon",
    },
    "Kolkata": {
        "base_risk": 0.65,
        "flood_prone": True,
        "monsoon_months": [6, 7, 8, 9],
        "risk_label": "Moderate-High",
        "primary_hazard": "monsoon waterlogging & nor'westers",
    },
    "Pune": {
        "base_risk": 0.45,
        "rain_prone": True,
        "monsoon_months": [6, 7, 8, 9],
        "risk_label": "Low-Moderate",
        "primary_hazard": "moderate monsoon rain",
    },
    "Jaipur": {
        "base_risk": 0.40,
        "heat_prone": True,
        "heat_months": [4, 5, 6],
        "risk_label": "Low-Moderate",
        "primary_hazard": "extreme heat (45°C+) in summer",
    },
}


# ═════════════════════════════════════════════════════════════════════════════
# 2. SUB-ZONE RISK MODIFIERS  (0.8 – 1.5)
# ═════════════════════════════════════════════════════════════════════════════
SUB_ZONE_MODIFIERS: dict[str, dict[str, float]] = {
    "Mumbai": {
        "Andheri": 1.10, "Bandra": 1.00, "Dadar": 1.35,
        "Borivali": 1.15, "Churchgate": 0.95, "Kurla": 1.25,
        "Malad": 1.05, "Goregaon": 1.00,
    },
    "Delhi": {
        "Connaught Place": 0.90, "Saket": 0.95, "Dwarka": 1.10,
        "Rohini": 1.15, "Lajpat Nagar": 1.05, "Karol Bagh": 1.00,
        "Janakpuri": 1.10, "Pitampura": 1.20,
    },
    "Bengaluru": {
        "Koramangala": 1.15, "Indiranagar": 1.00, "Whitefield": 1.25,
        "HSR Layout": 1.10, "Jayanagar": 0.95, "Malleshwaram": 0.90,
        "Electronic City": 1.30, "Marathahalli": 1.20,
    },
    "Hyderabad": {
        "Banjara Hills": 0.90, "Gachibowli": 1.00, "Madhapur": 1.05,
        "Secunderabad": 1.15, "Ameerpet": 1.10, "Kukatpally": 1.20,
        "HITEC City": 0.95, "Dilsukhnagar": 1.25,
    },
    "Chennai": {
        "T. Nagar": 1.10, "Adyar": 1.05, "Velachery": 1.35,
        "Anna Nagar": 1.00, "Mylapore": 1.15, "Guindy": 1.00,
        "Tambaram": 1.20, "Porur": 1.10,
    },
    "Kolkata": {
        "Salt Lake": 1.00, "Park Street": 0.90, "Howrah": 1.30,
        "Dum Dum": 1.15, "New Town": 0.95, "Gariahat": 1.05,
        "Tollygunge": 1.10, "Ballygunge": 0.95,
    },
    "Pune": {
        "Koregaon Park": 0.95, "Hinjawadi": 1.10, "Kharadi": 1.05,
        "Viman Nagar": 1.00, "Baner": 0.90, "Kothrud": 0.85,
        "Hadapsar": 1.15, "Aundh": 0.90,
    },
    "Jaipur": {
        "Malviya Nagar": 1.00, "Vaishali Nagar": 1.05, "Mansarovar": 1.10,
        "C-Scheme": 0.85, "Tonk Road": 1.15, "Jagatpura": 1.20,
        "Ajmer Road": 1.10, "Raja Park": 0.95,
    },
}

# Human-readable labels for sub-zone risk
SUB_ZONE_LABELS: dict[str, str] = {
    # Mumbai
    "Dadar": "historically flood-prone low-lying area",
    "Kurla": "chronic waterlogging zone near Mithi river",
    "Borivali": "proximity to Sanjay Gandhi National Park drainage",
    "Andheri": "dense urban area with moderate drainage issues",
    # Delhi
    "Pitampura": "low-lying area prone to monsoon waterlogging",
    "Rohini": "periphery zone with poor drainage infrastructure",
    "Dwarka": "reclaimed land with seasonal flooding risk",
    # Bengaluru
    "Electronic City": "low-lying IT corridor with recurring floods",
    "Whitefield": "rapid urbanisation impacting drainage capacity",
    "Marathahalli": "Varthur lake catchment overflow zone",
    "Koramangala": "historic flooding from storm water drains",
    # Chennai
    "Velachery": "major flood zone — worst-hit in 2015 & 2023 floods",
    "Tambaram": "Adyar river basin with cyclone exposure",
    "Mylapore": "coastal proximity increases cyclone impact",
    # Kolkata
    "Howrah": "low-lying industrial zone near Hooghly river",
    "Dum Dum": "airport area with monsoon waterlogging",
    # Hyderabad
    "Dilsukhnagar": "Musi river flood plain exposure",
    "Kukatpally": "rapid construction reducing drainage capacity",
    # Pune
    "Hadapsar": "Mula-Mutha river confluence flood risk",
    # Jaipur
    "Jagatpura": "periphery zone with heat-island effect",
    "Tonk Road": "commercial corridor with limited green cover",
}


# ═════════════════════════════════════════════════════════════════════════════
# 3. POLICY TIERS  (updated rates per spec)
# ═════════════════════════════════════════════════════════════════════════════
TIER_CONFIG: dict[str, dict] = {
    "basic": {
        "base_rate": 49,
        "max_payout_per_event": 300,
        "max_events_per_week": 2,
        "label": "Basic",
        "description": "Essential coverage for occasional disruptions",
    },
    "standard": {
        "base_rate": 79,
        "max_payout_per_event": 450,
        "max_events_per_week": 3,
        "label": "Standard",
        "description": "Balanced coverage for regular delivery riders",
    },
    "premium": {
        "base_rate": 129,
        "max_payout_per_event": 600,
        "max_events_per_week": 4,
        "label": "Premium",
        "description": "Enhanced protection for full-time riders",
    },
    "ultra": {
        "base_rate": 179,
        "max_payout_per_event": 800,
        "max_events_per_week": 5,
        "label": "Ultra",
        "description": "Maximum coverage for high-frequency riders",
    },
}

# Premium floor / ceiling
PREMIUM_FLOOR = 29
PREMIUM_CEILING = 299


# ═════════════════════════════════════════════════════════════════════════════
# PREMIUM ENGINE CLASS
# ═════════════════════════════════════════════════════════════════════════════
class PremiumEngine:
    """
    AI-powered dynamic premium calculation engine.

    Computes a personalised weekly insurance premium by evaluating
    7 independent risk factors and producing a transparent, human-readable
    breakdown of every pricing decision.
    """

    def __init__(self, db: Session):
        self.db = db
        self._now = datetime.now(timezone.utc)
        self._month = self._now.month

    # ─────────────────────────────────────────────────────────────────────
    # Factor 1: Zone Risk
    # ─────────────────────────────────────────────────────────────────────
    def _zone_risk(self, city: str) -> tuple[float, str]:
        """
        Evaluate geospatial zone risk based on the city's weather profile.

        Returns (multiplier, explanation).
        """
        data = ZONE_RISK_DATA.get(city)
        if not data:
            return 1.0, f"{city} has standard risk (no specific profile)"

        base = data["base_risk"]

        # Scale base_risk (0.0–1.0) to a multiplier range (0.8–1.6)
        multiplier = 0.8 + (base * 0.8)

        # Extra bump if currently in the city's high-risk season
        high_risk_months = (
            data.get("monsoon_months", [])
            + data.get("winter_smog_months", [])
            + data.get("heat_months", [])
        )
        if self._month in high_risk_months:
            multiplier += 0.15  # in-season surcharge baked into zone risk

        multiplier = round(multiplier, 2)
        label = data.get("risk_label", "Standard")
        hazard = data.get("primary_hazard", "general weather")
        explanation = f"{city} zone: {label} risk due to {hazard} (+{int((multiplier - 1) * 100)}%)"

        return multiplier, explanation

    # ─────────────────────────────────────────────────────────────────────
    # Factor 2: Sub-Zone Modifier
    # ─────────────────────────────────────────────────────────────────────
    def _sub_zone_modifier(self, city: str, sub_zone: str) -> tuple[float, str]:
        """
        Micro-geography modifier for the specific sub-zone.

        Returns (modifier, explanation).
        """
        city_subs = SUB_ZONE_MODIFIERS.get(city, {})
        modifier = city_subs.get(sub_zone, 1.0)

        label = SUB_ZONE_LABELS.get(sub_zone)
        if modifier > 1.0:
            if label:
                explanation = f"{sub_zone} sub-zone is {label} (+{int((modifier - 1) * 100)}%)"
            else:
                explanation = f"{sub_zone} has elevated micro-zone risk (+{int((modifier - 1) * 100)}%)"
        elif modifier < 1.0:
            explanation = f"{sub_zone} has lower-than-average risk for {city} ({int((modifier - 1) * 100)}%)"
        else:
            explanation = f"{sub_zone} has average risk for {city} (no adjustment)"

        return modifier, explanation

    # ─────────────────────────────────────────────────────────────────────
    # Factor 3: Seasonal Multiplier
    # ─────────────────────────────────────────────────────────────────────
    def _seasonal_multiplier(self, city: str) -> tuple[float, str]:
        """
        Season-aware pricing: peak, transition, or off-season.

        Returns (multiplier, explanation).
        """
        data = ZONE_RISK_DATA.get(city, {})
        high_risk_months = set(
            data.get("monsoon_months", [])
            + data.get("winter_smog_months", [])
            + data.get("heat_months", [])
        )

        month_names = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        month_name = month_names[self._month]

        if self._month in high_risk_months:
            # Peak season: 1.3–1.8 depending on city severity
            base_risk = data.get("base_risk", 0.5)
            multiplier = round(1.3 + (base_risk * 0.5), 2)  # higher-risk city → higher seasonal bump
            # Identify which hazard type
            if self._month in data.get("monsoon_months", []):
                hazard = "peak monsoon season"
            elif self._month in data.get("winter_smog_months", []):
                hazard = "winter smog & poor AQI season"
            elif self._month in data.get("heat_months", []):
                hazard = "extreme heat season"
            else:
                hazard = "high-risk weather season"
            explanation = f"{month_name} is {hazard} for {city} (+{int((multiplier - 1) * 100)}%)"
        else:
            # Check transition months (month before/after peak)
            transition_months = set()
            for m in high_risk_months:
                transition_months.add((m - 1) if m > 1 else 12)
                transition_months.add((m + 1) if m < 12 else 1)
            transition_months -= high_risk_months

            if self._month in transition_months:
                multiplier = round(random.uniform(1.1, 1.2), 2)  # seeded below for consistency
                explanation = f"{month_name} is a transition month for {city} — moderate risk (+{int((multiplier - 1) * 100)}%)"
            else:
                multiplier = round(random.uniform(0.8, 1.0), 2)
                explanation = f"{month_name} is low-risk season for {city} ({int((multiplier - 1) * 100)}%)"

        return multiplier, explanation

    # ─────────────────────────────────────────────────────────────────────
    # Factor 4: Trust / Loyalty Discount
    # ─────────────────────────────────────────────────────────────────────
    def _trust_discount(self, user: User) -> tuple[float, str]:
        """
        Loyalty-based discount using account tenure and fraud history.

        Returns (multiplier, explanation).  <1.0 = discount, >1.0 = surcharge.
        """
        # Fraud surcharge overrides loyalty
        if user.fraud_flags > 0:
            surcharge = 1.0 + (0.2 * min(user.fraud_flags, 3))  # cap at 60%
            return (
                round(surcharge, 2),
                f"⚠️  {user.fraud_flags} fraud flag(s) detected — risk surcharge (+{int((surcharge - 1) * 100)}%)",
            )

        # Calculate tenure in weeks
        if user.created_at:
            # Handle timezone-aware vs naive datetimes
            created = user.created_at
            if created.tzinfo is None:
                tenure_days = (self._now.replace(tzinfo=None) - created).days
            else:
                tenure_days = (self._now - created).days
            tenure_weeks = max(0, tenure_days // 7)
        else:
            tenure_weeks = 0

        if tenure_weeks <= 2:
            return 1.0, "New member (0-2 weeks) — no loyalty discount yet"
        elif tenure_weeks <= 8:
            return 0.95, f"Returning member ({tenure_weeks} weeks) — 5% loyalty discount"
        else:
            return 0.90, f"Loyal member ({tenure_weeks} weeks) — 10% loyalty discount 🎖️"

    # ─────────────────────────────────────────────────────────────────────
    # Factor 5: Claim History Factor
    # ─────────────────────────────────────────────────────────────────────
    def _claim_history_factor(self, user: User) -> tuple[float, str]:
        """
        Evaluate recent claim frequency (last 4 weeks).

        Returns (multiplier, explanation).
        """
        four_weeks_ago = self._now - timedelta(weeks=4)

        recent_claims = (
            self.db.query(Claim)
            .filter(
                Claim.user_id == user.id,
                Claim.initiated_at >= four_weeks_ago,
                Claim.status != ClaimStatus.REJECTED,
            )
            .count()
        )

        if recent_claims == 0:
            return 0.95, "No claims in the last 4 weeks — clean record discount (-5%)"
        elif recent_claims <= 2:
            return 1.0, f"{recent_claims} claim(s) in the last 4 weeks — within normal range"
        elif recent_claims <= 4:
            return 1.15, f"{recent_claims} claims in the last 4 weeks — above average (+15%)"
        else:
            return 1.30, f"{recent_claims} claims in the last 4 weeks — high frequency (+30%)"

    # ─────────────────────────────────────────────────────────────────────
    # Factor 6: Weather Forecast Factor (Simulated AI)
    # ─────────────────────────────────────────────────────────────────────
    def _weather_forecast_factor(self, city: str, sub_zone: str) -> tuple[float, str]:
        """
        Simulated 7-day AI weather prediction.

        In production this would call OpenWeatherMap / IMD APIs and feed
        into an ML model.  For MVP we simulate using deterministic
        pseudo-random data seeded by city+month+week for consistency.

        Returns (multiplier, explanation).
        """
        # Deterministic seed: same city+week → same forecast
        week_num = self._now.isocalendar()[1]
        seed_str = f"{city}-{sub_zone}-{self._now.year}-W{week_num}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        data = ZONE_RISK_DATA.get(city, {})
        high_risk_months = set(
            data.get("monsoon_months", [])
            + data.get("winter_smog_months", [])
            + data.get("heat_months", [])
        )

        # Simulate: how many of next 7 days have adverse weather?
        if self._month in high_risk_months:
            # Peak season: 3–6 bad days likely
            bad_days = rng.randint(3, 6)
            extreme_warning = rng.random() < 0.3  # 30% chance of extreme event
        else:
            # Off-season: 0–2 bad days
            bad_days = rng.randint(0, 2)
            extreme_warning = rng.random() < 0.05  # 5% chance

        # Determine forecast scenario
        if extreme_warning:
            multiplier = 1.40
            # Generate specific warning
            if data.get("flood_prone"):
                warning = "⛈️  EXTREME: Heavy rainfall warning — flooding expected"
            elif data.get("aqi_prone") and self._month in data.get("winter_smog_months", []):
                warning = "🫁  EXTREME: AQI forecast >400 — hazardous air quality"
            elif data.get("heat_prone") or self._month in data.get("heat_months", []):
                warning = "🌡️  EXTREME: Heatwave warning — temperatures >45°C expected"
            elif data.get("cyclone_prone"):
                warning = "🌀  EXTREME: Cyclone/depression forming — heavy rain expected"
            else:
                warning = "⚠️  EXTREME: Severe weather warning for the region"
            explanation = f"{warning} (+40%)"

        elif bad_days >= 3:
            multiplier = round(1.1 + (bad_days * 0.03), 2)
            if data.get("flood_prone") or data.get("rain_prone"):
                detail = f"rain predicted for {bad_days} of next 7 days"
            elif data.get("aqi_prone"):
                detail = f"poor AQI expected for {bad_days} of next 7 days"
            elif data.get("heat_prone"):
                detail = f"high temperatures forecast for {bad_days} of next 7 days"
            else:
                detail = f"adverse conditions forecast for {bad_days} of next 7 days"
            explanation = f"🌧️  AI forecast: {detail} (+{int((multiplier - 1) * 100)}%)"

        elif bad_days >= 1:
            multiplier = 1.0
            explanation = f"☁️  AI forecast: mild disruption possible ({bad_days} day{'s' if bad_days > 1 else ''}) — no adjustment"

        else:
            multiplier = 0.90
            explanation = "☀️  AI forecast: clear week ahead — good conditions discount (-10%)"

        return multiplier, explanation

    # ─────────────────────────────────────────────────────────────────────
    # MAIN CALCULATION
    # ─────────────────────────────────────────────────────────────────────
    def calculate_premium(
        self,
        user: User,
        tier: str = "basic",
    ) -> dict:
        """
        Compute the full personalised premium for a user and tier.

        Args:
            user: The User ORM object (must have city, zone, sub_zone).
            tier: One of 'basic', 'standard', 'premium', 'ultra'.

        Returns:
            dict with full breakdown, factors, explanations, and final price.
        """
        tier = tier.lower()
        if tier not in TIER_CONFIG:
            raise ValueError(f"Unknown tier '{tier}'. Must be one of {list(TIER_CONFIG.keys())}")

        tier_data = TIER_CONFIG[tier]
        base_rate = tier_data["base_rate"]
        city = user.city
        sub_zone = user.sub_zone

        # Seed RNG for deterministic seasonal randomness per user+week
        week_num = self._now.isocalendar()[1]
        seed_str = f"{city}-{self._now.year}-W{week_num}-seasonal"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        random.seed(seed)

        # Compute each factor
        zone_risk, zone_expl = self._zone_risk(city)
        sub_mod, sub_expl = self._sub_zone_modifier(city, sub_zone)
        seasonal, seasonal_expl = self._seasonal_multiplier(city)
        trust, trust_expl = self._trust_discount(user)
        claims, claims_expl = self._claim_history_factor(user)
        weather, weather_expl = self._weather_forecast_factor(city, sub_zone)

        # Reset RNG to avoid side effects
        random.seed()

        # Final formula
        raw_premium = (
            base_rate
            * zone_risk
            * sub_mod
            * seasonal
            * trust
            * claims
            * weather
        )

        # Clamp & round
        final_premium = int(round(max(PREMIUM_FLOOR, min(PREMIUM_CEILING, raw_premium))))

        # Build explanation list
        factors_explanation = [
            zone_expl,
            sub_expl,
            seasonal_expl,
            trust_expl,
            claims_expl,
            weather_expl,
        ]

        # Add clamping note if applied
        if raw_premium < PREMIUM_FLOOR:
            factors_explanation.append(
                f"Premium floor applied: ₹{round(raw_premium)} → ₹{PREMIUM_FLOOR}"
            )
        elif raw_premium > PREMIUM_CEILING:
            factors_explanation.append(
                f"Premium ceiling applied: ₹{round(raw_premium)} → ₹{PREMIUM_CEILING}"
            )

        return {
            "tier": tier,
            "tier_label": tier_data["label"],
            "tier_description": tier_data["description"],
            "base_rate": base_rate,
            "zone_risk_multiplier": zone_risk,
            "sub_zone_modifier": sub_mod,
            "seasonal_multiplier": seasonal,
            "trust_discount": trust,
            "claim_history_factor": claims,
            "weather_forecast_factor": weather,
            "raw_premium": round(raw_premium, 2),
            "final_weekly_premium": final_premium,
            "max_payout_per_event": tier_data["max_payout_per_event"],
            "max_events_per_week": tier_data["max_events_per_week"],
            "factors_explanation": factors_explanation,
            "city": city,
            "sub_zone": sub_zone,
            "calculated_at": self._now.isoformat(),
        }

    def calculate_all_tiers(self, user: User) -> list[dict]:
        """
        Compute premiums for ALL 4 tiers for comparison display.

        Returns a list of 4 premium breakdowns, one per tier.
        """
        results = []
        for tier_key in TIER_CONFIG:
            result = self.calculate_premium(user, tier_key)
            results.append(result)
        return results

    def get_risk_factors_summary(self, user: User) -> dict:
        """
        Return a human-readable summary of what's affecting this user's
        premium — without computing a specific tier.

        Perfect for "Why is my premium this price?" UX.
        """
        city = user.city
        sub_zone = user.sub_zone

        # Seed for deterministic results
        week_num = self._now.isocalendar()[1]
        seed_str = f"{city}-{self._now.year}-W{week_num}-seasonal"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        random.seed(seed)

        zone_risk, zone_expl = self._zone_risk(city)
        sub_mod, sub_expl = self._sub_zone_modifier(city, sub_zone)
        seasonal, seasonal_expl = self._seasonal_multiplier(city)
        trust, trust_expl = self._trust_discount(user)
        claims, claims_expl = self._claim_history_factor(user)
        weather, weather_expl = self._weather_forecast_factor(city, sub_zone)

        random.seed()

        # Categorise factors
        increasing = []
        decreasing = []
        neutral = []

        for name, value, expl in [
            ("Zone Risk", zone_risk, zone_expl),
            ("Sub-Zone", sub_mod, sub_expl),
            ("Season", seasonal, seasonal_expl),
            ("Trust / Loyalty", trust, trust_expl),
            ("Claim History", claims, claims_expl),
            ("Weather Forecast", weather, weather_expl),
        ]:
            entry = {"factor": name, "multiplier": value, "explanation": expl}
            if value > 1.01:
                increasing.append(entry)
            elif value < 0.99:
                decreasing.append(entry)
            else:
                neutral.append(entry)

        # Sort: biggest impact first
        increasing.sort(key=lambda x: x["multiplier"], reverse=True)
        decreasing.sort(key=lambda x: x["multiplier"])

        # Composite risk score (0–100)
        composite = zone_risk * sub_mod * seasonal * weather
        risk_score = min(100, int((composite - 0.5) / 2.5 * 100))
        risk_score = max(0, risk_score)

        if risk_score >= 75:
            risk_level = "Very High"
            risk_emoji = "🔴"
        elif risk_score >= 50:
            risk_level = "High"
            risk_emoji = "🟠"
        elif risk_score >= 30:
            risk_level = "Moderate"
            risk_emoji = "🟡"
        else:
            risk_level = "Low"
            risk_emoji = "🟢"

        zone_data = ZONE_RISK_DATA.get(city, {})

        return {
            "user_id": user.id,
            "city": city,
            "sub_zone": sub_zone,
            "overall_risk_score": risk_score,
            "overall_risk_level": f"{risk_emoji} {risk_level}",
            "primary_hazard": zone_data.get("primary_hazard", "general weather conditions"),
            "factors_increasing_premium": increasing,
            "factors_decreasing_premium": decreasing,
            "factors_neutral": neutral,
            "tips_to_reduce_premium": _generate_tips(user, trust, claims),
            "analysed_at": self._now.isoformat(),
        }


# ═════════════════════════════════════════════════════════════════════════════
# Helper: Generate actionable tips
# ═════════════════════════════════════════════════════════════════════════════
def _generate_tips(user: User, trust_factor: float, claims_factor: float) -> list[str]:
    """Generate personalised tips to help the user reduce their premium."""
    tips = []

    if trust_factor >= 1.0:
        if user.fraud_flags > 0:
            tips.append(
                "🛡️  Maintain clean records for 8+ weeks to clear fraud flags "
                "and unlock loyalty discounts."
            )
        else:
            tips.append(
                "📅  Stay insured for 3+ weeks to unlock the 5% loyalty discount."
            )

    if trust_factor == 0.95:
        tips.append(
            "🎖️  Keep your policy active for 9+ weeks to upgrade to the 10% loyalty tier."
        )

    if claims_factor > 1.0:
        tips.append(
            "📊  Fewer claims = lower premiums. Your rate adjusts based on "
            "a 4-week rolling window."
        )

    tips.append(
        "🌤️  Your premium auto-adjusts weekly based on AI weather forecasts — "
        "clear weeks mean lower prices."
    )

    tips.append(
        "💡  Consider upgrading your tier for better per-event coverage "
        "rather than filing frequent small claims."
    )

    return tips
