from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import time

from database import get_db
from models import Policy, Claim, User, TriggerEvent
from services.trigger_monitor import TriggerMonitor
from pydantic import BaseModel

# No Depends(get_current_user) applied for the prototype ease-of-demo
router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

class TriggerSimulationRequest(BaseModel):
    city: str  # maps to zone
    zone: str  # maps to sub_zone
    trigger_type: str
    trigger_value: float

@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Active Policies
    active_policies = db.query(Policy).filter(Policy.end_date >= now).count()
    if not active_policies: active_policies = 1247
    
    # 2. Claims Today
    claims_today = db.query(Claim).filter(Claim.initiated_at >= today_start).count()
    if not claims_today: claims_today = 23
    
    # 3. Payouts and Premiums this week
    payouts_week = db.query(func.sum(Claim.payout_amount)).filter(
        Claim.status == "paid", Claim.initiated_at >= week_start
    ).scalar() or 0.0
    if not payouts_week: payouts_week = 145800.0

    premiums_week = db.query(func.sum(Policy.weekly_premium)).filter(
        Policy.created_at >= week_start
    ).scalar() or 0.0
    if not premiums_week: premiums_week = 214000.0

    loss_ratio = round((payouts_week / premiums_week) * 100, 1) if premiums_week > 0 else 68.2

    # 4. Trigger Events this week
    trigger_counts = db.query(
        TriggerEvent.trigger_type, 
        func.count(TriggerEvent.id),
        func.sum(TriggerEvent.total_payout)
    ).filter(TriggerEvent.triggered_at >= week_start).group_by(TriggerEvent.trigger_type).all()

    triggers_list = []
    has_triggers = False
    for t_type, count, t_payout in trigger_counts:
        has_triggers = True
        triggers_list.append({
            "type": str(t_type).replace("TriggerType.", "").lower(), 
            "count": count, 
            "total_payout": t_payout or 0
        })
        
    if not has_triggers:
        triggers_list = [
            {"type": "heavy_rain", "count": 3, "total_payout": 89000},
            {"type": "aqi", "count": 1, "total_payout": 34000},
            {"type": "heat", "count": 0, "total_payout": 0}
        ]

    # 5. Claims by Status
    status_counts = db.query(Claim.status, func.count(Claim.id)).group_by(Claim.status).all()
    claims_by_status = {"auto_approved": 0, "flagged": 0, "held": 0, "rejected": 0}
    has_status = False
    for status, count in status_counts:
        has_status = True
        s_val = str(status).replace("ClaimStatus.", "").lower()
        if s_val == "auto_approved": claims_by_status["auto_approved"] = count
        elif s_val == "under_review": claims_by_status["flagged"] = count
        elif s_val == "rejected": claims_by_status["rejected"] = count
        elif s_val == "paid": claims_by_status["auto_approved"] += count
        
    if not has_status:
        claims_by_status = {"auto_approved": 78, "flagged": 15, "held": 5, "rejected": 2}

    # 6. Zone Summary
    zones = ["Mumbai", "Delhi"]
    zone_summary = []
    for z in zones:
        z_pol = db.query(Policy).join(User).filter(User.city == z, Policy.end_date >= now).count()
        z_claim = db.query(Claim).join(Policy).join(User).filter(User.city == z, Claim.initiated_at >= week_start).count()
        z_prem = db.query(func.sum(Policy.weekly_premium)).join(User).filter(User.city == z).scalar() or 0
        z_pay = db.query(func.sum(Claim.payout_amount)).join(Policy).join(User).filter(User.city == z, Claim.status == "paid").scalar() or 0
        
        lr = round((z_pay / z_prem * 100)) if z_prem > 0 else (82 if z == "Mumbai" else 45)
        risk = "high" if lr > 70 else "medium" if lr > 40 else "low"
        
        zone_summary.append({
            "zone": f"{z}-{'Dadar' if z == 'Mumbai' else 'Connaught'}",
            "active_policies": z_pol or (145 if z == "Mumbai" else 89),
            "claims_this_week": z_claim or (12 if z == "Mumbai" else 5),
            "loss_ratio": lr,
            "risk": risk
        })

    return {
        "active_policies": active_policies,
        "active_policies_change": 12.5,
        "claims_today": claims_today,
        "payouts_this_week": int(payouts_week),
        "loss_ratio": float(loss_ratio),
        "total_premiums_this_week": int(premiums_week),
        "trigger_events_this_week": triggers_list,
        "claims_by_status": claims_by_status,
        "zone_summary": zone_summary
    }

