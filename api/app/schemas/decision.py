# schemas/decision.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class DecisionContext(BaseModel):
    """Carries the working state through the decision graph."""
    message: str
    request_id: str
    target_date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
