"""
Contract tests for POST /agent/analyze.

File uploads are simulated via FastAPI's multipart form support in TestClient.
The ``mock_analyze`` fixture lets individual tests override the runner's return
value to exercise different classification paths without calling Groq.
"""
import pytest


_MINIMAL_TXT = b"Jane Doe\nSenior Python Engineer\n5 years experience\nSkills: FastAPI, LangGraph"


# ---------------------------------------------------------------------------
# Happy path — response shape
# ---------------------------------------------------------------------------

def test_analyze_response_has_required_keys(client):
    r = client.post(
        "/agent/analyze",
        files={"file": ("resume.txt", _MINIMAL_TXT, "text/plain")},
    )
    assert r.status_code == 200
    data = r.json()

    for key in ("request_id", "filename", "doc_type", "doc_type_confidence",
                "key_fields", "analysis", "summary", "actions_taken", "warnings"):
        assert key in data, f"missing key: {key}"


def test_analyze_confidence_is_in_valid_range(client):
    r = client.post(
        "/agent/analyze",
        files={"file": ("resume.txt", _MINIMAL_TXT, "text/plain")},
    )
    confidence = r.json()["doc_type_confidence"]
    assert 0.0 <= confidence <= 1.0


def test_analyze_x_session_id_header_accepted(client):
    r = client.post(
        "/agent/analyze",
        files={"file": ("resume.txt", _MINIMAL_TXT, "text/plain")},
        headers={"X-Session-ID": "candidate-jane-doe"},
    )
    assert r.status_code == 200


def test_analyze_optional_context_field(client):
    r = client.post(
        "/agent/analyze",
        files={"file": ("notes.txt", b"Interview notes for Jane Doe", "text/plain")},
        data={"context": "interview_notes"},
    )
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Parametrized — runner returns each valid doc_type correctly
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("doc_type,confidence", [
    ("resume",          0.95),
    ("cover_letter",    0.97),
    ("interview_notes", 0.88),
    ("scorecard",       0.91),
    ("unknown",         0.0),
])
def test_analyze_passes_through_doc_type(client, mock_analyze, doc_type, confidence):
    """Verify the endpoint serialises whatever doc_type the runner returns."""
    mock_analyze.return_value = {
        **mock_analyze.return_value,
        "doc_type":            doc_type,
        "doc_type_confidence": confidence,
    }
    r = client.post(
        "/agent/analyze",
        files={"file": ("doc.txt", b"content", "text/plain")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["doc_type"]            == doc_type
    assert data["doc_type_confidence"] == confidence


# ---------------------------------------------------------------------------
# Validation — bad input
# ---------------------------------------------------------------------------

def test_analyze_rejects_empty_file(client):
    r = client.post(
        "/agent/analyze",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


def test_analyze_rejects_missing_file_field(client):
    r = client.post("/agent/analyze", data={"context": "hint"})
    assert r.status_code == 422
