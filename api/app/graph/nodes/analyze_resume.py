# graph/nodes/analyze_resume.py
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from api.app.clients.inference_client import run_inference
from api.app.schemas.agent import ToolAction
from api.app.schemas.analyze import AnalyzeState

logger = logging.getLogger(__name__)

_ANALYZE_RESUME_SYSTEM = """You are an expert HR analyst and technical recruiter.

Analyze the resume provided and return ONLY a valid JSON object with these exact fields:

{
  "strengths": [],
  "experience_highlights": [],
  "skill_gaps": [],
  "risk_signals": [
    {"flag": "...", "severity": "low|medium|high", "detail": "..."}
  ],
  "seniority_assessment": "junior|mid|senior|lead|principal",
  "recommendation": "strong_hire|hire|consider|pass",
  "recommendation_confidence": 0.0,
  "narrative": "..."
}

Guidelines:
- strengths: 3-5 concrete strengths backed by evidence in the resume
- experience_highlights: 3-5 most impressive achievements or experiences
- skill_gaps: skills commonly expected for this role/level that appear missing or weak
- risk_signals: flag employment gaps (>6mo), short tenures (<1yr), no impact metrics,
  unclear progression, skill staleness (tech >5yrs old with no recent equivalent)
- seniority_assessment: infer from years of experience, role titles, and scope of work
- recommendation: your overall hiring recommendation
- narrative: 2-3 paragraph hiring manager memo — lead with recommendation, then evidence,
  then concerns or open questions

Return ONLY the JSON object. No markdown fences, no explanation."""


async def analyze_resume(state: AnalyzeState) -> Dict[str, Any]:
    """
    Deep resume analysis: strengths, risk signals, skill gaps, recommendation, narrative memo.
    Runs after classify_document when doc_type == 'resume'.
    """
    text = state["text"]
    context = state.get("context", "")
    key_fields = state.get("key_fields", {})
    t0 = time.perf_counter()

    context_line = f"\nHiring context: {context}" if context else ""
    classifier_line = (
        f"\nClassifier extracted: role={key_fields.get('current_role', 'unknown')}, "
        f"years={key_fields.get('years_experience', 'unknown')}"
        if key_fields else ""
    )
    user_prompt = f"Resume text:\n\n{text}{context_line}{classifier_line}"

    try:
        raw = await run_inference(_ANALYZE_RESUME_SYSTEM, user_prompt)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        parsed = json.loads(cleaned)

        analysis = {
            "strengths": parsed.get("strengths", []),
            "experience_highlights": parsed.get("experience_highlights", []),
            "skill_gaps": parsed.get("skill_gaps", []),
            "risk_signals": parsed.get("risk_signals", []),
            "seniority_assessment": parsed.get("seniority_assessment", ""),
            "recommendation": parsed.get("recommendation", ""),
            "recommendation_confidence": float(parsed.get("recommendation_confidence", 0.0)),
        }
        summary = parsed.get("narrative", "")

        logger.info(
            "analyze_resume filename=%s recommendation=%s confidence=%.2f ms=%d ok=true",
            state["filename"], analysis["recommendation"],
            analysis["recommendation_confidence"], elapsed_ms,
        )

        return {
            "analysis": analysis,
            "summary": summary,
            "actions_taken": [
                ToolAction(kind="llm", name="analyze_resume", ok=True, ms=elapsed_ms,
                           details={
                               "recommendation": analysis["recommendation"],
                               "confidence": analysis["recommendation_confidence"],
                               "risk_count": len(analysis["risk_signals"]),
                           })
            ],
        }

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.error("analyze_resume failed=%s ms=%d", exc, elapsed_ms)
        return {
            "analysis": {},
            "actions_taken": [
                ToolAction(kind="llm", name="analyze_resume", ok=False, ms=elapsed_ms,
                           details={"error": str(exc)})
            ],
            "warnings": [f"Resume analysis failed: {exc}"],
        }
