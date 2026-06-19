from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class ScanRequest(BaseModel):
    input: str
    model: Optional[str] = "llama3-8b-8192"

class MetricSchema(BaseModel):
    steps_count: int
    tool_error_rate: float
    schema_valid: bool
    unique_sources: int
    eval_score: int

class ScanResponse(BaseModel):
    input: str
    steps: List[str] = []
    data: Dict[str, Any] = {}
    output: Dict[str, Any] = {}
    errors: int = 0
    retries: int = 0
    run_id: str
    model: Optional[str] = None
    risk_level: Optional[str] = None
    model_used: Optional[str] = None
    metrics: Optional[MetricSchema] = None
    timestamp: Optional[datetime] = None
    diff: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class RunSummary(BaseModel):
    run_id: str
    input: str
    output: Dict[str, Any] = {}
    model_used: Optional[str] = None
    metrics: Optional[MetricSchema] = None
    errors: int = 0
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class LogResponse(BaseModel):
    timestamp: datetime
    run_id: str
    agent: str
    event: str
    status: str
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
