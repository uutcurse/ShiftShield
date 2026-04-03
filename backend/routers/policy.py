"""
ShiftShield Policy Lifecycle Router
====================================
Complete policy management with smart pricing, pro-rated upgrades,
and anti-fraud business rules.

Endpoints:
  POST   /api/policy/create      — Purchase new policy (dynamic price)
  GET    /api/policy/active       — View active policy + real-time stats
  GET    /api/policy/history      — Last 12 weeks of policy history
  POST   /api/policy/renew        — Renew for next week (re-priced)
  PUT    /api/policy/auto-renew   — Toggle auto-renewal
  POST   /api/policy/upgrade      — Mid-week tier upgrade (pro-rated)
  DELETE /api/policy/cancel       — Cancel policy (coverage until week end)

Business Rules:
  - ONE active policy per user
  - No purchase during active trigger events (anti-adverse-selection)
  - 72-hour cooling period on first-ever purchase (50% payout)
  - Policy week: Monday 06:00 → Sunday 23:59 IST
  - Saturday renewal notification (mock)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone, time as dt_time
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Claim,
    ClaimStatus,
    Policy,
    TriggerEvent,
    User,
)
from routers.auth import get_current_user
from services.premium_engine import PremiumEngine, TIER_CONFIG

router = APIRouter(prefix="/policy", tags=["Policy Lifecycle"])

# IST offset (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


# ═════════════════════════════════════════════════════════════════════════════
# Schemas (local to this router for cohesion)
# ═════════════════════════════════════════════════════════════════════════════
class CreatePolicyRequest(BaseModel):
    tier: str = Field(
        "basic",
        description="Policy tier: basic, standard, premium, or ultra",
        pattern=r"^(basic|standard|premium|ultra)$",
    )


class AutoRenewRequest(BaseModel):
    auto_renew: bool = Field(..., description="Enable or disable auto-renewal")


class UpgradeRequest(BaseModel):
    new_tier: str = Field(
        ...,
        description="Target tier to upgrade to",
        pattern=r"^(basic|standard|premium|ultra)$",
    )


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════
TIER_ORDER = {"basic": 0, "standard": 1, "premium": 2, "ultra": 3}


def _get_tier_key(policy: Policy) -> str:
    """Extract tier string from Policy (handles enum or raw string)."""
    t = policy.tier
    return t.value if hasattr(t, "value") else str(t)


def _now_ist() -> datetime:
    """Current datetime in IST."""
    return datetime.now(IST)


def _policy_week_dates(reference: date | None = None) -> tuple[date, date]:
    """
    Compute the policy week window (Monday → Sunday).

    If today IS Monday, the week starts today.
    Otherwise, the week starts next Monday.

    Returns (start_date, end_date) as date objects.
    """
    today = reference or date.today()
    weekday = today.weekday()  # Monday = 0

    if weekday == 0:
        # Today is Monday — start today
        start = today
    else:
        # Start next Monday
        days_ahead = 7 - weekday
        start = today + timedelta(days=days_ahead)

    end = start + timedelta(days=6)  # Sunday
    return start, end


def _next_week_dates(current_end: date) -> tuple[date, date]:
    """Given a policy end date (Sunday), return next week's Mon–Sun."""
    next_monday = current_end + timedelta(days=1)
    next_sunday = next_monday + timedelta(days=6)
    return next_monday, next_sunday


def _get_active_policy(user: User, db: Session) -> Policy | None:
    """Return the user's currently active policy, or None."""
    return (
        db.query(Policy)
        .filter(
            Policy.user_id == user.id,
            Policy.is_active == True,  # noqa: E712
        )
        .first()
    )


