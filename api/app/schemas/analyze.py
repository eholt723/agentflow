# schemas/analyze.py
from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field

from api.app.schemas.agent import ToolAction

VALID_DOC_TYPES = {
    "resume",
    "job_desc",
    "interview_notes",
    "scorecard",
    "policy_doc",
    "perf_review",
    "unknown",
}


class AnalyzeState(TypedDict):
    """Shared state passed through every node in the LangGraph analyze graph."""
    filename: str
    extension: str
    text: str                              # extracted text (may be truncated)
    rows: List[Dict[str, Any]]             # populated for CSV/XLSX only
    row_count: int
    request_id: str
    context: str                           # optional user-provided hint
    doc_type: Optional[str]               # set by classify_document node
    doc_type_confidence: float
    key_fields: Dict[str, Any]            # extracted by classify_document
    analysis: Dict[str, Any]              # filled by analysis nodes (Phase 4b)
    summary: str
    actions_taken: Annotated[List[ToolAction], operator.add]
    warnings: Annotated[List[str], operator.add]


class AnalyzeResponse(BaseModel):
    request_id: str
    filename: str
    doc_type: str
    doc_type_confidence: float
    key_fields: Dict[str, Any] = Field(default_factory=dict)
    analysis: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    actions_taken: List[ToolAction] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
