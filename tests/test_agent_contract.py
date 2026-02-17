from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)

def test_agent_contract_has_required_keys():
    r = client.post("/agent", json={"message": "Check for anomaly yesterday"})
    assert r.status_code == 200
    data = r.json()

    assert "request_id" in data
    assert "response" in data
    assert "anomaly_detected" in data
    assert "actions_taken" in data
    assert "warnings" in data

    assert isinstance(data["request_id"], str)
    assert isinstance(data["response"], str)
    assert isinstance(data["anomaly_detected"], bool)
    assert isinstance(data["actions_taken"], list)
    assert isinstance(data["warnings"], list)

def test_agent_rejects_missing_message():
    r = client.post("/agent", json={})
    assert r.status_code == 422