def _check_active_trigger_event(user: User, db: Session) -> TriggerEvent | None:
    """
    Anti-adverse-selection: check if any trigger event fired in the
    user's zone in the last 6 hours.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
    return (
        db.query(TriggerEvent)
        .filter(
            TriggerEvent.zone == user.city,
            TriggerEvent.sub_zone == user.sub_zone,
            TriggerEvent.triggered_at >= cutoff,
        )
        .first()
    )


def _count_week_claims(policy: Policy, db: Session) -> tuple[int, float]:
    """
    Count non-rejected claims and total payouts for the current policy week.

    Returns (claim_count, total_payout).
    """
    claims = (
        db.query(Claim)
        .filter(
            Claim.policy_id == policy.id,
            Claim.status != ClaimStatus.REJECTED,
        )
        .all()
    )
    count = len(claims)
    payout = sum(c.payout_amount for c in claims)
    return count, round(payout, 2)


def _is_first_ever_policy(user: User, db: Session) -> bool:
    """Check if this is the user's first-ever policy purchase."""
    count = db.query(Policy).filter(Policy.user_id == user.id).count()
    return count == 0


def _is_within_cooling_period(policy: Policy) -> bool:
    """
    Check if the policy is within the 72-hour cooling period.
    Only applies to the user's very first policy.
    """
    if not policy.created_at:
        return False
    created = policy.created_at
    now = datetime.now(timezone.utc)
    if created.tzinfo is None:
        now = now.replace(tzinfo=None)
    return (now - created) < timedelta(hours=72)


def _coverage_status(policy: Policy, db: Session) -> str:
    """Determine the real-time coverage status."""
    today = date.today()
    if not policy.is_active:
        return "cancelled"
    if today > policy.end_date:
        return "expired"
    claim_count, _ = _count_week_claims(policy, db)
    if claim_count >= policy.max_events_per_week:
        return "exhausted"
    return "active"


def _days_remaining(policy: Policy) -> int:
    """Days remaining in the policy period, inclusive of today."""
    today = date.today()
    if today > policy.end_date:
        return 0
    return (policy.end_date - today).days + 1


def _build_policy_response(
    policy: Policy,
    db: Session,
    premium_breakdown: dict | None = None,
) -> dict:
    """Build a rich policy response with real-time stats."""
    tier_key = _get_tier_key(policy)
    claim_count, total_payout = _count_week_claims(policy, db)
    status_val = _coverage_status(policy, db)
    days_left = _days_remaining(policy)

    cooling = False
    if _is_within_cooling_period(policy):
        # Check if this is the user's first policy
        first_policy_count = (
            db.query(Policy)
            .filter(Policy.user_id == policy.user_id)
            .count()
        )
        if first_policy_count == 1:
            cooling = True

    response = {
        "policy_id": policy.id,
        "tier": tier_key,
        "tier_label": TIER_CONFIG.get(tier_key, {}).get("label", tier_key.title()),
        "weekly_premium": policy.weekly_premium,
        "max_payout_per_event": policy.max_payout_per_event,
        "max_events_per_week": policy.max_events_per_week,
        "start_date": policy.start_date.isoformat(),
        "end_date": policy.end_date.isoformat(),
        "is_active": policy.is_active,
        "auto_renew": policy.auto_renew,
        "coverage_status": status_val,
        "days_remaining": days_left,
        "events_covered_this_week": claim_count,
        "events_remaining": max(0, policy.max_events_per_week - claim_count),
        "total_payout_this_week": total_payout,
        "cooling_period_active": cooling,
        "cooling_note": (
            "First-ever policy: payouts are 50% for the first 72 hours "
            "as a cooling-period safeguard."
        ) if cooling else None,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
    }

    if premium_breakdown:
        response["premium_breakdown"] = premium_breakdown

    return response


