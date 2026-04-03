"""
ShiftShield Pydantic Schemas
=============================
Request / response schemas for all API endpoints.
Uses Pydantic v2 model_config style.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


# ─────────────────────────────────────────────────────────────────────────────
# Shared Enums (mirrors models.py for validation)
# ─────────────────────────────────────────────────────────────────────────────
class PlatformEnum(str, Enum):
    swiggy = "swiggy"
    zomato = "zomato"
    both = "both"


class PolicyTierEnum(str, Enum):
    basic = "basic"
    standard = "standard"
    premium = "premium"
    ultra = "ultra"


class TriggerTypeEnum(str, Enum):
    rain = "rain"
    aqi = "aqi"
    heat = "heat"
    flood = "flood"
    curfew = "curfew"


class ClaimStatusEnum(str, Enum):
    auto_approved = "auto_approved"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    paid = "paid"


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    """Shared user fields."""
    phone: str = Field(
        ..., min_length=10, max_length=15,
        description="Indian mobile number, e.g. +919876543210",
        examples=["+919876543210"],
    )
    name: str = Field(..., min_length=1, max_length=120)
    city: str = Field(
        ..., max_length=50,
        description="Must be one of the supported cities (see config.ZONES).",
    )
    zone: str = Field(..., max_length=50)
    sub_zone: str = Field(..., max_length=80)
    platform: PlatformEnum = PlatformEnum.both
    upi_id: Optional[str] = Field(
        None, max_length=80,
        description="UPI VPA for payouts, e.g. worker@upi",
    )
    aadhaar_last4: Optional[str] = Field(
        None, min_length=4, max_length=4,
        description="Last 4 digits of Aadhaar for lightweight KYC.",
    )


class UserCreate(UserBase):
    """Payload to register a new user."""
    pass


class UserUpdate(BaseModel):
    """Partial-update payload for user profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    city: Optional[str] = Field(None, max_length=50)
    zone: Optional[str] = Field(None, max_length=50)
    sub_zone: Optional[str] = Field(None, max_length=80)
    platform: Optional[PlatformEnum] = None
    upi_id: Optional[str] = Field(None, max_length=80)
    aadhaar_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Full user object returned by the API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    is_active: bool
    trust_score: float
    total_claims: int
    total_payouts: float
    fraud_flags: int


class UserBrief(BaseModel):
    """Lightweight user reference (for nested responses)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    city: str


# ─────────────────────────────────────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────────────────────────────────────
class PolicyCreate(BaseModel):
    """Payload to purchase a new policy."""
    user_id: int
    tier: PolicyTierEnum = PolicyTierEnum.basic
    auto_renew: bool = True


class PolicyUpdate(BaseModel):
    """Partial-update payload for a policy."""
    tier: Optional[PolicyTierEnum] = None
    auto_renew: Optional[bool] = None
    is_active: Optional[bool] = None


class PolicyResponse(BaseModel):
    """Full policy object returned by the API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    tier: PolicyTierEnum
    weekly_premium: float
    max_payout_per_event: float
    max_events_per_week: int
    start_date: date
    end_date: date
    is_active: bool
    auto_renew: bool
    created_at: datetime


class PolicyBrief(BaseModel):
    """Lightweight policy reference."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tier: PolicyTierEnum
    is_active: bool
    start_date: date
    end_date: date


# ─────────────────────────────────────────────────────────────────────────────
# Claim
# ─────────────────────────────────────────────────────────────────────────────
class ClaimCreate(BaseModel):
    """Payload to initiate a new claim."""
    policy_id: int
    user_id: int
    trigger_type: TriggerTypeEnum
    trigger_value: float = Field(
        ..., gt=0,
        description="The actual measured environmental value.",
    )
    threshold_value: float = Field(
        ..., gt=0,
        description="The threshold that was exceeded.",
    )


class ClaimUpdateStatus(BaseModel):
    """Admin action to update claim status."""
    status: ClaimStatusEnum
    payment_ref: Optional[str] = None


class ClaimResponse(BaseModel):
    """Full claim object returned by the API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    user_id: int
    trigger_type: TriggerTypeEnum
    trigger_value: float
    threshold_value: float
    payout_amount: float
    status: ClaimStatusEnum
    fraud_score: float
    initiated_at: datetime
    paid_at: Optional[datetime] = None
    payment_ref: Optional[str] = None


class ClaimBrief(BaseModel):
    """Lightweight claim reference."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    trigger_type: TriggerTypeEnum
    payout_amount: float
    status: ClaimStatusEnum
    initiated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# TriggerEvent
# ─────────────────────────────────────────────────────────────────────────────
class TriggerEventCreate(BaseModel):
    """Payload to record a new environmental trigger event."""
    zone: str = Field(..., max_length=50)
    sub_zone: str = Field(..., max_length=80)
    trigger_type: TriggerTypeEnum
    measured_value: float = Field(..., gt=0)
    threshold: float = Field(..., gt=0)


class TriggerEventResponse(BaseModel):
    """Full trigger event returned by the API."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone: str
    sub_zone: str
    trigger_type: TriggerTypeEnum
    measured_value: float
    threshold: float
    triggered_at: datetime
    affected_policies_count: int
    total_payout: float


# ─────────────────────────────────────────────────────────────────────────────
# PremiumCalculation
# ─────────────────────────────────────────────────────────────────────────────
class PremiumCalcRequest(BaseModel):
    """Request to compute a personalised premium."""
    user_id: int
    tier: PolicyTierEnum = PolicyTierEnum.basic


class PremiumCalcResponse(BaseModel):
    """Detailed premium calculation breakdown."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    base_rate: float
    zone_risk_multiplier: float
    seasonal_multiplier: float
    trust_discount: float
    claim_history_factor: float
    final_premium: float
    calculated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Generic / Utility
# ─────────────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = "ok"
    version: str
    timestamp: datetime


class PaginatedResponse(BaseModel):
    """Wrapper for paginated list endpoints."""
    total: int
    page: int
    per_page: int
    items: List  # type: ignore[type-arg]  # subclassed per-endpoint


class ZonesResponse(BaseModel):
    """List of supported zones and sub-zones."""
    zones: dict[str, list[str]]


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    detail: Optional[str] = None
