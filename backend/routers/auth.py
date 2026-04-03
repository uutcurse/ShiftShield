"""
ShiftShield Auth Router
=======================
Multi-step OTP-based authentication and registration for gig workers.

Flow:
  1. POST /send-otp     → receive 6-digit OTP (simulated SMS)
  2. POST /verify-otp   → verify OTP → get temp_token
  3. POST /register     → complete registration → get JWT
  4. GET  /profile      → protected — view profile + active policy
  5. PUT  /profile      → protected — update UPI, zone, platform

JWT is generated using python-jose (HS256) with user_id in the payload.
OTPs are stored in-memory with TTL (Redis-ready interface).
"""

from __future__ import annotations

import random
import string
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    ZONES,
    CITY_NAMES,
)
from database import get_db
from models import User, Policy
from auth_schemas import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    RegisterRequest,
    AuthTokenResponse,
    LoginResponse,
    AuthUserProfile,
    ProfileWithPolicy,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
)
from schemas import PolicyBrief

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ═════════════════════════════════════════════════════════════════════════════
# In-Memory OTP Store  (swap with Redis for production)
# ═════════════════════════════════════════════════════════════════════════════
OTP_EXPIRY_SECONDS = 300  # 5 minutes

# { phone: { "otp": "123456", "expires_at": <unix_ts>, "attempts": 0 } }
_otp_store: dict[str, dict] = {}

# { temp_token: { "phone": "+91…", "expires_at": <unix_ts> } }
_temp_token_store: dict[str, dict] = {}


def _cleanup_expired() -> None:
    """Remove expired entries from both stores (lazy GC)."""
    now = time.time()
    for phone in list(_otp_store):
        if _otp_store[phone]["expires_at"] < now:
            del _otp_store[phone]
    for token in list(_temp_token_store):
        if _temp_token_store[token]["expires_at"] < now:
            del _temp_token_store[token]


# ═════════════════════════════════════════════════════════════════════════════
# JWT Helpers
# ═════════════════════════════════════════════════════════════════════════════
def _create_access_token(user_id: int, phone: str) -> str:
    """Generate a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "phone": phone,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _create_temp_token(phone: str) -> str:
    """
    Generate a short-lived opaque token proving phone ownership.
    Used between verify-otp and register.
    """
    token = "tmp_" + "".join(random.choices(string.ascii_letters + string.digits, k=48))
    _temp_token_store[token] = {
        "phone": phone,
        "expires_at": time.time() + 600,  # 10 min window to complete registration
    }
    return token


def _verify_temp_token(token: str) -> str:
    """
    Validate a temp token and return the associated phone number.
    Raises 401 if invalid or expired.
    """
    _cleanup_expired()
    entry = _temp_token_store.get(token)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired temporary token. Please verify OTP again.",
        )
    if entry["expires_at"] < time.time():
        del _temp_token_store[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Temporary token has expired. Please verify OTP again.",
        )
    return entry["phone"]


# ═════════════════════════════════════════════════════════════════════════════
# JWT Auth Dependency (for protected routes)
# ═════════════════════════════════════════════════════════════════════════════
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — extracts and validates the JWT Bearer token,
    then returns the authenticated User ORM object.

    Usage::

        @router.get("/protected")
        def protected(user: User = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact support.",
        )
    return user


# ═════════════════════════════════════════════════════════════════════════════
# Location Validation Helper
# ═════════════════════════════════════════════════════════════════════════════
def _validate_location(city: str, zone: str, sub_zone: str) -> None:
    """Raise 422 if the city/zone/sub_zone combination is invalid."""
    if city not in ZONES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported city '{city}'. Must be one of {CITY_NAMES}.",
        )
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


# ═════════════════════════════════════════════════════════════════════════════
# ORM → Pydantic helper
# ═════════════════════════════════════════════════════════════════════════════
def _user_to_profile(user: User) -> AuthUserProfile:
    """Convert a User ORM object to an AuthUserProfile schema."""
    return AuthUserProfile.model_validate(user)


# ═════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

# ── Step 1a: Send OTP ────────────────────────────────────────────────────────
@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Step 1 — Send OTP to phone",
    status_code=status.HTTP_200_OK,
)
def send_otp(payload: SendOTPRequest):
    """
    Generate a random 6-digit OTP and store it in memory with a 5-minute
    expiry.  In production this would trigger an SMS via an aggregator
    (MSG91, Twilio, etc.).  For dev, the OTP is returned in the response.

    **Rate limiting:** max 5 OTP requests per phone per 10 minutes.
    """
    _cleanup_expired()
    phone = payload.phone

    # Basic rate limiting
    existing = _otp_store.get(phone)
    if existing and existing["attempts"] >= 5 and existing["expires_at"] > time.time():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please wait before trying again.",
        )

    otp = "".join(random.choices(string.digits, k=6))

    _otp_store[phone] = {
        "otp": otp,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "attempts": (existing["attempts"] + 1) if existing else 1,
        "created_at": time.time(),
    }

    return SendOTPResponse(
        phone=phone,
        expires_in_seconds=OTP_EXPIRY_SECONDS,
        hint=f"DEV OTP: {otp}",  # Remove in production!
    )


# ── Step 1b: Verify OTP ──────────────────────────────────────────────────────
@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    summary="Step 1 — Verify phone OTP",
    status_code=status.HTTP_200_OK,
)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verify the 6-digit OTP for the given phone number.

    On success:
    - If user already exists → return temp_token + `is_existing_user=true`
      (client can call /login instead of /register).
    - If new user → return temp_token for use in /register.

    The OTP is consumed on successful verification (single-use).
    """
    _cleanup_expired()
    phone = payload.phone
    entry = _otp_store.get(phone)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found for this phone. Please request a new one.",
        )

    if entry["expires_at"] < time.time():
        del _otp_store[phone]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one.",
        )

    if entry["otp"] != payload.otp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP. Please check and try again.",
        )

    # OTP is valid — consume it
    del _otp_store[phone]

    # Check if user already exists
    existing_user = db.query(User).filter(User.phone == phone).first()
    is_existing = existing_user is not None

    temp_token = _create_temp_token(phone)

    return VerifyOTPResponse(
        phone=phone,
        temp_token=temp_token,
        is_existing_user=is_existing,
    )


