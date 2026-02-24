# app/main.py
from __future__ import annotations

import uuid
from typing import Any, List, Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse

from api.app.schemas.agent import AgentRequest, AgentResponse, ToolAction
from api.app.schemas.analyze import AnalyzeResponse
from api.app.runner.agent_runner import run_agent
from api.app.runner.analyze_runner import run_analyze

app = FastAPI(title="AgentFlow HR Intelligence API")


@app.get("/health")
async def health():
    return {"status": "ok"}


def _normalize_actions(actions: Any) -> List[ToolAction]:
    """
    Ensures actions_taken always conforms to List[ToolAction],
    even if lower layers return strings or raw dicts.
    """
    if not actions:
        return []

    normalized: List[ToolAction] = []

    if isinstance(actions, list):
        for item in actions:
            if isinstance(item, ToolAction):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append(
                    ToolAction(kind="event", name=item, ok=True, ms=0, details={})
                )
            elif isinstance(item, dict):
                normalized.append(ToolAction(**item))
            else:
                normalized.append(
                    ToolAction(
                        kind="event", name="invalid_action_item", ok=False, ms=0,
                        details={"type": type(item).__name__},
                    )
                )
        return normalized

    return [
        ToolAction(
            kind="event", name="invalid_actions_shape", ok=False, ms=0,
            details={"type": type(actions).__name__},
        )
    ]


@app.post("/agent", response_model=AgentResponse)
async def agent(request: AgentRequest) -> AgentResponse:
    """
    Message-driven agent endpoint.

    Accepts: JSON { message, metadata? }
    Returns: consistent AgentResponse shape every time.
    """
    request_id = str(uuid.uuid4())

    try:
        result = await run_agent(
            message=request.message,
            request_id=request_id,
            metadata=request.metadata,
        )
        result["actions_taken"] = _normalize_actions(result.get("actions_taken"))
        return AgentResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        return AgentResponse(
            request_id=request_id,
            response="Agent failed to process the request.",
            anomaly_detected=False,
            actions_taken=[
                ToolAction(kind="event", name="agent_error", ok=False, ms=0,
                           details={"error": str(e)})
            ],
            warnings=[str(e)],
        )


@app.post("/agent/analyze", response_model=AnalyzeResponse)
async def analyze_file(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
) -> AnalyzeResponse:
    """
    Document analysis endpoint.

    Accepts: multipart/form-data with a PDF, DOCX, TXT, CSV, or XLSX file.
    Optional `context` field provides a hint to the classifier (e.g. job title being hired for).
    Returns: AnalyzeResponse with doc_type, key_fields, summary, and action trail.
    """
    filename = (file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename on upload.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    request_id = str(uuid.uuid4())

    try:
        result = await run_analyze(
            filename=filename,
            content=content,
            request_id=request_id,
            context=context or "",
        )
        result["actions_taken"] = _normalize_actions(result.get("actions_taken"))
        return AnalyzeResponse(**result)

    except HTTPException:
        raise

    except Exception as e:
        return AnalyzeResponse(
            request_id=request_id,
            filename=filename,
            doc_type="unknown",
            doc_type_confidence=0.0,
            summary="",
            actions_taken=[
                ToolAction(kind="event", name="analyze_error", ok=False, ms=0,
                           details={"error": str(e)})
            ],
            warnings=[str(e)],
        )
