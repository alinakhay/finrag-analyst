from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["documents"] == 3


def test_lists_filings() -> None:
    response = client.get("/api/v1/filings")
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {"meridian", "northstar", "helix"}


def test_analysis_is_grounded_and_cited() -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"filing_id": "meridian", "question": "What changed in credit risk?"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["filing_id"] == "meridian"
    assert len(result["citations"]) == 2
    assert result["citations"][0]["chunk_id"] == "meridian-credit-01"
    assert "2.6%" in result["answer"]
    assert result["groundedness"] > 0.5


def test_unknown_filing_returns_404() -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"filing_id": "missing", "question": "What changed this year?"},
    )
    assert response.status_code == 404


def test_question_validation() -> None:
    response = client.post(
        "/api/v1/analyze", json={"filing_id": "meridian", "question": "why"}
    )
    assert response.status_code == 422
