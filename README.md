```markdown
# ShiftShield

## AI-Powered Parametric Income Protection for Gig Delivery Workers

**Income protection that works as hard as you do.**

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

Every day, millions of gig delivery workers step out not knowing if monsoon, smog, or a city bandh will wipe out their income. Traditional insurance does not understand them. Gig platforms will not protect them.

**ShiftShield fixes this.**

We are building parametric micro-insurance where payouts happen automatically. No claims. No forms. No waiting.

When the rain starts, the money lands.

---

## Problem

### The User: Priya

Priya delivers food in Bengaluru via Swiggy and Zomato. She rents a scooter for ₹200 per day, works 9 to 10 hours, and earns ₹800 to ₹1200 on good days.

She is classified as a "delivery partner." That means:

- Zero paid leave
- Zero income guarantee
- Zero safety net

### Where Income Loss Happens

| Disruption | Days Per Year | Income Impact |
|------------|---------------|---------------|
| Heavy rainfall (>15mm/hr) | 20 to 40 | 80 to 100% loss |
| Severe AQI (>300) | 15 to 30 | 50 to 70% loss |
| Protests or bandhs | 5 to 15 | 100% loss |
| Flash floods | 5 to 10 | 100% loss |

**Annual income at risk: ₹40,000 to ₹80,000** (20 to 30% of total earnings)

### Why Existing Systems Fail

| System | Why It Fails |
|--------|--------------|
| Traditional insurance | Requires claims, documentation, weeks to process |
| Gig platform benefits | Accident only, requires hospitalization |
| Government schemes | Bureaucratic, designed for agricultural workers |

**Core failure:** No product matches the rhythm of gig work. Fast, flexible, frictionless.

---

## Solution

### What ShiftShield Does

Weekly parametric micro-insurance that automatically compensates gig workers when external conditions make earning impossible.

**How it works in 30 seconds:**

1. Subscribe weekly for ₹79
2. We monitor weather and AQI in your work zones
3. Rainfall exceeds 25mm in 3 hours
4. ₹400 lands in your account within 2 hours
5. You did nothing. The data triggered it.

### What Makes Us Different

| Traditional Insurance | ShiftShield |
|----------------------|-------------|
| User files claim | Data triggers automatically |
| Manual verification | Algorithmic plus anti-fraud |
| Days to weeks | 2 to 4 hours |
| Annual commitment | Weekly subscription |
| Subjective assessment | Objective thresholds |

**We inverted the trust model.**

Traditional: "Prove you were harmed."

ShiftShield: "We already know. Here is your money."

---

## System Workflow

### End-to-End Flow

```
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
```

---

## AI/ML Architecture

### Phase 1: Rule-Based (MVP)

| Function | Approach |
|----------|----------|
| Trigger evaluation | Threshold rules (rainfall > 25mm/3hr) |
| Risk pricing | Zone lookup table plus seasonal multiplier |
| Fraud detection | 4-signal scoring formula |

### Phase 2: ML-Enhanced

| Function | Model Type | Data Required |
|----------|------------|---------------|
| Claim prediction | Gradient boosting | 3 months of claims |
| Behavioral anomaly | Isolation forest | 4 weeks per user |
| Dynamic pricing | Regression | 6 months of P&L data |

**Design principle:** If it can be an if-statement, it should be. ML adds value at scale, not at launch.

---

## Weekly Pricing Model

### Base Structure

| Zone Risk | Disruption Days/Year | Weekly Premium | Max Payout |
|-----------|---------------------|----------------|------------|
| Low | Below 15 | ₹49 | ₹300 |
| Medium | 15 to 30 | ₹79 | ₹450 |
| High | 30 to 50 | ₹129 | ₹600 |
| Extreme | Above 50 | ₹179 | ₹800 |

### Pricing Formula

```
final_premium = base_rate × seasonal_multiplier × trust_discount

