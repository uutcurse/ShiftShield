"""
ShiftShield Auth Schemas
========================
Pydantic models for the multi-step OTP + registration auth flow.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator

from schemas import PlatformEnum, PolicyBrief


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Phone + OTP
# ─────────────────────────────────────────────────────────────────────────────
class SendOTPRequest(BaseModel):
    """Step 1a — Request OTP for phone verification."""
    phone: str = Field(
        ..., min_length=10, max_length=15,
        description="Indian mobile number, e.g. +919876543210",
        examples=["+919876543210"],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "")
        if not cleaned.replace("+", "").isdigit():
            raise ValueError("Phone number must contain only digits and optional leading +")
        return cleaned


class SendOTPResponse(BaseModel):
    """Response after OTP is dispatched (simulated)."""
    message: str = "OTP sent successfully"
    phone: str
    expires_in_seconds: int = 300
    hint: Optional[str] = Field(
        None,
        description="DEV ONLY — the generated OTP for testing purposes.",
    )


class VerifyOTPRequest(BaseModel):
    """Step 1b — Verify phone with the received OTP."""
    phone: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

    @field_validator("otp")
    @classmethod
    def validate_otp_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP must be exactly 6 digits")
        return v


class VerifyOTPResponse(BaseModel):
    """Temporary token returned after OTP verification."""
    message: str = "Phone verified successfully"
    phone: str
    temp_token: str = Field(
        ...,
        description=(
            "Short-lived token proving phone ownership. "
            "Must be passed to /register to complete sign-up."
        ),
    )
    is_existing_user: bool = Field(
        False,
        description="True if phone is already registered — client can skip to login.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Steps 2-4: Full Registration
# ─────────────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    """
    Full registration payload — combines all 4 onboarding steps.

    The client collects these over a multi-screen flow:
      Step 1: phone + OTP  (already verified → temp_token)
      Step 2: name, platform
      Step 3: city, zone, sub_zone
      Step 4: upi_id, aadhaar_last4
    """
    # Auth proof
    temp_token: str = Field(
        ...,
        description="Temporary token from /verify-otp proving phone ownership.",
    )

    # Step 2 — Personal details
    name: str = Field(..., min_length=1, max_length=120)
    platform: PlatformEnum = PlatformEnum.both

    # Step 3 — Location
    city: str = Field(
        ..., max_length=50,
        description="One of the supported Indian cities.",
    )
    zone: str = Field(
        ..., max_length=50,
        description="Zone (equals city name in current model).",
    )
    sub_zone: str = Field(
        ..., max_length=80,
        description="Sub-zone locality within the city.",
    )

    # Step 4 — Payment & KYC
    upi_id: Optional[str] = Field(
        None, max_length=80,
        description="UPI VPA for payouts, e.g. worker@upi",
    )
    aadhaar_last4: Optional[str] = Field(
        None, min_length=4, max_length=4,
        description="Last 4 digits of Aadhaar for KYC.",
    )

    @field_validator("aadhaar_last4")
    @classmethod
    def validate_aadhaar(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.isdigit():
            raise ValueError("Aadhaar last 4 must be digits")
        return v


class AuthTokenResponse(BaseModel):
    """JWT token returned after successful registration or login."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: "AuthUserProfile"


class LoginResponse(BaseModel):
    """JWT token returned when an existing user verifies OTP."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: "AuthUserProfile"


# ─────────────────────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────────────────────
class AuthUserProfile(BaseModel):
    """User profile returned from auth endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    name: str
    city: str
    zone: str
    sub_zone: str
    platform: PlatformEnum
    upi_id: Optional[str] = None
    aadhaar_last4: Optional[str] = None
    created_at: datetime
    is_active: bool
    trust_score: float
    total_claims: int
    total_payouts: float
    fraud_flags: int


class ProfileWithPolicy(BaseModel):
    """User profile + their active policy info (GET /profile response)."""
    model_config = ConfigDict(from_attributes=True)

    user: AuthUserProfile
    active_policy: Optional[PolicyBrief] = None
    registration_complete: bool = True


class ProfileUpdateRequest(BaseModel):
    """PUT /profile — updatable fields."""
    upi_id: Optional[str] = Field(None, max_length=80)
    zone: Optional[str] = Field(None, max_length=50)
    sub_zone: Optional[str] = Field(None, max_length=80)
    platform: Optional[PlatformEnum] = None


class ProfileUpdateResponse(BaseModel):
    """Response after profile update."""
    message: str = "Profile updated successfully"
    user: AuthUserProfile


# Rebuild forward refs for nested models
AuthTokenResponse.model_rebuild()
LoginResponse.model_rebuild()
