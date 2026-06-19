import json
from datetime import datetime
import os

LOG_FILE = "logs/run_logs.jsonl"

# ensure logs folder exists
os.makedirs("logs", exist_ok=True)


def log_event(agent: str, step: str, status: str, run_id: str, error: str = None):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "run_id": run_id,   # 🔥 important
        "agent": agent,
        "step": step,
        "status": status,
        "error": error
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    try:
        from src.Database.database import SessionLocal
        from src.Database.crud import save_log
        
        db = SessionLocal()
        try:
            save_log(
                db=db,
                run_id=run_id,
                agent=agent,
                event=step,
                status=status,
                message=error
            )
            db.commit()
            print(f"[DB] Successfully saved log event for agent '{agent}' (event: '{step}', run_id: {run_id}) to database.")
        except Exception as e:
            db.rollback()
            print(f"[DB ERROR] Error committing transaction in log_event: {e}")
            raise
        finally:
            db.close()
    except Exception as db_err:
        print(f"[DB ERROR] Failed to log to database: {db_err}")