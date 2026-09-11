from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["market_assets"] == 3
    assert response.json()["documents"] == 3


def test_lists_market_assets() -> None:
    response = client.get("/api/v1/market-assets")
    assert response.status_code == 200
    assert {item["ticker"] for item in response.json()} == {"ASTR", "NVRB", "ORBT"}
    assert all(item["benchmark"] for item in response.json())


def test_market_analysis_returns_evidence_and_event_metrics() -> None:
    response = client.post(
        "/api/v1/market-analyze",
        json={
            "asset_id": "astr",
            "question": "Did guidance explain the unusual price and volume move?",
            "event_id": "astr-guidance",
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["ticker"] == "ASTR"
    assert result["evidence"][0]["id"] == "astr-guidance"
    assert result["evidence"][0]["quote"]
    assert result["metrics"]["cumulative_abnormal_return"] > 0
    assert result["metrics"]["volume_z_score"] > 2
    assert len(result["trace"]) == 4


def test_negative_catalyst_has_negative_abnormal_return() -> None:
    response = client.post(
        "/api/v1/market-analyze",
        json={
            "asset_id": "nvrb",
            "question": "What credit news caused the sell-off?",
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["evidence"][0]["category"] == "Credit"
    assert result["metrics"]["cumulative_abnormal_return"] < 0


def test_unknown_asset_returns_404() -> None:
    response = client.post(
        "/api/v1/market-analyze",
        json={"asset_id": "missing", "question": "What moved the price?"},
    )
    assert response.status_code == 404


def test_market_question_validation() -> None:
    response = client.post(
        "/api/v1/market-analyze",
        json={"asset_id": "astr", "question": "why"},
    )
    assert response.status_code == 422


def test_legacy_filing_analysis_remains_compatible() -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"filing_id": "meridian", "question": "What changed in credit risk?"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["filing_id"] == "meridian"
    assert result["citations"][0]["chunk_id"] == "meridian-credit-01"