# ═════════════════════════════════════════════════════════════════════════════
# POST /create — Purchase new policy
# ═════════════════════════════════════════════════════════════════════════════
@router.post(
    "/create",
    summary="Purchase a new policy",
    status_code=status.HTTP_201_CREATED,
)
def create_policy(
    payload: CreatePolicyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Purchase a new weekly insurance policy.

    **Business rules enforced:**
    1. Only ONE active policy per user.
    2. Cannot purchase during an active trigger event in your zone
       (anti-adverse-selection).
    3. First-ever purchase activates a 72-hour cooling period
       (payouts are 50% during this window).

    **Policy timing:**
    - If today is Monday → starts today at 06:00 IST
    - Otherwise → starts next Monday at 06:00 IST
    - Ends Sunday at 23:59 IST

    The premium is dynamically calculated by the AI pricing engine.
    """
    tier = payload.tier.lower()

    # Rule 1: One active policy at a time
    existing = _get_active_policy(user, db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "You already have an active policy.",
                "active_policy_id": existing.id,
                "tier": _get_tier_key(existing),
                "ends_on": existing.end_date.isoformat(),
                "hint": "Cancel or wait for expiry, or use /upgrade to change tier.",
            },
        )

    # Rule 2: Anti-adverse-selection
    active_trigger = _check_active_trigger_event(user, db)
    if active_trigger:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Cannot purchase policy during an active weather event.",
                "reason": "Anti-adverse-selection rule",
                "trigger_type": (
                    active_trigger.trigger_type.value
                    if hasattr(active_trigger.trigger_type, "value")
                    else str(active_trigger.trigger_type)
                ),
                "zone": f"{active_trigger.zone}/{active_trigger.sub_zone}",
                "triggered_at": active_trigger.triggered_at.isoformat(),
                "hint": "Please try again after the weather event subsides (6-hour window).",
            },
        )

    # Calculate dynamic premium
    engine = PremiumEngine(db=db)
    breakdown = engine.calculate_premium(user, tier)

    # Determine policy week
    start_date, end_date = _policy_week_dates()
    is_first = _is_first_ever_policy(user, db)

    # Create policy
    policy = Policy(
        user_id=user.id,
        tier=tier,
        weekly_premium=breakdown["final_weekly_premium"],
        max_payout_per_event=breakdown["max_payout_per_event"],
        max_events_per_week=breakdown["max_events_per_week"],
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        auto_renew=True,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    # Build response
    response = _build_policy_response(policy, db, premium_breakdown=breakdown)

    # Add purchase metadata
    response["purchase_summary"] = {
        "premium_charged": breakdown["final_weekly_premium"],
        "currency": "INR",
        "payment_status": "success (mock)",
        "coverage_starts": f"{start_date.isoformat()} 06:00 IST",
        "coverage_ends": f"{end_date.isoformat()} 23:59 IST",
        "is_first_ever_policy": is_first,
    }

    if is_first:
        response["purchase_summary"]["cooling_period"] = {
            "active": True,
            "duration": "72 hours from purchase",
            "effect": "Payouts are 50% during this window",
            "reason": (
                "New customer safeguard — protects the pool against "
                "immediate adverse claims."
            ),
        }

    return response


# ═════════════════════════════════════════════════════════════════════════════
# GET /active — View active policy + real-time stats
# ═════════════════════════════════════════════════════════════════════════════
@router.get(
    "/active",
    summary="View current active policy",
)
def get_active_policy(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the user's active policy with real-time coverage statistics.

    Includes:
    - Days remaining in current week
    - Events covered vs remaining
    - Total payout received this week
    - Coverage status: `active`, `expired`, `exhausted`, `cancelled`
    - Cooling period indicator (first 72 hours of first policy)
    - Saturday renewal reminder
    """
    policy = _get_active_policy(user, db)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "No active policy found.",
                "hint": "Use POST /api/policy/create to purchase a policy.",
            },
        )

    response = _build_policy_response(policy, db)

    # Saturday renewal reminder
    now = _now_ist()
    if now.weekday() == 5 and policy.auto_renew:  # Saturday
        response["renewal_reminder"] = {
            "message": "📢 Your policy expires tomorrow! Auto-renewal is ON.",
            "next_premium_estimate": "Use GET /api/premium/calculate to see next week's price.",
        }
    elif now.weekday() == 5 and not policy.auto_renew:
        response["renewal_reminder"] = {
            "message": (
                "⚠️ Your policy expires tomorrow and auto-renewal is OFF. "
                "Use POST /api/policy/renew to continue coverage."
            ),
        }

    # Net benefit calculation
    claim_count, total_payout = _count_week_claims(policy, db)
    net = round(total_payout - policy.weekly_premium, 2)
    response["weekly_summary"] = {
        "premium_paid": policy.weekly_premium,
        "total_payouts": total_payout,
        "net_benefit": net,
        "net_status": "profit" if net > 0 else ("break-even" if net == 0 else "cost"),
    }

    return response