Seasonal: 0.9x to 1.5x (monsoon periods are higher)
Trust: 0.90x for 6+ months tenure, 1.0x for new users
```

### Example Calculation

Priya in Bengaluru (Medium zone), July (monsoon at 1.3x), 4 months tenure (1.0x):

```
₹79 × 1.3 × 1.0 = ₹103 per week
```

### Why Weekly Works

- ₹103 per week feels small. ₹412 per month feels large.
- Aligns with gig cash flow (paid daily by platforms)
- Can skip weeks when not working
- Reduces commitment anxiety

---

## Parametric Trigger Design

### Defined Triggers

| Trigger | Threshold | Verification Method |
|---------|-----------|---------------------|
| Heavy rain | Above 25mm in 3 hour window | 2 of 2 sources must agree |
| Severe AQI | Above 350 for 4+ hours | 2 of 2 sources must agree |
| Extreme heat | Above 45°C for 3+ hours | 2 of 2 sources must agree |
| Official bandh | Government declared | Manual verification required |
| Flood warning | Disaster management alert | Official source required |

### Why These Thresholds

- **25mm/3hr:** Roads waterlog. Delivery platforms see 70%+ order drops.
- **AQI 350+:** Official "stay indoors" territory.
- **45°C:** Platforms issue heat advisories.

### Reliability Measures

- Multi-source verification. No single API can trigger payout.
- Zone-specific coverage at 2 to 5 km radius.
- Thresholds validated against historical delivery volume data.

---

## Adversarial Defense & Anti-Spoofing

### The Threat Model

**Scenario:** 500 fake accounts spoof GPS during Mumbai rain. Each claims ₹400. Total potential fraud: ₹2,00,000.

**Why detection is hard:** The rain genuinely occurred. The trigger legitimately fired. Each individual claim looks plausible.

### The Killer Insight

**GPS proves where a phone is. It does not prove someone is working.**

A delivery worker's phone has a distinct signature:

- Repeated short trips (pickup to delivery)
- Stop-start patterns (waiting at restaurants)
- Accelerometer shows vehicle movement
- Trajectory follows actual roads

A spoofer's phone:

- GPS shows movement but accelerometer shows stationary
- No stop-start pattern
- Movement does not match road geography
- Appears suddenly in trigger zone

**This is our moat.** Spoofing GPS is easy. Spoofing realistic work motion patterns while sitting at home is nearly impossible.

### Defense Layers (MVP: 4 Layers)

**Layer 1: Device Integrity**

```python
device_risk = 0
if is_rooted: device_risk += 0.5
if mock_location_enabled: device_risk += 0.4
if fingerprint_changed: device_risk += 0.3
return min(device_risk, 1.0)
```

**Layer 2: Work Signal Verification**

```python
def calculate_work_signal_risk(location_history, motion_data):
    risk = 0
    
    # GPS shows movement but phone is stationary
    if gps_shows_movement and accelerometer_shows_stationary:
        risk += 0.6
    
    # Real delivery has multiple stops
    stops = count_stops(location_history, min_duration=2)
    if stops < 2 in last 4 hours:
        risk += 0.3
    
    # Trajectory should follow roads
    if not trajectory_matches_roads(location_history):
        risk += 0.3
    
    return min(risk, 1.0)
```

**Layer 3: Account and Timing Analysis**

```python
account_risk = 0
if account_age < 7 days: account_risk += 0.4
if first_week_claim: account_risk += 0.3
if subscribed_within_48hr_of_forecast: account_risk += 0.2
return min(account_risk, 1.0)
```

**Layer 4: Cohort Anomaly Detection**

```python
def check_cohort_anomaly(trigger_event):
    claims = get_pending_claims(trigger_event)
    new_user_claims = [c for c in claims if c.user.age_days < 14]
    new_user_rate = len(new_user_claims) / len(claims)
    
    # Normal rate is around 10%. Above 40% is suspicious.
    if new_user_rate > 0.40:
        for claim in new_user_claims:
            claim.fraud_score += 25
            claim.flags.append("COHORT_ANOMALY")
```

### The Scoring Formula

```
FRAUD_SCORE = (
    Device_Risk × 0.20 +
    Work_Signal_Risk × 0.40 +
    Account_Risk × 0.20 +
    Cohort_Risk × 0.20
) × 100

