"""
Policy Router
=============
Endpoints to purchase, list, update, and manage insurance policies.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Policy, User
from schemas import (
    MessageResponse,
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
)
from config import POLICY_TIERS

router = APIRouter(prefix="/policies", tags=["Policies"])


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _get_policy_or_404(policy_id: int, db: Session) -> Policy:
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with id {policy_id} not found.",
        )
    return policy


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Purchase a new policy",
)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    """
    Create a new weekly insurance policy for a user.

    Automatically populates premium and payout limits from the selected
    tier configuration.
    """
    # Validate user exists and is active
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {payload.user_id} not found.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a policy for an inactive user.",
        )

    # Check for existing active policy
    active_policy = (
        db.query(Policy)
        .filter(
            Policy.user_id == payload.user_id,
            Policy.is_active == True,  # noqa: E712
        )
        .first()
    )
    if active_policy:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"User {payload.user_id} already has an active policy "
                f"(id={active_policy.id}). Deactivate it first or wait for expiry."
            ),
        )

    tier_config = POLICY_TIERS[payload.tier.value]
    today = date.today()

    policy = Policy(
        user_id=payload.user_id,
        tier=payload.tier.value,
        weekly_premium=tier_config["weekly_premium"],
        max_payout_per_event=tier_config["max_payout_per_event"],
        max_events_per_week=tier_config["max_events_per_week"],
        start_date=today,
        end_date=today + timedelta(days=7),
        is_active=True,
        auto_renew=payload.auto_renew,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get(
    "/",
    response_model=List[PolicyResponse],
    summary="List policies",
)
def list_policies(
    user_id: Optional[int] = Query(None, description="Filter by user"),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return a paginated list of policies."""
    query = db.query(Policy)
    if user_id is not None:
        query = query.filter(Policy.user_id == user_id)
    if is_active is not None:
        query = query.filter(Policy.is_active == is_active)
    return query.order_by(Policy.created_at.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{policy_id}",
    response_model=PolicyResponse,
    summary="Get policy by ID",
)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """Retrieve a single policy by its ID."""
    return _get_policy_or_404(policy_id, db)


@router.patch(
    "/{policy_id}",
    response_model=PolicyResponse,
    summary="Update a policy",
)
def update_policy(
    policy_id: int,
    payload: PolicyUpdate,
    db: Session = Depends(get_db),
):
    """
    Update policy settings (tier, auto_renew, is_active).

    Changing the tier mid-week adjusts the remaining coverage accordingly.
    """
    policy = _get_policy_or_404(policy_id, db)
    update_data = payload.model_dump(exclude_unset=True)

    # If tier is changing, update the financial fields too
    if "tier" in update_data:
        new_tier = update_data["tier"]
        tier_config = POLICY_TIERS[new_tier if isinstance(new_tier, str) else new_tier.value]
        policy.weekly_premium = tier_config["weekly_premium"]
        policy.max_payout_per_event = tier_config["max_payout_per_event"]
        policy.max_events_per_week = tier_config["max_events_per_week"]

    for field, value in update_data.items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)
    return policy


@router.post(
    "/{policy_id}/renew",
    response_model=PolicyResponse,
    summary="Renew a policy",
)
def renew_policy(policy_id: int, db: Session = Depends(get_db)):
    """
    Manually renew an expired policy for another week.

    The old policy is deactivated and a new one is created with the same
    tier and user.
    """
    old_policy = _get_policy_or_404(policy_id, db)

    # Deactivate the old one
    old_policy.is_active = False

    today = date.today()
    tier_config = POLICY_TIERS[
        old_policy.tier if isinstance(old_policy.tier, str) else old_policy.tier.value
    ]

    new_policy = Policy(
        user_id=old_policy.user_id,
        tier=old_policy.tier,
        weekly_premium=tier_config["weekly_premium"],
        max_payout_per_event=tier_config["max_payout_per_event"],
        max_events_per_week=tier_config["max_events_per_week"],
        start_date=today,
        end_date=today + timedelta(days=7),
        is_active=True,
        auto_renew=old_policy.auto_renew,
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return new_policy


@router.delete(
    "/{policy_id}",
    response_model=MessageResponse,
    summary="Cancel a policy",
)
def cancel_policy(policy_id: int, db: Session = Depends(get_db)):
    """Deactivate (cancel) a policy. Does not delete the record."""
    policy = _get_policy_or_404(policy_id, db)
    policy.is_active = False
    policy.auto_renew = False
    db.commit()
    return MessageResponse(
        message="Policy cancelled.",
        detail=f"Policy {policy_id} has been deactivated.",
    )
