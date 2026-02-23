# api/app/decision_graph.py
from __future__ import annotations

import re
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from api.app.graph.tools.analytics_tool import run_analytics_query
from api.app.graph.tools.database_tool import run_database_lookup
from api.app.schemas.agent import ToolAction


def _extract_target_date(message: str) -> str:
    m = re.search(r"\b(yesterday|today)\b", message.lower())
    if m and m.group(1) == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    return date.today().isoformat()


def _action(kind: str, name: str, ok: bool, ms: int, details: Dict[str, Any] = {}) -> ToolAction:
    return ToolAction(kind=kind, name=name, ok=ok, ms=ms, details=details)


async def run_graph(
    message: str,
    request_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    actions_taken: List[ToolAction] = [
        _action("event", "graph_start", ok=True, ms=0)
    ]
    warnings: List[str] = []

    anomaly_route = "anomaly" in message.lower()

    if anomaly_route:
        actions_taken.append(_action("route", "anomaly_check", ok=True, ms=0))

        target_date = _extract_target_date(message)

        # ---- Analytics Tool ----
        t0 = time.perf_counter()
        try:
            analytics_result = run_analytics_query(target_date)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            actions_taken.append(
                _action("tool", "analytics_query", ok=True, ms=elapsed_ms, details={"date": target_date})
            )
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            actions_taken.append(
                _action("tool", "analytics_query", ok=False, ms=elapsed_ms, details={"date": target_date, "error": str(e)})
            )
            warnings.append(str(e))
            actions_taken.append(_action("event", "graph_finalize", ok=False, ms=0))
            return {
                "request_id": request_id,
                "response": "Analytics query failed.",
                "anomaly_detected": False,
                "actions_taken": actions_taken,
                "warnings": warnings,
            }

        anomaly_detected = bool(analytics_result.get("anomaly", False))

        # ---- Database Tool (only if anomaly detected) ----
        db_context = None
        if anomaly_detected:
            t1 = time.perf_counter()
            try:
                db_context = run_database_lookup(target_date)
                elapsed_ms = int((time.perf_counter() - t1) * 1000)
                actions_taken.append(
                    _action("tool", "database_lookup", ok=True, ms=elapsed_ms, details={"date": target_date})
                )
            except Exception as e:
                elapsed_ms = int((time.perf_counter() - t1) * 1000)
                actions_taken.append(
                    _action("tool", "database_lookup", ok=False, ms=elapsed_ms, details={"error": str(e)})
                )
                warnings.append(str(e))

        # ---- Build Response ----
        response = (
            f"Analytics for {target_date}: "
            f"{analytics_result['metric']} = {analytics_result['value']} "
            f"(avg {analytics_result['previous_average']}, "
            f"delta {analytics_result['delta_percent']}%). "
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
        actions_taken.append(_action("route", "general", ok=True, ms=0))
        anomaly_detected = False
        response = f"Agent processed: {message}"

    actions_taken.append(_action("event", "graph_finalize", ok=True, ms=0))

    return {
        "request_id": request_id,
        "response": response,
        "anomaly_detected": anomaly_detected,
        "actions_taken": actions_taken,
        "warnings": warnings,
    }
