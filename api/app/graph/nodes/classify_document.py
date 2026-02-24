# graph/nodes/classify_document.py
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from api.app.clients.inference_client import run_inference
from api.app.schemas.agent import ToolAction
from api.app.schemas.analyze import AnalyzeState, VALID_DOC_TYPES

logger = logging.getLogger(__name__)

_CLASSIFY_SYSTEM_PROMPT = """You are a document classifier for an HR and hiring intelligence system.

Analyze the document text provided and return ONLY a valid JSON object with these exact fields:

{
  "doc_type": "<one of: resume, job_desc, interview_notes, scorecard, policy_doc, perf_review, unknown>",
  "confidence": <float 0.0 to 1.0>,
  "summary": "<1-2 sentence description of what this document is>",
  "key_fields": {
    // resume:          { "name": "", "current_role": "", "top_skills": [], "years_experience": "", "education": "" }
    // job_desc:        { "title": "", "company": "", "required_skills": [], "seniority_level": "" }
    // interview_notes: { "candidate_name": "", "interview_date": "", "interviewer": "", "key_observations": [], "concerns": [] }
    // scorecard:       { "candidate_name": "", "dimensions": [{"name": "", "score": ""}], "overall_rating": "" }
    // policy_doc:      { "policy_name": "", "key_obligations": [], "risk_flags": [] }
    // perf_review:     { "employee_name": "", "review_period": "", "overall_rating": "", "strengths": [], "concerns": [] }
    // unknown:         {}
  }
}

Return ONLY the JSON object. No markdown fences, no explanation."""


def _extension_fallback(extension: str) -> str:
    """Fallback classification based on file extension only."""
    return {
        "pdf": "unknown", "docx": "unknown", "txt": "unknown",
        "csv": "scorecard", "xlsx": "scorecard", "xls": "scorecard",
    }.get(extension, "unknown")


async def classify_document(state: AnalyzeState) -> Dict[str, Any]:
    """
    Classify the uploaded document type and extract key fields via LLM.
    Falls back to extension-based classification if LLM fails.
    """
    text = state["text"]
    extension = state["extension"]
    t0 = time.perf_counter()

    if not text.strip():
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.warning("classify_document empty_text filename=%s", state["filename"])
        return {
            "doc_type": _extension_fallback(extension),
            "doc_type_confidence": 0.3,
            "key_fields": {},
            "summary": "Document appears to be empty or unreadable.",
            "actions_taken": [
                ToolAction(kind="llm", name="classify_document", ok=False, ms=elapsed_ms,
                           details={"reason": "empty_text"})
            ],
            "warnings": ["Document text was empty; classification defaulted to extension."],
        }

    context_hint = f"\n\nContext from user: {state['context']}" if state.get("context") else ""
    user_prompt = f"Document text:\n\n{text}{context_hint}"

    try:
        raw = await run_inference(_CLASSIFY_SYSTEM_PROMPT, user_prompt)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        # Strip markdown fences if the model wrapped output anyway
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        parsed = json.loads(cleaned)
        doc_type = parsed.get("doc_type", "unknown").lower().strip()
        if doc_type not in VALID_DOC_TYPES:
            logger.warning("classify_document unknown_type=%r falling_back=extension", doc_type)
            doc_type = _extension_fallback(extension)

        confidence = float(parsed.get("confidence", 0.5))
        summary = parsed.get("summary", "")
        key_fields = parsed.get("key_fields", {})

        logger.info(
            "classify_document filename=%s doc_type=%s confidence=%.2f ms=%d ok=true",
            state["filename"], doc_type, confidence, elapsed_ms,
        )

        return {
            "doc_type": doc_type,
            "doc_type_confidence": confidence,
            "key_fields": key_fields,
            "summary": summary,
            "actions_taken": [
                ToolAction(kind="llm", name="classify_document", ok=True, ms=elapsed_ms,
                           details={"doc_type": doc_type, "confidence": confidence})
            ],
        }

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        fallback = _extension_fallback(extension)
        logger.warning(
            "classify_document failed=%s falling_back=%s ms=%d", exc, fallback, elapsed_ms
        )
        return {
            "doc_type": fallback,
            "doc_type_confidence": 0.3,
            "key_fields": {},
            "summary": "",
            "actions_taken": [
                ToolAction(kind="llm", name="classify_document", ok=False, ms=elapsed_ms,
                           details={"error": str(exc), "fallback": fallback})
            ],
            "warnings": [f"LLM classification failed: {exc}"],
        }