# ═════════════════════════════════════════════════════════════════════════════
# GET /history — Last 12 weeks of policies
# ═════════════════════════════════════════════════════════════════════════════
@router.get(
    "/history",
    summary="View policy history (last 12 weeks)",
)
def get_policy_history(
    weeks: int = Query(12, ge=1, le=52, description="Number of weeks to look back"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the user's policy history with per-week financial breakdown.

    Each entry includes:
    - Premium paid
    - Claims triggered
    - Payouts received
    - Net benefit (payouts − premium)
    - Tier active that week

    Also shows aggregate totals for the entire period.
    """
    policies = (
        db.query(Policy)
        .filter(Policy.user_id == user.id)
        .order_by(Policy.start_date.desc())
        .limit(weeks)
        .all()
    )

    history = []
    total_premiums = 0.0
    total_payouts = 0.0
    total_claims_count = 0

    for pol in policies:
        tier_key = _get_tier_key(pol)

        # Get claims for this policy
        claims = (
            db.query(Claim)
            .filter(
                Claim.policy_id == pol.id,
                Claim.status != ClaimStatus.REJECTED,
            )
            .all()
        )

        claim_count = len(claims)
        payout_sum = round(sum(c.payout_amount for c in claims), 2)
        net = round(payout_sum - pol.weekly_premium, 2)

        total_premiums += pol.weekly_premium
        total_payouts += payout_sum
        total_claims_count += claim_count

        history.append({
            "policy_id": pol.id,
            "tier": tier_key,
            "week": f"{pol.start_date.isoformat()} → {pol.end_date.isoformat()}",
            "start_date": pol.start_date.isoformat(),
            "end_date": pol.end_date.isoformat(),
            "premium_paid": pol.weekly_premium,
            "claims_triggered": claim_count,
            "payouts_received": payout_sum,
            "net_benefit": net,
            "net_indicator": "✅ Profit" if net > 0 else ("➖ Break-even" if net == 0 else "💸 Cost"),
            "was_active": pol.is_active,
            "auto_renew": pol.auto_renew,
        })

    total_net = round(total_payouts - total_premiums, 2)

    return {
        "user_id": user.id,
        "weeks_shown": len(history),
        "history": history,
        "aggregate": {
            "total_premiums_paid": round(total_premiums, 2),
            "total_payouts_received": round(total_payouts, 2),
            "total_claims": total_claims_count,
            "net_benefit": total_net,
            "net_indicator": (
                "✅ You've received more than you paid!"
                if total_net > 0
                else (
                    "➖ Equal value"
                    if total_net == 0
                    else "💸 Premium investment — protection has a cost"
                )
            ),
            "average_weekly_premium": (
                round(total_premiums / len(history), 2) if history else 0
            ),
            "claim_rate": (
                f"{(total_claims_count / len(history)):.1f} claims/week"
                if history
                else "N/A"
            ),
        },
    }


# ═════════════════════════════════════════════════════════════════════════════
# POST /renew — Renew for next week
# ═════════════════════════════════════════════════════════════════════════════
@router.post(
    "/renew",
    summary="Renew policy for next week",
)
def renew_policy(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Renew the current policy for the next week.

    The premium is **recalculated** — the price may change due to:
    - Seasonal shifts (e.g., monsoon onset)
    - Updated weather forecast
    - Loyalty discount upgrades
    - Claim history changes

    Returns a week-over-week price comparison with reasons for change.
    """
    old_policy = _get_active_policy(user, db)
    if not old_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "No active policy to renew.",
                "hint": "Use POST /api/policy/create to purchase a new policy.",
            },
        )

    old_tier = _get_tier_key(old_policy)
    old_premium = old_policy.weekly_premium

    # Anti-adverse-selection check
    active_trigger = _check_active_trigger_event(user, db)
    if active_trigger:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Cannot renew during an active weather event.",
                "reason": "Anti-adverse-selection rule",
                "hint": "Try again after the event subsides.",
            },
        )

    # Deactivate old policy
    old_policy.is_active = False
    old_policy.auto_renew = False

    # Calculate new premium
    engine = PremiumEngine(db=db)
    breakdown = engine.calculate_premium(user, old_tier)
    new_premium = breakdown["final_weekly_premium"]

    # Determine next week dates
    next_start, next_end = _next_week_dates(old_policy.end_date)

    # Create renewed policy
    new_policy = Policy(
        user_id=user.id,
        tier=old_tier,
        weekly_premium=new_premium,
        max_payout_per_event=breakdown["max_payout_per_event"],
        max_events_per_week=breakdown["max_events_per_week"],
        start_date=next_start,
        end_date=next_end,
        is_active=True,
        auto_renew=True,
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)

    # Price comparison
    price_diff = new_premium - old_premium
    pct_change = round((price_diff / old_premium) * 100, 1) if old_premium > 0 else 0

    # Generate change reasons
    change_reasons = []
    if abs(price_diff) < 1:
        change_reasons.append("No significant price change — your risk profile is stable.")
    else:
        for expl in breakdown.get("factors_explanation", []):
            if ("+" in expl and price_diff > 0) or ("-" in expl and price_diff < 0):
                change_reasons.append(expl)
        if not change_reasons:
            change_reasons = breakdown.get("factors_explanation", [])[:3]

    response = _build_policy_response(new_policy, db, premium_breakdown=breakdown)
    response["renewal_comparison"] = {
        "last_week_premium": old_premium,
        "this_week_premium": new_premium,
        "price_difference": round(price_diff, 2),
        "percentage_change": pct_change,
        "direction": (
            "⬆️ increased" if price_diff > 0
            else ("⬇️ decreased" if price_diff < 0 else "➡️ unchanged")
        ),
        "reasons": change_reasons,
        "old_policy_id": old_policy.id,
    }
    response["payment"] = {
        "amount": new_premium,
        "currency": "INR",
        "status": "success (mock)",
        "coverage": f"{next_start.isoformat()} → {next_end.isoformat()}",
    }

    return response


