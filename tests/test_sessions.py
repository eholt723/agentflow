"""
Tests for GET /sessions and GET /sessions/{session_id}.

The client fixture redirects SQLite to a per-test temp file, so each test
starts with a clean database.  Sessions are populated by making real /agent
calls through the mock, which still trigger the DB writes in main.py.
"""
import pytest


# ---------------------------------------------------------------------------
# GET /sessions
# ---------------------------------------------------------------------------

def test_sessions_returns_list_on_empty_db(client):
    r = client.get("/sessions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_sessions_returns_list_after_agent_call(client):
    client.post("/agent", json={"message": "anomaly check"})
    r = client.get("/sessions")
    assert r.status_code == 200
    sessions = r.json()
    assert len(sessions) >= 1


def test_sessions_limit_param_restricts_results(client):
    for i in range(5):
        client.post("/agent", json={"message": f"check {i}"})

    r = client.get("/sessions?limit=3")
    assert r.status_code == 200
    assert len(r.json()) <= 3


@pytest.mark.parametrize("bad_limit", [0, 101])
def test_sessions_limit_rejects_out_of_range(client, bad_limit):
    r = client.get(f"/sessions?limit={bad_limit}")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}
# ---------------------------------------------------------------------------

def test_session_by_id_returns_404_for_unknown(client):
    r = client.get("/sessions/nonexistent-session-xyz")
    assert r.status_code == 404


def test_session_by_id_returns_grouped_records(client):
    sid = "test-session-grouping"
    client.post("/agent", json={"message": "check A"}, headers={"X-Session-ID": sid})
    client.post("/agent", json={"message": "check B"}, headers={"X-Session-ID": sid})

    r = client.get(f"/sessions/{sid}")
    assert r.status_code == 200
    records = r.json()
    assert len(records) == 2
    assert all(rec["session_id"] == sid for rec in records)
