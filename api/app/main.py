# app/main.py
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, List, Optional

from fastapi import FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from api.app.db.database import init_db
from api.app.db.repository import (
    get_sessions_by_id,
    list_sessions,
    save_agent_session,
    save_analyze_session,
)
from api.app.schemas.agent import AgentRequest, AgentResponse, ToolAction
from api.app.schemas.analyze import AnalyzeResponse
from api.app.schemas.session import SessionRecord
from api.app.runner.agent_runner import run_agent
from api.app.runner.analyze_runner import run_analyze

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="AgentFlow HR Intelligence API", lifespan=lifespan)


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


def _extract_recommendation(analysis: dict) -> Optional[str]:
    """Pull recommendation string out of analysis dict if present."""
    return analysis.get("recommendation") if isinstance(analysis, dict) else None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/agent", response_model=AgentResponse)
async def agent(
    request: AgentRequest,
    x_session_id: Optional[str] = Header(default=None),
) -> AgentResponse:
    """
    Message-driven agent endpoint.

    Accepts: JSON { message, metadata? }
    Optional header X-Session-ID groups related calls into one session.
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
        response = AgentResponse(**result)

        await save_agent_session(
            session_id=x_session_id,
            request_id=request_id,
            message=request.message,
            intent=result.get("intent"),
            anomaly_detected=result.get("anomaly_detected", False),
            summary=result.get("response", ""),
            warnings=result.get("warnings", []),
        )

        return response

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
    x_session_id: Optional[str] = Header(default=None),
) -> AnalyzeResponse:
    """
    Document analysis endpoint.

    Accepts: multipart/form-data with a PDF, DOCX, TXT, CSV, XLSX, or image file.
    Optional header X-Session-ID groups related calls into one session.
    Optional `context` field provides a hint to the classifier.
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
        response = AnalyzeResponse(**result)

        await save_analyze_session(
            session_id=x_session_id,
            request_id=request_id,
            filename=filename,
            doc_type=result.get("doc_type", "unknown"),
            doc_type_confidence=result.get("doc_type_confidence", 0.0),
            recommendation=_extract_recommendation(result.get("analysis", {})),
            summary=result.get("summary", ""),
            warnings=result.get("warnings", []),
        )

        return response

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


@app.get("/sessions", response_model=List[SessionRecord])
async def get_sessions(limit: int = Query(default=20, ge=1, le=100)):
    """Return the most recent sessions across all endpoints."""
    rows = await list_sessions(limit=limit)
    return [SessionRecord(**r) for r in rows]


@app.get("/sessions/{session_id}", response_model=List[SessionRecord])
async def get_session(session_id: str):
    """Return all records grouped under a specific session_id."""
    rows = await get_sessions_by_id(session_id)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No session found: {session_id}")
    return [SessionRecord(**r) for r in rows]