@router.get("/weekly-trends")
def get_weekly_trends(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    
    trends = []
    # If the DB has no historical policies, output realistic mock data.
    has_history = db.query(Policy).count() > 0
    
    for i in range(11, -1, -1):
        w_start = week_start - timedelta(weeks=i)
        w_end = w_start + timedelta(days=7)
        if has_history:
            wp = db.query(func.sum(Policy.weekly_premium)).filter(Policy.created_at >= w_start, Policy.created_at < w_end).scalar() or 0
            wc = db.query(func.sum(Claim.payout_amount)).filter(Claim.status == "paid", Claim.initiated_at >= w_start, Claim.initiated_at < w_end).scalar() or 0
        else:
            wp = 120000 + i * 5000 + (10000 if i % 2 == 0 else 0)
            wc = wp * (0.6 if i != 2 else 0.9)
            
        trends.append({
            "week": f"Wk {12-i}",
            "premiums": int(wp),
            "payouts": int(wc)
        })
    return trends

@router.get("/fraud-alerts")
def get_fraud_alerts(db: Session = Depends(get_db)):
    flagged = db.query(Claim).filter(Claim.fraud_score > 40).order_by(Claim.fraud_score.desc()).all()
    
    alerts = []
    for c in flagged:
        user = c.policy.user if c.policy else None
        alerts.append({
            "id": c.id,
            "user": user.name if user else "Unknown",
            "amount": c.payout_amount,
            "fraud_score": c.fraud_score,
            "reason": "Anomaly detected during location sync" if c.fraud_score > 80 else "Multiple claims in 12h",
            "status": c.status.value
        })
        
    if not alerts:
        alerts = [
            {"id": "CLM-9091", "user": "Rohan M.", "amount": 450, "fraud_score": 85, "reason": "Geo-mismatch during rain flag", "status": "under_review"},
            {"id": "CLM-9092", "user": "Priya S.", "amount": 300, "fraud_score": 92, "reason": "Device ID spoofing detected", "status": "held"}
        ]
    return alerts

@router.get("/predictions")
def get_predictions():
    return {
        "title": "Next Week Forecast",
        "intro": "Based on weather predictions, we expect:",
        "bullets": [
             "Mumbai: 3 rain events, estimated payouts ₹45,000",
             "Delhi: AQI likely to exceed 350, estimated payouts ₹28,000"
        ],
        "reserve": 73000,
        "premium_adjustment": "+15% for Mumbai zones"
    }

from trigger_simulator.simulate import generate_logs_for_report
import time

@router.post("/simulate-trigger")
def simulate_trigger(payload: TriggerSimulationRequest, db: Session = Depends(get_db)):
    monitor = TriggerMonitor(db)
    start_time = time.time()
    
    try:
        report = monitor.simulate_trigger(
            city=payload.city,
            sub_zone=payload.zone,
            trigger_name=payload.trigger_type,
            value_override=payload.trigger_value
        )
        
        # Share the exact same log generator as the CLI tool
        raw_logs = generate_logs_for_report(report, start_time)
        logs = [msg for msg, color in raw_logs]
                
        return {
            "status": "success",
            "logs": logs,
            "report": report
        }
    except Exception as e:
        return {
            "status": "error",
            "logs": [f"[CRITICAL ERROR] Simulator failed: {str(e)}"]
        }
