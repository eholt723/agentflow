"""
Shared fixtures for the AgentFlow test suite.

The ``client`` fixture patches both async runners (run_agent, run_analyze) so
tests never touch the Groq API.  Each test gets a fresh TestClient backed by a
temporary SQLite database via ``monkeypatch`` + ``tmp_path``.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.app.main import app
from api.app.schemas.agent import ToolAction
from api.app.settings import settings

# ---------------------------------------------------------------------------
# Canonical mock payloads — mirrors what the real runners return
# ---------------------------------------------------------------------------

_AGENT_RESULT = {
    "request_id": "mock-agent-request-id",
    "response": "No anomaly detected in the requested date range.",
    "anomaly_detected": False,
    "intent": "anomaly_check",
    "actions_taken": [
        ToolAction(kind="route", name="intent_classification", ok=True, ms=12, details={"intent": "anomaly_check"}),
        ToolAction(kind="llm",   name="extract_inputs",        ok=True, ms=310, details={}),
        ToolAction(kind="tool",  name="analytics_query",       ok=True, ms=88,  details={"rows": 0}),
    ],
    "warnings": [],
}

_ANALYZE_RESULT = {
    "request_id": "mock-analyze-request-id",
    "filename": "sample_resume.txt",
    "doc_type": "resume",
    "doc_type_confidence": 0.95,
    "key_fields": {"name": "Jane Doe", "skills": ["Python", "LangGraph", "FastAPI"]},
    "analysis": {"recommendation": "Strong candidate — proceed to technical interview."},
    "summary": "Senior engineer with 8 years experience in Python and distributed systems.",
    "actions_taken": [
        ToolAction(kind="route", name="classify_document", ok=True, ms=180, details={"doc_type": "resume"}),
        ToolAction(kind="llm",   name="analyze_resume",   ok=True, ms=520, details={}),
    ],
    "warnings": [],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_agent() -> AsyncMock:
    """AsyncMock for api.app.runner.agent_runner.run_agent.

    Uses side_effect so the generated request_id from main.py is echoed back
    in the response — matching real runner behaviour.
    """
    async def _side_effect(message, request_id, **kwargs):
        return {**_AGENT_RESULT, "request_id": request_id}

    return AsyncMock(side_effect=_side_effect)


@pytest.fixture()
def mock_analyze() -> AsyncMock:
    """AsyncMock for api.app.runner.analyze_runner.run_analyze."""
    return AsyncMock(return_value=dict(_ANALYZE_RESULT))


@pytest.fixture()
def client(tmp_path, monkeypatch, mock_agent, mock_analyze) -> TestClient:
    """
    FastAPI TestClient with:
    - both async runners replaced with deterministic AsyncMocks
    - SQLite DB redirected to a per-test temp file (no leftover state)
    """
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test.db"))

    with (
        patch("api.app.main.run_agent",   mock_agent),
        patch("api.app.main.run_analyze", mock_analyze),
    ):
        with TestClient(app) as c:
            yield c
