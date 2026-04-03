"""
Claims Router
=============
Endpoints to initiate, list, and manage parametric insurance claims.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Claim, Policy, User, ClaimStatus, TriggerType
from routers.auth import get_current_user
from schemas import (
    ClaimCreate,
    ClaimResponse,
    ClaimUpdateStatus,
    MessageResponse,
)

router = APIRouter(prefix="/claims", tags=["Claims"])


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _compute_payout(
    trigger_value: float,
    threshold_value: float,
    max_payout: float,
) -> float:
    """
    Compute payout proportional to how far the trigger value exceeds the
    threshold, capped at the policy's max_payout_per_event.

    Formula: payout = max_payout × min(1.0, excess_ratio)
    where excess_ratio = (trigger_value - threshold) / threshold
    """
    if trigger_value <= threshold_value:
        return 0.0
    excess_ratio = (trigger_value - threshold_value) / threshold_value
    return round(min(max_payout, max_payout * min(1.0, excess_ratio)), 2)


def _compute_fraud_score(user: User, payout: float) -> float:
    """
    Lightweight fraud-risk score (0–100).

    Factors:
    - Low trust → higher score
    - Many past fraud flags → higher score
    - High payout relative to total → higher score
    """
    score = 0.0

    # Trust component (0–40)
    score += max(0, (100 - user.trust_score)) * 0.4

    # Fraud flag component (0–30)
    score += min(30, user.fraud_flags * 10)

    # Payout velocity (0–30)
    if user.total_payouts > 0 and user.total_claims > 0:
        avg_payout = user.total_payouts / user.total_claims
        if payout > avg_payout * 2:
            score += 20
        elif payout > avg_payout * 1.5:
            score += 10

    return round(min(100, score), 2)


def _get_claim_or_404(claim_id: int, db: Session) -> Claim:
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with id {claim_id} not found.",
        )
    return claim


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a new claim",
)
def create_claim(payload: ClaimCreate, db: Session = Depends(get_db)):
    """
    Initiate an insurance claim against an active policy.

    The claim is auto-approved if the user's fraud score is low (<20)
    and the trigger value exceeds the threshold.  Otherwise it's placed
    under review.
    """
    # Validate policy
    policy = db.query(Policy).filter(Policy.id == payload.policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {payload.policy_id} not found.",
        )
    if not policy.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot file a claim against an inactive policy.",
        )

    # Validate user
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {payload.user_id} not found.",
        )
    if policy.user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Policy does not belong to the specified user.",
        )

    # Check weekly claim limit
    weekly_claims = (
        db.query(Claim)
        .filter(
            Claim.policy_id == policy.id,
            Claim.status.notin_([ClaimStatus.REJECTED]),
        )
        .count()
    )
    if weekly_claims >= policy.max_events_per_week:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Weekly claim limit ({policy.max_events_per_week}) reached "
                f"for policy {policy.id}."
            ),
        )

    # Compute payout
    payout = _compute_payout(
        payload.trigger_value,
        payload.threshold_value,
        policy.max_payout_per_event,
    )
    if payout <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Trigger value ({payload.trigger_value}) does not exceed "
                f"threshold ({payload.threshold_value}). No payout applicable."
            ),
        )

    # Fraud scoring
    fraud_score = _compute_fraud_score(user, payout)

    # Auto-approve if low fraud risk and trust is high
    claim_status = (
        ClaimStatus.AUTO_APPROVED
        if fraud_score < 20 and user.trust_score >= 70
        else ClaimStatus.UNDER_REVIEW
    )

    claim = Claim(
        policy_id=payload.policy_id,
        user_id=payload.user_id,
        trigger_type=payload.trigger_type.value,
        trigger_value=payload.trigger_value,
        threshold_value=payload.threshold_value,
        payout_amount=payout,
        status=claim_status,
        fraud_score=fraud_score,
    )
    db.add(claim)

    # Update user stats
    user.total_claims += 1
    if claim_status == ClaimStatus.AUTO_APPROVED:
        user.total_payouts += payout

    db.commit()
    db.refresh(claim)
    return claim


@router.get(
    "/my-claims",
    response_model=List[ClaimResponse],
    summary="Get user's recent claims",
)
def get_my_claims(
    limit: int = Query(5, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's recent claims (default 5 for dashboard)."""
    return (
        db.query(Claim)
        .filter(Claim.user_id == user.id)
        .order_by(Claim.initiated_at.desc())
        .limit(limit)
        .all()
    )


@router.get(
    "/",
    response_model=List[ClaimResponse],
    summary="List claims",
)
def list_claims(
    user_id: Optional[int] = Query(None),
    policy_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    trigger_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return a paginated list of claims with optional filters."""
    query = db.query(Claim)
    if user_id is not None:
        query = query.filter(Claim.user_id == user_id)
    if policy_id is not None:
        query = query.filter(Claim.policy_id == policy_id)
    if status_filter:
        query = query.filter(Claim.status == status_filter)
    if trigger_type:
        query = query.filter(Claim.trigger_type == trigger_type)
    return query.order_by(Claim.initiated_at.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{claim_id}",
    response_model=ClaimResponse,
    summary="Get claim by ID",
)
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    """Retrieve a single claim by its ID."""
    return _get_claim_or_404(claim_id, db)


@router.patch(
    "/{claim_id}/status",
    response_model=ClaimResponse,
    summary="Update claim status (admin)",
)
def update_claim_status(
    claim_id: int,
    payload: ClaimUpdateStatus,
    db: Session = Depends(get_db),
):
    """
    Admin endpoint to approve, reject, or mark a claim as paid.

    When marking as 'paid', a payment_ref should be provided.
    """
    claim = _get_claim_or_404(claim_id, db)

    # Validate state transitions
    valid_transitions = {
        ClaimStatus.UNDER_REVIEW: {ClaimStatus.APPROVED, ClaimStatus.REJECTED},
        ClaimStatus.AUTO_APPROVED: {ClaimStatus.PAID, ClaimStatus.REJECTED},
        ClaimStatus.APPROVED: {ClaimStatus.PAID, ClaimStatus.REJECTED},
    }

    current = claim.status
    target = ClaimStatus(payload.status.value)

    allowed = valid_transitions.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition from '{current.value}' to '{target.value}'. "
                f"Allowed: {[s.value for s in allowed] if allowed else 'none'}."
            ),
        )

    claim.status = target

    if target == ClaimStatus.PAID:
        claim.paid_at = datetime.now(timezone.utc)
        if payload.payment_ref:
            claim.payment_ref = payload.payment_ref

        # Update user total_payouts if not already counted (from auto_approved)
        if current != ClaimStatus.AUTO_APPROVED:
            user = db.query(User).filter(User.id == claim.user_id).first()
            if user:
                user.total_payouts += claim.payout_amount

    elif target == ClaimStatus.REJECTED:
        # If it was auto-approved or approved, reverse the payout stat
        if current in (ClaimStatus.AUTO_APPROVED, ClaimStatus.APPROVED):
            user = db.query(User).filter(User.id == claim.user_id).first()
            if user:
                user.total_payouts = max(0, user.total_payouts - claim.payout_amount)
                user.fraud_flags += 1
                user.trust_score = max(0, user.trust_score - 5)

    db.commit()
    db.refresh(claim)
    return claim
