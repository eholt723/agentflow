from __future__ import annotations

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="AgentFlow Universal File Intelligence API")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/agent/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    run_anomaly: bool = Query(True, description="Run tabular anomaly detection when applicable"),
    run_dedup: bool = Query(True, description="Run tabular dedup/standardization when applicable"),
):
    """
    Phase 1: Contract-first endpoint.

    Accepts: CSV/XLSX/PDF/DOCX/TXT
    Returns: consistent JSON shape every time (reports enabled/disabled based on routing).
    """

    filename = (file.filename or "").strip()
    content_type = (file.content_type or "").strip().lower()

    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename on upload.")

    # Basic, deterministic fallback classification (Phase 1)
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext in {"csv", "xlsx", "xls"}:
        doc_label = "tabular_data"
        doc_reason = f"File extension .{ext} indicates tabular data."
        doc_confidence = 0.95
        routed = "tabular"
    elif ext in {"pdf", "docx", "txt"}:
        doc_label = "document_text"
        doc_reason = f"File extension .{ext} indicates a text document."
        doc_confidence = 0.85
        routed = "document"
    else:
        doc_label = "unknown"
        doc_reason = "File extension not recognized; treating as unknown."
        doc_confidence = 0.4
        routed = "unknown"

    # Contract-first, consistent shape
    payload = {
        "document_type": {
            "label": doc_label,
            "confidence": doc_confidence,
            "reason": doc_reason,
        },
        "detected": {
            "file_name": filename,
            "content_type": content_type or None,
            "file_extension": ext or None,
        },
        "tabular_reports": {
            "anomaly_report": {"enabled": bool(routed == "tabular" and run_anomaly), "anomalies": []},
            "dedup_report": {
                "enabled": bool(routed == "tabular" and run_dedup),
                "entity_column": None,
                "clusters": [],
            },
        },
        "document_reports": {
            "policy_check": {
                "enabled": bool(routed == "document"),
                "key_points": [],
                "risks": [],
                "missing": [],
            }
        },
        "summary": (
            "Detected tabular data; ready to run anomaly + dedup analyzers."
            if routed == "tabular"
            else "Detected document text; ready to run key points / risk checklist analyzer."
            if routed == "document"
            else "Could not confidently classify file; no analyzers run."
        ),
        "actions_taken": ["classified_document_type"],
    }

    return JSONResponse(content=payload)
