"""
Trigger Monitor — The Parametric Engine
========================================
The HEART of ShiftShield. Evaluates real-time weather + AQI data against
predefined thresholds. When a threshold is breached, it:
  1. Logs a TriggerEvent in the database
  2. Finds all active policies in the affected zone
  3. Auto-creates claims for each eligible policyholder
  4. Applies the 72-hour cooling period (50% payout for new users)

TriggerMonitor can be:
  - Called by the APScheduler background job (every 30 minutes)
  - Triggered manually via POST /api/triggers/simulate (for demos)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models import (
    Claim,
    ClaimStatus,
    Policy,
    TriggerEvent,
    TriggerType,
    User,
)
from services.weather_service import get_current_weather
from services.aqi_service import get_aqi


# ═════════════════════════════════════════════════════════════════════════════
# Trigger Thresholds (the parametric rules)
# ═════════════════════════════════════════════════════════════════════════════
THRESHOLDS: dict[str, dict] = {
    "heavy_rain": {
        "metric": "rain_mm_3hr",
        "threshold": 25.0,
        "payout_pct": 1.0,
        "trigger_type": TriggerType.RAIN,
        "label": "Heavy Rain",
        "unit": "mm/3hr",
        "description": "Rainfall ≥ 25mm in 3 hours — severe disruption",
    },
    "moderate_rain": {
        "metric": "rain_mm_3hr",
        "threshold": 15.0,
        "payout_pct": 0.6,
        "trigger_type": TriggerType.RAIN,
        "label": "Moderate Rain",
        "unit": "mm/3hr",
        "description": "Rainfall ≥ 15mm in 3 hours — significant slowdown",
    },
    "severe_aqi": {
        "metric": "aqi",
        "threshold": 350.0,
        "payout_pct": 1.0,
        "trigger_type": TriggerType.AQI,
        "label": "Severe AQI",
        "unit": "AQI index",
        "description": "AQI ≥ 350 — Very Poor/Hazardous conditions",
    },
    "bad_aqi": {
        "metric": "aqi",
        "threshold": 300.0,
        "payout_pct": 0.5,
        "trigger_type": TriggerType.AQI,
        "label": "Bad AQI",
        "unit": "AQI index",
        "description": "AQI ≥ 300 — Poor air quality, health risk",
    },
    "extreme_heat": {
        "metric": "temp_c",
        "threshold": 45.0,
        "payout_pct": 1.0,
        "trigger_type": TriggerType.HEAT,
        "label": "Extreme Heat",
        "unit": "°C",
        "description": "Temperature ≥ 45°C — dangerous working conditions",
    },
    "high_heat": {
        "metric": "temp_c",
        "threshold": 43.0,
        "payout_pct": 0.6,
        "trigger_type": TriggerType.HEAT,
        "label": "High Heat",
        "unit": "°C",
        "description": "Temperature ≥ 43°C — severe heat stress",
    },
    "flood_warning": {
        "metric": "flood_level",
        "threshold": 1.0,
        "payout_pct": 1.0,
        "trigger_type": TriggerType.FLOOD,
        "label": "Flood Warning",
        "unit": "level (1=active)",
        "description": "Active flood warning — waterlogging or inundation",
    },
    "curfew": {
        "metric": "curfew_active",
        "threshold": 1.0,
        "payout_pct": 1.0,
        "trigger_type": TriggerType.CURFEW,
        "label": "Curfew",
        "unit": "active (1=yes)",
        "description": "Government-declared curfew preventing delivery",
    },
}


def _get_trigger_type_str(tt: TriggerType) -> str:
    return tt.value if hasattr(tt, "value") else str(tt)


# ═════════════════════════════════════════════════════════════════════════════
class TriggerMonitor:
    """
    Parametric insurance trigger evaluation engine.

    Usage:
        monitor = TriggerMonitor(db)
        active = monitor.check_all_triggers("Mumbai", "Dadar")
        # → list of breached triggers with measured values
    """

    def __init__(self, db: Session):
        self.db = db
        self._now = datetime.now(timezone.utc)

    # ─────────────────────────────────────────────────────────────────────
    # Core: evaluate a single trigger rule
    # ─────────────────────────────────────────────────────────────────────
    def evaluate_trigger(
        self, trigger_name: str, measured_value: float
    ) -> tuple[bool, float]:
        """
        Test whether a measured value breaches a trigger threshold.

        Returns (is_triggered: bool, payout_pct: float).
        """
        rule = THRESHOLDS.get(trigger_name)
        if not rule:
            return False, 0.0
        breached = measured_value >= rule["threshold"]
        payout_pct = rule["payout_pct"] if breached else 0.0
        return breached, payout_pct

    # ─────────────────────────────────────────────────────────────────────
    # Check all real-time triggers for a city/sub-zone
    # ─────────────────────────────────────────────────────────────────────
    def check_all_triggers(
        self, city: str, sub_zone: str
    ) -> list[dict]:
        """
        Fetch live weather + AQI and evaluate all triggers.

        Returns a list of active (breached) triggers with readings.
        De-duplicates overlapping rules (e.g., heavy_rain supersedes moderate_rain).
        """
        # Fetch data
        weather = get_current_weather(city)
        aqi_data = get_aqi(city)

        readings = {
            "rain_mm_3hr": weather.get("rain_mm_3hr", 0),
            "rain_mm_1hr": weather.get("rain_mm_1hr", 0),
            "temp_c": weather.get("temp_c", 30),
            "aqi": aqi_data.get("aqi", 100),
            "humidity_pct": weather.get("humidity_pct", 60),
            "wind_speed_kmh": weather.get("wind_speed_kmh", 15),
            # Flood/curfew: binary flags (0 normally, 1 if active)
            "flood_level": 0.0,  # Set to 1 via simulate_trigger
            "curfew_active": 0.0,  # Set to 1 via simulate_trigger
        }

        active_triggers = []
        triggered_types: set[str] = set()

        # Evaluate in priority order (most severe first to prevent double-claiming)
        priority_order = [
            "heavy_rain", "moderate_rain",
            "severe_aqi", "bad_aqi",
            "extreme_heat", "high_heat",
            "flood_warning", "curfew",
        ]

        for name in priority_order:
            rule = THRESHOLDS[name]
            metric = rule["metric"]
            measured = readings.get(metric, 0)
            breached, payout_pct = self.evaluate_trigger(name, measured)

            # De-duplicate: skip lower-severity if higher already triggered for same metric group
            trigger_type = _get_trigger_type_str(rule["trigger_type"])
            if breached:
                if trigger_type in triggered_types:
                    continue  # Already have a higher-severity trigger of this type
                triggered_types.add(trigger_type)

                active_triggers.append({
                    "trigger_name": name,
                    "trigger_type": trigger_type,
                    "label": rule["label"],
                    "metric": metric,
                    "measured_value": measured,
                    "threshold": rule["threshold"],
                    "unit": rule["unit"],
                    "payout_pct": payout_pct,
                    "description": rule["description"],
                    "severity": "HIGH" if payout_pct == 1.0 else "MODERATE",
                    "city": city,
                    "sub_zone": sub_zone,
                })

        return active_triggers

    # ─────────────────────────────────────────────────────────────────────
    # History
    # ─────────────────────────────────────────────────────────────────────
    def get_trigger_history(
        self, city: str, days: int = 30, sub_zone: str | None = None
    ) -> list[dict]:
        """
        Retrieve past trigger events from the database for a city.
        """
        cutoff = self._now - timedelta(days=days)
        query = (
            self.db.query(TriggerEvent)
            .filter(
                TriggerEvent.zone == city,
                TriggerEvent.triggered_at >= cutoff,
            )
        )
        if sub_zone:
            query = query.filter(TriggerEvent.sub_zone == sub_zone)

        events = query.order_by(TriggerEvent.triggered_at.desc()).all()

        result = []
        for ev in events:
            tt = ev.trigger_type
            tt_str = tt.value if hasattr(tt, "value") else str(tt)
            result.append({
                "event_id": ev.id,
                "zone": ev.zone,
                "sub_zone": ev.sub_zone,
                "trigger_type": tt_str,
                "measured_value": ev.measured_value,
                "threshold": ev.threshold,
                "triggered_at": ev.triggered_at.isoformat(),
                "affected_policies": ev.affected_policies_count,
                "total_payout_inr": ev.total_payout,
                "days_ago": (self._now - ev.triggered_at.replace(tzinfo=timezone.utc)
                             if ev.triggered_at.tzinfo is None
                             else self._now - ev.triggered_at
                             ).days,
            })
        return result

    # ─────────────────────────────────────────────────────────────────────
    # Fire trigger: log event + auto-create claims
    # ─────────────────────────────────────────────────────────────────────
    def fire_trigger(
        self,
        city: str,
        sub_zone: str,
        trigger_name: str,
        measured_value: float,
        source: str = "monitor",
    ) -> dict:
        """
        Record a trigger event and auto-create claims for all affected policies.

        Steps:
          1. Validate trigger name
          2. Log TriggerEvent in DB
          3. Find all active policies in city/sub_zone
          4. For each: check weekly limit, compute payout, create Claim
          5. Apply 72-hour cooling period (50% payout for first-ever policy)
          6. Return full summary
        """
        rule = THRESHOLDS.get(trigger_name)
        if not rule:
            raise ValueError(f"Unknown trigger '{trigger_name}'")

        breached, payout_pct = self.evaluate_trigger(trigger_name, measured_value)
        if not breached:
            return {
                "result": "no_trigger",
                "trigger_name": trigger_name,
                "measured_value": measured_value,
                "threshold": rule["threshold"],
                "message": f"Value {measured_value} did not breach threshold {rule['threshold']}",
                "city": city,
                "sub_zone": sub_zone,
            }

        # 1. Log TriggerEvent
        event = TriggerEvent(
            zone=city,
            sub_zone=sub_zone,
            trigger_type=_get_trigger_type_str(rule["trigger_type"]),
            measured_value=measured_value,
            threshold=rule["threshold"],
        )
        self.db.add(event)
        self.db.flush()  # get event.id

        # 2. Find affected users in this sub-zone
        affected_users = (
            self.db.query(User)
            .filter(
                User.city == city,
                User.sub_zone == sub_zone,
                User.is_active == True,  # noqa: E712
            )
            .all()
        )

        claims_created = []
        total_payout = 0.0

        for user in affected_users:
            # Get active policy
            policy = (
                self.db.query(Policy)
                .filter(
                    Policy.user_id == user.id,
                    Policy.is_active == True,  # noqa: E712
                )
                .first()
            )
            if not policy:
                continue

            # Check weekly event cap
            week_claims = (
                self.db.query(Claim)
                .filter(
                    Claim.policy_id == policy.id,
                    Claim.status != ClaimStatus.REJECTED,
                )
                .count()
            )
            if week_claims >= policy.max_events_per_week:
                continue

            # Compute raw payout
            raw_payout = policy.max_payout_per_event * payout_pct

            # 72-hour cooling period: 50% payout for first-ever policy
            cooling_applied = False
            first_policy_count = (
                self.db.query(Policy).filter(Policy.user_id == user.id).count()
            )
            if first_policy_count == 1 and policy.created_at:
                created = policy.created_at
                if created.tzinfo is None:
                    age = self._now.replace(tzinfo=None) - created
                else:
                    age = self._now - created
                if age < timedelta(hours=72):
                    raw_payout *= 0.5
                    cooling_applied = True

            payout_amount = round(raw_payout, 2)
            if payout_amount <= 0:
                continue

            # Fraud scoring
            fraud_score = round(
                (100 - user.trust_score) * 0.4
                + min(30, user.fraud_flags * 10)
                + (5 if cooling_applied else 0),
                2,
            )
            claim_status = (
                ClaimStatus.AUTO_APPROVED
                if fraud_score < 20 and user.trust_score >= 70
                else ClaimStatus.UNDER_REVIEW
            )

            # Create claim
            claim = Claim(
                policy_id=policy.id,
                user_id=user.id,
                trigger_type=_get_trigger_type_str(rule["trigger_type"]),
                trigger_value=measured_value,
                threshold_value=rule["threshold"],
                payout_amount=payout_amount,
                status=claim_status,
                fraud_score=fraud_score,
            )
            self.db.add(claim)

            # Update user totals
            user.total_claims += 1
            if claim_status == ClaimStatus.AUTO_APPROVED:
                user.total_payouts += payout_amount
                claim.paid_at = self._now
                claim.payment_ref = f"UPI-AUTO-{event.id}-{user.id}"

            total_payout += payout_amount
            claims_created.append({
                "user_id": user.id,
                "user_name": user.name,
                "policy_id": policy.id,
                "payout_amount": payout_amount,
                "status": claim_status.value,
                "fraud_score": fraud_score,
                "cooling_period_applied": cooling_applied,
            })

        # Update event totals
        event.affected_policies_count = len(claims_created)
        event.total_payout = round(total_payout, 2)

        self.db.commit()
        self.db.refresh(event)

        return {
            "result": "triggered",
            "event_id": event.id,
            "trigger_name": trigger_name,
            "trigger_type": _get_trigger_type_str(rule["trigger_type"]),
            "label": rule["label"],
            "city": city,
            "sub_zone": sub_zone,
            "measured_value": measured_value,
            "threshold": rule["threshold"],
            "payout_pct": payout_pct,
            "source": source,
            "triggered_at": self._now.isoformat(),
            "affected_policies": len(claims_created),
            "total_payout_inr": round(total_payout, 2),
            "claims": claims_created,
        }

    # ─────────────────────────────────────────────────────────────────────
    # DEMO: Simulate a trigger (manual override for demos)
    # ─────────────────────────────────────────────────────────────────────
    def simulate_trigger(
        self,
        city: str,
        sub_zone: str,
        trigger_name: str,
        value_override: float | None = None,
    ) -> dict:
        """
        DEMO METHOD: Manually fire a trigger with a custom measured value.

        If no value_override is provided, uses 2× the trigger's threshold
        to guarantee a breach and a full (100%) payout.

        Perfect for demo videos: simulate a Mumbai monsoon flood,
        show all Dadar users receiving instant payouts.
        """
        rule = THRESHOLDS.get(trigger_name)
        if not rule:
            available = list(THRESHOLDS.keys())
            raise ValueError(
                f"Unknown trigger '{trigger_name}'. Available: {available}"
            )

        # Default: 1.5× threshold to guarantee a meaningful breach
        if value_override is None:
            measured = round(rule["threshold"] * 1.5, 1)
        else:
            measured = value_override

        result = self.fire_trigger(
            city=city,
            sub_zone=sub_zone,
            trigger_name=trigger_name,
            measured_value=measured,
            source="simulate",
        )
        result["is_simulation"] = True
        result["simulation_note"] = (
            f"This was a manual simulation. "
            f"Measured value {measured} {rule['unit']} was injected "
            f"(threshold: {rule['threshold']} {rule['unit']})."
        )
        return result

    # ─────────────────────────────────────────────────────────────────────
    # Full Scan: check all cities (for APScheduler job)
    # ─────────────────────────────────────────────────────────────────────
    def run_full_scan(self) -> dict:
        """
        Run trigger checks across ALL cities and their sub-zones.

        Called by the APScheduler background job every 30 minutes.
        Returns a summary of any triggers that fired.
        """
        from config import ZONES

        fired_events = []
        checked_zones = 0

        # Get a unique list of (city, sub_zone) pairs that have active users
        active_user_zones = (
            self.db.query(User.city, User.sub_zone)
            .filter(User.is_active == True)  # noqa: E712
            .distinct()
            .all()
        )

        # Also append all configured zones (so we scan even empty zones)
        all_zones = {
            (city, sub_zone)
            for city, subs in ZONES.items()
            for sub_zone in subs
        }
        active_set = set(active_user_zones)
        # Prioritise zones with users, then add remaining
        scan_zones = list(active_set) + list(all_zones - active_set)

        checked_cities: set[str] = set()

        for city, sub_zone in scan_zones:
            checked_zones += 1
            # Only fetch weather/AQI once per city
            if city not in checked_cities:
                checked_cities.add(city)

            active = self.check_all_triggers(city, sub_zone)
            for trig in active:
                try:
                    result = self.fire_trigger(
                        city=city,
                        sub_zone=sub_zone,
                        trigger_name=trig["trigger_name"],
                        measured_value=trig["measured_value"],
                        source="scheduler",
                    )
                    if result["result"] == "triggered":
                        fired_events.append(result)
                except Exception as e:
                    print(f"[TriggerMonitor] Error firing {trig['trigger_name']} in {city}/{sub_zone}: {e}")

        return {
            "scan_completed_at": self._now.isoformat(),
            "zones_checked": checked_zones,
            "cities_scanned": len(checked_cities),
            "triggers_fired": len(fired_events),
            "total_claims_created": sum(e["affected_policies"] for e in fired_events),
            "total_payout_inr": round(sum(e["total_payout_inr"] for e in fired_events), 2),
            "events": fired_events,
        }
