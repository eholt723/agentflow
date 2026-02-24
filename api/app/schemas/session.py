# api/app/schemas/session.py
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class SessionRecord(BaseModel):
    id: int
    session_id: Optional[str] = None
    request_id: str
    created_at: str
    endpoint: str
    # /agent/analyze fields
    filename: Optional[str] = None
    doc_type: Optional[str] = None
    doc_type_confidence: Optional[float] = None
    recommendation: Optional[str] = None
    # /agent fields
    message: Optional[str] = None
    intent: Optional[str] = None
    anomaly_detected: Optional[int] = None
    # shared
    summary: Optional[str] = None
    warnings: List[str] = []
