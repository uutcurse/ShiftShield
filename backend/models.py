"""
ShiftShield ORM Models
======================
SQLAlchemy models representing the core domain entities of the parametric
insurance platform for gig delivery workers.
"""

from __future__ import annotations

import enum
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────
class Platform(str, enum.Enum):
    """Delivery platform the worker operates on."""
    SWIGGY = "swiggy"
    ZOMATO = "zomato"
    BOTH = "both"


class PolicyTier(str, enum.Enum):
    """Insurance policy tier."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ULTRA = "ultra"


class TriggerType(str, enum.Enum):
    """Weather / environmental trigger types."""
    RAIN = "rain"
    AQI = "aqi"
    HEAT = "heat"
    FLOOD = "flood"
    CURFEW = "curfew"


class ClaimStatus(str, enum.Enum):
    """Lifecycle status of an insurance claim."""
    AUTO_APPROVED = "auto_approved"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────
class User(Base):
    """
    A gig delivery worker enrolled on the ShiftShield platform.

    Tracks identity, location, platform affiliation, trust score, and
    cumulative claims history.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(
        String(15), unique=True, nullable=False, index=True,
        doc="Indian mobile number (e.g. +919876543210)",
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    zone: Mapped[str] = mapped_column(
        String(50), nullable=False,
        doc="Major zone within the city (matches config.ZONES keys).",
    )
    sub_zone: Mapped[str] = mapped_column(
        String(80), nullable=False,
        doc="Sub-zone locality (matches config.ZONES[city] list).",
    )
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform), nullable=False, default=Platform.BOTH,
    )
    upi_id: Mapped[Optional[str]] = mapped_column(
        String(80), nullable=True,
        doc="UPI virtual payment address for payouts.",
    )
    aadhaar_last4: Mapped[Optional[str]] = mapped_column(
        String(4), nullable=True,
        doc="Last 4 digits of Aadhaar for lightweight KYC.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trust_score: Mapped[float] = mapped_column(
        Float, default=100.0, nullable=False,
        doc="0–100 score; lower indicates higher fraud risk.",
    )
    total_claims: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_payouts: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
        doc="Cumulative payout amount in INR.",
    )
    fraud_flags: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        doc="Number of times flagged for suspicious behaviour.",
    )

    # ORM relationships
    policies: Mapped[List["Policy"]] = relationship(
        "Policy", back_populates="user", cascade="all, delete-orphan",
    )
    claims: Mapped[List["Claim"]] = relationship(
        "Claim", back_populates="user", cascade="all, delete-orphan",
    )
    premium_calculations: Mapped[List["PremiumCalculation"]] = relationship(
        "PremiumCalculation", back_populates="user", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.phone} city={self.city}>"


# ─────────────────────────────────────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────────────────────────────────────
class Policy(Base):
    """
    An active insurance policy held by a user.

    Policies are weekly and auto-renewable. Each tier defines a premium,
    per-event payout cap, and weekly event limit.
    """

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    tier: Mapped[PolicyTier] = mapped_column(
        Enum(PolicyTier), nullable=False, default=PolicyTier.BASIC,
    )
    weekly_premium: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Weekly premium in INR.",
    )
    max_payout_per_event: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Maximum payout for a single trigger event in INR.",
    )
    max_events_per_week: Mapped[int] = mapped_column(
        Integer, nullable=False,
        doc="Cap on claimable events per policy week.",
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ORM relationships
    user: Mapped["User"] = relationship("User", back_populates="policies")
    claims: Mapped[List["Claim"]] = relationship(
        "Claim", back_populates="policy", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Policy id={self.id} user_id={self.user_id} "
            f"tier={self.tier.value} active={self.is_active}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Claim
# ─────────────────────────────────────────────────────────────────────────────
class Claim(Base):
    """
    An insurance claim triggered by an environmental event.

    Claims can be auto-approved when the trigger_value exceeds the threshold
    and the user's trust_score is high, or placed under review.
    """

    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    trigger_type: Mapped[TriggerType] = mapped_column(
        Enum(TriggerType), nullable=False,
    )
    trigger_value: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Actual measured value of the trigger parameter.",
    )
    threshold_value: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Threshold that was exceeded to trigger this claim.",
    )
    payout_amount: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Computed payout amount in INR.",
    )
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus), nullable=False, default=ClaimStatus.UNDER_REVIEW,
    )
    fraud_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
        doc="0–100 fraud probability score from the risk engine.",
    )
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    payment_ref: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True,
        doc="UPI / NEFT transaction reference once paid.",
    )

    # ORM relationships
    policy: Mapped["Policy"] = relationship("Policy", back_populates="claims")
    user: Mapped["User"] = relationship("User", back_populates="claims")

    def __repr__(self) -> str:
        return (
            f"<Claim id={self.id} type={self.trigger_type.value} "
            f"status={self.status.value} payout={self.payout_amount}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TriggerEvent
# ─────────────────────────────────────────────────────────────────────────────
class TriggerEvent(Base):
    """
    A recorded environmental trigger event for a specific zone/sub-zone.

    These are produced by the weather polling scheduler and used to
    batch-process claims for all affected policies.
    """

    __tablename__ = "trigger_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sub_zone: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    trigger_type: Mapped[TriggerType] = mapped_column(
        Enum(TriggerType), nullable=False,
    )
    measured_value: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="The sensor / API reading that exceeded the threshold.",
    )
    threshold: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="The threshold value that was breached.",
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    affected_policies_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    total_payout: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
        doc="Sum of payouts disbursed due to this event.",
    )

    def __repr__(self) -> str:
        return (
            f"<TriggerEvent id={self.id} zone={self.zone}/{self.sub_zone} "
            f"type={self.trigger_type.value} value={self.measured_value}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# PremiumCalculation
# ─────────────────────────────────────────────────────────────────────────────
class PremiumCalculation(Base):
    """
    Audit log of how a user's premium was computed.

    Captures each factor (base rate, zone risk, season, trust, claims
    history) so the calculation is fully transparent and reproducible.
    """

    __tablename__ = "premium_calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    base_rate: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Tier base premium before adjustments.",
    )
    zone_risk_multiplier: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Multiplier based on city/zone weather risk.",
    )
    seasonal_multiplier: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Multiplier based on current month.",
    )
    trust_discount: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Discount factor from user trust score (0.0–1.0).",
    )
    claim_history_factor: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Multiplier from recent claim frequency.",
    )
    final_premium: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Computed weekly premium in INR.",
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ORM relationships
    user: Mapped["User"] = relationship("User", back_populates="premium_calculations")

    def __repr__(self) -> str:
        return (
            f"<PremiumCalculation id={self.id} user_id={self.user_id} "
            f"final={self.final_premium}>"
        )