Below 60: Auto-payout
60 to 80: Expedited review
Above 80: Hold plus investigation
```

### Example: Catching a Fraud Ring

**Attack:** 200 accounts with clean phones, GPS spoofed to Andheri during rain.

| Signal | Score | Reason |
|--------|-------|--------|
| Device Risk | 0.0 | Clean phones used |
| Work Signal | 0.8 | GPS moving, accelerometer stationary |
| Account Risk | 0.5 | New accounts, pre-forecast subscription |
| Cohort Risk | 0.25 | 60% of claims from new users |

```
Base Score = (0.0 × 0.20) + (0.8 × 0.40) + (0.5 × 0.20) + (0.25 × 0.20) × 100
Base Score = (0 + 0.32 + 0.10 + 0.05) × 100 = 47

Cohort Penalty = +25 (triggered by anomaly detection)

Final Score = 47 + 25 = 72

Decision: EXPEDITED REVIEW
```

### The 72-Hour Rule

New subscribers cannot claim within first 72 hours. This kills impulse fraud. Attackers cannot see forecast, create account, and claim same day.

### Defense Economics

| Attack Type | Our Defense | Attacker Cost | Result |
|-------------|-------------|---------------|--------|
| Simple GPS spoof | Device integrity | ₹0 | Caught |
| Clean phone plus spoof | Work signal detection | ₹5,000 in phones | Caught |
| Aged accounts plus spoof | Work signal plus cohort | 3+ months waiting | Limited success |
| Full motion simulation | Must fake realistic delivery patterns | Infeasible | Blocked |

**Bottom line:** Faking work signals requires physical presence doing delivery-like activity. At that point, you might as well actually deliver.

---

## Data Sources

| Type | Primary Source | Backup Source | Update Frequency |
|------|----------------|---------------|------------------|
| Weather | OpenWeatherMap | IMD scraping | Every 30 minutes |
| AQI | AQICN | CPCB | Every hour |
| Traffic | Google Maps | HERE | Real-time |
| Events | News APIs | Manual verification | As needed |

**Cost optimization:** Backup APIs called only when primary exceeds threshold. Reduces API calls by approximately 90%.

---

## System Architecture

### Phase 1 (Hackathon MVP)

```
┌─────────────────────────────────────────────────────────────┐
│                  MOBILE APP (React Native)                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND MONOLITH (FastAPI)                  │
│  ├── User Service (signup, KYC-lite, zones)                │
│  ├── Policy Engine (weekly subscription, pricing)          │
│  ├── Trigger Evaluator (rule-based thresholds)             │
│  ├── Fraud Scorer (4-signal formula)                       │
│  └── Payout Queue (mock UPI integration)                   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        DATA LAYER                           │
│  PostgreSQL (users, policies)  │  Redis (location cache)   │
└─────────────────────────────────────────────────────────────┘
```

**Why monolith:** Small team. Fast iteration. No premature optimization.

---

## User Experience

### Onboarding (Under 4 Minutes)

```
Phone OTP → Map shows work zones → Confirm top 3 zones →
Select coverage tier → Aadhaar OTP → UPI autopay → Done
```

### During Trigger Event

```
Push notification:
"Heavy rain detected in your zone. ₹400 payout initiated. Arriving in 2 hours."

User action required: None
```

### Trust-Building Features

- Transparency log showing exactly why trigger fired
- Weather forecast for upcoming week
- Community stats: "847 workers protected this monsoon"
- Real-time payout tracking

---

## Edge Cases

### User in Zone But Not Working

**Problem:** Priya is at home in HSR Layout. It rains. She was not planning to work. Should she get paid?

**Solution:** Work Signal Verification. If no work motion signature in the 4 hours before trigger, flag for review. Workers who stopped early due to weather will show patterns before the trigger.

```python
if trigger_time - last_work_signal > 4 hours:
    claim.fraud_score += 15
    claim.flags.append("NO_RECENT_WORK_SIGNAL")
```

**Important:** We do not require active work during trigger. That defeats the purpose of insurance. We require evidence of intent to work that day.

### User Subscribed Because of Forecast

**Problem:** User sees heavy rain forecast for Friday, subscribes Thursday, claims Friday.

**Solution:** 72-Hour Rule plus Forecast Subscription Flag.

```python
if user.subscribed_within_hours(72):
    if trigger.was_forecasted_at_subscription_time:
        claim.fraud_score += 20
        claim.flags.append("FORECAST_SUBSCRIPTION")
