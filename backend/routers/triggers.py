"""
Trigger Events Router
=====================
Endpoints to record and list environmental trigger events (weather, AQI, etc.)
that can automatically generate claims for affected policyholders.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import TriggerEvent, Policy, Claim, User, ClaimStatus
from schemas import (
    TriggerEventCreate,
    TriggerEventResponse,
    MessageResponse,
)
from config import ZONES, TRIGGER_THRESHOLDS

router = APIRouter(prefix="/triggers", tags=["Trigger Events"])


@router.post(
    "/",
    response_model=TriggerEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a trigger event",
)
def create_trigger_event(
    payload: TriggerEventCreate,
    db: Session = Depends(get_db),
):
    """
    Record an environmental trigger event for a zone/sub-zone.

    This simulates what the weather-polling scheduler would do:
    1. Validate the zone/sub-zone.
    2. Check if the measured value exceeds the threshold.
    3. Find all active policies for users in that sub-zone.
    4. Auto-create claims for each affected policy.
    """
    # Validate zone
    if payload.zone not in ZONES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown zone '{payload.zone}'.",
        )
    if payload.sub_zone not in ZONES[payload.zone]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown sub-zone '{payload.sub_zone}' for zone '{payload.zone}'.",
        )

    # Verify threshold breach
    if payload.measured_value <= payload.threshold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Measured value ({payload.measured_value}) does not exceed "
                f"threshold ({payload.threshold}). No trigger event created."
            ),
        )

    # Create the trigger event
    event = TriggerEvent(
        zone=payload.zone,
        sub_zone=payload.sub_zone,
        trigger_type=payload.trigger_type.value,
        measured_value=payload.measured_value,
        threshold=payload.threshold,
    )
    db.add(event)
    db.flush()  # get event.id

    # Find affected users & policies
    affected_users = (
        db.query(User)
        .filter(
            User.city == payload.zone,  # zone == city
            User.sub_zone == payload.sub_zone,
            User.is_active == True,  # noqa: E712
        )
        .all()
    )

    total_payout = 0.0
    affected_count = 0

    for user in affected_users:
        # Find the user's active policy
        policy = (
            db.query(Policy)
            .filter(
                Policy.user_id == user.id,
                Policy.is_active == True,  # noqa: E712
            )
            .first()
        )
        if not policy:
            continue

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
            continue

        # Compute payout
        excess_ratio = (payload.measured_value - payload.threshold) / payload.threshold
        payout = round(
            min(policy.max_payout_per_event, policy.max_payout_per_event * min(1.0, excess_ratio)),
            2,
        )
        if payout <= 0:
            continue

        # Fraud scoring (simplified for batch)
        fraud_score = max(0, (100 - user.trust_score)) * 0.4 + min(30, user.fraud_flags * 10)
        claim_status = (
            ClaimStatus.AUTO_APPROVED
            if fraud_score < 20 and user.trust_score >= 70
            else ClaimStatus.UNDER_REVIEW
        )

        claim = Claim(
            policy_id=policy.id,
            user_id=user.id,
            trigger_type=payload.trigger_type.value,
            trigger_value=payload.measured_value,
            threshold_value=payload.threshold,
            payout_amount=payout,
            status=claim_status,
            fraud_score=round(fraud_score, 2),
        )
        db.add(claim)

        user.total_claims += 1
        if claim_status == ClaimStatus.AUTO_APPROVED:
            user.total_payouts += payout

        total_payout += payout
        affected_count += 1

    event.affected_policies_count = affected_count
    event.total_payout = round(total_payout, 2)

    db.commit()
    db.refresh(event)
    return event


@router.get(
    "/",
    response_model=List[TriggerEventResponse],
    summary="List trigger events",
)
def list_trigger_events(
    zone: Optional[str] = Query(None),
    sub_zone: Optional[str] = Query(None),
    trigger_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return a paginated list of trigger events."""
    query = db.query(TriggerEvent)
    if zone:
        query = query.filter(TriggerEvent.zone == zone)
    if sub_zone:
        query = query.filter(TriggerEvent.sub_zone == sub_zone)
    if trigger_type:
        query = query.filter(TriggerEvent.trigger_type == trigger_type)
    return query.order_by(TriggerEvent.triggered_at.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{event_id}",
    response_model=TriggerEventResponse,
    summary="Get trigger event by ID",
)
def get_trigger_event(event_id: int, db: Session = Depends(get_db)):
    """Retrieve a single trigger event by its ID."""
    event = db.query(TriggerEvent).filter(TriggerEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger event with id {event_id} not found.",
        )
    return event
