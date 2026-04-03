"""
Triggers Router — Parametric Engine API
========================================
Endpoints for real-time trigger monitoring, history, simulation, and
transparency.

  GET  /api/triggers/active      — current triggers in user's zone
  GET  /api/triggers/history     — past trigger events
  POST /api/triggers/simulate    — DEMO: inject a trigger manually
  GET  /api/triggers/thresholds  — all threshold rules (transparency)
  GET  /api/triggers/weather     — current weather in user's zone
  GET  /api/triggers/aqi         — current AQI in user's zone
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import User
from routers.auth import get_current_user
from services.trigger_monitor import TriggerMonitor, THRESHOLDS
from services.weather_service import get_current_weather, get_forecast
from services.aqi_service import get_aqi, get_aqi_trend

router = APIRouter(prefix="/triggers", tags=["Trigger Monitoring (Parametric Engine)"])


# ═════════════════════════════════════════════════════════════════════════════
# Schemas
# ═════════════════════════════════════════════════════════════════════════════
class SimulateTriggerRequest(BaseModel):
    trigger_name: str = Field(
        ...,
        description=(
            "Name of the trigger to simulate. One of: "
            "heavy_rain, moderate_rain, severe_aqi, bad_aqi, "
            "extreme_heat, high_heat, flood_warning, curfew"
        ),
    )
    city: str = Field(..., description="City to fire the trigger in")
    sub_zone: str = Field(..., description="Sub-zone within the city")
    value_override: Optional[float] = Field(
        None,
        description=(
            "Custom measured value to inject. "
            "If omitted, uses 1.5× the trigger threshold."
        ),
    )
    admin_key: str = Field(
        ...,
        description="Admin secret key (use 'DEMO_ADMIN' for the demo environment)",
    )


DEMO_ADMIN_KEY = "DEMO_ADMIN"


# ═════════════════════════════════════════════════════════════════════════════
# GET /active — Current triggers in user's zone
# ═════════════════════════════════════════════════════════════════════════════
@router.get(
    "/active",
    summary="Current active triggers in your zone",
)
def get_active_triggers(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check real-time weather and AQI for the authenticated user's zone
    and return any currently active (breached) triggers.

    This is what the mobile app calls every 10 minutes to show
    the "🌧️ Heavy rain detected — your claim is being processed" banner.

    Returns:
    - List of active triggers with measured values
    - Current weather snapshot
    - Current AQI snapshot
    - Whether any payout-triggering conditions are active
    """
    monitor = TriggerMonitor(db=db)
    active = monitor.check_all_triggers(user.city, user.sub_zone)

    weather = get_current_weather(user.city)
    aqi = get_aqi(user.city)

    # Check if user has an active policy
    from models import Policy
    active_policy = (
        db.query(Policy)
        .filter(Policy.user_id == user.id, Policy.is_active == True)  # noqa: E712
        .first()
    )

    return {
        "user_zone": {"city": user.city, "sub_zone": user.sub_zone},
        "has_active_policy": active_policy is not None,
        "active_triggers_count": len(active),
        "active_triggers": active,
        "any_payout_active": len(active) > 0,
        "payout_alert": (
            f"⚠️ {len(active)} trigger(s) active in {user.sub_zone}! "
            "Claims are being automatically processed."
            if active else
            f"✅ No active triggers in {user.sub_zone}. Conditions are safe."
        ),
        "current_conditions": {
            "weather": {
                "temp_c": weather.get("temp_c"),
                "rain_mm_3hr": weather.get("rain_mm_3hr"),
                "description": weather.get("description"),
                "humidity_pct": weather.get("humidity_pct"),
                "wind_speed_kmh": weather.get("wind_speed_kmh"),
                "source": weather.get("source"),
            },
            "aqi": {
                "aqi": aqi.get("aqi"),
                "category": aqi.get("category"),
                "category_emoji": aqi.get("category_emoji"),
                "advisory": aqi.get("advisory"),
                "primary_pollutant": aqi.get("primary_pollutant"),
            },
        },
        "checked_at": weather.get("timestamp"),
    }


