import pytest
from httpx import ASGITransport, AsyncClient

from emergencypulse.main import app


@pytest.mark.asyncio
async def test_public_best_route_api_returns_route_estimate() -> None:
    payload = {
        "origin": {"latitude": 40.7584, "longitude": -73.9857},
        "destination": {"latitude": 40.7648, "longitude": -73.9808},
        "priority": "emergency",
        "include_alternatives": True,
        "use_signal_priority": True,
        "traffic_level": 1.35,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post("/api/v1/routes/best", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["estimated_distance_meters"] > 0
    assert body["traffic_adjusted_duration_seconds"] > 0
    assert body["priority_savings_seconds"] > 0
    assert len(body["route_polyline"]) == 3
    assert len(body["alternatives"]) == 2
