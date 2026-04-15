import pytest

@pytest.mark.asyncio
async def test_auth_login_success(client, test_user):
    """Verify that a registered user can login and get a JWT token."""
    response = await client.post(
        "/api/auth/jwt/login",
        data={"username": test_user.email, "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_auth_login_invalid_credentials(client, test_user):
    """Verify that invalid credentials return 400."""
    response = await client.post(
        "/api/auth/jwt/login",
        data={"username": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_protected_route_unauthorized(client):
    """Verify that protected routes reject requests without token."""
    response = await client.post("/api/optimizer/solve?strategy=PROFIT")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_authorized(client, auth_token):
    """Verify that protected routes accept valid JWT tokens."""
    # We don't need to run the full solver, just check if it gets past auth.
    # Note: /api/optimizer/solve requires a POST
    response = await client.post(
        "/api/optimizer/solve?strategy=PROFIT",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # It might return 200 or 500 (if data missing), but not 401
    assert response.status_code != 401