# ═════════════════════════════════════════════════════════════════════════════
# GET /history — Past trigger events for user's zone
# ═════════════════════════════════════════════════════════════════════════════
@router.get(
    "/history",
    summary="Past trigger events in your zone",
)
def get_trigger_history(
    days: int = Query(30, ge=1, le=365, description="Days of history to retrieve"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the history of trigger events for the authenticated user's zone.

    Shows each event with:
    - What triggered (rain / AQI / heat / flood / curfew)
    - Measured vs threshold value
    - How many policies were affected
    - Total payout disbursed

    Useful for demonstrating how often triggers fire and
    proving the value of ShiftShield to sceptical riders.
    """
    monitor = TriggerMonitor(db=db)
    history = monitor.get_trigger_history(
        city=user.city, days=days, sub_zone=user.sub_zone
    )

    # Stats summary
    total_payouts = sum(e["total_payout_inr"] for e in history)
    total_policies = sum(e["affected_policies"] for e in history)

    return {
        "city": user.city,
        "sub_zone": user.sub_zone,
        "days_queried": days,
        "events_found": len(history),
        "summary": {
            "total_events": len(history),
            "total_policies_benefited": total_policies,
            "total_payouts_inr": round(total_payouts, 2),
            "avg_events_per_week": round(len(history) / max(1, days / 7), 1),
        },
        "events": history,
    }


# ═════════════════════════════════════════════════════════════════════════════
# POST /simulate — DEMO: Fire a trigger manually
# ═════════════════════════════════════════════════════════════════════════════
@router.post(
    "/simulate",
    summary="[DEMO] Simulate a trigger event",
    status_code=status.HTTP_201_CREATED,
)
def simulate_trigger(
    payload: SimulateTriggerRequest,
    db: Session = Depends(get_db),
):
    """
    **DEMO / ADMIN ONLY**: Manually simulate a trigger event.

    This is the **killer feature for demo videos**. Use it to:
    - Fire a monsoon rainstorm in Mumbai/Dadar → watch all riders get instant payouts
    - Trigger a Delhi AQI emergency → test the auto-claim pipeline
    - Simulate a Jaipur heatwave → demonstrate the parametric payout logic

    **Admin key**: Use `DEMO_ADMIN` in the demo environment.

    **Available trigger names:**
    - `heavy_rain` — ≥25mm/3hr (100% payout)
    - `moderate_rain` — ≥15mm/3hr (60% payout)
    - `severe_aqi` — AQI ≥350 (100% payout)
    - `bad_aqi` — AQI ≥300 (50% payout)
    - `extreme_heat` — ≥45°C (100% payout)
    - `high_heat` — ≥43°C (60% payout)
    - `flood_warning` — binary flag = 1 (100% payout)
    - `curfew` — binary flag = 1 (100% payout)

    **What happens:**
    1. A TriggerEvent is logged in the database.
    2. All active policies in the specified zone are found.
    3. Claims are auto-created (and auto-approved for high-trust users).
    4. The response shows exactly who got paid and how much.
    """
    # Verify admin key
    if payload.admin_key != DEMO_ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key. Use 'DEMO_ADMIN' for the demo environment.",
        )

    # Validate trigger name
    if payload.trigger_name not in THRESHOLDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Unknown trigger '{payload.trigger_name}'",
                "available_triggers": list(THRESHOLDS.keys()),
            },
        )

    monitor = TriggerMonitor(db=db)
    try:
        result = monitor.simulate_trigger(
            city=payload.city,
            sub_zone=payload.sub_zone,
            trigger_name=payload.trigger_name,
            value_override=payload.value_override,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if result["result"] == "no_trigger":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result


# ═════════════════════════════════════════════════════════════════════════════
# GET /thresholds — All trigger rules (transparency)
# ═════════════════════════════════════════════════════════════════════════════
@router.get(
    "/thresholds",
    summary="View all trigger thresholds",
)
def get_thresholds():
    """
    Return all parametric trigger rules — the contract between ShiftShield
    and its policyholders.

    **Transparency principle**: Riders can always see exactly what conditions
    trigger payouts and how much they'll receive. No fine print.
    """
    thresholds_out = []
    for name, rule in THRESHOLDS.items():
        tt = rule["trigger_type"]
        tt_str = tt.value if hasattr(tt, "value") else str(tt)
        thresholds_out.append({
            "trigger_name": name,
            "trigger_type": tt_str,
            "label": rule["label"],
            "metric_measured": rule["metric"],
            "threshold": rule["threshold"],
            "unit": rule["unit"],
            "payout_pct": rule["payout_pct"],
            "payout_display": f"{int(rule['payout_pct'] * 100)}% of your tier's max payout",
            "description": rule["description"],
            "example": _threshold_example(name, rule),
        })

    return {
        "total_triggers": len(thresholds_out),
        "trigger_types": ["rain", "aqi", "heat", "flood", "curfew"],
        "thresholds": thresholds_out,
        "transparency_note": (
            "All trigger conditions are fixed, objective, and publicly auditable. "
            "Payouts are initiated automatically — no claims form, no agent, no delay."
        ),
        "cooling_period_note": (
            "First-ever policy: payouts are 50% for the first 72 hours from purchase "
            "(anti-adverse-selection safeguard)."
        ),
    }


def _threshold_example(name: str, rule: dict) -> str:
    """Generate a human-readable example for a threshold rule."""
    examples = {
        "heavy_rain": "If 30mm of rain falls in a 3-hour window, Basic plan pays ₹300, Standard ₹450.",
        "moderate_rain": "If 18mm of rain falls in 3 hours, Standard pays ₹270 (60% of ₹450).",
        "severe_aqi": "If Delhi AQI hits 387, Ultra plan auto-pays ₹800 to all Ultra riders in the zone.",
        "bad_aqi": "If Mumbai AQI is 315, Basic riders receive ₹150 (50% of ₹300).",
        "extreme_heat": "If Jaipur hits 46°C, all active policies in Jaipur pay out at 100%.",
        "high_heat": "If temperature is 43.5°C, Premium riders get ₹360 (60% of ₹600).",
        "flood_warning": "When a flood warning is declared for Dadar, all Dadar riders get full payout.",
        "curfew": "During a curfew, all policies in the affected zone pay out at 100%.",
    }
    return examples.get(name, f"When {rule['metric']} ≥ {rule['threshold']} {rule['unit']}.")


# ═════════════════════════════════════════════════════════════════════════════
# GET /weather — Current weather for user's zone
# ═════════════════════════════════════════════════════════════════════════════
@router.get(
    "/weather",
    summary="Current weather in your zone",
)
def get_weather(
    include_forecast: bool = Query(False, description="Include 7-day forecast"),
    user: User = Depends(get_current_user),
):
    """
    Return current weather data for the authenticated user's city.

    Data comes from OpenWeatherMap (if API key configured) or
    realistic mock data with 30-minute caching.
    """
    weather = get_current_weather(user.city)
    response = {
        "city": user.city,
        "sub_zone": user.sub_zone,
        "weather": weather,
    }
    if include_forecast:
        response["forecast_7_days"] = get_forecast(user.city, days=7)
    return response


# ═════════════════════════════════════════════════════════════════════════════
# GET /aqi — Current AQI for user's zone
# ═════════════════════════════════════════════════════════════════════════════
@router.get(
    "/aqi",
    summary="Current AQI in your zone",
)
def get_aqi_endpoint(
    include_trend: bool = Query(False, description="Include 7-day AQI trend"),
    user: User = Depends(get_current_user),
):
    """
    Return current AQI data for the authenticated user's city.

    Includes component breakdown (PM2.5, PM10, NO2, CO, SO2)
    and a delivery worker health advisory.
    """
    aqi_data = get_aqi(user.city)
    response = {
        "city": user.city,
        "sub_zone": user.sub_zone,
        "aqi": aqi_data,
    }
    if include_trend:
        response["trend_7_days"] = get_aqi_trend(user.city, days=7)
    return response
