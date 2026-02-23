# api/app/graph/decision_graph.py
from __future__ import annotations

from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from api.app.graph.nodes.extract_inputs import extract_inputs
from api.app.graph.nodes.risk_flags import risk_flags
from api.app.graph.nodes.score_alignment import score_alignment
from api.app.graph.nodes.write_memo import write_memo
from api.app.schemas.decision import GraphState


def _route_after_extract(state: GraphState) -> str:
    """After parsing intent, go to risk_flags for anomaly checks, else write_memo."""
    if state.get("intent") == "anomaly_check":
        return "risk_flags"
    return "write_memo"


def _route_after_risk(state: GraphState) -> str:
    """If an anomaly was found, pull DB context; otherwise go straight to write_memo."""
    if state.get("anomaly_detected"):
        return "score_alignment"
    return "write_memo"


def _build_graph() -> StateGraph:
    builder = StateGraph(GraphState)

    builder.add_node("extract_inputs", extract_inputs)
    builder.add_node("risk_flags", risk_flags)
    builder.add_node("score_alignment", score_alignment)
    builder.add_node("write_memo", write_memo)

    builder.set_entry_point("extract_inputs")
    builder.add_conditional_edges("extract_inputs", _route_after_extract)
    builder.add_conditional_edges("risk_flags", _route_after_risk)
    builder.add_edge("score_alignment", "write_memo")
    builder.add_edge("write_memo", END)

    return builder.compile()


_graph = _build_graph()


async def run_graph(
    message: str,
    request_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    initial_state: GraphState = {
        "message": message,
        "request_id": request_id,
        "metadata": metadata or {},
        "target_date": None,
        "intent": None,
        "analytics_result": None,
        "db_context": None,
        "anomaly_detected": False,
        "response": "",
        "actions_taken": [],
        "warnings": [],
    }

    final_state = await _graph.ainvoke(initial_state)

    return {
        "request_id": final_state["request_id"],
        "response": final_state["response"],
        "anomaly_detected": final_state["anomaly_detected"],
        "actions_taken": final_state["actions_taken"],
        "warnings": final_state["warnings"],
    }
