from database import SessionLocal
from routers.admin import simulate_trigger, TriggerSimulationRequest

db = SessionLocal()
req = TriggerSimulationRequest(city="Mumbai", zone="Dadar", trigger_type="heavy_rain", trigger_value=30.0)
try:
    print(simulate_trigger(req, db))
except Exception as e:
    import traceback
    traceback.print_exc()
