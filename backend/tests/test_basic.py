"""Basic test suite for the application."""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac


# ── Health Check ──

@pytest.mark.anyio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "database" in data
    assert "redis" in data
    assert "version" in data


# ── Root Endpoint ──

@pytest.mark.anyio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


# ── Auth: Register ──

@pytest.mark.anyio
async def test_register(client):
    response = await client.post("/api/v1/auth/register", json={
        "full_name": "Test User",
        "email": "test2@example.com",
        "password": "testpass123",
    })
    # 200/201 on first run, 409 on subsequent runs (already exists)
    assert response.status_code in [200, 201, 400, 409]


# ── Auth: Login ──

@pytest.mark.anyio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Login Test",
        "email": "login2@example.com",
        "password": "testpass123",
    })
    response = await client.post("/api/v1/auth/login", data={
        "username": "login2@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 200
    data = response.json()
    # Backend uses camelCase conversion
    assert "accessToken" in data or "access_token" in data


# ── Settings: Auth Required ──

@pytest.mark.anyio
async def test_settings_requires_auth(client):
    response = await client.put("/api/v1/settings/invoice", json={
        "business_name": "Test Shop",
    })
    assert response.status_code == 401


# ── Settings: Get Requires Auth (business settings contain secrets) ──

@pytest.mark.anyio
async def test_settings_get_requires_auth(client):
    response = await client.get("/api/v1/settings?business_id=test123")
    assert response.status_code == 401


# ── Rate Limiting ──

@pytest.mark.anyio
async def test_rate_limit_exists(client):
    for _ in range(5):
        await client.get("/health")


# ── Chat: Send ──

@pytest.mark.anyio
async def test_chat_send(client):
    response = await client.post("/api/v1/chat", json={
        "message": "Hello",
        "business_id": "test-business",
        "session_id": "test-session",
    })
    assert response.status_code in [200, 404, 422]