# ── Steps 2-4: Register ──────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=AuthTokenResponse,
    summary="Steps 2-4 — Complete registration",
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Complete user registration after OTP verification.

    The client collects data across a multi-step onboarding UI:

    | Step | Fields                               |
    |------|--------------------------------------|
    | 1    | Phone + OTP *(already done)*         |
    | 2    | Name, platform                       |
    | 3    | City → Zone → Sub-zone               |
    | 4    | UPI ID, Aadhaar last 4               |

    Requires a valid `temp_token` from `/verify-otp`.
    """
    # Validate temp token → extract verified phone
    verified_phone = _verify_temp_token(payload.temp_token)

    # Ensure the phone in the token matches
    # (the client shouldn't change phones mid-flow)

    # Check duplicate
    existing = db.query(User).filter(User.phone == verified_phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Phone {verified_phone} is already registered. "
                "Use /verify-otp → login flow instead."
            ),
        )

    # Validate location
    _validate_location(payload.city, payload.zone, payload.sub_zone)

    # Create user
    user = User(
        phone=verified_phone,
        name=payload.name,
        city=payload.city,
        zone=payload.zone,
        sub_zone=payload.sub_zone,
        platform=payload.platform.value,
        upi_id=payload.upi_id,
        aadhaar_last4=payload.aadhaar_last4,
        trust_score=100.0,  # Initial trust score
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Consume the temp token
    _temp_token_store.pop(payload.temp_token, None)

    # Issue JWT
    access_token = _create_access_token(user.id, user.phone)

    return AuthTokenResponse(
        access_token=access_token,
        expires_in_minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        user=_user_to_profile(user),
    )


# ── Login (existing user after OTP) ──────────────────────────────────────────
@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login existing user after OTP",
    status_code=status.HTTP_200_OK,
)
def login(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    One-step login for returning users.

    Verifies OTP and immediately issues a JWT if the phone number
    belongs to an existing active user.  New users should use the
    `/verify-otp` → `/register` flow instead.
    """
    _cleanup_expired()
    phone = payload.phone
    entry = _otp_store.get(phone)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found for this phone. Call /send-otp first.",
        )

    if entry["expires_at"] < time.time():
        del _otp_store[phone]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one.",
        )

    if entry["otp"] != payload.otp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP.",
        )

    # OTP valid — consume
    del _otp_store[phone]

    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for this phone. Please register first.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact support.",
        )

    access_token = _create_access_token(user.id, user.phone)

    return LoginResponse(
        access_token=access_token,
        expires_in_minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        user=_user_to_profile(user),
    )


# ── GET /profile (protected) ─────────────────────────────────────────────────
@router.get(
    "/profile",
    response_model=ProfileWithPolicy,
    summary="Get authenticated user profile",
)
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated user's full profile together with their
    active policy details (if any).

    Requires a valid JWT Bearer token.
    """
    # Fetch active policy
    active_policy = (
        db.query(Policy)
        .filter(
            Policy.user_id == user.id,
            Policy.is_active == True,  # noqa: E712
        )
        .first()
    )

    policy_brief = PolicyBrief.model_validate(active_policy) if active_policy else None

    return ProfileWithPolicy(
        user=_user_to_profile(user),
        active_policy=policy_brief,
        registration_complete=bool(user.name and user.city and user.sub_zone),
    )


# ── PUT /profile (protected) ─────────────────────────────────────────────────
@router.put(
    "/profile",
    response_model=ProfileUpdateResponse,
    summary="Update user profile",
)
def update_profile(
    payload: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the authenticated user's profile.

    Updatable fields: `upi_id`, `zone`, `sub_zone`, `platform`.
    If zone/sub_zone are changed, the new combination is validated
    against the zone registry.
    """
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    # If zone/sub_zone are being changed, validate
    new_zone = update_data.get("zone", user.zone)
    new_sub_zone = update_data.get("sub_zone", user.sub_zone)
    if "zone" in update_data or "sub_zone" in update_data:
        _validate_location(user.city, new_zone, new_sub_zone)

    for field, value in update_data.items():
        setattr(user, field, value if not hasattr(value, "value") else value.value)

    db.commit()
    db.refresh(user)

    return ProfileUpdateResponse(
        user=_user_to_profile(user),
    )
