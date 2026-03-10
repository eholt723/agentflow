"""
Unit tests for Pydantic schemas, the _normalize_actions helper, and the DB layer.

Marked ``unit`` — no HTTP, no Groq, no TestClient.  These run in milliseconds.
The async DB test demonstrates pytest-asyncio integration against a real
(temporary) SQLite file.
"""
import pytest
from pydantic import ValidationError

from api.app.main import _normalize_actions
from api.app.schemas.agent import AgentRequest, ToolAction


# ---------------------------------------------------------------------------
# ToolAction — valid kinds
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.parametrize("kind", ["route", "tool", "event", "llm"])
def test_tool_action_accepts_all_valid_kinds(kind):
    action = ToolAction(kind=kind, name="op", ok=True, ms=0, details={})
    assert action.kind == kind


@pytest.mark.unit
def test_tool_action_rejects_invalid_kind():
    with pytest.raises(ValidationError):
        ToolAction(kind="unknown_kind", name="op", ok=True, ms=0, details={})


@pytest.mark.unit
def test_tool_action_defaults():
    action = ToolAction(kind="event", name="ping")
    assert action.ok is True
    assert action.ms == 0
    assert action.details == {}


# ---------------------------------------------------------------------------
# AgentRequest — validation
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_agent_request_rejects_empty_string():
    with pytest.raises(ValidationError):
        AgentRequest(message="")


@pytest.mark.unit
def test_agent_request_accepts_optional_metadata():
    req = AgentRequest(message="check", metadata={"source": "test"})
    assert req.metadata == {"source": "test"}


# ---------------------------------------------------------------------------
# _normalize_actions — edge cases
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_normalize_actions_passes_through_tool_action_objects():
    action = ToolAction(kind="llm", name="extract_inputs", ok=True, ms=100, details={})
    result = _normalize_actions([action])
    assert result == [action]


@pytest.mark.unit
def test_normalize_actions_coerces_dicts():
    raw = {"kind": "tool", "name": "analytics_query", "ok": True, "ms": 50, "details": {}}
    result = _normalize_actions([raw])
    assert isinstance(result[0], ToolAction)
    assert result[0].name == "analytics_query"


@pytest.mark.unit
def test_normalize_actions_coerces_strings():
    result = _normalize_actions(["some_legacy_event"])
    assert isinstance(result[0], ToolAction)
    assert result[0].kind == "event"
    assert result[0].name == "some_legacy_event"


@pytest.mark.unit
def test_normalize_actions_returns_empty_on_none():
    assert _normalize_actions(None) == []


@pytest.mark.unit
def test_normalize_actions_returns_empty_on_empty_list():
    assert _normalize_actions([]) == []


# ---------------------------------------------------------------------------
# Async DB layer — pytest-asyncio integration
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_db_initializes_and_list_sessions_returns_empty(tmp_path, monkeypatch):
    """
    Directly exercises the DB layer without going through HTTP.
    Demonstrates pytest-asyncio (asyncio_mode = 'auto' in pyproject.toml).
    """
    from api.app.db.database import init_db
    from api.app.db.repository import list_sessions
    from api.app.settings import settings

    monkeypatch.setattr(settings, "db_path", str(tmp_path / "unit_test.db"))
    await init_db()

    rows = await list_sessions(limit=10)
    assert rows == []
    assert (tmp_path / "unit_test.db").exists()
