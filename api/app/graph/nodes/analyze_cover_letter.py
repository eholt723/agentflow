# graph/nodes/analyze_cover_letter.py
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from api.app.clients.inference_client import run_inference
from api.app.schemas.agent import ToolAction
from api.app.schemas.analyze import AnalyzeState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert hiring analyst reviewing a cover letter.

Analyze the cover letter and return ONLY a valid JSON object with these fields:

{
  "candidate_name": "<name if identifiable, else ''>",
  "target_role": "<role they are applying for, if stated>",
  "target_company": "<company they are addressing, if stated>",
  "first_impression": "<1 sentence — overall tone and quality>",
  "motivation_clarity": "<how clearly and compellingly they explain why they want this role>",
  "communication_quality": "<assessment of writing clarity, professionalism, and structure>",
  "role_fit_signals": ["<evidence or claims of fit for the role>"],
  "red_flags": ["<concerns: generic letter, unexplained gaps, poor writing, over-claims, etc.>"],
  "recommendation": "<follow_up | pass>",
  "recommendation_confidence": <float 0.0 to 1.0>,
  "narrative": "<2-3 paragraph hiring memo summarising your assessment>"
}

Return ONLY the JSON object. No markdown fences, no explanation."""


async def analyze_cover_letter(state: AnalyzeState) -> Dict[str, Any]:
    text = state["text"]
    context = state.get("context", "")
    t0 = time.perf_counter()

    context_line = f"\n\nHiring context: {context}" if context else ""
    user_prompt = f"Cover letter text:\n\n{text}{context_line}"

    try:
        raw = await run_inference(_SYSTEM_PROMPT, user_prompt)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        parsed = json.loads(cleaned)
        recommendation = parsed.get("recommendation", "pass")
        confidence = float(parsed.get("recommendation_confidence", 0.5))
        narrative = parsed.get("narrative", "")

        logger.info(
            "analyze_cover_letter filename=%s recommendation=%s confidence=%.2f ms=%d ok=true",
            state["filename"], recommendation, confidence, elapsed_ms,
        )

        return {
            "analysis": parsed,
            "summary": narrative,
            "actions_taken": [
                ToolAction(kind="llm", name="analyze_cover_letter", ok=True, ms=elapsed_ms,
                           details={"recommendation": recommendation, "confidence": confidence,
                                    "red_flags": len(parsed.get("red_flags", []))})
            ],
        }

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.warning("analyze_cover_letter failed=%s ms=%d", exc, elapsed_ms)
        return {
            "analysis": {},
            "summary": "",
            "actions_taken": [
                ToolAction(kind="llm", name="analyze_cover_letter", ok=False, ms=elapsed_ms,
                           details={"error": str(exc)})
            ],
            "warnings": [f"Cover letter analysis failed: {exc}"],
        }
