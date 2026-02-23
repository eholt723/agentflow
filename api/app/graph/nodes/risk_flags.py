# graph/nodes/risk_flags.py
from __future__ import annotations

import time
from typing import Any, Dict

from api.app.graph.tools.analytics_tool import run_analytics_query
from api.app.schemas.agent import ToolAction
from api.app.schemas.decision import GraphState


def risk_flags(state: GraphState) -> Dict[str, Any]:
    """
    Run the analytics query and flag whether an anomaly was detected.
    Only reached when intent == 'anomaly_check'.
    """
    target_date = state["target_date"]
    t0 = time.perf_counter()

    try:
        result = run_analytics_query(target_date)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "analytics_result": result,
            "anomaly_detected": bool(result.get("anomaly", False)),
            "actions_taken": [
                ToolAction(kind="tool", name="analytics_query", ok=True, ms=elapsed_ms,
                           details={"date": target_date})
            ],
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "anomaly_detected": False,
            "actions_taken": [
                ToolAction(kind="tool", name="analytics_query", ok=False, ms=elapsed_ms,
                           details={"date": target_date, "error": str(e)})
            ],
            "warnings": [str(e)],
        }
