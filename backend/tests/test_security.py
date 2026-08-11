"""Security tests — business access control (IDOR prevention).

Verifies that `verify_business_access` correctly gates per-business data:
  - owner can access own business
  - outsider (another logged-in user) is denied (403)
  - active team member is allowed
  - super_admin bypasses ownership checks
"""

import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from main import app
from database import async_session
from models import User


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac


async def _register(client, prefix: str) -> dict:
    """Register a fresh user, return token + user id."""
    email = f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"
    resp = await client.post("/api/v1/auth/register", json={
        "full_name": f"Test {prefix}",
        "email": email,
        "password": "testpass123",
    })
    assert resp.status_code in [200, 201, 400, 409], resp.text
    data = resp.json()
    token = data.get("accessToken") or data.get("access_token")
    assert token, f"No token in register response: {data}"

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    return {"token": token, "user_id": me.json()["id"], "email": email}


async def _get_business_id(client, token: str) -> str:
    resp = await client.get("/api/v1/auth/business", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def _set_role(email: str, role: str):
    """Directly promote/demote a user's role in the DB."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        assert user, f"User {email} not found"
        user.role = role
        await db.commit()


# ── Owner ──

@pytest.mark.anyio
async def test_owner_can_access_own_business(client):
    owner = await _register(client, "owner")
    biz_id = await _get_business_id(client, owner["token"])
    resp = await client.get(
        f"/api/v1/bot/stats/{biz_id}",
        headers={"Authorization": f"Bearer {owner['token']}"},
    )
    assert resp.status_code == 200, resp.text


# ── Outsider (IDOR) ──

@pytest.mark.anyio
async def test_outsider_denied(client):
    owner = await _register(client, "ownera")
    biz_id = await _get_business_id(client, owner["token"])
    outsider = await _register(client, "outsider")

    # Outsider must NOT read owner's data
    resp = await client.get(
        f"/api/v1/bot/stats/{biz_id}",
        headers={"Authorization": f"Bearer {outsider['token']}"},
    )
    assert resp.status_code == 403, resp.text

    # Outsider must NOT create a coupon for owner's business
    resp = await client.post(
        "/api/v1/coupons",
        json={"business_id": biz_id, "code": f"LEAK{uuid.uuid4().hex[:6]}",
              "discount_type": "percent", "discount_value": 10},
        headers={"Authorization": f"Bearer {outsider['token']}"},
    )
    assert resp.status_code == 403, resp.text


# ── Team member ──

@pytest.mark.anyio
async def test_team_member_allowed(client):
    owner = await _register(client, "ownert")
    biz_id = await _get_business_id(client, owner["token"])
    member = await _register(client, "member")

    # Owner creates a team and adds the member
    team_resp = await client.post(
        "/api/v1/teams",
        json={"business_id": biz_id, "name": f"Sales {uuid.uuid4().hex[:6]}"},
        headers={"Authorization": f"Bearer {owner['token']}"},
    )
    assert team_resp.status_code == 200, team_resp.text
    team_id = team_resp.json()["id"]

    add_resp = await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": member["user_id"], "role": "staff"},
        headers={"Authorization": f"Bearer {owner['token']}"},
    )
    assert add_resp.status_code == 200, add_resp.text

    # Team member can now read the business data
    resp = await client.get(
        f"/api/v1/bot/stats/{biz_id}",
        headers={"Authorization": f"Bearer {member['token']}"},
    )
    assert resp.status_code == 200, resp.text


# ── Super admin ──

@pytest.mark.anyio
async def test_super_admin_allowed(client):
    owner = await _register(client, "owners")
    biz_id = await _get_business_id(client, owner["token"])
    admin = await _register(client, "superadmin")
    await _set_role(admin["email"], "super_admin")

    # Super admin can read any business
    resp = await client.get(
        f"/api/v1/bot/stats/{biz_id}",
        headers={"Authorization": f"Bearer {admin['token']}"},
    )
    assert resp.status_code == 200, resp.text


# ── Unauthenticated ──

@pytest.mark.anyio
async def test_unauthenticated_denied(client):
    resp = await client.get("/api/v1/bot/stats/some-business-id")
    assert resp.status_code == 401, resp.text
