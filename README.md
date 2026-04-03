<div align="center">

# 🛡️ ShiftShield

### AI-Powered Parametric Income Protection for India's Gig Delivery Workers

**Income protection that works as hard as you do.**

⚡ Real-time triggers · 🤖 AI-powered pricing · 🚀 Zero-touch payouts

---

[![Phase](https://img.shields.io/badge/Phase-2%20%7C%20Protect%20Your%20Worker-blue?style=for-the-badge)]()
[![Stack](https://img.shields.io/badge/FastAPI-React_19-green?style=for-the-badge)]()
[![Insurance](https://img.shields.io/badge/Type-Parametric%20%7C%20Weekly-orange?style=for-the-badge)]()
[![AI](https://img.shields.io/badge/AI-Dynamic%20Premium%20%2B%20Fraud%20Detection-purple?style=for-the-badge)]()

[Demo Video](#-demo-video) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [API Docs](#-api-reference) · [How It Works](#-how-it-works)

</div>

---

## 📋 Table of Contents

- [What's New in Phase 2](#-whats-new-in-phase-2)
- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [How It Works](#-how-it-works)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Features Deep Dive](#-features-deep-dive)
  - [Registration & Onboarding](#1-registration--onboarding)
  - [Dynamic Premium Engine](#2-ai-powered-dynamic-premium-engine)
  - [Policy Management](#3-policy-management)
  - [Parametric Trigger System](#4-parametric-trigger-system)
  - [Claims Automation](#5-zero-touch-claims-automation)
  - [Fraud Detection](#6-intelligent-fraud-detection)
  - [Admin God Mode Dashboard](#7-admin-god-mode-dashboard)
- [API Reference](#-api-reference)
- [Trigger Simulation Guide](#-trigger-simulation-guide)
- [Weekly Pricing Model](#-weekly-pricing-model)
- [Demo Video](#-demo-video)
- [Phase 1 → Phase 2 Evolution](#-phase-1--phase-2-evolution)
- [What's Next (Phase 3)](#-whats-next-phase-3)
- [Team](#-team)

---

## 🆕 What's New in Phase 2

| Component | Phase 1 (Ideation) | Phase 2 (Built & Working) |
|---|---|---|
| Registration | Described in docs | ✅ Full 4-step OTP onboarding |
| Premium Calculation | Formula on paper | ✅ AI engine with 7 dynamic risk factors |
| Policy Management | Concept | ✅ Full CRUD — create, renew, upgrade, cancel |
| Trigger Monitoring | Threshold list | ✅ Real-time background polling with APScheduler |
| Claims | Flow diagram | ✅ Fully automated: trigger → fraud check → payout |
| Fraud Detection | Scoring formula | ✅ 5-signal fraud scoring with auto-approve/flag/hold |
| Payout | Described | ✅ Simulated UPI instant payouts |
| Admin Dashboard | Not built | ✅ "God Mode" — live logs, simulation, analytics |
| Frontend | Not built | ✅ Premium React UI with Framer Motion animations |

> **Phase 1 was the blueprint. Phase 2 is the building.**

---

## 🔥 The Problem

### Meet Priya — A Food Delivery Partner in Mumbai

| Detail | Value |
|---|---|
| Platform | Swiggy + Zomato |
| Daily hours | 9-10 hours |
| Good day earnings | ₹800 - ₹1,200 |
| Daily scooter rent | ₹200 |
| Employment status | Independent contractor |
| Paid leave | ❌ None |
| Income guarantee | ❌ None |
| Safety net | ❌ None |

### When the world stops, her income stops

| Disruption | Days/Year | Income Impact |
|---|---|---|
| 🌧️ Heavy rainfall (>15mm/hr) | 20–40 | 80–100% loss |
| 💨 Severe AQI (>300) | 15–30 | 50–70% loss |
| 🚫 Protests / Bandhs | 5–15 | 100% loss |
| 🌊 Flash floods | 5–10 | 100% loss |

> **Annual income at risk: ₹40,000 – ₹80,000**

### Why nothing exists for her

| System | Why It Fails |
|---|---|
| Traditional insurance | Requires claims, takes weeks, annual commitment |
| Gig platform benefits | Covers accidents only, not income loss |
| Government schemes | Slow, bureaucratic, not designed for gig economy |

**Core failure:** No product matches the rhythm of gig work — fast, flexible, frictionless.

---

## 💡 Our Solution

**ShiftShield** is weekly parametric micro-insurance that automatically compensates gig workers when external conditions make earning impossible.

### How it works in 30 seconds

```
1. Subscribe weekly for ₹49–₹179 (AI-calculated for your zone)
2. We monitor weather, AQI, and disruptions in your work zone 24/7
3. Rainfall exceeds threshold? AQI hazardous?
4. ₹300–₹800 lands in your UPI within minutes
5. You did NOTHING. The system handled everything.
```

### What makes us different

| Traditional Insurance | ShiftShield |
|---|---|
| User files claim | Data triggers automatically |
| Manual verification | Algorithmic + anti-fraud |
| Days to weeks for payout | Minutes |
| Annual commitment | Weekly subscription |
| Subjective assessment | Objective thresholds |
| Complex paperwork | Zero paperwork |

---

## ⚙️ How It Works

### End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SHIFTSHIELD PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📱 ONBOARDING (2 min)                                              │
│  Phone OTP → Name + Platform → City + Zone → UPI + KYC → Active    │
│                          │                                          │
│                          ▼                                          │
│  📋 POLICY PURCHASE                                                 │
│  Select tier → AI calculates premium → Pay → Coverage starts        │
│                          │                                          │
│                          ▼                                          │
│  🔍 24/7 MONITORING (Background)                                    │
│  Weather API (30 min) ──┐                                           │
│  AQI Feed (60 min) ─────┼──► Threshold Engine ──► Trigger?          │
│  Flood Alerts ──────────┘         │                                 │
│                                   │ YES                             │
│                                   ▼                                 │
│  ⚡ TRIGGER ACTIVATION                                               │
│  Condition breached → Zone identified → Active policies found       │
│                          │                                          │
│                          ▼                                          │
│  🔒 FRAUD CHECK                                                     │
│  Device + Frequency + Timing + Location + Cohort = Fraud Score      │
│     │            │             │                                    │
│     ▼            ▼             ▼                                    │
│  Score < 40    40-70         > 70                                   │
│  AUTO-PAY    FLAG+PAY       HOLD                                    │
│                          │                                          │
│                          ▼                                          │
│  💰 INSTANT PAYOUT                                                  │
│  UPI transfer → Worker notified → Dashboard updated                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

### System Architecture

```
┌──────────────────┐     ┌──────────────────────────────────────────┐
│                  │     │            BACKEND (FastAPI)              │
│   React 19 SPA   │────▶│                                          │
│   (Vite + TW)    │◀────│  ┌─────────┐  ┌──────────┐  ┌────────┐  │
│                  │     │  │  Auth    │  │  Policy   │  │ Claims │  │
│  ┌────────────┐  │     │  │  Router  │  │  Router   │  │ Router │  │
│  │ Worker     │  │     │  └────┬────┘  └────┬──────┘  └───┬────┘  │
│  │ Dashboard  │  │     │       │            │             │       │
│  ├────────────┤  │     │  ┌────▼────────────▼─────────────▼────┐  │
│  │ Policy     │  │     │  │           SERVICE LAYER             │  │
│  │ Manager    │  │     │  │                                     │  │
│  ├────────────┤  │     │  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │ Claims     │  │     │  │  │  Premium    │  │  Trigger     │  │  │
│  │ Tracker    │  │     │  │  │  Engine     │  │  Monitor     │  │  │
│  ├────────────┤  │     │  │  │  (7 factors)│  │  (APScheduler│  │  │
│  │ Admin God  │  │     │  │  └─────────────┘  └─────────────┘  │  │
│  │ Mode Panel │  │     │  │  ┌─────────────┐  ┌─────────────┐  │  │
│  └────────────┘  │     │  │  │  Fraud      │  │  Payout     │  │  │
│                  │     │  │  │  Detector   │  │  Service     │  │  │
└──────────────────┘     │  │  └─────────────┘  └─────────────┘  │  │
                         │  └─────────────────────────────────────┘  │
                         │       │             │                     │
                         │  ┌────▼──┐    ┌─────▼───┐   ┌─────────┐  │
                         │  │SQLite │    │ Redis   │   │ Weather │  │
                         │  │  DB   │    │ Cache   │   │ + AQI   │  │
                         │  │       │    │         │   │  APIs   │  │
                         │  └───────┘    └─────────┘   └─────────┘  │
                         └──────────────────────────────────────────┘
```

### Data Flow for Auto-Claim

```
Weather API ──► Trigger Monitor (every 30 min)
                    │
                    ▼ threshold breached
              TriggerEvent created in DB
                    │
                    ▼
              Find active policies in affected zone
                    │
                    ▼
              For each policy:
                ├── Create Claim record
                ├── Run FraudDetector.calculate_fraud_score()
                ├── Score < 40? → Auto-approve → Process payout
                ├── Score 40-70? → Approve + Flag → Process payout
                └── Score > 70? → Hold → Notify admin
                    │
                    ▼
              PayoutService.process_payout()
                ├── Generate TXN ID
                ├── Simulate UPI transfer
                ├── Update claim status → "paid"
                └── Log to real-time stream
```

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend Framework** | FastAPI (Python) | Async, fast, auto-docs, type-safe |
| **ORM** | SQLAlchemy | Robust, flexible, hackathon-friendly |
| **Database** | SQLite (dev) | Zero-config, portable, demo-ready |
| **Cache** | Redis | Response caching, rate limiting |
| **Background Jobs** | APScheduler | Trigger polling every 30 minutes |
| **Auth** | JWT (python-jose) | Stateless, token-based |
| **HTTP Client** | Httpx | Async external API calls |
| **Frontend** | React 19 (Vite) | Fast HMR, modern React |
| **Styling** | Tailwind CSS | Utility-first, rapid UI development |
| **Animations** | Framer Motion | Premium, polished micro-interactions |
| **Charts** | Recharts | React-native charting for dashboards |
| **External APIs** | OpenWeatherMap, CPCB (mock) | Weather + AQI data sources |

---

## 🚀 Quick Start

### Prerequisites

```
Python 3.9+
Node.js 16+
Git
```

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/shiftshield.git
cd shiftshield
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# OR
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Seed sample data (populates DB with demo users, policies, claims)
python seed_data.py

# Start the server
uvicorn main:app --reload --port 8000
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

### 4. Run a Demo Simulation

```bash
# Option A: CLI Simulator
cd trigger_simulator
python simulate.py --city Mumbai --zone Dadar --trigger heavy_rain --value 32

# Option B: Admin Dashboard
# Navigate to /admin → Click "Simulate Trigger" → Select city + trigger → Fire 🔥
```

---

## 🎯 Features Deep Dive

### 1. Registration & Onboarding

**4 steps. 2 minutes. Done.**

```
Step 1: 📱 Phone + OTP
        Enter phone → Receive 6-digit OTP → Verify

Step 2: 👤 About You
        Name → Platform (Swiggy / Zomato / Both) → Working hours

Step 3: 📍 Your Zone
        City → Zone → Sub-zone (with live risk indicator)
        "⚠️ Dadar is HIGH risk for flooding"
        "💰 Estimated premium: ₹79–₹142/week"

Step 4: 💳 Payment Setup
        UPI ID → Aadhaar last 4 digits → Terms acceptance → Done ✅
```

**Design decisions:**
- Mobile-first — gig workers use phones, not laptops
- Minimal KYC — Aadhaar last 4 + UPI is sufficient for micro-insurance
- Zone-aware — risk indicator shown before purchase (transparency)
- No email required — phone-only auth matches gig worker behavior

---

### 2. AI-Powered Dynamic Premium Engine

This is the **core AI differentiator**. Premium is not a flat rate — it's calculated dynamically using **7 risk factors**.

#### The 7 Factors

| # | Factor | What It Measures | Range |
|---|---|---|---|
| 1 | **Zone Base Risk** | Historical risk profile of the city | 0.40 – 0.85 |
| 2 | **Sub-Zone Modifier** | Micro-location risk (e.g., Dadar floods more than Bandra) | 0.8x – 1.5x |
| 3 | **Seasonal Multiplier** | Is it monsoon? Winter smog? Heatwave season? | 0.8x – 1.8x |
| 4 | **Trust/Loyalty Discount** | Returning customers get rewarded | 0.90x – 1.2x |
| 5 | **Claim History Factor** | Too many recent claims? Price adjusts | 0.95x – 1.15x |
| 6 | **Weather Forecast Factor** | AI predicts: rain coming this week? Price adjusts | 0.9x – 1.4x |
| 7 | **Fraud Flag Surcharge** | Past fraud flags increase premium | 1.0x – 1.2x |

#### Formula

```python
final_premium = (base_rate
                 × zone_risk
                 × sub_zone_modifier
                 × seasonal_multiplier
                 × trust_discount
                 × claim_history_factor
                 × weather_forecast_factor)

# Clamped: ₹29 (floor) to ₹299 (ceiling)
```

#### Example: Priya in Mumbai-Dadar, July, Standard Tier

```
Base rate (Standard):                    ₹79
Mumbai zone risk (high floods):     × 1.30   → +30%
Dadar sub-zone (flood-prone):       × 1.10   → +10%
July (peak monsoon):                × 1.30   → +30%
Returning customer (week 5):        × 0.95   → -5%
Clean claim history:                × 1.00   →  0%
Rain forecast (4 days):             × 1.20   → +20%
────────────────────────────────────────────
Final weekly premium:                   ₹142

Explainer shown to user:
  "Mumbai zone has high flood risk (+30%)"
  "Dadar sub-zone is flood-prone (+10%)"
  "July is peak monsoon season (+30%)"
  "Returning customer discount (-5%)"
  "Rain forecast for 4 days this week (+20%)"
```

**Why this matters:** Judges see intelligent pricing, not a flat lookup table. Every user gets a personalized, explainable price.

---

### 3. Policy Management

| Operation | Endpoint | Description |
|---|---|---|
| **Create** | `POST /api/policy/create` | Select tier → AI calculates price → Coverage starts |
| **View Active** | `GET /api/policy/active` | Current coverage, days remaining, events left |
| **History** | `GET /api/policy/history` | Last 12 weeks with premiums paid vs payouts received |
| **Renew** | `POST /api/policy/renew` | Renew for next week (price may change!) |
| **Auto-Renew** | `PUT /api/policy/auto-renew` | Toggle automatic weekly renewal |
| **Upgrade** | `POST /api/policy/upgrade` | Change tier mid-week, pro-rated |
| **Cancel** | `DELETE /api/policy/cancel` | Cancel (coverage runs till week-end, no refund) |

#### Policy Tiers

| Tier | Base Rate | Max Payout/Event | Max Events/Week | Best For |
|---|---|---|---|---|
| 🥉 Basic | ₹49 | ₹300 | 2 | Part-time workers |
| 🥈 Standard | ₹79 | ₹450 | 3 | Regular delivery partners |
| 🥇 Premium | ₹129 | ₹600 | 4 | Full-time, high-risk zones |
| 💎 Ultra | ₹179 | ₹800 | 5 | Heavy earners, extreme zones |

#### Business Rules

- **One active policy per user** — no stacking
- **Anti-adverse-selection:** Cannot buy policy during an active trigger event
- **72-hour cooling period:** First-ever purchase + trigger within 72 hours = 50% payout
- **Auto-expiry:** Every Sunday 11:59 PM
- **Renewal nudge:** Saturday notification to renew

---

### 4. Parametric Trigger System

The heart of ShiftShield. The system monitors conditions 24/7 and fires triggers when thresholds are breached.

#### Defined Triggers

| Trigger | Metric | Threshold | Payout % | Data Source |
|---|---|---|---|---|
| 🌧️ Heavy Rain | Rainfall (mm/3hr) | > 25mm | 100% | OpenWeatherMap |
| 🌧️ Moderate Rain | Rainfall (mm/3hr) | > 15mm | 60% | OpenWeatherMap |
| 💨 Severe AQI | Air Quality Index | > 350 | 100% | CPCB / Mock |
| 💨 Bad AQI | Air Quality Index | > 300 | 50% | CPCB / Mock |
| 🌡️ Extreme Heat | Temperature (°C) | > 45°C | 100% | OpenWeatherMap |
| 🌡️ High Heat | Temperature (°C) | > 43°C | 60% | OpenWeatherMap |
| 🌊 Flood Warning | Flood alert level | Active | 100% | Mock |
| 🚫 Curfew/Bandh | Curfew status | Active | 100% | Mock |

#### Design Philosophy

> **We trigger payouts only when earning becomes impossible, not inconvenient.**

Light drizzle? Not a trigger. Roads submerged? Trigger.

#### Background Monitoring

```
APScheduler runs every 30 minutes:
  → Fetch weather for all active zones
  → Fetch AQI for all active cities
  → Compare against thresholds
  → If breached → initiate auto-claim flow for all affected policies
```

---

### 5. Zero-Touch Claims Automation

**The user does NOTHING. The system handles everything.**

```
TRIGGER FIRES
    │
    ▼
Find all active policies in affected zone
    │
    ▼
For each policy:
    ├── Check: policy active? ✓
    ├── Check: max events/week not exceeded? ✓
    ├── Calculate: payout = max_payout × trigger_payout_percentage
    ├── Run: FraudDetector.calculate_fraud_score()
    │       │
    │       ├── Score < 40  → AUTO-APPROVE → Process payout immediately
    │       ├── Score 40-70 → APPROVE + FLAG → Process payout, mark for review
    │       └── Score > 70  → HOLD → Notify admin for manual review
    │
    ▼
PayoutService.process_payout()
    ├── Generate mock TXN ID
    ├── Simulate UPI transfer
    ├── Update claim status → "paid"
    └── Worker sees: "₹450 deposited to priya@paytm ✅"
```

**Payout timing:**
- Auto-approved: Instant (simulated)
- Flagged: Instant with review flag
- Held: Pending admin approval

---

### 6. Intelligent Fraud Detection

#### 5-Signal Fraud Scoring

| Signal | Weight | What It Detects | Score Range |
|---|---|---|---|
| **Device Consistency** | 15% | Same device as registration? | 0–15 |
| **Claim Frequency** | 25% | Suspiciously many claims recently? | 0–25 |
| **Timing Pattern** | 20% | Subscribed right before a predictable event? | 0–20 |
| **Location Consistency** | 20% | Registered zone matches trigger zone? | 0–20 |
| **Cohort Analysis** | 20% | Solo claim vs cluster claim (real events affect many) | 0–20 |

#### Decision Thresholds

| Fraud Score | Risk Level | Action |
|---|---|---|
| 0 – 39 | 🟢 Low | Auto-approve, instant payout |
| 40 – 69 | 🟡 Medium | Approve + flag for review |
| 70 – 100 | 🔴 High | Hold, require admin review |

#### Why Cohort Analysis is Powerful

```
Real event: Heavy rain in Dadar
  → 45 workers in Dadar claim simultaneously
  → Cohort score: 0 (validates the event is real)
  → All auto-approved ✅

Fake claim: One worker claims "rain" but no one else does
  → Solo claim in a zone with no weather event
  → Cohort score: 20 (suspicious)
  → Combined with other signals → flagged/held ⚠️
```

> **To cheat ShiftShield, an attacker must fake weather data, spoof GPS, maintain clean account history, AND coordinate with a fake cohort. This makes fraud economically unviable.**

---

### 7. Admin "God Mode" Dashboard

A comprehensive insurer-facing analytics dashboard.

#### Dashboard Sections

**📊 Top Metrics**
- Active Policies (with week-over-week change)
- Claims Today
- Total Payouts This Week
- Loss Ratio (payouts / premiums — healthy if < 80%)

**📈 Analytics Charts**
- Premium vs Payouts trend (last 12 weeks)
- Claims by Status (donut: auto-approved / flagged / held / rejected)
- Trigger Events by Type (bar chart)
- Zone Risk Heatmap (table with color-coded risk levels)

**🚨 Fraud Alerts**
- List of flagged/held claims with fraud score breakdown
- One-click approve/reject for held claims

**🔮 Predictive Analytics (AI Showpiece)**
- "Next week forecast" based on weather predictions
- Estimated payouts per city
- Recommended financial reserves
- Suggested premium adjustments

**🎮 Simulation Controls (Demo Mode)**
- Select city + zone + trigger type
- Set trigger value with slider
- "Fire Trigger 🔥" button
- Real-time log stream showing every step of the auto-claim pipeline

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/send-otp` | Send OTP to phone number |
| `POST` | `/api/auth/verify-otp` | Verify OTP, get temp token |
| `POST` | `/api/auth/register` | Complete registration |
| `GET` | `/api/auth/profile` | Get user profile (JWT required) |
| `PUT` | `/api/auth/profile` | Update profile |

### Premium Calculation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/premium/calculate?tier=standard` | Calculate premium for logged-in user |
| `GET` | `/api/premium/all-tiers` | Show all 4 tier prices |
| `GET` | `/api/premium/factors` | Explain pricing factors |

### Policy Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/policy/create` | Create new weekly policy |
| `GET` | `/api/policy/active` | Get active policy details |
| `GET` | `/api/policy/history` | Last 12 weeks history |
| `POST` | `/api/policy/renew` | Renew for next week |
| `PUT` | `/api/policy/auto-renew` | Toggle auto-renewal |
| `POST` | `/api/policy/upgrade` | Upgrade tier mid-week |
| `DELETE` | `/api/policy/cancel` | Cancel current policy |

### Claims & Triggers

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/claims/my-claims` | User's claim history |
| `GET` | `/api/claims/{id}` | Detailed claim with fraud breakdown |
| `GET` | `/api/triggers/active` | Active triggers in user's zone |
| `GET` | `/api/triggers/history` | Past trigger events |
| `GET` | `/api/triggers/thresholds` | All trigger thresholds |

### Admin

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/dashboard-stats` | Dashboard metrics |
| `GET` | `/api/admin/weekly-trends` | 12-week premium vs payout trends |
| `GET` | `/api/admin/fraud-alerts` | Flagged claims for review |
| `GET` | `/api/admin/predictions` | Next-week predictive analytics |
| `POST` | `/api/admin/simulate-trigger` | Fire a simulated trigger event |

### Simulation

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/claims/simulate-full-flow` | End-to-end simulation with step-by-step log |

---

## 🎮 Trigger Simulation Guide

### Using the Admin Dashboard

```
1. Navigate to /admin
2. Scroll to "Simulation Controls"
3. Select: City → Mumbai, Zone → Dadar
4. Select: Trigger → Heavy Rain
5. Set value: 32 mm/3hr (threshold is 25)
6. Click "FIRE TRIGGER 🔥"
7. Watch the real-time log:
   ✅ Trigger detected
   ✅ 12 policies found
   ✅ 12 claims created
   ✅ Fraud checks: 10 auto-approved, 1 flagged, 1 held
   ✅ ₹4,500 total payout processed
```

### Using the CLI Simulator

```bash
# Single trigger
python simulate.py --city Mumbai --zone Dadar --trigger heavy_rain --value 32

# Preset scenarios
python simulate.py --scenario monsoon      # Rain across Mumbai, Pune, Bengaluru
python simulate.py --scenario delhi_smog   # AQI 420 across Delhi zones
python simulate.py --scenario heatwave     # 47°C in Jaipur
```

---

## 💰 Weekly Pricing Model

### Why Weekly?

| Reason | Explanation |
|---|---|
| **Affordable** | ₹49–₹179/week vs ₹5,000+/year for traditional insurance |
| **Matches gig rhythm** | Workers think in weeks, not months |
| **No lock-in** | Skip a week when you want, re-subscribe anytime |
| **Dynamic** | Price adjusts weekly based on conditions |

### Financial Viability

```
Average worker:
  Weekly premium paid:    ₹100 (avg across tiers and zones)
  Expected weekly claim:  ₹65 (actuarial estimate)
  Loss ratio:             65% (healthy range: 55-75%)
  Operating margin:       35%

For the insurer:
  1,000 workers × ₹100/week = ₹1,00,000 weekly premiums
  Expected payouts:               ₹65,000
  Operating costs:                ₹15,000
  Weekly profit:                  ₹20,000
```

### Price Transparency

Every user sees exactly **why** their premium is what it is:

```
Your Weekly Premium: ₹142

Breakdown:
  ├── Base rate (Standard tier):     ₹79
  ├── Mumbai high-risk zone:         +₹24  (+30%)
  ├── Dadar flood-prone sub-zone:    +₹9   (+10%)
  ├── July monsoon season:           +₹31  (+30%)
  ├── Loyal customer discount:       -₹7   (-5%)
  ├── Clean claim history:           ₹0    (0%)
  └── Rain forecast this week:       +₹20  (+20%)
  ═══════════════════════════════════════════
  Total:                             ₹142/week
  Maximum payout per event:          ₹450
  Events covered this week:          3
```

---

## 🎬 Demo Video

> 📹 **[Watch the 2-minute demo →](YOUR_VIDEO_LINK_HERE)**

### Demo Script

| Timestamp | Screen | Narration |
|---|---|---|
| 0:00–0:15 | Title + Problem | "Millions of gig workers lose 20-30% income to weather disruptions. ShiftShield is parametric micro-insurance that pays them automatically." |
| 0:15–0:35 | Registration flow | "Priya registers in 4 steps — phone OTP, her Swiggy platform, Mumbai-Dadar zone, and UPI ID. Two minutes, she's covered." |
| 0:35–0:55 | Premium page | "Our AI calculates her weekly premium: ₹142. See why — monsoon season, flood-prone zone, rain forecast. Every factor explained." |
| 0:55–1:10 | Buy policy | "She picks Standard tier. ₹450 max payout, 3 events per week. Coverage starts immediately." |
| 1:10–1:35 | **Admin triggers rain** | "Now watch — we simulate heavy rain in Dadar. 32mm detected, threshold is 25. System auto-creates claims for all 12 affected workers. Fraud checks run. Score 18 — auto-approved. ₹450 sent to her UPI." |
| 1:35–1:50 | Worker dashboard | "Priya's dashboard shows the payout. She did nothing. Zero touch." |
| 1:50–2:00 | Admin analytics | "Admin sees loss ratios, predictions for next week, fraud alerts. The full picture." |

---

## 📈 Phase 1 → Phase 2 Evolution

| Aspect | Phase 1 | Phase 2 |
|---|---|---|
| **Deliverable** | README + 2-min concept video | Working application + demo |
| **Premium** | Formula on paper | Live AI engine with 7 dynamic factors |
| **Triggers** | Threshold table | Real-time monitoring with APScheduler |
| **Claims** | Flow diagram | Fully automated pipeline |
| **Fraud** | Scoring concept | 5-signal detection system |
| **Frontend** | Not started | Premium React UI with animations |
| **Admin** | Not planned | God Mode dashboard with live simulation |
| **Database** | Not built | SQLite with full schema + seed data |
| **APIs** | Listed | Integrated (OpenWeatherMap + mocks) |

---

## 🔮 What's Next (Phase 3)

| Feature | Description |
|---|---|
| **Advanced Fraud Detection** | GPS spoofing detection, behavioral ML models (Isolation Forest) |
| **Instant Payout System** | Razorpay test mode / UPI sandbox integration |
| **ML Premium Model** | Gradient boosting for claim prediction, dynamic pricing regression |
| **Worker Dashboard v2** | Earnings protected graph, coverage calendar, renewal reminders |
| **Admin Predictive Analytics** | Next-week claim forecasting, reserve recommendations |
| **Performance** | Response time < 200ms, concurrent trigger processing |

---

## 🏗️ Project Structure

```
shiftshield/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── requirements.txt            # Python dependencies
│   ├── config.py                   # Configuration & constants
│   ├── database.py                 # SQLAlchemy setup
│   ├── models.py                   # Database models
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── seed_data.py                # Demo data population script
│   ├── routers/
│   │   ├── auth.py                 # Registration & authentication
│   │   ├── policy.py               # Policy CRUD operations
│   │   ├── premium.py              # Dynamic pricing endpoints
│   │   ├── claims.py               # Claims management
│   │   ├── triggers.py             # Trigger monitoring endpoints
│   │   └── admin.py                # Admin dashboard APIs
│   └── services/
│       ├── weather_service.py      # OpenWeatherMap integration
│       ├── aqi_service.py          # Air Quality Index service
│       ├── premium_engine.py       # 7-factor AI pricing engine
│       ├── trigger_monitor.py      # Background trigger polling
│       ├── fraud_detector.py       # 5-signal fraud scoring
│       ├── payout_service.py       # Mock UPI payout processing
│       └── risk_model.py           # Zone risk data & modeling
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Register.jsx        # 4-step onboarding
│   │   │   ├── Dashboard.jsx       # Worker home dashboard
│   │   │   ├── PolicyPage.jsx      # Policy selection & management
│   │   │   ├── ClaimsPage.jsx      # Claims history & tracking
│   │   │   └── AdminDashboard.jsx  # God Mode admin panel
│   │   ├── components/             # Reusable UI components
│   │   ├── services/
│   │   │   └── api.js              # Axios API client
│   │   ├── App.jsx                 # Router & layout
│   │   └── index.js                # Entry point
│   ├── package.json
│   └── vite.config.js
├── trigger_simulator/
│   └── simulate.py                 # CLI simulation tool
├── docs/
│   └── phase1_readme.md            # Original Phase 1 README
└── README.md                       # This file
```

---



---

<div align="center">

### Built with ❤️ for India's gig workers

**ShiftShield** — Income doesn't stop when the world does.

*Guidewire DEVTrails 2026 · Phase 2 Submission*

</div>
