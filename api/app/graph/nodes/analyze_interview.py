# graph/nodes/analyze_interview.py
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from api.app.clients.inference_client import run_inference
from api.app.schemas.agent import ToolAction
from api.app.schemas.analyze import AnalyzeState

logger = logging.getLogger(__name__)

_ANALYZE_INTERVIEW_SYSTEM = """You are a senior HR analyst specializing in structured hiring decisions.

You will receive raw interview notes — these may be rough, unformatted, or written quickly.
Convert them into a structured decision memo and return ONLY a valid JSON object:

{
  "candidate_name": "...",
  "role": "...",
  "interview_date": "...",
  "interviewer": "...",
  "key_observations": [],
  "technical_signals": {
    "strengths": [],
    "gaps": [],
    "unclear": []
  },
  "behavioral_signals": {
    "positive": [],
    "concerns": []
  },
  "inconsistencies": [],
  "open_questions": [],
  "recommendation": "strong_hire|hire|consider|pass",
  "recommendation_confidence": 0.0,
  "narrative": "..."
}

Guidelines:
- key_observations: 3-6 notable moments or statements from the interview
- technical_signals.unclear: topics that came up but were not explored enough to assess
- behavioral_signals: infer communication style, ownership, team fit, culture signals
- inconsistencies: anything that contradicts their resume or prior statements
- open_questions: questions the interviewer should ask in a follow-up
- recommendation_confidence: lower if notes are thin or ambiguous
- narrative: 2-3 paragraph structured decision memo — lead with recommendation,
  support with evidence from the notes, end with open questions or next steps

Return ONLY the JSON object. No markdown fences, no explanation."""


async def analyze_interview(state: AnalyzeState) -> Dict[str, Any]:
    """
    Converts raw interview notes into a structured hiring decision memo.
    Runs after classify_document when doc_type == 'interview_notes'.
    """
    text = state["text"]
    context = state.get("context", "")
    key_fields = state.get("key_fields", {})
    t0 = time.perf_counter()

    context_line = f"\nHiring context: {context}" if context else ""
    classifier_line = (
        f"\nClassifier identified: candidate={key_fields.get('candidate_name', 'unknown')}, "
        f"interviewer={key_fields.get('interviewer', 'unknown')}"
        if key_fields else ""
    )
    user_prompt = f"Interview notes:\n\n{text}{context_line}{classifier_line}"

    try:
        raw = await run_inference(_ANALYZE_INTERVIEW_SYSTEM, user_prompt)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        parsed = json.loads(cleaned)

        analysis = {
            "candidate_name": parsed.get("candidate_name", ""),
            "role": parsed.get("role", ""),
            "interview_date": parsed.get("interview_date", ""),
            "interviewer": parsed.get("interviewer", ""),
            "key_observations": parsed.get("key_observations", []),
            "technical_signals": parsed.get("technical_signals", {}),
            "behavioral_signals": parsed.get("behavioral_signals", {}),
            "inconsistencies": parsed.get("inconsistencies", []),
            "open_questions": parsed.get("open_questions", []),
            "recommendation": parsed.get("recommendation", ""),
            "recommendation_confidence": float(parsed.get("recommendation_confidence", 0.0)),
        }
        summary = parsed.get("narrative", "")

        logger.info(
            "analyze_interview filename=%s recommendation=%s confidence=%.2f ms=%d ok=true",
            state["filename"], analysis["recommendation"],
            analysis["recommendation_confidence"], elapsed_ms,
        )

        return {
            "analysis": analysis,
            "summary": summary,
            "actions_taken": [
                ToolAction(kind="llm", name="analyze_interview", ok=True, ms=elapsed_ms,
                           details={
                               "recommendation": analysis["recommendation"],
                               "confidence": analysis["recommendation_confidence"],
                               "inconsistencies": len(analysis["inconsistencies"]),
                               "open_questions": len(analysis["open_questions"]),
                           })
            ],
        }

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.error("analyze_interview failed=%s ms=%d", exc, elapsed_ms)
        return {
            "analysis": {},
            "actions_taken": [
                ToolAction(kind="llm", name="analyze_interview", ok=False, ms=elapsed_ms,
                           details={"error": str(exc)})
            ],
            "warnings": [f"Interview analysis failed: {exc}"],
        }
