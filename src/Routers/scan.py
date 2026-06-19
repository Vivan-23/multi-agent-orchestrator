from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.Database.database import get_db
from src.Database import crud
from src.Database.models import ScanRun
from src.Schemas.scan import ScanRequest, ScanResponse, RunSummary, LogResponse
from src.Core.orchestrator import run_pipeline

router = APIRouter()

@router.post("/run", response_model=ScanResponse)
def run_scan(payload: ScanRequest, db: Session = Depends(get_db)):
    try:
        # Run orchestrator pipeline
        state = run_pipeline(payload.input, payload.model)
        
        # Query DB to get the created ScanRun record (which contains the timestamp)
        db_run = db.query(ScanRun).filter(ScanRun.run_id == state["run_id"]).first()
        
        # Build the final response
        metrics_dict = state.get("metrics") or {}
        metrics_data = {
            "steps_count": metrics_dict.get("steps_count", len(state.get("steps", []))),
            "tool_error_rate": metrics_dict.get("tool_error_rate", 0.0),
            "schema_valid": metrics_dict.get("schema_valid", False),
            "unique_sources": metrics_dict.get("unique_sources", 0),
            "eval_score": metrics_dict.get("eval_score", 0)
        }
        
        resp_data = {
            "input": state.get("input"),
            "steps": state.get("steps", []),
            "data": state.get("data", {}),
            "output": state.get("output", {}),
            "errors": state.get("errors", 0),
            "retries": state.get("retries", 0),
            "run_id": state.get("run_id"),
            "model": state.get("model"),
            "risk_level": state.get("risk_level"),
            "model_used": state.get("model_used"),
            "metrics": metrics_data,
            "timestamp": db_run.timestamp if db_run else None,
            "diff": state.get("diff")
        }
        return resp_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs", response_model=List[RunSummary])
def get_runs(db: Session = Depends(get_db)):
    try:
        recent_runs = crud.get_recent_runs(db, limit=5)
        results = []
        for run in recent_runs:
            metrics_dict = run.metrics or {}
            
            # Extract metrics properties
            errors_val = metrics_dict.get("errors", 0)
            steps_count_val = metrics_dict.get("steps_count", len(metrics_dict.get("steps", [])))
            tool_error_rate_val = metrics_dict.get("tool_error_rate", 0.0)
            schema_valid_val = metrics_dict.get("schema_valid", False)
            unique_sources_val = metrics_dict.get("unique_sources", 0)
            eval_score_val = metrics_dict.get("eval_score", 0)
            
            metrics_obj = {
                "steps_count": steps_count_val,
                "tool_error_rate": tool_error_rate_val,
                "schema_valid": schema_valid_val,
                "unique_sources": unique_sources_val,
                "eval_score": eval_score_val
            }
            
            results.append({
                "run_id": run.run_id,
                "input": run.input,
                "output": run.output or {},
                "model_used": run.model_used,
                "metrics": metrics_obj,
                "errors": errors_val,
                "timestamp": run.timestamp
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{run_id}", response_model=List[LogResponse])
def get_logs(run_id: str, db: Session = Depends(get_db)):
    try:
        db_logs = crud.get_logs_by_run_id(db, run_id)
        results = []
        for log in db_logs:
            results.append({
                "timestamp": log.timestamp,
                "run_id": log.run_id,
                "agent": log.agent,
                "event": log.event,
                "status": log.status,
                "message": log.message
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