# ═════════════════════════════════════════════════════════════════════════════
# PUT /auto-renew — Toggle auto-renewal
# ═════════════════════════════════════════════════════════════════════════════
@router.put(
    "/auto-renew",
    summary="Toggle auto-renewal on/off",
)
def toggle_auto_renew(
    payload: AutoRenewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Enable or disable automatic weekly renewal for the active policy.

    When enabled, the policy automatically renews every Sunday night
    with a recalculated premium for the upcoming week.
    """
    policy = _get_active_policy(user, db)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active policy found.",
        )

    old_value = policy.auto_renew
    policy.auto_renew = payload.auto_renew
    db.commit()
    db.refresh(policy)

    return {
        "message": (
            "Auto-renewal enabled ✅" if payload.auto_renew
            else "Auto-renewal disabled ⚠️"
        ),
        "auto_renew": policy.auto_renew,
        "previous_value": old_value,
        "policy_id": policy.id,
        "note": (
            "Your policy will automatically renew next Sunday with a recalculated premium."
            if payload.auto_renew
            else (
                "Your policy will expire at the end of this week. "
                "Use POST /api/policy/renew to manually continue coverage."
            )
        ),
    }


# ═════════════════════════════════════════════════════════════════════════════
# POST /upgrade — Mid-week tier upgrade
# ═════════════════════════════════════════════════════════════════════════════
@router.post(
    "/upgrade",
    summary="Upgrade tier mid-week (pro-rated)",
)
def upgrade_policy(
    payload: UpgradeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upgrade (or downgrade) the policy tier mid-week.

    **Pro-ration logic:**
    - Calculates the premium difference between old and new tier
    - Pro-rates based on remaining days in the week
    - Immediately applies the new tier's higher coverage limits

    Example: Upgrading from Basic (₹89/wk) to Premium (₹180/wk) on
    Wednesday with 4 days remaining:
      pro_rated_charge = (180 - 89) × (4/7) = ₹52
    """
    new_tier = payload.new_tier.lower()

    policy = _get_active_policy(user, db)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active policy to upgrade.",
        )

    old_tier = _get_tier_key(policy)

    if new_tier == old_tier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already on the {old_tier} tier. No change needed.",
        )

    if new_tier not in TIER_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tier '{new_tier}'.",
        )

    # Determine direction
    is_upgrade = TIER_ORDER.get(new_tier, 0) > TIER_ORDER.get(old_tier, 0)

    # Calculate new premium
    engine = PremiumEngine(db=db)
    new_breakdown = engine.calculate_premium(user, new_tier)
    new_premium = new_breakdown["final_weekly_premium"]
    old_premium = policy.weekly_premium

    # Pro-rate
    days_left = _days_remaining(policy)
    total_days = 7
    pro_rate_fraction = days_left / total_days

    if is_upgrade:
        premium_diff = new_premium - old_premium
        pro_rated_charge = round(premium_diff * pro_rate_fraction, 2)
    else:
        # Downgrade: no refund for current week, new rate applies next renewal
        pro_rated_charge = 0.0

    # Update policy in-place
    policy.tier = new_tier
    policy.weekly_premium = new_premium
    policy.max_payout_per_event = new_breakdown["max_payout_per_event"]
    policy.max_events_per_week = new_breakdown["max_events_per_week"]

    db.commit()
    db.refresh(policy)

    response = _build_policy_response(policy, db, premium_breakdown=new_breakdown)
    response["upgrade_summary"] = {
        "direction": "⬆️ Upgrade" if is_upgrade else "⬇️ Downgrade",
        "old_tier": old_tier,
        "new_tier": new_tier,
        "old_premium": old_premium,
        "new_premium": new_premium,
        "days_remaining_in_week": days_left,
        "pro_rated_charge": pro_rated_charge,
        "pro_rate_note": (
            f"Charged ₹{pro_rated_charge} for {days_left} remaining days "
            f"at the higher rate."
            if is_upgrade and pro_rated_charge > 0
            else (
                "No additional charge. New rate applies from next renewal."
                if not is_upgrade
                else "No additional charge required."
            )
        ),
        "coverage_change": {
            "max_payout_per_event": {
                "before": TIER_CONFIG.get(old_tier, {}).get("max_payout_per_event", "?"),
                "after": new_breakdown["max_payout_per_event"],
            },
            "max_events_per_week": {
                "before": TIER_CONFIG.get(old_tier, {}).get("max_events_per_week", "?"),
                "after": new_breakdown["max_events_per_week"],
            },
        },
        "effective_immediately": True,
        "payment_status": "success (mock)" if pro_rated_charge > 0 else "no charge",
    }

    return response


