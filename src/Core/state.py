# src/Core/state.py
from pydantic import BaseModel
from typing import List, Dict, Optional

class AgentState(BaseModel):
    input: str
    steps: List[str] = []
    data: Dict = {}
    output: Dict = {}
    errors: int = 0
    retries: int = 0
    run_id: str
    model: str = "fast"

    # computed later
    risk_level: Optional[str] = None
    model_used: Optional[str] = None