```

**Balance:** After 2 weeks of coverage with no claims, remove new-user penalty.

### Phone Battery Died

**Problem:** User was working. Phone died. Trigger happened. No location data.

**Solution:** Use last-known location if under 6 hours old. Flag for review but do not auto-reject.

```python
if last_location_age > 6 hours:
    claim.requires_review = True
    claim.review_reason = "STALE_LOCATION"
else:
    claim.zone = last_known_zone
```

### Micro-Zone Weather Variation

**Problem:** Heavy rain in Koramangala but light rain in HSR Layout (3km away).

**Solution:** Zone granularity at 2 to 5 km. Users select up to 3 zones. Trigger must hit at least one registered zone.

**Future:** Hyper-local weather sensors for sub-zone accuracy in Phase 3.

---

## Phase 1 Scope (Hackathon)

### Fully Built

| Component | Technology |
|-----------|------------|
| Mobile app with onboarding and dashboard | React Native |
| Backend API with all core flows | FastAPI |
| Fraud scoring with 4-signal formula | Python |
| Admin panel with fraud queue | React |
| Database schema with sample data | PostgreSQL |

### Simulated

| Component | Simulation Approach |
|-----------|---------------------|
| Weather data | Pre-recorded Mumbai monsoon week |
| AQI data | Pre-recorded Delhi smog week |
| UPI payouts | Mock API returning success or failure |
| Push notifications | Console logging |
| Motion sensor data | Synthetic patterns |

### Explained Only

| Component | Documentation Provided |
|-----------|------------------------|
| ML models | Architecture plus training requirements |
| Graph fraud detection | Algorithm description |
| Work signal processing | Sensor fusion approach |
| Scaling to 1M users | Infrastructure plan |

### Demo Flow

```
1. Judge onboards as new user (2 minutes)
2. Selects Mumbai zone, pays ₹89 mock premium
3. Admin triggers simulated rain event
4. App shows payout notification
5. Dashboard updates with ₹400 received
6. Switch to admin panel
7. Show fraud queue with flagged accounts
8. Explain work signal detection
9. Present roadmap
```

---

## Performance Metrics

### Realistic Targets

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| Fraud detection rate | 70 to 80% | 85 to 90% | 93 to 97% |
| False positive rate | 8 to 12% | 4 to 6% | 2 to 3% |
| Trigger accuracy | 93 to 96% | 96 to 98% | 98 to 99% |
| Payout time | 2 to 4 hours | 1 to 2 hours | Under 30 min |

### Financial Model

```
Target loss ratio: 55 to 65%
Every ₹100 in premiums → ₹55 to 65 in payouts, ₹5 fraud loss, ₹30 to 40 margin

Break-even: Approximately 1,700 active weekly subscribers
With 15% fraud leakage: Approximately 2,200 subscribers

Each 10% improvement in fraud detection = 5% improvement in margin
```

---

## Why ShiftShield Wins

### 1. We Solve a Real Problem for Real People

15 million gig workers in India. Zero income protection products exist for them. Not because they do not want it. Because no one built for their reality.

Weekly payments. Instant payouts. No paperwork.

**We built it.**

### 2. Our Fraud Defense is a Moat

Anyone can copy parametric insurance. They cannot copy our Work Signal layer without building the same sensor fusion and behavioral modeling.

**GPS spoofing is easy. Faking realistic delivery motion while sitting at home is nearly impossible.**

### 3. The Unit Economics Work

- ₹79 per week premium
- ₹400 average payout
- 55% target loss ratio
- ₹50 customer acquisition cost
- 1,700 users to break even

**This is a business, not a charity.**

### 4. We Know What to Build First

- Phase 1: Rule-based. Works today.
- Phase 2: ML-enhanced. Works better.
- Phase 3: Fully autonomous. Works at scale.

No hand-waving. No "AI will solve it." Every component is buildable with a small team.

### 5. Parametric is the Future

Claims processes are broken. Manual review does not scale. Fraud investigation costs more than fraud itself.

**Parametric triggers plus behavioral fraud detection is the only way to serve this market profitably.**

We are not digitizing old insurance. We are building a new category.

---

## The Ask

We are building the financial safety net the gig economy forgot to include.

- 15 million workers
- ₹60,000 annual income at risk per worker
- ₹90,000 crore total addressable problem

**ShiftShield: Because your income should not depend on the weather.**

---

*Built by engineers who believe financial protection should not be a luxury.*
```
