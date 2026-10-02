from fastapi.testclient import TestClient

from src.server.main import app


def test_health_check_returns_ok_status() -> None:
    client = TestClient(app, base_url="http://localhost:8000")
    response = client.get("/health-check")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_openapi_spec_is_served() -> None:
    client = TestClient(app, base_url="http://localhost:8000")
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200

    print(response.json())

    assert sorted(response.json()["paths"]) == [
        "/health-check",
    ]
