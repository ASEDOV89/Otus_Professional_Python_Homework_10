import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://testserver"
    ) as ac:
        response = await ac.post(
            "/register",
            data={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "testpassword",
            },
        )
        assert response.status_code == 303

        response = await ac.post(
            "/login", data={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == 303

        cookies = response.cookies.jar
        assert any(cookie.name == "access_token" for cookie in cookies)

        ac.cookies.update(response.cookies)

        response = await ac.get("/")
        assert response.status_code == 200
        assert "Привет, testuser" in response.text
