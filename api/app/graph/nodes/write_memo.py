# graph/nodes/write_memo.py
from __future__ import annotations

from typing import Any, Dict

from api.app.schemas.agent import ToolAction
from api.app.schemas.decision import GraphState


def write_memo(state: GraphState) -> Dict[str, Any]:
    """
    Assemble the final response string from accumulated graph state.
    Always the last node before END.
    """
    analytics = state.get("analytics_result")
    db_context = state.get("db_context")
    target_date = state.get("target_date")
    anomaly_detected = state.get("anomaly_detected", False)

    if analytics:
        response = (
            f"Analytics for {target_date}: "
            f"{analytics['metric']} = {analytics['value']} "
            f"(avg {analytics['previous_average']}, "
            f"delta {analytics['delta_percent']}%). "
        )
        if anomaly_detected:
            response += "Anomaly detected. "
            if db_context:
                response += (
                    f"Context: {db_context['failed_transactions']} failed transactions, "
                    f"segment {db_context['top_customer_segment']}, "
                    f"region {db_context['region']}."
                )
        else:
            response += "No anomaly detected."
    else:
        response = f"Agent processed: {state['message']}"

    return {
        "response": response,
        "actions_taken": [
            ToolAction(kind="event", name="graph_finalize", ok=True, ms=0, details={})
        ],
    }
