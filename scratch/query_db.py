from src.Database.database import SessionLocal
from src.Database.models import ScanRun, ScanLog
import json

db = SessionLocal()
try:
    print("--- SCAN RUNS ---")
    runs = db.query(ScanRun).all()
    for r in runs:
        print(f"ID: {r.id} | RunID: {r.run_id} | Input: {r.input} | Model: {r.model_used} | Risk: {r.output.get('risk_level') if r.output else 'None'}")
        print(f"Output: {json.dumps(r.output)}")
        print(f"Metrics: {json.dumps(r.metrics)}")
        print("-" * 50)
        
    print("\n--- SCAN LOGS ---")
    logs = db.query(ScanLog).order_by(ScanLog.timestamp).all()
    for l in logs:
        print(f"ID: {l.id} | RunID: {l.run_id} | Agent: {l.agent} | Event: {l.event} | Status: {l.status} | Message: {l.message}")
        print("-" * 50)
finally:
    db.close()