# ═════════════════════════════════════════════════════════════════════════════
# DELETE /cancel — Cancel current policy
# ═════════════════════════════════════════════════════════════════════════════
@router.delete(
    "/cancel",
    summary="Cancel current policy",
)
def cancel_policy(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel the active policy.

    **Important:**
    - No refund (weekly model).
    - Coverage continues until the end of the current week
      (Sunday 23:59 IST).
    - Auto-renewal is turned off.
    - The policy remains in history for record-keeping.
    """
    policy = _get_active_policy(user, db)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active policy to cancel.",
        )

    tier_key = _get_tier_key(policy)
    days_left = _days_remaining(policy)

    # Deactivate
    policy.is_active = False
    policy.auto_renew = False
    db.commit()

    return {
        "message": "Policy cancelled successfully.",
        "policy_id": policy.id,
        "tier": tier_key,
        "cancellation_details": {
            "effective_date": date.today().isoformat(),
            "coverage_continues_until": f"{policy.end_date.isoformat()} 23:59 IST",
            "days_of_remaining_coverage": days_left,
            "refund_amount": 0,
            "refund_note": "No refunds for partial weeks in the weekly billing model.",
            "auto_renew_disabled": True,
        },
        "reactivation_note": (
            "You can purchase a new policy anytime using POST /api/policy/create."
        ),
    }
