import random
from datetime import datetime, timezone, timedelta
from database import SessionLocal, Base, engine
from models import User, Policy, Claim, TriggerEvent, Platform, PolicyTier, TriggerType, ClaimStatus

def seed_database():
    db = SessionLocal()
    try:
        print("Clearing existing data...")
        db.query(Claim).delete()
        db.query(Policy).delete()
        db.query(TriggerEvent).delete()
        db.query(User).delete()
        db.commit()

        print("Seeding 20 Users...")
        cities = [("Mumbai", "Dadar"), ("Mumbai", "Bandra"), ("Delhi", "Connaught Place"), ("Bengaluru", "Koramangala")]
        names = ["Aarti", "Rahul", "Priya", "Vikram", "Sneha", "Karan", "Anjali", "Ravi", "Pooja", "Amit",
                 "Neha", "Sanjay", "Kavita", "Rohan", "Meera", "Ajay", "Swati", "Nikhil", "Divya", "Arun"]
        users = []
        for i in range(20):
            city, sub = random.choice(cities)
            user = User(
                phone=f"+919876543{i:03d}",
                name=names[i % len(names)],
                city=city,
                zone=city,
                sub_zone=sub,
                platform=random.choice(list(Platform)),
                trust_score=random.uniform(60.0, 99.0)
            )
            db.add(user)
            users.append(user)
        db.commit()

        print("Seeding 15 Policies...")
        policies = []
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        
        for i in range(15):
            tier = random.choice(list(PolicyTier))
            premium = 49.0 if tier == PolicyTier.BASIC else 99.0 if tier == PolicyTier.STANDARD else 159.0
            payout = premium * 5
            
            # Mix of active and expired/historical
            is_active = i < 10
            start = week_start if is_active else (week_start - timedelta(days=7))
            
            policy = Policy(
                user_id=users[i].id,
                tier=tier,
                weekly_premium=premium,
                max_payout_per_event=payout,
                max_events_per_week=3,
                start_date=start.date(),
                end_date=(start + timedelta(days=6)).date(),
                is_active=is_active
            )
            db.add(policy)
            policies.append(policy)
        db.commit()

        print("Seeding 5 Trigger Events...")
        trigger_types = [TriggerType.RAIN, TriggerType.AQI, TriggerType.HEAT]
        events = []
        for i in range(5):
            t_type = random.choice(trigger_types)
            city, sub = random.choice(cities)
            event = TriggerEvent(
                zone=city,
                sub_zone=sub,
                trigger_type=t_type,
                measured_value=random.uniform(30.0, 150.0),
                threshold=random.uniform(30.0, 40.0),
                triggered_at=now - timedelta(hours=random.randint(1, 48)),
                affected_policies_count=random.randint(1, 10),
                total_payout=random.randint(1000, 5000)
            )
            db.add(event)
            events.append(event)
        db.commit()

        print("Seeding 10 Historical Claims...")
        statuses = [ClaimStatus.PAID, ClaimStatus.AUTO_APPROVED, ClaimStatus.UNDER_REVIEW, ClaimStatus.REJECTED]
        weights = [0.5, 0.2, 0.2, 0.1]
        
        for i in range(10):
            pol = random.choice(policies)
            status = random.choices(statuses, weights=weights)[0]
            score = random.uniform(30.0, 95.0)
            if status in [ClaimStatus.UNDER_REVIEW, ClaimStatus.REJECTED]:
                score = random.uniform(20.0, 50.0) # Lower trust drives review
            
            c = Claim(
                policy_id=pol.id,
                user_id=pol.user_id,
                trigger_type=random.choice(list(TriggerType)),
                trigger_value=random.uniform(50.0, 200.0),
                threshold_value=40.0,
                payout_amount=pol.max_payout_per_event,
                status=status,
                fraud_score=score,
                initiated_at=now - timedelta(hours=random.randint(1, 72))
            )
            db.add(c)
        db.commit()
        print("Database seeding complete! ✨")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
