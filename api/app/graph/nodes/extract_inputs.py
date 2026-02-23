# graph/nodes/extract_inputs.py
from __future__ import annotations

import re
import time
from datetime import date, timedelta
from typing import Any, Dict

from api.app.schemas.agent import ToolAction
from api.app.schemas.decision import GraphState


def _parse_date(message: str) -> str:
    m = re.search(r"\b(yesterday|today)\b", message.lower())
    if m and m.group(1) == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    return date.today().isoformat()


def extract_inputs(state: GraphState) -> Dict[str, Any]:
    """
    Parse the raw message and determine intent and target date.
    Routes to 'anomaly_check' or 'general'.
    """
    message = state["message"]
    intent = "anomaly_check" if "anomaly" in message.lower() else "general"
    target_date = _parse_date(message)

    return {
        "intent": intent,
        "target_date": target_date,
        "actions_taken": [
            ToolAction(kind="event", name="graph_start", ok=True, ms=0, details={}),
            ToolAction(kind="route", name=intent, ok=True, ms=0, details={"target_date": target_date}),
        ],
    }
