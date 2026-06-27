import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.utils.security import verify_token


@pytest.mark.asyncio
async def test_auth_workflow():
    """
    Integration test checking the full registration, login, verification, and refresh lifecycle.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register a new user
        register_payload = {
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "strongpassword123"
        }
        res_register = await ac.post("/api/auth/register", json=register_payload)
        # Handle the case where user might already exist from previous manual runs
        if res_register.status_code == 400:
            # Re-attempt with random suffix
            import random
            register_payload["email"] = f"testuser_{random.randint(1000, 9999)}@example.com"
            res_register = await ac.post("/api/auth/register", json=register_payload)

        assert res_register.status_code == 201
        user_data = res_register.json()
        assert user_data["name"] == register_payload["name"]
        assert user_data["email"] == register_payload["email"]
        assert user_data["is_verified"] is False

        # 2. Login with registered credentials
        login_payload = {
            "email": register_payload["email"],
            "password": register_payload["password"]
        }
        # JSON login
        res_login = await ac.post("/api/auth/login", json=login_payload)
        assert res_login.status_code == 200
        token_data = res_login.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Verify JWT Access Token subject matches user ID
        access_sub = verify_token(token_data["access_token"], "access")
        assert access_sub is not None
        assert int(access_sub) == user_data["id"]

        # 3. Refresh Token verification
        refresh_payload = {
            "refresh_token": token_data["refresh_token"]
        }
        res_refresh = await ac.post("/api/auth/refresh", json=refresh_payload)
        assert res_refresh.status_code == 200
        new_token_data = res_refresh.json()
        assert "access_token" in new_token_data
        assert "refresh_token" in new_token_data

        # 4. Forgot password & Reset password workflow
        # Trigger forgot password
        res_forgot = await ac.post(f"/api/auth/forgot-password?email={register_payload['email']}")
        assert res_forgot.status_code == 200
        forgot_data = res_forgot.json()
        debug_token = forgot_data.get("debug_token")
        assert debug_token is not None

        # Reset password with correct token
        res_reset = await ac.post(
            f"/api/auth/reset-password?token={debug_token}&new_password=newstrongpassword456"
        )
        assert res_reset.status_code == 200
        assert "successfully" in res_reset.json()["message"]

        # Attempt login with OLD password -> should fail
        res_login_old = await ac.post("/api/auth/login", json=login_payload)
        assert res_login_old.status_code == 401

        # Login with NEW password -> should succeed
        login_payload["password"] = "newstrongpassword456"
        res_login_new = await ac.post("/api/auth/login", json=login_payload)
        assert res_login_new.status_code == 200
