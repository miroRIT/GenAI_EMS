import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from emergencypulse.core.config import get_settings
from emergencypulse.core.security import create_access_token
from emergencypulse.db.session import AsyncSessionLocal
from emergencypulse.main import app

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def seed_available_ambulances() -> AsyncIterator[None]:
    if "DATABASE_URL" not in os.environ:
        pytest.skip("DATABASE_URL is required for integration tests")
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("UPDATE ambulances SET status = 'available'"))
            await session.commit()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Database is unavailable: {exc}")
    yield


@pytest.mark.asyncio
async def test_dispatch_incident_assigns_ambulance() -> None:
    token = create_access_token("dispatcher", ["dispatch:write"], get_settings())
    payload = {
        "patient_location": {"latitude": 40.7584, "longitude": -73.9857},
        "destination": {"latitude": 40.7648, "longitude": -73.9808},
        "severity": "critical",
        "notes": "Chest pain with shortness of breath",
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/api/v1/dispatch/incidents",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["severity"] == "critical"
    assert body["selected_route"]["estimated_arrival_seconds"] > 0
    assert body["selected_route"]["distance_to_patient_meters"] >= 0
