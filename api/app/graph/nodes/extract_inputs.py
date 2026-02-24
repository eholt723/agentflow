# graph/nodes/extract_inputs.py
from __future__ import annotations

import logging
import re
import time
from datetime import date, timedelta
from typing import Any, Dict

from api.app.clients.inference_client import run_inference
from api.app.schemas.agent import ToolAction
from api.app.schemas.decision import GraphState

logger = logging.getLogger(__name__)

_INTENT_SYSTEM_PROMPT = """You are an intent classifier for a business operations assistant.
Classify the user's message as exactly one of the following intents:
- anomaly_check: the user wants to detect or investigate anomalies, unusual patterns, or spikes in data
- general: anything else

Return only the intent label, nothing else. No explanation."""

_VALID_INTENTS = {"anomaly_check", "general"}


def _parse_date(message: str) -> str:
    m = re.search(r"\b(yesterday|today)\b", message.lower())
    if m and m.group(1) == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    return date.today().isoformat()


def _keyword_intent(message: str) -> str:
    return "anomaly_check" if "anomaly" in message.lower() else "general"


async def extract_inputs(state: GraphState) -> Dict[str, Any]:
    """
    Parse the raw message and determine intent and target date.
    Uses LLM for intent classification with keyword fallback.
    """
    message = state["message"]
    target_date = _parse_date(message)
    t0 = time.perf_counter()

    try:
        raw = await run_inference(_INTENT_SYSTEM_PROMPT, message)
        intent = raw.strip().lower()
        if intent not in _VALID_INTENTS:
            logger.warning("llm returned unknown intent=%r, falling back to keyword", intent)
            intent = _keyword_intent(message)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        llm_ok = True
        logger.info("intent_classify intent=%s ms=%d llm=true", intent, elapsed_ms)
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.warning("intent_classify llm_failed=%s falling_back=keyword ms=%d", exc, elapsed_ms)
        intent = _keyword_intent(message)
        llm_ok = False

    return {
        "intent": intent,
        "target_date": target_date,
        "actions_taken": [
            ToolAction(kind="event", name="graph_start", ok=True, ms=0, details={}),
            ToolAction(kind="llm", name="intent_classify", ok=llm_ok, ms=elapsed_ms,
                       details={"intent": intent, "target_date": target_date}),
            ToolAction(kind="route", name=intent, ok=True, ms=0, details={"target_date": target_date}),
        ],
    }
