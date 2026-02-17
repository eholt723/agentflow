from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AgentRequest(BaseModel):
    message: str
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    response: str
    anomaly_detected: Optional[bool] = None
    actions_taken: Optional[List[str]] = None
