from sqlalchemy import func
from sqlalchemy.orm import Session
from src.Database.models import ScanRun, ScanLog

def save_run(db: Session, state: dict):
    run_id = state.get("run_id")
    if not run_id:
        return None

    db_run = db.query(ScanRun).filter(ScanRun.run_id == run_id).first()

    # extract fields
    user_input = state.get("input")
    output = state.get("output")
    model_used = state.get("model_used")
    metrics = state.get("metrics") or {}
    
    if isinstance(metrics, dict):
        metrics = dict(metrics)  # make a copy to avoid mutation side effects
        metrics["errors"] = state.get("errors", 0)
        metrics["steps"] = state.get("steps", [])

    if db_run:
        db_run.input = user_input
        db_run.output = output
        db_run.model_used = model_used
        db_run.metrics = metrics
    else:
        db_run = ScanRun(
            run_id=run_id,
            input=user_input,
            output=output,
            model_used=model_used,
            metrics=metrics
        )
        db.add(db_run)

    db.commit()
    db.refresh(db_run)
    return db_run

def save_log(db: Session, run_id: str, agent: str, event: str, status: str, message: str = None):
    db_log = ScanLog(
        run_id=run_id,
        agent=agent,
        event=event,
        status=status,
        message=message
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_recent_runs(db: Session, limit: int = 5):
    return db.query(ScanRun).order_by(ScanRun.timestamp.desc()).limit(limit).all()

def get_logs_by_run_id(db: Session, run_id: str):
    return db.query(ScanLog).filter(ScanLog.run_id == run_id).order_by(ScanLog.timestamp.asc()).all()

def get_last_scan_for_domain(db: Session, domain: str, exclude_run_id: str = None):
    """
    Returns the most recent ScanRun for this exact domain string,
    excluding the current run if exclude_run_id is provided.
    Returns None if no previous scan exists.
    """
    query = db.query(ScanRun).filter(func.lower(ScanRun.input) == func.lower(domain))
    if exclude_run_id:
        query = query.filter(ScanRun.run_id != exclude_run_id)
    return query.order_by(ScanRun.timestamp.desc()).first()
