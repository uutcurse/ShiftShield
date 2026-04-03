"""
ShiftShield — Main Application
===============================
FastAPI application for parametric insurance targeting gig delivery workers
(Swiggy/Zomato) in India.

Run with::

    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from config import ZONES
from schemas import HealthResponse, ZonesResponse

# Import routers
from routers import auth, users, policies, claims, triggers, premiums, premium, policy, trigger_monitor, admin

# APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

_scheduler = BackgroundScheduler(timezone="UTC")


def _scheduled_trigger_scan() -> None:
    """
    Background job: runs every 30 minutes.
    Fetches live weather + AQI for all zones and fires any breached triggers.
    """
    from database import SessionLocal
    from services.trigger_monitor import TriggerMonitor
    db = SessionLocal()
    try:
        monitor = TriggerMonitor(db=db)
        result = monitor.run_full_scan()
        if result["triggers_fired"] > 0:
            print(
                f"🌩️  [Scheduler] {result['triggers_fired']} trigger(s) fired — "
                f"{result['total_claims_created']} claims created — "
                f"₹{result['total_payout_inr']} disbursed"
            )
        else:
            print(f"✅  [Scheduler] Scan complete — no triggers active")
    except Exception as e:
        print(f"❌  [Scheduler] Trigger scan error: {e}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    On startup:
      - Create all database tables (idempotent — safe for dev).
    On shutdown:
      - Dispose of the engine connection pool.
    """
    # ── Startup ──────────────────────────────────────────────────────────
    Base.metadata.create_all(bind=engine)
    print("✅  Database tables created / verified.")
    print(f"📍  Zones loaded: {list(ZONES.keys())}")

    # Start APScheduler — trigger scan every 30 minutes
    _scheduler.add_job(
        _scheduled_trigger_scan,
        trigger=IntervalTrigger(minutes=30),
        id="trigger_scan",
        name="Parametric Trigger Scan",
        replace_existing=True,
    )
    _scheduler.start()
    print("⏰  APScheduler started — trigger scan every 30 min")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    _scheduler.shutdown(wait=False)
    engine.dispose()
    print("🛑  Database connections closed.")


# ─────────────────────────────────────────────────────────────────────────────
# App Instance
# ─────────────────────────────────────────────────────────────────────────────
APP_VERSION = "0.1.0"

app = FastAPI(
    title="ShiftShield",
    description=(
        "Parametric insurance API for gig delivery workers in India. "
        "Provides weather-triggered, instant micro-payouts to protect "
        "Swiggy & Zomato riders from income loss due to rain, extreme "
        "heat, poor AQI, floods, and curfews."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────────────────────
# CORS Middleware (permissive for dev — tighten in production)
# ─────────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Include Routers
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(premium.router, prefix="/api")
app.include_router(policy.router, prefix="/api")
app.include_router(trigger_monitor.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(users.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(claims.router, prefix="/api/v1")
app.include_router(triggers.router, prefix="/api/v1")
app.include_router(premiums.router, prefix="/api/v1")


# ─────────────────────────────────────────────────────────────────────────────
# Root Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.get(
    "/",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
)
def root():
    """Return application health status, version, and server timestamp."""
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@app.get(
    "/api/v1/zones",
    response_model=ZonesResponse,
    tags=["Reference Data"],
    summary="List supported zones & sub-zones",
)
def get_zones():
    """
    Return the full mapping of supported cities (zones) to their
    sub-zone localities.
    """
    return ZonesResponse(zones=ZONES)
