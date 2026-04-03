"""
User Router
===========
CRUD endpoints for gig worker user management.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import (
    MessageResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from config import ZONES, CITY_NAMES

router = APIRouter(prefix="/users", tags=["Users"])


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _validate_location(city: str, zone: str, sub_zone: str) -> None:
    """Raise 422 if the city/zone/sub_zone combination is invalid."""
    if city not in ZONES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported city '{city}'. Must be one of {CITY_NAMES}.",
        )
    # For this platform zone == city (the city *is* the zone)
    if zone != city:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Zone must match the city. Got zone='{zone}' for city='{city}'.",
        )
    if sub_zone not in ZONES[city]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Sub-zone '{sub_zone}' is not valid for {city}. "
                f"Valid sub-zones: {ZONES[city]}"
            ),
        )


def _get_user_or_404(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )
    return user


# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new gig worker",
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new delivery worker on ShiftShield.

    Validates that the city, zone, and sub-zone are supported,
    and that the phone number is unique.
    """
    _validate_location(payload.city, payload.zone, payload.sub_zone)

    # Check duplicate phone
    existing = db.query(User).filter(User.phone == payload.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Phone number {payload.phone} is already registered.",
        )

    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users",
)
def list_users(
    city: Optional[str] = Query(None, description="Filter by city"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return a paginated list of registered users, optionally filtered."""
    query = db.query(User)
    if city:
        query = query.filter(User.city == city)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieve a single user by their ID."""
    return _get_user_or_404(user_id, db)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user profile",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
):
    """
    Partially update a user's profile.

    Only supplied fields are updated; omitted fields remain unchanged.
    """
    user = _get_user_or_404(user_id, db)
    update_data = payload.model_dump(exclude_unset=True)

    # If location fields are being changed, re-validate the combination
    new_city = update_data.get("city", user.city)
    new_zone = update_data.get("zone", user.zone)
    new_sub_zone = update_data.get("sub_zone", user.sub_zone)
    if any(k in update_data for k in ("city", "zone", "sub_zone")):
        _validate_location(new_city, new_zone, new_sub_zone)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Deactivate a user",
)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """Soft-delete: sets is_active=False rather than removing the row."""
    user = _get_user_or_404(user_id, db)
    user.is_active = False
    db.commit()
    return MessageResponse(
        message="User deactivated.",
        detail=f"User {user_id} ({user.name}) has been deactivated.",
    )
