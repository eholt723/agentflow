"""
Contract tests for POST /agent.

These tests verify the API surface (field names, types, HTTP status codes)
without hitting the Groq API.  The ``client`` fixture in conftest.py patches
run_agent with a deterministic AsyncMock.
"""
import uuid

import pytest


# ---------------------------------------------------------------------------
# Happy path — response shape
# ---------------------------------------------------------------------------

def test_agent_response_has_required_keys(client):
    r = client.post("/agent", json={"message": "Check for anomaly yesterday"})
    assert r.status_code == 200
    data = r.json()

    assert "request_id"      in data
    assert "response"        in data
    assert "anomaly_detected" in data
    assert "actions_taken"   in data
    assert "warnings"        in data


def test_agent_response_types(client):
    r = client.post("/agent", json={"message": "Check for anomaly yesterday"})
    data = r.json()

    assert isinstance(data["request_id"],       str)
    assert isinstance(data["response"],          str)
    assert isinstance(data["anomaly_detected"],  bool)
    assert isinstance(data["actions_taken"],     list)
    assert isinstance(data["warnings"],          list)


def test_agent_request_id_is_uuid(client):
    """Every response carries a valid UUID, even when the mock overrides the value."""
    r = client.post("/agent", json={"message": "Risk check"})
    data = r.json()
    # main.py generates its own request_id — should always be a valid UUID
    uuid.UUID(data["request_id"])  # raises ValueError if malformed


def test_agent_actions_have_tool_action_shape(client):
    r = client.post("/agent", json={"message": "anomaly check"})
    for action in r.json()["actions_taken"]:
        assert "kind" in action
        assert "name" in action
        assert "ok"   in action
        assert "ms"   in action
        assert action["kind"] in {"route", "tool", "event", "llm"}


def test_agent_accepts_optional_metadata(client):
    r = client.post("/agent", json={"message": "flag risk", "metadata": {"source": "hr_portal"}})
    assert r.status_code == 200


def test_agent_x_session_id_header_accepted(client):
    r = client.post(
        "/agent",
        json={"message": "anomaly check"},
        headers={"X-Session-ID": "session-abc-123"},
    )
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Validation — bad input
# ---------------------------------------------------------------------------

def test_agent_rejects_missing_message(client):
    r = client.post("/agent", json={})
    assert r.status_code == 422


def test_agent_rejects_empty_message(client):
    """min_length=1 is enforced at the schema level."""
    r = client.post("/agent", json={"message": ""})
    assert r.status_code == 422
