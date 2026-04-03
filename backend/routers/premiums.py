"""
Premium Calculation Router
==========================
Endpoints to compute and retrieve personalised premiums based on
zone risk, season, trust score, and claim history.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import PremiumCalculation, User
from schemas import PremiumCalcRequest, PremiumCalcResponse
from config import (
    POLICY_TIERS,
    ZONE_RISK_MULTIPLIERS,
    SEASONAL_MULTIPLIERS,
)

router = APIRouter(prefix="/premiums", tags=["Premium Calculations"])


def _calculate_premium(
    user: User,
    tier: str,
    now: datetime | None = None,
) -> dict:
    """
    Compute a personalised weekly premium for the given user and tier.

    Returns a dict with all breakdown fields.

    Formula::

        final = base_rate
                × zone_risk_multiplier
                × seasonal_multiplier
                × (1 - trust_discount)
                × claim_history_factor
    """
    if now is None:
        now = datetime.utcnow()

    base_rate = POLICY_TIERS[tier]["weekly_premium"]
    zone_risk = ZONE_RISK_MULTIPLIERS.get(user.city, 1.0)
    seasonal = SEASONAL_MULTIPLIERS.get(now.month, 1.0)

    # Trust discount: higher trust → bigger discount (max 15%)
    trust_discount = min(0.15, (user.trust_score / 100) * 0.15)

    # Claim history factor: more frequent claims → higher premium
    if user.total_claims <= 2:
        claim_factor = 1.0
    elif user.total_claims <= 5:
        claim_factor = 1.10
    elif user.total_claims <= 10:
        claim_factor = 1.25
    else:
        claim_factor = 1.40

    # If user has fraud flags, penalise further
    if user.fraud_flags > 0:
        claim_factor += 0.05 * user.fraud_flags

    final = round(
        base_rate * zone_risk * seasonal * (1 - trust_discount) * claim_factor,
        2,
    )

    return {
        "base_rate": base_rate,
        "zone_risk_multiplier": zone_risk,
        "seasonal_multiplier": seasonal,
        "trust_discount": round(trust_discount, 4),
        "claim_history_factor": round(claim_factor, 4),
        "final_premium": final,
    }


@router.post(
    "/calculate",
    response_model=PremiumCalcResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate a personalised premium",
)
def calculate_premium(
    payload: PremiumCalcRequest,
    db: Session = Depends(get_db),
):
    """
    Compute a personalised weekly premium for a user and a given tier.

    Persists the calculation for audit/transparency purposes.
    """
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {payload.user_id} not found.",
        )

    breakdown = _calculate_premium(user, payload.tier.value)

    calc = PremiumCalculation(
        user_id=user.id,
        **breakdown,
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


@router.get(
    "/",
    response_model=List[PremiumCalcResponse],
    summary="List premium calculations",
)
def list_premium_calculations(
    user_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve historical premium calculations."""
    query = db.query(PremiumCalculation)
    if user_id is not None:
        query = query.filter(PremiumCalculation.user_id == user_id)
    return (
        query.order_by(PremiumCalculation.calculated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{calc_id}",
    response_model=PremiumCalcResponse,
    summary="Get premium calculation by ID",
)
def get_premium_calculation(calc_id: int, db: Session = Depends(get_db)):
    """Retrieve a single premium calculation by its ID."""
    calc = db.query(PremiumCalculation).filter(PremiumCalculation.id == calc_id).first()
    if not calc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Premium calculation with id {calc_id} not found.",
        )
    return calc
