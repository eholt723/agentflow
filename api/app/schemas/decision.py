# schemas/decision.py
from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from api.app.schemas.agent import ToolAction


class GraphState(TypedDict):
    """Shared state passed through every node in the LangGraph decision graph."""
    message: str
    request_id: str
    metadata: Dict[str, Any]
    target_date: Optional[str]
    intent: Optional[str]                          # "anomaly_check" | "general"
    analytics_result: Optional[Dict[str, Any]]
    db_context: Optional[Dict[str, Any]]
    anomaly_detected: bool
    response: str
    actions_taken: Annotated[List[ToolAction], operator.add]   # each node appends
    warnings: Annotated[List[str], operator.add]               # each node appends
