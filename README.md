# ShiftShield

## AI-Powered Parametric Income Protection for Gig Delivery Workers

**Income protection that works as hard as you do.**

> ⚡ Real-time protection for real-world income loss

---

## Table of Contents

1. [Vision](#vision)  
2. [Problem](#problem)  
3. [Solution](#solution)  
4. [System Workflow](#system-workflow)  
5. [AI/ML Architecture](#aiml-architecture)  
6. [Weekly Pricing Model](#weekly-pricing-model)  
7. [Parametric Trigger Design](#parametric-trigger-design)  
8. [Adversarial Defense & Anti-Spoofing](#adversarial-defense--anti-spoofing)  
9. [Data Sources](#data-sources)  
10. [System Architecture](#system-architecture)  
11. [User Experience](#user-experience)  
12. [Edge Cases](#edge-cases)  
13. [Phase 1 Scope](#phase-1-scope-hackathon)  
14. [Why ShiftShield Wins](#why-shiftshield-wins)  

---

## Vision

Every day, millions of gig delivery workers step out not knowing if monsoon, smog, or a city bandh will wipe out their income.

Traditional insurance does not understand them.  
Gig platforms will not protect them.

**ShiftShield fixes this.**

We are building parametric micro-insurance where payouts happen automatically.

- No claims  
- No forms  
- No waiting  

**When the rain starts, the money lands.**

---

## Problem

### The User: Priya

Priya delivers food in Bengaluru via Swiggy and Zomato.

- Works 9 to 10 hours daily  
- Earns ₹800 to ₹1200 on good days  
- Rents a scooter for ₹200 per day  

She is classified as a delivery partner.

That means:

- No paid leave  
- No income guarantee  
- No safety net  

---

### Where Income Loss Happens

| Disruption | Days Per Year | Income Impact |
|------------|--------------|---------------|
| Heavy rainfall (>15mm/hr) | 20 to 40 | 80 to 100% loss |
| Severe AQI (>300) | 15 to 30 | 50 to 70% loss |
| Protests or bandhs | 5 to 15 | 100% loss |
| Flash floods | 5 to 10 | 100% loss |

**Annual income at risk: ₹40,000 to ₹80,000**

---

### Why Existing Systems Fail

| System | Why It Fails |
|--------|--------------|
| Traditional insurance | Requires claims and takes weeks |
| Gig platform benefits | Covers accidents only |
| Government schemes | Slow and not designed for gig workers |

**Core failure:** No product matches the rhythm of gig work. Fast. Flexible. Frictionless.

---
## Solution

### What ShiftShield Does

ShiftShield is weekly parametric micro-insurance that automatically compensates gig workers when external conditions make earning impossible.

**How it works in 30 seconds:**

1. Subscribe weekly for ₹79  
2. We monitor weather and AQI in your work zones  
3. Rainfall exceeds threshold  
4. **₹400 lands in your account within 2 hours**  
5. You did nothing. The system handles everything  

---

### What Makes Us Different

| Traditional Insurance | ShiftShield |
|----------------------|------------|
| User files claim | Data triggers automatically |
| Manual verification | Algorithmic plus anti-fraud |
| Days to weeks | 2 to 4 hours |
| Annual commitment | Weekly subscription |
| Subjective assessment | Objective thresholds |

---

## System Workflow

### End-to-End Flow
ONBOARDING (4 minutes)
Phone OTP → Zone selection → Coverage tier → KYC-lite → UPI setup → Active

WEEKLY CYCLE
Sunday notification → Confirm coverage → Auto-debit → Coverage starts Monday 6 AM

MONITORING (24/7)
Weather APIs every 30 min → AQI feeds hourly → Threshold evaluation per zone

TRIGGER ACTIVATION
Condition breached → Affected zones identified → Eligible users filtered →
Fraud score calculated → Payout decision

PAYOUT EXECUTION
Score below 60: Auto-payout in 2 hours
Score 60 to 80: Expedited review in 4 hours
Score above 80: Hold plus manual review

---

## AI/ML Architecture

### Phase 1: Rule-Based (MVP)

| Function | Approach |
|----------|----------|
| Trigger evaluation | Threshold rules |
| Risk pricing | Zone lookup plus seasonal multiplier |
| Fraud detection | 4-signal scoring |

---

### Phase 2: ML-Enhanced

| Function | Model Type | Data Required |
|----------|------------|---------------|
| Claim prediction | Gradient boosting | 3 months data |
| Behavioral anomaly | Isolation forest | 4 weeks per user |
| Dynamic pricing | Regression | 6 months data |

**Design principle:** If it can be an if-statement, it should be.
## Weekly Pricing Model

### Base Structure

| Zone Risk | Weekly Premium | Max Payout |
|-----------|--------------|------------|
| Low | ₹49 | ₹300 |
| Medium | ₹79 | ₹450 |
| High | ₹129 | ₹600 |
| Extreme | ₹179 | ₹800 |

---

### Pricing Formula

final_premium = base_rate × seasonal_multiplier × trust_discount

---

### Example Calculation
₹79 × 1.3 = ₹103 per week

---

### Why Weekly Works

- Feels affordable  
- Matches gig income cycles  
- No long-term commitment  
- Flexible usage  

---

## Parametric Trigger Design

### Defined Triggers

| Trigger | Threshold |
|---------|----------|
| Heavy rain | > 25mm in 3 hours |
| AQI | > 350 |
| Extreme heat | > 45°C |

---

### Key Idea

We trigger payouts only when earning becomes **impossible**, not inconvenient.

---

## Adversarial Defense & Anti-Spoofing

### The Threat Model

Fake users spoof GPS during events and claim payouts.

---

### The Core Insight

**GPS proves location. It does not prove work.**

---

### Our Defense Approach

We detect **work signals**, not just location:

- Movement patterns  
- Stop-start delivery behavior  
- GPS vs accelerometer mismatch  

---

### Fraud Score
FRAUD_SCORE =
(Device × 0.20) +
(Work Signal × 0.40) +
(Account × 0.20) +
(Cohort × 0.20)

---

### Decision Logic

- Score < 60 → Auto payout  
- Score 60–80 → Review  
- Score > 80 → Hold  

---

### Why This Works

To cheat the system, attackers must:

- Fake realistic movement  
- Maintain accounts over time  
- Avoid group detection  

**This makes large-scale fraud economically unviable.**
## System Architecture

### Phase 1 (Hackathon MVP)

- Mobile App: React Native  
- Backend: FastAPI  
- Database: PostgreSQL  
- Cache: Redis  

---

## User Experience

### Onboarding
Phone OTP → Select zones → Choose plan → KYC → UPI setup → Done

---

### During Trigger
Heavy rain detected in your zone.
₹400 payout initiated.
Arriving in your account within 2 hours.

---

### Core Principle

**User does nothing. System handles everything.**

---

## Edge Cases

### User not working during rain

We still pay.  
This is parametric insurance. It is designed to remove claim friction.

---

### User subscribes before forecast

Handled using:

- 72-hour rule  
- Risk scoring  

---

### GPS missing

We use last known location if recent.  
Otherwise flagged for review.

---

## Phase 1 Scope

### Built

- User onboarding  
- Subscription system  
- Trigger logic  
- Fraud scoring  
- Payout simulation  

---

### Simulated

- Weather data  
- AQI data  
- UPI payouts  

---

### Explained

- ML models  
- Advanced fraud detection  

---

## Performance Targets

| Metric | Value |
|--------|------|
| Fraud detection | 70–80% |
| False positives | 8–12% |
| Trigger accuracy | 93–96% |
| Payout time | 2–4 hours |

---

## Why ShiftShield Wins

### Real Problem

Millions of workers with zero income protection.

---

### Strong Defense

Fraud prevention based on behavior, not just GPS.

---

### Buildable System

No overengineering. Everything works from day one.

---

### Scalable Vision

Rule-based now. ML later.

---

## The Ask

We are building a financial safety net for gig workers.

**ShiftShield ensures income does not stop when the world does.**
