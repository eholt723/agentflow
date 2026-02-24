# api/app/graph/analyze_graph.py
from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from api.app.graph.nodes.classify_document import classify_document
from api.app.graph.nodes.analyze_resume import analyze_resume
from api.app.graph.nodes.analyze_interview import analyze_interview
from api.app.graph.nodes.analyze_scorecard import analyze_scorecard
from api.app.schemas.analyze import AnalyzeState
from api.app.schemas.agent import ToolAction

logger = logging.getLogger(__name__)


def write_analyze_memo(state: AnalyzeState) -> Dict[str, Any]:
    """
    Final node — logs completion and emits the finalize action.
    Analysis nodes enrich `analysis` and `summary` before this runs.
    """
    logger.info(
        "analyze_finalize request_id=%s doc_type=%s recommendation=%s",
        state.get("request_id"),
        state.get("doc_type"),
        state.get("analysis", {}).get("recommendation", "n/a"),
    )
    return {
        "actions_taken": [
            ToolAction(kind="event", name="analyze_finalize", ok=True, ms=0, details={})
        ],
    }


def _route_after_classify(state: AnalyzeState) -> str:
    doc_type = state.get("doc_type", "unknown")
    if doc_type == "resume":
        return "analyze_resume"
    if doc_type == "interview_notes":
        return "analyze_interview"
    if doc_type == "scorecard":
        return "analyze_scorecard"
    return "write_analyze_memo"


def _build_analyze_graph() -> StateGraph:
    builder = StateGraph(AnalyzeState)

    builder.add_node("classify_document", classify_document)
    builder.add_node("analyze_resume", analyze_resume)
    builder.add_node("analyze_interview", analyze_interview)
    builder.add_node("analyze_scorecard", analyze_scorecard)
    builder.add_node("write_analyze_memo", write_analyze_memo)

    builder.set_entry_point("classify_document")
    builder.add_conditional_edges("classify_document", _route_after_classify)
    builder.add_edge("analyze_resume", "write_analyze_memo")
    builder.add_edge("analyze_interview", "write_analyze_memo")
    builder.add_edge("analyze_scorecard", "write_analyze_memo")
    builder.add_edge("write_analyze_memo", END)

    return builder.compile()


_analyze_graph = _build_analyze_graph()


async def run_analyze_graph(
    filename: str,
    extension: str,
    text: str,
    rows: list,
    row_count: int,
    request_id: str,
    context: str = "",
) -> Dict[str, Any]:

    initial_state: AnalyzeState = {
        "filename": filename,
        "extension": extension,
        "text": text,
        "rows": rows,
        "row_count": row_count,
        "request_id": request_id,
        "context": context,
        "doc_type": None,
        "doc_type_confidence": 0.0,
        "key_fields": {},
        "analysis": {},
        "summary": "",
        "actions_taken": [],
        "warnings": [],
    }

    final_state = await _analyze_graph.ainvoke(initial_state)

    return {
        "request_id": final_state["request_id"],
        "filename": final_state["filename"],
        "doc_type": final_state["doc_type"] or "unknown",
        "doc_type_confidence": final_state["doc_type_confidence"],
        "key_fields": final_state["key_fields"],
        "analysis": final_state["analysis"],
        "summary": final_state["summary"],
        "actions_taken": final_state["actions_taken"],
        "warnings": final_state["warnings"],
    }
