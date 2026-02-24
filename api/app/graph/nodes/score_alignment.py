# graph/nodes/score_alignment.py
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from api.app.graph.tools.database_tool import run_database_lookup
from api.app.schemas.agent import ToolAction
from api.app.schemas.decision import GraphState

logger = logging.getLogger(__name__)


def score_alignment(state: GraphState) -> Dict[str, Any]:
    """
    Pull business context from the database to explain a detected anomaly.
    Only reached when anomaly_detected == True.
    """
    target_date = state["target_date"]
    t0 = time.perf_counter()

    try:
        result = run_database_lookup(target_date)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.info("database_lookup date=%s ms=%d ok=true", target_date, elapsed_ms)
        return {
            "db_context": result,
            "actions_taken": [
                ToolAction(kind="tool", name="database_lookup", ok=True, ms=elapsed_ms,
                           details={"date": target_date})
            ],
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.error("database_lookup date=%s error=%s ms=%d ok=false", target_date, e, elapsed_ms)
        return {
            "actions_taken": [
                ToolAction(kind="tool", name="database_lookup", ok=False, ms=elapsed_ms,
                           details={"error": str(e)})
            ],
            "warnings": [str(e)],
        }
