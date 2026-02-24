# graph/nodes/analyze_scorecard.py
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

from api.app.clients.inference_client import run_inference
from api.app.schemas.agent import ToolAction
from api.app.schemas.analyze import AnalyzeState

logger = logging.getLogger(__name__)

_ANALYZE_SCORECARD_SYSTEM = """You are an HR analytics expert specializing in hiring bias detection and panel evaluation quality.

You will receive structured statistics computed from a candidate evaluation scorecard.
Return ONLY a valid JSON object:

{
  "evaluator_findings": [
    {"evaluator": "...", "finding": "...", "severity": "low|medium|high"}
  ],
  "candidate_findings": [
    {"candidate": "...", "finding": "...", "severity": "low|medium|high"}
  ],
  "bias_signals": [],
  "top_candidates": [],
  "recommendation_summary": "...",
  "narrative": "..."
}

Guidelines:
- evaluator_findings: flag evaluators whose average score deviates significantly from the panel,
  or who show inconsistent scoring patterns across dimensions
- candidate_findings: flag candidates with unusually high variance across evaluators
  (panel disagreement), or who were scored as outliers in any dimension
- bias_signals: infer potential halo effects, recency bias, or leniency/severity bias
- top_candidates: rank the top candidates by average overall score
- narrative: 2-3 paragraph summary for the hiring manager covering panel alignment,
  standout candidates, and any concerns about evaluator reliability

Return ONLY the JSON object. No markdown fences, no explanation."""


def _compute_scorecard_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute per-candidate and per-evaluator statistics from scorecard rows.
    Detects which columns are ratings (numeric) vs identifiers (text).
    """
    if not rows:
        return {}

    import statistics

    # Detect column types from first row
    sample = rows[0]
    id_cols: List[str] = []
    rating_cols: List[str] = []

    for col, val in sample.items():
        try:
            float(str(val).replace(",", ""))
            rating_cols.append(col)
        except (ValueError, TypeError):
            id_cols.append(col)

    if not rating_cols:
        return {"error": "No numeric rating columns found in scorecard."}

    # Try to identify candidate and evaluator columns heuristically
    candidate_col = next(
        (c for c in id_cols if any(k in c.lower() for k in ("candidate", "name", "applicant"))),
        id_cols[0] if id_cols else None,
    )
    evaluator_col = next(
        (c for c in id_cols if any(k in c.lower() for k in ("evaluator", "interviewer", "reviewer", "rater"))),
        id_cols[1] if len(id_cols) > 1 else None,
    )

    def safe_float(v: Any) -> float:
        try:
            return float(str(v).replace(",", ""))
        except (ValueError, TypeError):
            return 0.0

    # Per-row overall score (mean of all rating columns)
    for row in rows:
        row["_overall"] = sum(safe_float(row.get(c, 0)) for c in rating_cols) / len(rating_cols)

    # Global stats
    all_scores = [r["_overall"] for r in rows]
    global_mean = statistics.mean(all_scores) if all_scores else 0
    global_stdev = statistics.stdev(all_scores) if len(all_scores) > 1 else 0

    # Per-candidate stats
    candidate_stats: Dict[str, Any] = {}
    if candidate_col:
        from itertools import groupby
        candidates_grouped: Dict[str, List[float]] = {}
        for row in rows:
            cname = str(row.get(candidate_col, "unknown"))
            candidates_grouped.setdefault(cname, []).append(row["_overall"])
        for cname, scores in candidates_grouped.items():
            mean = statistics.mean(scores)
            var = statistics.stdev(scores) if len(scores) > 1 else 0
            candidate_stats[cname] = {
                "mean": round(mean, 2),
                "stdev": round(var, 2),
                "n_evaluators": len(scores),
                "high_variance": var > 1.0,
            }

    # Per-evaluator stats
    evaluator_stats: Dict[str, Any] = {}
    if evaluator_col:
        evaluators_grouped: Dict[str, List[float]] = {}
        for row in rows:
            ename = str(row.get(evaluator_col, "unknown"))
            evaluators_grouped.setdefault(ename, []).append(row["_overall"])
        for ename, scores in evaluators_grouped.items():
            mean = statistics.mean(scores)
            deviation = mean - global_mean
            evaluator_stats[ename] = {
                "mean": round(mean, 2),
                "deviation_from_panel": round(deviation, 2),
                "outlier": abs(deviation) > max(global_stdev * 1.5, 0.5),
                "n_ratings": len(scores),
            }

    return {
        "rating_columns": rating_cols,
        "candidate_column": candidate_col,
        "evaluator_column": evaluator_col,
        "global_mean": round(global_mean, 2),
        "global_stdev": round(global_stdev, 2),
        "n_rows": len(rows),
        "candidate_stats": candidate_stats,
        "evaluator_stats": evaluator_stats,
    }


async def analyze_scorecard(state: AnalyzeState) -> Dict[str, Any]:
    """
    Detects scoring anomalies, evaluator bias, and panel disagreement in
    candidate evaluation scorecards. Runs after classify_document when
    doc_type == 'scorecard'.
    """
    rows = state["rows"]
    text = state["text"]
    context = state.get("context", "")
    t0 = time.perf_counter()

    if not rows:
        # Scorecard uploaded as PDF/DOCX — fall back to text-based LLM analysis
        logger.warning("analyze_scorecard no_rows filename=%s falling_back=text", state["filename"])
        rows_available = False
        stats: Dict[str, Any] = {}
        stats_text = f"Raw scorecard text:\n{text}"
    else:
        rows_available = True
        stats = _compute_scorecard_stats(rows)
        stats_text = f"Computed statistics:\n{json.dumps(stats, indent=2)}"

    context_line = f"\nHiring context: {context}" if context else ""
    user_prompt = f"{stats_text}{context_line}"

    try:
        raw = await run_inference(_ANALYZE_SCORECARD_SYSTEM, user_prompt)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        parsed = json.loads(cleaned)

        analysis = {
            "stats": stats if rows_available else {},
            "evaluator_findings": parsed.get("evaluator_findings", []),
            "candidate_findings": parsed.get("candidate_findings", []),
            "bias_signals": parsed.get("bias_signals", []),
            "top_candidates": parsed.get("top_candidates", []),
            "recommendation_summary": parsed.get("recommendation_summary", ""),
        }
        summary = parsed.get("narrative", "")

        anomaly_count = len(analysis["evaluator_findings"]) + len(analysis["candidate_findings"])
        logger.info(
            "analyze_scorecard filename=%s anomalies=%d top_candidates=%d ms=%d ok=true",
            state["filename"], anomaly_count, len(analysis["top_candidates"]), elapsed_ms,
        )

        return {
            "analysis": analysis,
            "summary": summary,
            "actions_taken": [
                ToolAction(kind="llm", name="analyze_scorecard", ok=True, ms=elapsed_ms,
                           details={
                               "rows_analyzed": len(rows),
                               "anomaly_count": anomaly_count,
                               "top_candidates": len(analysis["top_candidates"]),
                           })
            ],
        }

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.error("analyze_scorecard failed=%s ms=%d", exc, elapsed_ms)
        return {
            "analysis": {"stats": stats},
            "actions_taken": [
                ToolAction(kind="llm", name="analyze_scorecard", ok=False, ms=elapsed_ms,
                           details={"error": str(exc)})
            ],
            "warnings": [f"Scorecard analysis failed: {exc}"],
        }
