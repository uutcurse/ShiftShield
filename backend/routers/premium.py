"""
Smart Premium Router
====================
Authenticated endpoints powered by the AI PremiumEngine.

GET /api/premium/calculate?tier=standard  — personalised premium for one tier
GET /api/premium/all-tiers                — compare all 4 tiers side-by-side
GET /api/premium/factors                  — explain what's driving your price
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from routers.auth import get_current_user
from services.premium_engine import PremiumEngine, TIER_CONFIG

router = APIRouter(prefix="/premium", tags=["Smart Pricing (AI)"])


@router.get(
    "/calculate",
    summary="Calculate personalised premium for a tier",
    response_description="Full premium breakdown with all 7 risk factors",
)
def calculate_premium(
    tier: str = Query(
        "basic",
        description="Policy tier: basic, standard, premium, or ultra",
        regex="^(basic|standard|premium|ultra)$",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute a **personalised weekly premium** for the authenticated user
    using the AI-powered PremiumEngine.

    The engine evaluates 7 risk factors in real-time:

    | # | Factor              | Range       | Source            |
    |---|---------------------|-------------|-------------------|
    | 1 | Zone base risk      | 0.8–1.6×    | Geo-risk profile  |
    | 2 | Sub-zone modifier   | 0.8–1.5×    | Micro-geography   |
    | 3 | Seasonal multiplier | 0.8–1.8×    | Month / monsoon   |
    | 4 | Trust / loyalty     | 0.9–1.6×    | Tenure + fraud    |
    | 5 | Claim history       | 0.95–1.30×  | Last 4 weeks      |
    | 6 | Weather forecast    | 0.9–1.4×    | 7-day AI predict  |
    | 7 | Tier base rate      | ₹49–₹179    | Plan selection    |

    Final premium is clamped between **₹29** (floor) and **₹299** (ceiling).
    """
    engine = PremiumEngine(db=db)
    try:
        result = engine.calculate_premium(user, tier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return result


@router.get(
    "/all-tiers",
    summary="Compare all tier prices for the user",
    response_description="Array of 4 premium breakdowns (basic → ultra)",
)
def all_tiers(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute personalised premiums for **all 4 policy tiers** simultaneously
    so the user can compare side-by-side.

    Returns an array with one breakdown per tier, each including:
    - Final weekly premium (₹)
    - Max payout per event
    - Max events per week
    - Full factor explanations

    This powers the "Choose Your Plan" comparison UI.
    """
    engine = PremiumEngine(db=db)
    tiers = engine.calculate_all_tiers(user)

    # Add a "recommended" flag (best value = tier where final_premium / max_payout ratio is lowest)
    best_value_idx = 0
    best_ratio = float("inf")
    for i, t in enumerate(tiers):
        ratio = t["final_weekly_premium"] / t["max_payout_per_event"]
        if ratio < best_ratio:
            best_ratio = ratio
            best_value_idx = i

    for i, t in enumerate(tiers):
        t["is_recommended"] = (i == best_value_idx)
        t["value_score"] = round(
            t["max_payout_per_event"] / max(t["final_weekly_premium"], 1) * 10, 1
        )

    return {
        "user_id": user.id,
        "city": user.city,
        "sub_zone": user.sub_zone,
        "tiers": tiers,
        "recommendation": tiers[best_value_idx]["tier"],
        "recommendation_reason": (
            f"{tiers[best_value_idx]['tier_label']} offers the best value: "
            f"₹{tiers[best_value_idx]['final_weekly_premium']}/week for up to "
            f"₹{tiers[best_value_idx]['max_payout_per_event']} per event"
        ),
    }


@router.get(
    "/factors",
    summary="Explain what's affecting your price",
    response_description="Categorised risk factors with actionable tips",
)
def price_factors(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a **human-readable breakdown** of every risk factor affecting
    the authenticated user's premium.

    Factors are categorised into:
    - 📈 **Increasing** your premium (and why)
    - 📉 **Decreasing** your premium (discounts)
    - ➖ **Neutral** (no effect)

    Also includes:
    - Overall risk score (0–100)
    - Risk level indicator (🟢 Low → 🔴 Very High)
    - Personalised tips to reduce premium

    This powers the "Why is my price this?" transparency UX.
    """
    engine = PremiumEngine(db=db)
    return engine.get_risk_factors_summary(user)


@router.get(
    "/tiers-info",
    summary="Get tier configuration (no auth required)",
    tags=["Reference Data"],
)
def tiers_info():
    """
    Return the base configuration for all 4 policy tiers.

    This is static reference data — no personalisation applied.
    Useful for displaying plan features before the user logs in.
    """
    return {
        "tiers": [
            {
                "tier": key,
                "label": val["label"],
                "description": val["description"],
                "base_rate": val["base_rate"],
                "max_payout_per_event": val["max_payout_per_event"],
                "max_events_per_week": val["max_events_per_week"],
            }
            for key, val in TIER_CONFIG.items()
        ],
        "pricing_note": (
            "Displayed rates are base prices. Your actual weekly premium is "
            "dynamically calculated based on location, weather forecast, "
            "loyalty status, and claim history."
        ),
        "premium_range": {"floor": 29, "ceiling": 299, "currency": "INR"},
    }
