from httpx import AsyncClient


async def test_health_check_returns_ok_status(async_client: AsyncClient, test_engine) -> None:
    response = await async_client.get("http://localhost:8000/health-check")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


async def test_openapi_spec_is_served(async_client: AsyncClient) -> None:
    response = await async_client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health-check" in response.json()["paths"]
    assert "/api/v1/public/quote/{plate}" in response.json()["paths"]
