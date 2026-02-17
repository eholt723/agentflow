# runner/agent_runner.py
from __future__ import annotations

from typing import Any, Dict, Optional

from api.app.graph.decision_graph import run_graph


async def run_agent(
    message: str,
    request_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Orchestrates the agent run. Today: simple graph stub.
    Later: LangGraph compile + invoke.
    """
    return await run_graph(message=message, request_id=request_id, metadata=metadata)
