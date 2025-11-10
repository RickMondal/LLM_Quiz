import os
import pytest
from httpx import AsyncClient
from app.main import app
from app.config import get_settings

pytestmark = pytest.mark.anyio

@pytest.fixture
def anyio_backend():
    return "asyncio"

async def test_quiz_endpoint_contract():
    settings = get_settings()
    settings.secret = "testsecret"
    settings.email = "student@example.com"
    payload = {"email": settings.email, "secret": settings.secret, "url": "https://example.com/quiz-demo"}
    # Use ASGITransport explicitly to avoid deprecated shortcut and prevent background browser launch
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/quiz", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "accepted"
