# schemas/agent.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class ToolAction(BaseModel):
    kind: Literal["route", "tool", "event"]
    name: str
    ok: bool = True
    ms: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)


class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    request_id: str
    response: str
    anomaly_detected: bool = False
    actions_taken: List[ToolAction] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
